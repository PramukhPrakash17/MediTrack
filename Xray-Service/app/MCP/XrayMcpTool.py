from pathlib import Path
from PIL import Image, UnidentifiedImageError
from ..Service.Xray_Detection import XrayDetectionService
from fastmcp import FastMCP

from ..Service.ImageValidation import validate_img

from ..Model.Response.FinalResponse import XrayResponse
from ..Service.XrayExplantion import XrayExplanation

path = Path("app/Model/yolov8_1024_best.pt")

ALLOWED_TYPES = {".jpg", ".jpeg", ".png", ".jfif"}
mcp = FastMCP("XrayServer")
XrayExplanationObj = XrayExplanation()
xray_service = XrayDetectionService(path, XrayExplanationObj)


@mcp.tool()
async def analyze_xray(question: str, temp_path: str) -> XrayResponse:
    """
    Analyze an uploaded X-ray image for possible fracture regions.

    Use this tool only when an X-ray image has been uploaded and its
    temporary local path is available. Pass the doctor's complete
    question and the image path.

    Do not use this tool for symptom-only or medication-related questions.
    """
    path = Path(temp_path)
    if not path.exists():
        raise ValueError(f"Image was not found: {path}")

    if not path.is_file():
        raise ValueError(f"The supplied path is not a file: {path}")

    if path.suffix.lower() not in ALLOWED_TYPES:
        raise ValueError("Only JPG, JPEG and PNG X-ray images are supported.")

    content = path.read_bytes()
    img = validate_img(content)
    result = xray_service.analyze_image(question, img)
    return result


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8083)
