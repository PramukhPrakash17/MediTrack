from io import BytesIO

import cv2
import numpy as np
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

    return preprocess_xray(img)


def preprocess_xray(img: Image) -> Image:
    """Normalize photographed/scanned X-rays toward the grayscale,
    high-contrast look of the clean radiograph exports the model was
    trained on (strips color tint, evens out lighting/glare)."""

    rgb_array = np.array(img)
    gray_array = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2GRAY)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    equalized = clahe.apply(gray_array)

    rgb_equalized = cv2.cvtColor(equalized, cv2.COLOR_GRAY2RGB)
    return Image.fromarray(rgb_equalized)
