FROM apache/airflow:2.8.0-python3.11

USER root

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Copy requirements
COPY requirements-airflow.txt /opt/airflow/requirements-airflow.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /opt/airflow/requirements-airflow.txt

# Set working directory
WORKDIR /opt/airflow
