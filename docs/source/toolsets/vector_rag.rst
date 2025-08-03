Vector RAG
==========

The Vector RAG (Retrieval-Augmented Generation) toolset provides agents with semantic search capabilities using vector embeddings, enabling intelligent information retrieval from large document collections.

Overview
--------

Key features:
- **Vector Embeddings**: Convert text to semantic vectors
- **Similarity Search**: Find relevant content by meaning
- **Document Storage**: Efficient storage of embeddings
- **Hybrid Search**: Combine vector and keyword search
- **Incremental Updates**: Add documents dynamically

Basic Usage
-----------

Setting Up Vector Store
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from magique.ai.tools.rag import VectorRAGToolSet
   from pantheon.agent import Agent
   
   # Initialize vector store
   vector_tools = VectorRAGToolSet(
       name="knowledge_base",
       embedding_model="text-embedding-3-small",
       vector_db="chromadb",  # or "pinecone", "weaviate"
       dimension=1536
   )
   
   # Create RAG-enabled agent
   rag_agent = Agent(
       name="knowledge_assistant",
       instructions="Answer questions using the vector knowledge base.",
       model="gpt-4o"
   )
   await rag_agent.remote_toolset(vector_tools.service_id)

Adding Documents
~~~~~~~~~~~~~~~~

.. code-block:: python

   # Add documents to vector store
   response = await rag_agent.run([{
       "role": "user",
       "content": "Index these documents about machine learning into the knowledge base"
   }])
   
   # Agent will:
   # 1. Process documents
   # 2. Generate embeddings
   # 3. Store in vector database
   # 4. Create metadata indices

Semantic Search
~~~~~~~~~~~~~~~

.. code-block:: python

   # Search by meaning
   response = await rag_agent.run([{
       "role": "user",
       "content": "Find information about neural network architectures"
   }])
   
   # Agent performs:
   # 1. Embed query
   # 2. Vector similarity search
   # 3. Retrieve relevant chunks
   # 4. Generate answer with citations

Advanced Features
-----------------

Document Processing
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from magique.ai.tools.rag import DocumentProcessor
   
   # Configure document processing
   processor = DocumentProcessor(
       chunk_size=500,
       chunk_overlap=50,
       separators=["\n\n", "\n", ". ", " "],
       metadata_extractor=extract_metadata
   )
   
   doc_agent = Agent(
       name="document_processor",
       instructions="""Process documents intelligently:
       1. Extract text from various formats
       2. Split into semantic chunks
       3. Preserve context and metadata
       4. Generate summaries"""
   )

Hybrid Search
~~~~~~~~~~~~~

.. code-block:: python

   hybrid_search = VectorRAGToolSet(
       name="hybrid_kb",
       embedding_model="text-embedding-3-small",
       enable_keyword_search=True,
       keyword_weight=0.3,
       vector_weight=0.7
   )
   
   search_agent = Agent(
       name="hybrid_searcher",
       instructions="""Search using both semantic and keyword matching:
       1. Vector search for concepts
       2. Keyword search for specific terms
       3. Combine and rank results
       4. Return with confidence scores"""
   )

Multi-Modal RAG
~~~~~~~~~~~~~~~

.. code-block:: python

   multimodal_rag = VectorRAGToolSet(
       name="multimodal_kb",
       embedding_model="clip",  # For text and images
       supported_types=["text", "image", "pdf"]
   )
   
   visual_agent = Agent(
       name="visual_assistant",
       instructions="Search and retrieve both text and images."
   )

Common Patterns
---------------

Knowledge Base Q&A
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   qa_system = Agent(
       name="qa_bot",
       instructions="""Answer questions using the knowledge base:
       1. Search for relevant information
       2. Synthesize multiple sources
       3. Provide accurate answers
       4. Include source citations"""
   )
   
   # Example workflow
   await qa_system.run([{
       "role": "user",
       "content": "What are the main benefits of transformer models?"
   }])
   
   # Agent response includes:
   # - Direct answer
   # - Supporting evidence
   # - Source documents
   # - Confidence score

Document Analysis
~~~~~~~~~~~~~~~~~

.. code-block:: python

   analyst = Agent(
       name="doc_analyst",
       instructions="""Analyze document collections:
       1. Identify main themes
       2. Extract key insights
       3. Find connections
       4. Generate summaries"""
   )
   
   # Analyze corpus
   response = await analyst.run([{
       "role": "user",
       "content": "Analyze all research papers and identify emerging trends"
   }])

Conversational Memory
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   memory_agent = Agent(
       name="memory_assistant",
       instructions="""Use vector store for long-term memory:
       1. Store conversation history
       2. Retrieve relevant past interactions
       3. Maintain context over time
       4. Learn from conversations"""
   )
   
   # Store conversation
   await memory_agent.store_interaction(
       user_input="Tell me about quantum computing",
       assistant_response="Quantum computing uses quantum bits...",
       metadata={"topic": "quantum", "timestamp": datetime.now()}
   )

Vector Store Management
-----------------------

Index Operations
~~~~~~~~~~~~~~~~

