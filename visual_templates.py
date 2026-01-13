#!/usr/bin/env python3
"""
Visual Templates for Philosophy Video Generator

Manages reusable image generation templates that define the visual style/aesthetic
for philosophy videos. Similar to script templates, but for image generation prompts.

Templates can be applied to any list-style content (5 philosophers, 7 quotes, etc.)
to maintain consistent visual identity across all generated images.
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime

# Default templates directory
TEMPLATES_DIR = "visual_templates"

# Built-in templates
BUILTIN_TEMPLATES = {
    "ancient_chamber_glitch": {
        "id": "ancient_chamber_glitch",
        "name": "Ancient Chamber with Glitch",
        "description": "Dark ancient chamber with marble statues, golden text, and cyberpunk glitch effects. Perfect for dramatic 'X Philosophers Who Changed History' style videos.",
        "category": "epic_historical",
        "preview_image": None,
        "created_at": "2026-01-10T00:00:00",
        "is_builtin": True,
        "base_prompt": """A vertical poster in a dark, ancient chamber with cracked stone walls and an ornate wrought-iron hook hanging from the top center, oil painting style with high detail and dramatic shadows, warm flickering candlelight illuminating everything. Central bold text overlay '[TITLE_TEXT]' in large uppercase metallic gold serif font with engraved texture and subtle glow, exactly matching the thick vintage style of 'THEY CHANGED EVERYTHING'. Compose a collage of four marble statues around the text: on the left, a serious bust of [FIGURE1_DESCRIPTION]; upper right, a muscular [FIGURE2_DESCRIPTION] reaching upward holding a lit candle; lower left, a crouching [FIGURE3_DESCRIPTION] in dynamic pose; lower right, a seated wise [FIGURE4_DESCRIPTION] in thoughtful robes. Apply subtle digital glitch effects with RGB color separation and colorful pixel distortion lines on the statues' edges, blending historical epic atmosphere with modern cyberpunk interference. Photorealistic rendering, high contrast, no modern elements besides glitches, aspect ratio 9:16.""",
        "placeholders": {
            "TITLE_TEXT": {
                "description": "Main title text displayed prominently",
                "example": "THEY CHANGED EVERYTHING",
                "required": True
            },
            "FIGURE1_DESCRIPTION": {
                "description": "Description of the left bust figure",
                "example": "Socrates with intense gaze",
                "required": True
            },
            "FIGURE2_DESCRIPTION": {
                "description": "Description of the upper right reaching figure",
                "example": "Marcus Aurelius figure in imperial armor",
                "required": True
            },
            "FIGURE3_DESCRIPTION": {
                "description": "Description of the lower left crouching figure",
                "example": "Diogenes in dynamic questioning pose",
                "required": True
            },
            "FIGURE4_DESCRIPTION": {
                "description": "Description of the lower right seated wise figure",
                "example": "Plato in thoughtful robes holding a scroll",
                "required": True
            }
        },
        "style_notes": [
            "Oil painting texture on marble statues",
            "Subtle digital glitches (RGB separation)",
            "Warm candlelight illumination",
            "Dark atmospheric chamber with cracked walls",
            "Ornate hanging hook at top center",
            "Metallic gold serif font with engraved feel"
        ],
        "best_for": ["List videos (5 philosophers, 7 quotes)", "Epic introductions", "Historical figures"],
        "model_hints": {
            "midjourney": "--ar 9:16 --v 6 --style raw",
            "dall-e": "Use HD quality, vertical format",
            "stable_diffusion": "Strength 0.7-0.8 for consistency"
        }
    },
    "classical_renaissance": {
        "id": "classical_renaissance",
        "name": "Classical Renaissance",
        "description": "Traditional Renaissance oil painting style with Caravaggio/Rembrandt lighting. Timeless and elegant.",
        "category": "classical",
        "preview_image": None,
        "created_at": "2026-01-10T00:00:00",
        "is_builtin": True,
        "base_prompt": """A dramatic Renaissance oil painting in the style of Caravaggio and Rembrandt. [SCENE_DESCRIPTION]. The scene features [MAIN_SUBJECT] in [SETTING]. Masterful chiaroscuro lighting with deep shadows and golden highlights. Rich color palette of deep burgundy, warm gold, and dark umber tones. Contemplative and philosophical mood. Ancient or timeless setting elements. Oil on canvas texture with visible brushstrokes. Vertical composition optimized for 9:16 mobile format. Museum-quality fine art aesthetic. No modern elements, text, or logos.""",
        "placeholders": {
            "SCENE_DESCRIPTION": {
                "description": "Overall description of the scene",
                "example": "A philosopher contemplating in a candlelit study",
                "required": True
            },
            "MAIN_SUBJECT": {
                "description": "The primary figure or subject",
                "example": "an elderly bearded philosopher",
                "required": True
            },
            "SETTING": {
                "description": "The environment/location",
                "example": "a dimly lit ancient library with scrolls",
                "required": True
            }
        },
        "style_notes": [
            "Caravaggio chiaroscuro lighting",
            "Oil painting texture",
            "Deep shadows with golden highlights",
            "Rich classical color palette",
            "Contemplative, philosophical mood"
        ],
        "best_for": ["Narrative stories", "Single philosopher focus", "Quote visualizations"],
        "model_hints": {
            "midjourney": "--ar 9:16 --v 6",
            "dall-e": "Use HD quality",
            "stable_diffusion": "Add 'oil painting' to positive prompt"
        }
    },
    "stoic_marble": {
        "id": "stoic_marble",
        "name": "Stoic Marble Aesthetic",
        "description": "Clean marble statues on dark backgrounds. Minimalist but powerful. Perfect for stoic quotes and philosophical concepts.",
        "category": "minimalist",
        "preview_image": None,
        "created_at": "2026-01-10T00:00:00",
        "is_builtin": True,
        "base_prompt": """A stunning white marble statue of [FIGURE_DESCRIPTION] against a deep black background. The statue captures [EMOTIONAL_QUALITY] with masterful sculptural detail. Dramatic side lighting creates strong shadows and highlights the marble's texture. [OPTIONAL_ELEMENTS]. Style of ancient Greek and Roman sculpture. Photorealistic marble texture with subtle veins. The composition is powerful and contemplative. Museum-quality presentation. Ultra high detail, 8K resolution. Vertical 9:16 format. No text, no modern elements.""",
        "placeholders": {
            "FIGURE_DESCRIPTION": {
                "description": "Description of the marble figure",
                "example": "Marcus Aurelius in imperial robes, one hand raised thoughtfully",
                "required": True
            },
            "EMOTIONAL_QUALITY": {
                "description": "The emotional/philosophical quality to convey",
                "example": "stoic resolve and inner peace",
                "required": True
            },
            "OPTIONAL_ELEMENTS": {
                "description": "Additional sculptural elements (can be empty)",
                "example": "A Roman eagle perches nearby",
                "required": False
            }
        },
        "style_notes": [
            "Pure white marble against black",
            "Dramatic side lighting",
            "Greek/Roman sculptural style",
            "Minimalist, powerful composition",
            "Museum-quality presentation"
        ],
        "best_for": ["Stoic quotes", "Single philosopher portraits", "Minimalist aesthetic"],
        "model_hints": {
            "midjourney": "--ar 9:16 --v 6 --style raw",
            "dall-e": "Emphasize the black background contrast",
            "stable_diffusion": "Use ControlNet for pose consistency"
        }
    },
    "cosmic_wisdom": {
        "id": "cosmic_wisdom",
        "name": "Cosmic Wisdom",
        "description": "Philosophers against cosmic/nebula backgrounds. Blends ancient wisdom with the vastness of the universe.",
        "category": "surreal",
        "preview_image": None,
        "created_at": "2026-01-10T00:00:00",
        "is_builtin": True,
        "base_prompt": """A surreal cosmic artwork featuring [FIGURE_DESCRIPTION] set against a breathtaking nebula background. The figure appears [POSE_DESCRIPTION], connecting ancient wisdom with the infinity of space. Swirling galaxies, stars, and cosmic dust in deep purple, blue, and gold hues surround the scene. [SYMBOLIC_ELEMENTS]. The composition blends classical art with cosmic imagery. Ethereal lighting emanates from the cosmos. Sense of infinite wisdom and universal truth. Hyper-detailed, 8K resolution. Vertical 9:16 aspect ratio. No text.""",
        "placeholders": {
            "FIGURE_DESCRIPTION": {
                "description": "Description of the wise figure",
                "example": "an ancient philosopher in flowing robes",
                "required": True
            },
            "POSE_DESCRIPTION": {
                "description": "How the figure is positioned/interacting",
                "example": "meditating with arms outstretched toward the stars",
                "required": True
            },
            "SYMBOLIC_ELEMENTS": {
                "description": "Symbolic objects or elements in the scene",
                "example": "Sacred geometry patterns float around them",
                "required": False
            }
        },
        "style_notes": [
            "Nebula/cosmic backgrounds",
            "Deep purple, blue, gold palette",
            "Blend of classical and cosmic",
            "Ethereal, otherworldly lighting",
            "Sense of infinite wisdom"
        ],
        "best_for": ["Existential philosophy", "Eastern philosophy", "Universal truths"],
        "model_hints": {
            "midjourney": "--ar 9:16 --v 6",
            "dall-e": "Emphasize cosmic imagery",
            "stable_diffusion": "Blend nebula and portrait styles"
        }
    },
    "dark_academia": {
        "id": "dark_academia",
        "name": "Dark Academia",
        "description": "Moody library/study aesthetic with books, candles, and intellectual atmosphere. Modern dark academia trend.",
        "category": "aesthetic",
        "preview_image": None,
        "created_at": "2026-01-10T00:00:00",
        "is_builtin": True,
        "base_prompt": """A dark academia aesthetic scene in a moody ancient library. [SCENE_DESCRIPTION]. Towering bookshelves filled with leather-bound volumes. Warm candlelight flickers, casting dancing shadows. [SUBJECT_DESCRIPTION]. Rich mahogany wood and worn leather textures. Scattered papers with handwritten notes. An antique globe and brass instruments on an oak desk. Dust motes float in beams of warm light. Atmospheric and contemplative. Color palette of deep browns, burgundy, forest green, and aged gold. Vertical 9:16 composition. No modern elements. Cinematic photography style.""",
        "placeholders": {
            "SCENE_DESCRIPTION": {
                "description": "Overall scene/moment being captured",
                "example": "Late night study session in an Oxford-style library",
                "required": True
            },
            "SUBJECT_DESCRIPTION": {
                "description": "The main subject/figure in the scene",
                "example": "A scholar hunched over ancient texts, quill in hand",
                "required": True
            }
        },
        "style_notes": [
            "Moody library aesthetic",
            "Warm candlelight",
            "Leather and wood textures",
            "Scattered books and papers",
            "Dark academia color palette"
        ],
        "best_for": ["Book quotes", "Literary philosophy", "Modern aesthetic appeal"],
        "model_hints": {
            "midjourney": "--ar 9:16 --v 6",
            "dall-e": "Focus on atmospheric lighting",
            "stable_diffusion": "Add 'cinematic' to positive prompt"
        }
    }
}


