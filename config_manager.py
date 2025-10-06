"""
Centralized Configuration Manager
Handles all configuration settings for the document processing pipeline
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        pass  # Fallback if dotenv is not available


@dataclass
class ProcessingConfig:
    """Configuration for document processing"""
    supported_formats: List[str] = field(default_factory=lambda: ['.pdf', '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.html', '.htm'])
    temp_dir: str = "temp_images"
    batch_results_file: str = "batch_processing_results.json"
    max_file_size_mb: int = 100
    enable_image_enhancement: bool = True
    ocr_enabled: bool = True


@dataclass
class ExtractionConfig:
    """Configuration for data extraction"""
    default_model: str = "openai/gpt-4o-mini"
    use_vision: bool = True
    extraction_method: str = "auto"  # auto, natural, chain_of_thought, page_by_page
    max_retries: int = 3
    timeout_seconds: int = 300
    confidence_threshold: float = 0.7


@dataclass
class LLMConfig:
    """Configuration for LLM providers"""
    use_azure: bool = False
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    endpoint: Optional[str] = None
    deployment_name: Optional[str] = None
    api_version: Optional[str] = None


class ConfigManager:
    """Centralized configuration manager for the entire system"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration manager
        
        Args:
            config_file: Optional path to custom config file
        """
        self.config_file = config_file
        self.processing = ProcessingConfig()
        self.extraction = ExtractionConfig()
        self.llm = LLMConfig()
        
        # Load environment variables
        load_dotenv()
        
        # Load configurations
        self._load_environment_config()
        if config_file:
            self._load_config_file(config_file)
    
    def _load_environment_config(self):
        """Load configuration from environment variables"""
        # LLM Configuration
        self.llm.use_azure = os.getenv("USE_AZURE", "false").lower() == "true"
        
        if self.llm.use_azure:
            self.llm.api_key = os.getenv("AZURE_OPENAI_API_KEY")
            self.llm.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            self.llm.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
            self.llm.api_version = os.getenv("AZURE_OPENAI_API_VERSION")
        else:
            self.llm.api_key = os.getenv("OPENAI_API_KEY")
            self.llm.model_name = os.getenv("MODEL_NAME", "openai/gpt-4o-mini")
        
        # Processing Configuration
        temp_dir = os.getenv("TEMP_DIR")
        if temp_dir:
            self.processing.temp_dir = temp_dir
        
        batch_file = os.getenv("BATCH_RESULTS_FILE")
        if batch_file:
            self.processing.batch_results_file = batch_file
        
        # Extraction Configuration
        extraction_method = os.getenv("EXTRACTION_METHOD")
        if extraction_method:
            self.extraction.extraction_method = extraction_method
        
        use_vision = os.getenv("USE_VISION")
        if use_vision:
            self.extraction.use_vision = use_vision.lower() == "true"
    
    def _load_config_file(self, config_file: str):
        """Load configuration from JSON file"""
        import json
        
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            # Update configurations from file
            if 'processing' in config_data:
                for key, value in config_data['processing'].items():
                    if hasattr(self.processing, key):
                        setattr(self.processing, key, value)
            
            if 'extraction' in config_data:
                for key, value in config_data['extraction'].items():
                    if hasattr(self.extraction, key):
                        setattr(self.extraction, key, value)
            
            if 'llm' in config_data:
                for key, value in config_data['llm'].items():
                    if hasattr(self.llm, key):
                        setattr(self.llm, key, value)
                        
        except Exception as e:
            print(f"⚠️  Warning: Could not load config file {config_file}: {e}")
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration and return status"""
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Validate LLM configuration
        if self.llm.use_azure:
            required_azure_vars = [
                ("api_key", "AZURE_OPENAI_API_KEY"),
                ("endpoint", "AZURE_OPENAI_ENDPOINT"),
                ("deployment_name", "AZURE_OPENAI_DEPLOYMENT_NAME"),
                ("api_version", "AZURE_OPENAI_API_VERSION")
            ]
            
            for attr, env_var in required_azure_vars:
                if not getattr(self.llm, attr):
                    validation_results["errors"].append(f"Missing {env_var}")
                    validation_results["valid"] = False
        else:
            if not self.llm.api_key:
                validation_results["errors"].append("Missing OPENAI_API_KEY")
                validation_results["valid"] = False
        
        # Validate processing configuration
        if self.processing.max_file_size_mb <= 0:
            validation_results["errors"].append("max_file_size_mb must be positive")
            validation_results["valid"] = False
        
        if not self.processing.supported_formats:
            validation_results["errors"].append("No supported formats configured")
            validation_results["valid"] = False
        
        # Validate extraction configuration
        valid_methods = ["auto", "natural", "chain_of_thought", "page_by_page"]
        if self.extraction.extraction_method not in valid_methods:
            validation_results["errors"].append(f"Invalid extraction method: {self.extraction.extraction_method}")
            validation_results["valid"] = False
        
        if not 0 <= self.extraction.confidence_threshold <= 1:
            validation_results["errors"].append("confidence_threshold must be between 0 and 1")
            validation_results["valid"] = False
        
        # Warnings
        if self.extraction.max_retries > 5:
            validation_results["warnings"].append("High retry count may cause long processing times")
        
        if self.extraction.timeout_seconds < 60:
            validation_results["warnings"].append("Short timeout may cause processing failures")
        
        return validation_results
    
    def get_llm_config_info(self) -> Dict[str, Any]:
        """Get LLM configuration information"""
        if self.llm.use_azure:
            return {
                "provider": "Azure OpenAI",
                "deployment_name": self.llm.deployment_name,
                "endpoint": self.llm.endpoint,
                "api_version": self.llm.api_version,
                "api_key": self.llm.api_key[:8] + "..." if self.llm.api_key else None
            }
        else:
            return {
                "provider": "OpenAI",
                "model": self.llm.model_name or "openai/gpt-4o-mini",
                "api_key": self.llm.api_key[:8] + "..." if self.llm.api_key else None
            }
    
    def save_config(self, file_path: str):
        """Save current configuration to file"""
        import json
        
        config_data = {
            "processing": {
                "supported_formats": self.processing.supported_formats,
                "temp_dir": self.processing.temp_dir,
                "batch_results_file": self.processing.batch_results_file,
                "max_file_size_mb": self.processing.max_file_size_mb,
                "enable_image_enhancement": self.processing.enable_image_enhancement,
                "ocr_enabled": self.processing.ocr_enabled
            },
            "extraction": {
                "default_model": self.extraction.default_model,
                "use_vision": self.extraction.use_vision,
                "extraction_method": self.extraction.extraction_method,
                "max_retries": self.extraction.max_retries,
                "timeout_seconds": self.extraction.timeout_seconds,
                "confidence_threshold": self.extraction.confidence_threshold
            },
            "llm": {
                "use_azure": self.llm.use_azure,
                "model_name": self.llm.model_name,
                "endpoint": self.llm.endpoint,
                "deployment_name": self.llm.deployment_name,
                "api_version": self.llm.api_version
            }
        }
        
        with open(file_path, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def print_config_summary(self):
        """Print configuration summary"""
        print("🔧 Configuration Summary")
        print("=" * 50)
        
        # LLM Configuration
        llm_info = self.get_llm_config_info()
        print(f"🤖 LLM Provider: {llm_info['provider']}")
        if self.llm.use_azure:
            print(f"   Deployment: {llm_info['deployment_name']}")
            print(f"   Endpoint: {llm_info['endpoint']}")
            print(f"   API Version: {llm_info['api_version']}")
        else:
            print(f"   Model: {llm_info['model']}")
        print(f"   API Key: {llm_info['api_key']}")
        
        # Processing Configuration
        print(f"\n📄 Processing:")
        print(f"   Supported formats: {', '.join(self.processing.supported_formats)}")
        print(f"   Temp directory: {self.processing.temp_dir}")
        print(f"   Max file size: {self.processing.max_file_size_mb}MB")
        print(f"   Image enhancement: {self.processing.enable_image_enhancement}")
        print(f"   OCR enabled: {self.processing.ocr_enabled}")
        
        # Extraction Configuration
        print(f"\n🔍 Extraction:")
        print(f"   Method: {self.extraction.extraction_method}")
        print(f"   Use vision: {self.extraction.use_vision}")
        print(f"   Max retries: {self.extraction.max_retries}")
        print(f"   Timeout: {self.extraction.timeout_seconds}s")
        print(f"   Confidence threshold: {self.extraction.confidence_threshold}")


# Global configuration instance
_global_config = None


def get_config() -> ConfigManager:
    """Get the global configuration instance"""
    global _global_config
    if _global_config is None:
        _global_config = ConfigManager()
    return _global_config


def set_config(config: ConfigManager):
    """Set the global configuration instance"""
    global _global_config
    _global_config = config


if __name__ == "__main__":
    """Test the configuration manager"""
    print("🧪 Testing Configuration Manager")
    print("=" * 50)
    
    config = ConfigManager()
    
    # Validate configuration
    validation = config.validate_config()
    print(f"\n✅ Configuration valid: {validation['valid']}")
    
    if validation['errors']:
        print(f"❌ Errors: {validation['errors']}")
    
    if validation['warnings']:
        print(f"⚠️  Warnings: {validation['warnings']}")
    
    # Print configuration summary
    config.print_config_summary()
