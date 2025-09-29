from fastmcp import FastMCP

mcp = FastMCP("Demo 🚀")

@mcp.tool
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


import asyncio
from fastmcp import Client

async def main():
    async with Client("https://gofastmcp.com/mcp") as client:
        result = await client.call_tool(
            name="SearchFastMcp", 
            arguments={"query": "deploy a FastMCP server"}
        )
    print(result)

asyncio.run(main())

if __name__ == "__main__":
    mcp.run()