class VisualTemplateManager:
    """Manages visual templates for image generation"""
    
    def __init__(self, templates_dir: str = TEMPLATES_DIR):
        self.templates_dir = templates_dir
        os.makedirs(templates_dir, exist_ok=True)
        
        # Load custom templates
        self.custom_templates = self._load_custom_templates()
        
        # Merge with builtin templates
        self.all_templates = {**BUILTIN_TEMPLATES, **self.custom_templates}
    
    def _load_custom_templates(self) -> Dict:
        """Load custom templates from disk"""
        templates = {}
        templates_file = os.path.join(self.templates_dir, "custom_templates.json")
        
        if os.path.exists(templates_file):
            try:
                with open(templates_file, 'r') as f:
                    templates = json.load(f)
            except Exception as e:
                print(f"Error loading custom templates: {e}")
        
        return templates
    
    def _save_custom_templates(self):
        """Save custom templates to disk"""
        templates_file = os.path.join(self.templates_dir, "custom_templates.json")
        try:
            with open(templates_file, 'w') as f:
                json.dump(self.custom_templates, f, indent=2)
        except Exception as e:
            print(f"Error saving custom templates: {e}")
    
    def get_all_templates(self) -> Dict:
        """Get all templates (builtin + custom)"""
        return self.all_templates
    
    def get_template(self, template_id: str) -> Optional[Dict]:
        """Get a specific template by ID"""
        return self.all_templates.get(template_id)
    
    def get_templates_by_category(self, category: str) -> List[Dict]:
        """Get all templates in a category"""
        return [t for t in self.all_templates.values() if t.get('category') == category]
    
    def get_categories(self) -> List[str]:
        """Get list of all categories"""
        categories = set()
        for template in self.all_templates.values():
            if 'category' in template:
                categories.add(template['category'])
        return sorted(list(categories))
    
    def create_template(self, 
                       name: str,
                       description: str,
                       base_prompt: str,
                       placeholders: Dict,
                       category: str = "custom",
                       style_notes: List[str] = None,
                       best_for: List[str] = None,
                       model_hints: Dict = None) -> Dict:
        """Create a new custom template"""
        
        # Generate ID from name
        template_id = name.lower().replace(' ', '_').replace('-', '_')
        template_id = ''.join(c for c in template_id if c.isalnum() or c == '_')
        
        # Ensure unique ID
        base_id = template_id
        counter = 1
        while template_id in self.all_templates:
            template_id = f"{base_id}_{counter}"
            counter += 1
        
        template = {
            "id": template_id,
            "name": name,
            "description": description,
            "category": category,
            "preview_image": None,
            "created_at": datetime.now().isoformat(),
            "is_builtin": False,
            "base_prompt": base_prompt,
            "placeholders": placeholders,
            "style_notes": style_notes or [],
            "best_for": best_for or [],
            "model_hints": model_hints or {}
        }
        
        self.custom_templates[template_id] = template
        self.all_templates[template_id] = template
        self._save_custom_templates()
        
        return template
    
    def update_template(self, template_id: str, updates: Dict) -> Optional[Dict]:
        """Update an existing custom template"""
        if template_id not in self.custom_templates:
            if template_id in BUILTIN_TEMPLATES:
                print("Cannot modify builtin templates. Create a copy instead.")
            return None
        
        template = self.custom_templates[template_id]
        template.update(updates)
        template['updated_at'] = datetime.now().isoformat()
        
        self.all_templates[template_id] = template
        self._save_custom_templates()
        
        return template
    
    def delete_template(self, template_id: str) -> bool:
        """Delete a custom template"""
        if template_id in BUILTIN_TEMPLATES:
            print("Cannot delete builtin templates.")
            return False
        
        if template_id in self.custom_templates:
            del self.custom_templates[template_id]
            del self.all_templates[template_id]
            self._save_custom_templates()
            return True
        
        return False
    
    def duplicate_template(self, template_id: str, new_name: str = None) -> Optional[Dict]:
        """Create a copy of a template (useful for modifying builtins)"""
        original = self.get_template(template_id)
        if not original:
            return None
        
        new_name = new_name or f"{original['name']} (Copy)"
        
        return self.create_template(
            name=new_name,
            description=original.get('description', ''),
            base_prompt=original.get('base_prompt', ''),
            placeholders=original.get('placeholders', {}),
            category=original.get('category', 'custom'),
            style_notes=original.get('style_notes', []),
            best_for=original.get('best_for', []),
            model_hints=original.get('model_hints', {})
        )
    
    def apply_template(self, template_id: str, replacements: Dict[str, str]) -> str:
        """
        Apply a template with specific replacements.
        
        Args:
            template_id: The template to apply
            replacements: Dict mapping placeholder names to values
                         e.g., {"TITLE_TEXT": "THEY INVENTED THE FUTURE", ...}
        
        Returns:
            The final prompt with all placeholders replaced
        """
        template = self.get_template(template_id)
        if not template:
            return ""
        
        prompt = template['base_prompt']
        
        # Replace all placeholders
        for placeholder, value in replacements.items():
            prompt = prompt.replace(f"[{placeholder}]", value)
        
        # Remove any unreplaced optional placeholders (replace with empty)
        for ph_name, ph_info in template.get('placeholders', {}).items():
            if not ph_info.get('required', True):
                prompt = prompt.replace(f"[{ph_name}]", "")
        
        return prompt
    
    def generate_prompt_for_scene(self, 
                                   template_id: str,
                                   scene_data: Dict,
                                   story_data: Dict = None) -> str:
        """
        Intelligently generate a prompt for a scene using a template.
        
        Automatically maps scene data to template placeholders.
        """
        template = self.get_template(template_id)
        if not template:
            return ""
        
        replacements = {}
        placeholders = template.get('placeholders', {})
        
        # Smart mapping based on common placeholder patterns
        for ph_name, ph_info in placeholders.items():
            value = None
            
            # Try to find matching data
            if 'TITLE' in ph_name.upper():
                value = story_data.get('title', '') if story_data else ''
            elif 'SCENE' in ph_name.upper() or 'DESCRIPTION' in ph_name.upper():
                value = scene_data.get('visual_description', scene_data.get('key_concept', ''))
            elif 'FIGURE' in ph_name.upper() or 'SUBJECT' in ph_name.upper():
                value = scene_data.get('person_name', scene_data.get('key_concept', ''))
            elif 'SETTING' in ph_name.upper():
                value = scene_data.get('visual_description', 'an ancient philosophical setting')
            elif 'EMOTIONAL' in ph_name.upper() or 'MOOD' in ph_name.upper():
                value = 'contemplative wisdom and philosophical depth'
            elif 'POSE' in ph_name.upper():
                value = 'in a thoughtful, contemplative pose'
            elif 'SYMBOLIC' in ph_name.upper() or 'OPTIONAL' in ph_name.upper():
                value = ''  # Optional elements
            
            # Use example as fallback for required placeholders
            if not value and ph_info.get('required', True):
                value = ph_info.get('example', f'[{ph_name}]')
            
            if value is not None:
                replacements[ph_name] = value
        
        return self.apply_template(template_id, replacements)
    
    def get_template_preview_prompt(self, template_id: str) -> str:
        """Generate a preview prompt using example values"""
        template = self.get_template(template_id)
        if not template:
            return ""
        
        replacements = {}
        for ph_name, ph_info in template.get('placeholders', {}).items():
            replacements[ph_name] = ph_info.get('example', f'[{ph_name}]')
        
        return self.apply_template(template_id, replacements)


