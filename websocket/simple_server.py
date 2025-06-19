#!/usr/bin/env python3
################################################################################
# FILE: websocket/simple_server.py
# DESC: Simple working WebSocket server for Material UI frontend
# WHAT: Basic WebSocket bridge with proper handler signature
# WHY: Fix connection issues with frontend
# FAIL: Graceful error handling and logging
# UX: Seamless frontend connectivity
# DEBUG: Complete verbatim logging
################################################################################

import asyncio
import websockets
import json
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create logs directory
Path("logs").mkdir(exist_ok=True)

class SimpleWebSocketServer:
    """Simple WebSocket server for frontend connectivity"""
    
    def __init__(self, host="localhost", port=8080):
        self.host = host
        self.port = port
        self.clients = set()
    
    async def register_client(self, websocket):
        """Register new client"""
        self.clients.add(websocket)
        logger.info(f"Client connected: {websocket.remote_address}")
        logger.info(f"Total clients: {len(self.clients)}")
    
    async def unregister_client(self, websocket):
        """Unregister client"""
        if websocket in self.clients:
            self.clients.remove(websocket)
            logger.info(f"Client disconnected")
            logger.info(f"Total clients: {len(self.clients)}")
    
    async def broadcast_message(self, message):
        """Broadcast message to all clients"""
        if not self.clients:
            logger.warning("No clients connected")
            return
        
        disconnected = set()
        for client in self.clients.copy():
            try:
                await client.send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
                disconnected.add(client)
        
        # Remove disconnected clients
        for client in disconnected:
            await self.unregister_client(client)
    
    async def handle_message(self, websocket, message):
        """Handle incoming message from client"""
        try:
            data = json.loads(message)
            message_type = data.get('type', 'unknown')
            
            logger.info(f"Received message: {message_type}")
            
            if message_type == 'ping':
                await websocket.send(json.dumps({
                    'type': 'pong',
                    'timestamp': datetime.now().isoformat()
                }))
            
            elif message_type == 'process_solar_panel':
                await self.handle_solar_panel_processing(data)
            
            elif message_type == 'github_upload':
                await self.handle_github_upload(data)
            
            elif message_type == 'health_check':
                await websocket.send(json.dumps({
                    'type': 'health_status',
                    'status': 'healthy',
                    'clients': len(self.clients),
                    'timestamp': datetime.now().isoformat()
                }))
            
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def handle_solar_panel_processing(self, data):
        """Handle solar panel processing request"""
        logger.info("Starting solar panel processing simulation...")
        
        # Simulate processing steps
        steps = [
            "🔧 Initializing processors...",
            "🖼️ Processing image...",
            "🧠 AI analysis...",
            "📄 Generating results..."
        ]
        
        for i, step in enumerate(steps):
            progress_message = {
                'type': 'processing_progress',
                'step': i + 1,
                'total': len(steps),
                'description': step,
                'percentage': ((i + 1) / len(steps)) * 100
            }
            
            await self.broadcast_message(progress_message)
            await asyncio.sleep(1)  # Simulate work
        
        # Send completion
        completion_message = {
            'type': 'processing_complete',
            'success': True,
            'result': 'Solar panel processing completed successfully',
            'timestamp': datetime.now().isoformat()
        }
        
        await self.broadcast_message(completion_message)
        logger.info("Solar panel processing simulation completed")
    
    async def handle_github_upload(self, data):
        """Handle GitHub upload request"""
        logger.info("Starting GitHub upload simulation...")
        
        upload_message = {
            'type': 'github_upload_progress',
            'status': 'uploading',
            'progress': 50,
            'message': 'Uploading files to GitHub...'
        }
        
        await self.broadcast_message(upload_message)
        await asyncio.sleep(2)  # Simulate upload
        
        completion_message = {
            'type': 'github_upload_complete',
            'success': True,
            'url': 'https://github.com/user/repo/commit/abc123',
            'timestamp': datetime.now().isoformat()
        }
        
        await self.broadcast_message(completion_message)
        logger.info("GitHub upload simulation completed")
    
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
        logger.info(f"Starting WebSocket server on {self.host}:{self.port}")
        
        server = await websockets.serve(
            self.client_handler,
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=10
        )
        
        logger.info("✅ WebSocket server started successfully")
        
        # Keep server running
        await server.wait_closed()
    
    def run(self):
        """Run the server"""
        try:
            asyncio.run(self.start_server())
        except KeyboardInterrupt:
            logger.info("Server shutdown by user")
        except Exception as e:
            logger.error(f"Server error: {e}")

def main():
    """Launch simple WebSocket server"""
    server = SimpleWebSocketServer()
    server.run()

if __name__ == "__main__":
    main()
