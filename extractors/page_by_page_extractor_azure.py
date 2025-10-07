"""
Page-by-page extractor for Azure-only pipeline
Uses already-processed document images (no re-processing)
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


class PageByPageExtractorAzure(BaseDataExtractor):
    """
    Extract data from each page individually

    Designed for Azure-only pipeline:
    - Does NOT re-process documents (no OpenCV calls)
    - Uses already-processed images from Azure pipeline
    """

    def __init__(self, api_key: str, model_name: str = "openai/gpt-4o-mini", use_azure: bool = False):
        super().__init__(api_key, model_name, use_azure)
        self._setup_dspy()

    def _setup_dspy(self):
        """Setup DSPy for page-by-page extraction"""
        if not DSPY_AVAILABLE:
            self.page_extractor = None
            return

        from llm_config import LLMConfig

        llm_config = LLMConfig(use_azure=self.use_azure)
        self.lm = llm_config.get_lm()

        # Define page extraction signature
        class PageExtractionSignature(dspy.Signature):
            """Extract structured data from a single page and return as complete JSON format."""
            page_text: str = dspy.InputField()
            page_image: dspy.Image = dspy.InputField()
            page_number: int = dspy.InputField()

            extracted_data: str = dspy.OutputField(
                desc="Extract all relevant data from this page and return as a complete, valid JSON object."
            )

        self.page_extractor = dspy.Predict(PageExtractionSignature)

    def extract_data(self, processed_doc: Dict[str, Any], document_type: str) -> Dict[str, Any]:
        """Extract data from processed document (fallback to single extraction)"""
        try:
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

    def extract_page_by_page_from_processed(self, processed_doc: Dict[str, Any],
                                           file_path: str, document_type: str) -> Dict[str, Any]:
        """
        Extract data from each page using already-processed images

        KEY: This does NOT re-process the document
        It uses the images that were already processed by Azure-only pipeline

        Args:
            processed_doc: Already processed document with Azure-corrected images
            file_path: Original file path (for metadata)
            document_type: Type of document

        Returns:
            Dictionary with page-by-page results
        """
        try:
            print(f"📄 Page-by-page extraction from pre-processed images...")

            if not DSPY_AVAILABLE or self.page_extractor is None:
                return {
                    'success': True,
                    'document_type': document_type,
                    'file_path': file_path,
                    'total_pages': 1,
                    'page_results': [{
                        'page_number': 1,
                        'success': True,
                        'extracted_data': {
                            'note': 'DSPy not available - page-by-page extraction limited'
                        },
                        'confidence': 0.8
                    }],
                    'aggregated_data': {},
                    'metadata': {
                        'processing_info': {
                            'document_type': document_type,
                            'total_pages': 1,
                            'extraction_method': 'page_by_page',
                            'dspy_available': False
                        }
                    }
                }

            # Get already-processed images from Azure pipeline
            images = processed_doc.get('images', [])
            text_content = processed_doc.get('text_content', '')

            if not images:
                return {
                    'success': False,
                    'error': 'No images available for page-by-page extraction',
                    'file_path': file_path,
                    'document_type': document_type
                }

            # Process each page (using pre-processed images)
            page_results = []
            aggregated_data = {}

            for i, image_info in enumerate(images):
                page_num = i + 1
                print(f"   Processing page {page_num}/{len(images)}...")

                # Extract data from this page using ALREADY CORRECTED image
                page_result = self._extract_from_page(
                    text_content, image_info, document_type, page_num
                )

                if page_result['success']:
                    page_results.append({
                        'page_number': page_num,
                        'success': True,
                        'extracted_data': page_result['data'],
                        'confidence': page_result['confidence']
                    })

                    # Aggregate data
                    if isinstance(page_result['data'], dict):
                        aggregated_data.update(page_result['data'])
                else:
                    page_results.append({
                        'page_number': page_num,
                        'success': False,
                        'error': page_result['error'],
                        'confidence': 0
                    })

            result = {
                'success': True,
                'document_type': document_type,
                'file_path': file_path,
                'total_pages': len(images),
                'page_results': page_results,
                'aggregated_data': aggregated_data,
                'metadata': {
                    'processing_info': {
                        'document_type': document_type,
                        'total_pages': len(images),
                        'extraction_method': 'page_by_page_azure',
                        'dspy_available': True,
                        'successful_pages': len([p for p in page_results if p['success']]),
                        'failed_pages': len([p for p in page_results if not p['success']]),
                        'used_pre_processed_images': True
                    }
                }
            }

            print(f"   ✅ Completed {len(images)} pages")
            return result

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'file_path': file_path,
                'document_type': document_type
            }

    def extract_page_by_page(self, file_path: str, document_type: str) -> Dict[str, Any]:
        """
        Legacy method - should not be used in Azure-only pipeline
        Raises error to prevent re-processing
        """
        raise NotImplementedError(
            "This method re-processes documents with old processors. "
            "Use extract_page_by_page_from_processed() instead with already-processed images."
        )

    def _extract_from_page(self, page_text: str, page_image_info: Dict[str, Any],
                          document_type: str, page_num: int) -> Dict[str, Any]:
        """Extract data from a single page using DSPy"""
        try:
            # Use the ALREADY PROCESSED image object
            import dspy
            image_obj = dspy.Image.from_PIL(page_image_info['image_object'])

            print(f"      🤖 Extracting from corrected image...")

            # Extract data using DSPy
            result = self.page_extractor(
                page_text=page_text,
                page_image=image_obj,
                page_number=page_num
            )

            # Parse the result
            try:
                extracted_data = json.loads(result.extracted_data)
                confidence = 1.0
            except json.JSONDecodeError as e:
                print(f"      ⚠️  JSON parsing failed: {e}")
                fixed_json = self._fix_incomplete_json(result.extracted_data)
                if fixed_json:
                    try:
                        extracted_data = json.loads(fixed_json)
                        confidence = 0.9
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
        """Try to fix common JSON issues"""
        try:
            import re

            # Fix trailing commas
            json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)

            # Count braces
            open_braces = json_str.count('{')
            close_braces = json_str.count('}')
            open_brackets = json_str.count('[')
            close_brackets = json_str.count(']')

            # Add missing closing
            missing_braces = open_braces - close_braces
            missing_brackets = open_brackets - close_brackets

            if missing_braces > 0 or missing_brackets > 0:
                for _ in range(missing_brackets):
                    json_str += ']'
                for _ in range(missing_braces):
                    json_str += '}'

            return json_str

        except Exception as e:
            return None

    def cleanup(self):
        """Clean up resources"""
        pass
