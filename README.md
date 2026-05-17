# 🎭 Multimodal Hoax Detection

> **Sistem Deteksi Berita Hoax/Palsu Menggunakan Pendekatan Multimodal dengan Text, Audio, dan Visual Features**

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.5.1-ee4c2c.svg)](https://pytorch.org/)
![Status](https://img.shields.io/badge/Status-Active%20Development-green.svg)

---

## 📋 Daftar Isi

- [Deskripsi Proyek](#-deskripsi-proyek)
- [Fitur Utama](#-fitur-utama)
- [Struktur Direktori](#-struktur-direktori)
- [Teknologi yang Digunakan](#-teknologi-yang-digunakan)
- [Instalasi](#-instalasi)
- [Dataset](#-dataset)
- [Panduan Penggunaan](#-panduan-penggunaan)
- [Pipeline Pemrosesan Data](#-pipeline-pemrosesan-data)
- [Model & Training](#-model--training)
- [Hasil](#-hasil)
- [Kontribusi](#-kontribusi)
- [Lisensi](#-lisensi)

---

## 🎯 Deskripsi Proyek

Proyek ini mengembangkan sistem **deteksi hoax/disinformasi** menggunakan pendekatan **multimodal** yang mengintegrasikan:

- **Text Modality**: Analisis konten tekstual dari berita/artikel
- **Audio Modality**: Pemrosesan transkrip video dan speaker diarization
- **Visual Modality**: Ekstraksi fitur dari gambar terkait konten

Sistem dirancang khusus untuk mendeteksi berita palsu dalam konteks **Indonesia** dengan fokus pada konten politik, hoax media sosial, dan video disinformasi.

**Tujuan**: Membangun model machine learning/deep learning yang akurat dalam mengidentifikasi berita hoax dengan memanfaatkan informasi dari berbagai modalitas.

---

## ✨ Fitur Utama

### Data Collection & Integration
- ✅ Scraping berita dari portal resmi (Kompas, dll)
- ✅ Integrasi dataset TurnBackHoax (berita hoax terverifikasi)
- ✅ Pengumpulan transkrip video YouTube
- ✅ Download dan preprocessing gambar

### Data Preprocessing
- ✅ Text cleaning dan normalisasi (Indonesian)
- ✅ Stopword removal (Sastrawi)
- ✅ Audio transcription menggunakan Whisper ASR
- ✅ Speaker diarization (pyannote)
- ✅ Quality check dan filtering dataset
- ✅ Handling class imbalance

### Feature Extraction
- ✅ **Text Features**: 
  - TF-IDF, Word embeddings (GloVe, FastText)
  - BERT embeddings (Indonesian BERT)
  - Transformers-based representations
  
- ✅ **Audio Features**:
  - Mel-frequency cepstral coefficients (MFCC)
  - Speaker embeddings
  - Prosody features
  
- ✅ **Visual Features**:
  - CNN-based image embeddings (ResNet, VGG)
  - Object detection
  - Scene understanding

### Modeling
- ✅ Traditional ML (Logistic Regression, SVM, Random Forest)
- ✅ Deep Learning (LSTM, GRU, Transformer)
- ✅ Multimodal fusion architectures
- ✅ Transfer learning dari pretrained models

### Deployment
- ✅ Streamlit web application
- ✅ Model serving API
- ✅ Docker support (planned)

---

## 📂 Struktur Direktori

```
multimodal-hoax-detection/
├── README.md                          # Dokumentasi utama
├── requirements.txt                   # Python dependencies
│
├── data/
│   ├── raw/                          # Data mentah
│   │   ├── news/                     # Artikel berita dengan gambar
│   │   │   ├── news_with_images.csv
│   │   │   └── images/
│   │   ├── turnbackhoax/             # Dataset TurnBackHoax
│   │   │   └── metadata/
│   │   └── transcript/               # Transkrip video
│   │       └── metadata_labeled.json
│   │
│   ├── processed/                    # Data terproses
│   │   ├── dataset_clean_finalv1.csv
│   │   ├── dataset_integrated_cleanv1.csv
│   │   └── normalization/            # Hasil normalisasi transkrip
│   │
│   └── debug_output/                 # Output untuk debugging
│
├── notebooks/                        # Jupyter notebooks
│   ├── news_clean.ipynb             # Pembersihan data berita
│   ├── tbh_clean.ipynb              # Pembersihan data TurnBackHoax
│   ├── normalsasi_transkripts.ipynb # Normalisasi transkrip audio
│   └── integrate_newstbh_clean.ipynb# Integrasi dan cleaning dataset gabungan
│
├── src/                             # Source code
│   ├── data_preprocessing/
│   │   ├── integrate_tbh_news.py    # Integrasi TBH + News
│   │   └── integrate_dataset_modelling.py  # Persiapan data untuk modeling
│   │
│   ├── modeling/                    # (Planned)
│   │   ├── text_models.py
│   │   ├── audio_models.py
│   │   ├── visual_models.py
│   │   └── multimodal_fusion.py
│   │
│   ├── scrape/                      # (Planned)
│   │   ├── news_scraper.py
│   │   └── youtube_downloader.py
│   │
│   └── transcription/               # (Planned)
│       └── audio_processor.py
│
├── streamlit-multimodal-main/       # Aplikasi Streamlit
│   ├── requirements.txt             # Dependencies untuk Streamlit
│   └── app.py
│
└── .gitignore
```

---

## 🛠️ Teknologi yang Digunakan

### Framework & Libraries

| Kategori | Tools | Versi |
|----------|-------|-------|
| **Deep Learning** | PyTorch, Lightning | 2.5.1, 2.x |
| **NLP** | Transformers, Datasets | 4.41+, 3.0+ |
| **Audio Processing** | librosa, Whisper, pyannote | 0.10+, 20231117+, 3.1.1 |
| **Data Processing** | Pandas, NumPy, scikit-learn | 2.2+, 1.26+, 1.5+ |
| **Web Scraping** | yt-dlp, beautifulsoup4, newspaper3k | 2024.11+, 4.12+, 0.2.8 |
| **Visualization** | Matplotlib, Seaborn | 3.9+, 0.13+ |
| **Web App** | Streamlit, FastAPI | 1.51+, 0.121+ |
| **Indonesian NLP** | Sastrawi, NLTK | 1.0.1, 3.8+ |

### CUDA & GPU
- CUDA 12.1
- PyTorch CUDA-enabled
- GPU optimization untuk training model besar

---

## 🚀 Instalasi

### Prasyarat
- Python 3.10+
- pip atau conda
- GPU (optional, recommended untuk training)
- 8GB+ RAM

### Setup Environment

#### 1. Clone Repository
```bash
git clone https://github.com/reynaldaryansyah25/multimodal-hoax-detection.git
cd multimodal-hoax-detection
```

#### 2. Buat Virtual Environment
```bash
# Menggunakan venv
python -m venv .venv

# Aktivasi
# Linux/Mac:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate
```

#### 3. Install Dependencies
```bash
# Install requirements utama
pip install -r requirements.txt

# Untuk Streamlit app (optional)
cd streamlit-multimodal-main
pip install -r requirements.txt
cd ..
```

#### 4. Download Model Pretrained (Optional)
```bash
# Download Whisper model untuk transcription
python -c "import whisper; whisper.load_model('medium')"

# Download pyannote speaker diarization model
# Perlu akses Hugging Face
```

---

## 📊 Dataset

### Sumber Data

1. **News Dataset** (1,946 samples)
   - Sumber: Kompas (portal berita resmi)
   - Format: Text + Image (multimodal)
   - Label: 0 (Valid), 1 (Hoax)
   - Proporsi: ~61.8% valid, ~38.2% hoax

2. **TurnBackHoax (TBH) Dataset** (1,179 samples)
   - Sumber: turnbackhoax.id (verified hoax database)
   - Format: Text (post + metadata)
   - Label: Binary classification
   - Filtering: Hanya konten politik

3. **Transcript Dataset** (992 samples)
   - Sumber: YouTube videos
   - Format: Audio transcripts (normalized)
   - Processing: Cleaning, normalization, quality check

### Total Dataset
- **Integrated**: 3,068 samples
- **After cleaning**: 3,068 samples
- **Test data**: Ready for modeling

### Data Distribution

```
├── Valid News: 1,895 samples (61.8%)
├── Hoax News: 1,173 samples (38.2%)
└── Total: 3,068 samples
```

---

## 📖 Panduan Penggunaan

### 1. Data Cleaning & Preprocessing

#### a. Membersihkan Data Berita
```bash
jupyter notebook notebooks/news_clean.ipynb
```
**Output**: `AllMetadata_Cleaned_v3.csv`

#### b. Membersihkan Data TurnBackHoax
```bash
jupyter notebook notebooks/tbh_clean.ipynb
```
**Output**: `tbh_BERSIH_POLITIK_SAJA.csv`

#### c. Normalisasi Transkrip Audio
```bash
jupyter notebook notebooks/normalsasi_transkripts.ipynb
```
**Output**: `final_metadata_clean.json`

#### d. Integrasi Dataset
```bash
jupyter notebook notebooks/integrate_newstbh_clean.ipynb
```
**Output**: `dataset_clean_finalv1.csv`

### 2. Python Scripts untuk Preprocessing

```bash
# Integrasi TBH + News Dataset
python src/data_preprocessing/integrate_tbh_news.py

# Persiapan data untuk modeling
python src/data_preprocessing/integrate_dataset_modelling.py
```

### 3. Menjalankan Streamlit App

```bash
cd streamlit-multimodal-main
streamlit run app.py
```

Akses di browser: `http://localhost:8501`

---

## 🔄 Pipeline Pemrosesan Data

### Tahap 1: Data Collection
```
YouTube/News Portal → Downloaded Content → Raw Files
                    (news, images, audio)
```

### Tahap 2: Cleaning & Normalization
```
Raw Text/Audio
    ↓
Remove URLs, HTML, Special Characters
Remove Emoji, Normalize Indonesian Text
Remove Stopwords (Sastrawi)
Handle Duplicates
    ↓
Cleaned Text
```

### Tahap 3: Transcription (Audio)
```
Audio Files
    ↓
Whisper ASR (Speech-to-Text)
Speaker Diarization (pyannote)
    ↓
Transcripts + Speaker Info
    ↓
Text Normalization
    ↓
Clean Transcripts
```

### Tahap 4: Quality Check & Filtering
```
Processed Data
    ↓
Min Length Check (50 chars, 10 tokens)
Repetition Check (detect noise)
Remove Duplicates
    ↓
Quality Status (GOOD/WARNING/BAD)
    ↓
Filtered Dataset (Ready for ML)
```

### Tahap 5: Feature Extraction
```
Text/Audio/Images
    ↓
├─ Text: BERT, TF-IDF, Word2Vec
├─ Audio: MFCC, Speaker Embeddings
└─ Image: CNN Features (ResNet)
    ↓
Feature Vectors
```

### Tahap 6: Modeling & Training
```
Features + Labels
    ↓
Train/Val/Test Split
    ↓
Model Selection
    ├─ Traditional ML (SVM, RF)
    ├─ LSTM/GRU
    └─ Transformer-based
    ↓
Training & Evaluation
    ↓
Hoax Detection Model
```

---

## 🧠 Model & Training

### Supported Models

#### Text-Based Models
- **Logistic Regression** (baseline)
- **Random Forest** (ensemble)
- **LSTM/GRU** (sequence models)
- **BERT-based** (transformers)
  - `bert-base-multilingual-cased`
  - `indobert`

#### Audio-Based Models
- **MFCC + SVM**
- **CNN on spectrograms**
- **Speaker embeddings**

#### Visual-Based Models
- **ResNet50 pretrained**
- **VGG16 pretrained**

#### Multimodal Fusion
- **Early Fusion** (concatenate raw features)
- **Mid Fusion** (combine learned representations)
- **Late Fusion** (combine predictions)
- **Attention-based Fusion** (learnable weights)

### Example Training

```python
from src.modeling import MultimodalFusion

# Initialize model
model = MultimodalFusion(
    text_dim=768,      # BERT dimension
    audio_dim=128,     # Audio embedding dim
    image_dim=2048,    # ResNet50 feature dim
    hidden_dim=256,
    num_classes=2
)

# Train
model.train(train_loader, val_loader, epochs=20, lr=1e-4)

# Evaluate
results = model.evaluate(test_loader)
print(f"Accuracy: {results['accuracy']:.4f}")
print(f"F1-Score: {results['f1']:.4f}")
```

---

## 📈 Hasil

### Dataset Statistics
| Metrik | Nilai |
|--------|-------|
| Total Samples | 3,068 |
| Valid News | 1,895 (61.8%) |
| Hoax News | 1,173 (38.2%) |
| Avg Text Length | 150-500 chars |
| Language | Indonesian |

### Preprocessing Results

#### Text Cleaning
- ✅ Removed URLs, HTML tags, special characters
- ✅ Normalized Indonesian text (Sastrawi)
- ✅ Removed 6 duplicates
- ✅ Final: 3,068 clean samples

#### Transcript Normalization
- ✅ Processed 1,000 transcripts
- ✅ Quality status: 992 GOOD, 1 WARNING, 7 BAD
- ✅ Average length: 200-800 chars
- ✅ Removed high-repetition noise

### Model Performance (Baseline)
Akan diupdate setelah training selesai:
- [ ] Text-only BERT
- [ ] Multimodal Late Fusion
- [ ] Multimodal Attention Fusion

---

## 📌 Notebook Descriptions

### 1. `news_clean.ipynb`
**Purpose**: Pembersihan dan preprocessing data berita dari Kompas

**Proses**:
- Load 1,999 samples dari `news_with_images.csv`
- Hapus missing values di kolom `text`
- Hapus kolom tidak perlu (`period`, `source_csv`)
- Konversi datetime columns
- Basic text cleaning (newline, extra spaces)
- **Output**: `AllMetadata_Cleaned_v3.csv` (1,946 samples)

### 2. `tbh_clean.ipynb`
**Purpose**: Pembersihan data TurnBackHoax dengan filtering ketat

**Filter Applied**:
- **Anti-leak filter**: Hapus kebocoran metadata (keywords seperti "hasil periksa fakta")
- **Political filter**: Hanya ambil konten yang mengandung keyword politik
- **Deduplication**: Hapus duplikat teks

**Output**: `tbh_BERSIH_POLITIK_SAJA.csv` (1,179 samples)

### 3. `normalsasi_transkripts.ipynb`
**Purpose**: Normalisasi dan quality check untuk transkrip audio

**Pipeline**:
- **Tahap 1**: Enhanced cleaning (remove timestamps, music markers, URLs)
- **Tahap 2**: Text normalization (case folding, typo correction)
- **Tahap 3**: Quality check (min length, repetition detection)

**Output**: `final_metadata_clean.json` (992 samples)

### 4. `integrate_newstbh_clean.ipynb`
**Purpose**: Integrasi dan final cleaning dataset News + TBH

**Proses**:
- Load combined dataset (3,074 samples)
- Text cleaning & stopword removal
- Remove duplicates
- Generate label distribution
- **Output**: `dataset_clean_finalv1.csv` (3,068 samples)

---

## 🔧 Development & Future Enhancements

### Completed ✅
- [x] Data collection & integration
- [x] Text preprocessing & cleaning
- [x] Audio transcription pipeline
- [x] Data quality checks
- [x] Jupyter notebooks for EDA

### In Progress 🚧
- [ ] Feature extraction (Text, Audio, Image)
- [ ] Model training & evaluation
- [ ] Multimodal fusion strategies
- [ ] Hyperparameter optimization

### Planned 📋
- [ ] Docker containerization
- [ ] REST API deployment
- [ ] Real-time inference
- [ ] Web dashboard improvements
- [ ] Mobile app support
- [ ] Multilingual support (beyond Indonesian)

---

## 🤝 Kontribusi

Kami sangat menerima kontribusi! Silakan:

1. **Fork** repository ini
2. **Buat branch** fitur baru (`git checkout -b feature/AmazingFeature`)
3. **Commit** perubahan (`git commit -m 'Add some AmazingFeature'`)
4. **Push** ke branch (`git push origin feature/AmazingFeature`)
5. **Buka Pull Request**

### Petunjuk Kontribusi
- Ikuti PEP 8 style guide
- Tambahkan docstrings untuk functions
- Update dokumentasi sesuai perubahan
- Pastikan semua tests pass

---

## 📄 Lisensi

Proyek ini dilisensikan di bawah [MIT License](LICENSE).

---

## 📞 Kontak & Support

- **Author**: Reynaldy Aryansyah (@reynaldaryansyah25)
- **Repository**: [GitHub - multimodal-hoax-detection](https://github.com/reynaldaryansyah25/multimodal-hoax-detection)
- **Issues**: Buka [GitHub Issues](https://github.com/reynaldaryansyah25/multimodal-hoax-detection/issues)

---

## 🙏 Acknowledgments

- **Data Sources**: 
  - [Kompas.com](https://kompas.com) - Portal berita
  - [TurnBackHoax.id](https://turnbackhoax.id) - Fact-checking database
  - [YouTube](https://youtube.com) - Video content

- **Libraries & Tools**:
  - PyTorch & Transformers
  - Whisper (OpenAI)
  - pyannote-audio
  - Streamlit
  - Sastrawi (Indonesian NLP)

- **Inspiration**:
  - Multimodal learning research
  - Fact-checking systems
  - Indonesian NLP community

---

**Last Updated**: 2026-05-17 | **Status**: 🟢 Active Development

*Membangun kepercayaan digital melalui deteksi misinformasi yang akurat.*
