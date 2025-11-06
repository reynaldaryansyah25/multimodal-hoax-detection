import os
import re
import time
import json
import random
import requests
import pandas as pd
from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, List, Dict, Set
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ============== KONFIGURASI ==============
BASE_URL = "https://turnbackhoax.id/"
SITEMAP_BASE = "https://turnbackhoax.id/wp-sitemap-posts-post-"

START_DATE = os.getenv("TBH_START_DATE", "2024-10-20")
END_DATE = os.getenv("TBH_END_DATE", datetime.now().strftime("%Y-%m-%d"))
START_DT = datetime.fromisoformat(START_DATE)
END_DT = datetime.fromisoformat(END_DATE)

USER_AGENT_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]

BASE_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Referer": BASE_URL,
}

OUTPUT_DIR = "./data/raw/turnbackhoax/"
META_DIR = os.path.join(OUTPUT_DIR, "metadata")
STATE_DIR = os.path.join(META_DIR, "state")
os.makedirs(META_DIR, exist_ok=True)
os.makedirs(STATE_DIR, exist_ok=True)

# ============== SESSION DENGAN CONNECTION POOLING ==============
def buat_session() -> requests.Session:
    """
    Membuat session dengan retry strategy dan connection pooling
    untuk meningkatkan performa dan stabilitas request HTTP
    """
    session = requests.Session()
    
    retry_strategy = Retry(
        total=5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
        backoff_factor=1.5
    )
    
    adapter = HTTPAdapter(
        pool_connections=20,
        pool_maxsize=50,
        max_retries=retry_strategy,
        pool_block=False
    )
    
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update(BASE_HEADERS)
    
    return session

session = buat_session()

def pilih_headers() -> Dict[str, str]:
    """
    Memilih user agent secara random dari pool
    untuk menghindari deteksi sebagai bot
    """
    h = BASE_HEADERS.copy()
    h["User-Agent"] = random.choice(USER_AGENT_POOL)
    return h

def ambil_dengan_retry(url: str, max_retries: int = 6, timeout: int = 30) -> Optional[requests.Response]:
    """
    Mengambil halaman dengan retry otomatis dan exponential backoff
    Menangani rate limiting dan error HTTP secara graceful
    """
    backoff = 1.0
    
    for attempt in range(max_retries):
        try:
            time.sleep(random.uniform(0.5, 1.5))
            r = session.get(url, headers=pilih_headers(), timeout=timeout, allow_redirects=True)
            
            if r.status_code == 200 and r.content:
                return r
            
            if r.status_code in (429, 403):
                wait_time = backoff + random.uniform(0, 1.5)
                time.sleep(wait_time)
                backoff = min(backoff * 2, 15)
                continue
            
            if r.status_code == 404:
                return None
                
        except requests.RequestException as e:
            time.sleep(backoff + random.uniform(0, 1.0))
            backoff = min(backoff * 2, 15)
    
    return None

# ============== PENEMUAN URL DARI SITEMAP ==============
def temukan_urls_dari_sitemap(max_sitemaps: int = 14) -> List[str]:
    """
    Mengekstrak semua URL artikel dari sitemap XML
    Filter berdasarkan tahun (hanya 2024-2025)
    Fokus ke sitemaps 1-9 yang tersedia
    """
    all_urls = set()
    
    print("Menemukan URLs dari sitemap...")
    print("=" * 70)
    
    for sitemap_num in range(1, max_sitemaps + 1):
        sitemap_url = f"{SITEMAP_BASE}{sitemap_num}.xml"
        
        print(f"Mengambil sitemap {sitemap_num}/9: {sitemap_url}", end=" ")
        
        r = ambil_dengan_retry(sitemap_url, max_retries=4)
        if not r:
            print("Tidak ditemukan")
            continue
        
        try:
            soup = BeautifulSoup(r.content, "xml")
            locs = soup.find_all("loc")
            
            added = 0
            for loc in locs:
                url = loc.get_text(strip=True)
                
                if any(year in url for year in ["2024", "2025"]):
                    if url not in all_urls:
                        all_urls.add(url)
                        added += 1
            
            print(f"Berhasil +{added} URLs (total: {len(all_urls)})")
            
        except Exception as e:
            print(f"Error parse XML")
            continue
        
        time.sleep(0.8 + random.uniform(0, 0.3))
    
    print(f"\nTotal URLs dari sitemap: {len(all_urls)}")
    return list(all_urls)

