from pathlib import Path

from ultralytics import YOLO


PROJECT_ROOT = Path(
    "C:/Users/pramu/Desktop/MediTrack/Xray-Service"
)

DATASET_YAML = (
    PROJECT_ROOT
    / "data"
    / "yolo_dataset"
    / "dataset.yaml"
)

PRETRAINED_MODEL = (
    PROJECT_ROOT
    / "models"
    / "pretrained"
    / "yolov8n.pt"
)

TRAINING_RESULTS = (
    PROJECT_ROOT
    / "training_results"
)


def main():
    model = YOLO(str(PRETRAINED_MODEL))

    model.train(
        data=str(DATASET_YAML),
        epochs=100,
        imgsz=1024,
        batch=2,
        device=0,
        patience=20,
        workers=0,
        seed=42,
        deterministic=True,
        plots=True,
        save=True,
        amp=True,

        project=str(TRAINING_RESULTS),
        name="exp02_yolov8n_1024",
        exist_ok=False,
    )


if __name__ == "__main__":
    main()