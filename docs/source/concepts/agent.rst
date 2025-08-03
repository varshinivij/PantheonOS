Agent
=====

An Agent is the fundamental building block in Pantheon - an AI-powered entity that can understand instructions, use tools, maintain memory, and collaborate with other agents.

What is an Agent?
-----------------

An agent in Pantheon is:

- **Autonomous**: Can make decisions and take actions independently
- **Tool-enabled**: Can use various tools to extend its capabilities
- **Stateful**: Maintains context and memory across interactions
- **Collaborative**: Can work with other agents in teams

Core Components
---------------

Instructions
~~~~~~~~~~~~

Every agent has instructions that define its behavior and personality:

.. code-block:: python

   agent = Agent(
       name="researcher",
       instructions="You are an expert researcher. You excel at finding and analyzing information from various sources. Always cite your sources."
   )

Model Selection
~~~~~~~~~~~~~~~

Agents can use different LLM models based on requirements:

.. code-block:: python

   # For complex reasoning
   reasoning_agent = Agent(
       name="analyzer",
       model="o1-preview",
       instructions="Analyze complex problems step by step."
   )
   
   # For quick responses
   fast_agent = Agent(
       name="assistant",
       model="gpt-4o-mini",
       instructions="Provide quick, helpful responses."
   )

Tools and Capabilities
~~~~~~~~~~~~~~~~~~~~~~

Agents become powerful through tools:

.. code-block:: python

   from pantheon.agent import Agent
   
   agent = Agent(name="assistant", instructions="You are helpful.")
   
   # Add custom tools
   @agent.tool
   def calculate(expression: str) -> float:
       """Evaluate a mathematical expression."""
       return eval(expression)  # In production, use safe evaluation
   
   # Add pre-built toolsets
   from magique.ai.tools.web_browse import duckduckgo_search
   agent.tools.append(duckduckgo_search)

Memory and Context
~~~~~~~~~~~~~~~~~~

Agents maintain conversation context automatically:

.. code-block:: python

   # Context is maintained across calls
   response1 = await agent.run([
       {"role": "user", "content": "My name is Alice"}
   ])
   
   response2 = await agent.run([
       {"role": "user", "content": "What's my name?"}
   ])
   # Agent remembers: "Your name is Alice"

Agent Lifecycle
---------------

Creation
~~~~~~~~

Agents can be created programmatically or from configuration:

.. code-block:: python

   # Programmatic creation
   agent = Agent(
       name="expert",
       instructions="You are a domain expert.",
       model="gpt-4o",
       temperature=0.7
   )
   
   # From configuration
   agent = Agent.from_config("agent_config.yaml")

Execution
~~~~~~~~~

Agents process messages and return responses:

.. code-block:: python

   # Synchronous-style execution
   messages = [{"role": "user", "content": "Hello!"}]
   response = await agent.run(messages)
   
   # Streaming execution
   async for chunk in agent.run_stream(messages):
       print(chunk.get("content", ""), end="")

Tool Execution
~~~~~~~~~~~~~~

When agents use tools, the process is:

1. Agent decides which tool to use
2. Calls the tool with appropriate parameters
3. Processes the tool's output
4. Incorporates results into the response

Advanced Features
-----------------

Structured Output
~~~~~~~~~~~~~~~~~

Agents can return structured data:

.. code-block:: python

   from pydantic import BaseModel
   
   class Analysis(BaseModel):
       summary: str
       sentiment: str
       key_points: list[str]
   
   agent = Agent(
       name="analyzer",
       instructions="Analyze text and return structured data."
   )
   
   result = await agent.run(
       messages=[{"role": "user", "content": "Analyze this text..."}],
       response_format=Analysis
   )
   # result is an Analysis instance

Context Variables
~~~~~~~~~~~~~~~~~

Pass additional context to agents:

.. code-block:: python

   response = await agent.run(
       messages=messages,
       context_variables={
           "user_id": "123",
           "session_id": "abc",
           "preferences": {"language": "en"}
       }
   )

Parallel Tool Execution
~~~~~~~~~~~~~~~~~~~~~~~

Agents can execute multiple tools in parallel for efficiency:

.. code-block:: python

   agent = Agent(
       name="multi_tool",
       instructions="Use multiple tools efficiently.",
       parallel_tool_calls=True
   )

Remote Agents
~~~~~~~~~~~~~

Agents can run on remote machines:

.. code-block:: python

   # On remote machine
   agent = Agent(name="remote_expert", instructions="...")
   await agent.start_service(port=8000)
   
   # On local machine
   from pantheon.agent import RemoteAgent
   remote_agent = RemoteAgent("http://remote-host:8000")
   response = await remote_agent.run(messages)

Best Practices
--------------

1. **Clear Instructions**: Write specific, clear instructions that guide agent behavior
2. **Appropriate Models**: Choose models based on task complexity and response time needs
3. **Tool Selection**: Only add tools that are necessary for the agent's role
4. **Error Handling**: Implement proper error handling for tool failures
5. **Testing**: Test agents with various inputs to ensure robust behavior

Common Patterns
---------------

Specialist Agents
~~~~~~~~~~~~~~~~~

Create agents with focused expertise:

.. code-block:: python

   data_analyst = Agent(
       name="data_analyst",
       instructions="You specialize in data analysis and visualization. Always validate data before analysis."
   )
   
   writer = Agent(
       name="writer",
       instructions="You are an expert technical writer. Focus on clarity and accuracy."
   )

Tool-First Agents
~~~~~~~~~~~~~~~~~

Agents that primarily use tools:

.. code-block:: python

   code_executor = Agent(
       name="code_executor",
       instructions="Execute user's code requests safely. Always explain what the code does.",
       tools=[python_interpreter, static_analyzer]
   )

Validator Agents
~~~~~~~~~~~~~~~~

Agents that verify work:

.. code-block:: python

   validator = Agent(
       name="validator",
       instructions="Review and validate outputs. Check for accuracy, completeness, and potential issues."
   )