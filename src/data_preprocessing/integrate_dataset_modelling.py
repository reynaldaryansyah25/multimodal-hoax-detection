import pandas as pd
import numpy as np
import os
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# KONFIGURASI
# ============================================================================

CONFIG = {
    # Input files - Dataset gabungan (tanpa image)
    'path_combined': r'D:\INDONERIS-DATAMINING\multimodal-hoax-detection\data\processed\dataset_clean_finalv1.csv',
    
    # Input files - Data mentah (dengan image_path)
    'path_tbh_raw': r'D:\INDONERIS-DATAMINING\multimodal-hoax-detection\data\raw\turnbackhoax\metadata\tbh_complete_dataset1.csv',
    'path_news_raw': r'D:\INDONERIS-DATAMINING\multimodal-hoax-detection\data\raw\news\AllMetadata_Cleaned_v3.csv',
    
    # Input file - YouTube pseudo-labeled (punya thumbnail_path lokal)
    'path_youtube': r'D:\INDONERIS-DATAMINING\multimodal-hoax-detection\data\processed\youtube_pseudo_labeled_balanced.csv',
    
    # Output directory
    'output_dir': r'D:\INDONERIS-DATAMINING\multimodal-hoax-detection\data\training\multimodal_splits',
    
    # Feature groups (ganti image_url -> image_path)
    'feature_groups': {
        'text_only': {
            'features': ['title', 'text_content'],
            'modalities': ['text'],
            'description': 'Text unimodal'
        },
        'image_only': {
            'features': ['image_path'],
            'modalities': ['image'],
            'description': 'Image unimodal'
        },
        'text_image': {
            'features': ['title', 'text_content', 'image_path'],
            'modalities': ['text', 'image'],
            'description': 'Bimodal: Text + Image'
        },
        'text_audio': {
            'features': ['title', 'text_content', 'audio_path'],
            'modalities': ['text', 'audio'],
            'description': 'Bimodal: Text + Audio (YouTube only)'
        },
        'text_image_audio': {
            'features': ['title', 'text_content', 'image_path', 'audio_path'],
            'modalities': ['text', 'image', 'audio'],
            'description': 'Trimodal (YouTube only)'
        }
    }
}

# ============================================================================
# UTILITY
# ============================================================================

def print_header(text):
    print("\n" + "="*80)
    print(text)
    print("="*80)

def print_subheader(text):
    print("\n" + "-"*80)
    print(text)
    print("-"*80)

# ============================================================================
# STEP 1: MERGE IMAGE_PATH PER SUMBER (TBH vs NEWS)
# ============================================================================

