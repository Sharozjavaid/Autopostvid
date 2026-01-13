# GitHub Actions - GCP Deployment Setup

This guide explains how to set up automated deployment to GCP via GitHub Actions.

## Prerequisites

1. A GCP project with Compute Engine API enabled
2. An existing VM named `philosophy-bot-vm` in `us-central1-a`
3. A GCP service account with appropriate permissions

## Step 1: Create a GCP Service Account

```bash
# Create service account
gcloud iam service-accounts create github-actions-deploy \
    --display-name="GitHub Actions Deploy"

# Grant necessary permissions
PROJECT_ID=$(gcloud config get-value project)

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:github-actions-deploy@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/compute.instanceAdmin.v1"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:github-actions-deploy@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/compute.osLogin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:github-actions-deploy@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/iap.tunnelResourceAccessor"

# Create and download key
gcloud iam service-accounts keys create ~/github-actions-key.json \
    --iam-account=github-actions-deploy@$PROJECT_ID.iam.gserviceaccount.com

echo "Key saved to ~/github-actions-key.json"
```

## Step 2: Add GitHub Secrets

Go to your repository: https://github.com/Sharozjavaid/Autopostvid/settings/secrets/actions

Add the following secrets:

### Required Secrets

| Secret Name | Description | How to Get |
|------------|-------------|------------|
| `GCP_PROJECT_ID` | Your GCP project ID | `gcloud config get-value project` |
| `GCP_SA_KEY` | Service account JSON key | Contents of `~/github-actions-key.json` |

### API Keys (copy from your .env file)

| Secret Name | Description |
|------------|-------------|
| `GOOGLE_API_KEY` | Google/Gemini API key |
| `ELEVENLABS_API_KEY` | ElevenLabs voice API key |
| `FAL_KEY` | fal.ai API key for GPT Image 1.5 |
| `OPENAI_API_KEY` | OpenAI API key |
| `ANTHROPIC_API_KEY` | Anthropic API key |

### TikTok Integration (optional)

| Secret Name | Description |
|------------|-------------|
| `TIKTOK_CLIENT_KEY` | TikTok app client key |
| `TIKTOK_CLIENT_SECRET` | TikTok app client secret |

### Email Notifications (optional)

| Secret Name | Description |
|------------|-------------|
| `EMAIL_SENDER` | Gmail address for sending |
| `EMAIL_PASSWORD` | Gmail app password |
| `EMAIL_RECIPIENT` | Email to receive notifications |

## Step 3: How It Works

1. **Push to `main` branch** → GitHub Actions automatically triggers
2. **Workflow authenticates** to GCP using the service account
3. **Stops existing container** on the VM
4. **Copies updated files** to the VM
5. **Builds new Docker image** with your changes
6. **Starts new container** with the updated code
7. **Verifies deployment** and posts summary

## Step 4: Manual Deployment

You can also trigger deployment manually:
1. Go to Actions tab in GitHub
2. Select "Deploy to GCP" workflow
3. Click "Run workflow"

## Troubleshooting

### SSH Connection Issues

If you get SSH errors, ensure the service account has OS Login permissions:

```bash
gcloud compute instances add-iam-policy-binding philosophy-bot-vm \
    --zone=us-central1-a \
    --member="serviceAccount:github-actions-deploy@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/compute.osAdminLogin"
```

### Container Not Starting

Check logs via SSH:
```bash
gcloud compute ssh philosophy-bot-vm --zone=us-central1-a --command="sudo docker logs philosophy-agent"
```

### Viewing Deployment Status

- Go to: https://github.com/Sharozjavaid/Autopostvid/actions
- Click on the latest workflow run to see detailed logs

## Dashboard Access

After deployment, access your dashboard at:
```
http://23.251.149.244:8501
```

Login credentials:
- Username: `sharoz75`
- Password: `1028`
