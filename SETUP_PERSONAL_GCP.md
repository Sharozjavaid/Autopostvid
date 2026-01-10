# Setup Guide for Personal GCP Account

## Switch to Personal Account

Before deploying, make sure you're using your personal GCP account:

### 1. Login to your personal account
```bash
gcloud auth login sharoz75@gmail.com
```

### 2. List your GCP projects
```bash
gcloud projects list
```

### 3. Set your personal project
```bash
# Replace with your actual personal project ID
gcloud config set project YOUR_PERSONAL_PROJECT_ID
```

If you don't have a personal project yet:
```bash
# Create a new project
gcloud projects create philosophy-video-bot --name="Philosophy Video Bot"
gcloud config set project philosophy-video-bot
```

### 4. Enable required APIs
```bash
gcloud services enable compute.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### 5. Verify your configuration
```bash
gcloud config list
```

Make sure it shows:
- **account**: sharoz75@gmail.com
- **project**: your-personal-project-id

## Then Deploy

Once you've confirmed you're on the personal account, run:
```bash
./deploy_gcp.sh
```

## Current Configuration

Your current gcloud config:
- Account: sharoz@eyepop.ai (WORK)
- Project: eyepop-staging (WORK)

⚠️ **You need to switch before deploying!**
