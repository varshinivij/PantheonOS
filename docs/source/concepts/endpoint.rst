Endpoint
========

Endpoints in Pantheon enable distributed deployment of agents and toolsets by exposing them as network services. This allows for scalable, modular architectures where components can run on different machines.

What is an Endpoint?
--------------------

An endpoint is a network-accessible service that:

- **Exposes Functionality**: Makes agents or tools available over the network
- **Enables Distribution**: Allows components to run on different machines
- **Provides APIs**: Offers standardized interfaces for communication
- **Supports Scaling**: Facilitates horizontal scaling of services

Types of Endpoints
------------------

Agent Endpoints
~~~~~~~~~~~~~~~

Deploy agents as standalone services:

.. code-block:: python

   from pantheon.agent import Agent
   
   # Create and configure agent
   agent = Agent(
       name="expert_agent",
       instructions="You are a domain expert.",
       model="gpt-4o"
   )
   
   # Start as endpoint service
   await agent.start_service(
       host="0.0.0.0",
       port=8000,
       auth_token="secret_token"  # Optional authentication
   )
   
   # Access from another machine
   from pantheon.remote import RemoteAgent
   
   remote_agent = RemoteAgent(
       "http://agent-server:8000",
       auth_token="secret_token"
   )
   
   response = await remote_agent.run(messages)

Toolset Endpoints
~~~~~~~~~~~~~~~~~

Expose toolsets as services:

.. code-block:: python

   from magique.ai.tools.python import PythonInterpreterToolSet
   from magique.ai.toolset import run_toolset_service
   
   # Create toolset
   toolset = PythonInterpreterToolSet("python_service")
   
   # Start as endpoint
   await run_toolset_service(
       toolset,
       host="0.0.0.0",
       port=8001
   )
   
   # Agent connects to remote toolset
   agent = Agent(name="compute_agent", instructions="...")
   await agent.remote_toolset("http://toolset-server:8001")

ChatRoom Endpoints
~~~~~~~~~~~~~~~~~~

ChatRoom services with HTTP/WebSocket interfaces:

.. code-block:: python

   from pantheon.chatroom import ChatRoom
   
   chatroom = ChatRoom(
       name="Support ChatRoom",
       agents=[support_agent, technical_agent]
   )
   
   # Start with web interface
   await chatroom.start(
       host="0.0.0.0",
       port=8002,
       enable_web_ui=True
   )

Endpoint Architecture
---------------------

Communication Protocol
~~~~~~~~~~~~~~~~~~~~~~

Endpoints use standardized protocols:

.. code-block:: text

   Client → HTTP/WebSocket → Endpoint → Service
     ↓                          ↓          ↓
   Request                  Process    Execute
     ↓                          ↓          ↓
   Response ← HTTP/WebSocket ← Format ← Result

API Structure
~~~~~~~~~~~~~

RESTful API design:

.. code-block:: python

   # Agent endpoint routes
   POST   /run          # Run agent with messages
   POST   /run_stream   # Stream agent responses
   GET    /info         # Get agent information
   GET    /health       # Health check
   
   # Toolset endpoint routes  
   POST   /execute      # Execute tool function
   GET    /tools        # List available tools
   GET    /schema       # Get tool schemas

Authentication
~~~~~~~~~~~~~~

Secure endpoint access:

.. code-block:: python

   from pantheon.endpoint import EndpointAuth
   
   # Token-based authentication
   auth = EndpointAuth(
       type="bearer",
       token="your-secret-token"
   )
   
   agent.start_service(auth=auth)
   
   # API key authentication
   auth = EndpointAuth(
       type="api_key",
       key="your-api-key",
       header_name="X-API-Key"
   )

Creating Custom Endpoints
-------------------------

Basic Endpoint
~~~~~~~~~~~~~~

Create a simple endpoint:

.. code-block:: python

   from fastapi import FastAPI
   from pantheon.endpoint import create_endpoint
   
   app = FastAPI()
   
   # Create endpoint for your service
   endpoint = create_endpoint(
       service=my_service,
       prefix="/api/v1"
   )
   
   # Mount to FastAPI app
   app.mount("/", endpoint)

Advanced Endpoint
~~~~~~~~~~~~~~~~~

Endpoint with middleware and custom logic:

.. code-block:: python

   from pantheon.endpoint import Endpoint
   
   class CustomEndpoint(Endpoint):
       def __init__(self, service):
           super().__init__(service)
           self.request_count = 0
           
       async def middleware(self, request, call_next):
           # Rate limiting
           self.request_count += 1
           if self.request_count > 100:
               return JSONResponse(
                   status_code=429,
                   content={"error": "Rate limit exceeded"}
               )
           
           # Process request
           response = await call_next(request)
           
           # Add custom headers
           response.headers["X-Request-Count"] = str(self.request_count)
           
           return response

WebSocket Endpoint
~~~~~~~~~~~~~~~~~~

Real-time communication endpoint:

