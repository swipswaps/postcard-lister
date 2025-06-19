#!/usr/bin/env python3
################################################################################
# FILE: run_terminal_system.py
# DESC: Terminal-centric system launcher with self-healing
# SPEC: TERMINAL-CENTRIC-2025-06-18-LAUNCHER
# WHAT: Main launcher for terminal-centric solar panel catalog system
# WHY: Single entry point with self-healing and verbatim capture
# FAIL: Exits with error if system cannot be started
# UX: Rich terminal interface with setup guidance
# DEBUG: Complete verbatim capture and system diagnostics
################################################################################

import sys
import os
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

def echo_info(message):
    """Print info message with terminal formatting"""
    print(f"[INFO]  ℹ️  {message}")

def echo_ok(message):
    """Print success message with terminal formatting"""
    print(f"[PASS]  ✅ {message}")

def echo_warn(message):
    """Print warning message with terminal formatting"""
    print(f"[WARN]  ⚠️  {message}")

def echo_fail(message):
    """Print failure message with terminal formatting"""
    print(f"[FAIL]  ❌ {message}")

def check_dependencies():
    """
    WHAT: Check and self-heal dependencies
    WHY: Ensure all required packages are available
    FAIL: Returns False if critical dependencies cannot be installed
    UX: Shows dependency checking progress
    DEBUG: Logs all dependency operations
    """
    echo_info("🔧 Checking dependencies...")
    
    required_packages = [
        'websockets',
        'asyncio',
        'Pillow',
        'openai',
        'requests'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'asyncio':
                import asyncio
            elif package == 'websockets':
                import websockets
            elif package == 'Pillow':
                import PIL
            elif package == 'openai':
                import openai
            elif package == 'requests':
                import requests
            
            echo_ok(f"{package} - Available")
            
        except ImportError:
            echo_warn(f"{package} - Missing, will install")
            missing_packages.append(package)
    
    # Install missing packages
    if missing_packages:
        echo_info(f"Installing {len(missing_packages)} missing packages...")
        
        for package in missing_packages:
            try:
                echo_info(f"Installing {package}...")
                subprocess.run([
                    sys.executable, '-m', 'pip', 'install', package
                ], check=True, capture_output=True)
                echo_ok(f"{package} - Installed successfully")
                
            except subprocess.CalledProcessError as e:
                echo_fail(f"Failed to install {package}: {e}")
                return False
    
    echo_ok("All dependencies available")
    return True

def check_configuration():
    """
    WHAT: Check if system is configured
    WHY: Ensure setup has been completed
    FAIL: Returns False if configuration is missing
    UX: Shows configuration status
    DEBUG: Logs configuration check results
    """
    echo_info("⚙️ Checking configuration...")
    
    config_path = Path("config/settings.json")
    
    if not config_path.exists():
        echo_warn("Configuration not found")
        echo_info("Run setup: python3 cli/setup.py")
        return False
    
    try:
        import json
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Check required configuration
        if not config.get('openai_api_key'):
            echo_warn("OpenAI API key not configured")
            return False
        
        if not config.get('github_token'):
            echo_warn("GitHub token not configured")
            return False
        
        echo_ok("Configuration validated")
        return True
        
    except Exception as e:
        echo_fail(f"Configuration error: {e}")
        return False

def check_core_modules():
    """
    WHAT: Check if core modules are available
    WHY: Ensure all processing modules can be imported
    FAIL: Returns False if core modules are missing
    UX: Shows module availability
    DEBUG: Logs module import results
    """
    echo_info("📋 Checking core modules...")
    
    core_modules = [
        'core.enhanced_vision_handler',
        'core.multi_llm_analyzer',
        'core.image_processor',
        'core.github_catalog',
        'core.csv_generator'
    ]
    
    for module in core_modules:
        try:
            __import__(module)
            echo_ok(f"{module} - Available")
        except ImportError as e:
            echo_fail(f"{module} - Missing: {e}")
            return False
    
    echo_ok("All core modules available")
    return True

def show_usage():
    """Show usage examples and help"""
    print("\n🌞 SOLAR PANEL CATALOG SYSTEM - TERMINAL INTERFACE")
    print("=" * 60)
    print("Terminal-centric solar panel processing with Material UI mirroring")
    print("=" * 60)
    print()
    print("📋 AVAILABLE COMMANDS:")
    print()
    print("🔧 Setup and Configuration:")
    print("  python3 cli/setup.py                    # Interactive setup")
    print()
    print("🌞 Solar Panel Processing:")
    print("  python3 cli/main.py --input panel.jpg   # Process single panel")
    print("  python3 cli/main.py --input panel.jpg --verbose --github-upload")
    print()
    print("📦 Batch Processing:")
    print("  python3 cli/batch_processor.py --input solar_inventory/")
    print("  python3 cli/batch_processor.py --input solar_inventory/ --workers 8 --verbose")
    print()
    print("🌐 WebSocket Bridge (for Material UI):")
    print("  python3 websocket/server.py             # Start WebSocket bridge")
    print()
    print("🚀 System Launcher:")
    print("  python3 run_terminal_system.py --setup  # Run setup")
    print("  python3 run_terminal_system.py --check  # Check system status")
    print("  python3 run_terminal_system.py --websocket  # Start WebSocket bridge")
    print()
    print("💡 Examples:")
    print("  # Complete workflow")
    print("  python3 run_terminal_system.py --setup")
    print("  python3 cli/main.py --input solar_panel.jpg --verbose --github-upload")
    print()
    print("  # Batch processing with web interface")
    print("  python3 run_terminal_system.py --websocket &")
    print("  python3 cli/batch_processor.py --input solar_inventory/ --verbose")
    print()

def run_setup():
    """Run interactive setup"""
    echo_info("🔧 Starting interactive setup...")
    
    try:
        subprocess.run([sys.executable, 'cli/setup.py'], check=True)
        echo_ok("Setup completed successfully")
        return True
    except subprocess.CalledProcessError:
        echo_fail("Setup failed")
        return False
    except FileNotFoundError:
        echo_fail("Setup script not found: cli/setup.py")
        return False

def run_websocket_bridge():
    """Start WebSocket bridge for Material UI"""
    echo_info("🌐 Starting WebSocket bridge for Material UI...")
    
    try:
        subprocess.run([sys.executable, 'websocket/server.py'], check=True)
    except subprocess.CalledProcessError:
        echo_fail("WebSocket bridge failed")
        return False
    except FileNotFoundError:
        echo_fail("WebSocket server not found: websocket/server.py")
        return False
    except KeyboardInterrupt:
        echo_info("WebSocket bridge stopped by user")
        return True

def main():
    """
    WHAT: Main launcher entry point
    WHY: Single entry point for terminal-centric system
    FAIL: Exits with appropriate error codes
    UX: Rich terminal interface with guidance
    DEBUG: Complete system diagnostics
    """
    parser = argparse.ArgumentParser(
        description="🌞 Solar Panel Catalog System - Terminal Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--setup', action='store_true',
                       help='Run interactive setup')
    parser.add_argument('--check', action='store_true',
                       help='Check system status')
    parser.add_argument('--websocket', action='store_true',
                       help='Start WebSocket bridge for Material UI')
    parser.add_argument('--usage', action='store_true',
                       help='Show usage examples')
    
    args = parser.parse_args()
    
    # Show header
    print("🚀 SOLAR PANEL CATALOG SYSTEM - TERMINAL LAUNCHER")
    print("=" * 60)
    print(f"📅 Started: {datetime.now()}")
    print("=" * 60)
    
    # Handle specific actions
    if args.usage:
        show_usage()
        return
    
    if args.setup:
        if run_setup():
            echo_ok("🎉 Setup completed! System ready for use.")
        else:
            echo_fail("Setup failed. Please check errors above.")
            sys.exit(1)
        return
    
    if args.websocket:
        run_websocket_bridge()
        return
    
    # Default: system check
    echo_info("🔍 Performing system check...")
    
    # Check dependencies
    if not check_dependencies():
        echo_fail("Dependency check failed")
        sys.exit(1)
    
    # Check configuration
    if not check_configuration():
        echo_fail("Configuration check failed")
        echo_info("Run setup: python3 run_terminal_system.py --setup")
        sys.exit(1)
    
    # Check core modules
    if not check_core_modules():
        echo_fail("Core module check failed")
        sys.exit(1)
    
    # System ready
    echo_ok("🎉 System check passed! Terminal-centric system ready.")
    echo_info("Use --usage to see available commands")
    
    print("\n📋 QUICK START:")
    print("  • Process single panel: python3 cli/main.py --input panel.jpg --verbose")
    print("  • Batch process: python3 cli/batch_processor.py --input directory/ --verbose")
    print("  • Start web bridge: python3 run_terminal_system.py --websocket")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        echo_info("Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        echo_fail(f"Unexpected error: {e}")
        import traceback
        print(f"📋 Details: {traceback.format_exc()}")
        sys.exit(1)
