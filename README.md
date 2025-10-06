# Enhanced Document Processing System

A comprehensive, enterprise-grade document processing system using DSPy for PDF, image, and HTML documents. Features a clean, modular architecture with advanced error handling and result management.

## 🎯 Core Philosophy

- **Clean Architecture**: Modular design with separation of concerns
- **Natural DSPy Extraction**: Let DSPy handle reasoning naturally
- **Comprehensive Error Handling**: Robust error recovery and validation
- **Standardized Results**: Consistent result formats across all components
- **Configuration Management**: Centralized, validated configuration
- **Vision-Enhanced**: Leverage GPT-4o for visual document analysis

## 📁 Enhanced Project Structure

```
OCR_Stuff/
├── data/                           # Document input folder
│   └── report.pdf (your documents)
├── temp_images/                    # Generated page images
├── config_manager.py              # Centralized configuration
├── result_manager.py              # Result handling & validation
├── document_processor.py          # Enhanced document processing
├── dspy_extractors.py             # DSPy extraction modules
├── page_by_page_extractor.py      # Page-by-page extraction
├── data_extractor.py              # Main extraction orchestrator
├── batch_processor.py             # Enhanced batch processing
├── example_usage.py               # Architecture examples
├── ARCHITECTURE.md                # Detailed architecture docs
├── requirements.txt               # Dependencies
└── README.md                      # This file
```

## 🚀 Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set API key**:
   ```bash
   echo "OPENAI_API_KEY=your_key_here" > .env
   ```

3. **Run batch processing**:
   ```bash
   python batch_processor.py
   ```

4. **Run examples**:
   ```bash
   python example_usage.py
   ```

5. **Show configuration**:
   ```bash
   python batch_processor.py --config
   ```

## 🏗️ Enhanced Architecture

The system has been restructured with a clean, modular architecture:

### **Configuration Management**
- **`ConfigManager`**: Centralized configuration with validation
- Environment variable support
- LLM provider selection (OpenAI/Azure)
- Processing parameter management

### **Result Management**
- **`ResultManager`**: Standardized result handling
- **`ExtractionResult`**: Individual document results
- **`BatchResult`**: Batch processing results
- Comprehensive validation and error handling

### **Document Processing**
- **`DocumentProcessor`**: Enhanced file processing
- Support for PDF, image, and HTML files
- Improved error handling and validation
- Image enhancement and OCR integration

### **Extraction System**
- **`DataExtractor`**: Main extraction orchestrator
- **`ExtractorFactory`**: Factory pattern for extractors
- Multiple extraction methods (natural, chain-of-thought, vision-enhanced)
- Automatic retry logic and timeout handling

### **Batch Processing**
- **`BatchProcessor`**: Enhanced batch processing
- Document discovery with validation
- Progress tracking and detailed reporting
- Comprehensive result aggregation

## 💻 Usage Examples

### **Basic Batch Processing**
```python
from config_manager import get_config
from batch_processor import BatchProcessor

# Initialize with default configuration
config = get_config()
processor = BatchProcessor(data_folder="data", config_manager=config)

# Process all documents
batch_result = processor.process_all()
print(f"Processed {batch_result.successful_documents}/{batch_result.total_documents} documents")
```

### **Custom Configuration**
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

### **Result Management**
```python
from result_manager import get_result_manager, ResultStatus

manager = get_result_manager()
result = manager.create_extraction_result(
    file_path="document.pdf",
    status=ResultStatus.SUCCESS,
    extracted_data={"amount": "$100.00"},
    metadata=ProcessingMetadata(processing_time_seconds=2.5)
)

output_file = manager.save_extraction_result(result)
```

## 🔧 Core Components

### **DocumentExtractionSignature**
```python
class DocumentExtractionSignature(dspy.Signature):
    document_text: str = dspy.InputField()
    document_images: str = dspy.InputField()
    extracted_data: str = dspy.OutputField()
```

### **NaturalDocumentExtractor**
- Pure DSPy extraction without structured prompting
- Natural reasoning and data extraction
- Works with any document type

### **ChainOfThoughtExtractor**
- Uses DSPy's ChainOfThought for complex reasoning
- Better for long documents with complex layouts

## 📊 Usage Examples

### **Basic Extraction**
```python
from data_extractor import DataExtractor

extractor = DataExtractor(use_vision=True)
result = extractor.extract_from_file("data/report.pdf")
print(result["extracted_data"])
```

### **Page-by-Page Extraction**
```python
result = extractor.extract_page_by_page("data/report.pdf")
for page_result in result["page_results"]:
    print(f"Page {page_result['page_number']}: {page_result['extracted_data']}")
```

### **Batch Processing**
```python
files = ["doc1.pdf", "doc2.jpg", "doc3.pdf"]
results = extractor.batch_extract(files)
```
kartik
## 🎨 Key Features

- ✅ **Natural DSPy Extraction**: No structured prompting
- ✅ **Page-by-Page Processing**: Individual page analysis
- ✅ **Vision Capabilities**: GPT-4o for visual analysis
- ✅ **PyMuPDF Integration**: Reliable PDF processing
- ✅ **Image Enhancement**: OpenCV for better quality
- ✅ **Clean Architecture**: Minimal, focused codebase

## 📋 Output Format

```json
{
  "success": true,
  "document_type": "document",
  "extracted_data": {
    "content": { ... },
    "metadata": { ... }
  },
  "metadata": {
    "total_pages": 8,
    "has_images": true,
    "extraction_method": "natural"
  }
}
```

## 🔍 What Makes This Different

1. **No Structured Prompting**: DSPy handles reasoning naturally
2. **Generalized Approach**: Works with any document type
3. **Page-by-Page Analysis**: Captures data from each page individually
4. **Clean Codebase**: Removed unnecessary complexity
5. **Vision-Enhanced**: Leverages GPT-4o capabilities

## 🛠️ Dependencies

- `dspy`: DSPy framework for natural extraction
- `PyMuPDF`: Reliable PDF processing (no poppler needed)
- `opencv-python`: Image enhancement
- `python-dotenv`: Environment variables
- `pydantic`: Data validation

## 💡 Benefits

- **Simpler**: No complex schemas or structured prompting
- **More Natural**: DSPy handles reasoning organically
- **Generalized**: Works with any document type
- **Reliable**: PyMuPDF for robust PDF processing
- **Complete**: Page-by-page extraction captures all data

The system now uses pure DSPy natural extraction without any structured prompting, making it more flexible and generalized for any document type!
