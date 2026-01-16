# API Security Documentation

## Overview

The backend uses API key authentication to protect sensitive endpoints. All requests to protected endpoints MUST include the `X-API-Key` header.

**Security Stack:**
- **Authentication**: API Key via `X-API-Key` header
- **Rate Limiting**: slowapi with per-IP limits
- **Error Handling**: Generic errors in production (no stack traces)
- **Security Headers**: X-Frame-Options, X-Content-Type-Options, etc.
- **CORS**: Restricted to allowed origins only

## API Key Configuration

**Single Source of Truth:** `backend/app/config.py` → `api_key` setting

```python
# backend/app/config.py
class Settings(BaseSettings):
    api_key: str = ""  # Set in .env file
```

**Current API Key:** `b4TZ2d11ZDkXpDNU_V8m4KxyYdCdJMERKMyVvgyyYz0`

## Making Authenticated Requests

**Using curl:**
```bash
# Protected endpoint - requires API key
curl -H "X-API-Key: b4TZ2d11ZDkXpDNU_V8m4KxyYdCdJMERKMyVvgyyYz0" \
     https://api.cofndrly.com/api/automations

# Without API key - returns 401
curl https://api.cofndrly.com/api/automations
# Response: {"error": "Unauthorized"}
```

**Using fetch (JavaScript):**
```javascript
const response = await fetch('https://api.cofndrly.com/api/projects', {
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'b4TZ2d11ZDkXpDNU_V8m4KxyYdCdJMERKMyVvgyyYz0'
  }
});
```

**Frontend client (automatic):**
The `frontend/src/api/client.ts` automatically includes the API key from `VITE_API_KEY` environment variable.

## Public vs Protected Endpoints

| Endpoint | Auth Required | Rate Limit | Description |
|----------|---------------|------------|-------------|
| `GET /` | No | 100/min | Root health check |
| `GET /api/health` | No | 100/min | Health status |
| `GET /api/settings/models` | No | 100/min | Available fonts/themes |
| `GET /api/tiktok/media/*` | No | None | TikTok needs to fetch images |
| `* /api/projects/*` | **Yes** | 60/min | Project CRUD |
| `* /api/slides/*` | **Yes** | 60/min | Slide CRUD |
| `* /api/images/*` | **Yes** | 5/min | Image generation (heavy) |
| `* /api/automations/*` | **Yes** | 30/min | Automation management |
| `* /api/agent/*` | **Yes** | 20/min | AI agent chat |
| `* /api/gallery/*` | **Yes** | 60/min | Gallery CRUD |
| `* /api/tiktok/*` | **Yes** | 10/min | TikTok posting |
| `* /api/storage/*` | **Yes** | 30/min | Cloud storage info |

## SSE Streaming (Agent Chat)

EventSource doesn't support custom headers, so the agent streaming endpoint accepts API key as a query parameter:

```typescript
// Frontend sends API key via query param for SSE
const params = new URLSearchParams({ message });
params.append('api_key', API_KEY);  // Special case for SSE

const eventSource = new EventSource(
  `${API_BASE_URL}/api/agent/chat/stream?${params.toString()}`
);
```

## Security Middleware Files

```
backend/app/middleware/
├── __init__.py           # Exports all middleware
├── auth.py               # verify_api_key dependency
├── rate_limiter.py       # slowapi rate limiting
├── error_handler.py      # Global exception handling
└── security_headers.py   # Security response headers
```

## Security Headers Added

All responses include:
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
Cache-Control: no-store, max-age=0
```

## CORS Configuration

**Allowed Origins (backend/app/config.py):**
```python
cors_origins = [
    "http://localhost:5173",      # Vite dev server
    "http://127.0.0.1:5173",
    "https://app.cofndrly.com",   # Production frontend
]
```

**NOT allowed:** `*` wildcard, random domains

## Error Responses

**Production Mode (IS_PRODUCTION=True):**
```json
{"error": "Unauthorized"}           // 401
{"error": "Invalid request data"}   // 400
{"error": "Internal server error"}  // 500 (no details exposed)
```

**Development Mode (IS_PRODUCTION=False):**
```json
{
  "error": "Internal server error",
  "detail": "division by zero",
  "type": "ZeroDivisionError",
  "traceback": ["...last 5 lines..."]
}
```

## Deployment Checklist for Security

**GCP VM (Backend):**
1. Ensure `API_KEY` is set in `.env`
2. Install slowapi: `pip install slowapi`
3. Restart backend: `sudo systemctl restart philosophy-backend`

**Vercel (Frontend):**
1. Add `VITE_API_KEY` environment variable in Vercel dashboard
2. Value must match backend `API_KEY`
3. Redeploy to pick up new env var

## Generating a New API Key

```bash
# Generate a secure random key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Update both:
# 1. Backend .env: API_KEY=new-key-here
# 2. Frontend: VITE_API_KEY in Vercel dashboard
# 3. Restart/redeploy both services
```

## Testing Authentication

```bash
# Should return 401
curl -s https://api.cofndrly.com/api/projects
# {"error":"Unauthorized"}

# Should return 200 with data
curl -s -H "X-API-Key: YOUR_KEY" https://api.cofndrly.com/api/projects
# {"projects":[...],"total":5}

# Public endpoint (no key needed)
curl -s https://api.cofndrly.com/api/health
# {"status":"healthy"}
```
