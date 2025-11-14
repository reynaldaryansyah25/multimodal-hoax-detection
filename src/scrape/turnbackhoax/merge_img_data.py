import pandas as pd
import os
import json
from pathlib import Path
from typing import Dict, List, Any
import shutil

# ============== KONFIGURASI ==============
INPUT_CSV = "./data/raw/turnbackhoax/metadata/turnbackhoax_fix.csv"
IMAGES_DIR = "./data/raw/turnbackhoax/images"
OUTPUT_CSV = "./data/raw/turnbackhoax/tbh_complete_dataset1.csv"
OUTPUT_JSON = "./data/raw/turnbackhoax/tbh_dataset_info.json"

# ============== FUNGSI UTAMA ==============
def gabung_tbh_gambar():
    """
    Gabungkan data TBH CSV dengan gambar yang sudah didownload
    Auto-label semua data sebagai HOAX (0) karena dari TurnBackHoax
    """
    
    print("=" * 80)
    print("🔄 GABUNG TBH + GAMBAR - AUTO-LABEL HOAX")
    print("=" * 80)
    
    # Load CSV
    print("\n[1/4] 📊 Load CSV TBH...")
    if not os.path.exists(INPUT_CSV):
        print(f"❌ File CSV tidak ditemukan: {INPUT_CSV}")
        print("💡 Pastikan sudah menjalankan scraper terlebih dahulu!")
        return None
    
    try:
        df = pd.read_csv(INPUT_CSV)
        print(f"✅ CSV loaded: {len(df)} baris")
        print(f"📋 Kolom: {list(df.columns)}")
    except Exception as e:
        print(f"❌ Gagal load CSV: {e}")
        return None

    # Validasi dan clean data
    print("\n[2/4] 🧹 Validasi dan clean data...")
    
    # Handle missing values
    df_clean = df.copy()
    
    # Fill missing values
    text_columns = ['blog_title', 'post_text', 'blog_check', 'blog_conclusion']
    for col in text_columns:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].fillna('')
    
    # Clean thumbnail URLs
    if 'thumbnail' in df_clean.columns:
        df_clean['thumbnail'] = df_clean['thumbnail'].apply(
            lambda x: '' if pd.isna(x) or str(x).lower() in ['nan', 'null', 'none', ''] else str(x)
        )
    
    # AUTO-LABEL: Karena semua data dari TurnBackHoax adalah HOAX terverifikasi
    print("🏷️  Auto-label semua data sebagai HOAX (label = 0)...")
    df_clean['label'] = 0  # 0 = HOAX
    
    # Validasi data penting
    required_columns = ['id', 'blog_title', 'post_text']
    missing_columns = [col for col in required_columns if col not in df_clean.columns]
    if missing_columns:
        print(f"❌ Kolom penting tidak ditemukan: {missing_columns}")
        return None
    
    print(f"✅ Data cleaned: {len(df_clean)} baris valid")
    print(f"✅ Auto-label: Semua {len(df_clean)} baris diberi label HOAX (0)")

    # Mapping ke format unified dengan informasi lengkap
    print("\n[3/4] 📝 Mapping ke format unified...")
    
    df_output = pd.DataFrame({
        # Basic Info
        'id': df_clean['id'],
        'source': 'turnbackhoax',
        'source_type': 'fact_check',
        
        # Content
        'title': df_clean['blog_title'],
        'text': df_clean['post_text'],
        'full_content': df_clean.apply(
            lambda row: f"{row.get('blog_title', '')}. {row.get('post_text', '')}. {row.get('blog_check', '')}",
            axis=1
        ),
        
        # Metadata
        'date': df_clean['blog_date'],
        'post_date': df_clean['post_date'],
        'category': df_clean.get('categories', ''),
        'flag': df_clean.get('flag', 'SALAH'),
        'social_media': df_clean.get('social_media', ''),
        
        # Labels - SEMUA HOAX karena dari TurnBackHoax
        'label': df_clean['label'],  # 0 = hoax
        'label_text': 'hoax',  # Semua sama
        'verification_status': 'verified_false',  # Semua hoax terverifikasi
        'confidence_score': 1.0,  # High confidence karena dari sumber terpercaya
        
        # Media & URLs
        'image_path': '',  # Akan diisi dengan path lokal
        'thumbnail_url': df_clean.get('thumbnail', ''),  # Original thumbnail URL
        'post_url': df_clean.get('post_url', ''),
        'archive_url': df_clean.get('archive_url', ''),
        'blog_url': df_clean.get('blog_url', ''),
        
        # Engagement Metrics
        'views': df_clean.get('post_view', 0),
        'likes': df_clean.get('post_likes', 0),
        'comments': df_clean.get('post_comment', 0),
        'shares': df_clean.get('post_share', 0),
        
        # Verification Info
        'verification_process': df_clean.get('blog_check', ''),
        'conclusion': df_clean.get('blog_conclusion', ''),
        'fact_checker': 'TurnBackHoax/Mafindo',
        
        # Technical Info
        'has_local_image': False,  # Akan diupdate
        'image_file_name': '',  # Nama file gambar
        'image_file_size_mb': 0.0,  # Ukuran file
        'image_download_status': 'not_found',  # Akan diupdate
    })

    # Cari dan link gambar lokal untuk setiap artikel
    print("\n[4/4] 🔗 Link gambar lokal...")
    
    articles_with_images = 0
    total_image_size_mb = 0.0
    image_stats = {
        'jpg': 0, 'png': 0, 'gif': 0, 'webp': 0, 'other': 0
    }
    
    for idx, row in df_output.iterrows():
        article_id = str(row['id']).strip()
        
        # Multiple strategies untuk menemukan folder gambar
        possible_folders = [
            article_id,  # Exact match
            str(article_id).replace(' ', '_'),  # Dengan underscore
            str(article_id).replace('-', '_'),  # Replace dash
            f"article_{article_id}",  # Dengan prefix
            f"tb_{article_id}",  # Dengan prefix turnbackhoax
            f"id_{article_id}",  # Dengan prefix id
        ]
        
        image_found = False
        image_info = {}
        
        for folder_name in possible_folders:
            article_image_dir = os.path.join(IMAGES_DIR, folder_name)
            
            if os.path.exists(article_image_dir) and os.path.isdir(article_image_dir):
                images = [f for f in os.listdir(article_image_dir) 
                         if os.path.isfile(os.path.join(article_image_dir, f)) and
                         f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'))]
                
                if images:
                    # Ambil gambar pertama (biasanya thumbnail)
                    images.sort()
                    image_file = images[0]
                    image_path = os.path.join(article_image_dir, image_file)
                    
                    # Dapatkan info file
                    if os.path.exists(image_path):
                        file_size_mb = os.path.getsize(image_path) / (1024 * 1024)
                        file_ext = image_file.split('.')[-1].lower() if '.' in image_file else 'other'
                        
                        # Update stats
                        if file_ext in image_stats:
                            image_stats[file_ext] += 1
                        else:
                            image_stats['other'] += 1
                        
                        # Gunakan relative path untuk portability
                        image_path_rel = os.path.relpath(image_path)
                        
                        # Update dataframe
                        df_output.at[idx, 'image_path'] = image_path_rel
                        df_output.at[idx, 'has_local_image'] = True
                        df_output.at[idx, 'image_file_name'] = image_file
                        df_output.at[idx, 'image_file_size_mb'] = file_size_mb
                        df_output.at[idx, 'image_download_status'] = 'success'
                        
                        articles_with_images += 1
                        total_image_size_mb += file_size_mb
                        image_found = True
                        break
        
        if not image_found:
            # Update status untuk artikel tanpa gambar
            df_output.at[idx, 'image_download_status'] = 'not_found'
        
        # Progress reporting
        if (idx + 1) % 100 == 0:
            print(f"  Progress: {idx + 1}/{len(df_output)} - Found: {articles_with_images} images")
    
    # Save hasil gabungan
    print(f"\n💾 Menyimpan ke: {OUTPUT_CSV}")
    try:
        df_output.to_csv(OUTPUT_CSV, index=False, encoding='utf-8')
        print("✅ CSV berhasil disimpan")
    except Exception as e:
        print(f"❌ Gagal menyimpan CSV: {e}")
        return None

    # Generate dataset info
    print(f"\n📊 Generate dataset info...")
    dataset_info = generate_dataset_info(df_output, articles_with_images, total_image_size_mb, image_stats)
    
    try:
        with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
            json.dump(dataset_info, f, indent=2, ensure_ascii=False)
        print(f"✅ Dataset info disimpan: {OUTPUT_JSON}")
    except Exception as e:
        print(f"❌ Gagal menyimpan info: {e}")

    # Tampilkan statistik lengkap
    print("\n" + "=" * 80)
    print("📈 HASIL GABUNGAN - KOMPREHENSIF")
    print("=" * 80)
    
    print_statistics(df_output, dataset_info)
    
    return df_output

def generate_dataset_info(df: pd.DataFrame, articles_with_images: int, 
                         total_image_size_mb: float, image_stats: Dict) -> Dict:
    """Generate comprehensive dataset information"""
    
    # Basic stats
    total_articles = len(df)
    articles_without_images = total_articles - articles_with_images
    
    # Label distribution (semua hoax)
    label_counts = {0: total_articles}  # Semua label 0
    label_text_counts = {'hoax': total_articles}  # Semua hoax
    
    # Date range
    date_range = {
        'min': df['date'].min() if 'date' in df.columns and not df['date'].isna().all() else 'N/A',
        'max': df['date'].max() if 'date' in df.columns and not df['date'].isna().all() else 'N/A'
    }
    
    # Social media distribution
    social_media_counts = df['social_media'].value_counts().to_dict() if 'social_media' in df.columns else {}
    
    # Flag distribution
    flag_counts = df['flag'].value_counts().to_dict() if 'flag' in df.columns else {}
    
    # Text length stats
    df['text_length'] = df['text'].str.len()
    text_length_stats = {
        'min': int(df['text_length'].min()),
        'max': int(df['text_length'].max()),
        'mean': float(df['text_length'].mean()),
        'median': float(df['text_length'].median())
    }
    
    # Engagement stats
    engagement_stats = {}
    for metric in ['views', 'likes', 'comments', 'shares']:
        if metric in df.columns:
            engagement_stats[metric] = {
                'min': int(df[metric].min()),
                'max': int(df[metric].max()),
                'mean': float(df[metric].mean()),
                'median': float(df[metric].median())
            }
    
    # Image download stats
    download_status_counts = df['image_download_status'].value_counts().to_dict() if 'image_download_status' in df.columns else {}
    
    return {
        'dataset_info': {
            'name': 'TurnBackHoax Political Hoax Dataset',
            'version': '1.0',
            'created_date': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
            'description': 'Dataset berita hoax politik Indonesia dari TurnBackHoax - SEMUA DATA HOAX TERVERIFIKASI',
            'label_notes': 'Semua data diberi label HOAX (0) karena berasal dari TurnBackHoax fact-check'
        },
        'statistics': {
            'total_articles': total_articles,
            'articles_with_images': articles_with_images,
            'articles_without_images': articles_without_images,
            'image_coverage_percentage': round(articles_with_images / total_articles * 100, 2),
            'total_image_size_mb': round(total_image_size_mb, 2),
            'average_image_size_mb': round(total_image_size_mb / max(articles_with_images, 1), 2)
        },
        'image_statistics': {
            'format_distribution': image_stats,
            'total_images': articles_with_images,
            'download_status': download_status_counts
        },
        'label_distribution': {
            'numeric': label_counts,
            'text': label_text_counts,
            'note': 'ALL HOAX - Verified by TurnBackHoax'
        },
        'date_range': date_range,
        'social_media_distribution': social_media_counts,
        'flag_distribution': flag_counts,
        'text_statistics': text_length_stats,
        'engagement_statistics': engagement_stats,
        'files': {
            'csv_path': OUTPUT_CSV,
            'json_path': OUTPUT_JSON,
            'images_directory': IMAGES_DIR,
            'source_csv': INPUT_CSV
        }
    }

def print_statistics(df: pd.DataFrame, dataset_info: Dict):
    """Print comprehensive statistics"""
    
    stats = dataset_info['statistics']
    label_dist = dataset_info['label_distribution']
    image_stats = dataset_info['image_statistics']
    
    print(f"\n📊 STATISTIK UTAMA:")
    print(f"   Total artikel: {stats['total_articles']:,}")
    print(f"   Artikel dengan gambar: {stats['articles_with_images']:,} ({stats['image_coverage_percentage']}%)")
    print(f"   Artikel tanpa gambar: {stats['articles_without_images']:,}")
    print(f"   Total ukuran gambar: {stats['total_image_size_mb']:.2f} MB")
    print(f"   Rata-rata ukuran gambar: {stats['average_image_size_mb']:.2f} MB")
    
    print(f"\n🎯 DISTRIBUSI LABEL:")
    print(f"   🚨 SEMUA DATA: HOAX (Label 0) - {stats['total_articles']:,} artikel")
    print(f"   💡 Keterangan: Semua dari TurnBackHoax (fact-check terverifikasi)")
    
    print(f"\n🖼️  STATISTIK GAMBAR:")
    for format_type, count in image_stats['format_distribution'].items():
        if count > 0:
            percentage = (count / stats['articles_with_images']) * 100
            print(f"   {format_type.upper()}: {count:,} ({percentage:.1f}%)")
    
    # Download status
    if 'download_status' in image_stats:
        print(f"\n📥 STATUS DOWNLOAD GAMBAR:")
        for status, count in image_stats['download_status'].items():
            percentage = (count / stats['total_articles']) * 100
            print(f"   {status}: {count:,} ({percentage:.1f}%)")
    
    print(f"\n📅 RENTANG TANGGAL:")
    date_range = dataset_info['date_range']
    print(f"   Dari: {date_range['min']}")
    print(f"   Sampai: {date_range['max']}")
    
    if 'social_media_distribution' in dataset_info:
        print(f"\n📱 DISTRIBUSI SOCIAL MEDIA:")
        social_media = dataset_info['social_media_distribution']
        for platform, count in list(social_media.items())[:5]:  # Top 5
            percentage = (count / stats['total_articles']) * 100
            print(f"   {platform}: {count:,} ({percentage:.1f}%)")
    
    print(f"\n📏 STATISTIK TEKS:")
    text_stats = dataset_info['text_statistics']
    print(f"   Panjang min: {text_stats['min']:,} karakter")
    print(f"   Panjang max: {text_stats['max']:,} karakter")
    print(f"   Rata-rata: {text_stats['mean']:,.0f} karakter")
    print(f"   Median: {text_stats['median']:,.0f} karakter")
    
    print(f"\n💾 FILE OUTPUT:")
    files = dataset_info['files']
    print(f"   CSV: {files['csv_path']}")
    print(f"   JSON: {files['json_path']}")
    print(f"   Images: {files['images_directory']}")

def validate_dataset_integrity(df: pd.DataFrame):
    """Validasi integritas dataset"""
    print("\n" + "=" * 80)
    print("🔍 VALIDASI INTEGRITAS DATASET")
    print("=" * 80)
    
    issues = []
    warnings = []
    
    # Cek missing values
    required_columns = ['id', 'title', 'text']
    for col in required_columns:
        missing_count = df[col].isna().sum()
        if missing_count > 0:
            issues.append(f"❌ {col}: {missing_count} missing values")
        else:
            print(f"✅ {col}: No missing values")
    
    # Cek duplicate IDs
    duplicate_ids = df['id'].duplicated().sum()
    if duplicate_ids > 0:
        issues.append(f"❌ Duplicate IDs: {duplicate_ids}")
    else:
        print(f"✅ IDs: No duplicates")
    
    # Cek label consistency (harus semua 0)
    unique_labels = df['label'].unique()
    if len(unique_labels) != 1 or unique_labels[0] != 0:
        issues.append(f"❌ Label inconsistency: {unique_labels} (should be all 0)")
    else:
        print(f"✅ Labels: All HOAX (0) - Consistent")
    
    # Cek text length
    short_texts = (df['text'].str.len() < 10).sum()
    if short_texts > 0:
        warnings.append(f"⚠️  Short texts (<10 chars): {short_texts}")
    else:
        print(f"✅ Texts: Minimum length OK")
    
    # Cek image paths
    valid_image_paths = df['has_local_image'].sum()
    image_coverage = (valid_image_paths / len(df)) * 100
    print(f"✅ Images: {valid_image_paths} valid local images ({image_coverage:.1f}% coverage)")
    
    if image_coverage < 50:
        warnings.append(f"⚠️  Low image coverage: {image_coverage:.1f}%")
    
    # Tampilkan issues jika ada
    if issues:
        print(f"\n🚨 ISSUES DITEMUKAN:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print(f"\n🎉 SEMUA VALIDASI BERHASIL!")
    
    if warnings:
        print(f"\n⚠️  PERINGATAN:")
        for warning in warnings:
            print(f"   {warning}")
    
    return len(issues) == 0

def backup_dataset():
    """Buat backup dataset"""
    backup_dir = "./data/backups"
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    backup_csv = os.path.join(backup_dir, f"tbh_dataset_backup_{timestamp}.csv")
    backup_json = os.path.join(backup_dir, f"tbh_dataset_backup_{timestamp}.json")
    
    try:
        if os.path.exists(OUTPUT_CSV):
            shutil.copy2(OUTPUT_CSV, backup_csv)
        if os.path.exists(OUTPUT_JSON):
            shutil.copy2(OUTPUT_JSON, backup_json)
        print(f"✅ Backup created: {backup_csv}")
    except Exception as e:
        print(f"❌ Backup failed: {e}")

# ============== FUNGSI TAMBAHAN ==============
def explore_dataset():
    """Jelajahi dataset yang sudah digabungkan"""
    if not os.path.exists(OUTPUT_CSV):
        print("❌ Dataset belum digabungkan. Jalankan gabung_tbh_gambar() dulu.")
        return
    
    df = pd.read_csv(OUTPUT_CSV)
    
    print("\n" + "=" * 80)
    print("🔍 EXPLORE DATASET")
    print("=" * 80)
    
    print(f"\n📊 Shape: {df.shape}")
    print(f"📋 Columns: {list(df.columns)}")
    
    print(f"\n🎯 Sample data (3 baris pertama):")
    print("-" * 80)
    for idx, row in df.head(3).iterrows():
        print(f"\n{idx+1}. ID: {row['id']}")
        print(f"   Title: {row['title'][:80]}...")
        print(f"   Label: {row['label']} ({row['label_text']})")
        print(f"   Date: {row['date']}")
        print(f"   Has Image: {row['has_local_image']}")
        if row['has_local_image']:
            print(f"   Image: {row['image_file_name']} ({row['image_file_size_mb']:.2f} MB)")
        print(f"   Social Media: {row['social_media']}")
        print(f"   Flag: {row['flag']}")
        print(f"   Download Status: {row['image_download_status']}")

def get_dataset_summary():
    """Dapatkan summary dataset"""
    if not os.path.exists(OUTPUT_JSON):
        print("❌ Dataset info tidak ditemukan.")
        return
    
    with open(OUTPUT_JSON, 'r', encoding='utf-8') as f:
        info = json.load(f)
    
    print("\n" + "=" * 80)
    print("📋 DATASET SUMMARY")
    print("=" * 80)
    
    dataset_info = info['dataset_info']
    stats = info['statistics']
    
    print(f"\n📝 {dataset_info['name']}")
    print(f"🕒 Created: {dataset_info['created_date']}")
    print(f"📖 {dataset_info['description']}")
    print(f"💡 {dataset_info['label_notes']}")
    
    print(f"\n📊 Key Statistics:")
    print(f"   📄 Total Articles: {stats['total_articles']:,}")
    print(f"   🖼️  With Images: {stats['articles_with_images']:,} ({stats['image_coverage_percentage']}%)")
    print(f"   💾 Total Size: {stats['total_image_size_mb']:.2f} MB")
    print(f"   🚨 All Labeled: HOAX (Verified by TurnBackHoax)")

# ============== MENU UTAMA ==============
def main():
    """Menu utama"""
    print("=" * 80)
    print("🔄 TBH DATASET MERGER - AUTO-LABEL HOAX")
    print("=" * 80)
    
    while True:
        print(f"\n🎯 Pilih opsi:")
        print("1. 🔄 Gabungkan data + gambar (Auto-label HOAX)")
        print("2. 🔍 Validasi integritas dataset") 
        print("3. 📊 Explore dataset")
        print("4. 📋 Lihat summary")
        print("5. 💾 Buat backup")
        print("6. 🚀 Gabung + Validasi + Backup")
        print("0. ❌ Keluar")
        
        choice = input("\n🎲 Pilihan (0-6): ").strip()
        
        if choice == "1":
            result_df = gabung_tbh_gambar()
            if result_df is not None:
                validate_dataset_integrity(result_df)
        elif choice == "2":
            if os.path.exists(OUTPUT_CSV):
                df = pd.read_csv(OUTPUT_CSV)
                validate_dataset_integrity(df)
            else:
                print("❌ Dataset belum digabungkan.")
        elif choice == "3":
            explore_dataset()
        elif choice == "4":
            get_dataset_summary()
        elif choice == "5":
            backup_dataset()
        elif choice == "6":
            result_df = gabung_tbh_gambar()
            if result_df is not None:
                validate_dataset_integrity(result_df)
                backup_dataset()
        elif choice == "0":
            print("👋 Keluar...")
            break
        else:
            print("❌ Pilihan tidak valid")

# ============== JALANKAN LANGSUNG ==============
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "merge":
            gabung_tbh_gambar()
        elif sys.argv[1] == "validate":
            if os.path.exists(OUTPUT_CSV):
                df = pd.read_csv(OUTPUT_CSV)
                validate_dataset_integrity(df)
        elif sys.argv[1] == "explore":
            explore_dataset()
        elif sys.argv[1] == "summary":
            get_dataset_summary()
        elif sys.argv[1] == "backup":
            backup_dataset()
        else:
            print("❌ Argumen tidak valid")
            print("💡 Gunakan: merge, validate, explore, summary, backup")
    else:
        # Jalankan menu interaktif
        main()