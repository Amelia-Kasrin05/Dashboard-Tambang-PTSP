# ============================================================
# RITASE - Hauling & Logistics Dashboard
# ============================================================
# Industry-grade mining operations monitoring
# Version 1.0 - Ritase Analysis

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

from utils.data_loader import load_ritase_by_front, apply_global_filters, load_produksi
from utils.helpers import get_chart_layout

def show_ritase():
    """Hauling & Logistics Analysis - Professional Edition"""
    
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
    </style>
    
    <div class="page-header">
        <div class="page-header-icon">🚛</div>
        <div class="page-header-text">
            <h1>Analisis Ritase</h1>
            <p>Monitoring Logistik, Efisiensi Truk & Distribusi Material</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 1. GET PRELOADED DATA (INSTANT)
    # ----------------------------------------
    # Use preloaded data from session_state (no DB query on module switch)
    df_prod_raw = st.session_state.get('df_prod', pd.DataFrame())
    
    # Fallback if not preloaded (first load or after sync)
    if df_prod_raw.empty:
        with st.spinner("Loading Hauling Data..."):
            df_prod_raw = load_produksi()
    
    # Timestamp Info
    last_update = st.session_state.get('last_update_produksi', '-')
    st.caption(f"🕒 Data: **{last_update}** | ⚡ Pre-loaded")
    
    # Feedback for Force Sync
    if df_prod_raw.empty:
        st.warning("⚠️ Data produksi tidak tersedia (Kosong/Belum Sync). Silakan cek koneksi.")
        # Show debug log if empty
        if 'debug_log_produksi' in st.session_state and st.session_state['debug_log_produksi']:
             with st.expander("🛠️ Debug Info (Kenapa Data Kosong?)"):
                 st.json(st.session_state['debug_log_produksi'])
        return

    # Feedback for Force Sync
    if st.session_state.get('force_cloud_reload', False):
         st.toast("✅ Data Updated from Cloud!", icon="☁️")
    
    df_prod = apply_global_filters(df_prod_raw)

    # Explicitly filter invalid Tonnase for CHARTS (Charts must remain clean)
    # But we will keep df_prod_raw or create a display version for table later
    if 'Tonnase' in df_prod.columns:
         df_prod = df_prod[df_prod['Tonnase'] > 0]
        
    if df_prod.empty:
        st.warning("⚠️ Data produksi/ritase tidak tersedia untuk periode ini.")
        return


    # 2. KPI CALCULATIONS (TARGET VS ACTUAL)
    # ----------------------------------------
    from config import DAILY_PRODUCTION_TARGET  # Import Target
    
    total_rit = df_prod['Rit'].sum()
    total_ton = df_prod['Tonnase'].sum()
    total_days = df_prod['Date'].nunique()
    if total_days < 1: total_days = 1
    
    # Target Calculation
    target_period = DAILY_PRODUCTION_TARGET * total_days
    achievement_pct = (total_ton / target_period * 100) if target_period > 0 else 0
    
    # Avg load per trip
    avg_load = total_ton / total_rit if total_rit > 0 else 0
    
    # Determine Status Color
    if achievement_pct >= 100:
        status_color = "#10b981" # Green
        status_icon = "✅"
    elif achievement_pct >= 90:
        status_color = "#3b82f6" # Blue
        status_icon = "🔵"
    elif achievement_pct >= 75:
        status_color = "#f59e0b" # Orange
        status_icon = "⚠️"
    else:
        status_color = "#ef4444" # Red
        status_icon = "🔻"
    
    # 3. KPI CARDS (PROFESSIONAL)
    # ----------------------------------------
    st.markdown(f"""
    <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 2rem;">
        <div class="kpi-card" style="--card-accent: #d4a84b;">
            <div class="kpi-icon">🚛</div>
            <div class="kpi-label">Total Angkutan (Ritase)</div>
            <div class="kpi-value">{total_rit:,.0f}</div>
            <div class="kpi-subtitle">Trip</div>
        </div>
        <div class="kpi-card" style="--card-accent: #3b82f6;">
            <div class="kpi-icon">📦</div>
            <div class="kpi-label">Total Material (Tonase)</div>
            <div class="kpi-value">{total_ton:,.0f}</div>
            <div class="kpi-subtitle">Ton Material</div>
        </div>
        <div class="kpi-card" style="--card-accent: {status_color};">
            <div class="kpi-icon">{status_icon}</div>
            <div class="kpi-label">Realisasi vs Target</div>
            <div class="kpi-value">{achievement_pct:.1f}%</div>
            <div class="kpi-subtitle">Target: {target_period/1000:,.0f}k Ton</div>
        </div>
        <div class="kpi-card" style="--card-accent: #8b5cf6;">
            <div class="kpi-icon">⚖️</div>
            <div class="kpi-label">Rata-rata Muatan (Payload)</div>
            <div class="kpi-value">{avg_load:.1f}</div>
            <div class="kpi-subtitle">Ton / Rit</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 4. DETAILED ANALYSIS (GRID LAYOUT)
    # ----------------------------------------
    
    # ROW 1: Daily Trend with TARGET LINE
    with st.container(border=True):
        st.markdown("##### 📈 **TREN HARIAN ANGKUTAN & MATERIAL**")
        st.markdown("---")
        
        # Aggregate Daily
        rit_daily = df_prod.groupby('Date').agg({'Rit': 'sum', 'Tonnase': 'sum'}).reset_index()
        
        fig_trend = go.Figure()
        
        # 1. Bar: Actual Ritase
        fig_trend.add_trace(go.Bar(
            x=rit_daily['Date'], 
            y=rit_daily['Rit'],
            name='Total Ritase',
            marker_color='#d4a84b', # Gold
            opacity=0.8,
            hovertemplate='%{x|%d %b}: %{y} Trips<extra></extra>'
        ))
        
        # 2. Line: Tonnase (Secondary Axis)
        fig_trend.add_trace(go.Scatter(
            x=rit_daily['Date'],
            y=rit_daily['Tonnase'],
            name='Total Tonase',
            mode='lines+markers',
            yaxis='y2',
            line=dict(color='#3b82f6', width=3), # Blue
            marker=dict(size=6, symbol='circle')
        ))
        
        # 3. Line: Target (Constant)
        fig_trend.add_trace(go.Scatter(
            x=rit_daily['Date'],
            y=[DAILY_PRODUCTION_TARGET] * len(rit_daily),
            name='Target Rencana',
            yaxis='y2',
            mode='lines',
            line=dict(color='#ef4444', width=2, dash='dash') # Red Dashed
        ))
        
        # Standard professional layout first
        fig_trend.update_layout(**get_chart_layout(height=400))
        
        # Specific overrides
        fig_trend.update_layout(
            title="Tren Ritase & Tonase vs Target",
            xaxis=dict(title="Tanggal", tickformat='%d %b'),
            yaxis=dict(title="Total Ritase (Bar)", side="left", showgrid=False),
            yaxis2=dict(title="Tonase (Line)", side="right", overlaying="y", showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
            hovermode="x unified",
            # Legend moved down (-0.5) to avoid overlapping
            legend=dict(orientation="h", y=-0.5, x=0.5, xanchor="center"),
            # Increased bottom margin (120px) to hold the legend
            margin=dict(t=50, b=120, l=20, r=20)
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    # ROW 2: Productivity (Hourly) & Fleet
    col_left, col_right = st.columns([3, 2])
    
    with col_left:
        with st.container(border=True):
            st.markdown("##### ⏱️ **RATA-RATA RITASE PER JAM (HOURLY)**")
            st.markdown("---")
            
            # Helper to extract hour
            def get_hour_safe(t):
               try:
                   s = str(t)
                   if ':' in s: return int(s.split(':')[0])
                   return int(float(s))
               except: return -1
    
            if 'Hour' not in df_prod.columns:
                df_prod['Hour'] = df_prod['Time'].apply(get_hour_safe)
            
            valid_hours = df_prod[(df_prod['Hour'] >= 0) & (df_prod['Hour'] <= 23)]
            
            if not valid_hours.empty:
                # Group by Hour: Sum Ritase & Count Days to get Avg
                hourly_perf = valid_hours.groupby('Hour')['Rit'].sum().reset_index()
                hourly_perf['Avg_Rit_Hour'] = hourly_perf['Rit'] / total_days
                
                # Combo Chart: Avg Productivity
                fig_h = go.Figure()
                
                fig_h.add_trace(go.Bar(
                    x=hourly_perf['Hour'],
                    y=hourly_perf['Avg_Rit_Hour'],
                    name='Rata-rata Rit/Jam',
                    marker_color='#3b82f6', # Professional Blue
                    text=hourly_perf['Avg_Rit_Hour'],
                    texttemplate='%{text:,.1f}',
                    textposition='auto',
                    hovertemplate='Jam %{x}: %{y:,.1f} Rit<extra></extra>'
                ))
                
                fig_h.update_layout(
                    xaxis=dict(tickmode='linear', dtick=1, title="Jam Operasional"),
                    yaxis=dict(title="Rata-rata Produksi (Ritase)"),
                    showlegend=False,
                    margin=dict(t=20, b=0, l=0, r=0)
                )
                fig_h.update_layout(**get_chart_layout(height=350))
                st.plotly_chart(fig_h, use_container_width=True)
            else:
                st.warning("Data jam tidak tersedia.")

    with col_right:
        with st.container(border=True):
            st.markdown("##### 🚛 **KINERJA FORMASI ARMADA (FLEET)**")
            st.markdown("---")
            
            if 'Dump Truck' in df_prod.columns:
                # Group by number of DT units: sum ritase, count frequency, sum DT deployed
                truck_perf = df_prod.groupby('Dump Truck').agg(
                    Rit=('Rit', 'sum'),
                    Frekuensi=('Rit', 'count')
                ).reset_index()
                
                # Avg ritase per session
                truck_perf['Avg_Rit'] = (truck_perf['Rit'] / truck_perf['Frekuensi']).round(1)
                
                # Sort by total ritase (highest on top = professional standard)
                truck_perf = truck_perf.sort_values('Rit', ascending=True)
                if len(truck_perf) > 10: truck_perf = truck_perf.tail(10)
                
                # Label: "X Unit (Nx)" format — shows config + frequency
                truck_perf['Label'] = truck_perf.apply(
                    lambda r: f"{int(float(r['Dump Truck']))} Unit ({int(r['Frekuensi'])}x)" 
                    if str(r['Dump Truck']).replace('.','').isdigit() else str(r['Dump Truck']),
                    axis=1
                )
                
                # Rich hover tooltip
                truck_perf['Hover'] = truck_perf.apply(
                    lambda r: (
                        f"Konfigurasi: {int(float(r['Dump Truck']))} Dump Truck<br>"
                        f"Total Ritase: {int(r['Rit'])}<br>"
                        f"Frekuensi: {int(r['Frekuensi'])}x sesi<br>"
                        f"Rata-rata Rit/Sesi: {r['Avg_Rit']}"
                    ), axis=1
                )
                    
                # Industrial Gold Theme with rich hover
                fig_truck = go.Figure(go.Bar(
                    y=truck_perf['Label'],
                    x=truck_perf['Rit'],
                    orientation='h',
                    text=truck_perf['Rit'].apply(lambda x: f'{x:,.0f}'),
                    textposition='auto',
                    hovertext=truck_perf['Hover'],
                    hoverinfo='text',
                    marker_color='#d4a84b'
                ))
                
                fig_truck.update_layout(**get_chart_layout(height=350))
                fig_truck.update_layout(
                    xaxis_title="Total Ritase",
                    yaxis_title="Jumlah Dump Truck",
                    yaxis=dict(type='category'),
                    margin=dict(t=20, b=0, l=0, r=0)
                )
                st.plotly_chart(fig_truck, use_container_width=True)
            else:
                st.warning("Data Unit tidak tersedia.")

    # ROW 3: Front & Shift (Side by Side)
    c1, c2 = st.columns([1, 1])
    
    with c1:
        with st.container(border=True):
            st.markdown("##### 📍 **DISTRIBUSI LOKASI (FRONT)**")
            st.markdown("---")
            
            if 'Front' in df_prod.columns or 'BLOK' in df_prod.columns:
                group_col = 'Front' if 'Front' in df_prod.columns and df_prod['Front'].nunique() > 1 else 'BLOK'
                rit_front = df_prod.groupby(group_col)['Rit'].sum().reset_index().sort_values('Rit', ascending=True) # Ascending for BarH
                
                # REVISED: Horizontal Bar Chart for Ranking
                fig_src = px.bar(rit_front, x='Rit', y=group_col, orientation='h',
                                 text_auto='.0f',
                                 color_discrete_sequence=['#10b981']) # Emerald Green (Production Source)
                                   
                fig_src.update_layout(**get_chart_layout(height=380))
                # Removed reversed autorange to show highest at Top (because sort is Ascending)
                # Plotly default: Ascending sort -> Smallest at Bottom, Largest at Top
                fig_src.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
                st.plotly_chart(fig_src, use_container_width=True)

    with c2:
        with st.container(border=True):
            st.markdown("##### 🌓 **KONTRIBUSI SHIFT (%)**")
            st.markdown("---")
             
            if 'Shift' in df_prod.columns:
                shift_rit = df_prod.groupby('Shift')['Rit'].sum().reset_index()
                shift_rit['Shift'] = 'Shift ' + shift_rit['Shift'].astype(str).str.replace('Shift ', '')
                
                # Professional Colors
                SHIFT_COLORS = {'Shift 1': '#d4a84b', 'Shift 2': '#3b82f6', 'Shift 3': '#10b981'}
                
                fig_shift = px.pie(shift_rit, values='Rit', names='Shift', 
                                 hole=0.6,
                                 color='Shift',
                                 color_discrete_map=SHIFT_COLORS)
                
                fig_shift.update_traces(textposition='inside', textinfo='percent+label')
                fig_shift.update_layout(**get_chart_layout(height=380))
                fig_shift.update_layout(showlegend=False, margin=dict(t=20, b=20, l=20, r=20),
                                        annotations=[dict(text=f"{total_rit:,}<br>Trips", x=0.5, y=0.5, font_size=12, showarrow=False)])
                
                st.plotly_chart(fig_shift, use_container_width=True)

    # 5. DETAILED TABLE
    # ----------------------------------------
    st.markdown("### 📋 Log Ritase Detail")
    with st.expander("Lihat Data Tabel", expanded=True):
        # Prepare Data for Display: USE RAW FILTERED DATA (Includes 0 Tonnase)
        display_df = apply_global_filters(df_prod_raw).copy()
        
        # Format Date to String (YYYY-MM-DD)
        # Format Date to String (YYYY-MM-DD)
        if 'Date' in display_df.columns:
            display_df['Date'] = display_df['Date'].astype(str)
            
        # 1. SORTING (Must be done BEFORE column selection to use 'id')
        # Display Sort: ID Ascending (Shift 3/Low ID at Top = Reverse Excel/LIFO)
        if 'id' in display_df.columns:
             display_df = display_df.sort_values(by='id', ascending=True)
        else:
             # Fallback
             if 'Date' in display_df.columns and 'Time' in display_df.columns:
                 display_df = display_df.sort_values(by=['Date', 'Time'], ascending=[False, True])
            
        # Select relevant columns for Ritase view
        # Select relevant columns for Ritase view (MATCHING PRODUKSI)
        cols = ['Date', 'Time', 'Shift', 'BLOK', 'Front', 'Commodity', 
                'Excavator', 'Dump Truck', 'Dump Loc', 'Rit', 'Tonnase']
        
        # Filter existing columns
        show_cols = [c for c in cols if c in display_df.columns]
        
        st.dataframe(display_df[show_cols], use_container_width=True)
        
        # Excel Download (Sort Ascending = OLDEST FIRST for chronological order)
        # Using ID Descending (Shift 1 Top / Original Excel)
        
        # Prepare valid download source (Raw filtered)
        df_download = apply_global_filters(df_prod_raw).copy()
        
        if 'id' in df_download.columns:
             df_download = df_download.sort_values(by='id', ascending=False)
        elif 'Date' in df_download.columns and 'Time' in df_download.columns:
             df_download = df_download.sort_values(by=['Date', 'Time'], ascending=True)
        elif 'Date' in df_download.columns:
             df_download = df_download.sort_values(by=['Date'], ascending=True)
             
        # Format Date
        if 'Date' in df_download.columns:
             if pd.api.types.is_datetime64_any_dtype(df_download['Date']):
                 df_download['Date'] = df_download['Date'].dt.strftime('%Y-%m-%d')
             else:
                 df_download['Date'] = df_download['Date'].astype(str)

        # FINAL DISPATCH: Filter only relevant columns (Exclude ID)
        df_download_final = df_download[[c for c in cols if c in df_download.columns]]

        from utils.helpers import convert_df_to_excel
        excel_data = convert_df_to_excel(df_download_final)
        
        st.download_button(
            label="📥 Unduh Data Ritase (Excel)",
            data=excel_data,
            file_name=f"PTSP_Aktivitas_Ritase_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
