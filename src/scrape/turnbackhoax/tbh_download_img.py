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
CSV_FILE = os.path.join(OUTPUT_DIR, "metadata/turnbackhoax_fix.csv")  # Updated CSV path
IMAGES_DIR = os.path.join(OUTPUT_DIR, "images")

os.makedirs(IMAGES_DIR, exist_ok=True)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "image",
    "Sec-Fetch-Mode": "no-cors",
    "Sec-Fetch-Site": "cross-site",
}

# ============== FUNGSI DOWNLOAD ==============
def download_gambar(url: str, save_path: str, max_retries: int = 3) -> bool:
    """
    Download satu gambar dari URL dan simpan ke path lokal
    Retry otomatis jika gagal dengan exponential backoff
    Mengembalikan True jika sukses, False jika gagal
    """
    if os.path.exists(save_path):
        print(f"✓ File sudah ada: {save_path}")
        return True
    
    # Validasi URL
    if not url or url.lower() in ['nan', 'null', 'none', '']:
        print(f"✗ URL kosong: {url}")
        return False
    
    if not url.startswith(('http://', 'https://')):
        print(f"✗ URL tidak valid: {url}")
        return False
    
    backoff = 1.0
    for attempt in range(max_retries):
        try:
            time.sleep(random.uniform(0.3, 0.8))
            print(f"📥 Download attempt {attempt+1}: {url[:80]}...")
            
            response = requests.get(
                url, 
                headers=HEADERS, 
                timeout=15,
                stream=True  # Stream untuk file besar
            )
            
            if response.status_code == 200:
                # Cek content type untuk memastikan ini gambar
                content_type = response.headers.get('content-type', '')
                if not content_type.startswith('image/'):
                    print(f"✗ Bukan gambar: {content_type} - {url}")
                    return False
                
                # Cek ukuran file
                content_length = response.headers.get('content-length')
                if content_length and int(content_length) > 50 * 1024 * 1024:  # 50MB limit
                    print(f"✗ File terlalu besar: {int(content_length)/1024/1024:.1f}MB")
                    return False
                
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                
                # Download dengan chunk untuk handle file besar
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                # Verifikasi file berhasil ditulis
                if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
                    file_size = os.path.getsize(save_path) / 1024
                    print(f"✓ Download berhasil: {save_path} ({file_size:.1f} KB)")
                    return True
                else:
                    print(f"✗ File kosong: {save_path}")
                    if os.path.exists(save_path):
                        os.remove(save_path)
                    return False
            
            elif response.status_code == 404:
                print(f"✗ 404 Not Found: {url}")
                return False
                
            elif response.status_code == 403:
                print(f"✗ 403 Forbidden: {url}")
                time.sleep(backoff)
                backoff = min(backoff * 2, 10)
                continue
                
            elif response.status_code == 429:
                print(f"⚠ 429 Too Many Requests: {url}, tunggu {backoff}s")
                time.sleep(backoff)
                backoff = min(backoff * 2, 10)
                continue
                
            else:
                print(f"✗ HTTP {response.status_code}: {url}")
                time.sleep(backoff)
                backoff = min(backoff * 2, 10)
                
        except requests.exceptions.Timeout:
            print(f"✗ Timeout: {url}")
            time.sleep(backoff)
            backoff = min(backoff * 2, 10)
            
        except requests.exceptions.ConnectionError:
            print(f"✗ Connection Error: {url}")
            time.sleep(backoff)
            backoff = min(backoff * 2, 10)
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Request Error: {e} - {url}")
            time.sleep(backoff)
            backoff = min(backoff * 2, 10)
            
        except Exception as e:
            print(f"✗ Unexpected Error: {e} - {url}")
            time.sleep(backoff)
            backoff = min(backoff * 2, 10)
    
    print(f"✗ Gagal setelah {max_retries} attempts: {url}")
    return False

