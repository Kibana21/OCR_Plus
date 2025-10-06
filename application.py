"""
Main Application class for OCR document processing system
"""

import os
import json
import time
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from core.base_classes import DocumentType, ProcessingResult, DocumentMetadata
from core.exceptions import OCRProcessingError, ConfigurationError
from processors import ProcessorFactory
from extractors import ExtractorFactory
from config import ConfigurationManager


class OCRApplication:
    """Main application class that orchestrates the entire OCR processing system"""
    
    def __init__(self, use_azure: bool = False, config_file: Optional[str] = None):
        """
        Initialize the OCR application
        
        Args:
            use_azure: Whether to use Azure OpenAI
            config_file: Optional path to configuration file
        """
        self.use_azure = use_azure
        self.config_manager = ConfigurationManager(use_azure=use_azure, config_file=config_file)
        self.processor_factory = ProcessorFactory()
        self.extractor_factory = ExtractorFactory(
            api_key=self.config_manager.get_api_key(),
            use_azure=use_azure
        )
        
        # Processing statistics
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'processing_time': 0.0
        }
    
    def process_single_document(self, 
                              file_path: str, 
                              document_type: str = "auto",
                              extraction_method: str = "auto",
                              save_results: bool = True,
                              include_page_by_page: bool = False) -> ProcessingResult:
        """
        Process a single document
        
        Args:
            file_path: Path to the document file
            document_type: Type of document (auto, pdf, image, html)
            extraction_method: Extraction method to use
            save_results: Whether to save results to file
            include_page_by_page: Whether to also do page-by-page extraction
            
        Returns:
            ProcessingResult object with extraction results
        """
        start_time = time.time()
        
        try:
            print(f"🚀 Processing document: {Path(file_path).name}")
            
            # Validate file exists
            if not Path(file_path).exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Get document metadata
            metadata = self._get_document_metadata(file_path)
            
            # Create appropriate processor
            processor = self.processor_factory.create_processor(file_path)
            
            # Process document
            processed_doc = processor.process_document(file_path)
            
            # Create appropriate extractor
            extractor = self.extractor_factory.create_extractor(extraction_method)
            
            # Extract data
            extracted_data = extractor.extract_data(processed_doc, document_type)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Create result
            result = ProcessingResult(
                success=True,
                document_metadata=metadata,
                extracted_data=extracted_data,
                processing_time=processing_time,
                processing_method=extraction_method
            )
            
            # Do page-by-page extraction if requested and document supports it
            page_by_page_result = None
            if include_page_by_page and metadata.file_type in [DocumentType.PDF, DocumentType.HTML]:
                print(f"📄 Starting page-by-page extraction...")
                page_by_page_result = self._process_page_by_page(file_path, document_type, extractor)
                
                if page_by_page_result and page_by_page_result.get('success'):
                    print(f"✅ Page-by-page extraction completed")
                    
                    # Save page-by-page results
                    if save_results:
                        page_output_path = self._generate_page_by_page_output_path(file_path)
                        self._save_page_by_page_results(page_output_path, page_by_page_result)
                else:
                    print(f"⚠️  Page-by-page extraction failed or not available")
            
            # Save results if requested
            if save_results:
                self._save_results(file_path, result)
            
            # Update statistics
            self._update_stats(True, processing_time)
            
            print(f"✅ Successfully processed {Path(file_path).name} in {processing_time:.2f}s")
            
            # Add page-by-page result to the main result
            if page_by_page_result:
                result.page_by_page_result = page_by_page_result
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            self._update_stats(False, processing_time)
            
            print(f"❌ Failed to process {Path(file_path).name}: {str(e)}")
            
            return ProcessingResult(
                success=False,
                document_metadata=self._get_document_metadata(file_path),
                extracted_data={},
                processing_time=processing_time,
                error_message=str(e),
                processing_method=extraction_method
            )
        
        finally:
            # Cleanup processor resources
            if 'processor' in locals():
                processor.cleanup()
    
    def process_batch(self, 
                     file_paths: List[str], 
                     document_types: Union[str, List[str]] = "auto",
                     extraction_method: str = "auto",
                     save_results: bool = True,
                     include_page_by_page: bool = False) -> List[ProcessingResult]:
        """
        Process multiple documents in batch
        
        Args:
            file_paths: List of file paths to process
            document_types: Document types (single or list)
            extraction_method: Extraction method to use
            save_results: Whether to save results to files
            include_page_by_page: Whether to also do page-by-page extraction
            
        Returns:
            List of ProcessingResult objects
        """
        print(f"🚀 Starting batch processing of {len(file_paths)} documents")
        print("=" * 60)
        
        results = []
        
        # Handle single vs multiple document types
        if isinstance(document_types, str):
            document_types = [document_types] * len(file_paths)
        
        for i, file_path in enumerate(file_paths):
            doc_type = document_types[i] if i < len(document_types) else "auto"
            
            print(f"\n[{i+1}/{len(file_paths)}] Processing: {Path(file_path).name}")
            
            result = self.process_single_document(
                file_path=file_path,
                document_type=doc_type,
                extraction_method=extraction_method,
                save_results=save_results,
                include_page_by_page=include_page_by_page
            )
            
            results.append(result)
            
            if result.success:
                print(f"✅ Success!")
            else:
                print(f"❌ Failed: {result.error_message}")
        
        # Generate batch summary
        self._print_batch_summary(results)
        
        return results
    
    def process_directory(self, 
                         directory_path: str,
                         recursive: bool = True,
                         document_types: Union[str, List[str]] = "auto",
                         extraction_method: str = "auto",
                         save_results: bool = True,
                         include_page_by_page: bool = False) -> List[ProcessingResult]:
        """
        Process all supported documents in a directory
        
        Args:
            directory_path: Path to directory to process
            recursive: Whether to process subdirectories recursively
            document_types: Document types to process
            extraction_method: Extraction method to use
            save_results: Whether to save results to files
            include_page_by_page: Whether to also do page-by-page extraction
            
        Returns:
            List of ProcessingResult objects
        """
        directory = Path(directory_path)
        
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        # Find all supported files
        file_paths = self._find_supported_files(directory, recursive)
        
        if not file_paths:
            print(f"❌ No supported documents found in {directory_path}")
            return []
        
        print(f"📄 Found {len(file_paths)} documents to process")
        
        return self.process_batch(
            file_paths=file_paths,
            document_types=document_types,
            extraction_method=extraction_method,
            save_results=save_results,
            include_page_by_page=include_page_by_page
        )
    
    def _get_document_metadata(self, file_path: str) -> DocumentMetadata:
        """Get metadata for a document"""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Determine file type
        extension = path.suffix.lower().lstrip('.')
        if extension == 'pdf':
            file_type = DocumentType.PDF
        elif extension in ['jpg', 'jpeg', 'png', 'bmp', 'tiff']:
            file_type = DocumentType.IMAGE
        elif extension in ['html', 'htm']:
            file_type = DocumentType.HTML
        else:
            file_type = DocumentType.UNKNOWN
        
        return DocumentMetadata(
            file_path=str(path),
            file_size=path.stat().st_size,
            file_type=file_type,
            created_at=str(path.stat().st_ctime),
            modified_at=str(path.stat().st_mtime)
        )
    
    def _find_supported_files(self, directory: Path, recursive: bool = True) -> List[str]:
        """Find all supported files in directory"""
        supported_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.html', '.htm'}
        
        if recursive:
            pattern = "**/*"
        else:
            pattern = "*"
        
        files = []
        for file_path in directory.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                files.append(str(file_path))
        
        return sorted(files)
    
    def _save_results(self, file_path: str, result: ProcessingResult) -> None:
        """Save processing results to file"""
        try:
            output_path = self._generate_output_path(file_path)
            
            # Prepare data for saving
            save_data = {
                'success': result.success,
                'document_metadata': {
                    'file_path': result.document_metadata.file_path,
                    'file_size': result.document_metadata.file_size,
                    'file_type': result.document_metadata.file_type.value,
                    'total_pages': result.document_metadata.total_pages,
                    'has_images': result.document_metadata.has_images,
                    'text_length': result.document_metadata.text_length
                },
                'extracted_data': result.extracted_data,
                'processing_time': result.processing_time,
                'processing_method': result.processing_method,
                'confidence_score': result.confidence_score,
                'error_message': result.error_message
            }
            
            with open(output_path, 'w') as f:
                json.dump(save_data, f, indent=2)
            
            print(f"💾 Results saved to: {output_path.name}")
            
        except Exception as e:
            print(f"⚠️  Failed to save results: {e}")
    
    def _generate_output_path(self, file_path: str) -> Path:
        """Generate output file path"""
        path = Path(file_path)
        output_name = f"{path.stem}_extracted_data.json"
        return path.parent / output_name
    
    def _generate_page_by_page_output_path(self, file_path: str) -> Path:
        """Generate page-by-page output file path"""
        path = Path(file_path)
        output_name = f"{path.stem}_page_by_page_data.json"
        return path.parent / output_name
    
    def _process_page_by_page(self, file_path: str, document_type: str, extractor) -> Dict[str, Any]:
        """Process document page by page"""
        try:
            return extractor.extract_page_by_page(file_path, document_type)
        except Exception as e:
            print(f"⚠️  Page-by-page processing failed: {e}")
            return None
    
    def _save_page_by_page_results(self, output_path: Path, result: Dict[str, Any]) -> None:
        """Save page-by-page processing results to file"""
        try:
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2)
            
            print(f"💾 Page-by-page results saved to: {output_path.name}")
            
        except Exception as e:
            print(f"⚠️  Failed to save page-by-page results: {e}")
    
    def _update_stats(self, success: bool, processing_time: float) -> None:
        """Update processing statistics"""
        self.stats['total_processed'] += 1
        self.stats['processing_time'] += processing_time
        
        if success:
            self.stats['successful'] += 1
        else:
            self.stats['failed'] += 1
    
    def _print_batch_summary(self, results: List[ProcessingResult]) -> None:
        """Print batch processing summary"""
        total = len(results)
        successful = sum(1 for r in results if r.success)
        failed = total - successful
        success_rate = (successful / total * 100) if total > 0 else 0
        total_time = sum(r.processing_time for r in results)
        
        print("\n" + "=" * 60)
        print("📊 BATCH PROCESSING SUMMARY")
        print("=" * 60)
        print(f"📄 Total Documents: {total}")
        print(f"✅ Processed Successfully: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print(f"⏱️  Total Processing Time: {total_time:.2f}s")
        print(f"⚡ Average Time per Document: {total_time/total:.2f}s")
        print("=" * 60)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return self.stats.copy()
    
    def reset_statistics(self) -> None:
        """Reset processing statistics"""
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'processing_time': 0.0
        }
    
    def cleanup(self) -> None:
        """Clean up resources"""
        # Cleanup any remaining resources
        pass
