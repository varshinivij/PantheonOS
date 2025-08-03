Swarm Team
==========

Swarm Teams enable dynamic agent collaboration where agents can transfer control to each other based on the task requirements. This pattern provides flexible, adaptive workflows that can handle diverse and unpredictable user requests.

Overview
--------

Key features of Swarm Teams:
- **Dynamic Routing**: Agents decide when to transfer control
- **Flexible Workflows**: No predefined execution order
- **Context Preservation**: Maintain conversation context across transfers
- **Specialized Handling**: Route to the most appropriate agent
- **Adaptive Behavior**: Respond to changing requirements

Basic Usage
-----------

Creating a Swarm Team
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pantheon.team import SwarmTeam
   from pantheon.agent import Agent
   
   # Create specialized agents
   generalist = Agent(
       name="generalist",
       instructions="Handle general queries. Transfer specialized tasks to experts.",
       model="gpt-4o-mini"
   )
   
   tech_expert = Agent(
       name="tech_expert",
       instructions="Handle technical questions about programming and systems.",
       model="gpt-4o"
   )
   
   creative_expert = Agent(
       name="creative_expert",
       instructions="Handle creative tasks like writing and design.",
       model="gpt-4o"
   )
   
   # Define transfer functions
   @generalist.tool
   def transfer_to_tech_expert():
       """Transfer technical questions to the tech expert."""
       return tech_expert
   
   @generalist.tool
   def transfer_to_creative_expert():
       """Transfer creative tasks to the creative expert."""
       return creative_expert
   
   @tech_expert.tool
   def transfer_to_generalist():
       """Transfer back to generalist for non-technical matters."""
       return generalist
   
   @creative_expert.tool
   def transfer_to_generalist():
       """Transfer back to generalist for non-creative matters."""
       return generalist
   
   # Create swarm team
   team = SwarmTeam([generalist, tech_expert, creative_expert])
   
   # Run the team
   await team.chat()  # Interactive mode

Transfer Mechanisms
-------------------

Explicit Transfers
~~~~~~~~~~~~~~~~~~

Agents explicitly decide when to transfer:

.. code-block:: python

   support_agent = Agent(
       name="support_agent",
       instructions="""You are a customer support agent.
       Handle basic queries. For technical issues, transfer to tech_support.
       For billing issues, transfer to billing_support."""
   )
   
   tech_support = Agent(
       name="tech_support",
       instructions="Resolve technical problems. Transfer back when resolved."
   )
   
   billing_support = Agent(
       name="billing_support",
       instructions="Handle billing and payment issues."
   )
   
   # Define transfers with context
   @support_agent.tool
   def transfer_to_tech(issue_description: str):
       """Transfer technical issues with context."""
       return tech_support
   
   @support_agent.tool  
   def transfer_to_billing(account_id: str, issue: str):
       """Transfer billing issues with account context."""
       return billing_support

Conditional Transfers
~~~~~~~~~~~~~~~~~~~~~

Transfer based on conditions:

.. code-block:: python

   class ConditionalTransferAgent(Agent):
       def __init__(self, name, instructions, transfer_rules):
           super().__init__(name, instructions)
           self.transfer_rules = transfer_rules
       
       async def should_transfer(self, message):
           for condition, target_agent in self.transfer_rules.items():
               if await self.evaluate_condition(condition, message):
                   return target_agent
           return None
       
       async def evaluate_condition(self, condition, message):
           # Use LLM to evaluate if condition is met
           eval_response = await self.run([
               {"role": "system", "content": f"Does this message match: {condition}?"},
               {"role": "user", "content": message}
           ])
           return "yes" in eval_response.messages[-1]["content"].lower()
   
   # Create agent with transfer rules
   router = ConditionalTransferAgent(
       name="router",
       instructions="Route requests to appropriate agents.",
       transfer_rules={
           "technical programming question": tech_expert,
           "creative writing request": writer,
           "data analysis needed": analyst,
           "urgent or emergency": priority_handler
       }
   )

Advanced Patterns
-----------------

Multi-Level Swarm
~~~~~~~~~~~~~~~~~

Create hierarchical swarm structures:

