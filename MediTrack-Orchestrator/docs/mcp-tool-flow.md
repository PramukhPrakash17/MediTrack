# MCP Tool-Call Flow

How a doctor's question travels from `POST /chat` through the LangGraph agent,
out to the MCP servers (Symptoms RAG, Drug RAG, X-ray), and back — and why the
reply is the **raw** tool output, not an LLM paraphrase of it.

## Components involved

| File | Role |
|---|---|
| [`app/api/chat.py`](../app/api/chat.py) | HTTP entrypoint. Runs the graph, builds the final reply. |
| [`app/graph/agent_node.py`](../app/graph/agent_node.py) | The LLM step. Decides which tool(s) to call and with what question text. |
| [`app/graph/tool_node.py`](../app/graph/tool_node.py) | Executes the tool call(s) the agent requested, against the owning MCP server. |
| [`app/graph/graph_builder.py`](../app/graph/graph_builder.py) | Wires `agent` and `tools` into a loop: agent → tools → agent → ... → end. |
| [`app/graph/state.py`](../app/graph/state.py) | Per-consultation state threaded through the graph. |
| [`app/mcp_client/tool_registry.py`](../app/mcp_client/tool_registry.py) | Maps each MCP tool name to the server that owns it. |
| [`app/mcp_client/client.py`](../app/mcp_client/client.py) | Holds one long-lived MCP session per backend server (symptoms, drug, xray). |

## Step by step

1. **Request in** — `chat.py` receives the doctor's message, wraps it in a
   `HumanMessage`, and resets per-turn state: `xray_image_base64: None`,
   `raw_tool_outputs: []`.

2. **Agent turn** — `agent_node.py` sends the full message history (plus a
   short system prompt) to the orchestration LLM, bound with the schemas for
   every discovered MCP tool (`diagnose_patient`, `drug_information`,
   `analyze_xray`). The LLM decides:
   - whether a tool is needed at all,
   - which tool(s) to call,
   - what question text to send in each call.

   For a question touching more than one topic (e.g. symptoms *and* a drug),
   the LLM can emit **multiple tool_calls in one turn** (parallel), or call
   one tool, see the result, and decide to call another in a later turn
   (sequential). Both are possible — nothing in the code forces one or the
   other; it's the model's judgment call.

3. **Routing** — `graph_builder.py` checks the agent's response: if it
   contains `tool_calls`, route to the `tools` node; otherwise the turn ends.

4. **Tool execution** — `tool_node.py` loops over every tool call in the
   agent's message. For each one:
   - looks up the owning server via `tool_registry.server_for_tool(tool_name)`
     (`diagnose_patient` → symptoms server, `drug_information` → drug server,
     `analyze_xray` → xray server, with `temp_path` injected from state),
   - calls it over that server's MCP session (`client.py`),
   - takes the **raw text the server returned**, unmodified,
   - appends it to both a `ToolMessage` (for the LLM's own context) and to
     `raw_tool_outputs` (an accumulator carried in graph state — read the
     previous value, append this hop's results, return the combined list, so
     it survives across multiple tool-call rounds within the same turn).

5. **Loop or finish** — control returns to `agent_node`. The LLM sees the new
   `ToolMessage`(s) and either calls more tools, or produces a final message
   with no tool_calls, which ends the turn (`route_after_agent` → `END`).
   That final message's own wording is generated but is **not** what gets
   returned to the caller — see next step.

6. **Reply built** — `chat.py`'s `_build_reply()` picks the reply source:
   - **No tool was called** this turn → return the agent's own message
     (e.g. small talk, or a direct answer with no RAG/X-ray involvement).
   - **Exactly one tool was called** → return that tool's raw text,
     verbatim. Nothing reworded, nothing added.
   - **More than one tool was called** → return every raw text, each
     labeled with its tool name, joined with a blank line:
     ```
     [diagnose_patient] <raw symptoms RAG answer>

     [drug_information] <raw drug RAG answer>
     ```

## Why raw output, not an LLM summary

Earlier, the final agent LLM call (step 5) used to generate the reply itself
— rephrasing whatever the tools returned. Each RAG service already runs its
own tightly-grounded LLM call (dataset context only, no outside knowledge).
Letting the orchestrator's LLM rephrase that a second time risked it quietly
adding information the RAG never said (observed: it once added a drug's
generic name, `hydroxyzine` for Avil, that wasn't present in the retrieved
context). Returning the raw tool text sidesteps that: what the doctor sees
is exactly what the RAG/X-ray service produced.

## Known limitation: question splitting is not deterministic

Deciding *how* to split a compound question into separate tool calls, and
what text each call gets, is entirely up to the orchestrator LLM in step 2
— there's no code that guarantees a clean split. This mostly works for
questions spanning different tools (symptoms vs. drug), because tool
selection is naturally topic-based. It's less reliable for questions that
need the *same* tool called twice with different arguments — e.g. asking
about two different drugs in one message. `drug_information`'s own
description tells the LLM to *"pass the doctor's complete natural-language
question unchanged,"* and the underlying Drug RAG extracts exactly one drug
name per call (`drugName` is a single string, not a list). If the LLM obeys
that instruction literally for a two-drug question, only one drug gets
answered. This is a separate, not-yet-addressed problem — noted here for
follow-up.
