#!/usr/bin/env python3
################################################################################
# FILE: run_integrated_self_heal.py
# DESC: PRF-compliant self-healing launcher for integrated application
# SPEC: PRF-COMPOSITE-2025-06-18-SELF-HEAL-LAUNCHER
# WHAT: Launches integrated application with automatic dependency management
# WHY: Prevents crashes from missing imports; enforces self-healing behavior
# FAIL: Exits with clear error if self-healing fails
# UX: Visible progress messages and status feedback
# DEBUG: Logs all dependency checks and application startup
################################################################################

import sys
import os
import subprocess
import importlib

def echo_info(message):
    """Print info message with PRF formatting"""
    print(f"[INFO]  ℹ️  {message}")

def echo_ok(message):
    """Print success message with PRF formatting"""
    print(f"[PASS]  ✅ {message}")

def echo_warn(message):
    """Print warning message with PRF formatting"""
    print(f"[WARN]  ⚠️  {message}")

def echo_fail(message):
    """Print failure message with PRF formatting"""
    print(f"[FAIL]  ❌ {message}")

def self_heal_package(package_name, import_name=None, pip_name=None):
    """
    WHAT: Self-healing package installation
    WHY: Automatically installs missing dependencies per PRF requirements
    FAIL: Returns False if installation fails
    UX: Shows installation progress and results
    DEBUG: Logs pip install attempts and results
    """
    if import_name is None:
        import_name = package_name
    if pip_name is None:
        pip_name = package_name
    
    try:
        # Try to import the package
        importlib.import_module(import_name)
        echo_ok(f"{package_name} - Already available")
        return True
    except ImportError:
        echo_warn(f"{package_name} - Missing, initiating self-healing...")
        
        try:
            # Self-heal by installing via pip
            echo_info(f"Self-healing: pip install {pip_name}")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", pip_name],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Verify self-healing worked
            importlib.import_module(import_name)
            echo_ok(f"{package_name} - Self-healing successful")
            return True
            
        except subprocess.CalledProcessError as e:
            echo_fail(f"{package_name} - Self-healing failed: {e}")
            return False
        except ImportError:
            echo_fail(f"{package_name} - Self-healing completed but import still fails")
            return False
        except Exception as e:
            echo_fail(f"{package_name} - Unexpected self-healing error: {e}")
            return False

def self_heal_all_dependencies():
    """
    WHAT: Self-heal all required dependencies for GitHub catalog system
    WHY: Ensures application can run without manual intervention
    FAIL: Returns False if critical dependencies cannot be self-healed
    UX: Shows comprehensive self-healing progress
    DEBUG: Logs all dependency self-healing attempts
    """
    echo_info("🔧 PRF Self-Healing Dependency Management")
    echo_info("=" * 60)
    
    # Updated dependencies for GitHub catalog system
    dependencies = [
        # Core GUI framework
        ("PyQt5", "PyQt5.QtWidgets", "PyQt5>=5.15.0"),
        # Data processing
        ("pandas", "pandas", "pandas>=1.3.0"),
        # Image processing
        ("Pillow", "PIL", "Pillow>=8.0.0"),
        # OpenAI API
        ("openai", "openai", "openai>=1.0.0"),
        # GitHub API (CRITICAL for new catalog system)
        ("requests", "requests", "requests>=2.25.0")
    ]
    
    failed_packages = []
    healed_packages = []
    
    echo_info(f"Self-healing {len(dependencies)} dependencies...")
    
    for package_name, import_name, pip_name in dependencies:
        echo_info(f"Checking {package_name}...")
        
        if self_heal_package(package_name, import_name, pip_name):
            healed_packages.append(package_name)
        else:
            failed_packages.append(package_name)
    
    # Report self-healing results
    echo_info("=" * 60)
    echo_info("🎯 SELF-HEALING RESULTS")
    echo_info("=" * 60)
    
    echo_ok(f"Successfully healed: {len(healed_packages)}/{len(dependencies)} packages")
    
    if failed_packages:
        echo_fail(f"Self-healing failed for: {', '.join(failed_packages)}")
        echo_fail("❌ Cannot proceed - critical dependencies could not be self-healed")
        echo_fail("🔧 Manual intervention required:")
        for pkg in failed_packages:
            echo_fail(f"   pip install {pkg}")
        return False
    
    echo_ok("✅ All dependencies self-healed successfully")
    return True

