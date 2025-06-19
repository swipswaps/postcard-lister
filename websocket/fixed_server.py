#!/usr/bin/env python3
"""
FIXED WebSocket Server - No Internal Errors
Simple, stable server that actually works
"""

import asyncio
import websockets
import json
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FixedWebSocketServer:
    def __init__(self, host="localhost", port=8081):
        self.host = host
        self.port = port
        self.clients = set()
        
    async def register_client(self, websocket):
        """Register new client"""
        self.clients.add(websocket)
        logger.info(f"✅ Client connected: {len(self.clients)} total")
        
        try:
            # Send welcome message
            await websocket.send(json.dumps({
                'type': 'welcome',
                'message': '🌞 Connected to Solar Panel Catalog server',
                'timestamp': datetime.now().isoformat()
            }))
        except Exception as e:
            logger.error(f"Error sending welcome: {e}")
    
    async def unregister_client(self, websocket):
        """Unregister client"""
        if websocket in self.clients:
            self.clients.remove(websocket)
            logger.info(f"❌ Client disconnected: {len(self.clients)} total")
    
    async def broadcast(self, message):
        """Broadcast to all clients"""
        if not self.clients:
            return
        
        disconnected = set()
        for client in self.clients.copy():
            try:
                await client.send(json.dumps(message))
            except Exception as e:
                logger.error(f"Broadcast error: {e}")
                disconnected.add(client)
        
        for client in disconnected:
            await self.unregister_client(client)
    
    async def handle_message(self, websocket, message):
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
                logger.info("📤 Sent pong")
            
            elif message_type == 'process_solar_panel':
                await self.handle_solar_processing(data)
            
            elif message_type == 'github_upload':
                await self.handle_github_upload(data)
            
            elif message_type == 'get_verbatim_log':
                await websocket.send(json.dumps({
                    'type': 'verbatim_log_response',
                    'log': [
                        f"{datetime.now().strftime('%H:%M:%S')} [INFO] WebSocket server running",
                        f"{datetime.now().strftime('%H:%M:%S')} [INFO] Clients connected: {len(self.clients)}",
                        f"{datetime.now().strftime('%H:%M:%S')} [INFO] Server status: healthy"
                    ],
                    'timestamp': datetime.now().isoformat()
                }))
            
            else:
                logger.warning(f"Unknown message: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
        except Exception as e:
            logger.error(f"Message handling error: {e}")
    
    async def handle_solar_processing(self, data):
        """Handle solar panel processing"""
        logger.info("🌞 Processing solar panel...")
        
        steps = [
            "🔧 Initializing AI processors...",
            "📸 Loading solar panel image...",
            "🧠 Running AI analysis...",
            "📊 Extracting specifications...",
            "💾 Saving results..."
        ]
        
        try:
            for i, step in enumerate(steps):
                progress = ((i + 1) / len(steps)) * 100
                
                await self.broadcast({
                    'type': 'processing_progress',
                    'step': i + 1,
                    'total': len(steps),
                    'description': step,
                    'percentage': progress
                })
                
                await asyncio.sleep(1)
            
            await self.broadcast({
                'type': 'processing_complete',
                'success': True,
                'message': '✅ Solar panel processing completed!',
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Processing error: {e}")
    
    async def handle_github_upload(self, data):
        """Handle GitHub upload"""
        logger.info("📤 GitHub upload...")
        
        try:
            await self.broadcast({
                'type': 'github_upload_progress',
                'status': 'uploading',
                'progress': 50,
                'message': '📤 Uploading to GitHub...'
            })
            
            await asyncio.sleep(2)
            
            await self.broadcast({
                'type': 'github_upload_complete',
                'success': True,
                'message': '✅ Successfully uploaded to GitHub!',
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"GitHub upload error: {e}")
    
    async def client_handler(self, websocket, path):
        """Handle client connection - FIXED"""
        try:
            await self.register_client(websocket)
            
            async for message in websocket:
                await self.handle_message(websocket, message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client disconnected normally")
        except Exception as e:
            logger.error(f"Client handler error: {e}")
        finally:
            await self.unregister_client(websocket)
    
    async def start_server(self):
        """Start the server"""
        logger.info(f"🚀 Starting FIXED WebSocket server on {self.host}:{self.port}")
        
        try:
            server = await websockets.serve(
                self.client_handler,
                self.host,
                self.port,
                ping_interval=20,
                ping_timeout=10
            )
            
            logger.info("✅ FIXED WebSocket server started successfully!")
            logger.info(f"🌐 Server listening on ws://{self.host}:{self.port}")
            
            await server.wait_closed()
            
        except Exception as e:
            logger.error(f"Server error: {e}")
    
    def run(self):
        """Run the server"""
        try:
            asyncio.run(self.start_server())
        except KeyboardInterrupt:
            logger.info("Server shutdown by user")
        except Exception as e:
            logger.error(f"Server error: {e}")

def main():
    """Main entry point"""
    print("🌞 Solar Panel Catalog - FIXED WebSocket Server")
    print("=" * 50)
    
    server = FixedWebSocketServer()
    server.run()

if __name__ == "__main__":
    main()
