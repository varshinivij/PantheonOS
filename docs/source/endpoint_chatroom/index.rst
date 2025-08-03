Endpoint and Chatroom
=====================

This section covers the service layer of Pantheon - Endpoints for distributed deployment and ChatRooms for interactive agent sessions. These components enable scalable, production-ready multi-agent systems.

.. toctree::
   :maxdepth: 2
   
   architecture

Overview
--------

The service layer provides:

**Endpoints**
- Network-accessible agent and toolset services
- RESTful APIs and WebSocket support
- Authentication and authorization
- Load balancing and scaling
- Health monitoring

**ChatRooms**
- Interactive agent sessions
- Web UI integration
- Multi-user support
- Conversation persistence
- Real-time streaming

Architecture Overview
---------------------

.. code-block:: text

    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │   Web UI    │────▶│  ChatRoom   │────▶│   Agents    │
    │             │     │   Service   │     │             │
    └─────────────┘     └─────────────┘     └─────────────┘
           │                    │                    │
           │                    │                    │
           ▼                    ▼                    ▼
    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │   REST API  │     │  WebSocket  │     │  Endpoints  │
    │             │     │             │     │             │
    └─────────────┘     └─────────────┘     └─────────────┘

Quick Examples
--------------

Deploying an Agent as Endpoint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pantheon.agent import Agent
   
   # Create agent
   agent = Agent(
       name="api_agent",
       instructions="Process API requests.",
       model="gpt-4o-mini"
   )
   
   # Deploy as endpoint
   await agent.start_service(
       host="0.0.0.0",
       port=8000,
       auth_token="secret"
   )

Creating a ChatRoom
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pantheon.chatroom import ChatRoom
   from pantheon.team import SequentialTeam
   
   # Create team
   team = SequentialTeam([agent1, agent2, agent3])
   
   # Create ChatRoom
   chatroom = ChatRoom(
       name="Support Chat",
       team=team,
       enable_web_ui=True
   )
   
   # Start service
   await chatroom.start(port=8080)

Key Features
------------

Endpoints
~~~~~~~~~

- **Service Discovery**: Automatic registration and discovery
- **Load Balancing**: Distribute requests across instances
- **Fault Tolerance**: Handle failures gracefully
- **Monitoring**: Track performance and health
- **Security**: Authentication and encryption

ChatRooms
~~~~~~~~~

- **Session Management**: Handle multiple concurrent users
- **Real-time Communication**: WebSocket streaming
- **Persistence**: Save and restore conversations
- **Access Control**: User authentication and permissions
- **Customization**: Themes and branding

Common Patterns
---------------

Microservices Architecture
~~~~~~~~~~~~~~~~~~~~~~~~~~

Deploy each agent as a separate service:

.. code-block:: python

   # Agent services
   await research_agent.start_service(port=8001)
   await analysis_agent.start_service(port=8002)
   await writer_agent.start_service(port=8003)
   
   # Coordinator service
   coordinator = ChatRoom(
       name="Coordinator",
       remote_agents=[
           "http://localhost:8001",
           "http://localhost:8002",
           "http://localhost:8003"
       ]
   )

API Gateway Pattern
~~~~~~~~~~~~~~~~~~~

Central entry point for all services:

.. code-block:: python

   from pantheon.endpoint import APIGateway
   
   gateway = APIGateway(
       routes={
           "/chat": "http://chatroom:8080",
           "/agent/*": "http://agents:8000",
           "/tools/*": "http://tools:8001"
       },
       auth_enabled=True,
       rate_limiting=True
   )

Production Deployment
---------------------

Docker
~~~~~~

.. code-block:: dockerfile

   FROM python:3.9-slim
   
   WORKDIR /app
   COPY . .
   RUN pip install pantheon-agents
   
   EXPOSE 8000
   CMD ["python", "-m", "pantheon.chatroom"]

Kubernetes
~~~~~~~~~~

.. code-block:: yaml

   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: pantheon-chatroom
   spec:
     replicas: 3
     template:
       spec:
         containers:
         - name: chatroom
           image: pantheon/chatroom:latest
           ports:
           - containerPort: 8000

Best Practices
--------------

1. **Service Design**: Keep services focused and single-purpose
2. **API Versioning**: Version your endpoints
3. **Monitoring**: Implement comprehensive logging and metrics
4. **Security**: Use HTTPS and proper authentication
5. **Scalability**: Design for horizontal scaling
6. **Documentation**: Provide OpenAPI/Swagger docs

See the architecture page for detailed information about the service layer design and implementation.