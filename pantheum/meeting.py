import copy
import time
from typing import List, Literal
import asyncio
import datetime

from pydantic import BaseModel

from .agent import Agent
from .types import Task


class Record(BaseModel):
    timestamp: str
    source: str
    targets: List[str] | Literal["all", "user"]
    content: str


class Message(BaseModel):
    content: str
    targets: List[str] | Literal["all", "user"]


class ToolEvent(BaseModel):
    agent_name: str
    tool_name: str
    tool_args_info: str


class ToolResponseEvent(BaseModel):
    agent_name: str
    tool_name: str
    tool_response: str


class ThinkingEvent(BaseModel):
    agent_name: str


def format_record(record: Record) -> str:
    return (
        f"# Meeting message\n"
        f"Timestamp: {record.timestamp}\n"
        f"Source: {record.source}\n"
        f"Targets: {record.targets}\n"
        f"Content:\n{record.content}\n"
    )


def message_to_record(message: Message, source: str) -> Record:
    now = datetime.datetime.now()
    return Record(
        timestamp=now.strftime("%Y-%m-%d %H:%M:%S"),
        source=source,
        targets=message.targets,
        content=message.content,
    )


class AgentRunner:
    def __init__(
            self,
            agent: Agent,
            public_queue: asyncio.Queue,
            stream_queue: asyncio.Queue,
            message_time_threshold: float = 1.5):
        self.agent = agent
        self.public_queue = public_queue
        self.queue = asyncio.Queue()
        self.stream_queue = stream_queue
        self.message_time_threshold = message_time_threshold
        self.run_start_time = None

    async def process_step_message(self, message: dict):
        if tool_calls := message.get("tool_calls"):
            for tool_call in tool_calls:
                event = ToolEvent(
                    agent_name=self.agent.name,
                    tool_name=tool_call["function"]["name"],
                    tool_args_info=tool_call["function"]["arguments"],
                )
                await self.stream_queue.put(event)
        if message.get("role") == "tool":
            event = ToolResponseEvent(
                agent_name=self.agent.name,
                tool_name=message.get("tool_name"),
                tool_response=message.get("content"),
            )
            self.stream_queue.put_nowait(event)

    async def process_chunk(self, _):
        if self.run_start_time is not None:
            run_time = time.time() - self.run_start_time
            if run_time > self.message_time_threshold:
                self.stream_queue.put_nowait(
                    ThinkingEvent(agent_name=self.agent.name)
                )
                self.run_start_time = None

    async def run(self):
        while True:
            record = await self.queue.get()
            prompt = format_record(record)

            self.run_start_time = time.time()
            resp = await self.agent.run(
                prompt,
                response_format=Message,
                process_step_message=self.process_step_message,
                process_chunk=self.process_chunk,
            )
            self.run_start_time = None
            record = message_to_record(resp.content, self.agent.name)
            self.public_queue.put_nowait(record)


class Meeting:
    def __init__(self, agents: List[Agent]):
        self.agents = {agent.name: copy.deepcopy(agent) for agent in agents}
        self.inject_instructions()
        self.public_queue = asyncio.Queue()
        self.stream_queue = asyncio.Queue()
        self.agent_runners = {
            agent.name: AgentRunner(agent, self.public_queue, self.stream_queue)
            for agent in agents
        }

    def inject_instructions(self):
        for agent in self.agents.values():
            agent.instructions += (
                f"You are a meeting participant, your name is {agent.name}, "
                f"Don't send message to 'all', when it's not necessary. "
                f"Don't repeat the input message in your response."
            )

    async def process_public_queue(self):
        while True:
            record = await self.public_queue.get()
            self.stream_queue.put_nowait(record)
            if record.targets == "all":
                for runner in self.agent_runners.values():
                    if runner.agent.name != record.source:
                        runner.queue.put_nowait(record)
            elif isinstance(record.targets, list):
                for target in record.targets:
                    if target in self.agent_runners:
                        self.agent_runners[target].queue.put_nowait(record)

    async def run(self, initial_message: Record | None = None):
        if initial_message:
            self.public_queue.put_nowait(initial_message)

        await asyncio.gather(
            self.process_public_queue(),
            *[runner.run() for runner in self.agent_runners.values()],
        )


class Team:
    def __init__(
            self,
            leader: Agent,
            members: List[Agent]):
        self.leader = leader
        self.members = members

    async def solve(self, task: Task):
        pass
