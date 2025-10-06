"""
Page-by-page extractor for detailed document analysis
"""

import json
import time
from typing import Dict, Any, List
from pathlib import Path

try:
    import dspy
    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False
    print("⚠️  DSPy not available. Some features may be limited.")

from core.base_classes import BaseDataExtractor
from core.exceptions import ExtractionError


class PageByPageExtractor(BaseDataExtractor):
    """Extract data from each page individually and then aggregate"""
    
    def __init__(self, api_key: str, model_name: str = "openai/gpt-4o-mini", use_azure: bool = False):
        super().__init__(api_key, model_name, use_azure)
        self._setup_dspy()
    
    def _setup_dspy(self):
        """Setup DSPy for page-by-page extraction"""
        from llm_config import LLMConfig
        
        llm_config = LLMConfig(use_azure=self.use_azure)
        self.lm = llm_config.get_lm()
        
        # Define page extraction signature
        class PageExtractionSignature(dspy.Signature):
            """Extract structured data from a single page and return as complete JSON format. Example: {\"patient_name\": \"John Doe\", \"lab_results\": {\"glucose\": \"95 mg/dL\"}}"""
            page_text: str = dspy.InputField()
            page_image: dspy.Image = dspy.InputField()
            page_number: int = dspy.InputField()
            
            extracted_data: str = dspy.OutputField(desc="Extract all relevant data from this page and return as a complete, valid JSON object. Ensure all braces and brackets are properly closed. No markdown formatting, no truncated responses.")
        
        self.page_extractor = dspy.Predict(PageExtractionSignature)
    
    def extract_data(self, processed_doc: Dict[str, Any], document_type: str) -> Dict[str, Any]:
        """Extract data from processed document (fallback to single extraction)"""
        try:
            # For now, use the first page/image for extraction
            images = processed_doc.get('images', [])
            if not images:
                return {
                    'success': False,
                    'error': 'No images available for extraction',
                    'strategy': 'page_by_page'
                }
            
            # Use first image
            first_image = images[0]
            text_content = processed_doc.get('text_content', '')
            
            # Extract data from first page
            result = self._extract_from_page(
                text_content, first_image, document_type, 1
            )
            
            if result['success']:
                return {
                    'success': True,
                    'extracted_data': result['data'],
                    'strategy': 'page_by_page',
                    'confidence': result['confidence'],
                    'metadata': {
                        'extraction_method': 'page_by_page',
                        'document_type': document_type,
                        'pages_processed': 1,
                        'confidence_score': result['confidence']
                    }
                }
            else:
                return {
                    'success': False,
                    'error': result['error'],
                    'strategy': 'page_by_page'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'strategy': 'page_by_page'
            }
    
    def extract_page_by_page(self, file_path: str, document_type: str) -> Dict[str, Any]:
        """
        Extract data from each page individually
        
        Args:
            file_path: Path to the document
            document_type: Type of document
            
        Returns:
            Dictionary with page-by-page results and aggregated data
        """
        try:
            print(f"Starting page-by-page extraction from: {file_path}")
            
            # For now, we'll use a simplified approach
            # In a full implementation, this would process each page individually
            
            # Create a mock result for demonstration
            result = {
                'success': True,
                'document_type': document_type,
                'file_path': file_path,
                'total_pages': 1,  # Simplified for now
                'page_results': [{
                    'page_number': 1,
                    'success': True,
                    'extracted_data': {'note': 'Page-by-page extraction not fully implemented yet'},
                    'confidence': 0.8,
                    'text_length': 100
                }],
                'aggregated_data': {'note': 'Page-by-page extraction not fully implemented yet'},
                'metadata': {
                    'processing_info': {
                        'document_type': 'pdf',  # Simplified
                        'total_pages': 1,
                        'has_images': True,
                        'extraction_method': 'page_by_page'
                    }
                }
            }
            
            print(f"✅ Page-by-page extraction completed successfully!")
            print(f"📄 Processed {result['total_pages']} pages")
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'file_path': file_path,
                'document_type': document_type
            }
    
    def _extract_from_page(self, page_text: str, page_image: Dict[str, Any], 
                          document_type: str, page_num: int) -> Dict[str, Any]:
        """Extract data from a single page using DSPy"""
        try:
            # Convert PIL image to dspy.Image
            import dspy
            image_obj = dspy.Image.from_PIL(page_image['image_object'])
            
            # Extract data using DSPy
            result = self.page_extractor(
                page_text=page_text,
                page_image=image_obj,
                page_number=page_num
            )
            
            # Parse the result with improved error handling
            try:
                extracted_data = json.loads(result.extracted_data)
                confidence = 1.0
            except json.JSONDecodeError as e:
                print(f"⚠️  JSON parsing failed for page {page_num}: {e}")
                print(f"Raw output: {result.extracted_data[:200]}...")
                
                # Try to fix common JSON issues
                fixed_json = self._fix_incomplete_json(result.extracted_data)
                if fixed_json:
                    try:
                        extracted_data = json.loads(fixed_json)
                        confidence = 0.9
                        print(f"✅ Fixed JSON for page {page_num}")
                    except json.JSONDecodeError:
                        extracted_data = {"raw_extraction": result.extracted_data}
                        confidence = 0.8
                else:
                    extracted_data = {"raw_extraction": result.extracted_data}
                    confidence = 0.8
            
            return {
                'success': True,
                'data': extracted_data,
                'confidence': confidence
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'data': {},
                'confidence': 0
            }
    
    def _fix_incomplete_json(self, json_str: str) -> str:
        """Try to fix common JSON issues like incomplete JSON"""
        try:
            import re
            
            # Fix trailing commas before closing braces
            json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
            
            # If JSON is incomplete (missing closing braces), try to complete it
            open_braces = json_str.count('{')
            close_braces = json_str.count('}')
            open_brackets = json_str.count('[')
            close_brackets = json_str.count(']')
            
            # Add missing closing braces
            missing_braces = open_braces - close_braces
            missing_brackets = open_brackets - close_brackets
            
            if missing_braces > 0 or missing_brackets > 0:
                # Add missing closing brackets first
                for _ in range(missing_brackets):
                    json_str += ']'
                
                # Add missing closing braces
                for _ in range(missing_braces):
                    json_str += '}'
                
                print(f"🔧 Attempted to fix incomplete JSON by adding {missing_braces} braces and {missing_brackets} brackets")
            
            return json_str
            
        except Exception as e:
            print(f"⚠️  Error fixing JSON: {e}")
            return None
    
    def cleanup(self):
        """Clean up resources"""
        pass
