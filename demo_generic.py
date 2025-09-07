"""
Demo: Show the system works with any document type - no hardcoding!
"""

import os
from dotenv import load_dotenv
from data_extractor import DataExtractor

def demo_generic_extraction():
    """Demonstrate generic extraction for any document type"""
    
    print("🎯 Demo: Generic DSPy Extraction - No Hardcoding!")
    print("=" * 60)
    
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        return
    
    extractor = DataExtractor(api_key=api_key, extraction_method="auto")
    
    # Test with different document types
    test_cases = [
        ("data/report.pdf", "auto", "Any PDF document"),
        ("data/report.pdf", "document", "Generic document type"),
        ("data/report.pdf", "simple_document", "Simple document type")
    ]
    
    for file_path, doc_type, description in test_cases:
        print(f"\n📄 Testing: {description}")
        print(f"   File: {file_path}")
        print(f"   Type: {doc_type}")
        print("-" * 40)
        
        try:
            result = extractor.extract_from_file(file_path, doc_type)
            
            if result["success"]:
                print(f"✅ Success!")
                print(f"   Detected type: {result['document_type']}")
                print(f"   Extracted fields: {len(result['extracted_data'])}")
                
                # Show what DSPy naturally extracted
                for key, value in result["extracted_data"].items():
                    if isinstance(value, dict):
                        print(f"   {key}: {len(value)} fields")
                    elif isinstance(value, list):
                        print(f"   {key}: {len(value)} items")
                    else:
                        print(f"   {key}: {str(value)[:30]}...")
            else:
                print(f"❌ Failed: {result['error']}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n💡 Key Points:")
    print(f"  ✅ No hardcoded document types")
    print(f"  ✅ DSPy figures out content naturally")
    print(f"  ✅ Works with any PDF/image document")
    print(f"  ✅ Generic 'document' type for everything")
    print(f"  ✅ Auto-detection based on content")
    
    extractor.cleanup()

if __name__ == "__main__":
    demo_generic_extraction()
