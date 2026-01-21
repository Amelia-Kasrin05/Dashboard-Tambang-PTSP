# ============================================================
# SETTINGS - User & Theme Configuration
# ============================================================

import hashlib
import os

# ============================================================
# PASSWORD HASHING UTILITY
# ============================================================

def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt"""
    salt = "SemenPadangMining2025"  # Static salt for simplicity
    salted = f"{salt}{password}{salt}"
    return hashlib.sha256(salted.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == hashed

# ============================================================
# USER CREDENTIALS (Hashed passwords)
# ============================================================
# Note: Run hash_password("your_password") to generate hash for new users

# Pre-computed hashes for existing passwords:
# hash_password("super123") -> "..."
# hash_password("prod123") -> "..."
# etc.

USERS = {
    "supervisor": {
        "password_hash": hash_password("super123"),
        "role": "supervisor", 
        "name": "Supervisor Tambang"
    },
    "admin_produksi": {
        "password_hash": hash_password("prod123"),
        "role": "produksi", 
        "name": "Admin Produksi"
    },
    "admin_alat": {
        "password_hash": hash_password("alat123"),
        "role": "alat", 
        "name": "Admin Alat"
    },
    "admin_bbm": {
        "password_hash": hash_password("bbm123"),
        "role": "bbm", 
        "name": "Admin BBM"
    },
    "admin_planning": {
        "password_hash": hash_password("plan123"),
        "role": "planning", 
        "name": "Admin Planning"
    },
    "admin_safety": {
        "password_hash": hash_password("safety123"),
        "role": "safety", 
        "name": "Admin Safety"
    },
}

# ============================================================
# COLOR CONFIGURATION
# ============================================================

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

# ============================================================
# PRODUCTION TARGETS
# ============================================================

DAILY_PRODUCTION_TARGET = 18000  # Target produksi harian dalam ton
DAILY_INTERNAL_TARGET = 25000  # Target internal harian dalam ton
SHIFT_HOURS = 8  # Jam kerja per shift
SHIFTS_PER_DAY = 3  # Jumlah shift per hari