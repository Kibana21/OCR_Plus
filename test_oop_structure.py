"""
Simple test script to verify the OOP structure works
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_core_imports():
    """Test core module imports"""
    try:
        from core.base_classes import DocumentType, ProcessingResult, DocumentMetadata
        from core.interfaces import IDocumentProcessor, IDataExtractor
        from core.exceptions import OCRProcessingError, ConfigurationError
        print("✅ Core module imports successful")
        return True
    except Exception as e:
        print(f"❌ Core module import failed: {e}")
        return False

def test_config_import():
    """Test configuration manager import"""
    try:
        from config import ConfigurationManager
        print("✅ Configuration manager import successful")
        return True
    except Exception as e:
        print(f"❌ Configuration manager import failed: {e}")
        return False

def test_factory_patterns():
    """Test factory pattern imports"""
    try:
        from processors.processor_factory import ProcessorFactory
        from extractors.extractor_factory import ExtractorFactory
        print("✅ Factory pattern imports successful")
        return True
    except Exception as e:
        print(f"❌ Factory pattern import failed: {e}")
        return False

def test_data_models():
    """Test data models"""
    try:
        from core.base_classes import DocumentType, ProcessingResult, DocumentMetadata
        
        # Test DocumentType enum
        assert DocumentType.PDF.value == "pdf"
        assert DocumentType.IMAGE.value == "image"
        assert DocumentType.HTML.value == "html"
        
        # Test DocumentMetadata creation
        metadata = DocumentMetadata(
            file_path="test.pdf",
            file_size=1024,
            file_type=DocumentType.PDF
        )
        assert metadata.file_path == "test.pdf"
        assert metadata.file_size == 1024
        
        print("✅ Data models working correctly")
        return True
    except Exception as e:
        print(f"❌ Data models test failed: {e}")
        return False

def test_factory_functionality():
    """Test factory functionality"""
    try:
        from processors.processor_factory import ProcessorFactory
        
        # Test supported formats
        formats = ProcessorFactory.get_supported_formats()
        assert DocumentType.PDF in formats
        assert DocumentType.IMAGE in formats
        assert DocumentType.HTML in formats
        
        # Test format checking
        assert ProcessorFactory.is_supported_format("test.pdf") == True
        assert ProcessorFactory.is_supported_format("test.txt") == False
        
        print("✅ Factory functionality working correctly")
        return True
    except Exception as e:
        print(f"❌ Factory functionality test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing OOP Structure")
    print("=" * 40)
    
    tests = [
        test_core_imports,
        test_config_import,
        test_factory_patterns,
        test_data_models,
        test_factory_functionality
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 40)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! OOP structure is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
