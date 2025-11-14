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

START_DATE = os.getenv("TBH_START_DATE", "2021-01-01") 
END_DATE = os.getenv("TBH_END_DATE", datetime.now().strftime("%Y-%m-%d"))
START_DT = datetime.fromisoformat(START_DATE)
END_DT = datetime.fromisoformat(END_DATE)

# ============== NORMALIZER TEKS TBH (ANTI-SHORTCUT) ==============
TBH_TEXT_RULES = [
    r"\b(kesimpulan|kategori|narasi|penjelasan|referensi|pemeriksaan\s*fakta|periksa\s*fakta|cek\s*fakta)\b\s*[:\-]?",
    r"\b(tidak\s+ada|tidak\s+ditemukan)\s+informasi\s+(dari\s+)?kredibel.*?\bmerupakan\s+konten\b.*",
    r"\bberisi\s+klaim\b.*?\bmerupakan\s+konten\b.*",
    r"\b(video|unggahan|konten)\s+yang\s+beredar\b.*?\bmerupakan\b.*",
    r"\b(konten\s+(menyesatkan|palsu|dimanipulasi|tiruan|salah)|misleading\s*content|fabricated\s*content|false\s*context|impostor\s*content)\b",
    r"\bhasi[l]\s+[a-z\.\s]{2,60}\b",                 # "Hasil Dyah Febriyani"
    r"\barsip\b|\bar sip\b|\[arsip\]",
    r"\b(instagram|facebook|tiktok|youtube|x\s*\(twitter\)|twitter)\b",
    r"https?://\S+",
    r"\([^\)]{10,}\)", r"\[[^\]]{3,}\]", r"={3,}",
]

def normalize_tbh_text(raw: str) -> str:
    x = raw if isinstance(raw, str) else ""
    for p in TBH_TEXT_RULES:
        x = re.sub(p, " ", x, flags=re.IGNORECASE | re.DOTALL)
    x = re.sub(r"\s+", " ", x).strip()
    return x

def strip_tbh_title_label(title: str) -> str:
    t = title if isinstance(title, str) else ""
    t = re.sub(r"^\s*\[(SALAH|BENAR|PENIPUAN|DISINFORMASI|MISINFORMASI|HOAKS?)\]\s*", " ", t, flags=re.IGNORECASE)
    return re.sub(r"\s+"," ",t).strip()


