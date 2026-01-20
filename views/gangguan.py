# ============================================================
# GANGGUAN - Production Incident Analysis Page
# ============================================================
# VERSION: 2.0 - Full KPI & Charts Implementation

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config import MINING_COLORS, CHART_SEQUENCE
from utils import load_gangguan_all, get_gangguan_summary
from utils.helpers import get_chart_layout


def show_gangguan():
    """Render production incident analysis page"""
    
    # Page Header
    st.markdown("""
    <div class="page-header">
        <div class="page-header-icon">🚨</div>
        <div class="page-header-text">
            <h1>Gangguan Produksi</h1>
            <p>Production incident analysis & downtime tracking</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Load Data
    df = load_gangguan_all()
    
    if df.empty:
        st.warning("⚠️ Data gangguan tidak tersedia. Pastikan file Excel sudah terhubung.")
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
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        bulan_options = ['Semua'] + sorted(df['Bulan_Name'].dropna().unique().tolist(), 
                                           key=lambda x: ['Januari','Februari','Maret','April','Mei','Juni',
                                                         'Juli','Agustus','September','Oktober','November','Desember'].index(x) 
                                           if x in ['Januari','Februari','Maret','April','Mei','Juni',
                                                   'Juli','Agustus','September','Oktober','November','Desember'] else 99)
        selected_bulan = st.selectbox("📅 Bulan", bulan_options)
    
    with col2:
        shifts = ['Semua'] + sorted([int(x) for x in df['Shift'].dropna().unique() if pd.notna(x)])
        shifts = ['Semua'] + [str(s) for s in shifts[1:]]
        selected_shift = st.selectbox("🔄 Shift", shifts)
    
    with col3:
        kelompok_list = df['Kelompok Masalah'].dropna().unique().tolist()
        kelompok = ['Semua'] + sorted([str(k) for k in kelompok_list])
        selected_kelompok = st.selectbox("📂 Kelompok Masalah", kelompok)
    
    with col4:
        # Convert semua ke string untuk menghindari error sorting mixed types
        alat_list = df['Alat'].dropna().unique().tolist()
        alat_sorted = sorted([str(a) for a in alat_list])[:50]  # Limit to 50
        alat_options = ['Semua'] + alat_sorted
        selected_alat = st.selectbox("🔧 Alat", alat_options)
    
    # Apply Filters
    df_filtered = df.copy()
    if selected_bulan != 'Semua':
        df_filtered = df_filtered[df_filtered['Bulan_Name'] == selected_bulan]
    if selected_shift != 'Semua':
        df_filtered = df_filtered[df_filtered['Shift'] == int(selected_shift)]
    if selected_kelompok != 'Semua':
        df_filtered = df_filtered[df_filtered['Kelompok Masalah'] == selected_kelompok]
    if selected_alat != 'Semua':
        # Convert kolom Alat ke string untuk perbandingan
        df_filtered = df_filtered[df_filtered['Alat'].astype(str) == selected_alat]
    
    # Filter info
    st.markdown(f"""
    <p style="color:#64748b; font-size:0.85rem; margin:0.5rem 0 1.5rem 0;">
        📋 Menampilkan <strong style="color:#ef4444;">{len(df_filtered):,}</strong> dari {len(df):,} kejadian
    </p>
    """, unsafe_allow_html=True)
    
    # ===== KPI CARDS =====
    summary = get_gangguan_summary(df_filtered)
    
    # Calculate incident rate (per day)
    total_days = df_filtered['Tanggal'].nunique() if not df_filtered.empty else 1
    incident_rate = len(df_filtered) / max(total_days, 1)
    
    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi-card" style="--card-accent: #ef4444;">
            <div class="kpi-icon">🚨</div>
            <div class="kpi-label">Total Incidents</div>
            <div class="kpi-value">{summary['total_incidents']:,}</div>
            <div class="kpi-subtitle">kejadian tercatat</div>
        </div>
        <div class="kpi-card" style="--card-accent: #f59e0b;">
            <div class="kpi-icon">⏱️</div>
            <div class="kpi-label">Total Downtime</div>
            <div class="kpi-value">{summary['total_downtime']:,.1f}</div>
            <div class="kpi-subtitle">jam</div>
        </div>
        <div class="kpi-card" style="--card-accent: #3b82f6;">
            <div class="kpi-icon">📊</div>
            <div class="kpi-label">MTTR</div>
            <div class="kpi-value">{summary['mttr']*60:,.1f}</div>
            <div class="kpi-subtitle">menit/kejadian</div>
        </div>
        <div class="kpi-card" style="--card-accent: #10b981;">
            <div class="kpi-icon">📈</div>
            <div class="kpi-label">Incident Rate</div>
            <div class="kpi-value">{incident_rate:,.1f}</div>
            <div class="kpi-subtitle">per hari</div>
        </div>
        <div class="kpi-card" style="--card-accent: #8b5cf6;">
            <div class="kpi-icon">🔧</div>
            <div class="kpi-label">Alat Terdampak</div>
            <div class="kpi-value">{summary['total_alat']}</div>
            <div class="kpi-subtitle">unit</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ===== PARETO & KELOMPOK MASALAH =====
    st.markdown("""
    <div class="section-divider">
        <div class="section-divider-line"></div>
        <span class="section-divider-text">Analisis Pareto</span>
        <div class="section-divider-line" style="background: linear-gradient(90deg, transparent 0%, #1e3a5f 100%);"></div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<div class="chart-container"><div class="chart-header"><span class="chart-title">📊 Pareto Chart - Top 10 Gangguan</span><span class="chart-badge">80/20 Rule</span></div></div>', unsafe_allow_html=True)
        
        # Pareto data
        gangguan_count = df_filtered.groupby('Gangguan').agg({
            'Durasi': ['count', 'sum']
        }).reset_index()
        gangguan_count.columns = ['Gangguan', 'Frekuensi', 'Total_Durasi']
        gangguan_count = gangguan_count.sort_values('Frekuensi', ascending=False).head(10)
        
        # Calculate cumulative percentage
        total = gangguan_count['Frekuensi'].sum()
        gangguan_count['Cumulative'] = gangguan_count['Frekuensi'].cumsum() / total * 100
        
        # Create Pareto chart
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig.add_trace(
            go.Bar(
                x=gangguan_count['Gangguan'],
                y=gangguan_count['Frekuensi'],
                name='Frekuensi',
                marker_color='#ef4444',
                hovertemplate='<b>%{x}</b><br>Frekuensi: %{y:,}<extra></extra>'
            ),
            secondary_y=False
        )
        
        fig.add_trace(
            go.Scatter(
                x=gangguan_count['Gangguan'],
                y=gangguan_count['Cumulative'],
                name='Kumulatif %',
                line=dict(color='#d4a84b', width=3),
                mode='lines+markers',
                marker=dict(size=8),
                hovertemplate='<b>%{x}</b><br>Kumulatif: %{y:.1f}%<extra></extra>'
            ),
            secondary_y=True
        )
        
        # Add 80% line
        fig.add_hline(y=80, line_dash="dash", line_color="#64748b", 
                      annotation_text="80%", secondary_y=True)
        
        fig.update_layout(**get_chart_layout(height=380))
        fig.update_xaxes(tickangle=45)
        fig.update_yaxes(title_text="Frekuensi", secondary_y=False, showgrid=False)
        fig.update_yaxes(title_text="Kumulatif %", secondary_y=True, 
                         gridcolor='rgba(30,58,95,0.3)', range=[0, 105])
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    with col2:
        st.markdown('<div class="chart-container"><div class="chart-header"><span class="chart-title">📂 Kelompok Masalah</span></div></div>', unsafe_allow_html=True)
        
        kelompok_data = df_filtered.groupby('Kelompok Masalah')['Durasi'].agg(['count', 'sum']).reset_index()
        kelompok_data.columns = ['Kelompok', 'Frekuensi', 'Total_Durasi']
        
        fig = px.pie(
            kelompok_data, 
            values='Frekuensi', 
            names='Kelompok', 
            hole=0.6,
            color_discrete_sequence=['#ef4444', '#f59e0b', '#3b82f6', '#10b981']
        )
        fig.update_layout(**get_chart_layout(height=380, show_legend=True))
        fig.update_layout(legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5,
            font=dict(size=10)
        ))
        fig.update_traces(textposition='inside', textinfo='percent', textfont_size=12)
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # ===== TREN BULANAN =====
    st.markdown("""
    <div class="section-divider">
        <div class="section-divider-line"></div>
        <span class="section-divider-text">Tren Gangguan</span>
        <div class="section-divider-line" style="background: linear-gradient(90deg, transparent 0%, #1e3a5f 100%);"></div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="chart-container"><div class="chart-header"><span class="chart-title">📈 Tren Bulanan - Frekuensi & Downtime</span><span class="chart-badge">Combo Chart</span></div></div>', unsafe_allow_html=True)
    
    # Monthly trend
    bulan_order = ['Januari','Februari','Maret','April','Mei','Juni',
                   'Juli','Agustus','September','Oktober','November','Desember']
    
    monthly = df_filtered.groupby('Bulan_Name').agg({
        'Durasi': ['count', 'sum']
    }).reset_index()
    monthly.columns = ['Bulan', 'Frekuensi', 'Total_Downtime']
    monthly['Bulan'] = pd.Categorical(monthly['Bulan'], categories=bulan_order, ordered=True)
    monthly = monthly.sort_values('Bulan')
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Bar(
            x=monthly['Bulan'],
            y=monthly['Frekuensi'],
            name='Frekuensi',
            marker_color='rgba(239,68,68,0.7)',
            hovertemplate='<b>%{x}</b><br>Frekuensi: %{y:,}<extra></extra>'
        ),
        secondary_y=False
    )
    
    fig.add_trace(
        go.Scatter(
            x=monthly['Bulan'],
            y=monthly['Total_Downtime'],
            name='Total Downtime (jam)',
            line=dict(color='#d4a84b', width=3),
            mode='lines+markers',
            marker=dict(size=8),
            hovertemplate='<b>%{x}</b><br>Downtime: %{y:,.1f} jam<extra></extra>'
        ),
        secondary_y=True
    )
    
    fig.update_layout(**get_chart_layout(height=350))
    fig.update_yaxes(title_text="Frekuensi", secondary_y=False, showgrid=False, title_font=dict(color='#ef4444'))
    fig.update_yaxes(title_text="Downtime (jam)", secondary_y=True, gridcolor='rgba(30,58,95,0.3)', title_font=dict(color='#d4a84b'))
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # ===== TOP ALAT & SHIFT ANALYSIS =====
    st.markdown("""
    <div class="section-divider">
        <div class="section-divider-line"></div>
        <span class="section-divider-text">Analisis Detail</span>
        <div class="section-divider-line" style="background: linear-gradient(90deg, transparent 0%, #1e3a5f 100%);"></div>
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown('<div class="chart-container"><div class="chart-header"><span class="chart-title">🔧 Top 10 Alat Bermasalah</span></div></div>', unsafe_allow_html=True)
        
        alat_data = df_filtered.groupby('Alat')['Durasi'].agg(['count', 'sum']).reset_index()
        alat_data.columns = ['Alat', 'Frekuensi', 'Total_Durasi']
        alat_data = alat_data.sort_values('Frekuensi', ascending=True).tail(10)
        
        fig = px.bar(
            alat_data,
            x='Frekuensi',
            y='Alat',
            orientation='h',
            color='Frekuensi',
            color_continuous_scale=[[0, '#1e3a5f'], [0.5, '#ef4444'], [1, '#fbbf24']]
        )
        fig.update_layout(**get_chart_layout(height=320, show_legend=False))
        fig.update_coloraxes(showscale=False)
        fig.update_traces(hovertemplate='<b>%{y}</b><br>Frekuensi: %{x:,}<extra></extra>')
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    with c2:
        st.markdown('<div class="chart-container"><div class="chart-header"><span class="chart-title">🔄 Distribusi per Shift</span></div></div>', unsafe_allow_html=True)
        
        shift_data = df_filtered.groupby('Shift')['Durasi'].agg(['count', 'sum']).reset_index()
        shift_data.columns = ['Shift', 'Frekuensi', 'Total_Durasi']
        shift_data['Shift'] = shift_data['Shift'].astype(int).astype(str)
        shift_data['Shift'] = 'Shift ' + shift_data['Shift']
        
        fig = px.pie(
            shift_data,
            values='Frekuensi',
            names='Shift',
            hole=0.6,
            color_discrete_sequence=CHART_SEQUENCE[:3]
        )
        fig.update_layout(**get_chart_layout(height=320, show_legend=False))
        fig.update_traces(textposition='inside', textinfo='percent+label', textfont_size=12)
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    with c3:
        st.markdown('<div class="chart-container"><div class="chart-header"><span class="chart-title">⏱️ Downtime per Kelompok</span></div></div>', unsafe_allow_html=True)
        
        downtime_data = df_filtered.groupby('Kelompok Masalah')['Durasi'].sum().reset_index()
        downtime_data.columns = ['Kelompok', 'Total_Durasi']
        downtime_data = downtime_data.sort_values('Total_Durasi', ascending=True)
        
        fig = px.bar(
            downtime_data,
            x='Total_Durasi',
            y='Kelompok',
            orientation='h',
            color='Total_Durasi',
            color_continuous_scale=[[0, '#1e3a5f'], [0.5, '#f59e0b'], [1, '#ef4444']]
        )
        fig.update_layout(**get_chart_layout(height=320, show_legend=False))
        fig.update_coloraxes(showscale=False)
        fig.update_traces(hovertemplate='<b>%{y}</b><br>Downtime: %{x:,.1f} jam<extra></extra>')
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # ===== HEATMAP =====
    st.markdown("""
    <div class="section-divider">
        <div class="section-divider-line"></div>
        <span class="section-divider-text">Pola Gangguan</span>
        <div class="section-divider-line" style="background: linear-gradient(90deg, transparent 0%, #1e3a5f 100%);"></div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="chart-container"><div class="chart-header"><span class="chart-title">🔥 Heatmap Shift × Bulan</span><span class="chart-badge">Pattern Analysis</span></div></div>', unsafe_allow_html=True)
    
    # Create pivot for heatmap
    heatmap_data = df_filtered.copy()
    heatmap_data['Shift'] = 'Shift ' + heatmap_data['Shift'].astype(int).astype(str)
    
    pivot = heatmap_data.pivot_table(
        values='Durasi', 
        index='Shift', 
        columns='Bulan_Name', 
        aggfunc='count', 
        fill_value=0
    )
    
    # Reorder columns
    cols_order = [c for c in bulan_order if c in pivot.columns]
    pivot = pivot[cols_order]
    
    fig = px.imshow(
        pivot,
        color_continuous_scale=[[0, '#0f2744'], [0.3, '#1e3a5f'], [0.6, '#ef4444'], [1, '#fbbf24']],
        aspect='auto',
        labels=dict(x="Bulan", y="Shift", color="Frekuensi")
    )
    fig.update_layout(**get_chart_layout(height=250, show_legend=False))
    fig.update_xaxes(tickangle=45)
    
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
        # Kolom untuk export - sesuai dengan sheet All
        cols_export = ['Tanggal', 'Bulan', 'Tahun', 'Week', 'Shift', 'Start', 'End', 
                       'Durasi', 'Alat', 'Remarks', 'Kelompok Masalah', 'Gangguan', 
                       'Info CCR', 'Keterangan']
        cols_export = [c for c in cols_export if c in df_filtered.columns]
        csv = df_filtered[cols_export].to_csv(index=False)
        st.download_button(
            "📥 Export CSV",
            csv,
            "gangguan_filtered.csv",
            "text/csv",
            use_container_width=True
        )
    
    # Show dataframe - kolom sesuai sheet All
    cols_show = ['Tanggal', 'Shift', 'Start', 'End', 'Durasi', 'Alat', 
                 'Kelompok Masalah', 'Gangguan', 'Remarks', 'Info CCR']
    cols_show = [c for c in cols_show if c in df_filtered.columns]
    
    display_df = df_filtered[cols_show].copy()
    
    # Format tanggal
    if 'Tanggal' in display_df.columns:
        display_df['Tanggal'] = pd.to_datetime(display_df['Tanggal']).dt.strftime('%d/%m/%Y')
    
    # Format durasi
    if 'Durasi' in display_df.columns:
        display_df['Durasi'] = display_df['Durasi'].round(2)
    
    # Format waktu Start dan End
    if 'Start' in display_df.columns:
        display_df['Start'] = display_df['Start'].astype(str)
    if 'End' in display_df.columns:
        display_df['End'] = display_df['End'].astype(str)
    
    st.dataframe(
        display_df.sort_values('Tanggal', ascending=False),
        use_container_width=True,
        height=400,
        column_config={
            "Tanggal": st.column_config.TextColumn("Tanggal", width="small"),
            "Shift": st.column_config.NumberColumn("Shift", width="small"),
            "Start": st.column_config.TextColumn("Start", width="small"),
            "End": st.column_config.TextColumn("End", width="small"),
            "Durasi": st.column_config.NumberColumn("Durasi (jam)", format="%.2f", width="small"),
            "Alat": st.column_config.TextColumn("Alat", width="small"),
            "Kelompok Masalah": st.column_config.TextColumn("Kelompok Masalah", width="medium"),
            "Gangguan": st.column_config.TextColumn("Gangguan", width="medium"),
            "Remarks": st.column_config.TextColumn("Remarks", width="small"),
            "Info CCR": st.column_config.TextColumn("Info CCR", width="large"),
        }
    )