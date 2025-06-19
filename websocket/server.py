#!/usr/bin/env python3
################################################################################
# FILE: websocket/server.py
# DESC: WebSocket bridge for Material UI real-time terminal mirroring
# SPEC: TERMINAL-CENTRIC-2025-06-18-WEBSOCKET
# WHAT: Real-time streaming of terminal output to Material UI frontend
# WHY: Bridge between terminal-centric core and modern web interface
# FAIL: Exits with error if WebSocket server cannot start
# UX: Real-time terminal output mirroring in Material UI
# DEBUG: Streams verbatim capture to web interface for troubleshooting
################################################################################

import asyncio
import websockets
import json
import subprocess
import threading
import queue
import time
from datetime import datetime
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TerminalWebSocketBridge:
    """
    WHAT: WebSocket bridge for real-time terminal output streaming
    WHY: Enables Material UI to mirror terminal operations in real-time
    FAIL: Handles connection failures gracefully
    UX: Seamless real-time updates in web interface
    DEBUG: Streams verbatim capture for web-based troubleshooting
    """
    
    def __init__(self):
        self.clients = set()
        self.terminal_queue = queue.Queue()
        self.process_monitor = None
        
    async def register_client(self, websocket, path):
        """Register new WebSocket client"""
        self.clients.add(websocket)
        logger.info(f"Client connected: {websocket.remote_address}")
        
        # Send welcome message
        await websocket.send(json.dumps({
            'type': 'system',
            'content': '🔧 TERMINAL WEBSOCKET BRIDGE ACTIVE',
            'timestamp': time.time()
        }))
        
        try:
            await websocket.wait_closed()
        finally:
            self.clients.remove(websocket)
            logger.info(f"Client disconnected: {websocket.remote_address}")
    
    async def broadcast_message(self, message):
        """Broadcast message to all connected clients"""
        if self.clients:
            disconnected = set()
            
            for client in self.clients:
                try:
                    await client.send(json.dumps(message))
                except websockets.exceptions.ConnectionClosed:
                    disconnected.add(client)
                except Exception as e:
                    logger.error(f"Error sending to client: {e}")
                    disconnected.add(client)
            
            # Remove disconnected clients
            self.clients -= disconnected
    
    def start_terminal_process(self, command, cwd=None):
        """
        WHAT: Start terminal process with real-time output capture
        WHY: Execute terminal commands while streaming output to web
        FAIL: Returns False if process cannot be started
        UX: Real-time command execution visible in Material UI
        DEBUG: Complete verbatim capture streamed to web interface
        """
        try:
            logger.info(f"Starting terminal process: {command}")
            
            # Start process with real-time output capture
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                cwd=cwd
            )
            
            # Start output readers
            stdout_thread = threading.Thread(
                target=self._read_output,
                args=(process.stdout, 'stdout'),
                daemon=True
            )
            stderr_thread = threading.Thread(
                target=self._read_output,
                args=(process.stderr, 'stderr'),
                daemon=True
            )
            
            stdout_thread.start()
            stderr_thread.start()
            
            # Monitor process completion
            def monitor_process():
                process.wait()
                asyncio.create_task(self.broadcast_message({
                    'type': 'process_complete',
                    'exit_code': process.returncode,
                    'timestamp': time.time()
                }))
            
            monitor_thread = threading.Thread(target=monitor_process, daemon=True)
            monitor_thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start terminal process: {e}")
            return False
    
    def _read_output(self, pipe, stream_type):
        """Read output from pipe and queue for broadcasting"""
        try:
            for line in iter(pipe.readline, ''):
                if line:
                    line = line.rstrip()
                    message = {
                        'type': stream_type,
                        'content': line,
                        'timestamp': time.time()
                    }
                    
                    # Queue for async broadcasting
                    self.terminal_queue.put(message)
            
            pipe.close()
            
        except Exception as e:
            logger.error(f"Error reading {stream_type}: {e}")
    
    async def process_terminal_queue(self):
        """Process queued terminal output for broadcasting"""
        while True:
            try:
                # Check for queued messages
                while not self.terminal_queue.empty():
                    message = self.terminal_queue.get_nowait()
                    await self.broadcast_message(message)
                
                # Small delay to prevent CPU spinning
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error processing terminal queue: {e}")
                await asyncio.sleep(1)

