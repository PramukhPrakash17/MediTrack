from __future__ import annotations

import argparse
import csv
import json
import shutil
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

from PIL import Image, ImageFile


# =============================================================================
# FIXED PROJECT PATHS
# =============================================================================

PROJECT_ROOT = Path(
    "C:/Users/pramu/Desktop/MediTrack/Xray-Service"
)

# Existing one-class FracAtlas dataset:
#
# data/yolo_dataset/
# ├── images/{train,val,test}
# ├── labels/{train,val,test}
# └── dataset.yaml
FRACATLAS_ROOT = (
    PROJECT_ROOT
    / "data"
    / "yolo_dataset"
)

# GRAZ NDJSON manifest:
#
# data/GRAZPEDWRI-DX/grazpedwri-dx.ndjson
GRAZ_NDJSON = (
    PROJECT_ROOT
    / "data"
    / "GRAZPEDWRI-DX"
    / "grazpedwri-dx.ndjson"
)

# New combined dataset:
#
# data/combined_yolo_dataset/
COMBINED_ROOT = (
    PROJECT_ROOT
    / "data"
    / "combined_yolo_dataset"
)


# =============================================================================
# DATASET CONFIGURATION
# =============================================================================

SPLITS = ("train", "val", "test")

IMAGE_SUFFIXES = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
}

# Prefixes prevent filename collisions between the two datasets.
FRAC_PREFIX = "frac_"
GRAZ_PREFIX = "graz_"

# The final combined dataset contains only one class.
TARGET_CLASS_ID = 0
TARGET_CLASS_NAME = "fracture"

# Safe defaults for the GRAZ download server.
DEFAULT_WORKERS = 2
DEFAULT_RETRIES = 10
DEFAULT_TIMEOUT_SECONDS = 180
DEFAULT_RETRY_DELAY_SECONDS = 5

# Progress is printed after this many completed GRAZ records.
PROGRESS_INTERVAL = 250


# =============================================================================
# DATA TYPES
# =============================================================================

@dataclass(frozen=True)
class GrazRecord:
    split: str
    filename: str
    url: str
    width: int
    height: int
    fracture_boxes: tuple[
        tuple[float, float, float, float],
        ...
    ]


@dataclass(frozen=True)
class OutputRecord:
    image_id: str
    source: str
    split: str
    source_file: str
    output_file: str
    image_path: str
    label_path: str
    fractured: int
    fracture_count: int


@dataclass(frozen=True)
class DownloadResult:
    record: OutputRecord
    status: str
    error: str = ""


# =============================================================================
# PATH HELPERS
# =============================================================================

def images_dir(root: Path, split: str) -> Path:
    return root / "images" / split


def labels_dir(root: Path, split: str) -> Path:
    return root / "labels" / split


def splits_dir(root: Path) -> Path:
    return root / "splits"


def create_output_structure(fresh: bool) -> None:
    """
    Create exactly this structure:

    combined_yolo_dataset/
    ├── images/
    │   ├── train/
    │   ├── val/
    │   └── test/
    ├── labels/
    │   ├── train/
    │   ├── val/
    │   └── test/
    └── splits/
        ├── train.csv
        ├── val.csv
        └── test.csv
    """
    if fresh and COMBINED_ROOT.exists():
        print(
            "Deleting existing combined dataset:\n"
            f"  {COMBINED_ROOT}"
        )
        shutil.rmtree(COMBINED_ROOT)

    COMBINED_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    for split in SPLITS:
        images_dir(
            COMBINED_ROOT,
            split,
        ).mkdir(
            parents=True,
            exist_ok=True,
        )

        labels_dir(
            COMBINED_ROOT,
            split,
        ).mkdir(
            parents=True,
            exist_ok=True,
        )

    splits_dir(COMBINED_ROOT).mkdir(
        parents=True,
        exist_ok=True,
    )

    # Remove abandoned temporary files from a previous interrupted run.
    for temporary_file in COMBINED_ROOT.rglob("*.part"):
        temporary_file.unlink(missing_ok=True)


# =============================================================================
# IMAGE AND LABEL VALIDATION
# =============================================================================

def strict_image_is_valid(
    image_path: Path,
    expected_width: int | None = None,
    expected_height: int | None = None,
) -> bool:
    """
    Fully decode an image and optionally verify its dimensions.
    Truncated files are rejected.
    """
    if (
        not image_path.exists()
        or not image_path.is_file()
        or image_path.stat().st_size == 0
    ):
        return False

    previous_setting = (
        ImageFile.LOAD_TRUNCATED_IMAGES
    )
    ImageFile.LOAD_TRUNCATED_IMAGES = False

    try:
        with Image.open(image_path) as image:
            image.load()

            if (
                expected_width is not None
                and image.width != expected_width
            ):
                return False

            if (
                expected_height is not None
                and image.height != expected_height
            ):
                return False

        return True

    except Exception:
        return False

    finally:
        ImageFile.LOAD_TRUNCATED_IMAGES = (
            previous_setting
        )


def valid_yolo_box(
    x_center: float,
    y_center: float,
    width: float,
    height: float,
) -> bool:
    return (
        0.0 <= x_center <= 1.0
        and 0.0 <= y_center <= 1.0
        and 0.0 < width <= 1.0
        and 0.0 < height <= 1.0
    )