.. code-block:: python

   class VectorIndexManager:
       async def create_index(self, name: str, config: dict):
           """Create new vector index."""
           index = await self.vector_db.create_index(
               name=name,
               dimension=config['dimension'],
               metric=config.get('metric', 'cosine'),
               index_type=config.get('type', 'hnsw')
           )
           return index
       
       async def optimize_index(self, index_name: str):
           """Optimize index for better performance."""
           await self.vector_db.optimize(
               index_name,
               num_clusters=32,
               compression=True
           )

Metadata Filtering
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   filtered_search = Agent(
       name="filtered_searcher",
       instructions="Search with metadata filters."
   )
   
   # Search with filters
   results = await filtered_search.search(
       query="machine learning applications",
       filters={
           "date": {"$gte": "2023-01-01"},
           "category": "research",
           "author": {"$in": ["Smith", "Jones"]}
       },
       top_k=10
   )

Batch Operations
~~~~~~~~~~~~~~~~

.. code-block:: python

   batch_processor = Agent(
       name="batch_rag",
       instructions="Process documents in batches."
   )
   
   async def batch_index(self, documents: List[dict], batch_size: int = 100):
       """Index documents in batches."""
       for i in range(0, len(documents), batch_size):
           batch = documents[i:i+batch_size]
           
           # Generate embeddings
           embeddings = await self.embed_batch(batch)
           
           # Store in vector DB
           await self.vector_db.insert_batch(
               embeddings=embeddings,
               documents=batch,
               ids=[doc['id'] for doc in batch]
           )

Advanced Techniques
-------------------

Reranking
~~~~~~~~~

.. code-block:: python

   from magique.ai.tools.rag import Reranker
   
   reranker = Reranker(
       model="cross-encoder/ms-marco-MiniLM-L-12-v2"
   )
   
   advanced_search = Agent(
       name="advanced_searcher",
       instructions="""Search with reranking:
       1. Initial vector search (top 50)
       2. Rerank with cross-encoder
       3. Return top 10 most relevant"""
   )
   
   # Two-stage retrieval
   initial_results = await vector_search(query, top_k=50)
   reranked = await reranker.rerank(query, initial_results)
   final_results = reranked[:10]

Query Expansion
~~~~~~~~~~~~~~~

.. code-block:: python

   query_expander = Agent(
       name="query_expander",
       instructions="""Expand queries for better retrieval:
       1. Generate synonyms
       2. Add related terms
       3. Create variations
       4. Search with all versions"""
   )
   
   # Expand query
   original = "neural network optimization"
   expanded = [
       original,
       "deep learning optimization",
       "neural net training",
       "gradient descent methods"
   ]

Incremental Learning
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   learning_agent = Agent(
       name="incremental_learner",
       instructions="""Learn from user interactions:
       1. Track successful retrievals
       2. Update embeddings
       3. Improve ranking
       4. Adapt to user preferences"""
   )
   
   async def learn_from_feedback(self, query, selected_doc, feedback):
       """Update model based on user feedback."""
       if feedback == "helpful":
           # Strengthen association
           await self.update_embedding_weight(
               query_embedding,
               doc_embedding,
               boost_factor=1.1
           )

Performance Optimization
------------------------

Embedding Cache
~~~~~~~~~~~~~~~

.. code-block:: python

   class CachedEmbedder:
       def __init__(self, embedding_model):
           self.model = embedding_model
           self.cache = {}
           
       async def embed(self, text: str):
           """Embed text with caching."""
           cache_key = hashlib.md5(text.encode()).hexdigest()
           
           if cache_key in self.cache:
               return self.cache[cache_key]
           
           embedding = await self.model.embed(text)
           self.cache[cache_key] = embedding
           return embedding

Approximate Search
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Configure approximate nearest neighbor search
   ann_config = {
       "index_type": "ivf",
       "nlist": 100,
       "nprobe": 10,
       "quantization": "pq"
   }
   
   fast_search = VectorRAGToolSet(
       name="fast_kb",
       ann_config=ann_config,
       exact_search_threshold=100  # Use exact search for small result sets
   )

Best Practices
--------------

1. **Chunk Size**: Choose appropriate chunk sizes for your domain
2. **Embedding Model**: Select model based on performance/quality needs
3. **Metadata**: Store rich metadata for filtering
4. **Updates**: Implement incremental updates vs full reindex
5. **Monitoring**: Track search quality metrics
6. **Backup**: Regular backups of vector stores

Integration Examples
--------------------

With Web Search
~~~~~~~~~~~~~~~

.. code-block:: python

   # Augment KB with web search
   augmented_agent = Agent(
       name="augmented_assistant",
       instructions="""Answer using KB and web:
       1. Search vector store first
       2. If insufficient, search web
       3. Add new info to KB
       4. Provide comprehensive answer""",
       tools=[vector_search, web_search]
   )

With Document Processing
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Process and index documents
   indexer = Agent(
       name="doc_indexer",
       instructions="Process documents and build searchable KB.",
       tools=[read_file, extract_text, vector_index]
   )