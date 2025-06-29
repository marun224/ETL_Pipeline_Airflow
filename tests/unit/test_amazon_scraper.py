"""
Unit tests for AmazonBookScraper class.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import requests
from bs4 import BeautifulSoup
import sys
import os

# Add the dags directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../dags'))

from etl_functions import AmazonBookScraper
from tests.fixtures.sample_html import SAMPLE_AMAZON_HTML, EMPTY_AMAZON_HTML, MALFORMED_AMAZON_HTML


class TestAmazonBookScraper(unittest.TestCase):
    """Test cases for AmazonBookScraper class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.scraper = AmazonBookScraper()
        self.custom_headers = {"User-Agent": "Test Agent"}
    
    def test_init_default_headers(self):
        """Test scraper initialization with default headers."""
        scraper = AmazonBookScraper()
        self.assertIsNotNone(scraper.headers)
        self.assertIn('User-agent', scraper.headers)
        self.assertEqual(scraper.base_url, "https://www.amazon.com/s?k=data+engineering+books")
    
    def test_init_custom_headers(self):
        """Test scraper initialization with custom headers."""
        scraper = AmazonBookScraper(headers=self.custom_headers)
        self.assertEqual(scraper.headers, self.custom_headers)
    
    @patch('etl_functions.requests.get')
    def test_fetch_page_content_success(self, mock_get):
        """Test successful page content fetching."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = SAMPLE_AMAZON_HTML.encode('utf-8')
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.scraper.fetch_page_content(1)
        
        self.assertIsInstance(result, BeautifulSoup)
        mock_get.assert_called_once()
        
        # Verify the URL construction
        expected_url = "https://www.amazon.com/s?k=data+engineering+books&page=1"
        mock_get.assert_called_with(expected_url, headers=self.scraper.headers, timeout=30)
    
    @patch('etl_functions.requests.get')
    def test_fetch_page_content_http_error(self, mock_get):
        """Test page content fetching with HTTP error."""
        # Mock HTTP error
        mock_get.side_effect = requests.HTTPError("404 Not Found")
        
        result = self.scraper.fetch_page_content(1)
        
        self.assertIsNone(result)
    
    @patch('etl_functions.requests.get')
    def test_fetch_page_content_timeout(self, mock_get):
        """Test page content fetching with timeout."""
        # Mock timeout error
        mock_get.side_effect = requests.Timeout("Request timed out")
        
        result = self.scraper.fetch_page_content(1)
        
        self.assertIsNone(result)
    
    def test_extract_book_data_from_container_valid(self):
        """Test extracting book data from valid HTML container."""
        soup = BeautifulSoup(SAMPLE_AMAZON_HTML, 'html.parser')
        container = soup.find("div", {"class": "s-result-item"})
        
        result = self.scraper.extract_book_data_from_container(container)
        
        expected = {
            "Title": "Data Engineering with Python",
            "Author": "John Smith",
            "Price": "29",
            "Rating": "4.5 out of 5 stars"
        }
        self.assertEqual(result, expected)
    
    def test_extract_book_data_from_container_incomplete(self):
        """Test extracting book data from incomplete HTML container."""
        soup = BeautifulSoup(SAMPLE_AMAZON_HTML, 'html.parser')
        containers = soup.find_all("div", {"class": "s-result-item"})
        incomplete_container = containers[-1]  # Last container has missing price
        
        result = self.scraper.extract_book_data_from_container(incomplete_container)
        
        self.assertIsNone(result)
    
    def test_extract_book_data_from_container_malformed(self):
        """Test extracting book data from malformed HTML container."""
        soup = BeautifulSoup(MALFORMED_AMAZON_HTML, 'html.parser')
        container = soup.find("div", {"class": "s-result-item"})
        
        result = self.scraper.extract_book_data_from_container(container)
        
        self.assertIsNone(result)
    
    def test_extract_books_from_page_valid(self):
        """Test extracting all books from a valid page."""
        soup = BeautifulSoup(SAMPLE_AMAZON_HTML, 'html.parser')
        
        result = self.scraper.extract_books_from_page(soup)
        
        self.assertEqual(len(result), 3)  # 3 valid books in sample HTML
        self.assertEqual(result[0]["Title"], "Data Engineering with Python")
        self.assertEqual(result[1]["Title"], "Modern Data Engineering")
        self.assertEqual(result[2]["Title"], "Python for Data Engineers")
    
    def test_extract_books_from_page_empty(self):
        """Test extracting books from empty page."""
        soup = BeautifulSoup(EMPTY_AMAZON_HTML, 'html.parser')
        
        result = self.scraper.extract_books_from_page(soup)
        
        self.assertEqual(len(result), 0)
    
    @patch.object(AmazonBookScraper, 'fetch_page_content')
    def test_scrape_books_success(self, mock_fetch):
        """Test successful book scraping."""
        # Mock page content
        soup = BeautifulSoup(SAMPLE_AMAZON_HTML, 'html.parser')
        mock_fetch.return_value = soup
        
        result = self.scraper.scrape_books(num_books=2, max_pages=1)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["Title"], "Data Engineering with Python")
        self.assertEqual(result[1]["Title"], "Modern Data Engineering")
        mock_fetch.assert_called_once_with(1)
    
    @patch.object(AmazonBookScraper, 'fetch_page_content')
    def test_scrape_books_no_content(self, mock_fetch):
        """Test book scraping when no content is fetched."""
        mock_fetch.return_value = None
        
        result = self.scraper.scrape_books(num_books=5, max_pages=1)
        
        self.assertEqual(len(result), 0)
    
    @patch.object(AmazonBookScraper, 'fetch_page_content')
    def test_scrape_books_max_pages_limit(self, mock_fetch):
        """Test book scraping respects max_pages limit."""
        # Mock empty pages to force pagination
        soup = BeautifulSoup(EMPTY_AMAZON_HTML, 'html.parser')
        mock_fetch.return_value = soup
        
        result = self.scraper.scrape_books(num_books=100, max_pages=2)
        
        self.assertEqual(len(result), 0)
        self.assertEqual(mock_fetch.call_count, 2)  # Should stop at max_pages
    
    @patch.object(AmazonBookScraper, 'fetch_page_content')
    def test_scrape_books_duplicate_handling(self, mock_fetch):
        """Test that duplicate books are handled correctly."""
        # Create HTML with duplicate titles
        duplicate_html = """
        <html>
        <body>
            <div class="s-result-item">
                <span class="a-text-normal">Same Title</span>
                <a class="a-size-base">Author 1</a>
                <span class="a-price-whole">29</span>
                <span class="a-icon-alt">4.5 out of 5 stars</span>
            </div>
            <div class="s-result-item">
                <span class="a-text-normal">Same Title</span>
                <a class="a-size-base">Author 2</a>
                <span class="a-price-whole">35</span>
                <span class="a-icon-alt">4.2 out of 5 stars</span>
            </div>
        </body>
        </html>
        """
        soup = BeautifulSoup(duplicate_html, 'html.parser')
        mock_fetch.return_value = soup
        
        result = self.scraper.scrape_books(num_books=5, max_pages=1)
        
        # Should only return one book due to duplicate title filtering
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["Title"], "Same Title")


if __name__ == '__main__':
    unittest.main()