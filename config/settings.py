# ============================================================
# SETTINGS - User & Theme Configuration
# ============================================================

USERS = {
    "supervisor": {"password": "super123", "role": "supervisor", "name": "Supervisor Tambang"},
    "admin_produksi": {"password": "prod123", "role": "produksi", "name": "Admin Produksi"},
    "admin_alat": {"password": "alat123", "role": "alat", "name": "Admin Alat"},
    "admin_bbm": {"password": "bbm123", "role": "bbm", "name": "Admin BBM"},
    "admin_planning": {"password": "plan123", "role": "planning", "name": "Admin Planning"},
    "admin_safety": {"password": "safety123", "role": "safety", "name": "Admin Safety"},
}

COLORS = {
    "primary": "#00C853",
    "secondary": "#2196F3",
    "danger": "#FF5252",
    "warning": "#FFD600",
    "info": "#00BCD4",
    "dark": "#1a1a2e",
    "card": "#16213e",
}

CHART_COLORS = [
    "#00E676", "#2979FF", "#FF6D00",
    "#D500F9", "#FFEA00", "#00E5FF",
    "#FF1744", "#76FF03"
]

# Mining color palette for charts
MINING_COLORS = {
    'gold': '#d4a84b',
    'blue': '#3b82f6',
    'green': '#10b981',
    'red': '#ef4444',
    'orange': '#f59e0b',
    'purple': '#8b5cf6',
    'cyan': '#06b6d4',
    'slate': '#64748b'
}

CHART_SEQUENCE = [
    '#d4a84b', '#3b82f6', '#10b981', '#f59e0b', 
    '#8b5cf6', '#06b6d4', '#ef4444', '#ec4899'
]

# Di bagian bawah file settings.py, pastikan ada:

MINING_COLORS = {
    'gold': '#d4a84b',
    'blue': '#3b82f6',
    'green': '#10b981',
    'red': '#ef4444',
    'orange': '#f59e0b',
    'purple': '#8b5cf6',
    'cyan': '#06b6d4',
    'slate': '#64748b'
}

CHART_SEQUENCE = [
    '#d4a84b', '#3b82f6', '#10b981', '#f59e0b', 
    '#8b5cf6', '#06b6d4', '#ef4444', '#ec4899'
]