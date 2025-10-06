"""
Configuration management module
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from core.base_classes import BaseConfigurationManager
from core.exceptions import ConfigurationError


class ConfigurationManager(BaseConfigurationManager):
    """Enhanced configuration manager with file support"""
    
    def __init__(self, use_azure: bool = False, config_file: Optional[str] = None):
        """
        Initialize configuration manager
        
        Args:
            use_azure: Whether to use Azure OpenAI
            config_file: Optional path to configuration file
        """
        super().__init__(use_azure)
        self.config_file = config_file
        
        # Load environment variables
        load_dotenv()
        
        # Load configuration from file if provided
        if config_file:
            self._load_config_file(config_file)
        
        # Configure based on provider choice
        if use_azure:
            self._setup_azure_openai()
        else:
            self._setup_openai()
    
    def _load_config_file(self, config_file: str) -> None:
        """Load configuration from file"""
        try:
            if os.path.exists(config_file):
                load_dotenv(config_file)
                print(f"📁 Loaded configuration from: {config_file}")
        except Exception as e:
            print(f"⚠️  Warning: Could not load config file {config_file}: {e}")
    
    def _setup_azure_openai(self) -> None:
        """Setup Azure OpenAI configuration"""
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION")
        
        if not all([api_key, endpoint, deployment_name, api_version]):
            missing = []
            if not api_key: missing.append("AZURE_OPENAI_API_KEY")
            if not endpoint: missing.append("AZURE_OPENAI_ENDPOINT")
            if not deployment_name: missing.append("AZURE_OPENAI_DEPLOYMENT_NAME")
            if not api_version: missing.append("AZURE_OPENAI_API_VERSION")
            
            raise ConfigurationError(f"Azure OpenAI configuration incomplete. Missing: {', '.join(missing)}")
        
        # Configure DSPy for Azure OpenAI
        import dspy
        self.lm = dspy.LM(
            deployment_name,
            api_key=api_key,
            api_base=endpoint,
            api_version=api_version
        )
        
        # Store configuration info
        self.config_info = {
            "provider": "Azure OpenAI",
            "deployment_name": deployment_name,
            "endpoint": endpoint,
            "api_version": api_version,
            "api_key": api_key[:8] + "..." if api_key else None
        }
        
        # Configure DSPy globally
        dspy.configure(lm=self.lm)
    
    def _setup_openai(self) -> None:
        """Setup regular OpenAI configuration"""
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise ConfigurationError("OpenAI API key is required. Set OPENAI_API_KEY environment variable")
        
        # Configure DSPy for regular OpenAI
        import dspy
        self.lm = dspy.LM("openai/gpt-4o-mini", api_key=api_key)
        
        # Store configuration info
        self.config_info = {
            "provider": "OpenAI",
            "model": "gpt-4o-mini",
            "api_key": api_key[:8] + "..." if api_key else None
        }
        
        # Configure DSPy globally
        dspy.configure(lm=self.lm)
    
    def get_api_key(self) -> str:
        """Get the API key"""
        if self.use_azure:
            return os.getenv("AZURE_OPENAI_API_KEY")
        else:
            return os.getenv("OPENAI_API_KEY")
    
    def get_lm(self):
        """Get the configured LM instance"""
        return self.lm
    
    def get_config_info(self) -> Dict[str, Any]:
        """Get configuration information"""
        return self.config_info.copy()
    
    def print_config(self) -> None:
        """Print current configuration"""
        info = self.get_config_info()
        print(f"🔵 Using {info['provider']}")
        if self.use_azure:
            print(f"   Deployment: {info['deployment_name']}")
            print(f"   Endpoint: {info['endpoint']}")
            print(f"   API Version: {info['api_version']}")
        else:
            print(f"   Model: {info['model']}")
        print(f"   API Key: {info['api_key']}")
    
    def validate_configuration(self) -> bool:
        """Validate that all required configuration is present"""
        try:
            api_key = self.get_api_key()
            return bool(api_key) and bool(self.lm)
        except Exception:
            return False
    
    def get_processing_config(self) -> Dict[str, Any]:
        """Get processing configuration"""
        return {
            "use_azure": self.use_azure,
            "provider": self.config_info.get("provider"),
            "model": self.config_info.get("model", self.config_info.get("deployment_name")),
            "api_key_configured": bool(self.get_api_key())
        }
