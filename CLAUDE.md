# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Claude Code Settings

## Repository Overview

This is a React FastAPI template for building full-stack applications with React frontend (Vite) and FastAPI backend, designed for deployment to OpenShift using Docker containers and Kustomize.

## Project Structure

```
├── backend/              # FastAPI backend
│   ├── main.py          # Main FastAPI application
│   ├── pyproject.toml   # Python dependencies and project config
│   ├── uv.lock          # Locked dependency versions
│   └── Dockerfile       # Backend container
├── frontend/            # React frontend with Vite
│   ├── src/            # React source code
│   ├── package.json    # Node.js dependencies
│   └── Dockerfile      # Frontend container
├── k8s/                # Kubernetes/OpenShift manifests
│   ├── base/          # Base kustomize resources
│   └── overlays/      # Environment-specific overlays
└── scripts/           # Deployment automation scripts
```

## Development Commands

### Local Development (Node.js/Python)
```bash
make setup             # Install all dependencies
make dev              # Run both frontend and backend
make dev-frontend     # Run React dev server (port 8080)
make dev-backend      # Run FastAPI server (port 8000)
make help             # Show all available commands
```

### Building
```bash
make build                 # Build frontend and container images
```

### Testing
```bash
make test             # Run all tests (frontend and backend)
make test-frontend    # Run frontend tests only
make test-backend     # Run backend tests only
make lint             # Run linting
```

### Container Registry (Quay.io)
```bash
make build                           # Build frontend and container images (default: latest)
make push                            # Push images only (default: latest)
make build-prod                      # Build with prod tag (for production deployment)
make push-prod                       # Push with prod tag
make build TAG=latest                # Build with latest tag (explicit)
make push TAG=latest                 # Push with latest tag (explicit)
make TAG=v1.0.0 REGISTRY=quay.io/cfchase # Custom registry and tag
```

**Important**: The k8s overlays expect specific image tags:
- Development environment uses `latest` tag (default)
- Production environment requires `prod` tag

### OpenShift Deployment
```bash
# First build and push images with correct tags
make build && make push                     # For development (uses latest tag)
make build-prod && make push-prod           # For production

# Then deploy
make deploy           # Deploy to development
make deploy-prod      # Deploy to production
make undeploy         # Remove development deployment
make undeploy-prod    # Remove production deployment
make kustomize        # Preview dev manifests
make kustomize-prod   # Preview prod manifests
```

## Architecture

### Frontend (React + Vite)
- TypeScript for type safety
- Vite for fast development and building
- Axios for API communication
- Simple UI with health check button
- Vite dev server proxies /api/ to backend (local dev)
- Nginx proxies /api/ to backend service (production)

### Backend (FastAPI)
- Python 3.11 with FastAPI framework
- UV package manager for fast dependency management
- Uvicorn as ASGI server
- CORS middleware for frontend integration
- Minimal API with only health check endpoint at `/api/health`

### Deployment
- Docker containers for both services
- OpenShift Routes for external access
- Kustomize for environment-specific configuration
- Separate dev and prod overlays
- Quay.io as container registry
- OpenShift Security Context Constraints (SCC) compatible

## Configuration Files

### Environment Variables
- `backend/.env` - Backend configuration for local development only (copy from .env.example)
- `k8s/overlays/dev/.env` - Environment variables for dev deployments (used by kustomize secret generator)
- `k8s/overlays/prod/.env` - Environment variables for production deployments (used by kustomize secret generator)
- `frontend/.env` - Frontend configuration (copy from .env.example)

**Important**: All `.env*` files are excluded from Docker builds via `.dockerignore`. Deployment environment variables are managed through kustomize secret generators.

### Key Configuration
- `vite.config.ts` - Vite configuration with proxy to backend
- `docker-compose.yml` - Local development with containers
- `k8s/base/kustomization.yaml` - Base Kubernetes resources
- `k8s/overlays/*/kustomization.yaml` - Environment-specific configs

## API Endpoints

The FastAPI backend provides:
- `GET /` - Root endpoint  
- `GET /api/health` - Health check endpoint

## Development Workflow

1. Make changes to frontend (React) or backend (FastAPI)
2. Test locally with `make dev`
3. Build everything with `make build`
4. Build and push containers with `make build && make push`
5. Deploy to OpenShift with `make deploy` or `make deploy-prod`

## Common Tasks

### Adding New Dependencies
- Frontend: `cd frontend && npm install <package>`
- Backend: `cd backend && uv add <package>` (automatically updates pyproject.toml and uv.lock)
- Backend Dev Dependencies: `cd backend && uv add --dev <package>`

### Updating Container Images
- Update image tags in `k8s/base/kustomization.yaml`
- Update tags in overlay files for environment-specific versions

### Managing Secrets in OpenShift
- **Local Development**: Update `backend/.env` with your local API keys
- **Dev Environment**: Update `k8s/overlays/dev/.env` with your development API keys  
- **Production Environment**: Update `k8s/overlays/prod/.env` with your production API keys
- Environment variables include:
  - `ANTHROPIC_API_KEY`: Your Anthropic API key
  - `ANTHROPIC_MODEL`: Claude model to use (default: claude-sonnet-4-20250514)
  
**Important**: Secrets are automatically generated by kustomize from the .env files in each overlay directory. The deployment scripts (`make deploy` and `make deploy-prod`) use kustomize's built-in secret generator.

### Customizing for New Projects
- Update image names in kustomization files
- Update registry in build script
- Add API endpoints in `backend/main.py`
- Update frontend components in `frontend/src/`
- Update .env files with your actual API keys
- The template provides a minimal foundation - add your business logic as needed

## Git Commit Guidelines

When creating commits in this repository:
- **DO NOT** include Claude Code attribution in commit messages
- **DO NOT** include Claude-specific references in commit messages
- **DO NOT** mention "Generated with Claude Code" or similar attributions
- **DO NOT** add Co-Authored-By references to Claude
- Focus commit messages on the technical changes made
- Use conventional commit format when appropriate (feat:, fix:, docs:, etc.)