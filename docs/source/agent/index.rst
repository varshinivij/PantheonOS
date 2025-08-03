Agent
=====

This section covers the Agent API and related functionality in detail. Agents are the core building blocks of Pantheon, providing AI-powered entities that can reason, use tools, and collaborate.

.. toctree::
   :maxdepth: 2
   
   agent_api
   smart_func_api
   remote_agent

Overview
--------

The Agent module provides:

- **Core Agent Class**: The main ``Agent`` class for creating AI agents
- **Tool Integration**: Decorator-based tool creation and management
- **Smart Functions**: Convert agents into callable functions
- **Remote Agents**: Deploy and access agents over the network
- **Memory Systems**: Built-in conversation and long-term memory
- **Streaming Support**: Real-time response streaming

Quick Example
-------------

.. code-block:: python

   from pantheon.agent import Agent
   
   # Create an agent
   agent = Agent(
       name="assistant",
       instructions="You are a helpful AI assistant.",
       model="gpt-4o-mini"
   )
   
   # Add a tool
   @agent.tool
   def calculate(expression: str) -> float:
       """Safely evaluate a mathematical expression."""
       return eval(expression)  # Use safe evaluation in production
   
   # Run the agent
   response = await agent.run([
       {"role": "user", "content": "What is 2 + 2?"}
   ])
   
   print(response.messages[-1]["content"])

Key Features
------------

Model Support
~~~~~~~~~~~~~

Agents support various LLM providers:

- OpenAI models (GPT-4, GPT-3.5)
- Anthropic Claude
- Google Gemini
- Local models via Ollama
- Custom model integrations

Tool Capabilities
~~~~~~~~~~~~~~~~~

Agents can use:

- Custom Python functions
- Built-in toolsets (Python, R, Shell, Web)
- Remote toolsets over the network
- Async tools for I/O operations
- Parallel tool execution

Memory Management
~~~~~~~~~~~~~~~~~

Built-in memory features:

- Automatic conversation tracking
- Long-term memory persistence
- Shared memory between agents
- Vector memory for semantic search

Response Formats
~~~~~~~~~~~~~~~~

Flexible output options:

- Text responses
- Structured data (Pydantic models)
- Streaming responses
- Tool call results
- Mixed content types

Agent Patterns
--------------

The Agent module supports various usage patterns:

**Standalone Agents**
   Single agents for specific tasks

**Tool-Enhanced Agents**
   Agents with custom capabilities

**Remote Agents**
   Distributed agent deployment

**Smart Functions**
   Agents as callable functions

**Memory-Enabled Agents**
   Agents with persistent knowledge

See the following sections for detailed API documentation and examples.