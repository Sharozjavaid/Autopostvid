# Cloud Deployment Guide

This guide covers deploying the Philosophy Video Generator to run 24/7 on GCP.

## Option 1: Google Cloud Run (Recommended for Simplicity)

Cloud Run is serverless and easy to deploy, but has some limitations for long-running processes.

### Steps:

1. **Build and push Docker image:**
   ```bash
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/philosophy-bot
   ```

2. **Deploy to Cloud Run:**
   ```bash
   gcloud run deploy philosophy-bot \
     --image gcr.io/YOUR_PROJECT_ID/philosophy-bot \
     --platform managed \
     --region us-central1 \
     --no-allow-unauthenticated \
     --set-env-vars GOOGLE_API_KEY=your_key,ELEVENLABS_API_KEY=your_key,EMAIL_USER=your_email,EMAIL_PASSWORD=your_password,RECIPIENT_EMAIL=target_email
   ```

**Note:** Cloud Run has a 60-minute timeout for requests, so it's better suited for triggered jobs rather than continuous loops.

## Option 2: Google Compute Engine VM (Best for 24/7 Operation)

A VM gives you full control and can run indefinitely.

### Steps:

1. **Create a VM instance:**
   ```bash
   gcloud compute instances create philosophy-bot-vm \
     --zone=us-central1-a \
     --machine-type=e2-medium \
     --image-family=ubuntu-2204-lts \
     --image-project=ubuntu-os-cloud \
     --boot-disk-size=20GB
   ```

2. **SSH into the VM:**
   ```bash
   gcloud compute ssh philosophy-bot-vm --zone=us-central1-a
   ```

3. **Install Docker on the VM:**
   ```bash
   sudo apt-get update
   sudo apt-get install -y docker.io
   sudo systemctl start docker
   sudo systemctl enable docker
   ```

4. **Copy your project to the VM:**
   ```bash
   # On your local machine:
   gcloud compute scp --recurse /path/to/philosophy_video_generator philosophy-bot-vm:~ --zone=us-central1-a
   ```

5. **Build and run the Docker container on the VM:**
   ```bash
   # On the VM:
   cd philosophy_video_generator
   
   # Create .env file with your secrets
   nano .env
   # (paste your credentials)
   
   # Build the image
   sudo docker build -t philosophy-bot .
   
   # Run the container in detached mode
   sudo docker run -d --name philosophy-agent \
     --env-file .env \
     --restart unless-stopped \
     philosophy-bot
   ```

6. **Monitor logs:**
   ```bash
   sudo docker logs -f philosophy-agent
   ```

## Option 3: Google Cloud Functions (For Scheduled Runs)

If you prefer scheduled execution instead of continuous running:

1. Deploy as a Cloud Function triggered by Cloud Scheduler
2. Set it to run 3 times daily at your preferred times
3. Each invocation generates one video

## Recommended: Option 2 (Compute Engine VM)

This gives you:
- Full control over the runtime
- No timeout limitations
- Ability to run the smart scheduler continuously
- Easy access to logs and monitoring

## Cost Estimate

- **Compute Engine e2-medium VM**: ~$25/month
- **API costs** (Gemini + ElevenLabs): Variable based on usage
- **Storage**: Minimal (~$1/month)

**Total**: ~$30-50/month depending on API usage