def read_and_validate_one_class_label(
    label_path: Path,
) -> tuple[
    tuple[float, float, float, float],
    ...
]:
    """
    Validate a one-class YOLO label.

    Valid line:
        0 x_center y_center width height

    An empty file is valid and means background/no fracture.
    """
    if not label_path.exists():
        raise FileNotFoundError(
            f"Missing label file: {label_path}"
        )

    boxes: list[
        tuple[float, float, float, float]
    ] = []

    lines = label_path.read_text(
        encoding="utf-8"
    ).splitlines()

    for line_number, raw_line in enumerate(
        lines,
        start=1,
    ):
        line = raw_line.strip()

        if not line:
            continue

        parts = line.split()

        if len(parts) != 5:
            raise ValueError(
                f"Invalid YOLO label in {label_path}, "
                f"line {line_number}: {raw_line!r}"
            )

        try:
            class_id = int(float(parts[0]))
            x_center = float(parts[1])
            y_center = float(parts[2])
            box_width = float(parts[3])
            box_height = float(parts[4])

        except ValueError as error:
            raise ValueError(
                f"Non-numeric YOLO label in {label_path}, "
                f"line {line_number}: {raw_line!r}"
            ) from error

        if class_id != TARGET_CLASS_ID:
            raise ValueError(
                f"{label_path} contains class {class_id}. "
                "Only class 0 = fracture is allowed."
            )

        if not valid_yolo_box(
            x_center,
            y_center,
            box_width,
            box_height,
        ):
            raise ValueError(
                f"Invalid normalized YOLO box in "
                f"{label_path}, line {line_number}: "
                f"{raw_line!r}"
            )

        boxes.append(
            (
                x_center,
                y_center,
                box_width,
                box_height,
            )
        )

    return tuple(boxes)


def write_label_atomically(
    label_path: Path,
    boxes: tuple[
        tuple[float, float, float, float],
        ...
    ],
) -> None:
    """
    Write class 0 fracture boxes.

    If boxes is empty, an empty .txt file is created.
    """
    lines = [
        (
            f"{TARGET_CLASS_ID} "
            f"{x_center:.6f} "
            f"{y_center:.6f} "
            f"{box_width:.6f} "
            f"{box_height:.6f}"
        )
        for (
            x_center,
            y_center,
            box_width,
            box_height,
        ) in boxes
    ]

    content = "\n".join(lines)

    if content:
        content += "\n"

    temporary_path = (
        label_path.parent
        / f"{label_path.name}.tmp"
    )

    temporary_path.write_text(
        content,
        encoding="utf-8",
    )

    temporary_path.replace(label_path)


# =============================================================================
# INPUT VALIDATION
# =============================================================================

def validate_input_structure() -> None:
    if not FRACATLAS_ROOT.exists():
        raise FileNotFoundError(
            "FracAtlas YOLO dataset was not found:\n"
            f"  {FRACATLAS_ROOT}"
        )

    for split in SPLITS:
        source_images = images_dir(
            FRACATLAS_ROOT,
            split,
        )
        source_labels = labels_dir(
            FRACATLAS_ROOT,
            split,
        )

        if not source_images.exists():
            raise FileNotFoundError(
                f"Missing FracAtlas image folder: "
                f"{source_images}"
            )

        if not source_labels.exists():
            raise FileNotFoundError(
                f"Missing FracAtlas label folder: "
                f"{source_labels}"
            )

    if not GRAZ_NDJSON.exists():
        raise FileNotFoundError(
            "GRAZ NDJSON manifest was not found:\n"
            f"  {GRAZ_NDJSON}"
        )


# =============================================================================
# GRAZ MANIFEST READING
# =============================================================================

def find_fracture_class_id(
    metadata: dict[str, Any],
) -> int:
    class_names = metadata.get(
        "class_names"
    )

    if not isinstance(class_names, dict):
        raise ValueError(
            "The GRAZ metadata has no "
            "'class_names' dictionary."
        )

    matching_ids = [
        int(class_id)
        for class_id, class_name
        in class_names.items()
        if str(class_name).strip().lower()
        == TARGET_CLASS_NAME
    ]

    if len(matching_ids) != 1:
        raise ValueError(
            "Expected exactly one GRAZ class "
            f"named '{TARGET_CLASS_NAME}', "
            f"but found IDs: {matching_ids}"
        )

    return matching_ids[0]


def print_and_check_url_expiry(
    records: list[GrazRecord],
) -> None:
    expiries: list[int] = []

    for record in records:
        query_parameters = parse_qs(
            urlparse(record.url).query
        )

        for raw_expiry in query_parameters.get(
            "Expires",
            [],
        ):
            try:
                expiries.append(
                    int(raw_expiry)
                )
            except ValueError:
                continue

    if not expiries:
        print(
            "No signed URL expiry value was "
            "found in the manifest."
        )
        return

    earliest_expiry = datetime.fromtimestamp(
        min(expiries),
        tz=timezone.utc,
    )

    print(
        "Earliest signed GRAZ URL expiry: "
        f"{earliest_expiry.isoformat()}"
    )

    if earliest_expiry <= datetime.now(
        timezone.utc
    ):
        raise RuntimeError(
            "The GRAZ image URLs have expired. "
            "Download a fresh "
            "grazpedwri-dx.ndjson file."
        )


