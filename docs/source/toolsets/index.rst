Toolsets
========

This section covers the various toolsets available in Pantheon that extend agent capabilities. Toolsets provide agents with the ability to execute code, browse the web, manipulate files, and integrate with external services.

.. toctree::
   :maxdepth: 2
   
   python_interpreter
   r_interpreter
   shell
   web_browse
   scraper_api
   file_editor
   vector_rag
   rag_system

Overview
--------

Pantheon provides a rich ecosystem of toolsets:

- **Code Execution**: Python, R, and Shell interpreters
- **Web Access**: Browsing, searching, and scraping
- **File Operations**: Reading, writing, and editing files
- **RAG Systems**: Vector databases and retrieval systems
- **Custom Toolsets**: Build your own specialized tools

General Design Principles
-------------------------

All toolsets follow consistent design patterns:

1. **Async-First**: All operations are asynchronous
2. **Security**: Sandboxed execution environments
3. **Error Handling**: Graceful error recovery
4. **Type Safety**: Full type hints and validation
5. **Extensibility**: Easy to extend and customize

Creating Custom Toolsets
------------------------

Basic Custom Toolset
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from magique.ai.toolset import Toolset
   
   class MyCustomToolset(Toolset):
       def __init__(self, name="custom_tools"):
           super().__init__(name)
           
       def get_tools(self):
           """Return list of available tools."""
           return [
               self.tool1,
               self.tool2,
               self.complex_tool
           ]
           
       async def tool1(self, param: str) -> str:
           """Simple tool that processes a string."""
           return f"Processed: {param}"
           
       async def tool2(self, x: int, y: int) -> int:
           """Tool that performs calculation."""
           return x + y
           
       async def complex_tool(self, data: dict) -> dict:
           """Complex tool with multiple operations."""
           # Process data
           result = await self.process_data(data)
           # Validate result
           validated = await self.validate_result(result)
           return validated

Toolset with External Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import aiohttp
   from typing import List, Dict
   
   class APIToolset(Toolset):
       def __init__(self, api_key: str, base_url: str):
           super().__init__("api_tools")
           self.api_key = api_key
           self.base_url = base_url
           self.session = None
           
       async def initialize(self):
           """Initialize resources."""
           self.session = aiohttp.ClientSession(
               headers={"Authorization": f"Bearer {self.api_key}"}
           )
           
       async def cleanup(self):
           """Clean up resources."""
           if self.session:
               await self.session.close()
               
       def get_tools(self):
           return [
               self.fetch_data,
               self.post_data,
               self.search
           ]
           
       async def fetch_data(self, endpoint: str) -> Dict:
           """Fetch data from API endpoint."""
           async with self.session.get(f"{self.base_url}/{endpoint}") as resp:
               return await resp.json()
               
       async def post_data(self, endpoint: str, data: Dict) -> Dict:
           """Post data to API endpoint."""
           async with self.session.post(
               f"{self.base_url}/{endpoint}",
               json=data
           ) as resp:
               return await resp.json()
               
       async def search(self, query: str, filters: Dict = None) -> List[Dict]:
           """Search API with query and filters."""
           params = {"q": query}
           if filters:
               params.update(filters)
           async with self.session.get(
               f"{self.base_url}/search",
               params=params
           ) as resp:
               return await resp.json()

Remote Toolset Deployment
-------------------------

Deploy toolsets as services:

.. code-block:: python

   from magique.ai.toolset import run_toolset_service
   
   # Create toolset
   toolset = MyCustomToolset()
   
   # Run as service
   await run_toolset_service(
       toolset,
       host="0.0.0.0",
       port=8001,
       auth_token="secret-token"
   )
   
   # Agent connects to remote toolset
   agent = Agent(name="agent", instructions="...")
   await agent.remote_toolset("http://toolset-server:8001")

Toolset Composition
-------------------

Combine multiple toolsets:

.. code-block:: python

   class CompositeToolset(Toolset):
       def __init__(self):
           super().__init__("composite_tools")
           self.python_tools = PythonInterpreterToolSet()
           self.web_tools = WebBrowseToolSet()
           self.file_tools = FileToolSet()
           
       def get_tools(self):
           tools = []
           tools.extend(self.python_tools.get_tools())
           tools.extend(self.web_tools.get_tools())
           tools.extend(self.file_tools.get_tools())
           tools.append(self.integrated_analysis)
           return tools
           
       async def integrated_analysis(self, url: str) -> dict:
           """Fetch web data, analyze with Python, save results."""
           # Fetch data
           data = await self.web_tools.fetch_url(url)
           
           # Analyze with Python
           analysis = await self.python_tools.execute_code(f"""
               import json
               data = '''{data}'''
               # Analysis code here
               result = analyze(json.loads(data))
           """)
           
           # Save results
           await self.file_tools.write_file(
               "analysis_results.json",
               json.dumps(analysis)
           )
           
           return analysis

Best Practices
--------------

1. **Security First**: Always validate inputs and sanitize outputs
2. **Resource Management**: Properly initialize and cleanup resources
3. **Error Messages**: Provide clear, actionable error messages
4. **Documentation**: Document all tools with clear descriptions
5. **Testing**: Thoroughly test tools with various inputs
6. **Performance**: Consider caching and optimization

Common Patterns
---------------

Stateful Tools
~~~~~~~~~~~~~~

Tools that maintain state between calls:

.. code-block:: python

   class StatefulToolset(Toolset):
       def __init__(self):
           super().__init__("stateful_tools")
           self.state = {}
           
       async def set_context(self, key: str, value: Any) -> str:
           """Set a context value."""
           self.state[key] = value
           return f"Set {key} to {value}"
           
       async def get_context(self, key: str) -> Any:
           """Get a context value."""
           return self.state.get(key, f"No value set for {key}")
           
       async def process_with_context(self, data: str) -> str:
           """Process data using stored context."""
           context = self.state.get("processing_context", {})
           # Use context in processing
           return f"Processed {data} with context {context}"

Batch Processing Tools
~~~~~~~~~~~~~~~~~~~~~~

Tools optimized for batch operations:

.. code-block:: python

   class BatchToolset(Toolset):
       async def process_batch(self, items: List[str]) -> List[dict]:
           """Process multiple items efficiently."""
           # Process in parallel
           tasks = [self.process_single(item) for item in items]
           results = await asyncio.gather(*tasks)
           return results
           
       async def process_single(self, item: str) -> dict:
           """Process a single item."""
           # Processing logic
           return {"item": item, "result": "processed"}

Tool Validation
~~~~~~~~~~~~~~~

Validate tool inputs and outputs:

.. code-block:: python

   from pydantic import BaseModel, validator
   
   class ValidatedToolset(Toolset):
       class InputModel(BaseModel):
           text: str
           max_length: int = 1000
           
           @validator('text')
           def validate_text(cls, v):
               if len(v) > 10000:
                   raise ValueError("Text too long")
               return v
       
       class OutputModel(BaseModel):
           result: str
           confidence: float
           metadata: dict
       
       async def validated_tool(self, input_data: InputModel) -> OutputModel:
           """Tool with validated input/output."""
           # Process input
           result = await self.process(input_data.text)
           
           # Return validated output
           return self.OutputModel(
               result=result,
               confidence=0.95,
               metadata={"processed_at": datetime.now()}
           )