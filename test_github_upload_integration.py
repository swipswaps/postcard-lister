#!/usr/bin/env python3
################################################################################
# FILE: test_github_upload_integration.py
# DESC: Test script for GitHub upload integration in GUI
# SPEC: PRF-COMPOSITE-2025-06-18-GITHUB-UPLOAD-GUI
# WHAT: Validates GitHub upload functionality within the application
# WHY: Ensures seamless workflow from processing to GitHub upload
# FAIL: Exits with error if GitHub upload integration is broken
# UX: Shows comprehensive test results and integration status
# DEBUG: Logs all GitHub upload integration tests
################################################################################

import sys
import os
import subprocess

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

def test_github_upload_script_exists():
    """
    WHAT: Test that GitHub upload script exists and is executable
    WHY: GUI depends on this script for upload functionality
    FAIL: Returns False if script is missing or not executable
    UX: Shows script availability status
    DEBUG: Logs script file checks
    """
    echo_info("Testing GitHub upload script availability...")
    
    script_name = "github_upload_clean.sh"
    
    if not os.path.exists(script_name):
        echo_fail(f"GitHub upload script not found: {script_name}")
        return False
    
    echo_ok(f"GitHub upload script found: {script_name}")
    
    # Check if executable
    if not os.access(script_name, os.X_OK):
        echo_warn(f"Script not executable, attempting to fix...")
        try:
            os.chmod(script_name, 0o755)
            echo_ok("Script made executable")
        except Exception as e:
            echo_fail(f"Could not make script executable: {e}")
            return False
    else:
        echo_ok("Script is executable")
    
    return True

def test_gui_upload_integration():
    """
    WHAT: Test that GUI has GitHub upload integration
    WHY: Ensures upload functionality is properly integrated
    FAIL: Returns False if integration is incomplete
    UX: Shows GUI integration test results
    DEBUG: Logs GUI code analysis
    """
    echo_info("Testing GUI GitHub upload integration...")
    
    try:
        # Check if app_integrated.py has upload functionality
        with open("app_integrated.py", "r") as f:
            content = f.read()
        
        # Check for upload button
        if "Upload to GitHub" in content:
            echo_ok("GitHub upload button found in GUI")
        else:
            echo_fail("GitHub upload button missing from GUI")
            return False
        
        # Check for upload method
        if "def upload_to_github" in content:
            echo_ok("GitHub upload method implemented")
        else:
            echo_fail("GitHub upload method missing")
            return False
        
        # Check for script execution
        if "github_upload_clean.sh" in content:
            echo_ok("GUI references correct upload script")
        else:
            echo_fail("GUI does not reference upload script")
            return False
        
        # Check for error handling
        if "subprocess.run" in content and "capture_output=True" in content:
            echo_ok("Proper subprocess handling implemented")
        else:
            echo_fail("Subprocess handling missing or incomplete")
            return False
        
        return True
        
    except Exception as e:
        echo_fail(f"Error testing GUI integration: {e}")
        return False

def test_upload_button_locations():
    """
    WHAT: Test that upload buttons are in correct GUI locations
    WHY: Ensures good UX with upload buttons where needed
    FAIL: Returns False if buttons are not properly placed
    UX: Shows button placement test results
    DEBUG: Logs button location analysis
    """
    echo_info("Testing upload button locations...")
    
    try:
        with open("app_integrated.py", "r") as f:
            content = f.read()
        
        # Check for upload button in Settings tab
        settings_section = content[content.find("def create_settings_tab"):content.find("def create_process_tab")]
        if "Upload to GitHub" in settings_section:
            echo_ok("Upload button found in Settings tab")
        else:
            echo_fail("Upload button missing from Settings tab")
            return False
        
        # Check for upload button in Results tab
        results_section = content[content.find("def create_results_tab"):content.find("def load_config_to_gui")]
        if "Upload to GitHub" in results_section:
            echo_ok("Upload button found in Results tab")
        else:
            echo_fail("Upload button missing from Results tab")
            return False
        
        # Check that buttons are enabled/disabled appropriately
        if "upload_results_btn.setEnabled(True)" in content:
            echo_ok("Results upload button properly enabled after processing")
        else:
            echo_fail("Results upload button enabling logic missing")
            return False
        
        return True
        
    except Exception as e:
        echo_fail(f"Error testing button locations: {e}")
        return False

def test_commit_message_generation():
    """
    WHAT: Test that commit messages are properly generated
    WHY: Ensures meaningful commit messages for GitHub uploads
    FAIL: Returns False if commit message logic is broken
    UX: Shows commit message generation test results
    DEBUG: Logs commit message logic analysis
    """
    echo_info("Testing commit message generation...")
    
    try:
        with open("app_integrated.py", "r") as f:
            content = f.read()
        
        # Check for timestamp in commit messages
        if "datetime.now().strftime" in content:
            echo_ok("Timestamp generation found in commit messages")
        else:
            echo_fail("Timestamp generation missing from commit messages")
            return False
        
        # Check for descriptive commit message
        if "GUI Upload:" in content or "Configuration and catalog updates" in content:
            echo_ok("Descriptive commit message template found")
        else:
            echo_fail("Descriptive commit message template missing")
            return False
        
        return True
        
    except Exception as e:
        echo_fail(f"Error testing commit message generation: {e}")
        return False

