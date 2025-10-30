import os, time, re, json
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
import feedparser
from bs4 import BeautifulSoup
import pandas as pd
from src.utils.net import get
from src.utils.io import save_json

OUTPUT_DIR = "./data/raw/news/"
IMG_DIR = os.path.join(OUTPUT_DIR, "images")
RSS_FEEDS = {
    "kompas": "https://rss.kompas.com/nasional",
    "detik": "https://news.detik.com/berita/rss",
    "cnn":   "https://www.cnnindonesia.com/nasional/rss",
    "antaranews": "https://www.antaranews.com/rss/politik",
}

POLITICAL_KEYWORDS = [
    "UU", "undang-undang", "KUHP", "KUHAP", "ITE", "revisi", "peraturan", "hukum", "peradilan",
    "Mahkamah", "Kemenkumham", "Kejaksaan", "KPK", "Kepolisian", "penegakan hukum",
    "politik", "partai", "pemilu", "parpol", "koalisi", "kebijakan politik", "KPU", "Bawaslu",
    "caleg", "capres", "pilkada", "pemerintah", "menteri", "kabinet", "DPR", "MPR",
    "HAM", "Komnas HAM", "hak asasi", "pelanggaran HAM", "penghilangan paksa",
    "netralitas ASN", "pembela HAM", "reformasi hukum",
]

WIB_OFFSET = 7 * 3600

def parse_iso_like(dt_str):
    if not dt_str:
        return None
    s = dt_str.strip().replace(" ", "T")
    try_fmts = [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M%z",
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
    ]
    for fmt in try_fmts:
        try:
            dt = datetime.strptime(s, fmt)
            if dt.tzinfo is None:
                ts = dt.replace(tzinfo=timezone.utc).timestamp()
                dt = datetime.fromtimestamp(ts + WIB_OFFSET, tz=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return dt
        except Exception:
            continue
    return None

def to_iso(dt):
    return dt.astimezone(timezone.utc).isoformat()

def norm_url(u):
    parts = urlsplit(u)
    q = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if not k.lower().startswith("utm_")]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(q), parts.fragment))

def expand_rss_filtered(rss_url, keywords, limit=120, date_start=None, date_end=None):
    try:
        r = get(rss_url, timeout=20)
        d = feedparser.parse(r.text)
    except Exception:
        d = feedparser.parse(rss_url)
    urls = []
    for e in d.entries[:limit]:
        title = getattr(e, "title", "") or ""
        summary = getattr(e, "summary", "") or ""
        if not any(k.lower() in title.lower() or k.lower() in summary.lower() for k in keywords):
            continue
        dt_rss = None
        if getattr(e, "published", None):
            dt_rss = parse_iso_like(e.published)
        elif getattr(e, "updated", None):
            dt_rss = parse_iso_like(e.updated)
        elif getattr(e, "published_parsed", None):
            try:
                dt_rss = datetime(*e.published_parsed[:6], tzinfo=timezone.utc)
            except Exception:
                dt_rss = None
        if date_start or date_end:
            pass_ok = True
            if dt_rss:
                if date_start and dt_rss < date_start:
                    pass_ok = False
                if date_end and dt_rss > date_end:
                    pass_ok = False
            if not pass_ok:
                continue
        link = getattr(e, "link", "")
        if link:
            urls.append(norm_url(link))
    return list(dict.fromkeys(urls))

def extract_article_generic(url, source):
    r = get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    title_node = soup.find(["h1", "h2"])
    title = title_node.get_text(strip=True) if title_node else ""
    sel_map = {
        "kompas": "div.read__content",
        "detik": "div.detail__body-text",
        "cnn":   "div.detail-text, div.article",
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
    m = re.search(r'property="article:published_time" content="([^"]+)"', r.text) or \
        re.search(r'name="pubdate" content="([^"]+)"', r.text) or \
        re.search(r'itemprop="datePublished" content="([^"]+)"', r.text)
    date_raw = m.group(1) if m else ""
    og = re.search(r'property="og:image" content="([^"]+)"', r.text)
    image = og.group(1) if og else ""
    parsed_dt = parse_iso_like(date_raw)
    return {
        "url": url,
        "domain": urlsplit(url).netloc,
        "source": source,
        "title": title,
        "date": date_raw,
        "date_utc": to_iso(parsed_dt) if parsed_dt else "",
        "text": text,
        "text_len": len(text) if text else 0,
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

def create_metadata(news_data, topic="Kebijakan Hukum, Politik, & HAM"):
    created_utc = to_iso(datetime.now(timezone.utc))
    records = []
    for i, item in enumerate(news_data, 1):
        preview = (item.get("text","")[:280] + "…") if item.get("text","") and len(item["text"]) > 280 else item.get("text","")
        records.append({
            "id": i,
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "domain": item.get("domain", ""),
            "source": item.get("source", ""),
            "topic": topic,
            "date_raw": item.get("date", ""),
            "date_utc": item.get("date_utc", ""),
            "modality": "text",
            "language": "id",
            "text_len": item.get("text_len", 0),
            "text_preview": preview,
            "image_url": item.get("image", ""),
            "image_path": item.get("image_path", ""),
            "label": 0,
            "created_at_utc": created_utc,
            "notes": "berita valid hasil scraping portal resmi"
        })
    return records

def scrape_all_sources(
    output_dir=OUTPUT_DIR,
    keywords=POLITICAL_KEYWORDS,
    max_per_source=40,
    download_images=True,
    date_start=datetime(2024, 11, 1, tzinfo=timezone.utc),
    date_end=None
):
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(IMG_DIR, exist_ok=True)

    if date_end is None:
        date_end = datetime.now(timezone.utc)

    tasks = []
    for name, feed in RSS_FEEDS.items():
        urls = expand_rss_filtered(feed, keywords, limit=max_per_source * 3, date_start=date_start, date_end=date_end)
        print(f"{name}: candidates {len(urls)}")
        tasks.extend((name, u) for u in urls[:max_per_source])
        time.sleep(0.3)

    seen = set()
    uniq_tasks = []
    for src, u in tasks:
        if u not in seen:
            seen.add(u)
            uniq_tasks.append((src, u))
    print("Total unique URLs:", len(uniq_tasks))

    out, retry = [], []
    for i, (src, u) in enumerate(uniq_tasks, start=1):
        print(f"[{i}/{len(uniq_tasks)}] {src} -> {u}")
        try:
            art = extract_article_generic(u, src)
            if art["text"] and len(art["text"]) > 120:
                if download_images and art.get("image", "").startswith("http"):
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

    metadata = create_metadata(out)
    df = pd.DataFrame(metadata)
    df.to_csv(os.path.join(output_dir, "metadata_valid.csv"), index=False, encoding="utf-8")
    with open(os.path.join(output_dir, "metadata_valid.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print("Saved:", len(out), "articles,", len(retry), "retry")
    print("metadata_valid.csv & metadata_valid.json generated automatically!")
    return out

if __name__ == "__main__":
    scrape_all_sources(download_images=True, max_per_source=40)
