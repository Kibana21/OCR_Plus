# Enhanced Document Processing Architecture

This document describes the restructured class architecture for the OCR document processing system.

## Overview

The system has been restructured into a clean, modular architecture with proper separation of concerns, dependency injection, and comprehensive error handling.

## Core Components

### 1. Configuration Management (`config_manager.py`)

**`ConfigManager`** - Centralized configuration management
- Handles all system settings
- Supports environment variables and config files
- Provides validation and configuration info
- Manages LLM, processing, and extraction settings

**Key Features:**
- Environment variable loading
- Configuration validation
- LLM provider selection (OpenAI/Azure)
- Processing parameters management

### 2. Result Management (`result_manager.py`)

**`ResultManager`** - Standardized result handling
- Consistent result formatting across the system
- Result validation and error handling
- File output management
- Batch processing result aggregation

**Key Classes:**
- `ExtractionResult` - Individual document extraction results
- `BatchResult` - Batch processing results
- `ProcessingMetadata` - Processing information and metrics

### 3. Document Processing (`document_processor.py`)

**`DocumentProcessor`** - Enhanced document processing
- Supports PDF, image, and HTML files
- Improved error handling and validation
- Image enhancement and OCR integration
- Base64 image extraction from HTML

**Key Features:**
- File validation before processing
- Enhanced image quality processing
- Comprehensive error handling
- Temporary file management

### 4. DSPy Extractors (`dspy_extractors.py`)

**Extractor Architecture:**
- `BaseDocumentExtractor` - Abstract base class with retry logic
- `NaturalDocumentExtractor` - Direct extraction without structured prompting
- `ChainOfThoughtExtractor` - Step-by-step reasoning for complex documents
- `PageExtractor` - Page-specific extraction
- `VisionEnhancedExtractor` - Specialized for image-heavy documents
- `ExtractorFactory` - Factory pattern for extractor creation

**Key Features:**
- Automatic retry logic with validation
- Timeout handling
- Configurable extraction methods
- Result validation and error recovery

### 5. Data Extraction (`data_extractor.py`)

**`DataExtractor`** - Main extraction orchestrator
- Coordinates document processing and data extraction
- Supports multiple extraction methods
- Handles page-by-page extraction
- Provides comparison between extraction methods

**Key Features:**
- Method selection based on document characteristics
- Document type auto-detection
- Image preparation for DSPy processing
- Backward compatibility with legacy interface

### 6. Page-by-Page Extraction (`page_by_page_extractor.py`)

**`PageByPageExtractor`** - Detailed page analysis
- Processes each page individually
- Aggregates results from multiple pages
- Handles complex document structures
- Provides confidence scoring

### 7. Batch Processing (`batch_processor.py`)

**`BatchProcessor`** - Enhanced batch processing
- Recursive document discovery
- File validation and filtering
- Progress tracking and reporting
- Comprehensive result management

**Key Features:**
- Document discovery with validation
- Individual document processing
- Batch result aggregation
- Detailed progress reporting

## Architecture Benefits

### 1. **Separation of Concerns**
- Each class has a single, well-defined responsibility
- Clear interfaces between components
- Easy to test and maintain individual components

### 2. **Dependency Injection**
- Configuration and dependencies are injected rather than hardcoded
- Easy to swap implementations
- Better testability

### 3. **Error Handling**
- Comprehensive error handling at all levels
- Graceful degradation when components fail
- Detailed error reporting and logging

### 4. **Extensibility**
- Abstract base classes allow easy extension
- Factory patterns for flexible component creation
- Plugin-like architecture for new extractors

### 5. **Configuration Management**
- Centralized configuration with validation
- Environment variable support
- Runtime configuration updates

### 6. **Result Consistency**
- Standardized result formats across all components
- Comprehensive metadata tracking
- Validation and error reporting

## Usage Examples

### Basic Usage

```python
from config_manager import get_config
from batch_processor import BatchProcessor

# Initialize with default configuration
config = get_config()
processor = BatchProcessor(data_folder="data", config_manager=config)

# Process all documents
batch_result = processor.process_all()

# Print results
print(f"Processed {batch_result.successful_documents}/{batch_result.total_documents} documents")
```

### Custom Configuration

```python
from config_manager import ConfigManager
from data_extractor import DataExtractor

# Create custom configuration
config = ConfigManager()
config.extraction.extraction_method = "chain_of_thought"
config.processing.max_file_size_mb = 50

# Use custom extractor
extractor = DataExtractor(config_manager=config)
result = extractor.extract("document.pdf", "invoice")
```

### Result Management

```python
from result_manager import get_result_manager

manager = get_result_manager()

# Create extraction result
result = manager.create_extraction_result(
    file_path="document.pdf",
    status=ResultStatus.SUCCESS,
    extracted_data={"amount": "$100.00"},
    metadata=ProcessingMetadata(processing_time_seconds=2.5)
)

# Save result
output_file = manager.save_extraction_result(result)
```

## Migration Guide

### From Legacy to New Architecture

1. **Configuration**: Use `ConfigManager` instead of direct environment variable access
2. **Results**: Use `ResultManager` and `ExtractionResult` for consistent result handling
3. **Processing**: Use the new `DocumentProcessor.process()` method for enhanced processing
4. **Extraction**: Use `DataExtractor.extract()` for the new extraction interface
5. **Batch Processing**: Use `BatchProcessor.process_all()` for enhanced batch processing

### Backward Compatibility

The new architecture maintains backward compatibility through:
- Legacy method wrappers in `DataExtractor`
- Legacy format conversion in `BatchProcessor`
- Existing API preservation where possible

## Performance Improvements

1. **Parallel Processing**: Ready for future parallel processing implementation
2. **Caching**: Configuration and result caching capabilities
3. **Memory Management**: Better memory usage with lazy loading
4. **Error Recovery**: Faster recovery from transient errors
5. **Validation**: Early validation prevents unnecessary processing

## Future Enhancements

1. **Parallel Processing**: Multi-threaded document processing
2. **Caching**: Result and configuration caching
3. **Metrics**: Detailed performance metrics and monitoring
4. **Plugins**: Plugin system for custom extractors
5. **API**: REST API for remote processing
6. **Database**: Database storage for results and metadata
