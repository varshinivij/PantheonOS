Memory
======

Memory systems in Pantheon enable agents to maintain context, learn from interactions, and share knowledge. This persistence is crucial for building agents that can handle complex, multi-turn conversations and collaborative tasks.

What is Memory?
---------------

Memory in Pantheon provides:

- **Persistence**: Information survives beyond single interactions
- **Context**: Agents remember previous conversations
- **Learning**: Agents can accumulate knowledge over time
- **Sharing**: Multiple agents can access common information

Types of Memory
---------------

Conversation Memory
~~~~~~~~~~~~~~~~~~~

Stores the history of interactions within a session:

.. code-block:: python

   from pantheon.agent import Agent
   from pantheon.memory import ConversationMemory
   
   memory = ConversationMemory()
   agent = Agent(
       name="assistant",
       instructions="You are a helpful assistant.",
       memory=memory
   )
   
   # First interaction
   await agent.run([{"role": "user", "content": "My name is Alice"}])
   
   # Second interaction - agent remembers
   await agent.run([{"role": "user", "content": "What's my name?"}])
   # Response: "Your name is Alice"

Long-term Memory
~~~~~~~~~~~~~~~~

Persists information across sessions:

.. code-block:: python

   from pantheon.memory import LongTermMemory
   
   memory = LongTermMemory(storage_path="./agent_memory")
   agent = Agent(
       name="assistant",
       memory=memory
   )
   
   # Information persists even after restart
   await agent.remember("user_preferences", {
       "name": "Alice",
       "language": "English",
       "timezone": "PST"
   })

Shared Memory
~~~~~~~~~~~~~

Enables knowledge sharing between agents:

.. code-block:: python

   from pantheon.memory import SharedMemory
   
   shared_memory = SharedMemory()
   
   researcher = Agent(
       name="researcher",
       memory=shared_memory
   )
   
   writer = Agent(
       name="writer", 
       memory=shared_memory
   )
   
   # Researcher stores findings
   await researcher.remember("research_findings", findings)
   
   # Writer can access the same findings
   findings = await writer.recall("research_findings")

Vector Memory
~~~~~~~~~~~~~

Enables semantic search over stored information:

.. code-block:: python

   from pantheon.memory import VectorMemory
   
   memory = VectorMemory(
       embedding_model="text-embedding-3-small"
   )
   
   agent = Agent(
       name="knowledge_bot",
       memory=memory
   )
   
   # Store information with embeddings
   await memory.store(
       "Python is a high-level programming language.",
       metadata={"topic": "programming", "language": "python"}
   )
   
   # Semantic search
   results = await memory.search(
       "What programming languages do you know about?",
       top_k=5
   )

Memory Operations
-----------------

Storing Information
~~~~~~~~~~~~~~~~~~~

Different ways to store data in memory:

.. code-block:: python

   # Simple key-value storage
   await agent.memory.set("user_id", "12345")
   
   # Store structured data
   await agent.memory.set("session_data", {
       "start_time": datetime.now(),
       "topic": "AI discussion",
       "participants": ["Alice", "Bob"]
   })
   
   # Store with expiration
   await agent.memory.set(
       "temporary_token",
       "abc123",
       expires_in=3600  # Expires in 1 hour
   )

Retrieving Information
~~~~~~~~~~~~~~~~~~~~~~

Access stored data:

.. code-block:: python

   # Get specific value
   user_id = await agent.memory.get("user_id")
   
   # Get with default
   preference = await agent.memory.get(
       "color_preference",
       default="blue"
   )
   
   # Get multiple values
   data = await agent.memory.get_many([
       "user_id", 
       "session_data",
       "preferences"
   ])

Searching Memory
~~~~~~~~~~~~~~~~

Find relevant information:

.. code-block:: python

   # Pattern matching
   user_keys = await agent.memory.search_keys("user_*")
   
   # Semantic search (with vector memory)
   relevant_docs = await agent.memory.semantic_search(
       query="Tell me about Python",
       filters={"topic": "programming"},
       limit=10
   )
   
   # Time-based search
   recent = await agent.memory.get_recent(
       hours=24,
       pattern="conversation_*"
   )

Memory Strategies
-----------------

