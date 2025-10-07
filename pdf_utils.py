"""
Simple PDF utilities for tilt detection
Minimal dependencies, focused on core functionality
"""

import cv2
import numpy as np
import fitz  # PyMuPDF
from typing import List, Tuple
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential


class ImagePreprocessor:
    """Minimal image preprocessing"""

    @staticmethod
    def pdf_to_images(pdf_path: str, dpi: int = 350) -> List[np.ndarray]:
        """Convert PDF pages to images at specified DPI using PyMuPDF"""
        doc = fitz.open(pdf_path)
        images = []

        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)

        for page_num in range(len(doc)):
            page = doc[page_num]
            pix = page.get_pixmap(matrix=mat)

            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                pix.height, pix.width, pix.n
            )

            # Convert RGBA to RGB if necessary
            if pix.n == 4:
                img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
            elif pix.n == 1:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)

            images.append(img)

        doc.close()
        return images

    @staticmethod
    def grayscale(image: np.ndarray) -> np.ndarray:
        """Convert to grayscale"""
        if len(image.shape) == 3:
            return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        return image


class AzureOCREngine:
    """Minimal Azure Document Intelligence wrapper for tilt detection"""

    def __init__(self, endpoint: str, key: str):
        self.client = DocumentIntelligenceClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(key)
        )

    def get_page_angle(self, image: np.ndarray) -> float:
        """Get page angle from Azure Document Intelligence"""
        # Convert numpy array to bytes
        success, buffer = cv2.imencode('.png', image)
        if not success:
            raise ValueError("Failed to encode image")

        image_bytes = buffer.tobytes()

        # Call Azure Document Intelligence
        poller = self.client.begin_analyze_document(
            "prebuilt-read",
            analyze_request=image_bytes,
            content_type="application/octet-stream"
        )
        result = poller.result()

        # Get angle from first page
        if result.pages:
            return getattr(result.pages[0], 'angle', 0.0)

        return 0.0
