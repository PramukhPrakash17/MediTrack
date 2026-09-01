from pathlib import Path

import pandas as pd


# -------------------------------------------------------------------
# Dataset paths
# -------------------------------------------------------------------

DATASET_CSV = Path(
    "C:/Users/pramu/Desktop/MediTrack/Xray-Service/"
    "data/FracAtlas/dataset.csv"
)

FRACTURED_IMAGE_DIR = Path(
    "C:/Users/pramu/Desktop/MediTrack/Xray-Service/"
    "data/FracAtlas/images/Fractured"
)

NON_FRACTURED_IMAGE_DIR = Path(
    "C:/Users/pramu/Desktop/MediTrack/Xray-Service/"
    "data/FracAtlas/images/Non_fractured"
)


# -------------------------------------------------------------------
# Dataset configuration
# -------------------------------------------------------------------

REQUIRED_COLUMNS = {
    "image_id",
    "fractured",
    "fracture_count",
}

VALID_FRACTURE_VALUES = {
    0,
    1,
}

SUPPORTED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
}


def collect_image_names(directory: Path) -> set[str]:
    """
    Read all supported image files from the given directory
    and return only their filenames.

    Example:
    {
        "IMG0000001.jpg",
        "IMG0000002.jpg"
    }
    """

    image_names = set()

    for file_path in directory.iterdir():
        if (
            file_path.is_file()
            and file_path.suffix.lower()
            in SUPPORTED_IMAGE_EXTENSIONS
        ):
            image_names.add(file_path.name)

    return image_names


