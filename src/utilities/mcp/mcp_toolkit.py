import os

from autogen.mcp import create_toolkit
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


class MCPToolkit():
    
    def __init__(self, connection_url: str=None):
        self.connection_url = connection_url if connection_url else os.environ["MCP_HOST"]

    async def get_toolkit(self) -> any:
        async with (streamable_http_client("http://127.0.0.1:8000/mcp") as (read, write, _), ClientSession(read, write) as session,):
            await session.initialize()
            toolkit = await create_toolkit(session=session)
            return toolkit