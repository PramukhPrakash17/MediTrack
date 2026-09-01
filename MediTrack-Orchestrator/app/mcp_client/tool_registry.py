from mcp import ClientSession

# Name of the X-ray MCP tool. The temp_path argument is injected by the
# orchestrator from consultation state, so it must never be shown to the LLM
# as something it can fill in itself.
XRAY_TOOL_NAME = "analyze_xray"

# The MCP tool's own description talks about temp_path being "available",
# which made sense when the caller supplied it directly. Once temp_path is
# hidden from the LLM's schema, that phrasing makes the model unable to tell
# whether it's allowed to call the tool, so it hedges and asks the doctor to
# upload again instead of calling it. The orchestrator already returns a
# clear "no image uploaded" ToolMessage when temp_path is missing (see
# tool_node.py), so the LLM can simply always try.
XRAY_TOOL_DESCRIPTION_OVERRIDE = (
    "Analyze the X-ray image from the current consultation for possible fracture "
    "regions. Call this whenever the doctor asks to analyze, check, or review an "
    "X-ray. You do not need to know whether an image has been uploaded - call the "
    "tool and it will report if none is available yet. Not for saving a lab or "
    "blood report document - use add_lab_report for that."
)

# The MCP tool's own description says to pass the question through unchanged,
# which is right when a drug is named but says nothing about what to do when
# it isn't - that gap is what let the model start guessing candidate drug
# names and calling the tool once per guess. This override adds that missing
# instruction without touching the underlying Drug RAG service.
DRUG_TOOL_NAME = "drug_information"
DRUG_TOOL_DESCRIPTION_OVERRIDE = (
    "Look up information about a medication - uses, dosage, side effects, "
    "contraindications, interactions, substitutes, or pregnancy safety - using "
    "the MediTrack Drug RAG knowledge base. Call this once per medication the "
    "doctor actually named in their question, passing their question through "
    "as asked. If the doctor asks for a treatment or medication recommendation "
    "without naming a specific drug, call this tool at most once with that open "
    "question - do not invent, guess, or try multiple candidate drug names of "
    "your own. Do not use this tool to diagnose a condition from symptoms or to "
    "analyze an X-ray."
)

# insuranceNumber is different from temp_path: a doctor can legitimately say
# a patient's insurance number out loud in chat (e.g. when none is selected
# yet and the assistant has to ask for one), so it stays a *visible*
# parameter here rather than a hidden one. tool_node.py always prefers the
# session's already-known insurance_number over whatever the LLM fills in
# here once one is established - this parameter only matters for the
# bootstrap turn where nothing is known yet.
#
# Confirmed live: without the "you do not need to know" sentence (same gap
# XRAY_TOOL_DESCRIPTION_OVERRIDE already had to work around), the model
# asked the doctor for the insurance number *before* ever calling the tool,
# even when a patient was already selected in ServicesPage and the frontend
# had already sent insurance_number - because that value lives only in
# server-side state, the LLM has no way to see it without trying the call.
ADD_MEDICINE_TOOL_NAME = "add_medicine"
ADD_NOTE_TOOL_NAME = "add_doctor_note"
ADD_MEDICINE_DESCRIPTION_OVERRIDE = (
    "Add one or more medicines to a patient's record in MediTrack. Call this "
    "whenever the doctor explicitly asks to add, prescribe, or record "
    "medication(s) - include every medicine named in the same request in a "
    "single call, not one call per medicine. You do not need to know the "
    "patient's insurance number - call the tool and it will report if none "
    "is available yet, or use it automatically if a patient is already "
    "selected. Format each medicine's frequency as morning-afternoon-night "
    "shorthand (e.g. 1-0-1). Leave dosage blank if not stated - never invent "
    "one. Do not use this tool to look up drug information - use "
    "drug_information for that."
)
ADD_NOTE_DESCRIPTION_OVERRIDE = (
    "Add a free-text clinical note to a patient's record in MediTrack. Call "
    "this whenever the doctor explicitly asks to add, save, or record a "
    "note. You do not need to know the patient's insurance number - call "
    "the tool and it will report if none is available yet, or use it "
    "automatically if a patient is already selected. Do not use this tool "
    "for lab/blood reports or X-ray images - those have their own tools."
)

# add_lab_report is not backed by any MCP tool - Backend exposes no MCP tool
# for it. The Orchestrator calls Backend's existing multipart REST upload
# endpoint directly (see tool_node.py), so this schema is hand-registered
# here. The attached file itself is always server-injected (a filesystem
# path is never something a doctor would say out loud), but insuranceNumber
# is exposed the same way as the other two write tools, for the same
# bootstrap reason.
ADD_LAB_REPORT_TOOL_NAME = "add_lab_report"
ADD_LAB_REPORT_DESCRIPTION_OVERRIDE = (
    "Save the blood/lab report document (PDF or photographed report) the doctor "
    "has attached in this consultation to the patient's record. Call this "
    "whenever the doctor asks to add, save, or record a lab or blood report. "
    "You do not need to know whether a document has been attached, or the "
    "patient's insurance number - call the tool and it will report if either "
    "is missing, or use them automatically if already available. Not for "
    "X-ray images or fracture analysis - use analyze_xray for that."
)