def main() -> None:

    # ---------------------------------------------------------------
    # Task 1: Validate paths
    # ---------------------------------------------------------------

    print("=" * 70)
    print("FRACATLAS DATASET INSPECTION")
    print("=" * 70)

    required_paths = [
        DATASET_CSV,
        FRACTURED_IMAGE_DIR,
        NON_FRACTURED_IMAGE_DIR,
    ]

    for required_path in required_paths:
        if not required_path.exists():
            raise FileNotFoundError(
                f"Required path does not exist: {required_path}"
            )

    print("All required paths exist.")

    # ---------------------------------------------------------------
    # Task 2: Read CSV
    # ---------------------------------------------------------------

    dataframe = pd.read_csv(DATASET_CSV)

    print()
    print("-" * 70)
    print("CSV INFORMATION")
    print("-" * 70)

    print(f"Dataset loaded from: {DATASET_CSV}")
    print(f"Total rows: {len(dataframe)}")

    print()
    print("CSV columns:")
    print(list(dataframe.columns))

    # ---------------------------------------------------------------
    # Task 3: Validate required columns
    # ---------------------------------------------------------------

    csv_columns = set(dataframe.columns)

    missing_columns = REQUIRED_COLUMNS - csv_columns

    if missing_columns:
        raise ValueError(
            "CSV validation failed. Missing required columns: "
            f"{sorted(missing_columns)}"
        )

    print()
    print("CSV structure validation passed.")
    print("All required columns are available.")

    # ---------------------------------------------------------------
    # Task 4: Inspect CSV data quality
    # ---------------------------------------------------------------

    print()
    print("-" * 70)
    print("CSV DATA QUALITY")
    print("-" * 70)

    fracture_distribution = (
        dataframe["fractured"]
        .value_counts()
        .sort_index()
    )

    print("Fracture distribution:")

    for fracture_value, count in fracture_distribution.items():

        if fracture_value == 0:
            label = "Non-fractured"
        elif fracture_value == 1:
            label = "Fractured"
        else:
            label = "Unknown"

        print(
            f"  {fracture_value} ({label}) -> {count}"
        )

    duplicate_image_rows = dataframe[
        dataframe["image_id"].duplicated(keep=False)
    ]

    print()
    print(
        f"Duplicate image IDs in CSV: "
        f"{len(duplicate_image_rows)}"
    )

    if not duplicate_image_rows.empty:
        print(
            duplicate_image_rows[
                [
                    "image_id",
                    "fractured",
                    "fracture_count",
                ]
            ].to_string(index=False)
        )

    null_image_ids = (
        dataframe["image_id"]
        .isna()
        .sum()
    )

    print(f"Null image IDs: {null_image_ids}")

    empty_image_ids = (
        dataframe["image_id"]
        .fillna("")
        .astype(str)
        .str.strip()
        .eq("")
        .sum()
    )

    print(f"Empty image IDs: {empty_image_ids}")

    invalid_fracture_rows = dataframe[
        ~dataframe["fractured"].isin(
            VALID_FRACTURE_VALUES
        )
    ]

    print(
        f"Invalid fractured values: "
        f"{len(invalid_fracture_rows)}"
    )

    if not invalid_fracture_rows.empty:
        print(
            invalid_fracture_rows[
                [
                    "image_id",
                    "fractured",
                ]
            ].to_string(index=False)
        )

    # ---------------------------------------------------------------
    # Task 5: Read images from both folders
    # ---------------------------------------------------------------

    print()
    print("-" * 70)
    print("IMAGE FOLDER INSPECTION")
    print("-" * 70)

    fractured_image_names = collect_image_names(
        FRACTURED_IMAGE_DIR
    )

    non_fractured_image_names = collect_image_names(
        NON_FRACTURED_IMAGE_DIR
    )

    print(
        "Fractured folder images: "
        f"{len(fractured_image_names)}"
    )

    print(
        "Non-fractured folder images: "
        f"{len(non_fractured_image_names)}"
    )

    total_physical_images = (
        len(fractured_image_names)
        + len(non_fractured_image_names)
    )

    print(
        f"Total physical image files: "
        f"{total_physical_images}"
    )

    # ---------------------------------------------------------------
    # Task 6: Find filenames present in both folders
    # ---------------------------------------------------------------

    filenames_in_both_folders = (
        fractured_image_names
        & non_fractured_image_names
    )

    print()
    print(
        "Same filename present in both folders: "
        f"{len(filenames_in_both_folders)}"
    )

    for filename in sorted(
        filenames_in_both_folders
    ):
        matching_row = dataframe[
            dataframe["image_id"] == filename
        ]

        if not matching_row.empty:
            fracture_value = int(
                matching_row.iloc[0]["fractured"]
            )

            print(
                f"  {filename} "
                f"(CSV fractured value: {fracture_value})"
            )
        else:
            print(
                f"  {filename} "
                "(not present in CSV)"
            )

    # ---------------------------------------------------------------
    # Task 7: Compare CSV filenames with disk filenames
    # ---------------------------------------------------------------

    csv_image_names = set(
        dataframe["image_id"].astype(str)
    )

    all_disk_image_names = (
        fractured_image_names
        | non_fractured_image_names
    )

    images_missing_from_disk = (
        csv_image_names
        - all_disk_image_names
    )

    images_not_referenced_by_csv = (
        all_disk_image_names
        - csv_image_names
    )

    print()
    print(
        "Unique image IDs in CSV: "
        f"{len(csv_image_names)}"
    )

    print(
        "Unique image filenames on disk: "
        f"{len(all_disk_image_names)}"
    )

    print()
    print(
        "CSV images missing from disk: "
        f"{len(images_missing_from_disk)}"
    )

    for filename in sorted(
        images_missing_from_disk
    ):
        print(f"  {filename}")

    print()
    print(
        "Disk images not referenced by CSV: "
        f"{len(images_not_referenced_by_csv)}"
    )

    for filename in sorted(
        images_not_referenced_by_csv
    ):
        print(f"  {filename}")

    # ---------------------------------------------------------------
    # Task 8: Validate correct folder placement
    # ---------------------------------------------------------------

    print()
    print("-" * 70)
    print("IMAGE FOLDER PLACEMENT VALIDATION")
    print("-" * 70)

    fractured_csv_image_names = set(
        dataframe.loc[
            dataframe["fractured"] == 1,
            "image_id",
        ].astype(str)
    )

    non_fractured_csv_image_names = set(
        dataframe.loc[
            dataframe["fractured"] == 0,
            "image_id",
        ].astype(str)
    )

    fractured_images_missing_from_fractured_folder = (
        fractured_csv_image_names
        - fractured_image_names
    )

    non_fractured_images_missing_from_normal_folder = (
        non_fractured_csv_image_names
        - non_fractured_image_names
    )

    print(
        "Fractured CSV images missing from "
        "Fractured folder: "
        f"{len(fractured_images_missing_from_fractured_folder)}"
    )

    for filename in sorted(
        fractured_images_missing_from_fractured_folder
    ):
        print(f"  {filename}")

    print()
    print(
        "Non-fractured CSV images missing from "
        "Non_fractured folder: "
        f"{len(non_fractured_images_missing_from_normal_folder)}"
    )

    for filename in sorted(
        non_fractured_images_missing_from_normal_folder
    ):
        print(f"  {filename}")

    # ---------------------------------------------------------------
    # Final summary
    # ---------------------------------------------------------------

    critical_issues = (
        len(missing_columns)
        + len(duplicate_image_rows)
        + null_image_ids
        + empty_image_ids
        + len(invalid_fracture_rows)
        + len(images_missing_from_disk)
        + len(
            fractured_images_missing_from_fractured_folder
        )
        + len(
            non_fractured_images_missing_from_normal_folder
        )
    )

    warnings = (
        len(filenames_in_both_folders)
        + len(images_not_referenced_by_csv)
    )

    print()
    print("=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)

    print(f"CSV rows: {len(dataframe)}")

    print(
        f"Fractured CSV records: "
        f"{len(fractured_csv_image_names)}"
    )

    print(
        f"Non-fractured CSV records: "
        f"{len(non_fractured_csv_image_names)}"
    )

    print(
        f"Unique disk images: "
        f"{len(all_disk_image_names)}"
    )

    print(f"Critical issues: {critical_issues}")
    print(f"Warnings: {warnings}")

    print()

    if critical_issues == 0:
        print(
            "RESULT: Dataset passed all current "
            "CSV and image validation checks."
        )
    else:
        print(
            "RESULT: Dataset has critical issues "
            "that must be fixed."
        )

    if warnings > 0:
        print(
            "Warnings exist and should be reviewed."
        )

    print()
    print(
        "This script did not modify any files."
    )


if __name__ == "__main__":
    main()