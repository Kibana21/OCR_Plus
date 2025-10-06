"""
Result Management System
Handles consistent result formatting, validation, and output across the system
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ResultStatus(Enum):
    """Status enumeration for processing results"""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    PENDING = "pending"


@dataclass
class ProcessingMetadata:
    """Metadata for processing operations"""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    processing_time_seconds: float = 0.0
    extraction_method: str = "unknown"
    document_type: str = "unknown"
    file_size_bytes: int = 0
    page_count: int = 0
    confidence_score: float = 0.0
    error_message: Optional[str] = None


@dataclass
class ExtractionResult:
    """Standard result structure for extraction operations"""
    status: ResultStatus
    file_path: str
    extracted_data: Dict[str, Any]
    metadata: ProcessingMetadata
    error_details: Optional[Dict[str, Any]] = None
    page_results: Optional[List[Dict[str, Any]]] = None
    aggregated_data: Optional[Dict[str, Any]] = None


@dataclass
class BatchResult:
    """Result structure for batch processing operations"""
    batch_id: str
    total_documents: int
    successful_documents: int
    failed_documents: int
    processing_time_seconds: float
    start_time: str
    end_time: str
    results: List[ExtractionResult]
    summary: Dict[str, Any]


class ResultManager:
    """Manages result formatting, validation, and output"""
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize result manager
        
        Args:
            output_dir: Directory for saving result files
        """
        self.output_dir = Path(output_dir) if output_dir else Path.cwd()
        self.output_dir.mkdir(exist_ok=True)
    
    def create_extraction_result(self, 
                                file_path: str,
                                status: ResultStatus,
                                extracted_data: Dict[str, Any] = None,
                                metadata: ProcessingMetadata = None,
                                error_details: Dict[str, Any] = None,
                                page_results: List[Dict[str, Any]] = None,
                                aggregated_data: Dict[str, Any] = None) -> ExtractionResult:
        """
        Create a standardized extraction result
        
        Args:
            file_path: Path to the processed file
            status: Processing status
            extracted_data: Extracted data dictionary
            metadata: Processing metadata
            error_details: Error information if failed
            page_results: Page-by-page results if applicable
            aggregated_data: Aggregated data if applicable
            
        Returns:
            ExtractionResult object
        """
        if metadata is None:
            metadata = ProcessingMetadata()
        
        if extracted_data is None:
            extracted_data = {}
        
        return ExtractionResult(
            status=status,
            file_path=file_path,
            extracted_data=extracted_data,
            metadata=metadata,
            error_details=error_details,
            page_results=page_results,
            aggregated_data=aggregated_data
        )
    
    def create_batch_result(self,
                           batch_id: str,
                           results: List[ExtractionResult],
                           start_time: str,
                           end_time: str,
                           processing_time: float) -> BatchResult:
        """
        Create a standardized batch result
        
        Args:
            batch_id: Unique identifier for the batch
            results: List of extraction results
            start_time: Batch start time
            end_time: Batch end time
            processing_time: Total processing time
            
        Returns:
            BatchResult object
        """
        successful = sum(1 for r in results if r.status == ResultStatus.SUCCESS)
        failed = sum(1 for r in results if r.status == ResultStatus.FAILED)
        
        summary = self._generate_batch_summary(results)
        
        return BatchResult(
            batch_id=batch_id,
            total_documents=len(results),
            successful_documents=successful,
            failed_documents=failed,
            processing_time_seconds=processing_time,
            start_time=start_time,
            end_time=end_time,
            results=results,
            summary=summary
        )
    
    def _generate_batch_summary(self, results: List[ExtractionResult]) -> Dict[str, Any]:
        """Generate summary statistics for batch results"""
        if not results:
            return {"success_rate": 0.0, "total_pages": 0, "avg_confidence": 0.0}
        
        successful_results = [r for r in results if r.status == ResultStatus.SUCCESS]
        
        success_rate = len(successful_results) / len(results) * 100
        
        total_pages = sum(r.metadata.page_count for r in successful_results)
        
        avg_confidence = 0.0
        if successful_results:
            confidences = [r.metadata.confidence_score for r in successful_results if r.metadata.confidence_score > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Document type distribution
        doc_types = {}
        for result in successful_results:
            doc_type = result.metadata.document_type
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
        
        # Processing method distribution
        methods = {}
        for result in successful_results:
            method = result.metadata.extraction_method
            methods[method] = methods.get(method, 0) + 1
        
        return {
            "success_rate": round(success_rate, 2),
            "total_pages": total_pages,
            "avg_confidence": round(avg_confidence, 3),
            "document_types": doc_types,
            "extraction_methods": methods,
            "processing_stats": {
                "avg_processing_time": round(sum(r.metadata.processing_time_seconds for r in successful_results) / len(successful_results), 2) if successful_results else 0,
                "total_file_size": sum(r.metadata.file_size_bytes for r in successful_results)
            }
        }
    
    def save_extraction_result(self, 
                              result: ExtractionResult, 
                              output_path: Optional[str] = None,
                              format_type: str = "natural") -> Path:
        """
        Save extraction result to file
        
        Args:
            result: Extraction result to save
            output_path: Custom output path
            format_type: Type of extraction (natural, page_by_page, etc.)
            
        Returns:
            Path to saved file
        """
        if output_path is None:
            file_path = Path(result.file_path)
            base_name = file_path.stem
            
            if format_type == "natural":
                output_filename = f"{base_name}_extracted_data.json"
            elif format_type == "page_by_page":
                output_filename = f"{base_name}_page_by_page_data.json"
            else:
                output_filename = f"{base_name}_{format_type}_data.json"
            
            output_path = file_path.parent / output_filename
        
        # Convert result to dictionary
        result_dict = self._extract_result_to_dict(result)
        
        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, indent=2, ensure_ascii=False)
        
        return Path(output_path)
    
    def save_batch_result(self, 
                         batch_result: BatchResult, 
                         output_path: Optional[str] = None) -> Path:
        """
        Save batch result to file
        
        Args:
            batch_result: Batch result to save
            output_path: Custom output path
            
        Returns:
            Path to saved file
        """
        if output_path is None:
            output_path = self.output_dir / "batch_processing_results.json"
        
        # Convert result to dictionary
        result_dict = self._batch_result_to_dict(batch_result)
        
        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, indent=2, ensure_ascii=False)
        
        return Path(output_path)
    
    def _extract_result_to_dict(self, result: ExtractionResult) -> Dict[str, Any]:
        """Convert ExtractionResult to dictionary"""
        return {
            "success": result.status == ResultStatus.SUCCESS,
            "status": result.status.value,
            "file_path": result.file_path,
            "document_type": result.metadata.document_type,
            "extracted_data": result.extracted_data,
            "metadata": {
                "processing_info": {
                    "document_type": result.metadata.document_type,
                    "total_pages": result.metadata.page_count,
                    "text_length": len(str(result.extracted_data)),
                    "has_images": result.metadata.page_count > 0,
                    "file_size_bytes": result.metadata.file_size_bytes
                },
                "extraction_info": {
                    "method": result.metadata.extraction_method,
                    "confidence_score": result.metadata.confidence_score,
                    "processing_time_seconds": result.metadata.processing_time_seconds,
                    "timestamp": result.metadata.timestamp
                }
            },
            "error_details": result.error_details,
            "page_results": result.page_results,
            "aggregated_data": result.aggregated_data
        }
    
    def _batch_result_to_dict(self, batch_result: BatchResult) -> Dict[str, Any]:
        """Convert BatchResult to dictionary"""
        return {
            "batch_info": {
                "batch_id": batch_result.batch_id,
                "data_folder": str(self.output_dir),
                "total_documents": batch_result.total_documents,
                "processed_successfully": batch_result.successful_documents,
                "failed": batch_result.failed_documents,
                "success_rate": f"{batch_result.successful_documents / batch_result.total_documents * 100:.1f}%" if batch_result.total_documents > 0 else "0%",
                "processing_time_seconds": batch_result.processing_time_seconds,
                "start_time": batch_result.start_time,
                "end_time": batch_result.end_time
            },
            "summary": batch_result.summary,
            "results": [self._extract_result_to_dict(r) for r in batch_result.results]
        }
    
    def validate_result(self, result: Union[ExtractionResult, BatchResult]) -> Dict[str, Any]:
        """
        Validate result structure and content
        
        Args:
            result: Result to validate
            
        Returns:
            Validation result dictionary
        """
        validation = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        if isinstance(result, ExtractionResult):
            self._validate_extraction_result(result, validation)
        elif isinstance(result, BatchResult):
            self._validate_batch_result(result, validation)
        else:
            validation["valid"] = False
            validation["errors"].append("Unknown result type")
        
        return validation
    
    def _validate_extraction_result(self, result: ExtractionResult, validation: Dict[str, Any]):
        """Validate extraction result"""
        if not result.file_path:
            validation["errors"].append("Missing file path")
            validation["valid"] = False
        
        if result.status == ResultStatus.SUCCESS and not result.extracted_data:
            validation["warnings"].append("Successful result has no extracted data")
        
        if result.status == ResultStatus.FAILED and not result.error_details:
            validation["warnings"].append("Failed result has no error details")
        
        if result.metadata.confidence_score < 0 or result.metadata.confidence_score > 1:
            validation["errors"].append("Invalid confidence score")
            validation["valid"] = False
    
    def _validate_batch_result(self, result: BatchResult, validation: Dict[str, Any]):
        """Validate batch result"""
        if result.total_documents != len(result.results):
            validation["errors"].append("Total documents count mismatch")
            validation["valid"] = False
        
        if result.successful_documents + result.failed_documents != result.total_documents:
            validation["errors"].append("Success/failure count mismatch")
            validation["valid"] = False
        
        if result.processing_time_seconds < 0:
            validation["errors"].append("Invalid processing time")
            validation["valid"] = False
    
    def print_result_summary(self, result: Union[ExtractionResult, BatchResult]):
        """Print a formatted summary of the result"""
        if isinstance(result, ExtractionResult):
            self._print_extraction_summary(result)
        elif isinstance(result, BatchResult):
            self._print_batch_summary(result)
    
    def _print_extraction_summary(self, result: ExtractionResult):
        """Print extraction result summary"""
        print(f"\n📄 Extraction Result Summary")
        print("=" * 50)
        print(f"File: {result.file_path}")
        print(f"Status: {result.status.value.upper()}")
        print(f"Document Type: {result.metadata.document_type}")
        print(f"Processing Time: {result.metadata.processing_time_seconds:.2f}s")
        
        if result.status == ResultStatus.SUCCESS:
            print(f"Confidence: {result.metadata.confidence_score:.3f}")
            print(f"Pages: {result.metadata.page_count}")
            print(f"Data Fields: {len(result.extracted_data)}")
        else:
            print(f"Error: {result.error_details.get('message', 'Unknown error') if result.error_details else 'No error details'}")
    
    def _print_batch_summary(self, result: BatchResult):
        """Print batch result summary"""
        print(f"\n📊 Batch Processing Summary")
        print("=" * 60)
        print(f"Batch ID: {result.batch_id}")
        print(f"Total Documents: {result.total_documents}")
        print(f"✅ Successful: {result.successful_documents}")
        print(f"❌ Failed: {result.failed_documents}")
        print(f"📈 Success Rate: {result.summary['success_rate']:.1f}%")
        print(f"⏱️  Processing Time: {result.processing_time_seconds:.2f}s")
        print(f"📄 Total Pages: {result.summary['total_pages']}")
        print(f"🎯 Avg Confidence: {result.summary['avg_confidence']:.3f}")
        
        if result.summary.get('document_types'):
            print(f"\n📋 Document Types:")
            for doc_type, count in result.summary['document_types'].items():
                print(f"   {doc_type}: {count}")
        
        if result.summary.get('extraction_methods'):
            print(f"\n🔧 Extraction Methods:")
            for method, count in result.summary['extraction_methods'].items():
                print(f"   {method}: {count}")


