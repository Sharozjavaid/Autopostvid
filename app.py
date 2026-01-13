import streamlit as st
import json
import os
from gemini_handler import GeminiHandler
from smart_image_generator import SmartImageGenerator
from PIL import Image

from voice_generator import VoiceGenerator
from video_assembler import VideoAssembler
from tiktok_uploader import TikTokUploader
from visual_templates import VisualTemplateManager, parse_template_from_description

# OpenAI image generation (optional)
try:
    from openai_image_generator import OpenAIImageGenerator, check_openai_available
    OPENAI_AVAILABLE = check_openai_available()
except ImportError:
    OPENAI_AVAILABLE = False

# GPT Image 1.5 via fal.ai (recommended for bold text overlays)
try:
    from gpt_image_generator import GPTImageGenerator, check_gpt_image_available
    GPT15_AVAILABLE = check_gpt_image_available()
except ImportError:
    GPT15_AVAILABLE = False

# Slideshow generator (uses GPT Image 1.5 via fal.ai for text-heavy slides)
try:
    from slideshow_generator import SlideshowGenerator, check_slideshow_available
    SLIDESHOW_AVAILABLE = check_slideshow_available()  # Requires FAL_KEY
except ImportError:
    SLIDESHOW_AVAILABLE = False

# TikTok Slideshow Generator (new approach: AI background + programmatic text overlay)
try:
    from tiktok_slideshow import TikTokSlideshow
    from text_overlay import TextOverlay
    TIKTOK_SLIDESHOW_AVAILABLE = True
except ImportError:
    TIKTOK_SLIDESHOW_AVAILABLE = False

# fal.ai video generator (optional)
try:
    from fal_video_generator import FalVideoGenerator, check_fal_available
    FAL_AVAILABLE = check_fal_available()
except ImportError:
    FAL_AVAILABLE = False

# Timing calculator for audio-sync pipeline
try:
    from timing_calculator import (
        calculate_scene_durations,
        validate_pipeline_timing,
        print_timing_report,
        validate_and_log
    )
    TIMING_AVAILABLE = True
except ImportError:
    TIMING_AVAILABLE = False

# Automation manager for dashboard
try:
    from automation_manager import (
        AutomationManager,
        AutomationStatus,
        IMAGE_MODELS,
        TRANSITIONS,
        SCHEDULE_MODES,
        TOPIC_TYPES,
        TOPIC_FILES,
        FONT_STYLES,
        get_pending_topics_count,
        get_completed_topics_count,
        get_recent_completed_topics,
        get_recent_logs,
        get_topics_from_file,
        add_topics_to_file,
        get_topics_count_by_source,
        recycle_topic,
        recycle_all_completed_topics,
        get_all_topic_stats,
        get_topic_file_path
    )
    AUTOMATION_MANAGER_AVAILABLE = True
except ImportError:
    AUTOMATION_MANAGER_AVAILABLE = False

import glob

# Ensure directories exist
os.makedirs("generated_scripts", exist_ok=True)
os.makedirs("generated_images", exist_ok=True)
os.makedirs("generated_slideshows", exist_ok=True)
os.makedirs("generated_videos", exist_ok=True)
os.makedirs("generated_videos/clips", exist_ok=True)
os.makedirs("generated_audio", exist_ok=True)
os.makedirs("visual_templates", exist_ok=True)

# Helper functions for persistence
def save_story(story_data):
    title = story_data.get('title', 'Unknown Story')
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
    filename = f"generated_scripts/{safe_title}.json"
    with open(filename, "w") as f:
        json.dump(story_data, f, indent=4)
    return filename

def load_images_for_story(story_data):
    """Scan generated_images for files matching this story"""
    title = story_data.get('title', '')
    safe_title = title.replace(' ', '_')
    found_images = {}
    
    print(f"DEBUG: Looking for images with safe_title: '{safe_title}'")
    
    # Check for gpt15, nano, enhanced, and openai images
    # Pattern: {title}_scene_{num}_{type}.png
    # Priority: gpt15 > nano > openai > enhanced
    for scene in story_data.get('scenes', []):
        scene_num = scene.get('scene_number')
        
        # Look for existing files (in priority order)
        gpt15_path = f"generated_images/{safe_title}_scene_{scene_num}_gpt15.png"
        nano_path = f"generated_images/{safe_title}_scene_{scene_num}_nano.png"
        openai_path = f"generated_images/{safe_title}_scene_{scene_num}_openai.png"
        enhanced_path = f"generated_images/{safe_title}_scene_{scene_num}_enhanced.png"
        
        print(f"DEBUG: Checking {gpt15_path}")
        
        if os.path.exists(gpt15_path):
            found_images[f"image_{scene_num}"] = gpt15_path
            print(f"DEBUG: Found {gpt15_path}")
        elif os.path.exists(nano_path):
            found_images[f"image_{scene_num}"] = nano_path
            print(f"DEBUG: Found {nano_path}")
        elif os.path.exists(openai_path):
            found_images[f"image_{scene_num}"] = openai_path
            print(f"DEBUG: Found {openai_path}")
        elif os.path.exists(enhanced_path):
            found_images[f"image_{scene_num}"] = enhanced_path
            print(f"DEBUG: Found {enhanced_path}")
            
    return found_images

def load_transition_clips_for_story(story_data):
    """Scan generated_videos/clips for transition clips matching this story"""
    title = story_data.get('title', '')
    safe_title = title.replace(' ', '_')
    found_clips = []
    
    print(f"DEBUG: Looking for transition clips with safe_title: '{safe_title}'")
    
    # Pattern: {title}_transition_{num}.mp4
    clips_dir = "generated_videos/clips"
    if not os.path.exists(clips_dir):
        return []
    
    # Find all matching clips and sort by transition number
    import re
    for filename in os.listdir(clips_dir):
        if filename.startswith(safe_title) and "_transition_" in filename and filename.endswith(".mp4"):
            clip_path = os.path.join(clips_dir, filename)
            # Extract transition number
            match = re.search(r'_transition_(\d+)\.mp4$', filename)
            if match:
                transition_num = int(match.group(1))
                found_clips.append((transition_num, clip_path))
                print(f"DEBUG: Found clip {clip_path}")
    
    # Sort by transition number and return just the paths
    found_clips.sort(key=lambda x: x[0])
    return [clip[1] for clip in found_clips]

def load_audio_for_story(story_data):
    """Scan generated_audio for audio files matching this story"""
    title = story_data.get('title', '')
    safe_title = title.replace(' ', '_')
    found_audio = []
    
    print(f"DEBUG: Looking for audio with safe_title: '{safe_title}'")
    
    audio_dir = "generated_audio"
    if not os.path.exists(audio_dir):
        return []
    
    # Find all matching audio files
    for filename in os.listdir(audio_dir):
        if filename.startswith(safe_title) and filename.endswith(".mp3"):
            audio_path = os.path.join(audio_dir, filename)
            found_audio.append(audio_path)
            print(f"DEBUG: Found audio {audio_path}")
    
    # Sort by filename (most recent naming convention last)
    found_audio.sort()
    return found_audio

# Initialize generators
if 'gemini_handler' not in st.session_state:
    st.session_state.gemini_handler = GeminiHandler()
if 'image_generator' not in st.session_state:
    st.session_state.image_generator = SmartImageGenerator()
if 'voice_generator' not in st.session_state:
    st.session_state.voice_generator = VoiceGenerator()
if 'video_assembler' not in st.session_state:
    st.session_state.video_assembler = VideoAssembler()
if 'tiktok_uploader' not in st.session_state:
    st.session_state.tiktok_uploader = TikTokUploader()
else:
    # Hot-fix: Reload if keys were missing (e.g. before .env update)
    if not st.session_state.tiktok_uploader.client_key:
        st.session_state.tiktok_uploader = TikTokUploader()

if 'template_manager' not in st.session_state:
    st.session_state.template_manager = VisualTemplateManager()

st.set_page_config(layout="wide", page_title="Philosophy Video Generator")

# ==================== AUTHENTICATION ====================
# Credentials (in production, use environment variables or secrets management)
VALID_USERNAME = "sharoz75"
VALID_PASSWORD = "1028"

def check_credentials(username: str, password: str) -> bool:
    """Validate login credentials."""
    return username == VALID_USERNAME and password == VALID_PASSWORD

