"""End-to-end latency measurement for one /chat-equivalent turn.

Times each full agent<->tool round trip (LLM decision + MCP tool execution)
separately, then the total wall time per question, for a single-tool,
multi-tool and X-ray scenario. Uses whichever LLM_PROVIDER is set in .env,
so rerun after switching providers to compare Groq vs local Ollama.

Run with: python -m scripts.perf_check
"""

import asyncio
import sys
import time
from pathlib import Path

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from app.config.settings import settings
from app.graph.agent_node import AgentNode
from app.graph.graph_builder import build_graph
from app.graph.tool_node import MCPToolNode
from app.llm.llm_client import build_llm
from app.mcp_client.client import MCPClient
from app.mcp_client.tool_registry import ToolRegistry

sys.stdout.reconfigure(encoding="utf-8")


class TimedAgentNode(AgentNode):
    async def __call__(self, state):
        start = time.perf_counter()
        result = await super().__call__(state)
        print(f"    agent LLM call:  {time.perf_counter() - start:6.2f}s")
        return result


class TimedToolNode(MCPToolNode):
    async def __call__(self, state):
        start = time.perf_counter()
        result = await super().__call__(state)
        print(f"    tool execution:  {time.perf_counter() - start:6.2f}s")
        return result


async def ask(graph, thread_id: str, text: str, temp_path: str | None = None):
    graph_input: dict = {"messages": [HumanMessage(content=text)]}
    if temp_path:
        graph_input["temp_path"] = temp_path

    config = {"configurable": {"thread_id": thread_id}}
    print(f"\nQ: {text}")

    start = time.perf_counter()
    result = await graph.ainvoke(graph_input, config=config)
    total = time.perf_counter() - start

    print(f"A: {result['messages'][-1].content}")
    print(f"  TOTAL: {total:.2f}s")
    return total


async def main():
    print(f"LLM_PROVIDER = {settings.llm_provider}\n")

    client = MCPClient()
    try:
        await client.connect_all()

        tool_registry = ToolRegistry()
        await tool_registry.discover(client.sessions)

        llm = build_llm()
        llm_with_tools = llm.bind_tools(tool_registry.llm_tool_schemas)

        agent_node = TimedAgentNode(llm_with_tools)
        tool_node = TimedToolNode(client, tool_registry)
        graph = build_graph(agent_node, tool_node, checkpointer=MemorySaver())

        results = {}

        results["single-tool"] = await ask(
            graph,
            "perf-single",
            "The patient has fever, cough and shortness of breath. What could this be?",
        )

        results["multi-tool"] = await ask(
            graph,
            "perf-multi",
            "The patient has fever, cough and shortness of breath. What could this be, "
            "and would Amoxicillin be suitable?",
        )

        image_path = Path("app/mcp_client/test_images/Test_image.jpg")
        if image_path.exists():
            results["xray"] = await ask(
                graph,
                "perf-xray",
                "Please analyze this wrist X-ray for fractures.",
                temp_path=str(image_path.resolve()),
            )

        print("\n" + "=" * 40)
        print("SUMMARY")
        for label, seconds in results.items():
            print(f"  {label:12s} {seconds:6.2f}s")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
