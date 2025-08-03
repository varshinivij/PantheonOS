Project Architecture
====================

Pantheon follows a modular, distributed architecture designed for flexibility, scalability, and ease of use. This document provides an overview of the system's structure and key components.

System Overview
---------------

.. code-block:: text

    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │  pantheon   │     │  pantheon   │     │  pantheon   │
    │     ui      │────▶│     hub     │────▶│   agents    │
    │  (Vue.js)   │     │  (FastAPI)  │     │   (Core)    │
    └─────────────┘     └─────────────┘     └─────────────┘
           │                    │                    │
           │                    │                    │
           ▼                    ▼                    ▼
    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │   Browser   │     │  Database   │     │   LLM APIs  │
    │  Interface  │     │  (SQLite)   │     │ (OpenAI...)  │
    └─────────────┘     └─────────────┘     └─────────────┘

Core Components
---------------

pantheon-agents
~~~~~~~~~~~~~~~

The foundation of the system, providing:

- **Agent Framework**: Base classes and interfaces for creating agents
- **Team Implementations**: Various team collaboration patterns
- **Memory Systems**: Persistent storage and retrieval mechanisms
- **Tool Framework**: Extensible system for agent capabilities
- **ChatRoom Service**: Interactive session management

Key modules:

- ``pantheon.agent``: Core agent implementation
- ``pantheon.team``: Team coordination patterns
- ``pantheon.memory``: Memory persistence layer
- ``pantheon.tools``: Built-in toolsets
- ``pantheon.chatroom``: Service layer for interactions
- ``pantheon.remote``: Distributed computing support

pantheon-hub
~~~~~~~~~~~~

Backend API service built with FastAPI:

- **REST API**: HTTP endpoints for all operations
- **Authentication**: Secure access control
- **Session Management**: Handle multiple concurrent users
- **Database Layer**: Persistent storage for configurations
- **WebSocket Support**: Real-time communication

Key modules:

- ``pantheon_hub.api``: API endpoint definitions
- ``pantheon_hub.core``: Core business logic
- ``pantheon_hub.services``: Service layer implementations
- ``pantheon_hub.models``: Data models and schemas

pantheon-ui
~~~~~~~~~~~

Modern web interface using Vue.js 3:

- **Responsive Design**: Works on desktop and mobile
- **Real-time Updates**: Live streaming of agent responses
- **Session History**: View and continue past conversations
- **Configuration UI**: Easy agent and team setup
- **TypeScript**: Full type safety

Key components:

- ``stores/``: Pinia state management
- ``components/``: Reusable UI components
- ``network/``: API client implementation
- ``views/``: Main application pages

Data Flow
---------

1. **User Interaction**
   
   - User sends message via UI
   - UI calls Hub API endpoint
   - Hub validates and processes request

2. **Agent Processing**
   
   - Hub invokes appropriate agent/team
   - Agent processes with available tools
   - Results streamed back through Hub

3. **Response Delivery**
   
   - Hub formats agent response
   - UI receives and displays results
   - Session state updated

Communication Protocols
-----------------------

HTTP REST API
~~~~~~~~~~~~~

Standard RESTful endpoints for:

- Agent management
- ChatRoom operations
- Session handling
- Configuration

WebSocket
~~~~~~~~~

Real-time bidirectional communication for:

- Streaming agent responses
- Live status updates
- Interactive sessions

Internal RPC
~~~~~~~~~~~~

For distributed operations:

- Remote agent invocation
- Tool service communication
- Cross-process coordination

Storage Architecture
--------------------

Database (SQLite)
~~~~~~~~~~~~~~~~~

Stores:

- User sessions
- Agent configurations
- ChatRoom metadata
- System settings

File-based Memory
~~~~~~~~~~~~~~~~~

Persistent storage for:

- Conversation history
- Agent memory states
- Temporary tool outputs
- Cache data

Distributed Architecture
------------------------

Remote Agents
~~~~~~~~~~~~~

Agents can run on separate machines:

.. code-block:: python

    # On remote machine
    agent = Agent(...)
    await agent.start_service(port=8000)
    
    # On main machine
    remote_agent = RemoteAgent("http://remote-host:8000")

Remote Toolsets
~~~~~~~~~~~~~~~

Distribute computational tools:

.. code-block:: python

    # Tool server
    toolset = PythonInterpreterToolSet()
    await toolset.start_service(port=8001)
    
    # Agent using remote tool
    agent.remote_toolset("http://tool-server:8001")

Security Considerations
-----------------------

- **API Authentication**: Token-based authentication for Hub API
- **Sandboxed Execution**: Tools run in isolated environments
- **Input Validation**: All inputs sanitized before processing
- **Rate Limiting**: Prevent abuse of resources
- **Audit Logging**: Track all operations for security

Deployment Options
------------------

Local Development
~~~~~~~~~~~~~~~~~

- Single machine setup
- All components on localhost
- SQLite database
- File-based memory

Production Deployment
~~~~~~~~~~~~~~~~~~~~~

- Distributed services
- Load balancing
- External database (PostgreSQL)
- Object storage for memory
- Container orchestration (K8s)

Cloud Deployment
~~~~~~~~~~~~~~~~

- Managed services integration
- Auto-scaling capabilities
- CDN for UI assets
- Distributed tracing

Performance Optimization
------------------------

- **Async Operations**: Non-blocking I/O throughout
- **Connection Pooling**: Efficient resource usage
- **Caching Layer**: Reduce redundant operations
- **Lazy Loading**: Load components on demand
- **Streaming Responses**: Immediate feedback to users

Monitoring and Observability
----------------------------

- **Structured Logging**: Consistent log formats
- **Metrics Collection**: Performance tracking
- **Health Checks**: Service availability monitoring
- **Distributed Tracing**: Request flow visualization
- **Error Tracking**: Centralized error management