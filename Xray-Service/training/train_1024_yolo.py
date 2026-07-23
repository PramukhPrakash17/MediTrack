from ultralytics import YOLO


DATASET_YAML = "/content/dataset.yaml"

RESULTS_DIR = (
    "/content/drive/MyDrive/MediTrack/"
    "training_results"
)

EXPERIMENT_NAME = "exp04_combined_yolov8n_1024"


model = YOLO("yolov8n.pt")

model.train(
    data=DATASET_YAML,

    epochs=100,
    imgsz=1024,
    batch=8,
    device=0,
    workers=4,
    patience=20,
    seed=42,
    pretrained=True,
    amp=True,
    save=True,
    save_period=5,
    plots=True,
    val=True,
    project=RESULTS_DIR,
    name=EXPERIMENT_NAME,
    exist_ok=False,
    verbose=True
)