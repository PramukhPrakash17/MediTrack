from fastapi import File, Form, UploadFile, HTTPException, APIRouter
from PIL import Image, UnidentifiedImageError
from io import BytesIO
from ..Service.Xray_Detection import XrayDetectionService
from pathlib import Path
from ..Model.Response.FinalResponse import XrayResponse
from ..Service.XrayExplantion import XrayExplanation

router = APIRouter(prefix="/api/v1/xray", tags=["Xray Analysis"])


ALLOWED_TYPES = ["image/jpeg", "image/png"]
path = Path("app/Model/yolov8_1024_best.pt")

XrayExplanationObj = XrayExplanation()
xray_service = XrayDetectionService(path, XrayExplanationObj)


@router.post("/analyze", response_model=XrayResponse)
async def xray(question: str = Form(...), file: UploadFile = File(...)):
    # checking if the message is valid or not.
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail=f"File type {file.content_type} is not allowed.")
    content = await file.read()
    try:
        img = validate_img(content)
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error
    result = xray_service.analyze_image(question, img)
    return result


async def validate_img(bytes: bytes):

    content = bytes

    if not content:
        raise HTTPException(status_code=400, detail="File is empty.")

    buffer = BytesIO(content)

    try:
        with Image.open(buffer) as image:
            image.verify()

        buffer.seek(0)

        with Image.open(buffer) as image:
            img = image.convert("RGB")

    except (UnidentifiedImageError, OSError):
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is corrupted or is not a valid image.",
        )
    return img
