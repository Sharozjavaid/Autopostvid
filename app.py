import streamlit as st
import json
import os
from gemini_handler import GeminiHandler
from smart_image_generator import SmartImageGenerator
from PIL import Image

from voice_generator import VoiceGenerator
from video_assembler import VideoAssembler
from tiktok_uploader import TikTokUploader

import glob

# Ensure directories exist
os.makedirs("generated_scripts", exist_ok=True)
os.makedirs("generated_images", exist_ok=True)

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
    
    # Check for both 'nano' and 'enhanced' images
    # Pattern: {title}_scene_{num}_{type}.png
    for scene in story_data.get('scenes', []):
        scene_num = scene.get('scene_number')
        
        # Look for existing files
        nano_path = f"generated_images/{safe_title}_scene_{scene_num}_nano.png"
        enhanced_path = f"generated_images/{safe_title}_scene_{scene_num}_enhanced.png"
        
        print(f"DEBUG: Checking {nano_path}")
        
        if os.path.exists(nano_path):
            found_images[f"image_{scene_num}"] = nano_path
            print(f"DEBUG: Found {nano_path}")
        elif os.path.exists(enhanced_path):
            found_images[f"image_{scene_num}"] = enhanced_path
            print(f"DEBUG: Found {enhanced_path}")
            
    return found_images

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

st.set_page_config(layout="wide", page_title="Philosophy Video Generator")

st.title("Philosophy Video Generator")

# Sidebar for configuration and loading
with st.sidebar:
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
                    
                    st.success(f"Loaded {os.path.basename(selected_file)}!")
                    # Force rerun to update UI immediately
                    st.rerun()
            except Exception as e:
                print(f"DEBUG: General Error: {e}")
                st.error(f"Error loading file: {e}")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["1. Story Generation", "2. Image Generation", "3. Audio & Video", "4. Automation Dashboard"])

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
        st.subheader(f"Title: {st.session_state.story_data.get('title', topic)}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Script")
            st.text_area("Script Content", st.session_state.story_data.get('script', ''), height=400)
            
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
        # Style controls
        st.subheader("Global Style Settings")
        global_style = st.text_area("Base Style Prompt (applied to all)", 
                                  "Classical Old Master painting style, Caravaggio and Rembrandt influences, dramatic chiaroscuro lighting, deep shadows, golden highlights, oil on canvas texture, realistic human figures, 8k resolution")
        
        # Iterate through scenes

        
        # Batch Generation Button
        if st.button("🚀 Generate All Images (Batch)"):
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
                
                # Construct prompt
                scene_desc = scene.get('visual_description', '')
                scene_concept = scene.get('key_concept', '')
                # Use stored prompt if edited, else default
                prompt_key = f"prompt_{idx_num}"
                if prompt_key in st.session_state:
                    final_prompt = st.session_state[prompt_key]
                else:
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
            status_text.success("🎉 All images generated!")
            st.rerun()

        # Iterate through scenes
        for i, scene in enumerate(st.session_state.scenes):
            scene_num = scene.get('scene_number', i+1)
            
            with st.expander(f"Scene {scene_num}: {scene.get('key_concept', 'Concept')}", expanded=(i==0)):
                col_text, col_img = st.columns([1, 1])
                
                with col_text:
                    st.markdown(f"**Visual Description:** {scene.get('visual_description', '')}")
                    st.markdown(f"**Script:** _{scene.get('text', '')}_")
                    
                    # specific prompt for this scene
                    default_prompt = f"{global_style}, {scene.get('visual_description', '')}, {scene.get('key_concept', '')}"
                    
                    # Allow user to edit the FULL prompt for this scene
                    prompt_key = f"prompt_{scene_num}"
                    if prompt_key not in st.session_state:
                        st.session_state[prompt_key] = default_prompt
                        
                    user_prompt = st.text_area("Image Prompt", st.session_state[prompt_key], key=f"text_{scene_num}", height=150)
                    st.session_state[prompt_key] = user_prompt
                    
                    if st.button(f"Generate Image for Scene {scene_num}", key=f"btn_{scene_num}"):
                        with st.spinner("Generating..."):
                            # Call the generator
                            # We need to modify SmartImageGenerator to accept a direct prompt if possible, or just use the method we have
                            # Ideally we refactor `generate_image_with_nano` to take a raw string
                            
                            # Let's use the existing method but pass the prompt
                            # We might need to tweak `smart_image_generator.py` to allow passing the FULL prompt directly 
                            # instead of it constructing one.
                            # For now, let's assume we will pass it as the 'prompt' argument to `generate_image_with_nano`
                            story_title = st.session_state.story_data.get('title', 'Story')
                            # Pass user_prompt as prompt_override
                            image_path = st.session_state.image_generator.generate_image_with_nano(
                                prompt=user_prompt, # pass as primary prompt too just in case
                                scene_number=scene_num, 
                                story_title=story_title,
                                prompt_override=user_prompt
                            )
                            
                            # Store the result
                            img_key = f"image_{scene_num}"
                            st.session_state[img_key] = image_path
                            
                            if "enhanced" in image_path:
                                st.warning("⚠️ Generation failed, fell back to placeholder. Check console logs.")
                            else:
                                st.success("Image generated successfully!")

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
                    with st.spinner("Assembling video... this might take a minute..."):
                        video_path = st.session_state.video_assembler.create_philosophy_video(
                            scenes=scenes,
                            audio_path=st.session_state.audio_path,
                            image_paths=image_paths,
                            story_title=st.session_state.story_data.get('title', 'Philosophy Story')
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

# --- Tab 4: Automation Dashboard ---
with tab4:
    st.header("🤖 Automation Dashboard")
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

