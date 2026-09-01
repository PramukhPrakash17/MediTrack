from pathlib import Path
import pandas as pd
from PIL import Image

DATASET_CSV = Path("C:/Users/pramu/Desktop/MediTrack/Xray-Service/data/FracAtlas/dataset.csv")
file_prefix="C:/Users/pramu/Desktop/MediTrack/Xray-Service/data/FracAtlas/"


def main():
    print("=======IMAGE SUMMARY======")
    valid_paths=0
    missing_images=0
    valid_images=0
    invalid_images=0
    corrupted_image=0
    df = pd.read_csv(DATASET_CSV)
    for index ,row in df.iterrows():
        imageid = row["image_id"]
        check_fracture = row["fractured"]
        if check_fracture == 1:
            imagepath=file_prefix+"images/Fractured"
        else:
            imagepath=file_prefix+"images/Non_fractured"
        full_image_path=imagepath+"/"+imageid
        # print(full_image_path)
        temp=Path(full_image_path)
        if temp.exists():
            # print("files is present in the folder")
            valid_paths+=1
            try:
                with Image.open(temp) as img:
                    width = img.size[0]
                    height = img.size[1]
                    if(width > 0 and height > 0):
                        valid_images+=1
                    else:
                        invalid_images+=1
            except:
                corrupted_image+=1
                raise ValueError("Image not opening or now a valid image")
            print(img)
        else:
            missing_images+=1
            # raise ValueError("Image doesnt exist in the folder")
    
    print("\n======= IMAGE SUMMARY =======")
    print(f"Total CSV rows: {len(df)}")
    print(f"Valid images: {valid_images}")
    print(f"Missing images: {missing_images}")
    print(f"Corrupted images: {corrupted_image}")
    print(f"Invalid dimensions: {invalid_images}")    
        
        
    
    


if __name__ == "__main__":
    main()