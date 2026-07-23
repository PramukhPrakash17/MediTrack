from pathlib import Path

yolo_path=Path("C:/Users/pramu/Desktop/MediTrack/Xray-Service/data/FracAtlas/Annotations/YOLO")

def main():
    print("Yolo validation Started")
    print("====== SUMMARY ======")

label_files = list(yolo_path.glob("*.txt"))
print(f"Total YOLO label files: {len(label_files)}")

empty_label_files = 0
non_empty_label_files = 0
bounding_boxes = 0

for label_file in label_files:
    content = label_file.read_text().strip()

    if content != "":
        lines = content.splitlines()

        for line_number, line in enumerate(lines, start=1):
            parts = line.split()

            if len(parts) != 5:
                raise ValueError(
                    f"{label_file.name}, line {line_number}: "
                    f"Expected 5 values, found {len(parts)}"
                )

            try:
                class_id = int(parts[0])
                x_center = float(parts[1])
                y_center = float(parts[2])
                width = float(parts[3])
                height = float(parts[4])
            except ValueError:
                raise ValueError(
                    f"{label_file.name}, line {line_number}: "
                    f"All annotation values must be numeric"
                )

            if class_id != 0:
                raise ValueError(
                    f"{label_file.name}, line {line_number}: "
                    f"Invalid class ID {class_id}"
                )

            if not 0 <= x_center <= 1:
                raise ValueError(
                    f"{label_file.name}, line {line_number}: "
                    f"x_center must be between 0 and 1"
                )

            if not 0 <= y_center <= 1:
                raise ValueError(
                    f"{label_file.name}, line {line_number}: "
                    f"y_center must be between 0 and 1"
                )

            if not 0 < width <= 1:
                raise ValueError(
                    f"{label_file.name}, line {line_number}: "
                    f"width must be greater than 0 and at most 1"
                )

            if not 0 < height <= 1:
                raise ValueError(
                    f"{label_file.name}, line {line_number}: "
                    f"height must be greater than 0 and at most 1"
                )

        bounding_boxes += len(lines)
        non_empty_label_files += 1

    else:
        empty_label_files += 1

print(f"Empty label files: {empty_label_files}")
print(f"Non-empty label files: {non_empty_label_files}")
print(f"Total bounding boxes: {bounding_boxes}")
if __name__== "__main__" :
    main()
    print("====SUMMARY-END==========")
