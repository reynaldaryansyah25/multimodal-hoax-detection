"""
Scraper TurnBackHoax.ID (fokus politik: kategori dan tag)
Author: Reynald Aryansyah
Date: 2025-10-26
"""

import os, time, re, json
from datetime import datetime
from urllib.parse import urljoin, urlsplit, urlunsplit, parse_qsl, urlencode
import requests
from bs4 import BeautifulSoup

BASE = "https://turnbackhoax.id/"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"

# Slug politik (kategori dan tag) yang akan dicoba berurutan
POLITIC_SLUGS = [
    "kategori/hoax",
    "kategori/disinformasi", 
    "kategori/salah-kutip",
    "kategori/klarifikasi",
    "tag/politik",
    "tag/pemilu",
    "tag/presiden",
    "tag/partai",
    "tag/kampanye",
    "tag/kabinet",
]

def get(url, retries=3, timeout=15):
    last = None
    for i in range(retries):
        try:
            r = requests.get(url, headers={"User-Agent": UA, "Accept-Language":"id,en;q=0.8"}, timeout=timeout)
            r.raise_for_status()
            time.sleep(1.0)
            return r
        except Exception as e:
            last = e; time.sleep(1.5*(i+1))
    raise last

def norm_url(u):
    parts = urlsplit(u)
    q = [(k,v) for k,v in parse_qsl(parts.query, keep_blank_values=True) if not k.lower().startswith("utm_")]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(q), parts.fragment))

def list_archive(slug, page=1):
    url = urljoin(BASE, f"{slug}/page/{page}/")
    r = get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    items = []
    for a in soup.select("h3.entry-title a, h2.entry-title a, .td-module-title a"):
        href = a.get("href")
        if href:
            items.append(norm_url(href if href.startswith("http") else urljoin(BASE, href)))
    # dedup
    out, seen = [], set()
    for u in items:
        if u not in seen:
            seen.add(u); out.append(u)
    return out

def parse_article(url):
    r = get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    tnode = soup.find(["h1","h2"], {"class": re.compile("(entry|post|td-post)-title")}) or soup.find(["h1","h2"])
    title = tnode.get_text(strip=True) if tnode else ""
    # tanggal
    date = ""
    t = soup.find("time")
    if t and (t.get("datetime") or t.text):
        date = t.get("datetime") or t.get_text(strip=True)
    # isi
    text = ""
    for pat in ["entry-content", "post-content", "td-post-content", "content"]:
        node = soup.find("div", {"class": re.compile(pat)})
        if node:
            text = node.get_text("\n", strip=True); break
    if not text:
        art = soup.find("article")
        if art:
            text = "\n".join(p.get_text(" ", strip=True) for p in art.find_all("p"))
    # label
    labels = [c.get_text(strip=True) for c in soup.select("a[rel='category tag'], a[rel='tag'], .td-post-category a")]
    # gambar
    images = []
    for sel in ["article img", ".entry-content img", "img"]:
        for img in soup.select(sel):
            src = img.get("src") or img.get("data-src")
            if src: images.append(src)
        if images: break
    images = images[:3]
    return {"url": url, "title": title, "date": date, "text": text, "labels": labels, "images": images}

def download_image(url, path):
    try:
        r = get(url, timeout=20)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f: f.write(r.content)
        return True
    except Exception as e:
        print("img error:", url, e); return False

def scrape_and_save(output_dir="./data/raw/turnbackhoax/", pages_per_slug=3, max_per_slug=60):
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir,"images"), exist_ok=True)
    os.makedirs(os.path.join(output_dir,"metadata"), exist_ok=True)

    rows = []
    for slug in POLITIC_SLUGS:
        print(f"\n== Collecting from {slug} ==")
        urls = []
        for p in range(1, pages_per_slug+1):
            try:
                lst = list_archive(slug, page=p)
                print(f"{slug} page {p}: {len(lst)}")
                urls.extend(lst)
            except Exception as e:
                print("archive error", slug, "p", p, e)
        urls = list(dict.fromkeys(urls))[:max_per_slug]
        print("candidates:", len(urls))

        for i, u in enumerate(urls, start=1):
            print(f"- {slug} [{i}/{len(urls)}]")
            try:
                art = parse_article(u)
                sid = f"TBH_{slug.replace('/','-')}_{i:04d}"
                image_paths = []
                for j, img in enumerate(art["images"]):
                    ext = (img.split("?")[0].split(".")[-1] or "jpg")[:4]
                    ip = os.path.join(output_dir,"images", f"{sid}_{j+1}.{ext}")
                    if download_image(img, ip):
                        image_paths.append(ip)
                    time.sleep(0.4)
                rows.append({
                    "sample_id": sid,
                    "source": "turnbackhoax",
                    "slug": slug,
                    "title": art["title"],
                    "url": art["url"],
                    "date": art["date"],
                    "labels": "|".join(art["labels"]),
                    "text": art["text"],
                    "image_paths": "|".join(image_paths),
                    "num_images": len(image_paths),
                    "scraped_at": datetime.utcnow().isoformat()
                })
                time.sleep(0.8)
            except Exception as e:
                print("detail error:", u, e)

    with open(os.path.join(output_dir,"articles.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    import pandas as pd
    df = pd.DataFrame(rows)
    csv_path = os.path.join(output_dir,"metadata","turnbackhoax_metadata.csv")
    df.to_csv(csv_path, index=False, encoding="utf-8")
    print("Saved:", csv_path, "rows:", len(df))
    return df

if __name__ == "__main__":
    # kumpulkan politik dari beberapa kategori+tag
    scrape_and_save("./data/raw/turnbackhoax/", pages_per_slug=3, max_per_slug=60)
