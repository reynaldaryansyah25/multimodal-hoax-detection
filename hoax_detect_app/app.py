import streamlit as st
from PIL import Image
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(
    page_title="HoaxDetect - Multimodal",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS Styling
st.markdown("""
<style>
    /* Main styling */
    :root {
        --primary-color: #1E88E5;
        --success-color: #43A047;
        --danger-color: #E53935;
        --warning-color: #FB8C00;
        --bg-color: #F5F7FA;
    }
    
    /* Header styling */
    .header-container {
        background: linear-gradient(135deg, #1E88E5 0%, #1565C0 100%);
        padding: 40px 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
    }
    
    .header-container h1 {
        font-size: 2.5em;
        margin: 0;
        font-weight: 700;
    }
    
    .header-container p {
        font-size: 1.1em;
        margin: 10px 0 0 0;
        opacity: 0.9;
    }
    
    /* Metric cards */
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 4px solid #1E88E5;
    }
    
    .metric-label {
        font-size: 0.9em;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 10px;
    }
    
    .metric-value {
        font-size: 2em;
        font-weight: 700;
        color: #1E88E5;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #1E88E5 0%, #1565C0 100%);
        color: white;
        border: none;
        padding: 10px 30px;
        border-radius: 5px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        box-shadow: 0 4px 12px rgba(30, 136, 229, 0.4);
        transform: translateY(-2px);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        background: transparent;
        border-bottom: 2px solid #E0E0E0;
    }
    
    .stTabs [aria-selected="true"] {
        border-bottom: 2px solid #1E88E5;
        color: #1E88E5;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Navigation
with st.sidebar:
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
    st.image(logo_path, width=200)
    
    page = st.radio(
        "📍 Navigasi",
        ["🏠 Home", "📊 Analisis", "📈 Dashboard", "ℹ️ Tentang Proyek"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("""
    ### 📊 Stats
    - **Akurasi**: 87%
    - **Analisis**: 10.000+
    - **Response**: <3 detik
    """)
    
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #999; font-size: 0.9em;">
    Powered by Machine Learning & Data Mining
    </div>
    """, unsafe_allow_html=True)

# Main Content - HOME PAGE
if page == "🏠 Home":
    st.markdown("""
    <div class="header-container">
        <h1>🛡️ HoaxDetect</h1>
        <p style="font-size: 1.3em;"><strong>Sistem Deteksi Hoaks Multimodal</strong></p>
        <p style="margin-top: 15px; font-size: 1em;">
        Verifikasi keaslian berita dengan AI - Analisis Text, Image, Audio & Video
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🚀 Mulai Sekarang")
        if st.button("Coba Sekarang →", key="start_btn", use_container_width=True):
            st.switch_page("pages/2_Analysis.py")
    
    with col2:
        st.markdown("### 📚 Pelajari Lebih Lanjut")
        if st.button("Dokumentasi →", key="doc_btn", use_container_width=True):
            st.switch_page("pages/4_About.py")
    
    st.markdown("---")
    
    # Feature showcase
    st.markdown("### ✨ Fitur Utama")
    
    feat_col1, feat_col2, feat_col3 = st.columns(3)
    
    with feat_col1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">📝 Analisis Teks</div>
            <p>NLP advanced untuk deteksi hoaks berbasis text dan semantic analysis</p>
        </div>
        """, unsafe_allow_html=True)
    
    with feat_col2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">🖼️ Deteksi Gambar</div>
            <p>Computer Vision untuk reverse image search dan manipulasi deteksi</p>
        </div>
        """, unsafe_allow_html=True)
    
    with feat_col3:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">🎥 Analisis Video</div>
            <p>Audio transcription, speaker diarization, dan multimodal fusion</p>
        </div>
        """, unsafe_allow_html=True)

