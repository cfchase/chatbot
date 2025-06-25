# PatternFly FastAPI Template

A full-stack application template with React frontend (Vite) using PatternFly and FastAPI backend, ready for deployment to OpenShift.

## Architecture

- **Frontend**: React with TypeScript and Vite - simple UI with health check button
- **Backend**: FastAPI with Python - minimal API with health check endpoint
- **Containerization**: Docker and Docker Compose
- **Deployment**: OpenShift with Kustomize
- **Container Registry**: Quay.io
- **API Routing**: Vite proxy for local development, Nginx proxy for production

## Quick Start

### Prerequisites

- Node.js 22+
- Python 3.11+
- Docker
- OpenShift CLI (`oc`)
- Kustomize

### Local Development

1. **Clone and setup**:
   ```bash
   git clone https://github.com/cfchase/patternfly-fastapi-template
   cd patternfly-fastapi-template
   make setup
   # or alternatively: npm run setup
   ```

2. **Run locally**:
   ```bash
   # Run both frontend and backend
   make dev
   
   # Or run separately
   make dev-backend   # Backend on http://localhost:8000
   make dev-frontend  # Frontend on http://localhost:8080
   
   # Alternative npm commands
   npm run dev        # Run both
   npm run dev:backend npm run dev:frontend
   ```

### Building

```bash
# Build frontend and container images
make build
```

## Project Structure

```
├── backend/              # FastAPI backend
│   ├── main.py          # FastAPI application
│   ├── requirements.txt # Python dependencies
│   ├── Dockerfile       # Backend container
│   └── .env.example     # Environment variables
├── frontend/            # React frontend
│   ├── src/             # Source code
│   ├── package.json     # Node dependencies
│   ├── Dockerfile       # Frontend container
│   ├── nginx.conf       # Nginx configuration
│   └── .env.example     # Environment variables
├── k8s/                 # Kubernetes/OpenShift manifests
│   ├── base/           # Base kustomize resources
│   └── overlays/       # Environment-specific configs
│       ├── dev/        # Development environment
│       └── prod/       # Production environment
├── scripts/            # Deployment scripts
│   ├── build-and-push.sh
│   └── deploy.sh
└── docker-compose.yml  # Local development with Docker
```

## Deployment

### Container Images

Build and push to quay.io:

```bash
# Build frontend and container images (default tag: latest)
make build

# Build for production environment (uses prod tag)
make build-prod

# Build with specific tag and registry
make build TAG=v1.0.0 REGISTRY=quay.io/cfchase

# Push images (must build first, default tag: latest)
make push

# Build and push for development deployment (default)
make build
make push

# Build and push for production deployment
make build-prod
make push-prod

# Alternative script usage (defaults to latest tag)
./scripts/build-images.sh
./scripts/push-images.sh

# Or with specific tag
./scripts/build-images.sh prod quay.io/cfchase
./scripts/push-images.sh prod quay.io/cfchase
```

**Important**: The k8s overlays expect specific image tags:
- Development: `latest` tag (default)
- Production: `prod` tag

Make sure to build and push with the correct tag before deploying.

### OpenShift Deployment

1. **Login to OpenShift**:
   ```bash
   oc login --server=https://your-openshift-cluster
   ```

2. **Build and Push Images**:
   ```bash
   # For development (uses latest tag by default)
   make build
   make push
   
   # For production
   make build-prod
   make push-prod
   ```

3. **Deploy to development**:
   ```bash
   make deploy-dev
   # or: ./scripts/deploy.sh dev
   ```

4. **Deploy to production**:
   ```bash
   make deploy-prod
   # or: ./scripts/deploy.sh prod
   ```

5. **Preview deployments**:
   ```bash
   make kustomize       # Preview dev manifests
   make kustomize-prod  # Preview prod manifests
   ```

6. **Remove deployments**:
   ```bash
   make undeploy        # Remove development deployment
   make undeploy-prod   # Remove production deployment
   ```

## Configuration

### Backend Configuration

Copy `backend/.env.example` to `backend/.env` and configure:

```env
PORT=8000
ENVIRONMENT=development
```

### Frontend Configuration

Copy `frontend/.env.example` to `frontend/.env` and configure:

```env
VITE_API_URL=http://localhost:8000
```

## API Endpoints

The backend provides the following endpoints:

- `GET /` - Root endpoint
- `GET /api/health` - Health check endpoint

## Customization

### Update Container Registry

1. Update image references in `k8s/base/kustomization.yaml`
2. Update registry in `scripts/build-and-push.sh`
3. Update image references in overlay files

### Add Environment Variables

1. Add to `.env.example` files
2. Update deployment manifests in `k8s/base/`
3. Update Docker configurations

## License

Apache License 2.0