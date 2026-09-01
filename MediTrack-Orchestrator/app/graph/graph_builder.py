from langgraph.graph import END, StateGraph

from app.graph.state import ConsultationState


def route_after_agent(state: ConsultationState) -> str:
    last_message = state["messages"][-1]
    if getattr(last_message, "tool_calls", None):
        return "tools"
    return END


def build_graph(agent_node, tool_node, checkpointer):
    """Agent <-> tools loop: the agent can call tools repeatedly before answering."""
    graph = StateGraph(ConsultationState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", route_after_agent, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")
    return graph.compile(checkpointer=checkpointer)