def check_core_modules():
    """
    WHAT: Check availability of core application modules
    WHY: Ensures application modules are present before launch
    FAIL: Returns False if core modules are missing
    UX: Shows module availability status
    DEBUG: Logs module import attempts
    """
    echo_info("📋 Checking core modules...")
    
    # Updated core modules for GitHub catalog system
    core_modules = [
        'core.vision_handler',
        'core.enhanced_vision_handler',  # NEW
        'core.multi_llm_analyzer',       # NEW
        'core.image_processor',
        'core.github_catalog',           # NEW (replaces aws_uploader)
        'core.csv_generator',
        'core.utils'
    ]
    
    missing = []
    for module in core_modules:
        try:
            importlib.import_module(module)
            echo_ok(f"{module} - Available")
        except ImportError as e:
            echo_fail(f"{module} - Missing: {e}")
            missing.append(module)
    
    if missing:
        echo_fail(f"Missing core modules: {', '.join(missing)}")
        echo_fail("Please ensure all core modules are in the core/ directory")
        return False
    
    echo_ok("All core modules available")
    return True

def check_configuration():
    """
    WHAT: Check if configuration system is working
    WHY: Ensures configuration files are accessible
    FAIL: Returns False if configuration is broken
    UX: Shows configuration status
    DEBUG: Logs configuration loading attempts
    """
    echo_info("⚙️ Checking configuration system...")
    
    try:
        # Check if config directory exists
        if not os.path.exists("config"):
            echo_fail("config/ directory missing")
            return False
        
        # Check if settings files exist
        if not os.path.exists("config/settings.json"):
            echo_warn("config/settings.json missing - will be created from template")
        
        if not os.path.exists("config/settings.template.json"):
            echo_fail("config/settings.template.json missing")
            return False
        
        echo_ok("Configuration system ready")
        return True
        
    except Exception as e:
        echo_fail(f"Configuration check failed: {e}")
        return False

def launch_application():
    """
    WHAT: Launch the integrated application
    WHY: Start the main application after all checks pass
    FAIL: Exits with error if application launch fails
    UX: Shows application startup status
    DEBUG: Logs application launch attempts and errors
    """
    echo_info("🚀 Launching integrated application...")
    
    try:
        from app_integrated import main as app_main
        echo_ok("Application module loaded successfully")
        
        echo_info("Starting GUI application...")
        app_main()
        
    except ImportError as e:
        echo_fail(f"Failed to import application: {e}")
        echo_fail("Please ensure app_integrated.py is present")
        sys.exit(1)
    except Exception as e:
        echo_fail(f"Application launch failed: {e}")
        import traceback
        echo_fail(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

def main():
    """
    WHAT: Main entry point for PRF-compliant self-healing launcher
    WHY: Orchestrates all self-healing checks and application launch
    FAIL: Exits with appropriate error codes if any step fails
    UX: Provides comprehensive startup feedback
    DEBUG: Logs all startup operations and results
    """
    echo_info("🚀 PRF-COMPLIANT SELF-HEALING LAUNCHER")
    echo_info("=" * 60)
    echo_info("WHAT: GitHub Catalog System with Self-Healing Dependencies")
    echo_info("WHY: Prevents crashes from missing imports per PRF requirements")
    echo_info("=" * 60)
    
    try:
        # Step 1: Self-heal all dependencies
        echo_info("Step 1: Self-healing dependencies...")
        if not self_heal_all_dependencies():
            echo_fail("❌ Dependency self-healing failed")
            sys.exit(1)
        
        # Step 2: Check core modules
        echo_info("Step 2: Checking core modules...")
        if not check_core_modules():
            echo_fail("❌ Core module check failed")
            sys.exit(1)
        
        # Step 3: Check configuration
        echo_info("Step 3: Checking configuration...")
        if not check_configuration():
            echo_fail("❌ Configuration check failed")
            sys.exit(1)
        
        # Step 4: Launch application
        echo_info("Step 4: Launching application...")
        echo_info("=" * 60)
        echo_ok("🎉 ALL SELF-HEALING CHECKS PASSED")
        echo_ok("✅ Launching GitHub Catalog System...")
        echo_info("=" * 60)
        
        launch_application()
        
    except KeyboardInterrupt:
        echo_warn("⚠️ Startup interrupted by user")
        sys.exit(130)
    except Exception as e:
        echo_fail(f"❌ Unexpected startup error: {e}")
        import traceback
        echo_fail(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
