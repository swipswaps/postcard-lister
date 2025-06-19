#!/usr/bin/env python3
"""
GitHub CLI WebSocket Server with Verbatim Capture
Integrates the working github_upload_clean.sh with tee pattern verbatim logging
Uses gh CLI as primary method with git as fallback (as requested by user)
"""

import asyncio
import websockets
import json
import logging
import subprocess
import os
import tempfile
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global client set and verbatim log
clients = set()
verbatim_messages = []

def log_verbatim(message, level="INFO"):
    """Add message to verbatim log with timestamp and IMPROVED duplicate collapsing"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    log_entry = f"{timestamp} [{level}] {message}"

    # IMPROVED: Better duplicate detection and collapsing
    if verbatim_messages:
        last_entry = verbatim_messages[-1]

        # Extract just the message part (after timestamp and level)
        if '] ' in last_entry:
            last_message_only = last_entry.split('] ', 1)[1]
        else:
            last_message_only = last_entry

        # Remove existing count if present to get clean message
        if last_message_only.endswith(")") and " (x" in last_message_only:
            last_message_clean = last_message_only.rsplit(" (x", 1)[0]
        else:
            last_message_clean = last_message_only

        # Check if current message matches the clean last message
        if message.strip() == last_message_clean.strip():
            # This is a duplicate - update count at END of line
            if " (x" in verbatim_messages[-1] and verbatim_messages[-1].endswith(")"):
                # Extract and increment count
                base_part, count_part = verbatim_messages[-1].rsplit(" (x", 1)
                try:
                    current_count = int(count_part[:-1])  # Remove closing )
                    verbatim_messages[-1] = f"{base_part} (x{current_count + 1})"
                    logger.info(f"Duplicate message collapsed: {message} (count: {current_count + 1})")
                    return verbatim_messages[-1]  # Return the collapsed entry
                except ValueError:
                    # Malformed count, treat as new message
                    verbatim_messages.append(log_entry)
            else:
                # First duplicate, add (x2) at the end
                verbatim_messages[-1] = f"{verbatim_messages[-1]} (x2)"
                logger.info(f"First duplicate detected: {message}")
                return verbatim_messages[-1]  # Return the collapsed entry
        else:
            # Different message, add normally
            verbatim_messages.append(log_entry)
    else:
        # First message ever
        verbatim_messages.append(log_entry)

    # Keep reasonable history for troubleshooting
    if len(verbatim_messages) > 1000:
        verbatim_messages.pop(0)

    logger.info(message)
    return log_entry

async def run_github_upload_with_verbatim_capture(commit_message="Solar panel catalog update"):
    """
    Run the working github_upload_clean.sh script with full verbatim capture
    Uses tee patterns for complete system message capture
    """
    log_verbatim("🚀 Starting GitHub CLI upload with verbatim capture...")
    
    # Create timestamp for logs
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create log files for verbatim capture
    stdout_log = log_dir / f"github_upload_stdout_{timestamp}.log"
    stderr_log = log_dir / f"github_upload_stderr_{timestamp}.log"
    combined_log = log_dir / f"github_upload_combined_{timestamp}.log"
    
    log_verbatim(f"📋 Verbatim logs: {stdout_log}, {stderr_log}, {combined_log}")
    
    # Create enhanced script with COMPLETE verbatim capture including network progress
    enhanced_script = f"""#!/bin/bash
# Enhanced GitHub upload with COMPLETE verbatim message capture
# Based on PRF pattern: exec 2> >(stdbuf -oL ts | tee "$LOG_MASKED" | tee >(cat >&4))
# INCLUDES: Network progress, git progress, connection status, transfer rates

set -euo pipefail

# Setup logging with tee pattern for COMPLETE verbatim capture
exec 1> >(stdbuf -oL ts | tee "{stdout_log}" | tee >(cat >&1))
exec 2> >(stdbuf -oL ts | tee "{stderr_log}" | tee >(cat >&2))
exec 3> >(stdbuf -oL ts | tee "{combined_log}")

