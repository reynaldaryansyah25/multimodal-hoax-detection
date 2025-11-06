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


def get_timestamp():
    return datetime.now(timezone.utc).isoformat()


SEARCH_KEYWORDS = [
    "Prabowo presiden Indonesia 2024",
    "Kabinet merah putih Prabowo",
    "Menteri kabinet Prabowo",
    "Gibran Rakabuming Raka",
    "Menteri pertahanan Prabowo",
    "Wakil presiden Gibran",
    "Politik Indonesia terkini",
    "Berita politik hari ini",
    "Pemerintah Indonesia berita",
    "Kebijakan pemerintah terbaru",
    "Peraturan pemerintah Indonesia",
    "Pemilu Indonesia 2024",
    "Pilkada Indonesia 2024",
    "Partai Politik Indonesia",
    "Koalisi pemerintah Indonesia",
    "Pemilu legislatif 2024",
    "DPR RI anggota baru",
    "Hukum Indonesia terbaru",
    "KPK berita terkini",
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
    "Visi misi Prabowo presiden",
]

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}


def is_valid_duration(duration, min_dur=180, max_dur=600):
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


def search_youtube(keyword, max_results=30):
    print(f"Searching: '{keyword}'")
    
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
                    print(f"  {title[:60]}")
            
    except Exception as e:
        print(f"Search error: {e}")
    
    print(f"Found: {len(videos)} videos\n")
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
        
        print("  Downloading thumbnail...")
        r = requests.get(thumb_url, headers=HEADERS, timeout=15)
        
        with open(thumb_path, 'wb') as f:
            f.write(r.content)
        
        return thumb_path
        
    except Exception as e:
        print(f"  Thumbnail error: {e}")
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
        print("  Downloading audio...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        if os.path.exists(audio_out):
            return True, audio_out
        else:
            return False, ""
            
    except Exception as e:
        print(f"  Audio download failed: {e}")
        return False, ""


def main(keywords=SEARCH_KEYWORDS, max_per_keyword=30, 
         date_start="2024-10-20", date_end=None):
    
    if date_end is None:
        date_end = datetime.now().strftime("%Y-%m-%d")
    
    print(f"Date range: {date_start} to {date_end}")
    print(f"Total keywords: {len(keywords)}")
    print(f"Focus: Text (metadata) + Image (thumbnail) + Audio (WAV)")
    print(f"{'='*70}\n")
    
    records = []
    stats = {
        'discovered': 0,
        'downloaded': 0,
        'skipped_duration': 0,
        'skipped_date': 0,
        'failed': 0,
    }
    
    for kw_idx, keyword in enumerate(keywords, 1):
        print(f"\n{'='*70}")
        print(f"[{kw_idx}/{len(keywords)}] {keyword}")
        print(f"{'='*70}")
        
        videos = search_youtube(keyword, max_results=max_per_keyword)
        stats['discovered'] += len(videos)
        
        if not videos:
            print("No videos found\n")
            continue
        
        for vid_idx, video in enumerate(videos, 1):
            url = video['url']
            video_id = video['video_id']
            sample_id = f"YT_{stats['downloaded']+1:05d}"
            
            print(f"\n[{vid_idx}/{len(videos)}] {video['title'][:60]}")
            
            try:
                print("  Extracting info...")
                info = get_video_info(url)
                
                if not info:
                    print("  Cannot extract info")
                    stats['failed'] += 1
                    continue
                
                duration = info.get('duration')
                
                if not is_valid_duration(duration):
                    print(f"  Duration invalid ({duration//60}m)")
                    stats['skipped_duration'] += 1
                    continue
                
                upload_date = info.get('upload_date')
                if not is_valid_date(upload_date, date_start, date_end):
                    print(f"  Date out of range ({upload_date})")
                    stats['skipped_date'] += 1
                    continue
                
                print("  Saving metadata (text)...")
                save_json(f"./data/raw/youtube/json/{video_id}.json", info)
                
                print("  Downloading image (thumbnail)...")
                thumb_path = ""
                thumb_url = info.get('thumbnail')
                if thumb_url:
                    thumb_path = download_thumbnail(thumb_url, sample_id)
                
                print("  Downloading audio (WAV)...")
                audio_ok, audio_path = download_wav(url, sample_id)
                
                if not audio_ok:
                    print("  Audio download failed")
                    stats['failed'] += 1
                    time.sleep(2)
                    continue
                
                rec = {
                    'sample_id': sample_id,
                    'source': 'youtube',
                    'keyword': keyword,
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
                    'url': url,
                    'audio_path': audio_path,
                    'thumbnail_path': thumb_path,
                    'modality': 'text+image+audio',
                    'status': 'success',
                    'scraped_at': get_timestamp()
                }
                records.append(rec)
                stats['downloaded'] += 1
                
                print("  SUCCESS")
                time.sleep(1.5)
                
            except Exception as e:
                print(f"  ERROR: {e}")
                stats['failed'] += 1
                time.sleep(2)
        
        time.sleep(3)
    
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Total discovered: {stats['discovered']}")
    print(f"Downloaded: {stats['downloaded']}")
    print(f"Skipped (duration): {stats['skipped_duration']}")
    print(f"Skipped (date): {stats['skipped_date']}")
    print(f"Failed: {stats['failed']}")
    print(f"{'='*70}\n")
    
    ensure_dirs("./data/raw/youtube")
    save_json("./data/raw/youtube/metadata.json", records)
    print(f"Saved {len(records)} videos!")
    
    return records


if __name__ == "__main__":
    main(
        keywords=SEARCH_KEYWORDS,
        max_per_keyword=30,
        date_start="2024-10-20",
        date_end=None
    )
