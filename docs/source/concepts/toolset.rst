Toolset
=======

Toolsets extend agent capabilities by providing access to external functions, APIs, and services. They bridge the gap between AI reasoning and real-world actions.

What is a Toolset?
------------------

A toolset is a collection of functions that agents can use to:

- **Execute Code**: Run Python, R, or shell commands
- **Access Information**: Browse web, query databases
- **Manipulate Files**: Read, write, edit files
- **Integrate Services**: Connect to external APIs
- **Perform Computations**: Complex calculations and analysis

Built-in Toolsets
-----------------

Python Interpreter
~~~~~~~~~~~~~~~~~~

Execute Python code in a sandboxed environment:

.. code-block:: python

   from magique.ai.tools.python import PythonInterpreterToolSet
   from magique.ai.toolset import run_toolsets
   
   async def create_python_agent():
       toolset = PythonInterpreterToolSet("python_tool")
       
       async with run_toolsets([toolset]):
           agent = Agent(
               name="data_scientist",
               instructions="You can analyze data with Python."
           )
           await agent.remote_toolset(toolset.service_id)
           
           # Agent can now execute Python code
           await agent.run([{
               "role": "user",
               "content": "Calculate the mean of [1, 2, 3, 4, 5]"
           }])

R Interpreter
~~~~~~~~~~~~~

Statistical computing with R:

.. code-block:: python

   from magique.ai.tools.r import RInterpreterToolSet
   
   toolset = RInterpreterToolSet("r_stats")
   
   agent = Agent(
       name="statistician",
       instructions="Perform statistical analysis using R."
   )
   await agent.remote_toolset(toolset.service_id)

Shell Commands
~~~~~~~~~~~~~~

Execute system commands safely:

.. code-block:: python

   from magique.ai.tools.shell import ShellToolSet
   
   toolset = ShellToolSet(
       "shell_tool",
       allowed_commands=["ls", "pwd", "echo", "cat"]
   )
   
   agent = Agent(
       name="system_admin",
       instructions="Help with file system operations."
   )

Web Browsing
~~~~~~~~~~~~

Search and fetch web content:

.. code-block:: python

   from magique.ai.tools.web_browse import (
       duckduckgo_search,
       web_crawl
   )
   
   agent = Agent(
       name="researcher",
       instructions="Research topics using web search.",
       tools=[duckduckgo_search, web_crawl]
   )

File Operations
~~~~~~~~~~~~~~~

Read and write files:

.. code-block:: python

   from magique.ai.tools.filesystem import (
       read_file,
       write_file,
       list_directory
   )
   
   agent = Agent(
       name="file_manager",
       instructions="Manage files and directories.",
       tools=[read_file, write_file, list_directory]
   )

Creating Custom Tools
---------------------

Simple Function Tools
~~~~~~~~~~~~~~~~~~~~~

Convert any Python function into a tool:

.. code-block:: python

   from pantheon.agent import Agent
   
   agent = Agent(name="calculator", instructions="...")
   
   @agent.tool
   def calculate_compound_interest(
       principal: float,
       rate: float,
       time: int,
       n: int = 1
   ) -> float:
       """Calculate compound interest.
       
       Args:
           principal: Initial amount
           rate: Annual interest rate (as decimal)
           time: Time period in years
           n: Compounding frequency per year
           
       Returns:
           Final amount after compound interest
       """
       return principal * (1 + rate/n) ** (n * time)

Tool with Dependencies
~~~~~~~~~~~~~~~~~~~~~~

Tools can use external libraries:

.. code-block:: python

   @agent.tool
   def analyze_sentiment(text: str) -> dict:
       """Analyze sentiment of text using TextBlob."""
       from textblob import TextBlob
       
       blob = TextBlob(text)
       return {
           "polarity": blob.sentiment.polarity,
           "subjectivity": blob.sentiment.subjectivity,
           "sentiment": "positive" if blob.sentiment.polarity > 0 else "negative"
       }

Async Tools
~~~~~~~~~~~

Support for asynchronous operations:

.. code-block:: python

   @agent.tool
   async def fetch_weather(city: str) -> dict:
       """Fetch current weather for a city."""
       import aiohttp
       
       async with aiohttp.ClientSession() as session:
           url = f"https://api.weather.com/v1/location/{city}"
           async with session.get(url) as response:
               return await response.json()

Building Toolsets
-----------------

Custom Toolset Class
~~~~~~~~~~~~~~~~~~~~

Create reusable toolset classes:

.. code-block:: python

   from magique.ai.toolset import Toolset
   
   class DatabaseToolset(Toolset):
       def __init__(self, connection_string):
           super().__init__("database_tools")
           self.connection_string = connection_string
           
       def get_tools(self):
           return [
               self.query_database,
               self.insert_record,
               self.update_record
           ]
           
       async def query_database(self, query: str) -> list:
           """Execute a database query."""
           # Implementation here
           pass
           
       async def insert_record(self, table: str, data: dict) -> int:
           """Insert a record into database."""
           # Implementation here
           pass

