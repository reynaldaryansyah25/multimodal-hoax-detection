import streamlit as st
from models.audio_handler import AudioHandler
import os

@st.cache_resource
def get_audio_handler():
    return AudioHandler()

def show():
    st.subheader("Deteksi Keaslian Suara (Audio Deepfake)")
    st.caption("Menggunakan Model: **Wav2Vec 2.0**")
    try:
        handler = get_audio_handler()
    except Exception as e:
        st.error(f"Gagal inisialisasi Audio Handler: {e}")
        return
    uploaded_file = st.file_uploader("Upload File Audio (WAV/MP3)", type=["wav", "mp3", "flac"])
    if uploaded_file is not None:
        st.audio(uploaded_file, format='audio/wav')
        if st.button('Analisis Suara', type="primary", use_container_width=True):
            with st.spinner('Mendengarkan pola suara...'):
                temp_path = "temp_audio_upload.wav"
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                label, score = handler.predict(temp_path)
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                st.divider()
                if "Error" in label:
                    st.error(label)
                elif "Real" in label: 
                    st.success(f"SUARA ASLI (REAL)")
                    st.metric("Confidence", f"{score:.2f}%")
                    st.progress(int(score))
                else:
                    st.error(f"SUARA PALSU (FAKE/AI)")
                    st.metric("Confidence", f"{score:.2f}%")
                    st.progress(int(score))