#!/usr/bin/env python3
"""
Android-Style Solar Panel Catalog System Launcher
Simple, reliable system with Android-like interface
"""

import subprocess
import sys
import os
import time
import signal
from pathlib import Path

class AndroidSystemLauncher:
    def __init__(self):
        self.processes = []
        self.running = True
        
    def log(self, message, level="INFO"):
        """Simple logging"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"{timestamp} [{level}] {message}")
    
    def run_command(self, cmd, background=False):
        """Run command"""
        self.log(f"Running: {' '.join(cmd)}")
        try:
            if background:
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.processes.append(process)
                return process
            else:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.stdout:
                    print(result.stdout)
                if result.stderr:
                    print(result.stderr)
                return result.returncode == 0
        except Exception as e:
            self.log(f"Command failed: {e}", "ERROR")
            return False
    
    def start_websocket_server(self):
        """Start WebSocket server"""
        self.log("🚀 Starting WebSocket server...")
        cmd = [sys.executable, "websocket/android_server.py"]
        return self.run_command(cmd, background=True)
    
    def start_react_app(self):
        """Start React frontend"""
        self.log("🌐 Starting React frontend...")
        os.chdir("frontend")
        cmd = ["npm", "start"]
        process = self.run_command(cmd, background=True)
        os.chdir("..")
        return process
    
    def github_upload(self):
        """Simple GitHub upload"""
        self.log("📤 Starting GitHub upload...")
        cmd = [sys.executable, "simple_github_upload.py"]
        return self.run_command(cmd)
    
    def show_menu(self):
        """Show main menu"""
        print("\n" + "="*60)
        print("🌞 SOLAR PANEL CATALOG - ANDROID SYSTEM")
        print("="*60)
        print("1. 🚀 Start Complete System (WebSocket + React)")
        print("2. 📤 Upload to GitHub")
        print("3. 🔧 Test WebSocket Server Only")
        print("4. 🌐 Open Web Interface")
        print("5. 📊 Check System Status")
        print("6. 🛑 Stop All Services")
        print("0. ❌ Exit")
        print("="*60)
    
    def check_system_status(self):
        """Check system status"""
        self.log("📊 Checking system status...")
        
        # Check if git repo
        if Path('.git').exists():
            print("✅ Git repository: OK")
        else:
            print("❌ Git repository: Not found")
        
        # Check if React app exists
        if Path('frontend/package.json').exists():
            print("✅ React frontend: OK")
        else:
            print("❌ React frontend: Not found")
        
        # Check if WebSocket server exists
        if Path('websocket/android_server.py').exists():
            print("✅ WebSocket server: OK")
        else:
            print("❌ WebSocket server: Not found")
        
        # Check running processes
        print(f"🔧 Active processes: {len(self.processes)}")
        for i, process in enumerate(self.processes):
            if process.poll() is None:
                print(f"   Process {i+1}: Running")
            else:
                print(f"   Process {i+1}: Stopped")
    
    def stop_all_services(self):
        """Stop all running services"""
        self.log("🛑 Stopping all services...")
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass
        self.processes.clear()
        self.log("✅ All services stopped")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.log(f"Received signal {signum}, shutting down...")
        self.running = False
        self.stop_all_services()
        sys.exit(0)
    
    def run(self):
        """Main run loop"""
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        try:
            while self.running:
                self.show_menu()
                try:
                    choice = input("\n🎯 Enter your choice: ").strip()
                except KeyboardInterrupt:
                    self.log("Shutdown requested by user")
                    break
                
                if choice == "1":
                    self.log("🚀 Starting complete system...")
                    ws_process = self.start_websocket_server()
                    time.sleep(2)  # Give WebSocket time to start
                    react_process = self.start_react_app()
                    
                    if ws_process and react_process:
                        self.log("✅ System started successfully!")
                        self.log("🌐 Web interface: http://localhost:3000")
                        self.log("🔌 WebSocket server: ws://localhost:8081")
                        input("\nPress Enter to continue...")
                    else:
                        self.log("❌ Failed to start system", "ERROR")
                
                elif choice == "2":
                    success = self.github_upload()
                    if success:
                        self.log("✅ GitHub upload completed!")
                    else:
                        self.log("❌ GitHub upload failed", "ERROR")
                    input("\nPress Enter to continue...")
                
                elif choice == "3":
                    ws_process = self.start_websocket_server()
                    if ws_process:
                        self.log("✅ WebSocket server started!")
                        self.log("🔌 Server: ws://localhost:8081")
                        input("\nPress Enter to stop server...")
                        ws_process.terminate()
                    else:
                        self.log("❌ Failed to start WebSocket server", "ERROR")
                
                elif choice == "4":
                    self.log("🌐 Opening web interface...")
                    self.run_command(["xdg-open", "http://localhost:3000"])
                
                elif choice == "5":
                    self.check_system_status()
                    input("\nPress Enter to continue...")
                
                elif choice == "6":
                    self.stop_all_services()
                    input("\nPress Enter to continue...")
                
                elif choice == "0":
                    self.log("👋 Goodbye!")
                    break
                
                else:
                    self.log("❌ Invalid choice", "ERROR")
                    time.sleep(1)
        
        except Exception as e:
            self.log(f"System error: {e}", "ERROR")
        finally:
            self.stop_all_services()

def main():
    """Main entry point"""
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    launcher = AndroidSystemLauncher()
    launcher.run()

if __name__ == "__main__":
    main()
