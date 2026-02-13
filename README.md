# Dashboard Tambang PTSP

Mining Operations Dashboard PT Semen Padang.

## 📁 Struktur Proyek

```
Dashboard-Tambang-PTSP/
├── app.py                  # Entry point
├── config/
│   ├── settings.py         # Configuration & Constants
│   └── onedrive.py         # OneDrive Integration
├── views/                  # Dashboard Pages
│   ├── dashboard.py        # Executive Summary
│   ├── produksi.py         # Production Analysis
│   ├── gangguan.py         # Downtime Analysis
│   ├── ritase.py           # Ritase/Trip Analysis
│   ├── shipping.py         # Shipping Analysis
│   └── daily_plan.py       # Daily Plan Monitor
├── components/             # UI Components
│   ├── login.py            # Authentication
│   └── sidebar.py          # Navigation Sidebar
├── utils/                  # Helper Functions
│   ├── data_loader.py      # Excel Processing
│   └── db_manager.py       # Database Operations
├── assets/                 # Static Assets
└── requirements.txt
```

## 🚀 Cara Menjalankan

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Jalankan aplikasi:
```bash
streamlit run app.py
```

## 🔐 Demo Login

- **Username:** `admin_produksi`
- **Password:** `admin` (atau `prod123` jika belum direset)

## 📊 Fitur

- Dashboard overview dengan KPI cards
- Analisis produksi detail dengan filter
- Visualisasi interaktif (charts, heatmaps)
- Export data ke CSV
- Multi-user authentication

## ⚙️ Konfigurasi

### OneDrive
Edit `config/onedrive.py` untuk mengatur path OneDrive dan file Excel.

### Users
Edit `config/settings.py` untuk menambah/mengubah user credentials.

## 📝 License

© 2025 PT Semen Padang
