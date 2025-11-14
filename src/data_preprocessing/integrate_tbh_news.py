# integrate_news_tbh_master.py (FIXED)
import os, re, hashlib, json
import pandas as pd
import numpy as np
from urllib.parse import urlparse
from datasketch import MinHash, MinHashLSH

# ============== CONFIG ==============
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

DATA_RAW = "data/raw"
DATA_OUT = "data/processed"
os.makedirs(DATA_OUT, exist_ok=True)

NEWS_CSV = os.path.join(DATA_RAW, "news", "AllMetadata_Cleaned_v3.csv")
TBH_CSV  = os.path.join(DATA_RAW, "turnbackhoax", "metadata", "tbh_BERSIH_POLITIK_SAJA.csv")
OUT_FULL = os.path.join(DATA_OUT, "dataset_integrated_cleanv1.csv")
OUT_MANIFEST = os.path.join(DATA_OUT, "dataset_manifestv1.json")

LSH_THRESHOLD = 0.95
LSH_NUM_PERM  = 128
SHINGLE_K     = 5

# ============== Helpers ==============
PORTAL_PATTERNS = [
    r"\b(JAKARTA|SURABAYA|BANDUNG|LOMBOK|YOGYAKARTA)\s*,\s*KOMPAS\.com\b",
    r"\bKOMPAS\.com\b", r"\bCNN\s*Indonesia\b", r"\bkompas\.com\b", r"\bcnnindonesia\.com\b",
    r"\bdetik\.com\b", r"\btribunnews\.com\b", r"\bTEMPO\.co\b", r"\bKumparan\.com\b",
    r"[–—-]\s", r"http[s]?://\S+", r"www\.\S+",
    r"\bOleh\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b",
    r"\bReporter\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b",
    r"\bEditor\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b"
]
TBH_PATTERNS = [
    r"\[(SALAH|BENAR|PENIPUAN|DISINFORMASI|MISINFORMASI|HOAKS?)\]\s*",
    r"\b(Tim\s+Pemeriksa\s+Fakta|TurnBackHoax|Mafindo|Cek\s+Fakta)\b",
    r"\b(cek\s*fakta|pemeriksaan\s*fakta|verifikasi|menelusuri)\b\s*[:\-]?",
    r"\b(kesimpulan|disimpulkan|merupakan\s+konten)\b\s*[:\-]?",
    r"\b(misleading content|fabricated content|false context|konten\s+(menesesatkan|dimanipulasi))\b",
    r"\b(SUMBER|NARASI|PENJELASAN|REFERENSI|HASIL)\b\s*[:\]]?",
    r"={3,}", r"\([^\)]{10,}\)",
    r"berdasarkan\s+penelusuran\s+TurnBackHoax",
    r"hasil\s+penelusuran\s+Tim\s+Pemeriksa\s+Fakta",
    r"dilansir\s+dari\s+TurnBackHoax"
]

def norm_domain(u):
    try: 
        return urlparse(u).netloc.lower()
    except: 
        return ""

def normalize_timezone(dt):
    if pd.isna(dt): 
        return pd.NaT
    if hasattr(dt, 'tz') and dt.tz is not None: 
        return dt.tz_localize(None)
    return dt

def clean_news_text(s):
    x = s if isinstance(s, str) else ""
    for p in PORTAL_PATTERNS:
        x = re.sub(p, " ", x, flags=re.IGNORECASE)
    return re.sub(r"\s+"," ", x).strip()

def clean_tbh_text(s):
    x = s if isinstance(s, str) else ""
    for p in TBH_PATTERNS:
        x = re.sub(p, " ", x, flags=re.IGNORECASE)
    return re.sub(r"\s+"," ", x).strip()

def canon(s):
    if not isinstance(s, str): 
        return ""
    s = s.lower()
    s = re.sub(r"http[s]?://\S+", " ", s)
    s = re.sub(r"\W+", " ", s)
    return re.sub(r"\s+"," ", s).strip()

