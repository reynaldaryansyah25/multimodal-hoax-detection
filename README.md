# 🔍 Sistem Deteksi Hoaks Multimodal - Konten Politik Indonesia

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-red.svg)](https://pytorch.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.25+-ff0000.svg)](https://streamlit.io/)
[![License MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📖 Latar Belakang

Penyebaran berita hoaks di media sosial Indonesia, terutama konten politik, berkembang pesat dengan memanfaatkan **kombinasi teks menyesatkan, gambar out-of-context, dan audio deepfake**. Verifikasi manual oleh fact-checker tidak mampu mengimbangi volume konten masif.

**Masalah:**

- ❌ Mayoritas sistem deteksi hoaks Indonesia hanya menganalisis **teks saja** (unimodal)
- ❌ Minimnya sistem yang dapat mendeteksi **inkonsistensi lintas-modal** (text-image mismatch, deepfake audio)
- ❌ Kurangnya dataset hoaks multimodal terstruktur untuk konteks Indonesia
- ❌ Sulit untuk menjelaskan hasil prediksi kepada publik (black-box)

---

## 🎯 Tujuan

Mengembangkan sistem **deteksi hoaks berbasis deep learning multimodal** yang dapat:

1. Menganalisis **teks, gambar, dan audio secara terintegrasi** untuk deteksi hoaks lebih akurat
2. Mengidentifikasi **inkonsistensi lintas-modal** (cross-modal mismatch) sebagai indikator manipulasi
3. Mendeteksi **deepfake audio** dan **gambar AI-generated** untuk identifikasi media sintetis
4. Memberikan **penjelasan visual & tekstual** untuk setiap prediksi (explainability)
5. Menyediakan **dataset dan model open-source** untuk komunitas Indonesia

---

## 💡 Manfaat

### Untuk Masyarakat Umum

- 📱 Verifikasi berita sebelum share di media sosial
- 🔍 Pahami mengapa konten dianggap hoaks (interpretable)
- ⚡ Deteksi cepat tanpa perlu menunggu fact-checker

### Untuk Jurnalis & Fact-Checker

- 🚀 Mempercepat proses verifikasi konten
- 📊 Data-driven insights untuk investigasi lebih dalam
- 🎯 Fokus pada kasus ambigu, otomasi untuk clear-cut cases

### Untuk Peneliti & Developer

- 📚 Dataset Indonesia multimodal terstruktur (1000+ samples)
- 🛠️ Model & code open-source siap dikembangkan
- 🔬 Benchmark untuk hoax detection tasks dalam Bahasa Indonesia

### Untuk Platform Media & Pemerintah

- 🛡️ Content moderation otomatis pre-deployment
- 📈 Monitoring trend hoaks & misinformasi real-time
- ⚖️ Evidence-based policy untuk combat misinformation

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

## ✨ Fitur-Fitur Utama

### 1. **Deteksi Trimodal Terintegrasi**

- Analisis simultan teks, gambar, dan audio dari satu berita
- Missing modality handling untuk data yang tidak lengkap
- Flexible input: artikel teks, URL video YouTube, atau media terpisah

### 2. **Cross-Modal Consistency Checking**

- Deteksi **text-image mismatch** (gambar tidak sesuai narasi)
- Deteksi **text-audio mismatch** (ucapan berbeda dari klaim)
- Entity consistency scoring (apakah figur/lokasi match antar modalitas)

### 3. **Deepfake & Synthetic Media Detection**

- **Deepfake audio detection**: Identifikasi voice cloning, TTS, audio sintetis
- **AI-generated image detection**: Flag gambar buatan AI (Midjourney, DALL-E, Stable Diffusion)
- Confidence scoring untuk tingkat kepercayaan deteksi

### 4. **Explainability & Interpretability**

- **Highlighting**: Bagian teks mencurigakan ditandai dengan reasoning
- **Heatmap visual**: Menunjukkan region anomali di gambar
- **Audio breakdown**: Analisis detail sinyal audio (frequency, prosodi)
- Penjelasan Bahasa Indonesia yang mudah dipahami publik

### 5. **Real-Time Web Application**

- Upload teks, gambar, atau audio langsung dari Streamlit UI
- Live prediction dengan progress bar
- Visualisasi hasil prediksi yang interaktif dan informatif
- Export hasil ke PDF untuk sharing & reporting

### 6. **Dataset Indonesia Terstruktur**

- **300+ hoaks terverifikasi** dari Turnbackhoax.id
- **400+ berita valid** dari portal berita kredibel (Kompas, Detik, Tempo)
- **113 video YouTube** dengan ekstraksi text, image, audio
- Multi-level annotation: news-level, modality-level, cross-modal consistency
- Stratified split: 70% training, 15% validation, 15% testing

### 7. **Pretrained Models & Open Source**

- Model weights siap download & deploy
- Fine-tuning friendly untuk kasus khusus
- Modular architecture untuk eksperimen custom
- Code transparan & reproducible

---

## 📊 Hasil & Performa

### Overall Performance

╔═══════════════════════════════════════╗
║ TRIMODAL MODEL - TEST RESULTS ║
╠═══════════════════════════════════════╣
║ Accuracy:║
║ Precision:% ║
║ Recall: ║
║ F1-Score:║
║ ROC-AUC: ║
╚═══════════════════════════════════════╝

### Model Comparison

Model Accuracy Improvement
──────────────────────────────────────────────
Text-only 82.3% baseline
Image-only 76.8% -7.2%
Audio-only 71.5% -15.3%
Text + Image 86.4% +4.9%
Trimodal (BEST) 89.2% +7.2% ✓

### Dataset Statistics

Total Samples:
├─ Hoax:
├─ Valid:
├─ Training Set:
├─ Validation Set:
└─ Test Set:

Modality Distribution:
├─ Text + Image:
├─ Text + Image + Audio:
├─ Text Only:
└─ Text + Audio:
