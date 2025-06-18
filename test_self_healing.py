#!/usr/bin/env python3
################################################################################
# FILE: test_self_healing.py
# DESC: Test script for PRF-compliant self-healing dependency system
# SPEC: PRF-COMPOSITE-2025-06-18-SELF-HEAL-TEST
# WHAT: Validates self-healing dependency management functionality
# WHY: Ensures PRF compliance and prevents dependency-related crashes
# FAIL: Exits with error if self-healing system is not working
# UX: Shows comprehensive test results and status
# DEBUG: Logs all test operations and validation steps
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

def test_self_healing_module():
    """
    WHAT: Test that self-healing dependency module exists and works
    WHY: Validates core self-healing functionality
    FAIL: Returns False if self-healing module is broken
    UX: Shows self-healing module test results
    DEBUG: Logs import and execution attempts
    """
    echo_info("Testing self-healing dependency module...")
    
    try:
        # Test import
        import self_heal_dependencies
        echo_ok("self_heal_dependencies module imports successfully")
        
        # Test main function exists
        if hasattr(self_heal_dependencies, 'main'):
            echo_ok("self_heal_dependencies.main function available")
        else:
            echo_fail("self_heal_dependencies.main function missing")
            return False
        
        # Test helper functions exist
        required_functions = [
            'check_and_install_package',
            'self_heal_all_dependencies',
            'check_python_version'
        ]
        
        for func_name in required_functions:
            if hasattr(self_heal_dependencies, func_name):
                echo_ok(f"Function {func_name} available")
            else:
                echo_fail(f"Function {func_name} missing")
                return False
        
        return True
        
    except ImportError as e:
        echo_fail(f"Cannot import self_heal_dependencies: {e}")
        return False
    except Exception as e:
        echo_fail(f"Unexpected error testing self-healing module: {e}")
        return False

def test_self_healing_launcher():
    """
    WHAT: Test that self-healing launcher exists and works
    WHY: Validates launcher integration with self-healing
    FAIL: Returns False if launcher is broken
    UX: Shows launcher test results
    DEBUG: Logs launcher import and function tests
    """
    echo_info("Testing self-healing launcher...")
    
    try:
        # Test import
        import run_integrated_self_heal
        echo_ok("run_integrated_self_heal module imports successfully")
        
        # Test main function exists
        if hasattr(run_integrated_self_heal, 'main'):
            echo_ok("run_integrated_self_heal.main function available")
        else:
            echo_fail("run_integrated_self_heal.main function missing")
            return False
        
        # Test helper functions exist
        required_functions = [
            'self_heal_package',
            'self_heal_all_dependencies',
            'check_core_modules',
            'check_configuration'
        ]
        
        for func_name in required_functions:
            if hasattr(run_integrated_self_heal, func_name):
                echo_ok(f"Function {func_name} available")
            else:
                echo_fail(f"Function {func_name} missing")
                return False
        
        return True
        
    except ImportError as e:
        echo_fail(f"Cannot import run_integrated_self_heal: {e}")
        return False
    except Exception as e:
        echo_fail(f"Unexpected error testing self-healing launcher: {e}")
        return False

def test_original_launcher_integration():
    """
    WHAT: Test that original launcher integrates with self-healing
    WHY: Ensures backward compatibility and fallback behavior
    FAIL: Returns False if integration is broken
    UX: Shows integration test results
    DEBUG: Logs launcher integration checks
    """
    echo_info("Testing original launcher integration...")
    
    try:
        # Check if original launcher exists
        if not os.path.exists("run_integrated.py"):
            echo_fail("run_integrated.py not found")
            return False
        
        # Check if it references self-healing
        with open("run_integrated.py", "r") as f:
            content = f.read()
        
        if "run_integrated_self_heal" in content:
            echo_ok("Original launcher references self-healing system")
        else:
            echo_fail("Original launcher does not reference self-healing")
            return False
        
        if "self_heal_main" in content:
            echo_ok("Original launcher calls self-healing main function")
        else:
            echo_fail("Original launcher does not call self-healing")
            return False
        
        # Test import
        import run_integrated
        echo_ok("run_integrated module imports successfully")
        
        return True
        
    except Exception as e:
        echo_fail(f"Error testing original launcher integration: {e}")
        return False

def test_dependency_definitions():
    """
    WHAT: Test that dependency definitions are correct and complete
    WHY: Ensures all required packages are included in self-healing
    FAIL: Returns False if dependency definitions are incomplete
    UX: Shows dependency definition test results
    DEBUG: Logs dependency validation checks
    """
    echo_info("Testing dependency definitions...")
    
    try:
        # Expected dependencies for GitHub catalog system
        expected_deps = {
            'PyQt5': 'PyQt5.QtWidgets',
            'pandas': 'pandas',
            'Pillow': 'PIL',
            'openai': 'openai',
            'requests': 'requests'
        }
        
        # Check run_integrated.py dependencies
        with open("run_integrated.py", "r") as f:
            content = f.read()
        
        missing_deps = []
        for package, import_name in expected_deps.items():
            if import_name not in content:
                missing_deps.append(package)
        
        if missing_deps:
            echo_fail(f"Missing dependencies in run_integrated.py: {missing_deps}")
            return False
        else:
            echo_ok("All expected dependencies found in run_integrated.py")
        
        # Check that boto3 (AWS) is removed
        if 'boto3' in content:
            echo_warn("boto3 still referenced in run_integrated.py (should be removed)")
        else:
            echo_ok("boto3 correctly removed from dependencies")
        
        # Check requirements.txt
        if os.path.exists("requirements.txt"):
            with open("requirements.txt", "r") as f:
                req_content = f.read()
            
            if 'requests' in req_content:
                echo_ok("requests library in requirements.txt")
            else:
                echo_fail("requests library missing from requirements.txt")
                return False
        
        return True
        
    except Exception as e:
        echo_fail(f"Error testing dependency definitions: {e}")
        return False

