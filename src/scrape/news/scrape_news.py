# --- IMPOR PUSTAKA ---
import os
import time
import json
import re
from datetime import datetime, timezone, timedelta
from urllib.parse import urlsplit
from newspaper import Article
import requests
from bs4 import BeautifulSoup
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- KONFIGURASI AWAL ---
POLITICAL_KEYWORDS = [
    "uu ite", "ruu kuhp", "mahkamah", "kejaksaan", "kpk", "pengadilan", "penegakan hukum",
    "politik", "partai", "pemilu", "pilpres", "pilkada", "kpu", "bawaslu",
    "asn netral", "kabinet", "menteri", "presiden", "wakil presiden", "prabowo", "jokowi",
    "ham", "pelanggaran ham", "komnas ham", "kekerasan aparat", "kebebasan berpendapat", "diskriminasi"
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# Session pool untuk reuse connections
def create_session():
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry, pool_connections=20, pool_maxsize=20)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    session.headers.update(HEADERS)
    return session

SESSION = create_session()

print("Pustaka dan konfigurasi awal telah dimuat.")

# --- KONFIGURASI PATH ---
GDRIVE_BASE_PATH = './data/raw/news'
os.makedirs(GDRIVE_BASE_PATH, exist_ok=True)
print(f"✅ Output akan disimpan di: {GDRIVE_BASE_PATH}")

# ================================================================
# 📰 FUNGSI DISCOVER URL (OPTIMIZED)
# ================================================================

def discover_kompas_urls_with_date(start_date, end_date, max_pages_per_day=5):
    """Paralel scraping per tanggal"""
    print(f"  Kompas: Mencari URL dari {start_date.date()} hingga {end_date.date()}...")
    
    def scrape_date(date_obj):
        urls = []
        date_str = date_obj.strftime("%Y-%m-%d")
        for page in range(1, max_pages_per_day + 1):
            try:
                url = f"https://indeks.kompas.com/?site=all&date={date_str}&page={page}"
                r = SESSION.get(url, timeout=10)
                if r.status_code != 200: break
                
                soup = BeautifulSoup(r.text, 'html.parser')
                links = soup.select('.article-link')
                if not links: break
                
                for link in links:
                    if href := link.get('href'):
                        urls.append(href.split("?")[0])
            except: break
        return urls
    
    dates = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]
    all_urls = []
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        for result in executor.map(scrape_date, dates):
            all_urls.extend(result)
    
    all_urls = list(dict.fromkeys(all_urls))
    print(f"  Kompas: {len(all_urls)} URL ditemukan")
    return [('kompas', u) for u in all_urls]


def discover_detik_urls_with_date(start_date, end_date, limit_per_day=100):
    """Paralel scraping per tanggal"""
    print(f"  Detik: Mencari URL dari {start_date.date()} hingga {end_date.date()}...")
    
    def scrape_date(date_obj):
        urls = []
        date_str = date_obj.strftime("%m/%d/%Y")
        try:
            r = SESSION.get(f"https://news.detik.com/indeks?date={date_str}", timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            for link in soup.select('article h3 a, article h2 a')[:limit_per_day]:
                if href := link.get('href'):
                    urls.append(href)
        except: pass
        return urls
    
    dates = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]
    all_urls = []
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        for result in executor.map(scrape_date, dates):
            all_urls.extend(result)
    
    all_urls = list(dict.fromkeys(all_urls))
    print(f"  Detik: {len(all_urls)} URL ditemukan")
    return [('detik', u) for u in all_urls]


