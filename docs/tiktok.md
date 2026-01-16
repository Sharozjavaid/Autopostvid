# TikTok Integration Documentation

## ⚠️ CRITICAL: ALL UPLOADS GO TO DRAFTS (USER'S INBOX)
- All TikTok uploads go to DRAFTS (user's inbox), never direct publish
- User's TikTok account can be PUBLIC - sandbox mode works with public accounts for drafts
- User completes and publishes the post from their TikTok app
- NEVER change code to post directly to TikTok feed

## Two Different Endpoints for Videos vs Photo Slideshows

| Content Type | Endpoint | How to Send to Drafts | Backend File |
|-------------|----------|----------------------|--------------|
| **Videos** | `/v2/post/publish/inbox/video/init/` | Use this endpoint directly (it's the inbox endpoint) | `tiktok_cli.py`, `agent_tools.py`, `routers/tiktok.py` |
| **Photo Slideshows** | `/v2/post/publish/content/init/` | Use `post_mode: "MEDIA_UPLOAD"` | `services/tiktok_poster.py` |

## Video Uploads to Drafts

```python
# Endpoint for videos -> drafts
INBOX_VIDEO_URL = "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/"

# Just use FILE_UPLOAD source, no post_mode needed
payload = {
    "source_info": {
        "source": "FILE_UPLOAD",
        "video_size": file_size,
        "chunk_size": file_size,
        "total_chunk_count": 1
    }
}
```

## Photo Slideshow Uploads to Drafts

```python
# Endpoint for photos (same endpoint, different mode)
PHOTO_CONTENT_URL = "https://open.tiktokapis.com/v2/post/publish/content/init/"

# CRITICAL: Use MEDIA_UPLOAD mode for drafts, NOT DIRECT_POST
payload = {
    "post_info": {
        "title": caption,
        "description": caption
    },
    "source_info": {
        "source": "PULL_FROM_URL",
        "photo_cover_index": 0,
        "photo_images": ["https://...jpg", "https://...jpg"]  # Must be JPEG/WebP!
    },
    "post_mode": "MEDIA_UPLOAD",  # ✅ Sends to drafts (works with public accounts)
    "media_type": "PHOTO"
}
# NEVER use "post_mode": "DIRECT_POST" - requires private account in sandbox
```

## Image Format for Photo Slideshows (CRITICAL)
- TikTok photo API only accepts **JPEG (.jpg)** or **WebP** format
- **PNG files will FAIL** with `file_format_check_failed` error
- Always generate/convert images to JPEG before posting to TikTok
- The `tiktok_poster.py` automatically converts paths to .jpg URLs

## Configuration
- **Redirect URI**: `https://api.cofndrly.com/api/tiktok/callback`
- **Domain Verification**: ✅ `api.cofndrly.com` is verified in TikTok Developer Portal
- **Scopes**: `user.info.basic`, `video.upload`, `video.publish`
- Tokens stored in `.tiktok_tokens.json` (gitignored)
- Access tokens expire in 24 hours, refresh tokens last 365 days
- Token refresh happens automatically in `tiktok_poster.py`

## Key Backend Files
- `backend/app/services/tiktok_poster.py` - Photo slideshow posting (MEDIA_UPLOAD mode)
- `backend/app/routers/tiktok.py` - Video upload endpoints
- `backend/app/services/agent_tools.py` - Agent's TikTok upload tool
- `tiktok_cli.py` - CLI for manual uploads and auth

## TikTok CLI Commands

```bash
# Start OAuth flow
python tiktok_cli.py auth

# Exchange code for tokens
python tiktok_cli.py token --code "YOUR_CODE"

# Refresh expired access token (uses refresh token)
python tiktok_cli.py refresh

# Upload video to drafts
python tiktok_cli.py upload --video "path/to/video.mp4" --title "Caption"

# Upload photo slideshow to drafts (images must be JPEG, not PNG!)
python tiktok_cli.py slideshow --images "img1.jpg,img2.jpg" --title "Caption"

# Check upload status
python tiktok_cli.py status --publish-id "PUBLISH_ID"

# View config and token status
python tiktok_cli.py info
```