def show_login_page():
    """Display the login form."""
    st.title("🔐 Philosophy Video Generator")
    st.markdown("### Please log in to continue")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login", use_container_width=True)
        
        if submit:
            if check_credentials(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("❌ Invalid username or password")

# Check authentication
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    show_login_page()
    st.stop()

# ==================== MAIN APP (only shown when authenticated) ====================

st.title("Philosophy Video Generator")

# Sidebar for configuration and loading
with st.sidebar:
    # User info and logout
    st.markdown(f"👤 Logged in as: **{st.session_state.get('username', 'User')}**")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.pop('username', None)
        st.rerun()
    st.markdown("---")
    
    st.header("Configuration")
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("GOOGLE_API_KEY not found. Please check .env file.")
    
    eleven_key = os.getenv("ELEVENLABS_API_KEY")
    if not eleven_key:
        st.warning("ELEVENLABS_API_KEY not found. Audio generation will fail.")
    else:
        st.success("API Keys detected.")
        
    st.markdown("---")
    st.header("TikTok Integration")
    
    # Check if we have an access token
    if 'tiktok_access_token' in st.session_state:
        st.success("✅ Connected to TikTok")
        if st.button("Disconnect TikTok"):
            del st.session_state.tiktok_access_token
            st.rerun()
    else:
        st.warning("Not connected to TikTok")
        
        # PKCE Flow: Generate if not already in session
        if 'tiktok_code_verifier' not in st.session_state:
            verifier, challenge = st.session_state.tiktok_uploader.generate_pkce_pair()
            st.session_state.tiktok_code_verifier = verifier
            st.session_state.tiktok_code_challenge = challenge
        
        # Use existing challenge to keep URL consistent
        auth_url = st.session_state.tiktok_uploader.get_auth_url(st.session_state.tiktok_code_challenge)
        st.markdown(f"[🔗 Connect TikTok Account]({auth_url})")
        
        auth_code = st.text_input("Paste Auth Code here:")
        if st.button("Authorize TikTok"):
            if auth_code:
                try:
                    # Handle URL-encoded pastes just in case
                    import urllib.parse
                    clean_code = urllib.parse.unquote(auth_code.strip())
                    
                    token_data = st.session_state.tiktok_uploader.get_access_token(
                        clean_code, 
                        st.session_state.tiktok_code_verifier
                    )
                    
                    # Debug: Print full response to see structure
                    print(f"DEBUG: Token Response: {token_data}")
                    
                    # Handle nested data structure (TikTok API V2 often wraps in 'data')
                    if 'data' in token_data:
                        access_token = token_data['data'].get('access_token')
                    else:
                        access_token = token_data.get('access_token')
                        
                    if not access_token:
                        st.error("Could not find access_token in response. Check terminal logs.")
                    else:
                        st.session_state.tiktok_access_token = access_token
                        st.success("Successfully connected!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Auth failed: {e}")
            else:
                st.error("Please enter the code from the URL.")

    st.markdown("---")

    st.header("💾 Load Saved Story")
    saved_files = glob.glob("generated_scripts/*.json")
    if saved_files:
        selected_file = st.selectbox("Select a story:", saved_files, format_func=lambda x: os.path.basename(x))
        if st.button("Load Story"):
            try:
                print(f"DEBUG: Loading file {selected_file}")
                with open(selected_file, 'r') as f:
                    content = f.read()
                    print(f"DEBUG: File content length: {len(content)}")
                    try:
                        loaded_data = json.loads(content)
                        st.session_state.story_data = loaded_data
                        print("DEBUG: JSON parsed successfully")
                    except json.JSONDecodeError as e:
                        print(f"DEBUG: JSON Parse Error: {e}")
                        st.error(f"JSON Parse Error: {e}")
                        # (omitted simple retry logic for brevity during debug)
                            
                if 'story_data' in st.session_state:
                    st.session_state.scenes = st.session_state.story_data.get('scenes', [])
                    print(f"DEBUG: Scenes loaded: {len(st.session_state.scenes)}")
                        
                    # Load images
                    found_imgs = load_images_for_story(st.session_state.story_data)
                    st.session_state.update(found_imgs)
                    print(f"DEBUG: Images found: {found_imgs.keys()}")
                    
                    # Load transition clips for Tab 5 (Video from Images)
                    found_clips = load_transition_clips_for_story(st.session_state.story_data)
                    if found_clips:
                        st.session_state.fal_video_paths = found_clips
                        print(f"DEBUG: Transition clips found: {len(found_clips)}")
                    
                    # Load audio files for this story
                    found_audio = load_audio_for_story(st.session_state.story_data)
                    if found_audio:
                        st.session_state.story_audio_files = found_audio
                        # Set the most recent as current
                        st.session_state.fal_audio_path = found_audio[-1]
                        print(f"DEBUG: Audio files found: {len(found_audio)}")
                    
                    st.success(f"Loaded {os.path.basename(selected_file)}!")
                    load_info = []
                    if found_clips:
                        load_info.append(f"📹 {len(found_clips)} transition clips")
                    if found_audio:
                        load_info.append(f"🎙️ {len(found_audio)} audio files")
                    if load_info:
                        st.info(f"Also loaded: {', '.join(load_info)}")
                    # Force rerun to update UI immediately
                    st.rerun()
            except Exception as e:
                print(f"DEBUG: General Error: {e}")
                st.error(f"Error loading file: {e}")

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs(["1. Story Generation", "2. Image Generation", "3. Audio & Video", "4. Slideshows", "5. Video from Images", "6. Automation Dashboard", "7. Visual Templates", "8. TikTok Slideshow", "9. 📊 History"])

# --- Tab 1: Story Generation ---
with tab1:
    st.header("Generate or View Script")
    topic = st.text_input("Enter a philosophy topic (e.g., 'Stoicism', 'The Absurd'):", "Plato's Cave Allegory")
    
    col_gen, col_save = st.columns([1,4])
    with col_gen:
        if st.button("Generate New Story"):
            with st.spinner("Generating script and scenes..."):
                story_data = st.session_state.gemini_handler.generate_philosophy_story(topic)
                if story_data:
                    # Add title if missing
                    if 'title' not in story_data:
                        story_data['title'] = topic
                        
                    st.session_state.story_data = story_data
                    st.session_state.scenes = story_data.get('scenes', [])
                    
                    # Auto-save
                    saved_path = save_story(story_data)
                    st.success(f"Story generated and saved to {saved_path}!")
                else:
                    st.error("Failed to generate story.")


    if 'story_data' in st.session_state:
        story_data = st.session_state.story_data
        content_type = story_data.get('content_type', 'story')
        
        # Display title and content type badge
        col_title, col_badge = st.columns([3, 1])
        with col_title:
            st.subheader(f"Title: {story_data.get('title', topic)}")
        with col_badge:
            if content_type == 'list':
                st.markdown("🎯 **LIST/SLIDESHOW**")
            else:
                st.markdown("📖 **NARRATIVE STORY**")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Script")
            st.text_area("Script Content", story_data.get('script', ''), height=400)
            
            # Show list items if present (for list-style content)
            if 'list_items' in story_data and story_data['list_items']:
                st.markdown("### 📋 List Items")
                for item in story_data['list_items']:
                    with st.expander(f"{item.get('number', '?')}. {item.get('name', 'Unknown')}"):
                        st.markdown(f"**Quote/Idea:** _{item.get('quote_or_idea', 'N/A')}_")
                        st.markdown(f"**Why it matters:** {item.get('explanation', 'N/A')}")
            
        with col2:
            st.markdown("### Scenes")
            scenes = st.session_state.scenes
            st.json(scenes)


# --- Tab 2: Image Generation ---
with tab2:
    st.header("Interactive Image Generation")
    
    if 'scenes' not in st.session_state or not st.session_state.scenes:
        st.warning("Please generate a story in Tab 1 first.")
    else:
        # Template Selection Section
        st.subheader("🎨 Visual Template")
        
        all_templates = st.session_state.template_manager.get_all_templates()
        template_options = ["None (Use Custom Style)"] + [f"{t['name']}" for t in all_templates.values()]
        template_ids = [None] + list(all_templates.keys())
        
        # Pre-select if a template was chosen in Tab 7
        default_idx = 0
        if 'selected_template_id' in st.session_state and st.session_state.selected_template_id in template_ids:
            default_idx = template_ids.index(st.session_state.selected_template_id)
        
        col_template, col_preview = st.columns([2, 1])
        with col_template:
            selected_template_idx = st.selectbox(
                "Select Visual Template:",
                range(len(template_options)),
                format_func=lambda x: template_options[x],
                index=default_idx,
                key="image_gen_template_select"
            )
            selected_template_id = template_ids[selected_template_idx]
        
        with col_preview:
            if selected_template_id:
                template = all_templates.get(selected_template_id)
                if template:
                    st.caption(f"**{template.get('category', 'N/A')}**")
                    st.caption(template.get('description', '')[:100] + "...")
        
        # Show template details if selected
        if selected_template_id:
            template = all_templates.get(selected_template_id)
            if template:
                with st.expander("📋 Template Details & Placeholders", expanded=False):
                    st.markdown(f"**Template:** {template['name']}")
                    st.markdown(f"**Best for:** {', '.join(template.get('best_for', []))}")
                    
                    # Show placeholders that need to be filled
                    st.markdown("**Placeholders:**")
                    for ph_name, ph_info in template.get('placeholders', {}).items():
                        required = "🔴" if ph_info.get('required', True) else "⚪"
                        st.markdown(f"{required} `[{ph_name}]`: {ph_info.get('description', '')} (e.g., _{ph_info.get('example', 'N/A')}_)")
                    
                    # Preview prompt with examples
                    if st.button("👁️ Show Preview Prompt", key="preview_template_tab2"):
                        preview = st.session_state.template_manager.get_template_preview_prompt(selected_template_id)
                        st.code(preview, language="text")
                
                # When template is selected, update session state
                st.session_state.selected_template_id = selected_template_id
                use_template_mode = True
            else:
                use_template_mode = False
        else:
            use_template_mode = False
        
        st.markdown("---")
        
        # Style controls (shown when NOT using a template)
        if not use_template_mode:
            st.subheader("Global Style Settings")
            global_style = st.text_area("Base Style Prompt (applied to all)", 
                                      "Classical Old Master painting style, Caravaggio and Rembrandt influences, dramatic chiaroscuro lighting, deep shadows, golden highlights, oil on canvas texture, realistic human figures, 8k resolution")
        else:
            global_style = ""  # Template provides the style
            st.info(f"🎨 Using template: **{template['name']}** - Template style will be applied to all images.")
        
        # Model Selection
        st.subheader("🤖 Image Generation Model")
        model_options = ["Nano (Gemini)"]
        
        # GPT Image 1.5 via fal.ai - RECOMMENDED for bold text overlays
        if GPT15_AVAILABLE:
            model_options.insert(0, "⭐ GPT Image 1.5 (fal.ai)")  # Put first as recommended
        else:
            st.info("💡 GPT Image 1.5 not configured. Add FAL_KEY to .env to enable (recommended for bold text overlays).")
        
        if OPENAI_AVAILABLE:
            model_options.extend(["OpenAI DALL-E 3", "OpenAI GPT-Image-1.5 (direct)"])
        
        selected_model = st.selectbox("Select Image Model:", model_options, 
                                      help="GPT Image 1.5 via fal.ai is recommended for consistent bold text overlays")
        
        # Initialize GPT Image 1.5 generator if selected
        if "GPT Image 1.5 (fal.ai)" in selected_model and GPT15_AVAILABLE:
            if 'gpt15_image_generator' not in st.session_state:
                try:
                    st.session_state.gpt15_image_generator = GPTImageGenerator(quality="low")
                    st.success("✅ GPT Image 1.5 (fal.ai) ready - with bold text overlays!")
                except Exception as e:
                    st.error(f"Failed to initialize GPT Image 1.5: {e}")
        
        # Initialize OpenAI generator if selected
        if "OpenAI" in selected_model and OPENAI_AVAILABLE:
            if 'openai_image_generator' not in st.session_state:
                try:
                    model_slug = "dall-e-3" if "DALL-E" in selected_model else "gpt-image-1.5"
                    st.session_state.openai_image_generator = OpenAIImageGenerator(model=model_slug)
                except Exception as e:
                    st.error(f"Failed to initialize OpenAI: {e}")
        
        # Batch Generation Buttons
        col_batch_gpt15, col_batch_nano, col_batch_openai = st.columns(3)
        
        # GPT Image 1.5 via fal.ai - RECOMMENDED
        with col_batch_gpt15:
            if GPT15_AVAILABLE:
                if st.button("⭐ Generate All (GPT 1.5)", help="Recommended - with bold text overlays"):
                    progress_bar_gpt = st.progress(0)
                    status_text_gpt = st.empty()
                    
                    total_scenes = len(st.session_state.scenes)
                    story_title = st.session_state.story_data.get('title', 'Story')
                    story_data = st.session_state.story_data
                    list_items = story_data.get('list_items', [])
                    
                    # Initialize generator
                    if 'gpt15_image_generator' not in st.session_state:
                        st.session_state.gpt15_image_generator = GPTImageGenerator(quality="low")
                    
                    gpt15_gen = st.session_state.gpt15_image_generator
                    
                    for idx, scene in enumerate(st.session_state.scenes):
                        idx_num = scene.get('scene_number', idx+1)
                        img_key = f"image_{idx_num}"
                        
                        status_text_gpt.text(f"GPT 1.5: Generating Scene {idx_num} of {total_scenes}...")
                        progress_bar_gpt.progress((idx) / total_scenes)
                        
                        # Skip if exists
                        if img_key in st.session_state and os.path.exists(st.session_state.get(img_key, '')):
                            continue
                        
                        # Enrich scene with person name from list_items
                        enriched_scene = {**scene}
                        list_item_num = scene.get('list_item', 0)
                        if list_item_num and list_items:
                            matching_item = next((item for item in list_items if item.get('number') == list_item_num), None)
                            if matching_item:
                                enriched_scene['person_name'] = matching_item.get('name', '')
                        
                        try:
                            image_path = gpt15_gen.generate_philosophy_image(
                                scene_data=enriched_scene,
                                story_title=story_title,
                                story_data=story_data
                            )
                            if image_path:
                                st.session_state[img_key] = image_path
                        except Exception as e:
                            print(f"GPT 1.5 error for scene {idx_num}: {e}")
                    
                    progress_bar_gpt.progress(1.0)
                    status_text_gpt.success("🎉 All images generated with GPT Image 1.5!")
                    st.rerun()
            else:
                st.button("⭐ Generate All (GPT 1.5)", disabled=True, help="Add FAL_KEY to enable")
        
        with col_batch_nano:
            if st.button("🚀 Generate All (Nano)"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                total_scenes = len(st.session_state.scenes)
                story_title = st.session_state.story_data.get('title', 'Story')
                
                for idx, scene in enumerate(st.session_state.scenes):
                    idx_num = scene.get('scene_number', idx+1)
                    img_key = f"image_{idx_num}"
                    
                    # Update status
                    status_text.text(f"Generating image for Scene {idx_num} of {total_scenes}...")
                    progress_bar.progress((idx) / total_scenes)
                    
                    # Check if image already exists to save time/cost
                    if img_key in st.session_state and os.path.exists(st.session_state[img_key]):
                        continue
                    
                    # Construct prompt - use template if selected
                    prompt_key = f"prompt_{idx_num}"
                    if prompt_key in st.session_state:
                        # Use stored/edited prompt
                        final_prompt = st.session_state[prompt_key]
                    elif use_template_mode and selected_template_id:
                        # Generate prompt from template
                        final_prompt = st.session_state.template_manager.generate_prompt_for_scene(
                            selected_template_id,
                            scene,
                            st.session_state.story_data
                        )
                    else:
                        # Use global style + scene description
                        scene_desc = scene.get('visual_description', '')
                        scene_concept = scene.get('key_concept', '')
                        final_prompt = f"{global_style}, {scene_desc}, {scene_concept}"
                    
                    # Generate
                    try:
                        image_path = st.session_state.image_generator.generate_image_with_nano(
                            prompt=final_prompt,
                            scene_number=idx_num, 
                            story_title=story_title,
                            prompt_override=final_prompt
                        )
                        st.session_state[img_key] = image_path
                    except Exception as e:
                        print(f"Error producing batch image for scene {idx_num}: {e}")
                
                progress_bar.progress(1.0)
                status_text.success("🎉 All images generated with Nano!")
                st.rerun()
        
        with col_batch_openai:
            if OPENAI_AVAILABLE:
                if st.button("🚀 Generate All (OpenAI)"):
                    progress_bar_oa = st.progress(0)
                    status_text_oa = st.empty()
                    
                    total_scenes = len(st.session_state.scenes)
                    story_title = st.session_state.story_data.get('title', 'Story')
                    
                    # Initialize OpenAI generator
                    try:
                        model_slug = "dall-e-3" if "DALL-E" in selected_model else "gpt-image-1.5"
                        openai_gen = OpenAIImageGenerator(model=model_slug)
                    except Exception as e:
                        st.error(f"OpenAI init failed: {e}")
                        openai_gen = None
                    
                    if openai_gen:
                        for idx, scene in enumerate(st.session_state.scenes):
                            idx_num = scene.get('scene_number', idx+1)
                            img_key = f"image_{idx_num}"
                            
                            status_text_oa.text(f"OpenAI: Generating Scene {idx_num} of {total_scenes}...")
                            progress_bar_oa.progress((idx) / total_scenes)
                            
                            # Skip if exists
                            if img_key in st.session_state and os.path.exists(st.session_state[img_key]):
                                continue
                            
                            # Construct prompt - use template if selected
                            prompt_key = f"prompt_{idx_num}"
                            if prompt_key in st.session_state:
                                final_prompt = st.session_state[prompt_key]
                            elif use_template_mode and selected_template_id:
                                # Generate prompt from template
                                final_prompt = st.session_state.template_manager.generate_prompt_for_scene(
                                    selected_template_id,
                                    scene,
                                    st.session_state.story_data
                                )
                            else:
                                scene_desc = scene.get('visual_description', '')
                                scene_concept = scene.get('key_concept', '')
                                final_prompt = f"{global_style}, {scene_desc}, {scene_concept}"
                            
                            try:
                                paths = openai_gen.generate_image(final_prompt, idx_num, story_title)
                                if paths:
                                    st.session_state[img_key] = paths[0]
                            except Exception as e:
                                print(f"OpenAI error for scene {idx_num}: {e}")
                        
                        progress_bar_oa.progress(1.0)
                        status_text_oa.success("🎉 All images generated with OpenAI!")
                        st.rerun()
            else:
                st.button("🚀 Generate All (OpenAI)", disabled=True, help="Add OPENAI_API_KEY to enable")

        # Iterate through scenes
        for i, scene in enumerate(st.session_state.scenes):
            scene_num = scene.get('scene_number', i+1)
            
            with st.expander(f"Scene {scene_num}: {scene.get('key_concept', 'Concept')}", expanded=(i==0)):
                col_text, col_img = st.columns([1, 1])
                
                with col_text:
                    st.markdown(f"**Visual Description:** {scene.get('visual_description', '')}")
                    st.markdown(f"**Script:** _{scene.get('text', '')}_")
                    
                    # Generate default prompt - from template if selected, else global style
                    if use_template_mode and selected_template_id:
                        default_prompt = st.session_state.template_manager.generate_prompt_for_scene(
                            selected_template_id,
                            scene,
                            st.session_state.story_data
                        )
                    else:
                        default_prompt = f"{global_style}, {scene.get('visual_description', '')}, {scene.get('key_concept', '')}"
                    
                    # Allow user to edit the FULL prompt for this scene
                    prompt_key = f"prompt_{scene_num}"
                    
                    # Show button to regenerate from template
                    if use_template_mode and selected_template_id:
                        if st.button(f"🔄 Reset to Template", key=f"reset_template_{scene_num}"):
                            st.session_state[prompt_key] = default_prompt
                            st.rerun()
                    
                    if prompt_key not in st.session_state:
                        st.session_state[prompt_key] = default_prompt
                        
                    user_prompt = st.text_area("Image Prompt", st.session_state[prompt_key], key=f"text_{scene_num}", height=150)
                    st.session_state[prompt_key] = user_prompt
                    
                    # Show slide_subject if available
                    slide_subject = scene.get('slide_subject', '')
                    if slide_subject:
                        st.markdown(f"**Bold Text Overlay:** `{slide_subject}`")
                    
                    # Generation buttons - GPT 1.5, Nano and OpenAI
                    btn_col0, btn_col1, btn_col2 = st.columns(3)
                    
                    with btn_col0:
                        if GPT15_AVAILABLE:
                            if st.button(f"⭐ GPT 1.5", key=f"btn_gpt15_{scene_num}", help="With bold text overlay"):
                                with st.spinner("Generating with GPT Image 1.5..."):
                                    story_title = st.session_state.story_data.get('title', 'Story')
                                    story_data = st.session_state.story_data
                                    list_items = story_data.get('list_items', [])
                                    
                                    # Initialize generator
                                    if 'gpt15_image_generator' not in st.session_state:
                                        st.session_state.gpt15_image_generator = GPTImageGenerator(quality="low")
                                    
                                    # Enrich scene with person name
                                    enriched_scene = {**scene}
                                    list_item_num = scene.get('list_item', 0)
                                    if list_item_num and list_items:
                                        matching_item = next((item for item in list_items if item.get('number') == list_item_num), None)
                                        if matching_item:
                                            enriched_scene['person_name'] = matching_item.get('name', '')
                                    
                                    try:
                                        image_path = st.session_state.gpt15_image_generator.generate_philosophy_image(
                                            scene_data=enriched_scene,
                                            story_title=story_title,
                                            story_data=story_data
                                        )
                                        
                                        if image_path:
                                            img_key = f"image_{scene_num}"
                                            st.session_state[img_key] = image_path
                                            st.success("GPT 1.5 image generated!")
                                        else:
                                            st.error("GPT 1.5 generation failed.")
                                    except Exception as e:
                                        st.error(f"GPT 1.5 error: {e}")
                        else:
                            st.button(f"⭐ GPT 1.5", key=f"btn_gpt15_{scene_num}", disabled=True, help="Add FAL_KEY to enable")
                    
                    with btn_col1:
                        if st.button(f"🎨 Nano", key=f"btn_nano_{scene_num}"):
                            with st.spinner("Generating with Nano..."):
                                story_title = st.session_state.story_data.get('title', 'Story')
                                image_path = st.session_state.image_generator.generate_image_with_nano(
                                    prompt=user_prompt,
                                    scene_number=scene_num, 
                                    story_title=story_title,
                                    prompt_override=user_prompt
                                )
                                
                                img_key = f"image_{scene_num}"
                                st.session_state[img_key] = image_path
                                
                                if "enhanced" in image_path:
                                    st.warning("⚠️ Fell back to placeholder.")
                                else:
                                    st.success("Nano image generated!")
                    
                    with btn_col2:
                        if OPENAI_AVAILABLE:
                            if st.button(f"🤖 OpenAI", key=f"btn_openai_{scene_num}"):
                                with st.spinner("Generating with OpenAI..."):
                                    try:
                                        story_title = st.session_state.story_data.get('title', 'Story')
                                        model_slug = "dall-e-3" if "DALL-E" in selected_model else "gpt-image-1.5"
                                        openai_gen = OpenAIImageGenerator(model=model_slug)
                                        paths = openai_gen.generate_image(user_prompt, scene_num, story_title)
                                        
                                        if paths:
                                            img_key = f"image_{scene_num}"
                                            st.session_state[img_key] = paths[0]
                                            st.success("OpenAI image generated!")
                                        else:
                                            st.error("OpenAI generation failed.")
                                    except Exception as e:
                                        st.error(f"OpenAI error: {e}")
                        else:
                            st.button(f"🤖 OpenAI", key=f"btn_openai_{scene_num}", disabled=True)

                with col_img:
                    img_key = f"image_{scene_num}"
                    if img_key in st.session_state:
                        image_path = st.session_state[img_key]
                        if os.path.exists(image_path):
                            st.image(image_path, caption=f"Scene {scene_num}")
                            st.text(f"Path: {image_path}")
                        else:
                            st.error(f"Image file not found: {image_path}")
                    else:
                        st.info("No image generated yet.")



# --- Tab 3: Audio & Video ---
with tab3:
    st.header("Audio & Final Video Assembly")
    
    if 'story_data' not in st.session_state:
        st.warning("Please generate a story in Tab 1 first.")
    else:
        st.subheader("1. Voice Selection")
        
        # Get available voices
        voices = st.session_state.voice_generator.get_available_voices()
        voice_options = {v['name']: v['id'] for v in voices}
        
        selected_voice_name = st.selectbox("Choose a narrator:", list(voice_options.keys()))
        selected_voice_id = voice_options[selected_voice_name]
        
        # Audio Generation
        st.subheader("2. Generate Audio")
        if st.button("Generate Narration Audio"):
            if not os.getenv("ELEVENLABS_API_KEY"):
                st.error("ElevenLabs API Key missing!")
            else:
                with st.spinner("Generating audio (this may take a moment)..."):
                    script = st.session_state.story_data.get('script', '')
                    title = st.session_state.story_data.get('title', 'story')
                    
                    # Generate single audio file
                    audio_path = st.session_state.voice_generator.generate_voiceover(
                        script, 
                        voice_id=selected_voice_id,
                        filename=f"{title.replace(' ', '_')}_audio.mp3"
                    )
                    
                    if audio_path:
                        st.session_state.audio_path = audio_path
                        # Clear scene paths if they exist to avoid confusion
                        if 'scene_audio_paths' in st.session_state:
                            del st.session_state.scene_audio_paths
                        st.success("Audio generated successfully!")
                    else:
                        st.error("Audio generation failed.")
        
        # Audio Preview
        if 'audio_path' in st.session_state and os.path.exists(st.session_state.audio_path):
            st.audio(st.session_state.audio_path)
            st.text(f"Audio Path: {st.session_state.audio_path}")
            
        # Video Assembly
        st.subheader("3. Assemble Video")
        
        # Transition options
        st.markdown("**🎬 Transition Effects**")
        col_trans, col_dur = st.columns(2)
        with col_trans:
            transition_type = st.selectbox(
                "Transition Type:",
                ["crossfade", "fade_black", "slide_left", "slide_right", "slide_up", "none"],
                help="Effect between scene transitions"
            )
        with col_dur:
            transition_duration = st.slider(
                "Transition Duration (s):",
                min_value=0.1,
                max_value=1.0,
                value=0.3,
                step=0.1,
                help="How long the transition lasts"
            )
        
        if st.button("Create Final Video"):
            # Check prerequisites
            if 'audio_path' not in st.session_state:
                st.error("Please generate audio first.")
            elif 'scenes' not in st.session_state:
                st.error("No scenes found.")
            else:
                # Collect image paths
                missing_images = []
                image_paths = []
                scenes = st.session_state.scenes
                
                for i, scene in enumerate(scenes):
                    scene_num = scene.get('scene_number', i+1)
                    img_key = f"image_{scene_num}"
                    
                    if img_key in st.session_state and os.path.exists(st.session_state[img_key]):
                        image_paths.append(st.session_state[img_key])
                    else:
                        missing_images.append(scene_num)
                
                if missing_images:
                    st.warning(f"Missing images for scenes: {missing_images}. Please generate them in Tab 2.")
                else:
                    with st.spinner("Assembling video with transitions... this might take a minute..."):
                        video_path = st.session_state.video_assembler.create_philosophy_video(
                            scenes=scenes,
                            audio_path=st.session_state.audio_path,
                            image_paths=image_paths,
                            story_title=st.session_state.story_data.get('title', 'Philosophy Story'),
                            transition=transition_type,
                            transition_duration=transition_duration
                        )
                        
                        if video_path and os.path.exists(video_path):
                            st.session_state.video_path = video_path
                            st.success("Video created!")
                            st.balloons()
                        else:
                            st.error("Video assembly failed.")
                            
        # Final Video Preview
        if 'video_path' in st.session_state and os.path.exists(st.session_state.video_path):
            st.video(st.session_state.video_path)
            with open(st.session_state.video_path, 'rb') as v_file:
                 st.download_button("Download Video", v_file, file_name="philosophy_video.mp4")

            # TikTok Upload
            st.markdown("---")
            st.subheader("Post to TikTok")
            
            if 'tiktok_access_token' not in st.session_state:
                st.info("Connect TikTok in the sidebar to post.")
            else:
                tiktok_caption = st.text_input("Caption", st.session_state.story_data.get('title', 'Philosophy Video'))
                if st.button("Upload to TikTok Strategy (Draft/Private)"):
                    with st.spinner("Uploading to TikTok..."):
                        try:
                            result = st.session_state.tiktok_uploader.upload_video(
                                access_token=st.session_state.tiktok_access_token,
                                file_path=st.session_state.video_path,
                                title=tiktok_caption
                            )
                            st.success(f"Uploaded! Publish ID: {result.get('publish_id')}")
                            st.info("Check your TikTok 'Private' tab or Drafts (depending on implementation).")
                        except Exception as e:
                            st.error(f"Upload failed: {e}")

# --- Tab 4: Slideshows ---
with tab4:
    st.header("🎴 Slideshow Generator")
    st.info("Create TikTok-style slideshows with text burned directly into images using GPT Image 1.5. Perfect for TikTok/Instagram carousels with clean white/black text overlays.")
    
    if not SLIDESHOW_AVAILABLE:
        st.error("❌ Slideshow generator requires fal.ai. Please add FAL_KEY to your .env file.")
        st.code("FAL_KEY=your-fal-api-key", language="text")
    else:
        # Initialize slideshow generator
        if 'slideshow_generator' not in st.session_state:
            st.session_state.slideshow_generator = SlideshowGenerator()
        
        # Topic input with option to load from generated stories
        st.subheader("1. Enter Topic")
        
        # Check for existing generated scripts to load topics from
        existing_scripts = []
        if os.path.exists("generated_scripts"):
            for f in os.listdir("generated_scripts"):
                if f.endswith(".json"):
                    existing_scripts.append(f.replace(".json", "").replace("_", " ").title())
        
        # Option to load from existing story
        topic_source = st.radio(
            "Topic Source:",
            ["Enter manually", "Load from generated story"],
            horizontal=True
        )
        
        if topic_source == "Load from generated story" and existing_scripts:
            selected_story = st.selectbox(
                "Select a generated story:",
                options=existing_scripts,
                help="Use a topic from your previously generated stories"
            )
            slideshow_topic = selected_story
        elif topic_source == "Load from generated story" and not existing_scripts:
            st.warning("No generated stories found. Generate a story in Tab 1 first, or enter a topic manually.")
            slideshow_topic = st.text_input(
                "Slideshow Topic:", 
                "5 philosophers who changed the world",
                help="Topics like '5 philosophers...', '7 Stoic quotes...', etc. work best"
            )
        else:
            slideshow_topic = st.text_input(
                "Slideshow Topic:", 
                "5 philosophers who changed the world",
                help="Topics like '5 philosophers...', '7 Stoic quotes...', etc. work best"
            )
        
        col_gen, col_info = st.columns([1, 3])
        with col_gen:
            generate_slideshow_btn = st.button("🎴 Generate Slideshow", type="primary")
        with col_info:
            st.caption("Uses Gemini for script + GPT Image 1.5 via fal.ai for TikTok-style images with text overlays")
        
        if generate_slideshow_btn:
            with st.spinner("Generating slideshow... This may take a minute..."):
                try:
                    result = st.session_state.slideshow_generator.generate_slideshow(slideshow_topic)
                    
                    if result['script']:
                        st.session_state.slideshow_script = result['script']
                        st.session_state.slideshow_images = result['image_paths']
                        st.success(f"✅ Generated {len(result['image_paths'])} slides!")
                        st.rerun()
                    else:
                        st.error("Failed to generate slideshow script")
                except Exception as e:
                    st.error(f"Error: {e}")
        
        # Display generated slideshow
        if 'slideshow_script' in st.session_state and st.session_state.slideshow_script:
            st.markdown("---")
            st.subheader("2. Generated Slideshow")
            
            script = st.session_state.slideshow_script
            images = st.session_state.get('slideshow_images', [])
            
            # Script info
            col_info1, col_info2 = st.columns(2)
            with col_info1:
                st.metric("Title", script.get('title', 'Untitled'))
            with col_info2:
                st.metric("Slides Generated", len(images))
            
            # Display slides in a grid
            st.subheader("Slides Preview")
            
            slides = script.get('slides', [])
            
            # Create columns for slide display (3 per row)
            for i in range(0, len(slides), 3):
                cols = st.columns(3)
                for j, col in enumerate(cols):
                    idx = i + j
                    if idx < len(slides):
                        slide = slides[idx]
                        slide_num = slide.get('slide_number', idx)
                        
                        with col:
                            # Find matching image
                            matching_img = None
                            for img_path in images:
                                if f"_slide_{slide_num}.png" in img_path:
                                    matching_img = img_path
                                    break
                            
                            if matching_img and os.path.exists(matching_img):
                                st.image(matching_img, caption=f"Slide {slide_num}")
                            else:
                                st.info(f"Slide {slide_num}: No image yet")
                            
                            # Show slide details
                            with st.expander(f"Slide {slide_num} Details"):
                                st.markdown(f"**Type:** {slide.get('slide_type', 'unknown')}")
                                st.markdown(f"**Text:** {slide.get('display_text', '')}")
                                if slide.get('subtitle'):
                                    st.markdown(f"**Subtitle:** {slide.get('subtitle', '')}")
                                if slide.get('person_name'):
                                    st.markdown(f"**Person:** {slide.get('person_name', '')}")
            
            # Regenerate individual slides
            st.markdown("---")
            st.subheader("3. Regenerate Individual Slides")
            
            regen_col1, regen_col2 = st.columns([1, 2])
            with regen_col1:
                slide_to_regen = st.selectbox(
                    "Select slide to regenerate:",
                    options=range(len(slides)),
                    format_func=lambda x: f"Slide {slides[x].get('slide_number', x)}: {slides[x].get('display_text', '')[:30]}..."
                )
            with regen_col2:
                if st.button("🔄 Regenerate This Slide"):
                    with st.spinner(f"Regenerating slide {slides[slide_to_regen].get('slide_number', slide_to_regen)}..."):
                        try:
                            new_path = st.session_state.slideshow_generator.generate_slide(
                                slides[slide_to_regen],
                                script.get('title', 'slideshow')
                            )
                            if new_path:
                                # Update the images list
                                slide_num = slides[slide_to_regen].get('slide_number', slide_to_regen)
                                # Remove old path if exists
                                st.session_state.slideshow_images = [
                                    p for p in st.session_state.slideshow_images 
                                    if f"_slide_{slide_num}.png" not in p
                                ]
                                st.session_state.slideshow_images.append(new_path)
                                st.success(f"✅ Regenerated slide {slide_num}")
                                st.rerun()
                            else:
                                st.error("Failed to regenerate slide")
                        except Exception as e:
                            st.error(f"Error: {e}")
            
            # Download section
            st.markdown("---")
            st.subheader("4. Download")
            
            if images:
                st.markdown("**Download individual slides:**")
                download_cols = st.columns(min(len(images), 4))
                for idx, img_path in enumerate(images):
                    if os.path.exists(img_path):
                        col_idx = idx % 4
                        with download_cols[col_idx]:
                            with open(img_path, 'rb') as f:
                                st.download_button(
                                    f"📥 Slide {idx}",
                                    f,
                                    file_name=os.path.basename(img_path),
                                    mime="image/png",
                                    key=f"download_slide_{idx}"
                                )
        
        # Load existing slideshows
        st.markdown("---")
        st.subheader("📂 Load Existing Slideshow")
        
        # Scan for existing slideshow images
        existing_slideshows = {}
        if os.path.exists("generated_slideshows"):
            for f in os.listdir("generated_slideshows"):
                if f.endswith(".png"):
                    # Extract slideshow name from filename (everything before _slide_)
                    parts = f.rsplit("_slide_", 1)
                    if len(parts) == 2:
                        name = parts[0]
                        if name not in existing_slideshows:
                            existing_slideshows[name] = []
                        existing_slideshows[name].append(f"generated_slideshows/{f}")
        
        if existing_slideshows:
            selected_slideshow = st.selectbox(
                "Select a slideshow:",
                options=list(existing_slideshows.keys()),
                format_func=lambda x: x.replace("_", " ").title()
            )
            
            if st.button("Load Slideshow"):
                st.session_state.slideshow_images = sorted(existing_slideshows[selected_slideshow])
                st.session_state.slideshow_script = {
                    'title': selected_slideshow.replace("_", " ").title(),
                    'slides': [{'slide_number': i, 'display_text': f'Slide {i}'} 
                              for i in range(len(existing_slideshows[selected_slideshow]))]
                }
                st.success(f"Loaded {len(existing_slideshows[selected_slideshow])} slides")
                st.rerun()
        else:
            st.info("No existing slideshows found. Generate one above!")

# --- Tab 5: Video from Images (fal.ai) ---
with tab5:
    st.header("🎬 Video from Images")
    st.info("Create smooth AI-generated transition videos between your scene images using fal.ai's MiniMax Hailuo-02 model.")
    
    if not FAL_AVAILABLE:
        st.error("❌ fal.ai not configured. Please add FAL_KEY to your .env file.")
        st.code("FAL_KEY=your-fal-api-key", language="text")
    else:
        # Initialize fal video generator
        if 'fal_video_generator' not in st.session_state:
            st.session_state.fal_video_generator = FalVideoGenerator()
        
        st.subheader("1. Select Images")
        
        # Option to use current story images or select from folder
        image_source = st.radio(
            "Image Source:",
            ["Use Current Story Images", "Select from Folder"],
            horizontal=True
        )
        
        selected_images = []
        
        if image_source == "Use Current Story Images":
            if 'scenes' not in st.session_state or not st.session_state.scenes:
                st.warning("Please generate a story and images in Tabs 1-2 first, or select images from folder.")
            else:
                # Collect images from current story
                for i, scene in enumerate(st.session_state.scenes):
                    scene_num = scene.get('scene_number', i+1)
                    img_key = f"image_{scene_num}"
                    if img_key in st.session_state and os.path.exists(st.session_state[img_key]):
                        selected_images.append(st.session_state[img_key])
                
                if selected_images:
                    st.success(f"Found {len(selected_images)} images from current story")
                    
                    # Preview images in a row
                    cols = st.columns(min(len(selected_images), 6))
                    for idx, img_path in enumerate(selected_images[:6]):
                        with cols[idx]:
                            st.image(img_path, caption=f"Scene {idx+1}", width=100)
                    if len(selected_images) > 6:
                        st.caption(f"...and {len(selected_images) - 6} more")
                else:
                    st.warning("No images found for current story. Generate images in Tab 2 first.")
        
        else:  # Select from folder
            # Scan generated_images folder
            import glob as glob_module
            all_images = sorted(glob_module.glob("generated_images/*.png"))
            
            if not all_images:
                st.warning("No images found in generated_images/ folder.")
            else:
                # Group by story
                stories = {}
                for img in all_images:
                    # Extract story name (everything before _scene_)
                    basename = os.path.basename(img)
                    if "_scene_" in basename:
                        story_name = basename.rsplit("_scene_", 1)[0]
                        if story_name not in stories:
                            stories[story_name] = []
                        stories[story_name].append(img)
                
                if stories:
                    selected_story = st.selectbox(
                        "Select a story:",
                        options=list(stories.keys()),
                        format_func=lambda x: x.replace("_", " ").title()
                    )
                    
                    if selected_story:
                        # Sort images by scene number
                        story_images = stories[selected_story]
                        
                        def extract_scene_num(path):
                            basename = os.path.basename(path)
                            try:
                                parts = basename.rsplit("_scene_", 1)[1]
                                num = int(parts.split("_")[0])
                                return num
                            except:
                                return 0
                        
                        story_images = sorted(story_images, key=extract_scene_num)
                        selected_images = story_images
                        
                        st.success(f"Found {len(selected_images)} images for '{selected_story.replace('_', ' ').title()}'")
                        
                        # Preview
                        cols = st.columns(min(len(selected_images), 6))
                        for idx, img_path in enumerate(selected_images[:6]):
                            with cols[idx]:
                                st.image(img_path, caption=f"Scene {idx+1}", width=100)
                        if len(selected_images) > 6:
                            st.caption(f"...and {len(selected_images) - 6} more")
        
        if len(selected_images) >= 2:
            st.markdown("---")
            st.subheader("2. Generation Settings")
            
            # Explain the continuous video flow
            num_transitions = len(selected_images) - 1
            st.markdown(f"""
            **How it works:** Each clip starts on one image and transitions to the next.
            The clips chain together seamlessly:
            """)
            
            # Show the chain visually
            chain_str = " → ".join([f"Image {i+1}" for i in range(min(len(selected_images), 5))])
            if len(selected_images) > 5:
                chain_str += " → ..."
            st.code(chain_str)
            
            col_settings1, col_settings2, col_settings3 = st.columns(3)
            
            with col_settings1:
                clip_duration = st.selectbox(
                    "Clip Duration",
                    options=["5", "6"],
                    index=1,
                    help="Duration of each transition clip in seconds"
                )
            
            with col_settings2:
                crossfade_duration = st.slider(
                    "Crossfade Duration (seconds)",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.5,
                    step=0.1,
                    help="Duration of crossfade between video clips when concatenating"
                )
            
            with col_settings3:
                story_title_input = st.text_input(
                    "Video Title",
                    value=st.session_state.story_data.get('title', 'Philosophy_Story') if 'story_data' in st.session_state else "Philosophy_Story",
                    help="Title for output video filename"
                )
            
            # Cost estimate
            cost_per_clip = 0.045 * int(clip_duration)  # $0.045/sec
            estimated_cost = num_transitions * cost_per_clip
            total_duration = num_transitions * int(clip_duration)
            st.info(f"📊 **Estimated:** {num_transitions} clips × {clip_duration}s = **{total_duration}s video** | Cost: ~**${estimated_cost:.2f}**")
            
            # ========================================
            # ADVANCED: Audio-Sync Pipeline Settings
            # ========================================
            with st.expander("⚙️ Advanced: Audio-Sync Pipeline", expanded=False):
                st.markdown("""
                **Audio-Sync Mode** uses word-level timestamps from ElevenLabs to calculate 
                exact scene durations, then adjusts video clip lengths to match the audio perfectly.
                
                This eliminates the need to speed up or slow down the final video.
                """)
                
                use_audio_sync = st.checkbox(
                    "🔄 Enable Audio-Sync Mode",
                    value=False,
                    key="use_audio_sync_mode",
                    help="When enabled, audio will be generated with timestamps and clip durations will be optimized per-scene"
                )
                
                if use_audio_sync:
                    st.success("✅ Audio-Sync Mode enabled")
                    st.caption("When you generate audio below, it will include word-level timestamps for precise scene timing.")
                    
                    # Show timing validation option
                    show_timing_report = st.checkbox(
                        "📊 Show detailed timing report",
                        value=True,
                        key="show_timing_report"
                    )
                    
                    # Option to use dynamic clip durations
                    use_dynamic_durations = st.checkbox(
                        "🎬 Use dynamic clip durations (5s or 6s per scene)",
                        value=True,
                        key="use_dynamic_durations",
                        help="Each scene will get a 5s or 6s clip based on its audio duration"
                    )
                else:
                    show_timing_report = False
                    use_dynamic_durations = False
            
            st.markdown("---")
            st.subheader("3. Generate Transition Videos")
            
            if st.button("🎬 Generate All Transitions", type="primary"):
                # Store in session state for the progress UI
                st.session_state.fal_generating = True
                st.session_state.fal_video_paths = []
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                detail_text = st.empty()
                
                try:
                    # Get scene descriptions if available
                    scene_descriptions = []
                    if 'scenes' in st.session_state:
                        for scene in st.session_state.scenes:
                            desc = scene.get('visual_description', scene.get('key_concept', ''))
                            scene_descriptions.append(desc)
                    
                    # Upload phase
                    status_text.text("📤 Uploading images to fal.ai storage...")
                    uploaded_urls = []
                    for i, img_path in enumerate(selected_images):
                        progress_bar.progress((i + 1) / (len(selected_images) + num_transitions))
                        detail_text.text(f"   Uploading: {os.path.basename(img_path)}")
                        url = st.session_state.fal_video_generator.upload_image(img_path)
                        uploaded_urls.append(url)
                    
                    detail_text.text(f"   ✅ All {len(selected_images)} images uploaded")
                    
                    # Generation phase - each clip: image[i] → image[i+1]
                    status_text.text("🎬 Generating transition clips...")
                    video_paths = []
                    
                    for i in range(num_transitions):
                        progress = (len(selected_images) + i + 1) / (len(selected_images) + num_transitions)
                        progress_bar.progress(progress)
                        
                        # Show which images this clip transitions between
                        detail_text.text(f"   Clip {i + 1}: Image {i + 1} (start) → Image {i + 2} (end)")
                        
                        # Build prompt
                        if i < len(scene_descriptions):
                            scene_desc = scene_descriptions[i]
                        else:
                            scene_desc = f"Scene {i + 1} transitioning to scene {i + 2}"
                        
                        prompt = st.session_state.fal_video_generator.TRANSITION_PROMPT_TEMPLATE.format(
                            scene_description=scene_desc
                        )
                        
                        # Generate: start on image[i], end on image[i+1]
                        video_path = st.session_state.fal_video_generator.generate_transition_video(
                            start_image_url=uploaded_urls[i],
                            end_image_url=uploaded_urls[i + 1],
                            prompt=prompt,
                            scene_number=i + 1,
                            story_title=story_title_input,
                            duration=clip_duration
                        )
                        
                        if video_path:
                            video_paths.append(video_path)
                    
                    progress_bar.progress(1.0)
                    st.session_state.fal_video_paths = video_paths
                    st.session_state.fal_generating = False
                    
                    if video_paths:
                        status_text.success(f"✅ Generated {len(video_paths)}/{num_transitions} transition clips!")
                        detail_text.text("   Ready for concatenation with audio")
                    else:
                        status_text.error("Failed to generate transition videos")
                        
                except Exception as e:
                    st.session_state.fal_generating = False
                    status_text.error(f"Error: {e}")
                    import traceback
                    detail_text.code(traceback.format_exc())
            
            # Show generated videos
            if 'fal_video_paths' in st.session_state and st.session_state.fal_video_paths:
                st.markdown("---")
                st.subheader("4. Preview Generated Clips")
                
                video_paths = st.session_state.fal_video_paths
                
                for i, vpath in enumerate(video_paths):
                    if os.path.exists(vpath):
                        with st.expander(f"Transition {i + 1}", expanded=(i == 0)):
                            st.video(vpath)
                
                # ========================================
                # STEP 5: AUDIO GENERATION (Separate)
                # ========================================
                st.markdown("---")
                st.subheader("5. 🎙️ Audio Generation")
                st.caption("Generate and test different voice narrations for your script")
                
                # Voice selection
                voices = st.session_state.voice_generator.get_available_voices()
                voice_options = {v['name']: v['id'] for v in voices}
                
                # Default to Documentary Narrator
                default_voice = "Documentary Narrator" if "Documentary Narrator" in voice_options else list(voice_options.keys())[0]
                
                col_voice, col_info = st.columns([2, 1])
                with col_voice:
                    selected_voice_name = st.selectbox(
                        "Select Narrator Voice:", 
                        list(voice_options.keys()),
                        index=list(voice_options.keys()).index(default_voice),
                        key="fal_voice_select"
                    )
                    selected_voice_id = voice_options[selected_voice_name]
                with col_info:
                    # Show voice description
                    for v in voices:
                        if v['name'] == selected_voice_name:
                            st.caption(f"_{v.get('description', '')}_")
                            break
                
                # Script source
                if 'story_data' in st.session_state and st.session_state.story_data.get('script'):
                    use_script = st.text_area(
                        "Script for Narration",
                        st.session_state.story_data.get('script', ''),
                        height=150,
                        key="fal_script_preview"
                    )
                else:
                    use_script = st.text_area(
                        "Enter Script for Narration",
                        "Enter your narration script here...",
                        height=150,
                        key="fal_script_input"
                    )
                
                # Check if audio-sync mode is enabled
                audio_sync_enabled = st.session_state.get('use_audio_sync_mode', False)
                
                # Generate Audio Button
                button_label = "🎙️ Generate Audio with Timestamps" if audio_sync_enabled else "🎙️ Generate Audio"
                
                if st.button(button_label, type="primary", key="btn_generate_audio"):
                    if not use_script or use_script == "Enter your narration script here...":
                        st.error("Please provide a script for narration")
                    else:
                        with st.spinner("Generating voiceover audio..." + (" (with timestamps)" if audio_sync_enabled else "")):
                            try:
                                # Include voice name in filename to differentiate
                                voice_slug = selected_voice_name.replace(' ', '_').replace('🎙️', '').strip('_')
                                audio_filename = f"{story_title_input.replace(' ', '_')}_{voice_slug}.mp3"
                                
                                if audio_sync_enabled and 'scenes' in st.session_state:
                                    # Use the new timestamps endpoint
                                    audio_result = st.session_state.voice_generator.generate_voiceover_with_timestamps(
                                        script=use_script,
                                        scenes=st.session_state.scenes,
                                        voice_id=selected_voice_id,
                                        filename=audio_filename
                                    )
                                    
                                    if audio_result:
                                        audio_path = audio_result['audio_path']
                                        st.session_state.fal_audio_path = audio_path
                                        st.session_state.audio_timestamps = audio_result
                                        
                                        # Calculate scene durations and validate
                                        if TIMING_AVAILABLE:
                                            scene_timings = audio_result.get('scene_timings', [])
                                            enhanced_scenes = calculate_scene_durations(
                                                st.session_state.scenes, 
                                                scene_timings
                                            )
                                            validation = validate_pipeline_timing(enhanced_scenes)
                                            
                                            st.session_state.enhanced_scenes = enhanced_scenes
                                            st.session_state.timing_validation = validation
                                            
                                            # Show timing report if enabled
                                            if st.session_state.get('show_timing_report', True):
                                                st.markdown("### 📊 Timing Validation Report")
                                                
                                                col_metrics1, col_metrics2, col_metrics3 = st.columns(3)
                                                with col_metrics1:
                                                    st.metric("Audio Duration", f"{audio_result['total_duration']:.1f}s")
                                                with col_metrics2:
                                                    st.metric("Total Clip Duration", f"{validation['total_clip_duration']}s")
                                                with col_metrics3:
                                                    variance = validation['overall_variance']
                                                    st.metric("Variance", f"{variance:+.1f}s", 
                                                             delta_color="off" if abs(variance) < 2 else "inverse")
                                                
                                                # Status breakdown
                                                status_str = " | ".join([
                                                    f"🎯 {validation['scenes_by_status'].get('perfect', 0)}",
                                                    f"✅ {validation['scenes_by_status'].get('good', 0)}",
                                                    f"⚠️ {validation['scenes_by_status'].get('acceptable', 0)}",
                                                    f"❌ {validation['scenes_by_status'].get('warning', 0)}"
                                                ])
                                                st.caption(f"Scene timing status: {status_str}")
                                                
                                                # Show speed adjustment info
                                                adj_quality = validation.get('adjustment_quality', 'unknown')
                                                adj_note = validation.get('adjustment_note', '')
                                                adj_pct = validation.get('speed_adjustment_pct', 0)
                                                
                                                if adj_quality == 'perfect':
                                                    st.success(f"✅ {adj_note} - Excellent sync!")
                                                elif adj_quality == 'good':
                                                    st.success(f"✅ {adj_note} - Good sync!")
                                                elif adj_quality == 'acceptable':
                                                    st.warning(f"⚠️ {adj_note} - May be slightly noticeable")
                                                else:
                                                    st.error(f"❌ {adj_note} - Consider regenerating script with fewer words")
                                                
                                                # Show per-scene details in expander
                                                with st.expander("Scene-by-scene timing details"):
                                                    for scene in enhanced_scenes:
                                                        scene_num = scene.get('scene_number', '?')
                                                        audio_dur = scene.get('audio_duration', 0)
                                                        clip_dur = scene.get('clip_duration', 6)
                                                        status = scene.get('timing_status', 'unknown')
                                                        variance = scene.get('timing_variance', 0)
                                                        
                                                        emoji = {'perfect': '🎯', 'good': '✅', 'acceptable': '⚠️', 'warning': '❌'}.get(status, '📊')
                                                        st.text(f"{emoji} Scene {scene_num}: {audio_dur:.2f}s audio → {clip_dur}s clip ({variance:+.2f}s)")
                                        
                                        # Add to audio files list
                                        if 'story_audio_files' not in st.session_state:
                                            st.session_state.story_audio_files = []
                                        if audio_path not in st.session_state.story_audio_files:
                                            st.session_state.story_audio_files.append(audio_path)
                                        
                                        st.success(f"✅ Audio generated with timestamps: {os.path.basename(audio_path)}")
                                    else:
                                        st.error("Failed to generate audio with timestamps")
                                else:
                                    # Standard audio generation (no timestamps)
                                    audio_path = st.session_state.voice_generator.generate_voiceover(
                                        use_script,
                                        voice_id=selected_voice_id,
                                        filename=audio_filename
                                    )
                                    
                                    if audio_path:
                                        st.session_state.fal_audio_path = audio_path
                                        # Add to audio files list
                                        if 'story_audio_files' not in st.session_state:
                                            st.session_state.story_audio_files = []
                                        if audio_path not in st.session_state.story_audio_files:
                                            st.session_state.story_audio_files.append(audio_path)
                                        st.success(f"✅ Audio generated: {os.path.basename(audio_path)}")
                                        st.rerun()
                                    else:
                                        st.error("Failed to generate audio")
                            except Exception as e:
                                st.error(f"Error generating audio: {e}")
                                import traceback
                                st.code(traceback.format_exc())
                
                # Show all generated audio files for this story
                if 'story_audio_files' in st.session_state and st.session_state.story_audio_files:
                    st.markdown("**🎧 Generated Audio Files:**")
                    
                    for i, audio_file in enumerate(st.session_state.story_audio_files):
                        if os.path.exists(audio_file):
                            # Check if this is the currently selected audio
                            is_selected = st.session_state.get('fal_audio_path') == audio_file
                            
                            with st.expander(f"{'✅ ' if is_selected else ''}{os.path.basename(audio_file)}", expanded=is_selected):
                                st.audio(audio_file)
                                
                                col_select, col_download = st.columns(2)
                                with col_select:
                                    if not is_selected:
                                        if st.button(f"🎯 Use This Audio", key=f"select_audio_{i}"):
                                            st.session_state.fal_audio_path = audio_file
                                            st.rerun()
                                    else:
                                        st.success("Selected for video")
                                with col_download:
                                    with open(audio_file, 'rb') as f:
                                        st.download_button(
                                            "📥 Download",
                                            f,
                                            file_name=os.path.basename(audio_file),
                                            mime="audio/mpeg",
                                            key=f"dl_audio_{i}"
                                        )
                
                # Show currently selected audio
                elif 'fal_audio_path' in st.session_state and os.path.exists(st.session_state.fal_audio_path):
                    st.markdown("**🎧 Current Audio:**")
                    st.audio(st.session_state.fal_audio_path)
                    st.caption(f"File: {os.path.basename(st.session_state.fal_audio_path)}")
                
                # ========================================
                # STEP 6: VIDEO ASSEMBLY (Uses selected audio)
                # ========================================
                st.markdown("---")
                st.subheader("6. 🎬 Create Final Video")
                
                # Check if we have audio selected
                has_audio = 'fal_audio_path' in st.session_state and os.path.exists(st.session_state.get('fal_audio_path', ''))
                
                # Check if audio-sync mode was used
                has_timestamps = 'audio_timestamps' in st.session_state and st.session_state.audio_timestamps
                has_enhanced_scenes = 'enhanced_scenes' in st.session_state and st.session_state.enhanced_scenes
                
                if not has_audio:
                    st.warning("⚠️ Generate audio first (Step 5) before creating the final video.")
                else:
                    st.success(f"🎙️ Using audio: **{os.path.basename(st.session_state.fal_audio_path)}**")
                    
                    # Show audio-sync status
                    if has_timestamps and has_enhanced_scenes:
                        validation = st.session_state.get('timing_validation', {})
                        audio_dur = st.session_state.audio_timestamps.get('total_duration', 0)
                        clip_dur = validation.get('total_clip_duration', 0)
                        variance = validation.get('overall_variance', 0)
                        
                        st.info(f"🔄 **Audio-Sync Mode:** Audio {audio_dur:.1f}s | Clips {clip_dur}s | Variance {variance:+.1f}s")
                        
                        if abs(variance) < 2:
                            st.caption("✅ Good sync - minimal speedup/slowdown needed")
                        else:
                            st.caption(f"⚠️ Some adjustment may be needed ({abs(variance):.1f}s difference)")
                    
                    if st.button("🎬 Create Final Video with Selected Audio", type="primary", disabled=not has_audio):
                        progress_bar2 = st.progress(0)
                        status_text2 = st.empty()
                        
                        try:
                            status_text2.text("🎬 Concatenating videos and adding audio...")
                            progress_bar2.progress(0.3)
                            
                            # Create final video
                            final_path = st.session_state.fal_video_generator.create_final_video_with_audio(
                                video_paths=video_paths,
                                audio_path=st.session_state.fal_audio_path,
                                story_title=story_title_input,
                                crossfade_duration=crossfade_duration
                            )
                            
                            progress_bar2.progress(1.0)
                            
                            if final_path and os.path.exists(final_path):
                                st.session_state.fal_final_video = final_path
                                status_text2.success("✅ Final video created!")
                                st.balloons()
                            else:
                                status_text2.error("Failed to create final video")
                                
                        except Exception as e:
                            status_text2.error(f"Error: {e}")
                            import traceback
                            st.code(traceback.format_exc())
                
                # Show final video
                if 'fal_final_video' in st.session_state and os.path.exists(st.session_state.fal_final_video):
                    st.markdown("---")
                    st.subheader("🎉 Final Video")
                    st.video(st.session_state.fal_final_video)
                    
                    with open(st.session_state.fal_final_video, 'rb') as f:
                        st.download_button(
                            "📥 Download Final Video",
                            f,
                            file_name=os.path.basename(st.session_state.fal_final_video),
                            mime="video/mp4"
                        )
        
        elif len(selected_images) == 1:
            st.warning("Need at least 2 images to create transitions. Please generate more images.")
        
        # Show existing generated videos
        st.markdown("---")
        st.subheader("📂 Previously Generated Videos")
        
        import glob as glob_module
        existing_videos = sorted(glob_module.glob("generated_videos/*_final_with_audio.mp4"), reverse=True)
        
        if existing_videos:
            for vpath in existing_videos[:5]:
                with st.expander(os.path.basename(vpath)):
                    st.video(vpath)
                    with open(vpath, 'rb') as f:
                        st.download_button(
                            "📥 Download",
                            f,
                            file_name=os.path.basename(vpath),
                            mime="video/mp4",
                            key=f"dl_{os.path.basename(vpath)}"
                        )
        else:
            st.info("No videos generated yet. Create your first one above!")

# --- Tab 6: Automation Dashboard ---
with tab6:
    st.header("🤖 Automation Dashboard")
    
    # Initialize automation manager
    if AUTOMATION_MANAGER_AVAILABLE:
        if 'automation_manager' not in st.session_state:
            st.session_state.automation_manager = AutomationManager()
        
        auto_manager = st.session_state.automation_manager
        
        # Sub-tabs for dashboard sections
        dash_tab1, dash_tab2, dash_tab3, dash_tab4 = st.tabs([
            "📊 Overview", 
            "🚀 Active Automations", 
            "➕ Create New",
            "📝 Logs & History"
        ])
        
        # --- Dashboard Overview ---
        with dash_tab1:
            st.subheader("System Overview")
            
            # Summary metrics
            stats = auto_manager.get_stats_summary()
            pending_count = get_pending_topics_count()
            completed_count = get_completed_topics_count()
            
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("🤖 Total Automations", stats['total_automations'])
            with col2:
                st.metric("▶️ Running", stats['running'], 
                         delta=f"{stats['paused']} paused" if stats['paused'] > 0 else None)
            with col3:
                st.metric("📹 Items Produced", stats.get('total_items_produced', 0) + completed_count)
            with col4:
                st.metric("📋 Topics Pending", pending_count)
            with col5:
                st.metric("✅ Completed", completed_count)
            
            st.markdown("---")
            
            # Quick actions
            st.subheader("⚡ Quick Actions")
            
            col_action1, col_action2, col_action3 = st.columns(3)
            
            with col_action1:
                if st.button("🔄 Refresh All", use_container_width=True):
                    auto_manager.refresh_statuses()
                    st.rerun()
            
            with col_action2:
                if st.button("⏸️ Pause All Running", use_container_width=True):
                    for auto in auto_manager.get_active_automations():
                        if auto.status == AutomationStatus.RUNNING:
                            auto_manager.pause_automation(auto.id)
                    st.success("All running automations paused!")
                    st.rerun()
            
            with col_action3:
                if st.button("▶️ Resume All Paused", use_container_width=True):
                    for auto in auto_manager.get_all_automations():
                        if auto.status == AutomationStatus.PAUSED:
                            auto_manager.resume_automation(auto.id)
                    st.success("All paused automations resumed!")
                    st.rerun()
            
            st.markdown("---")
            
            # Recent activity
            st.subheader("📈 Recent Activity")
            recent_topics = get_recent_completed_topics(10)
            
            if recent_topics:
                for item in recent_topics:
                    st.markdown(f"✅ **{item['topic']}** - _{item['timestamp']}_")
            else:
                st.info("No completed topics yet. Start an automation to begin generating videos!")
        
        # --- Active Automations ---
        with dash_tab2:
            st.subheader("Active & Configured Automations")
            
            if st.button("🔄 Refresh Status", key="refresh_automations"):
                auto_manager.refresh_statuses()
                st.rerun()
            
            all_automations = auto_manager.get_all_automations()
            
            if not all_automations:
                st.info("No automations configured yet. Go to 'Create New' to set up your first automation!")
            else:
                for auto in all_automations:
                    # Status colors and icons
                    status_config = {
                        AutomationStatus.RUNNING: ("🟢", "success"),
                        AutomationStatus.PAUSED: ("🟡", "warning"),
                        AutomationStatus.STOPPED: ("🔴", "secondary"),
                        AutomationStatus.COMPLETED: ("✅", "info"),
                        AutomationStatus.ERROR: ("❌", "error")
                    }
                    status_icon, status_type = status_config.get(auto.status, ("❓", "secondary"))
                    
                    # Get model info
                    model_info = IMAGE_MODELS.get(auto.image_model, {"name": auto.image_model, "icon": "🖼️"})
                    
                    with st.expander(f"{status_icon} **{auto.name}** - {model_info['icon']} {model_info['name']}", expanded=(auto.status == AutomationStatus.RUNNING)):
                        
                        # Info columns
                        col_info1, col_info2, col_info3 = st.columns(3)
                        
                        with col_info1:
                            st.markdown(f"**Status:** {status_icon} {auto.status.value.title()}")
                            st.markdown(f"**Items Produced:** {auto.items_produced}")
                            if auto.current_topic:
                                st.markdown(f"**Current Topic:** _{auto.current_topic}_")
                        
                        with col_info2:
                            st.markdown(f"**Image Model:** {model_info['icon']} {model_info['name']}")
                            st.markdown(f"**Transition:** {TRANSITIONS.get(auto.transition, auto.transition)}")
                            st.markdown(f"**Schedule:** {SCHEDULE_MODES.get(auto.schedule_mode, {}).get('name', auto.schedule_mode)}")
                        
                        with col_info3:
                            st.markdown(f"**Created:** {auto.created_at[:16] if auto.created_at else 'N/A'}")
                            if auto.started_at:
                                st.markdown(f"**Started:** {auto.started_at[:16]}")
                            if auto.last_activity:
                                st.markdown(f"**Last Activity:** {auto.last_activity[:16]}")
                        
                        # Description
                        if auto.description:
                            st.markdown(f"📝 _{auto.description}_")
                        
                        # Error message if any
                        if auto.error_message:
                            st.error(f"⚠️ Error: {auto.error_message}")
                        
                        # Topics list
                        if auto.topics:
                            with st.expander("📋 Assigned Topics", expanded=False):
                                for topic in auto.topics:
                                    st.markdown(f"• {topic}")
                        
                        st.markdown("---")
                        
                        # Control buttons
                        col_ctrl1, col_ctrl2, col_ctrl3, col_ctrl4 = st.columns(4)
                        
                        with col_ctrl1:
                            if auto.status == AutomationStatus.STOPPED:
                                if st.button("▶️ Start", key=f"start_{auto.id}", use_container_width=True):
                                    if auto_manager.start_automation(auto.id):
                                        st.success(f"Started {auto.name}!")
                                        st.rerun()
                                    else:
                                        st.error("Failed to start automation")
                            elif auto.status == AutomationStatus.RUNNING:
                                if st.button("⏸️ Pause", key=f"pause_{auto.id}", use_container_width=True):
                                    if auto_manager.pause_automation(auto.id):
                                        st.success(f"Paused {auto.name}!")
                                        st.rerun()
                                    else:
                                        st.error("Failed to pause automation")
                            elif auto.status == AutomationStatus.PAUSED:
                                if st.button("▶️ Resume", key=f"resume_{auto.id}", use_container_width=True):
                                    if auto_manager.resume_automation(auto.id):
                                        st.success(f"Resumed {auto.name}!")
                                        st.rerun()
                                    else:
                                        st.error("Failed to resume automation")
                        
                        with col_ctrl2:
                            if auto.status in [AutomationStatus.RUNNING, AutomationStatus.PAUSED]:
                                if st.button("⏹️ Stop", key=f"stop_{auto.id}", use_container_width=True):
                                    if auto_manager.stop_automation(auto.id):
                                        st.success(f"Stopped {auto.name}!")
                                        st.rerun()
                                    else:
                                        st.error("Failed to stop automation")
                        
                        with col_ctrl3:
                            pass  # Spacer
                        
                        with col_ctrl4:
                            if st.button("🗑️ Delete", key=f"delete_{auto.id}", use_container_width=True):
                                if auto_manager.delete_automation(auto.id):
                                    st.success(f"Deleted {auto.name}!")
                                    st.rerun()
                                else:
                                    st.error("Failed to delete automation")
        
        # --- Create New Automation ---
        with dash_tab3:
            st.subheader("➕ Create New Automation")
            st.info("Configure a new slideshow/video automation. Choose between list-style (no voice) or narration-style (with voice) content.")
            
            with st.form("create_automation_form"):
                # Basic info
                st.markdown("### 📝 Basic Information")
                auto_name = st.text_input("Automation Name", placeholder="e.g., Daily Stoic Slideshows")
                auto_description = st.text_area("Description", placeholder="Describe what this automation does...", height=80)
                
                st.markdown("---")
                
                # Content Type Selection (Key Feature!)
                st.markdown("### 🎯 Content Type")
                st.markdown("""
                Choose the type of content this automation will generate:
                - **List Style**: "5 Philosophers", "7 Stoic Quotes" - slides with text, NO voice narration
                - **Narration Style**: Story-driven content - needs voice narration for full effect
                """)
                
                col_type1, col_type2 = st.columns(2)
                
                with col_type1:
                    topic_type_options = list(TOPIC_TYPES.keys())
                    topic_type_labels = [f"{TOPIC_TYPES[t]['icon']} {TOPIC_TYPES[t]['name']}" for t in topic_type_options]
                    selected_topic_type_idx = st.selectbox(
                        "Content Style",
                        range(len(topic_type_options)),
                        format_func=lambda x: topic_type_labels[x],
                        help="List style = no voice, Narration style = with voice"
                    )
                    selected_topic_type = topic_type_options[selected_topic_type_idx]
                    st.caption(f"_{TOPIC_TYPES[selected_topic_type]['description']}_")
                    st.caption(f"Example: {TOPIC_TYPES[selected_topic_type]['example']}")
                
                with col_type2:
                    # Topic file source
                    topic_file_options = list(TOPIC_FILES.keys())
                    topic_file_labels = [f"{TOPIC_FILES[t]['name']}" for t in topic_file_options]
                    selected_topic_file_idx = st.selectbox(
                        "Topic Source",
                        range(len(topic_file_options)),
                        format_func=lambda x: topic_file_labels[x],
                        help="Which topic queue to pull from"
                    )
                    selected_topic_file = topic_file_options[selected_topic_file_idx]
                    st.caption(TOPIC_FILES[selected_topic_file]['description'])
                
                st.markdown("---")
                
                # Generation settings
                st.markdown("### 🎨 Generation Settings")
                
                col_model, col_font = st.columns(2)
                
                with col_model:
                    model_options = list(IMAGE_MODELS.keys())
                    model_labels = [f"{IMAGE_MODELS[m]['icon']} {IMAGE_MODELS[m]['name']}" for m in model_options]
                    selected_model_idx = st.selectbox(
                        "Image Model",
                        range(len(model_options)),
                        format_func=lambda x: model_labels[x],
                        help="Select the AI model for image generation"
                    )
                    selected_model = model_options[selected_model_idx]
                    st.caption(IMAGE_MODELS[selected_model]['description'])
                
                with col_font:
                    font_options = list(FONT_STYLES.keys())
                    font_labels = [f"{FONT_STYLES[f]['name']}" for f in font_options]
                    selected_font_idx = st.selectbox(
                        "Font Style",
                        range(len(font_options)),
                        format_func=lambda x: font_labels[x],
                        help="Font for text overlay on slides"
                    )
                    selected_font = font_options[selected_font_idx]
                    st.caption(FONT_STYLES[selected_font].get('description', ''))
                
                st.markdown("---")
                
                # Voice & Video Options
                st.markdown("### 🎙️ Voice & Video Options")
                
                col_voice, col_video = st.columns(2)
                
                with col_voice:
                    # Auto-set based on topic type
                    default_voice = TOPIC_TYPES[selected_topic_type]['needs_voice']
                    enable_voice = st.checkbox(
                        "🎙️ Enable Voice Narration",
                        value=default_voice,
                        help="Add ElevenLabs voice narration (recommended for story-style content)"
                    )
                    if enable_voice:
                        st.caption("✅ Will generate audio narration")
                    else:
                        st.caption("📋 Slides only, no audio")
                
                with col_video:
                    enable_video_transitions = st.checkbox(
                        "🎬 Enable Video Transitions",
                        value=False,
                        help="Add AI-generated video transitions between slides (uses fal.ai)"
                    )
                    if enable_video_transitions:
                        st.caption("⚠️ Slower but more dynamic")
                    else:
                        st.caption("⚡ Faster, static slides")
                
                # Transition settings (only if video transitions enabled)
                if enable_video_transitions:
                    col_trans, col_dur = st.columns(2)
                    with col_trans:
                        transition_options = list(TRANSITIONS.keys())
                        selected_transition = st.selectbox(
                            "Transition Type",
                            transition_options,
                            format_func=lambda x: TRANSITIONS[x],
                            index=1  # Default to crossfade
                        )
                    with col_dur:
                        transition_duration = st.slider("Transition Duration (s)", 0.1, 1.0, 0.3, 0.1)
                else:
                    selected_transition = "crossfade"
                    transition_duration = 0.3
                
                st.markdown("---")
                
                # Schedule settings
                st.markdown("### ⏰ Schedule & Recycling")
                
                col_sched, col_recycle = st.columns(2)
                
                with col_sched:
                    schedule_options = list(SCHEDULE_MODES.keys())
                    schedule_labels = [f"{SCHEDULE_MODES[s]['name']}" for s in schedule_options]
                    selected_schedule_idx = st.selectbox(
                        "Schedule Mode",
                        range(len(schedule_options)),
                        format_func=lambda x: schedule_labels[x]
                    )
                    selected_schedule = schedule_options[selected_schedule_idx]
                    st.caption(SCHEDULE_MODES[selected_schedule]['description'])
                
                with col_recycle:
                    recycle_topics = st.checkbox(
                        "♻️ Recycle Topics",
                        value=False,
                        help="After completing a topic, add it back to the queue so it can be processed again later"
                    )
                    if recycle_topics:
                        st.caption("Topics will be reused indefinitely")
                    else:
                        st.caption("Topics are used once then marked completed")
                
                st.markdown("---")
                
                # Topics
                st.markdown("### 📋 Topics (Optional)")
                st.info(f"Leave empty to use the **{TOPIC_FILES[selected_topic_file]['name']}** queue, or add specific topics below.")
                
                topics_input = st.text_area(
                    "Topics (one per line)",
                    placeholder="5 Philosophers Who Changed the World\n7 Stoic Quotes for Daily Peace\nThe Death of Socrates",
                    height=120
                )
                
                st.markdown("---")
                
                # Submit
                col_submit, col_start = st.columns(2)
                with col_submit:
                    submitted = st.form_submit_button("💾 Create Automation", use_container_width=True)
                with col_start:
                    start_after_create = st.checkbox("Start immediately after creating", value=False)
                
                if submitted:
                    if not auto_name:
                        st.error("Please enter a name for the automation")
                    else:
                        # Parse topics
                        topics_list = [t.strip() for t in topics_input.split("\n") if t.strip()]
                        
                        # Create automation with new options
                        new_auto = auto_manager.create_automation(
                            name=auto_name,
                            description=auto_description,
                            topic_type=selected_topic_type,
                            image_model=selected_model,
                            font_name=selected_font,
                            enable_voice=enable_voice,
                            transition=selected_transition,
                            transition_duration=transition_duration,
                            enable_video_transitions=enable_video_transitions,
                            schedule_mode=selected_schedule,
                            topics=topics_list,
                            use_topic_file=selected_topic_file,
                            recycle_topics=recycle_topics
                        )
                        
                        st.success(f"✅ Created automation: **{auto_name}** (ID: {new_auto.id})")
                        
                        # Show summary
                        summary = []
                        summary.append(f"📋 Type: {TOPIC_TYPES[selected_topic_type]['name']}")
                        summary.append(f"🎨 Model: {IMAGE_MODELS[selected_model]['name']}")
                        if enable_voice:
                            summary.append("🎙️ Voice: Enabled")
                        if enable_video_transitions:
                            summary.append("🎬 Video: Enabled")
                        if recycle_topics:
                            summary.append("♻️ Recycling: On")
                        st.info(" | ".join(summary))
                        
                        if start_after_create:
                            if auto_manager.start_automation(new_auto.id):
                                st.success(f"▶️ Automation started!")
                            else:
                                st.warning("Created but failed to start. Check logs.")
                        
                        st.rerun()
        
        # --- Logs & History ---
        with dash_tab4:
            st.subheader("📝 Logs & Topic Management")
            
            # Sub-tabs for logs section
            log_tab1, log_tab2, log_tab3 = st.tabs(["📋 Topic Queues", "♻️ Recycle Topics", "📜 Logs"])
            
            # --- Topic Queues Tab ---
            with log_tab1:
                st.markdown("### 📊 All Topic Queues")
                
                # Get stats for all queues
                topic_stats = get_all_topic_stats()
                
                # Display queue metrics
                cols = st.columns(4)
                with cols[0]:
                    st.metric("📋 General Queue", topic_stats.get('general', {}).get('count', 0))
                with cols[1]:
                    st.metric("📋 List Topics", topic_stats.get('list', {}).get('count', 0))
                with cols[2]:
                    st.metric("🎙️ Narration Topics", topic_stats.get('narration', {}).get('count', 0))
                with cols[3]:
                    st.metric("✅ Completed", topic_stats.get('completed', {}).get('count', 0))
                
                st.markdown("---")
                
                # Queue selector
                queue_to_view = st.selectbox(
                    "Select Queue to View/Edit",
                    options=list(TOPIC_FILES.keys()),
                    format_func=lambda x: f"{TOPIC_FILES[x]['name']} ({topic_stats.get(x, {}).get('count', 0)} topics)"
                )
                
                col_view, col_edit = st.columns(2)
                
                with col_view:
                    st.markdown(f"**📋 {TOPIC_FILES[queue_to_view]['name']}**")
                    st.caption(TOPIC_FILES[queue_to_view]['description'])
                    
                    queue_topics = get_topics_from_file(queue_to_view)
                    if queue_topics:
                        for i, topic in enumerate(queue_topics[:30]):
                            st.markdown(f"{i+1}. {topic}")
                        if len(queue_topics) > 30:
                            st.caption(f"... and {len(queue_topics) - 30} more")
                    else:
                        st.info("Queue is empty")
                
                with col_edit:
                    st.markdown("**➕ Add Topics to This Queue**")
                    new_topics_input = st.text_area(
                        "Topics (one per line)",
                        placeholder="5 Philosophers Who Changed History\n7 Stoic Quotes for Inner Peace\nThe Death of Socrates",
                        height=150,
                        key=f"add_topics_{queue_to_view}"
                    )
                    
                    if st.button(f"Add to {TOPIC_FILES[queue_to_view]['name']}", key=f"add_btn_{queue_to_view}"):
                        if new_topics_input.strip():
                            topics_to_add = [t.strip() for t in new_topics_input.split("\n") if t.strip()]
                            added = add_topics_to_file(topics_to_add, queue_to_view)
                            st.success(f"✅ Added {added} topics to {TOPIC_FILES[queue_to_view]['name']}!")
                            st.rerun()
                        else:
                            st.warning("Please enter at least one topic")
                
                st.markdown("---")
                
                # Recent completions
                st.markdown("### ✅ Recent Completions")
                recent = get_recent_completed_topics(15)
                if recent:
                    for item in recent:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"✅ **{item['topic']}**")
                        with col2:
                            st.caption(item['timestamp'])
                else:
                    st.info("No completed topics yet.")
            
            # --- Recycle Topics Tab ---
            with log_tab2:
                st.markdown("### ♻️ Topic Recycling")
                st.info("Move completed topics back to a queue so they can be processed again. Great for evergreen content!")
                
                # Stats
                completed_count = topic_stats.get('completed', {}).get('count', 0)
                st.metric("Completed Topics Available", completed_count)
                
                if completed_count > 0:
                    st.markdown("---")
                    
                    col_target, col_count = st.columns(2)
                    
                    with col_target:
                        recycle_target = st.selectbox(
                            "Recycle To",
                            options=list(TOPIC_FILES.keys()),
                            format_func=lambda x: TOPIC_FILES[x]['name'],
                            help="Which queue to add recycled topics to"
                        )
                    
                    with col_count:
                        recycle_limit = st.number_input(
                            "How Many to Recycle",
                            min_value=1,
                            max_value=max(completed_count, 1),
                            value=min(10, completed_count),
                            help="Number of topics to move back to queue"
                        )
                    
                    col_recycle_btn, col_recycle_all = st.columns(2)
                    
                    with col_recycle_btn:
                        if st.button(f"♻️ Recycle {recycle_limit} Topics", use_container_width=True):
                            recycled = recycle_all_completed_topics(recycle_target, limit=recycle_limit)
                            st.success(f"♻️ Recycled {recycled} topics to {TOPIC_FILES[recycle_target]['name']}!")
                            st.rerun()
                    
                    with col_recycle_all:
                        if st.button(f"♻️ Recycle ALL ({completed_count})", use_container_width=True):
                            recycled = recycle_all_completed_topics(recycle_target, limit=None)
                            st.success(f"♻️ Recycled {recycled} topics to {TOPIC_FILES[recycle_target]['name']}!")
                            st.rerun()
                    
                    st.markdown("---")
                    
                    # Show recent completed topics that can be recycled
                    st.markdown("**Preview - Topics to Recycle:**")
                    recent = get_recent_completed_topics(10)
                    for item in recent:
                        st.markdown(f"• {item['topic']}")
                else:
                    st.info("No completed topics to recycle. Run some automations first!")
            
            # --- Logs Tab ---
            with log_tab3:
                st.markdown("### 📜 Automation Logs")
                
                col_refresh, _ = st.columns([1, 3])
                with col_refresh:
                    if st.button("🔄 Refresh Logs"):
                        st.rerun()
                
                logs = get_recent_logs(150)
                if logs:
                    st.code(logs, language="text")
                else:
                    st.info("No logs found yet. Logs appear when automations run.")
    
    else:
        # Fallback to basic dashboard if automation manager not available
        st.warning("Automation Manager not available. Showing basic dashboard.")
        st.info("This panel monitors the background automation agent.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Pending Topics Queue")
            try:
                if os.path.exists("topics.txt"):
                    with open("topics.txt", "r") as f:
                        topics = [l.strip() for l in f.readlines() if l.strip()]
                    st.metric("Topics Pending", len(topics))
                    st.dataframe(topics[:100], height=300, column_config={"value": "Topic"})
                else:
                    st.warning("topics.txt not found.")
            except Exception as e:
                st.error(f"Error reading topics: {e}")
                
        with col2:
            st.subheader("Completed History")
            try:
                if os.path.exists("completed_topics.txt"):
                    with open("completed_topics.txt", "r") as f:
                        completed = f.readlines()
                    st.metric("Videos Generated", len(completed))
                    st.text_area("History", "".join(reversed(completed[-20:])), height=300)
                else:
                    st.info("No completed topics yet.")
            except Exception as e:
                st.error(f"Error reading history: {e}")
                
        st.markdown("---")
        st.subheader("📝 Automation Logs")
        if st.button("Refresh Logs"):
            st.rerun()
            
        try:
            if os.path.exists("automation.log"):
                with open("automation.log", "r") as f:
                    logs = f.readlines()
                
                # Show last 50 lines
                log_content = "".join(logs[-50:])
                st.code(log_content, language="text")
            else:
                st.info("No logs found yet.")
        except Exception as e:
            st.error(f"Error reading logs: {e}")

# --- Tab 7: Visual Templates ---
with tab7:
    st.header("🎨 Visual Templates")
    st.info("""
    **Visual Templates** define the look and feel for your image generation.
    Just like script templates help structure content, visual templates ensure consistent aesthetic across all images.
    
    Use these for list-style content like "5 Philosophers", "7 Stoic Quotes", "3 Dostoevsky Pages", etc.
    """)
    
    # Sub-tabs for template management
    template_tab1, template_tab2, template_tab3 = st.tabs(["📚 Browse Templates", "✏️ Create Template", "🔧 Template Editor"])
    
    # --- Browse Templates ---
    with template_tab1:
        st.subheader("Available Visual Templates")
        
        # Category filter
        all_templates = st.session_state.template_manager.get_all_templates()
        categories = st.session_state.template_manager.get_categories()
        
        col_filter, col_count = st.columns([3, 1])
        with col_filter:
            selected_category = st.selectbox(
                "Filter by Category:",
                ["All"] + categories,
                key="template_category_filter"
            )
        with col_count:
            st.metric("Total Templates", len(all_templates))
        
        # Display templates as cards
        templates_to_show = all_templates.values()
        if selected_category != "All":
            templates_to_show = [t for t in templates_to_show if t.get('category') == selected_category]
        
        # Show templates in a grid (2 per row)
        templates_list = list(templates_to_show)
        for i in range(0, len(templates_list), 2):
            cols = st.columns(2)
            for j, col in enumerate(cols):
                idx = i + j
                if idx < len(templates_list):
                    template = templates_list[idx]
                    with col:
                        # Template card
                        is_builtin = template.get('is_builtin', False)
                        badge = "🔒 Built-in" if is_builtin else "✨ Custom"
                        
                        with st.container():
                            st.markdown(f"### {template['name']}")
                            st.caption(f"{badge} | Category: {template.get('category', 'N/A')}")
                            st.markdown(template.get('description', 'No description'))
                            
                            # Best for tags
                            if template.get('best_for'):
                                st.markdown("**Best for:** " + ", ".join(template['best_for']))
                            
                            # Placeholders
                            placeholders = template.get('placeholders', {})
                            if placeholders:
                                with st.expander(f"📝 Placeholders ({len(placeholders)})"):
                                    for ph_name, ph_info in placeholders.items():
                                        required = "Required" if ph_info.get('required', True) else "Optional"
                                        st.markdown(f"**`[{ph_name}]`** ({required})")
                                        st.caption(f"_{ph_info.get('description', 'No description')}_")
                                        st.caption(f"Example: {ph_info.get('example', 'N/A')}")
                            
                            # Style notes
                            if template.get('style_notes'):
                                with st.expander("🎨 Style Notes"):
                                    for note in template['style_notes']:
                                        st.markdown(f"• {note}")
                            
                            # Actions
                            btn_col1, btn_col2, btn_col3 = st.columns(3)
                            with btn_col1:
                                if st.button("👁️ Preview", key=f"preview_{template['id']}"):
                                    preview_prompt = st.session_state.template_manager.get_template_preview_prompt(template['id'])
                                    st.session_state[f"preview_prompt_{template['id']}"] = preview_prompt
                            with btn_col2:
                                if st.button("📋 Copy", key=f"copy_{template['id']}"):
                                    new_template = st.session_state.template_manager.duplicate_template(template['id'])
                                    if new_template:
                                        st.success(f"Created copy: {new_template['name']}")
                                        st.rerun()
                            with btn_col3:
                                if st.button("🎯 Use", key=f"use_{template['id']}"):
                                    st.session_state.selected_template_id = template['id']
                                    st.success(f"Selected: {template['name']}")
                                    st.info("Go to Tab 2 (Image Generation) to apply this template.")
                            
                            # Show preview if requested
                            if f"preview_prompt_{template['id']}" in st.session_state:
                                st.markdown("---")
                                st.markdown("**Preview Prompt (with example values):**")
                                st.code(st.session_state[f"preview_prompt_{template['id']}"], language="text")
                        
                        st.markdown("---")
    
    # --- Create Template ---
    with template_tab2:
        st.subheader("Create New Visual Template")
        st.markdown("""
        Create your own reusable visual template. Define placeholders with `[PLACEHOLDER_NAME]` syntax.
        These will be replaced with actual values when generating images.
        """)
        
        # Template name and category
        col_name, col_cat = st.columns([2, 1])
        with col_name:
            new_template_name = st.text_input("Template Name", placeholder="e.g., Epic Historical Collage")
        with col_cat:
            new_template_category = st.selectbox(
                "Category",
                ["epic_historical", "classical", "minimalist", "surreal", "aesthetic", "custom"],
                key="new_template_category"
            )
        
        new_template_description = st.text_area(
            "Description",
            placeholder="Describe what this template is best for and its visual characteristics...",
            height=80
        )
        
        # Base prompt with placeholder detection
        st.markdown("### Base Prompt")
        st.caption("Use `[PLACEHOLDER_NAME]` for dynamic values. Example: `[TITLE_TEXT]`, `[FIGURE1_DESCRIPTION]`")
        
        new_template_prompt = st.text_area(
            "Base Prompt Template",
            placeholder="""A vertical poster in a dark, ancient chamber with cracked stone walls...
Central bold text overlay '[TITLE_TEXT]' in large uppercase metallic gold serif font...
On the left, a serious bust of [FIGURE1_DESCRIPTION]...
aspect ratio 9:16.""",
            height=250,
            key="new_template_prompt"
        )
        
        # Auto-detect placeholders
        if new_template_prompt:
            import re
            detected_placeholders = list(set(re.findall(r'\[([A-Z0-9_]+)\]', new_template_prompt)))
            
            if detected_placeholders:
                st.markdown("### Detected Placeholders")
                st.success(f"Found {len(detected_placeholders)} placeholders: {', '.join(detected_placeholders)}")
                
                # Allow configuring each placeholder
                placeholder_configs = {}
                for ph in detected_placeholders:
                    with st.expander(f"Configure: [{ph}]", expanded=True):
                        cols = st.columns([2, 2, 1])
                        with cols[0]:
                            ph_desc = st.text_input(
                                "Description",
                                placeholder=f"What should [{ph}] contain?",
                                key=f"ph_desc_{ph}"
                            )
                        with cols[1]:
                            ph_example = st.text_input(
                                "Example Value",
                                placeholder=f"Example for [{ph}]",
                                key=f"ph_example_{ph}"
                            )
                        with cols[2]:
                            ph_required = st.checkbox("Required", value=True, key=f"ph_req_{ph}")
                        
                        placeholder_configs[ph] = {
                            "description": ph_desc or f"Replace with {ph.lower().replace('_', ' ')}",
                            "example": ph_example or f"Example {ph.lower().replace('_', ' ')}",
                            "required": ph_required
                        }
        
        # Style notes and best for
        col_style, col_best = st.columns(2)
        with col_style:
            style_notes_input = st.text_area(
                "Style Notes (one per line)",
                placeholder="Oil painting texture\nDramatic chiaroscuro lighting\nDark atmospheric mood",
                height=100,
                key="new_style_notes"
            )
        with col_best:
            best_for_input = st.text_area(
                "Best For (one per line)",
                placeholder="List videos (5 philosophers, 7 quotes)\nEpic introductions\nHistorical figures",
                height=100,
                key="new_best_for"
            )
        
        # Model hints
        with st.expander("🔧 Model-Specific Hints (Optional)"):
            col_mj, col_dalle, col_sd = st.columns(3)
            with col_mj:
                mj_hint = st.text_input("Midjourney", placeholder="--ar 9:16 --v 6", key="hint_mj")
            with col_dalle:
                dalle_hint = st.text_input("DALL-E", placeholder="Use HD quality", key="hint_dalle")
            with col_sd:
                sd_hint = st.text_input("Stable Diffusion", placeholder="Strength 0.7", key="hint_sd")
        
        # Create button
        st.markdown("---")
        if st.button("✨ Create Template", type="primary", disabled=not (new_template_name and new_template_prompt)):
            # Parse inputs
            style_notes = [s.strip() for s in style_notes_input.split('\n') if s.strip()] if style_notes_input else []
            best_for = [s.strip() for s in best_for_input.split('\n') if s.strip()] if best_for_input else []
            
            model_hints = {}
            if mj_hint:
                model_hints['midjourney'] = mj_hint
            if dalle_hint:
                model_hints['dall-e'] = dalle_hint
            if sd_hint:
                model_hints['stable_diffusion'] = sd_hint
            
            # Get placeholder configs if they exist
            placeholders = {}
            if 'placeholder_configs' in dir() and placeholder_configs:
                placeholders = placeholder_configs
            else:
                # Auto-generate from detected placeholders
                parsed = parse_template_from_description(new_template_prompt)
                placeholders = parsed.get('placeholders', {})
            
            # Create the template
            try:
                new_template = st.session_state.template_manager.create_template(
                    name=new_template_name,
                    description=new_template_description,
                    base_prompt=new_template_prompt,
                    placeholders=placeholders,
                    category=new_template_category,
                    style_notes=style_notes,
                    best_for=best_for,
                    model_hints=model_hints
                )
                st.success(f"✅ Template '{new_template['name']}' created with ID: {new_template['id']}")
                st.balloons()
            except Exception as e:
                st.error(f"Error creating template: {e}")
    
    # --- Template Editor ---
    with template_tab3:
        st.subheader("Edit Custom Templates")
        
        # Only show custom templates for editing
        custom_templates = {k: v for k, v in all_templates.items() if not v.get('is_builtin', False)}
        
        if not custom_templates:
            st.info("No custom templates yet. Create one in the 'Create Template' tab, or duplicate a built-in template from the 'Browse Templates' tab.")
        else:
            # Select template to edit
            template_to_edit = st.selectbox(
                "Select Template to Edit:",
                list(custom_templates.keys()),
                format_func=lambda x: custom_templates[x]['name']
            )
            
            if template_to_edit:
                template = custom_templates[template_to_edit]
                
                st.markdown(f"### Editing: {template['name']}")
                
                # Editable fields
                edit_name = st.text_input("Name", value=template['name'], key="edit_name")
                edit_description = st.text_area("Description", value=template.get('description', ''), key="edit_desc")
                edit_category = st.selectbox(
                    "Category",
                    ["epic_historical", "classical", "minimalist", "surreal", "aesthetic", "custom"],
                    index=["epic_historical", "classical", "minimalist", "surreal", "aesthetic", "custom"].index(template.get('category', 'custom')) if template.get('category', 'custom') in ["epic_historical", "classical", "minimalist", "surreal", "aesthetic", "custom"] else 5,
                    key="edit_category"
                )
                edit_prompt = st.text_area("Base Prompt", value=template.get('base_prompt', ''), height=300, key="edit_prompt")
                
                # Edit style notes
                current_style_notes = '\n'.join(template.get('style_notes', []))
                edit_style_notes = st.text_area("Style Notes (one per line)", value=current_style_notes, key="edit_style")
                
                # Edit best for
                current_best_for = '\n'.join(template.get('best_for', []))
                edit_best_for = st.text_area("Best For (one per line)", value=current_best_for, key="edit_best")
                
                col_save, col_delete = st.columns(2)
                with col_save:
                    if st.button("💾 Save Changes", type="primary"):
                        updates = {
                            'name': edit_name,
                            'description': edit_description,
                            'category': edit_category,
                            'base_prompt': edit_prompt,
                            'style_notes': [s.strip() for s in edit_style_notes.split('\n') if s.strip()],
                            'best_for': [s.strip() for s in edit_best_for.split('\n') if s.strip()]
                        }
                        
                        # Re-parse placeholders from updated prompt
                        parsed = parse_template_from_description(edit_prompt)
                        updates['placeholders'] = parsed.get('placeholders', {})
                        
                        result = st.session_state.template_manager.update_template(template_to_edit, updates)
                        if result:
                            st.success("Template updated!")
                            st.rerun()
                        else:
                            st.error("Failed to update template")
                
                with col_delete:
                    if st.button("🗑️ Delete Template", type="secondary"):
                        if st.session_state.template_manager.delete_template(template_to_edit):
                            st.success("Template deleted!")
                            st.rerun()
                        else:
                            st.error("Failed to delete template")
    
    # Quick reference section
    st.markdown("---")
    st.subheader("📖 Quick Reference: Using Templates")
    
    with st.expander("How to Use Visual Templates", expanded=False):
        st.markdown("""
        ### 1. Select a Template
        Browse the templates above and click "🎯 Use" to select one for your video.
        
        ### 2. Apply to Image Generation
        Go to **Tab 2 (Image Generation)** where you'll see a template selector. 
        When generating images, the template will structure your prompts automatically.
        
        ### 3. Customize Placeholders
        Each template has placeholders like `[TITLE_TEXT]` and `[FIGURE1_DESCRIPTION]`.
        These get filled in based on your story's content.
        
        ### 4. Create Your Own
        Use the "Create Template" tab to build templates matching your brand's visual identity.
        
        ### Template Format
        Templates use placeholders in square brackets:
        ```
        A dramatic scene showing [FIGURE_DESCRIPTION] in [SETTING].
        The mood is [EMOTIONAL_QUALITY]. Central text says '[TITLE_TEXT]'.
        ```
        
        ### Best Practices
        - **Be specific** about lighting, textures, and composition
        - **Include aspect ratio** (9:16 for TikTok vertical)
        - **Add negative prompts** if needed (e.g., "no modern elements")
        - **Test with Preview** before generating images
        """)
    
    # Show currently selected template
    if 'selected_template_id' in st.session_state:
        st.markdown("---")
        selected = st.session_state.template_manager.get_template(st.session_state.selected_template_id)
        if selected:
            st.success(f"🎯 Currently Selected Template: **{selected['name']}**")
            st.caption("This template will be available for use in Tab 2 (Image Generation)")

# --- Tab 8: TikTok Slideshow Generator ---
with tab8:
    st.header("🎴 TikTok Slideshow Generator")
    st.info("""
    **New Approach**: Generate viral TikTok slideshows with clean text overlays.
    
    1. **AI generates script** (Gemini creates text for each slide)
    2. **AI generates backgrounds** (fal.ai or solid gradients)
    3. **Text is burned onto images** (Pillow - perfect control over fonts/styling)
    
    This separates background from text, giving you consistent, professional results.
    """)
    
    if not TIKTOK_SLIDESHOW_AVAILABLE:
        st.error("TikTok Slideshow modules not available. Check that `tiktok_slideshow.py` and `text_overlay.py` exist.")
    else:
        # Initialize session state
        if 'tiktok_script' not in st.session_state:
            st.session_state.tiktok_script = None
        if 'tiktok_slides' not in st.session_state:
            st.session_state.tiktok_slides = []
        if 'tiktok_image_paths' not in st.session_state:
            st.session_state.tiktok_image_paths = []
        
        # Topic input
        st.subheader("📝 Step 1: Generate Script")
        
        tiktok_topic = st.text_input(
            "Enter your slideshow topic:",
            value="6 philosophical practices successful people use daily to find inner peace",
            key="tiktok_topic_input"
        )
        
        # Suggested topics
        st.markdown("**Suggested Topics:**")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("5 Stoic Quotes", key="tiktok_sug_1"):
                st.session_state.tiktok_topic_input = "5 powerful Stoic quotes that will change how you see life"
                st.rerun()
        with col2:
            if st.button("Philosophy for Peace", key="tiktok_sug_2"):
                st.session_state.tiktok_topic_input = "6 philosophical practices for finding inner peace"
                st.rerun()
        with col3:
            if st.button("Ancient Wisdom", key="tiktok_sug_3"):
                st.session_state.tiktok_topic_input = "5 ancient philosophers whose words still hit hard today"
                st.rerun()
        
        # Generate script button
        if st.button("🧠 Generate Script (Preview)", key="tiktok_gen_script"):
            with st.spinner("Generating script with Gemini..."):
                try:
                    slideshow = TikTokSlideshow()
                    script = slideshow._generate_script(tiktok_topic)
                    
                    if script:
                        st.session_state.tiktok_script = script
                        st.session_state.tiktok_slides = script.get('slides', [])
                        st.success(f"✅ Script generated: {script.get('title', 'Unknown')}")
                    else:
                        st.error("Failed to generate script")
                except Exception as e:
                    st.error(f"Error: {e}")
        
        # Display script preview
        if st.session_state.tiktok_script:
            st.markdown("---")
            st.subheader("📋 Script Preview")
            
            script = st.session_state.tiktok_script
            st.markdown(f"**Title:** {script.get('title', 'Unknown')}")
            st.markdown(f"**Total Slides:** {len(script.get('slides', []))}")
            
            # Editable slides
            st.markdown("**Edit Slides Below:**")
            edited_slides = []
            
            for i, slide in enumerate(st.session_state.tiktok_slides):
                with st.expander(f"Slide {slide.get('slide_number', i)} - {slide.get('slide_type', 'content').upper()}", expanded=i==0):
                    # Edit display text
                    new_display = st.text_input(
                        "Main Text:",
                        value=slide.get('display_text', ''),
                        key=f"tiktok_slide_{i}_display"
                    )
                    
                    # Edit subtitle
                    new_subtitle = st.text_area(
                        "Subtitle:",
                        value=slide.get('subtitle', ''),
                        key=f"tiktok_slide_{i}_subtitle",
                        height=80
                    )
                    
                    # Edit visual description (for background generation)
                    new_visual = st.text_area(
                        "Background Description (for AI image):",
                        value=slide.get('visual_description', ''),
                        key=f"tiktok_slide_{i}_visual",
                        height=80
                    )
                    
                    # Store edited values
                    edited_slide = slide.copy()
                    edited_slide['display_text'] = new_display
                    edited_slide['subtitle'] = new_subtitle
                    edited_slide['visual_description'] = new_visual
                    edited_slides.append(edited_slide)
            
            # Update slides with edits
            st.session_state.tiktok_slides = edited_slides
            
            # Step 2: Generate Images
            st.markdown("---")
            st.subheader("🎨 Step 2: Generate Slides")
            
            # Get available fonts
            overlay_check = TextOverlay()
            available_fonts = overlay_check.get_available_fonts()
            
            # Font options
            st.markdown("**🔤 Font Selection:**")
            
            # Create font options with descriptions
            font_options = {
                "auto": "Auto (based on style)",
            }
            for font_id, info in available_fonts.items():
                font_options[font_id] = f"{info['name']} - {info['description']}"
            
            font_list = list(font_options.keys())
            
            # Quick font buttons - these set a temporary variable, then we use it for the selectbox default
            st.markdown("**Quick Select:**")
            font_cols = st.columns(7)
            quick_fonts = [
                ("social", "📱 Social"),
                ("montserrat", "Modern"),
                ("oswald", "Impact"),
                ("bebas", "Bold"),
                ("cormorant", "Elegant"),
                ("montserrat-italic", "Italic"),
                ("cinzel", "Classical")
            ]
            
            # Initialize selected font if not set
            if "selected_font_value" not in st.session_state:
                st.session_state.selected_font_value = "auto"
            
            for i, (font_id, label) in enumerate(quick_fonts):
                with font_cols[i]:
                    if font_id in font_list:
                        if st.button(label, key=f"quick_font_{font_id}", use_container_width=True):
                            st.session_state.selected_font_value = font_id
                            st.rerun()
            
            col_font1, col_font2 = st.columns(2)
            with col_font1:
                # Get the current index based on stored value
                try:
                    current_index = font_list.index(st.session_state.selected_font_value)
                except ValueError:
                    current_index = 0
                
                selected_font = st.selectbox(
                    "Font:",
                    font_list,
                    format_func=lambda x: font_options[x],
                    index=current_index,
                    help="Choose a specific font or 'Auto' to let the style decide",
                    key="tiktok_font_select"
                )
                # Update stored value when selectbox changes
                st.session_state.selected_font_value = selected_font
                
            with col_font2:
                visual_style = st.selectbox(
                    "Visual Style:",
                    ["modern", "elegant", "philosophaire", "bold", "minimal"],
                    index=0,
                    help="modern = shadow, elegant/philosophaire = italic with shadow, bold = outline",
                    key="tiktok_visual_style"
                )
            
            st.markdown("**Background Options:**")
            col1, col2 = st.columns(2)
            with col1:
                use_ai_backgrounds = st.checkbox(
                    "Use AI-generated backgrounds",
                    value=False,
                    help="If unchecked, uses gradient backgrounds (faster, no API cost)"
                )
            with col2:
                image_generator = st.selectbox(
                    "Image Generator (if AI backgrounds):",
                    ["fal", "openai"],
                    index=0,
                    disabled=not use_ai_backgrounds
                )

            # Generation mode selection
            st.markdown("**Generation Mode:**")
            gen_mode = st.radio(
                "Choose how to generate slides:",
                ["Generate All at Once", "Generate One at a Time"],
                horizontal=True,
                key="tiktok_gen_mode",
                help="'One at a Time' lets you preview and approve each slide before moving to the next"
            )
            
            if gen_mode == "Generate All at Once":
                if st.button("🖼️ Generate All Slides", key="tiktok_gen_slides"):
                    with st.spinner("Generating slides..."):
                        try:
                            # Create updated script with edited slides
                            updated_script = st.session_state.tiktok_script.copy()
                            updated_script['slides'] = st.session_state.tiktok_slides
                            
                            # Add style settings to script
                            updated_script['font_name'] = selected_font if selected_font != "auto" else None
                            updated_script['visual_style'] = visual_style

                            slideshow = TikTokSlideshow(image_generator=image_generator)
                            result = slideshow.create_from_script(
                                updated_script,
                                skip_image_generation=not use_ai_backgrounds
                            )
                            
                            if result['image_paths']:
                                st.session_state.tiktok_image_paths = result['image_paths']
                                st.success(f"✅ Generated {len(result['image_paths'])} slides!")
                            else:
                                st.error("No slides generated")
                        except Exception as e:
                            st.error(f"Error: {e}")
                            import traceback
                            st.code(traceback.format_exc())
            
            else:  # Generate One at a Time
                st.markdown("---")
                st.markdown("### 🎯 Generate Slides One at a Time")
                st.info("Generate each slide individually. Preview and approve before moving to the next.")
                
                # Initialize tracking for individual slides
                if 'tiktok_individual_slides' not in st.session_state:
                    st.session_state.tiktok_individual_slides = {}
                
                # Get slideshow title for naming
                slideshow_title = st.session_state.tiktok_script.get('title', 'slideshow')
                
                # Display each slide with its own generate button
                for i, slide in enumerate(st.session_state.tiktok_slides):
                    slide_type = slide.get('slide_type', 'content').upper()
                    display_text = slide.get('display_text', f'Slide {i}')
                    
                    with st.expander(f"🎴 Slide {i}: {slide_type} - {display_text[:30]}...", expanded=(i==0)):
                        col_info, col_btn = st.columns([3, 1])
                        
                        with col_info:
                            st.markdown(f"**Display Text:** {slide.get('display_text', '')}")
                            if slide.get('subtitle'):
                                st.markdown(f"**Subtitle:** {slide.get('subtitle', '')}")
                            st.markdown(f"**Visual Description:** {slide.get('visual_description', '')[:100]}...")
                        
                        with col_btn:
                            # Check if this slide has been generated
                            slide_key = f"slide_{i}"
                            is_generated = slide_key in st.session_state.tiktok_individual_slides
                            
                            if is_generated:
                                st.success("✅ Generated")
                            
                            if st.button(
                                "🔄 Regenerate" if is_generated else "🎨 Generate",
                                key=f"gen_single_slide_{i}",
                                use_container_width=True
                            ):
                                with st.spinner(f"Generating slide {i}..."):
                                    try:
                                        slideshow = TikTokSlideshow(image_generator=image_generator)
                                        result = slideshow.generate_single_slide(
                                            slide=slide,
                                            slide_index=i,
                                            slideshow_title=slideshow_title,
                                            skip_image_generation=not use_ai_backgrounds,
                                            font_name=selected_font if selected_font != "auto" else None,
                                            visual_style=visual_style
                                        )
                                        
                                        if result['success']:
                                            st.session_state.tiktok_individual_slides[slide_key] = result
                                            st.success(f"✅ Slide {i} generated!")
                                            st.rerun()
                                        else:
                                            st.error(f"Failed to generate slide {i}")
                                    except Exception as e:
                                        st.error(f"Error: {e}")
                        
                        # Show generated slide preview
                        if slide_key in st.session_state.tiktok_individual_slides:
                            result = st.session_state.tiktok_individual_slides[slide_key]
                            if os.path.exists(result['image_path']):
                                img = Image.open(result['image_path'])
                                st.image(img, caption=f"Slide {i}", width=300)
                                
                                # Download button
                                with open(result['image_path'], "rb") as f:
                                    st.download_button(
                                        f"📥 Download Slide {i}",
                                        f.read(),
                                        file_name=os.path.basename(result['image_path']),
                                        mime="image/png",
                                        key=f"download_single_{i}"
                                    )
                
                # Summary of generated slides
                st.markdown("---")
                generated_count = len(st.session_state.tiktok_individual_slides)
                total_count = len(st.session_state.tiktok_slides)
                
                st.markdown(f"**Progress:** {generated_count}/{total_count} slides generated")
                
                if generated_count == total_count:
                    st.success("🎉 All slides generated!")
                    
                    # Collect all paths for the main display
                    all_paths = []
                    for i in range(total_count):
                        slide_key = f"slide_{i}"
                        if slide_key in st.session_state.tiktok_individual_slides:
                            all_paths.append(st.session_state.tiktok_individual_slides[slide_key]['image_path'])
                    
                    if st.button("📋 Copy to Main Gallery", key="copy_to_gallery"):
                        st.session_state.tiktok_image_paths = all_paths
                        st.success("Slides copied to gallery!")
                        st.rerun()
            
            # Display generated slides
            if st.session_state.tiktok_image_paths:
                st.markdown("---")
                st.subheader("🖼️ Generated Slides")
                
                # Grid display
                cols = st.columns(3)
                for i, path in enumerate(st.session_state.tiktok_image_paths):
                    with cols[i % 3]:
                        if os.path.exists(path):
                            img = Image.open(path)
                            # Resize for display
                            display_width = 300
                            ratio = display_width / img.width
                            display_height = int(img.height * ratio)
                            img_resized = img.resize((display_width, display_height))
                            
                            st.image(img_resized, caption=f"Slide {i}", use_container_width=True)
                            
                            # Download button
                            with open(path, "rb") as f:
                                st.download_button(
                                    f"📥 Download",
                                    f.read(),
                                    file_name=os.path.basename(path),
                                    mime="image/png",
                                    key=f"tiktok_download_{i}"
                                )
        
        # Font Playground - test fonts on existing images
        st.markdown("---")
        st.subheader("🎨 Font Playground")
        st.info("Test different fonts on your existing background images instantly. Pick an image, enter text, and compare fonts side-by-side!")
        
        # Find available background images
        bg_dir = "generated_slideshows/backgrounds"
        available_backgrounds = []
        if os.path.exists(bg_dir):
            available_backgrounds = sorted([
                os.path.join(bg_dir, f) for f in os.listdir(bg_dir) 
                if f.endswith('.png')
            ])
        
        # Also check for any slide images that could be used
        slide_dir = "generated_slideshows"
        available_slides = sorted(glob.glob(f"{slide_dir}/*_slide_*.png"))[:10]
        
        all_images = available_backgrounds + available_slides
        
        if all_images:
            col_img, col_text = st.columns([1, 1])
            
            with col_img:
                # Image selector
                selected_bg = st.selectbox(
                    "Select Background Image:",
                    all_images,
                    format_func=lambda x: os.path.basename(x),
                    key="playground_bg_select"
                )
                
                # Show thumbnail of selected image
                if selected_bg and os.path.exists(selected_bg):
                    img_preview = Image.open(selected_bg)
                    st.image(img_preview, caption="Selected Background", width=200)
            
            with col_text:
                # Text inputs
                playground_title = st.text_input(
                    "Title Text:",
                    value="The Path to Inner Peace",
                    key="playground_title"
                )
                playground_subtitle = st.text_area(
                    "Subtitle Text:",
                    value="Ancient wisdom for the modern soul",
                    height=80,
                    key="playground_subtitle"
                )
                playground_uppercase = st.checkbox(
                    "UPPERCASE title",
                    value=True,
                    key="playground_uppercase"
                )
            
            # Generate comparison button
            if st.button("🎨 Generate All Font Previews", key="playground_generate"):
                with st.spinner("Generating font previews..."):
                    try:
                        overlay = TextOverlay()
                        fonts = overlay.get_available_fonts()
                        
                        # Create output directory
                        preview_dir = "generated_slideshows/font_previews"
                        os.makedirs(preview_dir, exist_ok=True)
                        
                        preview_paths = {}
                        for font_id, info in fonts.items():
                            output_path = os.path.join(preview_dir, f"preview_{font_id}.png")
                            
                            overlay.create_slide(
                                background_path=selected_bg,
                                output_path=output_path,
                                title=playground_title,
                                subtitle=playground_subtitle if playground_subtitle else None,
                                font_name=font_id,
                                uppercase_title=playground_uppercase,
                                style="modern"
                            )
                            preview_paths[font_id] = output_path
                        
                        st.session_state.font_previews = preview_paths
                        st.success(f"✅ Generated {len(preview_paths)} font previews!")
                    except Exception as e:
                        st.error(f"Error: {e}")
            
            # Display font previews in a grid
            if 'font_previews' in st.session_state and st.session_state.font_previews:
                st.markdown("### 📊 Font Comparison")
                
                overlay = TextOverlay()
                fonts = overlay.get_available_fonts()
                
                # Create 3-column grid
                preview_items = list(st.session_state.font_previews.items())
                cols = st.columns(3)
                
                for i, (font_id, path) in enumerate(preview_items):
                    with cols[i % 3]:
                        if os.path.exists(path):
                            img = Image.open(path)
                            font_info = fonts.get(font_id, {})
                            
                            st.image(img, caption=f"{font_info.get('name', font_id)}", use_container_width=True)
                            st.caption(f"_{font_info.get('description', '')}_")
                            
                            # Download button
                            with open(path, "rb") as f:
                                st.download_button(
                                    f"📥 {font_id}",
                                    f.read(),
                                    file_name=f"slide_{font_id}.png",
                                    mime="image/png",
                                    key=f"playground_dl_{font_id}"
                                )
        else:
            st.warning("No background images found. Generate some slides first, or the backgrounds will be created automatically.")
        
        # Existing slideshows browser
        st.markdown("---")
        st.subheader("📁 Browse Existing Slideshows")
        
        slideshow_dir = "generated_slideshows"
        if os.path.exists(slideshow_dir):
            slideshow_files = sorted(glob.glob(f"{slideshow_dir}/*_slide_*.png"))
            
            if slideshow_files:
                # Group by slideshow name
                slideshows = {}
                for path in slideshow_files:
                    filename = os.path.basename(path)
                    # Extract slideshow name (everything before _slide_)
                    parts = filename.rsplit('_slide_', 1)
                    if len(parts) == 2:
                        name = parts[0]
                        if name not in slideshows:
                            slideshows[name] = []
                        slideshows[name].append(path)
                
                # Display each slideshow
                for name, paths in slideshows.items():
                    with st.expander(f"📂 {name} ({len(paths)} slides)"):
                        cols = st.columns(min(4, len(paths)))
                        for i, path in enumerate(sorted(paths)):
                            with cols[i % 4]:
                                if os.path.exists(path):
                                    img = Image.open(path)
                                    st.image(img, caption=os.path.basename(path), use_container_width=True)
            else:
                st.info("No slideshows found. Generate one above!")
        else:
            st.info("Slideshow directory not found.")

# --- Tab 9: Production History ---
with tab9:
    st.header("📊 Production History")
    st.markdown("View all generated content with full metadata, dates, models, and costs.")
    
    # Sub-tabs for different views
    history_tab1, history_tab2 = st.tabs(["📜 Logged Productions", "📁 Browse Slideshows"])
    
    # --- Tab 1: Logged Productions ---
    with history_tab1:
        # Try to import production history
        try:
            from production_history import get_production_history, ProductionRecord
            history = get_production_history()
            
            # Stats summary
            stats = history.get_stats()
            
            st.subheader("📈 Overview")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Productions", stats['total_productions'])
            with col2:
                st.metric("Total Slides", stats['total_slides'])
            with col3:
                st.metric("Emailed", stats['emailed_count'])
            with col4:
                st.metric("Total Cost", f"${stats['total_cost']:.2f}")
            
            # Breakdown by type
            st.subheader("📊 By Content Type")
            type_cols = st.columns(3)
            type_icons = {
                'slideshow': '🎴',
                'narration': '🎙️',
                'video_transitions': '🎬'
            }
            
            for i, (content_type, count) in enumerate(stats.get('by_type', {}).items()):
                with type_cols[i % 3]:
                    icon = type_icons.get(content_type, '📁')
                    st.metric(f"{icon} {content_type.replace('_', ' ').title()}", count)
            
            # Cost tracking
            try:
                from daily_production import cost_tracker
                
                st.subheader("💰 Cost Tracking")
                today_total, today_by_cat = cost_tracker.get_today_costs()
                month_total, month_by_cat = cost_tracker.get_month_costs()
                
                cost_col1, cost_col2 = st.columns(2)
                with cost_col1:
                    st.markdown("**Today's Costs**")
                    st.metric("Total", f"${today_total:.2f}")
                    for cat, cost in today_by_cat.items():
                        st.caption(f"  {cat}: ${cost:.2f}")
                
                with cost_col2:
                    st.markdown("**This Month's Costs**")
                    st.metric("Total", f"${month_total:.2f}")
                    for cat, cost in month_by_cat.items():
                        st.caption(f"  {cat}: ${cost:.2f}")
            except Exception as e:
                st.caption(f"Cost tracking not available: {e}")
            
            st.divider()
            
            # Recent productions
            st.subheader("📜 Recent Productions")
            
            # Filter options
            filter_col1, filter_col2 = st.columns(2)
            with filter_col1:
                type_filter = st.selectbox(
                    "Filter by type",
                    ["All", "slideshow", "narration", "video_transitions"],
                    key="history_type_filter"
                )
            with filter_col2:
                model_filter = st.selectbox(
                    "Filter by model",
                    ["All"] + list(stats.get('by_model', {}).keys()),
                    key="history_model_filter"
                )
            
            # Get records
            records = history.get_all()
            
            # Apply filters
            if type_filter != "All":
                records = [r for r in records if r.content_type == type_filter]
            if model_filter != "All":
                records = [r for r in records if r.image_model == model_filter]
            
            if not records:
                st.info("No productions found. Run `python3 daily_production.py` to generate content.")
            else:
                for record in records[:50]:  # Limit to 50 most recent
                    # Determine icon
                    icon = type_icons.get(record.content_type, '📁')
                    status_icon = "✅" if record.status == "completed" else "📧" if record.emailed else "⏳"
                    
                    with st.expander(f"{icon} {record.title} - {record.date} {status_icon}"):
                        # Main info
                        info_col1, info_col2 = st.columns(2)
                        
                        with info_col1:
                            st.markdown(f"**Topic:** {record.topic}")
                            st.markdown(f"**Type:** {record.content_type.replace('_', ' ').title()}")
                            st.markdown(f"**Date:** {record.timestamp[:19]}")
                            st.markdown(f"**Slides:** {record.slides_count}")
                        
                        with info_col2:
                            st.markdown(f"**Model:** `{record.image_model}`")
                            st.markdown(f"**Font:** {record.font_name}")
                            st.markdown(f"**Style:** {record.visual_style}")
                            st.markdown(f"**Cost:** ${record.estimated_cost:.2f}")
                        
                        # Pipeline config
                        st.markdown("**Pipeline Configuration:**")
                        pipeline_parts = []
                        pipeline_parts.append(f"🎨 {record.image_model}")
                        if record.has_voice:
                            pipeline_parts.append("🎙️ Voice")
                        if record.has_video_transitions:
                            pipeline_parts.append("🎬 Video Transitions")
                        pipeline_parts.append(f"📝 {record.font_name} font")
                        st.code(" → ".join(pipeline_parts))
                        
                        # Status
                        if record.emailed:
                            st.success(f"📧 Emailed at: {record.email_sent_at}")
                        
                        # Output files
                        if record.output_files:
                            st.markdown(f"**Output Files:** {len(record.output_files)} files")
                            with st.container():
                                # Show preview of first few images
                                preview_files = [f for f in record.output_files if f.endswith('.png')][:4]
                                if preview_files:
                                    preview_cols = st.columns(len(preview_files))
                                    for i, path in enumerate(preview_files):
                                        with preview_cols[i]:
                                            if os.path.exists(path):
                                                try:
                                                    img = Image.open(path)
                                                    st.image(img, use_container_width=True)
                                                except:
                                                    st.caption(os.path.basename(path))
                        
                        # Video preview
                        if record.video_path and os.path.exists(record.video_path):
                            st.markdown("**Video:**")
                            st.video(record.video_path)
            
            st.divider()
            
            # Daily breakdown
            st.subheader("📅 Daily Breakdown")
            by_date = stats.get('by_date', {})
            if by_date:
                # Create a simple table
                date_data = []
                for date, info in sorted(by_date.items(), reverse=True)[:14]:  # Last 14 days
                    date_data.append({
                        'Date': date,
                        'Productions': info['count'],
                        'Cost': f"${info['cost']:.2f}"
                    })
                
                if date_data:
                    import pandas as pd
                    df = pd.DataFrame(date_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No daily data available yet.")
            
            # Refresh button
            if st.button("🔄 Refresh History"):
                st.rerun()
                
        except ImportError as e:
            st.warning(f"Production history module not available: {e}")
            st.info("Run `python3 daily_production.py` to start generating content with history tracking.")
    
    # --- Tab 2: Browse All Slideshows ---
    with history_tab2:
        st.subheader("📁 Browse Generated Slideshows")
        st.markdown("View all slideshows in the `generated_slideshows/` directory, including those not logged.")
        
        # Scan for slideshows
        slideshow_base = "generated_slideshows"
        
        # Get all subdirectories and organize by folder
        slideshow_folders = {
            "gpt15": "GPT Image 1.5 (Best Quality)",
            "flux": "Flux Schnell (Fast)",
            "root": "Main Folder"
        }
        
        # Folder selector
        available_folders = ["All"]
        if os.path.exists(os.path.join(slideshow_base, "gpt15")):
            available_folders.append("gpt15")
        if os.path.exists(os.path.join(slideshow_base, "flux")):
            available_folders.append("flux")
        available_folders.append("root")
        
        folder_filter = st.selectbox(
            "Filter by folder",
            available_folders,
            key="slideshow_folder_filter"
        )
        
        # Collect all slideshows
        all_slideshows = {}  # title -> {slides: [], folder: str, script: path}
        
        def scan_folder(folder_path, folder_name):
            """Scan a folder for slideshow slides and group by title."""
            if not os.path.exists(folder_path):
                return
            
            for filename in os.listdir(folder_path):
                if filename.endswith('_slide_0.png'):
                    # Extract title from filename
                    title = filename.replace('_slide_0.png', '')
                    
                    # Find all slides for this title
                    slides = []
                    for i in range(20):  # Max 20 slides
                        slide_path = os.path.join(folder_path, f"{title}_slide_{i}.png")
                        if os.path.exists(slide_path):
                            slides.append(slide_path)
                        else:
                            break
                    
                    # Find script if exists
                    script_path = os.path.join(folder_path, f"{title}_script.json")
                    
                    if slides:
                        all_slideshows[f"{folder_name}/{title}"] = {
                            'title': title.replace('_', ' '),
                            'slides': slides,
                            'folder': folder_name,
                            'folder_label': slideshow_folders.get(folder_name, folder_name),
                            'script_path': script_path if os.path.exists(script_path) else None,
                            'slide_count': len(slides)
                        }
        
        # Scan folders
        if folder_filter in ["All", "gpt15"]:
            scan_folder(os.path.join(slideshow_base, "gpt15"), "gpt15")
        if folder_filter in ["All", "flux"]:
            scan_folder(os.path.join(slideshow_base, "flux"), "flux")
        if folder_filter in ["All", "root"]:
            scan_folder(slideshow_base, "root")
        
        if not all_slideshows:
            st.info("No slideshows found. Generate some using Tab 8: TikTok Slideshow.")
        else:
            st.success(f"Found {len(all_slideshows)} slideshows")
            
            # Display slideshows
            for key, slideshow in sorted(all_slideshows.items(), reverse=True):
                folder_badge = f"🟢 {slideshow['folder']}" if slideshow['folder'] == 'gpt15' else f"🟡 {slideshow['folder']}"
                
                with st.expander(f"🎴 {slideshow['title']} ({slideshow['slide_count']} slides) - {folder_badge}"):
                    st.markdown(f"**Folder:** {slideshow['folder_label']}")
                    st.markdown(f"**Slides:** {slideshow['slide_count']}")
                    
                    # Show script info if available
                    if slideshow['script_path']:
                        try:
                            with open(slideshow['script_path'], 'r') as f:
                                script_data = json.load(f)
                            st.markdown(f"**Topic:** {script_data.get('topic', 'N/A')}")
                            if 'slides' in script_data:
                                st.markdown(f"**Script slides:** {len(script_data['slides'])}")
                        except:
                            pass
                    
                    # Show all slides
                    st.markdown("**Slides:**")
                    
                    # Show slides in a grid (3 columns)
                    cols_per_row = 3
                    for row_start in range(0, len(slideshow['slides']), cols_per_row):
                        cols = st.columns(cols_per_row)
                        for col_idx, slide_idx in enumerate(range(row_start, min(row_start + cols_per_row, len(slideshow['slides'])))):
                            slide_path = slideshow['slides'][slide_idx]
                            with cols[col_idx]:
                                try:
                                    img = Image.open(slide_path)
                                    st.image(img, caption=f"Slide {slide_idx}", use_container_width=True)
                                except Exception as e:
                                    st.error(f"Error loading slide {slide_idx}: {e}")
                    
                    # Show backgrounds if they exist
                    bg_folder = os.path.join(os.path.dirname(slideshow['slides'][0]), "backgrounds")
                    if not os.path.exists(bg_folder):
                        bg_folder = os.path.join(slideshow_base, "backgrounds")
                    
                    title_prefix = slideshow['title'].replace(' ', '_')
                    bg_files = []
                    if os.path.exists(bg_folder):
                        for f in os.listdir(bg_folder):
                            if f.startswith(title_prefix) and f.endswith('.png'):
                                bg_files.append(os.path.join(bg_folder, f))
                    
                    if bg_files:
                        with st.expander(f"🎨 View Backgrounds ({len(bg_files)})"):
                            bg_cols_per_row = 4
                            for row_start in range(0, len(bg_files), bg_cols_per_row):
                                cols = st.columns(bg_cols_per_row)
                                for col_idx, bg_idx in enumerate(range(row_start, min(row_start + bg_cols_per_row, len(bg_files)))):
                                    bg_path = bg_files[bg_idx]
                                    with cols[col_idx]:
                                        try:
                                            img = Image.open(bg_path)
                                            st.image(img, caption=os.path.basename(bg_path), use_container_width=True)
                                        except:
                                            pass
        
        # Refresh button
        if st.button("🔄 Refresh Slideshows", key="refresh_slideshows"):
            st.rerun()

