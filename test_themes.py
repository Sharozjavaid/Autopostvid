#!/usr/bin/env python3
"""
Test script for theme-based image generation.

Generates sample images for each theme to validate the prompts and visual styles.
Run this to preview how each theme looks before using in production.

Usage:
    python test_themes.py                    # Test all themes
    python test_themes.py glitch_titans      # Test specific theme
    python test_themes.py --list             # List available themes
"""

import os
import sys
import json
import argparse
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Import theme config
from theme_config import (
    THEMES,
    get_theme,
    get_enabled_themes,
    build_scene_prompt,
    TextOverlayMode,
    PHILOSOPHER_SCENES
)


# Output directory for test images
TEST_OUTPUT_DIR = "test_themes_output"


def ensure_output_dir():
    """Create output directory if it doesn't exist"""
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
    return TEST_OUTPUT_DIR


def generate_image_with_fal(prompt: str, filename: str, model: str = "gpt15") -> str:
    """Generate image using fal.ai"""
    try:
        import fal_client
        from PIL import Image
        import requests
        import io

        # Model configs
        models = {
            "gpt15": {
                "id": "fal-ai/gpt-image-1.5",
                "args": {
                    "image_size": "1024x1536",
                    "quality": "low",
                    "output_format": "png"
                }
            },
            "flux": {
                "id": "fal-ai/flux/schnell",
                "args": {
                    "image_size": "portrait_16_9",
                    "num_inference_steps": 4
                }
            }
        }

        model_config = models.get(model, models["gpt15"])

        print(f"  Generating with {model}...")
        result = fal_client.subscribe(
            model_config["id"],
            arguments={
                "prompt": prompt,
                "num_images": 1,
                **model_config["args"]
            }
        )

        images = result.get('images', [])
        if not images:
            print(f"  ERROR: No images returned")
            return None

        image_url = images[0].get('url')
        if not image_url:
            print(f"  ERROR: No URL in response")
            return None

        # Download image
        if image_url.startswith('data:'):
            import base64
            header, encoded = image_url.split(',', 1)
            image_bytes = base64.b64decode(encoded)
        else:
            response = requests.get(image_url)
            response.raise_for_status()
            image_bytes = response.content

        # Save
        image = Image.open(io.BytesIO(image_bytes))
        image.save(filename, 'PNG')
        print(f"  Saved: {filename}")
        return filename

    except Exception as e:
        print(f"  ERROR: {e}")
        return None


def add_programmatic_text(image_path: str, output_path: str, theme, text_data: dict) -> str:
    """Add text overlay using Pillow based on theme config"""
    try:
        from text_overlay import TextOverlay

        overlay = TextOverlay()

        title = text_data.get("title", "SAMPLE TITLE")
        subtitle = text_data.get("subtitle", "Sample subtitle text")
        number = text_data.get("number")

        # Get font from theme
        font_name = theme.text_config.font_name

        overlay.create_slide(
            background_path=image_path,
            output_path=output_path,
            title=title,
            subtitle=subtitle,
            slide_number=number,
            font_name=font_name
        )

        print(f"  Text overlay added: {output_path}")
        return output_path

    except Exception as e:
        print(f"  ERROR adding text: {e}")
        return image_path


def truncate_prompt(prompt: str, max_len: int = 80) -> str:
    """Truncate prompt for display"""
    prompt = prompt.replace('\n', ' ').strip()
    prompt = ' '.join(prompt.split())  # Collapse whitespace
    if len(prompt) > max_len:
        return prompt[:max_len-3] + "..."
    return prompt


def print_summary_table(results: list):
    """Print a formatted summary table of all generated images"""

    print("\n")
    print("=" * 120)
    print("GENERATION SUMMARY TABLE")
    print("=" * 120)

    # Header
    print(f"{'Theme':<18} {'Type':<10} {'Image Path':<45} {'Text Mode':<12} {'Font':<12}")
    print("-" * 120)

    for item in results:
        theme_name = item.get('theme', 'unknown')[:17]
        img_type = item.get('type', 'unknown')[:9]
        img_path = os.path.basename(item.get('image_path', 'N/A'))[:44]
        text_mode = item.get('text_mode', 'N/A')[:11]
        font = item.get('font', 'N/A')[:11]

        print(f"{theme_name:<18} {img_type:<10} {img_path:<45} {text_mode:<12} {font:<12}")

    print("=" * 120)

    # Prompts section
    print("\n")
    print("=" * 120)
    print("IMAGE PROMPTS USED")
    print("=" * 120)

    for item in results:
        theme_name = item.get('theme', 'unknown')
        img_type = item.get('type', 'unknown')
        prompt = item.get('prompt', 'N/A')

        print(f"\n[{theme_name} / {img_type}]")
        print("-" * 60)
        # Print prompt in wrapped format
        words = prompt.replace('\n', ' ').split()
        line = ""
        for word in words:
            if len(line) + len(word) + 1 > 100:
                print(f"  {line}")
                line = word
            else:
                line = f"{line} {word}".strip()
        if line:
            print(f"  {line}")

    print("\n" + "=" * 120)


