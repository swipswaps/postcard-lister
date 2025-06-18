#!/usr/bin/env python3
################################################################################
# FILE: core/multi_llm_analyzer.py
# DESC: Multi-LLM analysis system with smart category detection
# FEAT: Uses multiple LLMs for enhanced accuracy and category detection
################################################################################

import json
import asyncio
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import openai
# Note: Add other LLM clients as needed (anthropic, google-generativeai, etc.)

@dataclass
class AnalysisResult:
    """Structure for LLM analysis results"""
    model_name: str
    confidence: float
    product_type: str
    category_id: str
    subcategory: str
    metadata: Dict
    raw_response: str
    processing_time: float

@dataclass
class ConsensusResult:
    """Final consensus result from multiple LLMs"""
    product_type: str
    category_id: str
    subcategory: str
    confidence: float
    metadata: Dict
    individual_results: List[AnalysisResult]
    consensus_method: str

################################################################################
# CATEGORY MAPPING DATABASE
################################################################################

CATEGORY_MAPPINGS = {
    "Solar Panel": {
        "ebay_category_id": "11700",
        "keywords": ["solar", "panel", "photovoltaic", "pv", "watt", "voltage"],
        "subcategories": {
            "Monocrystalline": {"id": "11701", "keywords": ["mono", "monocrystalline", "single crystal"]},
            "Polycrystalline": {"id": "11702", "keywords": ["poly", "polycrystalline", "multi crystal"]},
            "Flexible": {"id": "11703", "keywords": ["flexible", "bendable", "thin film"]},
            "Bifacial": {"id": "11704", "keywords": ["bifacial", "double sided", "dual face"]}
        }
    },
    "Postcard": {
        "ebay_category_id": "10398",
        "keywords": ["postcard", "vintage", "collectible", "greeting card"],
        "subcategories": {
            "Vintage": {"id": "10399", "keywords": ["vintage", "antique", "old"]},
            "Modern": {"id": "10400", "keywords": ["modern", "contemporary", "new"]},
            "Real Photo": {"id": "10401", "keywords": ["real photo", "rppc", "photograph"]}
        }
    },
    "Electronics": {
        "ebay_category_id": "58058",
        "keywords": ["electronic", "device", "circuit", "component"],
        "subcategories": {
            "Components": {"id": "58059", "keywords": ["component", "resistor", "capacitor"]},
            "Devices": {"id": "58060", "keywords": ["device", "gadget", "equipment"]}
        }
    }
}

################################################################################
# MULTI-LLM ANALYZER CLASS
################################################################################

