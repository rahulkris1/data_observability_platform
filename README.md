# Data Observability Platform

## About

Data Observability Platform is a local-first application for validating and monitoring datasets before they are loaded into a data warehouse.

The project reads CSV or JSON files, runs a series of data quality checks, generates dataset profiling information, stores audit logs, and displays the results through a web dashboard. Apache Airflow is used to orchestrate the pipeline, while Celery handles background processing.

Everything is designed to run locally using Docker. After completing the local implementation, the same project can be connected to AWS services such as Amazon S3, AWS Glue, and CloudWatch.

---

## Features

- Upload CSV and JSON datasets
- Dataset ingestion using PySpark
- Schema validation
- Null value validation
- Data type validation
- Duplicate record detection
- Primary and foreign key validation
- Dataset profiling
- Audit logging
- Warehouse loading
- Pipeline monitoring
- Retry failed validations
- Health score dashboard

---

## Workflow

```
Upload Dataset
        ↓
Store File (MinIO)
        ↓
Read Dataset (PySpark)
        ↓
Run Validation Rules
        ↓
Generate Dataset Profile
        ↓
Store Audit Logs
        ↓
Load Data into Warehouse
        ↓
Update Dashboard
```

---

## Tech Stack

### Backend

- FastAPI
- PySpark
- PostgreSQL
- SQLAlchemy
- Redis
- Celery
- Apache Airflow

### Frontend

- Next.js
- React
- Tailwind CSS
- Axios

### Local Infrastructure

- Docker
- Docker Compose
- MinIO

### Future Cloud Integration

- Amazon S3
- AWS Glue
- Amazon CloudWatch

---

## Project Structure

```
data_observability_platform/

├── backend/
├── frontend/
├── airflow/
├── glue_jobs/
├── tests/
├── docs/
└── docker-compose.yml
```

---

## Running the Project

Start Docker services.

```bash
docker compose up -d
```

Start the backend.

```bash
cd backend
uvicorn app.main:app --reload
```

Start the frontend.

```bash
cd frontend
npm install
npm run dev
```

Open the application.

```
Frontend : http://localhost:3000
Backend  : http://localhost:8000
Swagger  : http://localhost:8000/docs
Airflow  : http://localhost:8080
```

---

## Validation Rules

The application currently validates:

- Schema structure
- Required columns
- Null values
- Data types
- Duplicate records
- Primary key uniqueness
- Foreign key relationships

Validation results are stored in PostgreSQL and displayed on the dashboard.

---

## Dashboard

The dashboard provides:

- Dataset upload history
- Validation results
- Audit history
- Dataset profiling
- Pipeline execution status
- Warehouse status
- Health score
- Logs and metrics

---

## Sample Test Files

Use the sample datasets included with the project to test different scenarios.

- customers_valid.csv
- customers_missing_columns.csv
- customers_null_values.csv
- customers_duplicate_ids.csv
- orders_valid.csv
- orders_invalid_fk.csv
- products_valid.csv

---

## Future Improvements

The project currently runs completely in a local environment.

The next step is to integrate:

- Amazon S3 for file storage
- AWS Glue for distributed data processing
- Amazon CloudWatch for monitoring and logging

The application is designed so these services can be added without changing the overall workflow.

---