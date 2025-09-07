"""
Main Data Extractor class that orchestrates the entire extraction process
"""

import dspy
import json
import os
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from document_processor import DocumentProcessor
from dspy_extractors import NaturalDocumentExtractor, ChainOfThoughtExtractor
from page_by_page_extractor import PageByPageExtractor

class DataExtractor:
    """Main class for extracting structured data from documents using DSPy"""
    
    def __init__(self, 
                 api_key: str = None,
                 model_name: str = "openai/gpt-4o-mini",
                 use_vision: bool = True,
                 extraction_method: str = "auto"):
        """
        Initialize the Data Extractor
        
        Args:
            api_key: OpenAI API key (if not provided, will use environment variable)
            model_name: DSPy model to use
            use_vision: Whether to use vision-capable models
            extraction_method: Method to use ("auto", "simple", "chain_of_thought", "multi_step", "vision_enhanced")
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
        
        # Configure DSPy
        if use_vision and "gpt-4o" in model_name:
            # Use GPT-4o for vision capabilities
            self.lm = dspy.LM(model_name, api_key=self.api_key)
        else:
            self.lm = dspy.LM(model_name, api_key=self.api_key)
        
        dspy.configure(lm=self.lm)
        
        # Initialize components
        self.document_processor = DocumentProcessor()
        self.extraction_method = extraction_method
        self.page_by_page_extractor = PageByPageExtractor(api_key=self.api_key, model_name=model_name)
        
        # Initialize extractors
        self._initialize_extractors()
    
    def _initialize_extractors(self):
        """Initialize different extraction modules"""
        self.extractors = {
            "natural": NaturalDocumentExtractor(),
            "chain_of_thought": ChainOfThoughtExtractor()
        }
    
    def extract_from_file(self, 
                         file_path: str, 
                         document_type: str = "auto",
                         extraction_method: str = None) -> Dict[str, Any]:
        """
        Extract structured data from a document file using natural DSPy extraction
        
        Args:
            file_path: Path to the document file
            document_type: Type of document (for context, not structured prompting)
            extraction_method: Override default extraction method
            
        Returns:
            Dictionary containing extracted data and metadata
        """
        try:
            # Process document
            print(f"Processing document: {file_path}")
            processed_doc = self.document_processor.process_document(file_path)
            
            # Auto-detect document type if needed
            if document_type == "auto":
                document_type = self._detect_document_type(processed_doc)
                print(f"Detected document type: {document_type}")
            
            # Get extraction method
            method = extraction_method or self.extraction_method
            if method == "auto":
                method = self._select_best_method(processed_doc, document_type)
            
            # Extract data
            print(f"Extracting data using method: {method}")
            extracted_data = self._extract_data(
                processed_doc, document_type, method
            )
            
            # Format and validate output
            result = self._format_output(extracted_data, processed_doc, document_type)
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path,
                "document_type": document_type
            }
    
    def _detect_document_type(self, processed_doc: Dict[str, Any]) -> str:
        """Auto-detect document type based on content - generic approach"""
        text_content = processed_doc.get('text_content', '').lower()
        
        # Generic detection - let DSPy figure out the type naturally
        if len(text_content) > 100:
            return "document"  # Generic type
        else:
            return "simple_document"
    
    def _select_best_method(self, processed_doc: Dict[str, Any], document_type: str) -> str:
        """Select the best extraction method based on document characteristics"""
        has_images = len(processed_doc.get('images', [])) > 0
        text_length = len(processed_doc.get('text_content', ''))
        
        if text_length > 1000:
            return "chain_of_thought"
        else:
            return "natural"
    
    def _extract_data(self, processed_doc: Dict[str, Any], document_type: str, 
                     method: str) -> str:
        """Extract data using natural DSPy extraction"""
        
        # Prepare input data
        text_content = processed_doc.get('text_content', '')
        images_data = self._prepare_images_for_dspy(processed_doc.get('images', []))
        
        # Select extractor
        extractor = self.extractors.get(method, self.extractors["natural"])
        
        # Extract data using natural DSPy extraction
        result = extractor(document_text=text_content, document_image=images_data)
        return result.extracted_data
    
    def _prepare_images_for_dspy(self, images: List[Dict[str, Any]]) -> dspy.Image:
        """Prepare image data for DSPy processing using native dspy.Image"""
        if not images:
            # Return a placeholder image if no images available
            from PIL import Image
            placeholder = Image.new('RGB', (100, 100), color='white')
            return dspy.Image.from_PIL(placeholder)
        
        # For now, use the first image (DSPy limitation: single image only)
        # TODO: Handle multiple images by processing page by page
        first_image = images[0]['image_object']
        return dspy.Image.from_PIL(first_image)
    
    def _format_output(self, extracted_data: str, processed_doc: Dict[str, Any], 
                      document_type: str) -> Dict[str, Any]:
        """Format the final output"""
        try:
            # Parse JSON data
            parsed_data = json.loads(extracted_data)
        except json.JSONDecodeError as e:
            print(f"⚠️  JSON parsing failed: {e}")
            print(f"Raw output: {extracted_data[:200]}...")
            # If JSON parsing fails, return raw data
            parsed_data = {"raw_extraction": extracted_data}
        
        return {
            "success": True,
            "document_type": document_type,
            "file_path": processed_doc.get('file_path'),
            "extracted_data": parsed_data,
            "metadata": {
                "processing_info": {
                    "document_type": processed_doc.get('type'),
                    "total_pages": len(processed_doc.get('images', [])),
                    "text_length": len(processed_doc.get('text_content', '')),
                    "has_images": len(processed_doc.get('images', [])) > 0
                },
                "extraction_info": {
                    "method": self.extraction_method,
                    "schema_used": document_type
                }
            }
        }
    
    def batch_extract(self, file_paths: List[str], 
                     document_types: Union[str, List[str]] = "auto") -> List[Dict[str, Any]]:
        """Extract data from multiple files using natural DSPy extraction"""
        results = []
        
        # Handle single vs multiple document types
        if isinstance(document_types, str):
            document_types = [document_types] * len(file_paths)
        
        for i, file_path in enumerate(file_paths):
            doc_type = document_types[i] if i < len(document_types) else "auto"
            result = self.extract_from_file(file_path, doc_type)
            results.append(result)
        
        return results
    
    def extract_page_by_page(self, file_path: str, document_type: str = "auto") -> Dict[str, Any]:
        """
        Extract data from each page individually for detailed analysis
        
        Args:
            file_path: Path to the document file
            document_type: Type of document ("auto", "medical_report", "invoice", etc.)
            
        Returns:
            Dictionary containing page-by-page results and aggregated data
        """
        try:
            print(f"Starting page-by-page extraction from: {file_path}")
            
            # Use the page-by-page extractor
            result = self.page_by_page_extractor.extract_page_by_page(file_path, document_type)
            
            if result["success"]:
                print(f"✅ Page-by-page extraction completed successfully!")
                print(f"📄 Processed {result['total_pages']} pages")
                
                # Show summary of each page
                for page_result in result["page_results"]:
                    page_num = page_result["page_number"]
                    success = "✅" if page_result["success"] else "❌"
                    confidence = page_result.get("confidence", 0)
                    print(f"  Page {page_num}: {success} (confidence: {confidence:.2f})")
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path,
                "document_type": document_type
            }
    
    def extract_with_comparison(self, file_path: str, document_type: str = "auto") -> Dict[str, Any]:
        """
        Extract data using both methods and compare results
        
        Args:
            file_path: Path to the document file
            document_type: Type of document
            
        Returns:
            Dictionary containing both extraction results and comparison
        """
        print(f"Running comparison extraction for: {file_path}")
        
        # Standard extraction
        print("🔄 Running standard extraction...")
        standard_result = self.extract_from_file(file_path, document_type)
        
        # Page-by-page extraction
        print("🔄 Running page-by-page extraction...")
        page_by_page_result = self.extract_page_by_page(file_path, document_type)
        
        # Compare results
        comparison = self._compare_extraction_results(standard_result, page_by_page_result)
        
        return {
            "success": True,
            "file_path": file_path,
            "document_type": document_type,
            "standard_extraction": standard_result,
            "page_by_page_extraction": page_by_page_result,
            "comparison": comparison,
            "metadata": {
                "extraction_methods": ["standard", "page_by_page"],
                "comparison_timestamp": str(Path().cwd())
            }
        }
    
    def _compare_extraction_results(self, standard_result: Dict[str, Any], 
                                  page_by_page_result: Dict[str, Any]) -> Dict[str, Any]:
        """Compare results from different extraction methods"""
        comparison = {
            "standard_success": standard_result.get("success", False),
            "page_by_page_success": page_by_page_result.get("success", False),
            "data_comparison": {},
            "field_coverage": {},
            "recommendations": []
        }
        
        if not standard_result.get("success") or not page_by_page_result.get("success"):
            comparison["recommendations"].append("One or both extraction methods failed")
            return comparison
        
        # Compare extracted data
        standard_data = standard_result.get("extracted_data", {})
        page_by_page_data = page_by_page_result.get("aggregated_data", {})
        
        # Compare field coverage
        standard_fields = self._get_all_fields(standard_data)
        page_by_page_fields = self._get_all_fields(page_by_page_data)
        
        comparison["field_coverage"] = {
            "standard_fields": len(standard_fields),
            "page_by_page_fields": len(page_by_page_fields),
            "common_fields": len(set(standard_fields) & set(page_by_page_fields)),
            "standard_only": list(set(standard_fields) - set(page_by_page_fields)),
            "page_by_page_only": list(set(page_by_page_fields) - set(standard_fields))
        }
        
        # Generate recommendations
        if len(page_by_page_fields) > len(standard_fields):
            comparison["recommendations"].append("Page-by-page extraction found more fields")
        
        if page_by_page_result.get("total_pages", 0) > 1:
            comparison["recommendations"].append("Multi-page document detected - page-by-page extraction recommended")
        
        return comparison
    
    def _get_all_fields(self, data: Dict[str, Any], prefix: str = "") -> List[str]:
        """Recursively get all field names from nested data"""
        fields = []
        
        for key, value in data.items():
            field_name = f"{prefix}.{key}" if prefix else key
            fields.append(field_name)
            
            if isinstance(value, dict):
                fields.extend(self._get_all_fields(value, field_name))
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                # For lists of objects, get fields from first item
                fields.extend(self._get_all_fields(value[0], f"{field_name}[0]"))
        
        return fields
    
    def cleanup(self):
        """Clean up temporary files"""
        self.document_processor.cleanup_temp_files()
