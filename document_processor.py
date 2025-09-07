"""
Document Processor for PDF and Image files
Handles conversion to text and image extraction for DSPy processing
"""

import os
import io
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import base64

# PDF processing
import PyPDF2
import fitz  # PyMuPDF - much better than pdf2image
import pytesseract

# Image processing
from PIL import Image
import cv2
import numpy as np

class DocumentProcessor:
    """Processes PDF and image documents for data extraction"""
    
    def __init__(self, temp_dir: str = "temp_images"):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(exist_ok=True)
        
    def process_document(self, file_path: str) -> Dict[str, Any]:
        """
        Main processing function for documents
        
        Args:
            file_path: Path to the document (PDF or image)
            
        Returns:
            Dictionary containing text content, images, and metadata
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        if file_path.suffix.lower() == '.pdf':
            return self._process_pdf(file_path)
        elif file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
            return self._process_image(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
    
    def _process_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """Process PDF file - extract text and convert pages to images"""
        result = {
            'type': 'pdf',
            'file_path': str(pdf_path),
            'text_content': '',
            'images': [],
            'metadata': {}
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
                result['metadata']['total_pages'] = len(pdf_reader.pages)
                
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            result['text_content'] = ""
        
        # Convert PDF pages to images using PyMuPDF (much better than pdf2image)
        try:
            # Open PDF with PyMuPDF
            pdf_document = fitz.open(pdf_path)
            image_data = []
            
            for page_num in range(pdf_document.page_count):
                # Get page
                page = pdf_document[page_num]
                
                # Convert page to image with high DPI
                mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to PIL Image
                img_data = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_data))
                
                # Enhance image quality
                image = self._enhance_image(image)
                
                # Save individual page images for debugging
                page_filename = self.temp_dir / f"page_{page_num+1}.png"
                image.save(page_filename, format='PNG')
                
                image_data.append({
                    'page_number': page_num + 1,
                    'image_object': image,  # Store PIL Image object for DSPy
                    'width': image.width,
                    'height': image.height,
                    'file_path': str(page_filename)
                })
            
            # Close the PDF document
            pdf_document.close()
            
            result['images'] = image_data
            result['metadata']['total_pages'] = len(image_data)
            
        except Exception as e:
            print(f"Error converting PDF to images with PyMuPDF: {e}")
            print("Trying fallback method with PyPDF2...")
            
            # Fallback: Try to extract text-only and create a simple image representation
            try:
                result['images'] = self._create_fallback_images(pdf_path)
                result['metadata']['total_pages'] = len(result['images'])
            except Exception as e2:
                print(f"Fallback method also failed: {e2}")
                result['images'] = []
                result['metadata']['total_pages'] = 0
        
        return result
    
    def _process_image(self, image_path: Path) -> Dict[str, Any]:
        """Process image file - extract text using OCR and prepare for vision processing"""
        result = {
            'type': 'image',
            'file_path': str(image_path),
            'text_content': '',
            'images': [],
            'metadata': {}
        }
        
        try:
            # Load image
            image = Image.open(image_path)
            
            # Extract text using OCR
            try:
                ocr_text = pytesseract.image_to_string(image)
                result['text_content'] = ocr_text
            except Exception as e:
                print(f"OCR extraction failed: {e}")
                result['text_content'] = ""
            
            result['images'] = [{
                'page_number': 1,
                'image_object': image,  # Store PIL Image object for DSPy
                'width': image.width,
                'height': image.height
            }]
            
            result['metadata'] = {
                'format': image.format,
                'mode': image.mode,
                'size': image.size
            }
            
        except Exception as e:
            print(f"Error processing image: {e}")
            raise
        
        return result
    
    def _enhance_image(self, image: Image.Image) -> Image.Image:
        """Enhance image quality for better OCR and vision processing"""
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
    
    def _create_fallback_images(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """Create fallback image representations when PyMuPDF fails"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                image_data = []
                
                for page_num in range(len(pdf_reader.pages)):
                    # Create a simple text-based image representation
                    page_text = pdf_reader.pages[page_num].extract_text()
                    
                    # Create a simple image with text
                    img = Image.new('RGB', (800, 1000), color='white')
                    
                    # Save as PNG
                    page_filename = self.temp_dir / f"page_{page_num+1}_fallback.png"
                    img.save(page_filename, format='PNG')
                    
                    image_data.append({
                        'page_number': page_num + 1,
                        'image_object': img,  # Store PIL Image object for DSPy
                        'width': img.width,
                        'height': img.height,
                        'file_path': str(page_filename),
                        'fallback': True,
                        'text_content': page_text[:500]  # First 500 chars for context
                    })
                
                return image_data
                
        except Exception as e:
            print(f"Fallback image creation failed: {e}")
            return []
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        if self.temp_dir.exists():
            for file in self.temp_dir.iterdir():
                file.unlink()
            self.temp_dir.rmdir()
