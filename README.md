# Data Observability Platform

A comprehensive platform for monitoring data quality, lineage, and health across your data infrastructure.

## Overview

The Data Observability Platform provides real-time insights into your data pipelines, quality metrics, and overall data health. Built with modern technologies for scalability and ease of use.

## Features

- 📊 **Real-time Dashboard** - Monitor data quality metrics at a glance
- 🗄️ **Object Storage** - MinIO integration for raw, processed, and audit data
- 🔍 **Data Quality Tracking** - Track completeness, accuracy, and timeliness
- 📈 **Metrics & Analytics** - Comprehensive data observability metrics
- 🎯 **Minimal Setup** - Easy local development with Docker Compose

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Primary database
- **Redis** - Caching layer
- **MinIO** - S3-compatible object storage
- **Python 3.9+**

### Frontend
- **Next.js** - React framework
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **Axios** - HTTP client

### Infrastructure
- **Docker & Docker Compose** - Containerization
- **Local Development** - No cloud dependencies required

## Quick Start

### Prerequisites

- Docker Desktop ([installation guide](docs/DOCKER_SETUP.md))
- Python 3.9+
- Node.js 18+

### Setup Steps

1. **Clone and navigate to the project**
   ```bash
   cd data_observability_platform
   ```

2. **Start Docker services**
   ```bash
   docker-compose up -d
   ```

3. **Set up backend**
   ```bash
   cd backend
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # macOS/Linux
   pip install -r requirements.txt
   python test_minio_connection.py
   ```

4. **Set up frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

5. **Access the application**
   - Frontend: [http://localhost:3000/dashboard](http://localhost:3000/dashboard)
   - Backend API: [http://localhost:8000/docs](http://localhost:8000/docs)
   - MinIO Console: [http://localhost:9001](http://localhost:9001)

For detailed setup instructions, see [Quick Start Guide](docs/QUICK_START.md).

## Project Structure

```
data_observability_platform/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── main.py            # Application entry point
│   │   ├── core/              # Core configuration
│   │   ├── storage/           # MinIO client
│   │   ├── api/               # API endpoints
│   │   ├── models/            # Database models
│   │   ├── schemas/           # Pydantic schemas
│   │   └── services/          # Business logic
│   ├── .env                   # Backend configuration
│   └── requirements.txt       # Python dependencies
├── frontend/                  # Next.js frontend
│   ├── src/
│   │   ├── pages/            # Next.js pages
│   │   ├── components/       # Reusable components
│   │   ├── layouts/          # Layout components
│   │   └── services/         # API client
│   ├── .env.local           # Frontend configuration
│   └── package.json         # Node dependencies
├── docker-compose.yml       # Docker services
├── docs/                    # Documentation
│   ├── DOCKER_SETUP.md     # Docker installation guide
│   └── QUICK_START.md      # Quick start guide
└── README.md               # This file
```

## Docker Services

The platform uses the following Docker services:

- **PostgreSQL** (port 5432) - Primary database
  - Database: `data_observability`
  - User: `dop_user`
  - Password: `dop_password`

- **Redis** (port 6379) - Cache layer
  - Default configuration

- **MinIO** (ports 9000, 9001) - Object storage
  - API: `localhost:9000`
  - Console: `localhost:9001`
  - Credentials: `minioadmin` / `minioadmin123`
  - Buckets: `raw-data`, `processed-data`, `audit-data`

## Configuration

### Backend Environment Variables

Located at `backend/.env`:

```env
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=dop_user
POSTGRES_PASSWORD=dop_password
POSTGRES_DB=data_observability

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET_RAW=raw-data
MINIO_BUCKET_PROCESSED=processed-data
MINIO_BUCKET_AUDIT=audit-data
```

### Frontend Environment Variables

Located at `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_VERSION=/api/v1
```

## Development

### Start All Services

```bash
# Start Docker services
docker-compose up -d

# Start backend (in one terminal)
cd backend
.venv/Scripts/activate
cd app
uvicorn main:app --reload

# Start frontend (in another terminal)
cd frontend
npm run dev
```

### Stop Services

```bash
# Stop Docker services
docker-compose down

# Stop backend and frontend with Ctrl+C
```

### View Logs

```bash
# Docker services
docker-compose logs -f

# Specific service
docker-compose logs -f postgres
docker-compose logs -f redis
docker-compose logs -f minio
```

## Testing

### Backend

```bash
cd backend
python test_minio_connection.py
```

### Frontend

```bash
cd frontend
npm run lint
npm run build
```

## What's NOT Included

This is a minimal local development setup. The following are intentionally NOT included:

- ❌ Kubernetes
- ❌ Prometheus
- ❌ Grafana
- ❌ OpenTelemetry
- ❌ Sentry
- ❌ CI/CD pipelines
- ❌ Production monitoring
- ❌ Authentication
- ❌ Advanced caching
- ❌ Airflow (not yet)
- ❌ Celery (not yet)
- ❌ PySpark (not yet)

## Documentation

- [Docker Setup Guide](docs/DOCKER_SETUP.md) - Detailed Docker installation and setup
- [Quick Start Guide](docs/QUICK_START.md) - Get up and running quickly

## Troubleshooting

### Common Issues

1. **Port conflicts** - Make sure ports 3000, 5432, 6379, 8000, 9000, 9001 are available
2. **Docker not running** - Ensure Docker Desktop is running
3. **Containers not healthy** - Check logs with `docker-compose logs`

See [Docker Setup Guide - Troubleshooting](docs/DOCKER_SETUP.md#troubleshooting) for detailed solutions.

## License

This project is for development and educational purposes.

## Version

v0.1.0 - Initial minimal setup with Docker services, backend, and frontend dashboard.
