import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime
import os
import sys
import base64

sys.path.append('.')
from utils.data_loader import *
from config import USERS, COLORS, CHART_COLORS
from onedrive_config import CACHE_TTL

# ============================================================
# LOGO LOADER
# ============================================================
def get_logo_base64():
    """Load logo dan convert ke base64"""
    logo_paths = [
        "logo_semen_padang.jpg",
        "logo.jpg", 
        "assets/logo.jpg",
        "static/logo.jpg",
        "images/logo.jpg"
    ]
    for path in logo_paths:
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    return base64.b64encode(f.read()).decode()
            except:
                continue
    return None

LOGO_BASE64 = get_logo_base64()

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Mining Dashboard | Semen Padang",
    page_icon="⛏️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# PROFESSIONAL MINING CSS - Navy & Gold Theme
# ============================================================
st.markdown("""
<style>
/* ===== IMPORTS ===== */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ===== ROOT VARIABLES ===== */
:root {
    --bg-primary: #0a1628;
    --bg-secondary: #0f2744;
    --bg-card: #122a46;
    --bg-card-hover: #1a3a5c;
    --accent-gold: #d4a84b;
    --accent-gold-light: #e8c97a;
    --accent-blue: #3b82f6;
    --accent-green: #10b981;
    --accent-red: #ef4444;
    --accent-orange: #f59e0b;
    --text-primary: #f1f5f9;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    --border-color: #1e3a5f;
    --shadow: 0 4px 24px rgba(0,0,0,0.4);
}

/* ===== GLOBAL STYLES ===== */
.stApp {
    background: linear-gradient(180deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
    font-family: 'Inter', -apple-system, sans-serif;
}

/* Hide default streamlit elements */
#MainMenu, footer, header {visibility: hidden;}
.block-container {padding: 1rem 2rem 2rem 2rem !important; max-width: 100% !important;}

/* ===== SIDEBAR ===== */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #071020 0%, #0a1628 100%);
    border-right: 1px solid var(--border-color);
}
section[data-testid="stSidebar"] .block-container {padding: 1rem !important;}

/* Sidebar buttons */
section[data-testid="stSidebar"] button {
    background: transparent !important;
    border: 1px solid transparent !important;
    color: var(--text-secondary) !important;
    text-align: left !important;
    transition: all 0.2s ease !important;
    border-radius: 8px !important;
    margin: 2px 0 !important;
}
section[data-testid="stSidebar"] button:hover {
    background: var(--bg-card) !important;
    border-color: var(--border-color) !important;
    color: var(--text-primary) !important;
}
section[data-testid="stSidebar"] button[kind="primary"] {
    background: linear-gradient(135deg, var(--accent-gold) 0%, #b8942f 100%) !important;
    color: #0a1628 !important;
    font-weight: 600 !important;
    border: none !important;
}

/* ===== TYPOGRAPHY ===== */
h1, h2, h3, h4 {color: var(--text-primary) !important; font-weight: 600 !important;}

.page-header {
    background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-secondary) 100%);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 1rem;
}
.page-header-icon {
    width: 56px;
    height: 56px;
    background: linear-gradient(135deg, var(--accent-gold) 0%, #b8942f 100%);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.75rem;
}
.page-header-text h1 {
    margin: 0 !important;
    font-size: 1.75rem !important;
    background: linear-gradient(90deg, var(--text-primary) 0%, var(--accent-gold-light) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.page-header-text p {
    margin: 0.25rem 0 0 0;
    color: var(--text-secondary);
    font-size: 0.9rem;
}

/* ===== KPI CARDS ===== */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin-bottom: 1.5rem;
}
.kpi-card {
    background: linear-gradient(145deg, var(--bg-card) 0%, var(--bg-secondary) 100%);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 1.25rem;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 4px;
    height: 100%;
    background: var(--card-accent, var(--accent-gold));
}
.kpi-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow);
    border-color: var(--card-accent, var(--accent-gold));
}
.kpi-icon {
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
    opacity: 0.9;
}
.kpi-label {
    font-size: 0.75rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-weight: 500;
    margin-bottom: 0.25rem;
}
.kpi-value {
    font-size: 1.75rem;
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1.2;
}
.kpi-subtitle {
    font-size: 0.8rem;
    color: var(--text-secondary);
    margin-top: 0.25rem;
}
.kpi-trend {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    font-size: 0.75rem;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    margin-top: 0.5rem;
}
.kpi-trend.up {background: rgba(16,185,129,0.15); color: var(--accent-green);}
.kpi-trend.down {background: rgba(239,68,68,0.15); color: var(--accent-red);}

/* ===== CHART CONTAINER ===== */
.chart-container {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 1.25rem;
    margin-bottom: 1rem;
}
.chart-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid var(--border-color);
}
.chart-title {
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-primary);
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.chart-badge {
    background: var(--accent-gold);
    color: var(--bg-primary);
    font-size: 0.65rem;
    font-weight: 600;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    text-transform: uppercase;
}

/* ===== SECTION DIVIDER ===== */
.section-divider {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin: 2rem 0 1.5rem 0;
}
.section-divider-line {
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, var(--border-color) 0%, transparent 100%);
}
.section-divider-text {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--accent-gold);
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* ===== LOGIN PAGE ===== */
.login-container {
    max-width: 420px;
    margin: 0 auto;
    padding: 2rem;
}
.login-card {
    background: linear-gradient(145deg, var(--bg-card) 0%, var(--bg-secondary) 100%);
    border: 1px solid var(--border-color);
    border-radius: 24px;
    padding: 2.5rem;
    box-shadow: var(--shadow);
}
.login-logo {
    text-align: center;
    margin-bottom: 2rem;
}
.login-logo-icon {
    width: 80px;
    height: 80px;
    background: linear-gradient(135deg, var(--accent-gold) 0%, #b8942f 100%);
    border-radius: 20px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 2.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 8px 32px rgba(212,168,75,0.3);
}
.login-title {
    font-size: 1.75rem;
    font-weight: 700;
    background: linear-gradient(90deg, var(--text-primary) 0%, var(--accent-gold-light) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
}
.login-subtitle {
    color: var(--text-secondary);
    font-size: 0.9rem;
    margin-top: 0.5rem;
}

/* ===== USER CARD (Sidebar) ===== */
.user-card {
    background: linear-gradient(145deg, var(--bg-card) 0%, rgba(212,168,75,0.1) 100%);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 1.25rem;
    text-align: center;
    margin-bottom: 1.5rem;
}
.user-avatar {
    width: 64px;
    height: 64px;
    background: linear-gradient(135deg, var(--accent-gold) 0%, #b8942f 100%);
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 1.75rem;
    margin-bottom: 0.75rem;
    box-shadow: 0 4px 16px rgba(212,168,75,0.3);
}
.user-name {
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
}
.user-role {
    font-size: 0.75rem;
    color: var(--accent-gold);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 0.25rem;
}

/* ===== STATUS INDICATOR ===== */
.status-grid {
    display: grid;
    gap: 0.5rem;
    margin-bottom: 1rem;
}
.status-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: var(--bg-secondary);
    border-radius: 8px;
    padding: 0.5rem 0.75rem;
    font-size: 0.8rem;
}
.status-name {color: var(--text-secondary);}
.status-value {font-weight: 500;}
.status-ok {color: var(--accent-green);}
.status-warn {color: var(--accent-orange);}
.status-err {color: var(--accent-red);}

/* ===== NAV LABEL ===== */
.nav-label {
    font-size: 0.7rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: 600;
    margin: 1rem 0 0.5rem 0.5rem;
}

/* ===== STREAMLIT OVERRIDES ===== */
div[data-testid="stMetric"] {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 1rem;
}
div[data-testid="stMetric"] label {color: var(--text-muted) !important; font-size: 0.8rem !important;}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {color: var(--text-primary) !important; font-size: 1.5rem !important;}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
    background: var(--bg-secondary);
    padding: 0.5rem;
    border-radius: 12px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    border-radius: 8px;
    color: var(--text-secondary);
    font-weight: 500;
}
.stTabs [aria-selected="true"] {
    background: var(--bg-card) !important;
    color: var(--accent-gold) !important;
}

/* Selectbox & Inputs */
div[data-baseweb="select"] > div {
    background: var(--bg-secondary) !important;
    border-color: var(--border-color) !important;
    border-radius: 8px !important;
}
div[data-baseweb="input"] > div {
    background: var(--bg-secondary) !important;
    border-color: var(--border-color) !important;
}
input {color: var(--text-primary) !important;}

/* Dataframe */
.stDataFrame {border-radius: 12px; overflow: hidden;}

/* Expander */
.streamlit-expanderHeader {
    background: var(--bg-card) !important;
    border-radius: 8px !important;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# SESSION STATE
# ============================================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.name = None
if 'current_menu' not in st.session_state:
    st.session_state.current_menu = "Dashboard"


# ============================================================
# AUTH FUNCTIONS
# ============================================================
def login(username, password):
    if username in USERS and USERS[username]['password'] == password:
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.role = USERS[username]['role']
        st.session_state.name = USERS[username]['name']
        return True
    return False

def logout():
    for key in ['logged_in', 'username', 'role', 'name']:
        st.session_state[key] = None if key != 'logged_in' else False


# ============================================================
# CHART THEME
# ============================================================
def get_chart_layout(height=350, show_legend=True):
    """Professional chart layout for mining dashboard"""
    return dict(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=height,
        margin=dict(l=20, r=20, t=40, b=40),
        font=dict(family='Inter', color='#94a3b8'),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=True,
            linecolor='#1e3a5f',
            tickfont=dict(size=11)
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(30,58,95,0.5)',
            zeroline=False,
            showline=False,
            tickfont=dict(size=11)
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=-0.2,
            xanchor='center',
            x=0.5,
            bgcolor='rgba(0,0,0,0)'
        ) if show_legend else dict(visible=False),
        hoverlabel=dict(
            bgcolor='#122a46',
            font_size=12,
            font_family='Inter'
        )
    )

# Mining color palette
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

CHART_SEQUENCE = ['#d4a84b', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4', '#ef4444', '#ec4899']


# ============================================================
# LOGIN PAGE
# ============================================================
def show_login():
    logo_base64 = LOGO_BASE64
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        # Logo section
        if logo_base64:
            logo_html = f'<img src="data:image/jpeg;base64,{logo_base64}" alt="Logo" style="width:100px; height:auto; margin-bottom:1rem; border-radius:16px; box-shadow: 0 8px 32px rgba(212,168,75,0.3);">'
        else:
            logo_html = '<div class="login-logo-icon">⛏️</div>'
        
        st.markdown(f"""
        <div class="login-container">
            <div class="login-card">
                <div class="login-logo">
                    {logo_html}
                    <h1 class="login-title">Mining Dashboard</h1>
                    <p class="login-subtitle">Semen Padang Operations Center</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form", clear_on_submit=False):
            st.markdown("##### 👤 Username")
            username = st.text_input("Username", label_visibility="collapsed", placeholder="Enter username")
            
            st.markdown("##### 🔒 Password")
            password = st.text_input("Password", type="password", label_visibility="collapsed", placeholder="Enter password")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.form_submit_button("🚀 Sign In", use_container_width=True, type="primary"):
                if login(username, password):
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")
        
        st.markdown("""
        <div style="text-align:center; margin-top:1.5rem; padding:1rem; background:rgba(212,168,75,0.1); border-radius:12px;">
            <p style="color:#94a3b8; font-size:0.85rem; margin:0;">
                <strong style="color:#d4a84b;">Demo Access:</strong><br>
                admin_produksi / prod123
            </p>
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# SIDEBAR
# ============================================================
def render_sidebar():
    logo_base64 = LOGO_BASE64
    
    with st.sidebar:
        # Logo & Brand
        if logo_base64:
            logo_html = f'<img src="data:image/jpeg;base64,{logo_base64}" alt="Logo" style="width:60px; height:auto; border-radius:10px; margin-bottom:0.5rem; box-shadow: 0 4px 16px rgba(0,0,0,0.3);">'
        else:
            logo_html = '<span style="font-size:2rem;">⛏️</span>'
        
        st.markdown(f"""
        <div style="text-align:center; padding:1rem 0 0.5rem 0;">
            {logo_html}
            <p style="color:#d4a84b; font-weight:700; font-size:1.1rem; margin:0.5rem 0 0 0;">
                MINING OPS
            </p>
            <p style="color:#64748b; font-size:0.7rem; margin:0;">Semen Padang</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # User Card
        st.markdown(f"""
        <div class="user-card">
            <div class="user-avatar">👤</div>
            <p class="user-name">{st.session_state.name}</p>
            <p class="user-role">{st.session_state.role}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Connection Status
        st.markdown('<p class="nav-label">📡 Data Status</p>', unsafe_allow_html=True)
        
        status = check_onedrive_status()
        status_html = '<div class="status-grid">'
        for name, stat in status.items():
            if "✅" in stat:
                status_class = "status-ok"
            elif "⚠️" in stat:
                status_class = "status-warn"
            else:
                status_class = "status-err"
            status_html += f'<div class="status-item"><span class="status-name">{name}</span><span class="status-value {status_class}">{stat}</span></div>'
        status_html += '</div>'
        st.markdown(status_html, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
        with col2:
            st.markdown(f'<p style="color:#64748b; font-size:0.75rem; text-align:center; margin-top:0.5rem;">Cache: {CACHE_TTL}s</p>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Navigation
        st.markdown('<p class="nav-label">📋 Navigation</p>', unsafe_allow_html=True)
        
        menus = [
            ("🏠", "Dashboard"),
            ("📊", "Produksi"),
            ("🚨", "Gangguan"),
            ("⛽", "Monitoring"),
            ("📋", "Daily Plan")
        ]
        
        for icon, menu in menus:
            btn_type = "primary" if st.session_state.current_menu == menu else "secondary"
            if st.button(f"{icon}  {menu}", key=f"nav_{menu}", use_container_width=True, type=btn_type):
                st.session_state.current_menu = menu
                st.rerun()
        
        st.markdown("---")
        
        # Logout
        if st.button("🚪 Sign Out", use_container_width=True):
            logout()
            st.rerun()
        
        # Footer
        st.markdown("""
        <div style="text-align:center; margin-top:2rem; padding-top:1rem; border-top:1px solid #1e3a5f;">
            <p style="color:#64748b; font-size:0.7rem; margin:0;">
                Mining Dashboard v4.0<br>
                © 2025 Semen Padang
            </p>
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# DASHBOARD OVERVIEW
# ============================================================
def show_dashboard():
    # Page Header
    st.markdown("""
    <div class="page-header">
        <div class="page-header-icon">📊</div>
        <div class="page-header-text">
            <h1>Operations Dashboard</h1>
            <p>Real-time mining production overview • Last updated: """ + datetime.now().strftime("%d %b %Y, %H:%M") + """</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Load Data
    df_prod = load_produksi()
    df_bbm = load_bbm()
    df_gangguan = load_gangguan("Januari")
    df_daily = load_daily_plan()
    
    # ===== KPI CARDS =====
    total_rit = df_prod['Rit'].sum() if not df_prod.empty else 0
    total_ton = df_prod['Tonnase'].sum() if not df_prod.empty else 0
    total_exc = df_prod['Excavator'].nunique() if not df_prod.empty else 0
    total_bbm = df_bbm['Total'].sum() if not df_bbm.empty else 0
    total_gangguan = len(df_gangguan) if not df_gangguan.empty else 0
    
    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi-card" style="--card-accent: #d4a84b;">
            <div class="kpi-icon">🚛</div>
            <div class="kpi-label">Total Ritase</div>
            <div class="kpi-value">{total_rit:,.0f}</div>
            <div class="kpi-subtitle">trips completed</div>
        </div>
        <div class="kpi-card" style="--card-accent: #3b82f6;">
            <div class="kpi-icon">⚖️</div>
            <div class="kpi-label">Total Tonase</div>
            <div class="kpi-value">{total_ton:,.0f}</div>
            <div class="kpi-subtitle">metric tons</div>
        </div>
        <div class="kpi-card" style="--card-accent: #10b981;">
            <div class="kpi-icon">🏗️</div>
            <div class="kpi-label">Active Units</div>
            <div class="kpi-value">{total_exc}</div>
            <div class="kpi-subtitle">excavators</div>
        </div>
        <div class="kpi-card" style="--card-accent: #f59e0b;">
            <div class="kpi-icon">⛽</div>
            <div class="kpi-label">Fuel Usage</div>
            <div class="kpi-value">{total_bbm:,.0f}</div>
            <div class="kpi-subtitle">liters consumed</div>
        </div>
        <div class="kpi-card" style="--card-accent: #ef4444;">
            <div class="kpi-icon">🚨</div>
            <div class="kpi-label">Incidents</div>
            <div class="kpi-value">{total_gangguan}</div>
            <div class="kpi-subtitle">reported issues</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ===== MAIN CHARTS ROW =====
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        <div class="chart-container">
            <div class="chart-header">
                <span class="chart-title">📈 Production Trend</span>
                <span class="chart-badge">Daily</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if not df_prod.empty:
            daily = df_prod.groupby('Date').agg({'Tonnase': 'sum', 'Rit': 'sum'}).reset_index()
            
            fig = go.Figure()
            
            # Area chart for tonnage
            fig.add_trace(go.Scatter(
                x=daily['Date'],
                y=daily['Tonnase'],
                name='Tonase',
                fill='tozeroy',
                line=dict(color=MINING_COLORS['gold'], width=2),
                fillcolor='rgba(212,168,75,0.15)',
                hovertemplate='<b>%{x}</b><br>Tonase: %{y:,.0f}<extra></extra>'
            ))
            
            # Line for ritase
            fig.add_trace(go.Scatter(
                x=daily['Date'],
                y=daily['Rit'] * 50,  # Scale for visibility
                name='Ritase (scaled)',
                line=dict(color=MINING_COLORS['blue'], width=2, dash='dot'),
                hovertemplate='<b>%{x}</b><br>Ritase: %{customdata:,.0f}<extra></extra>',
                customdata=daily['Rit']
            ))
            
            fig.update_layout(**get_chart_layout(height=320))
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("📊 Production data not available")
    
    with col2:
        st.markdown("""
        <div class="chart-container">
            <div class="chart-header">
                <span class="chart-title">🏗️ By Excavator</span>
                <span class="chart-badge">Top 6</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if not df_prod.empty:
            exc = df_prod.groupby('Excavator')['Tonnase'].sum().reset_index()
            exc = exc.sort_values('Tonnase', ascending=True).tail(6)
            
            fig = px.bar(
                exc,
                x='Tonnase',
                y='Excavator',
                orientation='h',
                color='Tonnase',
                color_continuous_scale=[[0, '#1e3a5f'], [0.5, '#3b82f6'], [1, '#d4a84b']]
            )
            fig.update_layout(**get_chart_layout(height=320, show_legend=False))
            fig.update_coloraxes(showscale=False)
            fig.update_traces(hovertemplate='<b>%{y}</b><br>Tonase: %{x:,.0f}<extra></extra>')
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("📊 Data not available")
    
    # ===== SECTION DIVIDER =====
    st.markdown("""
    <div class="section-divider">
        <div class="section-divider-line"></div>
        <span class="section-divider-text">Distribution Analysis</span>
        <div class="section-divider-line" style="background: linear-gradient(90deg, transparent 0%, #1e3a5f 100%);"></div>
    </div>
    """, unsafe_allow_html=True)
    
    # ===== DISTRIBUTION CHARTS =====
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.markdown('<div class="chart-container"><div class="chart-header"><span class="chart-title">🪨 Material</span></div></div>', unsafe_allow_html=True)
        if not df_prod.empty:
            mat = df_prod.groupby('Commudity')['Tonnase'].sum().reset_index()
            fig = px.pie(mat, values='Tonnase', names='Commudity', hole=0.6, color_discrete_sequence=CHART_SEQUENCE)
            fig.update_layout(**get_chart_layout(height=220, show_legend=False))
            fig.update_traces(textposition='inside', textinfo='percent', textfont_size=11)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    with c2:
        st.markdown('<div class="chart-container"><div class="chart-header"><span class="chart-title">🔄 By Shift</span></div></div>', unsafe_allow_html=True)
        if not df_prod.empty:
            shift = df_prod.groupby('Shift')['Tonnase'].sum().reset_index()
            fig = px.bar(shift, x='Shift', y='Tonnase', color='Shift', color_discrete_sequence=CHART_SEQUENCE[:3])
            fig.update_layout(**get_chart_layout(height=220, show_legend=False))
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    with c3:
        st.markdown('<div class="chart-container"><div class="chart-header"><span class="chart-title">🚨 Top Issues</span></div></div>', unsafe_allow_html=True)
        if not df_gangguan.empty:
            dg = df_gangguan.head(5)
            fig = px.bar(dg, x='Frekuensi', y='Row Labels', orientation='h', color_discrete_sequence=[MINING_COLORS['red']])
            fig.update_layout(**get_chart_layout(height=220, show_legend=False))
            fig.update_yaxes(categoryorder='total ascending')
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("No data")
    
    with c4:
        st.markdown('<div class="chart-container"><div class="chart-header"><span class="chart-title">⛽ Fuel by Type</span></div></div>', unsafe_allow_html=True)
        if not df_bbm.empty:
            bbm = df_bbm.groupby('Alat Berat')['Total'].sum().reset_index().head(5)
            fig = px.pie(bbm, values='Total', names='Alat Berat', hole=0.6, color_discrete_sequence=CHART_SEQUENCE)
            fig.update_layout(**get_chart_layout(height=220, show_legend=False))
            fig.update_traces(textposition='inside', textinfo='percent', textfont_size=11)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("No data")
    
    # ===== HEATMAP =====
    if not df_prod.empty:
        st.markdown("""
        <div class="section-divider">
            <div class="section-divider-line"></div>
            <span class="section-divider-text">Productivity Heatmap</span>
            <div class="section-divider-line" style="background: linear-gradient(90deg, transparent 0%, #1e3a5f 100%);"></div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="chart-container"><div class="chart-header"><span class="chart-title">🔥 Shift × Excavator Performance</span></div></div>', unsafe_allow_html=True)
        
        pivot = df_prod.pivot_table(values='Tonnase', index='Excavator', columns='Shift', aggfunc='sum', fill_value=0)
        
        fig = px.imshow(
            pivot,
            color_continuous_scale=[[0, '#0f2744'], [0.3, '#1e3a5f'], [0.6, '#3b82f6'], [1, '#d4a84b']],
            aspect='auto',
            labels=dict(x="Shift", y="Excavator", color="Tonase")
        )
        fig.update_layout(**get_chart_layout(height=300, show_legend=False))
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


# ============================================================
# PLACEHOLDER PAGES (akan dilengkapi di tahap selanjutnya)
# ============================================================
def show_produksi():
    # Page Header
    st.markdown("""
    <div class="page-header">
        <div class="page-header-icon">📊</div>
        <div class="page-header-text">
            <h1>Produksi Harian</h1>
            <p>Detailed daily production analysis and performance metrics</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    df = load_produksi()
    
    if df.empty:
        st.warning("⚠️ Data produksi tidak tersedia. Pastikan file Excel sudah terhubung.")
        return
    
    # ===== FILTER SECTION =====
    st.markdown("""
    <div class="chart-container">
        <div class="chart-header">
            <span class="chart-title">🔍 Filter Data</span>
            <span class="chart-badge">Interactive</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    min_date, max_date = df['Date'].min(), df['Date'].max()
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        start_date = st.date_input("📅 Dari", min_date, min_value=min_date, max_value=max_date)
    with col2:
        end_date = st.date_input("📅 Sampai", max_date, min_value=min_date, max_value=max_date)
    with col3:
        shifts = ['Semua'] + sorted(df['Shift'].dropna().unique().tolist())
        selected_shift = st.selectbox("🔄 Shift", shifts)
    with col4:
        excavators = ['Semua'] + sorted(df['Excavator'].dropna().unique().tolist())
        selected_exc = st.selectbox("🏗️ Excavator", excavators)
    with col5:
        bloks = ['Semua'] + sorted(df['BLOK'].dropna().unique().tolist())
        selected_blok = st.selectbox("🧱 BLOK", bloks)
    with col6:
        fronts = ['Semua'] + sorted(df['Front'].dropna().unique().tolist())
        selected_front = st.selectbox("📍 Front", fronts)
    
    # Apply filters
    mask = (df['Date'] >= start_date) & (df['Date'] <= end_date)
    if selected_shift != 'Semua':
        mask &= (df['Shift'] == selected_shift)
    if selected_exc != 'Semua':
        mask &= (df['Excavator'] == selected_exc)
    if selected_blok != 'Semua':
        mask &= (df['BLOK'] == selected_blok)
    if selected_front != 'Semua':
        mask &= (df['Front'] == selected_front)
    
    df_filtered = df[mask].copy()
    
    # Filter info
    st.markdown(f"""
    <p style="color:#64748b; font-size:0.85rem; margin:0.5rem 0 1.5rem 0;">
        📋 Menampilkan <strong style="color:#d4a84b;">{len(df_filtered):,}</strong> dari {len(df):,} data 
        &nbsp;|&nbsp; 📅 {start_date} s/d {end_date}
    </p>
    """, unsafe_allow_html=True)
    
    # ===== KPI CARDS =====
    total_rit = df_filtered['Rit'].sum()
    total_ton = df_filtered['Tonnase'].sum()
    avg_ton = df_filtered['Tonnase'].mean() if len(df_filtered) > 0 else 0
    total_exc = df_filtered['Excavator'].nunique()
    total_days = df_filtered['Date'].nunique()
    
    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi-card" style="--card-accent: #d4a84b;">
            <div class="kpi-icon">🚛</div>
            <div class="kpi-label">Total Ritase</div>
            <div class="kpi-value">{total_rit:,.0f}</div>
            <div class="kpi-subtitle">trips</div>
        </div>
        <div class="kpi-card" style="--card-accent: #3b82f6;">
            <div class="kpi-icon">⚖️</div>
            <div class="kpi-label">Total Tonase</div>
            <div class="kpi-value">{total_ton:,.0f}</div>
            <div class="kpi-subtitle">metric tons</div>
        </div>
        <div class="kpi-card" style="--card-accent: #10b981;">
            <div class="kpi-icon">📊</div>
            <div class="kpi-label">Avg per Trip</div>
            <div class="kpi-value">{avg_ton:,.1f}</div>
            <div class="kpi-subtitle">tons/trip</div>
        </div>
        <div class="kpi-card" style="--card-accent: #f59e0b;">
            <div class="kpi-icon">🏗️</div>
            <div class="kpi-label">Excavator</div>
            <div class="kpi-value">{total_exc}</div>
            <div class="kpi-subtitle">active units</div>
        </div>
        <div class="kpi-card" style="--card-accent: #8b5cf6;">
            <div class="kpi-icon">📅</div>
            <div class="kpi-label">Hari Kerja</div>
            <div class="kpi-value">{total_days}</div>
            <div class="kpi-subtitle">days</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ===== PRODUKSI PER BLOK =====
    st.markdown("""
    <div class="section-divider">
        <div class="section-divider-line"></div>
        <span class="section-divider-text">Produksi per BLOK</span>
        <div class="section-divider-line" style="background: linear-gradient(90deg, transparent 0%, #1e3a5f 100%);"></div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="chart-container"><div class="chart-header"><span class="chart-title">🧱 Tonase per BLOK</span></div></div>', unsafe_allow_html=True)
    
    blok_prod = df_filtered.groupby('BLOK')['Tonnase'].sum().reset_index().sort_values('Tonnase', ascending=True)
    
    fig = px.bar(
        blok_prod,
        x='Tonnase',
        y='BLOK',
        orientation='h',
        color='Tonnase',
        color_continuous_scale=[[0, '#0f2744'], [0.5, '#3b82f6'], [1, '#d4a84b']]
    )
    fig.update_layout(**get_chart_layout(height=max(250, len(blok_prod) * 35), show_legend=False))
    fig.update_coloraxes(showscale=False)
    fig.update_traces(hovertemplate='<b>%{y}</b><br>Tonase: %{x:,.0f}<extra></extra>')
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # ===== TREN HARIAN =====
    st.markdown("""
    <div class="section-divider">
        <div class="section-divider-line"></div>
        <span class="section-divider-text">Tren Produksi Harian</span>
        <div class="section-divider-line" style="background: linear-gradient(90deg, transparent 0%, #1e3a5f 100%);"></div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="chart-container"><div class="chart-header"><span class="chart-title">📈 Tonase & Ritase Harian</span><span class="chart-badge">Combo Chart</span></div></div>', unsafe_allow_html=True)
    
    daily = df_filtered.groupby('Date').agg({'Tonnase': 'sum', 'Rit': 'sum'}).reset_index()
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Bar untuk Ritase
    fig.add_trace(
        go.Bar(
            x=daily['Date'],
            y=daily['Rit'],
            name='Ritase',
            marker_color='rgba(59,130,246,0.6)',
            hovertemplate='<b>%{x}</b><br>Ritase: %{y:,.0f}<extra></extra>'
        ),
        secondary_y=False
    )
    
    # Line untuk Tonase
    fig.add_trace(
        go.Scatter(
            x=daily['Date'],
            y=daily['Tonnase'],
            name='Tonase',
            line=dict(color='#d4a84b', width=3),
            mode='lines+markers',
            marker=dict(size=6),
            hovertemplate='<b>%{x}</b><br>Tonase: %{y:,.0f}<extra></extra>'
        ),
        secondary_y=True
    )
    
    fig.update_layout(**get_chart_layout(height=380))
    fig.update_yaxes(title_text="Ritase", secondary_y=False, showgrid=False, title_font=dict(color='#3b82f6'))
    fig.update_yaxes(title_text="Tonase", secondary_y=True, gridcolor='rgba(30,58,95,0.5)', title_font=dict(color='#d4a84b'))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # ===== DISTRIBUTION CHARTS =====
    st.markdown("""
    <div class="section-divider">
        <div class="section-divider-line"></div>
        <span class="section-divider-text">Distribusi Produksi</span>
        <div class="section-divider-line" style="background: linear-gradient(90deg, transparent 0%, #1e3a5f 100%);"></div>
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown('<div class="chart-container"><div class="chart-header"><span class="chart-title">🔄 Per Shift</span></div></div>', unsafe_allow_html=True)
        shift_data = df_filtered.groupby('Shift')['Tonnase'].sum().reset_index()
        fig = px.pie(shift_data, values='Tonnase', names='Shift', hole=0.6, color_discrete_sequence=CHART_SEQUENCE[:3])
        fig.update_layout(**get_chart_layout(height=280, show_legend=False))
        fig.update_traces(textposition='inside', textinfo='percent+label', textfont_size=12)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    with c2:
        st.markdown('<div class="chart-container"><div class="chart-header"><span class="chart-title">🏗️ Per Excavator</span></div></div>', unsafe_allow_html=True)
        exc_data = df_filtered.groupby('Excavator')['Tonnase'].sum().reset_index().sort_values('Tonnase', ascending=True).tail(8)
        fig = px.bar(exc_data, x='Tonnase', y='Excavator', orientation='h', color='Tonnase',
                     color_continuous_scale=[[0, '#1e3a5f'], [1, '#10b981']])
        fig.update_layout(**get_chart_layout(height=280, show_legend=False))
        fig.update_coloraxes(showscale=False)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    with c3:
        st.markdown('<div class="chart-container"><div class="chart-header"><span class="chart-title">🪨 Per Material</span></div></div>', unsafe_allow_html=True)
        mat_data = df_filtered.groupby('Commudity')['Tonnase'].sum().reset_index()
        fig = px.pie(mat_data, values='Tonnase', names='Commudity', hole=0.6, color_discrete_sequence=CHART_SEQUENCE)
        fig.update_layout(**get_chart_layout(height=280, show_legend=False))
        fig.update_traces(textposition='inside', textinfo='percent+label', textfont_size=11)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # ===== ANALISIS PRODUKTIVITAS =====
    st.markdown("""
    <div class="section-divider">
        <div class="section-divider-line"></div>
        <span class="section-divider-text">Analisis Produktivitas</span>
        <div class="section-divider-line" style="background: linear-gradient(90deg, transparent 0%, #1e3a5f 100%);"></div>
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown('<div class="chart-container"><div class="chart-header"><span class="chart-title">🔗 Korelasi Rit vs Tonase</span></div></div>', unsafe_allow_html=True)
        sample = df_filtered.sample(min(500, len(df_filtered))) if len(df_filtered) > 0 else df_filtered
        fig = px.scatter(
            sample, x='Rit', y='Tonnase', color='Shift',
            color_discrete_sequence=CHART_SEQUENCE[:3],
            opacity=0.7
        )
        fig.update_layout(**get_chart_layout(height=320))
        fig.update_traces(marker=dict(size=8))
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    with c2:
        st.markdown('<div class="chart-container"><div class="chart-header"><span class="chart-title">🔥 Heatmap Shift × Excavator</span></div></div>', unsafe_allow_html=True)
        pivot = df_filtered.pivot_table(values='Tonnase', index='Excavator', columns='Shift', aggfunc='sum', fill_value=0)
        fig = px.imshow(
            pivot,
            color_continuous_scale=[[0, '#0f2744'], [0.3, '#1e3a5f'], [0.6, '#3b82f6'], [1, '#d4a84b']],
            aspect='auto'
        )
        fig.update_layout(**get_chart_layout(height=320, show_legend=False))
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # ===== DATA TABLE =====
    st.markdown("""
    <div class="section-divider">
        <div class="section-divider-line"></div>
        <span class="section-divider-text">Data Detail</span>
        <div class="section-divider-line" style="background: linear-gradient(90deg, transparent 0%, #1e3a5f 100%);"></div>
    </div>
    """, unsafe_allow_html=True)
    
    col_dl, col_btn = st.columns([4, 1])
    with col_btn:
        cols_export = ['Date', 'Shift', 'BLOK', 'Front', 'Commudity', 'Excavator', 'Dump Truck', 'Rit', 'Tonnase']
        cols_export = [c for c in cols_export if c in df_filtered.columns]
        csv = df_filtered[cols_export].to_csv(index=False)
        st.download_button(
            "📥 Export CSV",
            csv,
            "produksi_filtered.csv",
            "text/csv",
            use_container_width=True
        )
    
    # Show dataframe
    cols_show = ['Date', 'Time', 'Shift', 'BLOK', 'Front', 'Commudity', 'Excavator', 'Dump Truck', 'Dump Loc', 'Rit', 'Tonnase']
    cols_show = [c for c in cols_show if c in df_filtered.columns]
    st.dataframe(
        df_filtered[cols_show].sort_values('Date', ascending=False),
        use_container_width=True,
        height=400
    )

def show_gangguan():
    st.markdown("""
    <div class="page-header">
        <div class="page-header-icon">🚨</div>
        <div class="page-header-text">
            <h1>Gangguan Produksi</h1>
            <p>Production incident analysis</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.info("🚧 Halaman ini akan di-redesign di tahap berikutnya")

def show_monitoring():
    st.markdown("""
    <div class="page-header">
        <div class="page-header-icon">⛽</div>
        <div class="page-header-text">
            <h1>Monitoring BBM & Ritase</h1>
            <p>Fuel consumption and trip monitoring</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.info("🚧 Halaman ini akan di-redesign di tahap berikutnya")

def show_daily_plan():
    st.markdown("""
    <div class="page-header">
        <div class="page-header-icon">📋</div>
        <div class="page-header-text">
            <h1>Daily Plan & Realisasi</h1>
            <p>Planning vs actual performance</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.info("🚧 Halaman ini akan di-redesign di tahap berikutnya")


# ============================================================
# MAIN
# ============================================================
def main():
    if not st.session_state.logged_in:
        show_login()
    else:
        render_sidebar()
        
        if st.session_state.current_menu == "Dashboard":
            show_dashboard()
        elif st.session_state.current_menu == "Produksi":
            show_produksi()
        elif st.session_state.current_menu == "Gangguan":
            show_gangguan()
        elif st.session_state.current_menu == "Monitoring":
            show_monitoring()
        elif st.session_state.current_menu == "Daily Plan":
            show_daily_plan()


if __name__ == "__main__":
    main()