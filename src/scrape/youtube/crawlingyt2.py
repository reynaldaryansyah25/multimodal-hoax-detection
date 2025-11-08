import os
import time
import json
import yt_dlp
import requests
from datetime import datetime, timezone


def ensure_dirs(*dirs):
    for d in dirs:
        os.makedirs(d, exist_ok=True)


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def classify_channel_type(record):
    """Auto-classify channel_type untuk data lama"""
    # Safety check untuk None values
    channel = (record.get('channel') or '').lower()
    keyword = (record.get('keyword') or '').lower()
    
    # Dari channel
    if any(w in channel for w in ['kompas', 'metro', 'cnn', 'tvone', 'detik', 'bbc']):
        return 'news'
    if any(w in channel for w in ['narasi', 'mata najwa', 'deeplab']):
        return 'analysis'
    if any(w in channel for w in ['turnbackhoax', 'cekfakta', 'hoax']):
        return 'factcheck'
    
    # Dari keyword
    if any(w in keyword for w in ['hoax', 'misinformasi', 'cek fakta', 'debunking']):
        return 'factcheck'
    if any(w in keyword for w in ['viral', 'heboh', 'trending', 'kontroversi']):
        return 'viral'
    if any(w in keyword for w in ['analisis', 'opini', 'diskusi', 'perdebatan']):
        return 'analysis'
    if any(w in keyword for w in ['prabowo', 'gibran']):
        return 'prabowo'
    
    return 'default'


def load_existing_metadata(path="./data/raw/youtube/metadata.json"):
    """Load existing metadata and normalize schema"""
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                records = json.load(f)
            
            print(f"📂 Found existing metadata file with {len(records)} records")
            
            # Normalize: add channel_type and keyword_tier ke data lama
            valid_records = []
            for i, record in enumerate(records):
                try:
                    # Skip record yang corrupt/invalid
                    if not isinstance(record, dict):
                        print(f"  ⚠️ Skipping invalid record #{i}: not a dict")
                        continue
                    
                    if 'video_id' not in record:
                        print(f"  ⚠️ Skipping record #{i}: no video_id")
                        continue
                    
                    # Add missing fields
                    if 'channel_type' not in record:
                        record['channel_type'] = classify_channel_type(record)
                    if 'keyword_tier' not in record:
                        record['keyword_tier'] = 'legacy'
                    
                    valid_records.append(record)
                    
                except Exception as e:
                    print(f"  ⚠️ Error processing record #{i}: {e}")
                    continue
            
            video_ids = {r['video_id'] for r in valid_records if 'video_id' in r}
            print(f"✓ Loaded {len(valid_records)} valid records")
            print(f"✓ Unique video_ids: {len(video_ids)}")
            
            return valid_records, video_ids
            
        except json.JSONDecodeError as e:
            print(f"❌ Error: metadata.json is corrupted - {e}")
            print("Creating backup and starting fresh...")
            
            # Backup corrupted file
            backup_path = path.replace('.json', f'_backup_{int(time.time())}.json')
            try:
                import shutil
                shutil.copy2(path, backup_path)
                print(f"✓ Backed up to: {backup_path}")
            except:
                pass
            
            return [], set()
            
        except Exception as e:
            print(f"❌ Error loading metadata: {e}")
            return [], set()
    
    print("📂 No existing metadata found, starting fresh")
    return [], set()


def get_next_sample_id(existing_records):
    """Generate next sample_id berdasarkan existing records"""
    if not existing_records:
        return "YT_00001"
    
    # Cari sample_id tertinggi
    max_num = 0
    for rec in existing_records:
        sample_id = rec.get('sample_id', '')
        if sample_id.startswith('YT_'):
            try:
                num = int(sample_id.split('_')[1])
                max_num = max(max_num, num)
            except:
                continue
    
    next_id = f"YT_{max_num + 1:05d}"
    print(f"🆔 Next sample_id will be: {next_id}")
    return next_id
  

def get_timestamp():
    return datetime.now(timezone.utc).isoformat()


# ============== STRATIFIED KEYWORDS ==============
NEWS_KEYWORDS = [
    "Prabowo presiden Indonesia 2024",
    "Kabinet merah putih Prabowo",
    "Menteri kabinet Prabowo",
    "Gibran Rakabuming Raka",
    "Berita politik hari ini",
    "Pemerintah Indonesia berita",
    "Kebijakan pemerintah terbaru",
    "Pemilu Indonesia 2024",
    "DPR RI anggota baru",
    "KPK berita terkini",
]


