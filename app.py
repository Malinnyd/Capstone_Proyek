# TUMBUH (Teknologi Unggul Menuju Budidaya Hasil Utama Hebat)

import streamlit as st
import pandas as pd
import joblib
import requests  
import os       
import pandas as pd
import datetime
import streamlit as st
from streamlit_gsheets import GSheetsConnection


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


    
        #  TAMPILKAN HASIL
    
  
if st.button("🚀 Buat Prediksi dan Rekomendasi", type="primary", use_container_width=True, key="tombol_prediksi"):
    if commodity == "- (Tidak ada data) -":
        st.error("Silakan pilih komoditas yang valid.")
    else:
        with st.spinner("⏳ Model sedang menganalisis data..."):
            
            # ---  PREDIKSI HASIL PANEN 
            prod = models["production"].predict(input_data_prediksi)[0]
            
            # ---  PREDIKSI BIAYA 
            # cap = models["capital"].predict(input_data_prediksi)[0]     # <-- DIHAPUS
            # maint = models["maintenance"].predict(input_data_prediksi)[0] # <-- DIHAPUS

            # --- REKOMENDASI PUPUK ---
            hasil_rekom = models["recommender"].recommend(
                commodity=commodity, province=province,
                soil_ph=defaults["Soil_pH"], temp_c=defaults["Temp_C"]
            )
            

            # --- Definisi biaya dasar per hektar (Rp) ---
            modal_awal_dict = {
                "Pengolahan Lahan (bajak, garu)": 1500000,
                "Pembelian Benih/Bibit Unggul": 800000,
                "Pupuk Dasar (sebelum tanam)": 1000000,
                "Sewa Lahan (jika menyewa)": 3000000,
                "Peralatan Kecil (cangkul, semprotan, dll.)": 500000
            }

            perawatan_dict = {
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
                scale_factor = 0.85 

            # --- Hitung total biaya ---
            total_modal_calc = sum(modal_awal_dict.values()) * area * scale_factor
            total_rawat_calc = sum(perawatan_dict.values()) * area * scale_factor
            total_all_calc = total_modal_calc + total_rawat_calc
            
            # Hitung biaya per hektar untuk caption
            modal_per_ha_calc = sum(modal_awal_dict.values()) * scale_factor
            rawat_per_ha_calc = sum(perawatan_dict.values()) * scale_factor
            
 
        #  TAMPILKAN HASIL (BAGIAN INI DIUBAH)
    
        st.success(" Analisis Selesai!")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📈 Prediksi Hasil Panen & Biaya")
            st.info(f"Perhitungan untuk lahan seluas **{area:.2f} hektar**.")
            st.metric("🌾 Total Estimasi Hasil Panen", f"{prod * area:,.0f} Kg")
            
            # --- GUNAKAN VARIABEL KALKULATOR MANUAL ---
            st.metric("💰 Total Estimasi Modal Awal", f"Rp {total_modal_calc:,.0f}")
            st.metric("🧾 Total Estimasi Biaya Perawatan", f"Rp {total_rawat_calc:,.0f}")
            
            # --- PERBAIKI CAPTION ---
            st.caption(f"Estimasi per hektar: {prod:,.0f} Kg/Ha, Modal Rp {modal_per_ha_calc:,.0f}/Ha, Perawatan Rp {rawat_per_ha_calc:,.0f}/Ha.")
            
            st.markdown("---") 

            # --- L ---
            with st.popover("📦 Lihat Detail Estimasi Komponen Biaya (Dinamis)"):
                st.markdown("###  Komponen Biaya Berdasarkan Luas Lahan dan Skala Usaha")

                st.info(
                    f"📏 Luas lahan **{area:.2f} ha**, faktor efisiensi **{scale_factor:.2f}** "
                    f"(estimasi biaya menyesuaikan skala usaha)"
                )

                st.write(f"💰 **Total Modal Awal:** Rp {total_modal_calc:,.0f}")
                st.write(f"🧾 **Total Biaya Perawatan:** Rp {total_rawat_calc:,.0f}")
                st.write(f"🪴 **Total Biaya Keseluruhan:** Rp {total_all_calc:,.0f}")

                # --- Tampilkan tabel detail modal dan perawatan ---
                st.markdown("#### 📊 Rincian Komponen Modal Awal (Rp)")
                df_modal = pd.DataFrame({
                    "Komponen": list(modal_awal_dict.keys()),
                    "Biaya per Ha": [f"Rp {v:,.0f}" for v in modal_awal_dict.values()],
                    "Estimasi Total": [f"Rp {v * area * scale_factor:,.0f}" for v in modal_awal_dict.values()]
                })
                st.dataframe(df_modal, hide_index=True, use_container_width=True)

                st.markdown("#### 📊 Rincian Komponen Biaya Perawatan (Rp)")
                df_rawat = pd.DataFrame({
                    "Komponen": list(perawatan_dict.keys()),
                    "Biaya per Ha": [f"Rp {v:,.0f}" for v in perawatan_dict.values()],
                    "Estimasi Total": [f"Rp {v * area * scale_factor:,.0f}" for v in perawatan_dict.values()]
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


# 🌾 PADI

with tabs[0]:
    st.markdown("## 🌾 Tips Budidaya Padi")
    st.markdown("""
    - Gunakan varietas unggul tahan penyakit seperti **Inpari 32**, **Ciherang Sub 1**.
    - Terapkan **irigasi berselang (AWD)** untuk efisiensi air hingga 30%.
    - Gunakan **pupuk seimbang (N:P:K = 5:3:2)** dan bahan organik.
    - Terapkan sistem **jajar legowo 2:1** untuk peningkatan hasil.
    - Tanam tanaman **refugia** di tepi sawah untuk menarik musuh alami hama.
    """)

    with st.expander("📗 Liu et al. (2024) – Effects of Long-Term Sustainable Inorganic Fertilization on Rice Productivity"):
        st.markdown("""
        **Ringkasan:**
        - Pemupukan anorganik seimbang (NPK) secara jangka panjang menjaga kesuburan tanah.
        - Penggunaan hanya N atau P menurunkan produktivitas karena gangguan mikroba tanah.
        - Pupuk seimbang terbukti menjaga hasil padi dalam jangka 30 tahun percobaan.

        **Implikasi Praktis:**
        - Gunakan kombinasi pupuk N, P, dan K dalam dosis seimbang.
        - Hindari hanya menambahkan nitrogen.
        """)
        st.link_button("🔗 Buka Jurnal", "https://www.mdpi.com/2073-4395/14/10/2311")

    with st.expander("📘 Zhuang et al. (2022) – Optimized Fertilization Practices for Sustainable Rice Production"):
        st.markdown("""
        **Ringkasan:**
        - Kombinasi pupuk organik dan anorganik meningkatkan efisiensi nitrogen 15–25%.
        - Teknik slow-release fertilizer mengurangi kehilangan unsur hara dan polusi air.
        - Biochar dan pupuk hayati mendukung produksi berkelanjutan.

        **Implikasi Praktis:**
        - Tambahkan bahan organik (kompos/biochar).
        - Pertimbangkan penggunaan pupuk pelepasan lambat (slow-release).
        """)
        st.link_button("🔗 Buka Jurnal", "https://link.springer.com/article/10.1007/s13593-022-00759-7")



# 🌽 JAGUNG

with tabs[1]:
    st.markdown("## 🌽 Tips Budidaya Jagung")
    st.markdown("""
    - Gunakan varietas **Bima 20 URI** atau **NK 7328** tahan kekeringan.
    - Pertahankan pH tanah 5.5–6.8.
    - Terapkan pemupukan **NPK 15-15-15 (200 kg/ha)** dan Urea susulan 150 kg/ha di umur 25 HST.
    - Lakukan rotasi tanaman dengan kacang tanah untuk menambah N alami.
    - Kendalikan ulat grayak menggunakan agen hayati *Trichogramma sp.*.
    """)

    with st.expander("📗 Ssemugenze et al. (2025) – Foliar Fertilizer for Maize Nutrient Efficiency"):
        st.markdown("""
        **Ringkasan:**
        - Pemupukan daun (foliar) meningkatkan penyerapan N, P, K saat tanah miskin hara.
        - Waktu aplikasi menentukan hasil panen optimal.
        - Kombinasi foliar + pupuk tanah meningkatkan hasil hingga 15–20%.

        **Implikasi Praktis:**
        - Gunakan pupuk foliar saat fase bunga/pengisian tongkol.
        - Perhatikan waktu dan kondisi cuaca saat aplikasi.
        """)
        st.link_button("🔗 Buka Jurnal", "https://www.mdpi.com/2073-4395/15/1/176")

    with st.expander("📘 Saputri et al. (2025) – Peran Amelioran dan Mikroba Tanah"):
        st.markdown("""
        **Ringkasan:**
        - Mikroba tanah (Actinobacteria) + amelioran meningkatkan serapan hara.
        - Efektif di tanah marginal/pasang surut dengan produktivitas naik hingga 8,4 ton/ha.
        - Meningkatkan efisiensi pupuk dan kesehatan tanah.

        **Implikasi Praktis:**
        - Gunakan pupuk hayati atau mikroorganisme tanah.
        - Tambahkan bahan pembenah tanah (amelioran) untuk lahan miskin hara.
        """)
        st.link_button("🔗 Buka Penelitian", "https://www.researchgate.net/publication/382031802_Yield_Response_and_Nutrient_Uptake_of_Shallots_by_Giving_Ameliorants_and_Actinobacteria")



# 🍬 TEBU

with tabs[2]:
    st.markdown("## 🍬 Tips Budidaya Tebu")
    st.markdown("""
    - Gunakan varietas **PSJK 922** atau **BL-4** dengan rendemen tinggi.
    - Gunakan **pupuk kandang 10 ton/ha + NPK seimbang**.
    - Lakukan pembumbunan dan perempalan agar batang seragam.
    - Pertahankan pH tanah 6.5–7.5.
    - Manfaatkan sisa batang tebu (ratoon) untuk penanaman berikutnya.
    """)

    with st.expander("📗 Mirbakhsh & Zahed (2023) – Enhancing Phosphorus Uptake in Sugarcane"):
        st.markdown("""
        **Ringkasan:**
        - Kombinasi asam humik + pupuk fosfor meningkatkan serapan P di tanah alkali.
        - Aktivitas akar meningkat signifikan → hasil naik 10–15%.
        - Peningkatan efisiensi pupuk fosfor hingga 25%.

        **Implikasi Praktis:**
        - Campurkan bahan organik/humik dalam pupuk P.
        - Uji pH tanah sebelum aplikasi fosfor.
        """)
        st.link_button("🔗 Buka Jurnal", "https://arxiv.org/abs/2309.03928")

    with st.expander("📘 Xu et al. (2021) – Sugarcane Ratooning Ability"):
        st.markdown("""
        **Ringkasan:**
        - Tanaman ratoon (tanaman ke-2/3) dapat mengurangi kebutuhan pupuk 20–30%.
        - Produktivitas bisa stabil dengan pengelolaan residu batang yang baik.
        - Sistem ratoon meningkatkan efisiensi dan menekan biaya produksi.

        **Implikasi Praktis:**
        - Pertahankan sisa batang tebu untuk ratoon berikutnya.
        - Kurangi pupuk di musim ke-2, optimalkan sisa biomassa.
        """)
        st.link_button("🔗 Buka Jurnal", "https://pmc.ncbi.nlm.nih.gov/articles/PMC8533141/")



# 🧅 BAWANG MERAH

with tabs[3]:
    st.markdown("## 🧅 Tips Budidaya Bawang Merah")
    st.markdown("""
    - Gunakan umbi benih 5–10 g dengan jarak tanam 15×15 cm.
    - Gunakan mulsa plastik untuk menjaga kelembapan.
    - Pemupukan bertahap: 0, 10, 25, 40 HST.
    - Gunakan pestisida nabati (bawang putih, daun nimba).
    """)

    with st.expander("📗 Sitorus et al. (2025) – Optimizing Shallot Growth through NPK Variation and Density"):
        st.markdown("""
        **Ringkasan:**
        - Dosis optimum: N = 126.85 kg/ha, P = 178.06 kg/ha, K = 95.25 kg/ha.
        - Jarak tanam rapat (20×10 cm) meningkatkan hasil 84%.
        - Interaksi positif antara dosis pupuk dan kerapatan tanam.

        **Implikasi Praktis:**
        - Gunakan jarak tanam rapat + dosis pupuk optimal.
        - Sesuaikan kebutuhan berdasarkan kesuburan tanah.
        """)
        st.link_button("🔗 Buka Jurnal", "https://jgiass.com/pdf-reader.php?file=Optimizing-Shallot-Growth-through-Variations-Fertilization-NPK-and--Plant-Density.pdf")

    with st.expander("📘 Sariyoga et al. (2025) – Impact of Production Factor Utilization on Shallot Production"):
        st.markdown("""
        **Ringkasan:**
        - Elastisitas faktor: lahan (0.47), pupuk (0.23), benih (0.22).
        - Peningkatan input berlebih tidak proporsional terhadap hasil.
        - Efisiensi input penting untuk menjaga keuntungan.

        **Implikasi Praktis:**
        - Gunakan pupuk dan benih secara efisien, bukan berlebihan.
        - Evaluasi efisiensi biaya setiap musim tanam.
        """)
        st.link_button("🔗 Buka Jurnal", "https://journals.nasspublishing.com/index.php/rwae/article/view/2366")



# 🌶️ CABAI RAWIT

with tabs[4]:
    st.markdown("## 🌶️ Tips Budidaya Cabai Rawit")
    st.markdown("""
    - Gunakan varietas tahan virus seperti **Dewata F1** atau **Bara F1**.
    - Gunakan ajir bambu dan pemangkasan tunas bawah.
    - Aplikasikan pestisida nabati (neem oil, tembakau, serai).
    - Panen saat 80% buah berwarna merah.
    """)

    with st.expander("📗 Wilyus et al. (2022) – Integrated Pest Management on Chili Cultivation"):
        st.markdown("""
        **Ringkasan:**
        - Model IPM (tanaman refugia + pagar jagung) menurunkan hama hingga 40%.
        - Mengurangi ketergantungan pada pestisida kimia.
        - Produksi meningkat dengan pendekatan ekologi.

        **Implikasi Praktis:**
        - Terapkan IPM: gunakan refugia, tanaman pagar, dan pestisida alami.
        - Lakukan monitoring hama secara rutin.
        """)
        st.link_button("🔗 Buka Jurnal", "https://jlsuboptimal.unsri.ac.id/index.php/jlso/article/view/579")

    with st.expander("📘 Pertiwi & Rahadian (2021) – Nutrient Management and Productivity of Chili"):
        st.markdown("""
        **Ringkasan:**
        - Kombinasi NPK 300:150:100 kg/ha + biofertilizer meningkatkan hasil 22%.
        - Pupuk berimbang menjaga produktivitas tinggi di iklim lembab.
        - Disarankan pemupukan bertahap berdasarkan fase pertumbuhan.

        **Implikasi Praktis:**
        - Gunakan pupuk berimbang dan biofertilizer.
        - Atur dosis sesuai umur tanaman cabai.
        """)
        st.link_button("🔗 Buka Jurnal", "https://doi.org/10.17503/jtcs.2021.34")


# 🗣️ SECTION: FEEDBACK DARI PENGGUNA

st.divider()
st.subheader("🗣️ Beri Feedback Anda")

# Inisialisasi koneksi ke Google Sheet
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("❌ Gagal membuat koneksi ke Google Sheets.")
    st.stop()

# Coba baca data awal dari sheet
try:
    existing_data = conn.read(worksheet="Sheet1", usecols=list(range(4)), ttl=5)
except Exception:
    existing_data = pd.DataFrame(columns=["nama", "rating", "komentar", "tanggal"])

# Pastikan kolom sudah ada
if existing_data is None or existing_data.empty:
    existing_data = pd.DataFrame(columns=["nama", "rating", "komentar", "tanggal"])


# 📝 FORMULIR FEEDBACK

with st.form("feedback_form", clear_on_submit=True):
    nama = st.text_input("Nama Anda")
    rating = st.slider("Penilaian Aplikasi (1 = Buruk, 5 = Sangat Baik)", 1, 5, 5)
    komentar = st.text_area("Tulis feedback atau saran Anda di sini...")
    submitted = st.form_submit_button("Kirim Feedback")

    if submitted:
        if nama.strip() == "" or komentar.strip() == "":
            st.warning("⚠️ Mohon isi nama dan komentar sebelum mengirim.")
        else:
            new_feedback = pd.DataFrame([{
                "nama": nama,
                "rating": rating,
                "komentar": komentar,
                "tanggal": datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
            }])

            try:
                updated_data = pd.concat([existing_data, new_feedback], ignore_index=True)
                conn.update(worksheet="Sheet1", data=updated_data)
                st.success("✅ Terima kasih! Feedback Anda berhasil disimpan ke Google Sheets.")
            except Exception as e:
                st.error("❌ Gagal menyimpan feedback ke Google Sheets. Pastikan sheet dapat diakses.")
                
# 💬 TAMPILKAN SEMUA FEEDBACK

st.divider()
st.subheader("💬 Umpan Balik dari Pengguna")

if not existing_data.empty:
    for _, fb in existing_data.iloc[::-1].iterrows():  # menampilkan terbaru di atas
        with st.container():
            st.markdown(f"**🧑 {fb['nama']}** | ⭐ {fb['rating']}/5 | *{fb['tanggal']}*")
            st.markdown(f"_{fb['komentar']}_")
            st.markdown("---")
else:
    st.info("Belum ada feedback. Jadilah yang pertama memberikan pendapat Anda!")

#  FOOTER


st.divider()
st.caption("© 2025 TUMBUH | Dikembangkan oleh **Malinny Debra (DB8-PI034) - B25B8M080** •DICODING MACHINE LEARNING BOOTCAMP BATCH 8 • Machine Learning Capstone 🌿")










