"""
Factory pattern for creating document processors
"""

from typing import Dict, Type
from pathlib import Path

from core.base_classes import BaseDocumentProcessor, DocumentType
from core.exceptions import UnsupportedFormatError

# Import processors only when needed to avoid heavy dependencies
try:
    from .pdf_processor import PDFProcessor
    PDF_PROCESSOR_AVAILABLE = True
except ImportError:
    PDF_PROCESSOR_AVAILABLE = False
    print("⚠️  PDF processor not available (PyPDF2/PyMuPDF not installed)")

try:
    from .image_processor import ImageProcessor
    IMAGE_PROCESSOR_AVAILABLE = True
except ImportError:
    IMAGE_PROCESSOR_AVAILABLE = False
    print("⚠️  Image processor not available (PIL/pytesseract not installed)")

try:
    from .html_processor import HTMLProcessor
    HTML_PROCESSOR_AVAILABLE = True
except ImportError:
    HTML_PROCESSOR_AVAILABLE = False
    print("⚠️  HTML processor not available (BeautifulSoup not installed)")


class ProcessorFactory:
    """Factory for creating document processors based on file type"""
    
    _processors: Dict[DocumentType, Type[BaseDocumentProcessor]] = {}
    
    def __init__(self):
        """Initialize the processor registry"""
        self._register_processors()
    
    def _register_processors(self):
        """Register available processors"""
        if PDF_PROCESSOR_AVAILABLE:
            self._processors[DocumentType.PDF] = PDFProcessor
        if IMAGE_PROCESSOR_AVAILABLE:
            self._processors[DocumentType.IMAGE] = ImageProcessor
        if HTML_PROCESSOR_AVAILABLE:
            self._processors[DocumentType.HTML] = HTMLProcessor
    
    @classmethod
    def create_processor(cls, file_path: str, temp_dir: str = "temp_images") -> BaseDocumentProcessor:
        """
        Create appropriate processor for the given file
        
        Args:
            file_path: Path to the document file
            temp_dir: Temporary directory for processing
            
        Returns:
            Appropriate document processor instance
            
        Raises:
            UnsupportedFormatError: If file format is not supported
        """
        path = Path(file_path)
        extension = path.suffix.lower().lstrip('.')
        
        # Determine document type
        if extension == 'pdf':
            doc_type = DocumentType.PDF
        elif extension in ['jpg', 'jpeg', 'png', 'bmp', 'tiff']:
            doc_type = DocumentType.IMAGE
        elif extension in ['html', 'htm']:
            doc_type = DocumentType.HTML
        else:
            raise UnsupportedFormatError(f"Unsupported file format: {extension}")
        
        # Get processor class
        processor_class = cls._processors.get(doc_type)
        if not processor_class:
            raise UnsupportedFormatError(f"No processor available for document type: {doc_type}")
        
        # Create and return processor instance
        return processor_class(temp_dir=temp_dir)
    
    @classmethod
    def register_processor(cls, doc_type: DocumentType, processor_class: Type[BaseDocumentProcessor]):
        """
        Register a new processor type
        
        Args:
            doc_type: Document type
            processor_class: Processor class to register
        """
        cls._processors[doc_type] = processor_class
    
    @classmethod
    def get_supported_formats(cls) -> Dict[DocumentType, list]:
        """
        Get list of supported formats for each document type
        
        Returns:
            Dictionary mapping document types to supported file extensions
        """
        return {
            DocumentType.PDF: ['pdf'],
            DocumentType.IMAGE: ['jpg', 'jpeg', 'png', 'bmp', 'tiff'],
            DocumentType.HTML: ['html', 'htm']
        }
    
    @classmethod
    def is_supported_format(cls, file_path: str) -> bool:
        """
        Check if file format is supported
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if format is supported, False otherwise
        """
        try:
            cls.create_processor(file_path)
            return True
        except UnsupportedFormatError:
            return False
    
    @classmethod
    def get_available_processors(cls) -> Dict[str, bool]:
        """
        Get information about which processors are available
        
        Returns:
            Dictionary showing processor availability
        """
        return {
            'pdf_processor': PDF_PROCESSOR_AVAILABLE,
            'image_processor': IMAGE_PROCESSOR_AVAILABLE,
            'html_processor': HTML_PROCESSOR_AVAILABLE
        }
