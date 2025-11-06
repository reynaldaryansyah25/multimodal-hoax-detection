import streamlit as st
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.config import apply_custom_css

st.set_page_config(
    page_title="HoaxDetect - Home",
    page_icon="🛡️",
    layout="wide"
)

# Header
st.markdown("""
<div class="header-container">
    <h1>🛡️ HoaxDetect</h1>
    <p style="font-size: 1.3em;"><strong>Sistem Deteksi Hoaks Multimodal</strong></p>
    <p style="margin-top: 15px; font-size: 1em;">
    Verifikasi keaslian berita dengan AI - Analisis Text, Image, Audio & Video
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Call to action
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 🚀 Mulai Analisis")
    if st.button("Buka Analisis →", key="analysis_btn", use_container_width=True):
        st.switch_page("pages/2_Analysis.py")

with col2:
    st.markdown("### 📊 Lihat Dashboard")
    if st.button("Dashboard →", key="dashboard_btn", use_container_width=True):
        st.switch_page("pages/3_Dashboard.py")

with col3:
    st.markdown("### ℹ️ Tentang Proyek")
    if st.button("Selengkapnya →", key="about_btn", use_container_width=True):
        st.switch_page("pages/4_About.py")

st.markdown("---")

# Features Section
st.markdown("### ✨ Fitur Utama")

feat_col1, feat_col2, feat_col3 = st.columns(3)

with feat_col1:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-label">📝 Analisis Teks</div>
        <p>NLP advanced untuk deteksi hoaks berbasis text semantic dan pattern analysis</p>
    </div>
    """, unsafe_allow_html=True)

with feat_col2:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-label">🖼️ Deteksi Gambar</div>
        <p>Computer Vision untuk reverse image search, metadata extraction & manipulasi deteksi</p>
    </div>
    """, unsafe_allow_html=True)

with feat_col3:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-label">🎥 Analisis Video</div>
        <p>Audio transcription, speaker diarization, dan multimodal fusion analysis</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Stats Overview
st.markdown("### 📊 Quick Stats")

stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)

with stats_col1:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-label">Akurasi</div>
        <div class="metric-value">87%</div>
    </div>
    """, unsafe_allow_html=True)

with stats_col2:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-label">Dataset</div>
        <div class="metric-value">10K+</div>
    </div>
    """, unsafe_allow_html=True)

with stats_col3:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-label">Response Time</div>
        <div class="metric-value"><3s</div>
    </div>
    """, unsafe_allow_html=True)

with stats_col4:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-label">Models</div>
        <div class="metric-value">4x</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Footer
st.markdown("""
<div style="text-align: center; color: #999; font-size: 0.9em; margin-top: 30px;">
    <p>🔬 Powered by Machine Learning & Data Mining</p>
    <p>Reynald Aryansyah | Computer Science Student | 23.11.5583</p>
</div>
""", unsafe_allow_html=True)
