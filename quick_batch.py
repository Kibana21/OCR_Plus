"""
Quick Batch Processor - Simple version for fast processing
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from data_extractor import DataExtractor

def quick_batch_process(data_folder: str = "data"):
    """Quickly process all documents in data folder"""
    
    # Load environment
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not set")
        return
    
    # Initialize extractor
    extractor = DataExtractor(api_key=api_key, extraction_method="auto")
    
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
    data_folder = sys.argv[1] if len(sys.argv) > 1 else "data"
    quick_batch_process(data_folder)