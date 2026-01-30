# ============================================================
# GANGGUAN - Production Incident Analysis Page
# ============================================================
# VERSION: 3.0 - Professional Layout with Global Filters

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from config import MINING_COLORS
from utils.data_loader import load_gangguan_all, apply_global_filters, load_produksi # Added load_produksi
from utils.helpers import get_chart_layout


def show_gangguan():
    """Maintenance & Breakdown Analysis"""
    
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
        <div class="page-header-icon">🚨</div>
        <div class="page-header-text">
            <h1>Gangguan Produksi</h1>
            <p>Analisis kerusakan unit & availability (Maintenance)</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 1. LOAD DATA
    with st.spinner("Loading Maintenance Data..."):
        df_gangguan = load_gangguan_all()
        # Load Production to get Total Active Fleet Size (Professional Standard)
        df_prod = load_produksi()
        
        # Apply Global Filters
        df_gangguan = apply_global_filters(df_gangguan, date_col='Tanggal')
        df_prod = apply_global_filters(df_prod, date_col='Date')
        
    if df_gangguan.empty:
        st.warning("⚠️ Data Gangguan tidak tersedia.")
        return
        
    # 2. CALCULATE KPIS
    # ----------------------------------------
    total_downtime = df_gangguan['Durasi'].sum()
    total_incidents = len(df_gangguan)
    
    # PROFESSIONAL PA CALCULATION
    # Base: Total Active Fleet (from Production) * 24 Hours * Days
    # If using breakdown list only, we ignore healthy units -> PA is underestimated
    
    # Get Fleet Size from Production Data (Excavators + DTs)
    active_units_list = set()
    if not df_prod.empty:
        if 'Excavator' in df_prod.columns:
            active_units_list.update(df_prod['Excavator'].unique())
        if 'Dump Truck' in df_prod.columns:
            active_units_list.update(df_prod['Dump Truck'].unique())
            
    fleet_size = len(active_units_list)
    
    # Fallback if production data is missing but we have breakdown data
    if fleet_size == 0:
        fleet_size = df_gangguan['Alat'].nunique()
        
    # Calculate Calendar Time
    if 'Tanggal' in df_gangguan.columns and not df_gangguan.empty:
        days = (df_gangguan['Tanggal'].max() - df_gangguan['Tanggal'].min()).days + 1
    else:
        days = 1
        
    scheduled_hours = fleet_size * 24 * days
    
    # PA Formula
    if scheduled_hours > 0:
        pa_score = ((scheduled_hours - total_downtime) / scheduled_hours) * 100
    else:
        pa_score = 0
        
    mttr = total_downtime / total_incidents if total_incidents > 0 else 0
    
    # Determine pa_color for the gauge
    if pa_score >= 92:
        pa_color = '#10b981' # Green
    elif pa_score >= 85:
        pa_color = '#f59e0b' # Yellow
    else:
        pa_color = '#ef4444' # Red

    # 3. KPI CARDS (PROFESSIONAL WITH GAUGE)
    # ----------------------------------------
    
    # Create Columns: GAUSE (Left) + 3 CARDS (Right)
    col_gauge, col_kpi = st.columns([1.5, 3.5])
    
    with col_gauge:
        # GAUGE CHART FOR PA (Physical Availability)
        # Visualizing "Health" of the Fleet
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = pa_score,
            title = {'text': "Ketersediaan Fisik (PA)", 'font': {'size': 14, 'color': '#cbd5e1'}},
            number = {'suffix': "%", 'font': {'size': 24, 'color': 'white'}},
            gauge = {
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "white"},
                'bar': {'color': pa_color},
                'bgcolor': "rgba(0,0,0,0)",
                'borderwidth': 2,
                'bordercolor': "#334155",
                'steps': [
                    {'range': [0, 85], 'color': 'rgba(239, 68, 68, 0.3)'},   # Red Zone
                    {'range': [85, 92], 'color': 'rgba(245, 158, 11, 0.3)'}, # Yellow Zone
                    {'range': [92, 100], 'color': 'rgba(16, 185, 129, 0.3)'} # Green Zone
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 4},
                    'thickness': 0.75,
                    'value': 92 # Target PA
                }
            }
        ))
        
        fig_gauge.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", 
            font={'color': "white", 'family': "Arial"},
            margin=dict(t=30, b=10, l=30, r=30),
            height=200
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_kpi:
        # OTHER 3 METRICS IN CARDS
        st.markdown(f"""
        <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-top: 1rem;">
            <div class="kpi-card" style="--card-accent: #ef4444;">
                <div class="kpi-icon">🛑</div>
                <div class="kpi-label">Total Downtime</div>
                <div class="kpi-value">{total_downtime:,.1f}</div>
                <div class="kpi-subtitle">Jam (Hours)</div>
            </div>
            <div class="kpi-card" style="--card-accent: #f59e0b;">
                <div class="kpi-icon">⚡</div>
                <div class="kpi-label">Frekuensi Gangguan</div>
                <div class="kpi-value">{total_incidents:,.0f}</div>
                <div class="kpi-subtitle">Kali Kejadian</div>
            </div>
            <div class="kpi-card" style="--card-accent: #3b82f6;">
                <div class="kpi-icon">⏱️</div>
                <div class="kpi-label">MTTR (Rata-rata Perbaikan)</div>
                <div class="kpi-value">{mttr:,.1f}</div>
                <div class="kpi-subtitle">Jam / Kejadian</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 4. CHARTS
    # ----------------------------------------
    
    # INDUSTRIAL THEME PALETTE
    INDUSTRIAL_COLORS = ['#ef4444', '#f59e0b', '#10b981', '#3b82f6', '#8b5cf6', '#ec4899', '#6366f1', '#14b8a6']
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
         with st.container(border=True):
            st.markdown("#### 🕒 Linimasa Gangguan Unit")
            st.markdown("---")
            if 'Start' in df_gangguan.columns and 'End' in df_gangguan.columns and 'Alat' in df_gangguan.columns:
                # Ensure datetime format
                try:
                    df = df_gangguan.copy() # Use local copy
                    df['Start'] = pd.to_datetime(df['Start'], errors='coerce')
                    df['End'] = pd.to_datetime(df['End'], errors='coerce')
                    df_valid = df.dropna(subset=['Start', 'End', 'Alat'])
                    
                    if not df_valid.empty:
                        # OPTIMIZATION: Fixed Top N Units (Default 15)
                        # This balances "Clutter" vs "Detail" based on user preference
                        top_n_units = 15

                        # Filter Top N Units by Downtime for Readability
                        top_units_by_downtime = df_valid.groupby('Alat')['Durasi'].sum().sort_values(ascending=False).head(top_n_units).index
                        df_timeline = df_valid[df_valid['Alat'].isin(top_units_by_downtime)].copy()
                        
                        # Sort by Total Downtime for visual hierarchy
                        # We want the worst unit at the TOP of the Y-axis
                        unit_order = list(top_units_by_downtime) # Already sorted descending
                        
                        # Timeline with Single Professional Color (Red)
                        # "Less is More" - Avoid rainbow confetti
                        fig = px.timeline(df_timeline, x_start="Start", x_end="End", y="Alat", 
                                          # REMOVED color="Gangguan" to remove rainbow effect
                                          title="", 
                                          color_discrete_sequence=['#ef4444'], # Standard Breakdown Red
                                          opacity=0.85,
                                          hover_data=['Durasi', 'Keterangan', 'Penyebab', 'Gangguan'],
                                          category_orders={"Alat": unit_order}) 
                                          
                        fig.update_yaxes(autorange="reversed", title=f"Unit (Top {top_n_units})") 
                        
                        # Clean Layout without Legend
                        fig.update_layout(**get_chart_layout(height=450, show_legend=False)) 
                        fig.update_layout(margin=dict(t=10, b=0, l=0, r=0))
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Add Help Expander
                        with st.expander("ℹ️ Cara Membaca Timeline"):
                            st.write(f"""
                            *   **Sumbu Y (Kiri)**: Daftar Top {top_n_units} Unit yang paling lama rusak.
                            *   **Balok Merah**: Menandakan durasi kerusakan (Downtime). 
                            *   **Detail**: Arahkan kursor mouse ke balok merah untuk melihat **Jenis Masalah**.
                            """)
                        
                        if len(df_valid['Alat'].unique()) > top_n_units:
                            st.caption(f"ℹ️ Menampilkan {top_n_units} dari {len(df_valid['Alat'].unique())} unit dengan downtime tertinggi.")
                    else:
                        st.info("Data waktu Start/End tidak lengkap untuk Timeline.")
                except Exception as e:
                     st.error(f"Error rendering timeline: {e}")
            else:
                st.info("Kolom Start/End tidak ditemukan.")

    with col2:
        with st.container(border=True):
            st.markdown("#### 📊 Pareto Masalah (Top 10)")
            st.markdown("---")
            # Group by 'Gangguan' or 'Kelompok Masalah'
            pareto = df_gangguan.groupby('Gangguan').size().reset_index(name='Count').sort_values('Count', ascending=True).tail(10)
            
            # Simple Red Bar for Issues (Like Source Analysis in Production/Ritase which uses Red/Orange)
            fig = px.bar(pareto, x='Count', y='Gangguan', orientation='h', 
                         text_auto=True,
                         color_discrete_sequence=['#ef4444']) # Distinct Red for breakdown
            
            fig.update_layout(**get_chart_layout(height=500, show_legend=False))
            fig.update_layout(
                xaxis_title="Frekuensi Kejadian",
                yaxis_title="Jenis Masalah",
                # Force largest bars to Top (Total Ascending = Smallest at Bottom, Largest at Top)
                yaxis=dict(categoryorder='total ascending'),
                margin=dict(t=40, b=20, l=0, r=0)
            )
            st.plotly_chart(fig, use_container_width=True)

    # ROW 2: Trend & Bad Actors
    col3, col4 = st.columns([2, 1])
    
    with col3:
        with st.container(border=True):
            st.markdown("#### 📅 **TREN DOWNTIME** | Tren Harian")
            st.markdown("---")
            
            # Group by Date
            daily_dt = df_gangguan.groupby('Tanggal')['Durasi'].sum().reset_index().sort_values('Tanggal')
            
            fig_trend = go.Figure()
            
            # Bar Chart for Volume
            fig_trend.add_trace(go.Bar(
                x=daily_dt['Tanggal'],
                y=daily_dt['Durasi'],
                name='Jam Breakdown',
                marker_color='#ef4444', # Red for 'Bad' metric
                opacity=0.8
            ))
            
            # Line for Trend
            fig_trend.add_trace(go.Scatter(
                x=daily_dt['Tanggal'],
                y=daily_dt['Durasi'],
                mode='lines+markers',
                name='Trend',
                line=dict(color='#f59e0b', width=3)
            ))
            
            fig_trend.update_layout(**get_chart_layout(height=380, show_legend=False))
            fig_trend.update_layout(
                xaxis_title="Tanggal",
                yaxis_title="Total Jam Downtime",
                margin=dict(t=20, b=0, l=0, r=0)
            )
            st.plotly_chart(fig_trend, use_container_width=True)

    with col4:
         with st.container(border=True):
            st.markdown("#### 🚜 **UNIT BERMASALAH (BAD ACTORS)**")
            st.markdown("---")
            
            bad_actors = df_gangguan.groupby('Alat')['Durasi'].sum().reset_index().sort_values('Durasi', ascending=True)
            bad_actors = bad_actors.tail(10) # Top 10 worst
            
            fig_bad = px.bar(bad_actors, y='Alat', x='Durasi', orientation='h',
                             text_auto='.1f',
                             color_discrete_sequence=['#d4a84b']) # Warning color
                             
            fig_bad.update_layout(**get_chart_layout(height=380))
            fig_bad.update_layout(
                margin=dict(t=20, b=0, l=0, r=0),
                xaxis_title="Total Jam Downtime",
                yaxis_title="Unit",
                showlegend=False
            )
            st.plotly_chart(fig_bad, use_container_width=True)

    # 5. DATA TABLE
    # ----------------------------------------
    st.markdown("### 📋 Detail Log Gangguan")
    with st.expander("Lihat Data Tabel", expanded=True):
        # Format for display
        df_display = df_gangguan.copy()
        
        # 1. Format Tanggal (Date only: YYYY-MM-DD)
        if 'Tanggal' in df_display.columns:
             df_display['Tanggal'] = pd.to_datetime(df_display['Tanggal']).dt.strftime('%Y-%m-%d')
        
        # 2. Format Start/End (Time only: HH:MM)
        if 'Start' in df_display.columns:
             df_display['Start'] = pd.to_datetime(df_display['Start']).dt.strftime('%H:%M')
        if 'End' in df_display.columns:
             df_display['End'] = pd.to_datetime(df_display['End']).dt.strftime('%H:%M')
             
        # Format Durasi (2 decimal places)
        if 'Durasi' in df_display.columns:
             df_display['Durasi'] = pd.to_numeric(df_display['Durasi'], errors='coerce')
             df_display['Durasi'] = df_display['Durasi'].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "")
             
        # 3. Drop columns after Link/Lampiran (Clean up)
        if 'Link/Lampiran' in df_display.columns:
             try:
                 cols = list(df_display.columns)
                 idx = cols.index('Link/Lampiran')
                 # Keep columns up to Link/Lampiran inclusive
                 cols_to_keep = cols[:idx+1]
                 df_display = df_display[cols_to_keep]
             except:
                 pass
             
        # Sort latest first if possible, or reverse
        df_display = df_display.iloc[::-1]

        st.dataframe(df_display, use_container_width=True)
        

        
        # Excel Download (Sort Ascending = Oldest Data First)
        # 1. Sort by DATE THEN Start Time
        # The column in df_gangguan is 'Tanggal' (confirmed by file inspection)
        sort_cols = []
        if 'Tanggal' in df_gangguan.columns: sort_cols.append('Tanggal')
        if 'Start' in df_gangguan.columns: sort_cols.append('Start')
        
        df_download = df_gangguan.sort_values(by=sort_cols, ascending=True) if sort_cols else df_gangguan
        
        # 2. Format Date to String (YYYY-MM-DD) to remove 00:00:00 timestamp
        # 2. Format Date to String (YYYY-MM-DD) to remove 00:00:00 timestamp
        if 'Tanggal' in df_download.columns:
            # First ensure it's datetime just in case (though it should be from global filters)
            try:
                df_download['Tanggal'] = pd.to_datetime(df_download['Tanggal']).dt.strftime('%Y-%m-%d')
            except:
                pass # If it fails (already string or strange format), leave it
                
        # 3. Drop unwanted columns (Extra, Bulan_Name)
        # Explicit drop is safer than index truncation
        unwanted_cols = ['Extra', 'Bulan_Name', 'Month', 'Month_Name']
        df_download = df_download.drop(columns=unwanted_cols, errors='ignore')
        
        from utils.helpers import convert_df_to_excel
        excel_data = convert_df_to_excel(df_download)
        
        st.download_button(
            label="📥 Unduh Data (Excel)",
            data=excel_data,
            file_name=f"PTSP_Analisa_Kendala_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )