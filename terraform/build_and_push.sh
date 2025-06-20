#!/bin/bash

# This script builds and pushes all necessary Docker images to Azure Container Registry.
# It is designed to be run from INSIDE the 'terraform' directory.

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
# Your Azure Container Registry name (the short name, not the full URL)
ACR_NAME="bacheloracr"
ACR_URL="$ACR_NAME.azurecr.io"

# --- Script ---

echo "--> Logging in to Azure Container Registry: $ACR_NAME"
az acr login --name $ACR_NAME
echo "Login Succeeded."
echo ""

# --- Build and Push Each Service ---
# Note: The paths like ../database are relative to this script's location inside the terraform folder.

echo "--> Building and pushing 'database' image..."
docker build -t $ACR_URL/database:latest ../database
docker push $ACR_URL/database:latest
echo "Done."
echo ""

echo "--> Building and pushing 'frontend' image..."
docker build -t $ACR_URL/frontend:latest ../frontend
docker push $ACR_URL/frontend:latest
echo "Done."
echo ""

echo "--> Building and pushing 'backend' image..."
docker build -t $ACR_URL/backend:latest ../backend
docker push $ACR_URL/backend:latest
echo "Done."
echo ""

echo "--> Building and pushing 'api-gateway' image..."
docker build -t $ACR_URL/gateway:latest ../gateway
docker push $ACR_URL/gateway:latest
echo "Done."
echo ""

echo "--> Building and pushing 'scraper' image..."
docker build -t $ACR_URL/scraper:latest ../scraping2
docker push $ACR_URL/scraper:latest
echo "Done."
echo ""

echo "--> Building and pushing 'predictor' image..."
# Note: This command's file path (-f) and context (..) are also relative to this script's location.
docker build -f ../predictor/Dockerfile -t $ACR_URL/predictor:latest ..
docker push $ACR_URL/predictor:latest
echo "Done."
echo ""

echo "✅ All Docker images have been built and pushed successfully!"