"""
New main entry point using proper OOP structure
"""

import sys
import argparse
from pathlib import Path

from application import OCRApplication
from core.exceptions import ConfigurationError, OCRProcessingError


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="OCR Document Processing System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main_new.py document.pdf                    # Process single document
  python main_new.py --batch data/                  # Process all documents in data/
  python main_new.py --azure document.pdf           # Use Azure OpenAI
  python main_new.py --method chain_of_thought      # Use specific extraction method
  python main_new.py --config config.env            # Use custom config file
        """
    )
    
    parser.add_argument(
        'file_path',
        nargs='?',
        help='Path to document file or directory to process'
    )
    
    parser.add_argument(
        '--azure',
        action='store_true',
        help='Use Azure OpenAI instead of regular OpenAI'
    )
    
    parser.add_argument(
        '--batch',
        action='store_true',
        help='Process all supported documents in the specified directory'
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
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    return parser


def main():
    """Main function for the new OOP-based OCR system"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Print header
    print("🎯 OCR Document Processing System")
    print("=" * 60)
    print("✨ Object-Oriented Architecture")
    if args.azure:
        print("🔵 Using Azure OpenAI")
    else:
        print("🔵 Using OpenAI")
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
        
        # Determine what to process
        if not args.file_path:
            print("❌ Error: No file or directory specified")
            print("Use --help for usage information")
            return 1
        
        file_path = Path(args.file_path)
        
        if not file_path.exists():
            print(f"❌ Error: Path not found: {file_path}")
            return 1
        
        # Process based on arguments
        if args.batch or file_path.is_dir():
            # Batch processing
            print(f"📁 Processing directory: {file_path}")
            results = app.process_directory(
                directory_path=str(file_path),
                recursive=args.recursive,
                document_types=args.type,
                extraction_method=args.method,
                save_results=not args.no_save
            )
            
            if not results:
                print("❌ No documents found to process")
                return 1
            
        else:
            # Single file processing
            print(f"📄 Processing file: {file_path.name}")
            result = app.process_single_document(
                file_path=str(file_path),
                document_type=args.type,
                extraction_method=args.method,
                save_results=not args.no_save
            )
            
            if not result.success:
                print(f"❌ Processing failed: {result.error_message}")
                return 1
        
        # Print final statistics
        stats = app.get_statistics()
        print(f"\n📊 Final Statistics:")
        print(f"   Total Processed: {stats['total_processed']}")
        print(f"   Successful: {stats['successful']}")
        print(f"   Failed: {stats['failed']}")
        print(f"   Total Time: {stats['processing_time']:.2f}s")
        
        print("\n🎉 Processing completed successfully!")
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
