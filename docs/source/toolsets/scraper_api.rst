Scraper API
===========

The Scraper API toolset provides advanced web scraping capabilities with features like JavaScript rendering, proxy rotation, and anti-bot bypass mechanisms for reliable data extraction.

Overview
--------

Key features:
- **JavaScript Rendering**: Scrape dynamic websites
- **Proxy Rotation**: Automatic IP rotation
- **Anti-Bot Bypass**: Handle CAPTCHAs and rate limits
- **Structured Extraction**: CSS and XPath selectors
- **Session Management**: Maintain cookies and state

Basic Usage
-----------

Setting Up Scraper API
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from magique.ai.tools.scraper import ScraperAPIToolSet
   from pantheon.agent import Agent
   
   # Initialize Scraper API toolset
   scraper_tools = ScraperAPIToolSet(
       api_key="your_scraper_api_key",
       render_js=True,
       premium_proxy=True
   )
   
   # Create agent with scraping capabilities
   scraper_agent = Agent(
       name="data_scraper",
       instructions="Extract data from websites using advanced scraping techniques.",
       model="gpt-4o-mini"
   )
   await scraper_agent.remote_toolset(scraper_tools.service_id)

Basic Scraping
~~~~~~~~~~~~~~

.. code-block:: python

   # Scrape a simple page
   response = await scraper_agent.run([{
       "role": "user",
       "content": "Extract all product names and prices from https://example-shop.com/products"
   }])
   
   # Agent uses ScraperAPI to:
   # 1. Render JavaScript
   # 2. Wait for dynamic content
   # 3. Extract data using selectors
   # 4. Return structured results

Advanced Features
-----------------

JavaScript-Heavy Sites
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Configure for SPA/React sites
   spa_scraper = ScraperAPIToolSet(
       api_key="your_key",
       render_js=True,
       wait_for_selector=".product-loaded",  # Wait for specific element
       js_scenario={
           "actions": [
               {"type": "click", "selector": ".load-more-btn"},
               {"type": "wait", "value": 2000},
               {"type": "scroll", "value": "bottom"}
           ]
       }
   )
   
   dynamic_agent = Agent(
       name="spa_scraper",
       instructions="Scrape single-page applications with dynamic content loading."
   )

Session-Based Scraping
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Maintain session for multi-page scraping
   session_scraper = Agent(
       name="session_scraper",
       instructions="""Scrape data that requires login or session:
       1. Navigate to login page
       2. Submit credentials
       3. Maintain session cookies
       4. Scrape protected pages"""
   )
   
   # Agent handles:
   # - Form submission
   # - Cookie persistence
   # - Session validation
   # - Multi-step workflows

Structured Data Extraction
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   extractor_agent = Agent(
       name="structured_extractor",
       instructions="Extract data using CSS selectors and XPath."
   )
   
   response = await extractor_agent.run([{
       "role": "user",
       "content": """Extract from product pages:
       - Title: h1.product-title
       - Price: span.price-now
       - Description: div.product-description
       - Images: img.product-image@src
       - Reviews: div.review-item"""
   }])

Common Use Cases
----------------

E-commerce Monitoring
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   price_monitor = Agent(
       name="price_monitor",
       instructions="""Monitor product prices across multiple sites:
       1. Scrape product pages
       2. Extract current prices
       3. Compare with historical data
       4. Alert on significant changes"""
   )
   
   # Monitor configuration
   monitor_config = {
       "products": [
           {
               "url": "https://shop1.com/product/123",
               "selectors": {
                   "price": ".current-price",
                   "stock": ".availability"
               }
           }
       ],
       "check_interval": 3600  # 1 hour
   }

Real Estate Listings
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   realestate_scraper = Agent(
       name="property_scraper",
       instructions="""Extract real estate listings:
       1. Search properties by criteria
       2. Extract listing details
       3. Download images
       4. Compile into database"""
   )
   
   # Extract comprehensive data
   listing_data = {
       "address": "h1.property-address",
       "price": "span.listing-price",
       "bedrooms": "div.bed-count",
       "bathrooms": "div.bath-count",
       "sqft": "span.square-feet",
       "description": "div.property-description",
       "images": "img.property-photo@src",
       "agent": "div.agent-info"
   }

Job Market Analysis
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   job_scraper = Agent(
       name="job_market_analyst",
       instructions="""Analyze job market trends:
       1. Scrape job boards
       2. Extract job details
       3. Analyze requirements
       4. Track salary trends"""
   )
   
   # Scrape multiple job sites
   job_sites = [
       {
           "site": "indeed",
           "search_url": "https://indeed.com/jobs?q={query}",
           "selectors": {
               "title": ".jobTitle",
               "company": ".companyName",
               "salary": ".salary-snippet",
               "description": ".job-snippet"
           }
       }
   ]

Advanced Techniques
-------------------

