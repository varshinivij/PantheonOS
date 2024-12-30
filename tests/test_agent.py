from synago.agent import Agent
from pydantic import BaseModel, Field
from typing import List
import random


async def test_stream():
    agent = Agent(
        name="test",
        instructions="You are a sci-fi fan, you can answer any sci-fi related questions.",
        model="gpt-4o-mini",
    )
    msgs = [{"role": "user", "content": "What is the meaning of life? Just give me a number without any other words and symbols."}]
    stream = agent.get_stream(msgs)
    print("")
    print("answer:")
    resp = await agent.run_stream(
        stream,
        lambda chunk: print(chunk.get("content", "") or "", end="", flush=True))
    assert len(resp.messages) == 1


async def test_tool_use():
    agent = Agent(
        name="test",
        instructions="You are a weather agent, you can use the weather API to get the weather of a city.",
        model="gpt-4o-mini",
    )

    @agent.tool
    def get_weather(city: str):
        """Get the weather of a city."""
        return {"weather": "sunny"}

    msgs = [{"role": "user", "content": "What is the weather in Palo Alto?"}]
    stream = agent.get_stream(msgs)
    resp = await agent.run_stream(stream)
    print()
    print(resp)
    call_id = resp.messages[0]["tool_calls"][0]["id"]
    assert resp.context_variables[call_id]["weather"] == "sunny"


async def test_structured_output():
    agent = Agent(
        name="test",
        instructions="You are a sci-fi fan, you can answer any sci-fi related questions.",
        model="gpt-4o-mini",
    )

    class SciFiBook(BaseModel):
        title: str
        author: str
        year: int

    class SciFiBookList(BaseModel):
        books: List[SciFiBook]

    stream = agent.get_stream(
        messages=[{"role": "user", "content": "Recommend me 5 sci-fi books."}],
        response_format=SciFiBookList,
    )

    def assert_chunk(chunk):
        assert isinstance(chunk, dict)

    resp = await agent.run_stream(stream, assert_chunk)
    print(resp)
    assert isinstance(resp.messages[0]["parsed"], SciFiBookList)
    assert len(resp.messages[0]["parsed"].books) == 5


async def test_run():
    agent = Agent(
        name="test",
        instructions="You are a sci-fi fan, you can answer any sci-fi related questions, and you can use the tool calls to get the rating of each book.",
        model="gpt-4o-mini",
    )

    class SciFiBook(BaseModel):
        title: str
        author: str
        year: int

    class SciFiBookList(BaseModel):
        books: List[SciFiBook]
        ratings: List[float] = Field(description="Use tool calls to get the rating of each book.")

    @agent.tool
    def get_book_rating(title: str) -> float:
        """Get the rating of a book."""
        print(title)
        return random.random()

    resp = await agent.run(
        messages=[{"role": "user", "content": "Recommend me 5 sci-fi books."}],
        response_format=SciFiBookList,
    )
    print(resp)
    final_msg = resp.messages[-1]
    assert isinstance(final_msg["parsed"], SciFiBookList)
    assert len(final_msg["parsed"].books) == 5
    for r in final_msg["parsed"].ratings:
        assert 0 <= r <= 1.0
