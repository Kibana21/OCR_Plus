"""
Exception classes for the OCR document processing system
"""


class OCRProcessingError(Exception):
    """Base exception for OCR processing errors"""
    pass


class ConfigurationError(OCRProcessingError):
    """Exception for configuration-related errors"""
    pass


class DocumentProcessingError(OCRProcessingError):
    """Exception for document processing errors"""
    pass


class ExtractionError(OCRProcessingError):
    """Exception for data extraction errors"""
    pass


class UnsupportedFormatError(DocumentProcessingError):
    """Exception for unsupported file formats"""
    pass


class FileNotFoundError(DocumentProcessingError):
    """Exception for file not found errors"""
    pass


class APIError(OCRProcessingError):
    """Exception for API-related errors"""
    pass


class ValidationError(OCRProcessingError):
    """Exception for data validation errors"""
    pass
