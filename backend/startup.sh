#!/bin/bash

# Backend Startup Script for Data Observability Platform
set -e

echo "Starting Data Observability Platform Backend..."

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
until pg_isready -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done
echo "PostgreSQL is up - continuing..."

# Wait for Redis to be ready
echo "Waiting for Redis..."
until redis-cli -h $REDIS_HOST -p $REDIS_PORT ping | grep -q PONG; do
  echo "Redis is unavailable - sleeping"
  sleep 2
done
echo "Redis is up - continuing..."

# Wait for MinIO to be ready
echo "Waiting for MinIO..."
until curl -f http://$MINIO_ENDPOINT/minio/health/live > /dev/null 2>&1; do
  echo "MinIO is unavailable - sleeping"
  sleep 2
done
echo "MinIO is up - continuing..."

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application
echo "Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
