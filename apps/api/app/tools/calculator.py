# app/tools/calculator.py
from typing import Any

calculator_tool_definition: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": "Perform basic arithmetic operations.",
        "parameters": {
            "type": "object",
            "properties": {
                "operator": {
                    "type": "string",
                    "description": "Arithmetic operation to perform",
                    "enum": ["add", "subtract", "multiply", "divide"],
                },
                "first_number": {
                    "type": "number",
                    "description": "First number for the calculation",
                },
                "second_number": {
                    "type": "number",
                    "description": "Second number for the calculation",
                },
            },
            "required": ["operator", "first_number", "second_number"],
        },
    },
}


def calculator(operator: str, first_number: float, second_number: float):
    if operator == "add":
        return first_number + second_number
    elif operator == "subtract":
        return first_number - second_number
    elif operator == "multiply":
        return first_number * second_number
    elif operator == "divide":
        if second_number == 0:
            raise ValueError("Cannot divide by zero")
        return first_number / second_number
    else:
        raise ValueError(f"Unsupported operator: {operator}")


AVAILABLE_TOOLS = {
    "calculator": calculator,
}

TOOL_DEFINITIONS = [
    calculator_tool_definition,
]


def execute_tool(name: str, arguments: dict[str, Any]) -> Any:
    """Executes a registered tool by name with the given arguments."""
    if name not in AVAILABLE_TOOLS:
        raise ValueError(f"Tool '{name}' is not registered.")

    if name == "calculator":
        operator = str(arguments.get("operator", "")).strip().lower()
        first_number = float(arguments["first_number"])
        second_number = float(arguments["second_number"])
        result = calculator(
            operator=operator,
            first_number=first_number,
            second_number=second_number,
        )
        # Format as int if it's an exact integer, otherwise keep float
        if isinstance(result, float) and result.is_integer():
            return int(result)
        return result

    tool_fn = AVAILABLE_TOOLS[name]
    return tool_fn(**arguments)
