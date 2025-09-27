# Natural DSPy Data Extractor

A clean, generalized data extraction system using DSPy for PDF and image documents. **No structured prompting** - pure DSPy natural extraction.

## 🎯 Core Philosophy

- **Natural DSPy Extraction**: Let DSPy handle the reasoning naturally
- **No Structured Prompting**: Avoid rigid schemas and templates
- **Page-by-Page Processing**: Extract data from each page individually
- **Vision-Enhanced**: Leverage GPT-4o for visual document analysis

## 📁 Clean Project Structure

```
OCR_Stuff/
├── data/
│   └── report.pdf (your document)
├── temp_images/ (generated page images)
├── document_processor.py (PDF/image processing)
├── dspy_extractors.py (natural DSPy modules)
├── page_by_page_extractor.py (page-by-page extraction)
├── data_extractor.py (main orchestrator)
├── main.py (clean demo script)
├── requirements.txt (dependencies)
└── README.md (this file)
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

3. **Run extraction**:
   ```bash
   python main.py
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
