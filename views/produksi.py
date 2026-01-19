# ============================================================
# PRODUKSI - Detailed Production Page
# ============================================================

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config import CHART_SEQUENCE
from utils import load_produksi
from utils.helpers import get_chart_layout


def show_produksi():
    """Render production detail page"""
    
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