# ============== PARSING DAN EKSTRAKSI KONTEN ==============
def parse_tanggal(date_raw: str) -> Optional[datetime]:
    """
    Mem-parse tanggal dari berbagai format
    Mendukung format ISO, YYYY-MM-DD, dan DD Month YYYY
    """
    if not date_raw:
        return None
    
    try:
        return datetime.fromisoformat(date_raw.replace("Z", "").replace("+00:00", ""))
    except:
        pass
    
    m = re.search(r"(\d{4})/(\d{1,2})/(\d{1,2})", date_raw)
    if m:
        y, mn, d = map(int, m.groups())
        try:
            return datetime(y, mn, d)
        except:
            return None
    
    m2 = re.search(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", date_raw)
    if m2:
        try:
            day = int(m2.group(1))
            mon_str = m2.group(2).lower()
            year = int(m2.group(3))
            
            months = {
                "januari": 1, "februari": 2, "maret": 3, "april": 4, "mei": 5, "juni": 6,
                "juli": 7, "agustus": 8, "september": 9, "oktober": 10, "november": 11, "desember": 12,
                "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
                "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
            }
            
            mon = months.get(mon_str[:3], None)
            if mon:
                return datetime(year, mon, day)
        except:
            pass
    
    return None

def ekstrak_kategori(soup: BeautifulSoup) -> List[str]:
    """
    Mengekstrak kategori artikel dari halaman
    Mencari di berbagai selector CSS yang mungkin
    """
    cats = []
    seen = set()
    
    selectors = [
        "span.cat-links a",
        ".entry-meta a[rel='category tag']",
        "a[rel='category']",
        ".post-categories a",
        ".category a",
        "div.categories a",
    ]
    
    for sel in selectors:
        for a in soup.select(sel):
            txt = a.get_text(strip=True)
            if txt and txt not in seen and len(txt) > 1:
                seen.add(txt)
                cats.append(txt)
        if len(cats) >= 8:
            break
    
    return cats if cats else []

def ekstrak_gambar(soup: BeautifulSoup) -> List[str]:
    """
    Mengekstrak URL gambar dari artikel
    Menghindari avatar dan logo, maksimal 5 gambar
    """
    out, seen = [], set()
    
    img_selectors = [
        ".entry-content img",
        "article img",
        ".post-content img",
        ".content img",
        ".wp-post-image",
        "figure img",
    ]
    
    for sel in img_selectors:
        for img in soup.select(sel):
            src = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
            if not src:
                continue
            src = src.split("?")[0]
            if not src.startswith("http"):
                src = urljoin(BASE_URL, src)
            if src in seen or "avatar" in src.lower() or "logo" in src.lower():
                continue
            seen.add(src)
            out.append(src)
            if len(out) >= 5:
                return out
    
    return out

def ekstrak_teks(soup: BeautifulSoup) -> str:
    """
    Mengekstrak teks konten utama dari artikel
    Menggabungkan paragraf dan list items
    """
    candidates = [
        "article .entry-content",
        ".entry-content",
        ".post-content",
        "article",
        "main article",
        ".article-content",
    ]
    
    for sel in candidates:
        node = soup.select_one(sel)
        if node:
            paras = node.find_all(["p", "li"])
            text = "\n\n".join([
                p.get_text(" ", strip=True) 
                for p in paras 
                if len(p.get_text(strip=True)) > 20
            ])
            if len(text) >= 100:
                return text
    
    return ""

def ekstrak_judul(soup: BeautifulSoup) -> str:
    """
    Mengekstrak judul artikel dari berbagai selector h1
    """
    title_selectors = [
        "h1.entry-title",
        "h1.post-title",
        "article h1",
        "h1.mh-entry-title",
        "h1",
    ]
    
    for sel in title_selectors:
        el = soup.select_one(sel)
        if el:
            title = el.get_text(strip=True)
            if len(title) > 10:
                return title
    
    return ""

def ekstrak_artikel_hoax(url: str) -> Optional[Dict]:
    """
    Ekstrak artikel dengan fallback lebih agresif
    Lebih lenient dengan validasi
    """
    r = ambil_dengan_retry(url, max_retries=5, timeout=25)
    if not r:
        return None
    
    soup = BeautifulSoup(r.content, "html.parser")
    
    # TITLE: Lebih aggressive
    title = ""
    title_selectors = [
        "h1.entry-title", "h1.post-title", "article h1", 
        "h1.mh-entry-title", "h1", ".entry-title", ".post-title"
    ]
    
    for sel in title_selectors:
        el = soup.select_one(sel)
        if el:
            title = el.get_text(strip=True)
            if len(title) > 10:  
                break
    
    if not title or len(title) < 5:
        return None
    
    # TEXT: Lebih aggressive
    text = ""
    text_candidates = [
        "article .entry-content", ".entry-content", ".post-content",
        "article", "main article", ".article-content",
        ".mh-content-inner", ".td-page-content"  
    ]
    
    for sel in text_candidates:
        node = soup.select_one(sel)
        if node:
            # Extract semua text, bukan hanya <p>
            raw_text = node.get_text(" ", strip=True)
            # Bersihkan whitespace
            text = " ".join(raw_text.split())
            
            if len(text) >= 100: 
                break
    
    if len(text) < 100:
        return None
    
    # DATE
    date_raw = ""
    date_match = re.search(r"/(\d{4})/(\d{1,2})/(\d{1,2})/", url)
    if date_match:
        y, m, d = date_match.groups()
        date_raw = f"{y}-{m.zfill(2)}-{d.zfill(2)}"
        
        try:
            dt = parse_tanggal(date_raw)
            if dt and (dt < START_DT or dt > END_DT):
                return None
        except:
            pass
    
    # CATEGORIES
    cats = ekstrak_kategori(soup)
    
    # IMAGES
    imgs = ekstrak_gambar(soup)
    
    return {
        "url": url,
        "title": title[:200],  # Limit title
        "date_raw": date_raw,
        "text": text[:5000],  # Limit text
        "text_len": len(text),
        "categories": cats,
        "images": imgs,
        "label": 0
    }

# ============== MANAJEMEN STATE ==============
STATE_VISITED = os.path.join(STATE_DIR, "visited_urls.json")

def baca_visited() -> Set[str]:
    """
    Membaca set URL yang sudah dikunjungi dari file JSON
    Untuk resume jika scraping terputus
    """
    if os.path.exists(STATE_VISITED):
        with open(STATE_VISITED, "r", encoding="utf-8") as f:
            try:
                return set(json.load(f))
            except:
                return set()
    return set()

def simpan_visited(visited: Set[str]):
    """
    Menyimpan set URL yang sudah dikunjungi ke file JSON
    """
    with open(STATE_VISITED, "w", encoding="utf-8") as f:
        json.dump(sorted(list(visited)), f, ensure_ascii=False, indent=2)

# ============== PENYIMPANAN DATA ==============
FINAL_CSV = os.path.join(META_DIR, "tbh_prabowo_2024_2025.csv")

def ambil_first_atau_kosong(x: str) -> str:
    """
    Mengambil item pertama dari string dengan separator |
    """
    return x.split("|")[0] if isinstance(x, str) and x else ""

def simpan_batch(rows: List[Dict], total_collected: int):
    """
    Menyimpan batch artikel ke file CSV dengan schema lengkap
    Menambahkan field statis dan format yang sesuai
    """
    if not rows:
        return
    
    df = pd.DataFrame(rows)

    if "images" not in df:
        df["images"] = [[] for _ in range(len(df))]
    
    df["image_urls"] = df["images"].apply(lambda L: "|".join(L) if isinstance(L, list) else "")
    df["thumbnail"] = df["image_urls"].apply(ambil_first_atau_kosong)
    df["categories_str"] = df.get("categories", [[]]).apply(
        lambda L: "|".join(L) if isinstance(L, list) else ""
    )

    df["social_media"] = ""
    df["post_view"] = 0
    df["post_likes"] = 0
    df["post_comment"] = 0
    df["post_share"] = 0
    df["blog_check"] = "verified"
    df["blog_conclusion"] = "hoax"
    df["archive_url"] = df["url"]
    df["blog_url"] = BASE_URL
    df["id"] = [f"TBH_{(total_collected + i + 1):05d}" for i in range(len(df))]

    final_cols = [
        "id", "blog_date", "blog_title", "label", "social_media",
        "post_text", "post_date", "blog_check", "blog_conclusion",
        "post_view", "post_likes", "post_comment", "post_share",
        "post_url", "archive_url", "blog_url", "thumbnail", "categories"
    ]

    df["blog_date"] = df["date_raw"]
    df["blog_title"] = df["title"]
    df["post_text"] = df["text"]
    df["post_date"] = df["date_raw"]
    df["post_url"] = df["url"]
    df["categories"] = df["categories_str"]

    final_df = df[final_cols].copy()

    if os.path.exists(FINAL_CSV):
        final_df.to_csv(FINAL_CSV, index=False, mode="a", header=False, encoding="utf-8")
    else:
        final_df.to_csv(FINAL_CSV, index=False, encoding="utf-8")

# ============== MAIN RUNNER ==============
def jalankan_scraper(total_target: int = 5000, batch_size: int = 500, workers: int = 6):
    """
    Menjalankan proses scraping secara keseluruhan
    Menggunakan sitemap untuk penemuan URL
    Ekstraksi paralel dengan ThreadPoolExecutor
    """
    
    visited = baca_visited()
    total_collected = 0
    
    if os.path.exists(FINAL_CSV):
        try:
            existing_df = pd.read_csv(FINAL_CSV)
            total_collected = len(existing_df)
        except:
            total_collected = 0

    print("\n" + "=" * 70)
    print("TURNBACKHOAX SCRAPER - VERSI FINAL")
    print("=" * 70)
    print(f"Target: {total_target} | Batch: {batch_size} | Workers: {workers}")
    print(f"Rentang tanggal: {START_DATE} hingga {END_DATE}")
    print(f"Semua artikel: LABEL = 0 (HOAX)")
    if total_collected:
        print(f"Melanjutkan: {total_collected} artikel sudah dikumpulkan")
    print("=" * 70)

    batch_id = 1

    while total_collected < total_target:
        remaining = total_target - total_collected
        this_batch_target = min(batch_size, remaining)
        
        print(f"\n{'-' * 70}")
        print(f"BATCH {batch_id} | Target: {this_batch_target} | Sisa: {remaining}")
        print(f"{'-' * 70}")

        print("\nFase penemuan URL...")
        urls = temukan_urls_dari_sitemap(max_sitemaps=9)
        
        uniq_list = []
        seen_local = set()
        
        for u in urls:
            u_clean = u.rstrip("/")
            if u_clean in visited or u_clean in seen_local:
                continue
            seen_local.add(u_clean)
            uniq_list.append(u_clean)

        if len(uniq_list) > this_batch_target * 3:
            uniq_list = uniq_list[:this_batch_target * 3]

        print(f"Kandidat URL: {len(uniq_list)}")

        print(f"\nFase ekstraksi (Workers: {workers})...")
        
        def work(u: str) -> Optional[Dict]:
            try:
                return ekstrak_artikel_hoax(u)
            except Exception:
                return None

        arts: List[Dict] = []
        processed = 0
        
        with ThreadPoolExecutor(max_workers=max(1, min(workers, 10))) as ex:
            futures = {ex.submit(work, u): u for u in uniq_list}
            
            for fut in as_completed(futures):
                processed += 1
                art = None
                
                try:
                    art = fut.result(timeout=90)
                except Exception:
                    art = None
                
                if art:
                    arts.append(art)
                    visited.add(art["url"])
                
                if processed % 50 == 0:
                    print(f"Progress: {processed}/{len(uniq_list)}, Terekstrak: {len(arts)}")
                
                if len(arts) >= this_batch_target:
                    break

        print(f"\nTerekstrak: {len(arts)} artikel dari {processed} URLs")

        if not arts:
            simpan_visited(visited)
            print("Tidak ada artikel, tunggu 120 detik...")
            time.sleep(120)
            batch_id += 1
            continue

        print("Menyimpan ke CSV...")
        simpan_batch(arts, total_collected)
        total_collected += len(arts)
        simpan_visited(visited)
        
        print(f"Batch {batch_id} berhasil disimpan")
        print(f"Total terkumpul: {total_collected}/{total_target}")

        if total_collected >= total_target:
            break
        
        efficiency = len(arts) / max(processed, 1)
        sleep_min = 8 * 60 if efficiency > 0.7 else (5 * 60 if efficiency > 0.4 else 3 * 60)
        
        print(f"Menunggu: {sleep_min // 60} menit (Efisiensi: {efficiency:.1%})")
        time.sleep(sleep_min)
        
        batch_id += 1

    print(f"\n{'=' * 70}")
    print("SELESAI")
    print(f"{'=' * 70}")
    print(f"Total artikel: {total_collected}")
    print(f"Label: HOAX (0) untuk semua")
    print(f"File: {FINAL_CSV}")
    print(f"URLs dikunjungi: {len(visited)}")
    print(f"{'=' * 70}\n")

if __name__ == "__main__":
    jalankan_scraper(
        total_target=5000,
        batch_size=500,
        workers=6
    )
