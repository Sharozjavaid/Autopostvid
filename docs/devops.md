# DevOps & Deployment Documentation

## Domain & Infrastructure Overview
| Service | URL | Status |
|---------|-----|--------|
| **React Frontend** | `https://app.cofndrly.com` | ✅ Live on Vercel |
| **Backend API** | `https://api.cofndrly.com` | ✅ Live on GCP VM |
| **Static Images** | `https://api.cofndrly.com/static/images/...` | ✅ Served by FastAPI |
| **Static Slides** | `https://api.cofndrly.com/static/slides/...` | ✅ Served by FastAPI |
| **TikTok Callback** | `https://api.cofndrly.com/api/tiktok/callback` | ✅ Verified |

## GCP VM Details
- **VM Name**: `philosophy-bot-vm`
- **Zone**: `us-central1-a`
- **External IP**: `23.251.149.244`
- **Domain**: `api.cofndrly.com` → points to the VM (A record in GoDaddy)
- **Code Location on VM**: `/home/runner/philosophy_video_generator`
- **User on VM**: `runner` (run commands as `sudo -u runner bash -c '...'`)
- **Backend**: Uvicorn on port 8001, proxied by Nginx
- **No git on VM**: Code must be synced manually with `gcloud compute scp`
- **Separate databases**: Local and production DBs are independent

## Accessing the VM

```bash
# List VMs
gcloud compute instances list

# SSH into the VM
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a

# Run a command on the VM
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="your-command-here"

# Check if backend running
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="ps aux | grep uvicorn"

# View backend logs
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="tail -50 /home/runner/philosophy_video_generator/logs/backend.log"

# Restart backend
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="sudo pkill -f uvicorn; sleep 2; sudo -u runner bash -c 'cd /home/runner/philosophy_video_generator/backend && nohup python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8001 > ../logs/backend.log 2>&1 &'"

# Sync file to VM
gcloud compute scp /local/file philosophy-bot-vm:/tmp/file --zone=us-central1-a
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="sudo cp /tmp/file /home/runner/philosophy_video_generator/path/file && sudo chown runner:runner /home/runner/philosophy_video_generator/path/file"

# Clear Python cache (required after syncing code)
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="sudo find /home/runner/philosophy_video_generator -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null"

# Install Python package
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="sudo pip3 install <package>"
```

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| 502 Bad Gateway | Backend not running | Start uvicorn (see above) |
| Port already in use | Zombie uvicorn | `sudo lsof -ti:8001 \| xargs -r sudo kill -9` |
| ModuleNotFoundError | Missing dependency | `sudo pip3 install <module>` |
| AttributeError on startup | Outdated code on VM | Sync file + clear cache + restart |
| Changes not taking effect | Python cache | Clear `__pycache__` dirs |

## SSL/HTTPS Setup (Already Configured)
- **Nginx** is installed as a reverse proxy on the VM
- **Let's Encrypt** SSL certificate via certbot (auto-renews)
- Config file: `/etc/nginx/sites-available/api.cofndrly.com`

Nginx proxies:
- `https://api.cofndrly.com` → `http://127.0.0.1:8001` (backend)

To check nginx status:
```bash
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="sudo systemctl status nginx"
```

To reload nginx after config changes:
```bash
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="sudo nginx -t && sudo systemctl reload nginx"
```

## Static File Hosting
The FastAPI backend serves static files for TikTok API access:
- **Images**: Mounted at `/static/images/` → filesystem `generated_images/`
- **Slides**: Mounted at `/static/slides/` → filesystem `generated_slideshows/`

Example URLs:
```
https://api.cofndrly.com/static/images/King_Solomon_scene_1_nano.png
https://api.cofndrly.com/static/slides/gpt15/Stoicism_slide_0.png
```

## Firewall Rules
Ports 80 and 443 are open for HTTP/HTTPS traffic:
```bash
gcloud compute firewall-rules list --filter="name~http"
```

## Frontend (Vercel) - Quick Reference
- **URL:** `https://app.cofndrly.com`
- **Login:** Username `sharoz75`, Password `rosebud`
- **Auto-deploys** on `git push origin main` (see CI/CD section below)

