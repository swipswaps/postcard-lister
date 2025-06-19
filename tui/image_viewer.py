#!/usr/bin/env python3
################################################################################
# FILE: tui/image_viewer.py
# DESC: Terminal image display for Solar Panel TUI
# WHAT: Display images in terminal using ASCII art and Unicode blocks
# WHY: Visual feedback for solar panel processing in terminal
# FAIL: Falls back to file path display if image rendering fails
# UX: Thumbnail previews and full image display in terminal
################################################################################

import sys
from pathlib import Path

try:
    from PIL import Image
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.columns import Columns
    import io
except ImportError:
    print("🔧 Installing image display packages...")
    import subprocess
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'Pillow', 'rich'], check=True)
    from PIL import Image
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.columns import Columns

class TerminalImageViewer:
    """
    WHAT: Display images in terminal using ASCII and Unicode blocks
    WHY: Visual feedback for solar panel images in TUI
    FAIL: Shows file info if image display fails
    UX: Thumbnail and full-size image display
    """
    
    def __init__(self, console=None):
        self.console = console or Console()
        
    def image_to_ascii(self, image_path, width=80, height=24):
        """
        WHAT: Convert image to ASCII art for terminal display
        WHY: Show solar panel images visually in terminal
        FAIL: Returns error message if conversion fails
        UX: ASCII representation of solar panel image
        """
        try:
            # Open and resize image
            with Image.open(image_path) as img:
                # Convert to grayscale
                img = img.convert('L')
                
                # Calculate aspect ratio
                aspect_ratio = img.height / img.width
                new_height = int(width * aspect_ratio * 0.5)  # 0.5 for terminal character aspect
                
                # Resize image
                img = img.resize((width, new_height))
                
                # ASCII characters from dark to light
                ascii_chars = "@%#*+=-:. "
                
                # Convert pixels to ASCII
                ascii_art = []
                for y in range(img.height):
                    line = ""
                    for x in range(img.width):
                        pixel = img.getpixel((x, y))
                        char_index = pixel * (len(ascii_chars) - 1) // 255
                        line += ascii_chars[char_index]
                    ascii_art.append(line)
                
                return "\n".join(ascii_art)
                
        except Exception as e:
            return f"❌ Failed to display image: {e}\n📁 File: {image_path}"
    
    def image_to_unicode_blocks(self, image_path, width=40, height=20):
        """
        WHAT: Convert image to Unicode block characters for better quality
        WHY: Higher quality image display in terminal
        FAIL: Falls back to ASCII if Unicode blocks fail
        UX: Block-based image representation
        """
        try:
            # Unicode block characters for different brightness levels
            blocks = [" ", "░", "▒", "▓", "█"]
            
            with Image.open(image_path) as img:
                # Convert to grayscale
                img = img.convert('L')
                
                # Calculate aspect ratio
                aspect_ratio = img.height / img.width
                new_height = int(width * aspect_ratio * 0.5)
                
                # Resize image
                img = img.resize((width, new_height))
                
                # Convert pixels to Unicode blocks
                block_art = []
                for y in range(img.height):
                    line = ""
                    for x in range(img.width):
                        pixel = img.getpixel((x, y))
                        block_index = pixel * (len(blocks) - 1) // 255
                        line += blocks[block_index]
                    block_art.append(line)
                
                return "\n".join(block_art)
                
        except Exception as e:
            # Fall back to ASCII
            return self.image_to_ascii(image_path, width, height)
    
    def show_image_thumbnail(self, image_path):
        """
        WHAT: Display small thumbnail of image in terminal
        WHY: Quick preview of solar panel image
        FAIL: Shows file info if thumbnail fails
        UX: Small image preview with file details
        """
        try:
            # Get image info
            with Image.open(image_path) as img:
                width, height = img.size
                file_size = Path(image_path).stat().st_size
                
                # Create thumbnail
                thumbnail = self.image_to_unicode_blocks(image_path, width=30, height=15)
                
                # Image info
                info_text = f"📁 File: {Path(image_path).name}\n"
                info_text += f"📐 Size: {width}×{height}\n"
                info_text += f"💾 File Size: {file_size:,} bytes\n"
                info_text += f"🖼️ Format: {img.format}"
                
                # Create columns layout
                thumbnail_panel = Panel(thumbnail, title="🖼️ Preview", style="cyan")
                info_panel = Panel(info_text, title="📋 Image Info", style="blue")
                
                columns = Columns([thumbnail_panel, info_panel], equal=True)
                return columns
                
        except Exception as e:
            error_panel = Panel(
                f"❌ Cannot display image: {e}\n📁 File: {image_path}",
                title="🖼️ Image Error",
                style="red"
            )
            return error_panel
    
    def show_image_full(self, image_path):
        """
        WHAT: Display full-size image in terminal
        WHY: Detailed view of solar panel for analysis
        FAIL: Shows error message if display fails
        UX: Large image display with controls
        """
        try:
            # Get terminal size
            console_size = self.console.size
            max_width = min(console_size.width - 4, 120)
            max_height = min(console_size.height - 10, 40)
            
            # Create full-size display
            full_image = self.image_to_unicode_blocks(image_path, width=max_width, height=max_height)
            
            # Get image details
            with Image.open(image_path) as img:
                width, height = img.size
                
            title = f"🖼️ {Path(image_path).name} ({width}×{height})"
            
            image_panel = Panel(
                full_image,
                title=title,
                style="cyan",
                padding=(1, 2)
            )
            
            return image_panel
            
        except Exception as e:
            error_panel = Panel(
                f"❌ Cannot display full image: {e}\n📁 File: {image_path}",
                title="🖼️ Display Error",
                style="red"
            )
            return error_panel
    
    def show_image_gallery(self, image_paths):
        """
        WHAT: Display multiple images in a gallery layout
        WHY: Show batch processing results visually
        FAIL: Shows file list if gallery display fails
        UX: Grid of image thumbnails
        """
        try:
            thumbnails = []
            
            for image_path in image_paths[:6]:  # Limit to 6 images
                try:
                    thumbnail = self.image_to_unicode_blocks(image_path, width=20, height=10)
                    filename = Path(image_path).name
                    
                    thumb_panel = Panel(
                        thumbnail,
                        title=f"📷 {filename[:15]}...",
                        style="cyan",
                        width=25
                    )
                    thumbnails.append(thumb_panel)
                    
                except Exception:
                    # Skip failed images
                    continue
            
            if thumbnails:
                gallery = Columns(thumbnails, equal=True)
                
                gallery_panel = Panel(
                    gallery,
                    title=f"🖼️ Image Gallery ({len(image_paths)} images)",
                    style="blue"
                )
                return gallery_panel
            else:
                # Fallback to file list
                file_list = "\n".join([f"📁 {Path(p).name}" for p in image_paths])
                list_panel = Panel(
                    file_list,
                    title=f"📋 Image Files ({len(image_paths)} files)",
                    style="yellow"
                )
                return list_panel
                
        except Exception as e:
            error_panel = Panel(
                f"❌ Gallery display error: {e}\n📋 Files: {len(image_paths)} images",
                title="🖼️ Gallery Error",
                style="red"
            )
            return error_panel

def test_image_viewer():
    """Test the image viewer with sample images"""
    console = Console()
    viewer = TerminalImageViewer(console)
    
    # Test with a sample image (if available)
    test_images = [
        "solar_panel.jpg",
        "test_image.png",
        "sample.jpg"
    ]
    
    console.print("🔧 Testing Terminal Image Viewer", style="bold cyan")
    
    for image_path in test_images:
        if Path(image_path).exists():
            console.print(f"\n📷 Testing: {image_path}")
            console.print(viewer.show_image_thumbnail(image_path))
            break
    else:
        console.print("⚠️ No test images found. Place an image file to test.", style="yellow")

if __name__ == "__main__":
    test_image_viewer()
