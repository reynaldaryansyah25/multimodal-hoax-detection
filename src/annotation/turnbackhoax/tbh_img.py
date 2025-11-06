import os
import csv
import time
import random
import requests
import pandas as pd
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Dict, List

# ============== KONFIGURASI ==============
OUTPUT_DIR = "./data/raw/turnbackhoax/"
CSV_FILE = os.path.join(OUTPUT_DIR, "metadata/Turnbackhoax.csv")
IMAGES_DIR = os.path.join(OUTPUT_DIR, "images")

os.makedirs(IMAGES_DIR, exist_ok=True)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
HEADERS = {"User-Agent": USER_AGENT}

# ============== FUNGSI DOWNLOAD ==============
def download_gambar(url: str, save_path: str, max_retries: int = 3) -> bool:
    """
    Download satu gambar dari URL dan simpan ke path lokal
    Retry otomatis jika gagal dengan exponential backoff
    Mengembalikan True jika sukses, False jika gagal
    """
    if os.path.exists(save_path):
        return True
    
    backoff = 1.0
    for attempt in range(max_retries):
        try:
            time.sleep(random.uniform(0.3, 0.8))
            response = requests.get(url, headers=HEADERS, timeout=10)
            
            if response.status_code == 200:
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                return True
            
            if response.status_code in (429, 403):
                time.sleep(backoff)
                backoff = min(backoff * 2, 10)
                continue
            
            if response.status_code == 404:
                return False
                
        except requests.RequestException as e:
            time.sleep(backoff)
            backoff = min(backoff * 2, 10)
    
    return False

def ambil_ekstensi_file(url: str) -> str:
    """
    Mengekstrak ekstensi file dari URL
    Mendukung jpg, jpeg, png, gif, webp
    Default ke jpg jika tidak bisa ditentukan
    """
    try:
        path = url.split('?')[0]
        if '.' in path:
            ext = path.split('.')[-1].lower()
            if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                return ext
    except:
        pass
    return 'jpg'

def baca_csv_untuk_gambar() -> List[Dict]:
    """
    Membaca CSV dan mengekstrak data gambar
    Mengembalikan list dict dengan id dan thumbnail URL
    """
    data = []
    try:
        df = pd.read_csv(CSV_FILE)
        print(f"CSV loaded: {len(df)} rows")
        
        for idx, row in df.iterrows():
            article_id = row['id']
            thumbnail = str(row['thumbnail']) if pd.notna(row['thumbnail']) else ""
            
            if thumbnail and thumbnail != "" and thumbnail != "nan":
                data.append({
                    'id': article_id,
                    'thumbnail': thumbnail
                })
    except Exception as e:
        print(f"Error membaca CSV: {e}")
    
    return data

def tulis_progress_download(article_id: str, status: str, file_size_mb: float = 0):
    """
    Mencatat progress download ke file log
    Untuk tracking dan resume
    """
    log_file = os.path.join(OUTPUT_DIR, "metadata/download_log.txt")
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} | {article_id} | {status} | Size: {file_size_mb:.2f}MB\n"
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_entry)

def hitung_ukuran_file(filepath: str) -> float:
    """
    Menghitung ukuran file dalam MB
    """
    if os.path.exists(filepath):
        return os.path.getsize(filepath) / (1024 * 1024)
    return 0.0

def jalankan_download_gambar(max_workers: int = 4, skip_existing: bool = True):
    """
    Menjalankan download gambar secara paralel
    Membuat folder per artikel untuk organisasi
    
    max_workers: jumlah thread concurrent download
    skip_existing: skip jika file sudah ada
    """
    
    print("=" * 80)
    print("DOWNLOAD GAMBAR DARI CSV")
    print("=" * 80)
    
    if not os.path.exists(CSV_FILE):
        print(f"CSV tidak ditemukan: {CSV_FILE}")
        print(f"Jalankan tbh_scraper_clean.py dulu!")
        return
    
    print(f"\nMembaca data dari: {CSV_FILE}")
    data = baca_csv_untuk_gambar()
    
    if not data:
        print("Tidak ada gambar dalam CSV")
        return
    
    print(f"Total artikel dengan gambar: {len(data)}")
    print(f"Workers: {max_workers}")
    print(f"Penyimpanan: {IMAGES_DIR}")
    print("=" * 80)
    
    total_downloaded = 0
    total_failed = 0
    total_size_mb = 0.0
    
    def download_task(item: Dict) -> Dict:
        """
        Task untuk download satu gambar
        """
        article_id = item['id']
        thumbnail_url = item['thumbnail']
        
        article_dir = os.path.join(IMAGES_DIR, article_id)
        
        # Skip jika sudah ada dan skip_existing = True
        existing_files = []
        if os.path.exists(article_dir):
            existing_files = os.listdir(article_dir)
        
        if skip_existing and existing_files:
            return {
                'id': article_id,
                'downloaded': 0,
                'failed': 0,
                'skipped': len(existing_files),
                'size_mb': sum(hitung_ukuran_file(os.path.join(article_dir, f)) for f in existing_files)
            }
        
        # Download gambar
        os.makedirs(article_dir, exist_ok=True)
        
        ext = ambil_ekstensi_file(thumbnail_url)
        filename = f"image_1.{ext}"
        filepath = os.path.join(article_dir, filename)
        
        downloaded = 0
        failed = 0
        size_mb = 0.0
        
        if download_gambar(thumbnail_url, filepath):
            downloaded = 1
            size_mb = hitung_ukuran_file(filepath)
        else:
            failed = 1
        
        tulis_progress_download(article_id, f"downloaded={downloaded}, failed={failed}")
        
        return {
            'id': article_id,
            'downloaded': downloaded,
            'failed': failed,
            'skipped': 0,
            'size_mb': size_mb
        }
    
    print("\nMulai download gambar...\n")
    processed = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(download_task, item): item for item in data}
        
        for future in as_completed(futures):
            processed += 1
            try:
                result = future.result()
                total_downloaded += result['downloaded']
                total_failed += result['failed']
                total_size_mb += result['size_mb']
                
                if processed % 100 == 0:
                    print(f"Progress: {processed}/{len(data)} | "
                          f"Downloaded: {total_downloaded} | "
                          f"Failed: {total_failed} | "
                          f"Size: {total_size_mb:.2f}MB")
                
            except Exception as e:
                print(f"Error: {e}")
    
    print("\n" + "=" * 80)
    print("DOWNLOAD SELESAI")
    print("=" * 80)
    print(f"Total artikel diproses: {processed}")
    print(f"Gambar berhasil: {total_downloaded}")
    print(f"Gambar gagal: {total_failed}")
    print(f"Total ukuran: {total_size_mb:.2f} MB")
    print(f"Folder penyimpanan: {IMAGES_DIR}")
    print("=" * 80)
    print(f"\nLog progress: {os.path.join(OUTPUT_DIR, 'metadata/download_log.txt')}")

