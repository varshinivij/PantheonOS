Smart Function API
==================

The Smart Function API allows you to convert agents into callable functions, making it easy to integrate AI capabilities into existing codebases without explicit agent management.

Overview
--------

Smart functions wrap agents to provide a simple function interface while maintaining all agent capabilities including tools, memory, and context management.

Basic Usage
-----------

Creating Smart Functions
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pantheon.agent import smart_func
   
   @smart_func(
       instructions="You are a text analyzer. Analyze the sentiment and key themes.",
       model="gpt-4o-mini"
   )
   async def analyze_text(text: str) -> dict:
       """Analyze text for sentiment and themes."""
       pass  # Implementation handled by agent

   # Use as a regular function
   result = await analyze_text("I love using Pantheon! It makes AI development so easy.")
   print(result)
   # Output: {"sentiment": "positive", "themes": ["satisfaction", "ease of use"]}

With Type Hints
~~~~~~~~~~~~~~~~

Leverage type hints for structured outputs:

.. code-block:: python

   from pydantic import BaseModel
   from typing import List
   
   class EmailAnalysis(BaseModel):
       is_spam: bool
       confidence: float
       reasons: List[str]
       category: str
   
   @smart_func(
       instructions="You are an email classifier. Analyze emails for spam detection.",
       model="gpt-4o-mini"
   )
   async def classify_email(
       subject: str,
       body: str,
       sender: str
   ) -> EmailAnalysis:
       """Classify an email as spam or legitimate."""
       pass
   
   # Returns typed response
   analysis = await classify_email(
       subject="You've won $1,000,000!!!",
       body="Click here to claim your prize...",
       sender="unknown@suspicious.com"
   )
   print(f"Spam: {analysis.is_spam} (Confidence: {analysis.confidence})")

Advanced Features
-----------------

Adding Tools
~~~~~~~~~~~~

Enhance smart functions with tools:

.. code-block:: python

   def search_database(query: str) -> List[dict]:
       """Search the product database."""
       # Database search implementation
       return results
   
   def calculate_price(base_price: float, discount: float) -> float:
       """Calculate final price with discount."""
       return base_price * (1 - discount / 100)
   
   @smart_func(
       instructions="You are a shopping assistant. Help users find products and calculate prices.",
       model="gpt-4o-mini",
       tools=[search_database, calculate_price]
   )
   async def shopping_assistant(user_query: str) -> str:
       """Assist users with shopping queries."""
       pass
   
   response = await shopping_assistant(
       "Find me laptops under $1000 with 20% discount"
   )

Context Management
~~~~~~~~~~~~~~~~~~

Pass context to smart functions:

.. code-block:: python

   @smart_func(
       instructions="You are a personalized assistant. Use context to provide relevant help.",
       model="gpt-4o-mini"
   )
   async def personalized_help(
       query: str,
       user_id: str = None,
       preferences: dict = None
   ) -> str:
       """Provide personalized assistance based on user context."""
       pass
   
   # Context is automatically passed to the agent
   response = await personalized_help(
       query="Recommend a restaurant",
       user_id="user123",
       preferences={"cuisine": "Italian", "budget": "moderate"}
   )

Memory-Enabled Functions
~~~~~~~~~~~~~~~~~~~~~~~~

Smart functions with persistent memory:

.. code-block:: python

   from pantheon.memory import LongTermMemory
   
   @smart_func(
       instructions="You are a learning assistant that remembers user preferences.",
       model="gpt-4o-mini",
       memory=LongTermMemory("./assistant_memory")
   )
   async def learning_assistant(
       user_id: str,
       message: str
   ) -> str:
       """An assistant that learns and remembers user preferences."""
       pass
   
   # First interaction
   await learning_assistant("user123", "I prefer Python over Java")
   
   # Later interaction - remembers preference
   response = await learning_assistant(
       "user123", 
       "What programming language should I use for this project?"
   )

Streaming Responses
~~~~~~~~~~~~~~~~~~~

Enable streaming for long responses:

.. code-block:: python

   @smart_func(
       instructions="You are a story writer. Create engaging stories.",
       model="gpt-4o",
       stream=True
   )
   async def write_story(
       prompt: str,
       genre: str,
       length: str = "short"
   ) -> AsyncIterator[str]:
       """Write a story based on the prompt."""
       pass
   
   # Stream the response
   async for chunk in write_story(
       prompt="A robot discovers emotions",
       genre="sci-fi"
   ):
       print(chunk, end="", flush=True)

Complex Examples
----------------

Data Processing Pipeline
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from typing import List, Dict, Any
   import pandas as pd
   
   @smart_func(
       instructions="""You are a data analyst. Analyze datasets and provide insights.
       Focus on finding patterns, anomalies, and actionable recommendations.""",
       model="gpt-4o",
       tools=[pd.read_csv, pd.DataFrame.describe]
   )
   async def analyze_dataset(
       file_path: str,
       analysis_type: str = "general"
   ) -> Dict[str, Any]:
       """Analyze a dataset and return insights."""
       pass
   
   insights = await analyze_dataset(
       "sales_data.csv",
       analysis_type="trend_analysis"
   )

