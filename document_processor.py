"""
Enhanced Document Processor for PDF, Image, and HTML files
Handles conversion to text and image extraction for DSPy processing with improved error handling and validation
"""

import os
import io
import re
import base64
import time
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from abc import ABC, abstractmethod
from dataclasses import dataclass

# PDF processing
import PyPDF2
import fitz  # PyMuPDF - much better than pdf2image
import pytesseract

# Image processing
from PIL import Image
import cv2
import numpy as np

# HTML processing
from bs4 import BeautifulSoup

from config_manager import get_config
from result_manager import ProcessingMetadata


@dataclass
class ProcessingResult:
    """Result of document processing operation"""
    success: bool
    document_type: str
    file_path: str
    text_content: str
    images: List[Dict[str, Any]]
    metadata: ProcessingMetadata
    error_message: Optional[str] = None


class BaseDocumentProcessor:
    """Base class for document processors"""
    
    def __init__(self, temp_dir: Optional[str] = None):
        """
        Initialize document processor
        
        Args:
            temp_dir: Directory for temporary files
        """
        self.config = get_config()
        self.temp_dir = Path(temp_dir) if temp_dir else Path(self.config.processing.temp_dir)
        self.temp_dir.mkdir(exist_ok=True)
    
    def process(self, file_path: Union[str, Path]) -> ProcessingResult:
        """Process a document file - must be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement process")
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats - must be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement get_supported_formats")
    
    def validate_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Validate file before processing
        
        Args:
            file_path: Path to the file
            
        Returns:
            Validation result dictionary
        """
        file_path = Path(file_path)
        validation = {"valid": True, "errors": [], "warnings": []}
        
        # Check if file exists
        if not file_path.exists():
            validation["valid"] = False
            validation["errors"].append(f"File not found: {file_path}")
            return validation
        
        # Check file size
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.config.processing.max_file_size_mb:
            validation["valid"] = False
            validation["errors"].append(f"File too large: {file_size_mb:.1f}MB > {self.config.processing.max_file_size_mb}MB")
        
        # Check file format
        if file_path.suffix.lower() not in self.get_supported_formats():
            validation["valid"] = False
            validation["errors"].append(f"Unsupported file format: {file_path.suffix}")
        
        # Warnings
        if file_size_mb > self.config.processing.max_file_size_mb * 0.8:
            validation["warnings"].append("File is close to size limit")
        
        return validation
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        if self.temp_dir.exists():
            try:
                for file in self.temp_dir.iterdir():
                    if file.is_file():
                        file.unlink()
                print(f"🧹 Cleaned up temporary files in {self.temp_dir}")
            except Exception as e:
                print(f"⚠️  Warning: Could not clean up temporary files: {e}")


