Architecture
============

This document provides a detailed overview of Pantheon's service architecture, focusing on Endpoints and ChatRooms that enable distributed, scalable multi-agent systems.

System Architecture
-------------------

High-Level Overview
~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    ┌────────────────────────────────────────────────────────────┐
    │                        Clients                             │
    │  (Web UI, Mobile Apps, API Consumers, CLI Tools)          │
    └────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
    ┌────────────────────────────────────────────────────────────┐
    │                    API Gateway Layer                       │
    │  (Authentication, Rate Limiting, Routing, Load Balancing) │
    └────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
    ┌──────────────────────────┐   ┌──────────────────────────┐
    │   ChatRoom Services      │   │   Agent Endpoints        │
    │  (Session Management)     │   │  (Individual Agents)     │
    └──────────────────────────┘   └──────────────────────────┘
                    │                           │
                    └─────────────┬─────────────┘
                                  ▼
    ┌────────────────────────────────────────────────────────────┐
    │                    Toolset Services                        │
    │  (Python, R, Shell, Web, RAG, File Operations)            │
    └────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
    ┌────────────────────────────────────────────────────────────┐
    │                    Data Layer                              │
    │  (Databases, Vector Stores, File Storage, Cache)          │
    └────────────────────────────────────────────────────────────┘

Component Details
-----------------

Endpoint Architecture
~~~~~~~~~~~~~~~~~~~~~

**Core Components:**

1. **Service Registry**
   
   .. code-block:: python
   
      class ServiceRegistry:
          """Central registry for all services."""
          
          async def register(self, service_id: str, endpoint: str, metadata: dict):
              """Register a service endpoint."""
              await self.store.set(service_id, {
                  "endpoint": endpoint,
                  "metadata": metadata,
                  "health_check": f"{endpoint}/health",
                  "registered_at": datetime.now()
              })
          
          async def discover(self, service_type: str, tags: List[str] = None):
              """Discover services by type and tags."""
              services = await self.store.query(
                  type=service_type,
                  tags=tags,
                  status="healthy"
              )
              return services

2. **Load Balancer**
   
   .. code-block:: python
   
      class LoadBalancer:
          """Distribute requests across service instances."""
          
          def __init__(self, strategy="round_robin"):
              self.strategy = strategy
              self.instances = []
              self.current = 0
          
          async def get_instance(self):
              """Get next available instance."""
              if self.strategy == "round_robin":
                  instance = self.instances[self.current]
                  self.current = (self.current + 1) % len(self.instances)
                  return instance
              elif self.strategy == "least_connections":
                  return min(self.instances, key=lambda x: x.active_connections)

3. **Health Monitor**
   
   .. code-block:: python
   
      class HealthMonitor:
          """Monitor service health."""
          
          async def check_health(self, endpoint: str):
              """Perform health check."""
              try:
                  response = await self.http_client.get(f"{endpoint}/health")
                  return response.status == 200
              except:
                  return False
          
          async def monitor_loop(self):
              """Continuous health monitoring."""
              while True:
                  for service in self.services:
                      health = await self.check_health(service.endpoint)
                      if not health:
                          await self.handle_unhealthy(service)
                  await asyncio.sleep(30)

ChatRoom Architecture
~~~~~~~~~~~~~~~~~~~~~

**Core Components:**

1. **Session Manager**
   
   .. code-block:: python
   
      class SessionManager:
          """Manage user sessions."""
          
          def __init__(self):
              self.sessions = {}
              self.session_timeout = 3600  # 1 hour
          
          async def create_session(self, user_id: str, metadata: dict):
              """Create new session."""
              session = {
                  "id": generate_session_id(),
                  "user_id": user_id,
                  "created_at": datetime.now(),
                  "last_activity": datetime.now(),
                  "metadata": metadata,
                  "conversation": []
              }
              self.sessions[session["id"]] = session
              return session
          
          async def update_activity(self, session_id: str):
              """Update session activity timestamp."""
              if session_id in self.sessions:
                  self.sessions[session_id]["last_activity"] = datetime.now()