Multi-Step Workflow
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class ResearchReport(BaseModel):
       title: str
       summary: str
       key_findings: List[str]
       recommendations: List[str]
       sources: List[str]
   
   @smart_func(
       instructions="""You are a research analyst. Conduct thorough research and 
       create comprehensive reports. Always cite your sources.""",
       model="gpt-4o",
       tools=[search_web, analyze_document, create_chart]
   )
   async def create_research_report(
       topic: str,
       focus_areas: List[str],
       max_sources: int = 10
   ) -> ResearchReport:
       """Create a comprehensive research report on the given topic."""
       pass
   
   report = await create_research_report(
       topic="AI in Healthcare",
       focus_areas=["diagnosis", "treatment", "ethics"],
       max_sources=15
   )

API Integration
~~~~~~~~~~~~~~~

.. code-block:: python

   import aiohttp
   
   async def fetch_weather_api(city: str) -> dict:
       """Fetch weather data from API."""
       async with aiohttp.ClientSession() as session:
           async with session.get(f"https://api.weather.com/{city}") as resp:
               return await resp.json()
   
   @smart_func(
       instructions="You are a weather assistant. Provide weather information and advice.",
       model="gpt-4o-mini",
       tools=[fetch_weather_api]
   )
   async def weather_advisor(
       location: str,
       activity: str = None
   ) -> str:
       """Provide weather information and activity recommendations."""
       pass
   
   advice = await weather_advisor(
       location="San Francisco",
       activity="hiking"
   )

Error Handling
--------------

Graceful error handling in smart functions:

.. code-block:: python

   @smart_func(
       instructions="You are a calculator. Perform mathematical operations safely.",
       model="gpt-4o-mini",
       error_handling="graceful"
   )
   async def safe_calculate(expression: str) -> Union[float, str]:
       """Safely evaluate mathematical expressions."""
       pass
   
   # Handles errors gracefully
   result = await safe_calculate("10 / 0")
   # Returns: "Error: Division by zero is undefined"
   
   # Custom error handler
   async def custom_error_handler(error: Exception, context: dict) -> str:
       if isinstance(error, ValueError):
           return f"Invalid input: {context.get('expression')}"
       return f"An error occurred: {str(error)}"
   
   @smart_func(
       instructions="Calculate with custom error handling.",
       model="gpt-4o-mini",
       error_handler=custom_error_handler
   )
   async def calculate_custom(expression: str) -> float:
       pass

Configuration Options
---------------------

All smart function parameters:

.. code-block:: python

   @smart_func(
       instructions="Agent instructions",          # Required
       model="gpt-4o-mini",                       # Model selection
       temperature=0.7,                           # Creativity level
       max_tokens=1000,                           # Response limit
       tools=[],                                  # Available tools
       memory=None,                               # Memory instance
       stream=False,                              # Enable streaming
       parallel_tools=True,                       # Parallel execution
       error_handling="raise",                    # Error strategy
       timeout=30,                                # Timeout in seconds
       retry_attempts=3,                          # Retry on failure
       cache_responses=True,                      # Cache results
       cache_ttl=3600,                           # Cache duration
   )
   async def configured_function(...) -> ...:
       pass

Best Practices
--------------

1. **Clear Function Names**: Use descriptive names that indicate purpose
2. **Type Annotations**: Always include type hints for clarity
3. **Docstrings**: Document function purpose and parameters
4. **Error Handling**: Implement appropriate error strategies
5. **Tool Selection**: Only include necessary tools
6. **Response Types**: Use structured types when possible

Performance Optimization
------------------------

Caching
~~~~~~~

.. code-block:: python

   from functools import lru_cache
   
   @smart_func(
       instructions="Expensive analysis function",
       model="gpt-4o",
       cache_responses=True,
       cache_ttl=3600  # 1 hour
   )
   @lru_cache(maxsize=100)
   async def expensive_analysis(data: str) -> dict:
       """Perform expensive analysis with caching."""
       pass

Batch Processing
~~~~~~~~~~~~~~~~

.. code-block:: python

   @smart_func(
       instructions="Process multiple items efficiently",
       model="gpt-4o-mini"
   )
   async def batch_process(items: List[str]) -> List[dict]:
       """Process multiple items in a single call."""
       pass
   
   # More efficient than individual calls
   results = await batch_process(["item1", "item2", "item3"])

Testing Smart Functions
-----------------------

.. code-block:: python

   import pytest
   from unittest.mock import Mock
   
   @pytest.mark.asyncio
   async def test_smart_function():
       # Test with mocked agent
       with mock_smart_func() as mocked:
           mocked.return_value = {"result": "test"}
           
           result = await my_smart_function("input")
           assert result["result"] == "test"
   
   # Integration test
   @pytest.mark.asyncio
   @pytest.mark.integration
   async def test_real_smart_function():
       result = await analyze_text("Test text")
       assert "sentiment" in result
       assert isinstance(result["sentiment"], str)