def load_graz_manifest() -> tuple[
    dict[str, Any],
    int,
    list[GrazRecord],
]:
    """
    Read all GRAZ records, detect the fracture class by name,
    retain only fracture boxes, and preserve the supplied split.
    """
    records: list[GrazRecord] = []
    seen_filenames: set[str] = set()
    seen_stems: set[str] = set()

    with GRAZ_NDJSON.open(
        "r",
        encoding="utf-8",
    ) as manifest_file:
        first_line = (
            manifest_file.readline().strip()
        )

        if not first_line:
            raise ValueError(
                "The GRAZ NDJSON file is empty."
            )

        metadata = json.loads(first_line)

        if metadata.get("type") != "dataset":
            raise ValueError(
                "The first NDJSON line must be "
                "the dataset metadata record."
            )

        if metadata.get("task") != "detect":
            raise ValueError(
                "The GRAZ manifest is not an "
                "object-detection dataset."
            )

        fracture_class_id = (
            find_fracture_class_id(metadata)
        )

        for line_number, raw_line in enumerate(
            manifest_file,
            start=2,
        ):
            raw_line = raw_line.strip()

            if not raw_line:
                continue

            try:
                item = json.loads(raw_line)

            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid JSON on NDJSON line "
                    f"{line_number}: {error}"
                ) from error

            if item.get("type") != "image":
                continue

            split = str(
                item.get("split", "")
            ).strip().lower()

            if split not in SPLITS:
                raise ValueError(
                    f"Unsupported split {split!r} "
                    f"on NDJSON line {line_number}."
                )

            filename = Path(
                str(item.get("file", ""))
            ).name

            url = str(
                item.get("url", "")
            ).strip()

            width = int(
                item.get("width", 0)
            )
            height = int(
                item.get("height", 0)
            )

            if not filename:
                raise ValueError(
                    f"Missing filename on NDJSON "
                    f"line {line_number}."
                )

            if filename in seen_filenames:
                raise ValueError(
                    "Duplicate filename in GRAZ "
                    f"manifest: {filename}"
                )

            filename_stem = Path(filename).stem

            if filename_stem in seen_stems:
                raise ValueError(
                    "Two GRAZ images would map to the same YOLO "
                    f"label filename: {filename_stem}.txt"
                )

            seen_filenames.add(filename)
            seen_stems.add(filename_stem)

            if not url:
                raise ValueError(
                    f"Missing URL on NDJSON line "
                    f"{line_number}."
                )

            if width <= 0 or height <= 0:
                raise ValueError(
                    f"Invalid image size for {filename}: "
                    f"{width}x{height}"
                )

            fracture_boxes: list[
                tuple[
                    float,
                    float,
                    float,
                    float,
                ]
            ] = []

            annotations = (
                item.get("annotations", {})
                or {}
            )

            source_boxes = (
                annotations.get("boxes", [])
                or []
            )

            for box_number, source_box in enumerate(
                source_boxes,
                start=1,
            ):
                if (
                    not isinstance(source_box, list)
                    or len(source_box) != 5
                ):
                    raise ValueError(
                        f"Invalid source box for "
                        f"{filename}, box "
                        f"{box_number}: {source_box!r}"
                    )

                source_class_id = int(
                    source_box[0]
                )

                if (
                    source_class_id
                    != fracture_class_id
                ):
                    continue

                (
                    x_center,
                    y_center,
                    box_width,
                    box_height,
                ) = map(
                    float,
                    source_box[1:],
                )

                if not valid_yolo_box(
                    x_center,
                    y_center,
                    box_width,
                    box_height,
                ):
                    raise ValueError(
                        f"Invalid fracture box for "
                        f"{filename}, box "
                        f"{box_number}: {source_box!r}"
                    )

                fracture_boxes.append(
                    (
                        x_center,
                        y_center,
                        box_width,
                        box_height,
                    )
                )

            records.append(
                GrazRecord(
                    split=split,
                    filename=filename,
                    url=url,
                    width=width,
                    height=height,
                    fracture_boxes=tuple(
                        fracture_boxes
                    ),
                )
            )

    return (
        metadata,
        fracture_class_id,
        records,
    )


def print_graz_summary(
    records: list[GrazRecord],
) -> None:
    for split in SPLITS:
        split_records = [
            record
            for record in records
            if record.split == split
        ]

        fracture_images = sum(
            bool(record.fracture_boxes)
            for record in split_records
        )

        fracture_boxes = sum(
            len(record.fracture_boxes)
            for record in split_records
        )

        print(
            f"GRAZ {split}: "
            f"images={len(split_records)}, "
            f"fracture_images={fracture_images}, "
            f"background_images="
            f"{len(split_records) - fracture_images}, "
            f"fracture_boxes={fracture_boxes}"
        )


# =============================================================================
# COPY FRACATLAS
# =============================================================================

