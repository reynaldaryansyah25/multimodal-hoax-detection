import streamlit as st
from models.image_handler import ImageHandler

@st.cache_resource
def get_image_handler():
    return ImageHandler()

def show():
    st.subheader("Deteksi Manipulasi Gambar")
    st.caption("Menggunakan Model: **MobileNet V3** (Ringan & Cepat)")
    try:
        handler = get_image_handler()
    except Exception as e:
        st.error(f"Gagal inisialisasi sistem: {e}")
        return
    uploaded_file = st.file_uploader("Upload Gambar (JPG/PNG)", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        st.image(uploaded_file, caption='Preview Gambar', width=400) 
        if st.button('Mulai Deteksi', type="primary", use_container_width=True):
            with st.spinner('Sedang memindai piksel gambar...'):
                label, score = handler.predict(uploaded_file, "MobileNet")
                st.divider()
                if "Error" in label:
                    st.error(f"Terjadi Kesalahan: {label}")
                elif label == "Hoax":
                    st.success(f"HASIL: GAMBAR VALID")
                    st.write(f"Tingkat Keyakinan AI: **{score:.2f}%**")
                    st.progress(int(score))
                else:
                    st.error(f"HASIL: TERINDIKASI HOAX")
                    st.write(f"Tingkat Keyakinan AI: **{score:.2f}%**")
                    st.progress(int(score)) 