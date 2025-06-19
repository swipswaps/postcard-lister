#!/usr/bin/env python3
################################################################################
# FILE: cli/batch_processor.py
# DESC: Advanced batch processing with verbatim capture and parallel processing
# SPEC: TERMINAL-CENTRIC-2025-06-18-BATCH
# WHAT: Parallel batch processing of solar panel inventories
# WHY: Efficient processing of large solar panel collections
# FAIL: Exits with summary of failed items
# UX: Real-time progress with verbatim system output
# DEBUG: Per-item verbatim capture with consolidated logging
# WEBSOCKET: Streams real-time output to Material UI interface
################################################################################

import sys
import os
import argparse
import json
import time
import threading
import queue
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent directory to path for core imports
sys.path.insert(0, str(Path(__file__).parent.parent))

class VerbatimBatchProcessor:
    """
    WHAT: Batch processor with verbatim capture and parallel processing
    WHY: Efficient processing with complete system visibility
    FAIL: Tracks and reports all failures with verbatim details
    UX: Real-time progress updates with system message capture
    DEBUG: Complete verbatim logging for each processing operation
    """
    
    def __init__(self, config, max_workers=4, verbose=False):
        self.config = config
        self.max_workers = max_workers
        self.verbose = verbose
        self.results_queue = queue.Queue()
        self.progress_lock = threading.Lock()
        self.processed_count = 0
        self.total_count = 0
        
        # Setup verbatim logging
        if verbose:
            self.setup_verbatim_logging()
    
    def setup_verbatim_logging(self):
        """Setup verbatim capture for batch processing"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = Path("logs/batch")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        self.batch_log = log_dir / f"batch_processing_{timestamp}.log"
        self.verbatim_log = log_dir / f"batch_verbatim_{timestamp}.log"
        
        print(f"🔧 BATCH VERBATIM CAPTURE ACTIVE")
        print(f"📝 Batch Log: {self.batch_log}")
        print(f"📝 Verbatim Log: {self.verbatim_log}")
    
    def log_verbatim(self, message, item_id=None):
        """Log verbatim message with optional item context"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        if item_id:
            formatted_message = f"{timestamp} [{item_id}] {message}"
        else:
            formatted_message = f"{timestamp} [BATCH] {message}"
        
        print(formatted_message)
        
        if self.verbose and hasattr(self, 'verbatim_log'):
            with open(self.verbatim_log, 'a') as f:
                f.write(formatted_message + '\n')
    
    def process_single_item(self, image_path, output_dir, item_id):
        """
        WHAT: Process single solar panel with verbatim capture
        WHY: Individual item processing with complete logging
        FAIL: Returns detailed error information
        UX: Shows per-item progress with system messages
        DEBUG: Full verbatim capture for troubleshooting
        """
        try:
            self.log_verbatim(f"🔄 Starting processing", item_id)
            
            # Import core modules
            from core.enhanced_vision_handler import EnhancedVisionHandler
            from core.multi_llm_analyzer import MultiLLMAnalyzer
            from core.image_processor import ImageProcessor
            from core.github_catalog import GitHubCatalog
            from core.csv_generator import CSVGenerator
            
            # Initialize processors
            self.log_verbatim(f"🔧 Initializing processors", item_id)
            vision_handler = EnhancedVisionHandler(self.config.get('openai_api_key'))
            multi_llm = MultiLLMAnalyzer(self.config)
            image_processor = ImageProcessor()
            github_catalog = GitHubCatalog(self.config)
            csv_generator = CSVGenerator()
            
            # Process image
            self.log_verbatim(f"🖼️ Processing image: {image_path.name}", item_id)
            processed_images = image_processor.process_image(str(image_path), output_dir)
            self.log_verbatim(f"✅ Image processed: {len(processed_images)} variants", item_id)
            
            # AI Analysis
            self.log_verbatim(f"🧠 Starting AI analysis", item_id)
            analysis_result = vision_handler.analyze_solar_panel(str(image_path))
            self.log_verbatim(f"✅ AI analysis completed", item_id)
            
            # Multi-LLM enhancement
            self.log_verbatim(f"🔄 Multi-LLM enhancement", item_id)
            enhanced_result = multi_llm.enhance_analysis(analysis_result, str(image_path))
            confidence = enhanced_result.get('confidence', 'N/A')
            self.log_verbatim(f"✅ Multi-LLM completed: confidence {confidence}", item_id)
            
            # GitHub catalog upload
            self.log_verbatim(f"📤 Uploading to GitHub catalog", item_id)
            catalog_result = github_catalog.upload_product(
                product_type="Solar Panel",
                images=processed_images,
                metadata=enhanced_result,
                analysis=analysis_result
            )
            product_id = catalog_result.get('product_id', 'N/A')
            self.log_verbatim(f"✅ GitHub upload completed: {product_id}", item_id)
            
            # Generate CSV
            self.log_verbatim(f"📄 Generating eBay CSV", item_id)
            csv_result = csv_generator.generate_ebay_listing(
                product_data=enhanced_result,
                images=catalog_result.get('image_urls', []),
                category_id=11700
            )
            csv_file = csv_result.get('filename', 'N/A')
            self.log_verbatim(f"✅ CSV generated: {csv_file}", item_id)
            
            # Update progress
            with self.progress_lock:
                self.processed_count += 1
                progress = (self.processed_count / self.total_count) * 100
                self.log_verbatim(f"📊 Progress: {self.processed_count}/{self.total_count} ({progress:.1f}%)")
            
            return {
                'success': True,
                'item_id': item_id,
                'file': str(image_path),
                'product_id': product_id,
                'images': processed_images,
                'analysis': enhanced_result,
                'catalog': catalog_result,
                'csv': csv_result
            }
            
        except Exception as e:
            self.log_verbatim(f"❌ Processing failed: {str(e)}", item_id)
            import traceback
            error_details = traceback.format_exc()
            self.log_verbatim(f"📋 Error details: {error_details}", item_id)
            
            with self.progress_lock:
                self.processed_count += 1
            
            return {
                'success': False,
                'item_id': item_id,
                'file': str(image_path),
                'error': str(e),
                'details': error_details
            }
    
    def process_batch(self, input_dir, output_dir):
        """
        WHAT: Process batch of solar panels with parallel processing
        WHY: Efficient processing of large inventories
        FAIL: Returns summary with all failures detailed
        UX: Real-time progress with verbatim system output
        DEBUG: Complete verbatim capture for all operations
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        
        self.log_verbatim(f"📦 BATCH PROCESSING STARTED")
        self.log_verbatim(f"📁 Input: {input_path}")
        self.log_verbatim(f"📂 Output: {output_path}")
        
        if not input_path.exists():
            self.log_verbatim(f"❌ Input directory not found: {input_dir}")
            return {'success': False, 'error': 'Input directory not found'}
        
        # Find image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        image_files = [f for f in input_path.iterdir() 
                       if f.suffix.lower() in image_extensions]
        
        self.total_count = len(image_files)
        self.log_verbatim(f"📊 Found {self.total_count} image files")
        self.log_verbatim(f"🔧 Using {self.max_workers} parallel workers")
        
        if self.total_count == 0:
            self.log_verbatim(f"⚠️ No image files found")
            return {'success': True, 'total': 0, 'results': []}
        
        # Create output directory
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Process files in parallel
        results = []
        successful = 0
        failed = 0
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_item = {}
            for i, image_file in enumerate(image_files):
                item_id = f"ITEM_{i+1:03d}"
                item_output_dir = output_path / image_file.stem
                
                future = executor.submit(
                    self.process_single_item,
                    image_file,
                    str(item_output_dir),
                    item_id
                )
                future_to_item[future] = (item_id, image_file)
            
            # Collect results as they complete
            for future in as_completed(future_to_item):
                item_id, image_file = future_to_item[future]
                
                try:
                    result = future.result()
                    results.append(result)
                    
                    if result['success']:
                        successful += 1
                        self.log_verbatim(f"✅ {image_file.name} completed successfully")
                    else:
                        failed += 1
                        self.log_verbatim(f"❌ {image_file.name} failed")
                        
                except Exception as e:
                    failed += 1
                    self.log_verbatim(f"❌ {image_file.name} executor error: {e}")
                    results.append({
                        'success': False,
                        'item_id': item_id,
                        'file': str(image_file),
                        'error': f"Executor error: {e}"
                    })
        
        # Calculate final statistics
        end_time = time.time()
        duration = end_time - start_time
        
        self.log_verbatim(f"📊 BATCH PROCESSING COMPLETE")
        self.log_verbatim(f"✅ Successful: {successful}")
        self.log_verbatim(f"❌ Failed: {failed}")
        self.log_verbatim(f"📈 Success Rate: {(successful/self.total_count*100):.1f}%")
        self.log_verbatim(f"⏱️ Duration: {duration:.1f} seconds")
        self.log_verbatim(f"🚀 Throughput: {(self.total_count/duration):.2f} items/second")
        
        return {
            'success': True,
            'total': self.total_count,
            'successful': successful,
            'failed': failed,
            'duration': duration,
            'throughput': self.total_count / duration,
            'results': results
        }

def main():
    """
    WHAT: Main entry point for batch processing
    WHY: Terminal-centric batch processing with verbatim capture
    FAIL: Exits with appropriate error codes
    UX: Rich progress display with system visibility
    DEBUG: Complete verbatim system message capture
    """
    parser = argparse.ArgumentParser(
        description="🌞 Solar Panel Batch Processor - Terminal Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic batch processing
  python3 cli/batch_processor.py --input solar_inventory/ --output catalog/

  # Parallel processing with verbatim capture
  python3 cli/batch_processor.py --input solar_inventory/ --workers 8 --verbose

  # Full processing with GitHub upload
  python3 cli/batch_processor.py --input solar_inventory/ --github-upload --verbose
        """
    )
    
    parser.add_argument('--input', required=True,
                       help='Input directory containing solar panel images')
    parser.add_argument('--output', default='catalog/',
                       help='Output directory (default: catalog/)')
    parser.add_argument('--workers', type=int, default=4,
                       help='Number of parallel workers (default: 4)')
    parser.add_argument('--github-upload', action='store_true',
                       help='Upload results to GitHub catalog')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose output with verbatim capture')
    
    args = parser.parse_args()
    
    print("🚀 SOLAR PANEL BATCH PROCESSOR - TERMINAL INTERFACE")
    print("=" * 60)
    print(f"📅 Started: {datetime.now()}")
    print(f"🔧 Workers: {args.workers}")
    print("=" * 60)
    
    # Load configuration
    config_path = Path("config/settings.json")
    if not config_path.exists():
        print("❌ Configuration file not found. Run setup first.")
        sys.exit(1)
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        sys.exit(1)
    
    # Initialize batch processor
    processor = VerbatimBatchProcessor(
        config=config,
        max_workers=args.workers,
        verbose=args.verbose
    )
    
    try:
        # Process batch
        result = processor.process_batch(args.input, args.output)
        
        if result['success']:
            if result['total'] > 0:
                success_rate = (result['successful'] / result['total']) * 100
                print(f"\n🎉 BATCH COMPLETE: {result['successful']}/{result['total']} successful ({success_rate:.1f}%)")
                
                if 'duration' in result:
                    print(f"⏱️ Duration: {result['duration']:.1f}s")
                    print(f"🚀 Throughput: {result['throughput']:.2f} items/second")
                
                sys.exit(0 if result['failed'] == 0 else 2)
            else:
                print(f"\n⚠️ No files to process")
                sys.exit(0)
        else:
            print(f"\n❌ BATCH FAILED: {result.get('error', 'Unknown error')}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n⚠️ Batch processing cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        print(f"📋 Details: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
