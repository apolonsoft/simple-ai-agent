# app/tools/calculator.py
from collections.abc import Callable
from typing import Any, Literal

from app.tools.base import function_to_tool_definition, tool_execution
from app.tools.search import search_web


def calculator(
    operator: Literal["add", "subtract", "multiply", "divide"],
    first_number: float,
    second_number: float,
) -> float:
    """Perform basic arithmetic operations."""
    op = operator.strip().lower()
    if op == "add":
        return first_number + second_number
    elif op == "subtract":
        return first_number - second_number
    elif op == "multiply":
        return first_number * second_number
    elif op == "divide":
        if second_number == 0:
            raise ValueError("Cannot divide by zero")
        return first_number / second_number
    else:
        raise ValueError(f"Unsupported operator: {operator}")


AVAILABLE_TOOLS: dict[str, Callable[..., Any]] = {
    "calculator": calculator,
    "search_web": search_web,
}

# Dynamically generated schemas from registered Python functions
TOOL_DEFINITIONS: list[dict[str, Any]] = [
    function_to_tool_definition(tool) for tool in AVAILABLE_TOOLS.values()
]

# Direct dynamic definitions for explicit backward-compatible imports
calculator_tool_definition: dict[str, Any] = function_to_tool_definition(calculator)
search_web_tool_definition: dict[str, Any] = function_to_tool_definition(search_web)


def execute_tool(name: str, arguments: dict[str, Any]) -> Any:
    """Executes a registered tool by name with the given arguments using tool_execution."""
    tool_call = {
        "function": {
            "name": name,
            "arguments": arguments,
        }
    }
    return tool_execution(AVAILABLE_TOOLS, tool_call)
