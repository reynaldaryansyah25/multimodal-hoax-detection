import streamlit as st
from models.text_handler import TextHandler

@st.cache_resource
def get_text_handler():
    return TextHandler()
def show():
    st.subheader("Masukkan Judul Berita")
    try:
        handler = get_text_handler()
    except Exception as e:
        st.error(f"Gagal inisialisasi handler teks: {e}")
        return
    text_input = st.text_area("Masukkan Judul Berita:", height=150, placeholder="Contoh: Beredar kabar bahwa...")
    if st.button("Analisis Judul", type="primary"):
        if not text_input.strip():
            st.warning("Mohon isi teks terlebih dahulu.")
        else:
            with st.spinner('Menganalisis pola bahasa...'):
                label, score = handler.predict(text_input)
                
                st.divider()
                if label == "valid":
                    st.success(f"Hasil: VALID")
                    st.metric("Confidence", f"{score:.2f}%")
                elif label == "hoax":
                    st.error(f"Hasil: HOAX")
                    st.metric("Confidence", f"{score:.2f}%")
                else:
                    st.error("Gagal memproses teks. Cek apakah model/folder assets sudah benar.")