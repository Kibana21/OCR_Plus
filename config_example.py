"""
Example showing how to use the centralized LLM configuration
"""

from llm_config import LLMConfig, auto_setup_llm, setup_openai, setup_azure_openai

def example_1_manual_config():
    """Example 1: Manual configuration"""
    print("🔧 Example 1: Manual Configuration")
    print("-" * 40)
    
    # Use regular OpenAI
    config = LLMConfig(use_azure=False)
    config.print_config()
    
    # Get the LM instance
    lm = config.get_lm()
    print(f"LM instance: {type(lm)}")
    
    # Get API key
    api_key = config.get_api_key()
    print(f"API Key: {api_key[:8]}...")

def example_2_convenience_functions():
    """Example 2: Using convenience functions"""
    print("\n🔧 Example 2: Convenience Functions")
    print("-" * 40)
    
    # Setup OpenAI
    openai_config = setup_openai()
    openai_config.print_config()
    
    # Setup Azure OpenAI (if configured)
    try:
        azure_config = setup_azure_openai()
        azure_config.print_config()
    except ValueError as e:
        print(f"Azure OpenAI not configured: {e}")

def example_3_auto_detection():
    """Example 3: Auto-detection"""
    print("\n🔧 Example 3: Auto-Detection")
    print("-" * 40)
    
    # Auto-detect configuration
    config = auto_setup_llm()
    config.print_config()

def example_4_integration():
    """Example 4: Integration with DataExtractor"""
    print("\n🔧 Example 4: Integration with DataExtractor")
    print("-" * 40)
    
    from data_extractor import DataExtractor
    
    # Create extractor with centralized config
    extractor = DataExtractor(use_azure=False)
    
    # The extractor now uses the centralized configuration
    print(f"Extractor API Key: {extractor.api_key[:8]}...")
    print(f"Extractor LM: {type(extractor.lm)}")

if __name__ == "__main__":
    print("🎯 LLM Configuration Examples")
    print("=" * 50)
    
    try:
        example_1_manual_config()
        example_2_convenience_functions()
        example_3_auto_detection()
        example_4_integration()
        
        print("\n✅ All examples completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure you have set up your environment variables properly.")