# Function to show network status during long operations
show_network_progress() {{
    local operation="$1"
    echo "[NETWORK] Starting $operation..." >&3

    # Show network connectivity
    if ping -c 1 github.com >/dev/null 2>&1; then
        echo "[NETWORK] GitHub connectivity: OK" >&3
    else
        echo "[NETWORK] GitHub connectivity: FAILED" >&3
    fi

    # Show DNS resolution
    echo "[NETWORK] Resolving github.com..." >&3
    nslookup github.com 2>&1 | head -10 >&3

    # Show active connections
    echo "[NETWORK] Active connections to GitHub:" >&3
    netstat -an | grep github.com || echo "[NETWORK] No active GitHub connections" >&3
}}

# Function to monitor git push progress
monitor_git_push() {{
    echo "[GIT] Starting push monitoring..." >&3

    # Show git configuration
    echo "[GIT] Remote URL: $(git remote get-url origin)" >&3
    echo "[GIT] Current branch: $(git branch --show-current)" >&3
    echo "[GIT] Commits ahead: $(git rev-list --count origin/main..HEAD 2>/dev/null || echo 'unknown')" >&3

    # Show repository size
    echo "[GIT] Repository size: $(du -sh .git 2>/dev/null || echo 'unknown')" >&3
    echo "[GIT] Working directory size: $(du -sh . --exclude=.git 2>/dev/null || echo 'unknown')" >&3
}}

# Enhanced GitHub upload with COMPLETE progress monitoring
echo "[START] Enhanced GitHub upload with complete verbatim capture" >&3
show_network_progress "GitHub upload"

