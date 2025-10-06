"""
Interfaces for the OCR document processing system
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from pathlib import Path


class IDocumentProcessor(ABC):
    """Interface for document processors"""
    
    @abstractmethod
    def process_document(self, file_path: str) -> Dict[str, Any]:
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


class IExtractionStrategy(ABC):
    """Interface for extraction strategies"""
    
    @abstractmethod
    def extract(self, document_text: str, document_image: Any, document_type: str) -> Dict[str, Any]:
        """Extract data using this strategy"""
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """Get the name of this extraction strategy"""
        pass


class IBatchProcessor(ABC):
    """Interface for batch processing"""
    
    @abstractmethod
    def process_batch(self, file_paths: List[str], **kwargs) -> List[Dict[str, Any]]:
        """Process multiple files in batch"""
        pass
    
    @abstractmethod
    def get_processing_summary(self) -> Dict[str, Any]:
        """Get summary of batch processing results"""
        pass
