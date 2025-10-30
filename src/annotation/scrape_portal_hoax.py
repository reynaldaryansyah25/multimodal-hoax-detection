import os, time, re, json
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit, urlunsplit, parse_qsl, urlencode, quote_plus, urlunsplit
import random
import requests
from bs4 import BeautifulSoup
import pandas as pd

BASE = "https://turnbackhoax.id/"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"

OUTPUT_DIR = "./data/raw/turnbackhoax/"
IMG_DIR = os.path.join(OUTPUT_DIR, "images")
META_DIR = os.path.join(OUTPUT_DIR, "metadata")

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
    "tag/kementerian",
    "tag/dpr",
    "tag/mpr",
    "tag/anggaran",
    "tag/apbn",
    "tag/subsidi",
    "tag/uu",
    "tag/uu-ite",
    "tag/kuhp",
    "tag/kuhap",
    "tag/bawaslu",
    "tag/kpu",
    "tag/prabowo",
    "tag/gibran",
    "tag/pemerintah",
]

POLITICAL_KEYWORDS = [
    "politik","presiden","wakil presiden","prabowo","gibran","kabinet","menteri","kementerian",
    "dpr","mpr","apbn","anggaran","subsidi","bansos","kebijakan","perppu","perpres","permen",
    "uu","undang-undang","uu ite","kuhp","kuhap","bawaslu","kpu","kampanye","pilkada","pemilu",
    "partai","koalisi","oposisi","netralitas asn","hak pilih","mahkamah konstitusi","mk",
]

PRABOWO_GIBRAN_KEYWORDS = [
    "prabowo","gibran","kabinet indonesia maju","kabinet merah putih","menteri pertahanan",
    "wapres gibran","presiden prabowo","program makan siang gratis","stabilitas harga pangan",
]

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA, "Accept-Language": "id,en;q=0.8"})

def get(url, retries=3, timeout=20):
    last = None
    for i in range(retries):
        try:
            r = SESSION.get(url, timeout=timeout)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            time.sleep(0.6 + random.random() * 0.5)
            return r
        except Exception as e:
            last = e
            time.sleep(1.0 * (i + 1) + random.random())
    raise last

def norm_url(u):
    parts = urlsplit(u)
    q = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if not k.lower().startswith("utm_")]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(q), parts.fragment))

def parse_date_multi(soup):
    date_str = ""
    meta = soup.find("meta", {"property": "article:published_time"}) or \
           soup.find("meta", {"property": "og:updated_time"}) or \
           soup.find("meta", {"itemprop": "datePublished"})
    if meta and meta.get("content"):
        date_str = meta["content"]
    else:
        t = soup.find("time")
        if t and (t.get("datetime") or t.text):
            date_str = t.get("datetime") or t.get_text(strip=True)
    return date_str or ""

def to_utc_iso(dt_str):
    if not dt_str:
        return ""
    s = dt_str.strip().replace(" ", "T")
    fmts = [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M%z",
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
    ]
    for fmt in fmts:
        try:
            dt = datetime.strptime(s.replace("Z", "+00:00"), fmt)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc).isoformat()
            return dt.astimezone(timezone.utc).isoformat()
        except Exception:
            continue
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat()
    except Exception:
        return ""

def extract_sections(soup):
    def collect_after(node):
        out = []
        for sib in node.next_siblings:
            if getattr(sib, "name", None) in ["h1", "h2", "h3", "strong", "b"]:
                break
            if getattr(sib, "name", None) == "p":
                out.append(sib.get_text(" ", strip=True))
            if getattr(sib, "name", None) == "div":
                for p in sib.find_all("p"):
                    out.append(p.get_text(" ", strip=True))
        return "\n".join([x for x in out if x]).strip()
    narasi = ""
    penjelasan = ""
    for sel in ["h2", "h3", "strong", "b"]:
        for h in soup.find_all(sel):
            txt = (h.get_text(strip=True) or "").lower()
            if "narasi" in txt and not narasi:
                narasi = collect_after(h)
            if "penjelasan" in txt and not penjelasan:
                penjelasan = collect_after(h)
    return narasi.strip(), penjelasan.strip()

def list_archive(slug, page=1):
    url = urljoin(BASE, f"{slug}/page/{page}/")
    r = get(url)
    if r is None:
        return []
    soup = BeautifulSoup(r.text, "html.parser")
    items = []
    selectors = [
        "h3.entry-title a",
        "h2.entry-title a",
        ".td-module-title a",
        ".td-ss-main-content .td-module-title a",
        ".entry-title.td-module-title a",
    ]
    for sel in selectors:
        for a in soup.select(sel):
            href = a.get("href")
            if href:
                items.append(norm_url(href if href.startswith("http") else urljoin(BASE, href)))
    return list(dict.fromkeys(items))

