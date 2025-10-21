TUMBUH (Teknologi Unggul Menuju Budidaya Hasil Utama Hebat)
Dicoding Machine Learning Bootcamp Batch 8 - Machine Learning Capstone  Capstone Oleh: Malinny Debra (DB8-PI034)
Link : https://capstoneproyek-ktmxxjgponem9iefarzckf.streamlit.app/

📝 Ringkasan Aplikasi
TUMBUH adalah aplikasi web cerdas yang dibangun menggunakan Streamlit untuk membantu petani dan pemangku kepentingan di sektor agrikultur Indonesia. Aplikasi ini bertujuan untuk memberikan wawasan berbasis data untuk optimalisasi budidaya tanaman.

Dengan memasukkan lokasi (provinsi, kabupaten) dan komoditas, pengguna akan mendapatkan:

Prediksi Hasil Panen: Estimasi jumlah panen (dalam Kg/Ha).

Prediksi Biaya: Estimasi Modal Awal dan Biaya Perawatan (dalam Rp/Ha).

Rekomendasi Pemupukan: Rekomendasi dosis pupuk (Urea, SP-36, KCl) yang optimal berdasarkan data historis di wilayah serupa.

Aplikasi ini memanfaatkan model machine learning yang telah dilatih untuk memberikan estimasi dan rekomendasi yang akurat guna mendukung pengambilan keputusan yang lebih baik.

✨ Fitur Utama
Prediksi Multimodel: Memprediksi 3 target berbeda: Hasil Panen, Modal Awal, dan Biaya Perawatan.

Rekomendasi Cerdas: Memberikan rekomendasi pupuk menggunakan model berbasis kemiripan (similarity-based).

Input Dinamis: Pilihan kabupaten dan komoditas akan otomatis menyesuaikan berdasarkan provinsi yang dipilih.

Hosting Model Eksternal: Mengatasi batasan ukuran file GitHub dengan menghosting model machine learning (.pkl) di AWS S3 dan mengunduhnya saat aplikasi pertama kali dijalankan.

Tips Pertanian: Menyediakan bacaan dan tips praktis untuk komoditas unggulan (Padi, Jagung, Tebu, dll.).

🏗️ Arsitektur Proyek
Proyek ini menggunakan arsitektur hybrid untuk menangani file model yang besar:

GitHub: Bertindak sebagai pembuatan dan pengembangan aplikasi. Menyimpan semua kode aplikasi (app.py), data pendukung kecil (lookup_tabel.csv), dan file konfigurasi (requirements.txt).

AWS S3: penyimpanan besar seperti gudang. Berfungsi untuk Menyimpan semua file model .pkl yang ukurannya besar (di atas 100 MB).

Streamlit Community Cloud: Menjalankan aplikasi. Saat pertama kali dimulai, aplikasi akan membaca kode dari GitHub, lalu mengunduh file model dari AWS S3 untuk digunakan dalam prediksi.

🚀 Cara Menjalankan Proyek Secara Lokal (Reproduksi)
Anda dapat menjalankan aplikasi ini di komputer Anda dengan mengikuti langkah-langkah berikut.

Prasyarat
Python 3.9 - 3.13

Git

Koneksi internet (untuk mengunduh model dari S3 karena file yang cukup besar)

Langkah-Langkah Instalasi
Clone Repositori:

Bash

git clone https://github.com/Malinnyd/Capstone_Proyek.git
cd Capstone_Proyek
Buat Virtual Environment (Sangat Disarankan):

Bash

# Untuk Windows
python -m venv venv
venv\Scripts\activate

# Untuk macOS/Linux
python3 -m venv venv
source venv/bin/activate
Install Library yang Dibutuhkan: Semua library yang diperlukan sudah tercatat dalam requirements.txt.

Bash

pip install -r requirements.txt
Jalankan Aplikasi Streamlit:

Bash

streamlit run app.py
Aplikasi akan otomatis terbuka di browser Anda. Pada saat pertama kali dijalankan, Anda akan melihat pesan "Mengunduh model..." di terminal/konsol. Ini adalah proses normal di mana aplikasi mengambil file .pkl dari AWS S3.

P.S : Jika membutuhkan notebook dan datasetnya, Semuanya berada dalam folder Model_ML. Project ini dijalankan dengan menggunakan Google colab