def copy_fracatlas() -> list[OutputRecord]:
    print(
        "\n======= COPYING FRACATLAS ======="
    )

    output_records: list[OutputRecord] = []

    for split in SPLITS:
        source_image_dir = images_dir(
            FRACATLAS_ROOT,
            split,
        )
        source_label_dir = labels_dir(
            FRACATLAS_ROOT,
            split,
        )

        source_images = sorted(
            path
            for path in source_image_dir.iterdir()
            if (
                path.is_file()
                and path.suffix.lower()
                in IMAGE_SUFFIXES
            )
        )

        source_labels = {
            path.stem: path
            for path in source_label_dir.iterdir()
            if (
                path.is_file()
                and path.suffix.lower()
                == ".txt"
            )
        }

        image_stems = {
            path.stem
            for path in source_images
        }

        if len(image_stems) != len(source_images):
            raise RuntimeError(
                f"FracAtlas {split} contains two image files "
                "with the same stem, which would share one label."
            )

        label_stems = set(
            source_labels
        )

        missing_labels = (
            image_stems - label_stems
        )
        extra_labels = (
            label_stems - image_stems
        )

        if missing_labels:
            raise RuntimeError(
                f"FracAtlas {split} images "
                "without labels: "
                f"{sorted(missing_labels)[:10]}"
            )

        if extra_labels:
            raise RuntimeError(
                f"FracAtlas {split} labels "
                "without images: "
                f"{sorted(extra_labels)[:10]}"
            )

        fracture_image_count = 0
        fracture_box_count = 0

        for source_image_path in source_images:
            source_label_path = (
                source_labels[
                    source_image_path.stem
                ]
            )

            if not strict_image_is_valid(
                source_image_path
            ):
                raise RuntimeError(
                    "Invalid FracAtlas image:\n"
                    f"  {source_image_path}"
                )

            boxes = (
                read_and_validate_one_class_label(
                    source_label_path
                )
            )

            output_filename = (
                f"{FRAC_PREFIX}"
                f"{source_image_path.name}"
            )

            output_label_filename = (
                f"{FRAC_PREFIX}"
                f"{source_image_path.stem}.txt"
            )

            destination_image_path = (
                images_dir(
                    COMBINED_ROOT,
                    split,
                )
                / output_filename
            )

            destination_label_path = (
                labels_dir(
                    COMBINED_ROOT,
                    split,
                )
                / output_label_filename
            )

            shutil.copy2(
                source_image_path,
                destination_image_path,
            )

            shutil.copy2(
                source_label_path,
                destination_label_path,
            )

            if boxes:
                fracture_image_count += 1
                fracture_box_count += len(boxes)

            output_records.append(
                OutputRecord(
                    image_id=(
                        Path(output_filename).stem
                    ),
                    source="fracatlas",
                    split=split,
                    source_file=(
                        source_image_path.name
                    ),
                    output_file=output_filename,
                    image_path=(
                        Path("images")
                        / split
                        / output_filename
                    ).as_posix(),
                    label_path=(
                        Path("labels")
                        / split
                        / output_label_filename
                    ).as_posix(),
                    fractured=int(bool(boxes)),
                    fracture_count=len(boxes),
                )
            )

        print(
            f"FracAtlas {split}: "
            f"images={len(source_images)}, "
            f"fracture_images="
            f"{fracture_image_count}, "
            f"background_images="
            f"{len(source_images) - fracture_image_count}, "
            f"fracture_boxes="
            f"{fracture_box_count}"
        )

    return output_records


# =============================================================================
# DOWNLOAD AND APPEND GRAZ
# =============================================================================

def make_graz_output_record(
    record: GrazRecord,
) -> OutputRecord:
    output_filename = (
        f"{GRAZ_PREFIX}{record.filename}"
    )

    output_label_filename = (
        f"{GRAZ_PREFIX}"
        f"{Path(record.filename).stem}.txt"
    )

    return OutputRecord(
        image_id=Path(output_filename).stem,
        source="grazpedwri",
        split=record.split,
        source_file=record.filename,
        output_file=output_filename,
        image_path=(
            Path("images")
            / record.split
            / output_filename
        ).as_posix(),
        label_path=(
            Path("labels")
            / record.split
            / output_label_filename
        ).as_posix(),
        fractured=int(
            bool(record.fracture_boxes)
        ),
        fracture_count=len(
            record.fracture_boxes
        ),
    )


