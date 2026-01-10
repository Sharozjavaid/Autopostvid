#!/bin/bash

# Quick Deploy Script for GCP Compute Engine VM
# This script automates the VM deployment process

set -e

echo "🚀 Philosophy Video Generator - GCP Deployment Script"
echo "======================================================"

# Configuration
PROJECT_ID=${1:-$(gcloud config get-value project)}
VM_NAME="philosophy-bot-vm"
ZONE="us-central1-a"
MACHINE_TYPE="e2-medium"

echo "📋 Configuration:"
echo "   Project ID: $PROJECT_ID"
echo "   VM Name: $VM_NAME"
echo "   Zone: $ZONE"
echo ""

read -p "Continue with deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    exit 1
fi

# Step 1: Create VM
echo "🖥️  Creating VM instance..."
gcloud compute instances create $VM_NAME \
  --project=$PROJECT_ID \
  --zone=$ZONE \
  --machine-type=$MACHINE_TYPE \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=20GB \
  --tags=http-server,https-server

echo "✅ VM created successfully!"

# Step 2: Wait for VM to be ready
echo "⏳ Waiting for VM to be ready..."
sleep 10

# Step 3: Copy project files
echo "📦 Copying project files to VM..."
gcloud compute scp --recurse . $VM_NAME:~/philosophy_video_generator --zone=$ZONE

# Step 4: Setup script
echo "🔧 Setting up Docker and running container..."
gcloud compute ssh $VM_NAME --zone=$ZONE --command="
  sudo apt-get update && \
  sudo apt-get install -y docker.io && \
  sudo systemctl start docker && \
  sudo systemctl enable docker && \
  cd ~/philosophy_video_generator && \
  sudo docker build -t philosophy-bot . && \
  sudo docker run -d --name philosophy-agent \
    --env-file .env \
    --restart unless-stopped \
    philosophy-bot
"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 To view logs:"
echo "   gcloud compute ssh $VM_NAME --zone=$ZONE"
echo "   sudo docker logs -f philosophy-agent"
echo ""
echo "🛑 To stop the bot:"
echo "   gcloud compute ssh $VM_NAME --zone=$ZONE"
echo "   sudo docker stop philosophy-agent"
