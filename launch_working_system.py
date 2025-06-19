#!/usr/bin/env python3
"""
Launch Working Solar Panel Catalog System
All features working: WebSocket, GitHub upload, verbatim capture
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def log(message):
    """Simple logging with timestamp"""
    timestamp = time.strftime("%H:%M:%S")
    print(f"{timestamp} {message}")

def run_command(cmd, background=False):
    """Run command"""
    log(f"🔧 Running: {' '.join(cmd)}")
    try:
        if background:
            return subprocess.Popen(cmd)
        else:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)
            return result.returncode == 0
    except Exception as e:
        log(f"❌ Command failed: {e}")
        return False

def check_system():
    """Check system components"""
    log("📊 Checking system components...")
    
    checks = [
        ("Git repository", Path('.git').exists()),
        ("WebSocket server", Path('websocket/android_server.py').exists()),
        ("React frontend", Path('frontend/package.json').exists()),
        ("GitHub upload tool", Path('simple_github_upload.py').exists()),
        ("Android interface", Path('frontend/src/AndroidApp.js').exists())
    ]
    
    all_good = True
    for name, exists in checks:
        status = "✅" if exists else "❌"
        log(f"{status} {name}: {'OK' if exists else 'Missing'}")
        if not exists:
            all_good = False
    
    return all_good

def start_websocket_server():
    """Start WebSocket server"""
    log("🚀 Starting WebSocket server...")
    cmd = [sys.executable, "websocket/android_server.py"]
    return run_command(cmd, background=True)

def start_react_app():
    """Start React app"""
    log("🌐 Starting React frontend...")
    os.chdir("frontend")
    process = run_command(["npm", "start"], background=True)
    os.chdir("..")
    return process

def test_github_upload():
    """Test GitHub upload"""
    log("📤 Testing GitHub upload...")
    
    # Create test file
    test_file = "test_github_upload.txt"
    with open(test_file, "w") as f:
        f.write(f"Test GitHub upload - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Run upload
    success = run_command([sys.executable, "simple_github_upload.py"])
    
    # Clean up
    if Path(test_file).exists():
        Path(test_file).unlink()
    
    return success

def show_status():
    """Show system status"""
    print("\n" + "="*60)
    print("🌞 SOLAR PANEL CATALOG - SYSTEM STATUS")
    print("="*60)
    
    # Check WebSocket server
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 8081))
        sock.close()
        ws_status = "✅ Running" if result == 0 else "❌ Not running"
    except:
        ws_status = "❌ Not running"
    
    print(f"WebSocket Server (port 8081): {ws_status}")
    
    # Check React app
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 3000))
        sock.close()
        react_status = "✅ Running" if result == 0 else "❌ Not running"
    except:
        react_status = "❌ Not running"
    
    print(f"React Frontend (port 3000): {react_status}")
    
    # Check git status
    try:
        result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
        if result.returncode == 0:
            changes = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            git_status = f"✅ OK ({changes} uncommitted files)"
        else:
            git_status = "❌ Not a git repository"
    except:
        git_status = "❌ Git not available"
    
    print(f"Git Repository: {git_status}")
    
    print("\n🌐 Web Interface: http://localhost:3000")
    print("🔌 WebSocket Server: ws://localhost:8081")
    print("📤 GitHub Upload: Available via web interface or command line")
    print("📋 Verbatim Logging: Real-time in web interface")

def main():
    """Main function"""
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("🌞 SOLAR PANEL CATALOG - WORKING SYSTEM LAUNCHER")
    print("="*60)
    
    # Check system
    if not check_system():
        log("❌ System check failed. Some components are missing.")
        return 1
    
    log("✅ All system components found!")
    
    # Show menu
    while True:
        print("\n" + "="*40)
        print("📱 ANDROID SOLAR PANEL CATALOG")
        print("="*40)
        print("1. 🚀 Start Complete System")
        print("2. 📤 Test GitHub Upload")
        print("3. 🌐 Open Web Interface")
        print("4. 📊 Show System Status")
        print("5. 🔧 Start WebSocket Server Only")
        print("6. 🖥️ Start Terminal Interface")
        print("0. ❌ Exit")
        print("="*40)
        
        try:
            choice = input("🎯 Enter your choice: ").strip()
        except KeyboardInterrupt:
            log("👋 Goodbye!")
            break
        
        if choice == "1":
            log("🚀 Starting complete system...")
            
            # Start WebSocket server
            ws_process = start_websocket_server()
            if not ws_process:
                log("❌ Failed to start WebSocket server")
                continue
            
            time.sleep(2)  # Give server time to start
            
            # Start React app
            react_process = start_react_app()
            if not react_process:
                log("❌ Failed to start React app")
                continue
            
            log("✅ System started successfully!")
            log("🌐 Web interface: http://localhost:3000")
            log("🔌 WebSocket server: ws://localhost:8081")
            log("📋 Verbatim logging: Available in web interface")
            
            input("\nPress Enter to continue...")
        
        elif choice == "2":
            success = test_github_upload()
            if success:
                log("✅ GitHub upload test completed!")
            else:
                log("❌ GitHub upload test failed")
            input("\nPress Enter to continue...")
        
        elif choice == "3":
            log("🌐 Opening web interface...")
            run_command(["xdg-open", "http://localhost:3000"])
        
        elif choice == "4":
            show_status()
            input("\nPress Enter to continue...")
        
        elif choice == "5":
            ws_process = start_websocket_server()
            if ws_process:
                log("✅ WebSocket server started!")
                log("🔌 Server: ws://localhost:8081")
                input("\nPress Enter to stop server...")
                ws_process.terminate()
            else:
                log("❌ Failed to start WebSocket server")
        
        elif choice == "6":
            log("🖥️ Starting terminal interface...")
            run_command([sys.executable, "terminal_android_ui.py"])
        
        elif choice == "0":
            log("👋 Goodbye!")
            break
        
        else:
            log("❌ Invalid choice")
            time.sleep(1)

if __name__ == "__main__":
    main()
