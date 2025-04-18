
import asyncio
from pathlib import Path
from typing import Callable, Awaitable

from .room import ChatRoom
from ..agent import Agent
from ..team import Team
from .endpoint import Endpoint
from ..memory import MemoryManager


async def default_agent_factory() -> Agent | Team:
    agent = Agent(
        name="Pantheon",
        instructions="You are a helpful assistant that can answer questions and help with tasks.",
        model="gpt-4.1",
    )
    return agent


async def start_services(
    service_name: str = "pantheon-chatroom",
    memory_path: str = "./.pantheon-chatroom",
    workspace_path: str = "./.pantheon-chatroom-workspace",
    agent_factory: Callable[[], Awaitable[Agent | Team]] = default_agent_factory,
    log_level: str = "INFO",
):
    memory_manager = MemoryManager(memory_path)
    agent = await agent_factory()
    w_path = Path(workspace_path)
    w_path.mkdir(parents=True, exist_ok=True)
    endpoint = Endpoint(workspace_path=workspace_path)
    asyncio.create_task(endpoint.run(log_level=log_level))
    await asyncio.sleep(0.5)

    s = await endpoint.get_service("python_interpreter")
    if s is None:
        raise ValueError("Python interpreter service not found")
    if isinstance(agent, Agent):
        await agent.remote_toolset(s["id"])

    s = await endpoint.get_service("file_manager")
    if s is None:
        raise ValueError("File manager service not found")
    if isinstance(agent, Agent):
        await agent.remote_toolset(s["id"])

    chat_room = ChatRoom(
        agent,
        endpoint.worker.service_id,
        memory_manager,
        name=service_name,
    )
    await chat_room.run(log_level=log_level)
