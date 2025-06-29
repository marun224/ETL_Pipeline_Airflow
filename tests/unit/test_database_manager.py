"""
Unit tests for DatabaseManager class.
"""

import unittest
from unittest.mock import Mock, patch, call
import sys
import os

# Add the dags directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../dags'))

from etl_functions import DatabaseManager
from tests.fixtures.sample_data import SAMPLE_BOOK_DATA


class TestDatabaseManager(unittest.TestCase):
    """Test cases for DatabaseManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_postgres_hook = Mock()
        self.db_manager = DatabaseManager(self.mock_postgres_hook)
    
    def test_init(self):
        """Test DatabaseManager initialization."""
        self.assertEqual(self.db_manager.postgres_hook, self.mock_postgres_hook)
    
    def test_insert_books_success(self):
        """Test successful book insertion."""
        # Mock successful database operations
        self.mock_postgres_hook.run.return_value = None
        
        result = self.db_manager.insert_books(SAMPLE_BOOK_DATA)
        
        self.assertEqual(result, 3)  # Should insert 3 books
        self.assertEqual(self.mock_postgres_hook.run.call_count, 3)
        
        # Verify the SQL query and parameters
        expected_query = """
        INSERT INTO books (title, authors, price, rating)
        VALUES (%s, %s, %s, %s)
        """
        
        # Check first call
        first_call = self.mock_postgres_hook.run.call_args_list[0]
        self.assertEqual(first_call[0][0].strip(), expected_query.strip())
        self.assertEqual(
            first_call[1]['parameters'], 
            ('Data Engineering with Python', 'John Smith', '29', '4.5 out of 5 stars')
        )
    
    def test_insert_books_empty_data(self):
        """Test insertion with empty book data."""
        result = self.db_manager.insert_books([])
        
        self.assertEqual(result, 0)
        self.mock_postgres_hook.run.assert_not_called()
    
    def test_insert_books_partial_failure(self):
        """Test insertion with some failures."""
        # Mock database to fail on second book
        def side_effect(*args, **kwargs):
            if 'Jane Doe' in str(kwargs.get('parameters', '')):
                raise Exception("Database error")
            return None
        
        self.mock_postgres_hook.run.side_effect = side_effect
        
        result = self.db_manager.insert_books(SAMPLE_BOOK_DATA)
        
        self.assertEqual(result, 2)  # Should insert 2 out of 3 books
        self.assertEqual(self.mock_postgres_hook.run.call_count, 3)
    
    def test_insert_books_complete_failure(self):
        """Test insertion when all operations fail."""
        # Mock database to always fail
        self.mock_postgres_hook.run.side_effect = Exception("Database connection error")
        
        result = self.db_manager.insert_books(SAMPLE_BOOK_DATA)
        
        self.assertEqual(result, 0)
        self.assertEqual(self.mock_postgres_hook.run.call_count, 3)
    
    def test_create_books_table_success(self):
        """Test successful table creation."""
        self.mock_postgres_hook.run.return_value = None
        
        result = self.db_manager.create_books_table()
        
        self.assertTrue(result)
        self.mock_postgres_hook.run.assert_called_once()
        
        # Verify the SQL query
        call_args = self.mock_postgres_hook.run.call_args[0][0]
        self.assertIn("CREATE TABLE IF NOT EXISTS books", call_args)
        self.assertIn("id SERIAL PRIMARY KEY", call_args)
        self.assertIn("title TEXT NOT NULL", call_args)
    
    def test_create_books_table_failure(self):
        """Test table creation failure."""
        self.mock_postgres_hook.run.side_effect = Exception("Permission denied")
        
        result = self.db_manager.create_books_table()
        
        self.assertFalse(result)
        self.mock_postgres_hook.run.assert_called_once()
    
    def test_insert_books_data_validation(self):
        """Test that insert_books validates data structure."""
        invalid_data = [
            {
                "Title": "Valid Book",
                "Author": "Valid Author",
                "Price": "25",
                "Rating": "4.0 out of 5 stars"
            },
            {
                "WrongKey": "Invalid Book",  # Wrong key structure
                "Author": "Valid Author",
                "Price": "30",
                "Rating": "4.5 out of 5 stars"
            }
        ]
        
        # Mock to track what gets called
        self.mock_postgres_hook.run.return_value = None
        
        # This should handle the KeyError gracefully
        result = self.db_manager.insert_books(invalid_data)
        
        # Should only insert the valid book
        self.assertEqual(result, 1)
        # Should attempt to insert both books (one succeeds, one fails due to KeyError)
        self.assertEqual(self.mock_postgres_hook.run.call_count, 1)
    
    @patch('etl_functions.logger')
    def test_insert_books_logging(self, mock_logger):
        """Test that appropriate logging occurs during insertion."""
        self.mock_postgres_hook.run.return_value = None
        
        self.db_manager.insert_books(SAMPLE_BOOK_DATA)
        
        # Check that info log was called
        mock_logger.info.assert_called_with("Inserted 3 books into database")
    
    @patch('etl_functions.logger')
    def test_insert_books_error_logging(self, mock_logger):
        """Test error logging during insertion failures."""
        self.mock_postgres_hook.run.side_effect = Exception("Database error")
        
        self.db_manager.insert_books(SAMPLE_BOOK_DATA[:1])
        
        # Check that error log was called
        mock_logger.error.assert_called()
        error_call = mock_logger.error.call_args[0][0]
        self.assertIn("Failed to insert book", error_call)
    
    @patch('etl_functions.logger')
    def test_create_table_logging(self, mock_logger):
        """Test logging during table creation."""
        self.mock_postgres_hook.run.return_value = None
        
        self.db_manager.create_books_table()
        
        mock_logger.info.assert_called_with("Books table created successfully")
    
    def test_insert_books_sql_injection_protection(self):
        """Test that SQL injection is prevented through parameterized queries."""
        malicious_data = [
            {
                "Title": "'; DROP TABLE books; --",
                "Author": "Hacker",
                "Price": "0",
                "Rating": "1.0 out of 5 stars"
            }
        ]
        
        self.mock_postgres_hook.run.return_value = None
        
        result = self.db_manager.insert_books(malicious_data)
        
        self.assertEqual(result, 1)
        
        # Verify that parameters are passed separately (not concatenated into SQL)
        call_args = self.mock_postgres_hook.run.call_args
        self.assertIn('parameters', call_args[1])
        self.assertEqual(
            call_args[1]['parameters'][0], 
            "'; DROP TABLE books; --"
        )


if __name__ == '__main__':
    unittest.main()