class DocumentProcessor(BaseDocumentProcessor):
    """Processes PDF, image, and HTML documents for data extraction"""
    
    def __init__(self, temp_dir: Optional[str] = None):
        """Initialize document processor"""
        super().__init__(temp_dir)
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats"""
        return self.config.processing.supported_formats
    
    def process(self, file_path: Union[str, Path]) -> ProcessingResult:
        """
        Process a document file with enhanced error handling
        
        Args:
            file_path: Path to the document file
            
        Returns:
            ProcessingResult object
        """
        file_path = Path(file_path)
        start_time = time.time()
        
        # Validate file first
        validation = self.validate_file(file_path)
        if not validation["valid"]:
            return ProcessingResult(
                success=False,
                document_type="unknown",
                file_path=str(file_path),
                text_content="",
                images=[],
                metadata=ProcessingMetadata(
                    processing_time_seconds=time.time() - start_time,
                    file_size_bytes=0,
                    error_message="; ".join(validation["errors"])
                ),
                error_message="; ".join(validation["errors"])
            )
        
        # Process based on file type
        try:
            if file_path.suffix.lower() == '.pdf':
                return self._process_pdf_enhanced(file_path, start_time)
            elif file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
                return self._process_image_enhanced(file_path, start_time)
            elif file_path.suffix.lower() in ['.html', '.htm']:
                return self._process_html_enhanced(file_path, start_time)
            else:
                raise ValueError(f"Unsupported file format: {file_path.suffix}")
                
        except Exception as e:
            processing_time = time.time() - start_time
            return ProcessingResult(
                success=False,
                document_type="unknown",
                file_path=str(file_path),
                text_content="",
                images=[],
                metadata=ProcessingMetadata(
                    processing_time_seconds=processing_time,
                    file_size_bytes=file_path.stat().st_size,
                    error_message=str(e)
                ),
                error_message=str(e)
            )
    
    def process_document(self, file_path: str) -> Dict[str, Any]:
        """
        Main processing function for documents (backward compatibility)
        
        Args:
            file_path: Path to the document (PDF, image, or HTML)
            
        Returns:
            Dictionary containing text content, images, and metadata
        """
        result = self.process(file_path)
        
        # Convert ProcessingResult to legacy format for backward compatibility
        return {
            'type': result.document_type,
            'file_path': result.file_path,
            'text_content': result.text_content,
            'images': result.images,
            'metadata': {
                'processing_info': {
                    'document_type': result.document_type,
                    'total_pages': result.metadata.page_count,
                    'text_length': len(result.text_content),
                    'has_images': len(result.images) > 0,
                    'file_size_bytes': result.metadata.file_size_bytes,
                    'processing_time_seconds': result.metadata.processing_time_seconds
                },
                'success': result.success,
                'error_message': result.error_message
            }
        }
    
    def _process_pdf_enhanced(self, pdf_path: Path, start_time: float) -> ProcessingResult:
        """Enhanced PDF processing with better error handling"""
        file_size = pdf_path.stat().st_size
        
        try:
            # Extract text from PDF
            text_content = ""
            page_count = 0
            
            try:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text_content_list = []
                    
                    for page_num, page in enumerate(pdf_reader.pages):
                        page_text = page.extract_text()
                        text_content_list.append(f"--- Page {page_num + 1} ---\n{page_text}")
                    
                    text_content = '\n\n'.join(text_content_list)
                    page_count = len(pdf_reader.pages)
                    
            except Exception as e:
                print(f"⚠️  Text extraction failed: {e}")
                text_content = ""
            
            # Convert PDF pages to images
            images = []
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
                    
                    # Enhance image quality if enabled
                    if self.config.processing.enable_image_enhancement:
                        image = self._enhance_image(image)
                    
                    # Save individual page images
                    page_filename = self.temp_dir / f"page_{page_num+1}.png"
                    image.save(page_filename, format='PNG')
                    
                    image_data.append({
                        'page_number': page_num + 1,
                        'image_object': image,
                        'width': image.width,
                        'height': image.height,
                        'file_path': str(page_filename)
                    })
                
                pdf_document.close()
                images = image_data
                
            except Exception as e:
                print(f"⚠️  Image conversion failed: {e}")
                images = []
            
            processing_time = time.time() - start_time
            
            return ProcessingResult(
                success=True,
                document_type="pdf",
                file_path=str(pdf_path),
                text_content=text_content,
                images=images,
                metadata=ProcessingMetadata(
                    processing_time_seconds=processing_time,
                    file_size_bytes=file_size,
                    page_count=len(images),
                    document_type="pdf"
                )
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return ProcessingResult(
                success=False,
                document_type="pdf",
                file_path=str(pdf_path),
                text_content="",
                images=[],
                metadata=ProcessingMetadata(
                    processing_time_seconds=processing_time,
                    file_size_bytes=file_size,
                    error_message=str(e)
                ),
                error_message=str(e)
            )
    
    def _process_image_enhanced(self, image_path: Path, start_time: float) -> ProcessingResult:
        """Enhanced image processing with better error handling"""
        file_size = image_path.stat().st_size
        
        try:
            # Load image
            image = Image.open(image_path)
            
            # Extract text using OCR if enabled
            text_content = ""
            if self.config.processing.ocr_enabled:
                try:
                    text_content = pytesseract.image_to_string(image)
                except Exception as e:
                    print(f"⚠️  OCR extraction failed: {e}")
                    text_content = ""
            
            images = [{
                'page_number': 1,
                'image_object': image,
                'width': image.width,
                'height': image.height,
                'file_path': str(image_path)
            }]
            
            processing_time = time.time() - start_time
            
            return ProcessingResult(
                success=True,
                document_type="image",
                file_path=str(image_path),
                text_content=text_content,
                images=images,
                metadata=ProcessingMetadata(
                    processing_time_seconds=processing_time,
                    file_size_bytes=file_size,
                    page_count=1,
                    document_type="image"
                )
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return ProcessingResult(
                success=False,
                document_type="image",
                file_path=str(image_path),
                text_content="",
                images=[],
                metadata=ProcessingMetadata(
                    processing_time_seconds=processing_time,
                    file_size_bytes=file_size,
                    error_message=str(e)
                ),
                error_message=str(e)
            )
    
    def _process_html_enhanced(self, html_path: Path, start_time: float) -> ProcessingResult:
        """Enhanced HTML processing with better error handling"""
        file_size = html_path.stat().st_size
        
        try:
            # Read HTML file
            with open(html_path, 'r', encoding='utf-8') as file:
                html_content = file.read()
            
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract text content
            text_content = soup.get_text(separator='\n', strip=True)
            
            # Find and process embedded base64 images
            images = self._extract_base64_images(html_content, html_path)
            
            processing_time = time.time() - start_time
            
            return ProcessingResult(
                success=True,
                document_type="html",
                file_path=str(html_path),
                text_content=text_content,
                images=images,
                metadata=ProcessingMetadata(
                    processing_time_seconds=processing_time,
                    file_size_bytes=file_size,
                    page_count=len(images),
                    document_type="html"
                )
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return ProcessingResult(
                success=False,
                document_type="html",
                file_path=str(html_path),
                text_content="",
                images=[],
                metadata=ProcessingMetadata(
                    processing_time_seconds=processing_time,
                    file_size_bytes=file_size,
                    error_message=str(e)
                ),
                error_message=str(e)
            )
    
    def _process_html(self, html_path: Path) -> Dict[str, Any]:
        """Process HTML file - extract text and embedded base64 images"""
        result = {
            'type': 'html',
            'file_path': str(html_path),
            'text_content': '',
            'images': [],
            'metadata': {}
        }
        
        try:
            # Read HTML file
            with open(html_path, 'r', encoding='utf-8') as file:
                html_content = file.read()
            
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract text content
            text_content = soup.get_text(separator='\n', strip=True)
            result['text_content'] = text_content
            
            # Find and process embedded base64 images
            images = self._extract_base64_images(html_content, html_path)
            result['images'] = images
            
            # Extract metadata
            result['metadata'] = {
                'title': soup.title.string if soup.title else '',
                'total_images': len(images),
                'text_length': len(text_content),
                'has_images': len(images) > 0
            }
            
        except Exception as e:
            print(f"Error processing HTML file: {e}")
            raise
        
        return result
    
    def _extract_base64_images(self, html_content: str, html_path: Path) -> List[Dict[str, Any]]:
        """Extract base64 embedded images from HTML content"""
        images = []
        
        try:
            # Find all img tags with base64 data
            img_pattern = r'<img[^>]+src=["\']data:image/([^;]+);base64,([^"\']+)["\'][^>]*>'
            matches = re.findall(img_pattern, html_content, re.IGNORECASE)
            
            for i, (img_format, base64_data) in enumerate(matches):
                try:
                    # Decode base64 image
                    img_data = base64.b64decode(base64_data)
                    
                    # Convert to PIL Image
                    image = Image.open(io.BytesIO(img_data))
                    
                    # Enhance image quality
                    image = self._enhance_image(image)
                    
                    # Save individual image for debugging
                    img_filename = self.temp_dir / f"{html_path.stem}_img_{i+1}.{img_format}"
                    image.save(img_filename, format=img_format.upper())
                    
                    images.append({
                        'page_number': i + 1,
                        'image_object': image,  # Store PIL Image object for DSPy
                        'width': image.width,
                        'height': image.height,
                        'format': img_format,
                        'file_path': str(img_filename),
                        'source': 'base64_embedded'
                    })
                    
                except Exception as e:
                    print(f"Error processing base64 image {i+1}: {e}")
                    continue
            
            # Also look for base64 images in CSS background-image
            css_pattern = r'background-image:\s*url\(["\']?data:image/([^;]+);base64,([^"\'\)]+)["\']?\)'
            css_matches = re.findall(css_pattern, html_content, re.IGNORECASE)
            
            for i, (img_format, base64_data) in enumerate(css_matches):
                try:
                    # Decode base64 image
                    img_data = base64.b64decode(base64_data)
                    
                    # Convert to PIL Image
                    image = Image.open(io.BytesIO(img_data))
                    
                    # Enhance image quality
                    image = self._enhance_image(image)
                    
                    # Save individual image for debugging
                    img_filename = self.temp_dir / f"{html_path.stem}_css_img_{i+1}.{img_format}"
                    image.save(img_filename, format=img_format.upper())
                    
                    images.append({
                        'page_number': len(images) + 1,
                        'image_object': image,  # Store PIL Image object for DSPy
                        'width': image.width,
                        'height': image.height,
                        'format': img_format,
                        'file_path': str(img_filename),
                        'source': 'css_background'
                    })
                    
                except Exception as e:
                    print(f"Error processing CSS base64 image {i+1}: {e}")
                    continue
            
        except Exception as e:
            print(f"Error extracting base64 images: {e}")
        
        return images
    
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