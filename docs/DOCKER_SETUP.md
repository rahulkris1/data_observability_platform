# Docker Setup Guide

This guide will help you set up the local development environment for the Data Observability Platform.

## Prerequisites

- Windows 10/11 (64-bit) or macOS or Linux
- At least 4GB RAM available for Docker
- Administrator/sudo privileges

## Step 1: Install Docker Desktop

### Windows

1. Download Docker Desktop for Windows from [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)
2. Run the installer (`Docker Desktop Installer.exe`)
3. Follow the installation wizard
4. Restart your computer when prompted
5. Launch Docker Desktop from the Start menu
6. Wait for Docker to start (you'll see the Docker icon in the system tray)

### macOS

1. Download Docker Desktop for Mac from [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)
2. Open the downloaded `.dmg` file
3. Drag Docker to your Applications folder
4. Launch Docker from Applications
5. Authorize with your system password when prompted

### Linux

Follow the official Docker installation guide for your distribution:
- Ubuntu: [https://docs.docker.com/engine/install/ubuntu/](https://docs.docker.com/engine/install/ubuntu/)
- Debian: [https://docs.docker.com/engine/install/debian/](https://docs.docker.com/engine/install/debian/)
- Fedora: [https://docs.docker.com/engine/install/fedora/](https://docs.docker.com/engine/install/fedora/)

## Step 2: Verify Docker Installation

Open a terminal (PowerShell on Windows, Terminal on macOS/Linux) and run:

```bash
docker --version
docker-compose --version
```

You should see version information for both commands.

## Step 3: Start the Services

Navigate to the project root directory and start the Docker services:

```bash
cd path/to/data_observability_platform
docker-compose up -d
```

This will start:
- **PostgreSQL** on port `5432`
- **Redis** on port `6379`
- **MinIO** on ports `9000` (API) and `9001` (Console)

The `-d` flag runs the containers in detached mode (background).

## Step 4: Verify Service Startup

### Check Container Status

```bash
docker-compose ps
```

All services should show as "running" and "healthy".

### PostgreSQL Verification

Test PostgreSQL connection:

```bash
docker exec -it dop-postgres psql -U dop_user -d data_observability -c "SELECT version();"
```

You should see PostgreSQL version information.

### Redis Verification

Test Redis connection:

```bash
docker exec -it dop-redis redis-cli ping
```

You should see: `PONG`

### MinIO Verification

1. **Access MinIO Console**
   - Open your browser and go to: [http://localhost:9001](http://localhost:9001)
   - Login with:
     - Username: `minioadmin`
     - Password: `minioadmin123`

2. **Verify Buckets**
   - After logging in, click on "Buckets" in the left sidebar
   - You should see three buckets:
     - `raw-data`
     - `processed-data`
     - `audit-data`

## Step 5: Backend MinIO Connection Test

Install Python dependencies and run the connection test:

```bash
# Navigate to backend directory
cd backend

# Create/activate virtual environment (if not already done)
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run MinIO connection test
python test_minio_connection.py
```

You should see:
```
============================================================
MinIO Connection Test
============================================================

1. Testing MinIO connection...
   Endpoint: localhost:9000
   Access Key: minioadmin
   ✓ Connection successful!

2. Verifying required buckets...
   ✓ Bucket 'raw-data' (raw) exists
   ✓ Bucket 'processed-data' (processed) exists
   ✓ Bucket 'audit-data' (audit) exists

3. Testing upload/download operations...
   ✓ Upload test successful
   ✓ Download test successful
   ✓ Data integrity verified

============================================================
✓ All tests passed! MinIO is ready to use.
============================================================
```

## Step 6: View Logs

To view logs from any service:

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f postgres
docker-compose logs -f redis
docker-compose logs -f minio
```

Press `Ctrl+C` to stop following logs.

## Step 7: Stop Services

To stop all services:

```bash
docker-compose down
```

To stop and remove all data (volumes):

```bash
docker-compose down -v
```

⚠️ **Warning**: Using `-v` will delete all database data, Redis cache, and MinIO objects!

## Troubleshooting

### Port Already in Use

If you get a "port already in use" error:

1. Check what's using the port:
   ```bash
   # Windows
   netstat -ano | findstr :5432
   
   # macOS/Linux
   lsof -i :5432
   ```

2. Either stop the conflicting service or change the port in `docker-compose.yml`

### Container Won't Start

1. Check Docker Desktop is running
2. View specific container logs:
   ```bash
   docker-compose logs postgres
   ```
3. Try recreating the container:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

### MinIO Buckets Not Created

The `minio-setup` container handles bucket creation. Check its logs:

```bash
docker-compose logs minio-setup
```

If buckets are missing, restart the setup:

```bash
docker-compose restart minio-setup
```

### Cannot Connect to PostgreSQL

1. Ensure container is healthy:
   ```bash
   docker-compose ps postgres
   ```

2. Check PostgreSQL logs:
   ```bash
   docker-compose logs postgres
   ```

3. Try connecting from within the container:
   ```bash
   docker exec -it dop-postgres psql -U dop_user -d data_observability
   ```

## Quick Reference

### Service URLs

- **PostgreSQL**: `localhost:5432`
  - Database: `data_observability`
  - User: `dop_user`
  - Password: `dop_password`

- **Redis**: `localhost:6379`

- **MinIO API**: `http://localhost:9000`
- **MinIO Console**: `http://localhost:9001`
  - User: `minioadmin`
  - Password: `minioadmin123`

### Common Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View status
docker-compose ps

# View logs
docker-compose logs -f

# Restart a service
docker-compose restart <service-name>

# Rebuild and start
docker-compose up -d --build

# Remove all containers and volumes
docker-compose down -v
```

## Next Steps

After verifying all services are running:

1. Set up the backend API server (see backend README)
2. Set up the frontend development server (see frontend README)
3. Begin developing data observability features

---

**Note**: This setup is for local development only. Do not use these configurations in production!