# Execute original script with FULL monitoring
{{
    # NO FAKE MONITORING - git provides real progress output
    # Real git progress is captured directly from stdout

    # Run the actual upload with REAL git progress capture
    monitor_git_push

    # Enable git progress output and capture it
    export GIT_PROGRESS=1
    export GIT_CURL_VERBOSE=1

    # Run with REAL git progress capture only
    bash "github_upload_clean.sh" "{commit_message}" 2>&3 1>&3
    RESULT=$?

    echo "[COMPLETE] GitHub upload finished with exit code: $RESULT" >&3
    exit $RESULT
}}
"""
    
    # Write enhanced script to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
        f.write(enhanced_script)
        enhanced_script_path = f.name
    
    try:
        # Make script executable
        os.chmod(enhanced_script_path, 0o755)
        
        log_verbatim(f"🔧 Running enhanced GitHub upload script: {enhanced_script_path}")
        
        # Start process with ENHANCED real-time output capture
        process = await asyncio.create_subprocess_exec(
            "/bin/bash", enhanced_script_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.getcwd(),
            # Ensure unbuffered output for real-time capture
            env={**os.environ, 'PYTHONUNBUFFERED': '1', 'GIT_PROGRESS': '1'}
        )
        
        # Read output in real-time
        stdout_data = []
        stderr_data = []
        
        async def read_stdout():
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                line_str = line.decode().strip()
                if line_str:
                    log_verbatim(f"📤 STDOUT: {line_str}")
                    stdout_data.append(line_str)
                    
                    # Broadcast real-time progress with ALL verbatim data
                    await broadcast({
                        'type': 'github_upload_progress',
                        'status': 'running',
                        'message': line_str,
                        'verbatim_log': verbatim_messages  # Send ALL messages for troubleshooting
                    })
        
        async def read_stderr():
            while True:
                line = await process.stderr.readline()
                if not line:
                    break
                line_str = line.decode().strip()
                if line_str:
                    log_verbatim(f"🚨 STDERR: {line_str}")
                    stderr_data.append(line_str)
                    
                    # Broadcast real-time errors with ALL verbatim messages
                    await broadcast({
                        'type': 'github_upload_progress',
                        'status': 'error',
                        'message': line_str,
                        'verbatim_log': verbatim_messages  # Send ALL messages - no filtering
                    })
        
        # COMPLETELY REMOVED: No fake progress monitoring - git provides real progress
        async def monitor_real_git_progress():
            """DISABLED: Real git progress is captured directly from stdout"""
            # NO FAKE PROGRESS MESSAGES - git provides real progress output
            # Just wait for the process to complete
            while process.returncode is None:
                await asyncio.sleep(10)  # Just wait, no fake messages

        # Start reading both streams AND real git progress monitoring
        await asyncio.gather(read_stdout(), read_stderr(), monitor_real_git_progress())
        
        # Wait for process to complete
        returncode = await process.wait()
        
        log_verbatim(f"✅ GitHub upload process completed with exit code: {returncode}")
        
        # Read the actual log files for complete verbatim capture
        verbatim_stdout = []
        verbatim_stderr = []
        verbatim_combined = []
        
        try:
            if stdout_log.exists():
                verbatim_stdout = stdout_log.read_text().strip().split('\n')
                log_verbatim(f"📋 Captured {len(verbatim_stdout)} stdout lines")
            
            if stderr_log.exists():
                verbatim_stderr = stderr_log.read_text().strip().split('\n')
                log_verbatim(f"📋 Captured {len(verbatim_stderr)} stderr lines")
            
            if combined_log.exists():
                verbatim_combined = combined_log.read_text().strip().split('\n')
                log_verbatim(f"📋 Captured {len(verbatim_combined)} combined lines")
        except Exception as e:
            log_verbatim(f"⚠️ Error reading log files: {e}")
        
        # Determine success/failure
        success = returncode == 0
        
        # Get git status for evidence
        try:
            git_status_result = await asyncio.create_subprocess_exec(
                'git', 'status', '--porcelain',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            git_stdout, git_stderr = await git_status_result.communicate()
            has_changes = bool(git_stdout.decode().strip())
            
            git_log_result = await asyncio.create_subprocess_exec(
                'git', 'log', '--oneline', '-5',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            log_stdout, log_stderr = await git_log_result.communicate()
            recent_commits = log_stdout.decode().strip().split('\n') if log_stdout else []
            
            git_remote_result = await asyncio.create_subprocess_exec(
                'git', 'remote', 'get-url', 'origin',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            remote_stdout, remote_stderr = await git_remote_result.communicate()
            repo_url = remote_stdout.decode().strip() if remote_stdout else 'unknown'
            
        except Exception as e:
            log_verbatim(f"⚠️ Error getting git status: {e}")
            has_changes = False
            recent_commits = []
            repo_url = 'unknown'
        
        # Create comprehensive evidence
        evidence = {
            'success': success,
            'exit_code': returncode,
            'repo_url': repo_url,
            'has_changes': has_changes,
            'recent_commits': recent_commits,
            'verbatim_stdout': verbatim_stdout,  # ALL stdout lines - no filtering
            'verbatim_stderr': verbatim_stderr,  # ALL stderr lines - no filtering
            'verbatim_combined': verbatim_combined,  # ALL combined lines - no filtering
            'log_files': {
                'stdout': str(stdout_log),
                'stderr': str(stderr_log),
                'combined': str(combined_log)
            },
            'commit_message': commit_message,
            'timestamp': datetime.now().isoformat()
        }
        
        # Broadcast final result with complete evidence
        await broadcast({
            'type': 'github_upload_complete',
            'success': success,
            'message': '✅ GitHub upload completed successfully!' if success else f'❌ GitHub upload failed (exit code: {returncode})',
            'evidence': evidence,
            'verbatim_log': verbatim_messages,  # Send ALL verbatim messages
            'timestamp': datetime.now().isoformat()
        })
        
        log_verbatim(f"🎉 GitHub CLI upload completed with verbatim evidence")
        
    except Exception as e:
        error_msg = f"❌ GitHub upload error: {str(e)}"
        log_verbatim(error_msg, "ERROR")
        
        await broadcast({
            'type': 'github_upload_complete',
            'success': False,
            'message': error_msg,
            'evidence': {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            },
            'verbatim_log': verbatim_messages,  # Send ALL verbatim messages
            'timestamp': datetime.now().isoformat()
        })
    
    finally:
        # Clean up temporary script
        try:
            os.unlink(enhanced_script_path)
        except:
            pass

async def run_solar_panel_processing(file_path):
    """
    RESTORED: Complete solar panel processing with multi-LLM analysis
    Uses the original core modules that were working
    """
    log_verbatim("🌞 Starting solar panel processing with multi-LLM analysis...")

    try:
        # Import the working core modules (fix path for websocket directory)
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        from core.enhanced_vision_handler import get_enhanced_metadata
        from core.multi_llm_analyzer import MultiLLMAnalyzer
        from core.image_processor import process_image_set
        from core.github_catalog import GitHubCatalog
        from core.csv_generator import generate_csv

        log_verbatim(f"📁 Processing file: {file_path}")

        # Load configuration
        config = {}
        if os.path.exists('.env.local'):
            with open('.env.local', 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        config[key.lower()] = value

        log_verbatim("🔧 Configuration loaded")

        # Initialize processors
        multi_llm = MultiLLMAnalyzer(config)
        github_catalog = GitHubCatalog(config)

        log_verbatim("🧠 Starting multi-LLM analysis...")

        # Multi-LLM consensus analysis
        consensus_result = multi_llm.analyze_product(file_path, "solar panel")

        log_verbatim(f"✅ Multi-LLM analysis complete: {consensus_result.product_type} (confidence: {consensus_result.confidence:.2f})")

        # Enhanced metadata extraction
        enhanced_metadata = get_enhanced_metadata(file_path, config, "solar panel")

        log_verbatim("📊 Enhanced metadata extracted")

        # Image processing (multiple variants)
        output_dir = "catalog/processed/"
        os.makedirs(output_dir, exist_ok=True)

        # Process images (front, back, combined, vision variants)
        processed_images = process_image_set(file_path, file_path, output_dir, 1)

        log_verbatim(f"🖼️ Image processing complete: {len(processed_images)} variants created")

        # GitHub catalog upload
        catalog_result = github_catalog.upload_product(
            product_type="Solar Panel",
            images=processed_images,
            metadata=enhanced_metadata,
            analysis=consensus_result
        )

        log_verbatim(f"📤 GitHub catalog upload complete: {catalog_result.get('product_id', 'N/A')}")

        # Broadcast completion
        await broadcast({
            'type': 'solar_panel_processing_complete',
            'success': True,
            'message': '✅ Solar panel processing completed successfully!',
            'results': {
                'product_type': consensus_result.product_type,
                'confidence': consensus_result.confidence,
                'metadata': enhanced_metadata,
                'processed_images': processed_images,
                'catalog_result': catalog_result
            },
            'verbatim_log': verbatim_messages,
            'timestamp': datetime.now().isoformat()
        })

        log_verbatim("🎉 Solar panel processing completed successfully!")

    except Exception as e:
        error_msg = f"❌ Solar panel processing error: {str(e)}"
        log_verbatim(error_msg, "ERROR")

        await broadcast({
            'type': 'solar_panel_processing_complete',
            'success': False,
            'message': error_msg,
            'error': str(e),
            'verbatim_log': verbatim_messages,
            'timestamp': datetime.now().isoformat()
        })

async def run_batch_processing(input_dir, workers=4):
    """
    RESTORED: Batch processing with parallel workers
    Processes multiple solar panels in parallel with verbatim capture
    """
    log_verbatim(f"🔄 Starting batch processing: {input_dir} with {workers} workers")

    try:
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        from pathlib import Path

        # Find all image files
        input_path = Path(input_dir)
        if not input_path.exists():
            raise Exception(f"Input directory does not exist: {input_dir}")

        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        image_files = [f for f in input_path.iterdir()
                      if f.is_file() and f.suffix.lower() in image_extensions]

        log_verbatim(f"📁 Found {len(image_files)} image files to process")

        if not image_files:
            raise Exception("No image files found in input directory")

        # Process files in parallel
        processed_count = 0
        failed_count = 0

        async def process_single_file(file_path):
            nonlocal processed_count, failed_count
            try:
                log_verbatim(f"🔧 Processing {file_path.name}...")
                await run_solar_panel_processing(str(file_path))
                processed_count += 1
                log_verbatim(f"✅ Completed {file_path.name}")

                # Broadcast progress
                await broadcast({
                    'type': 'batch_processing_progress',
                    'processed': processed_count,
                    'failed': failed_count,
                    'total': len(image_files),
                    'current_file': file_path.name,
                    'verbatim_log': verbatim_messages[-10:],
                    'timestamp': datetime.now().isoformat()
                })

            except Exception as e:
                failed_count += 1
                log_verbatim(f"❌ Failed to process {file_path.name}: {str(e)}", "ERROR")

        # Create semaphore to limit concurrent processing
        semaphore = asyncio.Semaphore(workers)

        async def process_with_semaphore(file_path):
            async with semaphore:
                await process_single_file(file_path)

        # Process all files
        tasks = [process_with_semaphore(file_path) for file_path in image_files]
        await asyncio.gather(*tasks, return_exceptions=True)

        # Broadcast completion
        await broadcast({
            'type': 'batch_processing_complete',
            'success': True,
            'message': f'✅ Batch processing complete! Processed: {processed_count}, Failed: {failed_count}',
            'results': {
                'total_files': len(image_files),
                'processed': processed_count,
                'failed': failed_count,
                'success_rate': (processed_count / len(image_files)) * 100 if image_files else 0
            },
            'verbatim_log': verbatim_messages,
            'timestamp': datetime.now().isoformat()
        })

        log_verbatim(f"🎉 Batch processing completed! {processed_count}/{len(image_files)} successful")

    except Exception as e:
        error_msg = f"❌ Batch processing error: {str(e)}"
        log_verbatim(error_msg, "ERROR")

        await broadcast({
            'type': 'batch_processing_complete',
            'success': False,
            'message': error_msg,
            'error': str(e),
            'verbatim_log': verbatim_messages,
            'timestamp': datetime.now().isoformat()
        })

async def run_ebay_csv_generation():
    """
    RESTORED: eBay CSV generation with professional listings
    """
    log_verbatim("📄 Starting eBay CSV generation...")

    try:
        # Fix import path
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        from core.csv_generator import generate_csv

        # Look for processed catalog data
        catalog_dir = Path("catalog/")
        if not catalog_dir.exists():
            raise Exception("No catalog directory found. Process some solar panels first.")

        # Find all product data files
        product_files = list(catalog_dir.glob("**/metadata.json"))

        if not product_files:
            raise Exception("No processed products found. Process some solar panels first.")

        log_verbatim(f"📊 Found {len(product_files)} products for CSV generation")

        # Generate CSV with all products
        csv_output = "catalog/ebay_listings.csv"
        template_path = "templates/ebay_template.csv"

        # Create template if it doesn't exist
        if not os.path.exists(template_path):
            os.makedirs("templates", exist_ok=True)
            # Create basic eBay template
            template_content = """*Action(SiteID=US|Country=US|Currency=USD|Version=1193),Custom label (SKU),Title,Schedule Time,Item photo URL,Category ID,Condition ID,Category name,Start price,Quantity,Format,Duration,Best Offer Enabled,Location,Shipping profile name,Return profile name,Payment profile name,C:Unit of Sale,C:Region,C:City,C:Subject,C:Country,C:Country/Region of Manufacture,C:Original/Licensed Reprint,C:Theme,C:Type,C:Posted Condition,C:Era,Store category,Description
