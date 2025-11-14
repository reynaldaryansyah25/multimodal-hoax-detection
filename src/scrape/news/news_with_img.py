import pandas as pd
import os

def add_valid_image_path(csv_path, output_path, image_dir):
    # Baca file CSV
    df = pd.read_csv(csv_path)

    # Buat kolom image_path hanya jika file benar-benar ada
    def get_path(id_val):
        path = os.path.join(image_dir, f"{id_val}.jpg")
        return path if os.path.exists(path) else None

    df["image_path"] = df["id"].apply(get_path)

    # Simpan hasil ke file baru
    df.to_csv(output_path, index=False)
    print(f"Kolom image_path sudah ditambahkan ke {output_path}, hanya untuk gambar yang tersedia.")

if __name__ == "__main__":
    add_valid_image_path(
        "data/raw/news/metadata_news_final.csv",              
        "data/raw/news/news_with_images.csv", 
        "data/raw/news/images"                
    )