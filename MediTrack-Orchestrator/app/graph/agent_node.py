from datetime import date

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from app.graph.state import ConsultationState

# Kept in sync with tool_node.py's own copy of this string (see there for
# why): Symptoms RAG's exact "nothing found" sentence. The agent/tools loop
# can call diagnose_patient across several separate passes rather than
# batching every sub-topic's tool call into one AIMessage - when that
# happens, tool_node.py only ever sees one tool result at a time, so its own
# dedup logic never sees more than one message to compare and can't collapse
# anything. This is the same collapsing logic applied instead across the
# *whole* turn's accumulated tool results, every time before the LLM is
# asked to produce the next message, which is what actually catches the
# multi-pass case.
_NO_INFO_MARKER = "(no relevant information found for this sub-topic)"


def _is_no_info_result(text: str) -> bool:
    """Substring match rather than exact equality: the RAG service's own
    "reply exactly" instruction to its LLM isn't a hard guarantee - a stray
    extra space, differing punctuation, or minor rewording would silently
    break an exact-string comparison here even when the sentence is
    unmistakably the same "nothing found" result to a human reader."""
    return "does not contain enough information" in text

# Kept short deliberately: every token here is sent on every LLM call.
# {today} is filled in fresh per call (see _build_system_prompt) so relative
# dates ("next week", "for 5 days") resolve correctly - the model has no
# other way to know the current date.
_SYSTEM_PROMPT_TEMPLATE = (
    "You are a clinical decision-support assistant for doctors using MediTrack. "
    "Today's date is {today}.\n\n"
    "Use the available tools to answer from the Symptoms RAG, Drug RAG, X-ray "
    "analysis and Backend record-keeping services - do not answer from your own "
    "knowledge when a tool applies. Never invent a filesystem path or a "
    "patient's insurance number yourself - those are supplied automatically "
    "when known; only fill in insuranceNumber when the doctor has explicitly "
    "stated it in this conversation. Preserve any uncertainty from tool "
    "results and do not present them as a confirmed diagnosis. Keep answers "
    "short and precise: 2-4 sentences for most questions, plain prose only - "
    "no tables, headers, or bullet-point lists unless the doctor explicitly "
    "asks for a list or breakdown.\n\n"
    "When a question covers more than one topic, split it into one focused tool "
    "call per topic instead of one combined call:\n"
    "- If the question describes symptoms or asks what condition is likely, "
    "always call diagnose_patient with the symptom description, even if another "
    "tool is also being called in the same turn.\n"
    "- If the doctor asks what the treatment, therapy, or management is for a "
    "named condition (without naming a specific drug), call diagnose_patient "
    "with the condition and treatment intent - do not refuse and do not call "
    "drug_information for this.\n"
    "- If the question is about a fracture, bone, or an uploaded X-ray, call "
    "analyze_xray.\n"
    "- Call drug_information only when the doctor's question names a specific "
    "medication. If the doctor asks what drug, tablet, or medication treats a "
    "condition without naming one, call diagnose_patient instead (per the rule "
    "above) rather than drug_information. Never invent, guess, or substitute "
    "candidate drug names of your own.\n\n"
    "Adding data to a patient's record (add_medicine, add_doctor_note, "
    "add_lab_report):\n"
    "- Only call one of these when the doctor explicitly asks to add, save, "
    "record, or prescribe something - never as a side effect of a read-only "
    "question.\n"
    "- Call the tool immediately once you have the necessary details - there "
    "is no confirmation step, so do not ask the doctor to confirm before "
    "calling it.\n"
    "- If the doctor names multiple medicines in one message, include all of "
    "them in a single add_medicine call rather than one call per medicine.\n"
    "- Format each medicine's frequency as morning-afternoon-night shorthand "
    "(e.g. 1-0-1, 0-0-1, 1-1-1), converting phrases like \"three times a day\" "
    "yourself. Leave dosage strength blank if the doctor did not state one - "
    "never invent a number. Resolve start/end dates against today's actual "
    "date given above.\n"
    "- If the doctor attaches a file and asks to add, save, or record a lab "
    "or blood report, call add_lab_report - not analyze_xray. If they ask to "
    "analyze, check, or review it for a fracture, call analyze_xray - not "
    "add_lab_report. If an attachment was provided this turn, never ask the "
    "doctor to upload the image or file again - it has already been "
    "received. If it's genuinely unclear which action to take, ask which one "
    "they want instead of asking them to re-upload.\n"
    "- If no patient is currently known (a tool tells you so), ask the "
    "doctor for the patient's insurance number, then retry the same request "
    "once they answer.\n\n"
    "If the doctor asks for a summary, overview, or recap of the patient's "
    "condition, call get_summary - do not try to answer this yourself or "
    "from add_medicine/add_doctor_note results."
)


class AgentNode:
    """The LLM reasoning/tool-selection step of the graph.

    Not stored in state: the system prompt is prepended on every call instead
    of being persisted as a message, so it isn't duplicated in history.
    """

    def __init__(self, llm_with_tools):
        self._llm_with_tools = llm_with_tools

    async def __call__(self, state: ConsultationState) -> dict:
        _collapse_current_turn_fallbacks(state["messages"])
        messages = [SystemMessage(_build_system_prompt()), *state["messages"]]
        response = await self._llm_with_tools.ainvoke(messages)
        return {"messages": [response]}


def _collapse_current_turn_fallbacks(messages: list) -> None:
    """Mutates ToolMessages in place: within the current turn (everything
    after the last doctor message), if at least one tool call succeeded,
    collapse every "not enough information" result down to a short marker;
    if several tool calls returned the exact same text, keep only the first
    in full. Runs on every agent step so it catches sub-topic tool calls made
    across several separate agent<->tools passes, not just ones batched into
    a single AIMessage."""
    last_human_index = next(
        (i for i in range(len(messages) - 1, -1, -1) if isinstance(messages[i], HumanMessage)),
        -1,
    )
    current_turn_tool_messages = [
        msg for msg in messages[last_human_index + 1 :] if isinstance(msg, ToolMessage)
    ]
    if len(current_turn_tool_messages) < 2:
        return

    has_success = any(not _is_no_info_result(msg.content) for msg in current_turn_tool_messages)
    seen_no_info = False
    for msg in current_turn_tool_messages:
        if _is_no_info_result(msg.content):
            if has_success or seen_no_info:
                msg.content = _NO_INFO_MARKER
            else:
                seen_no_info = True


def _build_system_prompt() -> str:
    return _SYSTEM_PROMPT_TEMPLATE.format(today=date.today().isoformat())
