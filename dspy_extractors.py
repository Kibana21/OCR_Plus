"""
DSPy-based extraction modules for structured data extraction from documents
Enhanced with better inheritance, configuration, and error handling
"""

import dspy
import json
import time
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod
from config_manager import get_config
from result_manager import ResultStatus, ProcessingMetadata


class BaseDocumentExtractor(dspy.Module):
    """Abstract base class for document data extraction using DSPy"""
    
    def __init__(self, signature_class, max_retries: int = 3, timeout_seconds: int = 300):
        super().__init__()
        self.signature_class = signature_class
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.config = get_config()
        
        # Initialize the DSPy predictor
        self._initialize_predictor()
    
    def _initialize_predictor(self):
        """Initialize the DSPy predictor - must be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement _initialize_predictor")
    
    def forward(self, **kwargs) -> dspy.Prediction:
        """
        Forward pass with retry logic and error handling
        
        Args:
            **kwargs: Input arguments for the extraction
            
        Returns:
            DSPy prediction result
        """
        start_time = time.time()
        
        for attempt in range(self.max_retries):
            try:
                result = self._execute_extraction(**kwargs)
                
                # Validate result
                if self._validate_result(result):
                    return result
                else:
                    if attempt < self.max_retries - 1:
                        print(f"⚠️  Validation failed, retrying... (attempt {attempt + 2}/{self.max_retries})")
                        continue
                    else:
                        print(f"❌ All validation attempts failed")
                        return result
                        
            except Exception as e:
                if attempt < self.max_retries - 1:
                    print(f"⚠️  Extraction failed, retrying... (attempt {attempt + 2}/{self.max_retries}): {str(e)}")
                    continue
                else:
                    print(f"❌ All extraction attempts failed: {str(e)}")
                    raise
        
        # Timeout check
        if time.time() - start_time > self.timeout_seconds:
            raise TimeoutError(f"Extraction timed out after {self.timeout_seconds} seconds")
    
    def _execute_extraction(self, **kwargs) -> dspy.Prediction:
        """Execute the actual extraction - must be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement _execute_extraction")
    
    def _validate_result(self, result: dspy.Prediction) -> bool:
        """
        Validate extraction result
        
        Args:
            result: DSPy prediction result
            
        Returns:
            True if result is valid, False otherwise
        """
        if not result or not hasattr(result, 'extracted_data'):
            return False
        
        extracted_data = result.extracted_data
        if not extracted_data or not isinstance(extracted_data, str):
            return False
        
        # Try to parse as JSON to validate structure
        try:
            json.loads(extracted_data)
            return True
        except json.JSONDecodeError:
            return False
    
    def get_extraction_metadata(self) -> ProcessingMetadata:
        """Get metadata for this extractor"""
        return ProcessingMetadata(
            extraction_method=self.__class__.__name__.lower().replace('extractor', ''),
            document_type="unknown"
        )


class DocumentExtractionSignature(dspy.Signature):
    """Extract structured data from document and return as JSON format. Example: {\"patient_name\": \"John Doe\", \"age\": 30, \"lab_results\": {\"glucose\": \"95 mg/dL\"}}"""
    document_text: str = dspy.InputField(desc="Text content extracted from the document")
    document_image: dspy.Image = dspy.InputField(desc="Image representation of the document")
    
    extracted_data: str = dspy.OutputField(desc="Extract all relevant data and return as valid JSON object only, no markdown formatting. Ensure proper JSON structure with closed braces and brackets.")


class PageExtractionSignature(dspy.Signature):
    """Extract structured data from a single page and return as complete JSON format. Example: {\"patient_name\": \"John Doe\", \"lab_results\": {\"glucose\": \"95 mg/dL\"}}"""
    page_text: str = dspy.InputField(desc="Text content from the specific page")
    page_image: dspy.Image = dspy.InputField(desc="Image representation of the specific page")
    page_number: int = dspy.InputField(desc="Page number being processed")
    
    extracted_data: str = dspy.OutputField(desc="Extract all relevant data from this page and return as a complete, valid JSON object. Ensure all braces and brackets are properly closed. No markdown formatting, no truncated responses.")


class NaturalDocumentExtractor(BaseDocumentExtractor):
    """Natural document extraction using DSPy without structured prompting"""
    
    def _initialize_predictor(self):
        """Initialize natural extraction predictor"""
        self.extractor = dspy.Predict(DocumentExtractionSignature)
    
    def _execute_extraction(self, document_text: str, document_image: dspy.Image) -> dspy.Prediction:
        """Execute natural extraction"""
        return self.extractor(
            document_text=document_text,
            document_image=document_image
        )
    
    def forward(self, document_text: str, document_image: dspy.Image):
        """Forward pass for natural extraction"""
        return super().forward(document_text=document_text, document_image=document_image)


