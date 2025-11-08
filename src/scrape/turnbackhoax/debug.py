import os
import re
import time
import json
import random
import requests
from datetime import datetime
from urllib.parse import urljoin, quote_plus
from bs4 import BeautifulSoup
from typing import List, Dict, Set

# ============== CONFIG ==============
BASE_URL = "https://turnbackhoax.id/"

USER_AGENT_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
]

BASE_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Referer": BASE_URL,
}

DEBUG_DIR = "./debug_output/"
os.makedirs(DEBUG_DIR, exist_ok=True)

session = requests.Session()
session.headers.update(BASE_HEADERS)

# ============== HELPER FUNCTIONS ==============
def pick_headers() -> Dict[str, str]:
    h = BASE_HEADERS.copy()
    h["User-Agent"] = random.choice(USER_AGENT_POOL)
    return h

def get_page(url: str, timeout: int = 30):
    """Fetch page with retry"""
    try:
        time.sleep(random.uniform(1.0, 2.0))
        r = session.get(url, headers=pick_headers(), timeout=timeout)
        if r.status_code == 200:
            return r
        else:
            print(f"⚠️  Status {r.status_code} for {url}")
            return None
    except Exception as e:
        print(f"❌ Error fetching {url}: {e}")
        return None

# ============== DEBUG FUNCTIONS ==============

def debug_homepage():
    """Debug: Analisa struktur homepage"""
    print("\n" + "="*70)
    print("🏠 DEBUGGING HOMEPAGE")
    print("="*70)
    
    r = get_page(BASE_URL)
    if not r:
        print("❌ Failed to fetch homepage")
        return
    
    soup = BeautifulSoup(r.content, "html.parser")
    
    # Save HTML
    html_file = os.path.join(DEBUG_DIR, "homepage.html")
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(soup.prettify())
    print(f"✅ HTML saved: {html_file}")
    
    # Analyze structure
    print("\n📊 HOMEPAGE ANALYSIS:")
    
    # 1. Find all article containers
    article_containers = [
        ("article", soup.find_all("article")),
        ("div.post", soup.find_all("div", class_=re.compile("post"))),
        ("div.entry", soup.find_all("div", class_=re.compile("entry"))),
        ("div[class*='article']", soup.find_all("div", class_=re.compile("article"))),
    ]
    
    for name, containers in article_containers:
        if containers:
            print(f"\n   ✅ Found {len(containers)} <{name}> elements")
            if containers:
                first = containers[0]
                print(f"      Sample classes: {first.get('class', [])}")
    
    # 2. Find all links
    all_links = soup.find_all("a", href=True)
    print(f"\n   🔗 Total links: {len(all_links)}")
    
    # 3. Classify links
    article_links = []
    for a in all_links:
        href = a.get("href", "")
        if BASE_URL in href:
            path = href.replace(BASE_URL, "").strip("/")
            # Skip navigation/static pages
            if path and "/" in path and not any(x in path for x in [
                "kategori", "tag", "page", "author", "about", "contact", 
                "privacy", "wp-", "feed", ".jpg", ".png"
            ]):
                article_links.append(href)
    
    print(f"   📄 Potential article links: {len(article_links)}")
    
    # 4. Show sample article links
    print("\n   📝 Sample article URLs:")
    for i, link in enumerate(article_links[:10], 1):
        print(f"      {i}. {link}")
    
    # 5. Check for JavaScript/AJAX
    scripts = soup.find_all("script")
    ajax_count = sum(1 for s in scripts if "ajax" in str(s).lower())
    jquery_count = sum(1 for s in scripts if "jquery" in str(s).lower())
    
    print(f"\n   ⚙️  Scripts with AJAX: {ajax_count}")
    print(f"   ⚙️  Scripts with jQuery: {jquery_count}")
    
    # 6. Check pagination
    pagination = soup.find_all(class_=re.compile("pag"))
    print(f"\n   📑 Pagination elements: {len(pagination)}")
    if pagination:
        print(f"      Classes: {[p.get('class') for p in pagination[:3]]}")


