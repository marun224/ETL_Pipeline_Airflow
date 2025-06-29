"""
Sample HTML fixtures for testing web scraping functionality.
"""

SAMPLE_AMAZON_HTML = """
<html>
<body>
    <div class="s-result-item">
        <span class="a-text-normal">Data Engineering with Python</span>
        <a class="a-size-base">John Smith</a>
        <span class="a-price-whole">29</span>
        <span class="a-icon-alt">4.5 out of 5 stars</span>
    </div>
    <div class="s-result-item">
        <span class="a-text-normal">Modern Data Engineering</span>
        <a class="a-size-base">Jane Doe</a>
        <span class="a-price-whole">35</span>
        <span class="a-icon-alt">4.2 out of 5 stars</span>
    </div>
    <div class="s-result-item">
        <span class="a-text-normal">Python for Data Engineers</span>
        <a class="a-size-base">Bob Johnson</a>
        <span class="a-price-whole">42</span>
        <span class="a-icon-alt">4.7 out of 5 stars</span>
    </div>
    <div class="s-result-item">
        <!-- Incomplete data - missing price -->
        <span class="a-text-normal">Incomplete Book</span>
        <a class="a-size-base">Unknown Author</a>
        <span class="a-icon-alt">3.0 out of 5 stars</span>
    </div>
</body>
</html>
"""

EMPTY_AMAZON_HTML = """
<html>
<body>
    <div class="no-results">No results found</div>
</body>
</html>
"""

MALFORMED_AMAZON_HTML = """
<html>
<body>
    <div class="s-result-item">
        <span class="wrong-class">Wrong Class Book</span>
        <a class="wrong-author-class">Wrong Author</a>
        <span class="wrong-price-class">99</span>
        <span class="wrong-rating-class">5.0 out of 5 stars</span>
    </div>
</body>
</html>
"""