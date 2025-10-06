"""
PDF document processor with proper OOP structure
"""

import io
import time
from typing import Dict, Any, List
from pathlib import Path

import PyPDF2
import fitz  # PyMuPDF
from PIL import Image
import cv2
import numpy as np

from core.base_classes import BaseDocumentProcessor, DocumentType, ProcessingResult, DocumentMetadata
from core.exceptions import DocumentProcessingError
from core.image_preprocessing import ImagePreprocessor


class PDFProcessor(BaseDocumentProcessor):
    """PDF document processor with enhanced functionality"""
    
    def __init__(self, temp_dir: str = "temp_images"):
        super().__init__(temp_dir)
        self.supported_formats = {'pdf'}
        self.image_preprocessor = ImagePreprocessor()
        self.enable_orientation_correction = True  # Default to enabled
    
    def process_document(self, file_path: str) -> Dict[str, Any]:
        """
        Process PDF document - extract text and convert pages to images
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary containing text content, images, and metadata
        """
        start_time = time.time()
        
        try:
            # Get document metadata
            metadata = self.get_document_metadata(file_path)
            
            # Process PDF
            result = self._process_pdf(Path(file_path))
            
            # Update metadata with processing results
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
                    'document_metadata': metadata,
                    'processing_time': processing_time,
                    'total_pages': metadata.total_pages,
                    'has_images': metadata.has_images,
                    'text_length': metadata.text_length
                }
            }
            
        except Exception as e:
            raise DocumentProcessingError(f"Error processing PDF {file_path}: {str(e)}")
    
    def _process_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """Process PDF file - extract text and convert pages to images"""
        result = {
            'text_content': '',
            'images': []
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
            print(f"Error extracting text from PDF: {e}")
            result['text_content'] = ""
        
        # Convert PDF pages to images using PyMuPDF
        try:
            pdf_document = fitz.open(pdf_path)
            image_data = []
            
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                
                # Convert page to image with high DPI
                mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to PIL Image
                img_data = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_data))
                
                # Enhance image quality (includes orientation correction)
                enhanced_image = self._enhance_image(image)
                
                # Create corrected_images directory
                corrected_dir = Path("corrected_images")
                corrected_dir.mkdir(exist_ok=True)
                
                # Get document name for unique file naming
                doc_name = pdf_path.stem
                
                # Save original page image
                original_filename = corrected_dir / f"{doc_name}_page_{page_num+1}_original.png"
                image.save(original_filename, format='PNG')
                
                # Save corrected/enhanced page image
                corrected_filename = corrected_dir / f"{doc_name}_page_{page_num+1}_corrected.png"
                enhanced_image.save(corrected_filename, format='PNG')
                
                print(f"💾 Saved corrected image: {corrected_filename.name}")
                
                image_data.append({
                    'page_number': page_num + 1,
                    'image_object': enhanced_image,  # LLM gets the corrected image
                    'width': enhanced_image.width,
                    'height': enhanced_image.height,
                    'file_path': str(corrected_filename),
                    'original_file_path': str(original_filename),
                    'orientation_corrected': True
                })
            
            pdf_document.close()
            result['images'] = image_data
            
        except Exception as e:
            print(f"Error converting PDF to images: {e}")
            print("Trying fallback method...")
            
            # Fallback: Try to extract text-only and create simple image representation
            try:
                result['images'] = self._create_fallback_images(pdf_path)
            except Exception as e2:
                print(f"Fallback method also failed: {e2}")
                result['images'] = []
        
        return result
    
    def _enhance_image(self, image: Image.Image) -> Image.Image:
        """Enhance image quality for better OCR and vision processing with orientation correction"""
        try:
            if self.enable_orientation_correction:
                # Use the new image preprocessor for comprehensive enhancement
                preprocessing_result = self.image_preprocessor.process_document_page(image)
                
                if preprocessing_result['processing_successful']:
                    enhanced_image = preprocessing_result['processed_image']
                    
                    # Log orientation correction if applied
                    if preprocessing_result['orientation_corrected']:
                        print(f"🔄 Page orientation corrected: rotated {preprocessing_result['rotation_applied']}°")
                    
                    return enhanced_image
                else:
                    # Fallback to original enhancement if preprocessing fails
                    print("⚠️  Using fallback image enhancement")
                    return self._fallback_enhance_image(image)
            else:
                # Skip orientation correction, use fallback enhancement
                return self._fallback_enhance_image(image)
                
        except Exception as e:
            print(f"⚠️  Image preprocessing failed: {e}")
            return self._fallback_enhance_image(image)
    
    def _fallback_enhance_image(self, image: Image.Image) -> Image.Image:
        """Fallback image enhancement method"""
        try:
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert to numpy array for OpenCV processing
            img_array = np.array(image)
            
            # Apply image enhancement
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Apply adaptive thresholding to improve text clarity
            enhanced = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Apply morphological operations to clean up the image
            kernel = np.ones((1, 1), np.uint8)
            enhanced = cv2.morphologyEx(enhanced, cv2.MORPH_CLOSE, kernel)
            
            # Convert back to RGB
            enhanced_rgb = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2RGB)
            
            return Image.fromarray(enhanced_rgb)
            
        except Exception as e:
            print(f"Image enhancement failed: {e}")
            return image
    
    def _create_fallback_images(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """Create fallback image representations when PyMuPDF fails"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                image_data = []
                
                for page_num in range(len(pdf_reader.pages)):
                    page_text = pdf_reader.pages[page_num].extract_text()
                    
                    # Create a simple image with text
                    img = Image.new('RGB', (800, 1000), color='white')
                    
                    # Save as PNG
                    page_filename = self.temp_dir / f"page_{page_num+1}_fallback.png"
                    img.save(page_filename, format='PNG')
                    
                    image_data.append({
                        'page_number': page_num + 1,
                        'image_object': img,
                        'width': img.width,
                        'height': img.height,
                        'file_path': str(page_filename),
                        'fallback': True,
                        'text_content': page_text[:500]
                    })
                
                return image_data
                
        except Exception as e:
            print(f"Fallback image creation failed: {e}")
            return []
    
    def extract_text_by_page(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract text from each page separately"""
        pdf_path = Path(pdf_path)
        pages_data = []
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    
                    pages_data.append({
                        'page_number': page_num + 1,
                        'text_content': page_text,
                        'text_length': len(page_text)
                    })
                    
        except Exception as e:
            print(f"Error extracting text by page: {e}")
        
        return pages_data