Add,,,,,11700,3000-Used,/Business & Industrial/Healthcare/Medical/Solar Panels,,,FixedPrice,GTC,1,,,,,,,,,,,,,,,,"""
            with open(template_path, 'w') as f:
                f.write(template_content)

        # Load product data and generate CSV
        all_rows = []
        for product_file in product_files:
            try:
                with open(product_file, 'r') as f:
                    metadata = json.load(f)

                # Create row data for this product
                row_data = (
                    metadata,
                    metadata.get('front_image_url', ''),
                    metadata.get('back_image_url', ''),
                    metadata.get('combined_image_url', ''),
                    metadata.get('product_id', ''),
                    {'price': '150.00', 'zip_code': '12345', 'shipping_policy': 'Standard'}
                )
                all_rows.append(row_data)

            except Exception as e:
                log_verbatim(f"⚠️ Skipping {product_file}: {str(e)}", "WARNING")

        # Generate the CSV
        result_path = generate_csv(csv_output, template_path, all_rows)

        log_verbatim(f"✅ eBay CSV generated: {result_path}")

        # Broadcast completion
        await broadcast({
            'type': 'ebay_csv_generation_complete',
            'success': True,
            'message': f'✅ eBay CSV generated with {len(all_rows)} products!',
            'results': {
                'csv_path': result_path,
                'product_count': len(all_rows),
                'template_used': template_path
            },
            'verbatim_log': verbatim_messages,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        error_msg = f"❌ eBay CSV generation error: {str(e)}"
        log_verbatim(error_msg, "ERROR")

        await broadcast({
            'type': 'ebay_csv_generation_complete',
            'success': False,
            'message': error_msg,
            'error': str(e),
            'verbatim_log': verbatim_messages,
            'timestamp': datetime.now().isoformat()
        })

async def send_file_list(websocket, directory):
    """
    RESTORED: File browser functionality for Material UI
    """
    log_verbatim(f"📁 Listing files in: {directory}")

    try:
        from pathlib import Path

        dir_path = Path(directory)
        if not dir_path.exists():
            raise Exception(f"Directory does not exist: {directory}")

        files = []
        directories = []

        # List directories and files
        for item in dir_path.iterdir():
            if item.is_dir():
                directories.append({
                    'name': item.name,
                    'type': 'directory',
                    'path': str(item),
                    'size': None
                })
            else:
                # Check if it's an image file
                image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
                is_image = item.suffix.lower() in image_extensions

                files.append({
                    'name': item.name,
                    'type': 'image' if is_image else 'file',
                    'path': str(item),
                    'size': item.stat().st_size,
                    'is_image': is_image
                })

        # Sort directories first, then files
        directories.sort(key=lambda x: x['name'].lower())
        files.sort(key=lambda x: x['name'].lower())

        file_list = directories + files

        log_verbatim(f"📊 Found {len(directories)} directories and {len(files)} files")

        # Send file list
        await websocket.send(json.dumps({
            'type': 'file_list_response',
            'success': True,
            'directory': directory,
            'files': file_list,
            'total_items': len(file_list),
            'verbatim_log': verbatim_messages[-5:],
            'timestamp': datetime.now().isoformat()
        }))

    except Exception as e:
        error_msg = f"❌ File listing error: {str(e)}"
        log_verbatim(error_msg, "ERROR")

        await websocket.send(json.dumps({
            'type': 'file_list_response',
            'success': False,
            'message': error_msg,
            'error': str(e),
            'verbatim_log': verbatim_messages[-5:],
            'timestamp': datetime.now().isoformat()
        }))

async def register_client(websocket):
    """Register new client"""
    clients.add(websocket)
    logger.info(f"✅ Client connected: {len(clients)} total")
    
    try:
        # Send welcome with current status
        await websocket.send(json.dumps({
            'type': 'welcome',
            'message': '🌞 Connected to GitHub CLI server with verbatim capture',
            'verbatim_log': verbatim_messages,  # Send ALL verbatim messages
            'timestamp': datetime.now().isoformat()
        }))
    except Exception as e:
        logger.error(f"Error sending welcome: {e}")

async def unregister_client(websocket):
    """Unregister client"""
    if websocket in clients:
        clients.remove(websocket)
        logger.info(f"❌ Client disconnected: {len(clients)} total")

async def broadcast(message):
    """Broadcast to all clients"""
    if not clients:
        return
    
    disconnected = set()
    for client in clients.copy():
        try:
            await client.send(json.dumps(message))
        except:
            disconnected.add(client)
    
    for client in disconnected:
        await unregister_client(client)

async def handle_message(websocket, message):
    """Handle incoming message"""
    try:
        data = json.loads(message)
        message_type = data.get('type', 'unknown')
        
        logger.info(f"📨 Received: {message_type}")
        
        if message_type == 'ping':
            await websocket.send(json.dumps({
                'type': 'pong',
                'timestamp': datetime.now().isoformat()
            }))
        
        elif message_type == 'github_upload':
            # Run REAL GitHub CLI upload with verbatim capture
            commit_msg = data.get('commit_message', 'Solar panel catalog update')
            await run_github_upload_with_verbatim_capture(commit_msg)

        elif message_type == 'process_solar_panel':
            # RESTORED: Solar panel processing with multi-LLM analysis
            file_path = data.get('file', '')
            await run_solar_panel_processing(file_path)

        elif message_type == 'batch_process':
            # RESTORED: Batch processing with parallel workers
            input_dir = data.get('input_dir', '')
            workers = data.get('workers', 4)
            await run_batch_processing(input_dir, workers)

        elif message_type == 'generate_ebay_csv':
            # RESTORED: eBay CSV generation
            await run_ebay_csv_generation()

        elif message_type == 'list_files':
            # RESTORED: File browser functionality
            directory = data.get('directory', '.')
            await send_file_list(websocket, directory)
        
        elif message_type == 'get_verbatim_log':
            await websocket.send(json.dumps({
                'type': 'verbatim_log_response',
                'log': verbatim_messages,  # Send ALL log entries - no filtering
                'timestamp': datetime.now().isoformat()
            }))
        
        else:
            logger.warning(f"Unknown message: {message_type}")
            
    except Exception as e:
        logger.error(f"Message handling error: {e}")

async def client_handler(websocket):
    """Handle client connection"""
    try:
        await register_client(websocket)
        
        async for message in websocket:
            await handle_message(websocket, message)
            
    except websockets.exceptions.ConnectionClosed:
        logger.info("Client disconnected normally")
    except Exception as e:
        logger.error(f"Client handler error: {e}")
    finally:
        await unregister_client(websocket)

async def start_server():
    """Start the server"""
    host = "localhost"
    port = 8081
    
    logger.info(f"🚀 Starting GitHub CLI WebSocket server on {host}:{port}")
    
    async with websockets.serve(
        client_handler,
        host,
        port,
        ping_interval=20,
        ping_timeout=10
    ) as server:
        logger.info("✅ GitHub CLI WebSocket server started successfully!")
        logger.info(f"🌐 Server listening on ws://{host}:{port}")
        logger.info("🔧 Features: GitHub CLI, verbatim capture, tee patterns")
        
        # Keep server running
        await asyncio.Future()

def main():
    """Main entry point"""
    print("🌞 Solar Panel Catalog - GitHub CLI WebSocket Server")
    print("=" * 60)
    print("🔧 Features: GitHub CLI primary, git fallback, verbatim logging")
    print("📊 Provides: Real gh CLI output, tee pattern capture, evidence")
    print("=" * 60)
    
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        logger.info("Server shutdown by user")
    except Exception as e:
        logger.error(f"Server error: {e}")

if __name__ == "__main__":
    main()
