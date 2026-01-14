#!/usr/bin/env python3
"""
Text Overlay Module - Burns styled text onto images for TikTok slideshows

This module provides high-quality text rendering on images with:
- Multiple font styles (bold, regular, light)
- Text shadows and outlines for readability
- Smart text wrapping and positioning
- TikTok-style aesthetic (clean, bold, modern)

Usage:
    from text_overlay import TextOverlay
    
    overlay = TextOverlay()
    
    # Simple text overlay
    overlay.add_text_to_image(
        image_path="background.png",
        text="5 PHILOSOPHERS WHO CHANGED THE WORLD",
        output_path="slide_1.png"
    )
    
    # Multi-line slide with title and subtitle
    overlay.create_slide(
        background_path="bg.png",
        title="MARCUS AURELIUS",
        subtitle="The most powerful man on Earth asked himself every night: 'Was I a good person today?'",
        slide_number=1,
        output_path="slide.png"
    )
"""

import os
from typing import Optional, Tuple, List
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import textwrap
import math


class TextOverlay:
    """
    Creates TikTok-style text overlays on images.
    
    Mimics the aesthetic of CapCut/TikTok's text editor:
    - Bold, clean sans-serif fonts
    - White text with subtle shadows
    - Centered, prominent text placement
    - Modern, scroll-stopping look
    """
    
    # Default colors
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    SHADOW_COLOR = (0, 0, 0, 180)  # Semi-transparent black
    
    # TikTok slide dimensions (9:16 vertical)
    TIKTOK_WIDTH = 1080
    TIKTOK_HEIGHT = 1920
    
    # Available font options - each maps to specific font files
    # These can be selected in the UI for instant experimentation
    FONTS = {
        # TikTok Official Fonts - The authentic TikTok look
        "tiktok": {
            "name": "TikTok Sans",
            "description": "Official TikTok font - authentic app look, clean and modern",
            "file": "TikTokSans-Regular.ttf",
            "category": "tiktok",
            "settings": {
                "uppercase": False,  # TikTok uses sentence case
                "shadow": True,      # Drop shadow for legibility
                "outline": True,     # Thin outline for contrast
                "outline_width": 2,  # Thin outline
            }
        },
        "tiktok-bold": {
            "name": "TikTok Sans Display",
            "description": "Official TikTok display font - bold headlines",
            "file": "TikTokSans-Bold.ttf",
            "category": "tiktok",
            "settings": {
                "uppercase": False,
                "shadow": True,
                "outline": True,
                "outline_width": 2,
            }
        },
        
        # Social Media Style - Clean, readable, modern
        "social": {
            "name": "Social Media (Clean)",
            "description": "Clean sans-serif like Helvetica/Inter - perfect for social media, sentence case",
            "file": "Montserrat-Bold.ttf",
            "category": "social",
            "settings": {
                "uppercase": False,  # Sentence case
                "shadow": True,      # Drop shadow for legibility
                "outline": True,     # Thin outline for contrast
                "outline_width": 2,  # Thin outline
            }
        },
        
        # Modern Sans-Serif (TikTok/Instagram style)
        "montserrat": {
            "name": "Montserrat Bold",
            "description": "Clean geometric sans-serif - modern TikTok look",
            "file": "Montserrat-Bold.ttf",
            "category": "modern"
        },
        "oswald": {
            "name": "Oswald Bold",
            "description": "Condensed sans-serif - impactful headlines",
            "file": "Oswald-Bold.ttf",
            "category": "modern"
        },
        "bebas": {
            "name": "Bebas Neue",
            "description": "All-caps display font - very bold and punchy",
            "file": "Bebas-Regular.ttf",
            "category": "display"
        },
        
        # Elegant Italic (Philosophaire style)
        "cormorant": {
            "name": "Cormorant Garamond Italic",
            "description": "Classical italic - @philosophaire style, old-world sophistication",
            "file": "CormorantGaramond-Italic.ttf",
            "category": "elegant"
        },
        "montserrat-italic": {
            "name": "Montserrat Italic",
            "description": "Modern italic sans-serif - clean and stylish",
            "file": "Montserrat-Italic.ttf",
            "category": "elegant"
        },
        
        # Classical (Ancient/Roman style)
        "cinzel": {
            "name": "Cinzel Bold",
            "description": "Roman/classical capitals - ancient wisdom vibes",
            "file": "Cinzel-Bold.ttf",
            "category": "classical"
        },
    }
    
    # Grouped by style for easy selection
    FONT_CATEGORIES = {
        "tiktok": ["tiktok", "tiktok-bold"],
        "social": ["social"],
        "modern": ["montserrat", "oswald"],
        "elegant": ["cormorant", "montserrat-italic"],
        "classical": ["cinzel"],
        "display": ["bebas", "oswald", "tiktok-bold"]
    }
    
    # Legacy style mappings (for backwards compatibility)
    FONT_STYLES = {
        "bold": {
            "description": "Bold sans-serif (modern TikTok style)",
            "fonts": ["Montserrat-Bold.ttf", "Oswald-Bold.ttf", "Bebas-Regular.ttf"]
        },
        "italic": {
            "description": "Elegant italic (like @philosophaire style)",
            "fonts": ["CormorantGaramond-Italic.ttf", "Montserrat-Italic.ttf"]
        },
        "elegant": {
            "description": "Refined serif italic (sophisticated look)",
            "fonts": ["CormorantGaramond-Italic.ttf", "Montserrat-Italic.ttf"]
        },
        "classical": {
            "description": "Roman/classical style",
            "fonts": ["Cinzel-Bold.ttf"]
        },
        "display": {
            "description": "Bold display/headline fonts",
            "fonts": ["Bebas-Regular.ttf", "Oswald-Bold.ttf"]
        },
        "social": {
            "description": "Clean social media style - sentence case, readable",
            "fonts": ["Montserrat-Bold.ttf"]
        }
    }
    
    def __init__(self, fonts_dir: str = "fonts", default_style: str = "social"):
        """
        Initialize TextOverlay with font settings.
        
        Args:
            fonts_dir: Directory containing custom fonts (optional)
            default_style: Default font style ("social", "bold", "italic", "elegant")
                - "social": Clean sans-serif, sentence case (recommended for TikTok)
                - "bold": Bold sans-serif, uppercase
                - "italic"/"elegant": Italic serif
        """
        self.fonts_dir = fonts_dir
        self._font_cache = {}
        self.default_style = default_style
        
        # System font paths by platform (fallbacks)
        self.system_font_paths = {
            "darwin": [  # macOS
                "/System/Library/Fonts/Helvetica.ttc",
                "/System/Library/Fonts/HelveticaNeue.ttc",
                "/Library/Fonts/Arial Bold.ttf",
                "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                "/System/Library/Fonts/SFNS.ttf",
                # Italic fallbacks
                "/System/Library/Fonts/Supplemental/Times New Roman Italic.ttf",
                "/Library/Fonts/Georgia Italic.ttf",
            ],
            "linux": [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
            ],
            "win32": [
                "C:/Windows/Fonts/arialbd.ttf",
                "C:/Windows/Fonts/segoeui.ttf",
            ]
        }
        
        print(f"📝 TextOverlay initialized (style: {default_style})")
    
    def _get_font(self, size: int, style: str = None, font_name: str = None) -> ImageFont.FreeTypeFont:
        """
        Get a font at the specified size, with caching.
        
        Args:
            size: Font size in pixels
            style: Font style ("bold", "italic", "elegant", "classical", "display") 
            font_name: Specific font name (e.g., "playfair", "inter", "bebas") - overrides style
        
        Returns:
            PIL ImageFont object
        """
        # If specific font requested, use that
        if font_name and font_name in self.FONTS:
            cache_key = f"{size}_{font_name}"
            if cache_key in self._font_cache:
                return self._font_cache[cache_key]
            
            font_config = self.FONTS[font_name]
            font_path = os.path.join(self.fonts_dir, font_config["file"])
            
            if os.path.exists(font_path):
                try:
                    font = ImageFont.truetype(font_path, size)
                    self._font_cache[cache_key] = font
                    return font
                except Exception as e:
                    print(f"⚠️ Could not load font {font_name}: {e}")
        
        # Fall back to style-based selection
        if style is None:
            style = self.default_style
        
        cache_key = f"{size}_{style}"
        if cache_key in self._font_cache:
            return self._font_cache[cache_key]
        
        font = None
        
        # Get font names for this style
        style_config = self.FONT_STYLES.get(style, self.FONT_STYLES.get("bold", {"fonts": []}))
        font_names = style_config.get("fonts", [])
        
        # First, check for custom fonts in fonts_dir (preferred)
        if os.path.exists(self.fonts_dir):
            # Try style-specific fonts first
            for fname in font_names:
                font_path = os.path.join(self.fonts_dir, fname)
                if os.path.exists(font_path):
                    try:
                        font = ImageFont.truetype(font_path, size)
                        break
                    except:
                        pass
            
            # If not found, try any matching font file
            if font is None:
                style_keywords = {
                    "bold": ["bold", "inter", "montserrat", "oswald"],
                    "italic": ["italic", "oblique"],
                    "elegant": ["italic", "playfair", "lora", "cormorant"],
                    "classical": ["cinzel"],
                    "display": ["bebas", "oswald"]
                }
                keywords = style_keywords.get(style, ["bold"])
                
                for fname in os.listdir(self.fonts_dir):
                    if fname.lower().endswith(('.ttf', '.otf')):
                        if any(kw in fname.lower() for kw in keywords):
                            font_path = os.path.join(self.fonts_dir, fname)
                            try:
                                font = ImageFont.truetype(font_path, size)
                                break
                            except:
                                pass
        
        # Try system fonts
        if font is None:
            import sys
            platform = sys.platform
            font_paths = self.system_font_paths.get(platform, [])
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        font = ImageFont.truetype(font_path, size)
                        break
                    except:
                        pass
        
        # Ultimate fallback to default
        if font is None:
            try:
                font = ImageFont.truetype("Arial", size)
            except:
                font = ImageFont.load_default()
                print(f"⚠️ Using default font (custom fonts not found)")
        
        self._font_cache[cache_key] = font
        return font
    
    def get_available_fonts(self) -> dict:
        """
        Get list of all available fonts for UI selection.
        
        Returns:
            Dictionary with font info for each available font
        """
        available = {}
        for font_id, font_info in self.FONTS.items():
            font_path = os.path.join(self.fonts_dir, font_info["file"])
            if os.path.exists(font_path):
                available[font_id] = font_info
        return available
    
    def list_fonts(self):
        """Print available fonts to console."""
        print("\n📝 Available Fonts:")
        print("=" * 50)
        for font_id, info in self.get_available_fonts().items():
            print(f"  {font_id}: {info['name']}")
            print(f"     {info['description']}")
            print(f"     Category: {info['category']}")
            print()
    
    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
        """
        Wrap text to fit within a maximum width.
        
        Args:
            text: The text to wrap
            font: The font being used
            max_width: Maximum width in pixels
        
        Returns:
            List of text lines
        """
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
    
    def _draw_text_with_shadow(
        self,
        draw: ImageDraw.Draw,
        position: Tuple[int, int],
        text: str,
        font: ImageFont.FreeTypeFont,
        text_color: Tuple[int, int, int] = None,
        shadow_color: Tuple[int, int, int, int] = None,
        shadow_offset: Tuple[int, int] = (4, 4),
        shadow_blur: int = 8
    ):
        """
        Draw text with a shadow effect.
        
        Args:
            draw: PIL ImageDraw object
            position: (x, y) position for the text
            text: Text to draw
            font: Font to use
            text_color: RGB color tuple for text
            shadow_color: RGBA color tuple for shadow
            shadow_offset: (x, y) offset for shadow
            shadow_blur: Blur radius for shadow (not used with basic draw)
        """
        if text_color is None:
            text_color = self.WHITE
        if shadow_color is None:
            shadow_color = self.SHADOW_COLOR
        
        x, y = position
        sx, sy = shadow_offset
        
        # Draw shadow (multiple passes for blur effect)
        for offset in range(1, 4):
            shadow_pos = (x + sx * offset // 3, y + sy * offset // 3)
            # Draw shadow with decreasing opacity
            alpha = shadow_color[3] // offset if len(shadow_color) == 4 else 100
            draw.text(shadow_pos, text, font=font, fill=(*shadow_color[:3], alpha))
        
        # Draw main text
        draw.text((x, y), text, font=font, fill=text_color)
    
    def _draw_text_with_outline(
        self,
        draw: ImageDraw.Draw,
        position: Tuple[int, int],
        text: str,
        font: ImageFont.FreeTypeFont,
        text_color: Tuple[int, int, int] = None,
        outline_color: Tuple[int, int, int] = None,
        outline_width: int = 3
    ):
        """
        Draw text with an outline (stroke) effect.
        
        Args:
            draw: PIL ImageDraw object
            position: (x, y) position for the text
            text: Text to draw
            font: Font to use
            text_color: RGB color tuple for text
            outline_color: RGB color tuple for outline
            outline_width: Width of outline in pixels
        """
        if text_color is None:
            text_color = self.WHITE
        if outline_color is None:
            outline_color = self.BLACK
        
        x, y = position
        
        # Draw outline by drawing text in multiple positions
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
        
        # Draw main text
        draw.text((x, y), text, font=font, fill=text_color)
    
    def _draw_text_social_style(
        self,
        draw: ImageDraw.Draw,
        position: Tuple[int, int],
        text: str,
        font: ImageFont.FreeTypeFont,
        text_color: Tuple[int, int, int] = None,
        outline_color: Tuple[int, int, int] = None,
        shadow_color: Tuple[int, int, int, int] = None,
        outline_width: int = 2
    ):
        """
        Draw text with BOTH shadow AND thin outline - optimized for social media readability.
        
        This creates the clean, readable style common in Instagram/TikTok graphics:
        - Drop shadow for depth
        - Thin black outline for legibility against any background
        - White text for contrast
        
        Args:
            draw: PIL ImageDraw object
            position: (x, y) position for the text
            text: Text to draw
            font: Font to use
            text_color: RGB color tuple for text (default: white)
            outline_color: RGB color tuple for outline (default: black)
            shadow_color: RGBA color tuple for shadow
            outline_width: Width of outline in pixels (default: 2 for thin)
        """
        if text_color is None:
            text_color = self.WHITE
        if outline_color is None:
            outline_color = self.BLACK
        if shadow_color is None:
            shadow_color = self.SHADOW_COLOR
        
        x, y = position
        
        # Step 1: Draw drop shadow (offset to bottom-right)
        shadow_offset = (3, 3)
        sx, sy = shadow_offset
        for offset in range(1, 3):
            shadow_pos = (x + sx * offset // 2, y + sy * offset // 2)
            alpha = shadow_color[3] // offset if len(shadow_color) == 4 else 120
            draw.text(shadow_pos, text, font=font, fill=(*shadow_color[:3], alpha))
        
        # Step 2: Draw thin outline
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
        
        # Step 3: Draw main text on top
        draw.text((x, y), text, font=font, fill=text_color)
    
    def add_text_to_image(
        self,
        image_path: str,
        text: str,
        output_path: str,
        font_size: int = 80,
        position: str = "center",  # "center", "top", "bottom"
        text_color: Tuple[int, int, int] = None,
        use_shadow: bool = True,
        use_outline: bool = False,
        max_width_ratio: float = 0.85,
        y_offset: int = 0,
        font_style: str = None,  # "bold", "italic", "elegant"
        font_name: str = None  # Specific font: "inter", "playfair", "bebas", etc.
    ) -> str:
        """
        Add text overlay to an image.
        
        Args:
            image_path: Path to the background image
            text: Text to overlay
            output_path: Path for the output image
            font_size: Font size in pixels
            position: Vertical position ("center", "top", "bottom")
            text_color: RGB color tuple
            use_shadow: Add drop shadow
            use_outline: Add text outline
            max_width_ratio: Max text width as ratio of image width
            y_offset: Additional vertical offset in pixels
            font_style: Font style ("bold", "italic", "elegant")
            font_name: Specific font name ("inter", "playfair", "bebas", etc.)
        
        Returns:
            Path to the output image
        """
        # Load the image
        img = Image.open(image_path).convert("RGBA")
        
        # Create a transparent overlay for text
        txt_layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_layer)
        
        # Get font with specified style or specific font name
        font = self._get_font(font_size, style=font_style, font_name=font_name)
        
        # Calculate max width for text
        max_width = int(img.width * max_width_ratio)
        
        # Wrap text
        lines = self._wrap_text(text, font, max_width)
        
        # Calculate total text height
        line_heights = []
        for line in lines:
            bbox = font.getbbox(line)
            line_heights.append(bbox[3] - bbox[1])
        
        line_spacing = int(font_size * 0.3)
        total_height = sum(line_heights) + line_spacing * (len(lines) - 1)
        
        # Calculate starting Y position
        if position == "center":
            start_y = (img.height - total_height) // 2
        elif position == "top":
            start_y = int(img.height * 0.15)
        elif position == "bottom":
            start_y = int(img.height * 0.65)
        else:
            start_y = (img.height - total_height) // 2
        
        start_y += y_offset
        
        # Draw each line
        current_y = start_y
        for i, line in enumerate(lines):
            bbox = font.getbbox(line)
            line_width = bbox[2] - bbox[0]
            x = (img.width - line_width) // 2  # Center horizontally
            
            if use_outline:
                self._draw_text_with_outline(draw, (x, current_y), line, font, text_color)
            elif use_shadow:
                self._draw_text_with_shadow(draw, (x, current_y), line, font, text_color)
            else:
                if text_color is None:
                    text_color = self.WHITE
                draw.text((x, current_y), line, font=font, fill=text_color)
            
            current_y += line_heights[i] + line_spacing
        
        # Composite the text layer onto the image
        result = Image.alpha_composite(img, txt_layer)
        
        # Save
        result = result.convert("RGB")
        result.save(output_path, quality=95)
        
        return output_path
    
    def create_slide(
        self,
        background_path: str,
        output_path: str,
        title: Optional[str] = None,
        subtitle: Optional[str] = None,
        slide_number: Optional[int] = None,
        title_size: int = 90,
        subtitle_size: int = 50,
        number_size: int = 60,
        style: str = "modern",  # "modern", "bold", "minimal", "elegant", "philosophaire"
        font_style: str = None,  # "bold", "italic", "elegant" - overrides default
        font_name: str = None,  # Specific font: "inter", "playfair", "bebas", etc.
        uppercase_title: bool = True  # Whether to force title to uppercase
    ) -> str:
        """
        Create a complete TikTok slide with title, subtitle, and optional number.
        
        This creates the look you see in viral TikTok slideshows:
        - Optional "#1" at the top
        - Bold title in the center
        - Smaller subtitle below
        
        Args:
            background_path: Path to background image
            output_path: Path for output
            title: Main text (e.g., "MARCUS AURELIUS")
            subtitle: Secondary text (quote or explanation)
            slide_number: Optional number to display (e.g., 1 -> "#1")
            title_size: Font size for title
            subtitle_size: Font size for subtitle
            number_size: Font size for slide number
            style: Visual style preset ("modern", "bold", "minimal", "elegant", "philosophaire")
            font_style: Font style ("bold", "italic", "elegant") - None uses default
            font_name: Specific font name ("inter", "playfair", "bebas", "cinzel", etc.)
            uppercase_title: Whether to force title to uppercase
        
        Returns:
            Path to output image
        """
        # Load the image
        img = Image.open(background_path).convert("RGBA")
        
        # Resize to TikTok dimensions if needed
        if img.size != (self.TIKTOK_WIDTH, self.TIKTOK_HEIGHT):
            img = ImageOps.fit(img, (self.TIKTOK_WIDTH, self.TIKTOK_HEIGHT), method=Image.Resampling.LANCZOS)
        
        # Create text layer
        txt_layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_layer)
        
        # Check if font_name has special settings (like "social")
        font_settings = {}
        if font_name and font_name in self.FONTS:
            font_settings = self.FONTS[font_name].get('settings', {})
        
        # Apply font-specific settings if present
        if font_settings:
            # Social media style: sentence case, shadow + thin outline
            use_outline = font_settings.get('outline', False)
            use_shadow = font_settings.get('shadow', True)
            outline_width = font_settings.get('outline_width', 2)
            if 'uppercase' in font_settings:
                uppercase_title = font_settings['uppercase']
        # Style settings - determines outline/shadow behavior
        elif style == "bold":
            use_outline = True
            use_shadow = False
            outline_width = 4
        elif style == "minimal":
            use_outline = False
            use_shadow = False
        elif style in ["elegant", "philosophaire"]:
            # Elegant italic style like @philosophaire
            use_outline = False
            use_shadow = True
            if font_style is None:
                font_style = "italic"
            uppercase_title = False  # Elegant styles usually don't use all-caps
        elif style == "social":
            # Clean social media style - sentence case, readable
            use_outline = True
            use_shadow = True
            outline_width = 2
            uppercase_title = False
        else:  # modern (default)
            use_outline = False
            use_shadow = True
        
        # Determine which font to use (specific font_name takes priority)
        title_font_style = font_style if font_style else "bold"
        subtitle_font_style = font_style if font_style else "italic"  # Subtitles look good in italic
        
        # Calculate layout positions
        center_y = img.height // 2
        elements_height = 0
        spacing = 40
        
        # Calculate total content height to center everything
        if slide_number is not None:
            elements_height += number_size + spacing
        if title:
            elements_height += title_size + spacing
        if subtitle:
            subtitle_font = self._get_font(subtitle_size, style=subtitle_font_style, font_name=font_name)
            max_width = int(img.width * 0.85)
            subtitle_lines = self._wrap_text(subtitle, subtitle_font, max_width)
            subtitle_total_height = len(subtitle_lines) * (subtitle_size + 10)
            elements_height += subtitle_total_height
        
        # Start Y position (centered)
        current_y = center_y - elements_height // 2
        
        # Helper to draw text with correct style
        def draw_styled_text(draw_obj, pos, txt, fnt, o_width=None):
            if use_shadow and use_outline:
                # Social media style: shadow + thin outline
                self._draw_text_social_style(draw_obj, pos, txt, fnt, outline_width=o_width or outline_width)
            elif use_outline:
                self._draw_text_with_outline(draw_obj, pos, txt, fnt, outline_width=o_width or outline_width)
            elif use_shadow:
                self._draw_text_with_shadow(draw_obj, pos, txt, fnt)
            else:
                draw_obj.text(pos, txt, font=fnt, fill=self.WHITE)
        
        # Draw slide number (if provided)
        if slide_number is not None:
            number_text = f"#{slide_number}"
            number_font = self._get_font(number_size, style=title_font_style, font_name=font_name)
            bbox = number_font.getbbox(number_text)
            number_width = bbox[2] - bbox[0]
            x = (img.width - number_width) // 2
            
            draw_styled_text(draw, (x, current_y), number_text, number_font)
            current_y += number_size + spacing
        
        # Draw title
        if title:
            title_font = self._get_font(title_size, style=title_font_style, font_name=font_name)
            max_width = int(img.width * 0.9)
            display_title = title.upper() if uppercase_title else title
            title_lines = self._wrap_text(display_title, title_font, max_width)
            
            for line in title_lines:
                bbox = title_font.getbbox(line)
                line_width = bbox[2] - bbox[0]
                x = (img.width - line_width) // 2
                
                draw_styled_text(draw, (x, current_y), line, title_font)
                current_y += title_size + 10
            
            current_y += spacing - 10
        
        # Draw subtitle
        if subtitle:
            subtitle_font = self._get_font(subtitle_size, style=subtitle_font_style, font_name=font_name)
            max_width = int(img.width * 0.85)
            subtitle_lines = self._wrap_text(subtitle, subtitle_font, max_width)
            
            for line in subtitle_lines:
                bbox = subtitle_font.getbbox(line)
                line_width = bbox[2] - bbox[0]
                x = (img.width - line_width) // 2
                
                draw_styled_text(draw, (x, current_y), line, subtitle_font, o_width=2)
                current_y += subtitle_size + 10
        
        # Composite
        result = Image.alpha_composite(img, txt_layer)
        result = result.convert("RGB")
        result.save(output_path, quality=95)
        
        print(f"  ✅ Created slide: {output_path}")
        return output_path
    
    def create_hook_slide(
        self,
        background_path: str,
        output_path: str,
        hook_text: str,
        font_size: int = 85,
        style: str = "modern",  # "modern", "elegant", "philosophaire"
        font_style: str = None,
        font_name: str = None  # Specific font: "inter", "playfair", "bebas", etc.
    ) -> str:
        """
        Create a hook/intro slide (first slide that grabs attention).
        
        Args:
            background_path: Path to background image
            output_path: Path for output
            hook_text: The attention-grabbing text
            font_size: Font size
            style: Visual style ("modern", "elegant", "philosophaire")
            font_style: Font style ("bold", "italic", "elegant")
            font_name: Specific font name ("inter", "playfair", "bebas", etc.)
        
        Returns:
            Path to output image
        """
        # Determine uppercase based on style
        uppercase = style not in ["elegant", "philosophaire"]
        display_text = hook_text.upper() if uppercase else hook_text
        
        # Use italic for elegant styles (if no specific font_name given)
        if font_style is None and font_name is None and style in ["elegant", "philosophaire"]:
            font_style = "italic"
        
        return self.add_text_to_image(
            image_path=background_path,
            text=display_text,
            output_path=output_path,
            font_size=font_size,
            position="center",
            use_shadow=True,
            max_width_ratio=0.88,
            font_style=font_style,
            font_name=font_name
        )
    
    def create_outro_slide(
        self,
        background_path: str,
        output_path: str,
        text: str,
        subtitle: Optional[str] = None,
        font_size: int = 80,
        style: str = "modern",
        font_style: str = None,
        font_name: str = None
    ) -> str:
        """
        Create an outro/CTA slide (final slide).
        
        Args:
            background_path: Path to background image
            output_path: Path for output
            text: Main outro text
            subtitle: Optional secondary text
            font_size: Font size
            style: Visual style
            font_style: Font style
            font_name: Specific font name
        
        Returns:
            Path to output image
        """
        return self.create_slide(
            background_path=background_path,
            output_path=output_path,
            title=text,
            subtitle=subtitle,
            title_size=font_size,
            subtitle_size=int(font_size * 0.5),
            style=style,
            font_style=font_style,
            font_name=font_name
        )
    
    def create_solid_background(
        self,
        output_path: str,
        color: Tuple[int, int, int] = (20, 20, 25),  # Dark gray
        width: int = None,
        height: int = None,
        gradient: bool = True
    ) -> str:
        """
        Create a solid or gradient background image.
        
        Useful when you don't have a background image.
        
        Args:
            output_path: Path for output
            color: Base RGB color
            width: Image width (default: TikTok width)
            height: Image height (default: TikTok height)
            gradient: Add subtle vertical gradient
        
        Returns:
            Path to output image
        """
        width = width or self.TIKTOK_WIDTH
        height = height or self.TIKTOK_HEIGHT
        
        if gradient:
            # Create gradient from darker at bottom to lighter at top
            img = Image.new("RGB", (width, height))
            
            for y in range(height):
                # Calculate gradient factor (0 at bottom, 1 at top)
                factor = 1 - (y / height)
                
                # Lighter at top, darker at bottom
                r = int(color[0] + (40 * factor))
                g = int(color[1] + (40 * factor))
                b = int(color[2] + (50 * factor))
                
                for x in range(width):
                    img.putpixel((x, y), (r, g, b))
        else:
            img = Image.new("RGB", (width, height), color)
        
        img.save(output_path, quality=95)
        return output_path