ANALYSIS_KEYWORDS = [
    "analisis politik Indonesia",
    "opini tentang pemerintahan",
    "diskusi politik terkini",
    "perdebatan politik",
    "kritik pemerintah",
    "pandangan ahli politik",
]


FACTCHECK_KEYWORDS = [
    "hoax politik 2024",
    "misinformasi politik Indonesia",
    "cek fakta politik",
    "debunking politik",
    "klaim salah politik",
    "klarifikasi pemerintah",
]


VIRAL_KEYWORDS = [
    "viral politik Indonesia",
    "trending politik",
    "heboh politik",
    "kontroversi politik",
    "skandal politik",
    "isu yang beredar politik",
]


PRABOWO_KEYWORDS = [
    "program makan siang gratis",
    "visi misi Prabowo presiden",
    "IKN ibu kota nusantara",
    "Prabowo Gibran 2024",
]


# Tambahan dari keyword original
ADDITIONAL_KEYWORDS = [
    "Menteri pertahanan Prabowo",
    "Wakil presiden Gibran",
    "Politik Indonesia terkini",
    "Peraturan pemerintah Indonesia",
    "Pilkada Indonesia 2024",
    "Partai Politik Indonesia",
    "Koalisi pemerintah Indonesia",
    "Pemilu legislatif 2024",
    "Hukum Indonesia terbaru",
    "Kejaksaan agung RI",
    "Mahkamah konstitusi",
    "Mahkamah agung",
    "Pengadilan negeri",
    "Undang-undang RI terbaru",
    "KUHP revisi terbaru",
    "UU ITE Indonesia",
    "Hak asasi manusia Indonesia",
    "Komnas HAM laporan",
    "Pelanggaran HAM",
    "Keamanan nasional Indonesia",
    "Polri berita",
    "TNI berita terbaru",
    "Pertahanan Indonesia",
    "Ekonomi Indonesia 2024",
    "Kebijakan ekonomi Prabowo",
    "Pajak Indonesia terbaru",
    "Investasi Indonesia",
    "Bursa saham Indonesia",
    "Rupiah terhadap dollar",
    "Inflasi Indonesia terkini",
    "Program sosial pemerintah",
    "Bantuan sosial Indonesia",
    "Pendidikan Indonesia 2024",
    "Kesehatan masyarakat RI",
    "Kementerian sosial",
    "Pemerintah daerah Indonesia",
    "Gubernur berita",
    "Bupati berita",
    "Walikota berita",
    "Pemerintah lokal terbaru",
    "Infrastruktur Indonesia",
    "Proyek strategis nasional",
    "Jalan tol terbaru",
    "Bandara Indonesia",
    "Pelabuhan Indonesia",
    "Hubungan luar negeri Indonesia",
    "Diplomasi Indonesia",
    "Keamanan regional Asia",
    "ASEAN berita",
    "Reformasi pemerintah",
    "Deregulasi bisnis",
    "Transformasi digital RI",
    "Otonomi daerah",
    "Breaking news Indonesia",
    "Headline nasional hari ini",
    "Indonesia news update",
    "Berita utama nasional",
    "Top news Indonesia",
    "Kenaikan ibu kota",
    "Ibu kota nusantara",
    "Revolusi mental pemerintah",
    "Program prioritas nasional",
    "Pengurangan kemiskinan",
    "Pengangguran Indonesia",
    "Pemerintahan Prabowo",
    "Era Prabowo 2024",
    "Masa kepemimpinan Prabowo",
    "Langkah awal kabinet Prabowo",
]


# Gabung semua keyword
ALL_KEYWORDS = (
    NEWS_KEYWORDS +
    ANALYSIS_KEYWORDS +
    FACTCHECK_KEYWORDS +
    VIRAL_KEYWORDS +
    PRABOWO_KEYWORDS +
    ADDITIONAL_KEYWORDS
)


HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}


def is_valid_duration(duration, min_dur=120, max_dur=600):  
    if duration is None:
        return False
    return min_dur <= duration <= max_dur


def is_valid_date(upload_date_str, date_start, date_end):
    try:
        if not upload_date_str or len(upload_date_str) < 8:
            return True
        
        video_date = datetime.strptime(upload_date_str[:8], "%Y%m%d")
        start_date = datetime.strptime(date_start, "%Y-%m-%d")
        end_date = datetime.strptime(date_end, "%Y-%m-%d")
        
        return start_date <= video_date <= end_date
    except:
        return True


