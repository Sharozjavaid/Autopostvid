"""TikTok OAuth and Content Posting API router."""
import os
import io
import json
import secrets
import hashlib
import base64
import uuid
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from pydantic import BaseModel
from dotenv import load_dotenv
from PIL import Image

from ..config import get_settings

settings = get_settings()

# Load .env file from project root
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path)

router = APIRouter()
public_router = APIRouter()  # Public router for TikTok media - no auth required

# Token storage path
TOKEN_FILE = Path(__file__).parent.parent.parent.parent / ".tiktok_tokens.json"
PKCE_FILE = Path(__file__).parent.parent.parent.parent / ".tiktok_pkce.json"

# TikTok API endpoints
AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
INBOX_INIT_URL = "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/"
PUBLISH_INIT_URL = "https://open.tiktokapis.com/v2/post/publish/video/init/"
STATUS_URL = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"


def get_tiktok_config():
    """Get TikTok credentials from environment."""
    return {
        "client_key": os.getenv("TIKTOK_CLIENT_KEY"),
        "client_secret": os.getenv("TIKTOK_CLIENT_SECRET"),
        "redirect_uri": os.getenv("TIKTOK_REDIRECT_URI", "http://localhost:8001/api/tiktok/callback")
    }


def generate_pkce_pair():
    """Generate PKCE code_verifier and code_challenge."""
    code_verifier = secrets.token_urlsafe(32)
    m = hashlib.sha256()
    m.update(code_verifier.encode('ascii'))
    d = m.digest()
    code_challenge = base64.urlsafe_b64encode(d).decode('ascii').rstrip('=')
    return code_verifier, code_challenge


def save_pkce(code_verifier: str):
    """Save PKCE verifier."""
    with open(PKCE_FILE, 'w') as f:
        json.dump({"code_verifier": code_verifier, "timestamp": datetime.now().isoformat()}, f)


def load_pkce() -> Optional[str]:
    """Load PKCE verifier."""
    if PKCE_FILE.exists():
        with open(PKCE_FILE) as f:
            return json.load(f).get("code_verifier")
    return None


def save_tokens(token_data: dict):
    """Save tokens to file."""
    token_data["saved_at"] = datetime.now().isoformat()
    with open(TOKEN_FILE, 'w') as f:
        json.dump(token_data, f, indent=2)


def load_tokens() -> Optional[dict]:
    """Load tokens from file."""
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE) as f:
            return json.load(f)
    return None


class UploadRequest(BaseModel):
    video_path: str
    title: str = ""
    to_inbox: bool = True


class TokenResponse(BaseModel):
    has_tokens: bool
    open_id: Optional[str] = None
    scope: Optional[str] = None
    expires_in: Optional[int] = None


@router.get("/status")
async def get_tiktok_status():
    """Check TikTok connection status."""
    config = get_tiktok_config()
    tokens = load_tokens()
    
    return {
        "configured": bool(config["client_key"] and config["client_secret"]),
        "authenticated": bool(tokens and tokens.get("access_token")),
        "client_key": config["client_key"][:10] + "..." if config["client_key"] else None,
        "redirect_uri": config["redirect_uri"],
        "open_id": tokens.get("open_id") if tokens else None,
        "scope": tokens.get("scope") if tokens else None
    }


@router.get("/auth")
async def start_auth(request: Request):
    """Start TikTok OAuth flow - redirects to TikTok."""
    config = get_tiktok_config()
    
    if not config["client_key"]:
        raise HTTPException(status_code=400, detail="TikTok client key not configured")
    
    code_verifier, code_challenge = generate_pkce_pair()
    save_pkce(code_verifier)
    
    csrf_state = secrets.token_urlsafe(16)
    
    # Use request to build redirect URI if not set
    if not config["redirect_uri"] or config["redirect_uri"] == "http://localhost:8001/api/tiktok/callback":
        # Try to detect the actual host
        host = request.headers.get("host", "localhost:8001")
        scheme = request.headers.get("x-forwarded-proto", "http")
        config["redirect_uri"] = f"{scheme}://{host}/api/tiktok/callback"
    
    params = {
        "client_key": config["client_key"],
        "scope": "user.info.basic,video.upload,video.publish",
        "response_type": "code",
        "redirect_uri": config["redirect_uri"],
        "state": csrf_state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256"
    }
    
    param_str = "&".join(f"{k}={v}" for k, v in params.items())
    auth_url = f"{AUTH_URL}?{param_str}"
    
    return RedirectResponse(url=auth_url)