.. code-block:: python

   # Level 1: Front desk
   receptionist = Agent(
       name="receptionist",
       instructions="Greet users and route to appropriate department."
   )
   
   # Level 2: Department heads
   tech_lead = Agent(
       name="tech_lead",
       instructions="Handle technical department routing."
   )
   
   sales_lead = Agent(
       name="sales_lead",
       instructions="Handle sales department routing."
   )
   
   # Level 3: Specialists
   backend_dev = Agent(name="backend_dev", instructions="Backend development expert.")
   frontend_dev = Agent(name="frontend_dev", instructions="Frontend development expert.")
   account_exec = Agent(name="account_exec", instructions="Handle sales accounts.")
   
   # Define hierarchical transfers
   @receptionist.tool
   def route_to_tech():
       return tech_lead
   
   @receptionist.tool
   def route_to_sales():
       return sales_lead
   
   @tech_lead.tool
   def route_to_backend():
       return backend_dev
   
   @tech_lead.tool
   def route_to_frontend():
       return frontend_dev
   
   @sales_lead.tool
   def route_to_account_exec():
       return account_exec
   
   # Specialists can transfer back up
   for specialist in [backend_dev, frontend_dev]:
       @specialist.tool
       def escalate_to_lead():
           return tech_lead

Circular Swarm
~~~~~~~~~~~~~~~

Agents can form circular workflows:

.. code-block:: python

   # Research loop team
   researcher = Agent(
       name="researcher",
       instructions="Research information. Transfer to analyzer when data collected."
   )
   
   analyzer = Agent(
       name="analyzer",
       instructions="Analyze research data. Transfer to validator for verification."
   )
   
   validator = Agent(
       name="validator",
       instructions="Validate findings. Transfer back to researcher if more data needed."
   )
   
   synthesizer = Agent(
       name="synthesizer",
       instructions="Synthesize validated findings into final report."
   )
   
   # Create circular flow
   @researcher.tool
   def send_to_analyzer(data: dict):
       return analyzer
   
   @analyzer.tool
   def send_to_validator(analysis: dict):
       return validator
   
   @validator.tool
   def needs_more_research(gaps: list):
       """Send back to researcher with identified gaps."""
       return researcher
   
   @validator.tool
   def send_to_synthesizer(validated_data: dict):
       """Send validated data for final synthesis."""
       return synthesizer

Context Management
------------------

Preserving Context Across Transfers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class ContextAwareSwarmTeam(SwarmTeam):
       def __init__(self, agents):
           super().__init__(agents)
           self.transfer_history = []
           
       async def run(self, messages, initial_agent=None):
           current_agent = initial_agent or self.agents[0]
           context = {
               "transfer_count": 0,
               "visited_agents": [],
               "transfer_reasons": []
           }
           
           while True:
               # Add context to agent
               current_agent.context_variables = context
               
               # Run current agent
               response = await current_agent.run(messages)
               
               # Check for transfer
               transfer_agent = self.check_transfer(response)
               
               if transfer_agent:
                   # Update context
                   context["transfer_count"] += 1
                   context["visited_agents"].append(current_agent.name)
                   context["transfer_reasons"].append(
                       response.context_variables.get("transfer_reason", "")
                   )
                   
                   # Log transfer
                   self.transfer_history.append({
                       "from": current_agent.name,
                       "to": transfer_agent.name,
                       "reason": context["transfer_reasons"][-1],
                       "timestamp": datetime.now()
                   })
                   
                   current_agent = transfer_agent
                   messages = response.messages
               else:
                   return response

Shared Memory
~~~~~~~~~~~~~

Enable agents to share information:

.. code-block:: python

   from pantheon.memory import SharedMemory
   
   # Create shared memory
   team_memory = SharedMemory()
   
   # Create agents with shared memory
   intake_agent = Agent(
       name="intake",
       instructions="Gather initial information from user.",
       memory=team_memory
   )
   
   processor_agent = Agent(
       name="processor",
       instructions="Process information gathered by intake.",
       memory=team_memory
   )
   
   @intake_agent.tool
   async def save_user_info(name: str, issue: str, priority: str):
       """Save user information to shared memory."""
       await team_memory.set("current_user", {
           "name": name,
           "issue": issue,
           "priority": priority,
           "timestamp": datetime.now()
       })
       return processor_agent
   
   @processor_agent.tool
   async def get_user_info():
       """Retrieve user information from shared memory."""
       return await team_memory.get("current_user")

Use Cases
---------

