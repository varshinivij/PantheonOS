Team
====

Teams in Pantheon enable multiple agents to collaborate on complex tasks. Different team structures support various collaboration patterns, from simple sequential processing to sophisticated multi-agent reasoning.

What is a Team?
---------------

A team is a coordinated group of agents that:

- **Collaborate**: Work together towards a common goal
- **Specialize**: Each agent can focus on specific aspects
- **Communicate**: Share information and context
- **Coordinate**: Follow structured interaction patterns

Team Types
----------

Sequential Team
~~~~~~~~~~~~~~~

Agents process tasks in a predefined order, with each agent building on the previous one's output.

**Use Cases:**
- Multi-step workflows
- Progressive refinement
- Pipeline processing

.. code-block:: python

   from pantheon.team import SequentialTeam
   from pantheon.agent import Agent
   
   researcher = Agent(name="researcher", instructions="Research the topic")
   writer = Agent(name="writer", instructions="Write based on research")
   editor = Agent(name="editor", instructions="Edit and polish the text")
   
   team = SequentialTeam([researcher, writer, editor])
   result = await team.run("Write an article about AI")

Swarm Team
~~~~~~~~~~

Agents can dynamically transfer control to each other based on the task requirements.

**Use Cases:**
- Dynamic routing
- Specialized handling
- Flexible workflows

.. code-block:: python

   from pantheon.team import SwarmTeam
   
   generalist = Agent(name="generalist", instructions="Handle general queries")
   specialist = Agent(name="specialist", instructions="Handle technical queries")
   
   @generalist.tool
   def transfer_to_specialist():
       """Transfer complex technical questions to specialist."""
       return specialist
   
   team = SwarmTeam([generalist, specialist])

SwarmCenter Team
~~~~~~~~~~~~~~~~

A central coordinator agent manages and delegates tasks to worker agents.

**Use Cases:**
- Task distribution
- Centralized management
- Load balancing

.. code-block:: python

   from pantheon.team import SwarmCenterTeam
   
   coordinator = Agent(
       name="coordinator",
       instructions="Analyze tasks and delegate to appropriate workers"
   )
   
   workers = [
       Agent(name="analyst", instructions="Perform data analysis"),
       Agent(name="researcher", instructions="Conduct research"),
       Agent(name="writer", instructions="Create content")
   ]
   
   team = SwarmCenterTeam(coordinator, workers)

Mixture of Agents (MoA) Team
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Multiple agents work on the same problem independently, then their outputs are synthesized.

**Use Cases:**
- Ensemble reasoning
- Diverse perspectives
- Robust solutions

.. code-block:: python

   from pantheon.team import MoATeam
   
   agents = [
       Agent(name="expert1", instructions="Approach from perspective A"),
       Agent(name="expert2", instructions="Approach from perspective B"),
       Agent(name="expert3", instructions="Approach from perspective C")
   ]
   
   aggregator = Agent(
       name="aggregator",
       instructions="Synthesize all responses into the best solution"
   )
   
   team = MoATeam(agents, aggregator)

Pantheon Team
~~~~~~~~~~~~~

Advanced team structure that combines multiple collaboration patterns for complex scenarios.

**Use Cases:**
- Complex projects
- Hybrid workflows
- Advanced coordination

Team Coordination
-----------------

Message Flow
~~~~~~~~~~~~

Teams manage message flow between agents:

.. code-block:: python

   # Sequential flow
   User → Agent1 → Agent2 → Agent3 → Response
   
   # Swarm flow  
   User → Agent1 ↔ Agent2 ↔ Agent3 → Response
   
   # MoA flow
   User → [Agent1, Agent2, Agent3] → Aggregator → Response

Context Sharing
~~~~~~~~~~~~~~~

Teams share context between agents:

.. code-block:: python

   class ContextSharingTeam(SequentialTeam):
       async def run(self, messages, context_variables=None):
           # Context is passed between agents
           shared_context = context_variables or {}
           
           for agent in self.agents:
               response = await agent.run(
                   messages,
                   context_variables=shared_context
               )
               # Update shared context
               shared_context.update(response.context_variables)
               messages = response.messages
           
           return response

