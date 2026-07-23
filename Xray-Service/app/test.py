# print(__name__)
# from fastapi import FastAPI

# app = FastAPI()

# @app.get('/hello')
# def hello():
#     print("Hello World")
#     return{"message":"Hello"}  

from ultralytics import YOLO
from pathlib import Path

model_path = Path("C:/Users/pramu/Desktop/MediTrack/Xray-Service/models/production/yolov8_1024_best.pt")
model = YOLO(model_path)
# print(model)
print("model loaded successfully")
result = model.predict(source="app/test images/451_Simple Bone Fracture_original.jpg",imgsz=1024)

print(f"Boxes: {result[0].boxes}")
print("Names : " +str(result[0].names))
result[0].orig_shape
result[0].speed

prediction = result[0]
prediction.save(filename="app/outputs/fracture_result3.jpg")