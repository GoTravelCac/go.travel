# GoTravel - GitHub to Cloud Run Deployment Setup

This document outlines how to connect your GoTravel GitHub repository to Google Cloud Run for automatic deployment.

## Repository Information
- **Repository**: GoTravelCac/go.travel
- **Branch**: main
- **Cloud Run Service**: gotravel
- **Region**: us-central1

## Setup Instructions

### 1. Connect GitHub Repository to Google Cloud Build

1. Go to [Google Cloud Console - Cloud Build Triggers](https://console.cloud.google.com/cloud-build/triggers)
2. Click "Create Trigger"
3. Select "GitHub (Cloud Build GitHub App)"
4. Authenticate with GitHub if prompted
5. Select repository: `GoTravelCac/go.travel`
6. Configure the trigger:
   - **Name**: `gotravel-deploy-trigger`
   - **Event**: Push to a branch
   - **Source**: Branch = `^main$`
   - **Build Configuration**: Cloud Build configuration file (yaml or json)
   - **Cloud Build configuration file location**: `cloudbuild.yaml`

### 2. Environment Variables

The Cloud Build will automatically use the environment variables that are already configured in your Cloud Run service:
- GEMINI_API_KEY
- GOOGLE_API_KEY  
- OPENWEATHERMAP_API_KEY

### 3. Manual Trigger Creation (Alternative)

If the console method doesn't work, you can create the trigger using gcloud:

```bash
# First, connect GitHub repository (done through console)
# Then create the trigger
gcloud builds triggers create github \
  --repo-name=go.travel \
  --repo-owner=GoTravelCac \
  --branch-pattern="^main$" \
  --build-config=cloudbuild.yaml \
  --name=gotravel-deploy-trigger
```

## How It Works

Once set up, every time you push code to the `main` branch:

1. **GitHub** receives the push
2. **Cloud Build** is triggered automatically
3. **Docker image** is built using your Dockerfile
4. **Image** is pushed to Google Container Registry
5. **Cloud Run** service is updated with the new image
6. **Environment variables** are preserved automatically

## Benefits

- ✅ **Automatic Deployment**: No manual deployment needed
- ✅ **Version Control**: All changes tracked in GitHub
- ✅ **Rollback Capability**: Easy to revert to previous versions
- ✅ **Build History**: View all builds in Cloud Build console
- ✅ **Environment Consistency**: Same environment variables maintained

## Testing the Setup

After connecting, make a small change to your repository and push to main:

```bash
# Make a small change
echo "# Updated" >> README.md
git add README.md
git commit -m "Test automatic deployment"
git push origin main
```

Then check the Cloud Build console to see the automatic build and deployment in progress.