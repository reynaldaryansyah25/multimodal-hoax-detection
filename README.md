# Multimodal Hoax Detection (Pipeline Koleksi → Integrasi → Transkripsi)

Proyek ini membangun korpus multimodal untuk deteksi hoaks politik dari tiga sumber: TurnBackHoax (rujukan/label), portal berita resmi (valid), dan YouTube (teks+audio+visual), lalu mengintegrasikannya menjadi satu corpus untuk training dan evaluasi.​

# Fitur utama

Scraper arsip TurnBackHoax via kategori/tag politik dengan selector fleksibel dan unduh hingga 3 gambar/artikel.​

Scraper portal berita via RSS yang stabil (fetch XML dengan header kustom, parse dari string) + ekstraksi konten dan top image (opsional unduh).​

Koleksi YouTube: discovery query politik, enrichment metadata, unduh audio/video/thumbnail, dan transkripsi otomatis dengan Whisper “medium”.​

Integrator korpus menyatukan semua sumber ke skema seragam (CSV/JSON) untuk eksperimen multimodal.​

# Struktur folder

data/raw/turnbackhoax: images/, metadata/, articles.json dan retry_queue.json.​

data/raw/news: images/ (opsional), articles.json dan retry_queue.json.​

data/raw/youtube: audio/, videos/ (opsional), thumbnails/, json/, metadata_compiled.json.​

data/transcripts: hasil Whisper per audio YouTube (.txt & .json).​

data/processed: corpus_integrated.csv|json (korpus gabungan). ​

Persiapan lingkungan
Python 3.10+ dan virtual env aktif.​

Install dependensi:

pip install -r requirements.txt​

Untuk transkripsi GPU (opsional): install Torch CUDA yang sesuai.​

Jalankan pengumpulan data
TurnBackHoax (kategori/tag politik)

Perintah:

python -m src.annotation.turnbackhoax_standalone​

Output: data/raw/turnbackhoax/articles.json, metadata/turnbackhoax_metadata.csv, images/\*.​

Portal Berita via RSS

Perintah:

python -m src.annotation.news_portals_standalone​

Fitur: filter kata kunci politik, unduh top image opsional, retry queue untuk URL gagal.​

YouTube (opsional saat awal, disarankan aktif)

Di main.py sudah disediakan tahap discovery + enrich + download.​

Output: audio WAV, video MP4 (opsional), thumbnail JPG, metadata JSON.​

Integrasi korpus
Satukan semua sumber:

python -m src.main (atau jalankan fungsi integrator sesuai kebutuhan).​

Hasil: data/processed/corpus_integrated.csv|json berisi kolom: source, ref_id, title, text, url, date/domain/authors (jika ada), labels (TBH), media_paths (audio/video/gambar/transkrip). ​

Transkripsi Whisper (model “medium”)
Jalankan batch:

python -m src.transcription.whisper_asr (model default bisa diubah ke “medium”).​

Hasil per audio: data/transcripts/YT_XXXX.txt dan .json; integrator akan mengisi kolom text dengan transkrip jika tersedia (fallback ke deskripsi).​

Labeling dan penggunaan korpus
TurnBackHoax: sumber ground-truth “hoax/disinformasi/klarifikasi” (dipetakan ke kelas false).​

Portal berita resmi: dianggap “valid/true” sebagai rujukan.​

YouTube: awalnya “unlabeled”; dapat dipakai untuk pseudo-labeling menggunakan model yang dilatih dari TBH vs news.​

Tips troubleshooting
Jika TBH kosong: ganti slug ke kategori/hoax, kategori/disinformasi, atau tag/politik; cek log “Page X: found Y” dan adjust selector bila perlu.​

Jika RSS error/0 kandidat: pastikan fetch XML memakai header kustom (sudah diimplementasikan) dan jalankan retry; kurangi max_per_source untuk isolasi feed bermasalah.​

Jika hanya gambar tersimpan di TBH: aktifkan penyimpanan metadata progresif (JSONL/CSV per item) dan gunakan fallback <article><p> untuk teks.​

Evaluasi (ringkas)
Siapkan split train/val/test yang berimbang antar sumber/kelas.​

Lakukan ablation: text-only vs text+image (news/TBH) vs text+audio(+visual) (YouTube).​

Metrik: F1 macro, precision/recall per kelas, dan analisis error pada kasus politis spesifik.​

Etika dan legal
Gunakan rate limiting, hormati ketentuan situs, dan hindari PII yang tidak perlu; cantumkan sumber data pada laporan.​

Roadmap singkat
Selesaikan transkripsi semua audio (model “medium”), perluas scraping TBH/news, dan commit integrasi korpus terbaru.​

Tambahkan notebook inference/demo yang menerima URL dan mengeluarkan prediksi + highlight.​

README ini bersifat sementara untuk memandu eksekusi end-to-end (collect → integrate → transcribe) sebelum tahap training dan evaluasi lanjutan disiapkan di folder modeling.
