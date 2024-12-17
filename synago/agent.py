import os
import getpass
import typing as T

from langchain_core.language_models.llms import LLM
from langchain_openai import ChatOpenAI


class Agent:
    def __init__(
        self,
        name: str,
        system_prompt: str,
        llm: T.Optional[LLM] = None,
    ):
        self.name = name
        self.system_prompt = system_prompt
        if llm is None:
            self.llm = ChatOpenAI(
                api_key=(
                    os.getenv("OPENAI_API_KEY") or
                    getpass.getpass("OpenAI API Key: ")
                ),
                model="gpt-4o",
                temperature=0.0,
            )
        else:
            self.llm = llm

    def run(self, prompt: str) -> str:
        pass

