"""Instagram posting service using Post Bridge API.

Posts photo slideshows (carousel) to Instagram via Post Bridge.
https://api.post-bridge.com/reference

Post Bridge simplifies Instagram posting - no OAuth needed, just an API key.

API Flow:
1. Get social accounts to find the Instagram account ID
2. Use media_urls for publicly accessible images (or upload via create-upload-url)
3. Create post with social_accounts array containing the account ID
"""
import os
import json
import logging
import requests
from pathlib import Path
from typing import List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Post Bridge API configuration
POST_BRIDGE_API_KEY = os.getenv("POST_BRIDGE_API_KEY", "pb_live_RP1nqdE71wi7Fki6iVziL1")
INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME", "philosophizeme_app")

# Post Bridge API endpoints
POST_BRIDGE_BASE_URL = "https://api.post-bridge.com/v1"

# Base URL for serving images (from api.cofndrly.com)
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.cofndrly.com")


class InstagramPoster:
    """Posts content to Instagram via Post Bridge API."""
    
    def __init__(self, api_key: str = None, username: str = None):
        """Initialize the Instagram poster.
        
        Args:
            api_key: Post Bridge API key (defaults to env var)
            username: Instagram username to post to (defaults to env var)
        """
        self.api_key = api_key or POST_BRIDGE_API_KEY
        self.username = username or INSTAGRAM_USERNAME
        self._account_id = None  # Cached account ID
        
        logger.info(f"InstagramPoster initialized for @{self.username}")
    
    def _get_headers(self) -> dict:
        """Get headers for Post Bridge API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def upload_media(self, file_path: str) -> Optional[str]:
        """Upload a media file to Post Bridge and return the media_id.
        
        Args:
            file_path: Path to the local file
        
        Returns:
            media_id string or None if upload failed
        """
        path = Path(file_path)
        if not path.exists():
            logger.error(f"File not found: {file_path}")
            return None
        
        # Get file info
        file_size = path.stat().st_size
        file_name = path.name
        
        # Determine MIME type
        ext = path.suffix.lower()
        mime_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".mp4": "video/mp4",
            ".mov": "video/quicktime"
        }
        mime_type = mime_types.get(ext, "image/png")
        
        try:
            # Step 1: Request upload URL
            create_url_payload = {
                "name": file_name,
                "mime_type": mime_type,
                "size_bytes": file_size
            }
            
            response = requests.post(
                f"{POST_BRIDGE_BASE_URL}/media/create-upload-url",
                headers=self._get_headers(),
                json=create_url_payload
            )
            
            if response.status_code not in (200, 201):
                logger.error(f"Failed to get upload URL: {response.status_code} - {response.text}")
                return None
            
            result = response.json()
            media_id = result.get("media_id")
            upload_url = result.get("upload_url")
            
            if not media_id or not upload_url:
                logger.error(f"Invalid upload URL response: {result}")
                return None
            
            logger.info(f"Got upload URL for {file_name}, media_id: {media_id}")
            
            # Step 2: Upload file to signed URL
            with open(file_path, "rb") as f:
                file_data = f.read()
            
            upload_response = requests.put(
                upload_url,
                headers={"Content-Type": mime_type},
                data=file_data
            )
            
            if upload_response.status_code not in (200, 201, 204):
                logger.error(f"Failed to upload file: {upload_response.status_code} - {upload_response.text}")
                return None
            
            logger.info(f"Uploaded {file_name} successfully")
            return media_id
            
        except Exception as e:
            logger.exception(f"Error uploading media: {e}")
            return None
    
    def upload_multiple_media(self, file_paths: List[str]) -> List[str]:
        """Upload multiple files and return list of media_ids.
        
        Args:
            file_paths: List of local file paths
        
        Returns:
            List of media_id strings (may be fewer than input if some failed)
        """
        media_ids = []
        for file_path in file_paths:
            media_id = self.upload_media(file_path)
            if media_id:
                media_ids.append(media_id)
            else:
                logger.warning(f"Failed to upload {file_path}, continuing with others")
        return media_ids
    
    def _get_image_url(self, image_path: str) -> str:
        """Convert local image path to public URL.
        
        Instagram accepts most image formats including PNG and JPEG.
        
        Image paths look like:
        - generated_slideshows/gpt15/Topic_Name_gpt15_slide_0.png
        - generated_images/topic_scene_1.png
        - /full/path/to/generated_slideshows/gpt15/Topic_Name_gpt15_slide_0.png
        
        URL structure:
        - /static/slideshows/gpt15/filename.png -> generated_slideshows/gpt15/
        - /static/slides/filename.png -> generated_slides/
        - /static/images/filename.png -> generated_images/
        """
        path = Path(image_path)
        filename = path.name
        
        # Check if it's already a URL
        if image_path.startswith("http://") or image_path.startswith("https://"):
            return image_path
        
        # Check if it's in generated_slideshows (automation-generated)
        if "generated_slideshow" in image_path.lower():
            # Preserve the model subfolder (gpt15, flux, etc.)
            parts = path.parts
            for i, part in enumerate(parts):
                if part == "generated_slideshows" and i + 1 < len(parts):
                    model = parts[i + 1]  # e.g., "gpt15"
                    return f"{API_BASE_URL}/static/slideshows/{model}/{filename}"
            # Fallback: just use gpt15
            return f"{API_BASE_URL}/static/slideshows/gpt15/{filename}"
        
        # Also check for direct model paths like "gpt15/" or "flux/"
        if "/gpt15/" in image_path or "/flux/" in image_path or "/dall-e/" in image_path:
            parts = path.parts
            for i, part in enumerate(parts):
                if part in ("gpt15", "flux", "dall-e", "nano"):
                    return f"{API_BASE_URL}/static/slideshows/{part}/{filename}"
        
        # Frontend project slides (from generated_slides/)
        if "generated_slides" in image_path.lower():
            return f"{API_BASE_URL}/static/slides/{filename}"
        
        # Default: generated_images
        return f"{API_BASE_URL}/static/images/{filename}"
    
    def get_social_accounts(self, platform: str = None) -> dict:
        """Get connected social accounts from Post Bridge.
        
        Args:
            platform: Optional filter by platform (instagram, tiktok, etc.)
        
        Returns:
            dict with accounts data or error
        """
        try:
            url = f"{POST_BRIDGE_BASE_URL}/social-accounts"
            params = {}
            if platform:
                params["platform"] = platform
            
            response = requests.get(url, headers=self._get_headers(), params=params)
            result = response.json() if response.text else {}
            
            if response.status_code == 200:
                accounts = result.get("data", [])
                return {
                    "success": True,
                    "accounts": accounts,
                    "total": result.get("meta", {}).get("total", len(accounts))
                }
            else:
                return {
                    "success": False,
                    "error": result.get("message", f"HTTP {response.status_code}"),
                    "raw_response": result
                }
                
        except Exception as e:
            logger.exception(f"Error getting social accounts: {e}")
            return {"success": False, "error": str(e)}
    
    def get_instagram_account_id(self) -> Optional[int]:
        """Get the Post Bridge account ID for the Instagram account.
        
        Returns:
            Account ID (int) or None if not found
        """
        if self._account_id:
            return self._account_id
        
        result = self.get_social_accounts(platform="instagram")
        if not result.get("success"):
            logger.error(f"Failed to get social accounts: {result.get('error')}")
            return None
        
        accounts = result.get("accounts", [])
        for account in accounts:
            if account.get("username") == self.username or account.get("platform") == "instagram":
                self._account_id = account.get("id")
                logger.info(f"Found Instagram account: @{account.get('username')} (ID: {self._account_id})")
                return self._account_id
        
        # If no exact match, use first Instagram account
        if accounts:
            self._account_id = accounts[0].get("id")
            logger.info(f"Using first Instagram account: @{accounts[0].get('username')} (ID: {self._account_id})")
            return self._account_id
        
        logger.error(f"No Instagram account found in Post Bridge")
        return None
    
    def check_connection(self) -> dict:
        """Check if Post Bridge connection is working and account is connected.
        
        Returns:
            dict with connection status info
        """
        result = self.get_social_accounts(platform="instagram")
        
        if result.get("success"):
            accounts = result.get("accounts", [])
            if accounts:
                account = accounts[0]  # Use first Instagram account
                self._account_id = account.get("id")
                return {
                    "success": True,
                    "username": account.get("username"),
                    "account_id": self._account_id,
                    "platform": account.get("platform"),
                    "connected": True,
                    "total_accounts": len(accounts)
                }
            else:
                return {
                    "success": False,
                    "error": "No Instagram accounts connected to Post Bridge",
                    "hint": "Connect your Instagram account at https://post-bridge.com/dashboard"
                }
        else:
            return result
    
    def post_carousel(
        self,
        image_paths: List[str],
        caption: str,
        hashtags: List[str] = None,
        upload_files: bool = True
    ) -> dict:
        """Post a carousel (slideshow) to Instagram.
        
        Args:
            image_paths: List of local image paths or URLs
            caption: Caption for the post
            hashtags: Optional list of hashtags (without #)
            upload_files: If True, upload local files to Post Bridge (recommended for local files)
        
        Returns:
            dict with success status and post info or error
        """
        if len(image_paths) < 2:
            return {"success": False, "error": "Need at least 2 images for carousel"}
        
        if len(image_paths) > 10:
            return {"success": False, "error": "Maximum 10 images allowed for Instagram carousel"}
        
        # Get Instagram account ID
        account_id = self.get_instagram_account_id()
        if not account_id:
            return {
                "success": False, 
                "error": "No Instagram account found in Post Bridge. Connect at https://post-bridge.com/dashboard"
            }
        
        # Build full caption with hashtags
        full_caption = caption
        if hashtags:
            hashtag_str = " ".join(f"#{tag}" for tag in hashtags)
            full_caption = f"{caption}\n\n{hashtag_str}"
        
        # Check if files are local and need uploading
        local_files = [p for p in image_paths if not p.startswith("http") and Path(p).exists()]
        
        if upload_files and local_files:
            # Upload local files to Post Bridge
            logger.info(f"Uploading {len(local_files)} local files to Post Bridge...")
            media_ids = self.upload_multiple_media(image_paths)
            
            if len(media_ids) < 2:
                return {
                    "success": False,
                    "error": f"Only {len(media_ids)} files uploaded successfully, need at least 2"
                }
            
            logger.info(f"Posting carousel with {len(media_ids)} uploaded images (account_id: {account_id})")
            
            # Build Post Bridge post payload with uploaded media
            payload = {
                "caption": full_caption[:2200],
                "media": media_ids,  # Use media IDs for uploaded files
                "social_accounts": [account_id]
            }
        else:
            # Use URLs directly (for publicly accessible images)
            image_urls = [self._get_image_url(path) for path in image_paths]
            logger.info(f"Posting carousel with {len(image_urls)} image URLs (account_id: {account_id})")
            logger.debug(f"Image URLs: {image_urls}")
            
            payload = {
                "caption": full_caption[:2200],
                "media_urls": image_urls,
                "social_accounts": [account_id]
            }
        
        logger.debug(f"Caption: {full_caption[:100]}...")
        
        try:
            response = requests.post(
                f"{POST_BRIDGE_BASE_URL}/posts",
                headers=self._get_headers(),
                json=payload
            )
            
            result = response.json() if response.text else {}
            logger.info(f"Post Bridge API response: {response.status_code} - {result}")
            
            if response.status_code in (200, 201, 202):
                post_id = result.get("id")
                return {
                    "success": True,
                    "post_id": post_id,
                    "status": result.get("status", "processing"),
                    "image_count": len(image_paths),
                    "message": f"Carousel with {len(image_paths)} images posted to Instagram!",
                    "raw_response": result
                }
            else:
                error_msg = result.get("error", result.get("message", f"HTTP {response.status_code}"))
                if isinstance(error_msg, list):
                    error_msg = ", ".join(error_msg)
                logger.error(f"Post Bridge error: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "status_code": response.status_code,
                    "raw_response": result
                }
                
        except requests.RequestException as e:
            logger.exception(f"Request error: {e}")
            return {"success": False, "error": f"Request failed: {str(e)}"}
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            return {"success": False, "error": str(e)}
    
    def post_single_image(
        self,
        image_path: str,
        caption: str,
        hashtags: List[str] = None
    ) -> dict:
        """Post a single image to Instagram.
        
        Args:
            image_path: Local image path (will be converted to URL)
            caption: Caption for the post
            hashtags: Optional list of hashtags (without #)
        
        Returns:
            dict with success status and post info or error
        """
        # Get Instagram account ID
        account_id = self.get_instagram_account_id()
        if not account_id:
            return {
                "success": False, 
                "error": "No Instagram account found in Post Bridge"
            }
        
        # Convert to public URL
        image_url = self._get_image_url(image_path)
        
        # Build full caption with hashtags
        full_caption = caption
        if hashtags:
            hashtag_str = " ".join(f"#{tag}" for tag in hashtags)
            full_caption = f"{caption}\n\n{hashtag_str}"
        
        logger.info(f"Posting single image to Instagram (account_id: {account_id})")
        
        payload = {
            "caption": full_caption[:2200],
            "media_urls": [image_url],
            "social_accounts": [account_id]
        }
        
        try:
            response = requests.post(
                f"{POST_BRIDGE_BASE_URL}/posts",
                headers=self._get_headers(),
                json=payload
            )
            
            result = response.json() if response.text else {}
            
            if response.status_code in (200, 201, 202):
                post_id = result.get("id")
                return {
                    "success": True,
                    "post_id": post_id,
                    "status": result.get("status", "processing"),
                    "message": f"Image posted to Instagram!",
                    "raw_response": result
                }
            else:
                error_msg = result.get("error", result.get("message", f"HTTP {response.status_code}"))
                if isinstance(error_msg, list):
                    error_msg = ", ".join(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "status_code": response.status_code,
                    "raw_response": result
                }
                
        except Exception as e:
            logger.exception(f"Error posting to Instagram: {e}")
            return {"success": False, "error": str(e)}
    
    def get_post_status(self, post_id: str) -> dict:
        """Check the status of a post.
        
        Args:
            post_id: The post ID from Post Bridge
        
        Returns:
            dict with status info
        """
        try:
            response = requests.get(
                f"{POST_BRIDGE_BASE_URL}/posts/{post_id}",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "post_id": post_id,
                    "status": result.get("status"),
                    "caption": result.get("caption"),
                    "created_at": result.get("created_at"),
                    "raw_response": result
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "response": response.text
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_post_results(self, post_id: str) -> dict:
        """Get the results of a post (success/failure per platform).
        
        Args:
            post_id: The post ID from Post Bridge
        
        Returns:
            dict with results info
        """
        try:
            response = requests.get(
                f"{POST_BRIDGE_BASE_URL}/post-results",
                headers=self._get_headers(),
                params={"post_id": post_id}
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "results": result.get("data", []),
                    "raw_response": result
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "response": response.text
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}


# Convenience function for quick posting
def post_slideshow_to_instagram(
    image_paths: List[str],
    caption: str,
    hashtags: List[str] = None,
    username: str = None
) -> dict:
    """Quick function to post a slideshow to Instagram.
    
    Args:
        image_paths: List of image paths
        caption: Post caption
        hashtags: Optional hashtags
        username: Instagram username (defaults to env var)
    
    Returns:
        dict with result
    """
    poster = InstagramPoster(username=username)
    return poster.post_carousel(image_paths, caption, hashtags)
