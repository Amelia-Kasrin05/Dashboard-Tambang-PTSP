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
from utils.data_loader import (
    load_produksi,
    load_gangguan_all,
    load_shipping_data,
    load_stockpile_hopper,
    load_analisa_produksi_all,
    load_ritase_by_front,
    apply_global_filters
)
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
    with st.spinner("Memuat Data Eksekutif..."):
        # Load Raw Data
        df_prod = load_produksi()
        df_gangguan = load_gangguan_all()
        df_shipping = load_shipping_data()       # NEW: Load Shipping
        df_stockpile = load_stockpile_hopper()   # NEW: Load Stockpile
        
        # Apply Global Filters
      # 1. APPLY GLOBAL FILTERS
    # ----------------------------------------
    # Apply filters to ALL dataframes to ensure consistency
    # Note: apply_global_filters handles date range & shift filtering
    
    # Production
    if not df_prod.empty:
        df_prod = apply_global_filters(df_prod, date_col='Date', shift_col='Shift')
        
    # Shipping
    if not df_shipping.empty:
        df_shipping = apply_global_filters(df_shipping, date_col='Date', shift_col='Shift')

    # Downtime (Gangguan) - Use 'Tanggal' if 'Date' missing
    if not df_gangguan.empty:
        date_col_gangguan = 'Date' if 'Date' in df_gangguan.columns else 'Tanggal'
        df_gangguan = apply_global_filters(df_gangguan, date_col=date_col_gangguan, shift_col='Shift')
        # Ensure we have a standard 'Date' column for later merging
        if 'Date' not in df_gangguan.columns and 'Tanggal' in df_gangguan.columns:
            df_gangguan['Date'] = pd.to_datetime(df_gangguan['Tanggal'])

    # Stockpile
    if not df_stockpile.empty:
         # Map Tanggal to Date for consistency
         if 'Tanggal' in df_stockpile.columns:
             df_stockpile['Date'] = pd.to_datetime(df_stockpile['Tanggal'])
         
         if 'Date' in df_stockpile.columns:
             df_stockpile = apply_global_filters(df_stockpile, date_col='Date', shift_col='Shift')
        
    # 2. CALCULATE KPIS
    # ----------------------------------------
    kpi_prod = 0
    kpi_shipping = 0
    kpi_stockpile = 0
    kpi_downtime = 0
    
    # Production
    if not df_prod.empty:
        kpi_prod = df_prod['Tonnase'].sum()
        total_days = df_prod['Date'].nunique()
        target_prod = DAILY_PRODUCTION_TARGET * total_days if total_days > 0 else DAILY_PRODUCTION_TARGET
        ach_prod = (kpi_prod / target_prod * 100) if target_prod > 0 else 0
    else:
        ach_prod = 0
            
    # Shipping (Replaces Ritase)
    if not df_shipping.empty and 'Quantity' in df_shipping.columns:
        kpi_shipping = df_shipping['Quantity'].sum()
        
    # Stockpile (New Metric - Activity based)
    if not df_stockpile.empty and 'Ritase' in df_stockpile.columns:
        kpi_stockpile = df_stockpile['Ritase'].sum()
    elif not df_stockpile.empty and 'Volume' in df_stockpile.columns:
        kpi_stockpile = df_stockpile['Volume'].sum()

    # Gangguan
    if not df_gangguan.empty:
        kpi_downtime = df_gangguan['Durasi'].sum()
        
    
    # 3. DISPLAY KPI CARDS
    # ----------------------------------------
    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi-card" style="--card-accent: #3b82f6;">
            <div class="kpi-icon">⛏️</div>
            <div class="kpi-label">Total Produksi</div>
            <div class="kpi-value">{kpi_prod:,.0f} <span style="font-size:1rem;color:#64748b">ton</span></div>
            <div class="kpi-subtitle">Pencapaian: {ach_prod:.1f}% vs Rencana</div>
        </div>
        <div class="kpi-card" style="--card-accent: #10b981;">
            <div class="kpi-icon">🚢</div>
            <div class="kpi-label">Total Pengiriman</div>
            <div class="kpi-value">{kpi_shipping:,.0f} <span style="font-size:1rem;color:#64748b">ton</span></div>
            <div class="kpi-subtitle">Sales & Shipping</div>
        </div>
        <div class="kpi-card" style="--card-accent: #f59e0b;">
            <div class="kpi-icon">🏔️</div>
            <div class="kpi-label">Total Stockpile</div>
            <div class="kpi-value">{kpi_stockpile:,.0f} <span style="font-size:1rem;color:#64748b">ton</span></div>
            <div class="kpi-subtitle">Inventory Balance</div>
        </div>
        <div class="kpi-card" style="--card-accent: #ef4444;">
            <div class="kpi-icon">🛑</div>
            <div class="kpi-label">Total Downtime</div>
            <div class="kpi-value">{kpi_downtime:,.1f} <span style="font-size:1rem;color:#64748b">jam</span></div>
            <div class="kpi-subtitle">Kehilangan Waktu Alat</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 4. TIME ANALYSIS SECTION (Row 2)
    # ----------------------------------------
    col_trend1, col_trend2 = st.columns(2)
    
    with col_trend1:
        with st.container(border=True):
            st.markdown("#### 📈 Tren Produksi Harian")
            if not df_prod.empty:
                daily = df_prod.groupby('Date')['Tonnase'].sum().reset_index()
                
                # Load Dynamic Plan/Target
                df_plan = load_analisa_produksi_all()
                if not df_plan.empty and 'Tanggal' in df_plan.columns:
                     df_plan['Date'] = pd.to_datetime(df_plan['Tanggal'])
                     # Filter Plan to match selected date range
                     df_plan = apply_global_filters(df_plan, date_col='Date', shift_col=None) # Plan is daily, no shift
                     
                     # Group by Date to handle duplicates if any
                     daily_plan = df_plan.groupby('Date')['Plan'].sum().reset_index()
                     
                     # Merge
                     daily = pd.merge(daily, daily_plan, on='Date', how='left').fillna(0)
                
                # Professional Conditional Coloring
                # Logic:
                # - Green: >= Internal Target (Excellent)
                # - Blue: >= RKAP (Good/Safe)
                # - Red: < RKAP (Alert)
                def get_bar_color(row):
                    # Dynamic Plan (RKAP)
                    plan_target = row['Plan'] if 'Plan' in row and row['Plan'] > 0 else DAILY_PRODUCTION_TARGET
                    
                    if row['Tonnase'] >= DAILY_INTERNAL_TARGET:
                        return '#10b981' # Green (Emerald 500)
                    elif row['Tonnase'] >= plan_target:
                        return '#3b82f6' # Blue (Blue 500)
                    else:
                        return '#ef4444' # Red (Red 500)

                daily['Color'] = daily.apply(get_bar_color, axis=1)

                fig = px.bar(daily, x='Date', y='Tonnase', 
                             title="",
                             text_auto='.2s',  # Format: 24k
                             # Use direct color mapping
                             color_discrete_sequence=daily['Color'].unique().tolist()
                             )
                
                # Manual Color Update (Since px.bar with custom per-bar color is tricky, we update traces)
                fig.update_traces(marker_color=daily['Color'], textposition='inside', textangle=-90, textfont_size=12)
                
                # Add Dynamic Target Line (Plan/RKAP)
                if 'Plan' in daily.columns and daily['Plan'].sum() > 0:
                     fig.add_trace(go.Scatter(
                        x=daily['Date'], y=daily['Plan'],
                        name='Target RKAP',
                        mode='lines', 
                        line=dict(color='red', width=2, dash='dash')
                     ))
                else:
                     # Fallback
                     fig.add_hline(y=DAILY_PRODUCTION_TARGET, line_dash="dash", line_color="red", annotation_text="Target RKAP")

                # Add Internal Target Line (Static 25,000)
                # Use add_trace (Scatter) instead of hline so it appears in Legend
                fig.add_trace(go.Scatter(
                    x=daily['Date'], y=[DAILY_INTERNAL_TARGET]*len(daily),
                    name='Target Internal',
                    mode='lines',
                    line=dict(color='#f59e0b', width=2, dash='dot') # Gold/Orange dotted
                ))
                
                fig.update_layout(**get_chart_layout(height=350))
                fig.update_layout(legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center")) 
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Data produksi tidak tersedia")

    with col_trend2:
        with st.container(border=True):
            st.markdown("#### ⚖️ Balance: Produksi vs Pengiriman")
            
            # Prepare Data Merge
            daily_prod = pd.DataFrame()
            daily_ship = pd.DataFrame()
            
            if not df_prod.empty:
                daily_prod = df_prod.groupby('Date')['Tonnase'].sum().reset_index()
                daily_prod.rename(columns={'Tonnase': 'Produksi'}, inplace=True)
                
            if not df_shipping.empty:
                daily_ship = df_shipping.groupby('Date')['Quantity'].sum().reset_index()
                daily_ship.rename(columns={'Quantity': 'Pengiriman'}, inplace=True)
            
            if not daily_prod.empty:
                # Merge logic
                df_chart = daily_prod.copy()
                if not daily_ship.empty:
                    df_chart = pd.merge(df_chart, daily_ship, on='Date', how='outer').fillna(0)
                
                df_chart = df_chart.sort_values('Date')
                
                fig = go.Figure()
                
                # Bar: Produksi
                fig.add_trace(go.Bar(
                    x=df_chart['Date'], y=df_chart['Produksi'],
                    name='Produksi',
                    marker_color='#3b82f6',
                    opacity=0.7,
                    text=df_chart['Produksi'],
                    texttemplate='%{text:.2s}', # Format: 24k
                    textposition='inside',
                    textangle=-90,
                    textfont_size=12
                ))
                
                # Line: Pengiriman
                fig.add_trace(go.Scatter(
                    x=df_chart['Date'], y=df_chart.get('Pengiriman', [0]*len(df_chart)),
                    name='Pengiriman',
                    mode='lines+markers',
                    line=dict(color='#10b981', width=3)
                ))
                
                fig.update_layout(**get_chart_layout(height=350))
                fig.update_layout(legend=dict(orientation="h", y=1.1))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Data balance belum tersedia.")

    # 5. OPERATIONAL DETAIL SECTION (Row 3 - NEW)
    # ----------------------------------------
    col_ops1, col_ops2 = st.columns(2)
    
    with col_ops1:
        with st.container(border=True):
            st.markdown("#### 🚜 Top 5 Excavator Performance")
            if not df_prod.empty and 'Excavator' in df_prod.columns:
                # Group by Excavator
                exca_perf = df_prod.groupby('Excavator')['Tonnase'].sum().reset_index()
                exca_perf = exca_perf.sort_values('Tonnase', ascending=True).tail(5) # Top 5
                
                fig = px.bar(exca_perf, x='Tonnase', y='Excavator', orientation='h',
                             text='Tonnase',
                             # Solid Blue Color
                             color_discrete_sequence=['#3b82f6'])
                
                fig.update_layout(**get_chart_layout(height=320, show_legend=False))
                fig.update_traces(texttemplate='%{text:,.0f}', textposition='inside')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Data excavator tidak tersedia.")
                
    with col_ops2:
        with st.container(border=True):
            st.markdown("#### 📍 Ritase per Front (Lokasi)")
            # Use df_prod 'Front' if available, otherwise load_ritase_by_front?
            # df_prod usually has 'Front'. Let's check.
            data_source = pd.DataFrame()
            if not df_prod.empty and 'Front' in df_prod.columns:
                 data_source = df_prod.groupby('Front')['Rit'].sum().reset_index()
                 data_source.columns = ['Front', 'Total_Ritase']
            elif not df_ritase.empty:
                 data_source = df_ritase # load_ritase_by_front returns summary df
                 
            if not data_source.empty:
                data_source = data_source.sort_values('Total_Ritase', ascending=True)
                
                fig = px.bar(data_source, x='Total_Ritase', y='Front', orientation='h',
                             text='Total_Ritase',
                             # Solid Gold/Orange Color
                             color_discrete_sequence=['#f59e0b'])
                             
                fig.update_layout(**get_chart_layout(height=320, show_legend=False))
                fig.update_traces(texttemplate='%{text:,.0f}', textposition='inside')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Data lokasi front tidak tersedia.")

    # 6. DAILY RECAP TABLE (Replacement for Raw Data)
    # ----------------------------------------
    st.markdown("### 📋 Rekapitulasi Harian (Daily Report)")
    
    with st.expander("Lihat Data Harian", expanded=True):
        # 1. Aggregate Data by Date
        recap_df = pd.DataFrame()
        
        # Base: Date Range from Filter or from Data
        if not df_prod.empty:
            dates = df_prod['Date'].unique()
        elif not df_shipping.empty:
            dates = df_shipping['Date'].unique()
        else:
            dates = []
            
        if len(dates) > 0:
            recap_df = pd.DataFrame({'Date': sorted(dates)})
            
            # Merge Production
            if not df_prod.empty:
                d_prod = df_prod.groupby('Date')['Tonnase'].sum().reset_index()
                recap_df = pd.merge(recap_df, d_prod, on='Date', how='left')
                recap_df.rename(columns={'Tonnase': 'Produksi (Ton)'}, inplace=True)
                
            # Merge Shipping
            if not df_shipping.empty:
                d_ship = df_shipping.groupby('Date')['Quantity'].sum().reset_index()
                recap_df = pd.merge(recap_df, d_ship, on='Date', how='left')
                recap_df.rename(columns={'Quantity': 'Pengiriman (Ton)'}, inplace=True)
                
            # Merge Stockpile Activity
            # Note: Stockpile 'Date' might need care if it's snapshot only. 
            # Assuming df_stockpile has 'Tanggal' mapped to 'Date' in loader
            # But wait, df_stockpile from previous step might rely on 'Date' column.
            # Let's check df_stockpile columns first.
            if not df_stockpile.empty and 'Tanggal' in df_stockpile.columns:
                 # Rename for consistency if needed, but apply_global_filters uses 'Date'
                 # Loader returns 'Tanggal'. Let's ensure consistency.
                 # Ah, apply_global_filters was called on df_stockpile? No, it was skipped/commented or done?
                 # In Step 1: df_stockpile = load_stockpile_hopper() -> apply_global_filters NOT CALLLED on it for Date.
                 # Because Stockpile is usually snapshot.
                 # However, for Activity Log (Ritase), it IS historical.
                 # So we SHOULD aggregate it by Date if available.
                 
                 d_stock = df_stockpile.copy()
                 if 'Tanggal' in d_stock.columns:
                     d_stock['Date'] = pd.to_datetime(d_stock['Tanggal'])
                     d_stock = d_stock.groupby('Date')['Ritase'].sum().reset_index()
                     recap_df = pd.merge(recap_df, d_stock, on='Date', how='left')
                     recap_df.rename(columns={'Ritase': 'Stockpile Activity (Rit)'}, inplace=True)

            # Merge Downtime
            if not df_gangguan.empty:
                # Ensure Date column exists
                if 'Date' not in df_gangguan.columns and 'Tanggal' in df_gangguan.columns:
                    df_gangguan['Date'] = pd.to_datetime(df_gangguan['Tanggal'])
                
                if 'Date' in df_gangguan.columns:
                    d_down = df_gangguan.groupby('Date')['Durasi'].sum().reset_index()
                    recap_df = pd.merge(recap_df, d_down, on='Date', how='left')
                    recap_df.rename(columns={'Durasi': 'Downtime (Jam)'}, inplace=True)
            
            # Cleanup
            recap_df = recap_df.fillna(0)
            
            # Format Date
            recap_df['Date'] = recap_df['Date'].dt.strftime('%d-%b-%Y')
            
            # Display
            st.dataframe(recap_df, use_container_width=True, hide_index=True)
            
            # Prepare Excel Download (OLDEST to NEWEST)
            # Note: df_display is currently reversed (Newest First) for display
            # So we can just reverse it back or sort df_prod
            df_download = df_prod.sort_values(by=['Date', 'TimeStr'], ascending=True) if 'TimeStr' in df_prod.columns else df_prod.sort_values(by='Date', ascending=True)
             
            from utils.helpers import convert_df_to_excel
            excel_data = convert_df_to_excel(df_download)
            
            st.download_button(
                label="📥 Unduh Data (Excel)",
                data=excel_data,
                file_name=f"PTSP_Ringkasan_Eksekutif_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )
        else:
            st.warning("Tidak ada data untuk ditampilkan pada rentang tanggal ini.")