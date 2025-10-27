from src.data_preprocessing.youtube_discovery import yt_search_queries
from src.data_preprocessing.youtube_enrich_download import enrich_and_download
from src.annotation.turnbackhoax_standalone import scrape_and_save
from src.annotation.news_portals_standalone import scrape_all_sources
from src.data_preprocessing.integrate_dataset import integrate
from src.utils.io import save_json
import pandas as pd, json

QUERIES = [
    "Presiden Prabowo kebijakan",
    "DPR APBN 2025",
    "subsidi BBM Indonesia",
    "kabinet merah putih",
    "pemerintah Indonesia program",
    "menteri Indonesia berita",
    "Prabowo pidato",
    "politik Indonesia terbaru",
]

if __name__ == "__main__":
    # 1) YouTube
    disc = yt_search_queries(QUERIES, max_results=15)
    recs = enrich_and_download(disc, audio_only=False)
    save_json("./data/raw/youtube/metadata_compiled.json", recs)

    # 2) TurnBackHoax 
    scrape_and_save("./data/raw/turnbackhoax/", pages_per_slug=3, max_per_slug=60)

    # 3) News via RSS
    scrape_all_sources(download_images=True, max_per_source=40)

    # 4) Integrasi seluruh sumber ke korpus
    df = integrate()
    print("Integrated rows:", len(df))