.. code-block:: python

   from pantheon.endpoint import WebSocketEndpoint
   
   class StreamingEndpoint(WebSocketEndpoint):
       async def handle_connection(self, websocket):
           await websocket.accept()
           
           try:
               while True:
                   # Receive message
                   data = await websocket.receive_json()
                   
                   # Process with streaming
                   async for chunk in self.service.process_stream(data):
                       await websocket.send_json({
                           "type": "chunk",
                           "data": chunk
                       })
                   
                   # Send completion
                   await websocket.send_json({
                       "type": "complete"
                   })
                   
           except WebSocketDisconnect:
               pass

Endpoint Management
-------------------

Service Discovery
~~~~~~~~~~~~~~~~~

Automatic endpoint discovery:

.. code-block:: python

   from pantheon.endpoint import ServiceRegistry
   
   # Register service
   registry = ServiceRegistry("consul://localhost:8500")
   
   await registry.register(
       name="expert-agent",
       endpoint="http://10.0.0.5:8000",
       tags=["agent", "gpt-4", "expert"],
       health_check_url="/health"
   )
   
   # Discover services
   agents = await registry.discover("agent")
   expert_agents = await registry.discover(
       service_type="agent",
       tags=["expert"]
   )

Load Balancing
~~~~~~~~~~~~~~

Distribute requests across endpoints:

.. code-block:: python

   from pantheon.endpoint import LoadBalancer
   
   # Create load balancer
   balancer = LoadBalancer(
       endpoints=[
           "http://agent1:8000",
           "http://agent2:8000",
           "http://agent3:8000"
       ],
       strategy="round_robin"  # or "least_connections", "random"
   )
   
   # Use with remote agent
   remote_agent = RemoteAgent(balancer)

Health Monitoring
~~~~~~~~~~~~~~~~~

Monitor endpoint health:

.. code-block:: python

   from pantheon.endpoint import HealthMonitor
   
   monitor = HealthMonitor(
       check_interval=30,  # seconds
       timeout=5,
       failure_threshold=3
   )
   
   # Add endpoints to monitor
   monitor.add_endpoint(
       "http://agent1:8000",
       health_path="/health"
   )
   
   # Get healthy endpoints
   healthy = await monitor.get_healthy_endpoints()

Deployment Patterns
-------------------

Microservices Architecture
~~~~~~~~~~~~~~~~~~~~~~~~~~

Deploy each component as a separate service:

.. code-block:: yaml

   # docker-compose.yml
   version: '3.8'
   
   services:
     research-agent:
       image: pantheon-agent
       environment:
         AGENT_NAME: researcher
         MODEL: gpt-4o
       ports:
         - "8001:8000"
     
     python-tools:
       image: pantheon-toolset
       environment:
         TOOLSET: python_interpreter
       ports:
         - "8002:8000"
     
     chatroom:
       image: pantheon-chatroom
       environment:
         AGENTS: http://research-agent:8000
         TOOLSETS: http://python-tools:8000
       ports:
         - "8080:8000"

Kubernetes Deployment
~~~~~~~~~~~~~~~~~~~~~

Scale endpoints with Kubernetes:

.. code-block:: yaml

   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: agent-deployment
   spec:
     replicas: 3
     selector:
       matchLabels:
         app: pantheon-agent
     template:
       metadata:
         labels:
           app: pantheon-agent
       spec:
         containers:
         - name: agent
           image: pantheon/agent:latest
           ports:
           - containerPort: 8000
           env:
           - name: AGENT_CONFIG
             valueFrom:
               configMapKeyRef:
                 name: agent-config
                 key: config.yaml

Serverless Endpoints
~~~~~~~~~~~~~~~~~~~~

Deploy as serverless functions:

.. code-block:: python

   # AWS Lambda handler
   from pantheon.endpoint import serverless_handler
   from pantheon.agent import Agent
   
   agent = Agent(
       name="serverless_agent",
       instructions="Process requests efficiently."
   )
   
   # Lambda handler
   handler = serverless_handler(agent)

Best Practices
--------------

1. **Security**: Always use authentication for production endpoints
2. **Monitoring**: Implement comprehensive health checks and logging
3. **Versioning**: Version your endpoints (e.g., /api/v1/)
4. **Documentation**: Provide OpenAPI/Swagger documentation
5. **Error Handling**: Return consistent error responses
6. **Rate Limiting**: Protect endpoints from abuse

Performance Optimization
------------------------

Connection Pooling
~~~~~~~~~~~~~~~~~~

Reuse connections for efficiency:

.. code-block:: python

   from pantheon.endpoint import ConnectionPool
   
   pool = ConnectionPool(
       max_connections=100,
       max_idle_time=300,
       retry_attempts=3
   )
   
   remote_agent = RemoteAgent(endpoint, connection_pool=pool)

Caching
~~~~~~~

Cache responses for common requests:

.. code-block:: python

   from pantheon.endpoint import CachedEndpoint
   
   endpoint = CachedEndpoint(
       service=agent,
       cache_ttl=300,  # 5 minutes
       cache_size=1000
   )

Compression
~~~~~~~~~~~

Compress large responses:

.. code-block:: python

   from pantheon.endpoint import CompressionMiddleware
   
   endpoint.add_middleware(
       CompressionMiddleware(
           min_size=1000,  # Compress if > 1KB
           level=6
       )
   )