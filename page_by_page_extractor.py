"""
Page-by-page extraction module for detailed document analysis
"""

import dspy
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

from document_processor import DocumentProcessor
from dspy_extractors import NaturalDocumentExtractor, ChainOfThoughtExtractor, PageExtractor

class PageByPageExtractor:
    """Extract data from each page individually and then aggregate"""
    
    def __init__(self, api_key: str = None, model_name: str = "openai/gpt-4o-mini"):
        """Initialize the page-by-page extractor"""
        import os
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        # Configure DSPy with vision-capable model
        self.lm = dspy.LM(model_name, api_key=self.api_key)
        dspy.configure(lm=self.lm)
        
        # Initialize components
        self.document_processor = DocumentProcessor()
        self.page_extractor = PageExtractor()
    
    def extract_page_by_page(self, file_path: str, document_type: str = "document") -> Dict[str, Any]:
        """
        Extract data from each page individually
        
        Args:
            file_path: Path to the document
            document_type: Type of document
            
        Returns:
            Dictionary with page-by-page results and aggregated data
        """
        try:
            # Process document to get pages
            print(f"Processing document: {file_path}")
            processed_doc = self.document_processor.process_document(file_path)
            
            if not processed_doc.get('images'):
                print("No images found, falling back to text-only extraction")
                return self._fallback_extraction(processed_doc, document_type)
            
            # Extract data from each page
            page_results = []
            total_pages = len(processed_doc['images'])
            
            print(f"Extracting data from {total_pages} pages...")
            
            for i, page_image in enumerate(processed_doc['images']):
                page_num = page_image['page_number']
                print(f"Processing page {page_num}/{total_pages}...")
                
                # Get text for this specific page
                page_text = self._get_page_text(processed_doc, page_num)
                
                # Extract data from this page
                page_data = self._extract_from_page(
                    page_text, page_image, document_type, page_num
                )
                
                page_results.append({
                    'page_number': page_num,
                    'success': page_data['success'],
                    'extracted_data': page_data.get('data', {}),
                    'confidence': page_data.get('confidence', 0),
                    'text_length': len(page_text)
                })
            
            # Aggregate results from all pages
            aggregated_data = self._aggregate_page_results(page_results, document_type)
            
            return {
                'success': True,
                'document_type': document_type,
                'file_path': file_path,
                'total_pages': total_pages,
                'page_results': page_results,
                'aggregated_data': aggregated_data,
                'metadata': {
                    'processing_info': {
                        'document_type': processed_doc.get('type'),
                        'total_pages': total_pages,
                        'has_images': True,
                        'extraction_method': 'page_by_page'
                    }
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'file_path': file_path,
                'document_type': document_type
            }
    
    def _get_page_text(self, processed_doc: Dict[str, Any], page_num: int) -> str:
        """Get text content for a specific page"""
        # For now, we'll use the full text and let the LLM focus on the relevant page
        # In a more sophisticated implementation, we could extract text per page
        full_text = processed_doc.get('text_content', '')
        
        # Add page context
        page_context = f"\n\n--- PAGE {page_num} CONTENT ---\n"
        return page_context + full_text
    
    def _extract_from_page(self, page_text: str, page_image: Dict[str, Any], 
                          document_type: str, page_num: int) -> Dict[str, Any]:
        """Extract data from a single page using natural DSPy extraction with native image support"""
        try:
            # Convert PIL image to dspy.Image
            image_obj = dspy.Image.from_PIL(page_image['image_object'])
            
            # Extract data using DSPy (natural extraction, no structured prompting)
            result = self.page_extractor(
                page_text=page_text,
                page_image=image_obj,
                page_number=page_num
            )
            
            # Parse the result
            try:
                extracted_data = json.loads(result.extracted_data)
                confidence = 1.0  # DSPy handles confidence naturally
            except json.JSONDecodeError as e:
                print(f"⚠️  JSON parsing failed for page {page_num}: {e}")
                print(f"Raw output: {result.extracted_data[:200]}...")
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
    
    
    def _aggregate_page_results(self, page_results: List[Dict[str, Any]], 
                               document_type: str) -> Dict[str, Any]:
        """Aggregate data from all pages into a single structure"""
        aggregated = {}
        
        for page_result in page_results:
            if not page_result['success']:
                continue
            
            page_data = page_result['extracted_data']
            
            # Merge data from each page
            for section, data in page_data.items():
                try:
                    if isinstance(data, dict):
                        if section not in aggregated:
                            aggregated[section] = {}
                        # Deep merge for nested dictionaries
                        self._deep_merge(aggregated[section], data)
                    elif isinstance(data, list):
                        if section not in aggregated:
                            aggregated[section] = []
                        aggregated[section].extend(data)
                    else:
                        # For simple values, keep the most recent non-empty value
                        if data and (section not in aggregated or not aggregated[section]):
                            aggregated[section] = data
                except Exception as e:
                    print(f"⚠️  Error aggregating section '{section}': {e}")
                    print(f"Data type: {type(data)}, Data: {str(data)[:100]}...")
                    continue
        
        # Clean up and deduplicate
        return self._clean_aggregated_data(aggregated, document_type)
    
    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]):
        """Deep merge two dictionaries"""
        for key, value in source.items():
            try:
                if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                    # Recursively merge nested dictionaries
                    self._deep_merge(target[key], value)
                elif key in target and isinstance(target[key], list) and isinstance(value, list):
                    # Merge lists
                    target[key].extend(value)
                elif key in target and isinstance(target[key], list) and isinstance(value, dict):
                    # Convert dict to list item
                    target[key].append(value)
                elif key in target and isinstance(target[key], dict) and isinstance(value, list):
                    # Convert list to dict (keep existing dict)
                    pass  # Keep the existing dict structure
                else:
                    # Overwrite or add new values
                    target[key] = value
            except Exception as e:
                print(f"⚠️  Error in deep merge for key '{key}': {e}")
                print(f"Target type: {type(target.get(key))}, Source type: {type(value)}")
                # Fallback: just overwrite
                target[key] = value
    
    def _clean_aggregated_data(self, data: Dict[str, Any], document_type: str) -> Dict[str, Any]:
        """Clean and deduplicate aggregated data"""
        cleaned = {}
        
        for section, content in data.items():
            if isinstance(content, list):
                # Remove duplicates from lists
                cleaned[section] = self._deduplicate_list(content)
            elif isinstance(content, dict):
                # Clean dictionaries recursively
                cleaned[section] = self._clean_dict(content)
            else:
                cleaned[section] = content
        
        return cleaned
    
    def _clean_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean dictionary recursively"""
        cleaned = {}
        for k, v in data.items():
            if v:  # Only include non-empty values
                if isinstance(v, dict):
                    cleaned[k] = self._clean_dict(v)
                elif isinstance(v, list):
                    cleaned[k] = self._deduplicate_list(v)
                else:
                    cleaned[k] = v
        return cleaned
    
    def _deduplicate_list(self, items: List[Any]) -> List[Any]:
        """Remove duplicates from a list while preserving order"""
        seen = set()
        unique_items = []
        
        for item in items:
            if isinstance(item, dict):
                # For dictionaries, use a string representation for comparison
                item_str = json.dumps(item, sort_keys=True)
                if item_str not in seen:
                    seen.add(item_str)
                    unique_items.append(item)
            else:
                if item not in seen:
                    seen.add(item)
                    unique_items.append(item)
        
        return unique_items
    
    def _fallback_extraction(self, processed_doc: Dict[str, Any], document_type: str) -> Dict[str, Any]:
        """Fallback to text-only extraction if images are not available"""
        print("Using fallback text-only extraction")
        
        # Use the existing text extraction method
        from data_extractor import DataExtractor
        
        extractor = DataExtractor(
            api_key=self.api_key,
            model_name="openai/gpt-4o-mini",
            use_vision=False,
            extraction_method="chain_of_thought"
        )
        
        result = extractor.extract_from_file(
            file_path=processed_doc['file_path'],
            document_type=document_type
        )
        
        return result
    
    def cleanup(self):
        """Clean up temporary files"""
        self.document_processor.cleanup_temp_files()
