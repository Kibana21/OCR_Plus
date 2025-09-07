import dspy
import sys
from llm_config import LLMConfig

def main():
    """Simple DSPy example using centralized configuration"""
    
    # Check for Azure flag
    use_azure = "--azure" in sys.argv or "--use-azure" in sys.argv
    
    # Initialize LLM configuration
    try:
        config = LLMConfig(use_azure=use_azure)
        config.print_config()
    except ValueError as e:
        print(f"❌ Error: {e}")
        return
    
    # Simple sentiment classification example
    sentence = "it's a charming and often affecting journey."
    
    try:
        classify = dspy.Predict('sentence -> sentiment: bool')
        sentiment = classify(sentence=sentence).sentiment
        
        print(f"📝 Sentence: {sentence}")
        print(f"😊 Sentiment: {sentiment}")
        
    except Exception as e:
        print(f"❌ Error during classification: {e}")
        print("This might be due to:")
        print("- Invalid API key")
        print("- Network connectivity issues")
        print("- Azure deployment not accessible")
        print("- Rate limiting")

if __name__ == "__main__":
    print("🎯 DSPy Simple Example")
    print("=" * 30)
    main()