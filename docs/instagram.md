# Instagram Integration Documentation (Post Bridge API)

Instagram posting uses **Post Bridge** (https://post-bridge.com) - a service that simplifies social media posting without complex OAuth flows.

## Configuration
- **API Key**: `pb_live_RP1nqdE71wi7Fki6iVziL1`
- **Instagram Username**: `philosophizeme_app`
- **Account ID**: `41667` (in Post Bridge)
- **Dashboard**: https://post-bridge.com/dashboard

## API Flow
1. Get social accounts: `GET /v1/social-accounts?platform=instagram`
2. Upload media: `POST /v1/media/create-upload-url` → PUT to signed URL
3. Create post: `POST /v1/posts` with `social_accounts: [account_id]` and `media: [media_ids]`

## Key Backend Files
- `backend/app/services/instagram_poster.py` - Main Instagram posting service
- `backend/app/services/agent_tools.py` - Agent's Instagram tools
- `instagram_cli.py` - CLI for manual testing and posting

## Instagram CLI Commands

```bash
# Check Post Bridge connection
python3 instagram_cli.py status

# Post existing images as carousel
python3 instagram_cli.py post --images "img1.png,img2.png" --caption "Caption here"

# Generate slideshow and post to Instagram
python3 instagram_cli.py generate --topic "5 Stoic lessons" --theme oil_contrast --post

# Check post status
python3 instagram_cli.py check --post-id "YOUR_POST_ID"
```

## Agent Tools for Instagram
- `check_instagram_status` - Check if Instagram is connected
- `post_slideshow_to_instagram` - Post project slides as carousel
- `get_instagram_post_status` - Check post status and get URL

## Important Notes
- Posts go directly to Instagram (not drafts like TikTok)
- Maximum 10 images per carousel
- Local files are uploaded to Post Bridge automatically
- PNG format works (unlike TikTok which requires JPEG)