# ============== EXPANDED KEYWORDS ==============
POLITICAL_KEYWORDS = [
    "prabowo", "subianto", "prabowo subianto", "presiden prabowo", 
    "pemerintahan prabowo", "kabinet prabowo", "menteri prabowo",
    "presiden", "presiden terpilih", "capres", "calon presiden",
    "politik", "pemerintahan", "pemerintah", "negara", "demokrasi", 
    "parlemen", "dpr", "mpr", "dewan", "legislatif",
    "eksekutif", "yudikatif", "pemilu", "pilpres", "pilkada",
    "partai politik", "koalisi", "oposisi", "pemimpin",
    "ekonomi", "fiskal", "anggaran", "apbn", "pajak",
    "inflasi", "pertumbuhan ekonomi", "investasi", "pmdn", "pma",
    "utang", "defisit", "subsidi", "bansos", "bantuan sosial",
    "pembangunan", "infrastruktur", "proyek", "mega proyek",
    "kemenkeu", "kementerian keuangan", "sri mulyani",
    "perdagangan", "ekspor", "impor", "bea cukai",
    "industri", "manufaktur", "umkm", "koperasi",
    "sosial", "pendidikan", "sekolah", "kampus", "universitas",
    "kurikulum", "guru", "dosen", "mahasiswa", "pelajar",
    "kesehatan", "rumah sakit", "puskesmas", "bpjs",
    "nakes", "dokter", "perawat", "farmasi", "obat",
    "kemensos", "kementerian sosial", "kemendikbud",
    "kementerian pendidikan", "kebudayaan", "riset", "teknologi",
    "kemenkes", "kementerian kesehatan",
    "lingkungan", "energi", "alam", "hutan", "deforestasi",
    "perubahan iklim", "emisi", "karbon", "global warming",
    "sda", "sumber daya alam", "tambang", "minyak", "gas",
    "batubara", "minerba", "esdm", "kementerian esdm",
    "air", "sungai", "laut", "samudera", "pesisir",
    "renewable", "energi terbarukan", "surya", "angin",
    "panas bumi", "bioenergy", "pltn", "nuklir",
    "hukum", "ham", "hak asasi manusia", "peradilan", "mahkamah",
    "agung", "mk", "mahkamah konstitusi", "kejaksaan", "kejagung",
    "kepolisian", "polri", "bareskrim", "kpk", "korupsi",
    "advokat", "pengacara", "notaris", "legal", "perundangan",
    "uu", "undang-undang", "perpu", "peraturan pemerintah",
    "kebebasan", "kebebasan pers", "minoritas", "diskriminasi",
    "kesetaraan", "keadilan", "kemenkumham", "kementerian hukum",
    "partai gerindra", "gerindra", "partai demokrat", "demokrat",
    "pkb", "pan", "golkar", "psi", "perindo", "ppp",
    "pdip", "pdi perjuangan", "nasdem", "partai nasdem",
    "koalisi indonesia maju", "koalisi perubahan",
    "anies baswedan", "anies", "ganjar pranowo", "ganjar",
    "megawati", "hasto", "jokowi", "joko widodo",
    "maruf amin", "khofifah", "ridwan kamil",
    "ibu kota negara", "ikn", "nusantara", "kalimantan",
    "papua", "papua barat", "aceh", "perbatasan",
    "natuna", "militer", "tni", "alutsista", "pertahanan",
    "indonesia", "jakarta", "nasional", "kebijakan", "program",
    "rapat", "pertemuan", "kunjungan", "pernyataan", "pidato"
]

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
    """Membuat session dengan retry strategy dan connection pooling"""
    session = requests.Session()
    
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
        backoff_factor=1.0
    )
    
    adapter = HTTPAdapter(
        pool_connections=30,
        pool_maxsize=100,
        max_retries=retry_strategy,
        pool_block=False
    )
    
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update(BASE_HEADERS)
    
    return session

session = buat_session()

def pilih_headers() -> Dict[str, str]:
    """Memilih user agent secara random"""
    h = BASE_HEADERS.copy()
    h["User-Agent"] = random.choice(USER_AGENT_POOL)
    return h

def ambil_dengan_retry(url: str, max_retries: int = 3, timeout: int = 20) -> Optional[requests.Response]:
    """Mengambil halaman dengan retry otomatis"""
    backoff = 0.5
    
    for attempt in range(max_retries):
        try:
            time.sleep(random.uniform(0.05, 0.15))
            r = session.get(url, headers=pilih_headers(), timeout=timeout, allow_redirects=True)
            
            if r.status_code == 200 and r.content:
                return r
            
            if r.status_code in (429, 403):
                wait_time = backoff + random.uniform(0, 0.5)
                time.sleep(wait_time)
                backoff = min(backoff * 1.5, 3)
                continue
            
            if r.status_code == 404:
                return None
                
        except requests.RequestException as e:
            time.sleep(backoff)
            backoff = min(backoff * 1.5, 3)
    
    return None

# ============== EKSTRAKSI METRICS SOSIAL MEDIA ==============
def ekstrak_metrics_sosial(soup: BeautifulSoup) -> Dict[str, int]:
    """Ekstrak metrics dengan early exit strategy"""
    metrics = {"views": 0, "likes": 0, "comments": 0, "shares": 0}
    
    for selector in [".post-views", ".views", "[class*='view']"]:
        element = soup.select_one(selector)
        if element:
            numbers = re.findall(r'\d+', element.get_text())
            if numbers:
                metrics["views"] = int(numbers[0])
                break
    
    for selector in [".comments-link", ".comment-count", "[class*='comment']"]:
        element = soup.select_one(selector)
        if element:
            numbers = re.findall(r'\d+', element.get_text())
            if numbers:
                metrics["comments"] = int(numbers[0])
                break
    
    for selector in [".social-share-count", "[class*='share']"]:
        element = soup.select_one(selector)
        if element:
            numbers = re.findall(r'\d+', element.get_text())
            if numbers:
                metrics["shares"] = int(numbers[0])
                break
    
    return metrics

