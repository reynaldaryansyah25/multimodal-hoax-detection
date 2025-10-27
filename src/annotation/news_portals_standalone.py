"""
Scraper berita politik dari portal resmi (kompatibel pipeline)
Author: Reynald Aryansyah
Date: 2025-10-26
"""

import os, time, re
from datetime import datetime
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

import feedparser
from bs4 import BeautifulSoup

from src.utils.net import get
from src.utils.io import save_json

OUTPUT_DIR = "./data/raw/news/"
IMG_DIR = os.path.join(OUTPUT_DIR, "images")

# Feed yang stabil
RSS_FEEDS = {
    "kompas": "https://rss.kompas.com/nasional",
    "detik": "https://news.detik.com/berita/rss",
    "tempo": "https://rss.tempo.co/nasional",
    "antaranews": "https://www.antaranews.com/rss/politik",
}

POLITICAL_KEYWORDS = [
    "Presiden","Prabowo","pemerintah","kabinet","menteri",
    "DPR","APBN","kebijakan","subsidi","anggaran",
    "program","nasional","politik"
]

def norm_url(u):
    parts = urlsplit(u)
    q = [(k,v) for k,v in parse_qsl(parts.query, keep_blank_values=True) if not k.lower().startswith("utm_")]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(q), parts.fragment))

def expand_rss_filtered(rss_url, keywords, limit=120):
    # Ambil XML dengan header stabil, lalu parse string agar tidak ditolak server
    try:
        r = get(rss_url, timeout=20)
        d = feedparser.parse(r.text)
    except Exception:
        d = feedparser.parse(rss_url)
    urls = []
    for e in d.entries[:limit]:
        title = getattr(e, "title", "") or ""
        summary = getattr(e, "summary", "") or ""
        if any(k.lower() in title.lower() or k.lower() in summary.lower() for k in keywords):
            link = getattr(e, "link", "")
            if link:
                urls.append(norm_url(link))
    return list(dict.fromkeys(urls))

def extract_article_generic(url, source):
    r = get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    title_node = soup.find(["h1","h2"])
    title = title_node.get_text(strip=True) if title_node else ""
    # selector konten per sumber + fallback
    sel_map = {
        "kompas": "div.read__content",
        "detik": "div.detail__body-text",
        "tempo": "div.detail-content, div#isi",
        "antaranews": "div.post-content, div#content",
    }
    node = soup.select_one(sel_map.get(source, "article, div.entry-content, div.content"))
    text = ""
    if node:
        ps = node.find_all("p")
        text = " ".join(p.get_text(" ", strip=True) for p in ps) or node.get_text(" ", strip=True)
    if not text:
        art = soup.find("article")
        if art:
            text = " ".join(p.get_text(" ", strip=True) for p in art.find_all("p"))
    # tanggal
    m = re.search(r'property="article:published_time" content="([^"]+)"', r.text) or \
        re.search(r'name="pubdate" content="([^"]+)"', r.text) or \
        re.search(r'itemprop="datePublished" content="([^"]+)"', r.text)
    date = m.group(1) if m else ""
    # top image
    og = re.search(r'property="og:image" content="([^"]+)"', r.text)
    image = og.group(1) if og else ""
    return {
        "url": url,
        "domain": urlsplit(url).netloc,
        "source": source,
        "title": title,
        "date": date,
        "text": text,
        "image": image,
    }

def download_image(url, path):
    try:
        r = get(url, timeout=20)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(r.content)
        return True
    except Exception as e:
        print("img error:", url, e)
        return False

def scrape_all_sources(output_dir=OUTPUT_DIR, keywords=POLITICAL_KEYWORDS, max_per_source=40, download_images=True):
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(IMG_DIR, exist_ok=True)

    tasks = []
    for name, feed in RSS_FEEDS.items():
        urls = expand_rss_filtered(feed, keywords, limit=max_per_source*3)
        if not urls:
            time.sleep(1.5)
            urls = expand_rss_filtered(feed, keywords, limit=max_per_source*3)
        print(f"{name}: candidates {len(urls)}")
        tasks.extend((name, u) for u in urls[:max_per_source])
        time.sleep(0.3)

    # dedup global
    seen = set()
    uniq_tasks = []
    for src, u in tasks:
        if u not in seen:
            seen.add(u); uniq_tasks.append((src, u))
    print("Total unique URLs:", len(uniq_tasks))

    out, retry = [], []
    for i, (src, u) in enumerate(uniq_tasks, start=1):
        print(f"[{i}/{len(uniq_tasks)}] {src} -> {u}")
        try:
            art = extract_article_generic(u, src)
            if (art["text"] and len(art["text"]) > 120) or art["title"]:
                if download_images and art.get("image","").startswith("http"):
                    ext = (art["image"].split("?")[0].split(".")[-1] or "jpg")[:4]
                    ip = os.path.join(IMG_DIR, f"NEWS_{i:04d}.{ext}")
                    if download_image(art["image"], ip):
                        art["image_path"] = ip
                out.append(art)
            else:
                retry.append(u)
            time.sleep(0.6)
        except Exception as e:
            print("news error:", u, e)
            retry.append(u)
            time.sleep(1.0)

    save_json(os.path.join(output_dir, "articles.json"), out)
    save_json(os.path.join(output_dir, "retry_queue.json"), retry)
    print("Saved:", len(out), "articles,", len(retry), "retry")
    return out

if __name__ == "__main__":
    scrape_all_sources(download_images=True, max_per_source=40)
