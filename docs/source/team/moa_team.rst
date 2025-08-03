MoA Team
========

Mixture of Agents (MoA) Team implements an ensemble approach where multiple agents work on the same problem independently, and their outputs are synthesized by an aggregator agent. This pattern provides robust, diverse solutions by leveraging multiple perspectives.

Overview
--------

MoA Teams operate in two phases:
1. **Parallel Processing**: Multiple agents work on the same input simultaneously
2. **Aggregation**: A specialized agent synthesizes all outputs into a final response

This approach is inspired by ensemble methods in machine learning and provides:
- Diverse perspectives on problems
- Reduced bias from any single agent
- More robust and comprehensive solutions
- Higher quality outputs through synthesis

Basic Usage
-----------

Creating a MoA Team
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pantheon.team import MoATeam
   from pantheon.agent import Agent
   
   # Create diverse expert agents
   technical_expert = Agent(
       name="technical_expert",
       instructions="Provide technical analysis focusing on implementation details."
   )
   
   business_expert = Agent(
       name="business_expert",
       instructions="Analyze from a business perspective, considering ROI and strategy."
   )
   
   user_expert = Agent(
       name="user_expert",
       instructions="Focus on user experience and usability aspects."
   )
   
   # Create aggregator
   aggregator = Agent(
       name="aggregator",
       instructions="""Synthesize all expert opinions into a comprehensive response.
       Identify consensus, highlight disagreements, and provide a balanced conclusion."""
   )
   
   # Create MoA team
   team = MoATeam(
       agents=[technical_expert, business_expert, user_expert],
       aggregator=aggregator
   )
   
   # Run the team
   result = await team.run("Should we migrate our system to microservices?")

Advanced Configuration
----------------------

Custom Aggregation Strategy
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class WeightedAggregator(Agent):
       def __init__(self, weights=None):
           super().__init__(
               name="weighted_aggregator",
               instructions="Aggregate responses with weighted importance."
           )
           self.weights = weights or {}
       
       async def aggregate(self, responses):
           # Apply weights to different experts
           weighted_responses = []
           for agent_name, response in responses.items():
               weight = self.weights.get(agent_name, 1.0)
               weighted_responses.append({
                   "agent": agent_name,
                   "response": response,
                   "weight": weight
               })
           
           # Create weighted synthesis
           messages = [{
               "role": "system",
               "content": f"Synthesize these weighted expert opinions: {weighted_responses}"
           }]
           
           return await self.run(messages)
   
   # Use weighted aggregator
   aggregator = WeightedAggregator(weights={
       "technical_expert": 2.0,
       "business_expert": 1.5,
       "user_expert": 1.0
   })
   
   team = MoATeam(agents, aggregator)

Parallel Processing Control
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pantheon.team import MoATeam
   import asyncio
   
   class ControlledMoATeam(MoATeam):
       def __init__(self, agents, aggregator, max_concurrent=None, timeout=None):
           super().__init__(agents, aggregator)
           self.max_concurrent = max_concurrent or len(agents)
           self.timeout = timeout
       
       async def run(self, messages):
           # Create semaphore for concurrency control
           semaphore = asyncio.Semaphore(self.max_concurrent)
           
           async def run_agent_with_limit(agent):
               async with semaphore:
                   try:
                       if self.timeout:
                           return await asyncio.wait_for(
                               agent.run(messages),
                               timeout=self.timeout
                           )
                       return await agent.run(messages)
                   except asyncio.TimeoutError:
                       return {
                           "agent": agent.name,
                           "error": "Timeout",
                           "messages": [{"role": "assistant", "content": "Response timeout"}]
                       }
           
           # Run all agents with limits
           tasks = [run_agent_with_limit(agent) for agent in self.agents]
           responses = await asyncio.gather(*tasks, return_exceptions=True)
           
           # Aggregate responses
           return await self.aggregator.run(self.format_responses(responses))

Common Patterns
---------------

