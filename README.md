# Dashboard Tambang PTSP

Mining Operations Dashboard untuk PT Semen Padang.

## 📁 Struktur Proyek

```
Dashboard-Tambang-PTSP/
├── app.py                  # Entry point (minimal)
├── config/
│   ├── __init__.py
│   ├── settings.py         # User & theme config
│   └── onedrive.py         # OneDrive & file paths
├── utils/
│   ├── __init__.py
│   ├── data_loader.py      # Data loading functions
│   └── helpers.py          # Utility functions
├── components/
│   ├── __init__.py
│   ├── styles.py           # CSS styling
│   ├── login.py            # Login page & auth
│   └── sidebar.py          # Sidebar navigation
├── pages/
│   ├── __init__.py
│   ├── dashboard.py        # Main dashboard
│   ├── produksi.py         # Production page
│   ├── gangguan.py         # Incident page
│   ├── monitoring.py       # Monitoring page
│   └── daily_plan.py       # Daily plan page
├── assets/
│   └── logo_semen_padang.jpg
├── data/                   # Local data folder
├── requirements.txt
├── .gitignore
└── README.md
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
- **Password:** `prod123`

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