def discover_cnn_urls_with_date(start_date, end_date, max_pages_per_day=5):
    """Paralel scraping per tanggal"""
    print(f"  CNN: Mencari URL dari {start_date.date()} hingga {end_date.date()}...")
    
    def scrape_date(date_obj):
        urls = []
        date_str = date_obj.strftime("%Y/%m/%d")
        for page in range(1, max_pages_per_day + 1):
            try:
                url = f"https://www.cnnindonesia.com/nasional/indeks/3?date={date_str}&page={page}"
                r = SESSION.get(url, timeout=10)
                if r.status_code != 200: break
                
                soup = BeautifulSoup(r.text, 'html.parser')
                links = soup.select('article a')
                if not links: break
                
                for link in links:
                    if href := link.get('href'):
                        urls.append(href)
            except: break
        return urls
    
    dates = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]
    all_urls = []
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        for result in executor.map(scrape_date, dates):
            all_urls.extend(result)
    
    all_urls = list(dict.fromkeys(all_urls))
    print(f"  CNN: {len(all_urls)} URL ditemukan")
    return [('cnn', u) for u in all_urls]


def discover_tempo_urls_paginated(limit=200):
    """Paralel scraping pagination"""
    print(f"  Tempo: Mencari URL dengan paginasi...")
    
    def scrape_page(page):
        urls = []
        try:
            r = SESSION.get(f"https://nasional.tempo.co/indeks/{page}", timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            for link in soup.select('.title a, h2 a'):
                if href := link.get('href'):
                    urls.append(href)
        except: pass
        return urls
    
    all_urls = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        for result in executor.map(scrape_page, range(1, 11)):
            all_urls.extend(result)
            if len(all_urls) >= limit: break
    
    all_urls = list(dict.fromkeys(all_urls))[:limit]
    print(f"  Tempo: {len(all_urls)} URL ditemukan")
    return [('tempo', u) for u in all_urls]


def discover_antaranews_urls_paginated(limit=200):
    """Paralel scraping dengan date range"""
    print(f"  Antara: Mencari URL dengan paginasi...")
    
    def scrape_date(days_ago):
        urls = []
        date_str = (datetime.now() - timedelta(days=days_ago)).strftime("%Y/%m/%d")
        try:
            r = SESSION.get(f"https://www.antaranews.com/arsip/{date_str}", timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            for link in soup.select('.simple-post .post-title a'):
                if href := link.get('href'):
                    urls.append(href)
        except: pass
        return urls
    
    all_urls = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        for result in executor.map(scrape_date, range(30)):
            all_urls.extend(result)
            if len(all_urls) >= limit: break
    
    all_urls = list(dict.fromkeys(all_urls))[:limit]
    print(f"  Antara: {len(all_urls)} URL ditemukan")
    return [('antaranews', u) for u in all_urls]

print("✅ Semua fungsi 'discover' berhasil didefinisikan.")

# ================================================================
# ✍️ FUNGSI SCRAPE ARTIKEL & GAMBAR (OPTIMIZED)
# ================================================================

def extract_thumbnail_accurate(html_content, url):
    """Extract thumbnail dengan caching BeautifulSoup"""
    soup = BeautifulSoup(html_content, 'html.parser')
    for prop in ['og:image', 'twitter:image']:
        tag = soup.find('meta', property=prop) or soup.find('meta', name=prop)
        if tag and tag.get('content'):
            img_url = tag.get('content')
            if 'ads' not in img_url.lower() and 'logo' not in img_url.lower():
                return img_url
    return ""


def scrape_article(url, source_name):
    """Optimized article scraping dengan early filtering"""
    try:
        article = Article(url, language='id', fetch_images=False, memoize_articles=False)
        article.download()
        article.parse()
        
        title, text = article.title or "", article.text or ""
        
        # Early exit untuk artikel tidak relevan
        if len(text) < 150:
            return None
        
        combined_text = f"{title} {text}".lower()
        if not any(kw.lower() in combined_text for kw in POLITICAL_KEYWORDS):
            return None
        
        date_utc = article.publish_date.astimezone(timezone.utc).isoformat() if article.publish_date else ""
        thumbnail = extract_thumbnail_accurate(article.html, url)
        
        if thumbnail and not thumbnail.startswith('http'):
            base_url = f"{urlsplit(url).scheme}://{urlsplit(url).netloc}"
            thumbnail = f"https:{thumbnail}" if thumbnail.startswith('//') else f"{base_url}{thumbnail}"
        
        return {
            "url": url, "domain": urlsplit(url).netloc, "source": source_name,
            "title": title, "text": text, "text_len": len(text),
            "date_utc": date_utc, "authors": list(article.authors or []),
            "image": thumbnail, "image_path": ""
        }
    except:
        return None


def download_image(url, path, referer_url=None):
    """Optimized image download dengan streaming"""
    try:
        if not url or not url.startswith('http'):
            return ""
        if any(kw in url.lower() for kw in ['ads', 'logo', 'iklan']):
            return ""
        
        local_headers = HEADERS.copy()
        if referer_url:
            local_headers['Referer'] = referer_url
        
        r = SESSION.get(url, headers=local_headers, timeout=10, stream=True)
        r.raise_for_status()
        
        content_type = r.headers.get('content-type', '').lower()
        if 'image' not in content_type:
            return ""
        
        content_length = int(r.headers.get('content-length', 0))
        if content_length < 8000:
            return ""
        
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=16384):  # Larger chunks
                f.write(chunk)
        
        return path if os.path.getsize(path) >= 8000 else ""
    except:
        return ""

print("✅ Semua fungsi 'scrape' dan 'download' berhasil didefinisikan.")

# ================================================================
# 📦 FUNGSI METADATA & ORKESTRASI UTAMA
# ================================================================

def create_metadata(news_data, topic="Kebijakan Hukum, Politik, & HAM"):
    """Generate metadata dengan batch processing"""
    created_utc = datetime.now(timezone.utc).isoformat()
    records = []
    
    for i, item in enumerate(news_data, 1):
        text = item.get("text", "")
        records.append({
            "id": i,
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "domain": item.get("domain", ""),
            "source": item.get("source", ""),
            "topic": topic,
            "date_utc": item.get("date_utc", ""),
            "authors": ", ".join(item.get("authors", [])),
            "modality": "text+image" if item.get("image_path") else "text",
            "language": "id",
            "text_len": item.get("text_len", 0),
            "text_preview": (text[:280] + "...") if len(text) > 280 else text,
            "image_url": item.get("image", ""),
            "image_path": item.get("image_path", ""),
            "label": 1,
            "created_at_utc": created_utc,
            "notes": "berita valid hasil scraping portal resmi (newspaper4k)"
        })
    
    return records


def scrape_news(
    max_total=500,
    max_workers=25,  # Increased from 15
    download_images=True,
    start_date=datetime(2024, 10, 20, tzinfo=timezone.utc),
    end_date=None,
    sources=['kompas', 'detik', 'cnn', 'tempo', 'antaranews']
):
    """Main scraping orchestrator dengan optimasi paralel"""
    
    if end_date is None:
        end_date = datetime.now(timezone.utc)
    
    OUTPUT_DIR = GDRIVE_BASE_PATH
    IMG_DIR = os.path.join(OUTPUT_DIR, "images")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(IMG_DIR, exist_ok=True)
    
    print("="*70)
    print("NEWSPAPER4K NEWS SCRAPER (OPTIMIZED)")
    print("="*70)
    print(f"Periode: {start_date.date()} -> {end_date.date()}")
    print(f"Target: {max_total} artikel | Threads: {max_workers}")
    print(f"Output: {OUTPUT_DIR}")
    print(f"Gambar disimpan di: {IMG_DIR}")
    
    # Tahap 1: Discover URLs (Parallel)
    print("\n🔍 Tahap 1: Menemukan URLs...")
    start_time = time.time()
    
    all_urls = []
    discover_tasks = []
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        if 'kompas' in sources:
            discover_tasks.append(executor.submit(discover_kompas_urls_with_date, start_date, end_date))
        if 'detik' in sources:
            discover_tasks.append(executor.submit(discover_detik_urls_with_date, start_date, end_date))
        if 'cnn' in sources:
            discover_tasks.append(executor.submit(discover_cnn_urls_with_date, start_date, end_date))
        if 'tempo' in sources:
            discover_tasks.append(executor.submit(discover_tempo_urls_paginated, max_total))
        if 'antaranews' in sources:
            discover_tasks.append(executor.submit(discover_antaranews_urls_paginated, max_total))
        
        for future in as_completed(discover_tasks):
            all_urls.extend(future.result())
    
    unique_urls = list(dict.fromkeys(all_urls))
    discover_time = time.time() - start_time
    print(f"\n✅ Total URL unik: {len(unique_urls)} (waktu: {discover_time:.1f}s)")
    
    # Tahap 2: Scrape Articles (Parallel dengan batching)
    print(f"\n📰 Tahap 2: Scraping artikel...")
    scrape_start = time.time()
    
    articles = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(scrape_article, url, src): (src, url) for src, url in unique_urls}
        
        for fut in as_completed(futures):
            if len(articles) >= max_total:
                # Cancel remaining futures
                for f in futures:
                    f.cancel()
                break
            
            result = fut.result()
            if result:
                articles.append(result)
                if len(articles) % 50 == 0:
                    elapsed = time.time() - scrape_start
                    rate = len(articles) / elapsed
                    print(f"[{len(articles)}/{max_total}] ⚡ {rate:.1f} artikel/detik")
    
    scrape_time = time.time() - scrape_start
    print(f"\n✅ Scraping selesai: {len(articles)} artikel ({scrape_time:.1f}s, {len(articles)/scrape_time:.1f} artikel/s)")
    
    # Tahap 3: Download Images (Parallel)
    if download_images and articles:
        print(f"\n🖼️  Tahap 3: Mengunduh gambar...")
        img_start = time.time()
        
        def download_wrapper(args):
            idx, article = args
            img_url = article.get("image", "")
            if img_url:
                ext = img_url.split("?")[0].split(".")[-1][:4] or "jpg"
                img_path = os.path.join(IMG_DIR, f"EL_{idx:04d}.{ext}")
                article_url = article.get("url")
                if downloaded_path := download_image(img_url, img_path, referer_url=article_url):
                    article["image_path"] = os.path.relpath(downloaded_path, OUTPUT_DIR)
            return article
        
        with ThreadPoolExecutor(max_workers=20) as executor:  # Increased from 10
            articles = list(executor.map(download_wrapper, enumerate(articles, 1)))
        
        img_count = sum(1 for a in articles if a.get('image_path'))
        img_time = time.time() - img_start
        print(f"✅ Download selesai: {img_count} gambar ({img_time:.1f}s)")
    
    # Tahap 4: Save Results
    if articles:
        print(f"\n💾 Tahap 4: Menyimpan hasil...")
        
        # Save articles.json
        with open(os.path.join(OUTPUT_DIR, "articles.json"), "w", encoding="utf-8") as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        
        # Save metadata
        metadata = create_metadata(articles)
        pd.DataFrame(metadata).to_csv(os.path.join(OUTPUT_DIR, "metadata_news.csv"), index=False)
        with open(os.path.join(OUTPUT_DIR, "metadata_news.json"), "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        total_time = time.time() - start_time
        img_count = sum(1 for a in articles if a.get('image_path'))
        
        print("\n" + "="*70)
        print("📊 RINGKASAN")
        print("="*70)
        print(f"✅ Total artikel: {len(articles)}")
        print(f"🖼️  Total gambar: {img_count}")
        print(f"⏱️  Total waktu: {total_time:.1f}s ({total_time/60:.1f} menit)")
        print(f"⚡ Rata-rata: {len(articles)/total_time:.2f} artikel/detik")
        print(f"📁 Output: {OUTPUT_DIR}")
        print("="*70)
    else:
        print("❌ Tidak ada artikel yang sesuai kriteria.")
    
    return articles

print("✅ Semua fungsi utama berhasil didefinisikan.")

# ================================================================
# 🚀 EKSEKUSI SCRAPER
# ================================================================

if __name__ == "__main__":
    final_articles = scrape_news(
        max_total=2000,
        max_workers=25,  # Increased for better parallelization
        download_images=True,
        start_date=datetime(2024, 10, 20),
        end_date=datetime(2025, 10, 20),
        sources=['kompas', 'detik', 'cnn']
    )
    
    print("\n🎉 Scraping selesai! Cek folder ./data/raw/news untuk hasilnya.")
