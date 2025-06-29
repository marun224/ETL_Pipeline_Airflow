"""
Unit tests for ETL integration functions.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Mock Airflow modules before importing our functions
sys.modules['airflow'] = Mock()
sys.modules['airflow.providers'] = Mock()
sys.modules['airflow.providers.postgres'] = Mock()
sys.modules['airflow.providers.postgres.hooks'] = Mock()
sys.modules['airflow.providers.postgres.hooks.postgres'] = Mock()

# Add the dags directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../dags'))

from etl_functions import extract_amazon_books, load_books_to_postgres
from tests.fixtures.sample_data import SAMPLE_BOOK_DATA


class TestETLFunctions(unittest.TestCase):
    """Test cases for ETL integration functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_ti = Mock()
    
    @patch('etl_functions.AmazonBookScraper')
    @patch('etl_functions.BookDataProcessor')
    def test_extract_amazon_books_success(self, mock_processor_class, mock_scraper_class):
        """Test successful book extraction."""
        # Mock scraper
        mock_scraper = Mock()
        mock_scraper.scrape_books.return_value = SAMPLE_BOOK_DATA
        mock_scraper_class.return_value = mock_scraper
        
        # Mock processor
        mock_processor = Mock()
        mock_processor.validate_book_data.return_value = SAMPLE_BOOK_DATA
        mock_processor.books_to_dataframe.return_value = Mock()
        mock_processor.dataframe_to_records.return_value = SAMPLE_BOOK_DATA
        mock_processor_class.return_value = mock_processor
        
        # Execute function
        extract_amazon_books(50, self.mock_ti)
        
        # Verify calls
        mock_scraper.scrape_books.assert_called_once_with(50)
        mock_processor.validate_book_data.assert_called_once_with(SAMPLE_BOOK_DATA)
        self.mock_ti.xcom_push.assert_called_once_with(
            key='book_data', 
            value=SAMPLE_BOOK_DATA
        )
    
    @patch('etl_functions.AmazonBookScraper')
    @patch('etl_functions.BookDataProcessor')
    def test_extract_amazon_books_no_data(self, mock_processor_class, mock_scraper_class):
        """Test extraction when no books are found."""
        # Mock scraper returning empty data
        mock_scraper = Mock()
        mock_scraper.scrape_books.return_value = []
        mock_scraper_class.return_value = mock_scraper
        
        # Mock processor
        mock_processor = Mock()
        mock_processor.validate_book_data.return_value = []
        mock_processor.books_to_dataframe.return_value = Mock()
        mock_processor.dataframe_to_records.return_value = []
        mock_processor_class.return_value = mock_processor
        
        # Execute function
        extract_amazon_books(50, self.mock_ti)
        
        # Verify XCom push with empty data
        self.mock_ti.xcom_push.assert_called_once_with(
            key='book_data', 
            value=[]
        )
    
    @patch('etl_functions.AmazonBookScraper')
    def test_extract_amazon_books_scraper_failure(self, mock_scraper_class):
        """Test extraction when scraper fails."""
        # Mock scraper to raise exception
        mock_scraper = Mock()
        mock_scraper.scrape_books.side_effect = Exception("Scraping failed")
        mock_scraper_class.return_value = mock_scraper
        
        # Execute function and expect exception
        with self.assertRaises(Exception) as context:
            extract_amazon_books(50, self.mock_ti)
        
        self.assertIn("Scraping failed", str(context.exception))
    
    @patch('etl_functions.DatabaseManager')
    def test_load_books_to_postgres_success(self, mock_db_manager_class):
        """Test successful book loading to PostgreSQL."""
        # Mock XCom data
        self.mock_ti.xcom_pull.return_value = SAMPLE_BOOK_DATA
        
        # Mock DatabaseManager
        mock_db_manager = Mock()
        mock_db_manager.insert_books.return_value = 3
        mock_db_manager_class.return_value = mock_db_manager
        
        # Execute function
        load_books_to_postgres(self.mock_ti)
        
        # Verify calls
        self.mock_ti.xcom_pull.assert_called_once_with(
            key='book_data', 
            task_ids='fetch_book_data'
        )
        mock_db_manager.insert_books.assert_called_once_with(SAMPLE_BOOK_DATA)
    
    def test_load_books_to_postgres_no_data(self):
        """Test loading when no data is available in XCom."""
        # Mock XCom to return None
        self.mock_ti.xcom_pull.return_value = None
        
        # Execute function and expect ValueError
        with self.assertRaises(ValueError) as context:
            load_books_to_postgres(self.mock_ti)
        
        self.assertIn("No book data found in XCom", str(context.exception))
    
    def test_load_books_to_postgres_empty_data(self):
        """Test loading when XCom contains empty data."""
        # Mock XCom to return empty list
        self.mock_ti.xcom_pull.return_value = []
        
        # Execute function and expect ValueError
        with self.assertRaises(ValueError) as context:
            load_books_to_postgres(self.mock_ti)
        
        self.assertIn("No book data found in XCom", str(context.exception))
    
    @patch('etl_functions.DatabaseManager')
    def test_load_books_to_postgres_no_insertion(self, mock_db_manager_class):
        """Test loading when no books are actually inserted."""
        # Mock XCom data
        self.mock_ti.xcom_pull.return_value = SAMPLE_BOOK_DATA
        
        # Mock DatabaseManager to return 0 insertions
        mock_db_manager = Mock()
        mock_db_manager.insert_books.return_value = 0
        mock_db_manager_class.return_value = mock_db_manager
        
        # Execute function and expect ValueError
        with self.assertRaises(ValueError) as context:
            load_books_to_postgres(self.mock_ti)
        
        self.assertIn("No books were inserted into the database", str(context.exception))
    
    @patch('etl_functions.DatabaseManager')
    def test_load_books_to_postgres_database_error(self, mock_db_manager_class):
        """Test loading when database operations fail."""
        # Mock XCom data
        self.mock_ti.xcom_pull.return_value = SAMPLE_BOOK_DATA
        
        # Mock DatabaseManager to raise exception
        mock_db_manager = Mock()
        mock_db_manager.insert_books.side_effect = Exception("Database connection failed")
        mock_db_manager_class.return_value = mock_db_manager
        
        # Execute function and expect exception
        with self.assertRaises(Exception) as context:
            load_books_to_postgres(self.mock_ti)
        
        self.assertIn("Database connection failed", str(context.exception))
    
    @patch('etl_functions.logger')
    @patch('etl_functions.AmazonBookScraper')
    @patch('etl_functions.BookDataProcessor')
    def test_extract_amazon_books_logging(self, mock_processor_class, mock_scraper_class, mock_logger):
        """Test that extraction function logs appropriately."""
        # Mock successful extraction
        mock_scraper = Mock()
        mock_scraper.scrape_books.return_value = SAMPLE_BOOK_DATA
        mock_scraper_class.return_value = mock_scraper
        
        mock_processor = Mock()
        mock_processor.validate_book_data.return_value = SAMPLE_BOOK_DATA
        mock_processor.books_to_dataframe.return_value = Mock()
        mock_processor.dataframe_to_records.return_value = SAMPLE_BOOK_DATA
        mock_processor_class.return_value = mock_processor
        
        # Execute function
        extract_amazon_books(50, self.mock_ti)
        
        # Verify logging
        mock_logger.info.assert_called_with("Extracted and processed 3 books")
    
    @patch('etl_functions.logger')
    @patch('etl_functions.DatabaseManager')
    def test_load_books_logging(self, mock_db_manager_class, mock_logger):
        """Test that loading function logs appropriately."""
        # Mock successful loading
        self.mock_ti.xcom_pull.return_value = SAMPLE_BOOK_DATA
        
        mock_db_manager = Mock()
        mock_db_manager.insert_books.return_value = 3
        mock_db_manager_class.return_value = mock_db_manager
        
        # Execute function
        load_books_to_postgres(self.mock_ti)
        
        # Verify logging
        mock_logger.info.assert_called_with("Successfully loaded 3 books to PostgreSQL")


if __name__ == '__main__':
    unittest.main()