# ============== FILTER BERITA POLITIK ==============
def filter_berita_politik(artikel: Dict) -> bool:
    """
    Filter yang lebih FOKUS pada data politik.
    Strategi yang terlalu longgar (seperti cek tanggal) sudah dihapus.
    """
    if not artikel:
        return False
    
    title = artikel.get('title', '').lower()
    text = artikel.get('text', '').lower()  
    full = f"{title} {text}"
    
    if any(x in title for x in ["prabowo", "presiden prabowo", "pemerintah", "indonesia", "politik"]):
        return True
    
    political = ["pemerintah", "presiden", "menteri", "kebijakan", "ekonomi", 
                 "investasi", "pembangunan", "indonesia", "nasional", "politik",
                 "partai", "dpr", "anggaran", "program", "kebijakan"]
    
    if sum(1 for kw in political if kw in full) >= 1:
        return True
    
    if "prabowo" in full:
        return True
    
    return False

# ============== SITEMAP COVERAGE ==============
def temukan_urls_dari_sitemap(max_sitemaps: int = 50) -> List[str]:
    """
    Ekstrak URLs dengan parallel fetching.
    LOGIKA DIPERBAIKI: Filter berdasarkan START_DT, bukan string hard-coded.
    """
    all_urls = set()
    
    print("Menemukan URLs dari sitemap (PARALLEL)...")
    print("=" * 70)
    
    def fetch_sitemap(sitemap_num):
        sitemap_url = f"{SITEMAP_BASE}{sitemap_num}.xml"
        # Coba ambil dengan retry
        r = ambil_dengan_retry(sitemap_url, max_retries=3) 
        if not r:
            return [] # Gagal mengambil sitemap ini
        
        try:
            soup = BeautifulSoup(r.content, "xml")
            locs = soup.find_all("loc")
            urls = []
            for loc in locs:
                url = loc.get_text(strip=True)
                
                # --- LOGIKA PERBAIKAN ---
                # 1. Coba tebak tanggal dari URL (paling umum)
                date_match = re.search(r"/(\d{4})/(\d{1,2})/(\d{1,2})/", url)
                
                if date_match:
                    year, month, day = map(int, date_match.groups())
                    try:
                        # 2. Buat objek datetime
                        url_date = datetime(year, month, day)
                        
                        # 3. Cek apakah tanggal ada di rentang (START_DT s/d END_DT)
                        # START_DT Anda adalah 2021-01-01
                        if url_date >= START_DT and url_date <= END_DT:
                            urls.append(url)
                            
                    except ValueError:
                        # Tanggal invalid (misal /2023/02/30/), lewati
                        continue 
                # Jika URL tidak punya format tanggal (jarang), kita lewati
                # --- AKHIR PERBAIKAN ---
            return urls
        except Exception as e:
            return []
    
    with ThreadPoolExecutor(max_workers=10) as ex:
        # Kita cari dari sitemap 1 s/d max_sitemaps
        futures = {ex.submit(fetch_sitemap, i): i for i in range(1, max_sitemaps + 1)}
        for fut in as_completed(futures):
            sitemap_num = futures[fut]
            try:
                urls = fut.result(timeout=30) # Beri waktu 30 detik
                all_urls.update(urls)
                if urls: # Hanya print jika ada hasil
                    print(f"Sitemap {sitemap_num}: +{len(urls)} URLs")
            except Exception as e:
                # Gagal karena timeout atau error parsing
                print(f"Sitemap {sitemap_num}: GAGAL")
    
    print(f"Total URLs: {len(all_urls)}")
    return list(all_urls)

# ============== PARSING DAN EKSTRAKSI KONTEN ==============
def parse_tanggal(date_raw: str) -> Optional[datetime]:
    """Mem-parse tanggal dari berbagai format"""
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
    """Mengekstrak kategori artikel"""
    cats = []
    seen = set()
    selectors = ["span.cat-links a", ".entry-meta a[rel='category tag']", "a[rel='category']",
                 ".post-categories a", ".category a", "div.categories a"]
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
    """Mengekstrak URL gambar dari artikel"""
    out, seen = [], set()
    img_selectors = [".entry-content img", "article img", ".post-content img", ".content img",
                     ".wp-post-image", "figure img"]
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

