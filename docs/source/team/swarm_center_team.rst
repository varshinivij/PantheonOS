SwarmCenter Team
================

SwarmCenter Teams implement a hub-and-spoke pattern where a central coordinator agent manages and delegates tasks to specialized worker agents. This provides centralized control with distributed execution.

Overview
--------

Key characteristics:
- **Central Coordinator**: One agent manages all task distribution
- **Worker Specialization**: Each worker focuses on specific capabilities
- **Dynamic Delegation**: Coordinator decides which workers to engage
- **Parallel Execution**: Multiple workers can operate simultaneously
- **Result Synthesis**: Coordinator combines worker outputs

Basic Usage
-----------

Creating a SwarmCenter Team
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pantheon.team import SwarmCenterTeam
   from pantheon.agent import Agent
   
   # Create coordinator
   coordinator = Agent(
       name="project_manager",
       instructions="""You are a project manager. Analyze tasks and delegate to:
       - researcher: For information gathering
       - developer: For code implementation
       - tester: For testing and validation
       - documenter: For documentation
       Synthesize their outputs into cohesive responses.""",
       model="gpt-4o"
   )
   
   # Create specialized workers
   researcher = Agent(
       name="researcher",
       instructions="Research information and provide comprehensive findings.",
       tools=[web_search, read_papers]
   )
   
   developer = Agent(
       name="developer",
       instructions="Implement code solutions based on requirements.",
       tools=[python_interpreter]
   )
   
   tester = Agent(
       name="tester",
       instructions="Test code and validate functionality.",
       tools=[pytest_runner, code_analyzer]
   )
   
   documenter = Agent(
       name="documenter",
       instructions="Create clear documentation.",
       tools=[markdown_formatter]
   )
   
   # Create SwarmCenter team
   team = SwarmCenterTeam(
       center=coordinator,
       workers=[researcher, developer, tester, documenter]
   )
   
   # Run the team
   result = await team.run("Create a Python function to calculate fibonacci numbers")

Advanced Configuration
----------------------

Custom Delegation Strategy
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class SmartCoordinator(Agent):
       def __init__(self, workers):
           super().__init__(
               name="smart_coordinator",
               instructions="Intelligently delegate tasks to workers."
           )
           self.workers = {w.name: w for w in workers}
           
       @property
       def tools(self):
           # Dynamically create delegation tools
           tools = []
           for name, worker in self.workers.items():
               def make_delegate_tool(worker_name, worker_agent):
                   async def delegate(task: str) -> str:
                       f"""Delegate task to {worker_name}."""
                       response = await worker_agent.run([
                           {"role": "user", "content": task}
                       ])
                       return response.messages[-1]["content"]
                   delegate.__name__ = f"delegate_to_{worker_name}"
                   return delegate
               
               tools.append(make_delegate_tool(name, worker))
           return tools
   
   # Use smart coordinator
   coordinator = SmartCoordinator(workers)
   team = SwarmCenterTeam(center=coordinator, workers=workers)

Parallel Task Distribution
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import asyncio
   
   class ParallelCoordinator(Agent):
       async def distribute_tasks(self, tasks, workers):
           """Distribute tasks to workers in parallel."""
           async def run_worker_task(worker, task):
               try:
                   response = await worker.run([
                       {"role": "user", "content": task}
                   ])
                   return {
                       "worker": worker.name,
                       "task": task,
                       "result": response.messages[-1]["content"],
                       "success": True
                   }
               except Exception as e:
                   return {
                       "worker": worker.name,
                       "task": task,
                       "error": str(e),
                       "success": False
                   }
           
           # Create tasks for all worker-task pairs
           worker_tasks = []
           for task in tasks:
               # Determine best worker for task
               best_worker = await self.select_worker(task, workers)
               worker_tasks.append(run_worker_task(best_worker, task))
           
           # Run all tasks in parallel
           results = await asyncio.gather(*worker_tasks)
           return results
       
       async def select_worker(self, task, workers):
           """Select the best worker for a task."""
           # Use LLM to match task to worker
           selection_prompt = f"""
           Task: {task}
           Workers: {[w.name + ": " + w.instructions for w in workers]}
           Which worker is best suited for this task?
           """
           
           response = await self.run([
               {"role": "user", "content": selection_prompt}
           ])
           
           # Extract worker name and find matching worker
           selected_name = response.messages[-1]["content"].strip()
           return next((w for w in workers if w.name in selected_name), workers[0])

Common Patterns
---------------

