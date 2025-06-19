#!/usr/bin/env python3
################################################################################
# FILE: platforms/multiplatform_generator.py
# DESC: Multi-platform ad generator for Facebook, Craigslist, Twitter/X
# WHAT: Generate platform-specific ad layouts and content
# WHY: Maximize reach across multiple selling platforms
# FAIL: Provides generic templates if platform-specific generation fails
# UX: Visual preview of ads for each platform
# DEBUG: Verbatim capture of all generation steps
################################################################################

import sys
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich.columns import Columns
    from rich.text import Text
    from rich.markup import escape
except ImportError:
    print("🔧 Installing required packages...")
    import subprocess
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'rich'], check=True)
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich.columns import Columns
    from rich.text import Text
    from rich.markup import escape

class MultiPlatformAdGenerator:
    """
    WHAT: Generate ads optimized for different platforms
    WHY: Each platform has unique requirements and best practices
    FAIL: Provides generic templates if platform-specific fails
    UX: Visual preview of how ads will appear on each platform
    DEBUG: Complete verbatim logging of generation process
    """
    
    def __init__(self):
        self.console = Console()
        self.verbatim_log = []
        
        # Platform specifications
        self.platform_specs = {
            'facebook': {
                'title_max': 40,
                'description_max': 125,
                'image_ratio': '1:1',
                'hashtags_max': 30,
                'features': ['marketplace', 'boost_ads', 'targeting']
            },
            'craigslist': {
                'title_max': 70,
                'description_max': 8000,
                'image_ratio': '4:3',
                'hashtags_max': 0,  # No hashtags
                'features': ['categories', 'location_based', 'simple_text']
            },
            'twitter': {
                'title_max': 280,  # Combined title + description
                'description_max': 280,
                'image_ratio': '16:9',
                'hashtags_max': 10,
                'features': ['hashtags', 'mentions', 'threads']
            }
        }
    
    def log_verbatim(self, message):
        """Add message to verbatim log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"{timestamp} {message}"
        self.verbatim_log.append(log_entry)
    
    def generate_all_platforms(self, product_data):
        """Generate ads for all platforms"""
        self.console.clear()
        
        header = Panel(
            "📱 Multi-Platform Ad Generator\n"
            "Creating optimized ads for Facebook, Craigslist, and Twitter/X",
            style="cyan",
            padding=(1, 2)
        )
        self.console.print(header)
        
        self.log_verbatim("🚀 Starting multi-platform ad generation")
        
        # Generate for each platform
        platform_ads = {}
        
        for platform in ['facebook', 'craigslist', 'twitter']:
            self.log_verbatim(f"📱 Generating {platform.title()} ad...")
            platform_ads[platform] = self.generate_platform_ad(platform, product_data)
        
        # Show all generated ads
        self.show_platform_comparison(platform_ads)
        
        # Export options
        self.export_ads(platform_ads)
        
        return platform_ads
    
    def generate_platform_ad(self, platform, product_data):
        """Generate ad for specific platform"""
        specs = self.platform_specs[platform]
        
        if platform == 'facebook':
            return self.generate_facebook_ad(product_data, specs)
        elif platform == 'craigslist':
            return self.generate_craigslist_ad(product_data, specs)
        elif platform == 'twitter':
            return self.generate_twitter_ad(product_data, specs)
    
    def generate_facebook_ad(self, product_data, specs):
        """Generate Facebook Marketplace ad"""
        self.log_verbatim("📘 Generating Facebook Marketplace ad")
        
        # Optimize title for Facebook
        title = product_data.get('title', 'Solar Panel')
        if len(title) > specs['title_max']:
            title = title[:specs['title_max']-3] + "..."
        
        # Create engaging description
        description_parts = []
        
        # Key features first
        if product_data.get('wattage'):
            description_parts.append(f"⚡ {product_data['wattage']}W Power Output")
        
        if product_data.get('efficiency'):
            description_parts.append(f"🔋 {product_data['efficiency']}% Efficiency")
        
        if product_data.get('condition'):
            description_parts.append(f"✨ {product_data['condition']} Condition")
        
        # Add selling points
        description_parts.extend([
            "🌱 Eco-friendly renewable energy",
            "💰 Great investment for energy savings",
            "📦 Fast shipping available"
        ])
        
        description = " • ".join(description_parts)
        
        # Truncate if too long
        if len(description) > specs['description_max']:
            description = description[:specs['description_max']-3] + "..."
        
        # Generate hashtags
        hashtags = self.generate_hashtags(product_data, specs['hashtags_max'])
        
        facebook_ad = {
            'platform': 'facebook',
            'title': title,
            'description': description,
            'price': product_data.get('price', ''),
            'location': product_data.get('location', ''),
            'category': 'Electronics > Solar Panels',
            'hashtags': hashtags,
            'features': [
                'Boost this ad for more visibility',
                'Share to Facebook groups',
                'Cross-post to Instagram'
            ]
        }
        
        self.log_verbatim(f"✅ Facebook ad generated: {len(description)} chars")
        return facebook_ad
    
    def generate_craigslist_ad(self, product_data, specs):
        """Generate Craigslist ad"""
        self.log_verbatim("📋 Generating Craigslist ad")
        
        # Craigslist allows longer, more detailed descriptions
        title = product_data.get('title', 'Solar Panel for Sale')
        
        # Add key specs to title if space allows
        if product_data.get('wattage') and len(title) < 50:
            title += f" - {product_data['wattage']}W"
        
        # Create detailed description
        description_sections = []
        
        # Header
        description_sections.append("🌞 HIGH-QUALITY SOLAR PANEL FOR SALE 🌞")
        description_sections.append("")
        
        # Specifications
        if any([product_data.get('wattage'), product_data.get('voltage'), product_data.get('efficiency')]):
            description_sections.append("SPECIFICATIONS:")
            if product_data.get('wattage'):
                description_sections.append(f"• Power Output: {product_data['wattage']}W")
            if product_data.get('voltage'):
                description_sections.append(f"• Voltage: {product_data['voltage']}V")
            if product_data.get('current'):
                description_sections.append(f"• Current: {product_data['current']}A")
            if product_data.get('efficiency'):
                description_sections.append(f"• Efficiency: {product_data['efficiency']}%")
            if product_data.get('dimensions'):
                description_sections.append(f"• Dimensions: {product_data['dimensions']}")
            description_sections.append("")
        
        # Condition and details
        description_sections.append("CONDITION & DETAILS:")
        description_sections.append(f"• Condition: {product_data.get('condition', 'Good')}")
        if product_data.get('brand'):
            description_sections.append(f"• Brand: {product_data['brand']}")
        if product_data.get('model'):
            description_sections.append(f"• Model: {product_data['model']}")
        if product_data.get('warranty'):
            description_sections.append(f"• Warranty: {product_data['warranty']}")
        description_sections.append("")
        
        # Benefits
        description_sections.extend([
            "BENEFITS:",
            "• Reduce your electricity bills",
            "• Environmentally friendly renewable energy",
            "• Increase your property value",
            "• Perfect for off-grid applications",
            "• Easy installation (professional installation recommended)",
            ""
        ])
        
        # Pricing and contact
        description_sections.append("PRICING & CONTACT:")
        if product_data.get('price'):
            description_sections.append(f"• Price: ${product_data['price']}")
        description_sections.append("• Serious inquiries only")
        description_sections.append("• Cash or PayPal accepted")
        description_sections.append("• Local pickup preferred")
        if product_data.get('shipping_cost', '0') != '0':
            description_sections.append(f"• Shipping available (+${product_data['shipping_cost']})")
        
        description = "\n".join(description_sections)
        
        craigslist_ad = {
            'platform': 'craigslist',
            'title': title,
            'description': description,
            'price': product_data.get('price', ''),
            'location': product_data.get('location', ''),
            'category': 'for sale > electronics',
            'posting_tips': [
                'Include multiple clear photos',
                'Post in appropriate category',
                'Renew listing every few days',
                'Be responsive to inquiries'
            ]
        }
        
        self.log_verbatim(f"✅ Craigslist ad generated: {len(description)} chars")
        return craigslist_ad
    
    def generate_twitter_ad(self, product_data, specs):
        """Generate Twitter/X post"""
        self.log_verbatim("🐦 Generating Twitter/X post")
        
        # Twitter requires concise, engaging content
        tweet_parts = []
        
        # Hook
        tweet_parts.append("🌞 Solar Panel for Sale!")
        
        # Key specs (abbreviated)
        specs_text = []
        if product_data.get('wattage'):
            specs_text.append(f"{product_data['wattage']}W")
        if product_data.get('efficiency'):
            specs_text.append(f"{product_data['efficiency']}% eff")
        if product_data.get('condition'):
            specs_text.append(product_data['condition'].lower())
        
        if specs_text:
            tweet_parts.append(" • ".join(specs_text))
        
        # Price
        if product_data.get('price'):
            tweet_parts.append(f"💰 ${product_data['price']}")
        
        # Call to action
        tweet_parts.append("DM for details!")
        
        # Generate hashtags
        hashtags = self.generate_hashtags(product_data, specs['hashtags_max'])
        
        # Combine tweet
        tweet_text = " ".join(tweet_parts)
        if hashtags:
            tweet_text += " " + " ".join([f"#{tag}" for tag in hashtags])
        
        # Ensure under character limit
        if len(tweet_text) > specs['description_max']:
            # Trim hashtags first
            base_text = " ".join(tweet_parts)
            remaining_chars = specs['description_max'] - len(base_text) - 1
            
            if remaining_chars > 0:
                hashtag_text = " ".join([f"#{tag}" for tag in hashtags])
                if len(hashtag_text) <= remaining_chars:
                    tweet_text = base_text + " " + hashtag_text
                else:
                    # Fit as many hashtags as possible
                    fitted_hashtags = []
                    current_length = 0
                    for tag in hashtags:
                        tag_length = len(f"#{tag} ")
                        if current_length + tag_length <= remaining_chars:
                            fitted_hashtags.append(tag)
                            current_length += tag_length
                        else:
                            break
                    
                    if fitted_hashtags:
                        tweet_text = base_text + " " + " ".join([f"#{tag}" for tag in fitted_hashtags])
                    else:
                        tweet_text = base_text
            else:
                tweet_text = base_text[:specs['description_max']]
        
        twitter_ad = {
            'platform': 'twitter',
            'tweet': tweet_text,
            'character_count': len(tweet_text),
            'hashtags': hashtags,
            'engagement_tips': [
                'Post during peak hours (12-3pm, 5-6pm)',
                'Include high-quality images',
                'Engage with replies quickly',
                'Consider Twitter Ads for promotion'
            ]
        }
        
        self.log_verbatim(f"✅ Twitter post generated: {len(tweet_text)} chars")
        return twitter_ad
    
    def generate_hashtags(self, product_data, max_hashtags):
        """Generate relevant hashtags"""
        if max_hashtags == 0:
            return []
        
        base_hashtags = ['solar', 'renewable', 'energy', 'green', 'sustainable']
        
        # Add product-specific hashtags
        if product_data.get('brand'):
            base_hashtags.append(product_data['brand'].lower().replace(' ', ''))
        
        if product_data.get('wattage'):
            base_hashtags.append(f"{product_data['wattage']}w")
        
        # Add condition-based hashtags
        condition = product_data.get('condition', '').lower()
        if condition in ['new', 'used', 'refurbished']:
            base_hashtags.append(condition)
        
        # Add location if available
        if product_data.get('location'):
            location_parts = product_data['location'].split(',')
            if location_parts:
                city = location_parts[0].strip().lower().replace(' ', '')
                if len(city) < 15:  # Reasonable hashtag length
                    base_hashtags.append(city)
        
        # Remove duplicates and limit
        unique_hashtags = list(dict.fromkeys(base_hashtags))
        return unique_hashtags[:max_hashtags]
    
    def show_platform_comparison(self, platform_ads):
        """Show side-by-side comparison of platform ads"""
        self.console.print("\n📱 [bold cyan]Platform Ad Comparison[/bold cyan]")
        
        # Create panels for each platform
        panels = []
        
        for platform, ad_data in platform_ads.items():
            if platform == 'facebook':
                content = f"📘 [bold blue]Facebook Marketplace[/bold blue]\n\n"
                content += f"Title: {ad_data['title']}\n"
                content += f"Price: ${ad_data.get('price', 'N/A')}\n"
                content += f"Category: {ad_data['category']}\n\n"
                content += f"Description:\n{ad_data['description']}\n\n"
                if ad_data.get('hashtags'):
                    content += f"Tags: {', '.join(ad_data['hashtags'])}"
                
            elif platform == 'craigslist':
                content = f"📋 [bold green]Craigslist[/bold green]\n\n"
                content += f"Title: {ad_data['title']}\n"
                content += f"Category: {ad_data['category']}\n\n"
                content += f"Description:\n{ad_data['description'][:200]}..."
                
            elif platform == 'twitter':
                content = f"🐦 [bold cyan]Twitter/X[/bold cyan]\n\n"
                content += f"Tweet ({ad_data['character_count']}/280):\n"
                content += f"{ad_data['tweet']}\n\n"
                content += f"Hashtags: {len(ad_data.get('hashtags', []))}"
            
            panel = Panel(
                content,
                style=f"{'blue' if platform == 'facebook' else 'green' if platform == 'craigslist' else 'cyan'}",
                width=40
            )
            panels.append(panel)
        
        # Display in columns
        columns = Columns(panels, equal=True)
        self.console.print(columns)
    
    def export_ads(self, platform_ads):
        """Export ads to files"""
        if not Confirm.ask("\n💾 Export ads to files?"):
            return
        
        export_dir = Path("exports/ads")
        export_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for platform, ad_data in platform_ads.items():
            filename = f"{platform}_ad_{timestamp}.txt"
            filepath = export_dir / filename
            
            with open(filepath, 'w') as f:
                f.write(f"# {platform.title()} Ad Export\n")
                f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                for key, value in ad_data.items():
                    if isinstance(value, list):
                        f.write(f"{key.title()}:\n")
                        for item in value:
                            f.write(f"  - {item}\n")
                    else:
                        f.write(f"{key.title()}: {value}\n")
                f.write("\n")
            
            self.log_verbatim(f"📄 Exported {platform} ad to {filename}")
        
        self.console.print(f"✅ Ads exported to {export_dir}", style="green")

def main():
    """Test the multi-platform generator"""
    generator = MultiPlatformAdGenerator()
    
    # Sample product data
    sample_data = {
        'title': 'High Efficiency Monocrystalline Solar Panel',
        'brand': 'SolarTech',
        'model': 'ST-300W',
        'wattage': '300',
        'voltage': '24',
        'efficiency': '22',
        'condition': 'Used',
        'price': '150',
        'location': 'San Francisco, CA',
        'description': 'Excellent condition solar panel perfect for renewable energy projects'
    }
    
    generator.generate_all_platforms(sample_data)

if __name__ == "__main__":
    main()
