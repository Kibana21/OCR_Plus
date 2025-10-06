"""
Base classes and interfaces for the OCR document processing system
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from dataclasses import dataclass
from enum import Enum


class DocumentType(Enum):
    """Supported document types"""
    PDF = "pdf"
    IMAGE = "image"
    HTML = "html"
    UNKNOWN = "unknown"


class ProcessingStatus(Enum):
    """Processing status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DocumentMetadata:
    """Metadata for a document"""
    file_path: str
    file_size: int
    file_type: DocumentType
    total_pages: int = 0
    has_images: bool = False
    text_length: int = 0
    created_at: Optional[str] = None
    modified_at: Optional[str] = None


@dataclass
class ProcessingResult:
    """Result of document processing"""
    success: bool
    document_metadata: DocumentMetadata
    extracted_data: Dict[str, Any]
    processing_time: float
    error_message: Optional[str] = None
    confidence_score: float = 0.0
    processing_method: str = "unknown"


class IDocumentProcessor(ABC):
    """Interface for document processors"""
    
    @abstractmethod
    def process_document(self, file_path: str) -> ProcessingResult:
        """Process a document and return structured data"""
        pass
    
    @abstractmethod
    def supports_format(self, file_extension: str) -> bool:
        """Check if processor supports the given file format"""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources"""
        pass


class IDataExtractor(ABC):
    """Interface for data extractors"""
    
    @abstractmethod
    def extract_data(self, processed_doc: Dict[str, Any], document_type: str) -> Dict[str, Any]:
        """Extract structured data from processed document"""
        pass
    
    @abstractmethod
    def extract_page_by_page(self, file_path: str, document_type: str) -> Dict[str, Any]:
        """Extract data from each page individually"""
        pass


class IConfigurationManager(ABC):
    """Interface for configuration management"""
    
    @abstractmethod
    def get_api_key(self) -> str:
        """Get API key for LLM provider"""
        pass
    
    @abstractmethod
    def get_lm(self):
        """Get configured language model"""
        pass
    
    @abstractmethod
    def get_config_info(self) -> Dict[str, Any]:
        """Get configuration information"""
        pass


class IFileHandler(ABC):
    """Interface for file handling operations"""
    
    @abstractmethod
    def read_file(self, file_path: str) -> bytes:
        """Read file contents"""
        pass
    
    @abstractmethod
    def write_file(self, file_path: str, content: Union[str, bytes]) -> None:
        """Write content to file"""
        pass
    
    @abstractmethod
    def file_exists(self, file_path: str) -> bool:
        """Check if file exists"""
        pass


class BaseDocumentProcessor(IDocumentProcessor):
    """Base class for document processors"""
    
    def __init__(self, temp_dir: str = "temp_images"):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(exist_ok=True)
        self.supported_formats = set()
    
    def get_document_metadata(self, file_path: str) -> DocumentMetadata:
        """Get metadata for a document"""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Determine file type
        file_type = self._determine_file_type(path.suffix.lower())
        
        return DocumentMetadata(
            file_path=str(path),
            file_size=path.stat().st_size,
            file_type=file_type,
            created_at=str(path.stat().st_ctime),
            modified_at=str(path.stat().st_mtime)
        )
    
    def _determine_file_type(self, extension: str) -> DocumentType:
        """Determine document type from file extension"""
        extension = extension.lower().lstrip('.')
        
        if extension == 'pdf':
            return DocumentType.PDF
        elif extension in ['jpg', 'jpeg', 'png', 'bmp', 'tiff']:
            return DocumentType.IMAGE
        elif extension in ['html', 'htm']:
            return DocumentType.HTML
        else:
            return DocumentType.UNKNOWN
    
    def supports_format(self, file_extension: str) -> bool:
        """Check if processor supports the given file format"""
        return file_extension.lower().lstrip('.') in self.supported_formats
    
    def cleanup(self) -> None:
        """Clean up temporary files"""
        if self.temp_dir.exists():
            for file in self.temp_dir.iterdir():
                file.unlink()
            self.temp_dir.rmdir()


class BaseDataExtractor(IDataExtractor):
    """Base class for data extractors"""
    
    def __init__(self, api_key: str, model_name: str = "openai/gpt-4o-mini", use_azure: bool = False):
        self.api_key = api_key
        self.model_name = model_name
        self.use_azure = use_azure
        self.extraction_method = "auto"
    
    def validate_extraction_result(self, result: Dict[str, Any]) -> bool:
        """Validate extraction result"""
        return isinstance(result, dict) and len(result) > 0
    
    def format_extraction_result(self, raw_data: Any, document_type: str) -> Dict[str, Any]:
        """Format raw extraction data into structured format"""
        if isinstance(raw_data, dict):
            return raw_data
        elif isinstance(raw_data, str):
            try:
                import json
                return json.loads(raw_data)
            except json.JSONDecodeError:
                return {"raw_extraction": raw_data}
        else:
            return {"raw_extraction": str(raw_data)}


class BaseConfigurationManager(IConfigurationManager):
    """Base class for configuration management"""
    
    def __init__(self, use_azure: bool = False):
        self.use_azure = use_azure
        self.config_info = {}
        self.lm = None
    
    def validate_configuration(self) -> bool:
        """Validate that all required configuration is present"""
        return bool(self.get_api_key())
    
    def get_config_info(self) -> Dict[str, Any]:
        """Get configuration information"""
        return self.config_info.copy()
    
    def print_config(self) -> None:
        """Print current configuration"""
        info = self.get_config_info()
        provider = info.get('provider', 'Unknown')
        print(f"🔵 Using {provider}")
        
        for key, value in info.items():
            if key != 'provider' and value:
                print(f"   {key.title()}: {value}")


# Exception classes
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