def ambil_ekstensi_file(url: str) -> str:
    """
    Mengekstrak ekstensi file dari URL dengan lebih robust
    Mendukung berbagai format gambar
    """
    if not url:
        return 'jpg'
    
    # Mapping content type to extension
    content_type_map = {
        'image/jpeg': 'jpg',
        'image/jpg': 'jpg', 
        'image/png': 'png',
        'image/gif': 'gif',
        'image/webp': 'webp',
        'image/svg+xml': 'svg',
        'image/bmp': 'bmp'
    }
    
    try:
        # Coba dari URL path
        path = url.split('?')[0].split('#')[0]
        if '.' in path:
            ext = path.split('.')[-1].lower()
            if ext in content_type_map.values():
                return ext
            
        # Fallback: cek dari common patterns
        if 'jpg' in url.lower() or 'jpeg' in url.lower():
            return 'jpg'
        elif 'png' in url.lower():
            return 'png'
        elif 'gif' in url.lower():
            return 'gif'
        elif 'webp' in url.lower():
            return 'webp'
            
    except Exception as e:
        print(f"⚠ Error parse extension: {e}")
    
    return 'jpg'  # Default fallback

def baca_csv_untuk_gambar() -> List[Dict]:
    """
    Membaca CSV dan mengekstrak data gambar dengan filtering yang lebih baik
    """
    data = []
    try:
        df = pd.read_csv(CSV_FILE)
        print(f"📊 CSV loaded: {len(df)} rows")
        
        # Filter rows dengan thumbnail yang valid
        valid_thumbnails = 0
        for idx, row in df.iterrows():
            article_id = row['id']
            thumbnail = str(row['thumbnail']) if pd.notna(row['thumbnail']) else ""
            
            # Filter URL yang valid
            if (thumbnail and 
                thumbnail.strip() != "" and 
                thumbnail.lower() not in ['nan', 'null', 'none'] and
                thumbnail.startswith(('http://', 'https://'))):
                
                data.append({
                    'id': str(article_id).strip(),
                    'thumbnail': thumbnail.strip()
                })
                valid_thumbnails += 1
            else:
                print(f"⚠ Skip invalid thumbnail: ID {article_id}, URL: '{thumbnail}'")
        
        print(f"✅ Valid thumbnails: {valid_thumbnails}/{len(df)}")
        
    except Exception as e:
        print(f"❌ Error membaca CSV: {e}")
        # Fallback: coba baca manual
        try:
            with open(CSV_FILE, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('thumbnail') and row['thumbnail'].startswith(('http://', 'https://')):
                        data.append({
                            'id': row['id'],
                            'thumbnail': row['thumbnail']
                        })
            print(f"✅ Loaded {len(data)} images via manual read")
        except Exception as e2:
            print(f"❌ Juga gagal baca manual: {e2}")
    
    return data

def tulis_progress_download(article_id: str, status: str, file_size_mb: float = 0):
    """
    Mencatat progress download ke file log
    Untuk tracking dan resume
    """
    log_file = os.path.join(OUTPUT_DIR, "download_log.txt")
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} | {article_id} | {status} | Size: {file_size_mb:.2f}MB\n"
    
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_entry)

def hitung_ukuran_file(filepath: str) -> float:
    """
    Menghitung ukuran file dalam MB
    """
    if os.path.exists(filepath):
        return os.path.getsize(filepath) / (1024 * 1024)
    return 0.0

def download_task(item: Dict, skip_existing: bool = True) -> Dict:
    """
    Task untuk download satu gambar dengan error handling yang lebih baik
    """
    article_id = item['id']
    thumbnail_url = item['thumbnail']
    
    # Normalize article_id untuk folder name
    safe_article_id = "".join(c for c in str(article_id) if c.isalnum() or c in ('-', '_'))
    article_dir = os.path.join(IMAGES_DIR, safe_article_id)
    
    # Skip jika sudah ada dan skip_existing = True
    existing_files = []
    if os.path.exists(article_dir):
        existing_files = [f for f in os.listdir(article_dir) 
                         if os.path.isfile(os.path.join(article_dir, f))]
    
    if skip_existing and existing_files:
        total_size = sum(hitung_ukuran_file(os.path.join(article_dir, f)) 
                        for f in existing_files)
        print(f"⏭ Skip existing: {safe_article_id} ({len(existing_files)} files)")
        return {
            'id': safe_article_id,
            'downloaded': 0,
            'failed': 0,
            'skipped': len(existing_files),
            'size_mb': total_size
        }
    
    # Download gambar
    os.makedirs(article_dir, exist_ok=True)
    
    ext = ambil_ekstensi_file(thumbnail_url)
    filename = f"thumbnail.{ext}"
    filepath = os.path.join(article_dir, filename)
    
    downloaded = 0
    failed = 0
    size_mb = 0.0
    
    if download_gambar(thumbnail_url, filepath):
        downloaded = 1
        size_mb = hitung_ukuran_file(filepath)
        status = f"SUCCESS - {size_mb:.2f}MB"
    else:
        failed = 1
        status = "FAILED"
        # Cleanup failed download
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass
    
    tulis_progress_download(safe_article_id, status, size_mb)
    
    return {
        'id': safe_article_id,
        'downloaded': downloaded,
        'failed': failed,
        'skipped': 0,
        'size_mb': size_mb
    }

