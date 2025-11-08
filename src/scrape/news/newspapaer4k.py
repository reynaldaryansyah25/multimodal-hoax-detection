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

# --- KONFIGURASI AWAL ---
POLITICAL_KEYWORDS = [
    # Hukum & Regulasi
    "uu ite", "ruu kuhp", "mahkamah", "kejaksaan", "kpk", "pengadilan", "penegakan hukum",

    # Politik & Pemerintahan
    "politik", "partai", "pemilu", "pilpres", "pilkada", "kpu", "bawaslu",
    "asn netral", "kabinet", "menteri", "presiden", "wakil presiden", "prabowo", "jokowi",

    # HAM
    "ham", "pelanggaran ham", "komnas ham", "kekerasan aparat", "kebebasan berpendapat", "diskriminasi"
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

print("Pustaka dan konfigurasi awal telah dimuat.")

# --- KONFIGURASI PATH GOOGLE DRIVE ---
GDRIVE_BASE_PATH = './data/raw/news'
os.makedirs(GDRIVE_BASE_PATH, exist_ok=True)
print(f"✅ Semua output akan disimpan di dalam direktori dasar: {GDRIVE_BASE_PATH}")

# ================================================================
# 📰 FUNGSI DISCOVER URL
# ================================================================

def discover_kompas_urls_with_date(start_date, end_date, max_pages_per_day=5):
    all_urls = []
    current = start_date
    print(f"  Kompas: Mencari URL dari {start_date.date()} hingga {end_date.date()}...")
    while current <= end_date:
        date_str = current.strftime("%Y-%m-%d")
        for page in range(1, max_pages_per_day + 1):
            try:
                url_to_scrape = f"https://indeks.kompas.com/?site=all&date={date_str}&page={page}"
                r = requests.get(url_to_scrape, headers=HEADERS, timeout=15)
                if r.status_code != 200: break

                soup = BeautifulSoup(r.text, 'html.parser')
                links_on_page = soup.select('.article-link')
                if not links_on_page: break

                for link in links_on_page:
                    if href := link.get('href'):
                        clean_href = href.split("?")[0]
                        if clean_href not in all_urls:
                            all_urls.append(clean_href)
                time.sleep(0.3)
            except Exception:
                break
        current += timedelta(days=1)
    print(f"  Kompas: {len(all_urls)} URL ditemukan")
    return [('kompas', u) for u in all_urls]


def discover_detik_urls_with_date(start_date, end_date, limit_per_day=100):
    all_urls, current = [], start_date
    print(f"  Detik: Mencari URL dari {start_date.date()} hingga {end_date.date()}...")
    while current <= end_date:
        date_str = current.strftime("%m/%d/%Y")
        try:
            r = requests.get(f"https://news.detik.com/indeks?date={date_str}", headers=HEADERS, timeout=15)
            soup = BeautifulSoup(r.text, 'html.parser')
            for link in soup.select('article h3 a, article h2 a')[:limit_per_day]:
                if href := link.get('href'):
                    all_urls.append(href)
            time.sleep(0.3)
        except Exception:
            pass
        current += timedelta(days=1)
    print(f"  Detik: {len(all_urls)} URL ditemukan")
    return [('detik', u) for u in all_urls]


def discover_cnn_urls_with_date(start_date, end_date, max_pages_per_day=5):
    all_urls = []
    current = start_date
    print(f"  CNN: Mencari URL dari {start_date.date()} hingga {end_date.date()}...")
    while current <= end_date:
        date_str = current.strftime("%Y/%m/%d")
        for page in range(1, max_pages_per_day + 1):
            try:
                url_to_scrape = f"https://www.cnnindonesia.com/nasional/indeks/3?date={date_str}&page={page}"
                r = requests.get(url_to_scrape, headers=HEADERS, timeout=15)
                if r.status_code != 200: break
                soup = BeautifulSoup(r.text, 'html.parser')
                links_on_page = soup.select('article a')
                if not links_on_page: break
                for link in links_on_page:
                    if href := link.get('href'):
                        if href not in all_urls:
                            all_urls.append(href)
                time.sleep(0.3)
            except Exception:
                break
        current += timedelta(days=1)
    print(f"  CNN: {len(all_urls)} URL ditemukan")
    return [('cnn', u) for u in all_urls]


def discover_tempo_urls_paginated(limit=200):
    all_urls = []
    print(f"  Tempo: Mencari URL dengan paginasi...")
    for page in range(1, 11):
        if len(all_urls) >= limit: break
        try:
            r = requests.get(f"https://nasional.tempo.co/indeks/{page}", headers=HEADERS, timeout=15)
            soup = BeautifulSoup(r.text, 'html.parser')
            for link in soup.select('.title a, h2 a'):
                if href := link.get('href'):
                    all_urls.append(href)
            time.sleep(0.5)
        except Exception:
            pass
    print(f"  Tempo: {len(all_urls)} URL ditemukan")
    return [('tempo', u) for u in all_urls[:limit]]


def discover_antaranews_urls_paginated(limit=200):
    all_urls = []
    print(f"  Antara: Mencari URL dengan paginasi...")
    current = datetime.now()
    for i in range(10):
        if len(all_urls) >= limit: break
        date_str = (current - timedelta(days=i)).strftime("%Y/%m/%d")
        try:
            r = requests.get(f"https://www.antaranews.com/arsip/{date_str}", headers=HEADERS, timeout=15)
            soup = BeautifulSoup(r.text, 'html.parser')
            for link in soup.select('.simple-post .post-title a'):
                if href := link.get('href'):
                    if href not in all_urls:
                        all_urls.append(href)
            time.sleep(0.5)
        except Exception:
            pass
    print(f"  Antara: {len(all_urls)} URL ditemukan")
    return [('antaranews', u) for u in all_urls[:limit]]

print("✅ Semua fungsi 'discover' berhasil didefinisikan.")

# ================================================================
# ✍️ FUNGSI SCRAPE ARTIKEL & GAMBAR
# ================================================================

def extract_thumbnail_accurate(html_content, url):
    soup = BeautifulSoup(html_content, 'html.parser')
    for prop in ['og:image', 'twitter:image']:
        tag = soup.find('meta', property=prop) or soup.find('meta', name=prop)
        if tag and tag.get('content'):
            img_url = tag.get('content')
            if 'ads' not in img_url.lower() and 'logo' not in img_url.lower():
                return img_url
    return ""


def scrape_article(url, source_name):
    try:
        article = Article(url, language='id', fetch_images=True, memoize_articles=False)
        article.download()
        article.parse()

        title, text = article.title or "", article.text or ""
        if len(text) < 150 or not any(kw.lower() in f"{title} {text}".lower() for kw in POLITICAL_KEYWORDS):
            return None

        date_utc = article.publish_date.astimezone(timezone.utc).isoformat() if article.publish_date else ""
        thumbnail = extract_thumbnail_accurate(article.html, url) or article.top_image or ""
        if thumbnail and not thumbnail.startswith('http'):
            base_url = f"{urlsplit(url).scheme}://{urlsplit(url).netloc}"
            thumbnail = f"https:{thumbnail}" if thumbnail.startswith('//') else f"{base_url}{thumbnail}"

        return {
            "url": url, "domain": urlsplit(url).netloc, "source": source_name,
            "title": title, "text": text, "text_len": len(text),
            "date_utc": date_utc, "authors": list(article.authors or []),
            "image": thumbnail, "image_path": ""
        }
    except Exception:
        return None


def download_image(url, path, referer_url=None):
    try:
        if not url or not url.startswith('http') or any(kw in url.lower() for kw in ['ads', 'logo', 'iklan']):
            return ""
        local_headers = HEADERS.copy()
        if referer_url:
            local_headers['Referer'] = referer_url
        r = requests.get(url, headers=local_headers, timeout=15, stream=True)
        r.raise_for_status()
        if 'image' not in r.headers.get('content-type', '').lower(): return ""
        if int(r.headers.get('content-length', 0)) < 8000: return ""
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        return path if os.path.getsize(path) >= 8000 else ""
    except:
        return ""

print("✅ Semua fungsi 'scrape' dan 'download' berhasil didefinisikan.")

# ================================================================
# 📦 FUNGSI METADATA & ORKESTRASI UTAMA
# ================================================================

def create_metadata(news_data, topic="Kebijakan Hukum, Politik, & HAM"):
    created_utc = datetime.now(timezone.utc).isoformat()
    records = []
    for i, item in enumerate(news_data, 1):
        records.append({
            "id": i, "title": item.get("title", ""), "url": item.get("url", ""), "domain": item.get("domain", ""),
            "source": item.get("source", ""), "topic": topic, "date_utc": item.get("date_utc", ""),
            "authors": ", ".join(item.get("authors", [])),
            "modality": "text+image" if item.get("image_path") else "text",
            "language": "id", "text_len": item.get("text_len", 0),
            "text_preview": (item.get("text","")[:280] + "...") if len(item.get("text","")) > 280 else item.get("text",""),
            "image_url": item.get("image", ""), "image_path": item.get("image_path", ""), "label": 1,
            "created_at_utc": created_utc, "notes": "berita valid hasil scraping portal resmi (newspaper4k)"
        })
    return records


def scrape_news(
    max_total=500, max_workers=15, download_images=True,
    start_date=datetime(2024, 10, 20, tzinfo=timezone.utc), end_date=None,
    sources=['kompas', 'detik', 'cnn', 'tempo', 'antaranews']
):
    if end_date is None:
        end_date = datetime.now(timezone.utc)

    # Folder utama dan folder gambar tunggal
    OUTPUT_DIR = GDRIVE_BASE_PATH
    IMG_DIR = os.path.join(OUTPUT_DIR, "images")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(IMG_DIR, exist_ok=True)

    print("="*70 + "\nNEWSPAPER4K NEWS SCRAPER\n" + "="*70)
    print(f"Periode: {start_date.date()} -> {end_date.date()}")
    print(f"Target: {max_total} artikel | Threads: {max_workers}")
    print(f"Output: {OUTPUT_DIR}")
    print(f"Gambar disimpan di: {IMG_DIR}")

    # Tahap 1: Temukan URL
    all_urls = []
    if 'kompas' in sources: all_urls.extend(discover_kompas_urls_with_date(start_date, end_date))
    if 'detik' in sources: all_urls.extend(discover_detik_urls_with_date(start_date, end_date))
    if 'cnn' in sources: all_urls.extend(discover_cnn_urls_with_date(start_date, end_date))
    if 'tempo' in sources: all_urls.extend(discover_tempo_urls_paginated(max_total))
    if 'antaranews' in sources: all_urls.extend(discover_antaranews_urls_paginated(max_total))

    unique_urls = list(dict.fromkeys(all_urls))
    print(f"\nTotal URL unik ditemukan: {len(unique_urls)}")

    # Tahap 2: Scraping artikel
    articles = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(scrape_article, url, src): (src, url) for src, url in unique_urls}
        for fut in as_completed(futures):
            if len(articles) >= max_total: break
            result = fut.result()
            if result:
                articles.append(result)
                print(f"[{len(articles)}/{max_total}] ✅ ({result['source']}) {result['title'][:60]}...")

    # Tahap 3: Unduh gambar
    if download_images and articles:
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

        with ThreadPoolExecutor(max_workers=10) as executor:
            articles = list(executor.map(download_wrapper, enumerate(articles, 1)))

    # Tahap 4: Simpan hasil
    if articles:
        with open(os.path.join(OUTPUT_DIR, "articles.json"), "w", encoding="utf-8") as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)

        metadata = create_metadata(articles)
        pd.DataFrame(metadata).to_csv(os.path.join(OUTPUT_DIR, "metadata_news.csv"), index=False)
        with open(os.path.join(OUTPUT_DIR, "metadata_news.json"), "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        print(f"✅ Selesai! {len(articles)} artikel dan {sum(1 for a in articles if a.get('image_path'))} gambar disimpan.")
    else:
        print("Tidak ada artikel yang sesuai kriteria.")

    return articles

# ================================================================
# 🚀 EKSEKUSI SCRAPER
# ================================================================

final_articles = scrape_news(
    max_total=2000,
    max_workers=15,
    download_images=True,
    start_date=datetime(2024, 10, 20),
    end_date=datetime(2025, 10, 20),
    sources=['kompas', 'detik', 'cnn']
)

print("\n🎉 Scraping selesai! Cek folder ./data/raw/news untuk hasilnya.")
