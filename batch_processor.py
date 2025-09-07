"""
Batch Document Processor
Recursively processes all documents in data folder and saves JSON results in the same folder
"""

import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv
from data_extractor import DataExtractor
from llm_config import LLMConfig

class BatchProcessor:
    """Process all documents in data folder recursively"""
    
    def __init__(self, data_folder: str = "data", use_azure: bool = False):
        self.data_folder = Path(data_folder)
        self.supported_formats = ['.pdf', '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.html', '.htm']
        self.processed_count = 0
        self.failed_count = 0
        self.results = []
        self.use_azure = use_azure
        
        # Initialize LLM configuration
        self.llm_config = LLMConfig(use_azure=use_azure)
        self.api_key = self.llm_config.get_api_key()
        
        # Initialize extractor
        self.extractor = DataExtractor(
            api_key=self.api_key,
            model_name="openai/gpt-4o-mini",
            use_vision=True,
            extraction_method="auto",
            use_azure=use_azure
        )
    
    def find_documents(self) -> list:
        """Find all supported documents recursively"""
        documents = []
        
        if not self.data_folder.exists():
            print(f"❌ Data folder not found: {self.data_folder}")
            return documents
        
        print(f"🔍 Scanning {self.data_folder} for documents...")
        
        # Recursively find all supported files
        for file_path in self.data_folder.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in self.supported_formats:
                documents.append(file_path)
        
        print(f"📄 Found {len(documents)} documents:")
        for doc in documents:
            relative_path = doc.relative_to(self.data_folder)
            print(f"  - {relative_path}")
        
        return documents
    
    def process_document(self, file_path: Path) -> dict:
        """Process a single document and save results"""
        try:
            print(f"\n📄 Processing: {file_path.name}")
            print(f"📁 Location: {file_path.parent.relative_to(self.data_folder)}")
            
            # Extract data
            result = self.extractor.extract_from_file(str(file_path), "auto")
            
            if result["success"]:
                # Generate output filename
                output_file = self._generate_output_filename(file_path, "natural")
                
                # Save natural extraction results
                with open(output_file, 'w') as f:
                    json.dump(result, f, indent=2)
                
                print(f"✅ Natural extraction: {output_file.name}")
                
                # Also do page-by-page extraction for PDFs and HTML files
                if file_path.suffix.lower() in ['.pdf', '.html', '.htm']:
                    page_result = self.extractor.extract_page_by_page(str(file_path), "auto")
                    
                    if page_result["success"]:
                        page_output_file = self._generate_output_filename(file_path, "page_by_page")
                        
                        with open(page_output_file, 'w') as f:
                            json.dump(page_result, f, indent=2)
                        
                        print(f"✅ Page-by-page extraction: {page_output_file.name}")
                        
                        return {
                            "success": True,
                            "file": str(file_path),
                            "natural_output": str(output_file),
                            "page_by_page_output": str(page_output_file),
                            "document_type": result["document_type"]
                        }
                
                return {
                    "success": True,
                    "file": str(file_path),
                    "natural_output": str(output_file),
                    "document_type": result["document_type"]
                }
            else:
                print(f"❌ Extraction failed: {result['error']}")
                return {
                    "success": False,
                    "file": str(file_path),
                    "error": result["error"]
                }
                
        except Exception as e:
            print(f"❌ Error processing {file_path.name}: {str(e)}")
            return {
                "success": False,
                "file": str(file_path),
                "error": str(e)
            }
    
    def _generate_output_filename(self, file_path: Path, extraction_type: str) -> Path:
        """Generate appropriate output filename"""
        # Get the base name without extension
        base_name = file_path.stem
        
        # Create output filename
        if extraction_type == "natural":
            output_name = f"{base_name}_extracted_data.json"
        elif extraction_type == "page_by_page":
            output_name = f"{base_name}_page_by_page_data.json"
        else:
            output_name = f"{base_name}_{extraction_type}.json"
        
        # Save in the same folder as the original file
        return file_path.parent / output_name
    
    def process_all(self) -> dict:
        """Process all documents in the data folder"""
        print("🚀 Starting Batch Document Processing")
        print("=" * 60)
        
        # Find all documents
        documents = self.find_documents()
        
        if not documents:
            print("❌ No documents found to process")
            return {"success": False, "message": "No documents found"}
        
        print(f"\n🔄 Processing {len(documents)} documents...")
        print("=" * 60)
        
        # Process each document
        for i, doc_path in enumerate(documents, 1):
            print(f"\n[{i}/{len(documents)}] Processing: {doc_path.name}")
            
            result = self.process_document(doc_path)
            self.results.append(result)
            
            if result["success"]:
                self.processed_count += 1
                print(f"✅ Success!")
            else:
                self.failed_count += 1
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
        
        # Generate summary
        summary = self._generate_summary()
        
        # Save batch results
        self._save_batch_results()
        
        return summary
    
    def _generate_summary(self) -> dict:
        """Generate processing summary"""
        total = len(self.results)
        success_rate = (self.processed_count / total * 100) if total > 0 else 0
        
        summary = {
            "success": True,
            "total_documents": total,
            "processed_successfully": self.processed_count,
            "failed": self.failed_count,
            "success_rate": f"{success_rate:.1f}%",
            "results": self.results
        }
        
        print("\n" + "=" * 60)
        print("📊 BATCH PROCESSING SUMMARY")
        print("=" * 60)
        print(f"📄 Total Documents: {total}")
        print(f"✅ Processed Successfully: {self.processed_count}")
        print(f"❌ Failed: {self.failed_count}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print("=" * 60)
        
        return summary
    
    def _save_batch_results(self):
        """Save batch processing results"""
        batch_results = {
            "batch_info": {
                "data_folder": str(self.data_folder),
                "total_documents": len(self.results),
                "processed_successfully": self.processed_count,
                "failed": self.failed_count,
                "success_rate": f"{(self.processed_count / len(self.results) * 100):.1f}%" if self.results else "0%"
            },
            "results": self.results
        }
        
        batch_file = Path("batch_processing_results.json")
        with open(batch_file, 'w') as f:
            json.dump(batch_results, f, indent=2)
        
        print(f"💾 Batch results saved to: {batch_file}")
    
    def cleanup(self):
        """Clean up resources"""
        self.extractor.cleanup()

def main():
    """Main function for batch processing"""
    # Check for Azure flag first
    use_azure = "--azure" in sys.argv or "--use-azure" in sys.argv
    
    # Filter out flags to get the data folder
    non_flag_args = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
    
    if non_flag_args:
        data_folder = non_flag_args[0]
    else:
        data_folder = "data"
    
    try:
        processor = BatchProcessor(data_folder, use_azure=use_azure)
        summary = processor.process_all()
        
        if summary["success"]:
            print("\n🎉 Batch processing completed successfully!")
        else:
            print(f"\n❌ Batch processing failed: {summary.get('message', 'Unknown error')}")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    finally:
        if 'processor' in locals():
            processor.cleanup()
        print("\n🧹 Cleanup completed.")

if __name__ == "__main__":
    main()