import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime
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
.stTabs [data-baseweb="tab-list"] {gap:8px;background:#161b22;border-radius:10px;padding:5px;}
.stTabs [data-baseweb="tab"] {background:#21262d;border-radius:8px;color:#8b949e;padding:10px 20px;}
.stTabs [aria-selected="true"] {background:linear-gradient(90deg,#238636,#2ea043);color:#fff !important;}
div[data-testid="stMetric"] {background:linear-gradient(145deg,#1e2a3a,#16213e);border-radius:12px;padding:1rem;border:1px solid #30363d;}
div[data-testid="stMetric"] label {color:#8b949e !important;}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {color:#fff !important;}
.info-box {background:#1e3a5f;border-left:4px solid #58a6ff;padding:1rem;border-radius:0 8px 8px 0;margin:1rem 0;}
.filter-container {background:#161b22;border-radius:12px;padding:1rem;border:1px solid #30363d;margin-bottom:1rem;}
div[data-testid="stFileUploader"] {background:#21262d;border-radius:8px;padding:0.5rem;}
div[data-testid="stFileUploader"] section {padding:0.5rem;}
div[data-testid="stDateInput"] input {background:#21262d;border:1px solid #30363d;color:#fff;}
</style>
""", unsafe_allow_html=True)

# Session
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = st.session_state.role = st.session_state.name = None

def login(u, p):
    if u in USERS and USERS[u]['password'] == p:
        st.session_state.logged_in, st.session_state.username = True, u
        st.session_state.role, st.session_state.name = USERS[u]['role'], USERS[u]['name']
        return True
    return False

def logout():
    st.session_state.logged_in = False
    st.session_state.username = st.session_state.role = st.session_state.name = None

def chart_layout(title="", height=300):
    return dict(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=height,
        margin=dict(l=10,r=10,t=40 if title else 10,b=10),
        title=dict(text=title, x=0.5, font=dict(size=14)) if title else None,
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor='#21262d', zeroline=False),
        legend=dict(orientation='h', y=-0.15)
    )

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
        st.caption("Demo: supervisor/super123 | admin_produksi/prod123")

# ================================================================
# SUPERVISOR DASHBOARD - Executive Summary
# ================================================================
def show_supervisor():
    df = load_produksi()
    if df.empty: st.warning("⚠️ Data tidak tersedia"); return
    
    # KPI Cards Row
    cols = st.columns(5)
    metrics = [
        ("🚛", "Total Ritase", f"{df['Rit'].sum():,.0f}", "#00E676"),
        ("⚖️", "Total Tonase", f"{df['Tonnase'].sum():,.0f}", "#58a6ff"),
        ("🏗️", "Unit Excavator", f"{df['Excavator'].nunique()}", "#f0883e"),
        ("📅", "Hari Operasi", f"{df['Date'].nunique()}", "#a371f7"),
        ("📊", "Avg Ton/Hari", f"{df.groupby('Date')['Tonnase'].sum().mean():,.0f}", "#00E5FF")
    ]
    for col, (icon, label, value, color) in zip(cols, metrics):
        col.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">{icon}</div>
            <div class="metric-label">{label}</div>
            <div class="metric-value" style="color:{color}">{value}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Row 1: Trend + Per Excavator
    col1, col2 = st.columns([3,2])
    with col1:
        st.markdown('<div class="section-title">📈 Tren Produksi Harian (Area Chart)</div>', unsafe_allow_html=True)
        daily = df.groupby('Date').agg({'Tonnase':'sum','Rit':'sum'}).reset_index()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=daily['Date'], y=daily['Tonnase'], name='Tonase', fill='tozeroy',
                                 line=dict(color='#00E676',width=2), fillcolor='rgba(0,230,118,0.15)'))
        fig.update_layout(**chart_layout(height=320))
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown('<div class="section-title">🏗️ Produksi per Excavator (Horizontal Bar)</div>', unsafe_allow_html=True)
        exc = df.groupby('Excavator')['Tonnase'].sum().reset_index().sort_values('Tonnase')
        fig = px.bar(exc, x='Tonnase', y='Excavator', orientation='h', 
                     color='Tonnase', color_continuous_scale=['#1e3a5f','#58a6ff'])
        fig.update_layout(**chart_layout(height=320))
        fig.update_coloraxes(showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    
    # Row 2: Distribusi
    st.markdown('<div class="section-title">📊 Distribusi Produksi</div>', unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    
    with c1:
        mat = df.groupby('Commudity')['Tonnase'].sum().reset_index()
        fig = px.pie(mat, values='Tonnase', names='Commudity', hole=0.5,
                     color_discrete_sequence=['#00E676','#58a6ff','#f0883e','#a371f7'])
        fig.update_layout(**chart_layout("Material (Donut)", 240))
        st.plotly_chart(fig, use_container_width=True)
    
    with c2:
        shift = df.groupby('Shift')['Tonnase'].sum().reset_index()
        fig = px.bar(shift, x='Shift', y='Tonnase', color='Shift',
                     color_discrete_sequence=['#00E676','#58a6ff','#f0883e'])
        fig.update_layout(**chart_layout("Per Shift (Bar)", 240))
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with c3:
        front = df.groupby('Front')['Tonnase'].sum().reset_index().sort_values('Tonnase', ascending=False).head(8)
        fig = px.bar(front, x='Front', y='Tonnase', color_discrete_sequence=['#a371f7'])
        fig.update_layout(**chart_layout("Per Front (Bar)", 240))
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    
    with c4:
        dg = load_gangguan("Januari")
        if not dg.empty:
            fig = px.bar(dg.head(5), x='Frekuensi', y='Row Labels', orientation='h',
                         color_discrete_sequence=['#f85149'])
            fig.update_layout(**chart_layout("Top 5 Gangguan", 240))
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
    
    # Row 3: Heatmap Produktivitas
    st.markdown('<div class="section-title">🔥 Heatmap Produktivitas (Shift x Excavator)</div>', unsafe_allow_html=True)
    pivot = df.pivot_table(values='Tonnase', index='Excavator', columns='Shift', aggfunc='sum', fill_value=0)
    fig = px.imshow(pivot, color_continuous_scale='Greens', aspect='auto',
                    labels=dict(x="Shift", y="Excavator", color="Tonase"))
    fig.update_layout(**chart_layout(height=300))
    st.plotly_chart(fig, use_container_width=True)

# ================================================================
# PRODUKSI DASHBOARD - Detailed Analysis
# ================================================================
def show_produksi():
    tab1,tab2,tab3,tab4,tab5 = st.tabs(["📊 Produksi Harian","🚨 Gangguan","⛽ BBM & Monitoring","📈 Plan vs Aktual","📋 Daily Plan"])
    
    # TAB 1: PRODUKSI HARIAN
    with tab1:
        df = load_produksi()
        if df.empty: st.warning("⚠️ Data tidak tersedia"); return
        
        # Date Filter
        st.markdown('<div class="section-title">🔍 Filter Data</div>', unsafe_allow_html=True)
        col_f1, col_f2, col_f3, col_f4 = st.columns([1,1,1,1])
        
        min_date = df['Date'].min().date()
        max_date = df['Date'].max().date()
        
        with col_f1:
            start_date = st.date_input("📅 Dari Tanggal", min_date, min_value=min_date, max_value=max_date)
        with col_f2:
            end_date = st.date_input("📅 Sampai Tanggal", max_date, min_value=min_date, max_value=max_date)
        with col_f3:
            shifts = ['Semua'] + sorted(df['Shift'].unique().tolist())
            selected_shift = st.selectbox("🔄 Shift", shifts)
        with col_f4:
            excavators = ['Semua'] + sorted(df['Excavator'].unique().tolist())
            selected_exc = st.selectbox("🏗️ Excavator", excavators)
        
        # Apply filters
        mask = (df['Date'].dt.date >= start_date) & (df['Date'].dt.date <= end_date)
        if selected_shift != 'Semua':
            mask &= (df['Shift'] == selected_shift)
        if selected_exc != 'Semua':
            mask &= (df['Excavator'] == selected_exc)
        
        df_filtered = df[mask].copy()
        
        # Show filter info
        st.markdown(f'<p style="color:#8b949e;font-size:0.8rem;">Menampilkan {len(df_filtered):,} dari {len(df):,} data | {start_date} s/d {end_date}</p>', unsafe_allow_html=True)
        
        # KPI
        cols = st.columns(5)
        kpis = [
            ("🚛","Ritase",f"{df_filtered['Rit'].sum():,.0f}"),
            ("⚖️","Tonase",f"{df_filtered['Tonnase'].sum():,.0f}"),
            ("📊","Avg/Trip",f"{df_filtered['Tonnase'].mean():.0f}" if len(df_filtered) > 0 else "0"),
            ("🏗️","Excavator",f"{df_filtered['Excavator'].nunique()}"),
            ("📅","Hari",f"{df_filtered['Date'].nunique()}")
        ]
        for col,(icon,label,val) in zip(cols,kpis):
            col.markdown(f'<div class="metric-card"><div class="metric-icon">{icon}</div><div class="metric-label">{label}</div><div class="metric-value">{val}</div></div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Chart 1: Line + Bar Combo (Dual Axis)
        st.markdown('<div class="section-title">📈 Tren Produksi Harian - Tonase & Ritase (Combo Chart)</div>', unsafe_allow_html=True)
        daily = df_filtered.groupby('Date').agg({'Tonnase':'sum','Rit':'sum'}).reset_index()
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(x=daily['Date'], y=daily['Rit'], name='Ritase', marker_color='rgba(88,166,255,0.6)'), secondary_y=False)
        fig.add_trace(go.Scatter(x=daily['Date'], y=daily['Tonnase'], name='Tonase', line=dict(color='#00E676',width=3), mode='lines+markers'), secondary_y=True)
        fig.update_layout(**chart_layout(height=350))
        fig.update_yaxes(title_text="Ritase", secondary_y=False, showgrid=False)
        fig.update_yaxes(title_text="Tonase", secondary_y=True, showgrid=True, gridcolor='#21262d')
        st.plotly_chart(fig, use_container_width=True)
        
        # Row 2: Distribution Charts
        c1,c2,c3 = st.columns(3)
        with c1:
            st.markdown('<div class="section-title">🔄 Distribusi Shift (Donut)</div>', unsafe_allow_html=True)
            shift_data = df_filtered.groupby('Shift')['Tonnase'].sum().reset_index()
            fig = px.pie(shift_data, values='Tonnase', names='Shift', hole=0.5,
                         color_discrete_sequence=['#00E676','#58a6ff','#f0883e'])
            fig.update_layout(**chart_layout(height=280))
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        
        with c2:
            st.markdown('<div class="section-title">🏗️ Per Excavator (Horizontal Bar)</div>', unsafe_allow_html=True)
            exc = df_filtered.groupby('Excavator')['Tonnase'].sum().reset_index().sort_values('Tonnase')
            fig = px.bar(exc, x='Tonnase', y='Excavator', orientation='h',
                         color='Tonnase', color_continuous_scale='Greens')
            fig.update_layout(**chart_layout(height=280))
            fig.update_coloraxes(showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        
        with c3:
            st.markdown('<div class="section-title">🪨 Material (Donut)</div>', unsafe_allow_html=True)
            mat = df_filtered.groupby('Commudity')['Tonnase'].sum().reset_index()
            mat['Commudity'] = mat['Commudity'].astype(str)
            fig = px.pie(mat, values='Tonnase', names='Commudity', hole=0.5,
                         color_discrete_sequence=['#00E676','#58a6ff','#f0883e','#a371f7'])
            fig.update_layout(**chart_layout(height=280))
            st.plotly_chart(fig, use_container_width=True)
        
        # Row 3: Scatter & Heatmap
        c1,c2 = st.columns(2)
        with c1:
            st.markdown('<div class="section-title">🔗 Korelasi Rit vs Tonase (Scatter)</div>', unsafe_allow_html=True)
            sample = df_filtered.sample(min(500, len(df_filtered))) if len(df_filtered) > 0 else df_filtered
            fig = px.scatter(sample, x='Rit', y='Tonnase', color='Shift',
                             color_discrete_sequence=['#00E676','#58a6ff','#f0883e'],
                             opacity=0.7)
            fig.update_layout(**chart_layout(height=300))
            st.plotly_chart(fig, use_container_width=True)
        
        with c2:
            st.markdown('<div class="section-title">📅 Heatmap Produksi (Hari x Shift)</div>', unsafe_allow_html=True)
            df_filtered['DayOfWeek'] = df_filtered['Date'].dt.day_name()
            pivot = df_filtered.pivot_table(values='Tonnase', index='Shift', columns='DayOfWeek', aggfunc='mean', fill_value=0)
            day_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
            pivot = pivot.reindex(columns=[d for d in day_order if d in pivot.columns])
            fig = px.imshow(pivot, color_continuous_scale='Greens', aspect='auto')
            fig.update_layout(**chart_layout(height=300))
            st.plotly_chart(fig, use_container_width=True)
        
        # Data Table with Download
        st.markdown('<div class="section-title">📋 Data Detail</div>', unsafe_allow_html=True)
        col_dl1, col_dl2 = st.columns([4,1])
        with col_dl2:
            csv = df_filtered[['Date','Shift','Front','Commudity','Excavator','Dump Truck','Rit','Tonnase']].to_csv(index=False)
            st.download_button("📥 Download CSV", csv, "produksi_filtered.csv", "text/csv", use_container_width=True)
        st.dataframe(df_filtered[['Date','Shift','Front','Commudity','Excavator','Dump Truck','Rit','Tonnase']].sort_values('Date',ascending=False), 
                     use_container_width=True, height=300)
    
    # TAB 2: GANGGUAN
    with tab2:
        st.markdown('<div class="section-title">🚨 Analisis Gangguan Produksi</div>', unsafe_allow_html=True)
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
                # Pareto Chart
                st.markdown('<div class="section-title">📊 Pareto Chart - 80/20 Analysis</div>', unsafe_allow_html=True)
                dp = dg.head(10).copy()
                dp['Row Labels'] = dp['Row Labels'].astype(str)
                dp['Kumulatif'] = (dp['Frekuensi'].cumsum()/dg['Frekuensi'].sum()*100)
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                fig.add_trace(go.Bar(x=dp['Row Labels'], y=dp['Frekuensi'], name='Frekuensi', marker_color='#f85149'), secondary_y=False)
                fig.add_trace(go.Scatter(x=dp['Row Labels'], y=dp['Kumulatif'], name='Kumulatif %', 
                                         line=dict(color='#f0883e',width=3), mode='lines+markers'), secondary_y=True)
                fig.add_hline(y=80, line_dash="dash", line_color="#58a6ff", secondary_y=True, annotation_text="80%")
                fig.update_layout(**chart_layout(height=400))
                fig.update_xaxes(tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Pie Chart instead of Treemap (more stable)
                st.markdown('<div class="section-title">🥧 Proporsi Gangguan (Pie)</div>', unsafe_allow_html=True)
                dg_top = dg.head(8).copy()
                dg_top['Row Labels'] = dg_top['Row Labels'].astype(str)
                fig = px.pie(dg_top, values='Frekuensi', names='Row Labels', hole=0.4,
                             color_discrete_sequence=px.colors.sequential.Reds_r)
                fig.update_layout(**chart_layout(height=400))
                st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(dg, use_container_width=True, height=250)
        else:
            st.info(f"Data gangguan bulan {bulan} tidak tersedia")
    
    # TAB 3: BBM & MONITORING
    with tab3:
        st.markdown('<div class="section-title">⛽ Monitoring Konsumsi BBM</div>', unsafe_allow_html=True)
        db = load_bbm()
        
        if not db.empty:
            c1,c2,c3 = st.columns(3)
            c1.metric("⛽ Total BBM", f"{db['Total'].sum():,.0f} L")
            c2.metric("🏗️ Jumlah Alat", len(db))
            c3.metric("📊 Avg/Alat", f"{db['Total'].mean():,.0f} L")
            
            col1, col2 = st.columns(2)
            with col1:
                # Pie per Jenis Alat
                st.markdown('<div class="section-title">📊 Distribusi BBM per Jenis Alat (Donut)</div>', unsafe_allow_html=True)
                bbm_type = db.groupby('Alat Berat')['Total'].sum().reset_index()
                fig = px.pie(bbm_type, values='Total', names='Alat Berat', hole=0.5,
                             color_discrete_sequence=['#f0883e','#f85149','#a371f7','#00E676'])
                fig.update_layout(**chart_layout(height=350))
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Top 10 BBM
                st.markdown('<div class="section-title">🔝 Top 10 Konsumsi BBM (Horizontal Bar)</div>', unsafe_allow_html=True)
                top10 = db.nlargest(10,'Total')
                fig = px.bar(top10, x='Total', y='Tipe Alat', orientation='h',
                             color='Total', color_continuous_scale='OrRd')
                fig.update_layout(**chart_layout(height=350))
                fig.update_coloraxes(showscale=False)
                fig.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
            
            # Ritase per Front
            st.markdown('<div class="section-title">🚛 Ritase per Front (Stacked Bar)</div>', unsafe_allow_html=True)
            dr = load_ritase()
            if not dr.empty:
                rc = [c for c in dr.columns if c not in ['Tanggal','Shift','Pengawasan']]
                tot = dr[rc].sum().reset_index()
                tot.columns = ['Front','Total']
                tot = tot[tot['Total']>0].sort_values('Total', ascending=True)
                fig = px.bar(tot, x='Total', y='Front', orientation='h',
                             color='Total', color_continuous_scale='Blues')
                fig.update_layout(**chart_layout(height=400))
                fig.update_coloraxes(showscale=False)
                st.plotly_chart(fig, use_container_width=True)
    
    # TAB 4: PLAN VS AKTUAL
    with tab4:
        st.markdown('<div class="section-title">📈 Analisis Plan vs Aktual</div>', unsafe_allow_html=True)
        bln = st.selectbox("Pilih Bulan", ["Januari","Februari"], key="plan_bulan")
        da = load_analisa_produksi(bln)
        
        if not da.empty:
            # KPIs
            total_plan = da['Plan'].sum()
            total_aktual = da['Aktual'].sum()
            achievement = (total_aktual/total_plan*100) if total_plan > 0 else 0
            
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("📋 Total Plan", f"{total_plan:,.0f}")
            c2.metric("✅ Total Aktual", f"{total_aktual:,.0f}")
            c3.metric("📊 Achievement", f"{achievement:.1f}%")
            c4.metric("📉 Variance", f"{total_aktual-total_plan:,.0f}")
            
            col1, col2 = st.columns([2,1])
            with col1:
                # Grouped Bar
                st.markdown('<div class="section-title">📊 Plan vs Aktual Harian (Grouped Bar)</div>', unsafe_allow_html=True)
                fig = go.Figure()
                fig.add_trace(go.Bar(x=da['Tanggal'], y=da['Plan'], name='Plan', marker_color='#58a6ff'))
                fig.add_trace(go.Bar(x=da['Tanggal'], y=da['Aktual'], name='Aktual', marker_color='#00E676'))
                fig.update_layout(**chart_layout(height=400))
                fig.update_layout(barmode='group')
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Gauge Chart
                st.markdown('<div class="section-title">🎯 Achievement Rate (Gauge)</div>', unsafe_allow_html=True)
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number+delta",
                    value = achievement,
                    delta = {'reference': 100, 'relative': False},
                    gauge = {
                        'axis': {'range': [0, 120], 'tickwidth': 1},
                        'bar': {'color': "#00E676"},
                        'bgcolor': "white",
                        'borderwidth': 2,
                        'bordercolor': "#30363d",
                        'steps': [
                            {'range': [0, 70], 'color': '#f85149'},
                            {'range': [70, 90], 'color': '#f0883e'},
                            {'range': [90, 120], 'color': '#238636'}
                        ],
                        'threshold': {'line': {'color': "#58a6ff", 'width': 4}, 'thickness': 0.75, 'value': 100}
                    },
                    title = {'text': "Target 100%"}
                ))
                fig.update_layout(**chart_layout(height=300))
                st.plotly_chart(fig, use_container_width=True)
                
                # Variance Chart
                st.markdown('<div class="section-title">📉 Variance Harian</div>', unsafe_allow_html=True)
                da['Variance'] = da['Aktual'] - da['Plan']
                da['Color'] = da['Variance'].apply(lambda x: '#00E676' if x >= 0 else '#f85149')
                fig = go.Figure(go.Bar(x=da['Tanggal'], y=da['Variance'], marker_color=da['Color']))
                fig.update_layout(**chart_layout(height=200))
                fig.add_hline(y=0, line_color='#8b949e')
                st.plotly_chart(fig, use_container_width=True)
    
    # TAB 5: DAILY PLAN
    with tab5:
        st.markdown('<div class="section-title">📋 Daily Plan & Realisasi</div>', unsafe_allow_html=True)
        t1,t2 = st.tabs(["📅 Scheduling","✅ Realisasi"])
        
        with t1:
            dp = load_daily_plan()
            if not dp.empty:
                st.dataframe(dp, use_container_width=True, height=450)
            else:
                st.info("Data scheduling tidak tersedia")
        
        with t2:
            dr = load_realisasi()
            if not dr.empty:
                st.dataframe(dr, use_container_width=True, height=450)
            else:
                st.info("Data realisasi tidak tersedia")

# ================================================================
# MAIN
# ================================================================
def main():
    if not st.session_state.logged_in:
        show_login()
    else:
        with st.sidebar:
            if st.session_state.role == 'supervisor':
                st.markdown('<p class="sidebar-header">📊 Dashboard Supervisor</p>', unsafe_allow_html=True)
            else:
                st.markdown('<p class="sidebar-header">⚙️ Dashboard Produksi</p>', unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="text-align:center;padding:1rem;background:#21262d;border-radius:12px;margin:1rem 0;">
                <p style="font-size:2.5rem;margin:0;">👤</p>
                <p style="color:#fff;font-weight:600;margin:0.5rem 0 0 0;font-size:1.1rem;">{st.session_state.name}</p>
                <p style="color:#8b949e;font-size:0.8rem;margin:0;text-transform:uppercase;">{st.session_state.role}</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.session_state.role == 'supervisor':
                st.markdown("---")
                menu = st.radio("📋 Menu", ["🏠 Executive Summary","⚙️ Detail Produksi"], label_visibility="collapsed")
            else:
                menu = "⚙️ Detail Produksi"
            
            st.markdown("---")
            
            # File Upload Section
            st.markdown('<p style="color:#8b949e;font-size:0.85rem;margin-bottom:0.5rem;">📤 Upload Data Excel</p>', unsafe_allow_html=True)
            uploaded_file = st.file_uploader("", type=['xlsx','xls'], label_visibility="collapsed", key="excel_upload")
            if uploaded_file:
                try:
                    import os
                    upload_path = f"data/{uploaded_file.name}"
                    with open(upload_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    st.success(f"✅ {uploaded_file.name}")
                    # Clear cache to reload data
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"❌ Gagal upload")
            
            st.markdown("---")
            if st.button("🚪 Logout", use_container_width=True): logout(); st.rerun()
            
            st.markdown("---")
            st.markdown("""
            <div style="text-align:center;color:#8b949e;font-size:0.75rem;">
                <p style="margin:0;">⛏️ Dashboard Tambang</p>
                <p style="margin:0;">Semen Padang v2.1</p>
                <p style="margin:0.5rem 0 0 0;font-size:0.65rem;">© 2025 Mining Ops</p>
            </div>
            """, unsafe_allow_html=True)
        
        if st.session_state.role == 'supervisor' and menu == "🏠 Executive Summary":
            show_supervisor()
        else:
            show_produksi()

if __name__ == "__main__":
    main()