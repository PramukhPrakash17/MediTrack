from pathlib import Path
from ultralytics import YOLO
import base64
from PIL import Image
from io import BytesIO
from ..Model.Response.YOLO_Response import YoloResponse
from .XrayExplantion import XrayExplanation
from ..Model.Response.FinalResponse import XrayResponse


class XrayDetectionService:
    def __init__(self, model_path: Path, xrayExplnationObj: XrayExplanation):
        self.model_path = model_path
        self.model = YOLO(self.model_path)
        self.explantionObj = xrayExplnationObj
        print("model Loaded Successfully")

    def analyze_image(self, question: str, image: Image):
        results = self.model(image)
        prediction = results[0]
        detection_count = len(prediction.boxes)
        if detection_count > 0:
            highest_confidence = float(prediction.boxes.conf.max().item())
            annotatedImage = prediction.plot()
            img = self.serialize_image(annotatedImage)
            response = YoloResponse(
                fractureDetected=True,
                highestConfidence=round(highest_confidence, 4),
                suspiciousRegions=detection_count,
                image=img,
            )

        else:
            response = YoloResponse(
                fractureDetected=False,
                highestConfidence=None,
                suspiciousRegions=0,
                image=None,
            )

        yolo_result = str(
            f"Fracture detected: {response.fractureDetected}\n"
            f"Highest confidence: {response.highestConfidence}\n"
            f"Suspicious regions: {response.suspiciousRegions}"
        )

        llm_result = self.explantionObj.generate_response(question, yolo_result)
        final_response = XrayResponse(result=llm_result, image=response.image)
        return final_response

    def serialize_image(self, annotatedImage):
        print(type(annotatedImage))
        rgb_image = annotatedImage[:, :, ::-1]
        pil_image = Image.fromarray(rgb_image)
        buffer = BytesIO()
        pil_image.save(buffer, format="JPEG", quality=95)
        image_bytes = buffer.getvalue()
        base64_bytes = base64.b64encode(image_bytes)
        img = base64_bytes.decode("ascii")
        buffer.close()
        return img