def ekstrak_klaim_hoaks_asli(soup: BeautifulSoup) -> Optional[str]:
    """
    Ekstrak HANYA teks hoaks aslinya (klaim/narasi) berdasarkan
    struktur yang dikonfirmasi (NARASI -> blockquote -> PENJELASAN).
    """
    
    # 1. Cari container utama tempat artikel berada
    content_div = soup.select_one(".entry-content")
    if not content_div:
        return None  # Tidak ada div konten, lewati

    # 2. STRATEGI UTAMA: Cari <blockquote>
    #    Berdasarkan gambar Anda, ini adalah cara paling akurat dan konsisten.
    blockquote = content_div.find("blockquote")
    
    if blockquote:
        # 3. Bersihkan <blockquote> dari elemen yang tidak diinginkan (jika ada)
        for unwanted in blockquote.select("a, cite, .sumber-link, strong"):
            # Hapus link, "sumber:", atau "narasi:" jika ada di dalam blockquote
            unwanted.decompose()
        
        claim_text = blockquote.get_text(separator="\n", strip=True)
        
        # 4. Validasi
        if len(claim_text) > 20: # Pastikan bukan blockquote kosong
            return claim_text

    # 5. STRATEGI CADANGAN: Cari "NARASI:" jika <blockquote> tidak ditemukan
    #    Ini untuk menangani jika formatnya sedikit berbeda.
    narasi_tag = content_div.find(lambda tag: tag.name in ['strong', 'b'] and 'NARASI' in tag.get_text(strip=True).upper())
    
    if narasi_tag:
        # Coba ambil paragraf (<p>) berikutnya
        next_element = narasi_tag.find_parent("p").find_next_sibling()
        
        if next_element and (next_element.name == 'p' or next_element.name == 'div'):
            claim_text = next_element.get_text(strip=True)
            if len(claim_text) > 20:
                return claim_text
        
        # Fallback jika klaim ada di tag <p> yang sama setelah ":"
        full_parent_text = narasi_tag.find_parent("p").get_text(strip=True)
        if ":" in full_parent_text:
            try:
                claim_text = full_parent_text.split(":", 1)[1].strip()
                if len(claim_text) > 20:
                    return claim_text
            except:
                pass

    # 6. Jika tidak ada klaim yang ditemukan dengan kedua strategi
    return None

def ekstrak_judul(soup: BeautifulSoup) -> str:
    title_selectors = ["h1.entry-title", "h1.post-title", "article h1", "h1.mh-entry-title", "h1"]
    for sel in title_selectors:
        el = soup.select_one(sel)
        if el:
            title = el.get_text(strip=True)
            if len(title) > 10:
                return strip_tbh_title_label(title)
    return ""

# ============== EKSTRAKSI ARTIKEL DENGAN FORMAT BARU ==============
def ekstrak_artikel_hoax(url: str) -> Optional[Dict]:
    """Ekstrak artikel dengan format yang lebih clean untuk dataset"""
    r = ambil_dengan_retry(url, max_retries=5, timeout=25)
    if not r: 
        return None
    
    try:
        soup = BeautifulSoup(r.content, "html.parser")
    except:
        return None

    # Title (dibersihkan dari label [SALAH], [BENAR], dll)
    title = ""
    for sel in ["h1.entry-title", "h1.post-title", "article h1", "h1.mh-entry-title", "h1"]:
        el = soup.select_one(sel)
        if el and len(el.get_text(strip=True)) > 5:
            raw_title = el.get_text(strip=True)
            title = strip_tbh_title_label(raw_title)
            break
    
    if not title or len(title) < 10:
        return None

    # Text content - ekstrak yang lebih bersih
    text = ekstrak_klaim_hoaks_asli(soup)
    
    if not text or len(text) < 20:
        return None

    # Extract date from URL pattern
    date_raw = ""
    date_pattern = re.search(r"/(\d{4})/(\d{1,2})/(\d{1,2})/", url)
    if date_pattern:
        y, m, d = date_pattern.groups()
        date_raw = f"{y}-{m.zfill(2)}-{d.zfill(2)}"

    # Categories
    cats = ekstrak_kategori(soup)
    
    # Images
    imgs = ekstrak_gambar(soup)
    
    # Metrics
    metrics = ekstrak_metrics_sosial(soup)

    # Compile article data
    artikel_data = {
        "url": url,
        "title": title[:300],
        "date_raw": date_raw,
        "text": text[:8000],
        "text_len": len(text),
        "categories": cats,
        "images": imgs,
        "post_view": metrics["views"],
        "post_likes": metrics["likes"], 
        "post_comment": metrics["comments"],
        "post_share": metrics["shares"],
        "label": 0
    }
    
    return artikel_data if filter_berita_politik(artikel_data) else None

