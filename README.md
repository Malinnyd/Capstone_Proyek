# TUMBUH 🌱
Website Prediksi Hasil Panen dengan Machine Learning

##  Deskripsi
Project ini adalah aplikasi website yang dapat memprediksi hasil panen berdasarkan input user seperti:
- Lokasi
- Luas lahan
- Komoditas tumbuhan

Aplikasi ini terintegrasi dengan model Machine Learning, database, dan website frontend.

##  Struktur Folder
.
├── Backend/                      # API & Model siap pakai
│   ├── requirements.txt          # Dependency Python
│   ├── model_rekomendasi_pupuk.pkl
│   ├── xgboost_model_Init_Capital_RpHa.pkl
│   ├── xgboost_model_Maintenance_Cost_RpHa.pkl
│   ├── xgboost_model_Production_KgHa.pkl
│   └── venv/                     # Virtual environment (opsional untuk dicantumkan)
│
├── Frontend/ (SOON)                    # 
│   └── ...                      		 # 
│
├── Model_Machine_Learning/       # Training & eksperimen ML
│   ├── Capstone_Project.ipynb    # Notebook training
│   ├── capstone_project.py       # Script Python training
│   └── Dataset_pertanian_dengan_pupuk.csv
│
└── README.md                     # Dokumentasi project
