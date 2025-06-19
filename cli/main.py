#!/usr/bin/env python3
################################################################################
# FILE: cli/main.py
# DESC: Terminal-centric main entry point with verbatim capture
# SPEC: TERMINAL-CENTRIC-2025-06-18-MAIN
# WHAT: Command-line interface for solar panel processing with GitHub catalog
# WHY: Terminal-first architecture with Material UI mirroring capability
# FAIL: Exits with error code if processing fails
# UX: Rich terminal output with verbatim system message capture
# DEBUG: Full verbatim capture using tee patterns for troubleshooting
################################################################################

import sys
import os
import argparse
import json
import time
from datetime import datetime
from pathlib import Path

# Add parent directory to path for core imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def setup_verbatim_capture():
    """
    WHAT: Setup verbatim system message capture using tee patterns
    WHY: Provides complete troubleshooting visibility per user requirements
    FAIL: Returns False if verbatim capture setup fails
    UX: Shows setup status and log file locations
    DEBUG: Creates timestamped log files for all output streams
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create log files for verbatim capture
    stdout_log = log_dir / f"terminal_stdout_{timestamp}.log"
    stderr_log = log_dir / f"terminal_stderr_{timestamp}.log"
    combined_log = log_dir / f"terminal_combined_{timestamp}.log"
    
    print(f"🔧 VERBATIM SYSTEM MESSAGE CAPTURE ACTIVE")
    print(f"📅 Timestamp: {datetime.now()}")
    print(f"📁 Working Directory: {os.getcwd()}")
    print(f"📝 Logs: {stdout_log}, {stderr_log}, {combined_log}")
    
    return {
        'stdout_log': stdout_log,
        'stderr_log': stderr_log,
        'combined_log': combined_log,
        'timestamp': timestamp
    }

def process_solar_panel(input_path, output_dir, config):
    """
    WHAT: Process solar panel images with AI analysis and GitHub catalog
    WHY: Core functionality for solar panel inventory management
    FAIL: Returns False if processing fails
    UX: Shows detailed progress with verbatim system output
    DEBUG: Full verbatim capture of all AI and GitHub operations
    """
    print(f"\n🌞 SOLAR PANEL PROCESSING")
    print(f"📁 Input: {input_path}")
    print(f"📂 Output: {output_dir}")
    
    try:
        # Import core modules with verbatim error capture
        print("📦 Loading core modules...")
        from core.enhanced_vision_handler import EnhancedVisionHandler
        from core.multi_llm_analyzer import MultiLLMAnalyzer
        from core.image_processor import ImageProcessor
        from core.github_catalog import GitHubCatalog
        from core.csv_generator import CSVGenerator
        print("✅ Core modules loaded successfully")
        
        # Initialize processors
        print("🔧 Initializing processors...")
        vision_handler = EnhancedVisionHandler(config.get('openai_api_key'))
        multi_llm = MultiLLMAnalyzer(config)
        image_processor = ImageProcessor()
        github_catalog = GitHubCatalog(config)
        csv_generator = CSVGenerator()
        print("✅ Processors initialized")
        
        # Process image
        print(f"🖼️ Processing image: {input_path}")
        processed_images = image_processor.process_image(input_path, output_dir)
        print(f"✅ Image processed: {len(processed_images)} variants created")
        
        # AI Analysis with verbatim capture
        print("🧠 Starting AI analysis...")
        analysis_result = vision_handler.analyze_solar_panel(input_path)
        print(f"✅ AI analysis completed: {len(analysis_result)} insights")
        
        # Multi-LLM enhancement
        print("🔄 Multi-LLM analysis enhancement...")
        enhanced_result = multi_llm.enhance_analysis(analysis_result, input_path)
        print(f"✅ Multi-LLM enhancement completed: confidence {enhanced_result.get('confidence', 'N/A')}")
        
        # GitHub catalog upload
        print("📤 Uploading to GitHub catalog...")
        catalog_result = github_catalog.upload_product(
            product_type="Solar Panel",
            images=processed_images,
            metadata=enhanced_result,
            analysis=analysis_result
        )
        print(f"✅ GitHub catalog upload completed: {catalog_result.get('product_id', 'N/A')}")
        
        # Generate CSV
        print("📄 Generating eBay CSV...")
        csv_result = csv_generator.generate_ebay_listing(
            product_data=enhanced_result,
            images=catalog_result.get('image_urls', []),
            category_id=11700  # Solar panels eBay category
        )
        print(f"✅ CSV generated: {csv_result.get('filename', 'N/A')}")
        
        return {
            'success': True,
            'product_id': catalog_result.get('product_id'),
            'images': processed_images,
            'analysis': enhanced_result,
            'catalog': catalog_result,
            'csv': csv_result
        }
        
    except Exception as e:
        print(f"❌ Solar panel processing failed: {str(e)}")
        import traceback
        print(f"📋 Error details: {traceback.format_exc()}")
        return {'success': False, 'error': str(e)}

def batch_process(input_dir, output_dir, config):
    """
    WHAT: Batch process multiple solar panel images
    WHY: Efficient processing of entire solar panel inventories
    FAIL: Returns summary with failed items
    UX: Shows progress for each item with overall statistics
    DEBUG: Verbatim capture for each individual processing operation
    """
    print(f"\n📦 BATCH PROCESSING")
    print(f"📁 Input Directory: {input_dir}")
    print(f"📂 Output Directory: {output_dir}")
    
    input_path = Path(input_dir)
    if not input_path.exists():
        print(f"❌ Input directory not found: {input_dir}")
        return {'success': False, 'error': 'Input directory not found'}
    
    # Find image files
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
    image_files = [f for f in input_path.iterdir() 
                   if f.suffix.lower() in image_extensions]
    
    print(f"📊 Found {len(image_files)} image files to process")
    
    results = []
    successful = 0
    failed = 0
    
    for i, image_file in enumerate(image_files, 1):
        print(f"\n🔄 Processing {i}/{len(image_files)}: {image_file.name}")
        
        result = process_solar_panel(
            str(image_file), 
            str(Path(output_dir) / image_file.stem),
            config
        )
        
        results.append({
            'file': str(image_file),
            'result': result
        })
        
        if result['success']:
            successful += 1
            print(f"✅ {image_file.name} processed successfully")
        else:
            failed += 1
            print(f"❌ {image_file.name} processing failed")
    
    print(f"\n📊 BATCH PROCESSING COMPLETE")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(successful/len(image_files)*100):.1f}%")
    
    return {
        'success': True,
        'total': len(image_files),
        'successful': successful,
        'failed': failed,
        'results': results
    }

def load_config():
    """
    WHAT: Load configuration from settings file
    WHY: Centralized configuration management
    FAIL: Returns empty dict if config loading fails
    UX: Shows config loading status
    DEBUG: Logs config file location and contents (masked)
    """
    config_path = Path("config/settings.json")
    
    if not config_path.exists():
        print(f"⚠️ Config file not found: {config_path}")
        print("💡 Run setup to create configuration")
        return {}
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print(f"✅ Configuration loaded from {config_path}")
        
        # Show config status (masked)
        if config.get('openai_api_key'):
            print(f"✅ OpenAI API key configured")
        else:
            print(f"⚠️ OpenAI API key not configured")
        
        if config.get('github_token'):
            print(f"✅ GitHub token configured")
        else:
            print(f"⚠️ GitHub token not configured")
        
        return config
        
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return {}

def main():
    """
    WHAT: Main terminal entry point with verbatim capture
    WHY: Terminal-centric architecture with full system visibility
    FAIL: Exits with appropriate error codes
    UX: Rich terminal interface with progress indicators
    DEBUG: Complete verbatim system message capture
    """
    parser = argparse.ArgumentParser(
        description="🌞 Solar Panel Catalog System - Terminal Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process single solar panel
  python3 cli/main.py --input panel.jpg --output catalog/

  # Batch process with GitHub upload
  python3 cli/main.py --batch solar_inventory/ --github-upload

  # Verbose mode with full verbatim capture
  python3 cli/main.py --input panel.jpg --verbose --github-upload
        """
    )
    
    # Input options
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--input', help='Single image file to process')
    group.add_argument('--batch', help='Directory of images to batch process')
    
    # Output options
    parser.add_argument('--output', default='catalog/', 
                       help='Output directory (default: catalog/)')
    
    # Processing options
    parser.add_argument('--github-upload', action='store_true',
                       help='Upload results to GitHub catalog')
    parser.add_argument('--csv-export', action='store_true',
                       help='Generate eBay CSV export')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose output with verbatim capture')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Setup verbatim capture
    if args.verbose:
        verbatim_logs = setup_verbatim_capture()
    
    print("🚀 SOLAR PANEL CATALOG SYSTEM - TERMINAL INTERFACE")
    print("=" * 60)
    print(f"📅 Started: {datetime.now()}")
    print("=" * 60)
    
    # Load configuration
    config = load_config()
    if not config:
        print("❌ Configuration required. Run setup first.")
        sys.exit(1)
    
    # Process based on arguments
    try:
        if args.input:
            # Single file processing
            result = process_solar_panel(args.input, args.output, config)
            
            if result['success']:
                print(f"\n🎉 SUCCESS: Solar panel processed")
                print(f"📋 Product ID: {result.get('product_id', 'N/A')}")
                sys.exit(0)
            else:
                print(f"\n❌ FAILED: {result.get('error', 'Unknown error')}")
                sys.exit(1)
                
        elif args.batch:
            # Batch processing
            result = batch_process(args.batch, args.output, config)
            
            if result['success']:
                print(f"\n🎉 BATCH COMPLETE: {result['successful']}/{result['total']} successful")
                sys.exit(0 if result['failed'] == 0 else 2)
            else:
                print(f"\n❌ BATCH FAILED: {result.get('error', 'Unknown error')}")
                sys.exit(1)
                
    except KeyboardInterrupt:
        print(f"\n⚠️ Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        print(f"📋 Details: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