def determine_keyword_tier(keyword):
    """Tentukan tier dari keyword"""
    if keyword in NEWS_KEYWORDS:
        return 'news'
    elif keyword in ANALYSIS_KEYWORDS:
        return 'analysis'
    elif keyword in FACTCHECK_KEYWORDS:
        return 'factcheck'
    elif keyword in VIRAL_KEYWORDS:
        return 'viral'
    elif keyword in PRABOWO_KEYWORDS:
        return 'prabowo'
    else:
        return 'additional'


def search_youtube(keyword, max_results=50):
    print(f"🔍 Searching: '{keyword}'")
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': 'in_playlist',
        'playlistend': max_results,
        'default_search': 'ytsearch',
        'socket_timeout': 30,
        'retries': 5,
    }
    
    videos = []
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_query = f"ytsearch{max_results}:{keyword}"
            info = ydl.extract_info(search_query, download=False)
            
            for entry in info.get('entries', []):
                if not entry:
                    continue
                
                video_id = entry.get('id')
                title = entry.get('title', '')
                duration = entry.get('duration')
                url = f"https://www.youtube.com/watch?v={video_id}"
                
                if is_valid_duration(duration):
                    videos.append({
                        'url': url,
                        'video_id': video_id,
                        'title': title,
                        'duration': duration,
                    })
            
    except Exception as e:
        print(f"❌ Search error: {e}")
    
    print(f"✓ Found: {len(videos)} valid videos (2-15 min)\n")
    return videos


def get_video_info(url):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'socket_timeout': 30,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)
    except:
        return None


def download_thumbnail(thumb_url, sample_id, out_dir="./data/raw/youtube"):
    try:
        if not thumb_url:
            return ""
        
        ensure_dirs(f"{out_dir}/thumbnails")
        
        ext = thumb_url.split('?')[0].split('.')[-1][:4] or 'jpg'
        thumb_path = f"{out_dir}/thumbnails/{sample_id}.{ext}"
        
        r = requests.get(thumb_url, headers=HEADERS, timeout=15)
        
        with open(thumb_path, 'wb') as f:
            f.write(r.content)
        
        return thumb_path
        
    except Exception as e:
        return ""


