#!/usr/bin/env python3
"""
Interactive Font Testing Script

Run this to test different fonts on your existing background images instantly.

Usage:
    python3 test_fonts_live.py

This will:
1. Show you available fonts
2. Let you pick a background image
3. Generate samples with ALL fonts so you can compare
4. Or test a specific font with custom text
"""

import os
import sys
from text_overlay import TextOverlay

def list_backgrounds():
    """Find all background images in generated_slideshows/backgrounds/"""
    bg_dir = "generated_slideshows/backgrounds"
    if not os.path.exists(bg_dir):
        print(f"❌ No backgrounds folder found at {bg_dir}")
        return []
    
    backgrounds = [f for f in os.listdir(bg_dir) if f.endswith('.png')]
    return [os.path.join(bg_dir, f) for f in sorted(backgrounds)]

def list_any_images():
    """Find any PNG images we can use as backgrounds"""
    dirs_to_check = [
        "generated_slideshows/backgrounds",
        "generated_slideshows",
        "generated_images",
        "font_samples"
    ]
    
    images = []
    for d in dirs_to_check:
        if os.path.exists(d):
            for f in os.listdir(d):
                if f.endswith('.png') and 'sample_' not in f:
                    images.append(os.path.join(d, f))
    
    return sorted(images)[:10]  # Return max 10

def generate_all_font_samples(background_path: str, output_dir: str = "font_test_output"):
    """Generate the same slide with ALL available fonts for comparison."""
    
    os.makedirs(output_dir, exist_ok=True)
    overlay = TextOverlay()
    
    # Get available fonts
    fonts = overlay.get_available_fonts()
    
    print(f"\n🎨 Generating samples with {len(fonts)} fonts...")
    print(f"   Background: {background_path}")
    print(f"   Output: {output_dir}/\n")
    
    # Test text
    title = "The Kings of Wisdom"
    subtitle = "5 ancient minds whose words still echo through time"
    
    for font_id, info in fonts.items():
        output_path = os.path.join(output_dir, f"test_{font_id}.png")
        
        # Determine if uppercase based on category
        uppercase = info['category'] in ['modern', 'display', 'classical']
        
        overlay.create_slide(
            background_path=background_path,
            output_path=output_path,
            title=title,
            subtitle=subtitle,
            font_name=font_id,
            uppercase_title=uppercase,
            style="modern"
        )
        print(f"  ✅ {font_id}: {info['name']}")
    
    print(f"\n🎉 Done! Open {output_dir}/ to compare fonts")

def test_single_font(background_path: str, font_name: str, title: str, subtitle: str = None):
    """Test a single font with custom text."""
    
    overlay = TextOverlay()
    output_path = f"font_test_output/custom_{font_name}.png"
    os.makedirs("font_test_output", exist_ok=True)
    
    overlay.create_slide(
        background_path=background_path,
        output_path=output_path,
        title=title,
        subtitle=subtitle,
        font_name=font_name,
        style="modern"
    )
    
    print(f"✅ Created: {output_path}")
    return output_path

def test_quick(background_path: str = None):
    """Quick test with a gradient background if no image provided."""
    
    overlay = TextOverlay()
    os.makedirs("font_test_output", exist_ok=True)
    
    # Create gradient background if needed
    if background_path is None:
        background_path = "font_test_output/gradient_bg.png"
        overlay.create_solid_background(background_path, color=(25, 30, 45), gradient=True)
        print(f"Created gradient background: {background_path}")
    
    generate_all_font_samples(background_path)

def interactive_mode():
    """Interactive menu for testing fonts."""
    
    overlay = TextOverlay()
    print("\n" + "=" * 60)
    print("🎨 FONT TESTING - Interactive Mode")
    print("=" * 60)
    
    # Show available fonts
    print("\n📝 Available Fonts:")
    fonts = overlay.get_available_fonts()
    for font_id, info in fonts.items():
        print(f"   {font_id}: {info['name']} ({info['category']})")
    
    # Find available backgrounds
    print("\n🖼️ Available Background Images:")
    images = list_any_images()
    if images:
        for i, img in enumerate(images):
            print(f"   [{i}] {img}")
    else:
        print("   No images found - will create gradient background")
    
    print("\n" + "-" * 60)
    print("OPTIONS:")
    print("  1. Generate ALL fonts on a background (for comparison)")
    print("  2. Test specific font with custom text")
    print("  3. Quick test with gradient background")
    print("  q. Quit")
    print("-" * 60)
    
    choice = input("\nChoice (1/2/3/q): ").strip()
    
    if choice == "1":
        if images:
            idx = input(f"Pick background [0-{len(images)-1}] or press Enter for gradient: ").strip()
            if idx and idx.isdigit() and int(idx) < len(images):
                bg = images[int(idx)]
            else:
                bg = None
                overlay.create_solid_background("font_test_output/gradient_bg.png", gradient=True)
                bg = "font_test_output/gradient_bg.png"
        else:
            os.makedirs("font_test_output", exist_ok=True)
            overlay.create_solid_background("font_test_output/gradient_bg.png", gradient=True)
            bg = "font_test_output/gradient_bg.png"
        
        generate_all_font_samples(bg)
    
    elif choice == "2":
        font = input(f"Font name ({', '.join(fonts.keys())}): ").strip()
        if font not in fonts:
            print(f"❌ Unknown font. Available: {', '.join(fonts.keys())}")
            return
        
        title = input("Title text: ").strip() or "The Kings of Wisdom"
        subtitle = input("Subtitle (optional): ").strip() or None
        
        if images:
            idx = input(f"Pick background [0-{len(images)-1}] or Enter for gradient: ").strip()
            if idx and idx.isdigit() and int(idx) < len(images):
                bg = images[int(idx)]
            else:
                os.makedirs("font_test_output", exist_ok=True)
                overlay.create_solid_background("font_test_output/gradient_bg.png", gradient=True)
                bg = "font_test_output/gradient_bg.png"
        else:
            os.makedirs("font_test_output", exist_ok=True)
            overlay.create_solid_background("font_test_output/gradient_bg.png", gradient=True)
            bg = "font_test_output/gradient_bg.png"
        
        test_single_font(bg, font, title, subtitle)
    
    elif choice == "3":
        test_quick()
    
    elif choice.lower() == "q":
        print("Bye!")
    else:
        print("Invalid choice")

# Direct function for quick Python testing
def quick_test(font: str, title: str, subtitle: str = None, bg_path: str = None):
    """
    Quick function to test a font from Python console.
    
    Example:
        from test_fonts_live import quick_test
        quick_test("cormorant", "Inner Peace", "The path to wisdom begins within")
    """
    overlay = TextOverlay()
    os.makedirs("font_test_output", exist_ok=True)
    
    if bg_path is None:
        bg_path = "font_test_output/quick_bg.png"
        overlay.create_solid_background(bg_path, gradient=True)
    
    output = f"font_test_output/quick_{font}.png"
    overlay.create_slide(
        background_path=bg_path,
        output_path=output,
        title=title,
        subtitle=subtitle,
        font_name=font
    )
    print(f"✅ {output}")
    return output

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Command line mode
        if sys.argv[1] == "--all":
            # Generate all fonts on gradient
            test_quick()
        elif sys.argv[1] == "--bg" and len(sys.argv) > 2:
            # Generate all fonts on specific background
            generate_all_font_samples(sys.argv[2])
        else:
            print("Usage:")
            print("  python3 test_fonts_live.py           # Interactive mode")
            print("  python3 test_fonts_live.py --all     # All fonts on gradient")
            print("  python3 test_fonts_live.py --bg path/to/image.png")
    else:
        interactive_mode()
