# DevOps Architecture - Philosophy Video Generator

## Infrastructure Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRODUCTION ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────┐         ┌─────────────────────────────────────┐        │
│  │   FRONTEND      │         │           GCP VM                     │        │
│  │   (Vercel)      │◄───────►│      philosophy-bot-vm               │        │
│  │                 │  HTTPS  │                                      │        │
│  │ app.cofndrly.com│         │  ┌──────────┐    ┌──────────────┐   │        │
│  └─────────────────┘         │  │  Nginx   │───►│   Uvicorn    │   │        │
│                              │  │  :443    │    │   :8001      │   │        │
│                              │  │          │    │   (FastAPI)  │   │        │
│                              │  └──────────┘    └──────────────┘   │        │
│                              │        │                 │          │        │
│                              │        │         ┌───────▼───────┐  │        │
│                              │        │         │   SQLite DB   │  │        │
│                              │        │         │ (philosophy   │  │        │
│                              │        │         │  _generator   │  │        │
│                              │        │         │  .db)         │  │        │
│                              │        │         └───────────────┘  │        │
│                              │        │                            │        │
│  ┌─────────────────┐         │  api.cofndrly.com                   │        │
│  │  Google Cloud   │◄────────┤  IP: 23.251.149.244                 │        │
│  │  Storage (GCS)  │         │  Zone: us-central1-a                │        │
│  │                 │         └─────────────────────────────────────┘        │
│  │ philosophy-     │                                                        │
│  │ content-storage │                                                        │
│  └─────────────────┘                                                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Frontend (Vercel)

| Property | Value |
|----------|-------|
| **URL** | https://app.cofndrly.com |
| **Platform** | Vercel |
| **Framework** | React + Vite + TypeScript |
| **Project** | `frontend` in `sharozs-projects-b7468887` |
| **Deployment** | Auto-deploys on `git push origin main` |

**Environment Variables (Vercel Dashboard):**
```
VITE_API_URL=https://api.cofndrly.com
VITE_API_KEY=b4TZ2d11ZDkXpDNU_V8m4KxyYdCdJMERKMyVvgyyYz0
```

**Commands:**
```bash
# Manual deploy
cd frontend && npx vercel --prod

# View deployments
npx vercel ls

# View logs
npx vercel logs <deployment-url>
```

### 2. Backend (GCP VM)

| Property | Value |
|----------|-------|
| **URL** | https://api.cofndrly.com |
| **VM Name** | `philosophy-bot-vm` |
| **Zone** | `us-central1-a` |
| **External IP** | `23.251.149.244` |
| **Code Path** | `/home/runner/philosophy_video_generator` |
| **User** | `runner` |

**Stack on VM:**
- **Nginx** - Reverse proxy + SSL termination
- **Uvicorn** - ASGI server running FastAPI
- **SQLite** - Database at `./philosophy_generator.db`
- **Python 3.10** - Runtime

**Environment File (`.env` on VM):**
```
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
ELEVENLABS_API_KEY=...
FAL_KEY=...
ANTHROPIC_API_KEY=...
API_KEY=b4TZ2d11ZDkXpDNU_V8m4KxyYdCdJMERKMyVvgyyYz0
```

### 3. Cloud Storage (GCS)

| Property | Value |
|----------|-------|
| **Bucket** | `philosophy-content-storage` |
| **URL Pattern** | `https://storage.googleapis.com/philosophy-content-storage/...` |
| **Credentials** | `gcs-credentials.json` (gitignored) |

**Folder Structure:**
```
philosophy-content-storage/
├── backgrounds/    # AI-generated background images
├── slides/         # Final slides with text overlay
├── scripts/        # Generated scripts
└── test/           # Test uploads
```

## SSH & VM Access

### Connecting to the VM

```bash
# SSH into VM
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a

# Run command on VM
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="<command>"

# Copy file TO VM
gcloud compute scp /local/path philosophy-bot-vm:/remote/path --zone=us-central1-a

# Copy file FROM VM
gcloud compute scp philosophy-bot-vm:/remote/path /local/path --zone=us-central1-a

# Copy directory
gcloud compute scp --recurse /local/dir philosophy-bot-vm:/remote/dir --zone=us-central1-a
```

