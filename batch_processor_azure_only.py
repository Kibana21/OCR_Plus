"""
Simple Batch Processor - Azure Only
Uses ONLY Azure Document Intelligence for all tilt/rotation detection
NO OpenCV orientation methods

Usage:
    python batch_processor_azure_only.py --azure
    python batch_processor_azure_only.py --azure --tilt-threshold 3
    python batch_processor_azure_only.py --azure --page-by-page
"""

import sys
import argparse
import json
from pathlib import Path

from core.exceptions import ConfigurationError, OCRProcessingError
from config import ConfigurationManager
from extractors import ExtractorFactory

# Import Azure-only processors
from processors.pdf_processor_azure_only import PDFProcessorAzureOnly
from processors.image_processor_azure_only import ImageProcessorAzureOnly


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Batch OCR Processing - Azure Only (Simple & Clean)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage (default threshold 5°)
  python batch_processor_azure_only.py --azure

  # Correct slight tilts (threshold 3°)
  python batch_processor_azure_only.py --azure --tilt-threshold 3

  # With page-by-page extraction
  python batch_processor_azure_only.py --azure --page-by-page

  # Specific folder
  python batch_processor_azure_only.py data/folder1 --azure
        """
    )

    parser.add_argument(
        'data_folder',
        nargs='?',
        default='data',
        help='Path to data folder (default: data)'
    )

    parser.add_argument(
        '--azure',
        action='store_true',
        required=True,
        help='Use Azure OpenAI (required)'
    )

    parser.add_argument(
        '--tilt-threshold',
        type=float,
        default=5.0,
        help='Minimum tilt angle to correct in degrees (default: 5.0)'
    )

    parser.add_argument(
        '--no-page-by-page',
        action='store_true',
        help='Disable page-by-page extraction (enabled by default for PDFs)'
    )

    parser.add_argument(
        '--method',
        choices=['auto', 'natural', 'chain_of_thought'],
        default='auto',
        help='Extraction method (default: auto)'
    )

    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Do not save results'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Verbose output'
    )

    parser.add_argument(
        '--save-ground-truth',
        action='store_true',
        help='Save full Azure Document Intelligence output as ground truth for DSPy experiments'
    )

    parser.add_argument(
        '--dpi',
        type=int,
        default=300,
        help='DPI for PDF to image conversion (default: 300 for high quality)'
    )

    return parser


def process_directory(data_folder: Path, args) -> list:
    """Process all documents in directory"""

    # Find supported files
    supported_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
    files = []

    for file_path in data_folder.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
            files.append(file_path)

    if not files:
        print(f"❌ No supported documents found in {data_folder}")
        print(f"   Supported: PDF, JPG, PNG, BMP, TIFF")
        return []

    print(f"\n📄 Found {len(files)} documents")
    print("=" * 80)

    # Initialize configuration and extractors
    config_manager = ConfigurationManager(use_azure=True)

    if not config_manager.validate_configuration():
        raise ConfigurationError("Invalid Azure configuration")

    extractor_factory = ExtractorFactory(
        api_key=config_manager.get_api_key(),
        use_azure=True
    )

    # Process each file
    results = []

    for i, file_path in enumerate(files, 1):
        print(f"\n[{i}/{len(files)}] {file_path.name}")
        print("-" * 80)

        try:
            # Create appropriate processor
            if file_path.suffix.lower() == '.pdf':
                processor = PDFProcessorAzureOnly(
                    tilt_threshold=args.tilt_threshold,
                    save_ground_truth=args.save_ground_truth,
                    dpi=args.dpi
                )
            else:
                processor = ImageProcessorAzureOnly(
                    tilt_threshold=args.tilt_threshold,
                    save_ground_truth=args.save_ground_truth
                )

            # Process document
            processed_doc = processor.process_document(str(file_path))

            # Extract data
            extractor = extractor_factory.create_extractor(args.method)
            extracted_data = extractor.extract_data(processed_doc, 'auto')

            # Page-by-page (enabled by default for PDFs, unless --no-page-by-page)
            page_by_page_result = None
            enable_page_by_page = not args.no_page_by_page  # Enabled by default
            if enable_page_by_page and file_path.suffix.lower() == '.pdf':
                print(f"\n📄 Page-by-page extraction...")
                # Use Azure-specific page-by-page extractor (no re-processing!)
                from extractors.page_by_page_extractor_azure import PageByPageExtractorAzure

                pbp_extractor = PageByPageExtractorAzure(
                    api_key=config_manager.get_api_key(),
                    use_azure=True
                )

                # Extract using ALREADY PROCESSED images (no OpenCV re-processing)
                page_by_page_result = pbp_extractor.extract_page_by_page_from_processed(
                    processed_doc, str(file_path), 'auto'
                )

            # Save results
            if not args.no_save:
                # Main extraction
                output_file = file_path.parent / f"{file_path.stem}_extracted.json"
                with open(output_file, 'w') as f:
                    json.dump({
                        'file': str(file_path),
                        'extracted_data': extracted_data,
                        'metadata': processed_doc.get('metadata', {})
                    }, f, indent=2)

                print(f"\n💾 Saved: {output_file.name}")

                # Page-by-page if applicable
                if page_by_page_result:
                    pbp_file = file_path.parent / f"{file_path.stem}_page_by_page.json"
                    with open(pbp_file, 'w') as f:
                        json.dump(page_by_page_result, f, indent=2)
                    print(f"💾 Saved: {pbp_file.name}")

            results.append({
                'file': str(file_path),
                'success': True,
                'corrections': processed_doc.get('metadata', {}).get('corrections_summary', {})
            })

            print(f"\n✅ Success")

        except Exception as e:
            print(f"\n❌ Failed: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()

            results.append({
                'file': str(file_path),
                'success': False,
                'error': str(e)
            })

    return results


def print_summary(results: list, data_folder: Path):
    """Print processing summary"""
    total = len(results)
    successful = sum(1 for r in results if r['success'])
    failed = total - successful

    print("\n" + "=" * 80)
    print("📊 BATCH PROCESSING SUMMARY")
    print("=" * 80)
    print(f"Folder: {data_folder}")
    print(f"Total files: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success rate: {(successful/total*100):.1f}%")

    # Correction statistics
    total_pages = 0
    corrected_pages = 0

    for result in results:
        if result['success'] and 'corrections' in result:
            corrections = result['corrections']
            if corrections:
                total_pages += corrections.get('total_pages', 0)
                corrected_pages += corrections.get('corrected_pages', 0)

    if total_pages > 0:
        print(f"\n📐 Correction Statistics:")
        print(f"Total pages: {total_pages}")
        print(f"Pages corrected: {corrected_pages}")
        print(f"Correction rate: {(corrected_pages/total_pages*100):.1f}%")

    print("=" * 80)


def main():
    """Main function"""
    parser = create_parser()
    args = parser.parse_args()

    # Print header
    print("🚀 Azure-Only Batch Processor")
    print("=" * 80)
    print("✨ Simple & Clean - No OpenCV Enhancement")
    print(f"📁 Folder: {args.data_folder}")
    print(f"🔵 Tilt Threshold: {args.tilt_threshold}°")
    print(f"📄 Page-by-Page: {'Disabled' if args.no_page_by_page else 'Enabled (default)'}")
    print(f"🔧 Method: {args.method}")
    print("=" * 80)

    try:
        # Validate folder
        data_folder = Path(args.data_folder)
        if not data_folder.exists():
            print(f"❌ Folder not found: {data_folder}")
            return 1

        # Process
        results = process_directory(data_folder, args)

        if not results:
            return 1

        # Print summary
        print_summary(results, data_folder)

        # Save batch summary
        if not args.no_save:
            summary_file = Path("batch_summary_azure.json")
            with open(summary_file, 'w') as f:
                json.dump({
                    'folder': str(data_folder),
                    'threshold': args.tilt_threshold,
                    'results': results
                }, f, indent=2)
            print(f"\n💾 Batch summary: {summary_file}")

        print("\n🎉 Processing complete!")
        return 0

    except ConfigurationError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\nRequired environment variables:")
        print("  AZURE_OPENAI_API_KEY")
        print("  AZURE_OPENAI_ENDPOINT")
        print("  AZURE_OPENAI_DEPLOYMENT_NAME")
        print("  AZURE_OPENAI_API_VERSION")
        print("  AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
        print("  AZURE_DOCUMENT_INTELLIGENCE_KEY")
        return 1

    except Exception as e:
        print(f"\n❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