Customer Support Swarm
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Create support team
   greeter = Agent(
       name="greeter",
       instructions="""Welcome customers warmly.
       Identify their needs and route appropriately.""",
       model="gpt-4o-mini"
   )
   
   technical_support = Agent(
       name="technical_support",
       instructions="""Resolve technical issues.
       Provide step-by-step solutions.""",
       model="gpt-4o"
   )
   
   billing_support = Agent(
       name="billing_support",
       instructions="Handle billing inquiries and payment issues.",
       model="gpt-4o-mini"
   )
   
   escalation_manager = Agent(
       name="escalation_manager",
       instructions="Handle complex issues and complaints.",
       model="gpt-4o"
   )
   
   # Define routing logic
   @greeter.tool
   def route_technical():
       """Route to technical support."""
       return technical_support
   
   @greeter.tool
   def route_billing():
       """Route to billing support."""
       return billing_support
   
   @technical_support.tool
   @billing_support.tool
   def escalate_issue(reason: str):
       """Escalate complex issues."""
       return escalation_manager
   
   # Create support swarm
   support_swarm = SwarmTeam([
       greeter,
       technical_support,
       billing_support,
       escalation_manager
   ])

Project Management Swarm
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Project management team
   project_coordinator = Agent(
       name="coordinator",
       instructions="Coordinate project activities and route tasks."
   )
   
   requirements_analyst = Agent(
       name="requirements",
       instructions="Gather and analyze project requirements."
   )
   
   task_planner = Agent(
       name="planner",
       instructions="Create project plans and timelines."
   )
   
   resource_manager = Agent(
       name="resources",
       instructions="Manage team allocation and resources."
   )
   
   progress_tracker = Agent(
       name="tracker",
       instructions="Monitor progress and identify blockers."
   )
   
   # Create transfer network
   agents = [
       project_coordinator,
       requirements_analyst,
       task_planner,
       resource_manager,
       progress_tracker
   ]
   
   # Allow any agent to transfer to any other
   for source in agents:
       for target in agents:
           if source != target:
               @source.tool
               def transfer_to(agent_name: str = target.name):
                   f"""Transfer to {target.name}."""
                   return next(a for a in agents if a.name == agent_name)

Performance Optimization
------------------------

Transfer Limits
~~~~~~~~~~~~~~~

Prevent infinite transfer loops:

.. code-block:: python

   class LimitedSwarmTeam(SwarmTeam):
       def __init__(self, agents, max_transfers=10):
           super().__init__(agents)
           self.max_transfers = max_transfers
       
       async def run(self, messages):
           transfer_count = 0
           current_agent = self.agents[0]
           
           while transfer_count < self.max_transfers:
               response = await current_agent.run(messages)
               
               next_agent = self.check_transfer(response)
               if next_agent:
                   transfer_count += 1
                   current_agent = next_agent
                   messages = response.messages
               else:
                   return response
           
           # Max transfers reached
           final_response = await current_agent.run(
               messages + [{
                   "role": "system",
                   "content": "Maximum transfers reached. Provide final response."
               }]
           )
           return final_response

Transfer Analytics
~~~~~~~~~~~~~~~~~~

Track and optimize transfer patterns:

.. code-block:: python

   class AnalyticsSwarmTeam(SwarmTeam):
       def __init__(self, agents):
           super().__init__(agents)
           self.transfer_metrics = {
               "transfer_counts": {},
               "transfer_times": {},
               "transfer_paths": []
           }
       
       async def track_transfer(self, from_agent, to_agent, duration):
           # Update metrics
           key = f"{from_agent.name}->{to_agent.name}"
           self.transfer_metrics["transfer_counts"][key] = \
               self.transfer_metrics["transfer_counts"].get(key, 0) + 1
           
           if key not in self.transfer_metrics["transfer_times"]:
               self.transfer_metrics["transfer_times"][key] = []
           self.transfer_metrics["transfer_times"][key].append(duration)
           
           self.transfer_metrics["transfer_paths"].append({
               "from": from_agent.name,
               "to": to_agent.name,
               "timestamp": datetime.now(),
               "duration": duration
           })
       
       def get_analytics(self):
           """Get transfer analytics."""
           return {
               "most_common_transfers": sorted(
                   self.transfer_metrics["transfer_counts"].items(),
                   key=lambda x: x[1],
                   reverse=True
               )[:5],
               "average_transfer_times": {
                   k: sum(v) / len(v)
                   for k, v in self.transfer_metrics["transfer_times"].items()
               },
               "total_transfers": sum(self.transfer_metrics["transfer_counts"].values())
           }

Best Practices
--------------

1. **Clear Transfer Criteria**: Define when and why agents should transfer
2. **Avoid Loops**: Implement safeguards against infinite transfers
3. **Context Preservation**: Maintain important context across transfers
4. **Specialization**: Each agent should have clear expertise
5. **Graceful Degradation**: Handle transfer failures appropriately
6. **Monitoring**: Track transfer patterns for optimization