Decision Making Team
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Create specialists for different aspects
   risk_analyst = Agent(
       name="risk_analyst",
       instructions="Analyze risks and potential negative outcomes.",
       model="gpt-4o"
   )
   
   opportunity_analyst = Agent(
       name="opportunity_analyst",
       instructions="Identify opportunities and potential benefits.",
       model="gpt-4o"
   )
   
   technical_feasibility = Agent(
       name="technical_feasibility",
       instructions="Assess technical feasibility and requirements.",
       model="gpt-4o"
   )
   
   financial_analyst = Agent(
       name="financial_analyst",
       instructions="Analyze financial implications and ROI.",
       model="gpt-4o"
   )
   
   # Decision synthesizer
   decision_maker = Agent(
       name="decision_maker",
       instructions="""Synthesize all analyses into a clear recommendation.
       Structure your response as:
       1. Summary of each perspective
       2. Key consensus points
       3. Major disagreements
       4. Final recommendation with rationale
       5. Next steps""",
       model="gpt-4o"
   )
   
   decision_team = MoATeam(
       agents=[risk_analyst, opportunity_analyst, technical_feasibility, financial_analyst],
       aggregator=decision_maker
   )

Creative Content Team
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Different creative perspectives
   storyteller = Agent(
       name="storyteller",
       instructions="Focus on narrative and emotional engagement.",
       temperature=0.9
   )
   
   factual_writer = Agent(
       name="factual_writer",
       instructions="Ensure accuracy and include relevant data.",
       temperature=0.3
   )
   
   style_expert = Agent(
       name="style_expert",
       instructions="Focus on writing style, flow, and readability.",
       temperature=0.7
   )
   
   # Creative director as aggregator
   creative_director = Agent(
       name="creative_director",
       instructions="""Combine all creative inputs into a polished final piece.
       Maintain the narrative strength, factual accuracy, and stylistic excellence.""",
       temperature=0.6
   )
   
   creative_team = MoATeam(
       agents=[storyteller, factual_writer, style_expert],
       aggregator=creative_director
   )

Research Analysis Team
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Research specialists
   literature_reviewer = Agent(
       name="literature_reviewer",
       instructions="Review existing research and identify gaps.",
       tools=[search_academic_papers, summarize_paper]
   )
   
   data_analyst = Agent(
       name="data_analyst",
       instructions="Analyze quantitative data and statistics.",
       tools=[python_interpreter, create_charts]
   )
   
   methodology_expert = Agent(
       name="methodology_expert",
       instructions="Evaluate research methods and validity.",
       model="gpt-4o"
   )
   
   # Research synthesizer
   research_synthesizer = Agent(
       name="research_synthesizer",
       instructions="""Create a comprehensive research summary that:
       - Integrates findings from all analyses
       - Identifies patterns and contradictions
       - Provides evidence-based conclusions
       - Suggests future research directions""",
       model="gpt-4o"
   )
   
   research_team = MoATeam(
       agents=[literature_reviewer, data_analyst, methodology_expert],
       aggregator=research_synthesizer
   )

Advanced Features
-----------------

Voting Mechanism
~~~~~~~~~~~~~~~~

Implement voting-based aggregation:

.. code-block:: python

   class VotingAggregator(Agent):
       def __init__(self, voting_method="majority"):
           super().__init__(
               name="voting_aggregator",
               instructions="Aggregate responses using voting."
           )
           self.voting_method = voting_method
       
       async def aggregate_with_voting(self, responses):
           # Extract key decisions from each response
           votes = {}
           for agent_name, response in responses.items():
               # Use LLM to extract vote
               vote_prompt = f"Extract the main recommendation from: {response}"
               vote_response = await self.run([
                   {"role": "user", "content": vote_prompt}
               ])
               votes[agent_name] = vote_response.messages[-1]["content"]
           
           # Determine winning decision
           if self.voting_method == "majority":
               winner = self.majority_vote(votes)
           elif self.voting_method == "weighted":
               winner = self.weighted_vote(votes)
           
           # Create final response
           return await self.run([{
               "role": "system",
               "content": f"The team decision is: {winner}. Explain why based on: {responses}"
           }])

Quality Scoring
~~~~~~~~~~~~~~~