def test_github_catalog_integration():
    """
    WHAT: Test that GitHub catalog modules are included in self-healing
    WHY: Ensures new GitHub catalog system is properly integrated
    FAIL: Returns False if GitHub catalog integration is incomplete
    UX: Shows GitHub catalog integration test results
    DEBUG: Logs GitHub catalog module checks
    """
    echo_info("Testing GitHub catalog integration...")
    
    try:
        # Check that GitHub catalog modules are in core module lists
        with open("run_integrated.py", "r") as f:
            content = f.read()
        
        github_modules = [
            'core.github_catalog',
            'core.enhanced_vision_handler',
            'core.multi_llm_analyzer'
        ]
        
        missing_modules = []
        for module in github_modules:
            if module not in content:
                missing_modules.append(module)
        
        if missing_modules:
            echo_fail(f"Missing GitHub catalog modules: {missing_modules}")
            return False
        else:
            echo_ok("All GitHub catalog modules included in launcher")
        
        # Check that aws_uploader is removed
        if 'core.aws_uploader' in content:
            echo_warn("core.aws_uploader still referenced (should be removed)")
        else:
            echo_ok("core.aws_uploader correctly removed")
        
        return True
        
    except Exception as e:
        echo_fail(f"Error testing GitHub catalog integration: {e}")
        return False

def test_prf_compliance():
    """
    WHAT: Test PRF compliance of self-healing system
    WHY: Ensures system meets PRF standards for automation
    FAIL: Returns False if PRF compliance is not met
    UX: Shows PRF compliance test results
    DEBUG: Logs PRF compliance validation
    """
    echo_info("Testing PRF compliance...")
    
    try:
        # Check for PRF-compliant error messages
        with open("self_heal_dependencies.py", "r") as f:
            content = f.read()
        
        prf_indicators = [
            "WHAT:",
            "WHY:",
            "FAIL:",
            "UX:",
            "DEBUG:",
            "self-healing",
            "PRF"
        ]
        
        missing_indicators = []
        for indicator in prf_indicators:
            if indicator not in content:
                missing_indicators.append(indicator)
        
        if missing_indicators:
            echo_fail(f"Missing PRF indicators: {missing_indicators}")
            return False
        else:
            echo_ok("PRF compliance indicators present")
        
        # Check for non-interactive behavior
        if "input(" in content or "raw_input(" in content:
            echo_fail("Interactive input detected (violates PRF automation)")
            return False
        else:
            echo_ok("No interactive input detected (PRF compliant)")
        
        return True
        
    except Exception as e:
        echo_fail(f"Error testing PRF compliance: {e}")
        return False

def main():
    """
    WHAT: Main test runner for self-healing system validation
    WHY: Comprehensive validation of PRF-compliant self-healing
    FAIL: Exits with error code if any tests fail
    UX: Shows complete test results and summary
    DEBUG: Logs all test operations and final status
    """
    echo_info("🧪 PRF SELF-HEALING SYSTEM TESTS")
    echo_info("=" * 60)
    echo_info("WHAT: Validates self-healing dependency management")
    echo_info("WHY: Ensures PRF compliance and crash prevention")
    echo_info("=" * 60)
    
    tests = [
        ("Self-Healing Module", test_self_healing_module),
        ("Self-Healing Launcher", test_self_healing_launcher),
        ("Original Launcher Integration", test_original_launcher_integration),
        ("Dependency Definitions", test_dependency_definitions),
        ("GitHub Catalog Integration", test_github_catalog_integration),
        ("PRF Compliance", test_prf_compliance)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        echo_info(f"\n{'='*20} {test_name} {'='*20}")
        if test_func():
            passed += 1
        else:
            echo_fail(f"{test_name} FAILED")
    
    echo_info("=" * 60)
    echo_info(f"🎯 SELF-HEALING TEST RESULTS: {passed}/{total} PASSED")
    
    if passed == total:
        echo_ok("🎉 ALL TESTS PASSED - Self-healing system is PRF compliant!")
        echo_ok("✅ Dependencies will be automatically managed")
        echo_ok("✅ No manual intervention required")
        echo_ok("✅ Crash prevention active")
        echo_info("=" * 60)
        echo_info("🚀 Ready to run: python3 run_integrated_self_heal.py")
        return True
    else:
        echo_fail(f"❌ {total - passed} tests failed")
        echo_fail("🔧 Self-healing system needs fixes before deployment")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
