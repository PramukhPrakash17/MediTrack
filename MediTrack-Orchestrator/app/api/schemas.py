from pydantic import BaseModel


class NewPatientResponse(BaseModel):
    consultation_id: str


class ChatResponse(BaseModel):
    consultation_id: str
    reply: str
    xray_image_base64: str | None = None
    # Names of the tool(s) that actually ran this turn (e.g. ["add_medicine"]),
    # empty if none did. Lets the frontend know what changed without having
    # to parse `reply` - used to trigger ServicesPage's auto-refresh.
    tools_called: list[str] = []
