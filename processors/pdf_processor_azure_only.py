"""
Azure-Only PDF Processor - Clean and Simple
Uses ONLY Azure Document Intelligence for tilt/rotation detection
NO OpenCV orientation detection, NO heavy enhancement

Philosophy:
- Trust Azure for all angle detection (0-360°)
- Only correct if angle > threshold
- Keep images clean and unprocessed
- Clear naming showing what was corrected
"""

import io
import os
import time
from typing import Dict, Any, List, Optional
from pathlib import Path

import PyPDF2
import fitz  # PyMuPDF
from PIL import Image
import cv2
import numpy as np
from dotenv import load_dotenv

from core.base_classes import BaseDocumentProcessor, DocumentType, ProcessingResult, DocumentMetadata
from core.exceptions import DocumentProcessingError

# Import Azure tilt correction
try:
    from pdf_utils import AzureOCREngine
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    print("❌ Azure Document Intelligence not available. Install: pip install azure-ai-documentintelligence")


class PDFProcessorAzureOnly(BaseDocumentProcessor):
    """
    Pure Azure-based PDF processor

    Uses Azure Document Intelligence for ALL angle detection:
    - Small tilts (3°, 8°, 12°)
    - Major rotations (90°, 180°, 270°)
    - Everything in between

    NO OpenCV orientation detection
    NO heavy image enhancement
    """

    def __init__(self, temp_dir: str = "temp_images",
                 tilt_threshold: float = 5.0,
                 save_all: bool = False):
        """
        Initialize Azure-only PDF processor

        Args:
            temp_dir: Temporary directory for processing
            tilt_threshold: Minimum angle (degrees) to trigger correction (default: 5.0)
            save_all: Save all pages even if not corrected (default: False)
        """
        super().__init__(temp_dir)
        self.supported_formats = {'pdf'}
        self.tilt_threshold = tilt_threshold
        self.save_all = save_all

        # Initialize Azure OCR
        if not AZURE_AVAILABLE:
            raise ImportError("Azure Document Intelligence not available. Cannot proceed.")

        self._initialize_azure()

    def _initialize_azure(self):
        """Initialize Azure Document Intelligence"""
        load_dotenv()

        azure_endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
        azure_key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")

        if not azure_endpoint or not azure_key:
            raise ValueError(
                "Azure credentials not found. Set:\n"
                "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=...\n"
                "AZURE_DOCUMENT_INTELLIGENCE_KEY=..."
            )

        try:
            self.azure_ocr = AzureOCREngine(azure_endpoint, azure_key)
            print(f"✅ Azure Document Intelligence initialized")
            print(f"   Correction threshold: {self.tilt_threshold}°")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Azure: {e}")

    def process_document(self, file_path: str) -> Dict[str, Any]:
        """Process PDF using Azure-only methodology"""
        start_time = time.time()

        try:
            metadata = self.get_document_metadata(file_path)
            result = self._process_pdf(Path(file_path))

            metadata.total_pages = len(result.get('images', []))
            metadata.has_images = len(result.get('images', [])) > 0
            metadata.text_length = len(result.get('text_content', ''))

            processing_time = time.time() - start_time

            return {
                'type': 'pdf',
                'file_path': str(file_path),
                'text_content': result.get('text_content', ''),
                'images': result.get('images', []),
                'metadata': {
                    'file_path': metadata.file_path,
                    'file_size': metadata.file_size,
                    'file_type': metadata.file_type.value,  # Convert enum to string
                    'processing_time': processing_time,
                    'total_pages': metadata.total_pages,
                    'has_images': metadata.has_images,
                    'text_length': metadata.text_length,
                    'processor': 'azure_only',
                    'corrections_summary': result.get('corrections_summary', {})
                }
            }

        except Exception as e:
            raise DocumentProcessingError(f"Error processing PDF {file_path}: {str(e)}")

    def _process_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """Process PDF with Azure-only detection and correction"""
        result = {
            'text_content': '',
            'images': [],
            'corrections_summary': {
                'total_pages': 0,
                'corrected_pages': 0,
                'angles_detected': [],
                'corrections_applied': []
            }
        }

        # Extract text from PDF
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_content = []

                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    text_content.append(f"--- Page {page_num + 1} ---\n{page_text}")

                result['text_content'] = '\n\n'.join(text_content)

        except Exception as e:
            print(f"⚠️  Text extraction failed: {e}")
            result['text_content'] = ""

        # Convert PDF pages to images and process with Azure
        try:
            pdf_document = fitz.open(pdf_path)
            image_data = []

            print(f"\n📄 Processing PDF: {pdf_path.name}")
            print(f"   Total pages: {pdf_document.page_count}")
            print(f"   Threshold: {self.tilt_threshold}°")
            print("=" * 80)

            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]

                # Convert page to high-quality image
                mat = fitz.Matrix(2.0, 2.0)  # 2x zoom = ~144 DPI
                pix = page.get_pixmap(matrix=mat)

                # Convert to PIL Image
                img_data = pix.tobytes("png")
                original_image = Image.open(io.BytesIO(img_data))

                print(f"\n📄 Page {page_num + 1}/{pdf_document.page_count}:")

                # Process with Azure
                final_image, correction_info = self._process_page_with_azure(
                    original_image, page_num + 1
                )

                # Update summary
                result['corrections_summary']['total_pages'] += 1
                result['corrections_summary']['angles_detected'].append(correction_info['detected_angle'])

                if correction_info['corrected']:
                    result['corrections_summary']['corrected_pages'] += 1
                    result['corrections_summary']['corrections_applied'].append({
                        'page': page_num + 1,
                        'angle': correction_info['detected_angle']
                    })

                # Save images
                saved_paths = self._save_page_images(
                    pdf_path.stem, page_num + 1,
                    original_image, final_image, correction_info
                )

                image_data.append({
                    'page_number': page_num + 1,
                    'image_object': final_image,  # LLM gets this
                    'width': final_image.width,
                    'height': final_image.height,
                    'file_path': str(saved_paths['final_path']),
                    'original_file_path': str(saved_paths['original_path']),
                    'corrected': correction_info['corrected'],
                    'detected_angle': correction_info['detected_angle'],
                    'severity': correction_info['severity']
                })

            pdf_document.close()
            result['images'] = image_data

            # Print summary
            self._print_summary(result['corrections_summary'])

        except Exception as e:
            print(f"❌ Error converting PDF: {e}")
            result['images'] = []

        return result

    def _process_page_with_azure(self, image: Image.Image, page_num: int) -> tuple:
        """
        Process single page with Azure detection

        Returns:
            Tuple of (final_image, correction_info)
        """
        correction_info = {
            'detected_angle': 0.0,
            'corrected': False,
            'severity': 'none',
            'method': 'azure'
        }

        try:
            # Convert PIL to numpy
            image_np = np.array(image)

            # Convert to grayscale for Azure
            if len(image_np.shape) == 3:
                gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
            else:
                gray = image_np

            # Detect angle with Azure
            print(f"   🔍 Azure analyzing...")
            detected_angle = self.azure_ocr.get_page_angle(gray)
            correction_info['detected_angle'] = detected_angle

            # Classify severity
            abs_angle = abs(detected_angle)
            if abs_angle > 15 or abs_angle in [90, 180, 270]:
                severity = "severe"
            elif abs_angle > 5:
                severity = "moderate"
            elif abs_angle > 1:
                severity = "slight"
            else:
                severity = "none"

            correction_info['severity'] = severity

            print(f"      Angle: {detected_angle:.2f}° (severity: {severity})")

            # Apply correction if needed
            if abs_angle >= self.tilt_threshold:
                print(f"      🔄 Correcting (threshold: {self.tilt_threshold}°)...")
                corrected_np = self._correct_rotation(image_np, detected_angle)
                final_image = Image.fromarray(corrected_np)
                correction_info['corrected'] = True
                print(f"      ✅ Corrected")
            else:
                print(f"      ✅ No correction needed (< {self.tilt_threshold}°)")
                final_image = image
                correction_info['corrected'] = False

            return final_image, correction_info

        except Exception as e:
            print(f"      ❌ Azure processing failed: {e}")
            correction_info['error'] = str(e)
            return image, correction_info

    def _correct_rotation(self, image: np.ndarray, angle: float) -> np.ndarray:
        """
        Correct rotation using optimal method based on angle

        Args:
            image: Image as numpy array
            angle: Angle in degrees (positive = clockwise)

        Returns:
            Corrected image as numpy array
        """
        abs_angle = abs(angle)

        # 90-degree rotations (optimized, no quality loss)
        if 85 < abs_angle < 95:
            if angle > 0:
                return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
            else:
                return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)

        # 180-degree rotation
        elif 175 < abs_angle < 185:
            return cv2.rotate(image, cv2.ROTATE_180)

        # 270-degree rotation
        elif 265 < abs_angle < 275:
            if angle > 0:
                return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
            else:
                return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)

        # Arbitrary angle (for tilts)
        else:
            h, w = image.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, -angle, 1.0)
            corrected = cv2.warpAffine(
                image, M, (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE
            )
            return corrected

    def _save_page_images(self, doc_name: str, page_num: int,
                         original_image: Image.Image,
                         final_image: Image.Image,
                         correction_info: Dict) -> Dict[str, Path]:
        """
        Save images with clear naming - ONLY saves if correction was applied

        Naming (only for corrected pages):
        - doc_page_001_original.png          (before correction)
        - doc_page_001_corrected_12deg.png   (after correction, with angle)
        - doc_page_001_final.png             (what LLM receives)

        If no correction needed: saves nothing (saves disk space)
        """
        corrected_dir = Path("corrected_images")
        corrected_dir.mkdir(exist_ok=True)

        page_str = f"{page_num:03d}"

        # Only save if correction was applied (or save_all is True)
        if correction_info['corrected']:
            # Save original (before correction)
            original_path = corrected_dir / f"{doc_name}_page_{page_str}_original.png"
            original_image.save(original_path, format='PNG')

            # Save corrected version with angle in filename
            angle = int(abs(correction_info['detected_angle']))
            corrected_path = corrected_dir / f"{doc_name}_page_{page_str}_corrected_{angle}deg.png"
            final_image.save(corrected_path, format='PNG')

            # Save final (what LLM receives - same as corrected)
            final_path = corrected_dir / f"{doc_name}_page_{page_str}_final.png"
            final_image.save(final_path, format='PNG')

            print(f"      💾 Saved 3 versions: original, corrected_{angle}deg, final")

            return {
                'original_path': original_path,
                'final_path': final_path
            }

        elif self.save_all:
            # Save only final if save_all is True but no correction needed
            final_path = corrected_dir / f"{doc_name}_page_{page_str}_final.png"
            final_image.save(final_path, format='PNG')
            print(f"      💾 Saved: {final_path.name} (unchanged)")

            return {
                'original_path': None,
                'final_path': final_path
            }

        else:
            # No correction and save_all is False: don't save anything
            print(f"      ✓ No correction needed - not saved (saves disk space)")

            return {
                'original_path': None,
                'final_path': None
            }

    def _print_summary(self, summary: Dict):
        """Print processing summary"""
        print("\n" + "=" * 80)
        print("📊 PROCESSING SUMMARY")
        print("=" * 80)
        print(f"Total pages: {summary['total_pages']}")
        print(f"Pages corrected: {summary['corrected_pages']}")
        print(f"Pages unchanged: {summary['total_pages'] - summary['corrected_pages']}")

        if summary['corrections_applied']:
            print(f"\n✅ Corrections applied:")
            for correction in summary['corrections_applied']:
                print(f"   Page {correction['page']}: {correction['angle']:.2f}°")

        print(f"\n📐 Angle distribution:")
        angles = summary['angles_detected']
        none_count = sum(1 for a in angles if abs(a) < 1)
        slight_count = sum(1 for a in angles if 1 <= abs(a) < 5)
        moderate_count = sum(1 for a in angles if 5 <= abs(a) < 15)
        severe_count = sum(1 for a in angles if abs(a) >= 15)

        print(f"   None (< 1°): {none_count}")
        print(f"   Slight (1-5°): {slight_count}")
        print(f"   Moderate (5-15°): {moderate_count}")
        print(f"   Severe (> 15°): {severe_count}")
        print("=" * 80)