def debug_category_page(slug: str = "kategori/hoax", page: int = 1):
    """Debug: Analisa struktur halaman kategori"""
    print("\n" + "="*70)
    print(f"📂 DEBUGGING CATEGORY PAGE: {slug} (page {page})")
    print("="*70)
    
    url = f"{BASE_URL}{slug}/page/{page}/"
    r = get_page(url)
    
    if not r:
        print(f"❌ Failed to fetch {url}")
        return
    
    soup = BeautifulSoup(r.content, "html.parser")
    
    # Save HTML
    slug_safe = slug.replace('/', '_')
    filename = f"category_{slug_safe}_page{page}.html"
    html_file = os.path.join(DEBUG_DIR, filename)
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(soup.prettify())
    print(f"✅ HTML saved: {html_file}")
    
    print(f"\n📊 PAGE ANALYSIS: {url}")
    
    # 1. All links
    all_links = soup.find_all("a", href=True)
    print(f"\n   🔗 Total links on page: {len(all_links)}")
    
    # 2. Filter article links
    article_links = set()
    for a in all_links:
        href = a.get("href", "")
        if not href.startswith("http"):
            href = urljoin(BASE_URL, href)
        
        clean = href.split("?")[0].split("#")[0].rstrip("/")
        
        # Must be from BASE_URL
        if BASE_URL not in clean:
            continue
        
        # Get path
        path = clean.replace(BASE_URL, "").strip("/")
        
        # Skip non-articles
        skip_patterns = [
            "/page/", "/kategori/", "/tag/", "/author/",
            "/about", "/contact", "/privacy", "/terms",
            ".jpg", ".png", ".gif", ".pdf", "/feed", "/wp-",
            "facebook.com", "twitter.com", "instagram.com"
        ]
        
        if any(pattern in clean.lower() for pattern in skip_patterns):
            continue
        
        # Article must have reasonable path length
        if len(path) > 5 and "/" in path:
            article_links.add(clean)
    
    print(f"   📄 Article links found: {len(article_links)}")
    
    # 3. Show samples
    print("\n   📝 Sample article URLs:")
    for i, link in enumerate(list(article_links)[:15], 1):
        print(f"      {i}. {link}")
    
    # 4. Analyze link structure
    if article_links:
        sample_link = list(article_links)[0]
        path = sample_link.replace(BASE_URL, "")
        year_match = re.search(r'/202[0-9]/', path)
        month_match = re.search(r'/\d{2}/', path)
        
        print(f"\n   🔍 Sample link structure:")
        print(f"      URL: {sample_link}")
        print(f"      Path: {path}")
        print(f"      Has year: {bool(year_match)}")
        print(f"      Has month: {bool(month_match)}")
    
    # 5. Check for common selectors
    print("\n   🎯 Testing common CSS selectors:")
    selectors_to_test = [
        "article h2 a",
        "article h3 a",
        ".entry-title a",
        ".post-title a",
        "h2.entry-title a",
        "h2.post-title a",
        ".td-module-title a",
        "article.post a[href*='turnbackhoax']",
        "div.post-content a",
        ".mh-loop-title a",
    ]
    
    for selector in selectors_to_test:
        elements = soup.select(selector)
        if elements:
            print(f"      ✅ '{selector}': {len(elements)} elements")
            # Show first match
            first = elements[0]
            href = first.get("href", "")
            text = first.get_text(strip=True)[:50]
            print(f"         Sample: [{text}] -> {href}")
        else:
            print(f"      ❌ '{selector}': 0 elements")
    
    # 6. Check main content container
    print("\n   📦 Main content containers:")
    containers = [
        ("div#content", soup.select("div#content")),
        ("div#main", soup.select("div#main")),
        ("div.content", soup.select("div.content")),
        ("main", soup.select("main")),
        ("div#primary", soup.select("div#primary")),
    ]
    
    for name, elements in containers:
        if elements:
            print(f"      ✅ {name}: {len(elements)} found")
            # Count links inside
            links_inside = elements[0].find_all("a", href=True)
            print(f"         Links inside: {len(links_inside)}")