@router.get("/auth-url")
async def get_auth_url(request: Request):
    """Get TikTok auth URL without redirecting."""
    config = get_tiktok_config()
    
    if not config["client_key"]:
        raise HTTPException(status_code=400, detail="TikTok client key not configured")
    
    code_verifier, code_challenge = generate_pkce_pair()
    save_pkce(code_verifier)
    
    csrf_state = secrets.token_urlsafe(16)
    
    # Build redirect URI from request if needed
    host = request.headers.get("host", "localhost:8001")
    scheme = request.headers.get("x-forwarded-proto", "http")
    redirect_uri = config["redirect_uri"] or f"{scheme}://{host}/api/tiktok/callback"
    
    params = {
        "client_key": config["client_key"],
        "scope": "user.info.basic,video.upload,video.publish",
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "state": csrf_state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256"
    }
    
    param_str = "&".join(f"{k}={v}" for k, v in params.items())
    auth_url = f"{AUTH_URL}?{param_str}"
    
    return {
        "auth_url": auth_url,
        "redirect_uri": redirect_uri,
        "state": csrf_state
    }


@router.get("/callback", response_class=HTMLResponse)
async def oauth_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None)
):
    """Handle TikTok OAuth callback."""
    
    if error:
        return f"""
        <html>
        <head><title>TikTok Auth Error</title></head>
        <body style="font-family: Arial; padding: 40px; background: #1a1a2e; color: #eee;">
            <h1 style="color: #ff6b6b;">❌ Authorization Failed</h1>
            <p>Error: {error}</p>
            <p>{error_description or ''}</p>
            <a href="/" style="color: #00f5d4;">← Back to Dashboard</a>
        </body>
        </html>
        """
    
    if not code:
        return """
        <html>
        <head><title>TikTok Callback</title></head>
        <body style="font-family: Arial; padding: 40px; background: #1a1a2e; color: #eee;">
            <h1>Missing authorization code</h1>
            <a href="/" style="color: #00f5d4;">← Back to Dashboard</a>
        </body>
        </html>
        """
    
    # Exchange code for token
    config = get_tiktok_config()
    code_verifier = load_pkce()
    
    if not code_verifier:
        return """
        <html>
        <head><title>TikTok Auth Error</title></head>
        <body style="font-family: Arial; padding: 40px; background: #1a1a2e; color: #eee;">
            <h1 style="color: #ff6b6b;">❌ Session Expired</h1>
            <p>PKCE verifier not found. Please start the auth flow again.</p>
            <a href="/api/tiktok/auth" style="color: #00f5d4;">Try Again</a>
        </body>
        </html>
        """
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Cache-Control": "no-cache"
    }
    
    data = {
        "client_key": config["client_key"],
        "client_secret": config["client_secret"],
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": config["redirect_uri"],
        "code_verifier": code_verifier
    }
    
    response = requests.post(TOKEN_URL, headers=headers, data=data)
    
    if response.status_code == 200:
        result = response.json()
        
        if "error" in result:
            error_msg = result.get("error")
            error_desc = result.get("error_description", "")
            return f"""
            <html>
            <head><title>TikTok Auth Error</title></head>
            <body style="font-family: Arial; padding: 40px; background: #1a1a2e; color: #eee;">
                <h1 style="color: #ff6b6b;">❌ Token Exchange Failed</h1>
                <p>Error: {error_msg}</p>
                <p>{error_desc}</p>
                <a href="/api/tiktok/auth" style="color: #00f5d4;">Try Again</a>
            </body>
            </html>
            """
        
        # Save tokens
        token_data = {
            "access_token": result.get("access_token"),
            "refresh_token": result.get("refresh_token"),
            "open_id": result.get("open_id"),
            "scope": result.get("scope"),
            "expires_in": result.get("expires_in"),
            "refresh_expires_in": result.get("refresh_expires_in"),
            "token_type": result.get("token_type")
        }
        save_tokens(token_data)
        
        return f"""
        <html>
        <head>
            <title>TikTok Auth Success!</title>
            <script>
                // Notify parent window if in popup
                if (window.opener) {{
                    window.opener.postMessage({{ type: 'tiktok-auth-success' }}, '*');
                    window.close();
                }}
            </script>
        </head>
        <body style="font-family: Arial; padding: 40px; background: #1a1a2e; color: #eee; text-align: center;">
            <h1 style="color: #00f5d4;">✅ TikTok Connected!</h1>
            <p style="font-size: 1.2em;">Your TikTok account is now linked.</p>
            <div style="background: #16213e; padding: 20px; border-radius: 8px; margin: 20px auto; max-width: 400px;">
                <p><strong>Open ID:</strong> {token_data['open_id']}</p>
                <p><strong>Scope:</strong> {token_data['scope']}</p>
            </div>
            <p style="margin-top: 30px;">
                <a href="/" style="color: #00f5d4; font-size: 1.2em;">← Back to Dashboard</a>
            </p>
        </body>
        </html>
        """
    else:
        return f"""
        <html>
        <head><title>TikTok Auth Error</title></head>
        <body style="font-family: Arial; padding: 40px; background: #1a1a2e; color: #eee;">
            <h1 style="color: #ff6b6b;">❌ Request Failed</h1>
            <p>Status: {response.status_code}</p>
            <p>{response.text}</p>
            <a href="/api/tiktok/auth" style="color: #00f5d4;">Try Again</a>
        </body>
        </html>
        """