def merge_image_paths():
    """
    Merge gambar ke dataset gabungan dengan aturan:
    - TBH: image_path dari tbh_complete_dataset1.csv
    - News: image_path dari AllMetadata_Cleaned_v3.csv
    """
    print_header("STEP 1: MERGE IMAGE_PATH (TBH vs NEWS)")

    # Load dataset gabungan (TBH + News)
    print("\nLoading dataset_combined (TBH+News)...")
    df_combined = pd.read_csv(CONFIG['path_combined'])
    print(f"  Loaded: {len(df_combined):,} rows")
    
    if 'dataset_origin' not in df_combined.columns:
        raise ValueError("dataset_clean_finalv1.csv must contain 'dataset_origin' column")

    # Load raw TBH
    print("\nLoading TBH raw metadata...")
    df_tbh_raw = pd.read_csv(CONFIG['path_tbh_raw'])
    print(f"  TBH raw: {len(df_tbh_raw):,} rows")

    # Load raw News
    print("\nLoading News raw metadata...")
    df_news_raw = pd.read_csv(CONFIG['path_news_raw'])
    print(f"  News raw: {len(df_news_raw):,} rows")

    # Siapkan kolom image per sumber
    df_combined['image_path_tbh'] = None
    df_combined['image_path_news'] = None

    # ---------------------- TBH IMAGE_PATH ---------------------------
    print("\nMerging TBH image_path by id (only for TBH rows)...")
    mask_tbh = df_combined['dataset_origin'].astype(str).str.lower().str.contains('tbh') | \
               df_combined['dataset_origin'].astype(str).str.lower().str.contains('hoax')
    df_combined_tbh = df_combined[mask_tbh].copy()

    if 'id' in df_tbh_raw.columns and 'image_path' in df_tbh_raw.columns:
        df_tbh_merge = df_tbh_raw[['id', 'image_path']].copy()
        df_tbh_merged = df_combined_tbh.merge(
            df_tbh_merge,
            on='id',
            how='left',
            suffixes=('', '_tbh_raw')
        )
        n_tbh_img = df_tbh_merged['image_path'].notna().sum()
        print(f"  TBH rows: {len(df_combined_tbh):,}, with image_path: {n_tbh_img:,}")
        df_combined.loc[mask_tbh, 'image_path_tbh'] = df_tbh_merged['image_path'].values
    else:
        print("  WARNING: 'id' or 'image_path' not found in TBH raw")

    # ---------------------- NEWS IMAGE_PATH -------------------------
    print("\nMerging News image_path by id (only for News rows)...")
    mask_news = df_combined['dataset_origin'].astype(str).str.lower().eq('news')
    df_combined_news = df_combined[mask_news].copy()

    if 'id' in df_news_raw.columns and 'image_path' in df_news_raw.columns:
        df_news_merge = df_news_raw[['id', 'image_path']].copy()
        df_news_merged = df_combined_news.merge(
            df_news_merge,
            on='id',
            how='left',
            suffixes=('', '_news_raw')
        )
        n_news_img = df_news_merged['image_path'].notna().sum()
        print(f"  News rows: {len(df_combined_news):,}, with image_path: {n_news_img:,}")
        df_combined.loc[mask_news, 'image_path_news'] = df_news_merged['image_path'].values
    else:
        print("  WARNING: 'id' or 'image_path' not found in News raw")

    # ---------------------- UNIFY IMAGE_PATH COLUMN -----------------------------
    print("\nUnifying TBH/News images into single 'image_path' column...")
    df_combined['image_path'] = None

    df_combined.loc[mask_tbh, 'image_path'] = df_combined.loc[mask_tbh, 'image_path_tbh']
    df_combined.loc[mask_news, 'image_path'] = df_combined.loc[mask_news, 'image_path_news']

    df_combined = df_combined.drop(columns=['image_path_tbh', 'image_path_news'], errors='ignore')

    print_subheader("SUMMARY MERGE TBH+NEWS")
    total_with_image = df_combined['image_path'].notna().sum()
    pct_with_image = total_with_image / len(df_combined) * 100
    print(f"\nTotal TBH+News records with image_path: {total_with_image:,} / {len(df_combined):,} ({pct_with_image:.1f}%)")

    if 'dataset_origin' in df_combined.columns:
        print("\nImage availability per dataset_origin:")
        for origin in df_combined['dataset_origin'].unique():
            subset = df_combined[df_combined['dataset_origin'] == origin]
            n_with_img = subset['image_path'].notna().sum()
            pct = n_with_img / len(subset) * 100 if len(subset) > 0 else 0
            print(f"  {origin:15s}: {n_with_img:4,} / {len(subset):4,} ({pct:5.1f}%)")

    return df_combined

# ============================================================================
# STEP 2: PROCESS YOUTUBE DATA (thumbnail_path -> image_path)
# ============================================================================