### Common VM Operations

```bash
# Check if backend is running
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="ps aux | grep uvicorn | grep -v grep"

# View backend logs
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="tail -100 /home/runner/philosophy_video_generator/logs/backend.log"

# Check nginx status
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="sudo systemctl status nginx"

# Restart nginx
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="sudo systemctl restart nginx"

# Check disk space
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="df -h"

# Check memory
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="free -h"
```

## Starting/Stopping the Backend

### Start Backend
```bash
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="sudo -u runner bash -c 'cd /home/runner/philosophy_video_generator/backend && nohup python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8001 > ../logs/backend.log 2>&1 &'"
```

### Stop Backend
```bash
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="sudo pkill -f uvicorn"
```

### Restart Backend
```bash
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="sudo pkill -f uvicorn; sleep 2; sudo -u runner bash -c 'cd /home/runner/philosophy_video_generator/backend && nohup python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8001 > ../logs/backend.log 2>&1 &'"
```

### Check Port Usage
```bash
# Find what's using port 8001
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="sudo lsof -ti:8001"

# Kill process on port 8001
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="sudo lsof -ti:8001 | xargs -r sudo kill -9"
```

## Nginx Configuration

**Config File:** `/etc/nginx/sites-available/api.cofndrly.com`

```nginx
server {
    listen 443 ssl;
    server_name api.cofndrly.com;

    ssl_certificate /etc/letsencrypt/live/api.cofndrly.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.cofndrly.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name api.cofndrly.com;
    return 301 https://$server_name$request_uri;
}
```

**Commands:**
```bash
# Test nginx config
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="sudo nginx -t"

# Reload nginx
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="sudo systemctl reload nginx"

# View nginx error log
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="sudo tail -50 /var/log/nginx/error.log"
```

## SSL Certificate (Let's Encrypt)

The SSL certificate is managed by Certbot and auto-renews.

```bash
# Check certificate expiry
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="sudo certbot certificates"

# Force renewal
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="sudo certbot renew --force-renewal"

# Check auto-renewal timer
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="sudo systemctl status certbot.timer"
```

## Deployment Workflow

### Current Setup (Manual Sync Required)

The GCP VM does NOT have a git repository. Code must be manually synced.

```bash
# Sync a specific file to GCP
gcloud compute scp /local/path/to/file philosophy-bot-vm:/tmp/file --zone=us-central1-a
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="sudo cp /tmp/file /home/runner/philosophy_video_generator/path/to/file && sudo chown runner:runner /home/runner/philosophy_video_generator/path/to/file"

# Sync a directory
gcloud compute scp --recurse /local/dir philosophy-bot-vm:/tmp/dir --zone=us-central1-a
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="sudo cp -r /tmp/dir /home/runner/philosophy_video_generator/ && sudo chown -R runner:runner /home/runner/philosophy_video_generator/dir"
```

### After Code Changes

1. **Sync changed files to GCP** using `gcloud compute scp`
2. **Clear Python cache:**
   ```bash
   gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="sudo find /home/runner/philosophy_video_generator -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null; sudo find /home/runner/philosophy_video_generator -name '*.pyc' -delete 2>/dev/null"
   ```
3. **Restart backend:**
   ```bash
   gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="sudo pkill -f uvicorn; sleep 2; sudo -u runner bash -c 'cd /home/runner/philosophy_video_generator/backend && nohup python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8001 > ../logs/backend.log 2>&1 &'"
   ```
4. **Verify:**
   ```bash
   curl https://api.cofndrly.com/api/health
   ```

### Installing New Python Dependencies

```bash
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="sudo pip3 install <package>"

# Or install from requirements.txt
gcloud compute scp requirements.txt philosophy-bot-vm:/tmp/requirements.txt --zone=us-central1-a
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="sudo pip3 install -r /tmp/requirements.txt"
```

## Troubleshooting

### 502 Bad Gateway

**Cause:** Backend (uvicorn) is not running.

