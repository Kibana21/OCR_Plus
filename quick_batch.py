"""
Quick Batch Processor - Simple version for fast processing
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from data_extractor import DataExtractor
from llm_config import LLMConfig

def quick_batch_process(data_folder: str = "data", use_azure: bool = False):
    """Quickly process all documents in data folder"""
    
    # Initialize LLM configuration
    try:
        llm_config = LLMConfig(use_azure=use_azure)
        api_key = llm_config.get_api_key()
    except ValueError as e:
        print(f"❌ Error: {e}")
        return
    
    # Initialize extractor
    extractor = DataExtractor(api_key=api_key, extraction_method="auto", use_azure=use_azure)
    
    # Find all documents
    data_path = Path(data_folder)
    supported_formats = ['.pdf', '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.html', '.htm']
    
    documents = []
    for file_path in data_path.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in supported_formats:
            documents.append(file_path)
    
    print(f"🚀 Found {len(documents)} documents to process")
    
    # Process each document
    for i, doc_path in enumerate(documents, 1):
        print(f"\n[{i}/{len(documents)}] Processing: {doc_path.name}")
        
        try:
            # Extract data
            result = extractor.extract_from_file(str(doc_path), "auto")
            
            if result["success"]:
                # Save results in same folder
                output_file = doc_path.parent / f"{doc_path.stem}_extracted.json"
                
                with open(output_file, 'w') as f:
                    json.dump(result, f, indent=2)
                
                print(f"✅ Saved: {output_file.name}")
            else:
                print(f"❌ Failed: {result['error']}")
        
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    extractor.cleanup()
    print("\n🎉 Quick batch processing completed!")

if __name__ == "__main__":
    import sys
    
    # Check for Azure flag first
    use_azure = "--azure" in sys.argv or "--use-azure" in sys.argv
    
    # Filter out flags to get the data folder
    non_flag_args = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
    
    if non_flag_args:
        data_folder = non_flag_args[0]
    else:
        data_folder = "data"
    
    quick_batch_process(data_folder, use_azure=use_azure)