Contextual Memory
~~~~~~~~~~~~~~~~~

Organize memory by context:

.. code-block:: python

   class ContextualAgent(Agent):
       async def run(self, messages, context=None):
           # Create context-specific memory namespace
           context_id = context.get("session_id", "default")
           memory_namespace = f"session_{context_id}"
           
           # Store in context-specific area
           await self.memory.set(
               f"{memory_namespace}/messages",
               messages
           )
           
           # Retrieve context-specific data
           history = await self.memory.get(
               f"{memory_namespace}/history",
               default=[]
           )

Memory Summarization
~~~~~~~~~~~~~~~~~~~~

Compress old memories to save space:

.. code-block:: python

   from pantheon.memory import MemorySummarizer
   
   summarizer = MemorySummarizer(
       summary_model="gpt-4o-mini",
       chunk_size=100  # Summarize every 100 messages
   )
   
   agent = Agent(
       name="long_conversation_bot",
       memory=memory,
       memory_summarizer=summarizer
   )

Memory Hierarchies
~~~~~~~~~~~~~~~~~~

Implement multi-level memory systems:

.. code-block:: python

   from pantheon.memory import MemoryHierarchy
   
   memory = MemoryHierarchy([
       ("cache", CacheMemory(ttl=300)),      # 5-minute cache
       ("session", SessionMemory()),          # Session storage  
       ("persistent", DiskMemory())           # Long-term storage
   ])
   
   agent = Agent(name="hierarchical_bot", memory=memory)

Advanced Features
-----------------

Memory Indexing
~~~~~~~~~~~~~~~

Create indexes for faster retrieval:

.. code-block:: python

   from pantheon.memory import IndexedMemory
   
   memory = IndexedMemory()
   
   # Create indexes
   await memory.create_index("user_id")
   await memory.create_index("timestamp")
   
   # Store with indexed fields
   await memory.store({
       "user_id": "123",
       "timestamp": datetime.now(),
       "action": "login"
   })
   
   # Fast lookup by index
   user_actions = await memory.find_by_index(
       "user_id", 
       "123"
   )

Memory Policies
~~~~~~~~~~~~~~~

Define retention and eviction policies:

.. code-block:: python

   from pantheon.memory import MemoryPolicy
   
   policy = MemoryPolicy(
       max_size=1000,           # Maximum items
       max_age_days=30,         # Delete after 30 days
       eviction="lru"           # Least recently used
   )
   
   memory = LongTermMemory(policy=policy)

Memory Synchronization
~~~~~~~~~~~~~~~~~~~~~~

Sync memory across distributed agents:

.. code-block:: python

   from pantheon.memory import SynchronizedMemory
   
   memory = SynchronizedMemory(
       backend="redis://localhost:6379",
       sync_interval=60  # Sync every minute
   )
   
   # Multiple agents can share synchronized memory
   agent1 = Agent(name="agent1", memory=memory)
   agent2 = Agent(name="agent2", memory=memory)

Best Practices
--------------

1. **Namespace Organization**: Use clear namespaces to organize memory
2. **Data Expiration**: Set appropriate TTLs for temporary data
3. **Memory Limits**: Implement size limits to prevent unbounded growth
4. **Backup Strategy**: Regular backups for critical memory
5. **Privacy**: Be mindful of what personal data is stored

Common Patterns
---------------

User Preference Tracking
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   async def track_preferences(agent, user_id, preference):
       key = f"user:{user_id}:preferences"
       prefs = await agent.memory.get(key, default={})
       prefs.update(preference)
       await agent.memory.set(key, prefs)

Conversation Summarization
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   async def summarize_conversation(agent, messages):
       if len(messages) > 50:
           summary = await agent.summarize(messages[:-10])
           await agent.memory.set("conversation_summary", summary)
           return messages[-10:]  # Keep recent messages
       return messages

Knowledge Base Building
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   async def add_to_knowledge_base(agent, fact, category):
       kb_key = f"knowledge:{category}"
       facts = await agent.memory.get(kb_key, default=[])
       facts.append({
           "fact": fact,
           "timestamp": datetime.now(),
           "source": "user_provided"
       })
       await agent.memory.set(kb_key, facts)