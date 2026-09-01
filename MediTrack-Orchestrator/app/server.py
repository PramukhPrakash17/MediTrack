from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.memory import MemorySaver

from app.api.chat import router as chat_router
from app.consultation.session_manager import SessionManager
from app.graph.agent_node import AgentNode
from app.graph.graph_builder import build_graph
from app.graph.tool_node import MCPToolNode
from app.llm.llm_client import build_llm
from app.mcp_client.client import MCPClient
from app.mcp_client.tool_registry import ToolRegistry


@asynccontextmanager
async def lifespan(app: FastAPI):
    mcp_client = MCPClient()
    await mcp_client.connect_all()

    tool_registry = ToolRegistry()
    await tool_registry.discover(mcp_client.sessions)

    llm = build_llm()
    llm_with_tools = llm.bind_tools(tool_registry.llm_tool_schemas)

    agent_node = AgentNode(llm_with_tools)
    tool_node = MCPToolNode(mcp_client, tool_registry)
    graph = build_graph(agent_node, tool_node, checkpointer=MemorySaver())

    app.state.graph = graph
    app.state.session_manager = SessionManager()

    yield

    await mcp_client.close()


def create_app() -> FastAPI:
    app = FastAPI(title="MediTrack Orchestrator", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(chat_router)
    return app


app = create_app()
