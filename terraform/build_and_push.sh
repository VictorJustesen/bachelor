#!/bin/bash

# This script builds and pushes all necessary Docker images to Azure Container Registry.
# It tags images with the ':latest' tag.

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
ACR_NAME="bacheloracr"
ACR_URL="$ACR_NAME.azurecr.io"
TAG="latest"

# --- Script ---

echo "--> Logging in to Azure Container Registry: $ACR_NAME"
az acr login --name $ACR_NAME
echo "Login Succeeded."
echo ""

# --- Build and Push Each Service ---

echo "--> Building and pushing 'database' (Tag: $TAG)..."
docker build --platform linux/amd64 -t $ACR_URL/database:$TAG ../database
docker push $ACR_URL/database:$TAG
echo "Done."
echo ""

echo "--> Building and pushing 'frontend' (Tag: $TAG)..."
docker build --platform linux/amd64 -t $ACR_URL/frontend:$TAG ../frontend
docker push $ACR_URL/frontend:$TAG
echo "Done."
echo ""

echo "--> Building and pushing 'backend' (Tag: $TAG)..."
docker build --platform linux/amd64 -t $ACR_URL/backend:$TAG ../backend
docker push $ACR_URL/backend:$TAG
echo "Done."
echo ""

echo "--> Building and pushing 'scraper' (Tag: $TAG)..."
docker build --platform linux/amd64 -t $ACR_URL/scraper:$TAG ../scraping2
docker push $ACR_URL/scraper:$TAG
echo "Done."
echo ""

echo "--> Building and pushing 'predictor' (Tag: $TAG)..."
docker build --platform linux/amd64 -f ../predictor/Dockerfile -t $ACR_URL/predictor:$TAG ..
docker push $ACR_URL/predictor:$TAG
echo "Done."
echo ""


echo "✅ All Docker images pushed successfully with tag: $TAG"