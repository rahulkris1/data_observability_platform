# Docker Setup for Data Observability Platform

This directory contains Docker configuration for running the entire Data Observability Platform locally.

## Services

The platform consists of the following services:

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 3000 | Next.js web application |
| Backend API | 8000 | FastAPI backend service |
| PostgreSQL | 5432 | Primary database |
| Redis | 6379 | Cache and message broker |
| MinIO | 9000, 9001 | Object storage (S3-compatible) |
| Airflow Webserver | 8080 | Workflow orchestration UI |
| Airflow Scheduler | - | Workflow scheduler |
| Celery Worker | - | Background task processor |

## Prerequisites

- Docker Desktop installed and running
- At least 8GB RAM allocated to Docker
- At least 20GB free disk space

## Quick Start

### 1. Build and Start All Services

```powershell
# Option 1: Use the quick start script
.\start-docker.ps1

# Option 2: Manual start
docker-compose up -d --build
```

### 2. Verify Services

```powershell
.\verify-docker-setup.ps1
```

### 3. Access the Services

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Airflow UI**: http://localhost:8080 (admin/admin123)
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin123)

## Service Health Checks

All services include health checks:

```powershell
# Check all containers
docker-compose ps

# Check specific service health
docker inspect --format='{{.State.Health.Status}}' dop-backend
docker inspect --format='{{.State.Health.Status}}' dop-frontend
```

## Common Operations

### View Logs

```powershell
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Restart Services

```powershell
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### Stop Services

```powershell
# Stop all (preserve data)
docker-compose down

# Stop all and remove volumes (clean slate)
docker-compose down -v
```

### Rebuild Services

```powershell
# Rebuild all
docker-compose up -d --build

# Rebuild specific service
docker-compose up -d --build backend
docker-compose up -d --build frontend
```

## Networking

All services communicate through the `dop-network` bridge network:

- Services can reference each other by container name
- Backend connects to PostgreSQL via `postgres:5432`
- Backend connects to Redis via `redis:6379`
- Backend connects to MinIO via `minio:9000`
- Frontend connects to Backend via Docker network (internal) or `localhost:8000` (from host)

## Volumes

Persistent data is stored in Docker volumes:

- `postgres_data`: PostgreSQL database files
- `redis_data`: Redis persistence
- `minio_data`: Object storage data
- `airflow_logs`: Airflow execution logs
- `airflow_plugins`: Airflow plugins

To reset all data:

```powershell
docker-compose down -v
```

## Development Workflow

### Hot Reload

Both backend and frontend support hot reload:

- **Backend**: Changes to Python files trigger Uvicorn reload
- **Frontend**: Changes to source files trigger Next.js fast refresh

Volume mounts ensure code changes are reflected immediately.

### Database Migrations

Migrations run automatically on backend startup via `startup.sh`:

```powershell
# Manual migration (if needed)
docker-compose exec backend alembic upgrade head

# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "description"
```

### Access Container Shell

```powershell
# Backend
docker-compose exec backend bash

# Frontend
docker-compose exec frontend sh

# PostgreSQL
docker-compose exec postgres psql -U dop_user -d data_observability
```

## Troubleshooting

### Container Won't Start

1. Check logs:
   ```powershell
   docker-compose logs backend
   ```

2. Check container status:
   ```powershell
   docker-compose ps
   ```

3. Verify Docker resources (RAM, disk)

### Service Unhealthy

1. Wait for startup (some services take 30-60 seconds)
2. Check health status:
   ```powershell
   docker inspect --format='{{json .State.Health}}' dop-backend
   ```

### Port Conflicts

If ports are already in use:

1. Stop conflicting services, or
2. Modify ports in `docker-compose.yml`:
   ```yaml
   ports:
     - "8001:8000"  # Map to different host port
   ```

### Database Connection Issues

1. Ensure PostgreSQL is healthy:
   ```powershell
   docker-compose ps postgres
   ```

2. Check backend logs for connection errors:
   ```powershell
   docker-compose logs backend | Select-String "postgres"
   ```

3. Verify database is initialized:
   ```powershell
   docker-compose exec postgres psql -U dop_user -d data_observability -c "\dt"
   ```

### Clear Everything and Start Fresh

```powershell
# Stop all containers
docker-compose down -v

# Remove images (optional)
docker-compose down -v --rmi all

# Rebuild and start
docker-compose up -d --build
```

## Resource Usage

Monitor resource usage:

```powershell
# Real-time stats
docker stats

# Check disk usage
docker system df
```

Expected resource usage:
- RAM: 4-6GB total
- Disk: 5-10GB

## Production Considerations

**Important**: This Docker setup is designed for local development only.

**DO NOT use this configuration for production**:
- Hardcoded credentials
- No TLS/SSL
- Development mode for services
- Direct port exposure
- No backup strategies
- No high availability

For production deployment, consider:
- Kubernetes or managed container services
- Secrets management (AWS Secrets Manager, Azure Key Vault)
- Load balancers and reverse proxies
- Database replication and backups
- Monitoring and alerting
- Log aggregation
- Resource limits and autoscaling

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        dop-network                          │
│                                                             │
│  ┌──────────┐      ┌──────────┐      ┌────────────────┐   │
│  │ Frontend │─────▶│  Backend │─────▶│   PostgreSQL   │   │
│  │  :3000   │      │   :8000  │      │     :5432      │   │
│  └──────────┘      └──────────┘      └────────────────┘   │
│                          │                                  │
│                          ├──────────▶┌────────────────┐   │
│                          │           │     Redis      │   │
│                          │           │     :6379      │   │
│                          │           └────────────────┘   │
│                          │                                  │
│                          ├──────────▶┌────────────────┐   │
│                          │           │     MinIO      │   │
│                          │           │  :9000, :9001  │   │
│                          │           └────────────────┘   │
│                          │                                  │
│                          ├──────────▶┌────────────────┐   │
│                          │           │    Airflow     │   │
│  ┌──────────────┐        │           │     :8080      │   │
│  │Celery Worker │────────┤           └────────────────┘   │
│  └──────────────┘        │                                  │
│                          │                                  │
│                          ▼                                  │
│                     [All Services]                          │
└─────────────────────────────────────────────────────────────┘
```

## Support

For issues or questions:
1. Check logs: `docker-compose logs [service]`
2. Run verification: `.\verify-docker-setup.ps1`
3. Refer to service-specific documentation
