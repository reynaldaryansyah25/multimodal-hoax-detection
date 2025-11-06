import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from utils.config import apply_custom_css
from PIL import Image
import pandas as pd
import plotly.graph_objects as go

apply_custom_css()

st.set_page_config(
    page_title="HoaxDetect - Analysis",
    page_icon="📊",
    layout="wide"
)

# Custom CSS untuk tab yang lebih bagus
st.markdown("""
<style>
    .result-card-valid {
        background: linear-gradient(135deg, #43A047 0%, #2E7D32 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(67, 160, 71, 0.3);
    }
    
    .result-card-hoax {
        background: linear-gradient(135deg, #E53935 0%, #C62828 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(229, 57, 53, 0.3);
    }
    
    .result-card-warning {
        background: linear-gradient(135deg, #FB8C00 0%, #E65100 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(251, 140, 0, 0.3);
    }
    
    .result-item {
        background: #F5F7FA;
        padding: 15px;
        border-radius: 8px;
        margin: 8px 0;
        border-left: 4px solid #1E88E5;
    }
    
    .confidence-bar {
        background: #E0E0E0;
        border-radius: 10px;
        height: 30px;
        margin: 10px 0;
        position: relative;
        overflow: hidden;
    }
    
    .confidence-fill {
        background: linear-gradient(90deg, #1E88E5, #1565C0);
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header-container" style="padding: 25px;">
    <h2 style="margin: 0; color: white;">🔍 Analisis Konten</h2>
    <p style="margin: 10px 0 0 0; opacity: 0.95; font-size: 1.05em;">
    Verifikasi keaslian berita dengan AI multimodal - Teks, Gambar, Audio & Video
    </p>
</div>
""", unsafe_allow_html=True)

# Tab selection dengan icons
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📝 Analisis Teks",
    "🖼️ Analisis Gambar",
    "🎤 Analisis Audio",
    "🎥 Analisis Video",
    "🔀 Multimodal Fusion"
])

