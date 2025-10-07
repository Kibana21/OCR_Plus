"""
Auto-correct Tilted PDFs Utility

Detects tilt using Azure Document Intelligence and corrects severe tilts,
saving corrected images with proper naming convention.

Features:
- Detects tilt severity (slight/moderate/severe)
- Auto-corrects severe tilts only (configurable threshold)
- Saves images as: {filename}_page{N}_tilt{angle}.png
- Batch processing support
- Summary report generation
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime

import cv2
import numpy as np
from dotenv import load_dotenv

from pdf_utils import ImagePreprocessor, AzureOCREngine


class TiltSeverity:
    """Tilt severity classification"""
    NONE = "none"           # 0-1 degrees
    SLIGHT = "slight"       # 1-5 degrees
    MODERATE = "moderate"   # 5-15 degrees
    SEVERE = "severe"       # >15 degrees or 90/180/270


class TiltCorrection:
    """Result of tilt correction for a page"""
    def __init__(self, page_num: int, original_angle: float,
                 corrected_angle: float, severity: str,
                 corrected: bool, output_path: str = None):
        self.page_num = page_num
        self.original_angle = original_angle
        self.corrected_angle = corrected_angle
        self.severity = severity
        self.corrected = corrected
        self.output_path = output_path


class TiltCorrector:
    """Auto-correct tilted PDF pages"""

    def __init__(self, azure_endpoint: str, azure_key: str):
        self.ocr_engine = AzureOCREngine(azure_endpoint, azure_key)

    @staticmethod
    def classify_tilt(angle: float) -> str:
        """Classify tilt severity"""
        abs_angle = abs(angle)

        # Check for rotation (90/180/270 degrees)
        if abs_angle in [90, 180, 270] or (abs_angle > 85 and abs_angle < 95):
            return TiltSeverity.SEVERE

        # Check for severe tilt
        if abs_angle > 15:
            return TiltSeverity.SEVERE
        elif abs_angle > 5:
            return TiltSeverity.MODERATE
        elif abs_angle > 1:
            return TiltSeverity.SLIGHT
        else:
            return TiltSeverity.NONE

    @staticmethod
    def should_correct(angle: float, threshold: str = TiltSeverity.SEVERE) -> bool:
        """Determine if correction is needed based on threshold"""
        severity = TiltCorrector.classify_tilt(angle)

        severity_levels = {
            TiltSeverity.NONE: 0,
            TiltSeverity.SLIGHT: 1,
            TiltSeverity.MODERATE: 2,
            TiltSeverity.SEVERE: 3
        }

        return severity_levels.get(severity, 0) >= severity_levels.get(threshold, 3)

    @staticmethod
    def correct_rotation(image: np.ndarray, angle: float) -> np.ndarray:
        """Correct image rotation based on angle"""
        # Handle 90-degree rotations
        if 85 < abs(angle) < 95:
            if angle > 0:
                return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
            else:
                return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)

        # Handle 180-degree rotation
        elif 175 < abs(angle) < 185:
            return cv2.rotate(image, cv2.ROTATE_180)

        # Handle arbitrary angle rotation (for tilts)
        else:
            h, w = image.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, -angle, 1.0)  # Negative to counter-rotate
            corrected = cv2.warpAffine(image, M, (w, h),
                                       flags=cv2.INTER_CUBIC,
                                       borderMode=cv2.BORDER_REPLICATE)
            return corrected

    def detect_tilt(self, image: np.ndarray) -> float:
        """Detect tilt angle using Azure OCR"""
        # Minimal preprocessing for detection
        gray = ImagePreprocessor.grayscale(image)

        # Get angle from Azure
        angle = self.ocr_engine.get_page_angle(gray)

        return angle

    def process_pdf(self, pdf_path: str, output_dir: str = "./corrected_images",
                    correction_threshold: str = TiltSeverity.SEVERE,
                    save_all: bool = False) -> List[TiltCorrection]:
        """
        Process PDF and auto-correct tilted pages

        Args:
            pdf_path: Path to PDF file
            output_dir: Directory to save corrected images
            correction_threshold: Minimum severity to trigger correction
                                (NONE, SLIGHT, MODERATE, SEVERE)
            save_all: Save all pages (not just corrected ones)

        Returns:
            List of TiltCorrection results
        """
        pdf_name = Path(pdf_path).stem
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Load PDF pages
        images = ImagePreprocessor.pdf_to_images(pdf_path, dpi=350)

        results = []

        print(f"Processing: {pdf_path}")
        print(f"Correction threshold: {correction_threshold}")
        print(f"Total pages: {len(images)}")
        print("=" * 80)

        for page_num, image in enumerate(images, start=1):
            print(f"\nPage {page_num}/{len(images)}:")

            # Detect tilt
            original_angle = self.detect_tilt(image)
            severity = self.classify_tilt(original_angle)

            print(f"  Detected angle: {original_angle}°")
            print(f"  Severity: {severity}")

            # Determine if correction needed
            needs_correction = self.should_correct(original_angle, correction_threshold)

            if needs_correction:
                print(f"  ✓ Correcting tilt...")

                # Correct rotation
                corrected_image = self.correct_rotation(image, original_angle)

                # Verify correction
                corrected_angle = self.detect_tilt(corrected_image)

                print(f"  After correction: {corrected_angle}°")

                # Save corrected image
                output_filename = f"{pdf_name}_page{page_num:03d}_corrected_from_{int(original_angle)}deg.png"
                output_file = output_path / output_filename

                cv2.imwrite(str(output_file), corrected_image)

                print(f"  Saved: {output_filename}")

                results.append(TiltCorrection(
                    page_num=page_num,
                    original_angle=original_angle,
                    corrected_angle=corrected_angle,
                    severity=severity,
                    corrected=True,
                    output_path=str(output_file)
                ))

            else:
                print(f"  → No correction needed (severity: {severity})")

                if save_all:
                    # Save original image
                    output_filename = f"{pdf_name}_page{page_num:03d}_original_{int(original_angle)}deg.png"
                    output_file = output_path / output_filename

                    cv2.imwrite(str(output_file), image)
                    print(f"  Saved: {output_filename}")

                    results.append(TiltCorrection(
                        page_num=page_num,
                        original_angle=original_angle,
                        corrected_angle=original_angle,
                        severity=severity,
                        corrected=False,
                        output_path=str(output_file)
                    ))
                else:
                    results.append(TiltCorrection(
                        page_num=page_num,
                        original_angle=original_angle,
                        corrected_angle=original_angle,
                        severity=severity,
                        corrected=False
                    ))

        return results

    def generate_report(self, results: List[TiltCorrection],
                       pdf_path: str, output_dir: str):
        """Generate summary report of corrections"""

        pdf_name = Path(pdf_path).stem
        output_path = Path(output_dir)

        # Statistics
        total_pages = len(results)
        corrected_pages = sum(1 for r in results if r.corrected)
        severe_tilts = sum(1 for r in results if r.severity == TiltSeverity.SEVERE)
        moderate_tilts = sum(1 for r in results if r.severity == TiltSeverity.MODERATE)
        slight_tilts = sum(1 for r in results if r.severity == TiltSeverity.SLIGHT)

        # Generate report
        report = {
            "source_pdf": str(pdf_path),
            "processed_at": datetime.now().isoformat(),
            "statistics": {
                "total_pages": total_pages,
                "corrected_pages": corrected_pages,
                "uncorrected_pages": total_pages - corrected_pages,
                "severe_tilts": severe_tilts,
                "moderate_tilts": moderate_tilts,
                "slight_tilts": slight_tilts
            },
            "pages": []
        }

        for result in results:
            page_info = {
                "page_number": result.page_num,
                "original_angle": result.original_angle,
                "corrected_angle": result.corrected_angle if result.corrected else None,
                "severity": result.severity,
                "corrected": result.corrected,
                "output_file": result.output_path
            }
            report["pages"].append(page_info)

        # Save JSON report
        report_file = output_path / f"{pdf_name}_correction_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        # Print summary
        print("\n" + "=" * 80)
        print("CORRECTION SUMMARY")
        print("=" * 80)
        print(f"\nSource PDF: {pdf_path}")
        print(f"Total pages: {total_pages}")
        print(f"Pages corrected: {corrected_pages}")
        print(f"Pages unchanged: {total_pages - corrected_pages}")
        print(f"\nTilt severity breakdown:")
        print(f"  Severe: {severe_tilts}")
        print(f"  Moderate: {moderate_tilts}")
        print(f"  Slight: {slight_tilts}")
        print(f"  None: {total_pages - severe_tilts - moderate_tilts - slight_tilts}")
        print(f"\n✓ Report saved: {report_file}")
        print(f"✓ Images saved to: {output_dir}")

        return report


def process_single_pdf(pdf_path: str, output_dir: str = "./corrected_images",
                      threshold: str = TiltSeverity.SEVERE,
                      save_all: bool = False):
    """Process a single PDF"""

    load_dotenv()

    azure_endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
    azure_key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")

    if not azure_endpoint or not azure_key:
        raise ValueError("Missing Azure credentials")

    corrector = TiltCorrector(azure_endpoint, azure_key)

    results = corrector.process_pdf(
        pdf_path,
        output_dir=output_dir,
        correction_threshold=threshold,
        save_all=save_all
    )

    corrector.generate_report(results, pdf_path, output_dir)


def process_batch(pdf_directory: str, output_base_dir: str = "./corrected_images",
                 threshold: str = TiltSeverity.SEVERE):
    """Process multiple PDFs in a directory"""

    load_dotenv()

    azure_endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
    azure_key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")

    if not azure_endpoint or not azure_key:
        raise ValueError("Missing Azure credentials")

    corrector = TiltCorrector(azure_endpoint, azure_key)

    pdf_dir = Path(pdf_directory)
    pdf_files = list(pdf_dir.glob("*.pdf"))

    print(f"Found {len(pdf_files)} PDF files")
    print("=" * 80)

    all_reports = []

    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"\n[{i}/{len(pdf_files)}] Processing: {pdf_path.name}")

        # Create output directory for this PDF
        output_dir = Path(output_base_dir) / pdf_path.stem

        try:
            results = corrector.process_pdf(
                str(pdf_path),
                output_dir=str(output_dir),
                correction_threshold=threshold
            )

            report = corrector.generate_report(results, str(pdf_path), str(output_dir))
            all_reports.append(report)

        except Exception as e:
            print(f"✗ Error processing {pdf_path.name}: {e}")
            continue

    # Save batch summary
    batch_summary = {
        "processed_at": datetime.now().isoformat(),
        "total_pdfs": len(pdf_files),
        "successful": len(all_reports),
        "failed": len(pdf_files) - len(all_reports),
        "reports": all_reports
    }

    summary_file = Path(output_base_dir) / "batch_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(batch_summary, f, indent=2)

    print("\n" + "=" * 80)
    print("BATCH PROCESSING COMPLETE")
    print("=" * 80)
    print(f"Total PDFs: {len(pdf_files)}")
    print(f"Successful: {len(all_reports)}")
    print(f"Failed: {len(pdf_files) - len(all_reports)}")
    print(f"\n✓ Batch summary: {summary_file}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Auto-correct Tilted PDFs Utility")
        print("=" * 80)
        print("\nUsage:")
        print("  Single PDF:")
        print("    python auto_correct_tilt.py <pdf_path> [output_dir] [options]")
        print("")
        print("  Batch processing:")
        print("    python auto_correct_tilt.py --batch <pdf_directory> [output_dir]")
        print("")
        print("Options:")
        print("  --threshold <level>   Correction threshold (SLIGHT, MODERATE, SEVERE)")
        print("                        Default: SEVERE (only fix severe tilts)")
        print("  --save-all           Save all pages, not just corrected ones")
        print("")
        print("Examples:")
        print("  # Correct only severe tilts")
        print("  python auto_correct_tilt.py data/tilted.pdf ./corrected")
        print("")
        print("  # Correct moderate and severe tilts")
        print("  python auto_correct_tilt.py data/tilted.pdf ./corrected --threshold MODERATE")
        print("")
        print("  # Save all pages (corrected and uncorrected)")
        print("  python auto_correct_tilt.py data/tilted.pdf ./corrected --save-all")
        print("")
        print("  # Batch process directory")
        print("  python auto_correct_tilt.py --batch ./pdfs ./corrected")
        sys.exit(1)

    # Parse arguments
    if sys.argv[1] == "--batch":
        if len(sys.argv) < 3:
            print("Error: Specify directory containing PDFs")
            sys.exit(1)

        pdf_dir = sys.argv[2]
        output_dir = sys.argv[3] if len(sys.argv) > 3 else "./corrected_images"

        # Parse threshold
        threshold = TiltSeverity.SEVERE
        if "--threshold" in sys.argv:
            idx = sys.argv.index("--threshold")
            if idx + 1 < len(sys.argv):
                threshold = sys.argv[idx + 1].lower()

        process_batch(pdf_dir, output_dir, threshold)

    else:
        pdf_path = sys.argv[1]
        output_dir = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else "./corrected_images"

        # Parse threshold
        threshold = TiltSeverity.SEVERE
        if "--threshold" in sys.argv:
            idx = sys.argv.index("--threshold")
            if idx + 1 < len(sys.argv):
                threshold = sys.argv[idx + 1].lower()

        # Parse save-all flag
        save_all = "--save-all" in sys.argv

        process_single_pdf(pdf_path, output_dir, threshold, save_all)
