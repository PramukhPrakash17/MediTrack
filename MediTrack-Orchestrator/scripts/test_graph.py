"""Manual, no-FastAPI smoke test for the agent <-> tool loop.

Exercises phases A-E from the implementation plan directly against the three
MCP servers (make sure symptoms:8081, drug:8082 and xray:8083 are running,
and GROQ_API_KEY is set in .env) without going through the HTTP layer.

Run with: python -m scripts.test_graph
"""

import asyncio
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from app.graph.agent_node import AgentNode
from app.graph.graph_builder import build_graph
from app.graph.tool_node import MCPToolNode
from app.llm.llm_client import build_llm
from app.mcp_client.client import MCPClient
from app.mcp_client.tool_registry import ToolRegistry


async def ask(graph, thread_id: str, text: str, temp_path: str | None = None):
    graph_input: dict = {"messages": [HumanMessage(content=text)]}
    if temp_path:
        graph_input["temp_path"] = temp_path

    config = {"configurable": {"thread_id": thread_id}}
    result = await graph.ainvoke(graph_input, config=config)

    print(f"\nQ: {text}")
    print(f"A: {result['messages'][-1].content}")
    return result


async def main():
    client = MCPClient()
    try:
        print("Connecting to MCP servers...")
        await client.connect_all()

        print("Discovering tools...")
        tool_registry = ToolRegistry()
        await tool_registry.discover(client.sessions)
        for schema in tool_registry.llm_tool_schemas:
            print(" -", schema["function"]["name"])

        llm = build_llm()
        llm_with_tools = llm.bind_tools(tool_registry.llm_tool_schemas)

        agent_node = AgentNode(llm_with_tools)
        tool_node = MCPToolNode(client, tool_registry)
        graph = build_graph(agent_node, tool_node, checkpointer=MemorySaver())

        # Phase D: single-tool question
        await ask(
            graph,
            "test-thread",
            "The patient has fever, cough and shortness of breath. What could this be?",
        )

        # Phase E: multi-tool question (symptoms then drug suitability)
        await ask(
            graph,
            "test-thread",
            "Would Amoxicillin be a suitable treatment for that?",
        )

        # Phase F: X-ray with temp_path injected from outside the LLM
        image_path = Path("app/mcp_client/test_images/Test_image.jpg")
        if image_path.exists():
            await ask(
                graph,
                "test-thread",
                "Please analyze this wrist X-ray for fractures.",
                temp_path=str(image_path.resolve()),
            )
            # Follow-up without re-uploading the image
            await ask(graph, "test-thread", "What was the confidence of that result?")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
