# ETL Pipeline Architecture

## Overview

This project implements a robust ETL (Extract, Transform, Load) pipeline using Apache Airflow for orchestration, designed to scrape book data from Amazon and store it in a PostgreSQL database.

## Architecture Components

### Core Services

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Airflow       │    │   PostgreSQL    │    │    PGAdmin      │
│   Webserver     │◄──►│   Database      │◄──►│   Interface     │
│   (Port 8080)   │    │   (Port 5432)   │    │   (Port 5050)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │
         ▼                       │
┌─────────────────┐              │
│   Airflow       │              │
│   Scheduler     │──────────────┘
└─────────────────┘
         │
         ▼
┌─────────────────┐    ┌─────────────────┐
│   Airflow       │◄──►│     Redis       │
│   Worker        │    │   Message       │
│   (Celery)      │    │   Broker        │
└─────────────────┘    └─────────────────┘
```

### Data Flow Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Amazon    │───►│   Extract   │───►│ Transform   │───►│    Load     │
│  Website    │    │   (Scrape)  │    │  (Clean)    │    │ (Database)  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                           │                   │                   │
                           ▼                   ▼                   ▼
                   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
                   │ Web Scraping│    │   Pandas    │    │ PostgreSQL  │
                   │ BeautifulSoup│    │ DataFrame   │    │   Insert    │
                   │  Requests   │    │ Processing  │    │ Operations  │
                   └─────────────┘    └─────────────┘    └─────────────┘
```

## Technical Stack

### Orchestration Layer
- **Apache Airflow 2.10.4**: Workflow orchestration and scheduling
- **CeleryExecutor**: Distributed task execution
- **Redis**: Message broker for Celery workers

### Data Processing Layer
- **Python 3.x**: Core programming language
- **Pandas**: Data manipulation and analysis
- **BeautifulSoup4**: HTML parsing for web scraping
- **Requests**: HTTP library for web requests

### Storage Layer
- **PostgreSQL 13**: Primary database for structured data
- **Docker Volumes**: Persistent storage for database

### Infrastructure Layer
- **Docker**: Containerization platform
- **Docker Compose**: Multi-container orchestration
- **PGAdmin**: Database administration interface

## DAG Architecture

### Task Dependencies
```
fetch_book_data
       │
       ▼
  create_table
       │
       ▼
insert_book_data
```

### Task Details

#### 1. Extract Task (`fetch_book_data`)
- **Function**: `get_amazon_data_books()`
- **Purpose**: Scrape Amazon for book data
- **Output**: Book data stored in XCom
- **Error Handling**: HTTP request retries, duplicate detection

#### 2. Transform Task (`create_table`)
- **Operator**: `PostgresOperator`
- **Purpose**: Ensure database table exists
- **SQL**: CREATE TABLE IF NOT EXISTS statement
- **Idempotency**: Safe to run multiple times

#### 3. Load Task (`insert_book_data`)
- **Function**: `insert_book_data_into_postgres()`
- **Purpose**: Insert processed data into PostgreSQL
- **Input**: XCom data from extract task
- **Error Handling**: Database connection validation

## Data Model

### Books Table Schema
```sql
CREATE TABLE books (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    authors TEXT,
    price TEXT,
    rating TEXT
);
```

### Data Types and Constraints
- **id**: Auto-incrementing primary key
- **title**: Required field, book title
- **authors**: Optional, author information
- **price**: String format to handle various price formats
- **rating**: String format to handle rating variations

## Security Architecture

### Network Security
- **Internal Docker Network**: Services communicate via internal network
- **Port Exposure**: Only necessary ports exposed to host
- **Service Isolation**: Each service runs in isolated container

### Authentication
- **Airflow**: Basic authentication (configurable)
- **PostgreSQL**: Username/password authentication
- **PGAdmin**: Web-based authentication

### Data Security
- **Environment Variables**: Sensitive data stored in .env files
- **Volume Mounts**: Secure data persistence
- **Network Policies**: Restricted inter-service communication

## Scalability Considerations

### Horizontal Scaling
- **Celery Workers**: Can be scaled across multiple machines
- **Database Sharding**: PostgreSQL can be partitioned for large datasets
- **Load Balancing**: Multiple Airflow webserver instances

### Vertical Scaling
- **Resource Allocation**: CPU and memory can be adjusted per service
- **Database Tuning**: PostgreSQL configuration optimization
- **Worker Concurrency**: Adjustable worker thread counts

## Monitoring and Observability

### Airflow Monitoring
- **Web UI**: Real-time DAG and task monitoring
- **Logs**: Centralized logging for all tasks
- **Metrics**: Built-in performance metrics
- **Alerts**: Email notifications for failures

### Database Monitoring
- **PGAdmin**: Query performance and database health
- **Connection Pooling**: Monitor database connections
- **Storage Usage**: Track database growth

### Infrastructure Monitoring
- **Docker Stats**: Container resource usage
- **Health Checks**: Service availability monitoring
- **Log Aggregation**: Centralized log collection

## Performance Optimization

### Database Optimization
- **Indexing**: Strategic index creation for query performance
- **Connection Pooling**: Efficient database connection management
- **Batch Processing**: Bulk insert operations

### Airflow Optimization
- **Task Parallelism**: Concurrent task execution
- **Resource Allocation**: Optimal CPU and memory allocation
- **DAG Optimization**: Efficient task dependency design

### Scraping Optimization
- **Request Throttling**: Respectful scraping practices
- **Caching**: Avoid redundant requests
- **Error Recovery**: Robust error handling and retries

## Deployment Strategies

### Development Environment
- **Local Docker**: Full stack on single machine
- **Hot Reloading**: Code changes reflected immediately
- **Debug Mode**: Enhanced logging and error reporting

### Production Environment
- **Container Orchestration**: Kubernetes or Docker Swarm
- **Load Balancing**: Multiple service instances
- **Backup Strategy**: Regular database backups
- **Monitoring**: Comprehensive observability stack

## Future Enhancements

### Potential Improvements
1. **Data Quality**: Implement data validation and quality checks
2. **Real-time Processing**: Stream processing capabilities
3. **Machine Learning**: Predictive analytics on book data
4. **API Layer**: REST API for data access
5. **Dashboard**: Business intelligence dashboard
6. **Multi-source**: Support for additional data sources