#!/usr/bin/env python3
################################################################################
# FILE: core/enhanced_vision_handler.py
# DESC: Enhanced vision handler with multi-LLM support and smart category detection
# FEAT: Supports multiple product types (postcards, solar panels, etc.)
################################################################################

import openai
import json
import base64
import os
from openai import OpenAI
from typing import Dict, Optional
from .multi_llm_analyzer import analyze_product_with_consensus, get_available_categories

def image_to_base64(path):
    """Convert image to base64 encoding"""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def read_value_list(path):
    """Read value list from file"""
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def get_enhanced_metadata(combined_img_path: str, config: Dict, product_hint: str = None) -> Dict:
    """
    Enhanced metadata extraction using multi-LLM analysis and smart category detection
    
    Args:
        combined_img_path: Path to the combined image
        config: Configuration dictionary with API keys
        product_hint: Optional hint about product type (e.g., "solar panel", "postcard")
    
    Returns:
        Dictionary with enhanced metadata including category detection
    """
    try:
        print(f"🔍 Enhanced analysis starting for: {combined_img_path}")
        
        # Use multi-LLM analysis for enhanced accuracy
        if config.get("use_multi_llm", True):
            print("🧠 Using multi-LLM consensus analysis...")
            consensus_result = analyze_product_with_consensus(
                combined_img_path, 
                config, 
                product_hint
            )
            
            # Convert consensus result to our metadata format
            metadata = {
                "product_type": consensus_result.product_type,
                "category_id": consensus_result.category_id,
                "subcategory": consensus_result.subcategory,
                "confidence": consensus_result.confidence,
                "analysis_method": f"multi_llm_{consensus_result.consensus_method}",
                **consensus_result.metadata
            }
            
            print(f"✅ Multi-LLM analysis complete. Product: {consensus_result.product_type} (confidence: {consensus_result.confidence:.2f})")
            return metadata
            
        else:
            # Fallback to single LLM analysis
            print("🤖 Using single LLM analysis...")
            return get_single_llm_metadata(combined_img_path, config, product_hint)
            
    except Exception as e:
        print(f"❌ Enhanced analysis failed: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        
        # Fallback to original postcard analysis
        print("🔄 Falling back to original postcard analysis...")
        return get_postcard_metadata(combined_img_path, config.get("openai_api_key", ""))

def get_single_llm_metadata(combined_img_path: str, config: Dict, product_hint: str = None) -> Dict:
    """Single LLM analysis with smart prompting based on product type"""
    
    api_key = config.get("openai_api_key")
    if not api_key:
        raise Exception("OpenAI API key not configured")
    
    client = OpenAI(api_key=api_key)
    
    try:
        print(f"Processing image: {combined_img_path}")
        b64_image = image_to_base64(combined_img_path)
        print("Image converted to base64 successfully")
        
        # Determine product type and create appropriate prompt
        if product_hint and "solar" in product_hint.lower():
            system_message = create_solar_panel_prompt()
            print("🌞 Using solar panel analysis prompt")
        elif product_hint and "postcard" in product_hint.lower():
            system_message = create_postcard_prompt()
            print("📮 Using postcard analysis prompt")
        else:
            system_message = create_universal_prompt()
            print("🔍 Using universal product analysis prompt")
        
        print("Making API call to OpenAI...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{b64_image}",
                                "detail": "high"
                            }
                        },
                        {
                            "type": "text",
                            "text": "Please analyze this product and extract the metadata in JSON format."
                        }
                    ]
                }
            ],
            temperature=0.2,
            max_tokens=16384
        )
        print("API call completed successfully")
        
        raw = response.choices[0].message.content.strip()
        print(f"Raw response: {raw}")
        
        # Clean up response
        if raw.startswith("```"):
            raw = raw.split("```")[1].strip()
            if raw.lower().startswith("json"):
                raw = raw[4:].strip()
        
        result = json.loads(raw)
        
        # Add category detection
        result = enhance_with_category_detection(result)
        
        print(f"Parsed JSON result: {result}")
        return result
        
    except Exception as e:
        print(f"⚠️ Failed to parse AI response: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return {}

def create_solar_panel_prompt() -> str:
    """Create specialized prompt for solar panel analysis"""
    return """
    You are a solar panel expert that extracts structured metadata from solar panel images for marketplace listings.
    You are given images showing different views of a solar panel (front, back, connectors, data plate).
    
    Extract the following information in JSON format:
    {
        "product_type": "Solar Panel",
        "brand": "Manufacturer name",
        "model": "Model number",
        "power_rating": "Wattage (e.g., 400W)",
        "voltage": "Voltage rating",
        "current": "Current rating", 
        "efficiency": "Efficiency percentage",
        "technology": "Monocrystalline/Polycrystalline/Thin Film",
        "dimensions": "Physical dimensions",
        "weight": "Weight if visible",
        "certifications": "UL, IEC, etc.",
        "condition": "New/Used/Refurbished",
        "connector_type": "MC4, etc.",
        "frame_material": "Aluminum, etc.",
        "title": "SEO-optimized eBay title (80 chars max)",
        "description": "Detailed HTML description for eBay",
        "category_id": "11700",
        "subcategory": "Monocrystalline/Polycrystalline/etc"
    }
    
    Focus on extracting exact specifications from the data plate/label.
    For title, include wattage, brand, technology type, and condition.
    For description, provide technical details and selling points.
    """

def create_postcard_prompt() -> str:
    """Create specialized prompt for postcard analysis"""
    # Load postcard-specific value lists
    region_list = read_value_list("data/region_values.txt")
    city_list = read_value_list("data/city_values.txt")
    subject_list = read_value_list("data/subject_values.txt")
    country_list = read_value_list("data/country_values.txt")
    theme_list = read_value_list("data/theme_values.txt")
    type_list = read_value_list("data/type_values.txt")
    era_list = read_value_list("data/era_values.txt")
    
    return f"""
    You are a postcard expert that extracts structured metadata from postcard images for eBay listings.
    You are given a combined image of a postcard front and back.
    
    Extract the following fields in JSON format:
    {{
        "product_type": "Postcard",
        "City": "City name",
        "State": "State/Province", 
        "Country": "Country name",
        "Region": "Geographic region",
        "Year": "Year if determinable",
        "Publisher": "Publisher name",
        "Era": "Time period",
        "Type": "Postcard type",
        "Subject": "Main subject",
        "Theme": "Theme category",
        "Title": "eBay-optimized title (80 chars max)",
        "Description": "HTML description",
        "Posted": "Posted/Unposted",
        "category_id": "10398",
        "subcategory": "Vintage/Modern/Real Photo"
    }}
    
    Use these predefined values when possible:
    Region: {', '.join(region_list[:20])}...
    City: {', '.join(city_list[:20])}...
    Subject: {', '.join(subject_list[:20])}...
    Theme: {', '.join(theme_list[:20])}...
    Type: {', '.join(type_list)}
    Era: {', '.join(era_list)}
    
    For Title: Include "Postcard", location, subject, and era. Use all 80 characters.
    For Posted: "Posted" if stamped/written on, "Unposted" if blank.
    """

def create_universal_prompt() -> str:
    """Create universal prompt for unknown product types"""
    return """
    You are a product analysis expert. Analyze this product image and determine:
    
    1. What type of product this is
    2. Extract relevant specifications and details
    3. Suggest appropriate marketplace category
    
    Return JSON format:
    {
        "product_type": "Detected product category",
        "brand": "Brand name if visible",
        "model": "Model number if visible", 
        "specifications": {
            "key_spec_1": "value",
            "key_spec_2": "value"
        },
        "condition": "New/Used/Refurbished",
        "title": "SEO-optimized marketplace title",
        "description": "Detailed product description",
        "category_id": "Suggested category ID",
        "subcategory": "Specific subcategory",
        "confidence": 0.95
    }
    
    Focus on identifying the product type first, then extract relevant specifications.
    Provide marketplace-ready title and description.
    """

def enhance_with_category_detection(result: Dict) -> Dict:
    """Enhance result with smart category detection"""
    try:
        product_type = result.get("product_type", "Unknown")
        
        # Map to our category system
        categories = get_available_categories()
        
        # Find best matching category
        best_match = None
        for category_name, category_info in categories.items():
            if category_name.lower() in product_type.lower():
                best_match = category_info
                break
        
        if best_match:
            result["category_id"] = best_match["ebay_category_id"]
            result["category_name"] = category_name
            
            # Try to determine subcategory
            subcategory = result.get("subcategory", "")
            if subcategory:
                for sub_name, sub_info in best_match.get("subcategories", {}).items():
                    if any(kw.lower() in subcategory.lower() for kw in sub_info["keywords"]):
                        result["subcategory_id"] = sub_info["id"]
                        break
        
        # Add analysis metadata
        result["analysis_method"] = "single_llm_enhanced"
        result["categories_available"] = list(categories.keys())
        
        return result
        
    except Exception as e:
        print(f"Category detection failed: {e}")
        return result

# Backward compatibility function
def get_postcard_metadata(combined_img_path: str, api_key: str) -> dict:
    """Original postcard metadata function for backward compatibility"""
    config = {"openai_api_key": api_key, "use_multi_llm": False}
    return get_enhanced_metadata(combined_img_path, config, "postcard")
