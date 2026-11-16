# app/tools/__init__.py
from app.mcp_servers.pdf_server import create_pdf, inspect_pdf, merge_pdfs
from app.tools.base import (
    format_tool_definition,
    function_to_input_schema,
    function_to_tool_definition,
    simple_agent_loop,
    tool_execution,
)
from app.tools.calculator import (
    AVAILABLE_TOOLS,
    TOOL_DEFINITIONS,
    calculator,
    calculator_tool_definition,
    create_pdf_tool_definition,
    execute_tool,
    inspect_pdf_tool_definition,
    merge_pdfs_tool_definition,
    search_web_tool_definition,
)
from app.tools.search import search_web

__all__ = [
    "function_to_input_schema",
    "format_tool_definition",
    "function_to_tool_definition",
    "tool_execution",
    "simple_agent_loop",
    "calculator",
    "calculator_tool_definition",
    "search_web",
    "search_web_tool_definition",
    "create_pdf",
    "create_pdf_tool_definition",
    "inspect_pdf",
    "inspect_pdf_tool_definition",
    "merge_pdfs",
    "merge_pdfs_tool_definition",
    "AVAILABLE_TOOLS",
    "TOOL_DEFINITIONS",
    "execute_tool",
]
