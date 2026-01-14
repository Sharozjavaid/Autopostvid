"""TikTok posting service for automations.

Handles posting photo slideshows to TikTok using the Content Posting API.
Uses PULL_FROM_URL method to fetch images from our server.
"""
import os
import json
import logging
import requests
from pathlib import Path
from typing import List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Project root for token files
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
TOKEN_FILE = PROJECT_ROOT / ".tiktok_tokens.json"

# TikTok API endpoints
PHOTO_INIT_URL = "https://open.tiktokapis.com/v2/post/publish/content/init/"
STATUS_URL = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"

# Base URL for serving images (from api.cofndrly.com)
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.cofndrly.com")


class TikTokPoster:
    """Posts content to TikTok via the Content Posting API."""
    
    def __init__(self):
        self.tokens = self._load_tokens()
    
    def _load_tokens(self) -> Optional[dict]:
        """Load TikTok tokens from file."""
        if TOKEN_FILE.exists():
            with open(TOKEN_FILE) as f:
                return json.load(f)
        return None
    
    def is_authenticated(self) -> bool:
        """Check if we have valid tokens."""
        return bool(self.tokens and self.tokens.get("access_token"))
    
    def _get_image_url(self, image_path: str) -> str:
        """Convert local image path to public URL.
        
        Image paths look like:
        - generated_slideshows/gpt15/Topic_Name_gpt15_slide_0.png
        - /full/path/to/generated_slideshows/gpt15/Topic_Name_gpt15_slide_0.png
        
        We need to serve these from our static files endpoint.
        """
        # Extract just the filename
        filename = Path(image_path).name
        
        # Check if it's in generated_slideshows or generated_images
        if "slideshow" in image_path.lower() or "gpt15" in image_path or "flux" in image_path:
            return f"{API_BASE_URL}/static/slides/{filename}"
        else:
            return f"{API_BASE_URL}/static/images/{filename}"
    
    def post_photo_slideshow(
        self,
        image_paths: List[str],
        caption: str,
        to_drafts: bool = True,
        photo_cover_index: int = 0,
        post_mode: str = "DIRECT_POST"
    ) -> dict:
        """Post a photo slideshow to TikTok.
        
        Args:
            image_paths: List of local image paths (will be converted to URLs)
            caption: Caption/title for the post
            to_drafts: If True, post to drafts. If False, publish immediately.
            photo_cover_index: Which image to use as cover (0-indexed)
            post_mode: DIRECT_POST or MEDIA_UPLOAD
        
        Returns:
            dict with success status and publish_id or error
        """
        if not self.is_authenticated():
            return {"success": False, "error": "Not authenticated with TikTok"}
        
        if len(image_paths) < 2:
            return {"success": False, "error": "Need at least 2 images for slideshow"}
        
        if len(image_paths) > 35:
            return {"success": False, "error": "Maximum 35 images allowed"}
        
        # Convert local paths to public URLs
        image_urls = [self._get_image_url(path) for path in image_paths]
        
        logger.info(f"Posting {len(image_urls)} images to TikTok")
        logger.debug(f"Image URLs: {image_urls}")
        
        # Build photo images array
        photo_images = [{"image_url": url} for url in image_urls]
        
        # Build request payload
        payload = {
            "post_info": {
                "title": caption[:150],  # TikTok limits title length
                "privacy_level": "SELF_ONLY" if to_drafts else "PUBLIC_TO_EVERYONE",
                "disable_comment": False,
                "auto_add_music": True,
                "photo_cover_index": photo_cover_index
            },
            "source_info": {
                "source": "PULL_FROM_URL",
                "photo_cover_index": photo_cover_index,
                "photo_images": photo_images
            },
            "post_mode": post_mode
        }
        
        headers = {
            "Authorization": f"Bearer {self.tokens['access_token']}",
            "Content-Type": "application/json; charset=UTF-8"
        }
        
        try:
            response = requests.post(PHOTO_INIT_URL, headers=headers, json=payload)
            result = response.json()
            
            logger.info(f"TikTok API response: {result}")
            
            # Check for errors
            error = result.get("error", {})
            if error and error.get("code") != "ok":
                error_code = error.get("code", "unknown")
                error_msg = error.get("message", "Unknown error")
                logger.error(f"TikTok error: {error_code} - {error_msg}")
                return {
                    "success": False,
                    "error": f"{error_code}: {error_msg}",
                    "raw_response": result
                }
            
            # Success
            data = result.get("data", {})
            publish_id = data.get("publish_id")
            
            if publish_id:
                logger.info(f"Successfully initiated post: {publish_id}")
                return {
                    "success": True,
                    "publish_id": publish_id,
                    "status": "processing",
                    "image_count": len(image_urls)
                }
            else:
                return {
                    "success": False,
                    "error": "No publish_id in response",
                    "raw_response": result
                }
            
        except requests.RequestException as e:
            logger.exception(f"Request error: {e}")
            return {"success": False, "error": f"Request failed: {str(e)}"}
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            return {"success": False, "error": str(e)}
    
    def check_post_status(self, publish_id: str) -> dict:
        """Check the status of a pending post.
        
        Returns:
            dict with status info
        """
        if not self.is_authenticated():
            return {"success": False, "error": "Not authenticated"}
        
        headers = {
            "Authorization": f"Bearer {self.tokens['access_token']}",
            "Content-Type": "application/json; charset=UTF-8"
        }
        
        payload = {"publish_id": publish_id}
        
        try:
            response = requests.post(STATUS_URL, headers=headers, json=payload)
            result = response.json()
            
            error = result.get("error", {})
            if error and error.get("code") != "ok":
                return {
                    "success": False,
                    "error": f"{error.get('code')}: {error.get('message')}"
                }
            
            data = result.get("data", {})
            return {
                "success": True,
                "status": data.get("status"),
                "publicaly_available_post_id": data.get("publicaly_available_post_id"),
                "uploaded_bytes": data.get("uploaded_bytes"),
                "fail_reason": data.get("fail_reason")
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def refresh_tokens(self) -> bool:
        """Refresh TikTok access token."""
        if not self.tokens or not self.tokens.get("refresh_token"):
            return False
        
        from dotenv import load_dotenv
        load_dotenv(PROJECT_ROOT / ".env")
        
        client_key = os.getenv("TIKTOK_CLIENT_KEY")
        client_secret = os.getenv("TIKTOK_CLIENT_SECRET")
        
        if not client_key or not client_secret:
            logger.error("TikTok client credentials not configured")
            return False
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Cache-Control": "no-cache"
        }
        
        data = {
            "client_key": client_key,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
            "refresh_token": self.tokens["refresh_token"]
        }
        
        try:
            response = requests.post(
                "https://open.tiktokapis.com/v2/oauth/token/",
                headers=headers,
                data=data
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if "error" in result:
                    logger.error(f"Token refresh failed: {result}")
                    return False
                
                self.tokens["access_token"] = result.get("access_token", self.tokens["access_token"])
                self.tokens["refresh_token"] = result.get("refresh_token", self.tokens["refresh_token"])
                self.tokens["expires_in"] = result.get("expires_in")
                self.tokens["refreshed_at"] = datetime.now().isoformat()
                
                # Save updated tokens
                with open(TOKEN_FILE, 'w') as f:
                    json.dump(self.tokens, f, indent=2)
                
                logger.info("TikTok tokens refreshed successfully")
                return True
            else:
                logger.error(f"Token refresh failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.exception(f"Token refresh error: {e}")
            return False