2. **Message Router**
   
   .. code-block:: python
   
      class MessageRouter:
          """Route messages to appropriate handlers."""
          
          def __init__(self, agents: List[Agent]):
              self.agents = agents
              self.handlers = {
                  "message": self.handle_message,
                  "command": self.handle_command,
                  "feedback": self.handle_feedback
              }
          
          async def route(self, message: dict, session: dict):
              """Route message based on type."""
              msg_type = message.get("type", "message")
              handler = self.handlers.get(msg_type)
              
              if handler:
                  return await handler(message, session)
              else:
                  raise ValueError(f"Unknown message type: {msg_type}")

3. **Stream Manager**
   
   .. code-block:: python
   
      class StreamManager:
          """Handle streaming responses."""
          
          def __init__(self):
              self.active_streams = {}
          
          async def stream_response(self, session_id: str, response_generator):
              """Stream response to client."""
              stream_id = generate_stream_id()
              self.active_streams[stream_id] = True
              
              try:
                  async for chunk in response_generator:
                      if not self.active_streams.get(stream_id):
                          break  # Stream cancelled
                      
                      await self.send_chunk(session_id, chunk)
                      
                  await self.send_complete(session_id)
              finally:
                  del self.active_streams[stream_id]

Communication Protocols
-----------------------

REST API
~~~~~~~~

**Endpoint Structure:**

.. code-block:: text

    /api/v1/
    ├── agents/
    │   ├── {agent_id}/run        # POST - Run agent
    │   ├── {agent_id}/stream     # POST - Stream response
    │   └── {agent_id}/info       # GET  - Agent information
    ├── chatrooms/
    │   ├── create                # POST - Create chatroom
    │   ├── {room_id}/join        # POST - Join chatroom
    │   ├── {room_id}/message     # POST - Send message
    │   └── {room_id}/history     # GET  - Get history
    └── health                    # GET  - Service health

**Request/Response Format:**

.. code-block:: python

   # Request
   {
       "version": "1.0",
       "id": "request-123",
       "method": "agent.run",
       "params": {
           "messages": [
               {"role": "user", "content": "Hello"}
           ],
           "context": {}
       }
   }
   
   # Response
   {
       "version": "1.0",
       "id": "request-123",
       "result": {
           "messages": [
               {"role": "assistant", "content": "Hello! How can I help?"}
           ],
           "metadata": {}
       }
   }

WebSocket Protocol
~~~~~~~~~~~~~~~~~~

**Connection Flow:**

.. code-block:: python

   # Client connects
   ws = WebSocket("wss://server/ws")
   
   # Authentication
   ws.send({
       "type": "auth",
       "token": "bearer-token"
   })
   
   # Join session
   ws.send({
       "type": "join",
       "session_id": "session-123"
   })
   
   # Send message
   ws.send({
       "type": "message",
       "content": "Hello"
   })
   
   # Receive streaming response
   while True:
       msg = ws.receive()
       if msg["type"] == "chunk":
           print(msg["content"], end="")
       elif msg["type"] == "complete":
           break

Security Architecture
---------------------

Authentication
~~~~~~~~~~~~~~

**Multi-Layer Authentication:**

1. **API Gateway Level**
   - API key validation
   - Rate limiting by key
   - IP whitelisting

2. **Service Level**
   - JWT token validation
   - Role-based access control
   - Session management

3. **Resource Level**
   - Fine-grained permissions
   - Data isolation
   - Audit logging

.. code-block:: python

   class SecurityMiddleware:
       async def authenticate(self, request):
           """Multi-factor authentication."""
           # Check API key
           api_key = request.headers.get("X-API-Key")
           if not self.validate_api_key(api_key):
               raise AuthError("Invalid API key")
           
           # Validate JWT token
           token = request.headers.get("Authorization")
           if token:
               user = self.validate_jwt(token)
               request.user = user
           
           # Check permissions
           if not self.check_permissions(request):
               raise AuthError("Insufficient permissions")

