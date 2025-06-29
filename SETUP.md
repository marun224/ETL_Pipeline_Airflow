# ETL Pipeline Setup Guide

## Prerequisites

Before running this ETL pipeline, ensure you have the following installed:

- **Docker** (version 20.10 or higher)
- **Docker Compose** (version 1.29 or higher)
- **Git** for version control
- At least **4GB RAM** and **2 CPUs** available
- **10GB+ disk space** for containers and data

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/marun224/ETL_Pipeline_Airflow.git
cd ETL_Pipeline_Airflow
```

### 2. Environment Setup
The `.env` file contains the necessary environment variables. The `AIRFLOW_UID` is already configured.

### 3. Start the Services
```bash
# Initialize Airflow database and create admin user
docker-compose up airflow-init

# Start all services
docker-compose up -d
```

### 4. Access the Services

- **Airflow Web UI**: http://localhost:8080
  - Username: `airflow`
  - Password: `airflow`

- **PGAdmin**: http://localhost:5050
  - Email: `admin@admin.com`
  - Password: `root`

- **PostgreSQL Database**: localhost:5432
  - Username: `airflow`
  - Password: `airflow`
  - Database: `airflow`

## Configuration

### Setting up Airflow Connection

1. Open Airflow Web UI (http://localhost:8080)
2. Go to **Admin** → **Connections**
3. Create a new connection with the following details:
   - **Connection Id**: `books_connection`
   - **Connection Type**: `Postgres`
   - **Host**: `postgres`
   - **Schema**: `airflow`
   - **Login**: `airflow`
   - **Password**: `airflow`
   - **Port**: `5432`

### Configuring PGAdmin

1. Open PGAdmin (http://localhost:5050)
2. Add a new server:
   - **Name**: `Airflow PostgreSQL`
   - **Host**: `postgres`
   - **Port**: `5432`
   - **Username**: `airflow`
   - **Password**: `airflow`

## Running the Pipeline

1. In Airflow Web UI, navigate to **DAGs**
2. Find the `fetch_and_store_amazon_books` DAG
3. Toggle it **ON** to enable scheduling
4. Click **Trigger DAG** to run manually

## Monitoring

### Airflow Monitoring
- **DAG View**: Monitor pipeline execution status
- **Graph View**: Visualize task dependencies
- **Gantt Chart**: View task execution timeline
- **Task Logs**: Debug individual task failures

### Database Monitoring
- Use PGAdmin to query the `books` table
- Monitor data quality and completeness
- Set up custom queries for analytics

## Troubleshooting

### Common Issues

1. **Port Conflicts**
   - Ensure ports 8080, 5432, and 5050 are available
   - Modify docker-compose.yaml if needed

2. **Memory Issues**
   - Increase Docker memory allocation
   - Monitor container resource usage

3. **Connection Errors**
   - Verify PostgreSQL connection settings
   - Check container networking

### Logs
```bash
# View all service logs
docker-compose logs

# View specific service logs
docker-compose logs airflow-webserver
docker-compose logs postgres
```

## Stopping the Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: This will delete all data)
docker-compose down -v
```

## Development

### Adding New DAGs
1. Place new DAG files in the `dags/` directory
2. Airflow will automatically detect and load them

### Modifying the Pipeline
1. Edit `dags/app.py` for pipeline logic changes
2. Restart the scheduler: `docker-compose restart airflow-scheduler`

### Installing Additional Dependencies
1. Add packages to `requirements.txt`
2. Rebuild the Airflow image or use `_PIP_ADDITIONAL_REQUIREMENTS`

## Security Considerations

- Change default passwords in production
- Use environment variables for sensitive data
- Implement proper network security
- Regular security updates for containers

## Performance Optimization

- Adjust worker concurrency in docker-compose.yaml
- Monitor and tune PostgreSQL settings
- Implement data partitioning for large datasets
- Use connection pooling for database connections