class MultiLLMAnalyzer:
    """Multi-LLM analysis system with consensus building"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.openai_client = None
        self.claude_client = None
        self.gemini_client = None
        
        # Initialize available clients
        self._init_clients()
    
    def _init_clients(self):
        """Initialize LLM clients based on available API keys"""
        # OpenAI (Primary)
        if self.config.get("openai_api_key"):
            self.openai_client = openai.OpenAI(api_key=self.config["openai_api_key"])
        
        # Claude (Secondary) - Add when anthropic library available
        # if self.config.get("claude_api_key"):
        #     import anthropic
        #     self.claude_client = anthropic.Anthropic(api_key=self.config["claude_api_key"])
        
        # Gemini (Tertiary) - Add when google-generativeai available  
        # if self.config.get("gemini_api_key"):
        #     import google.generativeai as genai
        #     genai.configure(api_key=self.config["gemini_api_key"])
        #     self.gemini_client = genai
    
    def analyze_product(self, image_path: str, product_hint: str = None) -> ConsensusResult:
        """Analyze product using multiple LLMs and build consensus"""
        results = []
        
        # Run analysis with available LLMs
        if self.openai_client:
            result = self._analyze_with_openai(image_path, product_hint)
            if result:
                results.append(result)
        
        # Add other LLM analyses here when available
        # if self.claude_client:
        #     results.append(self._analyze_with_claude(image_path, product_hint))
        
        # Build consensus from results
        if results:
            return self._build_consensus(results)
        else:
            raise Exception("No LLM clients available for analysis")
    
    def _analyze_with_openai(self, image_path: str, product_hint: str = None) -> Optional[AnalysisResult]:
        """Analyze product using OpenAI GPT-4V"""
        try:
            import time
            start_time = time.time()
            
            # Prepare the analysis prompt
            prompt = self._create_analysis_prompt(product_hint)
            
            # Read and encode image
            import base64
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Call OpenAI Vision API
            response = self.openai_client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
            
            processing_time = time.time() - start_time
            raw_response = response.choices[0].message.content
            
            # Parse the response
            parsed_data = self._parse_openai_response(raw_response)
            
            return AnalysisResult(
                model_name="GPT-4V",
                confidence=parsed_data.get("confidence", 0.8),
                product_type=parsed_data.get("product_type", "Unknown"),
                category_id=parsed_data.get("category_id", ""),
                subcategory=parsed_data.get("subcategory", ""),
                metadata=parsed_data.get("metadata", {}),
                raw_response=raw_response,
                processing_time=processing_time
            )
            
        except Exception as e:
            print(f"OpenAI analysis failed: {e}")
            return None
    
    def _create_analysis_prompt(self, product_hint: str = None) -> str:
        """Create comprehensive analysis prompt"""
        base_prompt = """
        Analyze this product image and provide detailed information in JSON format.
        
        Focus on:
        1. PRODUCT IDENTIFICATION:
           - Exact product type and category
           - Brand, model, specifications
           - Key identifying features
        
        2. CATEGORY CLASSIFICATION:
           - Primary category (Solar Panel, Postcard, Electronics, etc.)
           - Subcategory (Monocrystalline, Vintage, etc.)
           - eBay category suggestion
        
        3. TECHNICAL SPECIFICATIONS:
           - Power ratings, dimensions, certifications
           - Condition assessment
           - Notable features or defects
        
        4. MARKETPLACE OPTIMIZATION:
           - SEO-optimized title
           - Detailed description
           - Key selling points
        
        Return response as JSON with these fields:
        {
            "product_type": "Primary category",
            "subcategory": "Specific subcategory", 
            "confidence": 0.95,
            "brand": "Brand name",
            "model": "Model number",
            "specifications": {
                "power": "400W",
                "voltage": "24V",
                "dimensions": "65x39 inches"
            },
            "condition": "New/Used/Refurbished",
            "title": "SEO optimized title",
            "description": "Detailed description",
            "category_id": "Suggested eBay category ID"
        }
        """
        
        if product_hint:
            base_prompt += f"\n\nHINT: This appears to be a {product_hint}. Focus analysis accordingly."
        
        return base_prompt
    
    def _parse_openai_response(self, response: str) -> Dict:
        """Parse OpenAI response and extract structured data"""
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                parsed = json.loads(json_str)
                
                # Map to our category system
                product_type = parsed.get("product_type", "Unknown")
                category_info = self._map_to_category(product_type, parsed)
                
                return {
                    "product_type": product_type,
                    "subcategory": parsed.get("subcategory", ""),
                    "category_id": category_info.get("category_id", ""),
                    "confidence": parsed.get("confidence", 0.8),
                    "metadata": {
                        "brand": parsed.get("brand", ""),
                        "model": parsed.get("model", ""),
                        "specifications": parsed.get("specifications", {}),
                        "condition": parsed.get("condition", ""),
                        "title": parsed.get("title", ""),
                        "description": parsed.get("description", "")
                    }
                }
            else:
                # Fallback parsing for non-JSON responses
                return self._fallback_parse(response)
                
        except Exception as e:
            print(f"Response parsing failed: {e}")
            return {"product_type": "Unknown", "confidence": 0.1, "metadata": {}}
    
    def _map_to_category(self, product_type: str, parsed_data: Dict) -> Dict:
        """Map detected product type to our category system"""
        # Find best matching category
        best_match = None
        best_score = 0
        
        for category, info in CATEGORY_MAPPINGS.items():
            score = 0
            
            # Check direct match
            if product_type.lower() in category.lower():
                score += 10
            
            # Check keyword matches
            for keyword in info["keywords"]:
                if keyword.lower() in product_type.lower():
                    score += 1
            
            if score > best_score:
                best_score = score
                best_match = category
        
        if best_match:
            category_info = CATEGORY_MAPPINGS[best_match]
            
            # Find subcategory
            subcategory_id = ""
            subcategory = parsed_data.get("subcategory", "")
            
            if subcategory:
                for sub_name, sub_info in category_info.get("subcategories", {}).items():
                    if any(kw.lower() in subcategory.lower() for kw in sub_info["keywords"]):
                        subcategory_id = sub_info["id"]
                        break
            
            return {
                "category_id": category_info["ebay_category_id"],
                "subcategory_id": subcategory_id
            }
        
        return {"category_id": "", "subcategory_id": ""}
    
    def _fallback_parse(self, response: str) -> Dict:
        """Fallback parsing for non-structured responses"""
        # Simple keyword-based extraction
        product_type = "Unknown"
        
        # Check for common product types
        response_lower = response.lower()
        for category in CATEGORY_MAPPINGS.keys():
            if category.lower() in response_lower:
                product_type = category
                break
        
        return {
            "product_type": product_type,
            "confidence": 0.5,
            "metadata": {"raw_analysis": response}
        }
    
    def _build_consensus(self, results: List[AnalysisResult]) -> ConsensusResult:
        """Build consensus from multiple LLM results"""
        if len(results) == 1:
            # Single result - use as-is
            result = results[0]
            return ConsensusResult(
                product_type=result.product_type,
                category_id=result.category_id,
                subcategory=result.subcategory,
                confidence=result.confidence,
                metadata=result.metadata,
                individual_results=results,
                consensus_method="single_model"
            )
        
        # Multiple results - build consensus
        # For now, use weighted average based on confidence
        # TODO: Implement more sophisticated consensus algorithms
        
        total_weight = sum(r.confidence for r in results)
        if total_weight == 0:
            total_weight = 1
        
        # Weighted consensus for categorical data
        product_type_votes = {}
        category_votes = {}
        
        for result in results:
            weight = result.confidence / total_weight
            
            # Vote for product type
            if result.product_type in product_type_votes:
                product_type_votes[result.product_type] += weight
            else:
                product_type_votes[result.product_type] = weight
            
            # Vote for category
            if result.category_id in category_votes:
                category_votes[result.category_id] += weight
            else:
                category_votes[result.category_id] = weight
        
        # Select winners
        consensus_product_type = max(product_type_votes, key=product_type_votes.get)
        consensus_category = max(category_votes, key=category_votes.get)
        consensus_confidence = max(product_type_votes.values())
        
        # Merge metadata (use highest confidence result's metadata as base)
        best_result = max(results, key=lambda r: r.confidence)
        consensus_metadata = best_result.metadata.copy()
        
        return ConsensusResult(
            product_type=consensus_product_type,
            category_id=consensus_category,
            subcategory=best_result.subcategory,
            confidence=consensus_confidence,
            metadata=consensus_metadata,
            individual_results=results,
            consensus_method="weighted_voting"
        )

################################################################################
# CONVENIENCE FUNCTIONS
################################################################################

def analyze_product_with_consensus(image_path: str, config: Dict, product_hint: str = None) -> ConsensusResult:
    """Main entry point for multi-LLM product analysis"""
    analyzer = MultiLLMAnalyzer(config)
    return analyzer.analyze_product(image_path, product_hint)

def get_available_categories() -> Dict:
    """Get all available product categories"""
    return CATEGORY_MAPPINGS
