"""
Check if Azure Document Intelligence detects tilt/angle in your PDF
"""

import os
import sys
from dotenv import load_dotenv
from pdf_utils import ImagePreprocessor, AzureOCREngine


def check_pdf_tilt(pdf_path: str):
    """Check what angle/tilt Azure detects in the PDF"""

    load_dotenv()

    azure_endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
    azure_key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")

    if not azure_endpoint or not azure_key:
        raise ValueError("Missing Azure credentials")

    # Load images
    images = ImagePreprocessor.pdf_to_images(pdf_path, dpi=350)

    ocr_engine = AzureOCREngine(azure_endpoint, azure_key)

    print(f"Analyzing tilt/angle for: {pdf_path}")
    print("=" * 80)

    for page_num, image in enumerate(images, start=1):
        print(f"\nPage {page_num}:")

        # Do minimal preprocessing
        gray = ImagePreprocessor.grayscale(image)

        # Run OCR to get Azure's angle detection
        azure_angle = ocr_engine.get_page_angle(gray)

        print(f"  Azure detected angle: {azure_angle}°")

        if abs(azure_angle) > 1.0:
            print(f"  ⚠️  Significant tilt detected!")
            if abs(azure_angle) > 10:
                print(f"  ⚠️  SEVERE tilt (>10°) - consider rotating image")
        else:
            print(f"  ✓  No significant tilt (< 1°)")

    print("\n" + "=" * 80)
    print("\n📊 What does the angle mean?")
    print("  - 0°: Document is perfectly aligned")
    print("  - < 5°: Slight tilt, usually acceptable")
    print("  - 5-15°: Moderate tilt, may affect quality")
    print("  - > 15°: Severe tilt, should be corrected")
    print("\nNote: This is different from 90°/180°/270° rotation!")
    print("  - Angle = clockwise tilt/skew of text lines")
    print("  - Rotation = page orientation (portrait vs landscape)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_tilt.py <pdf_path>")
        print("\nExample: python check_tilt.py data/data1.pdf")
        sys.exit(1)

    check_pdf_tilt(sys.argv[1])
