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
    """Enhanced Azure Document Intelligence wrapper for tilt detection and ground truth"""

    def __init__(self, endpoint: str, key: str, save_ground_truth: bool = False):
        self.client = DocumentIntelligenceClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(key)
        )
        self.save_ground_truth = save_ground_truth

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

    def analyze_document_full(self, image: np.ndarray, page_num: int = 1) -> dict:
        """
        Get FULL Azure Document Intelligence response for ground truth

        Returns complete structured output including:
        - Full text content
        - Word-level data with confidence scores
        - Bounding boxes (polygons)
        - Line and paragraph grouping

        Args:
            image: Input image as numpy array
            page_num: Page number for metadata

        Returns:
            Dictionary with complete Azure response
        """

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

        # Convert result to dict (handles Azure SDK objects)
        return self._azure_result_to_dict(result, page_num)

    def _azure_result_to_dict(self, result, page_num: int) -> dict:
        """Convert Azure SDK result to JSON-serializable dict"""
        output = {
            'page_number': page_num,
            'api_version': getattr(result, 'api_version', None),
            'model_id': getattr(result, 'model_id', None),
            'content': getattr(result, 'content', ''),
            'pages': [],
            'paragraphs': [],
            'confidence_scores': []
        }

        # Extract pages
        if result.pages:
            for page in result.pages:
                page_data = {
                    'page_number': page.page_number,
                    'angle': getattr(page, 'angle', 0.0),
                    'width': page.width,
                    'height': page.height,
                    'unit': page.unit,
                    'words': [],
                    'lines': []
                }

                # Extract words with confidence and bounding boxes
                if hasattr(page, 'words') and page.words:
                    for word in page.words:
                        word_data = {
                            'content': word.content,
                            'confidence': getattr(word, 'confidence', 0.0),
                            'polygon': word.polygon if hasattr(word, 'polygon') else [],
                            'span': {
                                'offset': word.span.offset,
                                'length': word.span.length
                            } if hasattr(word, 'span') else None
                        }
                        page_data['words'].append(word_data)
                        output['confidence_scores'].append(word_data['confidence'])

                # Extract lines
                if hasattr(page, 'lines') and page.lines:
                    for line in page.lines:
                        line_data = {
                            'content': line.content,
                            'polygon': line.polygon if hasattr(line, 'polygon') else [],
                            'spans': [
                                {'offset': s.offset, 'length': s.length}
                                for s in line.spans
                            ] if hasattr(line, 'spans') else []
                        }
                        page_data['lines'].append(line_data)

                output['pages'].append(page_data)

        # Extract paragraphs (logical grouping)
        if hasattr(result, 'paragraphs') and result.paragraphs:
            for para in result.paragraphs:
                para_data = {
                    'content': para.content,
                    'bounding_regions': []
                }

                if hasattr(para, 'bounding_regions'):
                    for br in para.bounding_regions:
                        para_data['bounding_regions'].append({
                            'page_number': br.page_number,
                            'polygon': br.polygon
                        })

                output['paragraphs'].append(para_data)

        # Calculate average confidence
        if output['confidence_scores']:
            output['average_confidence'] = sum(output['confidence_scores']) / len(output['confidence_scores'])
        else:
            output['average_confidence'] = 0.0

        return output
