#!/usr/bin/env python3
# tbh_debug_extraction.py
# Script untuk debug mengapa ekstraksi 0 artikel

import re
import requests
from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://turnbackhoax.id/"
START_DATE = "2024-10-20"
END_DATE = datetime.now().strftime("%Y-%m-%d")
START_DT = datetime.fromisoformat(START_DATE)
END_DT = datetime.fromisoformat(END_DATE)

def buat_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
        backoff_factor=1.5
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

session = buat_session()

def test_ekstraksi_url(url):
    """
    Test ekstraksi satu URL untuk lihat masalahnya
    """
    print(f"\n{'=' * 70}")
    print(f"TEST URL: {url}")
    print(f"{'=' * 70}\n")
    
    # Step 1: Fetch
    print("Step 1: Mengambil halaman...")
    try:
        r = session.get(url, timeout=25, headers={"User-Agent": "Mozilla/5.0"})
        print(f"Status: {r.status_code}")
        print(f"Content length: {len(r.content)} bytes")
        
        if r.status_code != 200:
            print("ERROR: Status bukan 200")
            return
    except Exception as e:
        print(f"ERROR: {e}")
        return
    
    # Step 2: Parse
    print("\nStep 2: Parse HTML...")
    soup = BeautifulSoup(r.content, "html.parser")
    print(f"HTML parsed successfully")
    
    # Step 3: Extract Title
    print("\nStep 3: Extract Title...")
    title_selectors = [
        "h1.entry-title",
        "h1.post-title",
        "article h1",
        "h1.mh-entry-title",
        "h1",
    ]
    
    title = ""
    for sel in title_selectors:
        el = soup.select_one(sel)
        if el:
            title = el.get_text(strip=True)
            print(f"Found with selector '{sel}': {title[:80]}")
            if len(title) > 10:
                break
    
    if not title or len(title) < 10:
        print(f"ERROR: Title terlalu pendek atau tidak ada ({len(title)} chars)")
    else:
        print(f"OK: Title valid")
    
    # Step 4: Extract Text
    print("\nStep 4: Extract Text...")
    candidates = [
        "article .entry-content",
        ".entry-content",
        ".post-content",
        "article",
        "main article",
        ".article-content",
    ]
    
    text = ""
    for sel in candidates:
        node = soup.select_one(sel)
        if node:
            paras = node.find_all(["p", "li"])
            text = "\n\n".join([
                p.get_text(" ", strip=True) 
                for p in paras 
                if len(p.get_text(strip=True)) > 20
            ])
            print(f"Found with selector '{sel}': {len(text)} chars")
            if len(text) >= 100:
                print(f"OK: Text valid")
                print(f"Preview: {text[:200]}...")
                break
    
    if len(text) < 100:
        print(f"ERROR: Text terlalu pendek ({len(text)} chars)")
    
    # Step 5: Extract Date
    print("\nStep 5: Extract Date...")
    date_raw = ""
    date_match = re.search(r"/(\d{4})/(\d{1,2})/(\d{1,2})/", url)
    if date_match:
        y, m, d = date_match.groups()
        date_raw = f"{y}-{m.zfill(2)}-{d.zfill(2)}"
        print(f"Date dari URL: {date_raw}")
        
        try:
            dt = datetime.fromisoformat(date_raw)
            if dt < START_DT or dt > END_DT:
                print(f"ERROR: Date di luar range ({START_DATE} - {END_DATE})")
            else:
                print(f"OK: Date dalam range")
        except:
            print("ERROR: Tidak bisa parse date")
    else:
        print("ERROR: Date pattern tidak match di URL")
    
    # Step 6: Extract Categories
    print("\nStep 6: Extract Categories...")
    cats = []
    selectors = [
        "span.cat-links a",
        ".entry-meta a[rel='category tag']",
        "a[rel='category']",
        ".post-categories a",
    ]
    
    for sel in selectors:
        items = soup.select(sel)
        if items:
            print(f"Found with selector '{sel}': {len(items)} items")
            for item in items[:3]:
                print(f"  - {item.get_text(strip=True)}")
            break
    
    # Step 7: Extract Images
    print("\nStep 7: Extract Images...")
    imgs = []
    for sel in [".entry-content img", "article img", ".post-content img"]:
        for img in soup.select(sel):
            src = img.get("src")
            if src:
                imgs.append(src)
    
    print(f"Found: {len(imgs)} images")
    if imgs:
        for img in imgs[:3]:
            print(f"  - {img[:80]}")
    
    print(f"\n{'=' * 70}")
    print("KESIMPULAN:")
    print(f"{'=' * 70}")
    
    if len(title) > 10 and len(text) >= 100 and date_raw:
        print("SUKSES: Artikel bisa diextract")
    else:
        print("GAGAL: Ada field yang missing/invalid")
        print(f"  - Title: {len(title)} chars (perlu >10)")
        print(f"  - Text: {len(text)} chars (perlu >=100)")
        print(f"  - Date: {date_raw if date_raw else 'TIDAK ADA'}")

# Test dengan beberapa URL dari sitemap
test_urls = [
    "https://turnbackhoax.id/2025/11/03/salah-prabowo-mendapat-surat-terbuka-dari-diaspora-belanda-berisi-6-tuntutan/",
    "https://turnbackhoax.id/2025/11/03/salah-puan-ke-kejagung-negara-tidak-boleh-menzalimi-koruptor/",
    "https://turnbackhoax.id/2025/11/02/salah-purbaya-resmi-menarik-anggaran-rp71-triliun-dari-program-mbg-untuk-dialihkan-ke-beras-gratis/",
]

if __name__ == "__main__":
    for url in test_urls:
        test_ekstraksi_url(url)
        print("\n")