def test_error_handling():
    """
    WHAT: Test that GitHub upload error handling is comprehensive
    WHY: Ensures graceful failure and user feedback
    FAIL: Returns False if error handling is inadequate
    UX: Shows error handling test results
    DEBUG: Logs error handling analysis
    """
    echo_info("Testing GitHub upload error handling...")
    
    try:
        with open("app_integrated.py", "r") as f:
            content = f.read()
        
        upload_method = content[content.find("def upload_to_github"):content.find("def log_message")]
        
        # Check for try-except blocks
        if "try:" in upload_method and "except" in upload_method:
            echo_ok("Exception handling implemented")
        else:
            echo_fail("Exception handling missing")
            return False
        
        # Check for return code checking
        if "result.returncode" in upload_method:
            echo_ok("Return code checking implemented")
        else:
            echo_fail("Return code checking missing")
            return False
        
        # Check for user feedback
        if "log_message" in upload_method:
            echo_ok("User feedback logging implemented")
        else:
            echo_fail("User feedback logging missing")
            return False
        
        # Check for stderr/stdout capture
        if "result.stderr" in upload_method and "result.stdout" in upload_method:
            echo_ok("Output capture implemented")
        else:
            echo_fail("Output capture missing")
            return False
        
        return True
        
    except Exception as e:
        echo_fail(f"Error testing error handling: {e}")
        return False

def test_workflow_integration():
    """
    WHAT: Test that GitHub upload integrates well with processing workflow
    WHY: Ensures seamless user experience from processing to upload
    FAIL: Returns False if workflow integration is poor
    UX: Shows workflow integration test results
    DEBUG: Logs workflow analysis
    """
    echo_info("Testing workflow integration...")
    
    try:
        with open("app_integrated.py", "r") as f:
            content = f.read()
        
        # Check that configuration is saved before upload
        upload_method = content[content.find("def upload_to_github"):content.find("def log_message")]
        if "save_config_from_gui" in upload_method:
            echo_ok("Configuration saved before upload")
        else:
            echo_fail("Configuration not saved before upload")
            return False
        
        # Check that upload button is enabled after processing
        processing_finished = content[content.find("def processing_finished"):content.find("def processing_error")]
        if "upload_results_btn.setEnabled(True)" in processing_finished:
            echo_ok("Upload button enabled after successful processing")
        else:
            echo_fail("Upload button not enabled after processing")
            return False
        
        return True
        
    except Exception as e:
        echo_fail(f"Error testing workflow integration: {e}")
        return False

def main():
    """
    WHAT: Main test runner for GitHub upload integration
    WHY: Comprehensive validation of GitHub upload GUI integration
    FAIL: Exits with error code if any tests fail
    UX: Shows complete test results and summary
    DEBUG: Logs all test operations and final status
    """
    echo_info("🧪 GITHUB UPLOAD GUI INTEGRATION TESTS")
    echo_info("=" * 60)
    echo_info("WHAT: Validates GitHub upload functionality in GUI")
    echo_info("WHY: Ensures seamless workflow from processing to GitHub")
    echo_info("=" * 60)
    
    tests = [
        ("GitHub Upload Script Exists", test_github_upload_script_exists),
        ("GUI Upload Integration", test_gui_upload_integration),
        ("Upload Button Locations", test_upload_button_locations),
        ("Commit Message Generation", test_commit_message_generation),
        ("Error Handling", test_error_handling),
        ("Workflow Integration", test_workflow_integration)
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
    echo_info(f"🎯 GITHUB UPLOAD INTEGRATION TEST RESULTS: {passed}/{total} PASSED")
    
    if passed == total:
        echo_ok("🎉 ALL TESTS PASSED - GitHub upload integration ready!")
        echo_ok("✅ Upload buttons available in Settings and Results tabs")
        echo_ok("✅ Proper error handling and user feedback")
        echo_ok("✅ Seamless workflow integration")
        echo_ok("✅ Meaningful commit messages with timestamps")
        echo_info("=" * 60)
        echo_info("🚀 Ready for GitHub upload workflow:")
        echo_info("  1. Process your solar panels")
        echo_info("  2. Click 'Upload to GitHub' in Results tab")
        echo_info("  3. Changes automatically pushed to repository")
        return True
    else:
        echo_fail(f"❌ {total - passed} tests failed")
        echo_fail("🔧 GitHub upload integration needs fixes")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
