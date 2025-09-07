"""
Centralized LLM Configuration Module
Handles both OpenAI and Azure OpenAI setup using environment variables
"""

import os
import dspy
from dotenv import load_dotenv
from typing import Optional, Dict, Any

class LLMConfig:
    """Centralized configuration for LLM providers"""
    
    def __init__(self, use_azure: bool = False):
        """
        Initialize LLM configuration
        
        Args:
            use_azure: Whether to use Azure OpenAI (True) or regular OpenAI (False)
        """
        self.use_azure = use_azure
        self.lm = None
        self.config_info = {}
        
        # Load environment variables
        load_dotenv()
        
        # Configure based on provider choice
        if use_azure:
            self._setup_azure_openai()
        else:
            self._setup_openai()
    
    def _setup_azure_openai(self):
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
            
            raise ValueError(f"Azure OpenAI configuration incomplete. Missing: {', '.join(missing)}")
        
        # Configure DSPy for Azure OpenAI
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
    
    def _setup_openai(self):
        """Setup regular OpenAI configuration"""
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable")
        
        # Configure DSPy for regular OpenAI
        self.lm = dspy.LM("openai/gpt-4o-mini", api_key=api_key)
        
        # Store configuration info
        self.config_info = {
            "provider": "OpenAI",
            "model": "gpt-4o-mini",
            "api_key": api_key[:8] + "..." if api_key else None
        }
        
        # Configure DSPy globally
        dspy.configure(lm=self.lm)
    
    def get_lm(self):
        """Get the configured LM instance"""
        return self.lm
    
    def get_config_info(self) -> Dict[str, Any]:
        """Get configuration information"""
        return self.config_info.copy()
    
    def get_api_key(self) -> str:
        """Get the API key"""
        if self.use_azure:
            return os.getenv("AZURE_OPENAI_API_KEY")
        else:
            return os.getenv("OPENAI_API_KEY")
    
    def print_config(self):
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

def setup_llm(use_azure: bool = False) -> LLMConfig:
    """
    Convenience function to setup LLM configuration
    
    Args:
        use_azure: Whether to use Azure OpenAI
        
    Returns:
        LLMConfig instance
    """
    return LLMConfig(use_azure=use_azure)

def get_llm_config(use_azure: bool = False) -> LLMConfig:
    """
    Get LLM configuration instance
    
    Args:
        use_azure: Whether to use Azure OpenAI
        
    Returns:
        LLMConfig instance
    """
    return LLMConfig(use_azure=use_azure)

# Convenience functions for common use cases
def setup_openai() -> LLMConfig:
    """Setup regular OpenAI configuration"""
    return LLMConfig(use_azure=False)

def setup_azure_openai() -> LLMConfig:
    """Setup Azure OpenAI configuration"""
    return LLMConfig(use_azure=True)

# Auto-detect configuration based on environment variables
def auto_setup_llm() -> LLMConfig:
    """
    Automatically detect which configuration to use based on available environment variables
    
    Returns:
        LLMConfig instance
    """
    load_dotenv()
    
    # Check if Azure OpenAI variables are available
    azure_vars = [
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT", 
        "AZURE_OPENAI_DEPLOYMENT_NAME",
        "AZURE_OPENAI_API_VERSION"
    ]
    
    if all(os.getenv(var) for var in azure_vars):
        print("🔵 Auto-detected: Azure OpenAI configuration")
        return LLMConfig(use_azure=True)
    elif os.getenv("OPENAI_API_KEY"):
        print("🔵 Auto-detected: OpenAI configuration")
        return LLMConfig(use_azure=False)
    else:
        raise ValueError("No valid LLM configuration found. Please set up either OpenAI or Azure OpenAI environment variables.")

if __name__ == "__main__":
    """Test the configuration module"""
    print("🧪 Testing LLM Configuration Module")
    print("=" * 50)
    
    try:
        # Test auto-detection
        config = auto_setup_llm()
        config.print_config()
        print("✅ Configuration successful!")
        
    except ValueError as e:
        print(f"❌ Configuration failed: {e}")
        print("\nPlease set up your environment variables:")
        print("For OpenAI: OPENAI_API_KEY")
        print("For Azure OpenAI: AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT_NAME, AZURE_OPENAI_API_VERSION")