def shingles(s, k=5):
    if not isinstance(s, str) or len(s.strip()) == 0:
        return []
    toks = s.split()
    if len(toks) < k: 
        return [' '.join(toks)]
    return [' '.join(toks[i:i+k]) for i in range(len(toks)-k+1)]

def to_target_news(df):
    """Process NEWS dataset dengan struktur kolom yang sesuai"""
    out = pd.DataFrame()
    
    # ID & URL
    out["id"] = df["id"].astype(str)
    out["url"] = df["url"].fillna("").astype(str)
    out["domain"] = df["domain"].astype(str).str.lower()
    
    # Date handling untuk news
    out["date"] = pd.to_datetime(df["date_utc"], errors="coerce", utc=True)
    out["date"] = out["date"].apply(normalize_timezone)
    
    # Title & Text
    out["title"] = df["title_cleaned"].fillna("").astype(str)
    out["text"] = df["text_cleaned"].fillna("").astype(str)  # News menggunakan text_preview
    
    # Metadata
    out["source_type"] = "news"
    out["dataset_origin"] = "news"
    out["label"] = 1  # News adalah valid news
    
    print(f"[to_target:news] rows={len(out)} null_date={(out['date'].isna().mean()):.3f}")
    return out

def to_target_tbh(df):
    """Process TBH dataset dengan struktur kolom yang sesuai"""
    out = pd.DataFrame()
    
    # ID & URL
    out["id"] = df["id"].astype(str)
    out["url"] = df["post_url"].fillna("").astype(str)  # TBH menggunakan post_url
    
    # Domain dari source
    out["domain"] = df["source"].fillna("").astype(str).str.lower()
    
    # Date handling untuk TBH - coba post_date dulu, lalu date
    if "post_date" in df.columns:
        out["date"] = pd.to_datetime(df["post_date"], errors="coerce", dayfirst=True, utc=True)
    else:
        out["date"] = pd.to_datetime(df["date"], errors="coerce", dayfirst=True, utc=True)
    out["date"] = out["date"].apply(normalize_timezone)
    
    # Title & Text
    out["title"] = df["title"].fillna("").astype(str)
    # TBH: prioritaskan text, lalu full_content
    if "text" in df.columns:
        out["text"] = df["text"].fillna("").astype(str)
    else:
        out["text"] = df["full_content"].fillna("").astype(str)
    
    # Metadata
    out["source_type"] = "tbh"
    out["dataset_origin"] = "turnbackhoax"
    
    # Label handling untuk TBH
    if "label" in df.columns:
        if df["label"].dtype == object:
            label_mapping = {
                "hoax": 0, "HOAX": 0, "false": 0, "FALSE": 0,
                "valid": 1, "VALID": 1, "true": 1, "TRUE": 1
            }
            out["label"] = df["label"].map(label_mapping)
        else:
            out["label"] = df["label"]
    else:
        out["label"] = 0  # Default untuk TBH
    
    print(f"[to_target:tbh] rows={len(out)} null_date={(out['date'].isna().mean()):.3f}")
    return out

# ============== Load sources ==============
print("Loading news...")
news_raw = pd.read_csv(NEWS_CSV)
print(f"News columns: {list(news_raw.columns)}")
print(f"News shape: {news_raw.shape}")

news_t = to_target_news(news_raw)
news_t["title_clean"] = news_t["title"].map(clean_news_text)
news_t["text_clean"] = news_t["text"].map(clean_news_text)
news_t = news_t[news_t["date"].notna()]
print(f"News after date filter: {len(news_t)}")

print("\nLoading TBH...")
tbh_raw = pd.read_csv(TBH_CSV)
print(f"TBH columns: {list(tbh_raw.columns)}")
print(f"TBH shape: {tbh_raw.shape}")

