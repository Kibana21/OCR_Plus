"""
Azure-Only Image Processor - Clean and Simple
Uses ONLY Azure Document Intelligence for tilt/rotation detection
NO OpenCV orientation detection, NO heavy enhancement
"""

import os
import time
import json
from typing import Dict, Any
from pathlib import Path

import pytesseract
from PIL import Image
import cv2
import numpy as np
from dotenv import load_dotenv

from core.base_classes import BaseDocumentProcessor
from core.exceptions import DocumentProcessingError

# Import Azure
try:
    from pdf_utils import AzureOCREngine
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    print("❌ Azure Document Intelligence not available")


class ImageProcessorAzureOnly(BaseDocumentProcessor):
    """Azure-only image processor"""

    def __init__(self, temp_dir: str = "temp_images",
                 tilt_threshold: float = 5.0,
                 save_ground_truth: bool = False):
        """
        Initialize Azure-only image processor

        Args:
            temp_dir: Temporary directory
            tilt_threshold: Minimum angle to trigger correction
            save_ground_truth: Save full Azure Document Intelligence response
        """
        super().__init__(temp_dir)
        self.supported_formats = {'jpg', 'jpeg', 'png', 'bmp', 'tiff'}
        self.tilt_threshold = tilt_threshold
        self.save_ground_truth = save_ground_truth

        if not AZURE_AVAILABLE:
            raise ImportError("Azure Document Intelligence not available")

        self._initialize_azure()

    def _initialize_azure(self):
        """Initialize Azure"""
        load_dotenv()

        azure_endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
        azure_key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")

        if not azure_endpoint or not azure_key:
            raise ValueError("Azure credentials not found")

        try:
            self.azure_ocr = AzureOCREngine(azure_endpoint, azure_key, save_ground_truth=self.save_ground_truth)
            print(f"✅ Azure initialized (threshold: {self.tilt_threshold}°)")
            if self.save_ground_truth:
                print(f"   📊 Ground truth saving: ENABLED")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Azure: {e}")

    def process_document(self, file_path: str) -> Dict[str, Any]:
        """Process image using Azure-only methodology"""
        start_time = time.time()

        try:
            metadata = self.get_document_metadata(file_path)
            result = self._process_image(Path(file_path))

            metadata.total_pages = 1
            metadata.has_images = True
            metadata.text_length = len(result.get('text_content', ''))

            processing_time = time.time() - start_time

            return {
                'type': 'image',
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
                    'correction_info': result.get('correction_info', {})
                }
            }

        except Exception as e:
            raise DocumentProcessingError(f"Error processing image {file_path}: {str(e)}")

    def _process_image(self, image_path: Path) -> Dict[str, Any]:
        """Process image with Azure detection"""
        result = {
            'text_content': '',
            'images': [],
            'correction_info': {}
        }

        try:
            # Load image
            original_image = Image.open(image_path)

            print(f"\n📷 Processing Image: {image_path.name}")

            # Process with Azure
            final_image, correction_info = self._process_with_azure(original_image)
            result['correction_info'] = correction_info

            # Extract text using OCR (on corrected image)
            try:
                ocr_text = pytesseract.image_to_string(final_image)
                result['text_content'] = ocr_text
            except Exception as e:
                print(f"⚠️  OCR failed: {e}")
                result['text_content'] = ""

            # Save images
            saved_paths = self._save_images(
                image_path.stem,
                original_image, final_image, correction_info
            )

            # Save ground truth if enabled
            if self.save_ground_truth and 'azure_ground_truth' in correction_info:
                self._save_ground_truth(
                    image_path.stem,
                    correction_info['azure_ground_truth']
                )

            result['images'] = [{
                'page_number': 1,
                'image_object': final_image,
                'width': final_image.width,
                'height': final_image.height,
                'file_path': str(saved_paths['final_path']),
                'original_file_path': str(saved_paths['original_path']),
                'corrected': correction_info['corrected'],
                'detected_angle': correction_info['detected_angle']
            }]

        except Exception as e:
            print(f"❌ Error: {e}")
            raise

        return result

    def _process_with_azure(self, image: Image.Image) -> tuple:
        """Process with Azure detection"""
        correction_info = {
            'detected_angle': 0.0,
            'corrected': False,
            'method': 'azure'
        }

        try:
            # Convert to numpy
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

            # Get full Azure response for ground truth if enabled
            if self.save_ground_truth:
                print(f"      📊 Getting full Azure response...")
                full_response = self.azure_ocr.analyze_document_full(gray, page_num=1)
                correction_info['azure_ground_truth'] = full_response

            print(f"      Angle: {detected_angle:.2f}°")

            # Apply correction if needed
            if abs(detected_angle) >= self.tilt_threshold:
                print(f"      🔄 Correcting...")
                corrected_np = self._correct_rotation(image_np, detected_angle)
                final_image = Image.fromarray(corrected_np)
                correction_info['corrected'] = True
                print(f"      ✅ Corrected")
            else:
                print(f"      ✅ No correction needed")
                final_image = image

            return final_image, correction_info

        except Exception as e:
            print(f"      ❌ Failed: {e}")
            correction_info['error'] = str(e)
            return image, correction_info

    def _correct_rotation(self, image: np.ndarray, angle: float) -> np.ndarray:
        """Correct rotation"""
        abs_angle = abs(angle)

        # 90-degree rotations
        if 85 < abs_angle < 95:
            if angle > 0:
                return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
            else:
                return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)

        # 180-degree rotation
        elif 175 < abs_angle < 185:
            return cv2.rotate(image, cv2.ROTATE_180)

        # Arbitrary angle
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

    def _save_images(self, doc_name: str,
                    original_image: Image.Image,
                    final_image: Image.Image,
                    correction_info: Dict) -> Dict[str, Path]:
        """
        Save images - ONLY if correction was applied

        Saves 3 versions only when tilt was corrected:
        - doc_original.png (before correction)
        - doc_corrected_12deg.png (after correction with angle)
        - doc_final.png (what LLM receives)

        If no correction: saves nothing (saves disk space)
        """
        corrected_dir = Path("corrected_images")
        corrected_dir.mkdir(exist_ok=True)

        # Only save if correction was applied
        if correction_info['corrected']:
            # Save original (before correction)
            original_path = corrected_dir / f"{doc_name}_original.png"
            original_image.save(original_path, format='PNG')

            # Save corrected with angle
            angle = int(abs(correction_info['detected_angle']))
            corrected_path = corrected_dir / f"{doc_name}_corrected_{angle}deg.png"
            final_image.save(corrected_path, format='PNG')

            # Save final (what LLM receives)
            final_path = corrected_dir / f"{doc_name}_final.png"
            final_image.save(final_path, format='PNG')

            print(f"      💾 Saved 3 versions: original, corrected_{angle}deg, final")

            return {
                'original_path': original_path,
                'final_path': final_path
            }
        else:
            # No correction needed - don't save anything
            print(f"      ✓ No correction needed - not saved (saves disk space)")

            return {
                'original_path': None,
                'final_path': None
            }

    def _save_ground_truth(self, doc_name: str, azure_response: dict):
        """Save Azure Document Intelligence full response as ground truth"""
        ground_truth_dir = Path("ground_truth")
        ground_truth_dir.mkdir(exist_ok=True)

        output_file = ground_truth_dir / f"{doc_name}_azure_ground_truth.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(azure_response, f, indent=2, ensure_ascii=False)

        # Show stats
        avg_conf = azure_response.get('average_confidence', 0.0)
        word_count = len(azure_response.get('pages', [{}])[0].get('words', []))
        print(f"      💾 Saved ground truth: {output_file.name}")
        print(f"         Words: {word_count}, Avg Confidence: {avg_conf:.3f}")
