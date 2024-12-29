from synago.agent import Agent


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