tbh_t = to_target_tbh(tbh_raw)
tbh_t["title_clean"] = tbh_t["title"].map(clean_tbh_text)
tbh_t["text_clean"] = tbh_t["text"].map(clean_tbh_text)
tbh_t = tbh_t[tbh_t["date"].notna()]
print(f"TBH after date filter: {len(tbh_t)}")

# Handle label conversion untuk TBH
tbh_t["label"] = tbh_t["label"].fillna(0).astype(int)

# ============== Merge & basic filter ==============
print("\nMerging datasets...")
df = pd.concat([news_t, tbh_t], ignore_index=True)
print(f"Combined dataset shape: {df.shape}")

# Filter data yang memiliki konten memadai
before_filter = len(df)
df = df[
    (df["text_clean"].str.len() > 50) | 
    (df["title_clean"].str.len() > 20)
].reset_index(drop=True)
after_filter = len(df)
print(f"Basic content filter: {before_filter} -> {after_filter} (removed {before_filter - after_filter})")

# Final label assignment
df["label"] = df["label"].astype(int)
df["label_str"] = df["label"].map({0: "hoax", 1: "valid"})

# ============== Dedup layer 1: exact ==============
print("\nDedup Layer 1 (Exact duplicates)...")
# Gunakan kombinasi title_clean + text_clean untuk key yang lebih akurat
df["__key__"] = (df["title_clean"] + " " + df["text_clean"]).map(canon)
df["__md5__"] = df["__key__"].map(lambda x: hashlib.md5(x.encode()).hexdigest() if x else "")

before_exact = len(df)
df = df.drop_duplicates(subset="__md5__").reset_index(drop=True)
after_exact = len(df)
print(f"Exact dedup removed: {before_exact - after_exact}")

# ============== Dedup layer 2: LSH near-duplicate ==============
print("\nDedup Layer 2 (LSH near-duplicates)...")
lsh = MinHashLSH(threshold=LSH_THRESHOLD, num_perm=LSH_NUM_PERM)
keep_indices = []
duplicate_count = 0

print("Building LSH index...")
for idx, row in df.iterrows():
    text_key = row["__key__"]
    
    if not isinstance(text_key, str) or len(text_key.strip()) == 0:
        keep_indices.append(idx)
        continue
        
    m = MinHash(num_perm=LSH_NUM_PERM)
    shingle_set = shingles(text_key, k=SHINGLE_K)
    
    if not shingle_set:
        keep_indices.append(idx)
        continue
        
    for sh in shingle_set:
        m.update(sh.encode("utf-8"))
    
    # Query for similar documents
    similar_docs = lsh.query(m)
    
    if not similar_docs:
        # No similar documents found, add to index and keep
        lsh.insert(str(idx), m)
        keep_indices.append(idx)
    else:
        # Found similar documents, discard this one
        duplicate_count += 1
        if duplicate_count % 100 == 0:
            print(f"Found {duplicate_count} duplicates so far...")

before_lsh = len(df)
df = df.loc[keep_indices].reset_index(drop=True)
after_lsh = len(df)

print(f"LSH dedup removed: {before_lsh - after_lsh}")
print(f"Total duplicates found: {duplicate_count}")

# Clean up temporary columns
df = df.drop(columns=["__key__", "__md5__"])

# ============== fp_new for grouping ==============
def make_fp(row):
    dom = (row.get("domain") or "").lower()
    t   = canon(row.get("title_clean", ""))[:128]
    day = str(row["date"].date()) if pd.notna(row["date"]) else "na"
    base = f"{dom}|{t}|{day}"
    return hashlib.md5(base.encode()).hexdigest()[:16]

print("\nCreating fingerprint (fp_new)...")
df["fp_new"] = df.apply(make_fp, axis=1)

# ============== Final DataFrame Preparation ==============
# Gunakan cleaned text untuk final output
df["title"] = df["title_clean"]
df["text"] = df["text_clean"]
df = df.drop(columns=["title_clean", "text_clean"])

