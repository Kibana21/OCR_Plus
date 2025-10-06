"""
Enhanced Batch Document Processor
Recursively processes all documents in data folder and saves JSON results with improved architecture
"""

import os
import json
import sys
import time
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        pass  # Fallback if dotenv is not available

from data_extractor import DataExtractor
from config_manager import get_config, ConfigManager
from result_manager import ResultManager, BatchResult, ExtractionResult, ResultStatus, ProcessingMetadata
from document_processor import DocumentProcessor


class BatchProcessor:
    """Enhanced batch processor for document processing with improved architecture"""
    
    def __init__(self, 
                 data_folder: str = "data", 
                 config_manager: Optional[ConfigManager] = None,
                 extraction_method: str = "auto"):
        """
        Initialize batch processor
        
        Args:
            data_folder: Path to data folder containing documents
            config_manager: Configuration manager instance
            extraction_method: Default extraction method to use
        """
        self.data_folder = Path(data_folder)
        self.config = config_manager or get_config()
        self.result_manager = ResultManager()
        
        # Initialize components
        self.document_processor = DocumentProcessor()
        self.extractor = DataExtractor(
            config_manager=self.config,
            extraction_method=extraction_method
        )
        
        # Batch processing state
        self.batch_id = str(uuid.uuid4())
        self.results: List[ExtractionResult] = []
        self.start_time: Optional[str] = None
        self.end_time: Optional[str] = None
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats"""
        return self.config.processing.supported_formats
    
    def find_documents(self) -> List[Path]:
        """Find all supported documents recursively with validation"""
        documents = []
        
        if not self.data_folder.exists():
            print(f"❌ Data folder not found: {self.data_folder}")
            return documents
        
        print(f"🔍 Scanning {self.data_folder} for documents...")
        
        supported_formats = self.get_supported_formats()
        
        # Recursively find all supported files
        for file_path in self.data_folder.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in supported_formats:
                # Validate file before adding
                validation = self.document_processor.validate_file(file_path)
                if validation["valid"]:
                    documents.append(file_path)
                else:
                    print(f"⚠️  Skipping invalid file {file_path}: {', '.join(validation['errors'])}")
        
        print(f"📄 Found {len(documents)} valid documents:")
        for doc in documents:
            relative_path = doc.relative_to(self.data_folder)
            print(f"  - {relative_path}")
        
        return documents
    
    def process_document(self, file_path: Path) -> ExtractionResult:
        """Process a single document and save results"""
        try:
            print(f"\n📄 Processing: {file_path.name}")
            print(f"📁 Location: {file_path.parent.relative_to(self.data_folder)}")
            
            # Extract data using the new extractor
            result = self.extractor.extract(str(file_path), "auto")
            
            if result.status == ResultStatus.SUCCESS:
                # Save natural extraction results
                output_file = self.result_manager.save_extraction_result(
                    result, 
                    format_type="natural"
                )
                print(f"✅ Natural extraction: {output_file.name}")
                
                # Also do page-by-page extraction for PDFs and HTML files
                if file_path.suffix.lower() in ['.pdf', '.html', '.htm']:
                    try:
                        page_result = self.extractor.extract_page_by_page(str(file_path), "auto")
                        
                        if page_result.status == ResultStatus.SUCCESS:
                            page_output_file = self.result_manager.save_extraction_result(
                                page_result,
                                format_type="page_by_page"
                            )
                            print(f"✅ Page-by-page extraction: {page_output_file.name}")
                            
                            # Update result with page-by-page information
                            result.page_results = page_result.page_results
                            result.aggregated_data = page_result.aggregated_data
                    except Exception as e:
                        print(f"⚠️  Page-by-page extraction failed: {e}")
                
                return result
            else:
                print(f"❌ Extraction failed: {result.error_details}")
                return result
                
        except Exception as e:
            print(f"❌ Error processing {file_path.name}: {str(e)}")
            return self.result_manager.create_extraction_result(
                file_path=str(file_path),
                status=ResultStatus.FAILED,
                metadata=ProcessingMetadata(
                    processing_time_seconds=0,
                    file_size_bytes=file_path.stat().st_size if file_path.exists() else 0,
                    error_message=str(e)
                ),
                error_details={"processing_error": str(e)}
            )
    
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
    
    def process_all(self) -> BatchResult:
        """Process all documents in the data folder"""
        print("🚀 Starting Enhanced Batch Document Processing")
        print("=" * 60)
        
        # Initialize batch processing
        self.start_time = time.strftime("%Y-%m-%d %H:%M:%S")
        start_timestamp = time.time()
        
        # Find all documents
        documents = self.find_documents()
        
        if not documents:
            print("❌ No documents found to process")
            self.end_time = time.strftime("%Y-%m-%d %H:%M:%S")
            return self.result_manager.create_batch_result(
                batch_id=self.batch_id,
                results=[],
                start_time=self.start_time,
                end_time=self.end_time,
                processing_time=time.time() - start_timestamp
            )
        
        print(f"\n🔄 Processing {len(documents)} documents...")
        print("=" * 60)
        
        # Process each document
        for i, doc_path in enumerate(documents, 1):
            print(f"\n[{i}/{len(documents)}] Processing: {doc_path.name}")
            
            result = self.process_document(doc_path)
            self.results.append(result)
            
            if result.status == ResultStatus.SUCCESS:
                print(f"✅ Success!")
            else:
                print(f"❌ Failed: {result.error_details}")
        
        # Finalize batch processing
        self.end_time = time.strftime("%Y-%m-%d %H:%M:%S")
        processing_time = time.time() - start_timestamp
        
        # Create batch result
        batch_result = self.result_manager.create_batch_result(
            batch_id=self.batch_id,
            results=self.results,
            start_time=self.start_time,
            end_time=self.end_time,
            processing_time=processing_time
        )
        
        # Save batch results
        self._save_batch_results(batch_result)
        
        # Print summary
        self.result_manager.print_result_summary(batch_result)
        
        return batch_result
    
    def _save_batch_results(self, batch_result: BatchResult):
        """Save batch processing results"""
        batch_file = self.result_manager.save_batch_result(batch_result)
        print(f"💾 Batch results saved to: {batch_file}")
    
    # Backward compatibility methods
    def process_all_legacy(self) -> dict:
        """Process all documents (backward compatibility)"""
        batch_result = self.process_all()
        
        # Convert to legacy format
        return {
            "success": batch_result.successful_documents > 0,
            "total_documents": batch_result.total_documents,
            "processed_successfully": batch_result.successful_documents,
            "failed": batch_result.failed_documents,
            "success_rate": f"{(batch_result.successful_documents / batch_result.total_documents * 100):.1f}%" if batch_result.total_documents > 0 else "0%",
            "results": [self._extract_result_to_legacy(r) for r in batch_result.results]
        }
    
    def _extract_result_to_legacy(self, result: ExtractionResult) -> dict:
        """Convert ExtractionResult to legacy format"""
        return {
            "success": result.status == ResultStatus.SUCCESS,
            "file": result.file_path,
            "document_type": result.metadata.document_type,
            "error": result.error_details.get("extraction_error") if result.error_details else None,
            "natural_output": f"{Path(result.file_path).stem}_extracted_data.json",
            "page_by_page_output": f"{Path(result.file_path).stem}_page_by_page_data.json" if result.page_results else None
        }
    
    def cleanup(self):
        """Clean up resources"""
        self.extractor.cleanup()

def main():
    """Main function for batch processing with enhanced architecture"""
    # Parse command line arguments
    use_azure = "--azure" in sys.argv or "--use-azure" in sys.argv
    show_config = "--config" in sys.argv
    
    # Filter out flags to get the data folder
    non_flag_args = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
    
    if non_flag_args:
        data_folder = non_flag_args[0]
    else:
        data_folder = "data"
    
    try:
        # Initialize configuration
        config = get_config()
        
        # Override Azure setting if --azure flag is used
        if use_azure:
            config.llm.use_azure = True
            # Reload environment config with Azure setting
            config._load_environment_config()
        
        # Show configuration if requested
        if show_config:
            config.print_config_summary()
            return
        
        # Validate configuration
        validation = config.validate_config()
        if not validation["valid"]:
            print(f"❌ Configuration validation failed: {validation['errors']}")
            return
        
        if validation["warnings"]:
            print(f"⚠️  Configuration warnings: {validation['warnings']}")
        
        # Initialize processor
        processor = BatchProcessor(
            data_folder=data_folder,
            config_manager=config,
            extraction_method="auto"
        )
        
        # Process all documents
        batch_result = processor.process_all()
        
        if batch_result.successful_documents > 0:
            print("\n🎉 Batch processing completed successfully!")
        else:
            print("\n❌ Batch processing failed - no documents were processed successfully")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        if 'processor' in locals():
            processor.cleanup()
        print("\n🧹 Cleanup completed.")

if __name__ == "__main__":
    main()