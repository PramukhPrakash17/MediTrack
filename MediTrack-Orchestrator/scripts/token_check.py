"""One-off token measurement for a single /chat turn.

Only the X-ray MCP server needs to be running for this (port 8083); the
symptoms/drug tool schemas are reproduced here from their real Java
@McpTool descriptions so the measured overhead matches production exactly,
even though those two services aren't live right now. The tool *results*
fed back to the LLM in the multi-tool run are fabricated, representative
RAG answers - clearly marked below - since we can't call the real services.

Run with: python -m scripts.token_check
"""

import asyncio

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from app.graph.agent_node import SYSTEM_PROMPT
from app.llm.llm_client import build_llm
from app.mcp_client.client import MCPClient
from app.mcp_client.tool_registry import ToolRegistry

# Reproduced verbatim from RAG/.../SymptomsMcpTool.java and
# Drug-RAG-Service/.../DrugMcpTool.java so the schema size matches reality.
SYMPTOMS_SCHEMA = {
    "type": "function",
    "function": {
        "name": "diagnose_patient",
        "description": (
            "Analyze patient symptoms described in natural language and identify "
            "possible medical conditions using the MediTrack Symptoms RAG knowledge base."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The doctor's complete natural-language question describing the patient's symptoms.",
                }
            },
            "required": ["question"],
        },
    },
}

DRUG_SCHEMA = {
    "type": "function",
    "function": {
        "name": "drug_information",
        "description": (
            "Analyze medication-related questions using the MediTrack Drug RAG knowledge base.\n\n"
            "Use this tool whenever the doctor asks about a medication, including its uses, indications, "
            "side effects, contraindications, dosage guidance, pregnancy safety, alcohol interactions, "
            "drug substitutions, therapeutic class, patient suitability, or whether a specific medication "
            "is appropriate for a patient's condition.\n\n"
            "Pass the doctor's complete natural-language question unchanged. The tool will retrieve relevant "
            "drug information from the MediTrack Drug RAG knowledge base and provide an evidence-based "
            "response using only the retrieved information.\n\n"
            "Do not use this tool for identifying diseases based on symptoms, providing differential "
            "diagnoses, or analyzing X-ray images. Those requests should be handled by their respective tools.\n"
        ),
        "parameters": {
            "type": "object",
            "properties": {"question": {"type": "string"}},
            "required": ["question"],
        },
    },
}

# Representative RAG answer lengths, used only to feed a realistic second
# LLM turn - not real service output.
FAKE_SYMPTOMS_RESULT = (
    "Based on the retrieved medical context, fever, cough and shortness of breath are "
    "commonly associated with pneumonia, influenza, bronchitis, and in some cases COVID-19. "
    "Pneumonia is suggested particularly when shortness of breath is prominent alongside fever. "
    "Further clinical evaluation, such as chest auscultation and possibly imaging, is recommended "
    "to narrow the differential diagnosis. This is a possible-conditions summary, not a confirmed diagnosis."
)
FAKE_DRUG_RESULT = (
    "Amoxicillin is a penicillin-class antibiotic commonly used to treat bacterial respiratory tract "
    "infections including bacterial pneumonia and bronchitis. It is generally considered suitable when "
    "a bacterial cause is suspected or confirmed. Contraindicated in patients with penicillin allergy. "
    "Common side effects include nausea, diarrhea and rash. Dosage should be adjusted per patient weight "
    "and renal function. This information is retrieved from the Drug RAG knowledge base."
)


def report(label: str, response: AIMessage):
    usage = response.usage_metadata or {}
    print(
        f"{label:38s} prompt={usage.get('input_tokens'):>5} "
        f"completion={usage.get('output_tokens'):>5} "
        f"total={usage.get('total_tokens'):>5}"
    )
    return usage.get("total_tokens", 0)


async def main():
    mcp_client = MCPClient()
    tool_registry = ToolRegistry()

    # Only xray is live right now - discover its real schema, and only
    # connect to that one session directly (skip symptoms/drug, which are down).
    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client
    from contextlib import AsyncExitStack

    stack = AsyncExitStack()
    read_stream, write_stream, _ = await stack.enter_async_context(
        streamable_http_client("http://localhost:8083/mcp")
    )
    xray_session = ClientSession(read_stream, write_stream)
    await stack.enter_async_context(xray_session)
    await xray_session.initialize()

    await tool_registry.discover({"xray": xray_session})
    all_schemas = [SYMPTOMS_SCHEMA, DRUG_SCHEMA, *tool_registry.llm_tool_schemas]

    llm = build_llm()
    llm_with_tools = llm.bind_tools(all_schemas)

    print(f"Tool schemas bound: {[s['function']['name'] for s in all_schemas]}\n")

    grand_total = 0

    # --- Single-tool turn -------------------------------------------------
    question = "The patient has fever, cough and shortness of breath. What could this be?"
    messages = [SystemMessage(SYSTEM_PROMPT), HumanMessage(question)]

    call1 = await llm_with_tools.ainvoke(messages)
    grand_total += report("Call 1 (agent picks a tool)", call1)

    tool_call = call1.tool_calls[0]
    messages += [
        call1,
        ToolMessage(content=FAKE_SYMPTOMS_RESULT, tool_call_id=tool_call["id"]),
    ]
    call2 = await llm_with_tools.ainvoke(messages)
    grand_total += report("Call 2 (final answer, 1 tool used)", call2)

    print(f"\nSingle-tool chat turn total: {grand_total} tokens\n")
    print("-" * 70)

    # --- Multi-tool turn (symptoms -> drug -> final answer) ---------------
    grand_total_multi = 0
    question2 = (
        "The patient has fever, cough and shortness of breath. What could this be, "
        "and would Amoxicillin be suitable?"
    )
    messages2 = [SystemMessage(SYSTEM_PROMPT), HumanMessage(question2)]

    m_call1 = await llm_with_tools.ainvoke(messages2)
    grand_total_multi += report("Call 1 (agent picks 1st tool)", m_call1)
    messages2.append(m_call1)
    for tc in m_call1.tool_calls:
        fake_result = FAKE_SYMPTOMS_RESULT if tc["name"] == "diagnose_patient" else FAKE_DRUG_RESULT
        messages2.append(ToolMessage(content=fake_result, tool_call_id=tc["id"]))

    m_call2 = await llm_with_tools.ainvoke(messages2)
    grand_total_multi += report("Call 2 (2nd tool or final)", m_call2)

    if m_call2.tool_calls:
        messages2.append(m_call2)
        for tc in m_call2.tool_calls:
            fake_result = FAKE_SYMPTOMS_RESULT if tc["name"] == "diagnose_patient" else FAKE_DRUG_RESULT
            messages2.append(ToolMessage(content=fake_result, tool_call_id=tc["id"]))
        m_call3 = await llm_with_tools.ainvoke(messages2)
        grand_total_multi += report("Call 3 (final answer)", m_call3)

    print(f"\nMulti-tool chat turn total: {grand_total_multi} tokens")

    await stack.aclose()


if __name__ == "__main__":
    asyncio.run(main())
