import yt_dlp, time
from src.utils.io import save_json
from tqdm import tqdm

def yt_search_queries(queries, max_results=20):
    ydl_opts = {'quiet': True, 'no_warnings': True, 'extract_flat': True, 'skip_download': True}
    urls = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for q in tqdm(queries, desc="YT search"):
            res = ydl.extract_info(f"ytsearch{max_results}:{q}", download=False)
            for e in (res.get('entries') or []):
                if not e: 
                    continue
                vid = e.get('id')
                url = e.get('url') or (f"https://www.youtube.com/watch?v={vid}" if vid else None)
                if url: 
                    urls.append({"video_id": vid, "url": url, "title": e.get('title','')})
            time.sleep(1.0)
    # dedup by video_id
    dedup = {}
    for it in urls:
        if it["video_id"] and it["video_id"] not in dedup:
            dedup[it["video_id"]] = it
    out = list(dedup.values())
    save_json("./data/raw/youtube/discovery_list.json", out)
    return out
