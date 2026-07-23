from ultralytics import YOLO


def main():
    model = YOLO(
        "C:/Users/pramu/Desktop/MediTrack/"
        "runs/detect/runs/fracture_baseline_v2/"
        "weights/best.pt"
    )

    metrics = model.val(
        data=(
            "C:/Users/pramu/Desktop/MediTrack/"
            "Xray-Service/data/yolo_dataset/dataset.yaml"
        ),
        split="test",
        imgsz=640,
        batch=4,
        device=0,
        workers=0,
        plots=True,
        project=(
            "C:/Users/pramu/Desktop/MediTrack/"
            "Xray-Service/training_results"
        ),
        name="fracture_baseline_test",
    )

    print("\n======= TEST RESULTS =======")
    print(f"Precision: {metrics.box.mp * 100:.2f}%")
    print(f"Recall: {metrics.box.mr * 100:.2f}%")
    print(f"mAP50: {metrics.box.map50 * 100:.2f}%")
    print(f"mAP50-95: {metrics.box.map * 100:.2f}%")


if __name__ == "__main__":
    main()