def download_one_graz_record(
    record: GrazRecord,
    retries: int,
    timeout_seconds: int,
    retry_delay_seconds: int,
) -> DownloadResult:
    output_record = make_graz_output_record(
        record
    )

    destination_image_path = (
        COMBINED_ROOT
        / output_record.image_path
    )

    destination_label_path = (
        COMBINED_ROOT
        / output_record.label_path
    )

    # For a reused image, regenerate its label only after the image
    # has passed strict decoding and dimension validation.
    if strict_image_is_valid(
        destination_image_path,
        expected_width=record.width,
        expected_height=record.height,
    ):
        write_label_atomically(
            destination_label_path,
            record.fracture_boxes,
        )

        return DownloadResult(
            record=output_record,
            status="reused",
        )

    # Remove an invalid pre-existing destination before retrying.
    destination_image_path.unlink(
        missing_ok=True
    )

    temporary_path = (
        destination_image_path.parent
        / f"{destination_image_path.name}.part"
    )

    temporary_path.unlink(
        missing_ok=True
    )

    request_headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64)"
        )
    }

    last_error = ""

    for attempt in range(
        1,
        retries + 1,
    ):
        try:
            request = Request(
                record.url,
                headers=request_headers,
            )

            with urlopen(
                request,
                timeout=timeout_seconds,
            ) as response:
                with temporary_path.open(
                    "wb"
                ) as output_file:
                    shutil.copyfileobj(
                        response,
                        output_file,
                        length=1024 * 1024,
                    )

            if not strict_image_is_valid(
                temporary_path,
                expected_width=record.width,
                expected_height=record.height,
            ):
                raise RuntimeError(
                    "Downloaded image is invalid or "
                    "its dimensions do not match "
                    f"{record.width}x{record.height}."
                )

            temporary_path.replace(
                destination_image_path
            )

            # Create the matching label only after the downloaded image
            # has passed strict validation and has been moved into place.
            write_label_atomically(
                destination_label_path,
                record.fracture_boxes,
            )

            return DownloadResult(
                record=output_record,
                status="downloaded",
            )

        except (
            HTTPError,
            URLError,
            TimeoutError,
            OSError,
            RuntimeError,
        ) as error:
            last_error = (
                f"{type(error).__name__}: {error}"
            )

            temporary_path.unlink(
                missing_ok=True
            )

            if attempt < retries:
                sleep_seconds = (
                    retry_delay_seconds
                    * attempt
                )

                time.sleep(sleep_seconds)

    # Keep the folder pair clean. A failed download must not leave
    # behind an orphan image, orphan label, or temporary file.
    destination_image_path.unlink(
        missing_ok=True
    )
    destination_label_path.unlink(
        missing_ok=True
    )
    temporary_path.unlink(
        missing_ok=True
    )

    return DownloadResult(
        record=output_record,
        status="failed",
        error=last_error,
    )


def append_graz(
    records: list[GrazRecord],
    workers: int,
    retries: int,
    timeout_seconds: int,
    retry_delay_seconds: int,
) -> list[OutputRecord]:
    print(
        "\n======= DOWNLOADING AND "
        "APPENDING GRAZ ======="
    )

    print(
        "Download configuration:"
    )
    print(f"  workers: {workers}")
    print(f"  retries per image: {retries}")
    print(
        f"  timeout per attempt: "
        f"{timeout_seconds} seconds"
    )
    print(
        f"  base retry delay: "
        f"{retry_delay_seconds} seconds"
    )

    downloaded_count = 0
    reused_count = 0
    failed_results: list[
        DownloadResult
    ] = []
    output_records: list[
        OutputRecord
    ] = []

    with ThreadPoolExecutor(
        max_workers=workers
    ) as executor:
        future_to_record = {
            executor.submit(
                download_one_graz_record,
                record,
                retries,
                timeout_seconds,
                retry_delay_seconds,
            ): record
            for record in records
        }

        for completed_count, future in enumerate(
            as_completed(
                future_to_record
            ),
            start=1,
        ):
            source_record = (
                future_to_record[future]
            )

            try:
                result = future.result()

            except Exception as error:
                output_record = (
                    make_graz_output_record(
                        source_record
                    )
                )

                result = DownloadResult(
                    record=output_record,
                    status="failed",
                    error=(
                        f"{type(error).__name__}: "
                        f"{error}"
                    ),
                )

            output_records.append(
                result.record
            )

            if result.status == "downloaded":
                downloaded_count += 1

            elif result.status == "reused":
                reused_count += 1

            else:
                failed_results.append(
                    result
                )

            if (
                completed_count
                % PROGRESS_INTERVAL
                == 0
                or completed_count
                == len(records)
            ):
                print(
                    f"Progress: "
                    f"{completed_count}/"
                    f"{len(records)} | "
                    f"downloaded="
                    f"{downloaded_count} | "
                    f"reused={reused_count} | "
                    f"failed="
                    f"{len(failed_results)}"
                )

    failed_downloads_path = (
        COMBINED_ROOT
        / "failed_downloads.csv"
    )

    if failed_results:
        with failed_downloads_path.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "split",
                    "source_file",
                    "output_file",
                    "error",
                ],
            )

            writer.writeheader()

            for result in sorted(
                failed_results,
                key=lambda item: (
                    item.record.split,
                    item.record.source_file,
                ),
            ):
                writer.writerow(
                    {
                        "split": (
                            result.record.split
                        ),
                        "source_file": (
                            result.record.source_file
                        ),
                        "output_file": (
                            result.record.output_file
                        ),
                        "error": result.error,
                    }
                )

        raise RuntimeError(
            f"{len(failed_results)} GRAZ "
            "downloads failed.\n"
            f"Review: {failed_downloads_path}\n"
            "The final CSV/YAML files were not created. "
            "Failed image-label pairs were removed. "
            "Do not delete the combined dataset. "
            "Rerun this script with --resume; "
            "valid image-label pairs will be reused."
        )

    failed_downloads_path.unlink(
        missing_ok=True
    )

    return output_records


# =============================================================================
# CSV, YAML AND SUMMARY OUTPUT
# =============================================================================

