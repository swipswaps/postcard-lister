#!/usr/bin/env python3
################################################################################
# FILE: test_enhanced_system.py
# DESC: Test script for enhanced multi-LLM system with smart category detection
# USAGE: python test_enhanced_system.py
################################################################################

import os
import json
from pathlib import Path

def test_enhanced_imports():
    """Test that enhanced modules can be imported"""
    print("🧪 Testing Enhanced Module Imports...")
    
    modules_to_test = [
        ('core.enhanced_vision_handler', 'get_enhanced_metadata'),
        ('core.multi_llm_analyzer', 'analyze_product_with_consensus'),
        ('core.multi_llm_analyzer', 'get_available_categories'),
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

def test_category_mappings():
    """Test category mapping system"""
    print("\n🧪 Testing Category Mappings...")
    
    try:
        from core.multi_llm_analyzer import get_available_categories
        
        categories = get_available_categories()
        
        print(f"✅ Found {len(categories)} product categories:")
        for category_name, category_info in categories.items():
            ebay_id = category_info.get("ebay_category_id", "N/A")
            subcats = len(category_info.get("subcategories", {}))
            print(f"  📂 {category_name} (eBay ID: {ebay_id}, {subcats} subcategories)")
        
        # Test specific categories
        required_categories = ["Solar Panel", "Postcard", "Electronics"]
        for req_cat in required_categories:
            if req_cat in categories:
                print(f"✅ Required category '{req_cat}' found")
            else:
                print(f"❌ Required category '{req_cat}' missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Category mapping test failed: {e}")
        return False

def test_enhanced_config():
    """Test enhanced configuration system"""
    print("\n🧪 Testing Enhanced Configuration...")
    
    try:
        from app_integrated import ConfigManager
        
        config_manager = ConfigManager()
        
        # Test multi-LLM setting
        config_manager.set("use_multi_llm", True)
        assert config_manager.get("use_multi_llm") == True
        
        config_manager.set("use_multi_llm", False)
        assert config_manager.get("use_multi_llm") == False
        
        print("✅ Multi-LLM configuration working")
        
        # Test product type settings
        config_manager.set("default_product_type", "Solar Panel")
        assert config_manager.get("default_product_type") == "Solar Panel"
        
        print("✅ Product type configuration working")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced configuration test failed: {e}")
        return False

def test_prompt_generation():
    """Test specialized prompt generation"""
    print("\n🧪 Testing Prompt Generation...")
    
    try:
        from core.enhanced_vision_handler import (
            create_solar_panel_prompt,
            create_postcard_prompt, 
            create_universal_prompt
        )
        
        # Test solar panel prompt
        solar_prompt = create_solar_panel_prompt()
        if "solar panel" in solar_prompt.lower() and "wattage" in solar_prompt.lower():
            print("✅ Solar panel prompt generated correctly")
        else:
            print("❌ Solar panel prompt missing key elements")
            return False
        
        # Test postcard prompt
        postcard_prompt = create_postcard_prompt()
        if "postcard" in postcard_prompt.lower() and "ebay" in postcard_prompt.lower():
            print("✅ Postcard prompt generated correctly")
        else:
            print("❌ Postcard prompt missing key elements")
            return False
        
        # Test universal prompt
        universal_prompt = create_universal_prompt()
        if "product" in universal_prompt.lower() and "category" in universal_prompt.lower():
            print("✅ Universal prompt generated correctly")
        else:
            print("❌ Universal prompt missing key elements")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Prompt generation test failed: {e}")
        return False

def test_mock_analysis():
    """Test analysis with mock data"""
    print("\n🧪 Testing Mock Analysis...")
    
    try:
        from core.enhanced_vision_handler import enhance_with_category_detection
        
        # Mock solar panel result
        mock_solar_result = {
            "product_type": "Solar Panel",
            "brand": "SunPower",
            "power_rating": "400W",
            "subcategory": "Monocrystalline"
        }
        
        enhanced_result = enhance_with_category_detection(mock_solar_result)
        
        if enhanced_result.get("category_id") == "11700":
            print("✅ Solar panel category detection working")
        else:
            print(f"❌ Solar panel category detection failed: {enhanced_result.get('category_id')}")
            return False
        
        # Mock postcard result
        mock_postcard_result = {
            "product_type": "Postcard",
            "City": "New York",
            "subcategory": "Vintage"
        }
        
        enhanced_postcard = enhance_with_category_detection(mock_postcard_result)
        
        if enhanced_postcard.get("category_id") == "10398":
            print("✅ Postcard category detection working")
        else:
            print(f"❌ Postcard category detection failed: {enhanced_postcard.get('category_id')}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Mock analysis test failed: {e}")
        return False

def test_gui_integration():
    """Test GUI integration without launching"""
    print("\n🧪 Testing GUI Integration...")
    
    try:
        # Test that enhanced app can be imported
        from app_integrated import IntegratedPostcardLister
        print("✅ Enhanced GUI class imports successfully")
        
        # Test that new widgets are available
        from PyQt5.QtWidgets import QComboBox, QCheckBox
        print("✅ Required GUI widgets available")
        
        return True
        
    except Exception as e:
        print(f"❌ GUI integration test failed: {e}")
        return False

def main():
    """Run all enhanced system tests"""
    print("🧪 ENHANCED MULTI-LLM SYSTEM TESTS")
    print("=" * 60)
    
    tests = [
        ("Enhanced Module Imports", test_enhanced_imports),
        ("Category Mappings", test_category_mappings),
        ("Enhanced Configuration", test_enhanced_config),
        ("Prompt Generation", test_prompt_generation),
        ("Mock Analysis", test_mock_analysis),
        ("GUI Integration", test_gui_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} FAILED")
    
    print(f"\n{'='*60}")
    print(f"🎯 ENHANCED SYSTEM TEST RESULTS: {passed}/{total} PASSED")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Enhanced system ready!")
        print("\n✅ Features Available:")
        print("  🧠 Multi-LLM consensus analysis")
        print("  🎯 Smart category detection")
        print("  🌞 Solar panel specialized analysis")
        print("  📮 Postcard specialized analysis")
        print("  🔍 Universal product analysis")
        print("  ⚙️ Enhanced GUI with product type selection")
        print("\n🚀 Ready to run: python3 run_integrated.py")
        return True
    else:
        print(f"❌ {total - passed} tests failed - Please fix issues before running")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
