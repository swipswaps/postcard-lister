#!/usr/bin/env python3
################################################################################
# FILE: self_heal_dependencies.py
# DESC: PRF-compliant self-healing dependency management system
# SPEC: PRF-COMPOSITE-2025-06-18-SELF-HEAL-DEPS
# WHAT: Auto-detects and installs missing Python dependencies
# WHY: Prevents crashes from missing imports; enforces self-healing behavior
# FAIL: Exits with clear error if package installation fails
# UX: Visible progress messages and status feedback
# DEBUG: Logs all installation attempts and results
################################################################################

import sys
import subprocess
import importlib
import os
from pathlib import Path

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

def check_and_install_package(package_name, import_name=None, pip_name=None):
    """
    WHAT: Check if package is available, install if missing
    WHY: Self-healing dependency management per PRF requirements
    FAIL: Returns False if installation fails
    UX: Shows progress and status messages
    DEBUG: Logs import attempts and pip install results
    """
    if import_name is None:
        import_name = package_name
    if pip_name is None:
        pip_name = package_name
    
    try:
        # Try to import the package
        importlib.import_module(import_name)
        echo_ok(f"{package_name} - Already installed")
        return True
    except ImportError:
        echo_warn(f"{package_name} - Missing, attempting self-healing installation...")
        
        try:
            # Attempt to install via pip
            echo_info(f"Installing {pip_name} via pip...")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", pip_name],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Verify installation worked
            importlib.import_module(import_name)
            echo_ok(f"{package_name} - Successfully installed and verified")
            return True
            
        except subprocess.CalledProcessError as e:
            echo_fail(f"{package_name} - pip install failed: {e}")
            echo_fail(f"pip stderr: {e.stderr}")
            return False
        except ImportError:
            echo_fail(f"{package_name} - Installation succeeded but import still fails")
            return False
        except Exception as e:
            echo_fail(f"{package_name} - Unexpected error during installation: {e}")
            return False

def self_heal_all_dependencies():
    """
    WHAT: Check and install all required dependencies for the application
    WHY: Ensures application can run without manual dependency management
    FAIL: Exits with error code if critical dependencies cannot be installed
    UX: Shows comprehensive progress and final status
    DEBUG: Logs all dependency checks and installation attempts
    """
    echo_info("🔧 PRF Self-Healing Dependency Management")
    echo_info("=" * 60)
    
    # Define all required dependencies
    dependencies = [
        # Core GUI framework
        {
            "package": "PyQt5",
            "import": "PyQt5.QtWidgets",
            "pip": "PyQt5>=5.15.0",
            "critical": True
        },
        # Data processing
        {
            "package": "pandas",
            "import": "pandas",
            "pip": "pandas>=1.3.0",
            "critical": True
        },
        # Image processing
        {
            "package": "Pillow",
            "import": "PIL",
            "pip": "Pillow>=8.0.0",
            "critical": True
        },
        # OpenAI API
        {
            "package": "openai",
            "import": "openai",
            "pip": "openai>=1.0.0",
            "critical": True
        },
        # GitHub API (NEW - for catalog system)
        {
            "package": "requests",
            "import": "requests",
            "pip": "requests>=2.25.0",
            "critical": True
        }
    ]
    
    failed_critical = []
    failed_optional = []
    installed_count = 0
    
    echo_info(f"Checking {len(dependencies)} dependencies...")
    
    for dep in dependencies:
        package_name = dep["package"]
        import_name = dep["import"]
        pip_name = dep["pip"]
        is_critical = dep["critical"]
        
        echo_info(f"Checking {package_name}...")
        
        success = check_and_install_package(package_name, import_name, pip_name)
        
        if success:
            installed_count += 1
        else:
            if is_critical:
                failed_critical.append(package_name)
            else:
                failed_optional.append(package_name)
    
    # Report results
    echo_info("=" * 60)
    echo_info("🎯 DEPENDENCY SELF-HEALING RESULTS")
    echo_info("=" * 60)
    
    echo_ok(f"Successfully verified/installed: {installed_count}/{len(dependencies)} packages")
    
    if failed_optional:
        echo_warn(f"Optional packages failed: {', '.join(failed_optional)}")
    
    if failed_critical:
        echo_fail(f"Critical packages failed: {', '.join(failed_critical)}")
        echo_fail("❌ Cannot proceed - critical dependencies missing")
        echo_fail("🔧 Manual intervention required:")
        for pkg in failed_critical:
            echo_fail(f"   pip install {pkg}")
        return False
    
    echo_ok("✅ All critical dependencies satisfied")
    echo_ok("🚀 Application ready to launch")
    return True

