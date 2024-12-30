from funcdesc.desc import Description, NotDef
from typing import List


def merge_fields(target, source):
    for key, value in source.items():
        if isinstance(value, str):
            target[key] += value
        elif value is not None and isinstance(value, dict):
            merge_fields(target[key], value)


def merge_chunk(final_response: dict, delta: dict) -> None:
    delta.pop("role", None)
    merge_fields(final_response, delta)

    tool_calls = delta.get("tool_calls")
    if tool_calls and len(tool_calls) > 0:
        index = tool_calls[0].pop("index")
        merge_fields(final_response["tool_calls"][index], tool_calls[0])


def desc_to_openai_function(
        desc: Description,
        skip_params: List[str] = []) -> dict:
    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
        type(None): "null",
    }

    parameters = {}
    required = []

    for arg in desc.inputs:
        if arg.name in skip_params:
            continue
        tp = type_map.get(arg.type, "string")
        parameters[arg.name] = {
            "type": tp,
            "description": arg.doc or "",
        }
        if arg.default is NotDef:
            required.append(arg.name)

    func_dict = {
        "type": "function",
        "function": {
            "name": desc.name,
            "description": desc.doc or "",
            "parameters": {
                "type": "object",
                "properties": parameters,
                "required": required,
                "additionalProperties": False,
            },
            "strict": True,
        },
    }

    return func_dict
