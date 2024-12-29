import os
import getpass
import functools
from typing import List, Dict

from openai import AsyncOpenAI


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

    async def get_stream(
        self,
        messages: List[Dict[str, str]],
        tools: List,
        **kwargs,
    ):
        return await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            stream=True,
            **kwargs,
        )


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
