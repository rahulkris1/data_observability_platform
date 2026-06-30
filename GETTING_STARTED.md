# Getting Started with Docker

## Prerequisites

Before you can run the Data Observability Platform with Docker, you need to install Docker Desktop.

### Step 1: Install Docker Desktop

1. **Download Docker Desktop**
   - Visit: https://www.docker.com/products/docker-desktop/
   - Download the Windows version
   - File size: ~500MB

2. **Install Docker Desktop**
   - Run the installer
   - Follow the installation wizard
   - Enable WSL 2 backend if prompted (recommended)
   - **Restart your computer** after installation

3. **Start Docker Desktop**
   - Find Docker Desktop in your Start Menu
   - Wait for Docker to start completely (whale icon in system tray)
   - First start may take 2-3 minutes

4. **Configure Docker Desktop**
   - Open Docker Desktop Settings (gear icon)
   - Go to **Resources** → **Advanced**
   - Set:
     - **CPUs**: 4 or more
     - **Memory**: 8 GB or more
     - **Disk image size**: 60 GB or more
   - Click **Apply & Restart**

### Step 2: Verify Installation

Run the prerequisites check:

```powershell
.\check-docker-prerequisites.ps1
```

You should see all checks pass with green checkmarks (✓).

## Quick Start

Once Docker Desktop is installed and running:

### 1. Start All Services

```powershell
.\start-docker.ps1
```

First time startup will:
- Download base images (~2GB)
- Build custom images
- Start all 8 services
- Initialize databases
- Create storage buckets

**Expected time**: 5-10 minutes on first run

### 2. Verify Services

```powershell
.\verify-docker-setup.ps1
```

### 3. Access the Platform

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Airflow**: http://localhost:8080 (admin/admin123)
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin123)

## Common Commands

### Start/Stop Services

```powershell
# Start all services
.\start-docker.ps1

# Start with rebuild
.\start-docker.ps1 -Rebuild

# Clean start (removes all data)
.\start-docker.ps1 -Clean

# Stop all services (preserves data)
docker compose down

# Stop all services and remove data
docker compose down -v
```

### View Logs

```powershell
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f frontend
```

### Restart Services

```powershell
# Restart all
docker compose restart

# Restart specific service
docker compose restart backend
```

## Troubleshooting

### Docker Desktop Won't Start

1. Check Windows updates are installed
2. Ensure virtualization is enabled in BIOS
3. Try restarting your computer
4. Check Docker Desktop logs: `%LOCALAPPDATA%\Docker\log.txt`

### Containers Won't Start

1. Check Docker Desktop is running (whale icon in system tray)
2. View logs: `docker compose logs backend`
3. Verify prerequisites: `.\check-docker-prerequisites.ps1`
4. Try clean restart: `.\start-docker.ps1 -Clean`

### Port Already in Use

If you see errors like "port is already allocated":

1. Check what's using the port:
   ```powershell
   netstat -ano | findstr :8000
   ```

2. Stop the conflicting service, or

3. Change the port in `docker-compose.yml`:
   ```yaml
   ports:
     - "8001:8000"  # Use port 8001 instead
   ```

### Out of Disk Space

1. Remove unused Docker data:
   ```powershell
   docker system prune -a
   ```

2. Check disk usage:
   ```powershell
   docker system df
   ```

### Services Show as Unhealthy

1. Wait 2-3 minutes for full startup
2. Check specific service logs:
   ```powershell
   docker compose logs backend
   ```
3. Verify health status:
   ```powershell
   docker inspect --format='{{json .State.Health}}' dop-backend
   ```

## Next Steps

Once all services are running:

1. **Explore the API**: http://localhost:8000/docs
2. **Check the Frontend**: http://localhost:3000
3. **View Airflow DAGs**: http://localhost:8080
4. **Browse MinIO**: http://localhost:9001

## Additional Resources

- [Docker Documentation](DOCKER.md) - Detailed Docker configuration guide
- [API Documentation](http://localhost:8000/docs) - Interactive API docs
- [Docker Desktop Docs](https://docs.docker.com/desktop/windows/) - Official Docker Desktop documentation

## Getting Help

If you encounter issues:

1. Run prerequisites check: `.\check-docker-prerequisites.ps1`
2. Run verification: `.\verify-docker-setup.ps1`
3. Check service logs: `docker compose logs [service-name]`
4. Review DOCKER.md for detailed troubleshooting
