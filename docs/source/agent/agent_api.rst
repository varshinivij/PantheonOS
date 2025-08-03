Agent API
=========

The Agent class is the core component of Pantheon, providing a flexible interface for creating AI-powered agents with tools, memory, and collaboration capabilities.

Agent Class
-----------

.. code-block:: python

   from pantheon.agent import Agent

Constructor
~~~~~~~~~~~

.. code-block:: python

   Agent(
       name: str,
       instructions: str,
       model: str = "gpt-4o-mini",
       tools: List[Callable] = None,
       temperature: float = 0.7,
       max_tokens: int = None,
       memory: Memory = None,
       parallel_tool_calls: bool = True,
       **kwargs
   )

**Parameters:**

- ``name`` (str): Unique identifier for the agent
- ``instructions`` (str): System instructions defining agent behavior
- ``model`` (str): LLM model to use (default: "gpt-4o-mini")
- ``tools`` (List[Callable]): List of tool functions
- ``temperature`` (float): Sampling temperature (0-2, default: 0.7)
- ``max_tokens`` (int): Maximum response tokens
- ``memory`` (Memory): Memory instance for persistence
- ``parallel_tool_calls`` (bool): Enable parallel tool execution
- ``**kwargs``: Additional model-specific parameters

Core Methods
------------

run()
~~~~~

Execute the agent with messages:

.. code-block:: python

   async def run(
       messages: List[Dict[str, Any]],
       context_variables: Dict[str, Any] = None,
       response_format: Type[BaseModel] = None,
       **kwargs
   ) -> AgentResponse

**Example:**

.. code-block:: python

   response = await agent.run([
       {"role": "user", "content": "Hello!"}
   ])
   
   # With context
   response = await agent.run(
       messages=[{"role": "user", "content": "Process this data"}],
       context_variables={"user_id": "123", "session": "abc"}
   )
   
   # With structured output
   from pydantic import BaseModel
   
   class Analysis(BaseModel):
       sentiment: str
       score: float
   
   response = await agent.run(
       messages=[{"role": "user", "content": "Analyze: I love this!"}],
       response_format=Analysis
   )

run_stream()
~~~~~~~~~~~~

Stream responses in real-time:

.. code-block:: python

   async def run_stream(
       messages: List[Dict[str, Any]],
       context_variables: Dict[str, Any] = None,
       process_chunk: Callable = None,
       **kwargs
   ) -> AsyncIterator[Dict[str, Any]]

**Example:**

.. code-block:: python

   # Simple streaming
   async for chunk in agent.run_stream(messages):
       print(chunk.get("content", ""), end="", flush=True)
   
   # With chunk processor
   async def process(chunk):
       # Custom processing
       print(f"Chunk: {chunk}")
   
   response = await agent.run_stream(
       messages,
       process_chunk=process
   )

chat()
~~~~~~

Interactive chat session:

.. code-block:: python

   async def chat(
       initial_message: str = None,
       context_variables: Dict[str, Any] = None
   ) -> None

**Example:**

.. code-block:: python

   # Start interactive chat
   await agent.chat()
   
   # With initial message
   await agent.chat("Hello! Let's discuss Python.")

Tool Management
---------------

Adding Tools
~~~~~~~~~~~~

Multiple ways to add tools to an agent:

.. code-block:: python

   # Method 1: Decorator
   @agent.tool
   def search_web(query: str) -> str:
       """Search the web for information."""
       return f"Results for: {query}"
   
   # Method 2: Constructor
   def calculate(expression: str) -> float:
       """Calculate mathematical expressions."""
       return eval(expression)
   
   agent = Agent(
       name="calculator",
       instructions="You can perform calculations.",
       tools=[calculate]
   )
   
   # Method 3: Add after creation
   agent.tools.append(my_tool_function)

Tool Requirements
~~~~~~~~~~~~~~~~~

Tools must follow these requirements:

1. **Type Hints**: All parameters must have type annotations
2. **Docstring**: Must include a description
3. **Return Value**: Should return JSON-serializable data

.. code-block:: python

   @agent.tool
   def good_tool(
       text: str,
       count: int = 10,
       include_metadata: bool = False
   ) -> Dict[str, Any]:
       """
       Process text with specified parameters.
       
       Args:
           text: The text to process
           count: Number of results to return
           include_metadata: Whether to include metadata
           
       Returns:
           Dictionary with processed results
       """
       results = process_text(text, count)
       
       if include_metadata:
           results["metadata"] = get_metadata()
           
       return results

Remote Toolsets
~~~~~~~~~~~~~~~

Connect to remote toolset services:

