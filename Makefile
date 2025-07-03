# React FastAPI Template Makefile

# Container Registry Operations
REGISTRY ?= quay.io/cfchase
TAG ?= latest


.PHONY: help setup dev build build-dev build-prod test clean push push-dev push-prod deploy deploy-dev deploy-prod undeploy undeploy-prod kustomize kustomize-prod

# Default target
help: ## Show this help message
	@echo "React FastAPI Template - Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Setup and Installation
setup: ## Install all dependencies
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Installing backend dependencies..."
	cd backend && uv sync --extra dev
	@echo "Setup complete!"

setup-frontend: ## Install frontend dependencies only
	cd frontend && npm install

setup-backend: ## Install backend dependencies only
	cd backend && uv sync --extra dev

# Development
dev: ## Run both frontend and backend in development mode
	@echo "Starting development servers..."
	npx concurrently "make dev-backend" "make dev-frontend"

dev-frontend: ## Run frontend development server
	cd frontend && npm run dev

dev-backend: ## Run backend development server
	cd backend && uv run python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Building
build-frontend: ## Build frontend for production
	cd frontend && npm run build

build-dev: build-frontend ## Build frontend and container images for development
	@echo "Building container images for $(REGISTRY) with tag $(TAG)..."
	./scripts/build-images.sh $(TAG) $(REGISTRY)

build: build-dev ## Alias for build-dev

build-prod: build-frontend ## Build frontend and container images for production
	@echo "Building container images for $(REGISTRY) with tag prod..."
	./scripts/build-images.sh prod $(REGISTRY)

# Testing
test: ## Run all tests (frontend and backend)
	@echo "Running frontend tests..."
	cd frontend && npm run test
	@echo "Running backend tests..."
	cd backend && uv run pytest

test-frontend: ## Run frontend tests
	cd frontend && npm run test

test-backend: ## Run backend tests
	cd backend && uv run pytest

test-backend-verbose: ## Run backend tests with verbose output
	cd backend && uv run pytest -v

lint: ## Run linting on frontend
	cd frontend && npm run lint

push-dev: ## Push container images to registry for development
	@echo "Pushing images to $(REGISTRY) with tag $(TAG)..."
	./scripts/push-images.sh $(TAG) $(REGISTRY)

push: push-dev ## Alias for push-dev

push-prod: ## Push container images to registry with prod tag
	@echo "Pushing images to $(REGISTRY) with tag prod..."
	./scripts/push-images.sh prod $(REGISTRY)

# OpenShift/Kubernetes Deployment
kustomize: ## Preview development deployment manifests
	kustomize build k8s/overlays/dev

kustomize-prod: ## Preview production deployment manifests
	kustomize build k8s/overlays/prod

deploy-dev: ## Deploy to development environment
	@echo "Deploying to development..."
	./scripts/deploy.sh dev

deploy: deploy-dev ## Alias for deploy-dev

deploy-prod: ## Deploy to production environment
	@echo "Deploying to production..."
	./scripts/deploy.sh prod

undeploy: ## Remove development deployment
	@echo "Removing development deployment..."
	./scripts/undeploy.sh dev

undeploy-prod: ## Remove production deployment
	@echo "Removing production deployment..."
	./scripts/undeploy.sh prod

# Environment Setup
env-setup: ## Copy environment example files
	@echo "Setting up environment files..."
	@if [ ! -f backend/.env ]; then cp backend/.env.example backend/.env; echo "Created backend/.env"; fi
	@if [ ! -f frontend/.env ]; then cp frontend/.env.example frontend/.env; echo "Created frontend/.env"; fi

env-setup-k8s: ## Copy Kubernetes example files for configuration
	@echo "Setting up Kubernetes configuration files..."
	@for env in dev prod; do \
		if [ ! -f k8s/overlays/$$env/.env ]; then \
			cp k8s/overlays/$$env/.env.example k8s/overlays/$$env/.env; \
			echo "Created k8s/overlays/$$env/.env - EDIT THIS FILE with your API keys"; \
		fi; \
		if [ ! -f k8s/overlays/$$env/mcp-config.json ]; then \
			cp k8s/overlays/$$env/mcp-config.example.json k8s/overlays/$$env/mcp-config.json; \
			echo "Created k8s/overlays/$$env/mcp-config.json"; \
		fi; \
	done
	@echo "⚠️  IMPORTANT: Edit the .env files with your actual API keys before deploying!"

# Health Checks
health-backend: ## Check backend health
	@echo "Checking backend health..."
	@curl -f http://localhost:8000/api/health || echo "Backend not responding"

health-frontend: ## Check if frontend is running
	@echo "Checking frontend..."
	@curl -f http://localhost:8080 || echo "Frontend not responding"

# Cleanup
clean: ## Clean build artifacts and dependencies
	@echo "Cleaning build artifacts..."
	rm -rf frontend/dist
	rm -rf frontend/node_modules
	rm -rf backend/__pycache__
	rm -rf backend/.pytest_cache

clean-all: clean ## Clean everything

# Development Workflow
fresh-start: clean setup env-setup ## Clean setup for new development
	@echo "Fresh development environment ready!"

quick-start: setup env-setup dev ## Quick start for development

