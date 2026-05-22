# Quick Start Guide

Get the Data Observability Platform up and running in minutes!

## Prerequisites

- Docker Desktop installed ([Setup Guide](DOCKER_SETUP.md))
- Python 3.9+ (for backend)
- Node.js 18+ (for frontend)

## Quick Setup (All Components)

### 1. Start Docker Services

```bash
# From project root
docker-compose up -d

# Verify all services are healthy
docker-compose ps
```

### 2. Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Test MinIO connection
python test_minio_connection.py

# Start backend server
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`

### 3. Frontend Setup

```bash
# Navigate to frontend (new terminal)
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at: `http://localhost:3000`

## Verify Everything Works

### 1. Check Docker Services

- **PostgreSQL**: Should be running on port 5432
  ```bash
  docker exec -it dop-postgres psql -U dop_user -d data_observability -c "SELECT 1;"
  ```

- **Redis**: Should be running on port 6379
  ```bash
  docker exec -it dop-redis redis-cli ping
  ```

- **MinIO Console**: Open [http://localhost:9001](http://localhost:9001)
  - Username: `minioadmin`
  - Password: `minioadmin123`
  - Verify buckets: `raw-data`, `processed-data`, `audit-data`

### 2. Check Backend

- API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)

### 3. Check Frontend

- Dashboard: [http://localhost:3000/dashboard](http://localhost:3000/dashboard)

## Environment Variables

### Backend (.env)

Located at: `backend/.env`

```env
# Application
DEBUG=True

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=dop_user
POSTGRES_PASSWORD=dop_password
POSTGRES_DB=data_observability

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_URL=redis://localhost:6379/0

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET_RAW=raw-data
MINIO_BUCKET_PROCESSED=processed-data
MINIO_BUCKET_AUDIT=audit-data
```

### Frontend (.env.local)

Located at: `frontend/.env.local`

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_VERSION=/api/v1

# Application
NEXT_PUBLIC_APP_NAME=Data Observability Platform
```

## Common Tasks

### Stop All Services

```bash
# Stop Docker services
docker-compose down

# Stop backend (Ctrl+C in backend terminal)

# Stop frontend (Ctrl+C in frontend terminal)
```

### Restart Services

```bash
# Restart Docker services
docker-compose restart

# Restart backend
# Ctrl+C then run: uvicorn main:app --reload

# Restart frontend
# Ctrl+C then run: npm run dev
```

### View Logs

```bash
# Docker services
docker-compose logs -f

# Backend logs
# Check terminal where uvicorn is running

# Frontend logs
# Check terminal where npm run dev is running
```

### Reset Data

```bash
# ⚠️ WARNING: This deletes all data!
docker-compose down -v
docker-compose up -d
```

## Project Structure

```
data_observability_platform/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── core/
│   │   │   └── config.py        # Configuration settings
│   │   ├── storage/
│   │   │   └── minio_client.py  # MinIO client
│   │   ├── api/                 # API endpoints
│   │   ├── models/              # Database models
│   │   └── schemas/             # Pydantic schemas
│   ├── .env                     # Backend environment variables
│   ├── requirements.txt         # Python dependencies
│   └── test_minio_connection.py # MinIO verification script
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   └── dashboard.tsx    # Main dashboard
│   │   ├── components/
│   │   │   └── MetricCard.tsx   # Reusable metric card
│   │   ├── layouts/
│   │   │   └── DashboardLayout.tsx
│   │   └── services/
│   │       └── apiClient.ts     # Axios API client
│   ├── .env.local               # Frontend environment variables
│   └── package.json             # Node dependencies
├── docker-compose.yml           # Docker services configuration
└── docs/
    ├── DOCKER_SETUP.md          # Detailed Docker setup
    └── QUICK_START.md           # This file
```

## Development Workflow

1. **Start Docker services** (once per session)
   ```bash
   docker-compose up -d
   ```

2. **Start backend** (in one terminal)
   ```bash
   cd backend
   .venv/Scripts/activate  # or source .venv/bin/activate
   cd app
   uvicorn main:app --reload
   ```

3. **Start frontend** (in another terminal)
   ```bash
   cd frontend
   npm run dev
   ```

4. **Develop features** - Files will auto-reload on changes

5. **Stop services** when done
   ```bash
   docker-compose down
   # Ctrl+C in backend and frontend terminals
   ```

## Troubleshooting

See [DOCKER_SETUP.md](DOCKER_SETUP.md#troubleshooting) for detailed troubleshooting steps.

### Quick Fixes

**Port conflicts:**
```bash
# Check what's using port 8000 (backend)
netstat -ano | findstr :8000

# Check what's using port 3000 (frontend)
netstat -ano | findstr :3000
```

**Services not connecting:**
```bash
# Check all containers are healthy
docker-compose ps

# View specific service logs
docker-compose logs postgres
docker-compose logs redis
docker-compose logs minio
```

**Frontend can't reach backend:**
- Verify backend is running on port 8000
- Check `NEXT_PUBLIC_API_URL` in `frontend/.env.local`
- Check browser console for errors

## Next Steps

1. ✅ All services running
2. ✅ Backend can connect to MinIO
3. ✅ Frontend dashboard displays
4. 📝 Start implementing data observability features!

---

Need help? Check the detailed [Docker Setup Guide](DOCKER_SETUP.md) or the main [README](../README.md).
