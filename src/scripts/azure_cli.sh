#!/bin/bash

# Exit on error
set -e

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    source .env
fi

# Configuration variables
RESOURCE_GROUP="weather-data-service-rg"
LOCATION="eastus"
AKS_CLUSTER_NAME="weather-data-aks"
ACR_NAME="weatherdataacr2025"
AKS_NODE_COUNT=1
AKS_NODE_VM_SIZE="Standard_DS2_v2"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper function for logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%dT%H:%M:%S%z')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%dT%H:%M:%S%z')] ERROR: $1${NC}" >&2
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%dT%H:%M:%S%z')] WARNING: $1${NC}"
}

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    error "Azure CLI is not installed. Please install it first."
    exit 1
fi

# Login to Azure
log "Logging into Azure..."
az login --only-show-errors

# Register necessary resource providers
log "Registering resource providers..."
PROVIDERS=("Microsoft.ContainerService" "Microsoft.ContainerRegistry" "Microsoft.Compute")
for provider in "${PROVIDERS[@]}"; do
    az provider register --namespace $provider --only-show-errors
    log "Registered $provider"
done

# Create resource group
log "Creating resource group..."
az group create \
    --name $RESOURCE_GROUP \
    --location $LOCATION \
    --only-show-errors

# Create Azure Container Registry
log "Creating Azure Container Registry..."
az acr create \
    --resource-group $RESOURCE_GROUP \
    --name $ACR_NAME \
    --sku Basic \
    --admin-enabled true \
    --only-show-errors

# Get ACR credentials
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query "username" -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv)

# Create AKS cluster
log "Creating AKS cluster (this may take a few minutes)..."
az aks create \
    --resource-group $RESOURCE_GROUP \
    --name $AKS_CLUSTER_NAME \
    --node-count $AKS_NODE_COUNT \
    --node-vm-size $AKS_NODE_VM_SIZE \
    --enable-managed-identity \
    --attach-acr $ACR_NAME \
    --enable-addons monitoring \
    --generate-ssh-keys \
    --only-show-errors

# Get AKS credentials
log "Getting AKS credentials..."
az aks get-credentials \
    --resource-group $RESOURCE_GROUP \
    --name $AKS_CLUSTER_NAME \
    --overwrite-existing

# Build and push Docker image
log "Building and pushing Docker image..."
az acr build \
    --registry $ACR_NAME \
    --image weather-app:v1 \
    --file Dockerfile \
    . \
    --only-show-errors

# Create GitHub Action secrets (if GitHub CLI is installed)
if command -v gh &> /dev/null; then
    log "Setting up GitHub secrets..."
    
    # Get Azure credentials for GitHub Actions
    SUBSCRIPTION_ID=$(az account show --query id -o tsv)
    
    # Create Azure service principal
    SP_JSON=$(az ad sp create-for-rbac \
        --name "weather-app-sp" \
        --role contributor \
        --scopes /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP \
        -o json)
    
    # Set GitHub secrets
    gh secret set AZURE_CREDENTIALS -b"$SP_JSON"
    gh secret set REGISTRY_USERNAME -b"$ACR_USERNAME"
    gh secret set REGISTRY_PASSWORD -b"$ACR_PASSWORD"
else
    warn "GitHub CLI not installed. Please manually set up the following secrets in your GitHub repository:"
    echo "AZURE_CREDENTIALS: $(echo $SP_JSON | base64)"
    echo "REGISTRY_USERNAME: $ACR_USERNAME"
    echo "REGISTRY_PASSWORD: $ACR_PASSWORD"
fi

# Apply Kubernetes configurations
log "Applying Kubernetes configurations..."
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Get the public IP
log "Waiting for service to get public IP..."
external_ip=""
while [ -z $external_ip ]; do
    external_ip=$(kubectl get svc weather-app-service \
        --template="{{range .status.loadBalancer.ingress}}{{.ip}}{{end}}")
    [ -z "$external_ip" ] && sleep 10
done

log "==================================================="
log "Setup completed successfully!"
log "Service is available at: http://$external_ip"
log "ACR Login Server: $ACR_NAME.azurecr.io"
log "==================================================="

# Cleanup instructions
cat << EOF
To clean up all resources when you're done:
    az group delete --name $RESOURCE_GROUP --yes --no-wait

To get kubectl credentials again in the future:
    az aks get-credentials --resource-group $RESOURCE_GROUP --name $AKS_CLUSTER_NAME
EOF