from typing import Annotated, Optional, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class ConsultationState(TypedDict):
    """State carried through one consultation's LangGraph run.

    Persisted per consultation by the graph's checkpointer (keyed on
    consultation_id), so temp_path and prior tool results are still there
    for follow-up questions without the doctor re-uploading anything.
    """

    messages: Annotated[list[BaseMessage], add_messages]
    temp_path: Optional[str]
    xray_image_base64: Optional[str]
    raw_tool_outputs: Optional[list[dict]]
    insurance_number: Optional[str]
