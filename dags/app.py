
"""
Amazon Books ETL Pipeline DAG

This DAG orchestrates the extraction, transformation, and loading of book data
from Amazon into a PostgreSQL database.

Tasks:
1. fetch_book_data: Extract book data from Amazon
2. create_table: Ensure the books table exists in PostgreSQL
3. insert_book_data: Load the processed data into the database
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator

# Import our refactored ETL functions
from etl_functions import extract_amazon_books, load_books_to_postgres


# DAG configuration
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 6, 20),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': False,
    'email_on_retry': False,
}

# Create the DAG
dag = DAG(
    'fetch_and_store_amazon_books',
    default_args=default_args,
    description='ETL pipeline to fetch book data from Amazon and store it in PostgreSQL',
    schedule_interval=timedelta(days=1),
    catchup=False,
    tags=['etl', 'amazon', 'books', 'postgresql'],
)

# Task 1: Extract book data from Amazon
fetch_book_data_task = PythonOperator(
    task_id='fetch_book_data',
    python_callable=extract_amazon_books,
    op_args=[50],  # Number of books to fetch
    dag=dag,
    doc_md="""
    ### Extract Book Data
    
    This task scrapes book data from Amazon search results for "data engineering books".
    It extracts title, author, price, and rating information and stores it in XCom.
    
    **Parameters:**
    - num_books: Number of books to extract (default: 50)
    
    **Output:**
    - XCom key 'book_data': List of book dictionaries
    """,
)

# Task 2: Create database table
create_table_task = PostgresOperator(
    task_id='create_table',
    postgres_conn_id='books_connection',
    sql="""
    CREATE TABLE IF NOT EXISTS books (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        authors TEXT,
        price TEXT,
        rating TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    dag=dag,
    doc_md="""
    ### Create Books Table
    
    This task ensures the books table exists in the PostgreSQL database.
    The table includes an auto-incrementing ID and timestamp for data tracking.
    """,
)

# Task 3: Load data into PostgreSQL
insert_book_data_task = PythonOperator(
    task_id='insert_book_data',
    python_callable=load_books_to_postgres,
    dag=dag,
    doc_md="""
    ### Load Book Data
    
    This task retrieves book data from XCom and inserts it into the PostgreSQL database.
    It includes error handling and logging for monitoring data quality.
    """,
)

# Define task dependencies
fetch_book_data_task >> create_table_task >> insert_book_data_task

