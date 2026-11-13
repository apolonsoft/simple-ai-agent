import os
from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer
from tavily import TavilyClient

# Load environment variables (.env at project root or apps/api/.env)
load_dotenv()

tavily_api_key = os.getenv("TAVILY_API_KEY")
tavily_client = TavilyClient(api_key=tavily_api_key) if tavily_api_key else None

# Initialize the MCP Server (MCP 2.x standard)
mcp = MCPServer("custom-tavily-search")


@mcp.tool()
def search_web(query: str, max_results: int = 5) -> str:
    """
    Search the web using Tavily API.

    Args:
        query: Search query string
        max_results: Maximum number of results to return (default: 5)

    Returns:
        Search results as formatted string
    """
    if not tavily_client:
        return "Error: TAVILY_API_KEY is not configured in the environment."

    try:
        response = tavily_client.search(
            query=query,
            max_results=max_results,
        )
        results = response.get("results", [])
        if not results:
            return "No results found."

        return "\n\n".join(
            f"Title: {r['title']}\nURL: {r['url']}\nContent: {r['content']}"
            for r in results
        )
    except Exception as e:
        return f"Error searching web: {str(e)}"


if __name__ == "__main__":
    port = int(os.getenv("MCP_TAVILY_PORT", "8001"))
    host = os.getenv("MCP_TAVILY_HOST", "127.0.0.1")
    print(f"Starting Tavily MCP Server on http://{host}:{port}/sse ...")
    mcp.run(transport="sse", host=host, port=port)
