# app/tools/base.py
import inspect
import json
from collections.abc import Callable, Mapping
from types import UnionType
from typing import Any, Literal, Union, get_args, get_origin

import httpx


def function_to_input_schema(func: Any) -> dict[str, Any]:
    """Generates an OpenAI-compatible JSON Schema from a Python function's signature and type annotations."""
    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
        type(None): "null",
    }
    func_name = getattr(func, "__name__", str(func))
    try:
        signature = inspect.signature(func)
    except ValueError as e:
        raise ValueError(
            f"Failed to get signature for function {func_name}: {e}"
        ) from e

    parameters: dict[str, Any] = {}
    for param in signature.parameters.values():
        annotation = param.annotation
        origin = get_origin(annotation)

        if origin in (Union, UnionType):
            non_none = [arg for arg in get_args(annotation) if arg is not type(None)]
            if len(non_none) == 1:
                annotation = non_none[0]
                origin = get_origin(annotation)

        if origin is Literal:
            literal_args = list(get_args(annotation))
            param_spec: dict[str, Any] = {
                "type": (
                    "string"
                    if all(isinstance(a, str) for a in literal_args)
                    else "number"
                ),
                "enum": literal_args,
            }
        else:
            param_type = type_map.get(annotation, "string")
            param_spec = {"type": param_type}

        if param.default != inspect._empty and param.default is not None:
            param_spec["default"] = param.default

        parameters[param.name] = param_spec

    required = [
        param.name
        for param in signature.parameters.values()
        if param.default == inspect._empty
    ]

    return {
        "type": "object",
        "properties": parameters,
        "required": required,
    }


def format_tool_definition(
    name: str, description: str, parameters: dict[str, Any]
) -> dict[str, Any]:
    """Wraps name, description, and parameter JSON schema into an OpenAI/Ollama function tool definition."""
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": parameters,
        },
    }


def function_to_tool_definition(func: Any) -> dict[str, Any]:
    """Converts a standard Python function into a function calling tool definition using its docstring."""
    name = getattr(func, "__name__", str(func))
    doc = getattr(func, "__doc__", None) or ""
    return format_tool_definition(
        name,
        doc,
        function_to_input_schema(func),
    )


def tool_execution(tool_box: Mapping[str, Any], tool_call: Any) -> Any:
    """
    Executes a tool call using the provided tool_box dictionary.
    Supports OpenAI/LiteLLM tool call objects as well as raw dictionaries.
    """
    if hasattr(tool_call, "function"):
        function_name = tool_call.function.name
        raw_args = tool_call.function.arguments
        function_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
    elif isinstance(tool_call, dict) and "function" in tool_call:
        fn = tool_call["function"]
        function_name = fn.get("name")
        raw_args = fn.get("arguments", {})
        function_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
    elif isinstance(tool_call, dict):
        function_name = tool_call.get("name") or tool_call.get("tool")
        raw_args = tool_call.get("arguments", {})
        function_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
    else:
        raise ValueError(f"Invalid tool_call structure: {tool_call}")

    if not function_name or function_name not in tool_box:
        raise ValueError(f"Tool '{function_name}' is not registered in tool_box.")

    tool_fn = tool_box[function_name]
    tool_result = tool_fn(**function_args)
    if isinstance(tool_result, float) and tool_result.is_integer():
        return int(tool_result)
    return tool_result


class ToolCallResponse:
    """Lightweight representation of an LLM tool call response for agent loops."""

    def __init__(self, id: str, name: str, arguments: str | dict[str, Any]):
        self.id = id
        self.function = type(
            "FunctionCall",
            (),
            {
                "name": name,
                "arguments": (
                    json.dumps(arguments) if isinstance(arguments, dict) else arguments
                ),
            },
        )()


class AgentMessageResponse:
    """Container for message responses in simple agent loops."""

    def __init__(
        self,
        content: str | None = None,
        tool_calls: list[ToolCallResponse] | None = None,
    ):
        self.content = content or ""
        self.tool_calls = tool_calls or []


class AgentCompletionResponse:
    def __init__(self, message: AgentMessageResponse):
        self.choices = [type("Choice", (), {"message": message})()]


def simple_agent_loop(
    system_prompt: str,
    question: str,
    tools: list[Callable[..., Any]] | None = None,
    api_base: str = "http://localhost:11434",
    model: str = "ollama/qwen2.5:7b",
    completion_fn: Callable[..., Any] | None = None,
) -> str:
    """
    Autonomous multi-turn agent loop:
    1. Derives tool definitions dynamically from python callables via `function_to_tool_definition`.
    2. Repeatedly prompts model until final text answer is produced.
    3. Executes requested tool calls via `tool_execution` and appends tool results to context.
    """
    from app.tools.calculator import calculator
    from app.tools.search import search_web

    active_tools = tools if tools is not None else [search_web, calculator]
    tool_box = {getattr(tool, "__name__", str(tool)): tool for tool in active_tools}
    tool_definitions = [function_to_tool_definition(tool) for tool in active_tools]

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question},
    ]

    while True:
        if completion_fn is not None:
            response = completion_fn(
                api_base=api_base,
                model=model,
                messages=messages,
                tools=tool_definitions,
            )
        else:
            # Default fallback calling Ollama REST /api/chat directly
            clean_model = model.split("/")[-1]
            ollama_url = f"{api_base.rstrip('/')}/api/chat"
            payload = {
                "model": clean_model,
                "messages": messages,
                "tools": tool_definitions,
                "stream": False,
            }
            try:
                with httpx.Client(timeout=60.0) as client:
                    resp = client.post(ollama_url, json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                    msg_data = data.get("message", {})
                    ollama_tool_calls = []
                    for idx, tc in enumerate(msg_data.get("tool_calls", [])):
                        fn_info = tc.get("function", {})
                        ollama_tool_calls.append(
                            ToolCallResponse(
                                id=f"call_{idx}",
                                name=fn_info.get("name", ""),
                                arguments=fn_info.get("arguments", {}),
                            )
                        )
                    response = AgentCompletionResponse(
                        AgentMessageResponse(
                            content=msg_data.get("content", ""),
                            tool_calls=ollama_tool_calls,
                        )
                    )
            except Exception as exc:
                return f"Agent execution error: {exc}"

        assistant_message = response.choices[0].message
        if assistant_message.tool_calls:
            # Append assistant message with its tool calls
            messages.append(
                {
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in assistant_message.tool_calls
                    ],
                }
            )
            for tool_call in assistant_message.tool_calls:
                tool_result = tool_execution(tool_box, tool_call)
                messages.append(
                    {
                        "role": "tool",
                        "content": str(tool_result),
                        "tool_call_id": tool_call.id,
                    }
                )
        else:
            return assistant_message.content