Memory Management
~~~~~~~~~~~~~~~~~

Teams can share memory across agents:

.. code-block:: python

   from pantheon.memory import SharedMemory
   
   memory = SharedMemory()
   
   agent1 = Agent(name="agent1", memory=memory)
   agent2 = Agent(name="agent2", memory=memory)
   
   team = SequentialTeam([agent1, agent2])
   # Both agents share the same memory

Building Effective Teams
------------------------

Agent Selection
~~~~~~~~~~~~~~~

Choose agents based on complementary skills:

.. code-block:: python

   # Research team example
   data_collector = Agent(
       name="collector",
       instructions="Gather relevant data from various sources"
   )
   
   analyzer = Agent(
       name="analyzer", 
       instructions="Analyze data and identify patterns"
   )
   
   reporter = Agent(
       name="reporter",
       instructions="Create clear, concise reports"
   )
   
   research_team = SequentialTeam([data_collector, analyzer, reporter])

Communication Patterns
~~~~~~~~~~~~~~~~~~~~~~

Design clear handoff patterns:

.. code-block:: python

   # Clear handoff instructions
   designer = Agent(
       name="designer",
       instructions="""Design the system architecture.
       Output a structured design document for the implementer."""
   )
   
   implementer = Agent(
       name="implementer",
       instructions="""Implement based on the design document.
       Create working code following the architecture."""
   )

Error Handling
~~~~~~~~~~~~~~

Implement robust error handling:

.. code-block:: python

   class RobustTeam(SequentialTeam):
       async def run(self, messages):
           try:
               return await super().run(messages)
           except Exception as e:
               # Fallback to a general agent
               fallback = Agent(
                   name="fallback",
                   instructions="Handle errors gracefully"
               )
               return await fallback.run(messages + [
                   {"role": "system", "content": f"Error occurred: {e}"}
               ])

Advanced Team Patterns
----------------------

Conditional Routing
~~~~~~~~~~~~~~~~~~~

Route to different agents based on conditions:

.. code-block:: python

   router = Agent(
       name="router",
       instructions="Analyze query and route to appropriate specialist"
   )
   
   @router.tool
   def route_query(query_type: str):
       routes = {
           "technical": technical_expert,
           "creative": creative_expert,
           "analytical": data_analyst
       }
       return routes.get(query_type, generalist)

Parallel Processing
~~~~~~~~~~~~~~~~~~~

Process subtasks in parallel:

.. code-block:: python

   import asyncio
   
   async def parallel_team_process(query):
       agents = [agent1, agent2, agent3]
       
       # Run agents in parallel
       tasks = [
           agent.run([{"role": "user", "content": query}])
           for agent in agents
       ]
       
       results = await asyncio.gather(*tasks)
       
       # Combine results
       combiner = Agent(name="combiner", instructions="Combine results")
       return await combiner.run([
           {"role": "system", "content": str(results)}
       ])

Hierarchical Teams
~~~~~~~~~~~~~~~~~~

Create teams of teams:

.. code-block:: python

   # Sub-teams
   research_team = SequentialTeam([researcher1, researcher2])
   analysis_team = SequentialTeam([analyst1, analyst2])
   
   # Coordinator
   coordinator = Agent(
       name="coordinator",
       instructions="Coordinate between research and analysis teams"
   )
   
   # Main team
   main_team = SwarmCenterTeam(
       coordinator,
       [research_team, analysis_team]
   )

Best Practices
--------------

1. **Clear Roles**: Define distinct responsibilities for each agent
2. **Efficient Communication**: Minimize redundant information passing
3. **Error Recovery**: Plan for failures and edge cases
4. **Testing**: Test team dynamics with various scenarios
5. **Monitoring**: Track team performance and optimize

Performance Optimization
------------------------

- Use appropriate team sizes (3-7 agents typically work well)
- Minimize sequential dependencies where possible
- Cache shared computations
- Use streaming for real-time feedback
- Profile and optimize bottlenecks