def save_report(results: list, output_dir: str) -> str:
    """Save detailed report as JSON and text"""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # JSON report
    json_path = f"{output_dir}/test_report_{timestamp}.json"
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    # Text report
    txt_path = f"{output_dir}/test_report_{timestamp}.txt"
    with open(txt_path, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write(f"THEME TEST REPORT - {timestamp}\n")
        f.write("=" * 80 + "\n\n")

        for item in results:
            f.write(f"Theme: {item.get('theme')}\n")
            f.write(f"Type: {item.get('type')}\n")
            f.write(f"Image: {item.get('image_path')}\n")
            f.write(f"Text Mode: {item.get('text_mode')}\n")
            f.write(f"Font: {item.get('font')}\n")
            f.write(f"Text Title: {item.get('text_title')}\n")
            f.write(f"Text Subtitle: {item.get('text_subtitle')}\n")
            f.write(f"\nPrompt:\n{item.get('prompt')}\n")
            f.write("\n" + "-" * 80 + "\n\n")

    print(f"\nReports saved:")
    print(f"  JSON: {json_path}")
    print(f"  TXT:  {txt_path}")

    return json_path


def test_theme(theme_id: str, with_text: bool = True) -> dict:
    """Test a single theme by generating sample images"""

    theme = get_theme(theme_id)
    if not theme:
        print(f"ERROR: Theme '{theme_id}' not found")
        return {"success": False, "error": "Theme not found", "items": []}

    print(f"\n{'='*60}")
    print(f"TESTING THEME: {theme.name} ({theme_id})")
    print(f"{'='*60}")
    print(f"Description: {theme.description}")
    print(f"Text mode: {theme.text_config.mode.value}")
    print(f"Model: {theme.image_config.model}")

    output_dir = ensure_output_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = {"theme": theme_id, "images": [], "items": []}

    # Test 1: Hook/Intro image
    print(f"\n[1/3] Generating HOOK image...")
    hook_prompt = theme.image_config.hook_prompt
    hook_filename = f"{output_dir}/{theme_id}_hook_{timestamp}.png"
    hook_text = {"title": "THEY CHANGED EVERYTHING", "subtitle": "5 minds that shaped reality"}

    hook_bg = generate_image_with_fal(hook_prompt, hook_filename, theme.image_config.model)

    if hook_bg and with_text and theme.text_config.mode == TextOverlayMode.PROGRAMMATIC:
        hook_final = hook_filename.replace(".png", "_text.png")
        hook_final = add_programmatic_text(hook_bg, hook_final, theme, hook_text)
        results["images"].append({"type": "hook", "path": hook_final})
    elif hook_bg:
        hook_final = hook_bg
        results["images"].append({"type": "hook", "path": hook_bg})
    else:
        hook_final = None

    # Track for summary
    results["items"].append({
        "theme": theme_id,
        "type": "hook",
        "image_path": hook_final,
        "prompt": hook_prompt,
        "text_mode": theme.text_config.mode.value,
        "font": theme.text_config.font_name,
        "text_title": hook_text["title"],
        "text_subtitle": hook_text["subtitle"]
    })

    # Test 2: Content image (single philosopher)
    print(f"\n[2/3] Generating CONTENT image...")

    # Pick a philosopher based on theme
    if theme_id == "scene_portrait":
        content_prompt = build_scene_prompt(theme, "epictetus", 0)
        philosopher_name = "EPICTETUS"
    else:
        content_prompt = theme.image_config.content_prompt
        content_prompt = content_prompt.replace("[PHILOSOPHER_NAME]", "Marcus Aurelius")
        philosopher_name = "MARCUS AURELIUS"

    content_text = {"title": philosopher_name, "subtitle": "Born a slave. Died a legend.", "number": 2}
    content_filename = f"{output_dir}/{theme_id}_content_{timestamp}.png"
    content_bg = generate_image_with_fal(content_prompt, content_filename, theme.image_config.model)

    if content_bg and with_text and theme.text_config.mode == TextOverlayMode.PROGRAMMATIC:
        content_final = content_filename.replace(".png", "_text.png")
        content_final = add_programmatic_text(content_bg, content_final, theme, content_text)
        results["images"].append({"type": "content", "path": content_final})
    elif content_bg:
        content_final = content_bg
        results["images"].append({"type": "content", "path": content_bg})
    else:
        content_final = None

    results["items"].append({
        "theme": theme_id,
        "type": "content",
        "image_path": content_final,
        "prompt": content_prompt,
        "text_mode": theme.text_config.mode.value,
        "font": theme.text_config.font_name,
        "text_title": content_text["title"],
        "text_subtitle": content_text["subtitle"]
    })

    # Test 3: Outro image
    print(f"\n[3/3] Generating OUTRO image...")
    outro_prompt = theme.image_config.outro_prompt
    outro_filename = f"{output_dir}/{theme_id}_outro_{timestamp}.png"
    outro_text = {"title": "CHOOSE YOUR PATH", "subtitle": "Follow for more ancient wisdom"}

    outro_bg = generate_image_with_fal(outro_prompt, outro_filename, theme.image_config.model)

    if outro_bg and with_text and theme.text_config.mode == TextOverlayMode.PROGRAMMATIC:
        outro_final = outro_filename.replace(".png", "_text.png")
        outro_final = add_programmatic_text(outro_bg, outro_final, theme, outro_text)
        results["images"].append({"type": "outro", "path": outro_final})
    elif outro_bg:
        outro_final = outro_bg
        results["images"].append({"type": "outro", "path": outro_bg})
    else:
        outro_final = None

    results["items"].append({
        "theme": theme_id,
        "type": "outro",
        "image_path": outro_final,
        "prompt": outro_prompt,
        "text_mode": theme.text_config.mode.value,
        "font": theme.text_config.font_name,
        "text_title": outro_text["title"],
        "text_subtitle": outro_text["subtitle"]
    })

    results["success"] = len(results["images"]) > 0

    print(f"\n{'='*60}")
    print(f"THEME TEST COMPLETE: {theme_id}")
    print(f"Generated {len(results['images'])} images")
    for img in results["images"]:
        print(f"  - {img['type']}: {img['path']}")
    print(f"{'='*60}")

    return results


def test_all_themes(with_text: bool = True) -> dict:
    """Test all enabled themes"""

    print("\n" + "="*60)
    print("TESTING ALL ENABLED THEMES")
    print("="*60)

    enabled = get_enabled_themes()
    print(f"Found {len(enabled)} enabled themes: {list(enabled.keys())}")

    all_results = {}
    all_items = []

    for theme_id in enabled:
        results = test_theme(theme_id, with_text)
        all_results[theme_id] = results
        all_items.extend(results.get("items", []))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for theme_id, results in all_results.items():
        status = "PASS" if results.get("success") else "FAIL"
        count = len(results.get("images", []))
        print(f"  [{status}] {theme_id}: {count} images")

    # Print table and save report
    if all_items:
        print_summary_table(all_items)
        save_report(all_items, TEST_OUTPUT_DIR)

    return all_results


def list_themes():
    """List all available themes"""
    from theme_config import list_all_themes
    list_all_themes()


def main():
    parser = argparse.ArgumentParser(description="Test theme-based image generation")
    parser.add_argument("theme", nargs="?", help="Specific theme to test (or 'all')")
    parser.add_argument("--list", action="store_true", help="List available themes")
    parser.add_argument("--no-text", action="store_true", help="Skip text overlay")
    parser.add_argument("--backgrounds-only", action="store_true", help="Only generate backgrounds")

    args = parser.parse_args()

    if args.list:
        list_themes()
        return

    with_text = not args.no_text and not args.backgrounds_only
    ensure_output_dir()

    if args.theme and args.theme != "all":
        results = test_theme(args.theme, with_text)
        # Print table and save report for single theme too
        items = results.get("items", [])
        if items:
            print_summary_table(items)
            save_report(items, TEST_OUTPUT_DIR)
    else:
        test_all_themes(with_text)


if __name__ == "__main__":
    main()
