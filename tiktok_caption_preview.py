#!/usr/bin/env python3
"""
TikTok Caption Preview Tool

Overlays TikTok-style captions on slideshow images to preview how they'll
look when posted. Simulates the TikTok caption bar that appears at the bottom.

Usage:
    python tiktok_caption_preview.py --image slide.png --caption "Your caption here"
    python tiktok_caption_preview.py --slideshow "Stoicism_in_60_Seconds" --caption "5 Stoic lessons..."
    python tiktok_caption_preview.py --interactive  # Live preview mode
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Optional, List, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import textwrap


class TikTokCaptionPreview:
    """Simulates TikTok caption overlay for preview purposes."""
    
    # TikTok UI dimensions (9:16 vertical)
    TIKTOK_WIDTH = 1080
    TIKTOK_HEIGHT = 1920
    
    # Caption bar settings
    CAPTION_AREA_HEIGHT = 280  # Height of the caption area at bottom
    CAPTION_PADDING = 40
    CAPTION_BOTTOM_MARGIN = 160  # Space for TikTok UI (like, comment, share buttons)
    
    # Username/profile area
    PROFILE_AREA_HEIGHT = 60
    
    # Colors
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    GRAY = (180, 180, 180)
    
    def __init__(self, fonts_dir: str = "fonts"):
        self.fonts_dir = fonts_dir
        self._font_cache = {}
        print("📱 TikTok Caption Preview initialized")
    
    def _get_font(self, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        """Get TikTok-style font."""
        cache_key = f"{size}_{bold}"
        if cache_key in self._font_cache:
            return self._font_cache[cache_key]
        
        font = None
        font_file = "TikTokSans-Bold.ttf" if bold else "TikTokSans-Regular.ttf"
        font_path = os.path.join(self.fonts_dir, font_file)
        
        if os.path.exists(font_path):
            try:
                font = ImageFont.truetype(font_path, size)
            except:
                pass
        
        # Fallback fonts
        if font is None:
            fallbacks = [
                os.path.join(self.fonts_dir, "Montserrat-Bold.ttf"),
                "/System/Library/Fonts/Helvetica.ttc",
                "/System/Library/Fonts/SFNS.ttf",
            ]
            for fb in fallbacks:
                if os.path.exists(fb):
                    try:
                        font = ImageFont.truetype(fb, size)
                        break
                    except:
                        pass
        
        if font is None:
            font = ImageFont.load_default()
        
        self._font_cache[cache_key] = font
        return font
    
    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
        """Wrap text to fit within max width."""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = font.getbbox(test_line)
            line_width = bbox[2] - bbox[0]
            
            if line_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def add_tiktok_caption(
        self,
        image_path: str,
        caption: str,
        output_path: Optional[str] = None,
        username: str = "@philosophaire",
        show_hashtags: bool = True,
        show_ui_elements: bool = True
    ) -> str:
        """
        Add TikTok-style caption overlay to an image.
        
        Args:
            image_path: Path to the slide image
            caption: The caption text
            output_path: Where to save (default: adds _preview suffix)
            username: TikTok username to display
            show_hashtags: Whether to show hashtag styling
            show_ui_elements: Whether to show simulated TikTok UI
        
        Returns:
            Path to the preview image
        """
        # Load image
        img = Image.open(image_path).convert("RGBA")
        
        # Resize to TikTok dimensions if needed
        if img.size != (self.TIKTOK_WIDTH, self.TIKTOK_HEIGHT):
            from PIL import ImageOps
            img = ImageOps.fit(img, (self.TIKTOK_WIDTH, self.TIKTOK_HEIGHT), method=Image.Resampling.LANCZOS)
        
        # Create overlay layer
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Add gradient at bottom for caption readability
        gradient_height = 400
        for y in range(gradient_height):
            alpha = int(180 * (y / gradient_height))  # Fade from transparent to semi-opaque
            y_pos = self.TIKTOK_HEIGHT - gradient_height + y
            draw.line([(0, y_pos), (self.TIKTOK_WIDTH, y_pos)], fill=(0, 0, 0, alpha))
        
        # Calculate caption area
        caption_y = self.TIKTOK_HEIGHT - self.CAPTION_BOTTOM_MARGIN - self.CAPTION_AREA_HEIGHT
        max_caption_width = self.TIKTOK_WIDTH - (self.CAPTION_PADDING * 2) - 100  # Leave space for right-side icons
        
        # Draw username
        username_font = self._get_font(42, bold=True)
        username_y = caption_y
        draw.text(
            (self.CAPTION_PADDING, username_y),
            username,
            font=username_font,
            fill=self.WHITE
        )
        
        # Draw caption text
        caption_font = self._get_font(36, bold=False)
        caption_lines = self._wrap_text(caption, caption_font, max_caption_width)
        
        # Limit to 3 lines (TikTok truncates)
        if len(caption_lines) > 3:
            caption_lines = caption_lines[:3]
            caption_lines[-1] = caption_lines[-1][:50] + "... more"
        
        line_y = username_y + 55
        line_height = 44
        
        for line in caption_lines:
            # Check for hashtags and style them
            if show_hashtags and '#' in line:
                # Draw hashtags in a slightly different style
                x_pos = self.CAPTION_PADDING
                words = line.split()
                for word in words:
                    if word.startswith('#'):
                        # Hashtag styling (slightly brighter)
                        draw.text((x_pos, line_y), word + " ", font=caption_font, fill=(200, 200, 255))
                    else:
                        draw.text((x_pos, line_y), word + " ", font=caption_font, fill=self.WHITE)
                    bbox = caption_font.getbbox(word + " ")
                    x_pos += bbox[2] - bbox[0]
            else:
                draw.text(
                    (self.CAPTION_PADDING, line_y),
                    line,
                    font=caption_font,
                    fill=self.WHITE
                )
            line_y += line_height
        
        # Draw simulated TikTok UI elements (right side icons)
        if show_ui_elements:
            self._draw_tiktok_ui(draw)
        
        # Composite
        result = Image.alpha_composite(img, overlay)
        result = result.convert("RGB")
        
        # Output path
        if output_path is None:
            base = Path(image_path)
            output_path = str(base.parent / f"{base.stem}_caption_preview{base.suffix}")
        
        result.save(output_path, quality=95)
        print(f"✅ Created preview: {output_path}")
        
        return output_path
    
    def _draw_tiktok_ui(self, draw: ImageDraw.Draw):
        """Draw simulated TikTok UI elements (like, comment, share icons)."""
        # Right side icon positions
        icon_x = self.TIKTOK_WIDTH - 70
        icon_size = 45
        icon_spacing = 80
        
        # Starting Y for icons (profile, like, comment, share, save)
        icons_start_y = self.TIKTOK_HEIGHT // 2 + 50
        
        icons = ["❤️", "💬", "↗️", "🔖"]
        counts = ["42.5K", "1,234", "Share", ""]
        
        count_font = self._get_font(24, bold=False)
        
        for i, (icon, count) in enumerate(zip(icons, counts)):
            y = icons_start_y + (i * icon_spacing)
            
            # Draw circle background for icon
            circle_radius = icon_size // 2
            draw.ellipse(
                [icon_x - circle_radius, y - circle_radius, 
                 icon_x + circle_radius, y + circle_radius],
                fill=(40, 40, 40, 200)
            )
            
            # Draw count below
            if count:
                bbox = count_font.getbbox(count)
                count_width = bbox[2] - bbox[0]
                draw.text(
                    (icon_x - count_width // 2, y + circle_radius + 8),
                    count,
                    font=count_font,
                    fill=self.WHITE
                )
        
        # Draw profile picture circle at top of icons
        profile_y = icons_start_y - 100
        profile_radius = 28
        draw.ellipse(
            [icon_x - profile_radius, profile_y - profile_radius,
             icon_x + profile_radius, profile_y + profile_radius],
            fill=(100, 100, 100, 255),
            outline=self.WHITE,
            width=2
        )
        
        # Draw + button for follow
        plus_y = profile_y + profile_radius + 5
        draw.ellipse(
            [icon_x - 12, plus_y - 12, icon_x + 12, plus_y + 12],
            fill=(255, 45, 85, 255)  # TikTok red/pink
        )
    
    def preview_slideshow(
        self,
        slideshow_name: str,
        caption: str,
        slides_dir: str = "generated_slideshows/gpt15",
        username: str = "@philosophaire"
    ) -> List[str]:
        """
        Preview captions on all slides of a slideshow.
        
        Args:
            slideshow_name: Name pattern to match slides
            caption: Caption to overlay
            slides_dir: Directory containing slides
            username: TikTok username
        
        Returns:
            List of preview image paths
        """
        slides_path = Path(slides_dir)
        
        # Find all matching slides
        pattern = f"{slideshow_name}*slide*.png"
        slides = sorted(slides_path.glob(pattern))
        
        if not slides:
            print(f"❌ No slides found matching: {pattern}")
            return []
        
        print(f"📱 Previewing {len(slides)} slides with caption...")
        
        output_dir = slides_path / "caption_previews"
        output_dir.mkdir(exist_ok=True)
        
        previews = []
        for slide in slides:
            output_path = output_dir / f"{slide.stem}_preview.png"
            self.add_tiktok_caption(
                str(slide),
                caption,
                str(output_path),
                username
            )
            previews.append(str(output_path))
        
        print(f"\n✅ Created {len(previews)} preview images in: {output_dir}")
        return previews


def main():
    parser = argparse.ArgumentParser(
        description="Preview TikTok captions on slideshow images"
    )
    parser.add_argument(
        "--image", "-i",
        help="Single image to preview"
    )
    parser.add_argument(
        "--slideshow", "-s",
        help="Slideshow name pattern (e.g., 'Stoicism_in_60_Seconds')"
    )
    parser.add_argument(
        "--caption", "-c",
        default="5 Stoic lessons that changed my life #stoicism #philosophy #wisdom",
        help="Caption text to overlay"
    )
    parser.add_argument(
        "--username", "-u",
        default="@philosophaire",
        help="TikTok username"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output path (for single image)"
    )
    parser.add_argument(
        "--list-slideshows",
        action="store_true",
        help="List available slideshows"
    )
    
    args = parser.parse_args()
    
    preview = TikTokCaptionPreview()
    
    if args.list_slideshows:
        slides_dir = Path("generated_slideshows/gpt15")
        if slides_dir.exists():
            # Find unique slideshow names
            names = set()
            for f in slides_dir.glob("*_slide_0.png"):
                name = f.stem.replace("_slide_0", "").replace("_gpt15", "")
                names.add(name)
            
            print("\n📂 Available Slideshows:")
            for name in sorted(names):
                print(f"  - {name}")
        return
    
    if args.image:
        preview.add_tiktok_caption(
            args.image,
            args.caption,
            args.output,
            args.username
        )
    elif args.slideshow:
        preview.preview_slideshow(
            args.slideshow,
            args.caption,
            username=args.username
        )
    else:
        # Demo mode - use the most recent slideshow
        print("\n🎬 Demo Mode - Previewing 'Stoicism_in_60_Seconds'")
        print("=" * 50)
        
        demo_caption = "5 Stoic lessons that will change your perspective forever #stoicism #philosophy #marcusaurelius #wisdom #motivation"
        
        preview.preview_slideshow(
            "Stoicism_in_60_Seconds_gpt15",
            demo_caption,
            username="@philosophaire"
        )


if __name__ == "__main__":
    main()
