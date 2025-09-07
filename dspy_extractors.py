"""
DSPy-based extraction modules for structured data extraction from documents
"""

import dspy
import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class DocumentExtractor(dspy.Module):
    """Base class for document data extraction using DSPy"""
    
    def __init__(self, signature_class, **kwargs):
        super().__init__()
        self.extractor = dspy.Predict(signature_class, **kwargs)
    
    def forward(self, **kwargs):
        return self.extractor(**kwargs)

class DocumentExtractionSignature(dspy.Signature):
    """Extract structured data from document and return as JSON format. Example: {\"patient_name\": \"John Doe\", \"age\": 30, \"lab_results\": {\"glucose\": \"95 mg/dL\"}}"""
    document_text: str = dspy.InputField()
    document_image: dspy.Image = dspy.InputField()
    
    extracted_data: str = dspy.OutputField(desc="Extract all relevant data and return as valid JSON object only, no markdown formatting")

class PageExtractionSignature(dspy.Signature):
    """Extract structured data from a single page and return as JSON format. Example: {\"patient_name\": \"John Doe\", \"lab_results\": {\"glucose\": \"95 mg/dL\"}}"""
    page_text: str = dspy.InputField()
    page_image: dspy.Image = dspy.InputField()
    page_number: int = dspy.InputField()
    
    extracted_data: str = dspy.OutputField(desc="Extract all relevant data from this page and return as valid JSON object only, no markdown formatting")

class NaturalDocumentExtractor(dspy.Module):
    """Natural document extraction using DSPy without structured prompting"""
    
    def __init__(self):
        super().__init__()
        self.extractor = dspy.Predict(DocumentExtractionSignature)
    
    def forward(self, document_text: str, document_image: dspy.Image):
        return self.extractor(
            document_text=document_text,
            document_image=document_image
        )

class ChainOfThoughtExtractor(dspy.Module):
    """Chain-of-thought extraction for complex reasoning"""
    
    def __init__(self):
        super().__init__()
        self.extractor = dspy.ChainOfThought(DocumentExtractionSignature)
    
    def forward(self, document_text: str, document_image: dspy.Image):
        return self.extractor(
            document_text=document_text,
            document_image=document_image
        )

class PageExtractor(dspy.Module):
    """Page-specific extraction using DSPy with native image support"""
    
    def __init__(self):
        super().__init__()
        self.extractor = dspy.Predict(PageExtractionSignature)
    
    def forward(self, page_text: str, page_image: dspy.Image, page_number: int):
        return self.extractor(
            page_text=page_text,
            page_image=page_image,
            page_number=page_number
        )

# Generic data model for any document type
class DocumentData(BaseModel):
    """Generic data model for any document type"""
    content: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    extracted_at: Optional[str] = None
