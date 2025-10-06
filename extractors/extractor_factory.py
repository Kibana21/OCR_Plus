"""
Factory pattern for creating data extractors
"""

from typing import Dict, Type
from core.base_classes import BaseDataExtractor
from core.exceptions import ExtractionError
from .extraction_strategies import (
    ExtractionStrategy,
    NaturalExtractionStrategy,
    ChainOfThoughtExtractionStrategy,
    AutoExtractionStrategy
)


class ExtractorFactory:
    """Factory for creating data extractors based on extraction method"""
    
    _strategies: Dict[str, Type[ExtractionStrategy]] = {
        "natural": NaturalExtractionStrategy,
        "chain_of_thought": ChainOfThoughtExtractionStrategy,
        "auto": AutoExtractionStrategy
    }
    
    def __init__(self, api_key: str, model_name: str = "openai/gpt-4o-mini", use_azure: bool = False):
        """
        Initialize extractor factory
        
        Args:
            api_key: API key for LLM provider
            model_name: Model name to use
            use_azure: Whether to use Azure OpenAI
        """
        self.api_key = api_key
        self.model_name = model_name
        self.use_azure = use_azure
    
    def create_extractor(self, extraction_method: str = "auto") -> BaseDataExtractor:
        """
        Create appropriate extractor for the given method
        
        Args:
            extraction_method: Method to use ("auto", "natural", "chain_of_thought")
            
        Returns:
            Appropriate data extractor instance
            
        Raises:
            ExtractionError: If extraction method is not supported
        """
        if extraction_method not in self._strategies:
            raise ExtractionError(f"Unsupported extraction method: {extraction_method}")
        
        # Get strategy class
        strategy_class = self._strategies[extraction_method]
        
        # Create strategy instance
        strategy = strategy_class(
            api_key=self.api_key,
            model_name=self.model_name,
            use_azure=self.use_azure
        )
        
        # Create extractor wrapper
        return DataExtractorWrapper(strategy)
    
    def register_strategy(self, method_name: str, strategy_class: Type[ExtractionStrategy]):
        """
        Register a new extraction strategy
        
        Args:
            method_name: Name of the extraction method
            strategy_class: Strategy class to register
        """
        self._strategies[method_name] = strategy_class
    
    def get_available_methods(self) -> list:
        """
        Get list of available extraction methods
        
        Returns:
            List of available method names
        """
        return list(self._strategies.keys())
    
    def get_method_info(self, method_name: str) -> dict:
        """
        Get information about a specific extraction method
        
        Args:
            method_name: Name of the extraction method
            
        Returns:
            Dictionary with method information
        """
        if method_name not in self._strategies:
            return {"error": f"Method {method_name} not found"}
        
        strategy_class = self._strategies[method_name]
        
        return {
            "name": method_name,
            "class": strategy_class.__name__,
            "description": strategy_class.__doc__ or "No description available"
        }


class DataExtractorWrapper(BaseDataExtractor):
    """Wrapper class that adapts extraction strategies to the BaseDataExtractor interface"""
    
    def __init__(self, strategy: ExtractionStrategy):
        """
        Initialize wrapper with extraction strategy
        
        Args:
            strategy: Extraction strategy to wrap
        """
        super().__init__(
            api_key=strategy.api_key,
            model_name=strategy.model_name,
            use_azure=strategy.use_azure
        )
        self.strategy = strategy
    
    def extract_data(self, processed_doc: dict, document_type: str) -> dict:
        """
        Extract structured data from processed document
        
        Args:
            processed_doc: Processed document data
            document_type: Type of document
            
        Returns:
            Dictionary containing extracted data
        """
        try:
            # Prepare input data
            text_content = processed_doc.get('text_content', '')
            images_data = self._prepare_images_for_extraction(processed_doc.get('images', []))
            
            # Use strategy to extract data
            result = self.strategy.extract(text_content, images_data, document_type)
            
            # Format result
            return self._format_extraction_result(result, document_type)
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'strategy': self.strategy.get_strategy_name()
            }
    
    def extract_page_by_page(self, file_path: str, document_type: str) -> dict:
        """
        Extract data from each page individually
        
        Args:
            file_path: Path to the document file
            document_type: Type of document
            
        Returns:
            Dictionary containing page-by-page results
        """
        try:
            # Import here to avoid circular imports
            from page_by_page_extractor import PageByPageExtractor
            
            # Create page-by-page extractor
            page_extractor = PageByPageExtractor(
                api_key=self.api_key,
                model_name=self.model_name,
                use_azure=self.use_azure
            )
            
            # Extract page by page
            result = page_extractor.extract_page_by_page(file_path, document_type)
            
            # Cleanup
            page_extractor.cleanup()
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'strategy': self.strategy.get_strategy_name()
            }
    
    def _prepare_images_for_extraction(self, images: list) -> any:
        """Prepare image data for extraction"""
        if not images:
            return None
        
        # For now, use the first image (DSPy limitation: single image only)
        # TODO: Handle multiple images by processing page by page
        return images[0]
    
    def _format_extraction_result(self, result: dict, document_type: str) -> dict:
        """Format extraction result"""
        if result.get('success', False):
            return {
                'success': True,
                'extracted_data': result.get('data', {}),
                'strategy': result.get('strategy', 'unknown'),
                'confidence': result.get('confidence', 0.0),
                'reasoning': result.get('reasoning'),  # For chain-of-thought
                'metadata': {
                    'extraction_method': result.get('strategy', 'unknown'),
                    'document_type': document_type,
                    'confidence_score': result.get('confidence', 0.0)
                }
            }
        else:
            return {
                'success': False,
                'error': result.get('error', 'Unknown error'),
                'strategy': result.get('strategy', 'unknown')
            }
