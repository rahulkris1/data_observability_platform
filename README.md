# Data Observability Platform

## About

I built this project to learn how modern data pipelines validate and monitor data before it is loaded into a warehouse.

The application accepts CSV or JSON datasets, validates the data, stores audit information, profiles the dataset, and shows the results in a web dashboard.

The entire project runs locally using Docker. Later, it can be connected to AWS services like S3, Glue, and CloudWatch without changing the overall application flow.

---

## What it does

The workflow looks like this:

```
Upload Dataset
        ↓
Store File
        ↓
Read with PySpark
        ↓
Run Data Validations
        ↓
Generate Data Profile
        ↓
Save Audit Information
        ↓
Load into Warehouse
        ↓
Display Results on Dashboard
```

---

## Validations

Currently the application checks:

- Schema validation
- Missing columns
- Null values
- Data types
- Duplicate records
- Primary key validation
- Foreign key validation

If any validation fails, the dataset is marked as failed and the reason is stored in the audit logs.

---

## Tech Stack

### Backend

- FastAPI
- PySpark
- PostgreSQL
- SQLAlchemy
- Celery
- Redis
- Apache Airflow

### Frontend

- Next.js
- React
- Tailwind CSS

### Local Infrastructure

- Docker
- Docker Compose
- MinIO

---

## Running the project

Clone the repository.

Start Docker services.

```bash
docker compose up
```

Run the backend.

```bash
cd backend
uvicorn app.main:app --reload
```

Run the frontend.

```bash
cd frontend
npm install
npm run dev
```

---

## Project Structure

```
backend/
frontend/
airflow/
glue_jobs/
tests/
docs/
```

---

## Sample datasets

The project includes sample datasets for testing different scenarios.

- Valid dataset
- Missing columns
- Null values
- Duplicate records
- Invalid foreign keys

---

## Future Work

The application currently runs completely locally.

The next step is connecting it with:

- Amazon S3
- AWS Glue
- Amazon CloudWatch

The goal is to keep the application logic the same and only replace the local infrastructure.

---

## Notes

This project was built as a learning project to understand data quality, observability, pipeline orchestration, and modern data engineering workflows.