import copy
import json
from typing import Optional, List, Callable, AsyncGenerator, Union
from collections import defaultdict
from dataclasses import dataclass

from funcdesc.parse import parse_func

from .utils.llm import LLM, get_model
from .utils.misc import merge_chunk, desc_to_openai_function


__CTX_VARS_NAME__ = "context_variables"


@dataclass
class AgentResponse:
    messages: List[dict]
    context_variables: dict


class Agent:
    def __init__(
        self,
        name: str,
        instructions: str,
        model: Union[LLM, str, None] = None,
        functions: Optional[List[Callable]] = None,
    ):
        self.name = name
        self.instructions = instructions
        if model is None:
            model = get_model()
        elif isinstance(model, str):
            model = get_model(model)
        self.model = model
        self.functions = {}
        if functions:
            for func in functions:
                self.functions[func.__name__] = func

    def tool(self, func: Callable):
        """
        Add a tool to the agent.
        """
        self.functions[func.__name__] = func
        return self

    def _convert_functions(self) -> List[dict]:
        """Convert function to the format that the model can understand."""
        functions = []

        for func in self.functions.values():
            func_dict = desc_to_openai_function(
                parse_func(func),
                skip_params=[__CTX_VARS_NAME__],
            )
            functions.append(func_dict)
        return functions

    async def handle_tool_calls(
            self, tool_calls: List, context_variables: dict):
        messages = []
        for call in tool_calls:
            func_name = call["function"]["name"]
            params = json.loads(call["function"]["arguments"])
            func = self.functions[func_name]
            if __CTX_VARS_NAME__ in func.__code__.co_varnames:
                params[__CTX_VARS_NAME__] = context_variables
            result = func(**params)
            context_variables[call["id"]] = result
            messages.append({
                "role": "tool",
                "tool_call_id": call["id"],
                "tool_name": func_name,
                "content": repr(result),
            })
        return messages

    async def get_stream(
        self,
        messages: List,
        max_turns: Union[int, float] = float("inf"),
        context_variables: Optional[dict] = None,
    ):
        history = copy.deepcopy(messages)
        history.insert(0, {"role": "system", "content": self.instructions})
        init_len = len(history)
        if context_variables is None:
            context_variables = {}

        while len(history) - init_len < max_turns:

            message = {
                "content": "",
                "sender": self.name,
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

            # get completion with current history, agent
            stream = await self.model.get_stream(
                messages=history,
                tools=self._convert_functions() or None,
            )

            yield {"delim": "start"}
            async for chunk in stream:
                delta = chunk.choices[0].delta.model_dump()
                if delta["role"] == "assistant":
                    delta["sender"] = self.name
                yield delta
                delta.pop("role", None)
                delta.pop("sender", None)
                merge_chunk(message, delta)
            yield {"delim": "end"}

            message["tool_calls"] = list(
                message.get("tool_calls", {}).values())
            if not message["tool_calls"]:
                message["tool_calls"] = None
            history.append(message)

            if not message["tool_calls"]:
                break

            tool_messages = await self.handle_tool_calls(
                message["tool_calls"],
                context_variables=context_variables,
            )
            history.extend(tool_messages)

        yield AgentResponse(
            messages=history[init_len:],
            context_variables=context_variables,
        )

    async def run_stream(
            self, stream: AsyncGenerator,
            process_chunk: Optional[Callable] = None):
        async for chunk in stream:
            if isinstance(chunk, dict):
                if process_chunk:
                    process_chunk(chunk)
            else:
                return chunk
