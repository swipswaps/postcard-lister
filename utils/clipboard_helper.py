#!/usr/bin/env python3
################################################################################
# FILE: utils/clipboard_helper.py
# DESC: Terminal clipboard operations helper
# WHAT: Cross-platform clipboard operations for terminal users
# WHY: Provide easy copy/paste functionality in terminal interface
# FAIL: Shows manual copy instructions if clipboard tools unavailable
# UX: Seamless clipboard integration with visual feedback
# DEBUG: Verbatim logging of all clipboard operations
################################################################################

import sys
import subprocess
import platform
from pathlib import Path
from datetime import datetime

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.text import Text
except ImportError:
    print("🔧 Installing rich...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'rich'], check=True)
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.text import Text

class ClipboardHelper:
    """
    WHAT: Cross-platform clipboard operations for terminal
    WHY: Enable easy copy/paste in terminal-centric workflow
    FAIL: Provides manual copy instructions if tools unavailable
    UX: Visual feedback and command suggestions
    DEBUG: Complete logging of clipboard operations
    """
    
    def __init__(self):
        self.console = Console()
        self.system = platform.system().lower()
        self.verbatim_log = []
        
        # Detect available clipboard tools
        self.clipboard_tools = self.detect_clipboard_tools()
    
    def log_verbatim(self, message):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"{timestamp} {message}"
        self.verbatim_log.append(log_entry)
    
    def detect_clipboard_tools(self):
        """Detect available clipboard tools on the system"""
        tools = {}
        
        # Linux tools
        if self.system == 'linux':
            # X11 tools
            if self.check_command('xclip'):
                tools['xclip'] = {
                    'copy': ['xclip', '-selection', 'clipboard'],
                    'paste': ['xclip', '-selection', 'clipboard', '-o']
                }
            
            if self.check_command('xsel'):
                tools['xsel'] = {
                    'copy': ['xsel', '--clipboard', '--input'],
                    'paste': ['xsel', '--clipboard', '--output']
                }
            
            # Wayland tools
            if self.check_command('wl-copy'):
                tools['wl-copy'] = {
                    'copy': ['wl-copy'],
                    'paste': ['wl-paste']
                }
        
        # macOS tools
        elif self.system == 'darwin':
            if self.check_command('pbcopy'):
                tools['pbcopy'] = {
                    'copy': ['pbcopy'],
                    'paste': ['pbpaste']
                }
        
        # Windows tools
        elif self.system == 'windows':
            if self.check_command('clip'):
                tools['clip'] = {
                    'copy': ['clip'],
                    'paste': ['powershell', 'Get-Clipboard']
                }
        
        self.log_verbatim(f"🔍 Detected clipboard tools: {list(tools.keys())}")
        return tools
    
    def check_command(self, command):
        """Check if a command is available"""
        try:
            subprocess.run([command, '--version'], 
                         capture_output=True, 
                         timeout=2)
            return True
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
            return False
    
    def copy_to_clipboard(self, text):
        """Copy text to clipboard"""
        if not self.clipboard_tools:
            self.show_manual_copy_instructions(text)
            return False
        
        # Try each available tool
        for tool_name, commands in self.clipboard_tools.items():
            try:
                result = subprocess.run(
                    commands['copy'],
                    input=text,
                    text=True,
                    capture_output=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    self.log_verbatim(f"✅ Copied to clipboard using {tool_name}")
                    self.console.print(f"✅ Copied to clipboard using {tool_name}", style="green")
                    return True
                else:
                    self.log_verbatim(f"❌ {tool_name} failed: {result.stderr}")
                    
            except Exception as e:
                self.log_verbatim(f"❌ {tool_name} error: {e}")
                continue
        
        # If all tools failed
        self.show_manual_copy_instructions(text)
        return False
    
    def paste_from_clipboard(self):
        """Paste text from clipboard"""
        if not self.clipboard_tools:
            self.show_manual_paste_instructions()
            return None
        
        # Try each available tool
        for tool_name, commands in self.clipboard_tools.items():
            try:
                result = subprocess.run(
                    commands['paste'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    content = result.stdout.strip()
                    self.log_verbatim(f"✅ Pasted from clipboard using {tool_name}")
                    self.console.print(f"✅ Pasted from clipboard using {tool_name}", style="green")
                    return content
                else:
                    self.log_verbatim(f"❌ {tool_name} failed: {result.stderr}")
                    
            except Exception as e:
                self.log_verbatim(f"❌ {tool_name} error: {e}")
                continue
        
        # If all tools failed
        self.show_manual_paste_instructions()
        return None
    
    def show_manual_copy_instructions(self, text):
        """Show manual copy instructions when clipboard tools unavailable"""
        instructions_panel = Panel(
            "📋 Manual Copy Instructions\n\n"
            "Clipboard tools not available. Please copy manually:\n\n"
            f"1. Select the text below:\n"
            f"2. Use Ctrl+C (Linux/Windows) or Cmd+C (macOS)\n\n"
            f"Text to copy:\n{text}",
            title="📋 Manual Copy Required",
            style="yellow"
        )
        self.console.print(instructions_panel)
        
        # Show platform-specific commands
        self.show_clipboard_commands()
        
        Prompt.ask("Press Enter when you've copied the text")
    
    def show_manual_paste_instructions(self):
        """Show manual paste instructions"""
        instructions_panel = Panel(
            "📋 Manual Paste Instructions\n\n"
            "Clipboard tools not available. Please:\n\n"
            "1. Use Ctrl+V (Linux/Windows) or Cmd+V (macOS)\n"
            "2. Or type/paste the content manually",
            title="📋 Manual Paste Required",
            style="yellow"
        )
        self.console.print(instructions_panel)
        
        # Show platform-specific commands
        self.show_clipboard_commands()
        
        return Prompt.ask("Enter the pasted content")
    
    def show_clipboard_commands(self):
        """Show platform-specific clipboard commands"""
        commands_text = ""
        
        if self.system == 'linux':
            commands_text = """
🐧 Linux Clipboard Commands:

X11 (most desktop environments):
  Copy: echo "text" | xclip -selection clipboard
  Paste: xclip -selection clipboard -o

Alternative (xsel):
  Copy: echo "text" | xsel --clipboard --input
  Paste: xsel --clipboard --output

Wayland (newer systems):
  Copy: echo "text" | wl-copy
  Paste: wl-paste

Install tools:
  Ubuntu/Debian: sudo apt install xclip xsel wl-clipboard
  Fedora: sudo dnf install xclip xsel wl-clipboard
  Arch: sudo pacman -S xclip xsel wl-clipboard
"""
        
        elif self.system == 'darwin':
            commands_text = """
🍎 macOS Clipboard Commands:

Built-in tools (always available):
  Copy: echo "text" | pbcopy
  Paste: pbpaste

Terminal shortcuts:
  Copy: Cmd+C
  Paste: Cmd+V
"""
        
        elif self.system == 'windows':
            commands_text = """
🪟 Windows Clipboard Commands:

Command Prompt:
  Copy: echo text | clip
  Paste: powershell Get-Clipboard

PowerShell:
  Copy: "text" | Set-Clipboard
  Paste: Get-Clipboard

Terminal shortcuts:
  Copy: Ctrl+C
  Paste: Ctrl+V
"""
        
        else:
            commands_text = """
❓ Unknown System

Try these common approaches:
  - Ctrl+C / Ctrl+V (most systems)
  - Cmd+C / Cmd+V (macOS)
  - Right-click context menu
"""
        
        commands_panel = Panel(
            commands_text.strip(),
            title="💻 Platform-Specific Commands",
            style="blue"
        )
        self.console.print(commands_panel)
    
    def copy_file_path(self, file_path):
        """Copy file path to clipboard"""
        path_str = str(Path(file_path).absolute())
        success = self.copy_to_clipboard(path_str)
        
        if success:
            self.console.print(f"📁 File path copied: {path_str}", style="green")
        
        return success
    
    def copy_command(self, command):
        """Copy terminal command to clipboard"""
        success = self.copy_to_clipboard(command)
        
        if success:
            self.console.print(f"⌨️ Command copied: {command}", style="green")
        
        return success
    
    def copy_multiline_text(self, lines):
        """Copy multiple lines of text"""
        text = "\n".join(lines)
        success = self.copy_to_clipboard(text)
        
        if success:
            self.console.print(f"📄 {len(lines)} lines copied to clipboard", style="green")
        
        return success
    
    def show_clipboard_status(self):
        """Show clipboard tool status"""
        status_panel = Panel(
            f"🔧 Clipboard Tool Status\n\n"
            f"System: {self.system.title()}\n"
            f"Available tools: {len(self.clipboard_tools)}\n\n"
            f"Tools detected:\n" + 
            "\n".join([f"  ✅ {tool}" for tool in self.clipboard_tools.keys()]) +
            (f"\n\n❌ No clipboard tools detected" if not self.clipboard_tools else ""),
            title="📋 Clipboard Status",
            style="cyan"
        )
        self.console.print(status_panel)
    
    def interactive_clipboard_test(self):
        """Interactive clipboard functionality test"""
        self.console.clear()
        self.console.print("🧪 [bold cyan]Clipboard Functionality Test[/bold cyan]")
        
        self.show_clipboard_status()
        
        # Test copy
        test_text = f"Test clipboard content - {datetime.now().strftime('%H:%M:%S')}"
        self.console.print(f"\n📤 Testing copy operation...")
        copy_success = self.copy_to_clipboard(test_text)
        
        if copy_success:
            # Test paste
            self.console.print(f"\n📥 Testing paste operation...")
            pasted_text = self.paste_from_clipboard()
            
            if pasted_text == test_text:
                self.console.print("✅ Clipboard test successful!", style="green")
            else:
                self.console.print("⚠️ Clipboard content mismatch", style="yellow")
                self.console.print(f"Expected: {test_text}")
                self.console.print(f"Got: {pasted_text}")
        else:
            self.console.print("❌ Clipboard copy test failed", style="red")

def main():
    """Test clipboard helper"""
    helper = ClipboardHelper()
    helper.interactive_clipboard_test()

if __name__ == "__main__":
    main()