Score and filter responses before aggregation:

.. code-block:: python

   class QualityScoringMoATeam(MoATeam):
       def __init__(self, agents, aggregator, quality_threshold=0.7):
           super().__init__(agents, aggregator)
           self.quality_threshold = quality_threshold
       
       async def score_response(self, response):
           # Use a scoring agent
           scorer = Agent(
               name="quality_scorer",
               instructions="Score response quality from 0-1 based on completeness, accuracy, and relevance."
           )
           
           score_response = await scorer.run([{
               "role": "user",
               "content": f"Score this response (0-1): {response}"
           }])
           
           # Extract score
           try:
               score = float(score_response.messages[-1]["content"])
               return score
           except:
               return 0.5  # Default score
       
       async def run(self, messages):
           # Get all responses
           responses = await super().get_agent_responses(messages)
           
           # Score and filter
           scored_responses = {}
           for agent_name, response in responses.items():
               score = await self.score_response(response)
               if score >= self.quality_threshold:
                   scored_responses[agent_name] = {
                       "response": response,
                       "score": score
                   }
           
           # Aggregate only quality responses
           return await self.aggregator.run(scored_responses)

Streaming MoA
~~~~~~~~~~~~~

Stream aggregated responses:

.. code-block:: python

   class StreamingMoATeam(MoATeam):
       async def run_stream(self, messages):
           # Collect all responses first
           responses = await self.get_agent_responses(messages)
           
           # Stream aggregation
           aggregation_messages = [{
               "role": "system",
               "content": f"Synthesize these responses: {responses}"
           }]
           
           async for chunk in self.aggregator.run_stream(aggregation_messages):
               yield chunk

Performance Optimization
------------------------

Caching Agent Responses
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from functools import lru_cache
   import hashlib
   
   class CachedMoATeam(MoATeam):
       def __init__(self, agents, aggregator, cache_ttl=3600):
           super().__init__(agents, aggregator)
           self.cache = {}
           self.cache_ttl = cache_ttl
       
       def get_cache_key(self, agent_name, messages):
           content = str(messages) + agent_name
           return hashlib.md5(content.encode()).hexdigest()
       
       async def run_agent_cached(self, agent, messages):
           cache_key = self.get_cache_key(agent.name, messages)
           
           # Check cache
           if cache_key in self.cache:
               cached_time, response = self.cache[cache_key]
               if time.time() - cached_time < self.cache_ttl:
                   return response
           
           # Run and cache
           response = await agent.run(messages)
           self.cache[cache_key] = (time.time(), response)
           return response

Early Termination
~~~~~~~~~~~~~~~~~

Stop processing if consensus is reached early:

.. code-block:: python

   class EarlyTerminationMoATeam(MoATeam):
       def __init__(self, agents, aggregator, consensus_threshold=0.8):
           super().__init__(agents, aggregator)
           self.consensus_threshold = consensus_threshold
       
       async def check_consensus(self, responses):
           # Use LLM to check consensus
           checker = Agent(
               name="consensus_checker",
               instructions="Determine consensus level (0-1) among responses."
           )
           
           result = await checker.run([{
               "role": "user",
               "content": f"Rate consensus (0-1) in: {responses}"
           }])
           
           try:
               return float(result.messages[-1]["content"])
           except:
               return 0.0
       
       async def run(self, messages):
           responses = {}
           
           for agent in self.agents:
               responses[agent.name] = await agent.run(messages)
               
               # Check for early consensus
               if len(responses) >= 2:
                   consensus = await self.check_consensus(responses)
                   if consensus >= self.consensus_threshold:
                       break
           
           return await self.aggregator.run(responses)

Best Practices
--------------

1. **Diverse Agents**: Use agents with different perspectives and approaches
2. **Clear Aggregation**: Design aggregator instructions for effective synthesis
3. **Error Handling**: Handle individual agent failures gracefully
4. **Performance**: Consider timeout and concurrency limits
5. **Quality Control**: Implement response validation and scoring
6. **Documentation**: Document each agent's role and perspective