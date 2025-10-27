import os, json

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_json(path, default=None):
    if not os.path.exists(path): 
        return default if default is not None else []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
