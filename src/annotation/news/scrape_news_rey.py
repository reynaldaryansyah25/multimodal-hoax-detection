import os, time, json
from datetime import datetime, timezone, timedelta
from urllib.parse import urlsplit
from newspaper import Article
import requests
from bs4 import BeautifulSoup
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed


OUTPUT_DIR = "./data/raw/news/"
IMG_DIR = os.path.join(OUTPUT_DIR, "images")


POLITICAL_KEYWORDS = [
    "UU", "undang-undang", "KUHP", "KUHAP", "ITE", "revisi", "peraturan", "hukum", "peradilan",
    "Mahkamah", "Kemenkumham", "Kejaksaan", "KPK", "Kepolisian", "penegakan hukum",
    "politik", "partai", "pemilu", "parpol", "koalisi", "kebijakan politik", "KPU", "Bawaslu",
    "caleg", "capres", "pilkada", "pemerintah", "menteri", "kabinet", "DPR", "MPR",
    "HAM", "Komnas HAM", "hak asasi", "pelanggaran HAM", "penghilangan paksa",
    "netralitas ASN", "pembela HAM", "reformasi hukum", "Prabowo", "kabinet merah putih"
]


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}


def discover_kompas_urls_with_date(start_date, end_date, limit_per_day=20):
    all_urls = []
    current = start_date
    
    print(f"  Kompas: Scraping from {start_date.date()} to {end_date.date()}...")
    
    while current <= end_date:
        date_str = current.strftime("%Y-%m-%d")
        
        try:
            url = f"https://indeks.kompas.com/?site=all&date={date_str}"
            r = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(r.text, 'html.parser')
            
            for link in soup.select('.article__link, .latest__link')[:limit_per_day]:
                href = link.get('href')
                if href and href.startswith('http') and 'kompas.com' in href:
                    all_urls.append(href)
            
            time.sleep(0.3)
        except Exception as e:
            pass
        
        current += timedelta(days=1)
    
    print(f"  Kompas: {len(all_urls)} URLs found")
    return [('kompas', u) for u in all_urls]


def discover_detik_urls_with_date(start_date, end_date, limit_per_day=20):
    all_urls = []
    current = start_date
    
    print(f"  Detik: Scraping from {start_date.date()} to {end_date.date()}...")
    
    while current <= end_date:
        date_str = current.strftime("%m/%d/%Y")
        
        try:
            url = f"https://news.detik.com/indeks?date={date_str}"
            r = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(r.text, 'html.parser')
            
            for link in soup.select('article h3 a, article h2 a')[:limit_per_day]:
                href = link.get('href')
                if href and href.startswith('http') and 'detik.com' in href:
                    all_urls.append(href)
            
            time.sleep(0.3)
        except Exception as e:
            pass
        
        current += timedelta(days=1)
    
    print(f"  Detik: {len(all_urls)} URLs found")
    return [('detik', u) for u in all_urls]


def discover_cnn_urls_paginated(limit=200):
    all_urls = []
    
    print(f"  CNN: Scraping with pagination...")
    
    for page in range(1, 11):
        try:
            url = f"https://www.cnnindonesia.com/nasional/indeks/{page}"
            r = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(r.text, 'html.parser')
            
            for link in soup.select('.media__link, article a'):
                href = link.get('href')
                if href:
                    if not href.startswith('http'):
                        href = 'https://www.cnnindonesia.com' + href
                    if 'cnnindonesia.com' in href and href not in all_urls:
                        all_urls.append(href)
            
            if len(all_urls) >= limit:
                break
            
            time.sleep(0.5)
        except Exception as e:
            pass
    
    print(f"  CNN: {len(all_urls)} URLs found")
    return [('cnn', u) for u in all_urls[:limit]]


def discover_tempo_urls_paginated(limit=200):
    all_urls = []
    
    print(f"  Tempo: Scraping with pagination...")
    
    for page in range(1, 11):
        try:
            url = f"https://nasional.tempo.co/indeks/{page}"
            r = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(r.text, 'html.parser')
            
            for link in soup.select('.title a, h2 a'):
                href = link.get('href')
                if href and href.startswith('http') and 'tempo.co' in href:
                    all_urls.append(href)
            
            if len(all_urls) >= limit:
                break
            
            time.sleep(0.5)
        except Exception as e:
            pass
    
    print(f"  Tempo: {len(all_urls)} URLs found")
    return [('tempo', u) for u in all_urls[:limit]]


def discover_antaranews_urls_paginated(limit=200):
    all_urls = []
    
    print(f"  Antara: Scraping with pagination...")
    
    for page in range(1, 11):
        try:
            url = f"https://www.antaranews.com/indeks/{page}"
            r = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(r.text, 'html.parser')
            
            for link in soup.select('.simple-post a, article a'):
                href = link.get('href')
                if href:
                    if not href.startswith('http'):
                        href = 'https://www.antaranews.com' + href
                    if 'antaranews.com' in href and href not in all_urls:
                        all_urls.append(href)
            
            if len(all_urls) >= limit:
                break
            
            time.sleep(0.5)
        except Exception as e:
            pass
    
    print(f"  Antara: {len(all_urls)} URLs found")
    return [('antaranews', u) for u in all_urls[:limit]]


