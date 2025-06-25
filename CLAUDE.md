# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a React FastAPI template for building full-stack applications with React frontend (Vite) and FastAPI backend, designed for deployment to OpenShift using Docker containers and Kustomize.

## Project Structure

```
├── backend/              # FastAPI backend
│   ├── main.py          # Main FastAPI application
│   ├── requirements.txt # Python dependencies
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
make test             # Run frontend tests
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
- `backend/.env` - Backend configuration (copy from .env.example)
- `frontend/.env` - Frontend configuration (copy from .env.example)

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
- Backend: Add to `backend/requirements.txt`

### Updating Container Images
- Update image tags in `k8s/base/kustomization.yaml`
- Update tags in overlay files for environment-specific versions

### Customizing for New Projects
- Update image names in kustomization files
- Update registry in build script
- Add API endpoints in `backend/main.py`
- Update frontend components in `frontend/src/`
- The template provides a minimal foundation - add your business logic as needed