def create_tiktok_slideshow(
    slides_data: List[dict],
    background_images: List[str],
    output_dir: str = "generated_slideshows"
) -> List[str]:
    """
    Convenience function to create a complete TikTok slideshow.
    
    Args:
        slides_data: List of dicts with 'title', 'subtitle', 'slide_number', 'slide_type'
        background_images: List of background image paths
        output_dir: Directory for output images
    
    Returns:
        List of paths to generated slides
    """
    os.makedirs(output_dir, exist_ok=True)
    overlay = TextOverlay()
    
    output_paths = []
    
    for i, slide in enumerate(slides_data):
        bg_path = background_images[i] if i < len(background_images) else background_images[-1]
        slide_type = slide.get('slide_type', 'content')
        output_path = os.path.join(output_dir, f"slide_{i}.png")
        
        if slide_type == 'hook':
            path = overlay.create_hook_slide(
                background_path=bg_path,
                output_path=output_path,
                hook_text=slide.get('display_text', slide.get('title', ''))
            )
        elif slide_type == 'outro':
            path = overlay.create_outro_slide(
                background_path=bg_path,
                output_path=output_path,
                text=slide.get('display_text', slide.get('title', '')),
                subtitle=slide.get('subtitle')
            )
        else:
            path = overlay.create_slide(
                background_path=bg_path,
                output_path=output_path,
                title=slide.get('display_text', slide.get('title')),
                subtitle=slide.get('subtitle'),
                slide_number=slide.get('slide_number')
            )
        
        output_paths.append(path)
    
    return output_paths


# Test
if __name__ == "__main__":
    print("🧪 Testing TextOverlay")
    print("=" * 50)
    
    overlay = TextOverlay()
    
    # Create a test background
    test_bg = "test_background.png"
    overlay.create_solid_background(test_bg, color=(25, 25, 35), gradient=True)
    print(f"✅ Created test background: {test_bg}")
    
    # Test hook slide
    hook_output = "test_hook_slide.png"
    overlay.create_hook_slide(
        background_path=test_bg,
        output_path=hook_output,
        hook_text="6 philosophical practices successful people use daily to find inner peace"
    )
    print(f"✅ Created hook slide: {hook_output}")
    
    # Test content slide
    content_output = "test_content_slide.png"
    overlay.create_slide(
        background_path=test_bg,
        output_path=content_output,
        title="MARCUS AURELIUS",
        subtitle="The most powerful man on Earth asked himself every night: 'Was I a good person today?'",
        slide_number=1
    )
    print(f"✅ Created content slide: {content_output}")
    
    print("\n🎉 Tests complete! Check the output files.")
