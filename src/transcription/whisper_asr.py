import os
import json
import torch
from pathlib import Path
from datetime import datetime, timezone
import whisper


def ensure_dirs(*dirs):
    for d in dirs:
        os.makedirs(d, exist_ok=True)


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_timestamp():
    return datetime.now(timezone.utc).isoformat()


def load_metadata(metadata_path="./data/raw/youtube/metadata.json"):
    with open(metadata_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def check_gpu():
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        return True
    else:
        print("GPU: Not available, using CPU")
        return False


def transcribe_audio(audio_path, model_name="base"):
    try:
        print(f"  Loading model: {model_name}...")
        model = whisper.load_model(model_name)
        
        print(f"  Transcribing: {Path(audio_path).name}...")
        result = model.transcribe(audio_path, language="id", verbose=False)
        
        return {
            'success': True,
            'text': result.get('text', ''),
            'language': result.get('language', 'id'),
            'duration': result.get('duration'),
        }
        
    except Exception as e:
        print(f"  Error: {e}")
        return {
            'success': False,
            'text': '',
            'language': 'id',
            'error': str(e)
        }


def process_youtube_transcripts(metadata_path="./data/raw/youtube/metadata.json", 
                                 model_name="base",
                                 output_dir="./data/transcript"):
    
    ensure_dirs(output_dir)
    
    print(f"{'='*70}")
    print("WHISPER TRANSCRIPTION PIPELINE")
    print(f"{'='*70}")
    print(f"Model: {model_name}")
    check_gpu()
    print(f"Output: {output_dir}")
    print(f"{'='*70}\n")
    
    # Load metadata
    print("Loading metadata...")
    try:
        records = load_metadata(metadata_path)
        print(f"Loaded {len(records)} records\n")
    except Exception as e:
        print(f"Error loading metadata: {e}")
        return
    
    stats = {
        'total': len(records),
        'transcribed': 0,
        'failed': 0,
        'skipped': 0,
    }
    
    output_records = []
    
    for idx, record in enumerate(records, 1):
        sample_id = record.get('sample_id')
        audio_path = record.get('audio_path')
        
        print(f"[{idx}/{len(records)}] {sample_id}")
        
        # Check audio exists
        if not audio_path or not os.path.exists(audio_path):
            print("  Audio file not found")
            stats['skipped'] += 1
            continue
        
        # Transcribe
        print(f"  Audio: {Path(audio_path).name}")
        transcript_result = transcribe_audio(audio_path, model_name=model_name)
        
        if not transcript_result['success']:
            print(f"  Failed: {transcript_result.get('error', 'Unknown error')}")
            stats['failed'] += 1
            continue
        
        # Save transcript file
        transcript_text = transcript_result['text']
        transcript_path = f"{output_dir}/{sample_id}.txt"
        
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write(transcript_text)
        
        # Create output record
        output_record = {
            'sample_id': sample_id,
            'source': record.get('source'),
            'keyword': record.get('keyword'),
            'video_id': record.get('video_id'),
            'title': record.get('title', ''),
            'channel': record.get('channel', ''),
            'duration': record.get('duration'),
            'upload_date': record.get('upload_date'),
            'url': record.get('url'),
            'audio_path': audio_path,
            'thumbnail_path': record.get('thumbnail_path'),
            'transcript_path': transcript_path,
            'transcript_text': transcript_text,
            'transcript_length': len(transcript_text),
            'language': transcript_result.get('language'),
            'label': 0,
            'status': 'success',
            'transcribed_at': get_timestamp()
        }
        output_records.append(output_record)
        
        print(f"  Length: {len(transcript_text)} chars")
        print("  SUCCESS")
        stats['transcribed'] += 1
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Total processed: {stats['total']}")
    print(f"Transcribed: {stats['transcribed']}")
    print(f"Skipped: {stats['skipped']}")
    print(f"Failed: {stats['failed']}")
    print(f"{'='*70}\n")
    
    # Save metadata
    output_metadata = f"{output_dir}/metadata.json"
    save_json(output_metadata, output_records)
    
    print(f"Output:")
    print(f"  Path: {output_dir}/")
    print(f"  Transcripts: {stats['transcribed']} files")
    print(f"  Metadata: {output_metadata}")
    
    return output_records


if __name__ == "__main__":
    process_youtube_transcripts(
        metadata_path="./data/raw/youtube/metadata.json",
        model_name="base",
        output_dir="./data/transcript"
    )