class ChainOfThoughtExtractor(BaseDocumentExtractor):
    """Chain-of-thought extraction for complex reasoning"""
    
    def _initialize_predictor(self):
        """Initialize chain-of-thought extraction predictor"""
        self.extractor = dspy.ChainOfThought(DocumentExtractionSignature)
    
    def _execute_extraction(self, document_text: str, document_image: dspy.Image) -> dspy.Prediction:
        """Execute chain-of-thought extraction"""
        return self.extractor(
            document_text=document_text,
            document_image=document_image
        )
    
    def forward(self, document_text: str, document_image: dspy.Image):
        """Forward pass for chain-of-thought extraction"""
        return super().forward(document_text=document_text, document_image=document_image)


class PageExtractor(BaseDocumentExtractor):
    """Page-specific extraction using DSPy with native image support"""
    
    def _initialize_predictor(self):
        """Initialize page extraction predictor"""
        self.extractor = dspy.Predict(PageExtractionSignature)
    
    def _execute_extraction(self, page_text: str, page_image: dspy.Image, page_number: int) -> dspy.Prediction:
        """Execute page-specific extraction"""
        return self.extractor(
            page_text=page_text,
            page_image=page_image,
            page_number=page_number
        )
    
    def forward(self, page_text: str, page_image: dspy.Image, page_number: int):
        """Forward pass for page extraction"""
        return super().forward(page_text=page_text, page_image=page_image, page_number=page_number)


class VisionEnhancedExtractor(BaseDocumentExtractor):
    """Vision-enhanced extraction with specialized image processing"""
    
    def _initialize_predictor(self):
        """Initialize vision-enhanced extraction predictor"""
        # Use chain-of-thought for better vision reasoning
        self.extractor = dspy.ChainOfThought(DocumentExtractionSignature)
    
    def _execute_extraction(self, document_text: str, document_image: dspy.Image) -> dspy.Prediction:
        """Execute vision-enhanced extraction"""
        return self.extractor(
            document_text=document_text,
            document_image=document_image
        )
    
    def forward(self, document_text: str, document_image: dspy.Image):
        """Forward pass for vision-enhanced extraction"""
        return super().forward(document_text=document_text, document_image=document_image)
    
    def _validate_result(self, result: dspy.Prediction) -> bool:
        """Enhanced validation for vision extraction"""
        base_valid = super()._validate_result(result)
        
        if not base_valid:
            return False
        
        # Additional validation for vision extraction
        extracted_data = result.extracted_data
        try:
            data = json.loads(extracted_data)
            # Check if vision-specific fields are present (heuristic)
            vision_fields = ['image_analysis', 'visual_elements', 'layout_info', 'table_data']
            has_vision_content = any(field in str(data).lower() for field in vision_fields)
            return has_vision_content or len(str(data)) > 50  # Fallback to length check
        except json.JSONDecodeError:
            return False


class ExtractorFactory:
    """Factory class for creating extractors based on configuration"""
    
    @staticmethod
    def create_extractor(extraction_method: str, **kwargs) -> BaseDocumentExtractor:
        """
        Create an extractor based on the specified method
        
        Args:
            extraction_method: Type of extraction method
            **kwargs: Additional arguments for extractor initialization
            
        Returns:
            Configured extractor instance
        """
        extractors = {
            "natural": NaturalDocumentExtractor,
            "chain_of_thought": ChainOfThoughtExtractor,
            "page_extractor": PageExtractor,
            "vision_enhanced": VisionEnhancedExtractor
        }
        
        if extraction_method not in extractors:
            print(f"⚠️  Unknown extraction method '{extraction_method}', using 'natural'")
            extraction_method = "natural"
        
        return extractors[extraction_method](**kwargs)
    
    @staticmethod
    def get_available_extractors() -> List[str]:
        """Get list of available extraction methods"""
        return ["natural", "chain_of_thought", "page_extractor", "vision_enhanced"]
    
    @staticmethod
    def get_extractor_info(extraction_method: str) -> Dict[str, Any]:
        """Get information about a specific extractor"""
        extractor_info = {
            "natural": {
                "name": "Natural Document Extractor",
                "description": "Direct extraction without structured prompting",
                "best_for": ["Simple documents", "Quick processing", "General use"],
                "performance": "Fast",
                "accuracy": "Good"
            },
            "chain_of_thought": {
                "name": "Chain of Thought Extractor",
                "description": "Step-by-step reasoning for complex documents",
                "best_for": ["Complex documents", "Multi-section documents", "High accuracy needed"],
                "performance": "Medium",
                "accuracy": "High"
            },
            "page_extractor": {
                "name": "Page-by-Page Extractor",
                "description": "Processes each page individually",
                "best_for": ["Multi-page documents", "Detailed analysis", "Page-specific data"],
                "performance": "Slow",
                "accuracy": "Very High"
            },
            "vision_enhanced": {
                "name": "Vision Enhanced Extractor",
                "description": "Specialized for image-heavy documents",
                "best_for": ["Scanned documents", "Images with text", "Visual layouts"],
                "performance": "Medium",
                "accuracy": "High"
            }
        }
        
        return extractor_info.get(extraction_method, {})


# Generic data model for any document type
class DocumentData(BaseModel):
    """Generic data model for any document type"""
    content: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    extracted_at: Optional[str] = None
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    processing_time_seconds: float = Field(default=0.0)
