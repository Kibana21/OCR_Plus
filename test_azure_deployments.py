"""
Test different Azure OpenAI deployment names
"""

import os
from dotenv import load_dotenv
from llm_config import LLMConfig

def test_deployment_name(deployment_name):
    """Test a specific deployment name"""
    print(f"\n🧪 Testing deployment: {deployment_name}")
    print("-" * 40)
    
    try:
        # Temporarily set the deployment name
        os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"] = deployment_name
        
        # Test configuration
        config = LLMConfig(use_azure=True)
        config.print_config()
        
        # Test simple request
        import dspy
        classify = dspy.Predict('text -> sentiment: str')
        result = classify(text="Hello")
        
        print(f"✅ SUCCESS! Deployment '{deployment_name}' works!")
        print(f"Result: {result.sentiment}")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def main():
    """Test common deployment names"""
    print("🔧 Testing Azure OpenAI Deployment Names")
    print("=" * 50)
    
    # Common deployment names to try
    deployment_names = [
        "gpt-4o-mini",
        "gpt-4o", 
        "gpt-4",
        "gpt-35-turbo",
        "gpt-3.5-turbo",
        "text-davinci-003"
    ]
    
    successful_deployments = []
    
    for deployment in deployment_names:
        if test_deployment_name(deployment):
            successful_deployments.append(deployment)
    
    print(f"\n📊 Results Summary")
    print("=" * 30)
    if successful_deployments:
        print(f"✅ Working deployments: {', '.join(successful_deployments)}")
        print(f"\n💡 Update your .env file with:")
        print(f"AZURE_OPENAI_DEPLOYMENT_NAME={successful_deployments[0]}")
    else:
        print("❌ No working deployments found")
        print("\n🔧 Troubleshooting:")
        print("1. Check if your Azure OpenAI resource is active")
        print("2. Verify you have access to the resource")
        print("3. Check if any deployments exist in Azure portal")
        print("4. Ensure your API key is correct")

if __name__ == "__main__":
    main()
