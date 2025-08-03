ChatRoom
========

ChatRoom is an interactive service that provides a user-friendly interface for conversations with agents and teams. It manages sessions, handles real-time communication, and integrates with web UIs.

What is a ChatRoom?
-------------------

A ChatRoom is a service layer that:

- **Hosts Conversations**: Manages interactive sessions with agents
- **Provides Interface**: Offers web UI and API access
- **Manages State**: Maintains conversation history and context
- **Handles Concurrency**: Supports multiple simultaneous users
- **Enables Persistence**: Saves and restores chat sessions

Core Features
-------------

Session Management
~~~~~~~~~~~~~~~~~~

ChatRooms manage user sessions automatically:

.. code-block:: python

   from pantheon.chatroom import ChatRoom
   from pantheon.agent import Agent
   
   # Create ChatRoom with an agent
   agent = Agent(
       name="assistant",
       instructions="You are a helpful assistant."
   )
   
   chatroom = ChatRoom(
       name="Support ChatRoom",
       agents=[agent],
       max_sessions=100,
       session_timeout=3600  # 1 hour
   )
   
   # Start the service
   await chatroom.start(port=8000)

Web UI Integration
~~~~~~~~~~~~~~~~~~

Connect to Pantheon's web interface:

.. code-block:: bash

   # Start ChatRoom
   python -m pantheon.chatroom
   
   # Output shows:
   # ChatRoom started with ID: abc123...
   # Connect at: https://pantheon-ui.vercel.app/
   
   # Users can then:
   # 1. Visit the web UI
   # 2. Enter the ChatRoom ID
   # 3. Start chatting

Real-time Communication
~~~~~~~~~~~~~~~~~~~~~~~

Stream responses as they're generated:

.. code-block:: python

   # ChatRoom automatically handles streaming
   chatroom = ChatRoom(
       agents=[agent],
       stream_responses=True,  # Default
       chunk_size=20  # Characters per chunk
   )

Creating ChatRooms
------------------

Basic ChatRoom
~~~~~~~~~~~~~~

Simple ChatRoom with a single agent:

.. code-block:: python

   import asyncio
   from pantheon.chatroom import ChatRoom
   from pantheon.agent import Agent
   
   async def main():
       # Create agent
       agent = Agent(
           name="helper",
           instructions="You are a helpful AI assistant.",
           model="gpt-4o-mini"
       )
       
       # Create and start ChatRoom
       chatroom = ChatRoom(agents=[agent])
       await chatroom.start()
       
       # Keep running
       await asyncio.Event().wait()
   
   if __name__ == "__main__":
       asyncio.run(main())

Team ChatRoom
~~~~~~~~~~~~~

ChatRoom with a team of agents:

.. code-block:: python

   from pantheon.team import SequentialTeam
   
   # Create specialized agents
   researcher = Agent(
       name="researcher",
       instructions="Research and gather information."
   )
   
   writer = Agent(
       name="writer",
       instructions="Write clear, engaging content."
   )
   
   editor = Agent(
       name="editor",
       instructions="Edit and improve text."
   )
   
   # Create team
   team = SequentialTeam([researcher, writer, editor])
   
   # Create ChatRoom with team
   chatroom = ChatRoom(
       name="Content Creation ChatRoom",
       team=team,
       description="Create high-quality content"
   )

Configuration-based ChatRoom
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create from YAML configuration:

.. code-block:: yaml

   # chatroom_config.yaml
   name: "Customer Support ChatRoom"
   description: "24/7 AI customer support"
   
   agents:
     - name: "greeter"
       instructions: "Greet customers warmly and understand their needs."
       model: "gpt-4o-mini"
       
     - name: "technical_support"
       instructions: "Provide technical assistance and troubleshooting."
       model: "gpt-4o"
       tools:
         - "search_knowledge_base"
         - "create_ticket"
         
     - name: "escalation"
       instructions: "Handle complex issues and escalations."
       model: "gpt-4o"
   
   team:
     type: "swarm"
     transfer_functions: true
   
   settings:
     welcome_message: "Welcome! How can I help you today?"
     session_timeout: 1800
     max_message_length: 1000

.. code-block:: python

   # Load from configuration
   chatroom = ChatRoom.from_config("chatroom_config.yaml")
   await chatroom.start()

Advanced Features
-----------------

Multi-user Support
~~~~~~~~~~~~~~~~~~

Handle multiple concurrent users:

.. code-block:: python

   chatroom = ChatRoom(
       agents=[agent],
       multi_user=True,
       user_isolation=True,  # Separate context per user
       max_users_per_session=5  # For collaborative sessions
   )
   
   # Track user activity
   @chatroom.on_user_join
   async def handle_user_join(user_id, session_id):
       print(f"User {user_id} joined session {session_id}")
   
   @chatroom.on_user_leave
   async def handle_user_leave(user_id, session_id):
       print(f"User {user_id} left session {session_id}")

Message Preprocessing
~~~~~~~~~~~~~~~~~~~~~

Process messages before sending to agents:

.. code-block:: python

   from pantheon.chatroom import MessageProcessor
   
   class ModerationProcessor(MessageProcessor):
       async def process(self, message, context):
           # Check for inappropriate content
           if await self.is_inappropriate(message["content"]):
               return {
                   "role": "system",
                   "content": "Please keep the conversation appropriate."
               }
           
           # Check message length
           if len(message["content"]) > 1000:
               message["content"] = message["content"][:1000] + "..."
           
           return message
   
   chatroom = ChatRoom(
       agents=[agent],
       message_processors=[ModerationProcessor()]
   )

