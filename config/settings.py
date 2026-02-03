# ============================================================
# SETTINGS - Centralized Configuration
# ============================================================
import os
import hashlib
from pathlib import Path

# ============================================================
# 1. PATHS & ENVIRONMENT
# ============================================================
BASE_DIR = Path(__file__).parent.parent.absolute()
ASSETS_DIR = BASE_DIR / "assets"

# User Data Paths
USER_HOME = Path.home()
ONEDRIVE_PATH = USER_HOME / "OneDrive" / "Dashboard_Tambang"

DEFAULT_EXCEL_PATH = str(ONEDRIVE_PATH / "Monitoring.xlsx")
PRODUKSI_EXCEL_PATH = str(ONEDRIVE_PATH / "Produksi_UTSG_Harian.xlsx")
GANGGUAN_EXCEL_PATH = str(ONEDRIVE_PATH / "Gangguan_Produksi.xlsx")

MONITORING_EXCEL_PATH = os.getenv("MONITORING_FILE", DEFAULT_EXCEL_PATH)
PRODUKSI_FILE = os.getenv("PRODUKSI_FILE", PRODUKSI_EXCEL_PATH)
GANGGUAN_FILE = os.getenv("GANGGUAN_FILE", GANGGUAN_EXCEL_PATH)

# ============================================================
# ONEDRIVE CONFIGURATION (PUBLIC LINKS)
# ============================================================
# Paste your OneDrive Share Links here.
# Format: "https://1drv.ms/x/s!Am..."
# NOTE: Ensure the link permission is set to "Anyone with the link" (Public)
ONEDRIVE_LINKS = {
    "produksi": "https://1drv.ms/x/c/07c1e1a8c3295b87/IQDvrAVlr7kFSrpX8-QHXuOnAd7QThWBm_Q2N5J7gzjuLSk?e=s0KJKk",        # Produksi
    "gangguan": "https://1drv.ms/x/c/07c1e1a8c3295b87/IQC0vxKHmHKqQb1xtVoNmbVbAbVkNIf6HNZ3NHs6Ja0w0Wc?e=PmQT07",        # Gangguan
    "monitoring": "https://1drv.ms/x/c/07c1e1a8c3295b87/IQCjeUwfc43DRJf4GO-ZcP42ASvhhEDn2xJj6HfDtE7ezlc?e=pqHs9l",      # Monitoring
    "daily_plan": "https://1drv.ms/x/c/07c1e1a8c3295b87/IQCdHgs2Q48oS6df5eUtFl2VAQXoPUVPMPSKVraYYeJF4d4?e=gtrFsF",      # Daily Plan
    "shipping": "",   # Paste Link for Shipping.xlsx
    "stockpile": ""   # Paste Link for Stockpile.xlsx
}

# Try to load from Streamlit Secrets if available (prioritized for Cloud)
try:
    import streamlit as st
    if hasattr(st, "secrets") and "onedrive" in st.secrets:
        for key in ONEDRIVE_LINKS.keys():
            if key in st.secrets["onedrive"]:
                ONEDRIVE_LINKS[key] = st.secrets["onedrive"][key]
except:
    pass

CACHE_TTL = 300

def get_monitoring_path():
    if os.path.exists(MONITORING_EXCEL_PATH):
        return MONITORING_EXCEL_PATH
    return None

def get_assets_path(filename):
    return str(ASSETS_DIR / filename)

# ============================================================
# 2. AUTHENTICATION & USERS
# ============================================================
def hash_password(password):
    return hashlib.sha256(str(password).encode()).hexdigest()

def verify_password(password, hashed):
    return hash_password(password) == hashed

USERS = {
    "admin_produksi": {
        "name": "Admin Produksi",
        "role": "admin",
        # Hashed 'admin' (Temporary Reset)
        "password_hash": "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918"
    },
    "guest": {
        "name": "Tamu",
        "role": "viewer",
        "password_hash": hash_password("guest")
    }
}

# ============================================================
# 3. VISUAL STYLING (COLORS)
# ============================================================
MINING_COLORS = {
    'gold': '#d4a84b', 
    'blue': '#3b82f6', 
    'green': '#10b981', 
    'red': '#ef4444',
    'dark': '#0a1628',
    'light': '#f1f5f9'
}

COLORS = MINING_COLORS  # Alias

CHART_COLORS = [
    '#d4a84b', '#3b82f6', '#10b981', '#ef4444', '#f59e0b', '#8b5cf6', '#06b6d4', '#ec4899'
]

CHART_SEQUENCE = CHART_COLORS

# ============================================================
# 4. OPERATIONAL CONSTANTS
# ============================================================
APP_TITLE = "Mining Dashboard | Semen Padang"
APP_ICON = str(ASSETS_DIR / "logo_semen_padang.jpg")

# Production Targets (Default Placeholders)
DAILY_PRODUCTION_TARGET = 18000  # Ton (Plan)
DAILY_INTERNAL_TARGET = 25000    # Ton (Internal)

# Shift Configuration
SHIFT_HOURS = 8
SHIFTS_PER_DAY = 3