Software Development Team
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Development team coordinator
   tech_lead = Agent(
       name="tech_lead",
       instructions="""You are a technical lead. For software tasks:
       1. Analyze requirements
       2. Create implementation plan
       3. Delegate to appropriate team members
       4. Review and integrate their work
       5. Ensure quality standards""",
       model="gpt-4o"
   )
   
   # Development team
   architect = Agent(
       name="architect",
       instructions="Design system architecture and technical specifications."
   )
   
   frontend_dev = Agent(
       name="frontend_dev",
       instructions="Implement user interfaces with React/Vue.",
       tools=[javascript_executor, ui_component_generator]
   )
   
   backend_dev = Agent(
       name="backend_dev",
       instructions="Implement server logic and APIs.",
       tools=[python_interpreter, api_generator]
   )
   
   database_dev = Agent(
       name="database_dev",
       instructions="Design and implement database schemas.",
       tools=[sql_executor, schema_designer]
   )
   
   qa_engineer = Agent(
       name="qa_engineer",
       instructions="Write tests and ensure code quality.",
       tools=[test_runner, code_reviewer]
   )
   
   # Create development team
   dev_team = SwarmCenterTeam(
       center=tech_lead,
       workers=[architect, frontend_dev, backend_dev, database_dev, qa_engineer]
   )

Research Team
~~~~~~~~~~~~~

.. code-block:: python

   # Research coordinator
   principal_investigator = Agent(
       name="principal_investigator",
       instructions="""Lead research projects by:
       1. Breaking down research questions
       2. Assigning tasks to specialists
       3. Synthesizing findings
       4. Drawing conclusions""",
       model="gpt-4o"
   )
   
   # Research specialists
   literature_analyst = Agent(
       name="literature_analyst",
       instructions="Review academic literature and identify key findings.",
       tools=[paper_search, citation_analyzer]
   )
   
   data_scientist = Agent(
       name="data_scientist",
       instructions="Analyze data and create visualizations.",
       tools=[python_interpreter, plotting_tools]
   )
   
   statistician = Agent(
       name="statistician",
       instructions="Perform statistical analysis and hypothesis testing.",
       tools=[r_interpreter, stats_tools]
   )
   
   domain_expert = Agent(
       name="domain_expert",
       instructions="Provide domain-specific insights and interpretations.",
       model="gpt-4o"
   )
   
   # Create research team
   research_team = SwarmCenterTeam(
       center=principal_investigator,
       workers=[literature_analyst, data_scientist, statistician, domain_expert]
   )

Content Creation Team
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Content director
   content_director = Agent(
       name="content_director",
       instructions="""Direct content creation:
       1. Understand content requirements
       2. Create content strategy
       3. Assign tasks to creators
       4. Edit and refine final output""",
       model="gpt-4o"
   )
   
   # Content creators
   copywriter = Agent(
       name="copywriter",
       instructions="Write engaging marketing copy.",
       temperature=0.8
   )
   
   technical_writer = Agent(
       name="technical_writer",
       instructions="Create technical documentation.",
       temperature=0.3
   )
   
   graphic_designer = Agent(
       name="graphic_designer",
       instructions="Create visual content descriptions.",
       tools=[image_generator, design_tools]
   )
   
   seo_specialist = Agent(
       name="seo_specialist",
       instructions="Optimize content for search engines.",
       tools=[keyword_analyzer, seo_checker]
   )
   
   # Create content team
   content_team = SwarmCenterTeam(
       center=content_director,
       workers=[copywriter, technical_writer, graphic_designer, seo_specialist]
   )

Advanced Features
-----------------

Worker Load Balancing
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class LoadBalancedCoordinator(Agent):
       def __init__(self, workers):
           super().__init__(
               name="load_balanced_coordinator",
               instructions="Distribute tasks with load balancing."
           )
           self.workers = workers
           self.worker_loads = {w.name: 0 for w in workers}
           self.worker_queue = asyncio.Queue()
           
       async def assign_task(self, task, worker_type=None):
           """Assign task to least loaded appropriate worker."""
           # Filter workers by type if specified
           available_workers = self.workers
           if worker_type:
               available_workers = [
                   w for w in self.workers
                   if worker_type in w.name or worker_type in w.instructions
               ]
           
           # Find least loaded worker
           least_loaded = min(
               available_workers,
               key=lambda w: self.worker_loads[w.name]
           )
           
           # Update load
           self.worker_loads[least_loaded.name] += 1
           
           # Process task
           try:
               result = await least_loaded.run([
                   {"role": "user", "content": task}
               ])
               return result
           finally:
               # Decrease load after completion
               self.worker_loads[least_loaded.name] -= 1