def debug_article_page(article_url: str = None):
    """Debug: Analisa struktur halaman artikel"""
    print("\n" + "="*70)
    print("📰 DEBUGGING ARTICLE PAGE")
    print("="*70)
    
    # If no URL provided, try to get one from homepage
    if not article_url:
        print("   Finding sample article from homepage...")
        r = get_page(BASE_URL)
        if r:
            soup = BeautifulSoup(r.content, "html.parser")
            links = soup.find_all("a", href=True)
            for a in links:
                href = a.get("href", "")
                if BASE_URL in href and "kategori" not in href and "tag" not in href:
                    article_url = href.split("?")[0].rstrip("/")
                    break
    
    if not article_url:
        print("❌ No article URL found")
        return
    
    print(f"   Article URL: {article_url}")
    
    r = get_page(article_url)
    if not r:
        print(f"❌ Failed to fetch article")
        return
    
    soup = BeautifulSoup(r.content, "html.parser")
    
    # Save HTML
    article_slug = article_url.split("/")[-1] or "article"
    html_file = os.path.join(DEBUG_DIR, f"article_{article_slug}.html")
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(soup.prettify())
    print(f"✅ HTML saved: {html_file}")
    
    print(f"\n📊 ARTICLE ANALYSIS:")
    
    # 1. Title
    title_selectors = [
        "h1.entry-title",
        "h1.post-title",
        "h1",
        "article h1",
        ".entry-header h1",
    ]
    
    print("\n   📌 TITLE:")
    for selector in title_selectors:
        title_el = soup.select_one(selector)
        if title_el:
            title = title_el.get_text(strip=True)
            print(f"      ✅ {selector}: '{title[:80]}...'")
            break
    else:
        print("      ❌ No title found")
    
    # 2. Date
    print("\n   📅 DATE:")
    date_selectors = [
        'meta[property="article:published_time"]',
        'meta[name="date"]',
        'time[datetime]',
        'time.published',
        '.entry-date',
        '.post-date',
    ]
    
    for selector in date_selectors:
        if selector.startswith("meta"):
            el = soup.select_one(selector)
            if el and el.get("content"):
                print(f"      ✅ {selector}: {el['content']}")
                break
        else:
            el = soup.select_one(selector)
            if el:
                date_text = el.get("datetime") or el.get_text(strip=True)
                print(f"      ✅ {selector}: {date_text}")
                break
    else:
        print("      ❌ No date found")
    
    # 3. Categories
    print("\n   🏷️  CATEGORIES:")
    cat_selectors = [
        "span.cat-links a",
        ".entry-meta a[rel='category tag']",
        "a[rel='category']",
        ".post-categories a",
    ]
    
    cats_found = False
    for selector in cat_selectors:
        cats = soup.select(selector)
        if cats:
            cat_texts = [c.get_text(strip=True) for c in cats]
            print(f"      ✅ {selector}: {cat_texts}")
            cats_found = True
            break
    
    if not cats_found:
        print("      ❌ No categories found")
    
    # 4. Content
    print("\n   📝 CONTENT:")
    content_selectors = [
        "article .entry-content",
        ".entry-content",
        ".post-content",
        "article",
        "main article",
    ]
    
    for selector in content_selectors:
        content_el = soup.select_one(selector)
        if content_el:
            paragraphs = content_el.find_all("p")
            total_text = " ".join([p.get_text(strip=True) for p in paragraphs])
            print(f"      ✅ {selector}: {len(paragraphs)} paragraphs, {len(total_text)} chars")
            if total_text:
                print(f"         Preview: {total_text[:150]}...")
            break
    else:
        print("      ❌ No content found")
    
    # 5. Images
    print("\n   🖼️  IMAGES:")
    img_selectors = [
        ".entry-content img",
        "article img",
        ".post-content img",
        ".wp-post-image",
    ]
    
    for selector in img_selectors:
        imgs = soup.select(selector)
        if imgs:
            print(f"      ✅ {selector}: {len(imgs)} images")
            for i, img in enumerate(imgs[:3], 1):
                src = img.get("src") or img.get("data-src")
                print(f"         {i}. {src}")
            break
    else:
        print("      ❌ No images found")


def debug_sitemap():
    """Debug: Cek sitemap availability"""
    print("\n" + "="*70)
    print("🗺️  DEBUGGING SITEMAP")
    print("="*70)
    
    sitemap_urls = [
        f"{BASE_URL}sitemap.xml",
        f"{BASE_URL}sitemap_index.xml",
        f"{BASE_URL}post-sitemap.xml",
        f"{BASE_URL}wp-sitemap.xml",
        f"{BASE_URL}wp-sitemap-posts-post-1.xml",
        f"{BASE_URL}sitemap-posts.xml",
        f"{BASE_URL}robots.txt",
    ]
    
    for sitemap_url in sitemap_urls:
        r = get_page(sitemap_url)
        
        if r and r.status_code == 200:
            print(f"\n   ✅ {sitemap_url}")
            
            # If robots.txt, look for sitemap
            if "robots.txt" in sitemap_url:
                lines = r.text.split("\n")
                for line in lines:
                    if "sitemap" in line.lower():
                        print(f"      Found: {line.strip()}")
            else:
                # Parse XML
                try:
                    soup = BeautifulSoup(r.content, "xml")
                    locs = soup.find_all("loc")
                    print(f"      URLs found: {len(locs)}")
                    
                    # Save sitemap
                    sitemap_name = sitemap_url.split("/")[-1]
                    sitemap_file = os.path.join(DEBUG_DIR, f"sitemap_{sitemap_name}")
                    with open(sitemap_file, "w", encoding="utf-8") as f:
                        f.write(soup.prettify())
                    print(f"      Saved: {sitemap_file}")
                    
                    # Show samples
                    if locs:
                        print("      Sample URLs:")
                        for loc in locs[:5]:
                            print(f"         - {loc.get_text(strip=True)}")
                    
                    # Check if it's sitemap index
                    sitemaps = soup.find_all("sitemap")
                    if sitemaps:
                        print(f"      This is a sitemap index with {len(sitemaps)} sub-sitemaps")
                        for sm in sitemaps[:3]:
                            sm_loc = sm.find("loc")
                            if sm_loc:
                                print(f"         - {sm_loc.get_text(strip=True)}")
                
                except Exception as e:
                    print(f"      ⚠️  XML parse error: {e}")
        else:
            print(f"   ❌ {sitemap_url} (not found)")