## Automation Scheduler
The backend includes APScheduler for running automations:

**How it works:**
1. Scheduler starts with the backend app
2. Loads all automations where `status="running"` and `is_active=True`
3. Creates cron jobs based on `schedule_times` and `schedule_days`
4. When triggered: generates slideshow → optionally posts to TikTok
5. Tracks run history in `automation_runs` table

**Key files:**
- `backend/app/services/scheduler.py` - APScheduler service
- `backend/app/services/tiktok_poster.py` - TikTok posting service
- `backend/app/models/automation_run.py` - Run history model

**API Endpoints:**
```bash
# Start/stop automation
POST /api/automations/{id}/start
POST /api/automations/{id}/stop

# Trigger immediate run (for testing)
POST /api/automations/{id}/run-now

# View run history
GET /api/automations/{id}/runs

# Get scheduler status
GET /api/automations/scheduler/status

# Configure TikTok posting
PUT /api/automations/{id}/tiktok-settings
```

**Enable TikTok auto-posting:**
Set `post_to_tiktok: true` in automation settings to automatically post slideshows.

## CI/CD Pipeline (Auto-Deploy on Git Push)

The project has fully automated CI/CD - pushing to `main` deploys both frontend and backend:

| Component | Platform | URL | Trigger |
|-----------|----------|-----|---------|
| **Backend** | GCP VM | `https://api.cofndrly.com` | GitHub Actions |
| **Frontend** | Vercel | `https://app.cofndrly.com` | Vercel Git Integration |

**Workflow:**
```
git push origin main
    │
    ├──► GitHub Actions (.github/workflows/deploy.yml)
    │       └── SSH into GCP VM → git pull → restart uvicorn
    │
    └──► Vercel (auto-triggered)
            └── Build from frontend/ directory → deploy to CDN
```

### Backend Deployment (GitHub Actions → GCP)

**File:** `.github/workflows/deploy.yml`

**What it does:**
1. SSHs into `philosophy-bot-vm` on GCP
2. Pulls latest code from GitHub
3. Installs any new Python dependencies
4. Restarts the uvicorn server

**Required GitHub Secrets:**
- `GCP_SSH_KEY` - Private SSH key for the VM
- `GCP_VM_IP` - External IP of the VM (23.251.149.244)

**Manual deploy (if needed):**
```bash
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="cd /home/runner/philosophy_video_generator && git pull && pip install -r requirements.txt && sudo systemctl restart philosophy-backend"
```

### Frontend Deployment (Vercel)

**Vercel Project:** `frontend` under `sharozs-projects-b7468887`
**Root Directory:** `frontend` (set in Vercel dashboard)
**Framework:** Vite
**Build Command:** `npm run build`
**Output Directory:** `dist`

**Environment Variables (set in Vercel dashboard):**
- `VITE_API_URL=https://api.cofndrly.com`

**Manual deploy (if needed):**
```bash
cd frontend
npx vercel --prod
```

**Vercel CLI commands:**
```bash
npx vercel ls                    # List recent deployments
npx vercel env ls                # List environment variables
npx vercel logs <deployment-url> # View deployment logs
npx vercel inspect <url>         # Inspect deployment details
```

### Git Configuration

**Important:** Use `sharoz75@gmail.com` as git author to avoid Vercel permission issues:
```bash
git config user.email "sharoz75@gmail.com"
git config user.name "Sharoz Javaid"
```

### Deployment Checklist

Before pushing to production:
1. ✅ Run `npm run build` in `frontend/` to check for TypeScript errors
2. ✅ Test locally with `./dev.sh`
3. ✅ Commit with descriptive message
4. ✅ Push to main: `git push origin main`
5. ✅ Monitor GitHub Actions: `gh run list --limit 3`
6. ✅ Monitor Vercel: `cd frontend && npx vercel ls`

## Checklist for Deploying Code Changes
- [ ] Sync changed files to GCP with `gcloud compute scp`
- [ ] Clear Python cache on VM
- [ ] Restart uvicorn
- [ ] Verify with `curl https://api.cofndrly.com/api/health`