def process_youtube_data():
    """Load dan process YouTube data dengan image_path dari thumbnail_path."""
    print_header("STEP 2: PROCESS YOUTUBE DATA")

    print("\nLoading YouTube pseudo-labeled data...")
    df_youtube = pd.read_csv(CONFIG['path_youtube'])
    print(f"  Loaded: {len(df_youtube):,} rows")

    # Gunakan thumbnail_path lokal sebagai image_path
    print("\nMapping YouTube thumbnail_path -> image_path...")
    if 'thumbnail_path' in df_youtube.columns:
        df_youtube['image_path'] = df_youtube['thumbnail_path']
        n_generated = df_youtube['image_path'].notna().sum()
        print(f"  Mapped: {n_generated:,} rows with image_path from thumbnail_path")
    else:
        print("  WARNING: 'thumbnail_path' column not found in YouTube data")
        df_youtube['image_path'] = None

    # Rename columns untuk consistency
    rename_map = {
        'pseudo_label': 'label',
        'pseudo_confidence': 'confidence',
        'labeling_source': 'data_source',
        'normalized_text': 'text_normalized'
    }
    actual_rename = {k: v for k, v in rename_map.items() if k in df_youtube.columns}
    if actual_rename:
        df_youtube = df_youtube.rename(columns=actual_rename)
        print(f"\n  Renamed columns: {list(actual_rename.keys())}")

    # Create text_content
    if 'text_content' not in df_youtube.columns:
        if 'transcript_text' in df_youtube.columns:
            df_youtube['text_content'] = df_youtube.apply(
                lambda x: f"{x['title']}. {x['transcript_text']}"
                if pd.notna(x.get('transcript_text')) else str(x.get('title', '')),
                axis=1
            )
            print("  Created 'text_content' from title + transcript")
        else:
            df_youtube['text_content'] = df_youtube.get('title', '')
            print("  Created 'text_content' from title only")

    print("\nYouTube data processed")
    print(f"  With image_path: {df_youtube['image_path'].notna().sum():,}")
    print(f"  With audio_path: {df_youtube.get('audio_path', pd.Series()).notna().sum():,}")

    return df_youtube

# ============================================================================
# STEP 3: HARMONIZE DAN INTEGRATE (TIDAK DIUBAH, KECUALI image_url -> image_path)
# ============================================================================

