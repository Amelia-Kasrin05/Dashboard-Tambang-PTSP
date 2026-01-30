# ============================================================
# DASHBOARD - Professional Mining Operations Overview
# ============================================================
# Industry-grade mining operations monitoring
# Version 3.0 - Global Filters & Downloadable Tables

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd

from config import MINING_COLORS, CHART_SEQUENCE, DAILY_PRODUCTION_TARGET, DAILY_INTERNAL_TARGET
from utils.data_loader import (load_produksi, load_gangguan_all, load_ritase_by_front, 
                               load_stockpile_hopper, apply_global_filters)
from utils.helpers import get_chart_layout


def show_dashboard():
    """Professional Mining Operations Executive Summary"""
    
    # Page Header
    # Page Header
    st.markdown("""
    <style>
    /* FORCE OVERRIDE FOR CONTAINERS */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        /* VISIBLE CONTRAST CARD STYLE */
        background: linear-gradient(145deg, #1c2e4a 0%, #16253b 100%) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 16px !important;
        padding: 1.25rem !important;
        box-shadow: 0 4px 24px rgba(0,0,0,0.5) !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: rgba(255, 255, 255, 0.3) !important;
        background: linear-gradient(145deg, #233554 0%, #1c2e4a 100%) !important;
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.6) !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] > div {
       pointer-events: auto; 
    }
    </style>
    
    <div class="page-header">
        <div class="page-header-icon">📊</div>
        <div class="page-header-text">
            <h1>Ringkasan Eksekutif</h1>
            <p>Mining Operations Overview • Global View</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 1. LOAD & FILTER DATA
    # ----------------------------------------
    with st.spinner("Loading Executive Data..."):
        # Load Raw Data
        df_prod = load_produksi()
        df_gangguan = load_gangguan_all()
        df_ritase = load_ritase_by_front()
        # df_stockpile = load_stockpile_hopper() # Load later if needed to save memory
        
        # Apply Global Filters
        df_prod = apply_global_filters(df_prod, date_col='Date', shift_col='Shift')
        df_gangguan = apply_global_filters(df_gangguan, date_col='Date', shift_col='Shift')
        # Ritase loader might return grouped data, check structure carefully.
        # Ideally we filter raw ritase before grouping, but here we assume loader handles date/shift internally or we filter result.
        # For now, let's filter the dataframes that have Date/Shift columns.
        
    
    # 2. CALCULATE KPIS
    # ----------------------------------------
    kpi_prod = 0
    kpi_ritase = 0
    kpi_downtime = 0
    kpi_active_units = 0
    
    # Production & Ritase
    if not df_prod.empty:
        kpi_prod = df_prod['Tonnase'].sum()
        # Use 'Rit' column from production data for consistency
        if 'Rit' in df_prod.columns:
            kpi_ritase = df_prod['Rit'].sum()
            
        total_days = df_prod['Date'].nunique()
        target_prod = DAILY_PRODUCTION_TARGET * total_days if total_days > 0 else DAILY_PRODUCTION_TARGET
        ach_prod = (kpi_prod / target_prod * 100) if target_prod > 0 else 0
        active_exc = df_prod['Excavator'].nunique()
        active_dt = df_prod['Dump Truck'].nunique()
        kpi_active_units = active_exc + active_dt
    else:
        ach_prod = 0
            
    # Gangguan
    if not df_gangguan.empty:
        kpi_downtime = df_gangguan['Durasi'].sum()
        
    
    # 3. DISPLAY KPI CARDS
    # ----------------------------------------
    st.markdown(f"""
    <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 2rem;">
        <div class="kpi-card" style="--card-accent: #3b82f6;">
            <div class="kpi-icon">⛏️</div>
            <div class="kpi-label">Total Produksi</div>
            <div class="kpi-value">{kpi_prod:,.0f} <span style="font-size:1rem;color:#64748b">ton</span></div>
            <div class="kpi-subtitle">Pencapaian: {ach_prod:.1f}% vs Rencana</div>
        </div>
        <div class="kpi-card" style="--card-accent: #d4a84b;">
            <div class="kpi-icon">🚛</div>
            <div class="kpi-label">Total Ritase</div>
            <div class="kpi-value">{kpi_ritase:,.0f} <span style="font-size:1rem;color:#64748b">rit</span></div>
            <div class="kpi-subtitle">Performa Hauling</div>
        </div>
        <div class="kpi-card" style="--card-accent: #ef4444;">
            <div class="kpi-icon">🛑</div>
            <div class="kpi-label">Total Downtime</div>
            <div class="kpi-value">{kpi_downtime:,.1f} <span style="font-size:1rem;color:#64748b">jam</span></div>
            <div class="kpi-subtitle">Kehilangan Waktu Alat</div>
        </div>
        <div class="kpi-card" style="--card-accent: #10b981;">
            <div class="kpi-icon">🏗️</div>
            <div class="kpi-label">Unit Aktif</div>
            <div class="kpi-value">{kpi_active_units} <span style="font-size:1rem;color:#64748b">unit</span></div>
            <div class="kpi-subtitle">Utilisasi Armada</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 4. CHARTS SECTION
    # ----------------------------------------
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.container(border=True):
            st.markdown("#### 📈 Tren Produksi Harian")
            if not df_prod.empty:
                daily = df_prod.groupby('Date')['Tonnase'].sum().reset_index()
                fig = px.bar(daily, x='Date', y='Tonnase', 
                             color='Tonnase',
                             color_continuous_scale=[[0, '#ef4444'], [0.5, '#f59e0b'], [1, '#10b981']])
                
                # Add Target Line
                fig.add_hline(y=DAILY_PRODUCTION_TARGET, line_dash="dash", line_color="red", annotation_text="Target")
                
                fig.update_layout(**get_chart_layout(height=350))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Data produksi tidak tersedia")
                
    with col2:
        with st.container(border=True):
            st.markdown("#### 🥧 Komposisi Breakdown")
            if not df_gangguan.empty:
                pie_data = df_gangguan.groupby('Gangguan').size().reset_index(name='Count')
                fig = px.pie(pie_data, values='Count', names='Gangguan', hole=0.4,
                             color_discrete_sequence=px.colors.qualitative.Prism)
                fig.update_layout(**get_chart_layout(height=350, show_legend=False))
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Data breakdown tidak tersedia")

    # 5. DATA TABLE (DOWNLOAD)
    # ----------------------------------------
    st.markdown("### 📋 Data Detail Ringkasan")
    
    with st.expander("Lihat Tabel Data", expanded=True):
        if not df_prod.empty:
            st.dataframe(df_prod.head(100), use_container_width=True)
            
            # CSV Download
            csv = df_prod.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Unduh Data Produksi (CSV)",
                data=csv,
                file_name=f"produksi_export_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("Data kosong untuk rentang tanggal yang dipilih.")