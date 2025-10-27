import os, json, time
from src.utils.io import save_json

def transcribe_batch(audio_items):
    results = []
    for it in audio_items:
        # TODO: ganti ke ASR aktual
        results.append({"sample_id": it["sample_id"], "text": "", "segments": []})
        time.sleep(0.1)
    save_json("./data/transcripts/asr_results.json", results)
    return results
