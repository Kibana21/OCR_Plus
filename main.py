"""
Natural DSPy Data Extractor - Clean and Simple
"""

import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

from data_extractor import DataExtractor
from llm_config import LLMConfig

def main(file_path: str = None, use_azure: bool = False):
    """Main function demonstrating natural DSPy extraction"""
    
    # Initialize LLM configuration
    try:
        llm_config = LLMConfig(use_azure=use_azure)
        api_key = llm_config.get_api_key()
        llm_config.print_config()
    except ValueError as e:
        print(f"❌ Error: {e}")
        return
    
    # Get file path from argument or use default
    if file_path is None:
        file_path = "data/report.pdf"  # Default file
    
    if not Path(file_path).exists():
        print(f"❌ Error: Document not found at {file_path}")
        return
    
    # Initialize the data extractor
    print("🚀 Initializing Natural DSPy Data Extractor...")
    extractor = DataExtractor(
        api_key=api_key,
        model_name="openai/gpt-4o-mini",
        use_vision=True,
        extraction_method="auto",
        use_azure=use_azure
    )
    
    print(f"📄 Extracting data from: {file_path}")
    print("=" * 60)
    
    try:
        # Extract data using natural DSPy extraction
        result = extractor.extract_from_file(
            file_path=file_path,
            document_type="auto"  # Let DSPy auto-detect
        )
        
        # Display results
        if result["success"]:
            print("✅ Natural DSPy extraction successful!")
            print(f"📊 Document Type: {result['document_type']}")
            print(f"📁 File: {result['file_path']}")
            
            # Show extracted data structure
            extracted_data = result["extracted_data"]
            print(f"\n📋 Extracted Data Structure:")
            if isinstance(extracted_data, dict):
                for key, value in extracted_data.items():
                    if isinstance(value, dict):
                        print(f"  {key}: {len(value)} fields")
                    elif isinstance(value, list):
                        print(f"  {key}: {len(value)} items")
                    else:
                        print(f"  {key}: {str(value)[:50]}...")
            
            # Save results
            file_stem = Path(file_path).stem
            output_file = f"{file_stem}_natural_extraction_results.json"
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\n💾 Results saved to: {output_file}")
            
        else:
            print("❌ Extraction failed!")
            print(f"Error: {result['error']}")
    
    except Exception as e:
        print(f"❌ An error occurred: {str(e)}")
    
    finally:
        # Cleanup
        extractor.cleanup()
        print("\n🧹 Cleanup completed.")

def test_page_by_page(file_path: str = None, use_azure: bool = False):
    """Test page-by-page extraction"""
    
    print("\n🔍 Testing Page-by-Page Extraction")
    print("=" * 50)
    
    # Initialize LLM configuration
    try:
        llm_config = LLMConfig(use_azure=use_azure)
        api_key = llm_config.get_api_key()
    except ValueError as e:
        print(f"❌ Error: {e}")
        return
    
    # Get file path from argument or use default
    if file_path is None:
        file_path = "data/report.pdf"  # Default file
    
    if not Path(file_path).exists():
        print(f"❌ Error: Document not found at {file_path}")
        return
    
    extractor = DataExtractor(api_key=api_key, extraction_method="auto", use_azure=use_azure)
    
    try:
        # Test page-by-page extraction
        result = extractor.extract_page_by_page(file_path, "auto")
        
        if result["success"]:
            print(f"✅ Page-by-page extraction successful!")
            print(f"📄 Processed {result['total_pages']} pages")
            
            # Show page results
            for page_result in result["page_results"]:
                page_num = page_result["page_number"]
                success = "✅" if page_result["success"] else "❌"
                confidence = page_result.get("confidence", 0)
                print(f"  Page {page_num}: {success} (confidence: {confidence:.2f})")
            
            # Save results
            file_stem = Path(file_path).stem
            output_file = f"{file_stem}_page_by_page_results.json"
            with open(output_file, "w") as f:
                json.dump(result, f, indent=2)
            print(f"\n💾 Page-by-page results saved to: {output_file}")
            
        else:
            print(f"❌ Page-by-page extraction failed: {result['error']}")
    
    except Exception as e:
        print(f"❌ Error in page-by-page extraction: {e}")
    
    finally:
        extractor.cleanup()

def show_usage():
    """Show usage information"""
    print("🎯 Natural DSPy Data Extractor")
    print("=" * 60)
    print("Usage:")
    print("  python main.py [file_path]")
    print("")
    print("Examples:")
    print("  python main.py                           # Use default file (data/report.pdf)")
    print("  python main.py data/AF22KB1231.pdf      # Extract from specific file")
    print("  python main.py data/invoice.pdf         # Extract from invoice")
    print("  python main.py data/receipt.jpg         # Extract from image")
    print("")
    print("Supported formats: PDF, JPG, JPEG, PNG, BMP, TIFF")
    print("=" * 60)

if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help', 'help']:
            show_usage()
            sys.exit(0)
        else:
            file_path = sys.argv[1]
    else:
        file_path = None  # Use default
    
    # Check for Azure flag
    use_azure = "--azure" in sys.argv or "--use-azure" in sys.argv
    
    print("🎯 Natural DSPy Data Extractor")
    print("=" * 60)
    print("✨ No structured prompting - Pure DSPy natural extraction")
    if use_azure:
        print("🔵 Using Azure OpenAI")
    else:
        print("🔵 Using OpenAI")
    print("=" * 60)
    
    # Run main extraction
    main(file_path, use_azure=use_azure)
    
    # Test page-by-page extraction
    test_page_by_page(file_path, use_azure=use_azure)
    
    print("\n🎉 All tests completed!")
    print("📁 Check the generated JSON files for results")