"""
End-to-end integration tests for the ETL pipeline.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
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

from etl_functions import (
    AmazonBookScraper, 
    BookDataProcessor, 
    DatabaseManager,
    extract_amazon_books,
    load_books_to_postgres
)
from tests.fixtures.sample_data import SAMPLE_BOOK_DATA
from tests.fixtures.sample_html import SAMPLE_AMAZON_HTML


class TestEndToEndETL(unittest.TestCase):
    """End-to-end integration tests for the ETL pipeline."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_ti = Mock()
        self.mock_postgres_hook = Mock()
    
    @patch('etl_functions.requests.get')
    def test_full_etl_pipeline_success(self, mock_get):
        """Test the complete ETL pipeline from scraping to database insertion."""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = SAMPLE_AMAZON_HTML.encode('utf-8')
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Step 1: Test scraping
        scraper = AmazonBookScraper()
        scraped_books = scraper.scrape_books(num_books=3, max_pages=1)
        
        self.assertEqual(len(scraped_books), 3)
        self.assertEqual(scraped_books[0]["Title"], "Data Engineering with Python")
        
        # Step 2: Test data processing
        processor = BookDataProcessor()
        validated_books = processor.validate_book_data(scraped_books)
        df = processor.books_to_dataframe(validated_books)
        records = processor.dataframe_to_records(df)
        
        self.assertEqual(len(records), 3)
        self.assertIsInstance(df, pd.DataFrame)
        
        # Step 3: Test database operations
        db_manager = DatabaseManager(self.mock_postgres_hook)
        
        # Mock successful database operations
        self.mock_postgres_hook.run.return_value = None
        
        # Test table creation
        table_created = db_manager.create_books_table()
        self.assertTrue(table_created)
        
        # Test data insertion
        inserted_count = db_manager.insert_books(records)
        self.assertEqual(inserted_count, 3)
        
        # Verify database calls
        self.assertGreater(self.mock_postgres_hook.run.call_count, 0)
    
    @patch('etl_functions.AmazonBookScraper')
    @patch('etl_functions.DatabaseManager')
    def test_airflow_task_integration(self, mock_db_manager_class, mock_scraper_class):
        """Test integration between Airflow tasks."""
        # Mock scraper
        mock_scraper = Mock()
        mock_scraper.scrape_books.return_value = SAMPLE_BOOK_DATA
        mock_scraper_class.return_value = mock_scraper
        
        # Mock DatabaseManager
        mock_db_manager = Mock()
        mock_db_manager.insert_books.return_value = 3
        mock_db_manager_class.return_value = mock_db_manager
        
        # Step 1: Extract data (simulating first Airflow task)
        extract_amazon_books(3, self.mock_ti)
        
        # Verify XCom push was called
        self.mock_ti.xcom_push.assert_called_once()
        pushed_data = self.mock_ti.xcom_push.call_args[1]['value']
        self.assertEqual(len(pushed_data), 3)
        
        # Step 2: Load data (simulating third Airflow task)
        # Mock XCom pull to return the data we just pushed
        self.mock_ti.xcom_pull.return_value = pushed_data
        
        load_books_to_postgres(self.mock_ti)
        
        # Verify XCom pull was called correctly
        self.mock_ti.xcom_pull.assert_called_once_with(
            key='book_data', 
            task_ids='fetch_book_data'
        )
        
        # Verify database operations were called
        mock_db_manager.insert_books.assert_called_once_with(pushed_data)
    
    def test_data_quality_pipeline(self):
        """Test data quality throughout the pipeline."""
        # Start with mixed quality data
        mixed_data = [
            {
                "Title": "Good Book 1",
                "Author": "Author 1",
                "Price": "25",
                "Rating": "4.0 out of 5 stars"
            },
            {
                "Title": "",  # Invalid - empty title
                "Author": "Author 2",
                "Price": "30",
                "Rating": "4.5 out of 5 stars"
            },
            {
                "Title": "Good Book 2",
                "Author": "Author 3",
                "Price": "35",
                "Rating": "4.2 out of 5 stars"
            },
            {
                "Title": "Good Book 1",  # Duplicate
                "Author": "Author 1",
                "Price": "25",
                "Rating": "4.0 out of 5 stars"
            }
        ]
        
        # Process through the pipeline
        processor = BookDataProcessor()
        
        # Step 1: Validation
        validated = processor.validate_book_data(mixed_data)
        self.assertEqual(len(validated), 3)  # Should remove invalid entry
        
        # Step 2: DataFrame conversion with deduplication
        df = processor.books_to_dataframe(validated)
        self.assertEqual(len(df), 2)  # Should remove duplicate
        
        # Step 3: Convert back to records
        final_records = processor.dataframe_to_records(df)
        self.assertEqual(len(final_records), 2)
        
        # Verify data quality
        titles = [book["Title"] for book in final_records]
        self.assertIn("Good Book 1", titles)
        self.assertIn("Good Book 2", titles)
        self.assertEqual(len(set(titles)), 2)  # All unique
    
    def test_error_handling_pipeline(self):
        """Test error handling throughout the pipeline."""
        # Test with mock scraper that returns empty data
        scraper = AmazonBookScraper()
        
        # Mock the fetch_page_content method to return None (simulating network error)
        with patch.object(scraper, 'fetch_page_content', return_value=None):
            books = scraper.scrape_books(num_books=5, max_pages=1)
            # Should handle error gracefully and return empty list
            self.assertEqual(len(books), 0)
        
        # Test empty data handling
        processor = BookDataProcessor()
        df = processor.books_to_dataframe([])
        records = processor.dataframe_to_records(df)
        
        self.assertEqual(len(records), 0)
        self.assertIsInstance(df, pd.DataFrame)
        
        # Test database error handling
        db_manager = DatabaseManager(self.mock_postgres_hook)
        self.mock_postgres_hook.run.side_effect = Exception("Database error")
        
        # Should handle database errors gracefully
        result = db_manager.insert_books(SAMPLE_BOOK_DATA)
        self.assertEqual(result, 0)  # No successful insertions
    
    def test_performance_with_large_dataset(self):
        """Test pipeline performance with larger dataset."""
        # Create a larger dataset
        large_dataset = []
        for i in range(100):
            large_dataset.append({
                "Title": f"Book {i}",
                "Author": f"Author {i}",
                "Price": f"{20 + i}",
                "Rating": f"{4.0 + (i % 10) * 0.1:.1f} out of 5 stars"
            })
        
        # Add some duplicates
        large_dataset.extend(large_dataset[:10])
        
        # Process through pipeline
        processor = BookDataProcessor()
        
        validated = processor.validate_book_data(large_dataset)
        self.assertEqual(len(validated), 110)  # All should be valid
        
        df = processor.books_to_dataframe(validated)
        self.assertEqual(len(df), 100)  # Should remove 10 duplicates
        
        records = processor.dataframe_to_records(df)
        self.assertEqual(len(records), 100)
        
        # Test database insertion simulation
        db_manager = DatabaseManager(self.mock_postgres_hook)
        self.mock_postgres_hook.run.return_value = None
        
        inserted_count = db_manager.insert_books(records)
        self.assertEqual(inserted_count, 100)
        self.assertEqual(self.mock_postgres_hook.run.call_count, 100)
    
    @patch('etl_functions.requests.get')
    def test_pagination_handling(self, mock_get):
        """Test that pagination is handled correctly."""
        # Mock multiple pages of results
        def mock_response_side_effect(url, **kwargs):
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None
            
            if "page=1" in url:
                # First page with 2 books
                html = """
                <html><body>
                    <div class="s-result-item">
                        <span class="a-text-normal">Book 1</span>
                        <a class="a-size-base">Author 1</a>
                        <span class="a-price-whole">25</span>
                        <span class="a-icon-alt">4.0 out of 5 stars</span>
                    </div>
                    <div class="s-result-item">
                        <span class="a-text-normal">Book 2</span>
                        <a class="a-size-base">Author 2</a>
                        <span class="a-price-whole">30</span>
                        <span class="a-icon-alt">4.5 out of 5 stars</span>
                    </div>
                </body></html>
                """
            else:
                # Second page with 1 book
                html = """
                <html><body>
                    <div class="s-result-item">
                        <span class="a-text-normal">Book 3</span>
                        <a class="a-size-base">Author 3</a>
                        <span class="a-price-whole">35</span>
                        <span class="a-icon-alt">4.2 out of 5 stars</span>
                    </div>
                </body></html>
                """
            
            mock_response.content = html.encode('utf-8')
            return mock_response
        
        mock_get.side_effect = mock_response_side_effect
        
        scraper = AmazonBookScraper()
        books = scraper.scrape_books(num_books=3, max_pages=2)
        
        self.assertEqual(len(books), 3)
        self.assertEqual(books[0]["Title"], "Book 1")
        self.assertEqual(books[1]["Title"], "Book 2")
        self.assertEqual(books[2]["Title"], "Book 3")
        
        # Verify both pages were called
        self.assertEqual(mock_get.call_count, 2)


if __name__ == '__main__':
    unittest.main()