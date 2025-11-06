import pandas as pd
import os

# ============== KONFIGURASI ==============
INPUT_CSV = "./data/raw/turnbackhoax/metadata/Turnbackhoax.csv"
IMAGES_DIR = "./data/raw/turnbackhoax/images"
OUTPUT_CSV = "./data/raw/turnbackhoax/metadata/tbh_with_images.csv"

# ============== FUNGSI ==============
def gabung_tbh_gambar():
    """
    Gabung TBH CSV + gambar
    Kolom yang ada: id,blog_date,blog_title,label,social_media,post_text,post_date,
                    blog_check,blog_conclusion,post_view,post_likes,post_comment,post_share,
                    post_url,archive_url,blog_url,thumbnail,categories
    """
    
    print("=" * 80)
    print("GABUNG TBH + GAMBAR")
    print("=" * 80)
    
    # Load CSV
    print("\n[1/3] Load CSV TBH...")
    df = pd.read_csv(INPUT_CSV)
    print(f"  Total baris: {len(df)}")
    
    # Mapping ke unified format
    print("\n[2/3] Mapping ke format unified...")
    
    df_output = pd.DataFrame({
        'id': df['id'],
        'source': 'turnbackhoax',
        'title': df['blog_title'],
        'text': df['post_text'],
        'date': df['blog_date'],
        'category': df['categories'],
        'label': df['label'],
        'image_path': '',  # Akan diisi
        'url': df['post_url'],
        'thumbnail_url': df['thumbnail'],  # Original thumbnail URL
    })
    
    # Cari gambar lokal untuk setiap artikel
    print("\n[3/3] Cari gambar lokal untuk setiap artikel...")
    
    articles_with_images = 0
    
    for idx, row in df_output.iterrows():
        article_id = str(row['id']).strip()
        article_image_dir = os.path.join(IMAGES_DIR, article_id)
        
        # Cek ada gambar lokal atau tidak
        if os.path.exists(article_image_dir):
            images = os.listdir(article_image_dir)
            if images:
                # Ambil gambar pertama
                images.sort()
                image_file = images[0]
                image_path = os.path.join(article_image_dir, image_file)
                
                # Gunakan relative path
                image_path_rel = os.path.relpath(image_path)
                
                df_output.at[idx, 'image_path'] = image_path_rel
                articles_with_images += 1
        
        if (idx + 1) % 500 == 0:
            print(f"  Progress: {idx + 1}/{len(df_output)}")
    
    # Save
    print(f"\nMenyimpan ke: {OUTPUT_CSV}")
    df_output.to_csv(OUTPUT_CSV, index=False, encoding='utf-8')
    
    # Statistik
    print("\n" + "=" * 80)
    print("HASIL GABUNGAN")
    print("=" * 80)
    
    print(f"\nTotal artikel: {len(df_output)}")
    print(f"Artikel dengan gambar lokal: {articles_with_images} ({100*articles_with_images/len(df_output):.1f}%)")
    print(f"Artikel tanpa gambar lokal: {len(df_output) - articles_with_images}")
    
    print(f"\nKolom output:")
    for col in df_output.columns:
        print(f"  - {col}")
    
    print(f"\nSample 3 baris:")
    print("-" * 80)
    for idx, row in df_output.head(3).iterrows():
        print(f"\n{idx+1}. ID: {row['id']}")
        print(f"   Title: {row['title'][:60]}...")
        print(f"   Date: {row['date']}")
        print(f"   Label: {row['label']}")
        print(f"   Image path: {row['image_path'] if row['image_path'] else 'NONE'}")
        print(f"   URL: {row['url']}")
    
    print("\n" + "=" * 80)
    print("SIAP UNTUK PSEUDO-LABELING!")
    print("=" * 80)
    print(f"\nOutput file: {OUTPUT_CSV}")
    print(f"Total: {len(df_output)} articles dengan gambar dan metadata")

# ============== JALANKAN ==============
if __name__ == "__main__":
    gabung_tbh_gambar()
