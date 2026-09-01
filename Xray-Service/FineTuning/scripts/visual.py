from pathlib import Path
import random

from PIL import Image, ImageDraw, ImageFont


# ============================================================
# CONFIGURATION
# ============================================================

YOLO_DATASET_ROOT = Path(
    "C:/Users/pramu/Desktop/MediTrack/Xray-Service/data/yolo_dataset"
)

OUTPUT_FOLDER = YOLO_DATASET_ROOT / "fracture_annotation_preview"

SAMPLES_PER_SPLIT = 5
RANDOM_SEED = 42

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
}

CLASS_NAMES = {
    0: "fracture",
}


# ============================================================
# READ YOLO LABELS
# ============================================================

def read_yolo_labels(label_path):
    """
    Reads a YOLO label file.

    Expected format:
    class_id x_center y_center width height

    Example:
    0 0.545380 0.446370 0.154703 0.046205
    """

    annotations = []

    if not label_path.exists():
        print(f"Missing label file: {label_path}")
        return annotations

    label_content = label_path.read_text(
        encoding="utf-8"
    ).strip()

    # Empty label file means no fracture annotation
    if not label_content:
        return annotations

    for line_number, line in enumerate(
        label_content.splitlines(),
        start=1,
    ):
        values = line.strip().split()

        if len(values) != 5:
            print(
                f"Invalid label format: {label_path}, "
                f"line {line_number}: {line}"
            )
            continue

        try:
            class_id = int(values[0])
            x_center = float(values[1])
            y_center = float(values[2])
            box_width = float(values[3])
            box_height = float(values[4])

        except ValueError:
            print(
                f"Invalid numeric values: {label_path}, "
                f"line {line_number}: {line}"
            )
            continue

        coordinates = [
            x_center,
            y_center,
            box_width,
            box_height,
        ]

        if not all(0 <= value <= 1 for value in coordinates):
            print(
                f"Coordinates outside 0-1 range: "
                f"{label_path}, line {line_number}: {line}"
            )
            continue

        annotations.append(
            {
                "class_id": class_id,
                "x_center": x_center,
                "y_center": y_center,
                "width": box_width,
                "height": box_height,
            }
        )

    return annotations


# ============================================================
# CONVERT YOLO COORDINATES TO PIXEL COORDINATES
# ============================================================

def yolo_to_pixel_coordinates(
    annotation,
    image_width,
    image_height,
):
    """
    Converts YOLO normalized coordinates:

    x_center, y_center, width, height

    into pixel coordinates:

    x_min, y_min, x_max, y_max
    """

    x_center_pixel = (
        annotation["x_center"] * image_width
    )

    y_center_pixel = (
        annotation["y_center"] * image_height
    )

    box_width_pixel = (
        annotation["width"] * image_width
    )

    box_height_pixel = (
        annotation["height"] * image_height
    )

    x_min = x_center_pixel - box_width_pixel / 2
    y_min = y_center_pixel - box_height_pixel / 2

    x_max = x_center_pixel + box_width_pixel / 2
    y_max = y_center_pixel + box_height_pixel / 2

    # Keep coordinates inside image boundaries
    x_min = max(0, min(x_min, image_width - 1))
    y_min = max(0, min(y_min, image_height - 1))

    x_max = max(0, min(x_max, image_width - 1))
    y_max = max(0, min(y_max, image_height - 1))

    return (
        int(round(x_min)),
        int(round(y_min)),
        int(round(x_max)),
        int(round(y_max)),
    )


# ============================================================
# LOAD FONT
# ============================================================

def load_font(size):
    """
    Tries to load Arial.
    Falls back to the default PIL font.
    """

    try:
        return ImageFont.truetype(
            "arial.ttf",
            size=size,
        )
    except OSError:
        return ImageFont.load_default()


# ============================================================
# DRAW CLASS LABEL
# ============================================================

def draw_class_label(
    draw,
    box,
    label_text,
):
    """
    Draws the class name near the bounding box.
    """

    x_min, y_min, _, _ = box

    font = load_font(20)

    text_box = draw.textbbox(
        (x_min, y_min),
        label_text,
        font=font,
    )

    text_width = text_box[2] - text_box[0]
    text_height = text_box[3] - text_box[1]

    text_y = max(
        0,
        y_min - text_height - 10,
    )

    draw.rectangle(
        [
            x_min,
            text_y,
            x_min + text_width + 10,
            text_y + text_height + 10,
        ],
        fill="red",
    )

    draw.text(
        (
            x_min + 5,
            text_y + 5,
        ),
        label_text,
        fill="white",
        font=font,
    )


# ============================================================
# ANNOTATE ONE IMAGE
# ============================================================

