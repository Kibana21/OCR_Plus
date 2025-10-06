"""
Image document processor with proper OOP structure
"""

import time
from typing import Dict, Any
from pathlib import Path

import pytesseract
from PIL import Image
import cv2
import numpy as np

from core.base_classes import BaseDocumentProcessor, DocumentType, ProcessingResult, DocumentMetadata
from core.exceptions import DocumentProcessingError
from core.image_preprocessing import ImagePreprocessor


class ImageProcessor(BaseDocumentProcessor):
    """Image document processor with OCR capabilities"""
    
    def __init__(self, temp_dir: str = "temp_images"):
        super().__init__(temp_dir)
        self.supported_formats = {'jpg', 'jpeg', 'png', 'bmp', 'tiff'}
        self.image_preprocessor = ImagePreprocessor()
        self.enable_orientation_correction = True  # Default to enabled
    
    def process_document(self, file_path: str) -> Dict[str, Any]:
        """
        Process image file - extract text using OCR and prepare for vision processing
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Dictionary containing text content, images, and metadata
        """
        start_time = time.time()
        
        try:
            # Get document metadata
            metadata = self.get_document_metadata(file_path)
            
            # Process image
            result = self._process_image(Path(file_path))
            
            # Update metadata with processing results
            metadata.total_pages = 1  # Images are single page
            metadata.has_images = True
            metadata.text_length = len(result.get('text_content', ''))
            
            processing_time = time.time() - start_time
            
            return {
                'type': 'image',
                'file_path': str(file_path),
                'text_content': result.get('text_content', ''),
                'images': result.get('images', []),
                'metadata': {
                    'document_metadata': metadata,
                    'processing_time': processing_time,
                    'total_pages': 1,
                    'has_images': True,
                    'text_length': metadata.text_length,
                    'format': result.get('format'),
                    'mode': result.get('mode'),
                    'size': result.get('size')
                }
            }
            
        except Exception as e:
            raise DocumentProcessingError(f"Error processing image {file_path}: {str(e)}")
    
    def _process_image(self, image_path: Path) -> Dict[str, Any]:
        """Process image file - extract text using OCR and prepare for vision processing"""
        result = {
            'text_content': '',
            'images': [],
            'format': None,
            'mode': None,
            'size': None
        }
        
        try:
            # Load image
            image = Image.open(image_path)
            
            # Store image metadata
            result['format'] = image.format
            result['mode'] = image.mode
            result['size'] = image.size
            
            # Extract text using OCR
            try:
                ocr_text = pytesseract.image_to_string(image)
                result['text_content'] = ocr_text
            except Exception as e:
                print(f"OCR extraction failed: {e}")
                result['text_content'] = ""
            
            # Enhance image for better processing (includes orientation correction)
            enhanced_image = self._enhance_image(image)
            
            # Create corrected_images directory
            corrected_dir = Path("corrected_images")
            corrected_dir.mkdir(exist_ok=True)
            
            # Get document name for unique file naming
            doc_name = image_path.stem
            
            # Save original image
            original_filename = corrected_dir / f"{doc_name}_original.png"
            image.save(original_filename, format='PNG')
            
            # Save corrected/enhanced image
            corrected_filename = corrected_dir / f"{doc_name}_corrected.png"
            enhanced_image.save(corrected_filename, format='PNG')
            
            print(f"💾 Saved corrected image: {corrected_filename.name}")
            
            result['images'] = [{
                'page_number': 1,
                'image_object': enhanced_image,  # LLM gets the corrected image
                'width': enhanced_image.width,
                'height': enhanced_image.height,
                'file_path': str(corrected_filename),
                'original_file_path': str(original_filename),
                'orientation_corrected': True
            }]
            
        except Exception as e:
            print(f"Error processing image: {e}")
            raise
        
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
                        print(f"🔄 Image orientation corrected: rotated {preprocessing_result['rotation_applied']}°")
                    
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
            # 1. Convert to grayscale for processing
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # 2. Apply adaptive thresholding to improve text clarity
            enhanced = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # 3. Apply morphological operations to clean up the image
            kernel = np.ones((1, 1), np.uint8)
            enhanced = cv2.morphologyEx(enhanced, cv2.MORPH_CLOSE, kernel)
            
            # 4. Convert back to RGB
            enhanced_rgb = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2RGB)
            
            # Convert back to PIL Image
            return Image.fromarray(enhanced_rgb)
            
        except Exception as e:
            print(f"Image enhancement failed: {e}")
            return image
    
    def extract_text_with_confidence(self, image_path: str) -> Dict[str, Any]:
        """Extract text with confidence scores"""
        try:
            image = Image.open(image_path)
            
            # Get detailed OCR data with confidence
            ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            # Extract text with confidence scores
            text_with_confidence = []
            for i, conf in enumerate(ocr_data['conf']):
                if int(conf) > 0:  # Only include text with confidence > 0
                    text_with_confidence.append({
                        'text': ocr_data['text'][i],
                        'confidence': int(conf),
                        'bbox': {
                            'left': ocr_data['left'][i],
                            'top': ocr_data['top'][i],
                            'width': ocr_data['width'][i],
                            'height': ocr_data['height'][i]
                        }
                    })
            
            return {
                'success': True,
                'text_with_confidence': text_with_confidence,
                'full_text': pytesseract.image_to_string(image),
                'average_confidence': sum(item['confidence'] for item in text_with_confidence) / len(text_with_confidence) if text_with_confidence else 0
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
