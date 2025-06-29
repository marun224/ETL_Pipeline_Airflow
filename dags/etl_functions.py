"""
ETL Functions for Amazon Books Data Pipeline

This module contains the core ETL functions that can be tested independently
from the Airflow DAG structure.
"""

import requests
import pandas as pd
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Set
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Headers for web scraping
DEFAULT_HEADERS = {
    "Referer": 'https://www.amazon.com/',
    "Sec-Ch-Ua": "Not_A Brand",
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": "macOS",
    'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
}


class AmazonBookScraper:
    """
    A class to handle Amazon book data scraping with improved error handling
    and testability.
    """
    
    def __init__(self, headers: Optional[Dict[str, str]] = None):
        """
        Initialize the scraper with custom headers.
        
        Args:
            headers: Custom headers for HTTP requests
        """
        self.headers = headers or DEFAULT_HEADERS
        self.base_url = "https://www.amazon.com/s?k=data+engineering+books"
        
    def fetch_page_content(self, page: int) -> Optional[BeautifulSoup]:
        """
        Fetch and parse a single page of Amazon search results.
        
        Args:
            page: Page number to fetch
            
        Returns:
            BeautifulSoup object or None if request fails
        """
        url = f"{self.base_url}&page={page}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, "html.parser")
        except requests.RequestException as e:
            logger.error(f"Failed to fetch page {page}: {e}")
            return None
    
    def extract_book_data_from_container(self, book_container) -> Optional[Dict[str, str]]:
        """
        Extract book information from a single book container element.
        
        Args:
            book_container: BeautifulSoup element containing book data
            
        Returns:
            Dictionary with book data or None if extraction fails
        """
        try:
            title_elem = book_container.find("span", {"class": "a-text-normal"})
            author_elem = book_container.find("a", {"class": "a-size-base"})
            price_elem = book_container.find("span", {"class": "a-price-whole"})
            rating_elem = book_container.find("span", {"class": "a-icon-alt"})
            
            if all([title_elem, author_elem, price_elem, rating_elem]):
                return {
                    "Title": title_elem.text.strip(),
                    "Author": author_elem.text.strip(),
                    "Price": price_elem.text.strip(),
                    "Rating": rating_elem.text.strip(),
                }
        except Exception as e:
            logger.warning(f"Failed to extract book data: {e}")
            
        return None
    
    def extract_books_from_page(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """
        Extract all book data from a parsed page.
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            List of book dictionaries
        """
        books = []
        book_containers = soup.find_all("div", {"class": "s-result-item"})
        
        for container in book_containers:
            book_data = self.extract_book_data_from_container(container)
            if book_data:
                books.append(book_data)
                
        return books
    
    def scrape_books(self, num_books: int, max_pages: int = 10) -> List[Dict[str, str]]:
        """
        Scrape book data from Amazon with duplicate detection.
        
        Args:
            num_books: Number of unique books to collect
            max_pages: Maximum pages to scrape
            
        Returns:
            List of unique book dictionaries
        """
        books = []
        seen_titles: Set[str] = set()
        page = 1
        
        while len(books) < num_books and page <= max_pages:
            logger.info(f"Scraping page {page}")
            soup = self.fetch_page_content(page)
            
            if not soup:
                logger.warning(f"Failed to fetch page {page}, stopping")
                break
                
            page_books = self.extract_books_from_page(soup)
            
            # Add unique books
            for book in page_books:
                title = book["Title"]
                if title not in seen_titles and len(books) < num_books:
                    seen_titles.add(title)
                    books.append(book)
                    
            page += 1
            
        logger.info(f"Scraped {len(books)} unique books")
        return books[:num_books]


class BookDataProcessor:
    """
    A class to handle book data processing and transformation.
    """
    
    @staticmethod
    def validate_book_data(book_data: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Validate and clean book data.
        
        Args:
            book_data: List of book dictionaries
            
        Returns:
            List of validated book dictionaries
        """
        valid_books = []
        required_fields = ["Title", "Author", "Price", "Rating"]
        
        for book in book_data:
            if all(field in book and book[field].strip() for field in required_fields):
                # Clean the data
                cleaned_book = {
                    field: book[field].strip() for field in required_fields
                }
                valid_books.append(cleaned_book)
            else:
                logger.warning(f"Invalid book data: {book}")
                
        return valid_books
    
    @staticmethod
    def books_to_dataframe(books: List[Dict[str, str]]) -> pd.DataFrame:
        """
        Convert book list to pandas DataFrame with deduplication.
        
        Args:
            books: List of book dictionaries
            
        Returns:
            Pandas DataFrame with unique books
        """
        if not books:
            return pd.DataFrame(columns=["Title", "Author", "Price", "Rating"])
            
        df = pd.DataFrame(books)
        df.drop_duplicates(subset="Title", inplace=True)
        return df
    
    @staticmethod
    def dataframe_to_records(df: pd.DataFrame) -> List[Dict[str, str]]:
        """
        Convert DataFrame to list of dictionaries.
        
        Args:
            df: Pandas DataFrame
            
        Returns:
            List of dictionaries
        """
        return df.to_dict('records')


class DatabaseManager:
    """
    A class to handle database operations.
    """
    
    def __init__(self, postgres_hook):
        """
        Initialize with PostgreSQL hook.
        
        Args:
            postgres_hook: Airflow PostgresHook instance
        """
        self.postgres_hook = postgres_hook
    
    def insert_books(self, book_data: List[Dict[str, str]]) -> int:
        """
        Insert book data into PostgreSQL database.
        
        Args:
            book_data: List of book dictionaries
            
        Returns:
            Number of books inserted
        """
        if not book_data:
            logger.warning("No book data to insert")
            return 0
            
        insert_query = """
        INSERT INTO books (title, authors, price, rating)
        VALUES (%s, %s, %s, %s)
        """
        
        inserted_count = 0
        for book in book_data:
            try:
                self.postgres_hook.run(
                    insert_query, 
                    parameters=(book['Title'], book['Author'], book['Price'], book['Rating'])
                )
                inserted_count += 1
            except KeyError as e:
                logger.error(f"Missing required field in book data: {e}")
            except Exception as e:
                book_title = book.get('Title', 'Unknown')
                logger.error(f"Failed to insert book {book_title}: {e}")
                
        logger.info(f"Inserted {inserted_count} books into database")
        return inserted_count
    
    def create_books_table(self) -> bool:
        """
        Create the books table if it doesn't exist.
        
        Returns:
            True if successful, False otherwise
        """
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS books (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            authors TEXT,
            price TEXT,
            rating TEXT
        );
        """
        
        try:
            self.postgres_hook.run(create_table_sql)
            logger.info("Books table created successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to create books table: {e}")
            return False


# Main ETL functions for Airflow integration
def extract_amazon_books(num_books: int, ti) -> None:
    """
    Airflow task function to extract book data from Amazon.
    
    Args:
        num_books: Number of books to extract
        ti: Airflow task instance for XCom
    """
    scraper = AmazonBookScraper()
    processor = BookDataProcessor()
    
    # Extract books
    books = scraper.scrape_books(num_books)
    
    # Validate and process
    valid_books = processor.validate_book_data(books)
    
    # Convert to DataFrame and back to records for consistency
    df = processor.books_to_dataframe(valid_books)
    records = processor.dataframe_to_records(df)
    
    # Push to XCom
    ti.xcom_push(key='book_data', value=records)
    logger.info(f"Extracted and processed {len(records)} books")


def load_books_to_postgres(ti) -> None:
    """
    Airflow task function to load book data into PostgreSQL.
    
    Args:
        ti: Airflow task instance for XCom
    """
    from airflow.providers.postgres.hooks.postgres import PostgresHook
    
    # Get data from XCom
    book_data = ti.xcom_pull(key='book_data', task_ids='fetch_book_data')
    
    if not book_data:
        raise ValueError("No book data found in XCom")
    
    # Initialize database manager
    postgres_hook = PostgresHook(postgres_conn_id='books_connection')
    db_manager = DatabaseManager(postgres_hook)
    
    # Insert books
    inserted_count = db_manager.insert_books(book_data)
    
    if inserted_count == 0:
        raise ValueError("No books were inserted into the database")
    
    logger.info(f"Successfully loaded {inserted_count} books to PostgreSQL")