class SolarPanelWebSocketAPI:
    """
    WHAT: WebSocket API for solar panel processing operations
    WHY: Provides web interface control over terminal operations
    FAIL: Handles API errors gracefully
    UX: Web-based control of solar panel processing
    DEBUG: API operations logged and streamed
    """
    
    def __init__(self, bridge):
        self.bridge = bridge
    
    async def handle_api_request(self, websocket, path):
        """Handle API requests from Material UI"""
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.process_api_request(data, websocket)
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'content': 'Invalid JSON format',
                        'timestamp': time.time()
                    }))
                except Exception as e:
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'content': f'API error: {str(e)}',
                        'timestamp': time.time()
                    }))
        
        except websockets.exceptions.ConnectionClosed:
            logger.info("API client disconnected")
    
    async def process_api_request(self, data, websocket):
        """Process individual API request"""
        request_type = data.get('type')
        
        if request_type == 'process_single':
            await self.handle_process_single(data, websocket)
        elif request_type == 'process_batch':
            await self.handle_process_batch(data, websocket)
        elif request_type == 'get_status':
            await self.handle_get_status(websocket)
        elif request_type == 'github_upload_test':
            await self.handle_github_upload_test(data, websocket)
        else:
            await websocket.send(json.dumps({
                'type': 'error',
                'content': f'Unknown request type: {request_type}',
                'timestamp': time.time()
            }))
    
    async def handle_process_single(self, data, websocket):
        """Handle single solar panel processing request"""
        input_file = data.get('input')
        output_dir = data.get('output', 'catalog/')
        verbose = data.get('verbose', True)
        github_upload = data.get('github_upload', False)

        if not input_file:
            await websocket.send(json.dumps({
                'type': 'error',
                'content': 'Input file required',
                'timestamp': time.time()
            }))
            return

        # Build command with proper verbatim capture
        command = f"python3 cli/main.py --input '{input_file}' --output '{output_dir}'"
        if verbose:
            command += " --verbose"
        if github_upload:
            command += " --github-upload"

        # Add verbatim capture redirection
        if verbose:
            command = f"bash -c 'exec 2> >(stdbuf -oL ts | tee /dev/stderr); {command}'"

        # Start terminal process
        success = self.bridge.start_terminal_process(command)

        await websocket.send(json.dumps({
            'type': 'process_started' if success else 'error',
            'content': f'Processing started with verbatim capture: {command}' if success else 'Failed to start processing',
            'command': command,
            'timestamp': time.time()
        }))
    
    async def handle_process_batch(self, data, websocket):
        """Handle batch processing request"""
        input_dir = data.get('input')
        output_dir = data.get('output', 'catalog/')
        workers = data.get('workers', 4)
        verbose = data.get('verbose', True)
        
        if not input_dir:
            await websocket.send(json.dumps({
                'type': 'error',
                'content': 'Input directory required',
                'timestamp': time.time()
            }))
            return
        
        # Build command
        command = f"python3 cli/batch_processor.py --input '{input_dir}' --output '{output_dir}' --workers {workers}"
        if verbose:
            command += " --verbose"
        
        # Start terminal process
        success = self.bridge.start_terminal_process(command)
        
        await websocket.send(json.dumps({
            'type': 'batch_started' if success else 'error',
            'content': 'Batch processing started' if success else 'Failed to start batch processing',
            'command': command,
            'timestamp': time.time()
        }))
    
    async def handle_get_status(self, websocket):
        """Handle status request"""
        await websocket.send(json.dumps({
            'type': 'status',
            'content': {
                'connected_clients': len(self.bridge.clients),
                'server_time': time.time(),
                'uptime': time.time() - server_start_time
            },
            'timestamp': time.time()
        }))

    async def handle_github_upload_test(self, data, websocket):
        """Handle GitHub upload test with verbatim capture"""
        verbose = data.get('verbose', True)

        # Test GitHub authentication and show verbatim output
        # NOTE: GitHub token should be loaded from environment or .env.local file
        command = "python3 debug_github_auth.py"

        if verbose:
            # Add verbatim capture for complete GitHub API visibility
            command = f"bash -c 'echo \"🔧 GITHUB UPLOAD TEST WITH VERBATIM CAPTURE\"; echo \"📅 $(date)\"; {command}'"

        # Start terminal process
        success = self.bridge.start_terminal_process(command)

        await websocket.send(json.dumps({
            'type': 'github_test_started' if success else 'error',
            'content': 'GitHub upload test started with verbatim capture' if success else 'Failed to start GitHub test',
            'command': command,
            'timestamp': time.time()
        }))

async def main():
    """
    WHAT: Main WebSocket server entry point
    WHY: Start WebSocket bridge for Material UI integration
    FAIL: Exits if server cannot start
    UX: Enables real-time web interface
    DEBUG: Logs server startup and operations
    """
    global server_start_time
    server_start_time = time.time()

    logger.info("🚀 Starting Terminal WebSocket Bridge")
    logger.info("=" * 50)

    # Initialize bridge and API
    bridge = TerminalWebSocketBridge()
    api = SolarPanelWebSocketAPI(bridge)

    # Start terminal queue processor
    asyncio.create_task(bridge.process_terminal_queue())

    # Start WebSocket servers with better error handling
    async def start_terminal_server():
        return await websockets.serve(
            bridge.register_client,
            "localhost",
            8080,
            ping_interval=20,
            ping_timeout=10
        )

    async def start_api_server():
        return await websockets.serve(
            api.handle_api_request,
            "localhost",
            8081,
            ping_interval=20,
            ping_timeout=10
        )

    logger.info("📡 Terminal output stream: ws://localhost:8080")
    logger.info("🔌 API endpoint: ws://localhost:8081")
    logger.info("✅ WebSocket bridge ready for Material UI")
    logger.info("=" * 50)

    # Start servers
    terminal_server = await start_terminal_server()
    api_server = await start_api_server()

    # Keep servers running
    try:
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        logger.info("Shutting down WebSocket bridge...")
    finally:
        terminal_server.close()
        api_server.close()
        await terminal_server.wait_closed()
        await api_server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("WebSocket bridge stopped by user")
    except Exception as e:
        logger.error(f"WebSocket bridge error: {e}")
        import traceback
        logger.error(traceback.format_exc())