# ============== Validate & save ==============
print("\n" + "="*50)
print("FINAL VALIDATION")
print("="*50)

# Validasi label
assert set(df["label"].unique()).issubset({0,1}), f"Invalid labels found: {df['label'].unique()}"

# Validasi null values
nulls = df.isna().mean().to_dict()
print("\nNull ratios:")
for col, ratio in nulls.items():
    if ratio > 0:
        print(f"  {col}: {ratio:.4f}")

# Validasi distribusi
label_dist = df['label'].value_counts().sort_index()
source_dist = df['source_type'].value_counts()

print(f"\n--- Label Distribution ---")
print(label_dist)
print(f"\n--- Source Distribution ---")
print(source_dist)
print("------------------------------")

# Validasi balance
total_samples = len(df)
min_samples = label_dist.min()
if min_samples < 10:
    print(f"!!! WARNING: Minority class has only {min_samples} samples !!!")
    print("!!! This may cause issues with stratified splitting !!!")
else:
    balance_ratio = min_samples / total_samples
    print(f"Balance ratio: {balance_ratio:.4f}")

# Persiapan kolom final
final_cols = ["id", "url", "domain", "date", "title", "text", "source_type", "dataset_origin", "fp_new", "label", "label_str"]

# Pastikan semua kolom ada
for col in final_cols:
    if col not in df.columns:
        print(f"Warning: Column '{col}' not found, creating empty column")
        df[col] = pd.NA

df_final = df[final_cols].copy()

# Simpan hasil
print(f"\nSaving results...")
df_final.to_csv(OUT_FULL, index=False)

# Buat manifest
manifest = {
    "random_seed": RANDOM_SEED,
    "lsh_threshold": LSH_THRESHOLD,
    "lsh_num_perm": LSH_NUM_PERM,
    "shingle_k": SHINGLE_K,
    "news_csv": NEWS_CSV,
    "tbh_csv": TBH_CSV,
    "total_rows": int(len(df_final)),
    "label_distribution": label_dist.to_dict(),
    "source_distribution": source_dist.to_dict(),
    "date_range": {
        "min": str(df_final["date"].min()),
        "max": str(df_final["date"].max())
    } if df_final["date"].notna().any() else {"min": None, "max": None},
    "processing_steps": {
        "initial_news": len(news_raw),
        "initial_tbh": len(tbh_raw),
        "after_date_filter_news": len(news_t),
        "after_date_filter_tbh": len(tbh_t),
        "after_content_filter": after_filter,
        "after_exact_dedup": after_exact,
        "after_lsh_dedup": after_lsh,
        "final": len(df_final)
    }
}

with open(OUT_MANIFEST, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)

print(f"✓ Saved master dataset: {OUT_FULL} ({len(df_final)} rows)")
print(f"✓ Saved manifest: {OUT_MANIFEST}")

# Preview
print("\n" + "="*50)
print("FINAL PREVIEW")
print("="*50)
print(f"Final shape: {df_final.shape}")
print(f"Memory usage: {df_final.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

if len(df_final) > 0:
    sample = df_final.sample(min(3, len(df_final)), random_state=RANDOM_SEED)
    print(f"\nSample records:")
    for i, row in sample.iterrows():
        print(f"\n--- Sample {i+1} ---")
        print(f"Source: {row['source_type']} | Label: {row['label_str']} ({row['label']})")
        print(f"Domain: {row['domain']}")
        print(f"Date: {row['date']}")
        print(f"Title: {row['title'][:100]}{'...' if len(row['title']) > 100 else ''}")
        print(f"Text: {row['text'][:150]}{'...' if len(row['text']) > 150 else ''}")
        print(f"Fingerprint: {row['fp_new']}")

print("\n" + "="*50)
print("PROCESS COMPLETED SUCCESSFULLY")
print("="*50)