def harmonize_and_integrate(df_tbh_news, df_youtube):
    """Harmonize columns dan integrate datasets"""
    print_header("STEP 3: HARMONIZE & INTEGRATE")

    print("\nHarmonizing TBH+News...")

    # TEXT COLUMNS
    if 'text' in df_tbh_news.columns and 'text_content' not in df_tbh_news.columns:
        df_tbh_news['text_content'] = df_tbh_news['text']
    if 'text_clean' in df_tbh_news.columns and 'text_normalized' not in df_tbh_news.columns:
        df_tbh_news['text_normalized'] = df_tbh_news['text_clean']

    # LABEL MAPPING
    print("  Mapping labels...")
    if 'label_str' in df_tbh_news.columns:
        df_tbh_news['label'] = df_tbh_news['label_str']
        print("    Using 'label_str' column")
    elif 'label' in df_tbh_news.columns:
        df_tbh_news['label'] = df_tbh_news['label'].apply(
            lambda x: 'hoax' if x == 0 else 'valid'
        )
        print("    Converted numeric label: 0->hoax, 1->valid")
    else:
        if 'dataset_origin' in df_tbh_news.columns:
            df_tbh_news['label'] = df_tbh_news['dataset_origin'].apply(
                lambda x: 'hoax' if 'hoax' in str(x).lower() or 'tbh' in str(x).lower()
                else 'valid'
            )
            print("    Generated label from dataset_origin")

    # SAMPLE_ID
    print("  Generating sample_id...")
    if 'sample_id' not in df_tbh_news.columns:
        def generate_sample_id(row):
            origin = str(row.get('dataset_origin', '')).lower()
            row_id = row.get('id', 0)
            if 'hoax' in origin or 'tbh' in origin:
                return f"TBH_{row_id}"
            elif 'news' in origin:
                return f"NEWS_{row_id}"
            else:
                return f"DATA_{row_id}"
        df_tbh_news['sample_id'] = df_tbh_news.apply(generate_sample_id, axis=1)

    # DATA_SOURCE
    print("\n  Mapping data_source...")
    if 'data_source' not in df_tbh_news.columns:
        if 'dataset_origin' in df_tbh_news.columns:
            def map_data_source(origin):
                o = str(origin).lower()
                if 'hoax' in o or 'tbh' in o:
                    return 'original_hoax'
                elif 'news' in o:
                    return 'original_valid'
                else:
                    return 'original_unknown'
            df_tbh_news['data_source'] = df_tbh_news['dataset_origin'].apply(map_data_source)

    # Add confidence and audio_path
    df_tbh_news['confidence'] = 1.0
    if 'audio_path' not in df_tbh_news.columns:
        df_tbh_news['audio_path'] = None

    print(f"\n  TBH+News harmonized: {len(df_tbh_news):,} rows")

    # Harmonize YT
    print("\nHarmonizing YouTube...")
    if 'domain' not in df_youtube.columns:
        df_youtube['domain'] = df_youtube.get('channel', None)
    if 'date' not in df_youtube.columns:
        df_youtube['date'] = df_youtube.get('upload_date', None)
    if 'url' not in df_youtube.columns and 'video_id' in df_youtube.columns:
        df_youtube['url'] = 'https://youtube.com/watch?v=' + df_youtube['video_id'].fillna('')

    print(f"  YouTube harmonized: {len(df_youtube):,} rows")

    # COMMON COLUMNS (image_path instead of image_url)
    common_cols = [
        'sample_id', 'label', 'data_source', 'confidence',
        'title', 'text_content', 'text_normalized',
        'image_path', 'audio_path',
        'domain', 'date'
    ]

    for col in common_cols:
        if col not in df_tbh_news.columns:
            df_tbh_news[col] = None
        if col not in df_youtube.columns:
            df_youtube[col] = None

    df_tbh_final = df_tbh_news[common_cols].copy()
    df_yt_final = df_youtube[common_cols].copy()

    print("\nIntegrating datasets...")
    df_integrated = pd.concat([df_tbh_final, df_yt_final], ignore_index=True)

    # Sample weighting
    df_integrated['sample_weight'] = df_integrated.apply(
        lambda x: 1.0 if 'original' in str(x.get('data_source', ''))
        else float(x.get('confidence', 0.5)) ** 2,
        axis=1
    )

    print_subheader("INTEGRATION SUMMARY")
    print(f"\nTotal samples: {len(df_integrated):,}")
    print(f"  TBH+News: {len(df_tbh_final):,}")
    print(f"  YouTube: {len(df_yt_final):,}")

    print("\nSample ID breakdown:")
    for prefix in ['TBH_', 'NEWS_', 'YT_', 'DATA_']:
        count = df_integrated['sample_id'].str.startswith(prefix, na=False).sum()
        if count > 0:
            pct = count / len(df_integrated) * 100
            print(f"  {prefix}*: {count:,} ({pct:.1f}%)")

    print("\nMultimodal features availability:")
    print(f"  Text:  {df_integrated[['title', 'text_content']].notna().any(axis=1).sum():,}")
    print(f"  Image: {df_integrated['image_path'].notna().sum():,}")
    print(f"  Audio: {df_integrated['audio_path'].notna().sum():,}")

    return df_integrated

# ============================================================================
# STEP 4: EXPORT PER MODALITY (image_path, tanpa url)
# ============================================================================

