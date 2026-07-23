from pathlib import Path
import shutil

import pandas as pd
from sklearn.model_selection import train_test_split


# ============================================================
# INPUT PATHS
# ============================================================

DATASET_ROOT = Path(
    "C:/Users/pramu/Desktop/MediTrack/Xray-Service/data/FracAtlas"
)

DATASET_CSV = DATASET_ROOT / "dataset.csv"

FRACTURED_IMAGE_FOLDER = DATASET_ROOT / "images" / "Fractured"

NON_FRACTURED_IMAGE_FOLDER = DATASET_ROOT / "images" / "Non_fractured"

# Change this path if your YOLO label folder has another name
YOLO_LABEL_FOLDER = DATASET_ROOT /"Annotations/YOLO"


# ============================================================
# OUTPUT PATHS
# ============================================================

OUTPUT_ROOT = Path(
    "C:/Users/pramu/Desktop/MediTrack/Xray-Service/data/yolo_dataset"
)

SPLITS_FOLDER = OUTPUT_ROOT / "splits"

TRAIN_IMAGES = OUTPUT_ROOT / "images" / "train"
VAL_IMAGES = OUTPUT_ROOT / "images" / "val"
TEST_IMAGES = OUTPUT_ROOT / "images" / "test"

TRAIN_LABELS = OUTPUT_ROOT / "labels" / "train"
VAL_LABELS = OUTPUT_ROOT / "labels" / "val"
TEST_LABELS = OUTPUT_ROOT / "labels" / "test"


# ============================================================
# CREATE OUTPUT FOLDERS
# ============================================================

def create_output_folders():
    folders = [
        SPLITS_FOLDER,
        TRAIN_IMAGES,
        VAL_IMAGES,
        TEST_IMAGES,
        TRAIN_LABELS,
        VAL_LABELS,
        TEST_LABELS,
    ]

    for folder in folders:
        folder.mkdir(parents=True, exist_ok=True)

    print("Output folders created successfully.")


# ============================================================
# PRINT CLASS DISTRIBUTION
# ============================================================

def print_distribution(name, dataframe):
    print(f"\n{name} distribution:")

    counts = dataframe["fractured"].value_counts().sort_index()

    percentages = (
        dataframe["fractured"]
        .value_counts(normalize=True)
        .sort_index()
        .mul(100)
        .round(2)
    )

    print("Counts:")
    print(counts)

    print("Percentages:")
    print(percentages)


# ============================================================
# VERIFY THAT SPLITS DO NOT OVERLAP
# ============================================================

def verify_no_overlap(train_df, val_df, test_df):
    train_ids = set(train_df["image_id"])
    val_ids = set(val_df["image_id"])
    test_ids = set(test_df["image_id"])

    train_val_overlap = train_ids.intersection(val_ids)
    train_test_overlap = train_ids.intersection(test_ids)
    val_test_overlap = val_ids.intersection(test_ids)

    print("\n======= OVERLAP CHECK =======")
    print(f"Train and validation overlap: {len(train_val_overlap)}")
    print(f"Train and test overlap: {len(train_test_overlap)}")
    print(f"Validation and test overlap: {len(val_test_overlap)}")

    if train_val_overlap:
        raise ValueError("Train and validation data overlap.")

    if train_test_overlap:
        raise ValueError("Train and test data overlap.")

    if val_test_overlap:
        raise ValueError("Validation and test data overlap.")

    print("No overlap found.")


# ============================================================
# COPY IMAGES AND LABELS
# ============================================================

def copy_split_files(
    split_name,
    split_df,
    destination_image_folder,
    destination_label_folder,
):
    copied_images = 0
    copied_labels = 0
    missing_images = 0
    missing_labels = 0

#   ignoring the string 
    for _, row in split_df.iterrows(): 
        image_id = str(row["image_id"]) 
        fractured = int(row["fractured"]) #converting image id to str and fractured to int

        # Select the source image folder
        if fractured == 1:
            source_image = FRACTURED_IMAGE_FOLDER / image_id
        else:
            source_image = NON_FRACTURED_IMAGE_FOLDER / image_id
                                                                                # getting the source imagename
        # Example: image123.jpg becomes image123.txt
        label_name = Path(image_id).with_suffix(".txt").name
        source_label = YOLO_LABEL_FOLDER / label_name                           # getting label name 

        destination_image = destination_image_folder / image_id
        destination_label = destination_label_folder / label_name

        # Copy image
        if source_image.exists():
            shutil.copy2(source_image, destination_image)
            copied_images += 1
        else:
            missing_images += 1
            print(f"Missing image: {source_image}")

        # Copy label, including empty label files
        if source_label.exists():
            shutil.copy2(source_label, destination_label)
            copied_labels += 1
        else:
            missing_labels += 1
            print(f"Missing label: {source_label}")

    print(f"\n======= {split_name.upper()} COPY SUMMARY =======")
    print(f"CSV rows: {len(split_df)}")
    print(f"Copied images: {copied_images}")
    print(f"Copied labels: {copied_labels}")
    print(f"Missing images: {missing_images}")
    print(f"Missing labels: {missing_labels}")

    return {
        "images": copied_images,
        "labels": copied_labels,
        "missing_images": missing_images,
        "missing_labels": missing_labels,
    }


# ============================================================
# GENERATE DATASET.YAML
# ============================================================