Remote Toolsets
~~~~~~~~~~~~~~~

Deploy toolsets as services:

.. code-block:: python

   from magique.ai.toolset import run_toolset_service
   
   # Create and start toolset service
   toolset = DatabaseToolset("postgresql://...")
   await run_toolset_service(
       toolset,
       host="0.0.0.0",
       port=8001
   )
   
   # Agent connects to remote toolset
   agent = Agent(name="db_agent", instructions="...")
   await agent.remote_toolset("http://toolset-server:8001")

Tool Composition
~~~~~~~~~~~~~~~~

Combine multiple tools into complex operations:

.. code-block:: python

   class DataPipelineToolset(Toolset):
       def __init__(self):
           super().__init__("data_pipeline")
           self.python_tools = PythonInterpreterToolSet()
           self.file_tools = FileToolSet()
           
       async def process_csv(self, filename: str) -> dict:
           """Read CSV, process with pandas, save results."""
           # Read file
           content = await self.file_tools.read_file(filename)
           
           # Process with Python
           result = await self.python_tools.execute_code(f"""
               import pandas as pd
               from io import StringIO
               
               df = pd.read_csv(StringIO('{content}'))
               summary = df.describe().to_dict()
           """)
           
           # Save results
           await self.file_tools.write_file(
               "results.json",
               json.dumps(result)
           )
           
           return result

Advanced Features
-----------------

Tool Validation
~~~~~~~~~~~~~~~

Validate inputs before execution:

.. code-block:: python

   from pydantic import BaseModel, validator
   
   class QueryParams(BaseModel):
       table: str
       conditions: dict
       
       @validator('table')
       def validate_table(cls, v):
           allowed_tables = ['users', 'orders', 'products']
           if v not in allowed_tables:
               raise ValueError(f"Table must be one of {allowed_tables}")
           return v
   
   @agent.tool
   def safe_query(params: QueryParams) -> list:
       """Safely query database with validation."""
       # Params are automatically validated
       return execute_query(params.table, params.conditions)

Tool Permissions
~~~~~~~~~~~~~~~~

Control tool access:

.. code-block:: python

   class PermissionedToolset(Toolset):
       def __init__(self, user_role):
           self.user_role = user_role
           
       def get_tools(self):
           tools = [self.read_data]
           
           if self.user_role in ['admin', 'writer']:
               tools.append(self.write_data)
               
           if self.user_role == 'admin':
               tools.append(self.delete_data)
               
           return tools

Tool Monitoring
~~~~~~~~~~~~~~~

Track tool usage and performance:

.. code-block:: python

   from functools import wraps
   import time
   
   def monitor_tool(func):
       @wraps(func)
       async def wrapper(*args, **kwargs):
           start = time.time()
           try:
               result = await func(*args, **kwargs)
               duration = time.time() - start
               
               # Log successful execution
               await log_tool_usage(
                   tool_name=func.__name__,
                   duration=duration,
                   status="success"
               )
               return result
               
           except Exception as e:
               # Log errors
               await log_tool_usage(
                   tool_name=func.__name__,
                   duration=time.time() - start,
                   status="error",
                   error=str(e)
               )
               raise
       
       return wrapper
   
   @agent.tool
   @monitor_tool
   async def monitored_operation(data: str) -> str:
       """Operation with monitoring."""
       return process_data(data)

Best Practices
--------------

1. **Clear Documentation**: Write detailed docstrings for tools
2. **Error Handling**: Implement robust error handling
3. **Input Validation**: Validate all inputs before processing
4. **Security**: Never expose sensitive operations directly
5. **Performance**: Consider async operations for I/O-bound tasks
6. **Testing**: Thoroughly test tools before deployment

Common Patterns
---------------

Tool Chains
~~~~~~~~~~~

Chain tools for complex workflows:

.. code-block:: python

   @agent.tool
   def data_pipeline(csv_url: str) -> dict:
       """Download, process, and analyze CSV data."""
       # Download
       data = download_file(csv_url)
       
       # Process
       df = process_csv(data)
       
       # Analyze
       results = analyze_dataframe(df)
       
       # Visualize
       chart = create_visualization(results)
       
       return {
           "analysis": results,
           "visualization": chart
       }

Conditional Tools
~~~~~~~~~~~~~~~~~

Tools that adapt based on context:

.. code-block:: python

   @agent.tool
   def smart_search(query: str, search_type: str = "auto") -> list:
       """Search with automatic source selection."""
       if search_type == "auto":
           if "code" in query.lower():
               return search_github(query)
           elif "news" in query.lower():
               return search_news(query)
           else:
               return search_web(query)
       
       # Specific search types
       search_functions = {
           "code": search_github,
           "news": search_news,
           "academic": search_scholar,
           "web": search_web
       }
       
       return search_functions[search_type](query)