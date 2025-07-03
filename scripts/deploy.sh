#!/bin/bash

# Deploy application to OpenShift using kustomize
# Usage: ./scripts/deploy.sh [environment] [namespace]

set -e

DEPLOY_ENV=${1:-dev}
NAMESPACE=${2:-chatbot-${DEPLOY_ENV}}

if [[ "$DEPLOY_ENV" != "dev" && "$DEPLOY_ENV" != "prod" ]]; then
    echo "Error: Environment must be 'dev' or 'prod'"
    exit 1
fi

echo "Deploying to $DEPLOY_ENV environment..."
echo "Namespace: $NAMESPACE"

# Check if oc is available
if ! command -v oc &> /dev/null; then
    echo "Error: oc (OpenShift CLI) is not installed or not in PATH"
    exit 1
fi

# Check if kustomize is available
if ! command -v kustomize &> /dev/null; then
    echo "Error: kustomize is not installed or not in PATH"
    exit 1
fi

# Check if logged in to OpenShift
if ! oc whoami &> /dev/null; then
    echo "Error: Not logged in to OpenShift. Please run 'oc login' first."
    exit 1
fi

# Check for required configuration files
if [ ! -f "k8s/overlays/$DEPLOY_ENV/.env" ]; then
    echo "Error: Missing .env file for $DEPLOY_ENV environment"
    echo "Please copy .env.example to .env and configure with your values:"
    echo "  cp k8s/overlays/$DEPLOY_ENV/.env.example k8s/overlays/$DEPLOY_ENV/.env"
    echo "  # Edit k8s/overlays/$DEPLOY_ENV/.env with your API keys"
    exit 1
fi

if [ ! -f "k8s/overlays/$DEPLOY_ENV/mcp-config.json" ]; then
    echo "Warning: Missing mcp-config.json file for $DEPLOY_ENV environment"
    echo "Creating default empty MCP configuration..."
    echo '{"mcpServers":{}}' > "k8s/overlays/$DEPLOY_ENV/mcp-config.json"
    echo "✅ Created k8s/overlays/$DEPLOY_ENV/mcp-config.json with empty MCP servers"
    echo "   To add MCP servers, copy from example: cp k8s/overlays/$DEPLOY_ENV/mcp-config.example.json k8s/overlays/$DEPLOY_ENV/mcp-config.json"
fi

# Create namespace if it doesn't exist
echo "Creating namespace if it doesn't exist..."
oc create namespace "$NAMESPACE" --dry-run=client -o yaml | oc apply -f -

# Apply kustomize configuration
echo "Applying kustomize configuration..."
kustomize build "k8s/overlays/$DEPLOY_ENV" | oc apply -f -

echo "Deployment complete!"
echo "You can check the status with:"
echo "  oc get pods -n $NAMESPACE"
echo "  oc get routes -n $NAMESPACE"