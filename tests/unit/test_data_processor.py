"""
Unit tests for BookDataProcessor class.
"""

import unittest
import pandas as pd
import sys
import os

# Add the dags directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../dags'))

from etl_functions import BookDataProcessor
from tests.fixtures.sample_data import (
    SAMPLE_BOOK_DATA, 
    INVALID_BOOK_DATA, 
    DUPLICATE_BOOK_DATA,
    MIXED_QUALITY_DATA
)


class TestBookDataProcessor(unittest.TestCase):
    """Test cases for BookDataProcessor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = BookDataProcessor()
    
    def test_validate_book_data_valid(self):
        """Test validation of valid book data."""
        result = self.processor.validate_book_data(SAMPLE_BOOK_DATA)
        
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["Title"], "Data Engineering with Python")
        self.assertEqual(result[1]["Author"], "Jane Doe")
        self.assertEqual(result[2]["Price"], "42")
    
    def test_validate_book_data_invalid(self):
        """Test validation filters out invalid book data."""
        result = self.processor.validate_book_data(INVALID_BOOK_DATA)
        
        # Only one book should be valid (the last one)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["Title"], "Complete Book")
    
    def test_validate_book_data_empty_list(self):
        """Test validation of empty book data list."""
        result = self.processor.validate_book_data([])
        
        self.assertEqual(len(result), 0)
        self.assertIsInstance(result, list)
    
    def test_validate_book_data_missing_fields(self):
        """Test validation with missing required fields."""
        incomplete_data = [
            {
                "Title": "Incomplete Book",
                "Author": "Some Author",
                # Missing Price and Rating
            }
        ]
        
        result = self.processor.validate_book_data(incomplete_data)
        
        self.assertEqual(len(result), 0)
    
    def test_validate_book_data_whitespace_handling(self):
        """Test validation handles whitespace correctly."""
        whitespace_data = [
            {
                "Title": "  Whitespace Book  ",
                "Author": "\tAuthor Name\n",
                "Price": " 25 ",
                "Rating": "4.0 out of 5 stars  "
            }
        ]
        
        result = self.processor.validate_book_data(whitespace_data)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["Title"], "Whitespace Book")
        self.assertEqual(result[0]["Author"], "Author Name")
        self.assertEqual(result[0]["Price"], "25")
        self.assertEqual(result[0]["Rating"], "4.0 out of 5 stars")
    
    def test_books_to_dataframe_valid(self):
        """Test conversion of valid books to DataFrame."""
        result = self.processor.books_to_dataframe(SAMPLE_BOOK_DATA)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 3)
        self.assertListEqual(
            list(result.columns), 
            ["Title", "Author", "Price", "Rating"]
        )
        self.assertEqual(result.iloc[0]["Title"], "Data Engineering with Python")
    
    def test_books_to_dataframe_empty(self):
        """Test conversion of empty book list to DataFrame."""
        result = self.processor.books_to_dataframe([])
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 0)
        self.assertListEqual(
            list(result.columns), 
            ["Title", "Author", "Price", "Rating"]
        )
    
    def test_books_to_dataframe_duplicates(self):
        """Test DataFrame creation removes duplicates."""
        result = self.processor.books_to_dataframe(DUPLICATE_BOOK_DATA)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)  # Should remove one duplicate
        
        # Check that duplicate was removed
        titles = result["Title"].tolist()
        self.assertEqual(titles.count("Data Engineering with Python"), 1)
    
    def test_dataframe_to_records_valid(self):
        """Test conversion of DataFrame to records."""
        df = pd.DataFrame(SAMPLE_BOOK_DATA)
        result = self.processor.dataframe_to_records(df)
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)
        self.assertIsInstance(result[0], dict)
        self.assertEqual(result[0]["Title"], "Data Engineering with Python")
    
    def test_dataframe_to_records_empty(self):
        """Test conversion of empty DataFrame to records."""
        df = pd.DataFrame(columns=["Title", "Author", "Price", "Rating"])
        result = self.processor.dataframe_to_records(df)
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)
    
    def test_full_processing_pipeline(self):
        """Test the complete data processing pipeline."""
        # Start with mixed quality data
        validated = self.processor.validate_book_data(MIXED_QUALITY_DATA)
        df = self.processor.books_to_dataframe(validated)
        records = self.processor.dataframe_to_records(df)
        
        # Should have 2 valid, unique books
        self.assertEqual(len(records), 2)
        
        titles = [book["Title"] for book in records]
        self.assertIn("Good Book 1", titles)
        self.assertIn("Good Book 2", titles)
        
        # Ensure no duplicates or invalid data
        self.assertEqual(len(set(titles)), 2)
    
    def test_validate_book_data_extra_fields(self):
        """Test validation ignores extra fields."""
        data_with_extra = [
            {
                "Title": "Book with Extra",
                "Author": "Author Name",
                "Price": "30",
                "Rating": "4.0 out of 5 stars",
                "ExtraField": "Should be ignored",
                "AnotherExtra": 123
            }
        ]
        
        result = self.processor.validate_book_data(data_with_extra)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0]), 4)  # Only required fields
        self.assertNotIn("ExtraField", result[0])
        self.assertNotIn("AnotherExtra", result[0])
    
    def test_books_to_dataframe_preserves_order(self):
        """Test that DataFrame preserves the order of books."""
        result = self.processor.books_to_dataframe(SAMPLE_BOOK_DATA)
        
        expected_titles = [book["Title"] for book in SAMPLE_BOOK_DATA]
        actual_titles = result["Title"].tolist()
        
        self.assertEqual(actual_titles, expected_titles)


if __name__ == '__main__':
    unittest.main()