def extract_thumbnail_manual(html_content, source_name):
    """Manual thumbnail extraction dengan fallback per portal"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Prioritas 1: og:image (standard untuk thumbnail)
    og_image = soup.find('meta', property='og:image')
    if og_image and og_image.get('content'):
        return og_image.get('content')
    
    # Prioritas 2: twitter:image
    tw_image = soup.find('meta', property='twitter:image')
    if tw_image and tw_image.get('content'):
        return tw_image.get('content')
    
    # Prioritas 3: Selector spesifik per portal
    selectors = {
        'kompas': ['.photo__img', '.read__img', 'img.photo'],
        'detik': ['.detail__media img', '.detail__body-img', 'img.detail__media-image'],
        'cnn': ['.detail-media img', '.detail-img', 'article img'],
        'tempo': ['.detail-img img', 'article img', '.img-content'],
        'antaranews': ['.post-content img', 'article img', '.detail-img']
    }
    
    if source_name in selectors:
        for selector in selectors[source_name]:
            img = soup.select_one(selector)
            if img and img.get('src'):
                return img.get('src')
    
    # Prioritas 4: First article image
    article_img = soup.select_one('article img, .article img')
    if article_img and article_img.get('src'):
        return article_img.get('src')
    
    return ""


def scrape_article(url, source_name):
    """Scrape article dengan improved thumbnail detection"""
    try:
        article = Article(url, language='id', fetch_images=True, memoize_articles=False)
        article.download()
        article.parse()
        
        title = article.title or ""
        text = article.text or ""
        
        if not any(kw.lower() in title.lower() or kw.lower() in text.lower() 
                   for kw in POLITICAL_KEYWORDS):
            return None
        
        if len(text) < 100:
            return None
        
        # Parse date
        date_str = ""
        date_utc = ""
        if article.publish_date:
            try:
                if isinstance(article.publish_date, str):
                    date_str = article.publish_date
                else:
                    date_str = article.publish_date.isoformat()
                    date_utc = article.publish_date.astimezone(timezone.utc).isoformat()
            except:
                pass
        
        # Improved thumbnail extraction
        thumbnail = article.top_image or ""
        
        # Fallback: manual extraction kalau newspaper4k gagal
        if not thumbnail or len(thumbnail) < 10:
            thumbnail = extract_thumbnail_manual(article.html, source_name)
        
        # Validasi URL thumbnail
        if thumbnail and not thumbnail.startswith('http'):
            # Convert relative URL to absolute
            base_url = f"{urlsplit(url).scheme}://{urlsplit(url).netloc}"
            if thumbnail.startswith('//'):
                thumbnail = f"https:{thumbnail}"
            elif thumbnail.startswith('/'):
                thumbnail = f"{base_url}{thumbnail}"
        
        return {
            "url": url,
            "domain": urlsplit(url).netloc,
            "source": source_name,
            "title": title,
            "text": text,
            "text_len": len(text),
            "date": date_str,
            "date_utc": date_utc,
            "authors": list(article.authors) if article.authors else [],
            "image": thumbnail,
            "image_path": "",
        }
        
    except Exception as e:
        return None


def download_image(url, path):
    """Download image dengan validasi"""
    try:
        # Skip jika URL tidak valid
        if not url or not url.startswith('http'):
            return ""
        
        # Download dengan timeout
        r = requests.get(url, headers=HEADERS, timeout=15, stream=True)
        
        # Check content type
        content_type = r.headers.get('content-type', '')
        if 'image' not in content_type.lower():
            return ""
        
        # Save file
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return path
    except Exception as e:
        return ""


def create_metadata(news_data, topic="Kebijakan Hukum, Politik, & HAM"):
    created_utc = datetime.now(timezone.utc).isoformat()
    records = []
    
    for i, item in enumerate(news_data, 1):
        preview = (item.get("text","")[:280] + "...") if len(item.get("text","")) > 280 else item.get("text","")
        records.append({
            "id": i,
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "domain": item.get("domain", ""),
            "source": item.get("source", ""),
            "topic": topic,
            "date_raw": item.get("date", ""),
            "date_utc": item.get("date_utc", ""),
            "authors": ", ".join(item.get("authors", [])),
            "modality": "text+image" if item.get("image_path") else "text",
            "language": "id",
            "text_len": item.get("text_len", 0),
            "text_preview": preview,
            "image_url": item.get("image", ""),
            "image_path": item.get("image_path", ""),
            "label": 0,
            "created_at_utc": created_utc,
            "notes": "berita valid hasil scraping portal resmi (newspaper4k)"
        })
    return records


def scrape_news(
    max_total=500,
    max_per_source=150,
    max_workers=15,
    download_images=True,
    start_date=datetime(2024, 10, 20, tzinfo=timezone.utc),
    end_date=None,
    sources=['kompas', 'detik', 'cnn', 'tempo', 'antaranews']
):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(IMG_DIR, exist_ok=True)
    
    if end_date is None:
        end_date = datetime.now(timezone.utc)
    
    print("="*70)
    print("NEWSPAPER4K NEWS SCRAPER - Era Prabowo")
    print("="*70)
    print(f"Period: {start_date.date()} -> {end_date.date()}")
    print(f"Target: {max_total} articles total ({max_per_source} per source)")
    print(f"Workers: {max_workers} threads")
    print(f"Sources: {', '.join(sources)}")
    print("="*70)
    
    print("\nDiscovering article URLs...\n")
    all_urls = []
    
    if 'kompas' in sources:
        all_urls.extend(discover_kompas_urls_with_date(start_date, end_date, limit_per_day=10))
        time.sleep(1)
    
    if 'detik' in sources:
        all_urls.extend(discover_detik_urls_with_date(start_date, end_date, limit_per_day=10))
        time.sleep(1)
    
    if 'cnn' in sources:
        all_urls.extend(discover_cnn_urls_paginated(max_per_source))
        time.sleep(1)
    
    if 'tempo' in sources:
        all_urls.extend(discover_tempo_urls_paginated(max_per_source))
        time.sleep(1)
    
    if 'antaranews' in sources:
        all_urls.extend(discover_antaranews_urls_paginated(max_per_source))
        time.sleep(1)
    
    seen = set()
    unique_urls = []
    for source, url in all_urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append((source, url))
    
    print(f"\nTotal unique URLs: {len(unique_urls)}")
    
    print(f"\nScraping articles (max: {max_total})...\n")
    articles = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {
            executor.submit(scrape_article, url, source): (source, url)
            for source, url in unique_urls
        }
        
        for i, future in enumerate(as_completed(future_to_url), 1):
            if len(articles) >= max_total:
                print(f"\nReached max_total: {max_total}")
                break
            
            source, url = future_to_url[future]
            
            try:
                result = future.result()
                if result:
                    articles.append(result)
                    img_status = "✓" if result.get('image') else "✗"
                    print(f"[{len(articles)}/{max_total}] {img_status} {source}: {result['title'][:50]}...")
            except:
                pass
    
    print(f"\n{'='*70}")
    print(f"Scraping complete: {len(articles)} articles")
    print(f"{'='*70}")
    
    if download_images and articles:
        print(f"\nDownloading thumbnails...\n")
        
        def download_wrapper(args):
            idx, article = args
            if article.get("image", "").startswith("http"):
                ext = article["image"].split("?")[0].split(".")[-1][:4] or "jpg"
                img_path = os.path.join(IMG_DIR, f"HPH_{idx:04d}.{ext}")
                downloaded = download_image(article["image"], img_path)
                if downloaded:
                    article["image_path"] = downloaded
                    if idx % 10 == 0:
                        print(f"  ✓ Downloaded {idx} thumbnails...")
            return article
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            articles = list(executor.map(download_wrapper, enumerate(articles, 1)))
        
        success = sum(1 for a in articles if a.get('image_path'))
        print(f"\n  Total downloaded: {success}/{len(articles)} thumbnails")
    
    if articles:
        with open(os.path.join(OUTPUT_DIR, "articles.json"), "w", encoding="utf-8") as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        
        metadata = create_metadata(articles)
        
        df = pd.DataFrame(metadata)
        df.to_csv(os.path.join(OUTPUT_DIR, "metadata_rey.csv"), index=False, encoding="utf-8")
        
        with open(os.path.join(OUTPUT_DIR, "metadata_rey.json"), "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        print(f"\n{'='*70}")
        print("SUCCESS!")
        print(f"{'='*70}")
        print(f"Total articles: {len(articles)}")
        print(f"With thumbnails: {sum(1 for a in articles if a.get('image_path'))}/{len(articles)}")
        print(f"Avg text length: {sum(a['text_len'] for a in articles) // len(articles)} chars")
        print(f"\nBreakdown by source:")
        for source in sources:
            count = sum(1 for a in articles if a['source'] == source)
            if count > 0:
                print(f"  {source}: {count} articles")
        print(f"{'='*70}")
        print(f"Files saved to: {OUTPUT_DIR}")
        print(f"  articles.json")
        print(f"  metadata_rey.csv")
        print(f"  metadata_rey.json")
        if download_images:
            print(f"  images/ ({sum(1 for a in articles if a.get('image_path'))} thumbnails)")
        print(f"{'='*70}")
    
    return articles


if __name__ == "__main__":
    articles = scrape_news(
        max_total=20,
        max_per_source=150,
        max_workers=15,
        download_images=True,
        start_date=datetime(2024, 10, 20, tzinfo=timezone.utc),
        end_date=datetime(2025, 10, 30, tzinfo=timezone.utc),
    )
