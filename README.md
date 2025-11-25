# Deteksi Kevalidan Berita Kebijakan Politik Tahun Pertama Pemerintahan Prabowo Menggunakan Model Multimodal Berbasis Teks, Citra, dan Audio

Repository ini menyediakan implementasi lengkap sistem klasifikasi kevalidan berita politik Indonesia menggunakan Multimodal Deep Learning. Sistem menggabungkan tiga modalitas informasi utama—teks, citra, dan audio—guna mendeteksi berita valid dan hoaks secara lebih akurat.

1. Overview

Pada era media digital, konten politik tersebar dalam berbagai bentuk, mulai dari teks hingga visual dan audio. Model deteksi hoaks tradisional yang hanya memanfaatkan teks tidak lagi memadai. Proyek ini menghadirkan solusi alternatif melalui pendekatan multimodal, serta melibatkan:

Scraping portal berita untuk data valid

Pengambilan data hoaks dari TurnBackHoax.id

Crawling YouTube (judul, thumbnail, audio)

Pseudo-labeling untuk memperluas dataset

Pelatihan model unimodal (IndoBERT, MobileNetV3, Wav2Vec2)

Late Fusion dan Hierarchical Fusion untuk multimodal

Evaluasi komprehensif pada semua konfigurasi model

2. Arsitektur Sistem
   ┌─────────────────────┐
   │ Data Collection │
   │ (News, Hoax, YT) │
   └─────────┬───────────┘
   │
   ┌─────────────────▼──────────────────┐
   │ Preprocessing │
   │ (Teks, Normalisasi Citra, Audio) │
   └─────────────────┬──────────────────┘
   │
   ┌─────────────────▼──────────────────┐
   │ Pseudo-Labeling │
   │ (IndoBERT sebagai Guru) │
   └─────────────────┬──────────────────┘
   │
   ┌────────────────────▼────────────────────┐
   │ Ekstraksi Fitur Unimodal │
   │ IndoBERT | MobileNetV3 | Wav2Vec2 │
   └────────────────────┬────────────────────┘
   │
   ┌────────────────────▼────────────────────┐
   │ Late / Hierarchical Fusion │
   │ (Teks+Citra, Teks+Audio, T+C+A) │
   └────────────────────┬────────────────────┘
   │
   ┌─────────▼──────────┐
   │ Klasifikasi │
   └─────────┬──────────┘
   │
   ┌─────────▼──────────┐
   │ Evaluasi │
   └─────────────────────┘
