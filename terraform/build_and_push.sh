#!/bin/bash

# This script builds and pushes all necessary Docker images to Azure Container Registry.
# It tags images with a unique version based on the current timestamp.

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
ACR_NAME="bacheloracr"
ACR_URL="$ACR_NAME.azurecr.io"
# Generate a unique version tag (e.g., 20250623123000)
VERSION_TAG=$(date +%Y%m%d%H%M%S)

# --- Script ---

echo "--> Logging in to Azure Container Registry: $ACR_NAME"
az acr login --name $ACR_NAME
echo "Login Succeeded."
echo ""

# --- Build and Push Each Service ---

echo "--> Building and pushing 'database' (Version: $VERSION_TAG)..."
docker build --platform linux/amd64 -t $ACR_URL/database:$VERSION_TAG ../database
docker push $ACR_URL/database:$VERSION_TAG
echo "Done."
echo ""

echo "--> Building and pushing 'frontend' (Version: $VERSION_TAG)..."
docker build --platform linux/amd64 -t $ACR_URL/frontend:$VERSION_TAG ../frontend
docker push $ACR_URL/frontend:$VERSION_TAG
echo "Done."
echo ""

echo "--> Building and pushing 'backend' (Version: $VERSION_TAG)..."
docker build --platform linux/amd64 -t $ACR_URL/backend:$VERSION_TAG ../backend
docker push $ACR_URL/backend:$VERSION_TAG
echo "Done."
echo ""

# The gateway service is removed as its role is replaced by Kubernetes Ingress.

echo "--> Building and pushing 'scraper' (Version: $VERSION_TAG)..."
docker build --platform linux/amd64 -t $ACR_URL/scraper:$VERSION_TAG ../scraping2
docker push $ACR_URL/scraper:$VERSION_TAG
echo "Done."
echo ""

echo "--> Building and pushing 'predictor' (Version: $VERSION_TAG)..."
docker build --platform linux/amd64 -f ../predictor/Dockerfile -t $ACR_URL/predictor:$VERSION_TAG ..
docker push $ACR_URL/predictor:$VERSION_TAG
echo "Done."
echo ""


echo "✅ All Docker images pushed successfully with tag: $VERSION_TAG"