# ============== MANAJEMEN STATE ==============
STATE_VISITED = os.path.join(STATE_DIR, "visited_urls2.json")

def baca_visited() -> Set[str]:
    """Membaca set URL yang sudah dikunjungi"""
    if os.path.exists(STATE_VISITED):
        with open(STATE_VISITED, "r", encoding="utf-8") as f:
            try:
                return set(json.load(f))
            except:
                return set()
    return set()

def simpan_visited(visited: Set[str]):
    """Menyimpan set URL yang sudah dikunjungi"""
    with open(STATE_VISITED, "w", encoding="utf-8") as f:
        json.dump(sorted(list(visited)), f, ensure_ascii=False, indent=2)

# ============== PENYIMPANAN DATA DENGAN FORMAT BARU ==============

FINAL_CSV = os.path.join(OUTPUT_DIR, "turnbackhoax_fix.csv")

def ambil_first_atau_kosong(x: str) -> str:
    return x.split("|")[0] if isinstance(x, str) and x else ""

def simpan_batch(rows: List[Dict], total_collected: int):
    if not rows:
        return
    
    df = pd.DataFrame(rows)
    
    start_id = total_collected + 1
    df["id"] = range(start_id, start_id + len(df))
    
    def format_tanggal(date_str):
        if not date_str:
            return ""
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d/%m/%Y")
        except:
            return ""
    
    df["blog_date"] = df["date_raw"].apply(format_tanggal)
    
    df["blog_title"] = df["title"]
    
    def determine_flag(row):
        title_lower = row.get('title', '').lower()
        if any(word in title_lower for word in ['penipuan', 'scam', 'phishing']):
            return 'PENIPUAN'
        elif '[salah]' in title_lower:
            return 'SALAH'
        elif '[benar]' in title_lower:
            return 'BENAR'
        else:
            return 'SALAH'
    
    df["flag"] = df.apply(determine_flag, axis=1)
    
    def extract_social_media(text):
        text_lower = text.lower() if text else ""
        platforms = {
            'Twitter': ['twitter', 'x.com'],
            'Facebook': ['facebook'],
            'Instagram': ['instagram'], 
            'TikTok': ['tiktok'],
            'WhatsApp': ['whatsapp'],
            'YouTube': ['youtube']
        }
        
        for platform, keywords in platforms.items():
            if any(keyword in text_lower for keyword in keywords):
                return platform
        return 'Twitter'
    
    df["social_media"] = df["text"].apply(extract_social_media)
    
    df["post_text"] = df["text"]
    
    df["post_date"] = df["blog_date"]
    
    df["blog_check"] = ""
    
    df["blog_conclusion"] = ""
    
    df["post_view"] = df.get("post_view", 0)
    df["post_likes"] = df.get("post_likes", 0) 
    df["post_comment"] = df.get("post_comment", 0)
    df["post_share"] = df.get("post_share", 0)
    
    df["post_url"] = df["url"]
    df["archive_url"] = ""
    df["blog_url"] = BASE_URL
    
    df["thumbnail"] = df.get("images", [[]]).apply(
        lambda x: x[0] if isinstance(x, list) and len(x) > 0 else ""
    )
    
    final_cols = [
        "id", "blog_date", "blog_title", "flag", "social_media", "post_text",
        "post_date", "blog_check", "blog_conclusion", "post_view", "post_likes", 
        "post_comment", "post_share", "post_url", "archive_url", "blog_url", "thumbnail"
    ]
    
    for col in final_cols:
        if col not in df.columns:
            df[col] = ""
    
    final_df = df[final_cols]
    
    if os.path.exists(FINAL_CSV):
        final_df.to_csv(FINAL_CSV, index=False, mode='a', header=False, encoding='utf-8')
    else:
        final_df.to_csv(FINAL_CSV, index=False, encoding='utf-8')
    
    print(f"✓ Disimpan {len(final_df)} records | Total: {total_collected + len(final_df)}")
