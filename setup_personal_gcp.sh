#!/bin/bash

# Interactive Setup Script for Personal GCP Account
# This ensures you're deploying to the right account

set -e

echo "🔐 GCP Account Setup for Personal Deployment"
echo "=============================================="
echo ""

# Check current account
CURRENT_ACCOUNT=$(gcloud config get-value account 2>/dev/null)
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)

echo "📋 Current Configuration:"
echo "   Account: $CURRENT_ACCOUNT"
echo "   Project: $CURRENT_PROJECT"
echo ""

# Warn if on work account
if [[ $CURRENT_ACCOUNT == *"eyepop.ai"* ]]; then
    echo "⚠️  WARNING: You're currently on your WORK account!"
    echo ""
    read -p "Switch to personal account (sharoz75@gmail.com)? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🔄 Switching to personal account..."
        gcloud auth login sharoz75@gmail.com
    else
        echo "❌ Deployment cancelled. Please switch accounts manually."
        exit 1
    fi
fi

# List projects
echo ""
echo "📁 Your GCP Projects:"
gcloud projects list --filter="parent.id:*" 2>/dev/null || echo "No projects found or unable to list."
echo ""

# Prompt for project
read -p "Enter your personal project ID (or press Enter to create new): " PROJECT_ID

if [ -z "$PROJECT_ID" ]; then
    # Create new project
    DEFAULT_PROJECT="philosophy-video-bot-$(date +%s)"
    read -p "Create new project? Enter name [$DEFAULT_PROJECT]: " NEW_PROJECT
    PROJECT_ID=${NEW_PROJECT:-$DEFAULT_PROJECT}
    
    echo "🆕 Creating project: $PROJECT_ID"
    gcloud projects create $PROJECT_ID --name="Philosophy Video Bot"
fi

# Set project
echo "🎯 Setting project to: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# Enable APIs
echo "🔧 Enabling required APIs..."
gcloud services enable compute.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# Verify
echo ""
echo "✅ Configuration Complete!"
echo ""
FINAL_ACCOUNT=$(gcloud config get-value account)
FINAL_PROJECT=$(gcloud config get-value project)
echo "   Account: $FINAL_ACCOUNT"
echo "   Project: $FINAL_PROJECT"
echo ""

if [[ $FINAL_ACCOUNT == "sharoz75@gmail.com" ]]; then
    echo "✅ You're on your PERSONAL account. Safe to deploy!"
    echo ""
    read -p "Deploy now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ./deploy_gcp.sh $FINAL_PROJECT
    fi
else
    echo "⚠️  Account mismatch. Please verify manually."
fi
