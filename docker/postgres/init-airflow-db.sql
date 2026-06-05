-- Create Airflow metadata database
CREATE DATABASE airflow_db;

-- Grant privileges to dop_user
GRANT ALL PRIVILEGES ON DATABASE airflow_db TO dop_user;
