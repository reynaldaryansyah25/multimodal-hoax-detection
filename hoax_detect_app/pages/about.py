import streamlit as st
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.config import apply_custom_css

apply_custom_css()

st.set_page_config(
    page_title="HoaxDetect - About",
    page_icon="ℹ️",
    layout="wide"
)

st.markdown("""
<div class="header-container" style="padding: 20px;">
    <h2 style="margin: 0; color: white;">Tentang HoaxDetect</h2>
</div>
""", unsafe_allow_html=True)

# Project Overview
st.markdown("### 🎯 Tujuan Proyek")
st.markdown("""
HoaxDetect adalah sistem deteksi hoaks **multimodal** yang dirancang untuk memverifikasi 
keaslian berita dan informasi dengan menganalisis **teks, gambar, audio, dan video** secara bersamaan.

Sistem ini memanfaatkan **Machine Learning dan Data Mining** untuk mengidentifikasi pola-pola 
hoaks dan misinformasi di media sosial dan platform online.
""")

st.markdown("---")

# Technology Stack
st.markdown("### 🔧 Teknologi yang Digunakan")

tech_col1, tech_col2, tech_col3 = st.columns(3)

with tech_col1:
    st.markdown("""
    #### 🧠 Deep Learning
    - **PyTorch** - Neural networks
    - **Transformers** - BERT, RoBERTa
    - **TensorFlow** - Backup framework
    """)

with tech_col2:
    st.markdown("""
    #### 📊 Data Processing
    - **Pandas** - Data manipulation
    - **NumPy** - Numerical computing
    - **Scikit-learn** - ML algorithms
    """)

with tech_col3:
    st.markdown("""
    #### 🎯 NLP & Vision
    - **Whisper** - Audio transcription
    - **pyannote.audio** - Speaker diarization
    - **OpenCV** - Computer vision
    """)

st.markdown("---")

# Frontend & Deployment
st.markdown("### 🚀 Frontend & Deployment")

frontend_data = {
    'Komponen': ['Frontend Framework', 'Styling', 'Charts', 'Deployment'],
    'Teknologi': ['Streamlit', 'Custom CSS', 'Plotly', 'Hugging Face Spaces / Railway']
}

st.table(frontend_data)

st.markdown("---")

# Dataset Information
st.markdown("### 📚 Dataset")

st.markdown("""
- **Ukuran Dataset**: 10,000+ samples
- **Sumber Data**: Indonesian news, social media, political content
- **Label**: Binary classification (Hoaks / Valid)
- **Periode**: Prabowo-Gibran Administration (2024-2025)
- **Format Data**: Text, Image, Audio, Video (Multimodal)
""")

st.markdown("---")

# Model Performance
st.markdown("### 📊 Performa Model")

performance_data = {
    'Model': ['Text-only', 'Text + Image', 'Multimodal'],
    'Accuracy': ['75%', '82%', '87%'],
    'Precision': ['73%', '80%', '85%'],
    'Recall': ['78%', '85%', '89%'],
    'F1-Score': ['75%', '82%', '87%']
}

st.dataframe(performance_data, use_container_width=True)

st.markdown("---")

# Developer Info
st.markdown("### 👤 Developer")

dev_col1, dev_col2 = st.columns(2)

with dev_col1:
    st.markdown("""
    **Reynald Aryansyah**
    
    - 🎓 Computer Science Student (Semester 5)
    - 🆔 Student ID: 23.11.5583
    - 📧 reynald@example.com
    - 💼 Portfolio: github.com/reynald
    """)

with dev_col2:
    st.markdown("""
    **Research Interests**
    
    - Machine Learning & AI
    - Natural Language Processing (NLP)
    - Indonesian Language Technology
    - Misinformation Detection
    - Multimodal Learning
    """)

st.markdown("---")

# Contact & Links
st.markdown("### 🔗 Connect")

col_links1, col_links2, col_links3 = st.columns(3)

with col_links1:
    if st.button("🔗 GitHub Profile", use_container_width=True):
        st.info("GitHub: github.com/reynald")

with col_links2:
    if st.button("💼 LinkedIn", use_container_width=True):
        st.info("LinkedIn: linkedin.com/in/reynald")

with col_links3:
    if st.button("📧 Email", use_container_width=True):
        st.info("Email: reynald@example.com")

st.markdown("---")

# Disclaimer
st.warning("""
### ⚠️ Disclaimer

Sistem HoaxDetect adalah tools bantu untuk verifikasi informasi. 
Hasil analisis tidak 100% akurat dan harus dikombinasikan dengan fact-checking manual. 
Selalu lakukan cross-referencing dengan multiple reliable sources.
""")

# Footer
st.markdown("""
<div style="text-align: center; color: #999; font-size: 0.9em; margin-top: 30px;">
    <p>🔬 Powered by Machine Learning & Data Mining</p>
    <p>Last updated: November 2025</p>
</div>
""", unsafe_allow_html=True)
