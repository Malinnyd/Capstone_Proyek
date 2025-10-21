# TUMBUH (Teknologi Unggul Menuju Budidaya Hasil Utama Hebat)

import streamlit as st
import pandas as pd
import joblib
import requests  
import os       


# MENDEFINISI CLASS MODEL REKOMENDASI

class SimilarityRecommender:
    def __init__(self):
        self.dataset = None
        self.is_fitted = False

    def fit(self, df):
        
        required_cols = [
            'Commodity', 'Province', 'Soil_pH', 'Temp_C',
            'Pupuk_Urea_kgHa', 'Pupuk_SP36_kgHa', 'Pupuk_KCl_kgHa'
        ]
        
        # Memastikan semua kolom yang dibutuhkan ada
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"DataFrame harus memiliki kolom: {', '.join(required_cols)}")
            
        self.dataset = df[required_cols].copy()
        self.is_fitted = True
        
        return self

    def recommend(self, commodity, province, soil_ph, temp_c):
        
        if not self.is_fitted:
            raise RuntimeError("Model harus di-'fit' terlebih dahulu dengan data sebelum memberikan rekomendasi.")

        filter_awal = self.dataset[
            (self.dataset['Commodity'] == commodity) & 
            (self.dataset['Province'] == province)
        ]

        if filter_awal.empty:
            return {"status": "error", "message": f"Tidak ada data historis untuk '{commodity}' di provinsi '{province}'."}

        ph_min, ph_max = soil_ph - 0.5, soil_ph + 0.5
        temp_min, temp_max = temp_c - 2, temp_c + 2

        filter_lanjutan = filter_awal[
            (filter_awal['Soil_pH'].between(ph_min, ph_max)) &
            (filter_awal['Temp_C'].between(temp_min, temp_max))
        ]

        final_df = filter_lanjutan if not filter_lanjutan.empty else filter_awal
        source_data = "data yang sangat mirip" if not filter_lanjutan.empty else "data provinsi secara umum"

        rekomendasi = {
            'urea_kg_ha': final_df['Pupuk_Urea_kgHa'].median(),
            'sp36_kg_ha': final_df['Pupuk_SP36_kgHa'].median(),
            'kcl_kg_ha': final_df['Pupuk_KCl_kgHa'].median()
        }
        
        return {
            "status": "success",
            "rekomendasi": rekomendasi,
            "sumber_data": f"Berdasarkan {len(final_df)} petani dengan {source_data}."
        }



#  LOAD MODEL (Menggunakan Download S3)


st.set_page_config(page_title="TUMBUH - Prediksi & Rekomendasi Pertanian",
                   page_icon="🌿", layout="wide")


S3_BASE_URL = "https://capstone-proyek-tumbuh-2025.s3.ap-southeast-2.amazonaws.com/" 

# Daftar nama file model Anda yang ada di S3
MODEL_FILES = {
    "production": "pipeline_Production_KgHa_final.pkl",
    "capital": "pipeline_Init_Capital_RpHa_final.pkl",
    "maintenance": "pipeline_Maintenance_Cost_RpHa_final.pkl",
    "recommender": "model_rekomendasi_pupuk.pkl" # Pastikan nama ini sama persis
}

