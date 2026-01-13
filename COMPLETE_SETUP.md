# Complete GCP Setup - Manual Steps Required

## ✅ What's Already Done
- Logged into personal account: `sharoz75@gmail.com`
- Created project: `philosophy-bot-05854`
- Project is set as active

## ⚠️ Action Required: Enable Billing

GCP requires a billing account to use Compute Engine (even with free tier credits).

### Steps:

1. **Go to GCP Console:**
   Open: https://console.cloud.google.com/billing?project=philosophy-bot-05854

2. **Link a Billing Account:**
   - Click "Link a billing account"
   - If you don't have one, click "Create billing account"
   - Enter payment info (you'll get $300 free credits for new accounts)
   - Link it to the `philosophy-bot-05854` project

3. **Enable Required APIs:**
   Once billing is enabled, run:
   ```bash
   gcloud config set project philosophy-bot-05854
   gcloud services enable compute.googleapis.com
   gcloud services enable cloudbuild.googleapis.com
   ```

4. **Deploy:**
   ```bash
   ./deploy_gcp.sh philosophy-bot-05854
   ```

## Alternative: Use Existing Personal Project

If you already have a personal GCP project with billing enabled:

```bash
# List your projects
gcloud projects list

# Set the project
gcloud config set project YOUR_EXISTING_PROJECT_ID

# Deploy
./deploy_gcp.sh YOUR_EXISTING_PROJECT_ID
```

## Cost Reminder
- **Free Tier**: $300 credits for new accounts (valid 90 days)
- **VM Cost**: ~$25/month for e2-medium
- **API Costs**: Variable based on usage

The free credits should cover several months of operation!
