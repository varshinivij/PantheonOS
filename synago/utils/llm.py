import os
import getpass
import functools
from typing import List, Dict, Optional
from collections import defaultdict

from pydantic import BaseModel
from openai import AsyncOpenAI, NotGiven

from .misc import merge_chunk


@functools.lru_cache
def get_openai_api_key() -> str:
    return os.getenv("OPENAI_API_KEY") or getpass.getpass("OpenAI API Key: ")


class LLM:
    def __init__(self, model: str):
        self.model = model

    def get_stream(
        self,
        messages: List[Dict[str, str]],
        tools: List,
        **kwargs,
    ):
        raise NotImplementedError


class OpenAIModel(LLM):
    def __init__(self, model: str):
        super().__init__(model)
        self.client = AsyncOpenAI(api_key=get_openai_api_key())

    async def get_stream_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List] = None,
        **kwargs,
    ):
        _pcall = True
        if not tools:
            _pcall = NotGiven()
            tools = NotGiven()
        return await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            parallel_tool_calls=_pcall,
            stream=True,
            **kwargs,
        )

    def get_structured_stream_completion(
        self,
        messages: List[Dict[str, str]],
        response_format: BaseModel,
        tools: Optional[List] = None,
        **kwargs,
    ):
        _pcall = True
        if not tools:
            _pcall = NotGiven()
            tools = NotGiven()
        return self.client.beta.chat.completions.stream(
            model=self.model,
            messages=messages,
            tools=tools,
            parallel_tool_calls=_pcall,
            response_format=response_format,
            **kwargs,
        )

    async def get_stream(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List] = None,
        sender: Optional[str] = None,
        response_format: Optional[BaseModel] = None,
        **kwargs,
    ):
        if response_format:
            return self.__get_structured_stream(
                messages=messages,
                tools=tools,
                response_format=response_format,
                sender=sender,
                **kwargs,
            )
        return self.__get_normal_stream(
            messages=messages,
            tools=tools,
            sender=sender,
            **kwargs,
        )

    async def __get_normal_stream(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List] = None,
        sender: Optional[str] = None,
        **kwargs,
    ):

        message = {
            "content": "",
            "role": "assistant",
            "function_call": None,
            "tool_calls": defaultdict(
                lambda: {
                    "function": {"arguments": "", "name": ""},
                    "id": "",
                    "type": "",
                }
            ),
        }
        if sender:
            message["sender"] = sender

        stream = await self.get_stream_completion(
            messages=messages,
            tools=tools,
            **kwargs,
        )

        yield {"delim": "start"}
        async for chunk in stream:
            delta = chunk.choices[0].delta.model_dump()
            if (delta["role"] == "assistant") and sender:
                delta["sender"] = sender
            yield delta
            delta.pop("role", None)
            delta.pop("sender", None)
            merge_chunk(message, delta)

        message["tool_calls"] = list(
            message.get("tool_calls", {}).values())
        if not message["tool_calls"]:
            message["tool_calls"] = None

        yield {"delim": "end", "complete": message}

    async def __get_structured_stream(
        self,
        messages: List[Dict[str, str]],
        response_format: BaseModel,
        tools: Optional[List] = None,
        sender: Optional[str] = None,
        **kwargs,
    ):
        async with self.get_structured_stream_completion(
            messages=messages,
            response_format=response_format,
            tools=tools,
            **kwargs,
        ) as stream:
            yield {"delim": "start"}
            async for event in stream:
                if event.type == "chunk":
                    delta = event.chunk.choices[0].delta.model_dump()
                    snapshot_msg = event.snapshot.choices[0].message
                    if snapshot_msg.role == "assistant" and sender:
                        delta["sender"] = sender
                    yield delta
            final_completion = await stream.get_final_completion()
            final_msg = final_completion.choices[0].message.model_dump()
            yield {"delim": "end", "complete": final_msg}


DEFAULT_MODEL = "gpt-4o"


def get_model(model: str = DEFAULT_MODEL) -> LLM:
    if "/" in model:
        provider, model_name = model.split("/")
    else:
        provider = "openai"
        model_name = model

    if provider == "openai":
        return OpenAIModel(model_name)

    raise ValueError(f"Unsupported model: {model}")