def search_site(query, page=1):
    q = quote_plus(query)
    url = urljoin(BASE, f"?s={q}&paged={page}")
    r = get(url)
    if r is None:
        return []
    soup = BeautifulSoup(r.text, "html.parser")
    items = []
    for a in soup.select("h3.entry-title a, h2.entry-title a, .td-module-title a"):
        href = a.get("href")
        if href:
            items.append(norm_url(href if href.startswith("http") else urljoin(BASE, href)))
    return list(dict.fromkeys(items))

def is_political_match(title, text, labels):
    t = (title or "").lower()
    x = (text or "").lower()
    lbs = " ".join(labels).lower() if labels else ""
    score = 0
    for kw in POLITICAL_KEYWORDS:
        if kw in t: score += 2
        if kw in x: score += 1
        if kw in lbs: score += 1
    return score, score >= 2

def is_prabowo_gibran_match(title, text, labels):
    t = (title or "").lower()
    x = (text or "").lower()
    lbs = " ".join(labels).lower() if labels else ""
    for kw in PRABOWO_GIBRAN_KEYWORDS:
        if kw in t or kw in x or kw in lbs:
            return True
    return False

def parse_article(url):
    r = get(url)
    if r is None:
        return None
    soup = BeautifulSoup(r.text, "html.parser")
    tnode = soup.find(["h1", "h2"], {"class": re.compile("(entry|post|td-post)-title")}) or soup.find(["h1", "h2"])
    title = tnode.get_text(strip=True) if tnode else ""
    date_raw = parse_date_multi(soup)
    date_utc = to_utc_iso(date_raw)
    narasi, penjelasan = extract_sections(soup)
    if narasi or penjelasan:
        text = f"Narasi:\n{narasi}\n\nPenjelasan:\n{penjelasan}".strip()
    else:
        text = ""
        for pat in ["entry-content", "post-content", "td-post-content", "content"]:
            node = soup.find("div", {"class": re.compile(pat)})
            if node:
                text = node.get_text("\n", strip=True)
                break
        if not text:
            art = soup.find("article")
            if art:
                text = "\n".join(p.get_text(" ", strip=True) for p in art.find_all("p"))
    labels = [c.get_text(strip=True) for c in soup.select("a[rel='category tag'], a[rel='tag'], .td-post-category a")]
    tags_lower = {x.lower() for x in labels}
    images = []
    seen_img = set()
    for sel in ["article img", ".entry-content img", "img"]:
        for img in soup.select(sel):
            src = img.get("src") or img.get("data-src") or ""
            if not src and img.get("srcset"):
                srcset = img.get("srcset")
                cand = [c.strip().split(" ")[0] for c in srcset.split(",") if c.strip()]
                if cand:
                    src = cand[-1]
            if src and src not in seen_img:
                seen_img.add(src)
                images.append(src)
        if images:
            break
    images = images[:3]
    pol_score, pol_match = is_political_match(title, text, labels)
    pg_match = is_prabowo_gibran_match(title, text, labels)
    return {
        "url": url,
        "title": title,
        "date_raw": date_raw,
        "date_utc": date_utc,
        "text": text,
        "text_len": len(text) if text else 0,
        "labels_src": labels,
        "tags_lower": list(tags_lower),
        "images": images,
        "political_score": pol_score,
        "is_political": int(pol_match),
        "is_prabowo_gibran": int(pg_match),
    }

def fix_host_https(u: str) -> str:
    try:
        p = urlsplit(u)
        if p.scheme not in ("http", "https"):
            return u
        host = p.netloc
        if host.lower() == "www.turnbackhoax.id":
            p = p._replace(netloc="turnbackhoax.id")
            return urlunsplit((p.scheme, p.netloc, p.path, p.query, p.fragment))
        return u
    except Exception:
        return u

def download_image(url, path):
    try:
        fixed = fix_host_https(url)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        try:
            r = SESSION.get(fixed, timeout=20, stream=True)
            if r is None or r.status_code == 404:
                return False
            r.raise_for_status()
            with open(path, "wb") as f:
                for chunk in r.iter_content(8192):
                    if chunk:
                        f.write(chunk)
            return True
        except requests.exceptions.SSLError as ssl_e:
            print("img ssl warn (retry verify=False):", fixed, ssl_e)
            try:
                r = SESSION.get(fixed, timeout=20, stream=True, verify=False)
                r.raise_for_status()
                with open(path, "wb") as f:
                    for chunk in r.iter_content(8192):
                        if chunk:
                            f.write(chunk)
                return True
            except Exception as e2:
                print("img ssl fallback error:", fixed, e2)
                try:
                    p = urlsplit(fixed)
                    if p.scheme == "https":
                        http_url = urlunsplit(("http", p.netloc, p.path, p.query, p.fragment))
                        r = SESSION.get(http_url, timeout=20, stream=True)
                        r.raise_for_status()
                        with open(path, "wb") as f:
                            for chunk in r.iter_content(8192):
                                if chunk:
                                    f.write(chunk)
                        return True
                except Exception as e3:
                    print("img http fallback error:", fixed, e3)
                    return False
    except Exception as e:
        print("img error:", url, e)
        return False