CSV_COLUMNS = [
    "image_id",
    "source",
    "split",
    "source_file",
    "output_file",
    "image_path",
    "label_path",
    "fractured",
    "fracture_count",
]


def write_csv(
    output_path: Path,
    records: list[OutputRecord],
) -> None:
    with output_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=CSV_COLUMNS,
        )

        writer.writeheader()

        for record in records:
            writer.writerow(
                asdict(record)
            )


def write_split_csvs(
    records: list[OutputRecord],
) -> None:
    print(
        "\n======= CREATING SPLIT CSV FILES ======="
    )

    total_rows = 0

    for split in SPLITS:
        split_records = sorted(
            (
                record
                for record in records
                if record.split == split
            ),
            key=lambda record: (
                record.source,
                record.output_file,
            ),
        )

        output_path = (
            splits_dir(COMBINED_ROOT)
            / f"{split}.csv"
        )

        write_csv(
            output_path,
            split_records,
        )

        fracture_images = sum(
            record.fractured
            for record in split_records
        )

        fracture_boxes = sum(
            record.fracture_count
            for record in split_records
        )

        print(
            f"{split}.csv: "
            f"rows={len(split_records)}, "
            f"fracture_images="
            f"{fracture_images}, "
            f"background_images="
            f"{len(split_records) - fracture_images}, "
            f"fracture_boxes="
            f"{fracture_boxes}"
        )

        total_rows += len(
            split_records
        )

    if total_rows != len(records):
        raise RuntimeError(
            "The total number of split CSV "
            "rows does not match the number "
            f"of output records: {total_rows} "
            f"!= {len(records)}"
        )


def write_source_manifest(
    records: list[OutputRecord],
) -> None:
    sorted_records = sorted(
        records,
        key=lambda record: (
            record.split,
            record.source,
            record.output_file,
        ),
    )

    write_csv(
        COMBINED_ROOT
        / "source_manifest.csv",
        sorted_records,
    )


def write_dataset_yaml() -> None:
    yaml_content = (
        f"path: "
        f"{COMBINED_ROOT.as_posix()}\n\n"
        "train: images/train\n"
        "val: images/val\n"
        "test: images/test\n\n"
        "names:\n"
        "  0: fracture\n"
    )

    (
        COMBINED_ROOT
        / "dataset.yaml"
    ).write_text(
        yaml_content,
        encoding="utf-8",
    )


def build_summary(
    records: list[OutputRecord],
) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "dataset_root": str(
            COMBINED_ROOT
        ),
        "class_names": {
            "0": TARGET_CLASS_NAME,
        },
        "total_images": len(records),
        "total_fracture_images": sum(
            record.fractured
            for record in records
        ),
        "total_background_images": sum(
            1 - record.fractured
            for record in records
        ),
        "total_fracture_boxes": sum(
            record.fracture_count
            for record in records
        ),
        "splits": {},
        "sources": {},
    }

    for split in SPLITS:
        split_records = [
            record
            for record in records
            if record.split == split
        ]

        fracture_images = sum(
            record.fractured
            for record in split_records
        )

        summary["splits"][split] = {
            "images": len(split_records),
            "fracture_images": fracture_images,
            "background_images": (
                len(split_records)
                - fracture_images
            ),
            "fracture_boxes": sum(
                record.fracture_count
                for record in split_records
            ),
        }

    for source in (
        "fracatlas",
        "grazpedwri",
    ):
        source_records = [
            record
            for record in records
            if record.source == source
        ]

        source_fracture_images = sum(
            record.fractured
            for record in source_records
        )

        summary["sources"][source] = {
            "images": len(source_records),
            "fracture_images": (
                source_fracture_images
            ),
            "background_images": (
                len(source_records)
                - source_fracture_images
            ),
            "fracture_boxes": sum(
                record.fracture_count
                for record in source_records
            ),
        }

    return summary


