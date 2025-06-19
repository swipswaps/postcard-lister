#!/usr/bin/env python3
"""
Terminal Android-Style UI for Solar Panel Catalog
Simple ncurses interface with Android-like design
"""

import curses
import subprocess
import sys
import os
import time
from pathlib import Path

class TerminalAndroidUI:
    def __init__(self):
        self.current_menu = 'main'
        self.selected_item = 0
        self.status_message = "Ready"
        self.processing = False
        
    def init_colors(self):
        """Initialize color pairs"""
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)    # Header
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_GREEN)   # Selected
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)   # Success
        curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)     # Error
        curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Warning
        curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)    # Info
    
    def draw_header(self, stdscr):
        """Draw header bar"""
        height, width = stdscr.getmaxyx()
        header = "🌞 SOLAR PANEL CATALOG - ANDROID TERMINAL UI"
        
        # Center the header
        x = max(0, (width - len(header)) // 2)
        stdscr.addstr(0, 0, " " * width, curses.color_pair(1))
        stdscr.addstr(0, x, header, curses.color_pair(1) | curses.A_BOLD)
    
    def draw_status_bar(self, stdscr):
        """Draw status bar at bottom"""
        height, width = stdscr.getmaxyx()
        status = f"Status: {self.status_message}"
        
        stdscr.addstr(height-1, 0, " " * width, curses.color_pair(1))
        stdscr.addstr(height-1, 2, status, curses.color_pair(1))
        
        # Add controls info
        controls = "↑↓: Navigate | Enter: Select | Q: Quit"
        x = max(0, width - len(controls) - 2)
        stdscr.addstr(height-1, x, controls, curses.color_pair(1))
    
    def draw_main_menu(self, stdscr):
        """Draw main menu"""
        height, width = stdscr.getmaxyx()
        
        menu_items = [
            "🚀 Start Complete System",
            "📸 Process Solar Panel",
            "📤 Upload to GitHub",
            "🌐 Open Web Interface",
            "📊 System Status",
            "⚙️ Settings",
            "❌ Exit"
        ]
        
        # Calculate menu position
        menu_height = len(menu_items) + 4
        start_y = max(2, (height - menu_height) // 2)
        start_x = max(0, (width - 40) // 2)
        
        # Draw menu box
        for i in range(menu_height):
            stdscr.addstr(start_y + i, start_x, " " * 40)
        
        # Draw menu title
        title = "📱 MAIN MENU"
        title_x = start_x + (40 - len(title)) // 2
        stdscr.addstr(start_y + 1, title_x, title, curses.A_BOLD | curses.color_pair(6))
        
        # Draw menu items
        for i, item in enumerate(menu_items):
            y = start_y + 3 + i
            x = start_x + 2
            
            if i == self.selected_item:
                stdscr.addstr(y, start_x, " " * 40, curses.color_pair(2))
                stdscr.addstr(y, x, f"► {item}", curses.color_pair(2) | curses.A_BOLD)
            else:
                stdscr.addstr(y, x, f"  {item}")
    
    def draw_processing_screen(self, stdscr):
        """Draw processing screen"""
        height, width = stdscr.getmaxyx()
        
        # Center processing message
        messages = [
            "🔧 Processing Solar Panel...",
            "",
            "Please wait while we analyze your solar panel image.",
            "This may take a few moments.",
            "",
            "Press 'q' to cancel"
        ]
        
        start_y = (height - len(messages)) // 2
        
        for i, msg in enumerate(messages):
            if msg:
                x = max(0, (width - len(msg)) // 2)
                color = curses.color_pair(6) if i == 0 else 0
                stdscr.addstr(start_y + i, x, msg, color | curses.A_BOLD if i == 0 else color)
    
    def draw_github_screen(self, stdscr):
        """Draw GitHub upload screen"""
        height, width = stdscr.getmaxyx()
        
        messages = [
            "📤 GitHub Upload",
            "",
            "Upload your solar panel catalog to GitHub repository.",
            "",
            "Features:",
            "• Automatic git staging and commit",
            "• Real-time upload progress",
            "• Verbatim logging of all operations",
            "",
            "Press Enter to start upload, or 'b' to go back"
        ]
        
        start_y = max(2, (height - len(messages)) // 2)
        
        for i, msg in enumerate(messages):
            if msg:
                x = max(0, (width - len(msg)) // 2)
                if i == 0:
                    stdscr.addstr(start_y + i, x, msg, curses.color_pair(6) | curses.A_BOLD)
                elif msg.startswith("•"):
                    stdscr.addstr(start_y + i, x, msg, curses.color_pair(3))
                else:
                    stdscr.addstr(start_y + i, x, msg)
    
    def draw_status_screen(self, stdscr):
        """Draw system status screen"""
        height, width = stdscr.getmaxyx()
        
        # Check system components
        status_items = []
        
        # Git repository
        if Path('.git').exists():
            status_items.append("✅ Git Repository: OK")
        else:
            status_items.append("❌ Git Repository: Not Found")
        
        # React frontend
        if Path('frontend/package.json').exists():
            status_items.append("✅ React Frontend: OK")
        else:
            status_items.append("❌ React Frontend: Not Found")
        
        # WebSocket server
        if Path('websocket/android_server.py').exists():
            status_items.append("✅ WebSocket Server: OK")
        else:
            status_items.append("❌ WebSocket Server: Not Found")
        
        # GitHub upload tool
        if Path('simple_github_upload.py').exists():
            status_items.append("✅ GitHub Upload Tool: OK")
        else:
            status_items.append("❌ GitHub Upload Tool: Not Found")
        
        messages = ["📊 System Status", ""] + status_items + ["", "Press 'b' to go back"]
        
        start_y = max(2, (height - len(messages)) // 2)
        
        for i, msg in enumerate(messages):
            if msg:
                x = max(0, (width - len(msg)) // 2)
                if i == 0:
                    color = curses.color_pair(6) | curses.A_BOLD
                elif msg.startswith("✅"):
                    color = curses.color_pair(3)
                elif msg.startswith("❌"):
                    color = curses.color_pair(4)
                else:
                    color = 0
                stdscr.addstr(start_y + i, x, msg, color)
    
    def run_command(self, cmd):
        """Run system command"""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)
    
    def handle_main_menu_input(self, key):
        """Handle main menu input"""
        menu_size = 7  # Number of menu items
        
        if key == curses.KEY_UP:
            self.selected_item = (self.selected_item - 1) % menu_size
        elif key == curses.KEY_DOWN:
            self.selected_item = (self.selected_item + 1) % menu_size
        elif key == ord('\n') or key == ord('\r'):
            if self.selected_item == 0:  # Start Complete System
                self.status_message = "Starting system..."
                # Start WebSocket server and React app
                subprocess.Popen([sys.executable, "websocket/android_server.py"])
                time.sleep(1)
                subprocess.Popen(["npm", "start"], cwd="frontend")
                self.status_message = "System started! Check http://localhost:3000"
            elif self.selected_item == 1:  # Process Solar Panel
                self.current_menu = 'processing'
                self.status_message = "Processing mode"
            elif self.selected_item == 2:  # Upload to GitHub
                self.current_menu = 'github'
                self.status_message = "GitHub upload mode"
            elif self.selected_item == 3:  # Open Web Interface
                self.run_command("xdg-open http://localhost:3000")
                self.status_message = "Web interface opened"
            elif self.selected_item == 4:  # System Status
                self.current_menu = 'status'
                self.status_message = "System status"
            elif self.selected_item == 5:  # Settings
                self.status_message = "Settings coming soon..."
            elif self.selected_item == 6:  # Exit
                return False
        
        return True
    
    def handle_other_input(self, key):
        """Handle input for other screens"""
        if key == ord('b') or key == ord('B'):
            self.current_menu = 'main'
            self.status_message = "Back to main menu"
        elif key == ord('\n') or key == ord('\r'):
            if self.current_menu == 'github':
                self.status_message = "Starting GitHub upload..."
                success, stdout, stderr = self.run_command("python3 simple_github_upload.py")
                if success:
                    self.status_message = "GitHub upload completed!"
                else:
                    self.status_message = f"GitHub upload failed: {stderr[:50]}"
        
        return True
    
    def main_loop(self, stdscr):
        """Main UI loop"""
        self.init_colors()
        curses.curs_set(0)  # Hide cursor
        stdscr.timeout(100)  # Non-blocking input
        
        while True:
            stdscr.clear()
            
            # Draw UI components
            self.draw_header(stdscr)
            self.draw_status_bar(stdscr)
            
            if self.current_menu == 'main':
                self.draw_main_menu(stdscr)
            elif self.current_menu == 'processing':
                self.draw_processing_screen(stdscr)
            elif self.current_menu == 'github':
                self.draw_github_screen(stdscr)
            elif self.current_menu == 'status':
                self.draw_status_screen(stdscr)
            
            stdscr.refresh()
            
            # Handle input
            key = stdscr.getch()
            
            if key == ord('q') or key == ord('Q'):
                break
            elif key != -1:  # Key was pressed
                if self.current_menu == 'main':
                    if not self.handle_main_menu_input(key):
                        break
                else:
                    self.handle_other_input(key)
    
    def run(self):
        """Run the terminal UI"""
        try:
            curses.wrapper(self.main_loop)
        except KeyboardInterrupt:
            print("\nGoodbye!")
        except Exception as e:
            print(f"UI Error: {e}")

def main():
    """Main entry point"""
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("🌞 Solar Panel Catalog - Terminal Android UI")
    print("Starting terminal interface...")
    time.sleep(1)
    
    ui = TerminalAndroidUI()
    ui.run()

if __name__ == "__main__":
    main()
