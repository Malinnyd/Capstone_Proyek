🌿 TUMBUH

Teknologi Unggul Menuju Budidaya Hasil Utama Hebat
Dicoding Machine Learning Bootcamp Batch 8 – Capstone Project
👩‍💻 Oleh: Malinny Debra (DB8-PI034)
🔗 🌐 Akses Aplikasi Streamlit

📝 Ringkasan Proyek

TUMBUH adalah aplikasi Machine Learning Agritech berbasis web yang membantu petani, penyuluh, dan investor pertanian dalam membuat keputusan berbasis data.
Melalui antarmuka sederhana, pengguna dapat memasukkan lokasi (provinsi, kabupaten) dan komoditas pertanian, lalu mendapatkan hasil analisis otomatis berupa:

📈 Prediksi Hasil Panen – Estimasi produksi (Kg/Ha).

💰 Prediksi Biaya – Estimasi Modal Awal & Biaya Perawatan (Rp/Ha).

🌱 Rekomendasi Pemupukan – Dosis Urea, SP-36, dan KCl optimal berdasarkan data historis wilayah serupa.

Aplikasi ini memanfaatkan model machine learning yang telah dilatih untuk memberikan estimasi akurat serta mendukung pengambilan keputusan pertanian yang lebih efisien dan berkelanjutan.

✨ Fitur Utama

🤖 Prediksi Multi-Model:
Memprediksi tiga target berbeda — Hasil Panen, Modal Awal, dan Biaya Perawatan.

🌾 Rekomendasi Cerdas:
Menggunakan model berbasis similarity (kemiripan kondisi tanah dan iklim) untuk merekomendasikan dosis pupuk.

⚙️ Input Dinamis:
Pilihan kabupaten & komoditas otomatis menyesuaikan provinsi yang dipilih.

☁️ Hosting Model Eksternal:
Model .pkl besar di-host di AWS S3, kemudian diunduh otomatis saat aplikasi dijalankan.

📚 Fitur Edukasi:
Menyediakan bacaan ilmiah & tips pertanian berbasis sumber akademik 5 tahun terakhir.

💬 Feedback Section:
Pengguna dapat memberikan saran & umpan balik untuk peningkatan fitur.

🏗️ Arsitektur Sistem

Proyek TUMBUH menggunakan arsitektur hybrid untuk efisiensi penyimpanan dan performa:

GitHub (kode sumber)  →  AWS S3 (penyimpanan model ML)  →  Streamlit Cloud (deployment aplikasi)


GitHub: Menyimpan kode aplikasi (app.py), file pendukung (lookup_tabel.csv), dan konfigurasi (requirements.txt).

AWS S3: Menyimpan model .pkl besar (>100 MB).

Streamlit Cloud: Menjalankan aplikasi secara publik dan memuat model dari AWS saat runtime.

⚙️ Cara Menjalankan Proyek Secara Lokal
📋 Prasyarat

Pastikan telah menginstal:

Python 3.9 – 3.13

Git

Koneksi internet aktif (untuk mengunduh model dari AWS S3)

🚀 Langkah-Langkah Instalasi
1️⃣ Clone repositori
git clone https://github.com/Malinnyd/Capstone_Proyek.git
cd Capstone_Proyek

2️⃣ Buat Virtual Environment

Windows

python -m venv venv
venv\Scripts\activate


macOS / Linux

python3 -m venv venv
source venv/bin/activate

3️⃣ Install dependensi
pip install -r requirements.txt

4️⃣ Jalankan aplikasi
streamlit run app.py


🟢 Aplikasi akan otomatis terbuka di browser.
Pada saat pertama kali dijalankan, sistem akan menampilkan pesan “Mengunduh model…” — ini normal karena aplikasi sedang mengambil model .pkl dari AWS S3.

📂 Struktur Direktori
Capstone_Proyek/
│
├── app.py                # Aplikasi utama Streamlit
├── lookup_tabel.csv      # Dataset referensi lokasi & komoditas
├── .gitignore            # Mengabaikan file model besar & env
├── Model_ML/             # Notebook pelatihan & Dataset
├── requirements.txt      # Library dependensi
└── README.md             # Dokumentasi utama

💡 Catatan Tambahan

Notebook dan dataset pelatihan tersedia di folder Model_ML/.

Model dikembangkan di Google Colab, kemudian diunggah ke AWS S3 untuk efisiensi penyimpanan.

Semua model, data, dan script sepenuhnya dapat direplikasi dari repositori ini.

🌾 Tentang Proyek

Proyek ini merupakan bagian dari Dicoding Machine Learning Bootcamp Batch 8 (Capstone Project) dengan tema Machine Learning for Agritech.
Dikembangkan untuk mendukung transformasi digital sektor pertanian menuju Smart Farming Indonesia 4.0.

📎 Sumber Daya Pendukung

Streamlit Documentation

AWS S3 Python 

GOOGLE COLAB


Kontributor

Malinny Debra (DB8-PI034)
📧 malinny.debra@email.com

💻 GitHub Profile
