#!/bin/bash

# =============================================================================
# Philosophy Video Generator - GCP Deployment Script
# =============================================================================
# 
# This script deploys the application to a GCP Compute Engine VM.
# 
# What gets deployed:
# - Streamlit Dashboard (always running) - http://[IP]:8501
# - Daily Production Scheduler (paused by default)
#
# After deployment:
# - Dashboard is immediately accessible
# - Automation is PAUSED until you enable it
#
# =============================================================================

set -e

echo "🚀 Philosophy Video Generator - GCP Deployment"
echo "================================================"

# Configuration
PROJECT_ID=${1:-$(gcloud config get-value project)}
VM_NAME="philosophy-bot-vm"
ZONE="us-central1-a"
MACHINE_TYPE="e2-medium"

echo ""
echo "📋 Configuration:"
echo "   Project ID: $PROJECT_ID"
echo "   VM Name: $VM_NAME"
echo "   Zone: $ZONE"
echo "   Machine Type: $MACHINE_TYPE"
echo ""

read -p "Continue with deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Check if VM already exists
if gcloud compute instances describe $VM_NAME --zone=$ZONE --project=$PROJECT_ID &>/dev/null; then
    echo ""
    echo "⚠️  VM '$VM_NAME' already exists."
    echo ""
    echo "Options:"
    echo "  1) Update existing VM (copy new files, rebuild container)"
    echo "  2) Delete and recreate VM"
    echo "  3) Cancel"
    echo ""
    read -p "Choose option (1/2/3): " -n 1 -r
    echo
    
    case $REPLY in
        1)
            echo "📦 Updating existing VM..."
            
            # Stop container
            echo "🛑 Stopping container..."
            gcloud compute ssh $VM_NAME --zone=$ZONE --command="sudo docker stop philosophy-agent 2>/dev/null || true"
            
            # Copy files
            echo "📁 Copying updated files..."
            gcloud compute scp --recurse . $VM_NAME:~/philosophy_video_generator --zone=$ZONE
            
            # Rebuild and restart
            echo "🔨 Rebuilding container..."
            gcloud compute ssh $VM_NAME --zone=$ZONE --command="
                cd ~/philosophy_video_generator && \
                sudo docker rm philosophy-agent 2>/dev/null || true && \
                sudo docker build -t philosophy-bot . && \
                sudo docker run -d --name philosophy-agent \
                    -p 8501:8501 \
                    --env-file .env \
                    --restart unless-stopped \
                    philosophy-bot
            "
            ;;
        2)
            echo "🗑️  Deleting existing VM..."
            gcloud compute instances delete $VM_NAME --zone=$ZONE --project=$PROJECT_ID --quiet
            ;;
        3)
            echo "Cancelled."
            exit 0
            ;;
        *)
            echo "Invalid option."
            exit 1
            ;;
    esac
fi

# Create VM if it doesn't exist (or was just deleted)
if ! gcloud compute instances describe $VM_NAME --zone=$ZONE --project=$PROJECT_ID &>/dev/null; then
    # Create firewall rule for Streamlit
    echo "🔥 Creating firewall rule for Streamlit (port 8501)..."
    gcloud compute firewall-rules create allow-streamlit \
        --project=$PROJECT_ID \
        --allow=tcp:8501 \
        --target-tags=streamlit-server \
        --description="Allow incoming traffic on port 8501 for Streamlit" \
        2>/dev/null || echo "   (Firewall rule already exists)"

    # Create VM
    echo "🖥️  Creating VM instance..."
    gcloud compute instances create $VM_NAME \
        --project=$PROJECT_ID \
        --zone=$ZONE \
        --machine-type=$MACHINE_TYPE \
        --image-family=ubuntu-2204-lts \
        --image-project=ubuntu-os-cloud \
        --boot-disk-size=30GB \
        --tags=http-server,https-server,streamlit-server

    echo "✅ VM created!"
    echo "⏳ Waiting for VM to be ready..."
    sleep 15

    # Copy project files
    echo "📦 Copying project files to VM..."
    gcloud compute scp --recurse . $VM_NAME:~/philosophy_video_generator --zone=$ZONE

    # Setup Docker and run container
    echo "🔧 Setting up Docker..."
    gcloud compute ssh $VM_NAME --zone=$ZONE --command="
        sudo apt-get update && \
        sudo apt-get install -y docker.io && \
        sudo systemctl start docker && \
        sudo systemctl enable docker && \
        cd ~/philosophy_video_generator && \
        sudo docker build -t philosophy-bot . && \
        sudo docker run -d --name philosophy-agent \
            -p 8501:8501 \
            --env-file .env \
            --restart unless-stopped \
            philosophy-bot
    "
fi

# Get external IP
EXTERNAL_IP=$(gcloud compute instances describe $VM_NAME --zone=$ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo ""
echo "============================================================"
echo "✅ DEPLOYMENT COMPLETE!"
echo "============================================================"
echo ""
echo "🌐 Dashboard URL:"
echo "   http://$EXTERNAL_IP:8501"
echo ""
echo "📊 Current Status:"
echo "   - Streamlit Dashboard: RUNNING ✅"
echo "   - Daily Production: PAUSED ⏸️  (by design)"
echo ""
echo "============================================================"
echo "🔧 CONTROL COMMANDS"
echo "============================================================"
echo ""
echo "SSH into VM:"
echo "   gcloud compute ssh $VM_NAME --zone=$ZONE"
echo ""
echo "View container logs:"
echo "   gcloud compute ssh $VM_NAME --zone=$ZONE --command='sudo docker logs -f philosophy-agent'"
echo ""
echo "============================================================"
echo "🚀 TO ENABLE DAILY AUTOMATION:"
echo "============================================================"
echo ""
echo "Option 1 - Quick enable (runs immediately + schedules daily):"
echo "   gcloud compute ssh $VM_NAME --zone=$ZONE --command='sudo docker exec philosophy-agent supervisorctl start production-scheduler'"
echo ""
echo "Option 2 - Run once manually:"
echo "   gcloud compute ssh $VM_NAME --zone=$ZONE --command='sudo docker exec philosophy-agent python3 daily_production.py'"
echo ""
echo "============================================================"
echo "⏸️  TO PAUSE AUTOMATION:"
echo "============================================================"
echo ""
echo "   gcloud compute ssh $VM_NAME --zone=$ZONE --command='sudo docker exec philosophy-agent supervisorctl stop production-scheduler'"
echo ""
echo "============================================================"
echo "📊 VIEW PRODUCTION HISTORY:"
echo "============================================================"
echo ""
echo "   Visit http://$EXTERNAL_IP:8501 and go to 'Production History' tab"
echo ""
echo "============================================================"
echo "💰 VIEW COSTS:"
echo "============================================================"
echo ""
echo "   gcloud compute ssh $VM_NAME --zone=$ZONE --command='sudo docker exec philosophy-agent python3 daily_production.py --costs'"
echo ""
