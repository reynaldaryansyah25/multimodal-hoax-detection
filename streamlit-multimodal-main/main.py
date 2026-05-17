import streamlit as st
st.set_page_config(
    page_title="Multimodal Hoax Detector",
    page_icon="🛡️",
    layout="centered",
    initial_sidebar_state="collapsed"
)
from views import image_page
from views import text_page

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
try:
    local_css(r"D:\INDONERIS-DATAMINING\multimodal-hoax-detection\streamlit-multimodal-main\assets\style.css")
except FileNotFoundError:
    st.warning("File style.css tidak ditemukan di folder assets.")

def main(): 
    st.markdown('<div class="main-title">Deteksi Kevalidan Berita Politik</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Sistem Deteksi Multimedia (Gambar, Teks, & Audio)</div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab_multi = st.tabs(["Beranda", "Cek Judul", "Cek Gambar", "Cek Audio", "Multimodal",])

    with tab_multi:
        st.markdown("---")
        try:
            from views import multimodal_page
            multimodal_page.show()
        except Exception as e:
            st.warning(f"Modul Multimodal belum siap: {e}")

    with tab1:
        st.markdown("---")
        col1, col2 = st.columns([1, 2])
        with col1:
            st.image("https://cdn-icons-png.flaticon.com/512/4712/4712010.png", width=150)
        with col2:
            st.markdown("""
            ### Selamat Datang!
            Aplikasi ini mendeteksi manipulasi informasi pada:
            * **Gambar:** Deteksi edit/manipulasi visual.
            * **Teks:** Analisis judul berita clickbait/palsu.
            * **Audio:** Deteksi suara Deepfake/AI Generated.
            * **Multimodal:** Analisis gabungan semua bukti untuk kesimpulan komprehensif.
            """)
        st.info("💡 **Tips:** Pastikan koneksi internet stabil saat pertama kali menjalankan aplikasi.")

    with tab2:
        st.markdown("---")
        try:
            text_page.show()
        except Exception as e:
            st.error(f"Error Modul Teks: {e}")

    with tab3:
        st.markdown("---")
        try:
            image_page.show()
        except Exception as e:
            st.error(f"Error Modul Gambar: {e}")

    with tab4:
        st.markdown("---")
        try:
            from views import audio_page 
            audio_page.show()
        except ImportError:
            st.warning("Modul audio belum tersedia.")
        except Exception as e:
            st.error(f"Error Modul Audio: {e}")

if __name__ == '__main__':
    main()
