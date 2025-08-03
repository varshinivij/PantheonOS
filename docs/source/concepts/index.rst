Concepts
========

This section introduces the core concepts in Pantheon. Understanding these fundamental building blocks will help you effectively use the framework to build sophisticated multi-agent systems.

Core Concepts Overview
----------------------

Pantheon is built around several key abstractions:

.. toctree::
   :maxdepth: 1

   agent
   team
   memory
   toolset
   endpoint
   chatroom

Agent
-----

An **Agent** is the fundamental unit in Pantheon - an AI-powered entity with specific instructions, capabilities, and memory. Agents can:

- Process natural language inputs
- Use tools to perform actions
- Maintain conversation context
- Collaborate with other agents

Learn more: :doc:`agent`

Team
----

A **Team** is a collection of agents working together following specific collaboration patterns. Teams enable:

- Task distribution among specialized agents
- Sequential processing workflows
- Parallel problem-solving
- Dynamic agent selection

Learn more: :doc:`team`

Memory
------

**Memory** systems allow agents to persist information across conversations and sessions. This includes:

- Conversation history
- Learned information
- Shared knowledge between agents
- Long-term storage

Learn more: :doc:`memory`

Toolset
-------

**Toolsets** extend agent capabilities by providing access to external functions and services:

- Code execution (Python, R, Shell)
- Web browsing and search
- File operations
- Custom integrations

Learn more: :doc:`toolset`

Endpoint
--------

An **Endpoint** is a network service that exposes agent or toolset functionality:

- Remote agent services
- Distributed tool execution
- API access points
- Service discovery

Learn more: :doc:`endpoint`

ChatRoom
--------

A **ChatRoom** is an interactive service that hosts agent conversations:

- Web UI integration
- Session management
- Real-time interactions
- Multi-user support

Learn more: :doc:`chatroom`

How They Work Together
----------------------

These concepts form a coherent system:

1. **Agents** use **Toolsets** to perform actions
2. **Teams** coordinate multiple **Agents** for complex tasks
3. **Memory** persists information across agent interactions
4. **Endpoints** enable distributed deployment of agents and tools
5. **ChatRooms** provide user-friendly interfaces to interact with the system

Example Flow
~~~~~~~~~~~~

.. code-block:: text

    User → ChatRoom → Team → Agent 1 → Toolset → Result
                            ↓
                          Agent 2 → Memory → Result
                            ↓
                        Final Response → User

This modular architecture allows you to:

- Start simple with a single agent
- Scale up to complex multi-agent systems
- Distribute components across infrastructure
- Maintain flexibility in system design