def export_multimodal_datasets(df_integrated):
    """Export datasets per modality configuration (tanpa kolom url)."""
    print_header("STEP 4: EXPORT PER MODALITY")

    os.makedirs(CONFIG['output_dir'], exist_ok=True)
    print(f"\nOutput directory: {CONFIG['output_dir']}")

    exported_files = {}
    config_summary = []

    for name, config in CONFIG['feature_groups'].items():
        print(f"\n{'-'*80}")
        print(f"Processing: {name.upper()}")
        print(f"  Required features: {', '.join(config['features'])}")

        mask = pd.Series([True] * len(df_integrated))

        for feat in config['features']:
            if feat in df_integrated.columns:
                feat_mask = df_integrated[feat].notna()
                n_avail = feat_mask.sum()
                pct = n_avail / len(df_integrated) * 100
                print(f"    {feat}: {n_avail:,} / {len(df_integrated):,} ({pct:.1f}%)")
                mask = mask & feat_mask
            else:
                print(f"    {feat}: NOT FOUND")
                mask = pd.Series([False] * len(df_integrated))
                break

        df_modality = df_integrated[mask].copy()

        if len(df_modality) == 0:
            print("  SKIP: No data available")
            continue

        if 'data_source' in df_modality.columns:
            print("\n  Data source breakdown:")
            for source, count in df_modality['data_source'].value_counts().items():
                pct = count / len(df_modality) * 100
                print(f"    {source:30s}: {count:5,} ({pct:.1f}%)")

        print("\n  Sample ID breakdown:")
        for prefix in ['TBH_', 'NEWS_', 'YT_']:
            count = df_modality['sample_id'].str.startswith(prefix, na=False).sum()
            if count > 0:
                pct = count / len(df_modality) * 100
                print(f"    {prefix}*: {count:,} ({pct:.1f}%)")

        export_cols = ['sample_id', 'label', 'data_source', 'confidence', 'sample_weight']
        export_cols.extend(config['features'])
        export_cols.extend(['domain', 'date'])

        export_cols = list(dict.fromkeys(export_cols))
        export_cols = [c for c in export_cols if c in df_modality.columns]

        df_export = df_modality[export_cols].copy()

        output_file = os.path.join(CONFIG['output_dir'], f'{name}_dataset.csv')
        df_export.to_csv(output_file, index=False, encoding='utf-8')

        exported_files[name] = output_file

        label_dist = df_export['label'].value_counts() if 'label' in df_export.columns else pd.Series()
        n_hoax = label_dist.get('hoax', 0)
        n_valid = label_dist.get('valid', 0)

        n_tbh = df_export['sample_id'].str.startswith('TBH_', na=False).sum()
        n_news = df_export['sample_id'].str.startswith('NEWS_', na=False).sum()
        n_yt = df_export['sample_id'].str.startswith('YT_', na=False).sum()

        print(f"\n  EXPORTED: {os.path.basename(output_file)}")
        print(f"  Total: {len(df_export):,}")
        print(f"  Label: hoax={n_hoax:,}, valid={n_valid:,}")
        print(f"  Source: TBH={n_tbh:,}, News={n_news:,}, YouTube={n_yt:,}")

        config_summary.append({
            'experiment_name': name,
            'modalities': ', '.join(config['modalities']),
            'n_samples': len(df_export),
            'n_hoax': n_hoax,
            'n_valid': n_valid,
            'n_tbh': n_tbh,
            'n_news': n_news,
            'n_youtube': n_yt,
            'filepath': output_file
        })

    if config_summary:
        df_summary = pd.DataFrame(config_summary)
        summary_file = os.path.join(CONFIG['output_dir'], 'training_configuration_summary.csv')
        df_summary.to_csv(summary_file, index=False)

        print_header("EXPORT SUMMARY")
        print(f"\nTotal configurations exported: {len(exported_files)}")
        print("\nFiles:")
        for idx, nm in enumerate(exported_files.keys(), 1):
            print(f"  {idx}. {nm}_dataset.csv")

        cols = ['experiment_name', 'n_samples', 'n_hoax', 'n_valid', 'n_tbh', 'n_news', 'n_youtube']
        print("\nConfiguration table:")
        print(df_summary[cols].to_string(index=False))
        print(f"\nSummary saved: {os.path.basename(summary_file)}")

    return exported_files, config_summary

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("="*80)
    print("INTEGRASI DATASET MULTIMODAL DENGAN IMAGE_PATH SUPPORT")
    print("Version 4.2 (TBH/News image_path, YT thumbnail_path, url removed)")
    print("="*80)

    try:
        df_tbh_news = merge_image_paths()
        df_youtube = process_youtube_data()
        df_integrated = harmonize_and_integrate(df_tbh_news, df_youtube)
        exported_files, summary = export_multimodal_datasets(df_integrated)

        print_header("SELESAI")
        print("\nIntegrasi dataset BERHASIL!")
        print(f"\nOutput: {CONFIG['output_dir']}")
        print(f"Files: {len(exported_files)} modality datasets + 1 summary")
        return 0

    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