def parse_template_from_description(description: str) -> Dict:
    """
    Helper function to parse a template from a natural language description.
    Useful for creating templates from user input.
    """
    # Extract placeholders (text in square brackets)
    import re
    placeholders = {}
    
    placeholder_pattern = r'\[([A-Z0-9_]+)\]'
    found_placeholders = re.findall(placeholder_pattern, description)
    
    for ph in set(found_placeholders):
        placeholders[ph] = {
            "description": f"Replace with {ph.lower().replace('_', ' ')}",
            "example": f"Example {ph.lower().replace('_', ' ')}",
            "required": True
        }
    
    return {
        "base_prompt": description,
        "placeholders": placeholders
    }


# Example usage and testing
if __name__ == "__main__":
    manager = VisualTemplateManager()
    
    print("=== Available Templates ===")
    for template_id, template in manager.get_all_templates().items():
        print(f"\n📋 {template['name']} ({template_id})")
        print(f"   Category: {template.get('category', 'N/A')}")
        print(f"   Best for: {', '.join(template.get('best_for', []))}")
        print(f"   Placeholders: {list(template.get('placeholders', {}).keys())}")
    
    print("\n=== Example: Apply Ancient Chamber Template ===")
    prompt = manager.apply_template("ancient_chamber_glitch", {
        "TITLE_TEXT": "THEY INVENTED THE FUTURE",
        "FIGURE1_DESCRIPTION": "Thomas Edison with intense gaze",
        "FIGURE2_DESCRIPTION": "Nikola Tesla figure crackling with energy",
        "FIGURE3_DESCRIPTION": "Leonardo da Vinci sketching",
        "FIGURE4_DESCRIPTION": "Ada Lovelace in Victorian attire"
    })
    print(f"\nGenerated Prompt:\n{prompt[:500]}...")
    
    print("\n=== Categories ===")
    print(manager.get_categories())
