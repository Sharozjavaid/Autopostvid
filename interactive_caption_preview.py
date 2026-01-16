#!/usr/bin/env python3
"""
Interactive TikTok Caption Preview

Opens a simple GUI window where you can:
1. View your slideshow images
2. Type different captions and see them overlaid in real-time
3. Cycle through slides with arrow keys
4. Save previews

Usage:
    python interactive_caption_preview.py
    python interactive_caption_preview.py --slideshow "Stoicism_in_60_Seconds_gpt15"
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from PIL import Image, ImageTk, ImageDraw, ImageFont
from typing import List, Optional
import threading


class InteractiveCaptionPreview:
    """Interactive GUI for previewing TikTok captions on images."""
    
    def __init__(self, slideshow_name: Optional[str] = None):
        self.root = tk.Tk()
        self.root.title("TikTok Caption Preview")
        self.root.geometry("600x1100")
        self.root.configure(bg="#1a1a2e")
        
        # State
        self.slides: List[Path] = []
        self.current_index = 0
        self.fonts_dir = "fonts"
        self._font_cache = {}
        
        # Setup UI
        self._setup_ui()
        
        # Load slideshow if provided
        if slideshow_name:
            self.load_slideshow(slideshow_name)
        else:
            self._find_slideshows()
    
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
        
        if font is None:
            fallbacks = [
                os.path.join(self.fonts_dir, "Montserrat-Bold.ttf"),
                "/System/Library/Fonts/Helvetica.ttc",
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
    
    def _setup_ui(self):
        """Create the UI layout."""
        # Main container
        main_frame = tk.Frame(self.root, bg="#1a1a2e")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Slideshow selector
        selector_frame = tk.Frame(main_frame, bg="#1a1a2e")
        selector_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            selector_frame, 
            text="Slideshow:", 
            fg="white", 
            bg="#1a1a2e",
            font=("Helvetica", 12)
        ).pack(side=tk.LEFT)
        
        self.slideshow_var = tk.StringVar()
        self.slideshow_combo = ttk.Combobox(
            selector_frame, 
            textvariable=self.slideshow_var,
            width=40
        )
        self.slideshow_combo.pack(side=tk.LEFT, padx=10)
        self.slideshow_combo.bind("<<ComboboxSelected>>", self._on_slideshow_selected)
        
        # Image display (scaled to fit window while maintaining aspect ratio)
        self.canvas = tk.Canvas(
            main_frame, 
            width=540, 
            height=960,  # 9:16 ratio scaled down
            bg="#000000",
            highlightthickness=0
        )
        self.canvas.pack(pady=10)
        
        # Navigation buttons
        nav_frame = tk.Frame(main_frame, bg="#1a1a2e")
        nav_frame.pack(fill=tk.X, pady=5)
        
        self.prev_btn = tk.Button(
            nav_frame,
            text="◀ Previous",
            command=self.prev_slide,
            bg="#16213e",
            fg="white",
            font=("Helvetica", 11),
            padx=20
        )
        self.prev_btn.pack(side=tk.LEFT, padx=5)
        
        self.slide_label = tk.Label(
            nav_frame,
            text="Slide 0/0",
            fg="white",
            bg="#1a1a2e",
            font=("Helvetica", 12, "bold")
        )
        self.slide_label.pack(side=tk.LEFT, expand=True)
        
        self.next_btn = tk.Button(
            nav_frame,
            text="Next ▶",
            command=self.next_slide,
            bg="#16213e",
            fg="white",
            font=("Helvetica", 11),
            padx=20
        )
        self.next_btn.pack(side=tk.RIGHT, padx=5)
        
        # Caption input
        caption_frame = tk.Frame(main_frame, bg="#1a1a2e")
        caption_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(
            caption_frame,
            text="Caption:",
            fg="white",
            bg="#1a1a2e",
            font=("Helvetica", 12)
        ).pack(anchor=tk.W)
        
        self.caption_text = tk.Text(
            caption_frame,
            height=3,
            width=60,
            font=("Helvetica", 11),
            wrap=tk.WORD
        )
        self.caption_text.pack(fill=tk.X, pady=5)
        self.caption_text.insert("1.0", "5 Stoic lessons that changed my life forever #stoicism #philosophy #wisdom")
        self.caption_text.bind("<KeyRelease>", self._on_caption_change)
        
        # Username input
        user_frame = tk.Frame(main_frame, bg="#1a1a2e")
        user_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(
            user_frame,
            text="Username:",
            fg="white",
            bg="#1a1a2e",
            font=("Helvetica", 11)
        ).pack(side=tk.LEFT)
        
        self.username_var = tk.StringVar(value="@philosophaire")
        self.username_entry = tk.Entry(
            user_frame,
            textvariable=self.username_var,
            font=("Helvetica", 11),
            width=20
        )
        self.username_entry.pack(side=tk.LEFT, padx=10)
        self.username_entry.bind("<KeyRelease>", self._on_caption_change)
        
        # Save button
        self.save_btn = tk.Button(
            user_frame,
            text="💾 Save Preview",
            command=self.save_current_preview,
            bg="#00f5d4",
            fg="#1a1a2e",
            font=("Helvetica", 11, "bold"),
            padx=15
        )
        self.save_btn.pack(side=tk.RIGHT)
        
        # Keyboard bindings
        self.root.bind("<Left>", lambda e: self.prev_slide())
        self.root.bind("<Right>", lambda e: self.next_slide())
        self.root.bind("<Command-s>", lambda e: self.save_current_preview())
    
    def _find_slideshows(self):
        """Find available slideshows."""
        slides_dir = Path("generated_slideshows/gpt15")
        if not slides_dir.exists():
            return
        
        names = set()
        for f in slides_dir.glob("*_slide_0.png"):
            # Extract slideshow name
            stem = f.stem
            if "_slide_" in stem:
                name = stem.rsplit("_slide_", 1)[0]
                names.add(name)
        
        self.slideshow_combo["values"] = sorted(names)
        if names:
            self.slideshow_combo.current(0)
            self.load_slideshow(sorted(names)[0])
    
    def _on_slideshow_selected(self, event):
        """Handle slideshow selection."""
        name = self.slideshow_var.get()
        self.load_slideshow(name)
    
    def load_slideshow(self, name: str):
        """Load a slideshow's slides."""
        slides_dir = Path("generated_slideshows/gpt15")
        
        # Find all slides for this slideshow
        pattern = f"{name}*slide*.png"
        self.slides = sorted(slides_dir.glob(pattern))
        
        if not self.slides:
            messagebox.showwarning("No Slides", f"No slides found for: {name}")
            return
        
        self.current_index = 0
        self._update_display()
    
    def _on_caption_change(self, event=None):
        """Handle caption text change - update preview."""
        # Debounce: wait a bit before updating
        if hasattr(self, '_update_timer'):
            self.root.after_cancel(self._update_timer)
        self._update_timer = self.root.after(200, self._update_display)
    
    def _update_display(self):
        """Update the displayed image with caption overlay."""
        if not self.slides:
            return
        
        slide_path = self.slides[self.current_index]
        caption = self.caption_text.get("1.0", tk.END).strip()
        username = self.username_var.get()
        
        # Load and process image
        img = Image.open(slide_path).convert("RGBA")
        
        # Resize to TikTok dimensions
        target_size = (1080, 1920)
        if img.size != target_size:
            from PIL import ImageOps
            img = ImageOps.fit(img, target_size, method=Image.Resampling.LANCZOS)
        
        # Add caption overlay
        img = self._add_caption_overlay(img, caption, username)
        
        # Scale for display (fit in canvas)
        display_width = 540
        display_height = 960
        img_display = img.resize((display_width, display_height), Image.Resampling.LANCZOS)
        
        # Convert to PhotoImage
        self.photo = ImageTk.PhotoImage(img_display)
        
        # Update canvas
        self.canvas.delete("all")
        self.canvas.create_image(
            display_width // 2, 
            display_height // 2, 
            image=self.photo
        )
        
        # Update slide counter
        self.slide_label.config(text=f"Slide {self.current_index + 1}/{len(self.slides)}")
    
    def _add_caption_overlay(
        self, 
        img: Image.Image, 
        caption: str, 
        username: str
    ) -> Image.Image:
        """Add TikTok-style caption overlay to image."""
        # Create overlay
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        width, height = img.size
        
        # Gradient at bottom
        gradient_height = 400
        for y in range(gradient_height):
            alpha = int(180 * (y / gradient_height))
            y_pos = height - gradient_height + y
            draw.line([(0, y_pos), (width, y_pos)], fill=(0, 0, 0, alpha))
        
        # Caption area
        padding = 40
        bottom_margin = 160
        caption_y = height - bottom_margin - 200
        max_width = width - (padding * 2) - 100
        
        # Username
        username_font = self._get_font(42, bold=True)
        draw.text((padding, caption_y), username, font=username_font, fill=(255, 255, 255))
        
        # Caption
        caption_font = self._get_font(36, bold=False)
        
        # Wrap text
        words = caption.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = caption_font.getbbox(test_line)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        
        # Limit lines
        if len(lines) > 3:
            lines = lines[:3]
            lines[-1] = lines[-1][:40] + "..."
        
        line_y = caption_y + 55
        for line in lines:
            draw.text((padding, line_y), line, font=caption_font, fill=(255, 255, 255))
            line_y += 44
        
        # Right side icons (simplified)
        icon_x = width - 70
        icons_start_y = height // 2 + 50
        icon_spacing = 80
        
        for i in range(4):
            y = icons_start_y + (i * icon_spacing)
            draw.ellipse(
                [icon_x - 22, y - 22, icon_x + 22, y + 22],
                fill=(40, 40, 40, 200)
            )
        
        # Profile pic
        profile_y = icons_start_y - 100
        draw.ellipse(
            [icon_x - 28, profile_y - 28, icon_x + 28, profile_y + 28],
            fill=(100, 100, 100, 255),
            outline=(255, 255, 255),
            width=2
        )
        
        # Composite
        return Image.alpha_composite(img, overlay)
    
    def prev_slide(self):
        """Go to previous slide."""
        if self.slides and self.current_index > 0:
            self.current_index -= 1
            self._update_display()
    
    def next_slide(self):
        """Go to next slide."""
        if self.slides and self.current_index < len(self.slides) - 1:
            self.current_index += 1
            self._update_display()
    
    def save_current_preview(self):
        """Save the current preview image."""
        if not self.slides:
            return
        
        slide_path = self.slides[self.current_index]
        caption = self.caption_text.get("1.0", tk.END).strip()
        username = self.username_var.get()
        
        # Generate preview
        img = Image.open(slide_path).convert("RGBA")
        target_size = (1080, 1920)
        if img.size != target_size:
            from PIL import ImageOps
            img = ImageOps.fit(img, target_size, method=Image.Resampling.LANCZOS)
        
        img = self._add_caption_overlay(img, caption, username)
        img = img.convert("RGB")
        
        # Save
        output_dir = slide_path.parent / "caption_previews"
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"{slide_path.stem}_preview.png"
        
        img.save(str(output_path), quality=95)
        messagebox.showinfo("Saved", f"Preview saved to:\n{output_path}")
    
    def run(self):
        """Start the GUI."""
        self.root.mainloop()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Interactive TikTok caption preview")
    parser.add_argument("--slideshow", "-s", help="Slideshow name to load")
    args = parser.parse_args()
    
    app = InteractiveCaptionPreview(args.slideshow)
    app.run()


if __name__ == "__main__":
    main()
