"""
Core module for OCR document processing system
Contains base classes, interfaces, and common utilities
"""

from .base_classes import (
    BaseDocumentProcessor,
    BaseDataExtractor,
    BaseConfigurationManager,
    ProcessingResult,
    DocumentMetadata
)

from .interfaces import (
    IDocumentProcessor,
    IDataExtractor,
    IConfigurationManager,
    IFileHandler
)

from .exceptions import (
    OCRProcessingError,
    ConfigurationError,
    DocumentProcessingError,
    ExtractionError
)

__all__ = [
    'BaseDocumentProcessor',
    'BaseDataExtractor', 
    'BaseConfigurationManager',
    'ProcessingResult',
    'DocumentMetadata',
    'IDocumentProcessor',
    'IDataExtractor',
    'IConfigurationManager',
    'IFileHandler',
    'OCRProcessingError',
    'ConfigurationError',
    'DocumentProcessingError',
    'ExtractionError'
]
