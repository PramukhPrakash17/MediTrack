from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from langchain_core.messages import HumanMessage

from app.api.schemas import ChatResponse, NewPatientResponse

router = APIRouter()

# Now carries either an X-ray image or a lab-report document - which one it
# is gets decided by the doctor's wording, not the file extension (see the
# system prompt's attachment-routing rule).
ALLOWED_ATTACHMENT_TYPES = {".jpg", ".jpeg", ".png", ".jfif", ".pdf"}


@router.post("/new-patient", response_model=NewPatientResponse)
async def new_patient(request: Request):
    """Ends the current consultation and starts a fresh, empty one."""
    session_manager = request.app.state.session_manager
    consultation_id = session_manager.start_new_consultation()
    return NewPatientResponse(consultation_id=consultation_id)


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: Request,
    message: str = Form(...),
    attachment: UploadFile | None = File(None),
    insurance_number: str | None = Form(None),
):
    session_manager = request.app.state.session_manager
    graph = request.app.state.graph
    consultation_id = session_manager.current_consultation_id()

    # Reset every turn: an X-ray image should only come back in the response
    # for the turn that actually produced it, not ride along on later,
    # unrelated questions. The tool node still carries it forward correctly
    # across multiple tool hops *within* this same turn.
    graph_input: dict = {
        "messages": [HumanMessage(content=message)],
        "xray_image_base64": None,
        "raw_tool_outputs": [],
    }

    if attachment is not None:
        suffix = Path(attachment.filename or "").suffix.lower()
        if suffix not in ALLOWED_ATTACHMENT_TYPES:
            raise HTTPException(
                status_code=400,
                detail="Only JPG, JPEG, PNG X-ray images or PDF lab reports are supported.",
            )
        temp_path = session_manager.save_upload(attachment.filename, await attachment.read())
        graph_input["temp_path"] = str(temp_path)

    # Only set when the frontend actually sent one, so an already-known
    # patient from earlier in this consultation isn't clobbered by a turn
    # that didn't include it (same reasoning as temp_path above).
    if insurance_number:
        graph_input["insurance_number"] = insurance_number

    config = {"configurable": {"thread_id": consultation_id}}
    result_state = await graph.ainvoke(graph_input, config=config)

    raw_outputs = result_state.get("raw_tool_outputs") or []
    return ChatResponse(
        consultation_id=consultation_id,
        reply=_build_reply(result_state),
        xray_image_base64=result_state.get("xray_image_base64"),
        tools_called=[o["tool"] for o in raw_outputs],
    )


def _build_reply(result_state: dict) -> str:
    """Prefer the raw tool output(s) from this turn over the agent's rephrased
    answer, so doctors see exactly what the RAG/X-ray services returned."""
    raw_outputs = result_state.get("raw_tool_outputs") or []
    if not raw_outputs:
        return result_state["messages"][-1].content
    return "\n\n".join(o["text"] for o in raw_outputs)
