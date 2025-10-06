#!/usr/bin/env python3
"""
Example usage of the enhanced document processing architecture
"""

import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from config_manager import get_config, ConfigManager
from data_extractor import DataExtractor
from batch_processor import BatchProcessor
from result_manager import get_result_manager, ResultStatus, ProcessingMetadata


def example_basic_usage():
    """Basic usage example"""
    print("🔧 Basic Usage Example")
    print("=" * 50)
    
    # Get default configuration
    config = get_config()
    config.print_config_summary()
    
    # Initialize extractor
    extractor = DataExtractor(config_manager=config)
    
    # Process a single document (if available)
    test_files = list(Path("data").glob("**/*.pdf"))[:1]  # Get first PDF
    
    if test_files:
        file_path = str(test_files[0])
        print(f"\n📄 Processing: {file_path}")
        
        result = extractor.extract(file_path)
        
        if result.status == ResultStatus.SUCCESS:
            print("✅ Extraction successful!")
            print(f"   Document type: {result.metadata.document_type}")
            print(f"   Processing time: {result.metadata.processing_time_seconds:.2f}s")
            print(f"   Confidence: {result.metadata.confidence_score:.3f}")
        else:
            print("❌ Extraction failed!")
            print(f"   Error: {result.error_details}")
    else:
        print("⚠️  No test files found in data/ directory")


def example_custom_configuration():
    """Custom configuration example"""
    print("\n🔧 Custom Configuration Example")
    print("=" * 50)
    
    # Create custom configuration
    config = ConfigManager()
    
    # Modify settings
    config.extraction.extraction_method = "chain_of_thought"
    config.extraction.max_retries = 5
    config.processing.max_file_size_mb = 25
    config.processing.enable_image_enhancement = True
    
    # Validate configuration
    validation = config.validate_config()
    print(f"Configuration valid: {validation['valid']}")
    
    if validation['warnings']:
        print(f"Warnings: {validation['warnings']}")
    
    # Use custom configuration
    extractor = DataExtractor(config_manager=config)
    print(f"Available extraction methods: {extractor.get_supported_methods()}")


def example_batch_processing():
    """Batch processing example"""
    print("\n🔧 Batch Processing Example")
    print("=" * 50)
    
    # Initialize batch processor
    config = get_config()
    processor = BatchProcessor(
        data_folder="data",
        config_manager=config,
        extraction_method="auto"
    )
    
    # Find documents
    documents = processor.find_documents()
    print(f"Found {len(documents)} documents to process")
    
    if documents:
        # Process first document as example
        doc = documents[0]
        print(f"\n📄 Processing example document: {doc.name}")
        
        result = processor.process_document(doc)
        
        if result.status == ResultStatus.SUCCESS:
            print("✅ Document processed successfully!")
        else:
            print("❌ Document processing failed!")
    else:
        print("⚠️  No documents found in data/ directory")


def example_result_management():
    """Result management example"""
    print("\n🔧 Result Management Example")
    print("=" * 50)
    
    # Get result manager
    manager = get_result_manager()
    
    # Create a sample result
    result = manager.create_extraction_result(
        file_path="example.pdf",
        status=ResultStatus.SUCCESS,
        extracted_data={
            "document_type": "invoice",
            "amount": "$150.00",
            "date": "2024-01-15",
            "vendor": "Example Corp"
        },
        metadata=ProcessingMetadata(
            processing_time_seconds=2.5,
            file_size_bytes=1024000,
            page_count=1,
            document_type="invoice",
            extraction_method="natural",
            confidence_score=0.95
        )
    )
    
    # Validate result
    validation = manager.validate_result(result)
    print(f"Result valid: {validation['valid']}")
    
    # Print result summary
    manager.print_result_summary(result)


def example_extractor_factory():
    """Extractor factory example"""
    print("\n🔧 Extractor Factory Example")
    print("=" * 50)
    
    from dspy_extractors import ExtractorFactory
    
    # Get available extractors
    available_extractors = ExtractorFactory.get_available_extractors()
    print(f"Available extractors: {available_extractors}")
    
    # Get information about each extractor
    for method in available_extractors:
        info = ExtractorFactory.get_extractor_info(method)
        print(f"\n{method}:")
        print(f"  Name: {info.get('name', 'Unknown')}")
        print(f"  Description: {info.get('description', 'No description')}")
        print(f"  Best for: {', '.join(info.get('best_for', []))}")
        print(f"  Performance: {info.get('performance', 'Unknown')}")
        print(f"  Accuracy: {info.get('accuracy', 'Unknown')}")


def main():
    """Run all examples"""
    print("🚀 Enhanced Document Processing Architecture Examples")
    print("=" * 60)
    
    try:
        # Run examples
        example_basic_usage()
        example_custom_configuration()
        example_batch_processing()
        example_result_management()
        example_extractor_factory()
        
        print("\n🎉 All examples completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
