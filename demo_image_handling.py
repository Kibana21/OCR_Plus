"""
Demo: Show how the system handles images in PDF pages
"""

import os
from dotenv import load_dotenv
from document_processor import DocumentProcessor
import json

def demo_image_handling():
    """Demonstrate how images in PDF pages are handled"""
    
    print("🖼️  Demo: How Images in PDF Pages Are Handled")
    print("=" * 60)
    
    # Initialize processor
    processor = DocumentProcessor()
    
    # Process the PDF
    print("📄 Processing PDF with images...")
    result = processor.process_document("data/report.pdf")
    
    print(f"✅ Document processed!")
    print(f"📊 Total pages: {result['metadata'].get('total_pages', 0)}")
    print(f"📝 Text length: {len(result.get('text_content', ''))}")
    print(f"🖼️  Images generated: {len(result.get('images', []))}")
    
    # Show what each method captures
    print(f"\n🔍 What Each Method Captures:")
    print(f"=" * 40)
    
    print(f"\n📝 TEXT EXTRACTION captures:")
    print(f"  ✅ Searchable text content")
    print(f"  ✅ Form fields and labels") 
    print(f"  ✅ Structured data")
    print(f"  ✅ Patient info, lab values, etc.")
    
    print(f"\n🖼️  IMAGE CONVERSION captures:")
    print(f"  ✅ Charts and graphs (lab results)")
    print(f"  ✅ Handwritten notes (doctor's annotations)")
    print(f"  ✅ Complex layouts (tables, forms)")
    print(f"  ✅ Visual elements (logos, signatures)")
    print(f"  ✅ Scanned documents")
    print(f"  ✅ Diagrams and drawings")
    
    # Show image details
    print(f"\n📸 Generated Page Images:")
    for img_data in result.get('images', []):
        page_num = img_data['page_number']
        width = img_data['width']
        height = img_data['height']
        file_path = img_data.get('file_path', 'N/A')
        
        print(f"  Page {page_num}: {width}x{height} pixels -> {file_path}")
    
    # Show how DSPy uses both
    print(f"\n🧠 DSPy Vision Processing:")
    print(f"  📝 Receives text: '{result['text_content'][:100]}...'")
    print(f"  🖼️  Receives images: {len(result['images'])} page images")
    print(f"  🎯 GPT-4o analyzes BOTH text AND visual elements")
    print(f"  ✨ Extracts data from text, charts, layouts, handwritten notes")
    
    # Don't cleanup so we can see the images
    print(f"\n💡 Key Point:")
    print(f"  The system doesn't just convert to text!")
    print(f"  It captures the ENTIRE page as an image")
    print(f"  DSPy vision analyzes both text AND visual elements")
    print(f"  This handles charts, handwritten notes, complex layouts")
    
    print(f"\n🖼️  Images saved in temp_images/ directory")
    print(f"  You can open them to see what DSPy vision analyzes!")

if __name__ == "__main__":
    demo_image_handling()