def validasi_gambar_downloaded():
    """
    Validasi gambar yang sudah didownload
    Cek file corruption dan integrity
    """
    print("\n" + "=" * 80)
    print("VALIDASI GAMBAR")
    print("=" * 80)
    
    if not os.path.exists(IMAGES_DIR):
        print("❌ Folder gambar tidak ada")
        return 0, 0, 0
    
    valid_files = 0
    corrupted_files = 0
    zero_size_files = 0
    
    for article_folder in os.listdir(IMAGES_DIR):
        article_path = os.path.join(IMAGES_DIR, article_folder)
        if os.path.isdir(article_path):
            for file in os.listdir(article_path):
                file_path = os.path.join(article_path, file)
                if os.path.isfile(file_path):
                    file_size = os.path.getsize(file_path)
                    
                    if file_size == 0:
                        zero_size_files += 1
                        print(f"⚠ Zero size: {file_path}")
                        # Optional: hapus file corrupt
                        # os.remove(file_path)
                    
                    elif file_size < 100:  # File terlalu kecil, mungkin corrupt
                        corrupted_files += 1
                        print(f"⚠ Possibly corrupt (small): {file_path}")
                    
                    else:
                        valid_files += 1
    
    print(f"\n📊 Hasil Validasi:")
    print(f"✅ Valid files: {valid_files}")
    print(f"⚠ Zero size: {zero_size_files}") 
    print(f"❌ Corrupted: {corrupted_files}")
    print(f"📁 Total folders: {len(os.listdir(IMAGES_DIR))}")
    
    return valid_files, corrupted_files, zero_size_files

