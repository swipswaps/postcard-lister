#!/usr/bin/env python3
"""
REAL GitHub WebSocket Server
Integrates actual git commands with verbatim logging and evidence display
"""

import asyncio
import websockets
import json
import logging
import subprocess
import os
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global client set and verbatim log
clients = set()
verbatim_messages = []

def log_verbatim(message, level="INFO"):
    """Add message to verbatim log with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    log_entry = f"{timestamp} [{level}] {message}"
    verbatim_messages.append(log_entry)
    
    # Keep only last 100 messages to prevent memory issues
    if len(verbatim_messages) > 100:
        verbatim_messages.pop(0)
    
    logger.info(message)
    return log_entry

async def run_git_command(cmd, cwd=None):
    """Run git command with real verbatim capture"""
    if cwd is None:
        cwd = os.getcwd()
    
    log_verbatim(f"🔧 Running: {' '.join(cmd)}")
    
    try:
        # Run command with real capture
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd
        )
        
        stdout, stderr = await process.communicate()
        
        # Log actual output
        if stdout:
            stdout_text = stdout.decode().strip()
            for line in stdout_text.split('\n'):
                if line.strip():
                    log_verbatim(f"📤 STDOUT: {line}")
        
        if stderr:
            stderr_text = stderr.decode().strip()
            for line in stderr_text.split('\n'):
                if line.strip():
                    log_verbatim(f"🚨 STDERR: {line}")
        
        success = process.returncode == 0
        log_verbatim(f"✅ Command {'succeeded' if success else 'failed'} (exit code: {process.returncode})")
        
        return {
            'success': success,
            'returncode': process.returncode,
            'stdout': stdout.decode() if stdout else '',
            'stderr': stderr.decode() if stderr else ''
        }
        
    except Exception as e:
        error_msg = f"❌ Command execution failed: {e}"
        log_verbatim(error_msg, "ERROR")
        return {
            'success': False,
            'returncode': -1,
            'stdout': '',
            'stderr': str(e)
        }

async def get_git_status():
    """Get current git repository status with evidence"""
    log_verbatim("🔍 Checking git repository status...")
    
    # Get current branch
    branch_result = await run_git_command(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])
    current_branch = branch_result['stdout'].strip() if branch_result['success'] else 'unknown'
    
    # Get repository URL
    url_result = await run_git_command(['git', 'remote', 'get-url', 'origin'])
    repo_url = url_result['stdout'].strip() if url_result['success'] else 'unknown'
    
    # Get current commit
    commit_result = await run_git_command(['git', 'rev-parse', 'HEAD'])
    current_commit = commit_result['stdout'].strip()[:8] if commit_result['success'] else 'unknown'
    
    # Get status
    status_result = await run_git_command(['git', 'status', '--porcelain'])
    has_changes = bool(status_result['stdout'].strip()) if status_result['success'] else False
    
    # Get recent commits for evidence
    log_result = await run_git_command(['git', 'log', '--oneline', '-5'])
    recent_commits = log_result['stdout'].strip().split('\n') if log_result['success'] else []
    
    return {
        'branch': current_branch,
        'repo_url': repo_url,
        'current_commit': current_commit,
        'has_changes': has_changes,
        'recent_commits': recent_commits
    }

async def register_client(websocket):
    """Register new client"""
    clients.add(websocket)
    logger.info(f"✅ Client connected: {len(clients)} total")
    
    # Send welcome with current git status
    git_status = await get_git_status()
    
    try:
        await websocket.send(json.dumps({
            'type': 'welcome',
            'message': '🌞 Connected to Solar Panel Catalog server',
            'git_status': git_status,
            'verbatim_log': verbatim_messages[-10:],
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

async def handle_real_github_upload():
    """Handle REAL GitHub upload with actual git commands and evidence"""
    log_verbatim("🚀 Starting REAL GitHub upload with verbatim capture...")
    
    try:
        # Step 1: Get initial status
        await broadcast({
            'type': 'github_upload_progress',
            'status': 'checking',
            'progress': 10,
            'message': '🔍 Checking git repository status...',
            'verbatim_log': verbatim_messages[-5:]
        })
        
        git_status = await get_git_status()
        log_verbatim(f"📊 Repository: {git_status['repo_url']}")
        log_verbatim(f"🌿 Branch: {git_status['branch']}")
        log_verbatim(f"📝 Current commit: {git_status['current_commit']}")
        
        # Step 2: Stage changes
        await broadcast({
            'type': 'github_upload_progress',
            'status': 'staging',
            'progress': 30,
            'message': '📦 Staging all changes...',
            'verbatim_log': verbatim_messages[-5:]
        })
        
        result = await run_git_command(['git', 'add', '.'])
        if not result['success']:
            raise Exception(f"Git add failed: {result['stderr']}")
        
        # Step 3: Check what's staged
        await broadcast({
            'type': 'github_upload_progress',
            'status': 'checking_staged',
            'progress': 40,
            'message': '🔍 Checking staged changes...',
            'verbatim_log': verbatim_messages[-5:]
        })
        
        staged_result = await run_git_command(['git', 'diff', '--cached', '--name-only'])
        staged_files = staged_result['stdout'].strip().split('\n') if staged_result['stdout'].strip() else []
        
        if not staged_files:
            log_verbatim("ℹ️ No changes to commit")
            await broadcast({
                'type': 'github_upload_complete',
                'success': True,
                'message': 'ℹ️ No changes to commit - repository is up to date',
                'evidence': {
                    'staged_files': [],
                    'git_status': git_status,
                    'action': 'no_changes'
                },
                'verbatim_log': verbatim_messages[-10:],
                'timestamp': datetime.now().isoformat()
            })
            return
        
        log_verbatim(f"📁 Files to commit: {len(staged_files)}")
        for file in staged_files[:10]:  # Show first 10 files
            log_verbatim(f"   📄 {file}")
        
        # Step 4: Commit
        commit_msg = f"Solar panel catalog update - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        await broadcast({
            'type': 'github_upload_progress',
            'status': 'committing',
            'progress': 60,
            'message': f'💾 Committing {len(staged_files)} files...',
            'verbatim_log': verbatim_messages[-5:]
        })
        
        result = await run_git_command(['git', 'commit', '-m', commit_msg])
        if not result['success']:
            raise Exception(f"Git commit failed: {result['stderr']}")
        
        # Get new commit hash
        new_commit_result = await run_git_command(['git', 'rev-parse', 'HEAD'])
        new_commit = new_commit_result['stdout'].strip()[:8] if new_commit_result['success'] else 'unknown'
        log_verbatim(f"📝 New commit: {new_commit}")
        
        # Step 5: Push
        await broadcast({
            'type': 'github_upload_progress',
            'status': 'pushing',
            'progress': 80,
            'message': '📤 Pushing to GitHub...',
            'verbatim_log': verbatim_messages[-5:]
        })
        
        result = await run_git_command(['git', 'push', 'origin', git_status['branch']])
        if not result['success']:
            raise Exception(f"Git push failed: {result['stderr']}")
        
        # Step 6: Get final evidence
        final_status = await get_git_status()
        
        # Success with complete evidence
        await broadcast({
            'type': 'github_upload_complete',
            'success': True,
            'message': f'✅ Successfully uploaded {len(staged_files)} files to GitHub!',
            'evidence': {
                'staged_files': staged_files,
                'commit_message': commit_msg,
                'old_commit': git_status['current_commit'],
                'new_commit': new_commit,
                'branch': git_status['branch'],
                'repo_url': git_status['repo_url'],
                'recent_commits': final_status['recent_commits']
            },
            'verbatim_log': verbatim_messages[-15:],
            'timestamp': datetime.now().isoformat()
        })
        
        log_verbatim("✅ GitHub upload completed successfully!")
        
    except Exception as e:
        error_msg = f"❌ GitHub upload failed: {str(e)}"
        log_verbatim(error_msg, "ERROR")
        
        await broadcast({
            'type': 'github_upload_complete',
            'success': False,
            'message': error_msg,
            'evidence': {
                'error': str(e),
                'git_status': await get_git_status()
            },
            'verbatim_log': verbatim_messages[-10:],
            'timestamp': datetime.now().isoformat()
        })

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
            # Run REAL GitHub upload
            await handle_real_github_upload()
        
        elif message_type == 'get_verbatim_log':
            await websocket.send(json.dumps({
                'type': 'verbatim_log_response',
                'log': verbatim_messages[-50:],  # Send more log entries
                'timestamp': datetime.now().isoformat()
            }))
        
        elif message_type == 'get_git_status':
            git_status = await get_git_status()
            await websocket.send(json.dumps({
                'type': 'git_status_response',
                'git_status': git_status,
                'verbatim_log': verbatim_messages[-5:],
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
    
    logger.info(f"🚀 Starting REAL GitHub WebSocket server on {host}:{port}")
    
    # Initialize with current git status
    await get_git_status()
    
    async with websockets.serve(
        client_handler,
        host,
        port,
        ping_interval=20,
        ping_timeout=10
    ) as server:
        logger.info("✅ REAL GitHub WebSocket server started successfully!")
        logger.info(f"🌐 Server listening on ws://{host}:{port}")
        
        # Keep server running
        await asyncio.Future()

def main():
    """Main entry point"""
    print("🌞 Solar Panel Catalog - REAL GitHub WebSocket Server")
    print("=" * 60)
    print("🔧 Features: Real git commands, verbatim logging, evidence display")
    print("📊 Provides: Actual file lists, commit hashes, repository URLs")
    print("=" * 60)
    
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        logger.info("Server shutdown by user")
    except Exception as e:
        logger.error(f"Server error: {e}")

if __name__ == "__main__":
    main()