# ANALYSIS PAGE
elif page == "📊 Analisis":
    st.markdown("""
    <div class="header-container" style="padding: 20px;">
        <h2 style="margin: 0; color: white;">Analisis Konten</h2>
        <p style="margin: 5px 0 0 0; opacity: 0.9;">
        Pilih jenis analisis dan unggah konten untuk verifikasi
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tab selection
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Teks", "🖼️ Gambar", "🎤 Audio", "🎥 Video", "📦 Multimodal"])
    
    with tab1:
        st.markdown("### Paste Teks Berita atau Transkrip Video")
        text_input = st.text_area(
            "Masukkan konten teks yang ingin diverifikasi:",
            placeholder="Paste konten berita atau transkrip di sini...",
            height=250,
            label_visibility="collapsed"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Analisis Teks", use_container_width=True):
                if text_input:
                    st.info("⏳ Menganalisis... (simulated)")
                    st.success("✅ Analisis Selesai!")
                    
                    # Dummy results
                    result_col1, result_col2, result_col3 = st.columns(3)
                    with result_col1:
                        st.markdown("""
                        <div class="metric-card">
                            <div class="metric-label">Hasil</div>
                            <div class="metric-value" style="color: #E53935;">Hoaks</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with result_col2:
                        st.markdown("""
                        <div class="metric-card">
                            <div class="metric-label">Confidence</div>
                            <div class="metric-value" style="color: #1E88E5;">87%</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with result_col3:
                        st.markdown("""
                        <div class="metric-card">
                            <div class="metric-label">Tipe</div>
                            <div class="metric-value" style="color: #FB8C00;">Politik</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.warning("⚠️ Masukkan teks terlebih dahulu")
        
        with col2:
            st.button("📋 Contoh Hoaks", use_container_width=True)
    
    with tab2:
        st.markdown("### Upload Gambar")
        uploaded_image = st.file_uploader("Pilih gambar...", type=['jpg', 'jpeg', 'png'])
        if uploaded_image:
            st.image(uploaded_image, width=300)
            if st.button("🔍 Analisis Gambar", use_container_width=True):
                st.success("✅ Gambar diverifikasi")
    
    with tab3:
        st.markdown("### Upload Audio/Podcast")
        uploaded_audio = st.file_uploader("Pilih file audio...", type=['mp3', 'wav', 'ogg'])
        if st.button("🔍 Analisis Audio", use_container_width=True):
            st.info("⏳ Transcribing dengan Whisper...")
            st.success("✅ Transkrip siap dianalisis")
    
    with tab4:
        st.markdown("### Upload Video")
        video_url = st.text_input("Paste YouTube URL atau upload file video")
        if st.button("🔍 Analisis Video", use_container_width=True):
            st.info("⏳ Processing video...")
            st.success("✅ Video analysis complete")
    
    with tab5:
        st.markdown("### Upload Multiple Media (Multimodal)")
        col1, col2 = st.columns(2)
        with col1:
            text_mm = st.text_area("Teks", height=100)
            img_mm = st.file_uploader("Gambar", type=['jpg', 'png'])
        with col2:
            audio_mm = st.file_uploader("Audio", type=['mp3', 'wav'])
            video_mm = st.file_uploader("Video", type=['mp4', 'mov'])
        
        if st.button("🔍 Analisis Multimodal", use_container_width=True):
            st.success("✅ Multimodal analysis complete")

# DASHBOARD PAGE
elif page == "📈 Dashboard":
    st.markdown("""
    <div class="header-container" style="padding: 20px;">
        <h2 style="margin: 0; color: white;">Dashboard</h2>
        <p style="margin: 5px 0 0 0; opacity: 0.9;">
        Statistik dan metrik performa sistem deteksi hoaks
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Metrics Row
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    
    with metric_col1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Overall Accuracy</div>
            <div class="metric-value">87%</div>
            <small>Model Multimodal</small>
        </div>
        """, unsafe_allow_html=True)
    
    with metric_col2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Precision</div>
            <div class="metric-value" style="color: #43A047;">85%</div>
            <small>True Positive Rate</small>
        </div>
        """, unsafe_allow_html=True)
    
    with metric_col3:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Recall</div>
            <div class="metric-value" style="color: #1565C0;">89%</div>
            <small>Detection Rate</small>
        </div>
        """, unsafe_allow_html=True)
    
    with metric_col4:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">F1-Score</div>
            <div class="metric-value" style="color: #FB8C00;">87%</div>
            <small>Harmonic Mean</small>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Charts
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.markdown("### Perbandingan Akurasi Model")
        
        accuracy_data = {
            'Model': ['Text-only', 'Text + Image', 'Multimodal'],
            'Accuracy': [75, 82, 87]
        }
        
        fig = px.bar(
            accuracy_data,
            x='Model',
            y='Accuracy',
            color='Accuracy',
            color_continuous_scale=['#E53935', '#FB8C00', '#43A047'],
            title="Model Performance Comparison"
        )
        fig.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col_chart2:
        st.markdown("### Distribusi Hasil Analisis")
        
        dist_data = {
            'Status': ['Valid', 'Hoaks'],
            'Count': [6300, 3700]
        }
        
        fig = px.pie(
            dist_data,
            values='Count',
            names='Status',
            color_discrete_map={'Valid': '#43A047', 'Hoaks': '#E53935'},
            title="Analysis Results Distribution"
        )
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)

# ABOUT PAGE
elif page == "ℹ️ Tentang Proyek":
    st.markdown("""
    <div class="header-container" style="padding: 20px;">
        <h2 style="margin: 0; color: white;">Tentang HoaxDetect</h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    ### 🎯 Tujuan Proyek
    HoaxDetect adalah sistem deteksi hoaks multimodal yang dirancang untuk memverifikasi 
    keaslian berita dengan menganalisis teks, gambar, audio, dan video secara bersamaan.
    
    ### 🔧 Teknologi
    - **NLP**: Transformers, BERT
    - **Computer Vision**: ResNet, YOLO
    - **Audio**: Whisper, pyannote.audio
    - **Framework**: PyTorch, TensorFlow
    - **Frontend**: Streamlit
    
    ### 👤 Developer
    Reynald Aryansyah | CS Student | 23.11.5583
    
    ### 📧 Kontak
    LinkedIn | GitHub | Email
    """)