@router.post("/upload")
async def upload_video(req: UploadRequest):
    """Upload a video to TikTok drafts (inbox) or publish directly."""
    tokens = load_tokens()
    
    if not tokens or not tokens.get("access_token"):
        raise HTTPException(status_code=401, detail="Not authenticated. Please connect TikTok first.")
    
    video_path = Path(req.video_path)
    if not video_path.exists():
        raise HTTPException(status_code=404, detail=f"Video file not found: {req.video_path}")
    
    file_size = video_path.stat().st_size
    access_token = tokens["access_token"]
    
    # Choose endpoint
    init_url = INBOX_INIT_URL if req.to_inbox else PUBLISH_INIT_URL
    
    if req.to_inbox:
        init_data = {
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": file_size,
                "chunk_size": file_size,
                "total_chunk_count": 1
            }
        }
    else:
        init_data = {
            "post_info": {
                "title": req.title,
                "privacy_level": "SELF_ONLY",
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
                "video_cover_timestamp_ms": 1000
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": file_size,
                "chunk_size": file_size,
                "total_chunk_count": 1
            }
        }
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8"
    }
    
    # Step 1: Initialize upload
    init_response = requests.post(init_url, headers=headers, json=init_data)
    
    if init_response.status_code != 200:
        raise HTTPException(status_code=init_response.status_code, detail=f"Init failed: {init_response.text}")
    
    init_result = init_response.json()
    
    if "error" in init_result:
        error_info = init_result.get("error", {})
        if isinstance(error_info, dict) and error_info.get("code") != "ok":
            raise HTTPException(status_code=400, detail=f"API Error: {error_info}")
    
    data = init_result.get("data", {})
    upload_url = data.get("upload_url")
    publish_id = data.get("publish_id")
    
    if not upload_url:
        raise HTTPException(status_code=500, detail="No upload URL in response")
    
    # Step 2: Upload video file
    with open(video_path, 'rb') as f:
        video_data = f.read()
    
    upload_headers = {
        "Content-Type": "video/mp4",
        "Content-Length": str(file_size),
        "Content-Range": f"bytes 0-{file_size - 1}/{file_size}"
    }
    
    upload_response = requests.put(upload_url, headers=upload_headers, data=video_data)
    
    if upload_response.status_code not in [200, 201, 202]:
        raise HTTPException(status_code=upload_response.status_code, detail=f"Upload failed: {upload_response.text}")
    
    return {
        "status": "success",
        "publish_id": publish_id,
        "destination": "inbox" if req.to_inbox else "publish",
        "message": "Video uploaded to TikTok drafts!" if req.to_inbox else "Video published!"
    }


@router.get("/upload-status/{publish_id}")
async def get_upload_status(publish_id: str):
    """Check the status of a video upload."""
    tokens = load_tokens()
    
    if not tokens or not tokens.get("access_token"):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    headers = {
        "Authorization": f"Bearer {tokens['access_token']}",
        "Content-Type": "application/json; charset=UTF-8"
    }
    
    response = requests.post(STATUS_URL, headers=headers, json={"publish_id": publish_id})
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    
    return response.json()


