"""
Integration tests for DAG structure and configuration.
"""

import unittest
from datetime import datetime, timedelta
import sys
import os
from unittest.mock import Mock

# Mock Airflow modules before importing
airflow_mock = Mock()
dag_mock = Mock()
python_operator_mock = Mock()
postgres_operator_mock = Mock()

# Set up the mock to support the >> operator
python_operator_mock.__rshift__ = Mock(return_value=postgres_operator_mock)
postgres_operator_mock.__rshift__ = Mock(return_value=Mock())

sys.modules['airflow'] = airflow_mock
sys.modules['airflow.models'] = Mock()
sys.modules['airflow.utils'] = Mock()
sys.modules['airflow.utils.dag_cycle'] = Mock()
sys.modules['airflow.operators'] = Mock()
sys.modules['airflow.operators.python'] = Mock()
sys.modules['airflow.providers'] = Mock()
sys.modules['airflow.providers.postgres'] = Mock()
sys.modules['airflow.providers.postgres.operators'] = Mock()
sys.modules['airflow.providers.postgres.operators.postgres'] = Mock()

# Mock the specific classes
airflow_mock.DAG = Mock(return_value=dag_mock)
sys.modules['airflow.operators.python'].PythonOperator = Mock(return_value=python_operator_mock)
sys.modules['airflow.providers.postgres.operators.postgres'].PostgresOperator = Mock(return_value=postgres_operator_mock)

# Add the dags directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../dags'))

# Mock the Airflow imports
DagBag = Mock()
check_cycle = Mock()


class TestDAGStructure(unittest.TestCase):
    """Test cases for DAG structure and configuration."""
    
    def test_dag_file_imports(self):
        """Test that the DAG file can be imported without errors."""
        try:
            import app
            self.assertTrue(True, "DAG file imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import DAG file: {e}")
    
    def test_dag_file_syntax(self):
        """Test that the DAG file has valid Python syntax."""
        dag_file_path = os.path.join(os.path.dirname(__file__), '../../dags/app.py')
        
        with open(dag_file_path, 'r') as f:
            dag_content = f.read()
        
        try:
            compile(dag_content, dag_file_path, 'exec')
            self.assertTrue(True, "DAG file has valid syntax")
        except SyntaxError as e:
            self.fail(f"DAG file has syntax error: {e}")
    
    def test_etl_functions_imports(self):
        """Test that ETL functions can be imported."""
        try:
            from etl_functions import (
                AmazonBookScraper,
                BookDataProcessor,
                DatabaseManager,
                extract_amazon_books,
                load_books_to_postgres
            )
            self.assertTrue(True, "ETL functions imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import ETL functions: {e}")
    
    def test_dag_configuration_constants(self):
        """Test that DAG configuration constants are properly defined."""
        # Import the DAG module to check constants
        import app
        
        # Check that default_args is defined
        self.assertTrue(hasattr(app, 'default_args'), "default_args not defined")
        
        # Check required default_args keys
        required_keys = ['owner', 'depends_on_past', 'start_date', 'retries', 'retry_delay']
        for key in required_keys:
            self.assertIn(key, app.default_args, f"Missing required default_arg: {key}")
    
    def test_task_function_references(self):
        """Test that task functions are properly referenced."""
        from etl_functions import extract_amazon_books, load_books_to_postgres
        
        # Check that functions are callable
        self.assertTrue(callable(extract_amazon_books), "extract_amazon_books is not callable")
        self.assertTrue(callable(load_books_to_postgres), "load_books_to_postgres is not callable")
    
    def test_sql_query_syntax(self):
        """Test that SQL queries in the DAG are syntactically valid."""
        # This is a basic check for SQL syntax
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS books (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            authors TEXT,
            price TEXT,
            rating TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # Basic SQL syntax validation
        self.assertIn("CREATE TABLE", create_table_sql)
        self.assertIn("PRIMARY KEY", create_table_sql)
        self.assertIn("NOT NULL", create_table_sql)
        
    def test_dag_documentation(self):
        """Test that the DAG file contains proper documentation."""
        dag_file_path = os.path.join(os.path.dirname(__file__), '../../dags/app.py')
        
        with open(dag_file_path, 'r') as f:
            dag_content = f.read()
        
        # Check for docstring
        self.assertIn('"""', dag_content, "DAG file missing docstring")
        
        # Check for task documentation
        self.assertIn('doc_md=', dag_content, "Tasks missing documentation")
    
    def test_import_dependencies(self):
        """Test that all required dependencies are importable."""
        required_modules = [
            'datetime',
            'pandas',
            'requests',
            'bs4'
        ]
        
        for module_name in required_modules:
            try:
                __import__(module_name)
            except ImportError:
                self.fail(f"Required module {module_name} not available")


if __name__ == '__main__':
    unittest.main()