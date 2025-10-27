import os, time, shutil, yt_dlp
from src.utils.io import save_json, ensure_dirs, timestamp
from src.utils.net import get

def _check_ffmpeg():
    if shutil.which('ffmpeg') is None:
        print("Warning: FFmpeg not found in PATH.")

def yt_detail(url):
    ydl_opts = {'quiet': True, 'no_warnings': True, 'skip_download': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)

def yt_download(url, sample_id, out_dir="./data/raw/youtube", audio_only=True):
    """
    Unduh media YouTube dengan koneksi lebih stabil.
    - audio_only=True: hanya ekstrak audio (WAV) untuk efisiensi.
    - audio_only=False: unduh video MP4 + audio WAV.
    Output:
      {"video_path": <path or "">, "audio_path": <path>}
    """

    ensure_dirs(f"{out_dir}/videos", f"{out_dir}/audio", f"{out_dir}/thumbnails", f"{out_dir}/json")
    _check_ffmpeg()

    video_out = f"{out_dir}/videos/{sample_id}.mp4"
    audio_out = f"{out_dir}/audio/{sample_id}.wav"

    # Opsi umum untuk stabilitas koneksi (retry, chunking, IPv4, UA)
    ydl_common = {
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'retries': 10,
        'fragment_retries': 20,
        'http_chunk_size': 10 * 1024 * 1024,   # 10 MB per fragmen
        'socket_timeout': 30,
        'source_address': '0.0.0.0',           # paksa IPv4
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
        'geo_bypass': True,
    }  # [web:54][web:21]

    # Video: gabung bestvideo+bestaudio -> MP4
    ydl_opts_video = {
        **ydl_common,
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': video_out,
        'merge_output_format': 'mp4',
    }

    # Audio: pilih stream audio stabil (webm/opus) lalu convert ke WAV
    ydl_opts_audio = {
        **ydl_common,
        'format': 'bestaudio[ext=webm]/bestaudio/best',
        'outtmpl': audio_out.replace('.wav', '.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
    }

    # Unduh
    try:
        if not audio_only:
            print(f"[yt_download] Downloading VIDEO -> {video_out}")
            with yt_dlp.YoutubeDL(ydl_opts_video) as ydl:
                ydl.download([url])
        print(f"[yt_download] Downloading AUDIO -> {audio_out}")
        with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl:
            ydl.download([url])
        return {
            "video_path": video_out if not audio_only else "",
            "audio_path": audio_out,
        }
    except Exception as e:
        print(f"[yt_download] ERROR: {e}")
        # fallback: coba set chunk lebih kecil jika error berulang
        try:
            ydl_common_fallback = {**ydl_common, 'http_chunk_size': 5 * 1024 * 1024}
            if not audio_only:
                with yt_dlp.YoutubeDL({**ydl_opts_video, **ydl_common_fallback}) as ydl:
                    ydl.download([url])
            with yt_dlp.YoutubeDL({**ydl_opts_audio, **ydl_common_fallback}) as ydl:
                ydl.download([url])
            return {
                "video_path": video_out if not audio_only else "",
                "audio_path": audio_out,
            }
        except Exception as e2:
            print(f"[yt_download] FALLBACK ERROR: {e2}")
            return {"video_path": "" if not audio_only else "", "audio_path": "", "error": str(e2)}

def enrich_and_download(discovery_list, audio_only=True):
    records = []
    for idx, item in enumerate(discovery_list, start=1):
        url = item["url"]; sample_id = f"YT_{idx:04d}"
        try:
            info = yt_detail(url)
            vid = info.get("id", item["video_id"])
            save_json(f"./data/raw/youtube/json/{vid}.json", info)
            # thumbnail
            thumb_url = info.get('thumbnail')
            thumb_path = ""
            if thumb_url:
                try:
                    r = get(thumb_url)
                    os.makedirs("./data/raw/youtube/thumbnails", exist_ok=True)
                    thumb_path = f"./data/raw/youtube/thumbnails/{sample_id}.jpg"
                    with open(thumb_path,"wb") as f: f.write(r.content)
                except Exception as e:
                    print("thumb error:", e)
            # media
            dl = yt_download(url, sample_id, audio_only=audio_only)
            rec = {
                "sample_id": sample_id,
                "source": "youtube",
                "video_id": vid,
                "title": info.get("title",""),
                "description": info.get("description",""),
                "channel": info.get("uploader",""),
                "channel_id": info.get("channel_id",""),
                "upload_date": info.get("upload_date",""),
                "duration": info.get("duration"),
                "view_count": info.get("view_count"),
                "like_count": info.get("like_count"),
                "comment_count": info.get("comment_count"),
                "video_url": url,
                "video_path": dl.get("video_path",""),
                "audio_path": dl.get("audio_path",""),
                "thumbnail_path": thumb_path,
                "scraped_at": timestamp()
            }
            records.append(rec)
            time.sleep(1.2)
        except Exception as e:
            print("enrich error:", url, e)
            time.sleep(2.0)
    return records
