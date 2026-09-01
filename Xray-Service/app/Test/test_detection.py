import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.append(str(APP_ROOT))

from Xray_Detection import XrayDetectionService

path = APP_ROOT / "Model" / "yolov8_1024_best.pt"
image_path = APP_ROOT / "Upload" / "Test_image.jpg"
service = XrayDetectionService(path)
print("New class called successfully")
service.analyze_image(image_path)