def jalankan_download_gambar(max_workers: int = 4, skip_existing: bool = True):
    """
    Menjalankan download gambar secara paralel dengan progress yang lebih baik
    """
    
    print("=" * 80)
    print("📥 DOWNLOAD GAMBAR DARI CSV - IMPROVED")
    print("=" * 80)
    
    if not os.path.exists(CSV_FILE):
        print(f"❌ CSV tidak ditemukan: {CSV_FILE}")
        print(f"💡 Jalankan scraper dulu!")
        return
    
    print(f"\n📊 Membaca data dari: {CSV_FILE}")
    data = baca_csv_untuk_gambar()
    
    if not data:
        print("❌ Tidak ada gambar valid dalam CSV")
        return
    
    print(f"✅ Total artikel dengan gambar: {len(data)}")
    print(f"👷 Workers: {max_workers}")
    print(f"💾 Penyimpanan: {IMAGES_DIR}")
    print("=" * 80)
    
    total_downloaded = 0
    total_failed = 0
    total_skipped = 0
    total_size_mb = 0.0
    
    start_time = time.time()
    
    def download_task_with_progress(item: Dict) -> Dict:
        """Wrapper dengan progress tracking"""
        result = download_task(item, skip_existing)
        
        # Real-time progress update
        nonlocal total_downloaded, total_failed, total_skipped, total_size_mb
        total_downloaded += result['downloaded']
        total_failed += result['failed'] 
        total_skipped += result['skipped']
        total_size_mb += result['size_mb']
        
        return result
    
    print("\n🚀 Mulai download gambar...\n")
    processed = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(download_task_with_progress, item): item for item in data}
        
        for future in as_completed(futures):
            processed += 1
            try:
                result = future.result(timeout=60)  # Timeout per task
                
                if processed % 10 == 0 or processed == len(data):
                    elapsed = time.time() - start_time
                    rate = processed / elapsed if elapsed > 0 else 0
                    remaining = len(data) - processed
                    eta = remaining / rate if rate > 0 else 0
                    
                    print(f"📈 Progress: {processed}/{len(data)} "
                          f"({processed/len(data)*100:.1f}%) | "
                          f"Rate: {rate:.1f} items/sec | "
                          f"ETA: {eta:.0f}s | "
                          f"Downloaded: {total_downloaded} | "
                          f"Failed: {total_failed} | "
                          f"Skipped: {total_skipped}")
                
            except Exception as e:
                print(f"❌ Task error: {e}")
                total_failed += 1
    
    # Final statistics
    elapsed_time = time.time() - start_time
    print("\n" + "=" * 80)
    print("✅ DOWNLOAD SELESAI")
    print("=" * 80)
    print(f"⏱️  Waktu: {elapsed_time:.1f} detik")
    print(f"📊 Total diproses: {processed}")
    print(f"✅ Berhasil: {total_downloaded}")
    print(f"❌ Gagal: {total_failed}")
    print(f"⏭️  Skipped: {total_skipped}")
    print(f"💾 Total ukuran: {total_size_mb:.2f} MB")
    print(f"📁 Folder: {IMAGES_DIR}")
    
    # Validasi hasil
    if total_downloaded > 0:
        print(f"\n🔍 Melakukan validasi...")
        valid_files, corrupted_files, zero_size_files = validasi_gambar_downloaded()
        
        # Summary
        print(f"\n📋 SUMMARY:")
        print(f"   Total folders created: {len(os.listdir(IMAGES_DIR))}")
        print(f"   Valid images: {valid_files}")
        print(f"   Corrupted images: {corrupted_files}")
        print(f"   Zero-size files: {zero_size_files}")
    
    print("=" * 80)
    print(f"\n📝 Log: {os.path.join(OUTPUT_DIR, 'download_log2.txt')}")

def tampilkan_statistik_gambar():
    """
    Menampilkan statistik download gambar
    Folder structure dan ukuran storage
    """
    
    print("\n" + "=" * 80)
    print("STATISTIK GAMBAR")
    print("=" * 80)
    
    if not os.path.exists(IMAGES_DIR):
        print("❌ Folder gambar belum ada")
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
    
    print(f"\n📊 Statistik:")
    print(f"   📁 Artikel dengan gambar: {articles_with_images}")
    print(f"   🖼️  Total file gambar: {total_files}")
    print(f"   💾 Total ukuran: {total_size_mb:.2f} MB")
    
    if articles_with_images > 0:
        print(f"   📐 Rata-rata per artikel: {total_size_mb/articles_with_images:.2f} MB")
        print(f"   📏 Rata-rata ukuran file: {total_size_mb/max(total_files, 1):.2f} MB")
    
    print(f"\n📂 Struktur folder:")
    print(f"   {IMAGES_DIR}/")
    print(f"   ├── article_1/")
    print(f"   │   └── thumbnail.jpg")
    print(f"   ├── article_2/")
    print(f"   │   └── thumbnail.png")
    print(f"   └── ...")
    
    # Show first 5 folders as example
    print(f"\n🎯 Contoh folder (max 5):")
    folders = os.listdir(IMAGES_DIR)[:5]
    for folder in folders:
        folder_path = os.path.join(IMAGES_DIR, folder)
        files = os.listdir(folder_path) if os.path.isdir(folder_path) else []
        print(f"   📁 {folder}: {files}")
    
    print("\n" + "=" * 80)

def bersihkan_folder_gambar():
    """
    Menghapus semua gambar yang sudah didownload
    Untuk reset jika perlu download ulang
    """
    if not os.path.exists(IMAGES_DIR):
        print("❌ Folder gambar tidak ada")
        return
    
    confirm = input("⚠️  Yakin hapus SEMUA gambar? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Dibatalkan")
        return
    
    print("🗑️  Menghapus folder gambar...")
    import shutil
    try:
        shutil.rmtree(IMAGES_DIR)
        print("✅ Folder berhasil dihapus")
        
        # Juga hapus log file
        log_file = os.path.join(OUTPUT_DIR, "download_log2.txt")
        if os.path.exists(log_file):
            os.remove(log_file)
            print("✅ Log file dihapus")
            
    except Exception as e:
        print(f"❌ Gagal menghapus: {e}")

