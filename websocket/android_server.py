#!/usr/bin/env python3
"""
Android-style WebSocket server for solar panel catalog
Simple, reliable, with proper error handling and verbatim capture
"""

import asyncio
import websockets
import json
import logging
import subprocess
import os
from datetime import datetime
from pathlib import Path
import signal
import sys

# Setup logging with verbatim capture
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Create verbatim log file
verbatim_log_file = log_dir / f"websocket_verbatim_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(verbatim_log_file)
    ]
)
logger = logging.getLogger(__name__)

# Verbatim capture list
verbatim_messages = []

def log_verbatim(message, level="INFO"):
    """Log message with verbatim capture"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    log_entry = f"{timestamp} [{level}] {message}"
    verbatim_messages.append(log_entry)
    logger.info(message)

    # Keep only last 1000 messages
    if len(verbatim_messages) > 1000:
        verbatim_messages.pop(0)

class AndroidWebSocketServer:
    def __init__(self, host="localhost", port=8081):
        self.host = host
        self.port = port
        self.clients = set()
        self.server = None
        self.running = False
        log_verbatim(f"🔧 Initializing WebSocket server on {host}:{port}")

    async def register_client(self, websocket):
        """Register a new client"""
        self.clients.add(websocket)
        log_verbatim(f"✅ Client connected from {websocket.remote_address}")
        log_verbatim(f"📊 Total clients: {len(self.clients)}")

        # Send welcome message with verbatim log
        await self.send_to_client(websocket, {
            'type': 'welcome',
            'message': 'Connected to Solar Panel Catalog server',
            'verbatim_log': verbatim_messages[-10:],  # Send last 10 messages
            'timestamp': datetime.now().isoformat()
        })

    async def unregister_client(self, websocket):
        """Unregister a client"""
        if websocket in self.clients:
            self.clients.remove(websocket)
            logger.info(f"❌ Client disconnected")
            logger.info(f"📊 Total clients: {len(self.clients)}")

    async def send_to_client(self, websocket, message):
        """Send message to a specific client"""
        try:
            await websocket.send(json.dumps(message))
        except websockets.exceptions.ConnectionClosed:
            await self.unregister_client(websocket)
        except Exception as e:
            logger.error(f"Error sending to client: {e}")

    async def broadcast(self, message):
        """Broadcast message to all clients"""
        if not self.clients:
            logger.warning("No clients to broadcast to")
            return

        disconnected = set()
        for client in self.clients.copy():
            try:
                await client.send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)
            except Exception as e:
                logger.error(f"Broadcast error: {e}")
                disconnected.add(client)

        # Clean up disconnected clients
        for client in disconnected:
            await self.unregister_client(client)

    async def handle_message(self, websocket, message):
        """Handle incoming message from client"""
        try:
            data = json.loads(message)
            message_type = data.get('type', 'unknown')
            
            logger.info(f"📨 Received: {message_type}")

            if message_type == 'ping':
                await self.send_to_client(websocket, {
                    'type': 'pong',
                    'timestamp': datetime.now().isoformat()
                })

            elif message_type == 'process_solar_panel':
                await self.handle_solar_processing(data)

            elif message_type == 'github_upload':
                await self.handle_github_upload(data)

            elif message_type == 'health_check':
                await self.send_to_client(websocket, {
                    'type': 'health_response',
                    'status': 'healthy',
                    'clients': len(self.clients),
                    'timestamp': datetime.now().isoformat()
                })

            elif message_type == 'get_verbatim_log':
                await self.send_to_client(websocket, {
                    'type': 'verbatim_log_response',
                    'log': verbatim_messages,
                    'timestamp': datetime.now().isoformat()
                })

            else:
                log_verbatim(f"Unknown message type: {message_type}", "WARNING")

        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
        except Exception as e:
            logger.error(f"Message handling error: {e}")

    async def handle_solar_processing(self, data):
        """Simulate solar panel processing"""
        logger.info("🌞 Starting solar panel processing...")
        
        steps = [
            "🔧 Initializing AI processors...",
            "📸 Loading solar panel image...",
            "🧠 Running AI analysis...",
            "📊 Extracting specifications...",
            "💾 Saving results...",
            "✅ Processing complete!"
        ]

        for i, step in enumerate(steps):
            progress = ((i + 1) / len(steps)) * 100
            
            await self.broadcast({
                'type': 'processing_progress',
                'step': i + 1,
                'total': len(steps),
                'description': step,
                'percentage': progress,
                'timestamp': datetime.now().isoformat()
            })
            
            await asyncio.sleep(1)  # Simulate work

        await self.broadcast({
            'type': 'processing_complete',
            'success': True,
            'message': 'Solar panel processing completed successfully!',
            'timestamp': datetime.now().isoformat()
        })

    async def handle_github_upload(self, data):
        """Real GitHub upload with verbatim capture"""
        log_verbatim("📤 Starting real GitHub upload...")

        try:
            # Step 1: Check git status
            await self.broadcast({
                'type': 'github_upload_progress',
                'status': 'checking',
                'progress': 10,
                'message': '🔍 Checking git repository status...',
                'verbatim_log': verbatim_messages[-5:]
            })

            # Run git status
            result = await self.run_git_command(['git', 'status', '--porcelain'])
            if not result['success']:
                raise Exception(f"Git status failed: {result['error']}")

            # Step 2: Stage changes
            await self.broadcast({
                'type': 'github_upload_progress',
                'status': 'staging',
                'progress': 30,
                'message': '📦 Staging changes...',
                'verbatim_log': verbatim_messages[-5:]
            })

            result = await self.run_git_command(['git', 'add', '.'])
            if not result['success']:
                raise Exception(f"Git add failed: {result['error']}")

            # Step 3: Commit
            commit_msg = f"Solar panel catalog update - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            await self.broadcast({
                'type': 'github_upload_progress',
                'status': 'committing',
                'progress': 50,
                'message': f'💾 Committing: {commit_msg}',
                'verbatim_log': verbatim_messages[-5:]
            })

            result = await self.run_git_command(['git', 'commit', '-m', commit_msg])
            if not result['success'] and 'nothing to commit' not in result['error']:
                raise Exception(f"Git commit failed: {result['error']}")

            # Step 4: Push
            await self.broadcast({
                'type': 'github_upload_progress',
                'status': 'pushing',
                'progress': 80,
                'message': '📤 Pushing to GitHub...',
                'verbatim_log': verbatim_messages[-5:]
            })

            result = await self.run_git_command(['git', 'push', 'origin', 'HEAD'])
            if not result['success']:
                raise Exception(f"Git push failed: {result['error']}")

            # Success
            await self.broadcast({
                'type': 'github_upload_complete',
                'success': True,
                'message': '✅ Successfully uploaded to GitHub!',
                'verbatim_log': verbatim_messages[-10:],
                'timestamp': datetime.now().isoformat()
            })

        except Exception as e:
            log_verbatim(f"❌ GitHub upload error: {e}", "ERROR")
            await self.broadcast({
                'type': 'github_upload_complete',
                'success': False,
                'message': f'❌ Upload failed: {str(e)}',
                'verbatim_log': verbatim_messages[-10:],
                'timestamp': datetime.now().isoformat()
            })

    async def run_git_command(self, cmd):
        """Run git command with verbatim capture"""
        log_verbatim(f"🔧 Running: {' '.join(cmd)}")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=Path.cwd()
            )

            stdout, stderr = await process.communicate()

            stdout_text = stdout.decode() if stdout else ""
            stderr_text = stderr.decode() if stderr else ""

            if stdout_text:
                log_verbatim(f"📤 STDOUT: {stdout_text.strip()}")
            if stderr_text:
                log_verbatim(f"📥 STDERR: {stderr_text.strip()}")

            success = process.returncode == 0
            log_verbatim(f"{'✅' if success else '❌'} Command {'succeeded' if success else 'failed'} (code {process.returncode})")

            return {
                'success': success,
                'stdout': stdout_text,
                'stderr': stderr_text,
                'returncode': process.returncode
            }

        except Exception as e:
            log_verbatim(f"💥 Command error: {e}", "ERROR")
            return {
                'success': False,
                'stdout': "",
                'stderr': str(e),
                'returncode': -1
            }

    async def client_handler(self, websocket, path):
        """Handle individual client connection"""
        await self.register_client(websocket)
        
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client connection closed normally")
        except Exception as e:
            logger.error(f"Client handler error: {e}")
        finally:
            await self.unregister_client(websocket)

    async def start_server(self):
        """Start the WebSocket server"""
        logger.info(f"🚀 Starting Android WebSocket server on {self.host}:{self.port}")
        
        try:
            self.server = await websockets.serve(
                self.client_handler,
                self.host,
                self.port,
                ping_interval=20,
                ping_timeout=10
            )
            
            self.running = True
            logger.info("✅ Android WebSocket server started successfully!")
            logger.info(f"🌐 Server listening on ws://{self.host}:{self.port}")
            
            # Keep server running
            await self.server.wait_closed()
            
        except Exception as e:
            logger.error(f"❌ Server startup error: {e}")
            self.running = False

    async def stop_server(self):
        """Stop the WebSocket server"""
        if self.server:
            logger.info("🛑 Stopping WebSocket server...")
            self.server.close()
            await self.server.wait_closed()
            self.running = False
            logger.info("✅ WebSocket server stopped")

    def run(self):
        """Run the server with proper signal handling"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            asyncio.create_task(self.stop_server())

        # Setup signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            asyncio.run(self.start_server())
        except KeyboardInterrupt:
            logger.info("Server shutdown by user")
        except Exception as e:
            logger.error(f"Server error: {e}")

def main():
    """Main entry point"""
    print("🌞 Solar Panel Catalog - Android WebSocket Server")
    print("=" * 50)
    
    server = AndroidWebSocketServer()
    server.run()

if __name__ == "__main__":
    main()
