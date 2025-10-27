import os, json, time
import whisper

def transcribe_dir(audio_dir="./data/raw/youtube/audio", out_dir="./data/transcripts", model_name="medium", language="id"):
    os.makedirs(out_dir, exist_ok=True)
    model = whisper.load_model(model_name)
    results = []
    for fn in sorted(os.listdir(audio_dir)):
        if not fn.lower().endswith((".wav",".mp3",".m4a",".mp4",".webm")):
            continue
        in_path = os.path.join(audio_dir, fn)
        base = os.path.splitext(fn)[0]
        txt_out = os.path.join(out_dir, base + ".txt")
        json_out = os.path.join(out_dir, base + ".json")

        if os.path.exists(txt_out) and os.path.exists(json_out):
            print("skip exists:", fn); continue

        print("transcribing:", fn)
        t0 = time.time()
        out = model.transcribe(in_path, language=language, fp16=False)
        text = out.get("text","").strip()
        with open(txt_out, "w", encoding="utf-8") as f: f.write(text)
        with open(json_out, "w", encoding="utf-8") as f: json.dump(out, f, ensure_ascii=False, indent=2)
        results.append({"file": fn, "seconds": time.time()-t0, "chars": len(text)})
    return results

if __name__ == "__main__":
    transcribe_dir(model_name="medium", language="id")
