from io import BytesIO

from PIL import Image, UnidentifiedImageError
from fastapi import HTTPException


def validate_img(data: bytes):

    content = data

    if not content:
        raise ValueError("File is empty.")

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