def debug_search():
    """Debug: Test search functionality"""
    print("\n" + "="*70)
    print("🔍 DEBUGGING SEARCH")
    print("="*70)
    
    test_query = "hoax prabowo"
    search_url = f"{BASE_URL}?s={quote_plus(test_query)}"
    
    print(f"   Search URL: {search_url}")
    
    r = get_page(search_url)
    if not r:
        print("❌ Search failed")
        return
    
    soup = BeautifulSoup(r.content, "html.parser")
    
    # Save HTML
    query_safe = test_query.replace(' ', '_')
    html_file = os.path.join(DEBUG_DIR, f"search_{query_safe}.html")
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(soup.prettify())
    print(f"✅ HTML saved: {html_file}")
    
    # Count results
    all_links = soup.find_all("a", href=True)
    article_links = []
    
    for a in all_links:
        href = a.get("href", "")
        if BASE_URL in href:
            path = href.replace(BASE_URL, "").strip("/")
            if path and "/" in path and not any(x in path for x in [
                "kategori", "tag", "page", "author", "wp-"
            ]):
                article_links.append(href)
    
    print(f"\n   📄 Search results: {len(article_links)} articles found")
    
    if article_links:
        print("\n   Sample results:")
        for i, link in enumerate(article_links[:10], 1):
            print(f"      {i}. {link}")


def generate_summary_report():
    """Generate summary report dari semua debug files"""
    print("\n" + "="*70)
    print("📋 GENERATING SUMMARY REPORT")
    print("="*70)
    
    report_file = os.path.join(DEBUG_DIR, "DEBUG_REPORT.txt")
    
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("="*70 + "\n")
        f.write("TURNBACKHOAX SCRAPER - DEBUG REPORT\n")
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"Generated: {timestamp}\n")
        f.write("="*70 + "\n\n")
        
        f.write("FILES GENERATED:\n")
        for filename in os.listdir(DEBUG_DIR):
            if filename.endswith(".html") or filename.endswith(".xml"):
                filepath = os.path.join(DEBUG_DIR, filename)
                size = os.path.getsize(filepath)
                size_formatted = f"{size:,}"
                f.write(f"  - {filename} ({size_formatted} bytes)\n")
        
        f.write("\n" + "="*70 + "\n")
        f.write("NEXT STEPS:\n")
        f.write("="*70 + "\n")
        f.write("1. Open HTML files in browser to inspect structure\n")
        f.write("2. Look for article link patterns\n")
        f.write("3. Identify correct CSS selectors\n")
        f.write("4. Check if JavaScript rendering is needed\n")
        f.write("5. Update scraper with correct selectors\n")
    
    print(f"✅ Report saved: {report_file}")
    print(f"\n📁 All debug files in: {DEBUG_DIR}")


# ============== MAIN DEBUG RUNNER ==============
def run_full_debug():
    """Jalankan semua debug tests"""
    print("\n" + "="*70)
    print("🔬 TURNBACKHOAX SCRAPER - FULL DEBUG MODE")
    print("="*70)
    print(f"Output directory: {DEBUG_DIR}\n")
    
    # Test 1: Homepage
    print("\n[1/6] Testing homepage...")
    debug_homepage()
    time.sleep(2)
    
    # Test 2: Category page 1
    print("\n[2/6] Testing category page 1...")
    debug_category_page("kategori/hoax", page=1)
    time.sleep(2)
    
    # Test 3: Category page 2
    print("\n[3/6] Testing category page 2...")
    debug_category_page("kategori/hoax", page=2)
    time.sleep(2)
    
    # Test 4: Article page
    print("\n[4/6] Testing article page...")
    debug_article_page()
    time.sleep(2)
    
    # Test 5: Sitemap
    print("\n[5/6] Testing sitemap...")
    debug_sitemap()
    time.sleep(2)
    
    # Test 6: Search
    print("\n[6/6] Testing search...")
    debug_search()
    
    # Generate summary
    print("\n" + "="*70)
    generate_summary_report()
    
    print("\n" + "="*70)
    print("✅ DEBUG COMPLETE!")
    print("="*70)
    print(f"\n📁 Check files in: {DEBUG_DIR}")
    report_path = os.path.join(DEBUG_DIR, "DEBUG_REPORT.txt")
    print(f"📋 Read: {report_path}")
    print("\nNext: Inspect HTML files in browser to find correct selectors")
    print("="*70 + "\n")


# ============== ENTRY POINT ==============
if __name__ == "__main__":
    run_full_debug()
