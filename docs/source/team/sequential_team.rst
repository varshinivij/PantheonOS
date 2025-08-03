Sequential Team
===============

Sequential Teams process tasks through a series of agents in a predefined order, with each agent building upon the work of the previous one. This pattern is ideal for workflows with clear dependencies and multi-step processes.

Overview
--------

In a Sequential Team:
- Agents execute in a fixed order
- Each agent receives the output of the previous agent
- Context accumulates as it passes through the pipeline
- The final agent's output becomes the team's response

Basic Usage
-----------

Creating a Sequential Team
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pantheon.team import SequentialTeam
   from pantheon.agent import Agent
   
   # Create specialized agents
   researcher = Agent(
       name="researcher",
       instructions="Research the topic and gather relevant information."
   )
   
   analyst = Agent(
       name="analyst",
       instructions="Analyze the research and identify key insights."
   )
   
   writer = Agent(
       name="writer",
       instructions="Create a well-structured report based on the analysis."
   )
   
   # Create sequential team
   team = SequentialTeam([researcher, analyst, writer])
   
   # Run the team
   result = await team.run("Analyze the impact of AI on healthcare")

With Tools
~~~~~~~~~~

Enhance agents with specific tools:

.. code-block:: python

   from magique.ai.tools.web_browse import duckduckgo_search
   from magique.ai.tools.python import PythonInterpreterToolSet
   
   # Research agent with web search
   researcher = Agent(
       name="researcher",
       instructions="Research using web search.",
       tools=[duckduckgo_search]
   )
   
   # Analyst with Python for data analysis
   analyst = Agent(
       name="analyst",
       instructions="Analyze data using Python.",
   )
   await analyst.remote_toolset(python_toolset.service_id)
   
   # Writer with formatting tools
   writer = Agent(
       name="writer",
       instructions="Create formatted reports.",
       tools=[create_chart, format_table]
   )
   
   team = SequentialTeam([researcher, analyst, writer])

Advanced Features
-----------------

Context Accumulation
~~~~~~~~~~~~~~~~~~~~

Control how context flows through the team:

.. code-block:: python

   class CustomSequentialTeam(SequentialTeam):
       def __init__(self, agents, accumulate_context=True):
           super().__init__(agents)
           self.accumulate_context = accumulate_context
       
       async def run(self, messages, context_variables=None):
           current_messages = messages
           accumulated_context = context_variables or {}
           
           for i, agent in enumerate(self.agents):
               # Add stage info to context
               accumulated_context["stage"] = i + 1
               accumulated_context["previous_agent"] = (
                   self.agents[i-1].name if i > 0 else None
               )
               
               # Run agent
               response = await agent.run(
                   current_messages,
                   context_variables=accumulated_context
               )
               
               # Prepare for next agent
               if self.accumulate_context:
                   # Keep all messages
                   current_messages.extend(response.messages)
               else:
                   # Only pass last response
                   current_messages = response.messages
               
               # Update context
               accumulated_context.update(response.context_variables)
           
           return response

Error Handling
~~~~~~~~~~~~~~

Implement robust error recovery:

.. code-block:: python

   class ResilientSequentialTeam(SequentialTeam):
       def __init__(self, agents, max_retries=3):
           super().__init__(agents)
           self.max_retries = max_retries
       
       async def run_with_retry(self, agent, messages, context):
           for attempt in range(self.max_retries):
               try:
                   return await agent.run(messages, context)
               except Exception as e:
                   if attempt == self.max_retries - 1:
                       # Final attempt failed
                       return await self.handle_failure(
                           agent, messages, context, e
                       )
                   await asyncio.sleep(2 ** attempt)  # Exponential backoff
       
       async def handle_failure(self, agent, messages, context, error):
           # Fallback to a general agent
           fallback = Agent(
               name="fallback",
               instructions=f"Handle the error from {agent.name}: {error}"
           )
           return await fallback.run(messages, context)

Progress Tracking
~~~~~~~~~~~~~~~~~

Monitor team progress:

.. code-block:: python

   class ProgressTrackingTeam(SequentialTeam):
       def __init__(self, agents, progress_callback=None):
           super().__init__(agents)
           self.progress_callback = progress_callback
       
       async def run(self, messages):
           total_agents = len(self.agents)
           
           for i, agent in enumerate(self.agents):
               # Notify progress
               if self.progress_callback:
                   await self.progress_callback({
                       "current_agent": agent.name,
                       "stage": i + 1,
                       "total_stages": total_agents,
                       "percentage": (i / total_agents) * 100
                   })
               
               # Run agent
               response = await agent.run(messages)
               messages = response.messages
           
           # Notify completion
           if self.progress_callback:
               await self.progress_callback({
                   "status": "completed",
                   "percentage": 100
               })
           
           return response
   
   # Usage
   async def on_progress(status):
       print(f"Progress: {status['percentage']:.0f}% - {status.get('current_agent', 'Done')}")
   
   team = ProgressTrackingTeam(agents, on_progress)

Common Patterns
---------------