Authorization
~~~~~~~~~~~~~

**Role-Based Access Control:**

.. code-block:: python

   class RBAC:
       roles = {
           "admin": ["*"],  # All permissions
           "user": ["chat.send", "chat.read", "agent.run"],
           "viewer": ["chat.read"]
       }
       
       def check_permission(self, user_role: str, action: str) -> bool:
           """Check if role has permission for action."""
           permissions = self.roles.get(user_role, [])
           return "*" in permissions or action in permissions

Scalability Patterns
--------------------

Horizontal Scaling
~~~~~~~~~~~~~~~~~~

**Service Scaling:**

.. code-block:: yaml

   # Kubernetes HPA
   apiVersion: autoscaling/v2
   kind: HorizontalPodAutoscaler
   metadata:
     name: chatroom-hpa
   spec:
     scaleTargetRef:
       apiVersion: apps/v1
       kind: Deployment
       name: chatroom
     minReplicas: 2
     maxReplicas: 10
     metrics:
     - type: Resource
       resource:
         name: cpu
         target:
           type: Utilization
           averageUtilization: 70

Caching Strategy
~~~~~~~~~~~~~~~~

**Multi-Level Cache:**

.. code-block:: python

   class CacheStrategy:
       def __init__(self):
           self.l1_cache = {}  # In-memory
           self.l2_cache = Redis()  # Distributed
           self.l3_cache = CDN()  # Edge cache
       
       async def get(self, key: str):
           """Get from cache hierarchy."""
           # L1 - Memory
           if key in self.l1_cache:
               return self.l1_cache[key]
           
           # L2 - Redis
           value = await self.l2_cache.get(key)
           if value:
               self.l1_cache[key] = value
               return value
           
           # L3 - CDN
           value = await self.l3_cache.get(key)
           if value:
               await self.warm_caches(key, value)
               return value

Monitoring and Observability
----------------------------

Metrics Collection
~~~~~~~~~~~~~~~~~~

**Key Metrics:**

- Request rate and latency
- Error rates and types
- Resource utilization
- Active sessions and connections
- Cache hit rates

.. code-block:: python

   class MetricsCollector:
       def __init__(self):
           self.prometheus = PrometheusClient()
       
       async def record_request(self, endpoint: str, duration: float, status: int):
           """Record request metrics."""
           self.prometheus.histogram(
               "http_request_duration_seconds",
               duration,
               labels={"endpoint": endpoint, "status": status}
           )
           
           self.prometheus.increment(
               "http_requests_total",
               labels={"endpoint": endpoint, "status": status}
           )

Distributed Tracing
~~~~~~~~~~~~~~~~~~~

**Request Tracing:**

.. code-block:: python

   from opentelemetry import trace
   
   tracer = trace.get_tracer(__name__)
   
   async def traced_endpoint(request):
       """Endpoint with distributed tracing."""
       with tracer.start_as_current_span("handle_request") as span:
           span.set_attribute("request.id", request.id)
           span.set_attribute("user.id", request.user_id)
           
           # Process request
           with tracer.start_span("process_logic"):
               result = await process(request)
           
           # Call downstream service
           with tracer.start_span("call_agent"):
               agent_result = await call_agent(result)
           
           return agent_result

Best Practices
--------------

1. **Service Design**
   - Single responsibility principle
   - Stateless services where possible
   - Clear API contracts
   - Version management

2. **Reliability**
   - Circuit breakers for external calls
   - Retry with exponential backoff
   - Graceful degradation
   - Comprehensive error handling

3. **Performance**
   - Connection pooling
   - Request batching
   - Async operations
   - Efficient serialization

4. **Security**
   - Defense in depth
   - Principle of least privilege
   - Regular security audits
   - Encryption at rest and in transit