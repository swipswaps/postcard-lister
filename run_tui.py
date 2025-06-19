#!/usr/bin/env python3
################################################################################
# FILE: run_tui.py
# DESC: Launch Terminal User Interface for Solar Panel Catalog System
# WHAT: Start the visual terminal GUI with forms, buttons, and image display
# WHY: No command memorization - visual interface in terminal
# FAIL: Falls back to command-line help if TUI fails
# UX: Material UI-style forms and buttons in terminal
################################################################################

import sys
import os
from pathlib import Path

def check_dependencies():
    """Check and install TUI dependencies"""
    required_packages = ['rich', 'textual', 'Pillow']
    missing = []
    
    for package in required_packages:
        try:
            if package == 'Pillow':
                import PIL
            else:
                __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print("🔧 Installing TUI dependencies...")
        import subprocess
        for package in missing:
            subprocess.run([sys.executable, '-m', 'pip', 'install', package], check=True)
        print("✅ Dependencies installed!")

def main():
    """Launch the Terminal User Interface"""
    print("🌞 Solar Panel Catalog System - Terminal GUI")
    print("=" * 50)
    
    # Check dependencies
    try:
        check_dependencies()
    except Exception as e:
        print(f"❌ Failed to install dependencies: {e}")
        print("💡 Try running: pip install rich textual Pillow")
        return 1
    
    # Launch TUI
    try:
        from tui.main import SolarPanelTUI
        app = SolarPanelTUI()
        app.run()
        return 0
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        return 0
    except Exception as e:
        print(f"❌ TUI Error: {e}")
        print("\n💡 Fallback options:")
        print("   • python3 cli/main.py --help")
        print("   • python3 run_terminal_system.py --usage")
        return 1

if __name__ == "__main__":
    sys.exit(main())
