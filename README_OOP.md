# OCR Document Processing System - Object-Oriented Architecture

## Overview

This project has been restructured with a proper object-oriented design following SOLID principles and design patterns. The new architecture provides better maintainability, extensibility, and testability.

## New Architecture

### Core Components

#### 1. Core Module (`core/`)
- **Base Classes**: Abstract base classes for processors, extractors, and configuration managers
- **Interfaces**: Well-defined interfaces for all major components
- **Exceptions**: Custom exception hierarchy for better error handling
- **Data Models**: Structured data models for results and metadata

#### 2. Processors Module (`processors/`)
- **PDFProcessor**: Specialized PDF document processing
- **ImageProcessor**: Image document processing with OCR
- **HTMLProcessor**: HTML document processing with embedded image extraction
- **ProcessorFactory**: Factory pattern for creating appropriate processors

#### 3. Extractors Module (`extractors/`)
- **Extraction Strategies**: Strategy pattern for different extraction methods
  - `NaturalExtractionStrategy`: Natural DSPy extraction
  - `ChainOfThoughtExtractionStrategy`: Chain-of-thought reasoning
  - `AutoExtractionStrategy`: Automatic strategy selection
- **ExtractorFactory**: Factory pattern for creating extractors

#### 4. Configuration Module (`config.py`)
- **ConfigurationManager**: Centralized configuration management
- Support for both OpenAI and Azure OpenAI
- Environment variable and file-based configuration

#### 5. Application Module (`application.py`)
- **OCRApplication**: Main application class that orchestrates everything
- Batch processing capabilities
- Statistics tracking
- Result management

## Key Design Patterns Used

### 1. Factory Pattern
- `ProcessorFactory`: Creates appropriate document processors based on file type
- `ExtractorFactory`: Creates appropriate data extractors based on extraction method

### 2. Strategy Pattern
- Different extraction strategies can be selected at runtime
- Easy to add new extraction methods without modifying existing code

### 3. Template Method Pattern
- Base classes define the overall structure while allowing subclasses to customize specific steps

### 4. Composition over Inheritance
- Components are composed together rather than relying heavily on inheritance
- Better flexibility and testability

## Usage

### New Entry Points

#### Single Document Processing
```bash
# Process a single document
python main_new.py document.pdf

# Use Azure OpenAI
python main_new.py --azure document.pdf

# Use specific extraction method
python main_new.py --method chain_of_thought document.pdf

# Use custom configuration
python main_new.py --config config.env document.pdf
```

#### Batch Processing
```bash
# Process all documents in data folder
python batch_processor_new.py --azure

# Process specific directory
python batch_processor_new.py /path/to/documents

# Use specific extraction method
python batch_processor_new.py --method natural data/

# Process without saving results
python batch_processor_new.py --no-save data/
```

### Programmatic Usage

```python
from application import OCRApplication

# Initialize application
app = OCRApplication(use_azure=True)

# Process single document
result = app.process_single_document(
    file_path="document.pdf",
    document_type="auto",
    extraction_method="auto"
)

# Process batch
results = app.process_batch([
    "doc1.pdf",
    "doc2.jpg",
    "doc3.html"
])

# Process directory
results = app.process_directory(
    directory_path="data/",
    recursive=True,
    extraction_method="chain_of_thought"
)
```

## Benefits of New Architecture

### 1. **Maintainability**
- Clear separation of concerns
- Each class has a single responsibility
- Easy to locate and fix issues

### 2. **Extensibility**
- Easy to add new document types by creating new processors
- Easy to add new extraction methods by creating new strategies
- Factory patterns allow runtime selection of components

### 3. **Testability**
- Each component can be tested independently
- Dependency injection makes mocking easier
- Clear interfaces make unit testing straightforward

### 4. **Reusability**
- Components can be reused in different contexts
- Base classes provide common functionality
- Factory patterns enable flexible component creation

### 5. **Error Handling**
- Custom exception hierarchy provides better error context
- Graceful degradation when components fail
- Comprehensive error reporting

## Migration from Old Structure

The old files are still available for backward compatibility, but the new OOP structure is recommended for:

- **New projects**: Use `main_new.py` and `batch_processor_new.py`
- **Existing projects**: Gradually migrate to the new structure
- **Custom implementations**: Extend the base classes and interfaces

## File Structure

```
OCR_Stuff/
├── core/                          # Core components
│   ├── __init__.py
│   ├── base_classes.py            # Base classes and data models
│   ├── interfaces.py              # Interface definitions
│   └── exceptions.py              # Custom exceptions
├── processors/                     # Document processors
│   ├── __init__.py
│   ├── processor_factory.py       # Factory for processors
│   ├── pdf_processor.py          # PDF processing
│   ├── image_processor.py        # Image processing
│   └── html_processor.py         # HTML processing
├── extractors/                    # Data extractors
│   ├── __init__.py
│   ├── extractor_factory.py      # Factory for extractors
│   └── extraction_strategies.py  # Extraction strategies
├── application.py                 # Main application class
├── config.py                     # Configuration management
├── main_new.py                   # New main entry point
├── batch_processor_new.py        # New batch processor
└── README_OOP.md                 # This documentation
```

## Configuration

### Environment Variables

#### OpenAI
```bash
export OPENAI_API_KEY="your-openai-api-key"
```

#### Azure OpenAI
```bash
export AZURE_OPENAI_API_KEY="your-azure-api-key"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_DEPLOYMENT_NAME="your-deployment-name"
export AZURE_OPENAI_API_VERSION="2024-02-15-preview"
```

### Configuration File
Create a `.env` file:
```
OPENAI_API_KEY=your-key-here
# or
AZURE_OPENAI_API_KEY=your-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

## Future Enhancements

The new architecture makes it easy to add:

1. **New Document Types**: Create new processor classes
2. **New Extraction Methods**: Create new strategy classes
3. **Custom Processing Pipelines**: Compose existing components
4. **Advanced Error Handling**: Extend exception hierarchy
5. **Performance Monitoring**: Add metrics collection
6. **Caching**: Add result caching mechanisms
7. **Parallel Processing**: Add concurrent processing capabilities

## Testing

The new structure enables comprehensive testing:

```python
# Test individual components
from processors import PDFProcessor
from extractors import ExtractorFactory

# Test processors
processor = PDFProcessor()
result = processor.process_document("test.pdf")

# Test extractors
factory = ExtractorFactory(api_key="test-key")
extractor = factory.create_extractor("natural")
```

This object-oriented architecture provides a solid foundation for the OCR document processing system while maintaining backward compatibility with the existing codebase.



python batch_processor_new.py --azure --page-by-page
kartik