# Global result manager instance
_global_result_manager = None


def get_result_manager() -> ResultManager:
    """Get the global result manager instance"""
    global _global_result_manager
    if _global_result_manager is None:
        _global_result_manager = ResultManager()
    return _global_result_manager


def set_result_manager(manager: ResultManager):
    """Set the global result manager instance"""
    global _global_result_manager
    _global_result_manager = manager


if __name__ == "__main__":
    """Test the result manager"""
    print("🧪 Testing Result Manager")
    print("=" * 50)
    
    manager = ResultManager()
    
    # Create test extraction result
    metadata = ProcessingMetadata(
        extraction_method="natural",
        document_type="invoice",
        page_count=2,
        confidence_score=0.95,
        processing_time_seconds=3.5
    )
    
    result = manager.create_extraction_result(
        file_path="test_document.pdf",
        status=ResultStatus.SUCCESS,
        extracted_data={"amount": "$100.00", "date": "2024-01-01"},
        metadata=metadata
    )
    
    # Validate and print
    validation = manager.validate_result(result)
    print(f"✅ Result valid: {validation['valid']}")
    
    if validation['errors']:
        print(f"❌ Errors: {validation['errors']}")
    
    if validation['warnings']:
        print(f"⚠️  Warnings: {validation['warnings']}")
    
    manager.print_result_summary(result)
