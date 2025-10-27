import json, os, pandas as pd
from src.utils.io import save_json

def load_json(path):
    if not os.path.exists(path): return []
    return json.load(open(path,"r",encoding="utf-8"))

def integrate():
    # YouTube detail JSON -> baris ringkas (sama seperti sebelumnya)
    yt_rows = []
    yt_json_dir = "./data/raw/youtube/json"
    if os.path.exists(yt_json_dir):
        for i, f in enumerate(sorted(os.listdir(yt_json_dir))):
            if f.endswith(".json"):
                d = json.load(open(os.path.join(yt_json_dir,f),"r",encoding="utf-8"))
                yt_rows.append({
                    "source":"youtube",
                    "ref_id": d.get("id",""),
                    "title": d.get("title",""),
                    "text": d.get("description",""),
                    "url": f"https://www.youtube.com/watch?v={d.get('id','')}",
                    "labels": [],
                    "media_paths": {
                        "audio": f"./data/raw/youtube/audio/YT_{i+1:04d}.wav",
                        "video": f"./data/raw/youtube/videos/YT_{i+1:04d}.mp4",
                        "thumbnail": f"./data/raw/youtube/thumbnails/YT_{i+1:04d}.jpg",
                    }
                })
    tbh = load_json("./data/raw/turnbackhoax/articles.json")
    tbh_rows = [{
        "source":"turnbackhoax","ref_id": x.get("url",""),
        "title": x.get("title",""), "text":x.get("text",""),
        "url": x.get("url",""), "labels": x.get("labels",[]),
        "media_paths":{"images": x.get("images",[])}
    } for x in tbh]
    news = load_json("./data/raw/news/articles.json")
    news_rows = [{
        "source":"news","ref_id": x.get("url",""),
        "title": x.get("title",""), "text": x.get("text",""),
        "url": x.get("url",""), "date": x.get("date",""),
        "authors": "|".join(x.get("authors",[])) if isinstance(x.get("authors"), list) else str(x.get("authors","")),
        "domain": x.get("domain",""), "labels": [],
        "media_paths":{"top_image": x.get("image","")}
    } for x in news]
    all_rows = yt_rows + tbh_rows + news_rows
    df = pd.DataFrame(all_rows)
    os.makedirs("./data/processed", exist_ok=True)
    df.to_csv("./data/processed/corpus_integrated.csv", index=False, encoding="utf-8")
    save_json("./data/processed/corpus_integrated.json", all_rows)
    return df