def write_summary(
    records: list[OutputRecord],
) -> dict[str, Any]:
    summary = build_summary(records)

    (
        COMBINED_ROOT
        / "dataset_summary.json"
    ).write_text(
        json.dumps(
            summary,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return summary


# =============================================================================
# FINAL STRICT VALIDATION
# =============================================================================

def validate_generated_graz_labels(
    graz_records: list[GrazRecord],
) -> None:
    """
    Independently compare every generated GRAZ label with the
    fracture boxes from its original NDJSON record.
    """
    for index, record in enumerate(
        graz_records,
        start=1,
    ):
        output_record = (
            make_graz_output_record(
                record
            )
        )

        label_path = (
            COMBINED_ROOT
            / output_record.label_path
        )

        actual_boxes = (
            read_and_validate_one_class_label(
                label_path
            )
        )

        expected_boxes = tuple(
            (
                round(box[0], 6),
                round(box[1], 6),
                round(box[2], 6),
                round(box[3], 6),
            )
            for box in record.fracture_boxes
        )

        rounded_actual_boxes = tuple(
            (
                round(box[0], 6),
                round(box[1], 6),
                round(box[2], 6),
                round(box[3], 6),
            )
            for box in actual_boxes
        )

        if rounded_actual_boxes != expected_boxes:
            raise RuntimeError(
                "Generated GRAZ label does not "
                "match its original NDJSON record:\n"
                f"  image: {record.filename}\n"
                f"  label: {label_path}\n"
                f"  expected: {expected_boxes}\n"
                f"  actual: {rounded_actual_boxes}"
            )

        if index % 5000 == 0:
            print(
                "Verified GRAZ labels: "
                f"{index}/{len(graz_records)}"
            )


def validate_split_csv(
    split: str,
    expected_records: list[OutputRecord],
) -> None:
    csv_path = (
        splits_dir(COMBINED_ROOT)
        / f"{split}.csv"
    )

    if not csv_path.exists():
        raise FileNotFoundError(
            f"Missing split CSV: {csv_path}"
        )

    with csv_path.open(
        "r",
        newline="",
        encoding="utf-8",
    ) as file:
        rows = list(
            csv.DictReader(file)
        )

    if len(rows) != len(
        expected_records
    ):
        raise RuntimeError(
            f"{split}.csv rows="
            f"{len(rows)}, expected="
            f"{len(expected_records)}"
        )

    csv_output_files = {
        row["output_file"]
        for row in rows
    }

    expected_output_files = {
        record.output_file
        for record in expected_records
    }

    if csv_output_files != expected_output_files:
        missing = (
            expected_output_files
            - csv_output_files
        )
        extra = (
            csv_output_files
            - expected_output_files
        )

        raise RuntimeError(
            f"{split}.csv file mismatch. "
            f"Missing={sorted(missing)[:10]}, "
            f"extra={sorted(extra)[:10]}"
        )

    for row in rows:
        image_path = (
            COMBINED_ROOT
            / row["image_path"]
        )
        label_path = (
            COMBINED_ROOT
            / row["label_path"]
        )

        if not image_path.exists():
            raise FileNotFoundError(
                f"CSV image does not exist: "
                f"{image_path}"
            )

        if not label_path.exists():
            raise FileNotFoundError(
                f"CSV label does not exist: "
                f"{label_path}"
            )


def validate_combined_dataset(
    records: list[OutputRecord],
    graz_records: list[GrazRecord],
) -> dict[str, Any]:
    print(
        "\n======= STRICT FINAL VALIDATION ======="
    )

    if len(
        {
            record.output_file
            for record in records
        }
    ) != len(records):
        raise RuntimeError(
            "Duplicate output filenames exist "
            "in the combined dataset."
        )

    global_image_ids: set[str] = set()

    for split in SPLITS:
        split_records = [
            record
            for record in records
            if record.split == split
        ]

        expected_image_names = {
            record.output_file
            for record in split_records
        }

        actual_images = sorted(
            path
            for path in images_dir(
                COMBINED_ROOT,
                split,
            ).iterdir()
            if (
                path.is_file()
                and path.suffix.lower()
                in IMAGE_SUFFIXES
            )
        )

        actual_labels = sorted(
            path
            for path in labels_dir(
                COMBINED_ROOT,
                split,
            ).iterdir()
            if (
                path.is_file()
                and path.suffix.lower()
                == ".txt"
            )
        )

        actual_image_names = {
            path.name
            for path in actual_images
        }

        image_stems = {
            path.stem
            for path in actual_images
        }

        label_stems = {
            path.stem
            for path in actual_labels
        }

        if (
            actual_image_names
            != expected_image_names
        ):
            missing = (
                expected_image_names
                - actual_image_names
            )
            extra = (
                actual_image_names
                - expected_image_names
            )

            raise RuntimeError(
                f"{split} image mismatch. "
                f"Missing={sorted(missing)[:10]}, "
                f"extra={sorted(extra)[:10]}"
            )

        if image_stems != label_stems:
            missing_labels = (
                image_stems - label_stems
            )
            extra_labels = (
                label_stems - image_stems
            )

            raise RuntimeError(
                f"{split} image/label mismatch. "
                f"Missing labels="
                f"{sorted(missing_labels)[:10]}, "
                f"extra labels="
                f"{sorted(extra_labels)[:10]}"
            )

        split_fracture_images = 0
        split_fracture_boxes = 0

        for image_path in actual_images:
            if not strict_image_is_valid(
                image_path
            ):
                raise RuntimeError(
                    f"Invalid image: {image_path}"
                )

            label_path = (
                labels_dir(
                    COMBINED_ROOT,
                    split,
                )
                / f"{image_path.stem}.txt"
            )

            boxes = (
                read_and_validate_one_class_label(
                    label_path
                )
            )

            if boxes:
                split_fracture_images += 1
                split_fracture_boxes += len(
                    boxes
                )

            if image_path.stem in global_image_ids:
                raise RuntimeError(
                    "The same image ID appears in "
                    "more than one split: "
                    f"{image_path.stem}"
                )

            global_image_ids.add(
                image_path.stem
            )

        expected_fracture_images = sum(
            record.fractured
            for record in split_records
        )

        expected_fracture_boxes = sum(
            record.fracture_count
            for record in split_records
        )

        if (
            split_fracture_images
            != expected_fracture_images
        ):
            raise RuntimeError(
                f"{split} fracture-image count "
                "does not match records: "
                f"{split_fracture_images} != "
                f"{expected_fracture_images}"
            )

        if (
            split_fracture_boxes
            != expected_fracture_boxes
        ):
            raise RuntimeError(
                f"{split} fracture-box count "
                "does not match records: "
                f"{split_fracture_boxes} != "
                f"{expected_fracture_boxes}"
            )

        validate_split_csv(
            split,
            split_records,
        )

        print(
            f"{split}: "
            f"images={len(actual_images)}, "
            f"labels={len(actual_labels)}, "
            f"CSV rows="
            f"{len(split_records)}, "
            f"fracture_images="
            f"{split_fracture_images}, "
            f"background_images="
            f"{len(actual_images) - split_fracture_images}, "
            f"fracture_boxes="
            f"{split_fracture_boxes}"
        )

    print(
        "\nVerifying every generated GRAZ "
        "label against the original NDJSON..."
    )

    validate_generated_graz_labels(
        graz_records
    )

    summary = build_summary(records)

    print(
        f"\nTotal images: "
        f"{summary['total_images']}"
    )
    print(
        "Total fracture images: "
        f"{summary['total_fracture_images']}"
    )
    print(
        "Total background images: "
        f"{summary['total_background_images']}"
    )
    print(
        "Total fracture boxes: "
        f"{summary['total_fracture_boxes']}"
    )
    print(
        "Combined dataset validation passed."
    )

    return summary


# =============================================================================
# ARGUMENTS AND MAIN
# =============================================================================

def positive_integer(
    value: str,
) -> int:
    parsed_value = int(value)

    if parsed_value <= 0:
        raise argparse.ArgumentTypeError(
            "Value must be greater than zero."
        )

    return parsed_value


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a one-class YOLO fracture "
            "dataset by combining FracAtlas "
            "and GRAZPEDWRI-DX."
        )
    )

    mode_group = (
        parser.add_mutually_exclusive_group(
            required=True
        )
    )

    mode_group.add_argument(
        "--fresh",
        action="store_true",
        help=(
            "Delete any existing combined "
            "dataset and build it from scratch."
        ),
    )

    mode_group.add_argument(
        "--resume",
        action="store_true",
        help=(
            "Keep valid existing images and "
            "download only missing/invalid ones."
        ),
    )

    parser.add_argument(
        "--workers",
        type=positive_integer,
        default=DEFAULT_WORKERS,
        help=(
            "Parallel GRAZ download workers. "
            f"Default: {DEFAULT_WORKERS}"
        ),
    )

    parser.add_argument(
        "--retries",
        type=positive_integer,
        default=DEFAULT_RETRIES,
        help=(
            "Download attempts per image. "
            f"Default: {DEFAULT_RETRIES}"
        ),
    )

    parser.add_argument(
        "--timeout",
        type=positive_integer,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=(
            "Timeout in seconds per attempt. "
            f"Default: "
            f"{DEFAULT_TIMEOUT_SECONDS}"
        ),
    )

    parser.add_argument(
        "--retry-delay",
        type=positive_integer,
        default=DEFAULT_RETRY_DELAY_SECONDS,
        help=(
            "Base delay in seconds between "
            "retries. Default: "
            f"{DEFAULT_RETRY_DELAY_SECONDS}"
        ),
    )

    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()

    print(
        "======= BUILD COMBINED YOLO DATASET ======="
    )
    print(f"Project root: {PROJECT_ROOT}")
    print(
        f"FracAtlas source: "
        f"{FRACATLAS_ROOT}"
    )
    print(
        f"GRAZ manifest: {GRAZ_NDJSON}"
    )
    print(
        f"Combined output: {COMBINED_ROOT}"
    )
    print(
        f"Mode: "
        f"{'fresh' if arguments.fresh else 'resume'}"
    )

    validate_input_structure()

    (
        _metadata,
        fracture_class_id,
        graz_records,
    ) = load_graz_manifest()

    print_and_check_url_expiry(
        graz_records
    )

    print(
        "GRAZ fracture source class ID: "
        f"{fracture_class_id}"
    )
    print(
        "GRAZ records loaded: "
        f"{len(graz_records)}"
    )

    print_graz_summary(
        graz_records
    )

    create_output_structure(
        fresh=arguments.fresh
    )

    fracatlas_records = (
        copy_fracatlas()
    )

    graz_output_records = append_graz(
        records=graz_records,
        workers=arguments.workers,
        retries=arguments.retries,
        timeout_seconds=arguments.timeout,
        retry_delay_seconds=(
            arguments.retry_delay
        ),
    )

    all_records = (
        fracatlas_records
        + graz_output_records
    )

    write_dataset_yaml()
    write_source_manifest(
        all_records
    )
    write_split_csvs(
        all_records
    )
    write_summary(
        all_records
    )

    validate_combined_dataset(
        records=all_records,
        graz_records=graz_records,
    )

    print(
        "\n======= COMPLETE ======="
    )
    print(
        f"Combined dataset:\n"
        f"  {COMBINED_ROOT}"
    )
    print(
        f"Dataset YAML:\n"
        f"  {COMBINED_ROOT / 'dataset.yaml'}"
    )
    print(
        "Split CSV files:"
    )

    for split in SPLITS:
        print(
            "  "
            f"{splits_dir(COMBINED_ROOT) / f'{split}.csv'}"
        )


if __name__ == "__main__":
    main()
