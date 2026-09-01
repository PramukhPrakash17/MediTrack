from pydantic import BaseModel
from typing import Optional


class YoloResponse(BaseModel):
    fractureDetected: bool
    highestConfidence: float | None = None
    suspiciousRegions: int
    image: str | None = None
