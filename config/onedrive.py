# ============================================================
# ONEDRIVE CONFIG - Windows Path & File Configuration
# ============================================================

import os

# ============================================================
# CACHE SETTINGS
# ============================================================
CACHE_TTL = 30  # 30 detik

# ============================================================
# ONEDRIVE LINKS (Kosongkan jika menggunakan file lokal)
# ============================================================
ONEDRIVE_LINKS = {
    "produksi": "",
    "gangguan": "",
    "monitoring": "",
    "daily_plan": "",
}

# ============================================================
# PATH LOKAL - AUTOMATIC DETECTION
# ============================================================

def get_onedrive_path():
    """Auto-detect OneDrive folder path"""
    username = os.getenv('USERNAME') or os.getenv('USER') or 'user'
    
    base_paths = [
        os.path.join('C:', 'Users', username, 'OneDrive', 'Dashboard_Tambang'),
        os.path.join('C:', 'Users', username, 'OneDrive - Personal', 'Dashboard_Tambang'),
        os.path.join('C:', 'Users', username, 'OneDrive', 'AMELIA - Personal', 'Dashboard_Tambang'),
        os.path.join('C:', 'Users', 'user', 'OneDrive', 'Dashboard_Tambang'),
        os.path.join('D:', 'OneDrive', 'Dashboard_Tambang'),
    ]
    
    for path in base_paths:
        if os.path.exists(path):
            normalized = os.path.normpath(path)
            print(f"✅ Found OneDrive folder: {normalized}")
            return normalized
    
    print("⚠️ OneDrive folder not found, using relative path")
    return "data"

ONEDRIVE_FOLDER = get_onedrive_path()

# ============================================================
# FILE PATHS
# ============================================================

LOCAL_FILE_NAMES = {
    "produksi": [
        os.path.join(ONEDRIVE_FOLDER, "Produksi_UTSG_Harian.xlsx"),
        os.path.join("data", "Produksi_UTSG_Harian.xlsx"),
        "Produksi_UTSG_Harian.xlsx",
    ],
    "gangguan": [
        os.path.join(ONEDRIVE_FOLDER, "Gangguan_Produksi_2025_baru.xlsx"),
        os.path.join("data", "Gangguan_Produksi_2025_baru.xlsx"),
        "Gangguan_Produksi_2025_baru.xlsx",
    ],
    "monitoring": [
        os.path.join(ONEDRIVE_FOLDER, "Monitoring_2025_.xlsx"),
        os.path.join("data", "Monitoring_2025_.xlsx"),
        "Monitoring_2025_.xlsx",
    ],
    "daily_plan": [
        os.path.join(ONEDRIVE_FOLDER, "DAILY_PLAN.xlsx"),
        os.path.join("data", "DAILY_PLAN.xlsx"),
        "DAILY_PLAN.xlsx",
    ],
}

# ============================================================
# DEBUG INFO
# ============================================================

def print_config_info():
    """Print configuration info for debugging"""
    print("=" * 60)
    print("🔍 ONEDRIVE CONFIG INFO")
    print("=" * 60)
    print(f"OneDrive Folder: {ONEDRIVE_FOLDER}")
    print(f"Folder exists: {os.path.exists(ONEDRIVE_FOLDER)}")
    print()
    
    for file_key, paths in LOCAL_FILE_NAMES.items():
        print(f"📄 {file_key.upper()}:")
        for path in paths:
            exists = "✅" if os.path.exists(path) else "❌"
            print(f"  {exists} {path}")
        print()
    print("=" * 60)
