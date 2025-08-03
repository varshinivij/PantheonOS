Web Browse
==========

The Web Browse toolset enables agents to search the web, fetch content from URLs, and extract information from web pages. This provides access to current information and online resources.

Overview
--------

Key features:
- **Web Search**: Search using DuckDuckGo and other engines
- **Content Fetching**: Retrieve and parse web pages
- **HTML Parsing**: Extract structured data from HTML
- **Link Following**: Navigate through web pages
- **Content Extraction**: Get clean text from web pages

Basic Usage
-----------

Using Web Search
~~~~~~~~~~~~~~~~

.. code-block:: python

   from magique.ai.tools.web_browse import duckduckgo_search, web_crawl
   from pantheon.agent import Agent
   
   # Create agent with web browsing capabilities
   web_agent = Agent(
       name="web_researcher",
       instructions="You are a web researcher. Search for information and analyze web content.",
       model="gpt-4o-mini",
       tools=[duckduckgo_search, web_crawl]
   )
   
   # Search the web
   response = await web_agent.run([{
       "role": "user",
       "content": "Search for recent developments in quantum computing"
   }])

Fetching Web Content
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Fetch and analyze specific URL
   response = await web_agent.run([{
       "role": "user",
       "content": "Analyze the content at https://example.com/article"
   }])
   
   # Agent will:
   # 1. Fetch the URL using web_crawl
   # 2. Parse the HTML content
   # 3. Extract relevant information
   # 4. Provide analysis

Available Tools
---------------

DuckDuckGo Search
~~~~~~~~~~~~~~~~~

.. code-block:: python

   async def duckduckgo_search(
       query: str,
       max_results: int = 5,
       region: str = "us-en"
   ) -> List[Dict[str, str]]:
       """
       Search DuckDuckGo for information.
       
       Returns:
           List of search results with title, url, and snippet
       """

Web Crawl
~~~~~~~~~

.. code-block:: python

   async def web_crawl(
       url: str,
       max_depth: int = 0,
       extract_links: bool = False
   ) -> Dict[str, Any]:
       """
       Fetch and parse web page content.
       
       Returns:
           Dictionary with content, title, links, and metadata
       """

Advanced Features
-----------------

Multi-Page Research
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   research_agent = Agent(
       name="deep_researcher",
       instructions="""Conduct thorough research:
       1. Search for multiple sources
       2. Visit each relevant link
       3. Extract and synthesize information
       4. Provide comprehensive analysis""",
       tools=[duckduckgo_search, web_crawl]
   )
   
   response = await research_agent.run([{
       "role": "user",
       "content": "Research the impact of AI on healthcare with at least 5 sources"
   }])

Content Extraction
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   extractor_agent = Agent(
       name="content_extractor",
       instructions="Extract specific information from web pages.",
       tools=[web_crawl]
   )
   
   # Extract structured data
   response = await extractor_agent.run([{
       "role": "user",
       "content": """From this product page, extract:
       - Product name
       - Price
       - Features
       - Customer reviews summary
       URL: https://example.com/product"""
   }])

Link Following
~~~~~~~~~~~~~~

.. code-block:: python

   crawler_agent = Agent(
       name="web_crawler",
       instructions="Navigate through websites by following relevant links.",
       tools=[web_crawl]
   )
   
   # Crawl with depth
   response = await crawler_agent.run([{
       "role": "user",
       "content": "Starting from the homepage, find all documentation pages"
   }])

Common Patterns
---------------

News Monitoring
~~~~~~~~~~~~~~~

.. code-block:: python

   news_agent = Agent(
       name="news_monitor",
       instructions="""Monitor news on specific topics:
       1. Search for recent news
       2. Filter by date and relevance
       3. Summarize key developments
       4. Identify trends""",
       tools=[duckduckgo_search, web_crawl]
   )
   
   # Monitor specific topic
   response = await news_agent.run([{
       "role": "user",
       "content": "Find news about renewable energy from the past week"
   }])

Competitive Analysis
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   competitor_agent = Agent(
       name="competitor_analyst",
       instructions="""Analyze competitor websites:
       1. Find competitor sites
       2. Extract product information
       3. Compare features and pricing
       4. Identify market positioning""",
       tools=[duckduckgo_search, web_crawl]
   )

Fact Checking
~~~~~~~~~~~~~