# Parameter names to hide from the LLM per tool - values the tool_node
# injects server-side and the model must never invent or supply itself.
# insuranceNumber is deliberately NOT here (see comment above) - only
# genuinely unspeakable values like a filesystem path are hidden.
_HIDDEN_PARAMS: dict[str, set[str]] = {
    XRAY_TOOL_NAME: {"temp_path"},
}

# Backend's Java @McpToolParam(required = true) makes insuranceNumber a
# required property in the MCP-discovered schema. Groq's function-calling
# validates tool_call arguments strictly against that schema server-side and
# rejects a call that omits a required property (confirmed via a live 400:
# "missing properties: 'insuranceNumber'") - so it must be demoted to
# optional here even though Backend itself always needs a value; tool_node.py
# is what actually guarantees one is present before the MCP call is made.
_OPTIONAL_OVERRIDES: dict[str, set[str]] = {
    ADD_MEDICINE_TOOL_NAME: {"insuranceNumber"},
    ADD_NOTE_TOOL_NAME: {"insuranceNumber"},
}

_DESCRIPTION_OVERRIDES: dict[str, str] = {
    XRAY_TOOL_NAME: XRAY_TOOL_DESCRIPTION_OVERRIDE,
    DRUG_TOOL_NAME: DRUG_TOOL_DESCRIPTION_OVERRIDE,
    ADD_MEDICINE_TOOL_NAME: ADD_MEDICINE_DESCRIPTION_OVERRIDE,
    ADD_NOTE_TOOL_NAME: ADD_NOTE_DESCRIPTION_OVERRIDE,
}


class ToolRegistry:
    """Discovers MCP tools from every connected server and prepares them for LLM tool-calling.

    Tool schemas come from each server's own `list_tools()` response, so
    schemas never need to be hand-duplicated here - except add_lab_report,
    which isn't an MCP tool at all (see its constant above) and is appended
    by hand after discovery.
    """

    def __init__(self):
        self._tool_to_server: dict[str, str] = {}
        self.llm_tool_schemas: list[dict] = []

    async def discover(self, sessions: dict[str, ClientSession]) -> None:
        for server_name, session in sessions.items():
            response = await session.list_tools()
            for tool in response.tools:
                self._tool_to_server[tool.name] = server_name
                self.llm_tool_schemas.append(self._to_llm_schema(tool))

        self.llm_tool_schemas.append(
            {
                "type": "function",
                "function": {
                    "name": ADD_LAB_REPORT_TOOL_NAME,
                    "description": ADD_LAB_REPORT_DESCRIPTION_OVERRIDE,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "insuranceNumber": {
                                "type": "string",
                                "description": (
                                    "The patient's insurance number - only fill "
                                    "this in if the doctor has explicitly stated "
                                    "it in this conversation, otherwise leave it "
                                    "out."
                                ),
                            }
                        },
                        "required": [],
                    },
                },
            }
        )

    def server_for_tool(self, tool_name: str) -> str:
        server_name = self._tool_to_server.get(tool_name)
        if server_name is None:
            raise ValueError(f"'{tool_name}' is not a known MCP tool.")
        return server_name

    def _to_llm_schema(self, tool) -> dict:
        input_schema = getattr(tool, "inputSchema", None) or getattr(tool, "input_schema")
        parameters = dict(input_schema)
        description = _DESCRIPTION_OVERRIDES.get(tool.name, tool.description or "")
        hidden = _HIDDEN_PARAMS.get(tool.name)
        if hidden:
            parameters = self._hide_params(parameters, hidden)
        optional = _OPTIONAL_OVERRIDES.get(tool.name)
        if optional:
            parameters = self._make_optional(parameters, optional)
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": description,
                "parameters": parameters,
            },
        }

    @staticmethod
    def _hide_params(parameters: dict, names: set[str]) -> dict:
        parameters = dict(parameters)
        parameters["properties"] = {
            name: schema
            for name, schema in parameters.get("properties", {}).items()
            if name not in names
        }
        if "required" in parameters:
            parameters["required"] = [
                name for name in parameters["required"] if name not in names
            ]
        return parameters

    @staticmethod
    def _make_optional(parameters: dict, names: set[str]) -> dict:
        """Drops names from `required` only - unlike _hide_params, the
        property stays visible so the LLM can still fill it in when it
        genuinely knows the value (see _OPTIONAL_OVERRIDES)."""
        parameters = dict(parameters)
        if "required" in parameters:
            parameters["required"] = [
                name for name in parameters["required"] if name not in names
            ]
        return parameters