Pagination Handling
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class PaginationScraper(Agent):
       async def scrape_all_pages(self, base_url: str, max_pages: int = None):
           """Scrape all pages from paginated results."""
           all_data = []
           page = 1
           
           while True:
               # Scrape current page
               url = f"{base_url}?page={page}"
               data = await self.scrape_page(url)
               
               if not data or (max_pages and page >= max_pages):
                   break
                   
               all_data.extend(data)
               page += 1
               
               # Respect rate limits
               await asyncio.sleep(2)
           
           return all_data

Anti-Detection Strategies
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   stealth_scraper = ScraperAPIToolSet(
       api_key="your_key",
       # Rotation settings
       country_code="us",
       premium_proxy=True,
       
       # Browser fingerprinting
       headers={
           "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
           "Accept-Language": "en-US,en;q=0.9",
           "Accept-Encoding": "gzip, deflate, br"
       },
       
       # Behavior mimicking
       random_delay=(1000, 3000),  # Random delay between actions
       mouse_movements=True         # Simulate mouse movements
   )

Parallel Scraping
~~~~~~~~~~~~~~~~~

.. code-block:: python

   class ParallelScraper(Agent):
       async def scrape_multiple(self, urls: List[str], max_concurrent: int = 5):
           """Scrape multiple URLs in parallel."""
           semaphore = asyncio.Semaphore(max_concurrent)
           
           async def scrape_with_limit(url):
               async with semaphore:
                   return await self.scrape_url(url)
           
           tasks = [scrape_with_limit(url) for url in urls]
           results = await asyncio.gather(*tasks, return_exceptions=True)
           
           return [r for r in results if not isinstance(r, Exception)]

Error Handling
--------------

Retry Logic
~~~~~~~~~~~

.. code-block:: python

   class ResilientScraper(Agent):
       async def scrape_with_retry(self, url: str, max_retries: int = 3):
           """Scrape with exponential backoff retry."""
           for attempt in range(max_retries):
               try:
                   result = await self.scrape(url)
                   if self.validate_result(result):
                       return result
               except Exception as e:
                   if attempt == max_retries - 1:
                       raise
                   wait_time = (2 ** attempt) + random.uniform(0, 1)
                   await asyncio.sleep(wait_time)

CAPTCHA Handling
~~~~~~~~~~~~~~~~

.. code-block:: python

   captcha_handler = Agent(
       name="captcha_solver",
       instructions="""Handle CAPTCHA challenges:
       1. Detect CAPTCHA presence
       2. Use CAPTCHA solving service
       3. Submit solution
       4. Verify success"""
   )
   
   # Integration with CAPTCHA services
   scraper_config = {
       "captcha_solver": "2captcha",
       "solver_api_key": "your_2captcha_key",
       "auto_solve": True
   }

Data Processing
---------------

Clean and Structure
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   data_processor = Agent(
       name="scrape_processor",
       instructions="""Process scraped data:
       1. Clean HTML artifacts
       2. Normalize formats
       3. Validate data types
       4. Handle missing values"""
   )
   
   # Processing pipeline
   async def process_scraped_data(raw_data):
       # Clean text
       cleaned = clean_html_tags(raw_data)
       
       # Parse numbers
       prices = parse_prices(cleaned['prices'])
       
       # Standardize dates
       dates = standardize_dates(cleaned['dates'])
       
       # Validate
       return validate_data_quality(processed)

Export Formats
~~~~~~~~~~~~~~

.. code-block:: python

   exporter_agent = Agent(
       name="data_exporter",
       instructions="Export scraped data in various formats."
   )
   
   # Export options
   export_formats = {
       "csv": lambda data: pd.DataFrame(data).to_csv(),
       "json": lambda data: json.dumps(data, indent=2),
       "excel": lambda data: pd.DataFrame(data).to_excel(),
       "database": lambda data: insert_to_db(data)
   }

Best Practices
--------------

1. **Respect robots.txt**: Check site policies
2. **Rate Limiting**: Add delays between requests
3. **Error Recovery**: Implement robust error handling
4. **Data Validation**: Verify scraped data quality
5. **Legal Compliance**: Ensure scraping is allowed
6. **Resource Management**: Clean up sessions

Performance Optimization
------------------------

- Use appropriate concurrency limits
- Cache static content
- Minimize JavaScript rendering when not needed
- Batch similar requests
- Use webhook callbacks for long operations

Integration Examples
--------------------

With Data Analysis
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Scrape and analyze
   market_analyst = Agent(
       name="market_scraper",
       instructions="Scrape market data and perform analysis."
   )
   await market_analyst.remote_toolset(scraper_tools.service_id)
   await market_analyst.remote_toolset(python_tools.service_id)

With Database Storage
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Scrape to database pipeline
   db_scraper = Agent(
       name="database_scraper",
       instructions="""Scrape data and store in database:
       1. Extract data from websites
       2. Transform to schema
       3. Insert into database
       4. Update existing records"""
   )