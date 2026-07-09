#!/bin/bash

# Backend Production Startup Script for Data Observability Platform
set -e

echo "========================================="
echo "Data Observability Platform - Production"
echo "========================================="
echo "Starting Backend Service..."
echo ""

# Function to wait for service with timeout
wait_for_service() {
    local service_name=$1
    local check_command=$2
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Waiting for $service_name..."
    while [ $attempt -le $max_attempts ]; do
        if eval "$check_command" > /dev/null 2>&1; then
            echo "✅ $service_name is ready!"
            return 0
        fi
        echo "   Attempt $attempt/$max_attempts - $service_name not ready yet..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ ERROR: $service_name failed to become ready within timeout"
    exit 1
}

# Wait for PostgreSQL
wait_for_service "PostgreSQL" "pg_isready -h \$POSTGRES_HOST -p \$POSTGRES_PORT -U \$POSTGRES_USER"

# Wait for Redis
wait_for_service "Redis" "redis-cli -h \$REDIS_HOST -p \$REDIS_PORT -a \$REDIS_PASSWORD ping | grep -q PONG"

# Wait for MinIO (only if using MinIO storage provider)
if [ "$STORAGE_PROVIDER" = "minio" ]; then
    wait_for_service "MinIO" "curl -f http://\$MINIO_ENDPOINT/minio/health/live"
fi

echo ""
echo "📊 Running database migrations..."
alembic upgrade head
if [ $? -eq 0 ]; then
    echo "✅ Database migrations completed successfully"
else
    echo "❌ ERROR: Database migrations failed"
    exit 1
fi

echo ""
echo "🔍 Validating configuration..."
# Add any pre-flight checks here
if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "CHANGE_THIS_TO_A_SECURE_RANDOM_STRING_IN_PRODUCTION" ]; then
    echo "⚠️  WARNING: SECRET_KEY is not configured! Please set a secure secret key."
fi

if [ -z "$JWT_SECRET_KEY" ] || [ "$JWT_SECRET_KEY" = "CHANGE_THIS_TO_A_SECURE_RANDOM_STRING_IN_PRODUCTION" ]; then
    echo "⚠️  WARNING: JWT_SECRET_KEY is not configured! Please set a secure JWT secret key."
fi

echo ""
echo "🚀 Starting FastAPI application in production mode..."
echo "   Workers: ${WORKERS:-4}"
echo "   Host: 0.0.0.0"
echo "   Port: 8000"
echo "   Environment: production"
echo ""

# Start application with Gunicorn for production
exec gunicorn app.main:app \
    --workers ${WORKERS:-4} \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --worker-connections ${WORKER_CONNECTIONS:-1000} \
    --keep-alive ${KEEP_ALIVE:-5} \
    --access-logfile - \
    --error-logfile - \
    --log-level ${LOG_LEVEL:-info} \
    --timeout 120 \
    --graceful-timeout 30