def download_wav(url, sample_id, out_dir="./data/raw/youtube"):
    ensure_dirs(f"{out_dir}/audio")
    
    audio_out = f"{out_dir}/audio/{sample_id}.wav"
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'retries': 10,
        'fragment_retries': 20,
        'http_chunk_size': 10 * 1024 * 1024,
        'socket_timeout': 30,
        'format': 'bestaudio[ext=webm]/bestaudio/best',
        'outtmpl': audio_out.replace('.wav', '.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        if os.path.exists(audio_out):
            return True, audio_out
        else:
            return False, ""
            
    except Exception as e:
        return False, ""


def main(keywords=ALL_KEYWORDS, max_per_keyword=50, 
         date_start="2024-09-01", date_end=None, target_total=1000):
    
    if date_end is None:
        date_end = datetime.now().strftime("%Y-%m-%d")
    
    # Load & normalize existing data
    existing_records, existing_video_ids = load_existing_metadata()
    current_count = len(existing_records)
    
    print(f"\n{'='*70}")
    print(f"BALANCED YOUTUBE SCRAPER for PSEUDO-LABELING")
    print(f"{'='*70}")
    print(f"Resume: Starting from {current_count} existing videos")
    print(f"Target total: {target_total}")
    print(f"Need: {max(0, target_total - current_count)} more videos")
    print(f"Date range: {date_start} to {date_end}")
    print(f"Keywords: {len(keywords)} (stratified)")
    print(f"{'='*70}\n")
    
    records = existing_records.copy()
    stats = {
        'discovered': 0,
        'downloaded': 0,
        'skipped_duplicate': 0,
        'skipped_duration': 0,
        'skipped_date': 0,
        'failed': 0,
        'by_tier': {'news': 0, 'analysis': 0, 'factcheck': 0, 'viral': 0, 'prabowo': 0, 'additional': 0, 'legacy': 0}
    }
    
    # Hitung distribusi existing data
    for rec in existing_records:
        tier = rec.get('keyword_tier', 'legacy')
        stats['by_tier'][tier] = stats['by_tier'].get(tier, 0) + 1
    
    if current_count >= target_total:
        print(f"✓ Target already reached! ({current_count}/{target_total})")
        return records
    
    # Get next sample_id once at start
    next_sample_num = 1
    if existing_records:
        max_num = 0
        for rec in existing_records:
            sample_id = rec.get('sample_id', '')
            if sample_id.startswith('YT_'):
                try:
                    num = int(sample_id.split('_')[1])
                    max_num = max(max_num, num)
                except:
                    continue
        next_sample_num = max_num + 1
        print(f"🆔 Will continue from: YT_{next_sample_num:05d}\n")
    
    for kw_idx, keyword in enumerate(keywords, 1):
        if len(records) >= target_total:
            print(f"\n✓ Target reached! ({len(records)}/{target_total})")
            break
        
        tier = determine_keyword_tier(keyword)
        
        print(f"\n[{kw_idx}/{len(keywords)}] {keyword} [Tier: {tier}]")
        print(f"Progress: {len(records)}/{target_total} (Need: {target_total - len(records)} more)")
        
        videos = search_youtube(keyword, max_results=max_per_keyword)
        stats['discovered'] += len(videos)
        
        if not videos:
            continue
        
        for vid_idx, video in enumerate(videos, 1):
            if len(records) >= target_total:
                break
            
            video_id = video['video_id']
            
            if video_id in existing_video_ids:
                stats['skipped_duplicate'] += 1
                continue
            
            # Generate sample_id incrementally
            sample_id = f"YT_{next_sample_num:05d}"
            next_sample_num += 1
            
            try:
                info = get_video_info(video['url'])
                
                if not info:
                    stats['failed'] += 1
                    continue
                
                duration = info.get('duration')
                
                if not is_valid_duration(duration):
                    stats['skipped_duration'] += 1
                    continue
                
                upload_date = info.get('upload_date')
                if not is_valid_date(upload_date, date_start, date_end):
                    stats['skipped_date'] += 1
                    continue
                
                ensure_dirs("./data/raw/youtube/json")
                save_json(f"./data/raw/youtube/json/{video_id}.json", info)
                
                thumb_path = download_thumbnail(info.get('thumbnail'), sample_id)
                audio_ok, audio_path = download_wav(video['url'], sample_id)
                
                if not audio_ok:
                    stats['failed'] += 1
                    time.sleep(2)
                    continue
                
                # Infer channel_type
                channel_type = classify_channel_type({'channel': info.get('uploader', ''), 'keyword': keyword})
                
                rec = {
                    'sample_id': sample_id,
                    'source': 'youtube',
                    'keyword': keyword,
                    'keyword_tier': tier,
                    'channel_type': channel_type,
                    'video_id': video_id,
                    'title': info.get('title', ''),
                    'description': info.get('description', '')[:500],
                    'channel': info.get('uploader', ''),
                    'channel_id': info.get('channel_id', ''),
                    'duration': duration,
                    'duration_str': f"{duration//60}m {duration%60}s",
                    'upload_date': upload_date,
                    'view_count': info.get('view_count'),
                    'like_count': info.get('like_count'),
                    'url': video['url'],
                    'audio_path': audio_path,
                    'thumbnail_path': thumb_path,
                    'modality': 'text+image+audio',
                    'status': 'success',
                    'scraped_at': get_timestamp()
                }
                records.append(rec)
                existing_video_ids.add(video_id)
                stats['downloaded'] += 1
                stats['by_tier'][tier] += 1
                
                print(f"  ✓ [{sample_id}] {video['title'][:50]} ({len(records)}/{target_total})")
                
                if stats['downloaded'] % 5 == 0:
                    save_json("./data/raw/youtube/metadata.json", records)
                    print(f"  💾 Auto-saved at {len(records)} videos")
                
                time.sleep(1.5)
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
                stats['failed'] += 1
                time.sleep(2)
        
        time.sleep(2)
    
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Starting count: {current_count}")
    print(f"Total discovered: {stats['discovered']}")
    print(f"Newly downloaded: {stats['downloaded']}")
    print(f"Skipped (duplicate): {stats['skipped_duplicate']}")
    print(f"Skipped (duration): {stats['skipped_duration']}")
    print(f"Skipped (date): {stats['skipped_date']}")
    print(f"Failed: {stats['failed']}")
    print(f"Final total: {len(records)}")
    print(f"\nDistribution by tier:")
    for tier, count in sorted(stats['by_tier'].items(), key=lambda x: x[1], reverse=True):
        pct = (count/len(records)*100) if len(records) > 0 else 0
        print(f"  {tier}: {count} ({pct:.1f}%)")
    print(f"{'='*70}\n")
    
    ensure_dirs("./data/raw/youtube")
    save_json("./data/raw/youtube/metadata.json", records)
    print(f"✓ Saved {len(records)} videos total!")
    
    return records


if __name__ == "__main__":
    main(
        keywords=ALL_KEYWORDS,
        max_per_keyword=50,
        date_start="2024-10-20",
        date_end=None,
        target_total=1000
    )
