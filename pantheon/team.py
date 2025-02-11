import asyncio
from abc import ABC

from .agent import Agent, AgentTransfer, AgentInput


class Team(ABC):

    def __init__(self, agents: list[Agent]):
        self.agents = {}
        for agent in agents:
            self.agents[agent.name] = agent
        self.events_queue = asyncio.Queue()

    async def gather_events(self):
        async def _gather_agent_events(agent: Agent):
            while True:
                event = await agent.events_queue.get()
                new_event = {
                    "agent_name": agent.name,
                    "event": event,
                }
                self.events_queue.put_nowait(new_event)

        tasks = []
        for agent in self.agents.values():
            tasks.append(_gather_agent_events(agent))
        await asyncio.gather(*tasks)

    async def run(self, msg: AgentInput, **kwargs):
        pass


class SwarmTeam(Team):
    """Team that run agents in handoff & routines patterns like
    OpenAI's [Swarm framework](https://github.com/openai/swarm).
    """
    def __init__(self, agents: list[Agent]):
        super().__init__(agents)
        self.active_agent = agents[0]

    async def run(self, msg: AgentInput, **kwargs):
        while True:
            resp = await self.active_agent.run(msg, **kwargs)
            if isinstance(resp, AgentTransfer):
                self.active_agent = self.agents[resp.to_agent]
                msg = resp
            else:
                return resp
