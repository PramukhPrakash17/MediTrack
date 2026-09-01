from ultralytics import YOLO


DATASET_YAML = "/content/dataset.yaml"

RESULTS_DIR = (
    "/content/drive/MyDrive/MediTrack/"
    "training_results"
)

EXPERIMENT_NAME = "exp03_combined_yolov8n_640"


model = YOLO("yolov8n.pt")

model.train(
    data=DATASET_YAML,

    epochs=100,
    imgsz=640,
    batch=16,

    device=0,
    workers=2,

    patience=20,
    seed=42,
    deterministic=True,

    pretrained=True,
    amp=True,
    cache=False,

    save=True,
    save_period=5,
    plots=True,
    val=True,

    project=RESULTS_DIR,
    name=EXPERIMENT_NAME,
    exist_ok=False,

    verbose=True
)