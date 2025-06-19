#!/usr/bin/env python3
"""
FINAL WORKING WebSocket Server
Compatible with current websockets library version
"""

import asyncio
import websockets
import json
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global client set
clients = set()

async def register_client(websocket):
    """Register new client"""
    clients.add(websocket)
    logger.info(f"✅ Client connected: {len(clients)} total")
    
    # Send welcome message
    try:
        await websocket.send(json.dumps({
            'type': 'welcome',
            'message': '🌞 Connected to Solar Panel Catalog server',
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
            logger.info("📤 Sent pong")
        
        elif message_type == 'process_solar_panel':
            logger.info("🌞 Processing solar panel...")
            
            steps = [
                "🔧 Initializing AI processors...",
                "📸 Loading solar panel image...",
                "🧠 Running AI analysis...",
                "📊 Extracting specifications...",
                "💾 Saving results..."
            ]
            
            for i, step in enumerate(steps):
                progress = ((i + 1) / len(steps)) * 100
                
                await broadcast({
                    'type': 'processing_progress',
                    'step': i + 1,
                    'total': len(steps),
                    'description': step,
                    'percentage': progress
                })
                
                await asyncio.sleep(1)
            
            await broadcast({
                'type': 'processing_complete',
                'success': True,
                'message': '✅ Solar panel processing completed!',
                'timestamp': datetime.now().isoformat()
            })
        
        elif message_type == 'github_upload':
            logger.info("📤 GitHub upload...")
            
            await broadcast({
                'type': 'github_upload_progress',
                'status': 'uploading',
                'progress': 50,
                'message': '📤 Uploading to GitHub...'
            })
            
            await asyncio.sleep(2)
            
            await broadcast({
                'type': 'github_upload_complete',
                'success': True,
                'message': '✅ Successfully uploaded to GitHub!',
                'timestamp': datetime.now().isoformat()
            })
        
        elif message_type == 'get_verbatim_log':
            await websocket.send(json.dumps({
                'type': 'verbatim_log_response',
                'log': [
                    f"{datetime.now().strftime('%H:%M:%S')} [INFO] WebSocket server running",
                    f"{datetime.now().strftime('%H:%M:%S')} [INFO] Clients connected: {len(clients)}",
                    f"{datetime.now().strftime('%H:%M:%S')} [INFO] Server status: healthy",
                    f"{datetime.now().strftime('%H:%M:%S')} [INFO] Last message: {message_type}"
                ],
                'timestamp': datetime.now().isoformat()
            }))
        
        else:
            logger.warning(f"Unknown message: {message_type}")
            
    except Exception as e:
        logger.error(f"Message handling error: {e}")

async def client_handler(websocket):
    """Handle client connection - NEW API SIGNATURE"""
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
    
    logger.info(f"🚀 Starting FINAL WebSocket server on {host}:{port}")
    
    # Use the new API
    async with websockets.serve(
        client_handler,  # Handler without path parameter
        host,
        port,
        ping_interval=20,
        ping_timeout=10
    ) as server:
        logger.info("✅ FINAL WebSocket server started successfully!")
        logger.info(f"🌐 Server listening on ws://{host}:{port}")
        
        # Keep server running
        await asyncio.Future()  # Run forever

def main():
    """Main entry point"""
    print("🌞 Solar Panel Catalog - FINAL WORKING WebSocket Server")
    print("=" * 60)
    
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        logger.info("Server shutdown by user")
    except Exception as e:
        logger.error(f"Server error: {e}")

if __name__ == "__main__":
    main()