def collect_urls(pages_per_slug, max_per_slug, extra_queries=None, search_pages=3):
    urls = []
    for slug in POLITIC_SLUGS:
        for p in range(1, pages_per_slug + 1):
            lst = list_archive(slug, page=p)
            if not lst:
                break
            urls.extend(lst)
    if extra_queries:
        for q in extra_queries:
            for p in range(1, search_pages + 1):
                lst = search_site(q, page=p)
                urls.extend(lst)
    urls = list(dict.fromkeys(urls))
    if max_per_slug:
        urls = urls[:max_per_slug * max(1, len(POLITIC_SLUGS))]
    return urls

def scrape_and_save(
    output_dir=OUTPUT_DIR,
    pages_per_slug=10,
    max_per_slug=180,
    filter_start=datetime(2024, 11, 1, tzinfo=timezone.utc),
    filter_end=None
):
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(IMG_DIR, exist_ok=True)
    os.makedirs(META_DIR, exist_ok=True)
    if filter_end is None:
        filter_end = datetime.now(timezone.utc)
    extra_queries = [
        "prabowo", "gibran", "kabinet", "menteri", "kementerian",
        "kebijakan pemerintah", "apbn", "anggaran", "subsidi",
        "revisi uu ite", "kuhp", "kuhap", "bawaslu", "kpu", "kampanye", "pilkada", "pemilu"
    ]
    all_urls = collect_urls(pages_per_slug, max_per_slug, extra_queries=extra_queries, search_pages=4)
    print("Total candidates:", len(all_urls))
    rows = []
    kept = 0
    for i, u in enumerate(all_urls, start=1):
        try:
            art = parse_article(u)
            if not art:
                continue
            art_dt = None
            if art.get("date_utc"):
                try:
                    art_dt = datetime.fromisoformat(art["date_utc"].replace("Z", "+00:00"))
                except Exception:
                    art_dt = None
            if art_dt:
                if art_dt < filter_start or art_dt > filter_end:
                    continue
            if not art.get("is_political"):
                continue
            sid = f"TBH_POL_{i:06d}"
            image_paths = []
            img_ok = 0
            for j, img in enumerate(art["images"]):
                ext = (img.split("?")[0].split(".")[-1] or "jpg")[:4]
                ip = os.path.join(IMG_DIR, f"{sid}_{j+1}.{ext}")
                if download_image(img, ip):
                    image_paths.append(ip)
                    img_ok += 1
                time.sleep(0.2 + random.random() * 0.2)
            rows.append({
                "sample_id": sid,
                "source": "turnbackhoax",
                "title": art["title"],
                "url": u,
                "date_raw": art["date_raw"],
                "date_utc": art["date_utc"],
                "labels_src": "|".join(art["labels_src"]),
                "label": 1,
                "is_politics": art.get("is_political", 0),
                "political_score": art.get("political_score", 0),
                "is_prabowo_gibran": art.get("is_prabowo_gibran", 0),
                "text": art["text"],
                "text_len": art["text_len"],
                "text_preview": (art["text"][:280] + "…") if art["text"] and len(art["text"]) > 280 else art["text"],
                "image_first": art["images"][0] if art["images"] else "",
                "image_paths": "|".join(image_paths),
                "num_images": len(image_paths),
                "scraped_at_utc": datetime.utcnow().isoformat() + "Z"
            })
            kept += 1
            if kept % 50 == 0:
                print(f"Kept {kept} items...")
            time.sleep(0.5 + random.random() * 0.4)
        except Exception as e:
            print("detail error:", u, e)
    df = pd.DataFrame(rows)
    csv_path = os.path.join(META_DIR, "metadata.csv")
    json_path = os.path.join(META_DIR, "metadata.json")
    df.to_csv(csv_path, index=False, encoding="utf-8")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print("\nSaved:", csv_path, "| Rows:", len(df))
    print("Saved:", json_path)
    return df

if __name__ == "__main__":
    scrape_and_save(
        OUTPUT_DIR,
        pages_per_slug=10,
        max_per_slug=180,
        filter_start=datetime(2024, 11, 1, tzinfo=timezone.utc),
        filter_end=None
    )
