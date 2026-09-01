from contextlib import AsyncExitStack

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from app.config.settings import MCP_SERVER_URLS


class MCPClient:
    """Owns one long-lived MCP session per backend service for the app's lifetime.

    Sessions are opened once at startup (`connect_all`) and reused for every
    request; they are only torn down at shutdown (`close`). Reconnecting per
    request is intentionally avoided.
    """

    def __init__(self):
        self.sessions: dict[str, ClientSession] = {}
        self._exit_stack = AsyncExitStack()

    async def connect_all(self) -> None:
        for server_name, url in MCP_SERVER_URLS.items():
            streams = await self._exit_stack.enter_async_context(
                streamable_http_client(url)
            )
            read_stream, write_stream = streams[:2]
            session = ClientSession(read_stream, write_stream)
            await self._exit_stack.enter_async_context(session)
            await session.initialize()
            self.sessions[server_name] = session

    async def close(self) -> None:
        await self._exit_stack.aclose()
        self.sessions.clear()