def annotate_image(
    image_path,
    label_path,
    output_path,
):
    """
    Opens one image, reads its YOLO labels,
    draws all fracture bounding boxes,
    and saves the annotated image.
    """

    try:
        with Image.open(image_path) as source_image:
            image = source_image.convert("RGB")

    except Exception as error:
        print(f"Could not open image: {image_path}")
        print(f"Reason: {error}")
        return False

    image_width, image_height = image.size

    annotations = read_yolo_labels(label_path)

    if not annotations:
        print(
            f"No valid fracture annotations found: "
            f"{label_path}"
        )
        return False

    draw = ImageDraw.Draw(image)

    for annotation in annotations:
        box = yolo_to_pixel_coordinates(
            annotation,
            image_width,
            image_height,
        )

        class_id = annotation["class_id"]

        class_name = CLASS_NAMES.get(
            class_id,
            f"class_{class_id}",
        )

        draw.rectangle(
            box,
            outline="red",
            width=4,
        )

        draw_class_label(
            draw,
            box,
            class_name,
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    image.save(output_path)

    print(
        f"Saved: {output_path} | "
        f"Bounding boxes: {len(annotations)}"
    )

    return True


# ============================================================
# FIND FRACTURED IMAGES
# ============================================================

def get_fractured_images(split_name):
    """
    Returns only images that have a non-empty
    and valid YOLO label file.
    """

    image_folder = (
        YOLO_DATASET_ROOT
        / "images"
        / split_name
    )

    label_folder = (
        YOLO_DATASET_ROOT
        / "labels"
        / split_name
    )

    if not image_folder.exists():
        print(
            f"Image folder does not exist: "
            f"{image_folder}"
        )
        return []

    if not label_folder.exists():
        print(
            f"Label folder does not exist: "
            f"{label_folder}"
        )
        return []

    fractured_images = []

    for image_path in image_folder.iterdir():

        if not image_path.is_file():
            continue

        if image_path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue

        label_name = (
            image_path
            .with_suffix(".txt")
            .name
        )

        label_path = (
            label_folder
            / label_name
        )

        if not label_path.exists():
            print(f"Missing label: {label_path}")
            continue

        label_content = label_path.read_text(
            encoding="utf-8"
        ).strip()

        # Empty file means no fracture bounding box
        if not label_content:
            continue

        annotations = read_yolo_labels(label_path)

        if annotations:
            fractured_images.append(image_path)

    return sorted(fractured_images)


# ============================================================
# PROCESS ONE SPLIT
# ============================================================

def process_split(
    split_name,
    samples_per_split,
):
    """
    Randomly selects only fractured images
    from one split and creates annotation previews.
    """

    fractured_images = get_fractured_images(
        split_name
    )

    if not fractured_images:
        print(
            f"No fractured images found in "
            f"{split_name}"
        )

        return {
            "fractured_available": 0,
            "selected": 0,
            "saved": 0,
            "failed": 0,
        }

    number_of_samples = min(
        samples_per_split,
        len(fractured_images),
    )

    selected_images = random.sample(
        fractured_images,
        number_of_samples,
    )

    label_folder = (
        YOLO_DATASET_ROOT
        / "labels"
        / split_name
    )

    split_output_folder = (
        OUTPUT_FOLDER
        / split_name
    )

    saved_count = 0
    failed_count = 0

    print(
        f"\n======= PROCESSING FRACTURED "
        f"{split_name.upper()} IMAGES ======="
    )

    print(
        f"Fractured images available: "
        f"{len(fractured_images)}"
    )

    for image_path in selected_images:

        label_name = (
            image_path
            .with_suffix(".txt")
            .name
        )

        label_path = (
            label_folder
            / label_name
        )

        output_name = (
            f"{image_path.stem}_annotated.jpg"
        )

        output_path = (
            split_output_folder
            / output_name
        )

        success = annotate_image(
            image_path,
            label_path,
            output_path,
        )

        if success:
            saved_count += 1
        else:
            failed_count += 1

    print(
        f"\n======= {split_name.upper()} SUMMARY ======="
    )

    print(
        f"Fractured images available: "
        f"{len(fractured_images)}"
    )

    print(
        f"Selected fractured images: "
        f"{number_of_samples}"
    )

    print(f"Saved previews: {saved_count}")
    print(f"Failed previews: {failed_count}")

    return {
        "fractured_available": len(fractured_images),
        "selected": number_of_samples,
        "saved": saved_count,
        "failed": failed_count,
    }


# ============================================================
# MAIN
# ============================================================

def main():
    random.seed(RANDOM_SEED)

    OUTPUT_FOLDER.mkdir(
        parents=True,
        exist_ok=True,
    )

    results = {}

    for split_name in [
        "train",
        "val",
        "test",
    ]:
        results[split_name] = process_split(
            split_name,
            SAMPLES_PER_SPLIT,
        )

    print(
        "\n======= FINAL FRACTURE ANNOTATION "
        "PREVIEW SUMMARY ======="
    )

    total_available = 0
    total_selected = 0
    total_saved = 0
    total_failed = 0

    for split_name, result in results.items():

        print(
            f"{split_name}: "
            f"fractured_available="
            f"{result['fractured_available']}, "
            f"selected={result['selected']}, "
            f"saved={result['saved']}, "
            f"failed={result['failed']}"
        )

        total_available += (
            result["fractured_available"]
        )

        total_selected += result["selected"]
        total_saved += result["saved"]
        total_failed += result["failed"]

    print(
        f"\nTotal fractured images available: "
        f"{total_available}"
    )

    print(f"Total selected: {total_selected}")
    print(f"Total saved: {total_saved}")
    print(f"Total failed: {total_failed}")

    print(
        f"\nAnnotated fractured images are saved in:\n"
        f"{OUTPUT_FOLDER}"
    )


if __name__ == "__main__":
    main()