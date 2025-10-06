"""
New batch processor using proper OOP structure
"""

import sys
import argparse
from pathlib import Path

from application import OCRApplication
from core.exceptions import ConfigurationError, OCRProcessingError


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser for batch processing"""
    parser = argparse.ArgumentParser(
        description="Batch OCR Document Processing System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python batch_processor_new.py --azure                    # Process all documents with page-by-page (default)
  python batch_processor_new.py data/                     # Process all documents in data/
  python batch_processor_new.py --method chain_of_thought # Use specific extraction method
  python batch_processor_new.py --config config.env       # Use custom config file
  python batch_processor_new.py --no-save                 # Process without saving results
  python batch_processor_new.py --no-page-by-page         # Skip page-by-page extraction
        """
    )
    
    parser.add_argument(
        'data_folder',
        nargs='?',
        default='data',
        help='Path to data folder containing documents (default: data)'
    )
    
    parser.add_argument(
        '--azure',
        action='store_true',
        help='Use Azure OpenAI instead of regular OpenAI'
    )
    
    parser.add_argument(
        '--recursive',
        action='store_true',
        default=True,
        help='Process subdirectories recursively (default: True)'
    )
    
    parser.add_argument(
        '--method',
        choices=['auto', 'natural', 'chain_of_thought'],
        default='auto',
        help='Extraction method to use (default: auto)'
    )
    
    parser.add_argument(
        '--type',
        choices=['auto', 'pdf', 'image', 'html'],
        default='auto',
        help='Document type (default: auto)'
    )
    
    parser.add_argument(
        '--config',
        help='Path to configuration file (.env format)'
    )
    
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Do not save results to files'
    )
    
    parser.add_argument(
        '--no-page-by-page',
        action='store_true',
        help='Skip page-by-page extraction (page-by-page is enabled by default for PDFs and HTML)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--summary-only',
        action='store_true',
        help='Only show summary, not individual file processing'
    )
    
    return parser


def main():
    """Main function for batch processing using OOP structure"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Print header
    print("🚀 Batch OCR Document Processing System")
    print("=" * 60)
    print("✨ Object-Oriented Architecture")
    if args.azure:
        print("🔵 Using Azure OpenAI")
    else:
        print("🔵 Using OpenAI")
    print(f"📁 Data Folder: {args.data_folder}")
    print(f"🔧 Extraction Method: {args.method}")
    print(f"📄 Document Type: {args.type}")
    print(f"📄 Page-by-Page: {'Enabled (default)' if not args.no_page_by_page else 'Disabled'}")
    print("=" * 60)
    
    try:
        # Initialize application
        app = OCRApplication(
            use_azure=args.azure,
            config_file=args.config
        )
        
        # Print configuration
        app.config_manager.print_config()
        
        # Validate configuration
        if not app.config_manager.validate_configuration():
            raise ConfigurationError("Invalid configuration. Please check your API keys.")
        
        # Validate data folder
        data_folder = Path(args.data_folder)
        if not data_folder.exists():
            print(f"❌ Error: Data folder not found: {data_folder}")
            return 1
        
        if not data_folder.is_dir():
            print(f"❌ Error: Path is not a directory: {data_folder}")
            return 1
        
        # Process directory
        print(f"\n🔍 Scanning {data_folder} for documents...")
        
        results = app.process_directory(
            directory_path=str(data_folder),
            recursive=args.recursive,
            document_types=args.type,
            extraction_method=args.method,
            save_results=not args.no_save,
            include_page_by_page=not args.no_page_by_page  # Default to True, unless --no-page-by-page is used
        )
        
        if not results:
            print("❌ No supported documents found to process")
            print("Supported formats: PDF, JPG, JPEG, PNG, BMP, TIFF, HTML, HTM")
            return 1
        
        # Print detailed results if not summary-only
        if not args.summary_only:
            print("\n📋 Individual Results:")
            print("-" * 40)
            for i, result in enumerate(results, 1):
                status = "✅" if result.success else "❌"
                print(f"{i:2d}. {status} {Path(result.document_metadata.file_path).name}")
                if not result.success and args.verbose:
                    print(f"    Error: {result.error_message}")
        
        # Print final statistics
        stats = app.get_statistics()
        print(f"\n📊 Final Statistics:")
        print(f"   Total Processed: {stats['total_processed']}")
        print(f"   Successful: {stats['successful']}")
        print(f"   Failed: {stats['failed']}")
        print(f"   Success Rate: {(stats['successful']/stats['total_processed']*100):.1f}%")
        print(f"   Total Time: {stats['processing_time']:.2f}s")
        print(f"   Average Time: {stats['processing_time']/stats['total_processed']:.2f}s per document")
        
        # Save batch results
        if not args.no_save:
            batch_results_file = Path("batch_processing_results.json")
            batch_data = {
                'batch_info': {
                    'data_folder': str(data_folder),
                    'total_documents': stats['total_processed'],
                    'successful': stats['successful'],
                    'failed': stats['failed'],
                    'success_rate': f"{(stats['successful']/stats['total_processed']*100):.1f}%",
                    'total_time': stats['processing_time'],
                    'extraction_method': args.method,
                    'document_type': args.type
                },
                'results': [
                    {
                        'file_path': result.document_metadata.file_path,
                        'success': result.success,
                        'processing_time': result.processing_time,
                        'error_message': result.error_message
                    }
                    for result in results
                ]
            }
            
            import json
            with open(batch_results_file, 'w') as f:
                json.dump(batch_data, f, indent=2)
            
            print(f"\n💾 Batch results saved to: {batch_results_file}")
        
        print("\n🎉 Batch processing completed successfully!")
        return 0
        
    except ConfigurationError as e:
        print(f"❌ Configuration Error: {e}")
        print("\nPlease check your environment variables:")
        if args.azure:
            print("For Azure OpenAI: AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT_NAME, AZURE_OPENAI_API_VERSION")
        else:
            print("For OpenAI: OPENAI_API_KEY")
        return 1
        
    except OCRProcessingError as e:
        print(f"❌ Processing Error: {e}")
        return 1
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
        
    finally:
        # Cleanup
        if 'app' in locals():
            app.cleanup()
        print("\n🧹 Cleanup completed.")


if __name__ == "__main__":
    sys.exit(main())