def tampilkan_statistik_gambar():
    """
    Menampilkan statistik download gambar
    Folder structure dan ukuran storage
    """
    
    print("\n" + "=" * 80)
    print("STATISTIK GAMBAR")
    print("=" * 80)
    
    if not os.path.exists(IMAGES_DIR):
        print("Folder gambar belum ada")
        return
    
    total_files = 0
    total_size_mb = 0
    articles_with_images = 0
    
    for article_folder in os.listdir(IMAGES_DIR):
        article_path = os.path.join(IMAGES_DIR, article_folder)
        if os.path.isdir(article_path):
            articles_with_images += 1
            for file in os.listdir(article_path):
                file_path = os.path.join(article_path, file)
                if os.path.isfile(file_path):
                    total_files += 1
                    total_size_mb += os.path.getsize(file_path) / (1024 * 1024)
    
    print(f"\nArtikel dengan gambar: {articles_with_images}")
    print(f"Total file gambar: {total_files}")
    print(f"Total ukuran: {total_size_mb:.2f} MB")
    
    if articles_with_images > 0:
        print(f"Rata-rata per artikel: {total_size_mb/articles_with_images:.2f} MB")
        print(f"Rata-rata ukuran file: {total_size_mb/max(total_files, 1):.2f} MB")
    
    print("\nStruktur folder:")
    print(f"{IMAGES_DIR}/")
    print("├── TBH_00001/")
    print("│   └── image_1.jpg")
    print("├── TBH_00002/")
    print("│   └── image_1.png")
    print("└── ...")
    
    print("\n" + "=" * 80)

def bersihkan_folder_gambar():
    """
    Menghapus semua gambar yang sudah didownload
    Untuk reset jika perlu download ulang
    """
    if not os.path.exists(IMAGES_DIR):
        print("Folder gambar tidak ada")
        return
    
    print("Menghapus folder gambar...")
    import shutil
    shutil.rmtree(IMAGES_DIR)
    print("Folder berhasil dihapus")

# ============== MENU UTAMA ==============
def tampilkan_menu():
    """
    Menampilkan menu pilihan download
    """
    print("\n" + "=" * 80)
    print("TURNBACKHOAX IMAGE DOWNLOADER")
    print("=" * 80)
    print("\nPilih opsi:")
    print("1. Download gambar (normal)")
    print("2. Download gambar (skip existing)")
    print("3. Lihat statistik gambar")
    print("4. Hapus semua gambar")
    print("5. Download + Statistik")
    print("0. Keluar")
    print("\n" + "=" * 80)
    
    while True:
        choice = input("\nPilihan (0-5): ").strip()
        
        if choice == "1":
            jalankan_download_gambar(max_workers=4, skip_existing=False)
        elif choice == "2":
            jalankan_download_gambar(max_workers=4, skip_existing=True)
        elif choice == "3":
            tampilkan_statistik_gambar()
        elif choice == "4":
            confirm = input("Yakin hapus semua gambar? (y/n): ").strip().lower()
            if confirm == 'y':
                bersihkan_folder_gambar()
        elif choice == "5":
            jalankan_download_gambar(max_workers=4, skip_existing=True)
            tampilkan_statistik_gambar()
        elif choice == "0":
            print("Keluar...")
            break
        else:
            print("Pilihan tidak valid")

# ============== ENTRY POINT ==============
if __name__ == "__main__":
    tampilkan_menu()