@router.post("/refresh-token")
async def refresh_access_token():
    """Refresh the TikTok access token."""
    tokens = load_tokens()
    config = get_tiktok_config()
    
    if not tokens or not tokens.get("refresh_token"):
        raise HTTPException(status_code=401, detail="No refresh token available")
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Cache-Control": "no-cache"
    }
    
    data = {
        "client_key": config["client_key"],
        "client_secret": config["client_secret"],
        "grant_type": "refresh_token",
        "refresh_token": tokens["refresh_token"]
    }
    
    response = requests.post(TOKEN_URL, headers=headers, data=data)
    
    if response.status_code == 200:
        result = response.json()
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result)
        
        tokens["access_token"] = result.get("access_token", tokens["access_token"])
        tokens["refresh_token"] = result.get("refresh_token", tokens["refresh_token"])
        tokens["expires_in"] = result.get("expires_in")
        save_tokens(tokens)
        
        return {"status": "success", "message": "Token refreshed"}
    else:
        raise HTTPException(status_code=response.status_code, detail=response.text)


@router.delete("/disconnect")
async def disconnect_tiktok():
    """Remove TikTok connection (delete tokens)."""
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()
    if PKCE_FILE.exists():
        PKCE_FILE.unlink()
    return {"status": "success", "message": "TikTok disconnected"}


@public_router.get("/media/{image_id}")
async def serve_tiktok_media(image_id: str):
    """Serve TikTok media images from our verified domain.
    
    TikTok requires URL ownership verification for PULL_FROM_URL.
    Since api.cofndrly.com is verified, we serve images from here.
    
    URL format: /api/tiktok/media/{filename.jpg}
    Images are stored in: generated_tiktok_media/
    
    This endpoint is PUBLIC (no auth) so TikTok can fetch the images.
    """
    # Define media directory
    tiktok_media_dir = settings.base_dir / "generated_tiktok_media"
    
    # Security: prevent directory traversal
    if ".." in image_id or "/" in image_id or "\\" in image_id:
        raise HTTPException(status_code=400, detail="Invalid image ID")
    
    image_path = tiktok_media_dir / image_id
    
    if not image_path.exists():
        raise HTTPException(status_code=404, detail=f"Image not found: {image_id}")
    
    # Read and serve the image
    try:
        with open(image_path, "rb") as f:
            image_data = f.read()
        
        return Response(
            content=image_data,
            media_type="image/jpeg",
            headers={
                "Cache-Control": "public, max-age=86400",  # Cache for 1 day
                "Access-Control-Allow-Origin": "*"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read image: {str(e)}")


@router.post("/upload-media")
async def upload_tiktok_media(
    file: UploadFile = File(...),
    filename: Optional[str] = Form(None)
):
    """Upload an image for TikTok posting.
    
    This endpoint:
    1. Accepts image files (PNG, JPEG, etc.)
    2. Converts to JPEG (required by TikTok)
    3. Saves to generated_tiktok_media/ folder
    4. Returns the public URL that TikTok can access
    
    The returned URL is on our verified domain (api.cofndrly.com).
    """
    # Create media directory
    tiktok_media_dir = settings.base_dir / "generated_tiktok_media"
    tiktok_media_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Read the uploaded file
        contents = await file.read()
        
        # Open with PIL and convert to JPEG
        with Image.open(io.BytesIO(contents)) as img:
            # Convert to RGB if necessary (PNG might have alpha)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Generate unique filename
            base_name = filename or file.filename or "image"
            base_name = Path(base_name).stem  # Remove extension
            unique_id = uuid.uuid4().hex[:8]
            output_filename = f"{base_name}_{unique_id}.jpg"
            output_path = tiktok_media_dir / output_filename
            
            # Save as JPEG
            img.save(output_path, format='JPEG', quality=95)
        
        # Return the public URL
        # This will be accessible at https://api.cofndrly.com/api/tiktok/media/{filename}
        public_url = f"/api/tiktok/media/{output_filename}"
        
        return {
            "success": True,
            "filename": output_filename,
            "public_url": public_url,
            "full_url": f"https://api.cofndrly.com{public_url}"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process image: {str(e)}")
