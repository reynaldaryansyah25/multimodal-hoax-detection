import pandas as pd
import requests
import os

def download_images(csv_path, output_dir):
    # Baca file CSV
    df = pd.read_csv(csv_path)

    # Pastikan folder tujuan ada
    os.makedirs(output_dir, exist_ok=True)

    success, fail = 0, 0

    # Loop setiap baris untuk download gambar
    for idx, row in df.iterrows():
        url = row.get("image_url")
        if pd.isna(url):
            continue
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # Tentukan nama file (pakai id agar unik)
            filename = os.path.join(output_dir, f"{row['id']}.jpg")

            with open(filename, "wb") as f:
                f.write(response.content)

            success += 1
            print(f"[OK] {filename}")
        except Exception as e:
            fail += 1
            print(f"[FAIL] {url}: {e}")

    print(f"\nSelesai. Berhasil: {success}, Gagal: {fail}")

if __name__ == "__main__":
    # Jalankan fungsi utama
    download_images("data/raw/news/metadata_news_final.csv", "data/raw/news/images")