def check_python_version():
    """
    WHAT: Verify Python version compatibility
    WHY: Prevents runtime errors from version incompatibility
    FAIL: Returns False if Python version is too old
    UX: Shows version check results
    DEBUG: Logs Python version details
    """
    echo_info("🐍 Checking Python version...")
    
    version = sys.version_info
    min_version = (3, 8)
    
    if version >= min_version:
        echo_ok(f"Python {version.major}.{version.minor}.{version.micro} - Compatible")
        return True
    else:
        echo_fail(f"Python {version.major}.{version.minor}.{version.micro} - Too old")
        echo_fail(f"Minimum required: Python {min_version[0]}.{min_version[1]}")
        return False

def check_virtual_environment():
    """
    WHAT: Check if running in virtual environment
    WHY: Provides information about environment setup
    FAIL: Never fails, just informational
    UX: Shows environment status
    DEBUG: Logs virtual environment detection
    """
    echo_info("🏠 Checking virtual environment...")
    
    # Check for virtual environment indicators
    venv_indicators = [
        ("VIRTUAL_ENV", os.environ.get("VIRTUAL_ENV")),
        ("CONDA_DEFAULT_ENV", os.environ.get("CONDA_DEFAULT_ENV")),
        ("PIPENV_ACTIVE", os.environ.get("PIPENV_ACTIVE"))
    ]
    
    active_venv = None
    for indicator, value in venv_indicators:
        if value:
            active_venv = (indicator, value)
            break
    
    if active_venv:
        echo_ok(f"Virtual environment active: {active_venv[0]}={active_venv[1]}")
    else:
        echo_warn("No virtual environment detected (recommended but not required)")
    
    return True

def main():
    """
    WHAT: Main entry point for self-healing dependency management
    WHY: Orchestrates all dependency checks and installations
    FAIL: Exits with error code if critical checks fail
    UX: Provides comprehensive status and progress feedback
    DEBUG: Logs all operations and results
    """
    echo_info("🚀 PRF-COMPLIANT SELF-HEALING DEPENDENCY MANAGER")
    echo_info("=" * 60)
    echo_info("WHAT: Auto-detects and installs missing Python dependencies")
    echo_info("WHY: Prevents crashes from missing imports per PRF requirements")
    echo_info("=" * 60)
    
    try:
        # Step 1: Check Python version
        if not check_python_version():
            echo_fail("❌ Python version check failed")
            sys.exit(1)
        
        # Step 2: Check virtual environment (informational)
        check_virtual_environment()
        
        # Step 3: Self-heal all dependencies
        if not self_heal_all_dependencies():
            echo_fail("❌ Dependency self-healing failed")
            sys.exit(1)
        
        echo_info("=" * 60)
        echo_ok("🎉 SELF-HEALING COMPLETE - ALL SYSTEMS READY")
        echo_ok("✅ Application can now be launched safely")
        echo_info("=" * 60)
        
        return True
        
    except KeyboardInterrupt:
        echo_warn("⚠️ Self-healing interrupted by user")
        sys.exit(130)
    except Exception as e:
        echo_fail(f"❌ Unexpected error during self-healing: {e}")
        import traceback
        echo_fail(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