def create_dataset_yaml():
    yaml_content = f"""path: {OUTPUT_ROOT.as_posix()}

train: images/train
val: images/val
test: images/test

names:
  0: fracture
"""

    yaml_path = OUTPUT_ROOT / "dataset.yaml"

    yaml_path.write_text(
        yaml_content,
        encoding="utf-8",
    )

    print(f"\ndataset.yaml created: {yaml_path}")


# ============================================================
# MAIN FUNCTION
# ============================================================

def main():
    print("======= YOLO DATASET CREATION =======")

    # Check required inputs
    if not DATASET_CSV.exists():
        raise FileNotFoundError(
            f"dataset.csv not found: {DATASET_CSV}"
        )

    if not FRACTURED_IMAGE_FOLDER.exists():
        raise FileNotFoundError(
            f"Fractured image folder not found: "
            f"{FRACTURED_IMAGE_FOLDER}"
        )

    if not NON_FRACTURED_IMAGE_FOLDER.exists():
        raise FileNotFoundError(
            f"Non-fractured image folder not found: "
            f"{NON_FRACTURED_IMAGE_FOLDER}"
        )

    if not YOLO_LABEL_FOLDER.exists():
        raise FileNotFoundError(
            f"YOLO label folder not found: "
            f"{YOLO_LABEL_FOLDER}"
        )

    # Create output folders
    create_output_folders()

    # Read CSV
    df = pd.read_csv(DATASET_CSV)

    print(f"\nTotal CSV rows: {len(df)}")
    print(f"Columns: {df.columns.tolist()}")

    required_columns = ["image_id", "fractured"]

    for column in required_columns:
        if column not in df.columns:
            raise ValueError(
                f"Missing required CSV column: {column}"
            )

    # Check duplicate image IDs
    duplicate_count = df["image_id"].duplicated().sum()

    print(f"Duplicate image IDs: {duplicate_count}")

    if duplicate_count > 0:
        raise ValueError(
            "Duplicate image IDs found in dataset.csv."
        )

    # --------------------------------------------------------
    # First split: 80% train, 20% temporary
    # --------------------------------------------------------

    train_df, temporary_df = train_test_split(
        df,
        test_size=0.20,
        random_state=42,
        stratify=df["fractured"],
    )

    # --------------------------------------------------------
    # Second split: temporary 20% into 10% val and 10% test
    # --------------------------------------------------------

    val_df, test_df = train_test_split(
        temporary_df,
        test_size=0.50,
        random_state=42,
        stratify=temporary_df["fractured"],
    )

    # Reset the DataFrame indexes
    train_df = train_df.reset_index(drop=True)
    val_df = val_df.reset_index(drop=True)
    test_df = test_df.reset_index(drop=True)

    print("\n======= SPLIT SIZE =======")
    print(f"Total rows: {len(df)}")
    print(f"Train rows: {len(train_df)}")
    print(f"Validation rows: {len(val_df)}")
    print(f"Test rows: {len(test_df)}")

    # Verify total count
    total_split_rows = (
        len(train_df)
        + len(val_df)
        + len(test_df)
    )

    if total_split_rows != len(df):
        raise ValueError(
            "Split row count does not match the original dataset."
        )

    # Print class distributions
    print_distribution("Original", df)
    print_distribution("Train", train_df)
    print_distribution("Validation", val_df)
    print_distribution("Test", test_df)

    # Verify no overlap
    verify_no_overlap(
        train_df,
        val_df,
        test_df,
    )

    # Save CSV files
    train_df.to_csv(
        SPLITS_FOLDER / "train.csv",
        index=False,
    )

    val_df.to_csv(
        SPLITS_FOLDER / "val.csv",
        index=False,
    )

    test_df.to_csv(
        SPLITS_FOLDER / "test.csv",
        index=False,
    )

    print("\nSplit CSV files saved successfully.")

    # Copy files
    train_result = copy_split_files(
        "train",
        train_df,
        TRAIN_IMAGES,
        TRAIN_LABELS,
    )

    val_result = copy_split_files(
        "validation",
        val_df,
        VAL_IMAGES,
        VAL_LABELS,
    )

    test_result = copy_split_files(
        "test",
        test_df,
        TEST_IMAGES,
        TEST_LABELS,
    )

    # Create dataset.yaml
    create_dataset_yaml()

    # Final summary
    print("\n======= FINAL SUMMARY =======")
    print(f"Total dataset rows: {len(df)}")

    print(f"\nTrain rows: {len(train_df)}")
    print(f"Train images: {train_result['images']}")
    print(f"Train labels: {train_result['labels']}")

    print(f"\nValidation rows: {len(val_df)}")
    print(f"Validation images: {val_result['images']}")
    print(f"Validation labels: {val_result['labels']}")

    print(f"\nTest rows: {len(test_df)}")
    print(f"Test images: {test_result['images']}")
    print(f"Test labels: {test_result['labels']}")

    total_missing_images = (
        train_result["missing_images"]
        + val_result["missing_images"]
        + test_result["missing_images"]
    )

    total_missing_labels = (
        train_result["missing_labels"]
        + val_result["missing_labels"]
        + test_result["missing_labels"]
    )

    print(f"\nTotal missing images: {total_missing_images}")
    print(f"Total missing labels: {total_missing_labels}")

    if total_missing_images == 0 and total_missing_labels == 0:
        print("\nYOLO dataset created successfully.")
    else:
        print("\nDataset created, but some files are missing.")


if __name__ == "__main__":
    main()