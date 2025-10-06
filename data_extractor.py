"""
Enhanced Data Extractor class that orchestrates the entire extraction process
With improved architecture, dependency injection, and error handling
"""

import dspy
import json
import time
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from abc import ABC, abstractmethod

from document_processor import DocumentProcessor, ProcessingResult
from dspy_extractors import ExtractorFactory, BaseDocumentExtractor
from page_by_page_extractor import PageByPageExtractor
from config_manager import get_config, ConfigManager
from result_manager import ResultManager, ExtractionResult, ResultStatus, ProcessingMetadata


class BaseDataExtractor:
    """Base class for data extractors"""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        Initialize data extractor
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager or get_config()
        self.result_manager = ResultManager()
    
    def extract(self, file_path: str, document_type: str = "auto") -> ExtractionResult:
        """Extract data from document - must be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement extract")
    
    def get_supported_methods(self) -> List[str]:
        """Get list of supported extraction methods - must be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement get_supported_methods")


class DataExtractor(BaseDataExtractor):
    """Main class for extracting structured data from documents using DSPy"""
    
    def __init__(self, 
                 config_manager: Optional[ConfigManager] = None,
                 extraction_method: str = "auto"):
        """
        Initialize the Data Extractor
        
        Args:
            config_manager: Configuration manager instance
            extraction_method: Method to use ("auto", "natural", "chain_of_thought", "vision_enhanced")
        """
        super().__init__(config_manager)
        
        # Initialize LLM configuration
        self._setup_llm()
        
        # Initialize components
        self.document_processor = DocumentProcessor()
        self.extraction_method = extraction_method or self.config.extraction.extraction_method
        
        # Initialize extractors
        self._initialize_extractors()
    
    def get_supported_methods(self) -> List[str]:
        """Get list of supported extraction methods"""
        return ExtractorFactory.get_available_extractors()
    
    def _setup_llm(self):
        """Setup LLM configuration"""
        from llm_config import LLMConfig
        
        self.llm_config = LLMConfig(use_azure=self.config.llm.use_azure)
        self.lm = self.llm_config.get_lm()
        self.api_key = self.llm_config.get_api_key()
        self.use_azure = self.config.llm.use_azure
    
    def _initialize_extractors(self):
        """Initialize different extraction modules"""
        self.extractors = {}
        
        # Initialize extractors using factory
        for method in self.get_supported_methods():
            try:
                self.extractors[method] = ExtractorFactory.create_extractor(method)
            except Exception as e:
                print(f"⚠️  Warning: Could not initialize {method} extractor: {e}")
    
    def extract(self, file_path: str, document_type: str = "auto") -> ExtractionResult:
        """
        Extract structured data from a document file
        
        Args:
            file_path: Path to the document file
            document_type: Type of document (for context)
            
        Returns:
            ExtractionResult object
        """
        start_time = time.time()
        
        try:
            # Process document
            print(f"Processing document: {file_path}")
            processing_result = self.document_processor.process(file_path)
            
            if not processing_result.success:
                return self.result_manager.create_extraction_result(
                    file_path=file_path,
                    status=ResultStatus.FAILED,
                    metadata=ProcessingMetadata(
                        processing_time_seconds=time.time() - start_time,
                        file_size_bytes=0,
                        error_message=processing_result.error_message
                    ),
                    error_details={"processing_error": processing_result.error_message}
                )
            
            # Auto-detect document type if needed
            if document_type == "auto":
                document_type = self._detect_document_type(processing_result)
                print(f"Detected document type: {document_type}")
            
            # Get extraction method
            method = self._select_best_method(processing_result, document_type)
            
            # Extract data
            print(f"Extracting data using method: {method}")
            extracted_data = self._extract_data(
                processing_result, document_type, method
            )
            
            processing_time = time.time() - start_time
            
            return self.result_manager.create_extraction_result(
                file_path=file_path,
                status=ResultStatus.SUCCESS,
                extracted_data=extracted_data,
                metadata=ProcessingMetadata(
                    processing_time_seconds=processing_time,
                    file_size_bytes=processing_result.metadata.file_size_bytes,
                    page_count=processing_result.metadata.page_count,
                    document_type=document_type,
                    extraction_method=method,
                    confidence_score=0.9  # Default confidence
                )
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return self.result_manager.create_extraction_result(
                file_path=file_path,
                status=ResultStatus.FAILED,
                metadata=ProcessingMetadata(
                    processing_time_seconds=processing_time,
                    file_size_bytes=0,
                    error_message=str(e)
                ),
                error_details={"extraction_error": str(e)}
            )
    
    def extract_from_file(self, 
                         file_path: str, 
                         document_type: str = "auto",
                         extraction_method: str = None) -> Dict[str, Any]:
        """
        Extract structured data from a document file (backward compatibility)
        
        Args:
            file_path: Path to the document file
            document_type: Type of document (for context)
            extraction_method: Override default extraction method
            
        Returns:
            Dictionary containing extracted data and metadata
        """
        # Use the new extraction method
        result = self.extract(file_path, document_type)
        
        # Convert ExtractionResult to legacy format for backward compatibility
        if result.status == ResultStatus.SUCCESS:
            return {
                "success": True,
                "document_type": result.metadata.document_type,
                "file_path": result.file_path,
                "extracted_data": result.extracted_data,
                "metadata": {
                    "processing_info": {
                        "document_type": result.metadata.document_type,
                        "total_pages": result.metadata.page_count,
                        "text_length": len(str(result.extracted_data)),
                        "has_images": result.metadata.page_count > 0,
                        "file_size_bytes": result.metadata.file_size_bytes
                    },
                    "extraction_info": {
                        "method": result.metadata.extraction_method,
                        "confidence_score": result.metadata.confidence_score,
                        "processing_time_seconds": result.metadata.processing_time_seconds,
                        "timestamp": result.metadata.timestamp
                    }
                }
            }
        else:
            return {
                "success": False,
                "error": result.error_details.get("extraction_error", "Unknown error") if result.error_details else "Unknown error",
                "file_path": result.file_path,
                "document_type": result.metadata.document_type
            }
    
    def _detect_document_type(self, processing_result: ProcessingResult) -> str:
        """Auto-detect document type based on content - generic approach"""
        text_content = processing_result.text_content.lower()
        
        # Generic detection - let DSPy figure out the type naturally
        if len(text_content) > 100:
            return "document"  # Generic type
        else:
            return "simple_document"
    
    def _select_best_method(self, processing_result: ProcessingResult, document_type: str) -> str:
        """Select the best extraction method based on document characteristics"""
        has_images = len(processing_result.images) > 0
        text_length = len(processing_result.text_content)
        
        if text_length > 1000:
            return "chain_of_thought"
        elif has_images and processing_result.document_type in ["pdf", "html"]:
            return "vision_enhanced"
        else:
            return "natural"
    
    def _extract_data(self, processing_result: ProcessingResult, document_type: str, 
                     method: str) -> Dict[str, Any]:
        """Extract data using DSPy extraction"""
        
        # Prepare input data
        text_content = processing_result.text_content
        images_data = self._prepare_images_for_dspy(processing_result.images)
        
        # Select extractor
        extractor = self.extractors.get(method, self.extractors.get("natural"))
        
        if not extractor:
            raise ValueError(f"Extractor not found for method: {method}")
        
        # Extract data using DSPy extraction
        result = extractor(document_text=text_content, document_image=images_data)
        
        # Parse JSON data
        try:
            extracted_data = json.loads(result.extracted_data)
        except json.JSONDecodeError as e:
            print(f"⚠️  JSON parsing failed: {e}")
            print(f"Raw output: {result.extracted_data[:200]}...")
            # If JSON parsing fails, return raw data
            extracted_data = {"raw_extraction": result.extracted_data}
        
        return extracted_data
    
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