# ===== TAB 1: TEXT ANALYSIS =====
with tab1:
    st.markdown("### 📝 Paste Teks Berita atau Transkrip Video")
    
    col_text_info = st.columns(1)[0]
    with col_text_info:
        st.info("💡 Tip: Paste konten berita, postingan media sosial, atau transkrip video untuk dianalisis")
    
    text_input = st.text_area(
        "Masukkan konten teks:",
        placeholder="Paste konten berita atau transkrip di sini...",
        height=200,
        label_visibility="collapsed"
    )
    
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    
    with col_btn1:
        if st.button("🚀 Analisis Sekarang", use_container_width=True, key="analyze_text", help="Jalankan model deteksi hoaks"):
            if text_input.strip():
                with st.spinner("⏳ Menganalisis teks dengan NLP models..."):
                    import time
                    time.sleep(1)  # Simulasi loading
                    
                    # Model results (simulasi - nanti ganti dengan actual model)
                    result = {
                        "status": "Hoaks 🚨",
                        "confidence": 0.87,
                        "category": "Politik",
                        "indicators": [
                            "Klaim tanpa sumber kredibel",
                            "Mengandung emoticon misleading",
                            "Pattern matching hoaks terdeteksi"
                        ],
                        "model_scores": {
                            "BERT_NLP": 0.89,
                            "TF_IDF": 0.85,
                            "SVM": 0.87,
                            "Ensemble": 0.87
                        },
                        "sentiment": "Negatif",
                        "text_length": len(text_input),
                        "word_count": len(text_input.split())
                    }
                
                st.success("✅ Analisis Selesai!", icon="✅")
                
                st.markdown("---")
                
                # Main Result Card
                status_color = "result-card-hoax" if "Hoaks" in result["status"] else "result-card-valid"
                st.markdown(f"""
                <div class="{status_color}">
                    <h2 style="margin: 0; font-size: 2.5em;">{result["status"]}</h2>
                    <p style="margin: 10px 0 0 0; font-size: 1.1em; opacity: 0.95;">
                    Kepercayaan: {result['confidence']*100:.1f}%
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("---")
                
                # Key Metrics
                col_metric1, col_metric2, col_metric3 = st.columns(3)
                
                with col_metric1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">🏷️ Kategori</div>
                        <div class="metric-value" style="color: #FB8C00; font-size: 1.8em;">{result['category']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_metric2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">😊 Sentimen</div>
                        <div class="metric-value" style="color: #E53935; font-size: 1.8em;">{result['sentiment']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_metric3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">📊 Ukuran</div>
                        <div class="metric-value" style="color: #1E88E5; font-size: 1.8em;">{result['word_count']} kata</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("---")
                
                # Model Scores Comparison
                st.markdown("### 🤖 Model Performance Scores")
                
                scores_df = pd.DataFrame(list(result['model_scores'].items()), columns=['Model', 'Score'])
                
                fig = go.Figure()
                colors = ['#43A047' if score >= 0.85 else '#FB8C00' if score >= 0.75 else '#E53935' 
                         for score in scores_df['Score']]
                
                fig.add_trace(go.Bar(
                    y=scores_df['Model'],
                    x=scores_df['Score'],
                    orientation='h',
                    marker=dict(color=colors),
                    text=[f"{score:.2f}" for score in scores_df['Score']],
                    textposition='auto',
                ))
                
                fig.update_layout(
                    height=300,
                    xaxis_title="Confidence Score",
                    yaxis_title="",
                    showlegend=False,
                    margin=dict(l=0, r=0, t=0, b=0)
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("---")
                
                # Red Flags / Indicators
                st.markdown("### 🚩 Indikator Terdeteksi")
                
                for idx, indicator in enumerate(result["indicators"], 1):
                    st.markdown(f"""
                    <div class="result-item">
                        <strong>⚠️ Indikator {idx}:</strong> {indicator}
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("---")
                
                # Detailed Analysis
                st.markdown("### 📋 Statistik Teks")
                
                stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
                
                with stats_col1:
                    st.metric("Total Karakter", f"{result['text_length']:,}")
                
                with stats_col2:
                    st.metric("Total Kata", f"{result['word_count']:,}")
                
                with stats_col3:
                    avg_word_length = result['text_length'] / max(result['word_count'], 1)
                    st.metric("Rata-rata Panjang Kata", f"{avg_word_length:.1f}")
                
                with stats_col4:
                    keyword_count = 5  # simulasi
                    st.metric("Keyword Suspisious", keyword_count)
                
                st.markdown("---")
                
                # Action buttons
                col_action1, col_action2, col_action3 = st.columns(3)
                
                with col_action1:
                    if st.button("💾 Simpan Hasil", use_container_width=True):
                        st.success("✅ Hasil disimpan ke history")
                
                with col_action2:
                    if st.button("📥 Export JSON", use_container_width=True):
                        import json
                        st.download_button(
                            label="Download JSON",
                            data=json.dumps(result, indent=2),
                            file_name="analysis_result.json",
                            mime="application/json"
                        )
                
                with col_action3:
                    if st.button("🔄 Analisis Lagi", use_container_width=True):
                        st.rerun()
            else:
                st.warning("⚠️ Silakan masukkan teks terlebih dahulu")
    
    with col_btn2:
        if st.button("📋 Lihat Contoh", use_container_width=True, key="example_text"):
            example_text = """HOAKS TERDETEKSI: Presiden Akan Menghapus Pajak Untuk Semua Rakyat Mulai Bulan Depan!

Sumber tidak jelas, dibagikan tanpa fakta pendukung, dan menggunakan claims yang berlebihan."""
            st.info(example_text)
    
    with col_btn3:
        if st.button("📚 Bantuan", use_container_width=True, key="help_text"):
            st.markdown("""
            ### Panduan Penggunaan
            1. **Paste konten** - Tempel berita atau transkrip
            2. **Klik Analisis** - Sistem akan memproses dengan AI
            3. **Review hasil** - Lihat score dari berbagai model
            4. **Simpan** - Store hasil untuk tracking
            """)

# ===== TAB 2: IMAGE ANALYSIS =====
with tab2:
    st.markdown("### 🖼️ Upload & Analisis Gambar")
    
    col_img_info = st.columns(1)[0]
    with col_img_info:
        st.info("💡 Tip: Upload gambar untuk deteksi manipulasi, reverse image search, & verifikasi konteks")
    
    uploaded_image = st.file_uploader(
        "Pilih gambar:",
        type=['jpg', 'jpeg', 'png'],
        label_visibility="collapsed"
    )
    
    if uploaded_image:
        image = Image.open(uploaded_image)
        
        col_img_preview, col_img_info = st.columns([1, 1])
        
        with col_img_preview:
            st.image(image, use_column_width=True, caption="Preview Gambar")
        
        with col_img_info:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-label">File Info</div>
                <p><strong>Nama:</strong> """ + uploaded_image.name + """</p>
                <p><strong>Ukuran:</strong> """ + f"{uploaded_image.size / 1024:.2f} KB" + """</p>
                <p><strong>Format:</strong> """ + uploaded_image.type + """</p>
            </div>
            """, unsafe_allow_html=True)
        
        if st.button("🚀 Analisis Gambar", use_container_width=True, key="analyze_image"):
            with st.spinner("⏳ Menganalisis gambar..."):
                import time
                time.sleep(1)
                
                result = {
                    "status": "Valid ✅",
                    "confidence": 0.92,
                    "is_manipulated": False,
                    "manipulation_score": 0.08,
                    "reverse_search": "Gambar ditemukan di 5+ sumber kredibel",
                    "context_verified": True,
                    "metadata": {
                        "filename": uploaded_image.name,
                        "size_kb": f"{uploaded_image.size / 1024:.2f}",
                        "format": uploaded_image.type,
                        "dimensions": f"{image.width}x{image.height}px"
                    }
                }
            
            st.success("✅ Analisis Selesai!")
            
            st.markdown("---")
            
            # Main Result
            status_color = "result-card-valid" if not result["is_manipulated"] else "result-card-hoax"
            st.markdown(f"""
            <div class="{status_color}">
                <h2 style="margin: 0; font-size: 2.5em;">{result["status"]}</h2>
                <p style="margin: 10px 0 0 0;">Tingkat Kepercayaan: {result['confidence']*100:.1f}%</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            col_img_m1, col_img_m2, col_img_m3 = st.columns(3)
            
            with col_img_m1:
                manip_text = "Asli 🎯" if not result["is_manipulated"] else "Termanipulasi ⚠️"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Status Manipulasi</div>
                    <div style="font-size: 1.5em; color: #43A047;">{manip_text}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_img_m2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Skor Manipulasi</div>
                    <div style="font-size: 1.5em; color: #1E88E5;">{result['manipulation_score']*100:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_img_m3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Reverse Search</div>
                    <div style="font-size: 1.2em; color: #FB8C00;">5+ Matches</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("### 📊 Metadata Gambar")
            st.json(result["metadata"])

# ===== TAB 3: AUDIO ANALYSIS =====
with tab3:
    st.markdown("### 🎤 Upload & Analisis Audio")
    
    st.info("💡 Tip: Upload audio untuk transkripsi, speaker diarization, & deteksi deepfake")
    
    uploaded_audio = st.file_uploader(
        "Pilih file audio:",
        type=['mp3', 'wav', 'ogg', 'm4a'],
        label_visibility="collapsed"
    )
    
    if uploaded_audio:
        st.audio(uploaded_audio)
        
        col_audio1, col_audio2 = st.columns(2)
        
        with col_audio1:
            if st.button("🎙️ Transkripsi (Whisper)", use_container_width=True, key="transcribe_audio"):
                with st.spinner("⏳ Transcribing audio..."):
                    import time
                    time.sleep(2)
                    
                    transcript = """[00:00] Assalamualaikum, selamat pagi. 
[00:05] Saya ingin berbagi informasi penting tentang kebijakan terbaru.
[00:15] Presiden akan mengumumkan keputusan besar minggu depan.
[00:30] Ini adalah kesempatan untuk semua rakyat Indonesia."""
                    
                    st.session_state.transcript = transcript
                    st.success("✅ Transkripsi berhasil!")
                
                st.text_area("Hasil Transkrip:", value=transcript, height=150, disabled=True)
        
        with col_audio2:
            if st.button("👥 Speaker Diarization", use_container_width=True, key="diarize_audio"):
                with st.spinner("⏳ Detecting speakers..."):
                    import time
                    time.sleep(1.5)
                    st.success("✅ Diarization complete!")
                
                st.markdown("""
                **Speaker Detected:**
                - Speaker 1: 75% (Main speaker)
                - Speaker 2: 25% (Background)
                """)

# ===== TAB 4: VIDEO ANALYSIS =====
with tab4:
    st.markdown("### 🎥 Upload & Analisis Video")
    
    st.info("💡 Tip: Upload video YouTube atau file untuk analisis multimodal lengkap")
    
    col_video1, col_video2 = st.columns(2)
    
    with col_video1:
        video_url = st.text_input(
            "URL YouTube:",
            placeholder="https://www.youtube.com/watch?v=...",
        )
    
    with col_video2:
        uploaded_video = st.file_uploader(
            "Atau upload file video:",
            type=['mp4', 'mov', 'avi'],
        )
    
    if st.button("🚀 Analisis Video Lengkap", use_container_width=True, key="analyze_video"):
        with st.spinner("⏳ Processing video..."):
            import time
            
            steps = [
                ("📥 Downloading video", 0.2),
                ("🎬 Extracting frames", 0.4),
                ("🎙️ Transcribing audio", 0.7),
                ("🔍 Analyzing multimodal", 1.0)
            ]
            
            progress_bar = st.progress(0)
            
            for step_text, progress in steps:
                st.info(step_text)
                progress_bar.progress(progress)
                time.sleep(0.5)
        
        st.success("✅ Video analysis complete!")
        
        st.markdown("---")
        
        col_video_res1, col_video_res2 = st.columns(2)
        
        with col_video_res1:
            st.markdown("""
            <div class="result-card-hoax">
                <h3 style="margin: 0;">🚨 Hoaks Terdeteksi</h3>
                <p style="margin: 10px 0 0 0; font-size: 1.2em;">Confidence: 78%</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col_video_res2:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-label">Duration</div>
                <p>12:45</p>
                <div class="metric-label">Frames Analyzed</div>
                <p>450 frames</p>
            </div>
            """, unsafe_allow_html=True)

# ===== TAB 5: MULTIMODAL FUSION =====
with tab5:
    st.markdown("### 🔀 Fusion Multimodal (Text + Image + Audio + Video)")
    
    st.info("💡 Tip: Kombinasikan semua media untuk hasil analisis paling akurat")
    
    col_mm1, col_mm2 = st.columns(2)
    
    with col_mm1:
        st.markdown("#### Input Media")
        text_mm = st.text_area("📝 Teks:", height=80, key="text_mm")
        img_mm = st.file_uploader("🖼️ Gambar:", type=['jpg', 'png'], key="img_mm")
    
    with col_mm2:
        st.markdown("#### Input Media (lanjutan)")
        audio_mm = st.file_uploader("🎤 Audio:", type=['mp3', 'wav'], key="audio_mm")
        video_mm = st.file_uploader("🎥 Video:", type=['mp4', 'mov'], key="video_mm")
    
    if img_mm or audio_mm:
        st.markdown("---")
        col_preview1, col_preview2 = st.columns(2)
        with col_preview1:
            if img_mm:
                st.image(Image.open(img_mm), width=200)
        with col_preview2:
            if audio_mm:
                st.audio(audio_mm)
    
    if st.button("🚀 Fusion & Analisis", use_container_width=True, key="analyze_multimodal"):
        input_count = sum([bool(x) for x in [text_mm, img_mm, audio_mm, video_mm]])
        
        if input_count > 0:
            with st.spinner(f"⏳ Fusing {input_count} modalities..."):
                import time
                time.sleep(2)
            
            st.success("✅ Multimodal analysis complete!")
            
            st.markdown("---")
            
            # Individual results
            col_fusion1, col_fusion2, col_fusion3, col_fusion4 = st.columns(4)
            
            results_map = [
                (col_fusion1, "Teks", "Valid", "#43A047"),
                (col_fusion2, "Gambar", "Valid", "#43A047"),
                (col_fusion3, "Audio", "Hoaks", "#E53935"),
                (col_fusion4, "Video", "Undecided", "#FB8C00")
            ]
            
            for col, media, status, color in results_map[:input_count]:
                with col:
                    emoji = "✅" if "Valid" in status else "🚨" if "Hoaks" in status else "❓"
                    st.markdown(f"""
                    <div class="metric-card" style="border-left: 4px solid {color};">
                        <div class="metric-label">{media}</div>
                        <p>{emoji} {status}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Fusion result
            fusion_col1, fusion_col2 = st.columns(2)
            
            with fusion_col1:
                st.markdown("""
                <div class="result-card-hoax">
                    <h2 style="margin: 0;">🚨 HOAKS</h2>
                    <p style="margin: 10px 0 0 0;">Fusion Confidence: 82%</p>
                </div>
                """, unsafe_allow_html=True)
            
            with fusion_col2:
                st.markdown("""
                <div class="metric-card">
                    <div class="metric-label">Fusion Method</div>
                    <p>Late Fusion + Attention Mechanism</p>
                    <div class="metric-label">Processing Time</div>
                    <p>2.3 seconds</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("⚠️ Upload minimal 1 media untuk fusion")
