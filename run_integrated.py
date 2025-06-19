#!/usr/bin/env python3
################################################################################
# FILE: run_integrated.py
# DESC: Simple launcher for the integrated postcard lister
# USAGE: python run_integrated.py
################################################################################

import sys
import os

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_modules = [
        ('PyQt5', 'PyQt5.QtWidgets'),
        ('pandas', 'pandas'),
        ('PIL', 'PIL'),
        ('openai', 'openai'),
        ('requests', 'requests')  # For GitHub API
    ]
    
    missing = []
    for name, import_name in required_modules:
        try:
            __import__(import_name)
            print(f"✅ {name} - OK")
        except ImportError:
            print(f"❌ {name} - MISSING")
            missing.append(name)
    
    if missing:
        print(f"\n❌ Missing dependencies: {', '.join(missing)}")
        print("Please install them with: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies satisfied!")
    return True

def check_core_modules():
    """Check if core modules are available"""
    core_modules = [
        'core.vision_handler',
        'core.enhanced_vision_handler',
        'core.multi_llm_analyzer',
        'core.image_processor',
        'core.github_catalog',  # Replaces aws_uploader
        'core.csv_generator',
        'core.utils'
    ]
    
    missing = []
    for module in core_modules:
        try:
            __import__(module)
            print(f"✅ {module} - OK")
        except ImportError as e:
            print(f"❌ {module} - MISSING: {e}")
            missing.append(module)
    
    if missing:
        print(f"\n❌ Missing core modules: {', '.join(missing)}")
        print("Please ensure all core modules are in the core/ directory")
        return False
    
    print("✅ All core modules found!")
    return True

def main():
    """Main launcher function with PRF self-healing"""
    print("🚀 GitHub Catalog System - Self-Healing Launcher")
    print("=" * 50)

    # Try self-healing launcher first
    print("\n🔧 Attempting PRF self-healing startup...")
    try:
        from run_integrated_self_heal import main as self_heal_main
        print("✅ Self-healing launcher available - using PRF-compliant startup")
        self_heal_main()
        return
    except ImportError:
        print("⚠️ Self-healing launcher not found - using basic startup")
    except Exception as e:
        print(f"⚠️ Self-healing startup failed: {e}")
        print("🔄 Falling back to basic startup...")

    # Fallback to basic checks
    print("\n📋 Checking dependencies...")
    if not check_dependencies():
        print("\n🔧 TIP: For automatic dependency installation, run:")
        print("  python3 run_integrated_self_heal.py")
        sys.exit(1)

    print("\n📋 Checking core modules...")
    if not check_core_modules():
        sys.exit(1)

    print("\n🎯 Starting integrated application...")

    try:
        from app_integrated import main as app_main
        app_main()
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