.. code-block:: python

   fact_checker = Agent(
       name="fact_checker",
       instructions="""Verify claims by:
       1. Searching multiple sources
       2. Finding authoritative references
       3. Cross-referencing information
       4. Providing confidence assessment""",
       tools=[duckduckgo_search, web_crawl]
   )
   
   response = await fact_checker.run([{
       "role": "user",
       "content": "Verify: The Great Wall of China is visible from space"
   }])

Integration Patterns
--------------------

With Data Analysis
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Combine web data with analysis
   market_analyst = Agent(
       name="market_analyst",
       instructions="Gather market data from web and analyze trends.",
       tools=[duckduckgo_search, web_crawl]
   )
   await market_analyst.remote_toolset(python_tools.service_id)
   
   # Agent workflow:
   # 1. Search for market data sources
   # 2. Fetch data from multiple sites
   # 3. Use Python to analyze trends
   # 4. Create visualizations

With Content Creation
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   content_researcher = Agent(
       name="content_researcher",
       instructions="""Research topics and create content:
       1. Search for authoritative sources
       2. Gather diverse perspectives
       3. Extract key information
       4. Create original content""",
       tools=[duckduckgo_search, web_crawl, write_file]
   )

Best Practices
--------------

1. **Rate Limiting**: Respect website rate limits
2. **Error Handling**: Handle network errors gracefully
3. **Content Validation**: Verify extracted information
4. **Source Attribution**: Always cite sources
5. **Privacy**: Respect robots.txt and privacy policies

Error Handling
--------------

Network Errors
~~~~~~~~~~~~~~

.. code-block:: python

   class RobustWebAgent(Agent):
       async def fetch_with_retry(self, url: str, max_retries: int = 3):
           """Fetch URL with retry logic."""
           for attempt in range(max_retries):
               try:
                   response = await self.run([{
                       "role": "user",
                       "content": f"Fetch content from {url}"
                   }])
                   return response
               except Exception as e:
                   if attempt == max_retries - 1:
                       # Try alternative approach
                       return await self.search_cache(url)
                   await asyncio.sleep(2 ** attempt)

Content Parsing
~~~~~~~~~~~~~~~

.. code-block:: python

   class SmartExtractor(Agent):
       async def extract_safely(self, url: str, selectors: List[str]):
           """Extract content with fallbacks."""
           try:
               # Try primary extraction
               content = await self.extract_with_selectors(url, selectors)
           except:
               # Fallback to general extraction
               content = await self.extract_general(url)
           
           return self.validate_content(content)

Advanced Usage
--------------

Custom Search Engines
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class MultiSearchAgent(Agent):
       async def search_multiple(self, query: str):
           """Search across multiple search engines."""
           results = {}
           
           # DuckDuckGo
           results['duckduckgo'] = await self.run([{
               "role": "user",
               "content": f"Search DuckDuckGo for: {query}"
           }])
           
           # Could add other search APIs
           # results['bing'] = await self.search_bing(query)
           # results['google'] = await self.search_google(query)
           
           # Merge and deduplicate results
           return self.merge_results(results)

Semantic Search
~~~~~~~~~~~~~~~

.. code-block:: python

   semantic_searcher = Agent(
       name="semantic_searcher",
       instructions="""Perform semantic search:
       1. Understand search intent
       2. Generate multiple search queries
       3. Filter results by relevance
       4. Extract semantic meaning""",
       tools=[duckduckgo_search, web_crawl]
   )

Web Monitoring
~~~~~~~~~~~~~~

.. code-block:: python

   monitor_agent = Agent(
       name="web_monitor",
       instructions="""Monitor web pages for changes:
       1. Fetch current content
       2. Compare with previous version
       3. Identify significant changes
       4. Alert on important updates""",
       tools=[web_crawl]
   )

Performance Tips
----------------

- Cache frequently accessed pages
- Batch multiple searches when possible
- Use appropriate timeouts
- Extract only necessary content
- Implement progressive loading for large sites

Limitations
-----------

- JavaScript-heavy sites may not render fully
- Some sites block automated access
- Rate limits apply to search engines
- Cannot handle authentication-required pages
- Limited to publicly accessible content

Security Considerations
-----------------------

- Validate URLs before fetching
- Sanitize extracted content
- Respect robots.txt
- Implement user-agent headers
- Handle malicious content safely