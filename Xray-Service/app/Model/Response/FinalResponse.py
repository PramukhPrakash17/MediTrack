from pydantic import BaseModel
from typing import Optional


class XrayResponse(BaseModel):
    result: str
    image: str | None = None
