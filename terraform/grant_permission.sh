#!/bin/bash

# --- Configuration ---
ACR_NAME="bacheloracr"
AKS_NAME="bacheloraks"
RESOURCE_GROUP="bachelorrg"

echo "--> Granting permissions for AKS cluster '$AKS_NAME' to pull from ACR '$ACR_NAME'..."

# Get the full Resource ID of your ACR
ACR_ID=$(az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query "id" --output tsv)

# Get the Principal ID of your AKS cluster's managed identity
# (This is the 'user account' for your cluster)
ASSIGNEE_ID=$(az aks show --name $AKS_NAME --resource-group $RESOURCE_GROUP --query "identity.principalId" --output tsv)

# Create the role assignment that gives the AKS cluster the 'AcrPull' role for the ACR
az role assignment create --assignee $ASSIGNEE_ID --role AcrPull --scope $ACR_ID

echo ""
echo "✅ Permission granted. It may take up to a minute for permissions to apply."