**Fix:**
```bash
# Check if uvicorn is running
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="ps aux | grep uvicorn"

# Check logs for errors
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="tail -50 /home/runner/philosophy_video_generator/logs/backend.log"

# Start backend
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="sudo -u runner bash -c 'cd /home/runner/philosophy_video_generator/backend && nohup python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8001 > ../logs/backend.log 2>&1 &'"
```

### Port Already in Use

**Cause:** Previous uvicorn process didn't exit cleanly.

**Fix:**
```bash
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="sudo lsof -ti:8001 | xargs -r sudo kill -9"
```

### Module Not Found Error

**Cause:** Missing Python dependency on VM.

**Fix:**
```bash
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="sudo pip3 install <missing-module>"
```

### Attribute Error on Startup

**Cause:** Code on VM is outdated (missing new attributes/methods).

**Fix:**
1. Sync the updated file to GCP
2. Clear Python cache
3. Restart backend

### Database Differences (Local vs Production)

**Understanding:** Local and production have **completely separate databases**.

| Environment | Database Location |
|-------------|-------------------|
| Local (Mac) | `~/Desktop/TV Clips/philosophy_video_generator/philosophy_generator.db` |
| Production (GCP) | `/home/runner/philosophy_video_generator/philosophy_generator.db` |

**They do NOT sync automatically.** Projects created locally stay local; projects created on production stay on production.

**To copy database from local to production:**
```bash
gcloud compute scp philosophy_generator.db philosophy-bot-vm:/tmp/philosophy_generator.db --zone=us-central1-a
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="sudo cp /tmp/philosophy_generator.db /home/runner/philosophy_video_generator/philosophy_generator.db && sudo chown runner:runner /home/runner/philosophy_video_generator/philosophy_generator.db"
```

### Python Cache Issues

**Symptom:** Code changes don't take effect after syncing.

**Fix:**
```bash
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="sudo find /home/runner/philosophy_video_generator -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null; sudo find /home/runner/philosophy_video_generator -name '*.pyc' -delete 2>/dev/null"
```

## Health Checks

### Quick Health Check
```bash
# Should return {"status":"healthy"}
curl https://api.cofndrly.com/api/health
```

### Full System Check
```bash
# Check nginx
curl -I https://api.cofndrly.com 2>/dev/null | head -1

# Check auth (should return 401 without key)
curl -s https://api.cofndrly.com/api/projects | head -20

# Check auth (should return 200 with key)
curl -s -H "X-API-Key: b4TZ2d11ZDkXpDNU_V8m4KxyYdCdJMERKMyVvgyyYz0" https://api.cofndrly.com/api/projects | head -20

# Check frontend
curl -I https://app.cofndrly.com 2>/dev/null | head -1
```

## Monitoring & Logs

### Backend Logs
```bash
# Tail logs in real-time
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="tail -f /home/runner/philosophy_video_generator/logs/backend.log"

# Last 100 lines
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="tail -100 /home/runner/philosophy_video_generator/logs/backend.log"

# Search for errors
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="grep -i error /home/runner/philosophy_video_generator/logs/backend.log | tail -20"
```

### Nginx Logs
```bash
# Access log
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="sudo tail -100 /var/log/nginx/access.log"

# Error log
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="sudo tail -100 /var/log/nginx/error.log"
```

## Domain & DNS

| Domain | Type | Points To | Managed By |
|--------|------|-----------|------------|
| `api.cofndrly.com` | A | `23.251.149.244` | GoDaddy |
| `app.cofndrly.com` | CNAME | Vercel | GoDaddy |

## Security Checklist

- [ ] API_KEY is set in `.env` on GCP VM
- [ ] VITE_API_KEY is set in Vercel dashboard
- [ ] SSL certificate is valid and auto-renewing
- [ ] CORS origins are restricted (no wildcards)
- [ ] Rate limiting is enabled (slowapi)
- [ ] Error messages don't expose stack traces in production

## Future Improvements

1. **Set up git on GCP VM** for proper version control
2. **GitHub Actions deployment** for auto-deploy on push
3. **systemd service** for uvicorn auto-restart on crash
4. **Database backups** to GCS
5. **Monitoring dashboard** (Grafana/Prometheus)
6. **Container deployment** (Docker/Cloud Run)