# ============== MAIN RUNNER ==============
def jalankan_scraper(total_target: int = 2000, batch_size: int = 200, workers: int = 12):
    """Scraper dengan optimasi untuk mendapatkan lebih banyak data"""
    
    visited = baca_visited()
    total_collected = 0
    
    if os.path.exists(FINAL_CSV):
        try:
            existing_df = pd.read_csv(FINAL_CSV)
            total_collected = len(existing_df)
        except:
            total_collected = 0
    
    print("\n" + "=" * 70)
    print("TURNBACKHOAX SCRAPER - BERITA POLITIK (FORMAT FIXED)")
    print("=" * 70)
    print(f"Target: {total_target} | Batch: {batch_size} | Workers: {workers}")
    print(f"Rentang tanggal: {START_DATE} hingga {END_DATE}") # Akan print 2021-01-01
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
        
        print("\nFase penemuan URL (PARALLEL FETCH)...")
        
        # =======================================================
        # PERBAIKAN DI SINI: Naikkan angka max_sitemaps
        # =======================================================
        urls = temukan_urls_dari_sitemap(max_sitemaps=70) # Naikkan dari 20 ke 70
        # =======================================================
        
        uniq_list = []
        seen_local = set()
        for u in urls:
            u_clean = u.rstrip("/")
            if u_clean in visited or u_clean in seen_local:
                continue
            seen_local.add(u_clean)
            uniq_list.append(u_clean)
        
        # Ambil sampel acak agar tidak terlalu berurutan
        random.shuffle(uniq_list) 
        
        if len(uniq_list) > this_batch_target * 5:
            uniq_list = uniq_list[:this_batch_target * 5]
        
        print(f"Kandidat URL: {len(uniq_list)}")
        print(f"\nFase ekstraksi (Workers: {workers})...")
        
        def work(u: str) -> Optional[Dict]:
            try:
                return ekstrak_artikel_hoax(u)
            except Exception:
                return None
        
        arts: List[Dict] = []
        processed = 0
        
        with ThreadPoolExecutor(max_workers=max(1, min(workers, 20))) as ex:
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
        
        print(f"\nTerekstrak: {len(arts)} artikel politik dari {processed} URLs")
        
        if arts:
            avg_views = sum(a.get('post_view', 0) for a in arts) / len(arts)
            avg_likes = sum(a.get('post_likes', 0) for a in arts) / len(arts)
            avg_comments = sum(a.get('post_comment', 0) for a in arts) / len(arts)
            avg_shares = sum(a.get('post_share', 0) for a in arts) / len(arts)
            print(f"Metrics rata-rata - Views: {avg_views:.1f}, Likes: {avg_likes:.1f}, "
                  f"Comments: {avg_comments:.1f}, Shares: {avg_shares:.1f}")
        
        if not arts:
            simpan_visited(visited)
            print("Tidak ada artikel baru, tunggu 90 detik...")
            time.sleep(90)
            batch_id += 1
            # Jika tidak ada URL kandidat DAN tidak ada artikel terekstrak, mungkin sudah habis
            if not uniq_list:
                print("Tidak ada URL kandidat baru ditemukan. Menghentikan scraper.")
                break 
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
        if efficiency > 0.6:
            sleep_time = 90
        elif efficiency > 0.3:
            sleep_time = 150
        else:
            sleep_time = 210
        
        print(f"Menunggu: {sleep_time // 60} menit (Efisiensi: {efficiency:.1%})")
        time.sleep(sleep_time)
        
        batch_id += 1
    
    print(f"\n{'=' * 70}")
    print("SELESAI")
    print(f"{'=' * 70}")
    print(f"Total artikel politik: {total_collected}")
    print(f"File: {FINAL_CSV}")
    print(f"Format: EXACT match dengan contoh data")
    print(f"{'=' * 70}\n")

if __name__ == "__main__":
    jalankan_scraper(
        total_target=3500,
        batch_size=200, 
        workers=15,
    ) 