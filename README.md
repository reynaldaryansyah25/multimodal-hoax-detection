# 🔍 Sistem Deteksi Hoaks Multimodal — Konten Politik Indonesia

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-red.svg)](https://pytorch.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.25+-ff0000.svg)](https://streamlit.io/)
[![License MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📖 Latar Belakang

Penyebaran berita hoaks di media sosial Indonesia, terutama dalam konteks **politik**, berkembang pesat melalui **teks menyesatkan, gambar out-of-context, dan audio deepfake**.  
Verifikasi manual oleh fact-checker sulit mengimbangi volume konten yang masif.

**Masalah utama:**

- ❌ Sistem deteksi hoaks di Indonesia umumnya hanya menganalisis **teks (unimodal)**
- ❌ Belum mampu mendeteksi **inkonsistensi lintas-modal** (text–image mismatch, deepfake audio)
- ❌ Kurangnya dataset multimodal berbahasa Indonesia yang terstruktur
- ❌ Hasil prediksi sulit dijelaskan ke publik (black-box model)

---

## 🎯 Tujuan

Mengembangkan sistem **deteksi hoaks berbasis deep learning multimodal** yang mampu:

1. Menganalisis **teks, gambar, dan audio secara terintegrasi**
2. Mengidentifikasi **inkonsistensi lintas-modal** sebagai indikasi manipulasi
3. Mendeteksi **deepfake audio** dan **gambar buatan AI**
4. Menyediakan **penjelasan visual dan tekstual** yang dapat dipahami publik
5. Membuka akses **dataset dan model open-source** untuk komunitas Indonesia

---

## 💡 Manfaat

### 👥 Untuk Masyarakat Umum

- 📱 Verifikasi berita sebelum dibagikan di media sosial
- 🔍 Pahami alasan konten dikategorikan sebagai hoaks
- ⚡ Deteksi cepat tanpa menunggu fact-checker

### 📰 Untuk Jurnalis & Fact-Checker

- 🚀 Mempercepat proses verifikasi konten
- 📊 Mendapat insight berbasis data untuk investigasi
- 🎯 Fokus pada kasus ambigu, otomatisasi untuk kasus jelas

### 🧠 Untuk Peneliti & Developer

- 📚 Dataset multimodal Indonesia terstruktur (1000+ sampel)
- 🛠️ Model dan kode open-source siap dikembangkan
- 🔬 Benchmark tugas hoax detection dalam Bahasa Indonesia

### 🏛️ Untuk Platform Media & Pemerintah

- 🛡️ Moderasi konten otomatis sebelum publikasi
- 📈 Pemantauan tren hoaks & misinformasi secara real-time
- ⚖️ Dasar kebijakan berbasis data dalam melawan hoaks

---

## 🛠️ Tools & Technologies

| Komponen             | Tools                                    |
| -------------------- | ---------------------------------------- |
| **ML Framework**     | PyTorch 2.0, Transformers (Hugging Face) |
| **Text Processing**  | IndoBERT, NLTK, Sastrawi                 |
| **Image Processing** | EfficientNet, OpenCV, Pillow, CLIP       |
| **Audio Processing** | Librosa, CNN, Whisper (ASR)              |
| **Web Application**  | Streamlit, Plotly                        |
| **Data Tools**       | Pandas, NumPy, Scikit-learn              |
| **Media Retrieval**  | YouTube API, yt-dlp, BeautifulSoup       |

---

## ✨ Fitur Utama

### 1. 🧩 Deteksi Trimodal Terintegrasi

- Analisis simultan **teks, gambar, dan audio** dari satu berita
- Mendukung **data tidak lengkap (missing modality handling)**
- Input fleksibel: teks, URL YouTube, atau media terpisah

### 2. 🔄 Cross-Modal Consistency Checking

- Deteksi **ketidaksesuaian teks–gambar**
- Deteksi **ketidaksesuaian teks–audio**
- Scoring konsistensi entitas (figur/lokasi antar-modalitas)

### 3. 🧠 Deteksi Deepfake & Media Sintetis

- Deteksi **deepfake audio** (voice cloning, TTS, sintetis)
- Deteksi **gambar buatan AI** (Midjourney, DALL·E, Stable Diffusion)
- Confidence score untuk tingkat kepercayaan hasil deteksi

### 4. 🪄 Explainability & Interpretability

- **Highlight teks** mencurigakan dengan alasan deteksi
- **Heatmap visual** area anomali pada gambar
- **Audio breakdown**: analisis sinyal frekuensi dan prosodi
- Penjelasan berbahasa Indonesia yang mudah dipahami publik

### 5. ⚡ Aplikasi Web Real-Time

- Upload teks, gambar, atau audio langsung dari antarmuka Streamlit
- Prediksi real-time dengan progress bar
- Visualisasi hasil interaktif dan informatif
- Export hasil ke **PDF** untuk pelaporan

### 6. 🗂️ Dataset Multimodal Indonesia

- **1000+ hoaks** dari Turnbackhoax.id
- **1000+ berita valid** dari Kompas, Detik, Tempo
- **300+ video YouTube** dengan ekstraksi teks, gambar, dan audio
- **Multi-level annotation**: level berita, modalitas, dan konsistensi lintas-modal
- Stratified split: 70% train, 15% validation, 15% test

### 7. 🔓 Pretrained Models & Open Source

- Model siap diunduh dan digunakan langsung
- Dapat di-fine-tune untuk kasus khusus
- Arsitektur modular & reproducible
- Kode transparan dan terdokumentasi

---

## 📊 Hasil & Performa

### 🧪 Hasil Uji Model (Trimodal)

| Metrik    | Nilai |
| --------- | ----- |
| Accuracy  | –     |
| Precision | –     |
| Recall    | –     |
| F1-Score  | –     |
| ROC-AUC   | –     |

### ⚖️ Perbandingan Model

| Model               | Akurasi | Peningkatan |
| ------------------- | ------- | ----------- |
| Text-only           | –       | –           |
| Image-only          | –       | –           |
| Audio-only          | –       | –           |
| Text + Image        | –       | –           |
| **Trimodal (Best)** | –       | –           |

### 📈 Statistik Dataset

| Kategori     | Jumlah |
| ------------ | ------ |
| Total Sampel | –      |
| Hoax         | –      |
| Valid        | –      |
| Training     | –      |
| Validation   | –      |
| Testing      | –      |

**Distribusi Modalitas:**

- Text + Image
- Text + Image + Audio
- Text Only
- Text + Audio

---

## 📜 Lisensi

Proyek ini dilisensikan di bawah **MIT License** — lihat [LICENSE](LICENSE) untuk detail.

---