.. code-block:: python

   # Connect to remote toolset
   await agent.remote_toolset("http://toolset-server:8001")
   
   # Multiple remote toolsets
   await agent.remote_toolset([
       "http://python-tools:8001",
       "http://web-tools:8002"
   ])

Memory Integration
------------------

Conversation Memory
~~~~~~~~~~~~~~~~~~~

Automatic conversation tracking:

.. code-block:: python

   from pantheon.memory import ConversationMemory
   
   agent = Agent(
       name="assistant",
       instructions="You are a helpful assistant.",
       memory=ConversationMemory()
   )
   
   # Conversation is automatically saved
   await agent.run([{"role": "user", "content": "Remember my name is Alice"}])
   await agent.run([{"role": "user", "content": "What's my name?"}])
   # Agent responds: "Your name is Alice"

Custom Memory Operations
~~~~~~~~~~~~~~~~~~~~~~~~

Direct memory access:

.. code-block:: python

   # Store information
   await agent.memory.set("user_preference", "dark_mode")
   
   # Retrieve information
   preference = await agent.memory.get("user_preference")
   
   # Search memory
   related = await agent.memory.search("user_*")

Advanced Features
-----------------

Context Variables
~~~~~~~~~~~~~~~~~

Pass additional context to agents:

.. code-block:: python

   response = await agent.run(
       messages=messages,
       context_variables={
           "user_id": "123",
           "session_id": "abc",
           "user_role": "admin",
           "timestamp": datetime.now()
       }
   )
   
   # Access in tools
   @agent.tool
   def get_user_data(field: str) -> str:
       """Get user data based on context."""
       user_id = agent.context_variables.get("user_id")
       return fetch_user_field(user_id, field)

Error Handling
~~~~~~~~~~~~~~

Robust error handling patterns:

.. code-block:: python

   try:
       response = await agent.run(messages)
   except ToolExecutionError as e:
       print(f"Tool failed: {e.tool_name} - {e.message}")
       # Retry without the tool
       response = await agent.run(
           messages + [{"role": "system", "content": f"Tool {e.tool_name} is unavailable"}]
       )
   except ModelError as e:
       print(f"Model error: {e}")
       # Fallback to different model
       agent.model = "gpt-3.5-turbo"
       response = await agent.run(messages)

Custom Response Processing
~~~~~~~~~~~~~~~~~~~~~~~~~~

Process responses before returning:

.. code-block:: python

   class CustomAgent(Agent):
       async def process_response(self, response):
           # Add metadata
           response.metadata = {
               "timestamp": datetime.now(),
               "model_used": self.model,
               "token_count": response.usage.total_tokens
           }
           
           # Log response
           await self.log_response(response)
           
           return response

Agent Lifecycle
~~~~~~~~~~~~~~~

Manage agent lifecycle:

.. code-block:: python

   # Initialize agent
   agent = Agent(name="worker", instructions="...")
   
   # Start background services
   await agent.start()
   
   # Use agent
   response = await agent.run(messages)
   
   # Cleanup
   await agent.stop()
   
   # Context manager pattern
   async with Agent(name="temp", instructions="...") as agent:
       response = await agent.run(messages)
       # Automatically cleaned up

Configuration
-------------

From Configuration File
~~~~~~~~~~~~~~~~~~~~~~~

Load agents from YAML:

.. code-block:: yaml

   # agent_config.yaml
   name: research_assistant
   instructions: |
     You are an expert research assistant.
     Always cite your sources.
   model: gpt-4o
   temperature: 0.5
   tools:
     - search_web
     - analyze_document
   memory:
     type: long_term
     path: ./agent_memory

.. code-block:: python

   agent = Agent.from_config("agent_config.yaml")

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

Configure via environment:

.. code-block:: python

   # Reads from environment
   # AGENT_MODEL=gpt-4
   # AGENT_TEMPERATURE=0.8
   
   agent = Agent(
       name="assistant",
       instructions="...",
       model=os.getenv("AGENT_MODEL", "gpt-4o-mini"),
       temperature=float(os.getenv("AGENT_TEMPERATURE", "0.7"))
   )

Best Practices
--------------

1. **Clear Instructions**: Write specific, actionable instructions
2. **Tool Selection**: Only include necessary tools
3. **Error Recovery**: Implement fallback strategies
4. **Memory Management**: Use appropriate memory types
5. **Resource Usage**: Monitor token usage and costs
6. **Testing**: Test with various inputs and edge cases

Performance Tips
----------------

- Use streaming for better user experience
- Enable parallel tool calls when possible
- Cache frequently used data in memory
- Choose appropriate models for tasks
- Implement request batching for efficiency