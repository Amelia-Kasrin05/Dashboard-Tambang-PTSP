import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime
import os
import sys
sys.path.append('.')
from utils.data_loader import *
from config import USERS, COLORS, CHART_COLORS

st.set_page_config(page_title="Dashboard Tambang Semen Padang", page_icon="⛏️", layout="wide")

# Enhanced CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
.stApp {background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%); font-family: 'Inter', sans-serif;}
div[data-testid="stSidebar"] {background: linear-gradient(180deg, #0d1117 0%, #161b22 100%); border-right: 1px solid #30363d;}
.sidebar-header {font-size:1.3rem;font-weight:700;background:linear-gradient(90deg,#00C853,#00E5FF);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-align:center;padding:0.5rem 0;}
.metric-card {background:linear-gradient(145deg,#1e2a3a,#16213e);border-radius:16px;padding:1.2rem;border:1px solid #30363d;box-shadow:0 4px 20px rgba(0,0,0,0.3);transition:transform 0.2s;}
.metric-card:hover {transform:translateY(-2px);}
.metric-value {font-size:1.8rem;font-weight:700;color:#fff;margin:0;}
.metric-label {font-size:0.8rem;color:#8b949e;margin-bottom:0.3rem;text-transform:uppercase;letter-spacing:0.5px;}
.metric-icon {font-size:1.3rem;margin-bottom:0.3rem;}
.section-title {font-size:1rem;color:#58a6ff;font-weight:600;margin:1.5rem 0 1rem 0;padding-left:12px;border-left:3px solid #58a6ff;}
.chart-container {background:#161b22;border-radius:12px;padding:1rem;border:1px solid #30363d;margin-bottom:1rem;}
div[data-testid="stMetric"] {background:linear-gradient(145deg,#1e2a3a,#16213e);border-radius:12px;padding:1rem;border:1px solid #30363d;}
div[data-testid="stMetric"] label {color:#8b949e !important;}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {color:#fff !important;}
div[data-testid="stFileUploader"] {background:#21262d;border-radius:8px;padding:0.5rem;}
div[data-testid="stDateInput"] input {background:#21262d;border:1px solid #30363d;color:#fff;}
.overview-card {background:linear-gradient(145deg,#1e2a3a,#16213e);border-radius:16px;padding:1.5rem;border:1px solid #30363d;margin-bottom:1rem;}
.overview-title {color:#58a6ff;font-size:1.1rem;font-weight:600;margin-bottom:1rem;display:flex;align-items:center;gap:0.5rem;}
</style>
""", unsafe_allow_html=True)

# Session State
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = st.session_state.role = st.session_state.name = None
if 'current_menu' not in st.session_state:
    st.session_state.current_menu = "Dashboard Overview"

def login(u, p):
    if u in USERS and USERS[u]['password'] == p:
        st.session_state.logged_in, st.session_state.username = True, u
        st.session_state.role, st.session_state.name = USERS[u]['role'], USERS[u]['name']
        return True
    return False

def logout():
    st.session_state.logged_in = False
    st.session_state.username = st.session_state.role = st.session_state.name = None

def chart_layout(title=None, height=300):
    layout = dict(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=height,
        margin=dict(
            l=60,
            r=30,
            t=50 if title else 30,
            b=60
        ),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            automargin=True
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#21262d',
            zeroline=False,
            automargin=True
        ),
        legend=dict(
            orientation='h',
            y=-0.25,
            x=0.5,
            xanchor='center'
        )
    )

    if title:
        layout["title"] = dict(
            text=title,
            x=0.5,
            font=dict(size=14)
        )

    return layout


def handle_upload(uploaded_file, target_name):
    if uploaded_file:
        try:
            upload_path = f"data/{target_name}"
            with open(upload_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.cache_data.clear()
            return True
        except:
            return False
    return False

# LOGIN PAGE
def show_login():
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        st.markdown("""
        <div style="text-align:center;padding:2rem 0;">
            <p style="font-size:3.5rem;margin:0;">⛏️</p>
            <h1 style="background:linear-gradient(90deg,#00C853,#00E5FF);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0.5rem 0;font-size:2.2rem;">Dashboard Tambang</h1>
            <p style="color:#8b949e;font-size:1rem;">Semen Padang Mining Operations</p>
        </div>
        """, unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("👤 Username")
            p = st.text_input("🔒 Password", type="password")
            if st.form_submit_button("🚀 Login", use_container_width=True):
                if login(u, p): st.rerun()
                else: st.error("❌ Login gagal!")
        st.caption("Demo: admin_produksi/prod123")

# ================================================================
# DASHBOARD OVERVIEW
# ================================================================
def show_overview():
    st.markdown('<h2 style="color:#fff;margin-bottom:1.5rem;">📊 Dashboard Overview</h2>', unsafe_allow_html=True)
    
    df_prod = load_produksi()
    df_bbm = load_bbm()
    df_gangguan = load_gangguan("Januari")
    df_daily = load_daily_plan()
    
    # Row 1: Main KPIs
    cols = st.columns(5)
    metrics = [
        ("🚛", "Total Ritase", f"{df_prod['Rit'].sum():,.0f}" if not df_prod.empty else "0", "#00E676"),
        ("⚖️", "Total Tonase", f"{df_prod['Tonnase'].sum():,.0f}" if not df_prod.empty else "0", "#58a6ff"),
        ("🏗️", "Unit Excavator", f"{df_prod['Excavator'].nunique()}" if not df_prod.empty else "0", "#f0883e"),
        ("⛽", "Total BBM (L)", f"{df_bbm['Total'].sum():,.0f}" if not df_bbm.empty else "0", "#a371f7"),
        ("🚨", "Jenis Gangguan", f"{len(df_gangguan)}" if not df_gangguan.empty else "0", "#f85149")
    ]
    for col, (icon, label, value, color) in zip(cols, metrics):
        col.markdown(f'<div class="metric-card"><div class="metric-icon">{icon}</div><div class="metric-label">{label}</div><div class="metric-value" style="color:{color}">{value}</div></div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Row 2: Charts
    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown('<div class="section-title">📈 Tren Produksi Harian</div>', unsafe_allow_html=True)
        if not df_prod.empty:
            daily = df_prod.groupby('Date').agg({'Tonnase':'sum','Rit':'sum'}).reset_index()
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=daily['Date'], y=daily['Tonnase'], name='Tonase', fill='tozeroy',
                                     line=dict(color='#00E676',width=2), fillcolor='rgba(0,230,118,0.15)'))
            fig.update_layout(**chart_layout(height=280))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Data produksi tidak tersedia")
    
    with col2:
        st.markdown('<div class="section-title">🏗️ Produksi per Excavator</div>', unsafe_allow_html=True)
        if not df_prod.empty:
            exc = df_prod.groupby('Excavator')['Tonnase'].sum().reset_index().sort_values('Tonnase').tail(6)
            fig = px.bar(exc, x='Tonnase', y='Excavator', orientation='h', 
                         color='Tonnase', color_continuous_scale=['#1e3a5f','#58a6ff'])
            fig.update_layout(**chart_layout(height=280))
            fig.update_coloraxes(showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Data tidak tersedia")
    
    # Row 3: Distribution
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown('<div class="section-title">🪨 Material</div>', unsafe_allow_html=True)
        if not df_prod.empty:
            mat = df_prod.groupby('Commudity')['Tonnase'].sum().reset_index()
            fig = px.pie(mat, values='Tonnase', names='Commudity', hole=0.5,
                         color_discrete_sequence=['#00E676','#58a6ff','#f0883e','#a371f7'])
            fig.update_layout(**chart_layout(height=200))
            fig.update_traces(textposition='inside', textinfo='percent')
            st.plotly_chart(fig, use_container_width=True)
    
    with c2:
        st.markdown('<div class="section-title">🔄 Per Shift</div>', unsafe_allow_html=True)
        if not df_prod.empty:
            shift = df_prod.groupby('Shift')['Tonnase'].sum().reset_index()
            fig = px.bar(shift, x='Shift', y='Tonnase', color='Shift',
                         color_discrete_sequence=['#00E676','#58a6ff','#f0883e'])
            fig.update_layout(**chart_layout(height=200), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    
    with c3:
        st.markdown('<div class="section-title">🚨 Top Gangguan</div>', unsafe_allow_html=True)
        if not df_gangguan.empty:
            dg_top = df_gangguan.head(5)
            fig = px.bar(
                dg_top,
                x='Frekuensi',
                y='Row Labels',
                orientation='h',
                color_discrete_sequence=['#f85149']
            )
            fig.update_layout(**chart_layout(height=200))
            fig.update_yaxes(categoryorder='total ascending')
            st.plotly_chart(fig, use_container_width=True)

        else:
            st.info("Data tidak tersedia")
    
    with c4:
        st.markdown('<div class="section-title">⛽ BBM per Alat</div>', unsafe_allow_html=True)
        if not df_bbm.empty:
            bbm_type = df_bbm.groupby('Alat Berat')['Total'].sum().reset_index().head(5)
            fig = px.pie(bbm_type, values='Total', names='Alat Berat', hole=0.5,
                         color_discrete_sequence=['#f0883e','#f85149','#a371f7','#00E676'])
            fig.update_layout(**chart_layout(height=200))
            fig.update_traces(textposition='inside', textinfo='percent')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Data tidak tersedia")
    
    # Row 4: Heatmap
    if not df_prod.empty:
        st.markdown('<div class="section-title">🔥 Heatmap Produktivitas (Shift x Excavator)</div>', unsafe_allow_html=True)
        pivot = df_prod.pivot_table(values='Tonnase', index='Excavator', columns='Shift', aggfunc='sum', fill_value=0)
        fig = px.imshow(pivot, color_continuous_scale='Greens', aspect='auto',
                        labels=dict(x="Shift", y="Excavator", color="Tonase"))
        fig.update_layout(**chart_layout(height=280))
        st.plotly_chart(fig, use_container_width=True)

# ================================================================
# PRODUKSI HARIAN
# ================================================================
def show_produksi():
    col_title, col_upload = st.columns([3,1])
    with col_title:
        st.markdown('<h2 style="color:#fff;margin-bottom:1rem;">📊 Produksi Harian</h2>', unsafe_allow_html=True)
    with col_upload:
        with st.expander("📤 Upload Data Produksi"):
            up = st.file_uploader("Upload file Excel", type=['xlsx','xls'], key="up_prod_main", label_visibility="collapsed")
            if up and handle_upload(up, "Produksi_UTSG_Harian.xlsx"):
                st.success("✅ Data berhasil diupload!")
                st.rerun()
    
    df = load_produksi()
    if df.empty: 
        st.warning("⚠️ Data tidak tersedia. Upload file Produksi_UTSG_Harian.xlsx")
        return
    
    # =========================
    # Filter
    # =========================
    st.markdown('<div class="section-title">🔍 Filter Data</div>', unsafe_allow_html=True)

    col_f1, col_f2, col_f3, col_f4, col_f5, col_f6 = st.columns(6)

    # tanggal min max
    min_date, max_date = df['Date'].min(), df['Date'].max()

    with col_f1:
        start_date = st.date_input(
            "📅 Dari Tanggal",
            min_date,
            min_value=min_date,
            max_value=max_date
        )

    with col_f2:
        end_date = st.date_input(
            "📅 Sampai Tanggal",
            max_date,
            min_value=min_date,
            max_value=max_date
        )

    with col_f3:
        selected_shift = st.selectbox(
            "🔄 Shift",
            ['Semua'] + sorted(df['Shift'].dropna().unique().tolist())
        )

    with col_f4:
        selected_exc = st.selectbox(
            "🏗️ Excavator",
            ['Semua'] + sorted(df['Excavator'].dropna().unique().tolist())
        )

    with col_f5:
        selected_blok = st.selectbox(
            "🧱 BLOK",
            ['Semua'] + sorted(df['BLOK'].dropna().unique().tolist())
        )

    with col_f6:
        selected_front = st.selectbox(
            "📍 Front",
            ['Semua'] + sorted(df['Front'].dropna().unique().tolist())
        )

    # =========================
    # Filtering logic
    # =========================
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

    st.markdown(
        f'<p style="color:#8b949e;font-size:0.8rem;">'
        f'Menampilkan {len(df_filtered):,} dari {len(df):,} data | '
        f'{start_date} s/d {end_date}'
        f'</p>',
        unsafe_allow_html=True
    )

    # KPI
    cols = st.columns(5)
    kpis = [("🚛","RITASE",f"{df_filtered['Rit'].sum():,.0f}"),("⚖️","TONASE",f"{df_filtered['Tonnase'].sum():,.0f}"),
            ("📊","AVG/TRIP",f"{df_filtered['Tonnase'].mean():.0f}" if len(df_filtered)>0 else "0"),
            ("🏗️","EXCAVATOR",f"{df_filtered['Excavator'].nunique()}"),("📅","HARI",f"{df_filtered['Date'].nunique()}")]
    for col,(icon,label,val) in zip(cols,kpis):
        col.markdown(f'<div class="metric-card"><div class="metric-icon">{icon}</div><div class="metric-label">{label}</div><div class="metric-value">{val}</div></div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">🧱 Produksi per BLOK</div>', unsafe_allow_html=True)

    blok_prod = (
        df_filtered
        .groupby('BLOK')['Tonnase']
        .sum()
        .reset_index()
        .sort_values('Tonnase', ascending=True)
    )

    fig = px.bar(
        blok_prod,
        x='Tonnase',
        y='BLOK',
        orientation='h',
        color='Tonnase',
        color_continuous_scale='Greens'
    )

    fig.update_layout(**chart_layout(height=350))
    fig.update_coloraxes(showscale=False)
    st.plotly_chart(fig, use_container_width=True)

    # Combo Chart
    st.markdown('<div class="section-title">📈 Tren Produksi Harian - Tonase & Ritase (Combo Chart)</div>', unsafe_allow_html=True)
    daily = df_filtered.groupby('Date').agg({'Tonnase':'sum','Rit':'sum'}).reset_index()
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=daily['Date'], y=daily['Rit'], name='Ritase', marker_color='rgba(88,166,255,0.6)'), secondary_y=False)
    fig.add_trace(go.Scatter(x=daily['Date'], y=daily['Tonnase'], name='Tonase', line=dict(color='#00E676',width=3), mode='lines+markers'), secondary_y=True)
    fig.update_layout(**chart_layout(height=350))
    fig.update_yaxes(title_text="Ritase", secondary_y=False, showgrid=False)
    fig.update_yaxes(title_text="Tonase", secondary_y=True, showgrid=True, gridcolor='#21262d')
    st.plotly_chart(fig, use_container_width=True)
    
    # Distribution Charts
    c1,c2,c3 = st.columns(3)
    with c1:
        st.markdown('<div class="section-title">🔄 Distribusi Shift (Donut)</div>', unsafe_allow_html=True)
        shift_data = df_filtered.groupby('Shift')['Tonnase'].sum().reset_index()
        fig = px.pie(shift_data, values='Tonnase', names='Shift', hole=0.5, color_discrete_sequence=['#00E676','#58a6ff','#f0883e'])
        fig.update_layout(**chart_layout(height=280))
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    
    with c2:
        st.markdown('<div class="section-title">🏗️ Per Excavator (Horizontal Bar)</div>', unsafe_allow_html=True)
        exc = df_filtered.groupby('Excavator')['Tonnase'].sum().reset_index().sort_values('Tonnase')
        fig = px.bar(exc, x='Tonnase', y='Excavator', orientation='h', color='Tonnase', color_continuous_scale='Greens')
        fig.update_layout(**chart_layout(height=280))
        fig.update_coloraxes(showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with c3:
        st.markdown('<div class="section-title">🪨 Material (Donut)</div>', unsafe_allow_html=True)
        mat = df_filtered.groupby('Commudity')['Tonnase'].sum().reset_index()
        fig = px.pie(mat, values='Tonnase', names='Commudity', hole=0.5, color_discrete_sequence=['#00E676','#58a6ff','#f0883e','#a371f7'])
        fig.update_layout(**chart_layout(height=280))
        st.plotly_chart(fig, use_container_width=True)
    
    # =========================================================
    # ANALISIS PRODUKTIVITAS
    # =========================================================
    st.markdown(
        """
        <div style="
            margin-top:20px;
            margin-bottom:10px;
            padding-left:6px;
            border-left:4px solid #00E676;
        ">
            <h3 style="margin:0;color:#e6edf3;">
                📊 Analisis Produktivitas
            </h3>
            <p style="margin:4px 0 0 0;color:#8b949e;font-size:0.85rem;">
                Hubungan ritase, tonase, dan pola waktu produksi
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # =========================================================
    # Scatter & Heatmap
    # =========================================================
    c1, c2 = st.columns(2)

    with c1:
        st.markdown(
            '<div class="section-title">🔗 Korelasi Rit vs Tonase</div>',
            unsafe_allow_html=True
        )

        sample = (
            df_filtered.sample(min(500, len(df_filtered)))
            if not df_filtered.empty
            else df_filtered
        )

        fig = px.scatter(
            sample,
            x='Rit',
            y='Tonnase',
            color='Shift',
            color_discrete_sequence=['#00E676', '#58a6ff', '#f0883e'],
            opacity=0.7
        )
        fig.update_layout(**chart_layout(height=300))
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown(
            '<div class="section-title">⏱️ Heatmap Produksi (Jam × Shift)</div>',
            unsafe_allow_html=True
        )

        # Ambil jam awal dari kolom Time (07:00-08:00 → 7)
        df_filtered['Jam'] = (
            df_filtered['Time']
            .astype(str)
            .str.split(':')
            .str[0]
            .astype(int)
        )

        all_hours = list(range(24))

        pivot = (
            df_filtered
            .pivot_table(
                values='Tonnase',
                index='Shift',
                columns='Jam',
                aggfunc='sum'
            )
            .reindex(columns=all_hours, fill_value=0)
        )

        fig = px.imshow(
            pivot,
            color_continuous_scale='Greens',
            aspect='auto',
            labels=dict(x="Jam", y="Shift", color="Tonase")
        )

        fig.update_layout(
            height=320,
            xaxis=dict(tickmode='array', tickvals=all_hours)
        )

        st.plotly_chart(fig, use_container_width=True)
       
    # Data Table
    st.markdown('<div class="section-title">📋 Data Detail</div>', unsafe_allow_html=True)
    col_dl1, col_dl2 = st.columns([4,1])
    with col_dl2:
        csv = df_filtered[['Date','Shift','Front','Commudity','Excavator','Dump Truck','Rit','Tonnase']].to_csv(index=False)
        st.download_button("📥 Download CSV", csv, "produksi_filtered.csv", "text/csv", use_container_width=True)
    cols_detail = [
        'Date',
        'Time',
        'Shift',
        'BLOK',
        'Front',
        'Commudity',
        'Excavator',
        'Dump Truck',
        'Dump Loc',
        'Rit',
        'Tonnase'
    ]

    cols_detail = [c for c in cols_detail if c in df_filtered.columns]

    st.dataframe(
        df_filtered[cols_detail].sort_values('Date', ascending=False),
        use_container_width=True,
        height=300
    )
# ================================================================
# GANGGUAN
# ================================================================
def show_gangguan():
    col_title, col_upload = st.columns([3,1])
    with col_title:
        st.markdown('<h2 style="color:#fff;margin-bottom:1rem;">🚨 Analisis Gangguan Produksi</h2>', unsafe_allow_html=True)
    with col_upload:
        with st.expander("📤 Upload Data Gangguan"):
            up = st.file_uploader("Upload file Excel", type=['xlsx','xls'], key="up_gang_main", label_visibility="collapsed")
            if up and handle_upload(up, "Gangguan_Produksi_2025_baru.xlsx"):
                st.success("✅ Data berhasil diupload!")
                st.rerun()
    
    bulan = st.selectbox("Pilih Bulan", ["Januari","Februari","Maret","April","Mei","Juni","Juli","Agustus","September","Oktober","November","Desember"])
    dg = load_gangguan(bulan)
    
    if not dg.empty:
        dg['Row Labels'] = dg['Row Labels'].astype(str)
        c1,c2,c3 = st.columns(3)
        c1.metric("🔢 Jenis Gangguan", len(dg))
        c2.metric("📊 Total Frekuensi", f"{dg['Frekuensi'].sum():,.0f}")
        c3.metric("🔝 Top Issue", dg.iloc[0]['Row Labels'][:25])
        
        col1, col2 = st.columns([2,1])
        with col1:
            st.markdown('<div class="section-title">📊 Pareto Chart - 80/20 Analysis</div>', unsafe_allow_html=True)
            dp = dg.head(10).copy()
            dp['Kumulatif'] = (dp['Frekuensi'].cumsum()/dg['Frekuensi'].sum()*100)
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(go.Bar(x=dp['Row Labels'], y=dp['Frekuensi'], name='Frekuensi', marker_color='#f85149'), secondary_y=False)
            fig.add_trace(go.Scatter(x=dp['Row Labels'], y=dp['Kumulatif'], name='Kumulatif %', line=dict(color='#f0883e',width=3), mode='lines+markers'), secondary_y=True)
            fig.add_hline(y=80, line_dash="dash", line_color="#58a6ff", secondary_y=True, annotation_text="80%")
            fig.update_layout(**chart_layout(height=400))
            fig.update_xaxes(tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown('<div class="section-title">🥧 Proporsi Gangguan (Pie)</div>', unsafe_allow_html=True)
            fig = px.pie(dg.head(8), values='Frekuensi', names='Row Labels', hole=0.4, color_discrete_sequence=px.colors.sequential.Reds_r)
            fig.update_layout(**chart_layout(height=400))
            st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(dg, use_container_width=True, height=250)
    else:
        st.info(f"Data gangguan bulan {bulan} tidak tersedia. Upload file Gangguan_Produksi_2025_baru.xlsx")

# ================================================================
# MONITORING
# ================================================================
def show_monitoring():
    col_title, col_upload = st.columns([3,1])
    with col_title:
        st.markdown('<h2 style="color:#fff;margin-bottom:1rem;">⛽ Monitoring BBM & Ritase</h2>', unsafe_allow_html=True)
    with col_upload:
        with st.expander("📤 Upload Data Monitoring"):
            up = st.file_uploader("Upload file Excel", type=['xlsx','xls'], key="up_mon_main", label_visibility="collapsed")
            if up and handle_upload(up, "Monitoring_2025_.xlsx"):
                st.success("✅ Data berhasil diupload!")
                st.rerun()
    
    tab1, tab2 = st.tabs(["⛽ BBM", "🚛 Ritase"])
    
    with tab1:
        db = load_bbm()
        if not db.empty:
            c1,c2,c3 = st.columns(3)
            c1.metric("⛽ Total BBM", f"{db['Total'].sum():,.0f} L")
            c2.metric("🏗️ Jumlah Alat", len(db))
            c3.metric("📊 Avg/Alat", f"{db['Total'].mean():,.0f} L")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="section-title">📊 Distribusi BBM per Jenis Alat</div>', unsafe_allow_html=True)
                bbm_type = db.groupby('Alat Berat')['Total'].sum().reset_index()
                fig = px.pie(bbm_type, values='Total', names='Alat Berat', hole=0.5, color_discrete_sequence=['#f0883e','#f85149','#a371f7','#00E676'])
                fig.update_layout(**chart_layout(height=350))
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown('<div class="section-title">🔝 Top 10 Konsumsi BBM</div>', unsafe_allow_html=True)
                fig = px.bar(
                    db.nlargest(10,'Total'),
                    x='Total',
                    y='Tipe Alat',
                    orientation='h',
                    color='Total',
                    color_continuous_scale='OrRd'
                )
                fig.update_layout(**chart_layout(height=350))
                fig.update_yaxes(categoryorder='total ascending')
                fig.update_coloraxes(showscale=False)
                st.plotly_chart(fig, use_container_width=True)   
                st.dataframe(db, use_container_width=True, height=300)
        else:
            st.info("Data BBM tidak tersedia. Upload file Monitoring_2025_.xlsx")
    
    with tab2:
        st.markdown('<div class="section-title">🚛 Ritase per Front</div>', unsafe_allow_html=True)
        dr = load_ritase()
        if not dr.empty:
            rc = [c for c in dr.columns if c not in ['Tanggal','Shift','Pengawasan']]
            tot = dr[rc].sum().reset_index()
            tot.columns = ['Front','Total']
            tot = tot[tot['Total']>0].sort_values('Total', ascending=True)
            fig = px.bar(tot, x='Total', y='Front', orientation='h', color='Total', color_continuous_scale='Blues')
            fig.update_layout(**chart_layout(height=400))
            fig.update_coloraxes(showscale=False)
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(dr, use_container_width=True, height=300)
        else:
            st.info("Data ritase tidak tersedia")

# ================================================================
# DAILY PLAN
# ================================================================
def show_daily_plan():
    col_title, col_upload = st.columns([3,1])
    with col_title:
        st.markdown('<h2 style="color:#fff;margin-bottom:1rem;">📋 Daily Plan & Realisasi</h2>', unsafe_allow_html=True)
    with col_upload:
        with st.expander("📤 Upload Data Daily Plan"):
            up = st.file_uploader("Upload file Excel", type=['xlsx','xls'], key="up_daily_main", label_visibility="collapsed")
            if up and handle_upload(up, "DAILY_PLAN.xlsx"):
                st.success("✅ Data berhasil diupload!")
                st.rerun()
    
    tab1, tab2 = st.tabs(["📅 Scheduling", "✅ Realisasi"])
    
    with tab1:
        dp = load_daily_plan()
        if not dp.empty:
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("📅 Total Record", len(dp))
            if 'Batu Kapur' in dp.columns:
                c2.metric("🪨 Target Batu Kapur", f"{pd.to_numeric(dp['Batu Kapur'], errors='coerce').sum():,.0f}")
            if 'Silika' in dp.columns:
                c3.metric("🏔️ Target Silika", f"{pd.to_numeric(dp['Silika'], errors='coerce').sum():,.0f}")
            if 'Clay' in dp.columns:
                c4.metric("🧱 Target Clay", f"{pd.to_numeric(dp['Clay'], errors='coerce').sum():,.0f}")
            
            st.markdown('<div class="section-title">📋 Data Scheduling</div>', unsafe_allow_html=True)
            st.dataframe(dp, use_container_width=True, height=400)
            
            # Placeholder Peta
            st.markdown('<div class="section-title">🗺️ Peta Lokasi (Coming Soon)</div>', unsafe_allow_html=True)
            st.info("📍 Fitur peta akan menggunakan data Blok, Grid, dan ROM untuk menampilkan lokasi penambangan.")
        else:
            st.info("Data scheduling tidak tersedia. Upload file DAILY_PLAN.xlsx")
    
    with tab2:
        dr = load_realisasi()
        if not dr.empty:
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("📅 Total Record", len(dr))
            if 'Batu Kapur' in dr.columns:
                c2.metric("🪨 Realisasi Batu Kapur", f"{pd.to_numeric(dr['Batu Kapur'], errors='coerce').sum():,.0f}")
            if 'Silika' in dr.columns:
                c3.metric("🏔️ Realisasi Silika", f"{pd.to_numeric(dr['Silika'], errors='coerce').sum():,.0f}")
            if 'Timbunan' in dr.columns:
                c4.metric("🏗️ Realisasi Timbunan", f"{pd.to_numeric(dr['Timbunan'], errors='coerce').sum():,.0f}")
            
            st.markdown('<div class="section-title">📋 Data Realisasi</div>', unsafe_allow_html=True)
            st.dataframe(dr, use_container_width=True, height=400)
        else:
            st.info("Data realisasi tidak tersedia")

# ================================================================
# SIDEBAR
# ================================================================
def render_sidebar():
    with st.sidebar:
        st.markdown('<p class="sidebar-header">⚙️ Dashboard Produksi</p>', unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="text-align:center;padding:1rem;background:#21262d;border-radius:12px;margin:1rem 0;">
            <p style="font-size:2.5rem;margin:0;">👤</p>
            <p style="color:#fff;font-weight:600;margin:0.5rem 0 0 0;">{st.session_state.name}</p>
            <p style="color:#8b949e;font-size:0.8rem;margin:0;text-transform:uppercase;">{st.session_state.role}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown('<p style="color:#58a6ff;font-size:0.85rem;font-weight:600;">📋 MENU NAVIGASI</p>', unsafe_allow_html=True)
        
        menus = [("🏠","Dashboard Overview"),("📊","Produksi Harian"),("🚨","Gangguan"),("⛽","Monitoring"),("📋","Daily Plan")]
        for icon, menu in menus:
            btn_type = "primary" if st.session_state.current_menu == menu else "secondary"
            if st.button(f"{icon} {menu}", key=f"menu_{menu}", use_container_width=True, type=btn_type):
                st.session_state.current_menu = menu
                st.rerun()
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True): logout(); st.rerun()
        
        st.markdown('<div style="text-align:center;color:#8b949e;font-size:0.75rem;margin-top:1rem;">⛏️ Semen Padang v3.0</div>', unsafe_allow_html=True)

# ================================================================
# MAIN
# ================================================================
def main():
    if not st.session_state.logged_in:
        show_login()
    else:
        render_sidebar()
        if st.session_state.current_menu == "Dashboard Overview": show_overview()
        elif st.session_state.current_menu == "Produksi Harian": show_produksi()
        elif st.session_state.current_menu == "Gangguan": show_gangguan()
        elif st.session_state.current_menu == "Monitoring": show_monitoring()
        elif st.session_state.current_menu == "Daily Plan": show_daily_plan()

if __name__ == "__main__":
    main()