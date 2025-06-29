"""
Sample data fixtures for testing.
"""

SAMPLE_BOOK_DATA = [
    {
        "Title": "Data Engineering with Python",
        "Author": "John Smith",
        "Price": "29",
        "Rating": "4.5 out of 5 stars"
    },
    {
        "Title": "Modern Data Engineering",
        "Author": "Jane Doe",
        "Price": "35",
        "Rating": "4.2 out of 5 stars"
    },
    {
        "Title": "Python for Data Engineers",
        "Author": "Bob Johnson",
        "Price": "42",
        "Rating": "4.7 out of 5 stars"
    }
]

INVALID_BOOK_DATA = [
    {
        "Title": "",  # Empty title
        "Author": "John Smith",
        "Price": "29",
        "Rating": "4.5 out of 5 stars"
    },
    {
        "Title": "Valid Book",
        "Author": "",  # Empty author
        "Price": "35",
        "Rating": "4.2 out of 5 stars"
    },
    {
        "Title": "Another Valid Book",
        "Author": "Jane Doe",
        "Price": "",  # Empty price
        "Rating": "4.7 out of 5 stars"
    },
    {
        "Title": "Complete Book",
        "Author": "Bob Johnson",
        "Price": "42",
        "Rating": "4.0 out of 5 stars"
    }
]

DUPLICATE_BOOK_DATA = [
    {
        "Title": "Data Engineering with Python",
        "Author": "John Smith",
        "Price": "29",
        "Rating": "4.5 out of 5 stars"
    },
    {
        "Title": "Data Engineering with Python",  # Duplicate title
        "Author": "John Smith",
        "Price": "29",
        "Rating": "4.5 out of 5 stars"
    },
    {
        "Title": "Modern Data Engineering",
        "Author": "Jane Doe",
        "Price": "35",
        "Rating": "4.2 out of 5 stars"
    }
]

MIXED_QUALITY_DATA = [
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