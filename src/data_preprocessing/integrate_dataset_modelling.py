#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script Integrasi Dataset Multimodal dengan Image URL Support
- Merge thumbnail dari TBH mentah
- Merge image_url dari News mentah  
- Generate thumbnail_url dari YouTube video_id
- Differentiate TBH vs News dalam sample_id
- Export dataset per modality

Author: INDONERIS Data Mining Team
Date: November 2025
Version: 4.0 (Final - Fixed TBH/News differentiation)
"""

import pandas as pd
import numpy as np
import os
import re
import warnings
warnings.filterwarnings('ignore')


# ============================================================================
# KONFIGURASI
# ============================================================================

CONFIG = {
    # Input files - Dataset gabungan (tanpa image)
    'path_combined': r'D:\INDONERIS-DATAMINING\multimodal-hoax-detection\data\processed\dataset_clean_finalv1.csv',
    
    # Input files - Data mentah (dengan image)
    'path_tbh_raw': r'D:\INDONERIS-DATAMINING\multimodal-hoax-detection\data\raw\turnbackhoax\metadata\turnbackhoax_fix.csv',
    'path_news_raw': r'D:\INDONERIS-DATAMINING\multimodal-hoax-detection\data\raw\news\AllMetadata_Cleaned_v3.csv',
    
    # Input file - YouTube pseudo-labeled
    'path_youtube': r'D:\INDONERIS-DATAMINING\multimodal-hoax-detection\data\processed\youtube_pseudo_labeled_balanced.csv',
    
    # Output directory
    'output_dir': r'D:\INDONERIS-DATAMINING\multimodal-hoax-detection\data\training\multimodal_splits',
    
    # Feature groups
    'feature_groups': {
        'text_only': {
            'features': ['title', 'text_content'],
            'modalities': ['text'],
            'description': 'Text unimodal'
        },
        'image_only': {
            'features': ['image_url'],
            'modalities': ['image'],
            'description': 'Image unimodal'
        },
        'text_image': {
            'features': ['title', 'text_content', 'image_url'],
            'modalities': ['text', 'image'],
            'description': 'Bimodal: Text + Image'
        },
        'text_audio': {
            'features': ['title', 'text_content', 'audio_path'],
            'modalities': ['text', 'audio'],
            'description': 'Bimodal: Text + Audio (YouTube only)'
        },
        'text_image_audio': {
            'features': ['title', 'text_content', 'image_url', 'audio_path'],
            'modalities': ['text', 'image', 'audio'],
            'description': 'Trimodal (YouTube only)'
        }
    }
}


# ============================================================================
# UTILITY FUNCTIONS
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
# STEP 1: MERGE IMAGE URLs KE DATASET GABUNGAN
# ============================================================================

def merge_image_urls():
    """Merge thumbnail/image_url dari data mentah ke dataset gabungan"""
    print_header("STEP 1: MERGE IMAGE URLs")
    
    # Load dataset gabungan
    print("\nLoading dataset gabungan...")
    df_combined = pd.read_csv(CONFIG['path_combined'])
    print(f"  Loaded: {len(df_combined):,} rows")
    print(f"  Columns: {df_combined.columns.tolist()}")
    
    # Load data mentah
    print("\nLoading data mentah...")
    df_tbh_raw = pd.read_csv(CONFIG['path_tbh_raw'])
    df_news_raw = pd.read_csv(CONFIG['path_news_raw'])
    print(f"  TBH raw: {len(df_tbh_raw):,} rows")
    print(f"  News raw: {len(df_news_raw):,} rows")
    
    # Merge TBH thumbnail
    print("\nMerging TBH thumbnail...")
    if 'thumbnail' in df_tbh_raw.columns and 'id' in df_tbh_raw.columns:
        # Select only id and thumbnail
        df_tbh_merge = df_tbh_raw[['id', 'thumbnail']].copy()
        
        df_combined = df_combined.merge(
            df_tbh_merge,
            on='id',
            how='left',
            suffixes=('', '_tbh_raw')
        )
        
        n_merged = df_combined['thumbnail'].notna().sum()
        print(f"  Merged: {n_merged:,} TBH records with thumbnail")
    else:
        print(f"  WARNING: 'thumbnail' or 'id' not found in TBH raw")
        df_combined['thumbnail'] = None
    
    # Merge News image_url
    print("\nMerging News image_url...")
    if 'image_url' in df_news_raw.columns and 'id' in df_news_raw.columns:
        # Select only id and image_url
        df_news_merge = df_news_raw[['id', 'image_url']].copy()
        
        df_combined = df_combined.merge(
            df_news_merge,
            on='id',
            how='left',
            suffixes=('', '_news_raw')
        )
        
        n_merged = df_combined['image_url'].notna().sum()
        print(f"  Merged: {n_merged:,} News records with image_url")
    else:
        print(f"  WARNING: 'image_url' or 'id' not found in News raw")
        if 'image_url' not in df_combined.columns:
            df_combined['image_url'] = None
    
    # Unify image columns
    print("\nUnifying image columns...")
    if 'thumbnail' in df_combined.columns and 'image_url' in df_combined.columns:
        # Combine: use image_url if exists, else use thumbnail
        df_combined['image_url'] = df_combined['image_url'].fillna(df_combined['thumbnail'])
        df_combined = df_combined.drop(columns=['thumbnail'], errors='ignore')
        print("  Unified 'thumbnail' and 'image_url' into 'image_url' column")
    elif 'thumbnail' in df_combined.columns:
        df_combined = df_combined.rename(columns={'thumbnail': 'image_url'})
        print("  Renamed 'thumbnail' to 'image_url'")
    
    # Summary
    print_subheader("SUMMARY MERGE")
    total_with_image = df_combined['image_url'].notna().sum()
    pct_with_image = total_with_image / len(df_combined) * 100
    print(f"\nTotal records with image_url: {total_with_image:,} / {len(df_combined):,} ({pct_with_image:.1f}%)")
    
    # Per dataset_origin
    if 'dataset_origin' in df_combined.columns:
        print("\nImage availability per dataset_origin:")
        for origin in df_combined['dataset_origin'].unique():
            subset = df_combined[df_combined['dataset_origin'] == origin]
            n_with_img = subset['image_url'].notna().sum()
            pct = n_with_img / len(subset) * 100 if len(subset) > 0 else 0
            print(f"  {origin:15s}: {n_with_img:4,} / {len(subset):4,} ({pct:5.1f}%)")
    
    return df_combined


# ============================================================================
# STEP 2: PROCESS YOUTUBE DATA
# ============================================================================

def process_youtube_data():
    """Load dan process YouTube data dengan thumbnail URL generation"""
    print_header("STEP 2: PROCESS YOUTUBE DATA")
    
    print("\nLoading YouTube pseudo-labeled data...")
    df_youtube = pd.read_csv(CONFIG['path_youtube'])
    print(f"  Loaded: {len(df_youtube):,} rows")
    print(f"  Columns: {df_youtube.columns.tolist()}")
    
    # Generate thumbnail URL dari video_id
    print("\nGenerating YouTube thumbnail URLs...")
    
    if 'video_id' in df_youtube.columns:
        df_youtube['image_url'] = df_youtube['video_id'].apply(
            lambda vid: f"https://i.ytimg.com/vi/{vid}/maxresdefault.jpg" 
            if pd.notna(vid) else None
        )
        n_generated = df_youtube['image_url'].notna().sum()
        print(f"  Generated: {n_generated:,} thumbnail URLs")
    else:
        print("  WARNING: 'video_id' column not found")
        df_youtube['image_url'] = None
    
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
    print(f"  With image_url: {df_youtube['image_url'].notna().sum():,}")
    print(f"  With audio_path: {df_youtube.get('audio_path', pd.Series()).notna().sum():,}")
    
    return df_youtube


# ============================================================================
# STEP 3: HARMONIZE DAN INTEGRATE
# ============================================================================

def harmonize_and_integrate(df_tbh_news, df_youtube):
    """Harmonize columns dan integrate datasets"""
    print_header("STEP 3: HARMONIZE & INTEGRATE")
    
    print("\nHarmonizing TBH+News...")
    
    # ========================================================================
    # TEXT COLUMNS
    # ========================================================================
    
    if 'text' in df_tbh_news.columns and 'text_content' not in df_tbh_news.columns:
        df_tbh_news['text_content'] = df_tbh_news['text']
    
    if 'text_clean' in df_tbh_news.columns and 'text_normalized' not in df_tbh_news.columns:
        df_tbh_news['text_normalized'] = df_tbh_news['text_clean']
    
    # ========================================================================
    # LABEL MAPPING
    # ========================================================================
    
    print("  Mapping labels...")
    
    if 'label_str' in df_tbh_news.columns:
        # Use label_str (hoax/valid)
        df_tbh_news['label'] = df_tbh_news['label_str']
        print("    Using 'label_str' column")
    elif 'label' in df_tbh_news.columns:
        # Convert numeric to string: 0 -> hoax, 1 -> valid
        df_tbh_news['label'] = df_tbh_news['label'].apply(
            lambda x: 'hoax' if x == 0 else 'valid'
        )
        print("    Converted numeric label: 0->hoax, 1->valid")
    else:
        # Fallback: use dataset_origin
        if 'dataset_origin' in df_tbh_news.columns:
            df_tbh_news['label'] = df_tbh_news['dataset_origin'].apply(
                lambda x: 'hoax' if 'hoax' in str(x).lower() or 'tbh' in str(x).lower()
                else 'valid'
            )
            print("    Generated label from dataset_origin")
    
    # ========================================================================
    # SAMPLE_ID GENERATION - DIFFERENTIATE TBH vs NEWS
    # ========================================================================
    
    print("  Generating sample_id...")
    
    if 'sample_id' not in df_tbh_news.columns:
        def generate_sample_id(row):
            """Generate sample_id dengan prefix TBH atau NEWS"""
            origin = str(row.get('dataset_origin', '')).lower()
            row_id = row.get('id', 0)
            
            if 'hoax' in origin or 'tbh' in origin:
                return f"TBH_{row_id}"
            elif 'news' in origin:
                return f"NEWS_{row_id}"
            else:
                return f"DATA_{row_id}"
        
        df_tbh_news['sample_id'] = df_tbh_news.apply(generate_sample_id, axis=1)
        
        # Show breakdown
        print("\n  Sample ID prefix breakdown:")
        for prefix in ['TBH_', 'NEWS_', 'DATA_']:
            count = df_tbh_news['sample_id'].str.startswith(prefix).sum()
            if count > 0:
                pct = count / len(df_tbh_news) * 100
                print(f"    {prefix}*: {count:,} ({pct:.1f}%)")
    
    # ========================================================================
    # DATA_SOURCE MAPPING
    # ========================================================================
    
    print("\n  Mapping data_source...")
    
    if 'data_source' not in df_tbh_news.columns:
        if 'dataset_origin' in df_tbh_news.columns:
            def map_data_source(origin):
                origin_lower = str(origin).lower()
                if 'hoax' in origin_lower or 'tbh' in origin_lower:
                    return 'original_hoax'
                elif 'news' in origin_lower:
                    return 'original_valid'
                else:
                    return 'original_unknown'
            
            df_tbh_news['data_source'] = df_tbh_news['dataset_origin'].apply(map_data_source)
            
            # Show breakdown
            print("  Data source breakdown:")
            for source, count in df_tbh_news['data_source'].value_counts().items():
                pct = count / len(df_tbh_news) * 100
                print(f"    {source:20s}: {count:,} ({pct:.1f}%)")
    
    # Add confidence and audio_path
    df_tbh_news['confidence'] = 1.0
    if 'audio_path' not in df_tbh_news.columns:
        df_tbh_news['audio_path'] = None
    
    print(f"\n  TBH+News harmonized: {len(df_tbh_news):,} rows, {len(df_tbh_news.columns)} columns")
    
    # ========================================================================
    # HARMONIZE YOUTUBE
    # ========================================================================
    
    print("\nHarmonizing YouTube...")
    
    if 'domain' not in df_youtube.columns:
        df_youtube['domain'] = df_youtube.get('channel', None)
    if 'date' not in df_youtube.columns:
        df_youtube['date'] = df_youtube.get('upload_date', None)
    if 'url' not in df_youtube.columns and 'video_id' in df_youtube.columns:
        df_youtube['url'] = 'https://youtube.com/watch?v=' + df_youtube['video_id'].fillna('')
    
    print(f"  YouTube harmonized: {len(df_youtube):,} rows, {len(df_youtube.columns)} columns")
    
    # ========================================================================
    # INTEGRATION
    # ========================================================================
    
    # Define common columns
    common_cols = [
        'sample_id', 'label', 'data_source', 'confidence',
        'title', 'text_content', 'text_normalized',
        'image_url', 'audio_path',
        'url', 'domain', 'date'
    ]
    
    # Add missing columns
    for col in common_cols:
        if col not in df_tbh_news.columns:
            df_tbh_news[col] = None
        if col not in df_youtube.columns:
            df_youtube[col] = None
    
    # Select and concat
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
    
    # ========================================================================
    # DETAILED SUMMARY
    # ========================================================================
    
    print_subheader("INTEGRATION SUMMARY")
    
    print(f"\nTotal samples: {len(df_integrated):,}")
    print(f"  TBH+News: {len(df_tbh_final):,}")
    print(f"  YouTube: {len(df_yt_final):,}")
    
    # Sample ID breakdown
    print(f"\nSample ID breakdown (by prefix):")
    for prefix in ['TBH_', 'NEWS_', 'YT_', 'DATA_']:
        count = df_integrated['sample_id'].str.startswith(prefix, na=False).sum()
        if count > 0:
            pct = count / len(df_integrated) * 100
            print(f"  {prefix}*: {count:,} ({pct:.1f}%)")
    
    # Label distribution
    if 'label' in df_integrated.columns:
        print(f"\nLabel distribution:")
        for label, count in df_integrated['label'].value_counts().items():
            pct = count / len(df_integrated) * 100
            print(f"  {label}: {count:,} ({pct:.1f}%)")
    
    # Data source distribution
    if 'data_source' in df_integrated.columns:
        print(f"\nData source distribution:")
        for source, count in df_integrated['data_source'].value_counts().items():
            pct = count / len(df_integrated) * 100
            print(f"  {source}: {count:,} ({pct:.1f}%)")
    
    # Cross-tabulation
    if 'label' in df_integrated.columns and 'data_source' in df_integrated.columns:
        print(f"\nCross-tabulation (Label x Data Source):")
        try:
            cross = pd.crosstab(
                df_integrated['data_source'],
                df_integrated['label'],
                margins=True
            )
            print(cross)
        except Exception as e:
            print(f"  Could not create crosstab: {e}")
    
    # Multimodal features
    print(f"\nMultimodal features availability:")
    print(f"  Text (title or text_content): {df_integrated[['title', 'text_content']].notna().any(axis=1).sum():,}")
    print(f"  Image (image_url): {df_integrated['image_url'].notna().sum():,}")
    print(f"  Audio (audio_path): {df_integrated['audio_path'].notna().sum():,}")
    
    return df_integrated


# ============================================================================
# STEP 4: EXPORT PER MODALITY
# ============================================================================

def export_multimodal_datasets(df_integrated):
    """Export datasets per modality configuration"""
    print_header("STEP 4: EXPORT PER MODALITY")
    
    os.makedirs(CONFIG['output_dir'], exist_ok=True)
    print(f"\nOutput directory: {CONFIG['output_dir']}")
    
    exported_files = {}
    config_summary = []
    
    for name, config in CONFIG['feature_groups'].items():
        print(f"\n{'-'*80}")
        print(f"Processing: {name.upper()}")
        print(f"  Required features: {', '.join(config['features'])}")
        
        # Filter samples with all required features
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
            print(f"  SKIP: No data available")
            continue
        
        # Data source breakdown
        if 'data_source' in df_modality.columns:
            print(f"\n  Data source breakdown:")
            for source, count in df_modality['data_source'].value_counts().items():
                pct = count / len(df_modality) * 100
                print(f"    {source:30s}: {count:5,} ({pct:5.1f}%)")
        
        # Sample ID prefix breakdown
        print(f"\n  Sample ID breakdown:")
        for prefix in ['TBH_', 'NEWS_', 'YT_']:
            count = df_modality['sample_id'].str.startswith(prefix, na=False).sum()
            if count > 0:
                pct = count / len(df_modality) * 100
                print(f"    {prefix}*: {count:,} ({pct:.1f}%)")
        
        # Export columns
        export_cols = ['sample_id', 'label', 'data_source', 'confidence', 'sample_weight']
        export_cols.extend(config['features'])
        export_cols.extend(['url', 'domain', 'date'])
        
        # Remove duplicates and filter existing
        export_cols = list(dict.fromkeys(export_cols))
        export_cols = [c for c in export_cols if c in df_modality.columns]
        
        df_export = df_modality[export_cols].copy()
        
        # Export to CSV
        output_file = os.path.join(CONFIG['output_dir'], f'{name}_dataset.csv')
        df_export.to_csv(output_file, index=False, encoding='utf-8')
        
        exported_files[name] = output_file
        
        # Statistics
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
    
    # Export summary
    if config_summary:
        df_summary = pd.DataFrame(config_summary)
        summary_file = os.path.join(CONFIG['output_dir'], 'training_configuration_summary.csv')
        df_summary.to_csv(summary_file, index=False)
        
        print_header("EXPORT SUMMARY")
        print(f"\nTotal configurations exported: {len(exported_files)}")
        
        print(f"\nFiles:")
        for idx, name in enumerate(exported_files.keys(), 1):
            print(f"  {idx}. {name}_dataset.csv")
        
        print(f"\nConfiguration table:")
        display_cols = ['experiment_name', 'n_samples', 'n_hoax', 'n_valid', 'n_tbh', 'n_news', 'n_youtube']
        print(df_summary[display_cols].to_string(index=False))
        
        print(f"\nSummary saved: {os.path.basename(summary_file)}")
    
    return exported_files, config_summary


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("="*80)
    print("INTEGRASI DATASET MULTIMODAL DENGAN IMAGE URL SUPPORT")
    print("Version 4.0 (Final - TBH/News differentiation fixed)")
    print("="*80)
    print(f"\nDate: 2025-11-14 15:53")
    
    try:
        # Step 1
        df_tbh_news = merge_image_urls()
        
        # Step 2
        df_youtube = process_youtube_data()
        
        # Step 3
        df_integrated = harmonize_and_integrate(df_tbh_news, df_youtube)
        
        # Step 4
        exported_files, summary = export_multimodal_datasets(df_integrated)
        
        print_header("SELESAI")
        print("\nIntegrasi dataset BERHASIL!")
        print(f"\nOutput: {CONFIG['output_dir']}")
        print(f"Files: {len(exported_files)} modality datasets + 1 summary")
        
        print("\nNext steps:")
        print("  1. Load dataset per modality")
        print("  2. Implement image loader from URL")
        print("  3. Train model dengan sample_weight")
        print("  4. Evaluate performance")
        
        return 0
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
