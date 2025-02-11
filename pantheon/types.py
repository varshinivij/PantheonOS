from typing import List, Any
from pydantic import BaseModel


class ResponseDetails(BaseModel):
    messages: List[dict]
    context_variables: dict


class AgentResponse(BaseModel):
    agent_name: str
    content: Any
    details: Any


class AgentTransfer(BaseModel):
    from_agent: str
    to_agent: str
    history: list[dict]
    context_variables: dict


AgentInput = str | BaseModel | AgentResponse | List[str | BaseModel | dict] | AgentTransfer