def download_gambar_cepat():
    """
    Mode download cepat dengan workers lebih banyak
    """
    print("\n🚀 MODE CEPAT - 8 Workers")
    print("⚠️  Hati-hati dengan rate limiting!")
    jalankan_download_gambar(max_workers=8, skip_existing=True)

def download_gambar_aman():
    """
    Mode download aman dengan workers sedikit
    """
    print("\n🐢 MODE AMAN - 2 Workers") 
    print("✅ Lebih aman untuk server")
    jalankan_download_gambar(max_workers=2, skip_existing=True)

# ============== MENU UTAMA ==============
def tampilkan_menu():
    """
    Menampilkan menu pilihan download
    """
    print("\n" + "=" * 80)
    print("🖼️  TURNBACKHOAX IMAGE DOWNLOADER - IMPROVED")
    print("=" * 80)
    
    # Check if CSV exists
    csv_exists = os.path.exists(CSV_FILE)
    csv_status = "✅ ADA" if csv_exists else "❌ TIDAK ADA"
    
    # Check if images folder exists
    images_exist = os.path.exists(IMAGES_DIR)
    images_status = "✅ ADA" if images_exist else "❌ TIDAK ADA"
    
    print(f"\n📊 Status:")
    print(f"   CSV File: {CSV_FILE} - {csv_status}")
    print(f"   Images Folder: {IMAGES_DIR} - {images_status}")
    
    if images_exist:
        image_count = len([f for f in os.listdir(IMAGES_DIR) if os.path.isdir(os.path.join(IMAGES_DIR, f))])
        print(f"   📁 Folder gambar: {image_count}")
    
    print("\n🎯 Pilih opsi:")
    print("1. 🚀 Download gambar (cepat - 8 workers)")
    print("2. 🐢 Download gambar (aman - 2 workers)") 
    print("3. ⚡ Download gambar (normal - 4 workers)")
    print("4. 📊 Lihat statistik gambar")
    print("5. 🔍 Validasi gambar yang sudah didownload")
    print("6. 🗑️  Hapus semua gambar (reset)")
    print("7. 📥 Download + Statistik + Validasi")
    print("0. ❌ Keluar")
    print("\n" + "=" * 80)
    
    while True:
        choice = input("\n🎲 Pilihan (0-7): ").strip()
        
        if choice == "1":
            download_gambar_cepat()
        elif choice == "2":
            download_gambar_aman()
        elif choice == "3":
            jalankan_download_gambar(max_workers=4, skip_existing=True)
        elif choice == "4":
            tampilkan_statistik_gambar()
        elif choice == "5":
            validasi_gambar_downloaded()
        elif choice == "6":
            bersihkan_folder_gambar()
        elif choice == "7":
            jalankan_download_gambar(max_workers=4, skip_existing=True)
            tampilkan_statistik_gambar()
            validasi_gambar_downloaded()
        elif choice == "0":
            print("👋 Keluar...")
            break
        else:
            print("❌ Pilihan tidak valid")

def main_direct():
    """
    Jalankan langsung tanpa menu (untuk automation)
    """
    print("🖼️  Menjalankan download gambar secara langsung...")
    jalankan_download_gambar(max_workers=4, skip_existing=True)
    tampilkan_statistik_gambar()

# ============== ENTRY POINT ==============
if __name__ == "__main__":
    # Cek jika ada argumen command line
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "direct":
            main_direct()
        elif sys.argv[1] == "fast":
            download_gambar_cepat()
        elif sys.argv[1] == "safe":
            download_gambar_aman()
        elif sys.argv[1] == "stats":
            tampilkan_statistik_gambar()
        elif sys.argv[1] == "validate":
            validasi_gambar_downloaded()
        elif sys.argv[1] == "clean":
            bersihkan_folder_gambar()
        else:
            print("❌ Argumen tidak valid")
            print("💡 Gunakan: direct, fast, safe, stats, validate, clean")
    else:
        # Jalankan menu interaktif
        tampilkan_menu()