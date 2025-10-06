"""
HTML document processor with proper OOP structure
"""

import io
import re
import base64
import time
from typing import Dict, Any, List
from pathlib import Path

from bs4 import BeautifulSoup
from PIL import Image

from core.base_classes import BaseDocumentProcessor, DocumentType, ProcessingResult, DocumentMetadata
from core.exceptions import DocumentProcessingError


class HTMLProcessor(BaseDocumentProcessor):
    """HTML document processor with embedded image extraction"""
    
    def __init__(self, temp_dir: str = "temp_images"):
        super().__init__(temp_dir)
        self.supported_formats = {'html', 'htm'}
    
    def process_document(self, file_path: str) -> Dict[str, Any]:
        """
        Process HTML file - extract text and embedded base64 images
        
        Args:
            file_path: Path to the HTML file
            
        Returns:
            Dictionary containing text content, images, and metadata
        """
        start_time = time.time()
        
        try:
            # Get document metadata
            metadata = self.get_document_metadata(file_path)
            
            # Process HTML
            result = self._process_html(Path(file_path))
            
            # Update metadata with processing results
            metadata.total_pages = len(result.get('images', []))
            metadata.has_images = len(result.get('images', [])) > 0
            metadata.text_length = len(result.get('text_content', ''))
            
            processing_time = time.time() - start_time
            
            return {
                'type': 'html',
                'file_path': str(file_path),
                'text_content': result.get('text_content', ''),
                'images': result.get('images', []),
                'metadata': {
                    'document_metadata': metadata,
                    'processing_time': processing_time,
                    'total_pages': metadata.total_pages,
                    'has_images': metadata.has_images,
                    'text_length': metadata.text_length,
                    'title': result.get('title', ''),
                    'total_images': len(result.get('images', []))
                }
            }
            
        except Exception as e:
            raise DocumentProcessingError(f"Error processing HTML {file_path}: {str(e)}")
    
    def _process_html(self, html_path: Path) -> Dict[str, Any]:
        """Process HTML file - extract text and embedded base64 images"""
        result = {
            'text_content': '',
            'images': [],
            'title': ''
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
            
            # Extract title
            title_tag = soup.find('title')
            result['title'] = title_tag.string if title_tag else ''
            
            # Find and process embedded base64 images
            images = self._extract_base64_images(html_content, html_path)
            result['images'] = images
            
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
                        'image_object': image,
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
                        'image_object': image,
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
    
    def _enhance_image(self, image: Image.Image) -> Image.Image:
        """Enhance image quality for better processing"""
        try:
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # For HTML images, we might want to apply different enhancement
            # depending on the image type and content
            return image
            
        except Exception as e:
            print(f"Image enhancement failed: {e}")
            return image
    
    def extract_links(self, html_path: str) -> List[Dict[str, str]]:
        """Extract all links from HTML file"""
        try:
            with open(html_path, 'r', encoding='utf-8') as file:
                html_content = file.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            links = []
            
            for link in soup.find_all('a', href=True):
                links.append({
                    'text': link.get_text(strip=True),
                    'href': link['href'],
                    'title': link.get('title', '')
                })
            
            return links
            
        except Exception as e:
            print(f"Error extracting links: {e}")
            return []
    
    def extract_metadata(self, html_path: str) -> Dict[str, Any]:
        """Extract metadata from HTML file"""
        try:
            with open(html_path, 'r', encoding='utf-8') as file:
                html_content = file.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            metadata = {
                'title': '',
                'description': '',
                'keywords': '',
                'author': '',
                'viewport': '',
                'charset': ''
            }
            
            # Extract title
            title_tag = soup.find('title')
            if title_tag:
                metadata['title'] = title_tag.string
            
            # Extract meta tags
            for meta in soup.find_all('meta'):
                name = meta.get('name', '').lower()
                content = meta.get('content', '')
                
                if name == 'description':
                    metadata['description'] = content
                elif name == 'keywords':
                    metadata['keywords'] = content
                elif name == 'author':
                    metadata['author'] = content
                elif name == 'viewport':
                    metadata['viewport'] = content
                elif meta.get('charset'):
                    metadata['charset'] = meta.get('charset')
            
            return metadata
            
        except Exception as e:
            print(f"Error extracting metadata: {e}")
            return {}
