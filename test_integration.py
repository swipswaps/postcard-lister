#!/usr/bin/env python3
################################################################################
# FILE: test_integration.py
# DESC: Test script to verify core module integration
# USAGE: python test_integration.py
################################################################################

import os
import json
from pathlib import Path

def test_config_management():
    """Test configuration loading and saving"""
    print("🧪 Testing Configuration Management...")
    
    try:
        from app_integrated import ConfigManager
        
        config_manager = ConfigManager()
        
        # Test setting and getting values
        config_manager.set("test_key", "test_value")
        assert config_manager.get("test_key") == "test_value"
        
        # Test saving and loading
        config_manager.save_config()
        
        # Create new instance to test loading
        config_manager2 = ConfigManager()
        assert config_manager2.get("test_key") == "test_value"
        
        print("✅ Configuration management working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Configuration management failed: {e}")
        return False

def test_core_module_imports():
    """Test that all core modules can be imported"""
    print("\n🧪 Testing Core Module Imports...")
    
    modules_to_test = [
        ('core.vision_handler', 'get_postcard_metadata'),
        ('core.image_processor', 'process_image_set'),
        ('core.aws_uploader', 'upload_to_s3'),
        ('core.csv_generator', 'generate_csv'),
        ('core.utils', 'is_image_file')
    ]
    
    all_passed = True
    
    for module_name, function_name in modules_to_test:
        try:
            module = __import__(module_name, fromlist=[function_name])
            func = getattr(module, function_name)
            print(f"✅ {module_name}.{function_name} - OK")
        except Exception as e:
            print(f"❌ {module_name}.{function_name} - FAILED: {e}")
            all_passed = False
    
    return all_passed

def test_directory_structure():
    """Test that required directories and files exist"""
    print("\n🧪 Testing Directory Structure...")
    
    required_paths = [
        "core/",
        "core/vision_handler.py",
        "core/image_processor.py", 
        "core/aws_uploader.py",
        "core/csv_generator.py",
        "core/utils.py",
        "config/",
        "config/settings.template.json"
    ]
    
    all_exist = True
    
    for path in required_paths:
        if os.path.exists(path):
            print(f"✅ {path} - EXISTS")
        else:
            print(f"❌ {path} - MISSING")
            all_exist = False
    
    return all_exist

def test_settings_template():
    """Test that settings template is valid JSON"""
    print("\n🧪 Testing Settings Template...")
    
    try:
        template_path = "config/settings.template.json"
        if not os.path.exists(template_path):
            print(f"❌ Template file missing: {template_path}")
            return False
        
        with open(template_path, 'r') as f:
            template_data = json.load(f)
        
        required_keys = [
            "aws_access_key",
            "aws_secret_key", 
            "s3_bucket",
            "openai_api_key"
        ]
        
        for key in required_keys:
            if key in template_data:
                print(f"✅ Template has key: {key}")
            else:
                print(f"❌ Template missing key: {key}")
                return False
        
        print("✅ Settings template is valid")
        return True
        
    except Exception as e:
        print(f"❌ Settings template test failed: {e}")
        return False

def test_output_directory():
    """Test that output directory can be created"""
    print("\n🧪 Testing Output Directory...")
    
    try:
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        if os.path.exists(output_dir) and os.path.isdir(output_dir):
            print(f"✅ Output directory ready: {output_dir}")
            return True
        else:
            print(f"❌ Could not create output directory: {output_dir}")
            return False
            
    except Exception as e:
        print(f"❌ Output directory test failed: {e}")
        return False

def main():
    """Run all integration tests"""
    print("🧪 POSTCARD LISTER - INTEGRATION TESTS")
    print("=" * 50)
    
    tests = [
        ("Directory Structure", test_directory_structure),
        ("Settings Template", test_settings_template),
        ("Core Module Imports", test_core_module_imports),
        ("Configuration Management", test_config_management),
        ("Output Directory", test_output_directory)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} FAILED")
    
    print(f"\n{'='*50}")
    print(f"🎯 INTEGRATION TEST RESULTS: {passed}/{total} PASSED")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Integration is working correctly!")
        print("\n✅ Ready to run: python run_integrated.py")
        return True
    else:
        print(f"❌ {total - passed} tests failed - Please fix issues before running")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