Conversation Persistence
~~~~~~~~~~~~~~~~~~~~~~~~

Save and restore conversations:

.. code-block:: python

   from pantheon.chatroom import ConversationStore
   
   # File-based storage
   store = ConversationStore("./conversations")
   
   chatroom = ChatRoom(
       agents=[agent],
       conversation_store=store,
       auto_save=True,
       save_interval=60  # Save every minute
   )
   
   # Load previous conversation
   await chatroom.load_conversation(conversation_id)

Custom Responses
~~~~~~~~~~~~~~~~

Add custom response handling:

.. code-block:: python

   @chatroom.custom_handler("help")
   async def handle_help(message, context):
       return {
           "content": "Here are the available commands:\n"
                     "/help - Show this message\n"
                     "/reset - Reset conversation\n"
                     "/status - Show system status",
           "metadata": {"type": "system_message"}
       }
   
   @chatroom.custom_handler("status")
   async def handle_status(message, context):
       return {
           "content": f"System Status: Active\n"
                     f"Active Sessions: {chatroom.active_sessions}\n"
                     f"Uptime: {chatroom.uptime}",
           "metadata": {"type": "status"}
       }

ChatRoom Management
-------------------

Monitoring
~~~~~~~~~~

Track ChatRoom metrics:

.. code-block:: python

   from pantheon.chatroom import ChatRoomMonitor
   
   monitor = ChatRoomMonitor(chatroom)
   
   # Get metrics
   metrics = await monitor.get_metrics()
   print(f"Total messages: {metrics['total_messages']}")
   print(f"Active users: {metrics['active_users']}")
   print(f"Avg response time: {metrics['avg_response_time']}s")
   
   # Set up alerts
   @monitor.alert_on("high_latency", threshold=5.0)
   async def handle_high_latency(latency):
       print(f"Warning: High latency detected: {latency}s")

Access Control
~~~~~~~~~~~~~~

Implement authentication and authorization:

.. code-block:: python

   from pantheon.chatroom import AccessControl
   
   class TokenAccessControl(AccessControl):
       def __init__(self, valid_tokens):
           self.valid_tokens = valid_tokens
           
       async def authenticate(self, request):
           token = request.headers.get("Authorization", "").replace("Bearer ", "")
           return token in self.valid_tokens
       
       async def authorize(self, user, action):
           # Implement authorization logic
           return True
   
   chatroom = ChatRoom(
       agents=[agent],
       access_control=TokenAccessControl(["token1", "token2"])
   )

Rate Limiting
~~~~~~~~~~~~~

Prevent abuse with rate limiting:

.. code-block:: python

   from pantheon.chatroom import RateLimiter
   
   rate_limiter = RateLimiter(
       messages_per_minute=10,
       messages_per_hour=100,
       tokens_per_minute=1000
   )
   
   chatroom = ChatRoom(
       agents=[agent],
       rate_limiter=rate_limiter
   )

Integration Options
-------------------

REST API
~~~~~~~~

ChatRooms expose REST endpoints:

.. code-block:: text

   POST   /chat              # Send message
   GET    /chat/history      # Get conversation history
   POST   /chat/reset        # Reset conversation
   GET    /sessions          # List active sessions
   GET    /health           # Health check

WebSocket API
~~~~~~~~~~~~~

Real-time communication via WebSocket:

.. code-block:: javascript

   // JavaScript client example
   const ws = new WebSocket('ws://localhost:8000/ws');
   
   ws.onopen = () => {
       // Send message
       ws.send(JSON.stringify({
           type: 'message',
           content: 'Hello!',
           session_id: 'user123'
       }));
   };
   
   ws.onmessage = (event) => {
       const response = JSON.parse(event.data);
       if (response.type === 'chunk') {
           // Streaming response chunk
           console.log(response.content);
       } else if (response.type === 'complete') {
           // Response complete
           console.log('Response finished');
       }
   };

SDK Integration
~~~~~~~~~~~~~~~

Use ChatRoom with various SDKs:

.. code-block:: python

   # Python SDK
   from pantheon.sdk import ChatRoomClient
   
   client = ChatRoomClient("http://localhost:8000")
   
   # Start conversation
   session = await client.create_session()
   
   # Send message
   response = await session.send_message("Hello!")
   
   # Stream response
   async for chunk in session.stream_message("Tell me a story"):
       print(chunk, end="")

Deployment
----------

Docker Deployment
~~~~~~~~~~~~~~~~~

.. code-block:: dockerfile

   # Dockerfile
   FROM python:3.9-slim
   
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   
   COPY . .
   
   ENV PYTHONUNBUFFERED=1
   CMD ["python", "-m", "pantheon.chatroom", "--config", "chatroom.yaml"]

Cloud Deployment
~~~~~~~~~~~~~~~~

Deploy to cloud platforms:

.. code-block:: yaml

   # kubernetes deployment
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: chatroom-deployment
   spec:
     replicas: 3
     template:
       spec:
         containers:
         - name: chatroom
           image: pantheon/chatroom:latest
           ports:
           - containerPort: 8000
           env:
           - name: OPENAI_API_KEY
             valueFrom:
               secretKeyRef:
                 name: api-keys
                 key: openai

Best Practices
--------------

1. **Session Management**: Set appropriate timeouts and limits
2. **Error Handling**: Provide graceful error messages to users
3. **Security**: Always use HTTPS in production
4. **Monitoring**: Track usage and performance metrics
5. **Backup**: Regularly backup conversation data
6. **Scaling**: Use load balancers for high traffic