Research and Analysis Pipeline
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # 1. Data Gatherer
   gatherer = Agent(
       name="data_gatherer",
       instructions="Collect relevant data from multiple sources.",
       tools=[web_search, read_file, query_database]
   )
   
   # 2. Data Processor
   processor = Agent(
       name="processor",
       instructions="Clean and prepare data for analysis.",
       tools=[python_interpreter]
   )
   
   # 3. Analyst
   analyst = Agent(
       name="analyst",
       instructions="Perform statistical analysis and identify patterns.",
       tools=[python_interpreter, create_visualization]
   )
   
   # 4. Report Generator
   reporter = Agent(
       name="reporter",
       instructions="Create comprehensive report with visualizations.",
       tools=[format_document, create_chart]
   )
   
   research_pipeline = SequentialTeam([
       gatherer, processor, analyst, reporter
   ])

Content Creation Pipeline
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # 1. Ideation
   ideator = Agent(
       name="ideator",
       instructions="Generate creative ideas and outlines."
   )
   
   # 2. Researcher
   researcher = Agent(
       name="researcher",
       instructions="Research facts and gather supporting information.",
       tools=[web_search, fact_checker]
   )
   
   # 3. Writer
   writer = Agent(
       name="writer",
       instructions="Write engaging content based on outline and research."
   )
   
   # 4. Editor
   editor = Agent(
       name="editor",
       instructions="Edit for clarity, grammar, and style."
   )
   
   # 5. SEO Optimizer
   seo_optimizer = Agent(
       name="seo_optimizer",
       instructions="Optimize content for search engines.",
       tools=[keyword_analyzer, meta_generator]
   )
   
   content_pipeline = SequentialTeam([
       ideator, researcher, writer, editor, seo_optimizer
   ])

Code Development Pipeline
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # 1. Architect
   architect = Agent(
       name="architect",
       instructions="Design system architecture and create specifications."
   )
   
   # 2. Developer
   developer = Agent(
       name="developer",
       instructions="Implement code based on specifications.",
       tools=[code_generator, python_interpreter]
   )
   
   # 3. Tester
   tester = Agent(
       name="tester",
       instructions="Write and run tests for the code.",
       tools=[pytest_runner, code_analyzer]
   )
   
   # 4. Reviewer
   reviewer = Agent(
       name="reviewer",
       instructions="Review code for quality and best practices.",
       tools=[linter, security_scanner]
   )
   
   dev_pipeline = SequentialTeam([
       architect, developer, tester, reviewer
   ])

Configuration
-------------

YAML Configuration
~~~~~~~~~~~~~~~~~~

Define teams in configuration files:

.. code-block:: yaml

   # team_config.yaml
   type: sequential
   name: "Content Creation Pipeline"
   
   agents:
     - name: researcher
       instructions: "Research the topic thoroughly"
       model: "gpt-4o"
       tools:
         - web_search
         - read_documents
     
     - name: writer
       instructions: "Write engaging content"
       model: "gpt-4o"
       temperature: 0.8
     
     - name: editor
       instructions: "Edit and polish the content"
       model: "gpt-4o-mini"
   
   settings:
     timeout: 300
     max_retries: 2
     accumulate_context: true

.. code-block:: python

   from pantheon.team import SequentialTeam
   
   team = SequentialTeam.from_config("team_config.yaml")

Best Practices
--------------

1. **Clear Handoffs**: Ensure each agent clearly communicates what the next agent needs
2. **Appropriate Ordering**: Place agents in logical sequence based on dependencies
3. **Error Recovery**: Implement fallback strategies for agent failures
4. **Context Management**: Decide whether to accumulate or reset context
5. **Performance**: Consider parallel processing where dependencies allow

Performance Optimization
------------------------

Conditional Execution
~~~~~~~~~~~~~~~~~~~~~

Skip agents based on conditions:

.. code-block:: python

   class ConditionalSequentialTeam(SequentialTeam):
       async def run(self, messages):
           for agent in self.agents:
               # Check if agent should run
               if await self.should_run_agent(agent, messages):
                   response = await agent.run(messages)
                   messages = response.messages
               else:
                   print(f"Skipping {agent.name}")
           
           return response
       
       async def should_run_agent(self, agent, messages):
           # Custom logic to determine if agent should run
           if agent.name == "editor" and len(messages[-1]["content"]) < 100:
               return False  # Skip editor for short content
           return True

Caching
~~~~~~~

Cache intermediate results:

.. code-block:: python

   from functools import lru_cache
   
   class CachedSequentialTeam(SequentialTeam):
       def __init__(self, agents):
           super().__init__(agents)
           self.cache = {}
       
       async def run(self, messages):
           cache_key = self.get_cache_key(messages)
           
           for i, agent in enumerate(self.agents):
               stage_key = f"{cache_key}:stage_{i}"
               
               if stage_key in self.cache:
                   # Use cached result
                   messages = self.cache[stage_key]
               else:
                   # Run agent and cache
                   response = await agent.run(messages)
                   messages = response.messages
                   self.cache[stage_key] = messages
           
           return response