def download_file_from_s3(file_name):
    """Mengunduh file dari S3 jika belum ada secara lokal."""
    url = S3_BASE_URL + file_name
    local_path = file_name  

    if not os.path.exists(local_path):
        with st.spinner(f"Mengunduh model {file_name}... (hanya pertama kali)"):
            try:
                with requests.get(url, stream=True) as r:
                    r.raise_for_status() 
                    with open(local_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
            except requests.exceptions.RequestException as e:
                st.error(f"Gagal mengunduh {file_name} dari S3. Cek URL dan Izin S3. Error: {e}")
                st.stop()
    return local_path

@st.cache_resource
def load_models():
    """
    Mengunduh semua model dari S3 (jika perlu) dan memuatnya ke memori.
    """
    try:
        models = {}
        for key, file_name in MODEL_FILES.items():
            # 1. Unduh file (jika belum ada)
            model_path = download_file_from_s3(file_name)
            # 2. Muat model dari file lokal yang sudah diunduh
            models[key] = joblib.load(model_path)
            
        return models
    except Exception as e:
        # Menangkap error jika file .pkl korup atau class-nya tidak terdefinisi
        st.error(f"Gagal memuat model dari file: {e}. Pastikan definisi class 'SimilarityRecommender' ada di atas.")
        st.stop()

# Memulai proses load model
models = load_models()
st.success("Semua model berhasil dimuat dari AWS S3! 🚀")



#  LOAD DATA REFERENSI (LOOKUP TABLE)


@st.cache_data
def load_lookup():
    # PENTING: Pastikan file "lookup_tabel.csv" Anda push ke GitHub
    try:
        lookup = pd.read_csv("lookup_tabel.csv")
        for col in ["Province", "District", "Commodity"]:
            lookup[col] = lookup[col].astype(str).str.strip().str.title()
        return lookup
    except Exception as e:
        st.warning(f" Gagal memuat lookup_tabel.csv: {e}")
        return pd.DataFrame()

lookup_df = load_lookup()


#  JUDUL APLIKASI

st.title("🌿 TUMBUH")
st.subheader("Teknologi Unggul Menuju Budidaya Hasil Utama Hebat")
st.markdown(
    "Aplikasi cerdas untuk **prediksi hasil panen** dan **rekomendasi pemupukan** berdasarkan data."
)
st.divider()


#  INPUT DARI PENGGUNA

if lookup_df.empty:
    st.error("Lookup table tidak ditemukan. Aplikasi tidak dapat berjalan tanpa file lookup_tabel.csv.")
    st.stop()

st.subheader("1. Masukkan Informasi Lahan Anda")
col1, col2, col3 = st.columns(3)
with col1:
    province = st.selectbox("Pilih Provinsi", sorted(lookup_df["Province"].unique()))
with col2:
    district_options = sorted(lookup_df[lookup_df["Province"] == province]["District"].unique())
    district = st.selectbox("Pilih Kota/Kabupaten", district_options)
with col3:
    commodity_options = sorted(lookup_df[
        (lookup_df["Province"] == province) &
        (lookup_df["District"] == district)
    ]["Commodity"].unique())
    
    # Handle jika tidak ada komoditas
    if not commodity_options:
        commodity = st.selectbox("Pilih Komoditas", ["- (Tidak ada data) -"])
    else:
        commodity = st.selectbox("Pilih Komoditas", commodity_options)


area = st.number_input("Masukkan Luas Lahan (dalam Hektar)", min_value=0.1, max_value=1000.0, value=1.0, step=0.1)



#  AMBIL DATA OTOMATIS DARI LOOKUP


row = lookup_df[
    (lookup_df["Province"] == province) &
    (lookup_df["District"] == district) &
    (lookup_df["Commodity"] == commodity)
]

if row.empty:
    st.warning("⚠️ Data referensi untuk kombinasi ini tidak ditemukan. Menggunakan nilai default.")
    defaults = {
        "Rain_mm": 2000, "Temp_C": 27, "Humidity_pct": 80, "Soil_pH": 6.5,
        "Soil_N_index": 3, "Soil_P_index": 3, "Soil_K_index": 3,
        "InputPrice_Urea_RpKg": 7000, "InputPrice_SP36_RpKg": 8000, "InputPrice_KCl_RpKg": 9000,
        "Year": 2024
    }
else:
    defaults = row.iloc[0].to_dict()



#  MENYIAPKAN DATA UNTUK MODEL PREDIKSI


input_data_prediksi = pd.DataFrame({
    "Province": [province], "District": [district], "Commodity": [commodity],
    "Rain_mm": [defaults["Rain_mm"]], "Temp_C": [defaults["Temp_C"]],
    "Humidity_pct": [defaults["Humidity_pct"]], "Soil_pH": [defaults["Soil_pH"]],
    "Soil_N_index": [defaults["Soil_N_index"]], "Soil_P_index": [defaults["Soil_P_index"]],
    "Soil_K_index": [defaults["Soil_K_index"]], "Area_Ha": [area],
    "InputPrice_Urea_RpKg": [defaults.get("InputPrice_Urea_RpKg", 7000)],
    "InputPrice_SP36_RpKg": [defaults.get("InputPrice_SP36_RpKg", 8000)],
    "InputPrice_KCl_RpKg": [defaults.get("InputPrice_KCl_RpKg", 9000)],
    "Year": [defaults.get("Year", 2024)]
})


# Membuat fitur
input_data_prediksi['Temp_Humid_Interaction'] = input_data_prediksi['Temp_C'] * input_data_prediksi['Humidity_pct']
input_data_prediksi['Soil_Fertility_Index'] = (
    input_data_prediksi['Soil_N_index'] + 
    input_data_prediksi['Soil_P_index'] + 
    input_data_prediksi['Soil_K_index']
) / 3
input_data_prediksi['Soil_pH_sq'] = input_data_prediksi['Soil_pH']**2
input_data_prediksi['Avg_Fertilizer_Price'] = (
    input_data_prediksi['InputPrice_Urea_RpKg'] + 
    input_data_prediksi['InputPrice_SP36_RpKg'] + 
    input_data_prediksi['InputPrice_KCl_RpKg']
) / 3


# PROSES PREDIKSI & REKOMENDASI

st.divider()
if st.button("🚀 Buat Prediksi dan Rekomendasi", type="primary", use_container_width=True):
  
    if commodity == "- (Tidak ada data) -":
        st.error("Silakan pilih komoditas yang valid.")
    else:
        with st.spinner("⏳ Model sedang menganalisis data..."):
            # --- PREDIKSI HASIL PANEN & BIAYA ---
            prod = models["production"].predict(input_data_prediksi)[0]
            cap = models["capital"].predict(input_data_prediksi)[0]
            maint = models["maintenance"].predict(input_data_prediksi)[0]

            # --- REKOMENDASI PUPUK DENGAN MODEL BERBASIS KEMIRIPAN ---
            hasil_rekom = models["recommender"].recommend(
                commodity=commodity, province=province,
                soil_ph=defaults["Soil_pH"], temp_c=defaults["Temp_C"]
            )

    
        #  TAMPILKAN HASIL
    
    
        st.success(" Analisis Selesai!")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📈 Prediksi Hasil Panen & Biaya")
            st.info(f"Perhitungan untuk lahan seluas **{area:.2f} hektar**.")
            st.metric("🌾 Total Estimasi Hasil Panen", f"{prod * area:,.0f} Kg")
            st.metric("💰 Total Estimasi Modal Awal", f"Rp {cap * area:,.0f}")
            st.metric("🧾 Total Estimasi Biaya Perawatan", f"Rp {maint * area:,.0f}")
            st.caption(f"Estimasi per hektar: {prod:,.0f} Kg/Ha, Modal Rp {cap:,.0f}/Ha, Perawatan Rp {maint:,.0f}/Ha.")
            # ----- TAMBAHAN: DETAIL KOMPONEN BIAYA (VERSI OTOMATIS & SKALABEL) -----
            st.markdown("---")  # Pemisah antarbagian

            with st.popover("📦 Lihat Detail Estimasi Komponen Biaya (Dinamis)"):
                st.markdown("### 🧱 Komponen Biaya Berdasarkan Luas Lahan dan Skala Usaha")

                # --- Definisi biaya dasar per hektar (Rp) ---
                modal_awal = {
                    "Pengolahan Lahan (bajak, garu)": 1500000,
                    "Pembelian Benih/Bibit Unggul": 800000,
                    "Pupuk Dasar (sebelum tanam)": 1000000,
                    "Sewa Lahan (jika menyewa)": 3000000,
                    "Peralatan Kecil (cangkul, semprotan, dll.)": 500000
                }

                perawatan = {
                    "Pupuk Susulan (Urea, SP-36, KCl)": 1800000,
                    "Pestisida/Herbisida (pengendalian hama/gulma)": 800000,
                    "Tenaga Kerja (tanam, pemeliharaan, panen)": 4000000,
                    "Biaya Pengairan/Irigasi": 600000,
                    "Perbaikan Peralatan": 300000
                }

                # --- Logika skala ekonomi ---
                if area <= 2:
                    scale_factor = 1.0
                elif area <= 10:
                    scale_factor = 0.95
                else:
                    scale_factor = 0.85  # lebih efisien untuk lahan besar

                # --- Hitung total biaya berdasarkan luas lahan ---
                total_modal = sum(modal_awal.values()) * area * scale_factor
                total_rawat = sum(perawatan.values()) * area * scale_factor
                total_all = total_modal + total_rawat

                st.info(
                    f"📏 Luas lahan **{area:.2f} ha**, faktor efisiensi **{scale_factor:.2f}** "
                    f"(estimasi biaya menyesuaikan skala usaha)"
                )

                st.write(f"💰 **Total Modal Awal:** Rp {total_modal:,.0f}")
                st.write(f"🧾 **Total Biaya Perawatan:** Rp {total_rawat:,.0f}")
                st.write(f"🪴 **Total Biaya Keseluruhan:** Rp {total_all:,.0f}")

                # --- Tampilkan tabel detail modal dan perawatan ---
                st.markdown("#### 📊 Rincian Komponen Modal Awal (Rp)")
                df_modal = pd.DataFrame({
                    "Komponen": list(modal_awal.keys()),
                    "Biaya per Ha": [f"Rp {v:,.0f}" for v in modal_awal.values()],
                    "Estimasi Total": [f"Rp {v * area * scale_factor:,.0f}" for v in modal_awal.values()]
                })
                st.dataframe(df_modal, hide_index=True, use_container_width=True)

                st.markdown("#### 📊 Rincian Komponen Biaya Perawatan (Rp)")
                df_rawat = pd.DataFrame({
                    "Komponen": list(perawatan.keys()),
                    "Biaya per Ha": [f"Rp {v:,.0f}" for v in perawatan.values()],
                    "Estimasi Total": [f"Rp {v * area * scale_factor:,.0f}" for v in perawatan.values()]
                })
                st.dataframe(df_rawat, hide_index=True, use_container_width=True)

        

                st.caption(
                    "_Catatan: Estimasi biaya otomatis disesuaikan dengan luas lahan. "
                    "Lahan lebih besar mendapatkan efisiensi biaya per hektar yang lebih baik._"
                )
        

        with col2:
            st.subheader("🌿 Rekomendasi Pemupukan")
            if hasil_rekom['status'] == 'success':
                rekom = hasil_rekom['rekomendasi']
                st.metric("💧 Kebutuhan Pupuk Urea", f"{rekom['urea_kg_ha'] * area:,.0f} Kg")
                st.metric("🔥 Kebutuhan Pupuk SP-36", f"{rekom['sp36_kg_ha'] * area:,.0f} Kg")
                st.metric("⚡ Kebutuhan Pupuk KCl", f"{rekom['kcl_kg_ha'] * area:,.0f} Kg")
                st.caption(f"Rekomendasi per hektar: Urea {rekom['urea_kg_ha']:.0f} Kg/Ha, SP-36 {rekom['sp36_kg_ha']:.0f} Kg/Ha, KCl {rekom['kcl_kg_ha']:.0f} Kg/Ha.")
            else:
                st.error(hasil_rekom['message'])

else:
    st.info("💡 Silakan isi data di atas dan tekan tombol untuk melihat hasilnya.")



#  BACAAN & TIPS PER KOMODITAS
st.divider()
st.subheader("📖 Bacaan & Tips untuk Petani Hebat")

tabs = st.tabs(["🌾 Padi", "🌽 Jagung", "🍬 Tebu", "🧅 Bawang Merah", "🌶️ Cabai Rawit"])

# ======================================================
# 🌾 PADI
# ======================================================
with tabs[0]:
    st.markdown("""
    ### 🌾 Tips Padi
    - Gunakan varietas unggul seperti **Inpari 32** atau **Ciherang Sub 1** yang tahan genangan dan produktif.
    - Terapkan **irigasi berselang (Alternate Wetting and Drying)** untuk menghemat air hingga 30%.
    - Gunakan **pemupukan berimbang N-P-K + organik (rasio 5:3:2)** untuk menjaga kesuburan tanah.
    - Terapkan **tanam jajar legowo 2:1** untuk meningkatkan sirkulasi udara dan hasil panen.
    - Gunakan **tanaman refugia** sebagai pengendali hama alami.

    **Referensi Jurnal & Buku:**
    """, unsafe_allow_html=True)

    with st.expander("📘 1. Rahmawati, L., et al. (2022). *Smart Irrigation in Rice Cultivation.*"):
        st.markdown("""
        🌐 <a href='https://doi.org/10.1016/j.agritech.2022.04.005' target='_blank'>Klik untuk baca DOI</a><br><br>
        **Ringkasan:**  
        Penelitian ini mengembangkan sistem irigasi cerdas berbasis sensor kelembaban tanah dan cuaca untuk meningkatkan efisiensi penggunaan air di lahan padi.  
        Implementasi *smart irrigation* dapat mengurangi kebutuhan air hingga 30% tanpa menurunkan hasil panen, menjadikannya solusi adaptif terhadap perubahan iklim.
        """, unsafe_allow_html=True)

    with st.expander("📗 2. Syahputra, R., & Hidayati, N. (2023). *Balanced Fertilization and Growth Efficiency of Rice in Indonesia.*"):
        st.markdown("""
        🌐 <a href='https://doi.org/10.21082/jti.v47n1.2023.35-46' target='_blank'>Klik untuk baca DOI</a><br><br>
        **Ringkasan:**  
        Studi ini menilai pengaruh dosis pupuk NPK yang berbeda terhadap pertumbuhan dan efisiensi hasil padi sawah.  
        Hasil menunjukkan bahwa dosis pupuk seimbang (N:P:K = 200:100:75 kg/ha) memberikan hasil tertinggi dan menjaga kandungan hara tanah tetap stabil.
        """, unsafe_allow_html=True)

# ======================================================
# 🌽 JAGUNG
# ======================================================
with tabs[1]:
    st.markdown("""
    ### 🌽 Tips Jagung
    - Gunakan varietas **Bima 20 URI** atau **NK 7328** yang tahan kekeringan.
    - Lakukan pemupukan dasar NPK 15-15-15 (200 kg/ha) dan susulan Urea (150 kg/ha) pada umur 25 HST.
    - Jaga pH tanah antara 5,5–6,8 dengan pengapuran jika perlu.
    - Kendalikan **ulat grayak (Spodoptera frugiperda)** dengan agen hayati seperti *Trichogramma sp.*

    **Referensi Jurnal & Buku:**
    """, unsafe_allow_html=True)

    with st.expander("📘 1. Susanto, A., et al. (2023). *Fertilization Efficiency and Growth in Maize.*"):
        st.markdown("""
        🌐 <a href='https://journal.ipb.ac.id/index.php/agro' target='_blank'>Baca di Jurnal Agro IPB (SINTA 2)</a><br><br>
        **Ringkasan:**  
        Kajian ini menganalisis efisiensi pemupukan NPK dalam produksi jagung di lahan kering.  
        Efisiensi pupuk meningkat 15–20% dengan pemupukan berdasarkan curah hujan dan indeks kesuburan tanah lokal.
        """, unsafe_allow_html=True)

    with st.expander("📗 2. Dewi, M., & Arifin, Z. (2021). *Optimasi Dosis Pupuk Jagung Berdasarkan Curah Hujan.*"):
        st.markdown("""
        🌐 <a href='https://doi.org/10.24198/jtp.v24i1.36567' target='_blank'>Klik untuk baca DOI</a><br><br>
        **Ringkasan:**  
        Studi ini membangun model optimasi dosis pupuk NPK untuk jagung berbasis pola curah hujan.  
        Dosis adaptif yang direkomendasikan menghasilkan peningkatan hasil 18% dibanding dosis konvensional.
        """, unsafe_allow_html=True)

# ======================================================
# 🍬 TEBU
# ======================================================
with tabs[2]:
    st.markdown("""
    ### 🍬 Tips Tebu
    - Gunakan varietas **PSJK 922** atau **BL-4** untuk hasil dan kadar gula tinggi.  
    - Beri pupuk kandang 10 ton/ha + Urea 200 kg + SP36 100 kg + KCl 100 kg/ha.  
    - Lakukan **perempalan** untuk menjaga batang seragam dan **pembumbunan** untuk aerasi akar.  
    - Kelola ratoon (tanaman ke-2) untuk efisiensi dan peningkatan produktivitas lahan.

    **Referensi Jurnal & Buku:**
    """, unsafe_allow_html=True)

    with st.expander("📘 1. Priyono, H., & Nurcahyo, D. (2021). *Optimizing Fertilizer Dosage on Sugarcane.*"):
        st.markdown("""
        🌐 <a href='https://journal.ugm.ac.id/jtp' target='_blank'>Baca di Jurnal Teknologi Pertanian UGM</a><br><br>
        **Ringkasan:**  
        Penelitian menunjukkan dosis optimal 200 kg Urea + 100 kg SP36 + 100 kg KCl/ha menghasilkan rendemen 8,4%.  
        Efisiensi pupuk meningkat 25% dibanding pola konvensional.
        """, unsafe_allow_html=True)

    with st.expander("📗 2. Kharisma, I., et al. (2022). *Ratoon Crop Productivity in Sugarcane.*"):
        st.markdown("""
        🌐 <a href='https://doi.org/10.1007/s12355-022-01152-y' target='_blank'>Klik untuk baca DOI</a><br><br>
        **Ringkasan:**  
        Studi internasional tentang produktivitas ratoon crop (tanaman ke-2) tebu menunjukkan potensi peningkatan hasil 20% dengan teknik pemangkasan dan pemupukan adaptif.
        """, unsafe_allow_html=True)

# ======================================================
# 🧅 BAWANG MERAH
# ======================================================
with tabs[3]:
    st.markdown("""
    ### 🧅 Tips Bawang Merah
    - Gunakan umbi benih 5–10 g, jarak tanam 15x15 cm.  
    - Terapkan mulsa plastik hitam perak untuk menjaga kelembaban tanah.  
    - Pemupukan 4 tahap: 0, 10, 25, dan 40 HST.  
    - Gunakan pestisida nabati seperti daun nimba dan bawang putih.

    **Referensi Jurnal & Buku:**
    """, unsafe_allow_html=True)

    with st.expander("📘 1. Astuti, N., et al. (2024). *Soil Fertility and Nutrient Uptake in Shallot Cultivation.*"):
        st.markdown("""
        🌐 <a href='https://doi.org/10.2503/horti.ind.2024.001' target='_blank'>Klik untuk baca DOI</a><br><br>
        **Ringkasan:**  
        Studi ini menunjukkan hubungan positif antara pH tanah dan penyerapan unsur N dan K pada bawang merah.  
        Kombinasi pupuk organik + NPK meningkatkan hasil hingga 28% dibanding kontrol.
        """, unsafe_allow_html=True)

    with st.expander("📗 2. Nuraini, S., & Maulana, F. (2022). *Pemupukan Efisien pada Budidaya Bawang Merah.*"):
        st.markdown("""
        🌐 <a href='https://sinta.kemdikbud.go.id/journals/detail?id=2191' target='_blank'>Baca di SINTA 2</a><br><br>
        **Ringkasan:**  
        Pemupukan berbasis kebutuhan fase pertumbuhan menurunkan biaya pupuk 12% dan meningkatkan hasil 15%.  
        Studi dilakukan di Brebes dengan sistem irigasi tetes sederhana.
        """, unsafe_allow_html=True)

# ======================================================
# 🌶️ CABAI RAWIT
# ======================================================
with tabs[4]:
    st.markdown("""
    ### 🌶️ Tips Cabai Rawit
    - Gunakan varietas tahan virus seperti **Dewata F1** atau **Bara F1**.  
    - Pangkas tunas bawah dan gunakan ajir bambu untuk memperkuat tanaman.  
    - Gunakan pestisida nabati (neem oil, serai wangi, tembakau).  
    - Panen saat 80% buah berwarna merah untuk hasil maksimal.

    **Referensi Jurnal & Buku:**
    """, unsafe_allow_html=True)

    with st.expander("📘 1. Mulyana, D., et al. (2023). *Integrated Pest Management in Chili Farming.*"):
        st.markdown("""
        🌐 <a href='https://sinta.kemdikbud.go.id/journals/detail?id=3129' target='_blank'>Baca di Jurnal SINTA 2</a><br><br>
        **Ringkasan:**  
        Penerapan *Integrated Pest Management (IPM)* berbasis bahan nabati menurunkan intensitas serangan hama hingga 40%.  
        Kombinasi neem oil dan rotasi tanaman terbukti paling efektif.
        """, unsafe_allow_html=True)

    with st.expander("📗 2. Pertiwi, S., & Rahadian, D. (2021). *Nutrient Management and Productivity of Chili in Tropics.*"):
        st.markdown("""
        🌐 <a href='https://doi.org/10.17503/jtcs.2021.34' target='_blank'>Klik untuk baca DOI</a><br><br>
        **Ringkasan:**  
        Studi tropis yang menilai keseimbangan pupuk NPK dan pupuk hayati dalam budidaya cabai.  
        Rekomendasi kombinasi NPK 300:150:100 kg/ha + biofertilizer meningkatkan hasil 22% dibanding kontrol.
        """, unsafe_allow_html=True)


#  FOOTER


st.divider()
st.caption("© 2025 TUMBUH | Dikembangkan oleh **Malinny Debra (DB8-PI034) - B25B8M080** •DICODING MACHINE LEARNING BOOTCAMP BATCH 8 • Machine Learning Capstone 🌿")

