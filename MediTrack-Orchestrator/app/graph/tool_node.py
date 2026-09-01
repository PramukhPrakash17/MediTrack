from pathlib import Path

import httpx
from langchain_core.messages import ToolMessage

from app.config.settings import settings
from app.graph.state import ConsultationState
from app.mcp_client.client import MCPClient
from app.mcp_client.tool_registry import (
    ADD_LAB_REPORT_TOOL_NAME,
    ADD_MEDICINE_TOOL_NAME,
    ADD_NOTE_TOOL_NAME,
    XRAY_TOOL_NAME,
    ToolRegistry,
)

_WRITE_TOOL_NAMES = {ADD_MEDICINE_TOOL_NAME, ADD_NOTE_TOOL_NAME, ADD_LAB_REPORT_TOOL_NAME}

# Backend's /api/labreport/upload endpoint checks file.getContentType() with
# exact string equality against these three values (including the
# non-standard "image/jpg" rather than "image/jpeg") - matching that exactly
# here, not the standard MIME type, or every JPEG upload would be rejected.
_LAB_REPORT_MIME_TYPES = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpg",
    ".jpeg": "image/jpg",
}


class MCPToolNode:
    """Executes the tool call(s) the agent requested.

    Responsibilities: route each tool call to its owning MCP server (or, for
    add_lab_report, directly to Backend's existing REST upload endpoint -
    see _upload_lab_report), inject temp_path/insuranceNumber values the LLM
    must never invent, and keep any X-ray Base64 image out of the text
    handed back to the LLM.
    """

    def __init__(self, mcp_client: MCPClient, tool_registry: ToolRegistry):
        self._mcp_client = mcp_client
        self._tool_registry = tool_registry

    async def __call__(self, state: ConsultationState) -> dict:
        last_message = state["messages"][-1]
        tool_messages: list[ToolMessage] = []
        xray_image_base64 = state.get("xray_image_base64")
        raw_tool_outputs = list(state.get("raw_tool_outputs") or [])
        insurance_number = state.get("insurance_number")

        for tool_call in last_message.tool_calls:
            text, image_base64, resolved_insurance_number = await self._execute(tool_call, state)
            if image_base64:
                xray_image_base64 = image_base64
            if resolved_insurance_number:
                insurance_number = resolved_insurance_number
            tool_messages.append(
                ToolMessage(content=text, tool_call_id=tool_call["id"])
            )
            raw_tool_outputs.append({"tool": tool_call["name"], "text": text})

        return {
            "messages": tool_messages,
            "xray_image_base64": xray_image_base64,
            "raw_tool_outputs": raw_tool_outputs,
            "insurance_number": insurance_number,
        }

    async def _execute(
        self, tool_call: dict, state: ConsultationState
    ) -> tuple[str, str | None, str | None]:
        tool_name = tool_call["name"]
        arguments = dict(tool_call["args"])

        if tool_name == XRAY_TOOL_NAME:
            temp_path = state.get("temp_path")
            if not temp_path:
                return (
                    "No X-ray image is available in this consultation yet. "
                    "Ask the doctor to upload one first.",
                    None,
                    None,
                )
            arguments["temp_path"] = temp_path
            return await self._call_mcp_tool(tool_name, arguments, resolved_insurance_number=None)

        if tool_name in _WRITE_TOOL_NAMES:
            insurance_number = state.get("insurance_number") or arguments.get("insuranceNumber")
            if not insurance_number:
                return (
                    "No patient is selected. Ask the doctor for the patient's "
                    "insurance number before adding this.",
                    None,
                    None,
                )

            if tool_name == ADD_LAB_REPORT_TOOL_NAME:
                temp_path = state.get("temp_path")
                if not temp_path:
                    return (
                        "No document was attached. Ask the doctor to attach the "
                        "lab report file.",
                        None,
                        insurance_number,
                    )
                text = await self._upload_lab_report(insurance_number, temp_path)
                return text, None, insurance_number

            arguments["insuranceNumber"] = insurance_number
            return await self._call_mcp_tool(tool_name, arguments, resolved_insurance_number=insurance_number)

        return await self._call_mcp_tool(tool_name, arguments, resolved_insurance_number=None)

    async def _call_mcp_tool(
        self, tool_name: str, arguments: dict, resolved_insurance_number: str | None
    ) -> tuple[str, str | None, str | None]:
        try:
            server_name = self._tool_registry.server_for_tool(tool_name)
            session = self._mcp_client.sessions[server_name]
            result = await session.call_tool(tool_name, arguments=arguments)
        except Exception as exc:
            return f"Tool '{tool_name}' could not be executed: {exc}", None, resolved_insurance_number

        if result.structuredContent and "result" in result.structuredContent:
            return (
                result.structuredContent["result"],
                result.structuredContent.get("image"),
                resolved_insurance_number,
            )
        return result.content[0].text, None, resolved_insurance_number

    @staticmethod
    async def _upload_lab_report(insurance_number: str, temp_path: str) -> str:
        """Sends the attached file to Backend's existing multipart upload
        endpoint directly - add_lab_report has no MCP tool of its own."""
        path = Path(temp_path)
        if not path.exists() or not path.is_file():
            return "Tool 'add_lab_report' could not be executed: attached file not found."

        content_type = _LAB_REPORT_MIME_TYPES.get(path.suffix.lower())
        if content_type is None:
            return (
                "Tool 'add_lab_report' could not be executed: only PDF, PNG, or "
                "JPG files are supported for lab reports."
            )

        url = f"{settings.backend_base_url}/api/labreport/upload/{insurance_number}"
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                files = {"file": (path.name, path.read_bytes(), content_type)}
                response = await client.post(url, files=files)
                response.raise_for_status()
                return response.text
        except httpx.HTTPStatusError as exc:
            return (
                f"Tool 'add_lab_report' could not be executed: Backend returned "
                f"{exc.response.status_code}: {exc.response.text}"
            )
        except Exception as exc:
            return f"Tool 'add_lab_report' could not be executed: {exc}"