Result Aggregation
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class AggregatingCoordinator(Agent):
       def __init__(self, aggregation_strategy="comprehensive"):
           super().__init__(
               name="aggregating_coordinator",
               instructions="Coordinate and aggregate worker results."
           )
           self.aggregation_strategy = aggregation_strategy
           
       async def aggregate_results(self, results):
           """Aggregate results based on strategy."""
           if self.aggregation_strategy == "comprehensive":
               # Include all details
               prompt = f"""
               Synthesize these worker results comprehensively:
               {results}
               Include all important findings and details.
               """
           elif self.aggregation_strategy == "summary":
               # Concise summary
               prompt = f"""
               Create a concise summary of these results:
               {results}
               Focus on key findings only.
               """
           elif self.aggregation_strategy == "consensus":
               # Find consensus
               prompt = f"""
               Identify consensus and disagreements in:
               {results}
               Highlight areas of agreement and conflict.
               """
           
           response = await self.run([
               {"role": "user", "content": prompt}
           ])
           return response

Dynamic Worker Pool
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class DynamicSwarmCenter(SwarmCenterTeam):
       def __init__(self, center, initial_workers=None):
           super().__init__(center, initial_workers or [])
           self.worker_pool = []
           
       async def add_worker(self, worker):
           """Add worker to the pool dynamically."""
           self.workers.append(worker)
           self.worker_pool.append({
               "worker": worker,
               "added_at": datetime.now(),
               "tasks_completed": 0
           })
           
       async def remove_worker(self, worker_name):
           """Remove worker from the pool."""
           self.workers = [w for w in self.workers if w.name != worker_name]
           self.worker_pool = [
               w for w in self.worker_pool
               if w["worker"].name != worker_name
           ]
           
       async def scale_workers(self, load_threshold=5):
           """Auto-scale workers based on load."""
           current_load = await self.get_current_load()
           
           if current_load > load_threshold:
               # Add more workers
               new_worker = await self.create_worker_copy(self.workers[0])
               await self.add_worker(new_worker)
           elif current_load < load_threshold / 2 and len(self.workers) > 1:
               # Remove idle workers
               idle_worker = self.get_most_idle_worker()
               if idle_worker:
                   await self.remove_worker(idle_worker.name)

Monitoring and Analytics
------------------------

Performance Tracking
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class MonitoredSwarmCenter(SwarmCenterTeam):
       def __init__(self, center, workers):
           super().__init__(center, workers)
           self.metrics = {
               "task_distribution": {},
               "worker_performance": {},
               "coordination_time": [],
               "total_tasks": 0
           }
           
       async def run_with_monitoring(self, messages):
           start_time = time.time()
           
           # Track coordination
           result = await self.center.run(messages)
           coordination_time = time.time() - start_time
           
           self.metrics["coordination_time"].append(coordination_time)
           self.metrics["total_tasks"] += 1
           
           return result
           
       def get_analytics(self):
           """Get performance analytics."""
           return {
               "average_coordination_time": (
                   sum(self.metrics["coordination_time"]) /
                   len(self.metrics["coordination_time"])
                   if self.metrics["coordination_time"] else 0
               ),
               "tasks_per_worker": self.metrics["task_distribution"],
               "worker_efficiency": self.calculate_worker_efficiency(),
               "total_tasks_processed": self.metrics["total_tasks"]
           }

Worker Health Checks
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class HealthCheckCoordinator(Agent):
       async def check_worker_health(self, workers):
           """Perform health checks on all workers."""
           health_status = {}
           
           for worker in workers:
               try:
                   # Send health check
                   response = await worker.run([
                       {"role": "user", "content": "Status check: respond with 'healthy'"}
                   ])
                   
                   is_healthy = "healthy" in response.messages[-1]["content"].lower()
                   health_status[worker.name] = {
                       "status": "healthy" if is_healthy else "unhealthy",
                       "last_check": datetime.now(),
                       "response_time": response.context_variables.get("response_time")
                   }
               except Exception as e:
                   health_status[worker.name] = {
                       "status": "error",
                       "error": str(e),
                       "last_check": datetime.now()
                   }
           
           return health_status

Best Practices
--------------

1. **Clear Delegation Logic**: Coordinator should have clear rules for task distribution
2. **Worker Specialization**: Each worker should have distinct capabilities
3. **Error Handling**: Handle worker failures gracefully
4. **Load Distribution**: Balance work across workers
5. **Result Validation**: Coordinator should validate worker outputs
6. **Monitoring**: Track performance and optimize distribution

Performance Optimization
------------------------

- Use parallel execution for independent tasks
- Implement caching for repeated requests
- Monitor worker loads and balance accordingly
- Use appropriate models for coordinator vs workers
- Implement timeout mechanisms for worker tasks