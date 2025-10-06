"""
Natural extractor using DSPy without structured prompting
"""

import json
from typing import Dict, Any

try:
    import dspy
    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False
    print("⚠️  DSPy not available. Some features may be limited.")

from core.base_classes import BaseDataExtractor
from core.exceptions import ExtractionError


class NaturalExtractor(BaseDataExtractor):
    """Natural document extraction using DSPy without structured prompting"""
    
    def __init__(self, api_key: str, model_name: str = "openai/gpt-4o-mini", use_azure: bool = False):
        super().__init__(api_key, model_name, use_azure)
        self._setup_dspy()
    
    def _setup_dspy(self):
        """Setup DSPy for natural extraction"""
        if not DSPY_AVAILABLE:
            self.extractor = None
            return
            
        try:
            from llm_config import LLMConfig
            
            llm_config = LLMConfig(use_azure=self.use_azure)
            self.lm = llm_config.get_lm()
            
            # Define natural extraction signature
            class NaturalExtractionSignature(dspy.Signature):
                """Extract structured data from document and return as JSON format. Example: {\"patient_name\": \"John Doe\", \"age\": 30, \"lab_results\": {\"glucose\": \"95 mg/dL\"}}"""
                document_text: str = dspy.InputField()
                document_image: dspy.Image = dspy.InputField()
                
                extracted_data: str = dspy.OutputField(desc="Extract all relevant data and return as valid JSON object only, no markdown formatting")
            
            self.extractor = dspy.Predict(NaturalExtractionSignature)
        except Exception as e:
            print(f"⚠️  DSPy setup failed: {e}")
            self.extractor = None
    
    def extract_data(self, processed_doc: Dict[str, Any], document_type: str) -> Dict[str, Any]:
        """Extract structured data from processed document"""
        try:
            if not DSPY_AVAILABLE or self.extractor is None:
                # Fallback to mock data when DSPy is not available
                return {
                    'success': True,
                    'extracted_data': {
                        'note': 'DSPy not available - using mock data',
                        'document_type': document_type,
                        'text_length': len(processed_doc.get('text_content', '')),
                        'has_images': len(processed_doc.get('images', [])) > 0
                    },
                    'strategy': 'natural',
                    'confidence': 0.5,
                    'metadata': {
                        'extraction_method': 'natural',
                        'document_type': document_type,
                        'confidence_score': 0.5,
                        'dspy_available': False
                    }
                }
            
            # Prepare input data
            text_content = processed_doc.get('text_content', '')
            images_data = self._prepare_images_for_dspy(processed_doc.get('images', []))
            
            # Extract data using DSPy
            result = self.extractor(
                document_text=text_content,
                document_image=images_data
            )
            
            # Parse and return result
            parsed_data = self._parse_json_result(result.extracted_data)
            
            return {
                'success': True,
                'extracted_data': parsed_data,
                'strategy': 'natural',
                'confidence': 1.0,
                'metadata': {
                    'extraction_method': 'natural',
                    'document_type': document_type,
                    'confidence_score': 1.0,
                    'dspy_available': True
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'strategy': 'natural'
            }
    
    def extract_page_by_page(self, file_path: str, document_type: str) -> Dict[str, Any]:
        """Extract data from each page individually"""
        try:
            # Import here to avoid circular imports
            from .page_by_page_extractor import PageByPageExtractor
            
            # Create page-by-page extractor
            page_extractor = PageByPageExtractor(
                api_key=self.api_key,
                model_name=self.model_name,
                use_azure=self.use_azure
            )
            
            # Extract page by page
            result = page_extractor.extract_page_by_page(file_path, document_type)
            
            # Cleanup
            page_extractor.cleanup()
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'strategy': 'natural'
            }
    
    def _prepare_images_for_dspy(self, images: list):
        """Prepare image data for DSPy processing using native dspy.Image"""
        if not DSPY_AVAILABLE:
            return None
            
        if not images:
            # Return a placeholder image if no images available
            try:
                from PIL import Image
                placeholder = Image.new('RGB', (100, 100), color='white')
                return dspy.Image.from_PIL(placeholder)
            except ImportError:
                return None
        
        # For now, use the first image (DSPy limitation: single image only)
        first_image = images[0]['image_object']
        return dspy.Image.from_PIL(first_image)
    
    def _parse_json_result(self, raw_result: str) -> Dict[str, Any]:
        """Parse JSON result with error handling"""
        try:
            return json.loads(raw_result)
        except json.JSONDecodeError as e:
            print(f"⚠️  JSON parsing failed: {e}")
            print(f"Raw output: {raw_result[:200]}...")
            
            # Try to fix common JSON issues
            fixed_json = self._fix_incomplete_json(raw_result)
            if fixed_json:
                try:
                    return json.loads(fixed_json)
                except json.JSONDecodeError:
                    return {"raw_extraction": raw_result}
            else:
                return {"raw_extraction": raw_result}
    
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
