# ============================================================
# PRODUKSI - Professional Mining Production Dashboard
# ============================================================
# Industry-grade mining operations monitoring
# Version 3.0 - Global Filters, Heatmap, and Download

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

from config import CHART_SEQUENCE, DAILY_PRODUCTION_TARGET, DAILY_INTERNAL_TARGET
from utils.data_loader import load_produksi, apply_global_filters
from utils.helpers import get_chart_layout


def show_produksi():
    """Professional Mining Production Dashboard"""
    
    # Page Header (Consistent with Ritase)
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
        <div class="page-header-icon">⛏️</div>
        <div class="page-header-text">
            <h1>Produksi Tambang</h1>
            <p>Monitoring Produksi Harian, Kinerja Unit & Distribusi Material</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 1. LOAD & FILTER DATA
    # ----------------------------------------
    with st.spinner("Loading Production Data..."):
        df_prod = load_produksi()
        df_prod = apply_global_filters(df_prod)
        
    if df_prod.empty:
        st.warning("⚠️ Data produksi tidak tersedia atau kosong setelah difilter.")
        return
        
    # Pre-process Data for Analytics
    try:
        df_prod['TimeStr'] = df_prod['Time'].astype(str).str.strip()
        def get_hour(t_str):
            try:
                if ':' in t_str: return int(t_str.split(':')[0])
                return int(float(t_str))
            except: return -1
        df_prod['Hour'] = df_prod['TimeStr'].apply(get_hour)
        df_prod_valid_time = df_prod[(df_prod['Hour'] >= 0) & (df_prod['Hour'] <= 23)]
    except Exception as e:
        st.error(f"Error processing Time column: {e}")
        df_prod['Hour'] = 0
        df_prod_valid_time = df_prod
        
    # 2. KPI CALCULATIONS (TARGET VS ACTUAL)
    # ----------------------------------------
    total_prod = df_prod['Tonnase'].sum()
    total_rit = df_prod['Rit'].sum()
    total_days = df_prod['Date'].nunique()
    if total_days < 1: total_days = 1
    
    # Target Logic
    target_period = DAILY_PRODUCTION_TARGET * total_days
    achievement_pct = (total_prod / target_period * 100) if target_period > 0 else 0
    
    # Productivity Logic
    total_machine_hours = len(df_prod[df_prod['Tonnase'] > 0]) # Approximation
    avg_speed = (total_prod / total_machine_hours) if total_machine_hours > 0 else 0
    
    # Determine Status
    if achievement_pct >= 100:
        status_color, status_icon = "#10b981", "✅" # Green
    elif achievement_pct >= 90:
        status_color, status_icon = "#3b82f6", "🔵" # Blue
    elif achievement_pct >= 75:
        status_color, status_icon = "#f59e0b", "⚠️" # Orange
    else:
        status_color, status_icon = "#ef4444", "🔻" # Red
    
    # 3. KPI CARDS
    # ----------------------------------------
    # 3. KPI CARDS
    # ----------------------------------------
    st.markdown(f"""
    <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 2rem;">
        <div class="kpi-card" style="--card-accent: #3b82f6;">
            <div class="kpi-icon">⛏️</div>
            <div class="kpi-label">Total Produksi</div>
            <div class="kpi-value">{total_prod:,.0f}</div>
            <div class="kpi-subtitle">Ton Material</div>
        </div>
        <div class="kpi-card" style="--card-accent: {status_color};">
            <div class="kpi-icon">{status_icon}</div>
            <div class="kpi-label">Pencapaian</div>
            <div class="kpi-value">{achievement_pct:.1f}%</div>
            <div class="kpi-subtitle">Target: {target_period/1000:,.0f}k Ton</div>
        </div>
        <div class="kpi-card" style="--card-accent: #8b5cf6;">
            <div class="kpi-icon">⚡</div>
            <div class="kpi-label">Produktivitas</div>
            <div class="kpi-value">{avg_speed:,.1f}</div>
            <div class="kpi-subtitle">Ton/Unit/Jam</div>
        </div>
        <div class="kpi-card" style="--card-accent: #d4a84b;">
            <div class="kpi-icon">🚛</div>
            <div class="kpi-label">Total Ritase</div>
            <div class="kpi-value">{total_rit:,.0f}</div>
            <div class="kpi-subtitle">Trip</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 4. PRIMARY CHARTS (Top Level)
    # ----------------------------------------
    
    # ROW 1: Daily Trend (PROFESSIONAL THEME)
    with st.container(border=True):
        st.markdown("##### 📅 **PERFORMA HARIAN** | Realisasi Harian vs Target")
        st.markdown("---")
        
        if not df_prod.empty:
            daily_agg = df_prod.groupby('Date')['Tonnase'].sum().reset_index().sort_values('Date')
            
            # Color Logic: Red (Under) -> Blue (Target) -> Green (Internal)
            colors = []
            for val in daily_agg['Tonnase']:
                if val >= DAILY_INTERNAL_TARGET:
                    colors.append('#10b981') # Green (Internal Target)
                elif val >= DAILY_PRODUCTION_TARGET:
                    colors.append('#3b82f6') # Blue (Main Target)
                else:
                    colors.append('#ef4444') # Red (Under Target)
            
            fig = go.Figure()
            
            # 1. Bar: Actual Production (Conditional Color)
            fig.add_trace(go.Bar(
                x=daily_agg['Date'], 
                y=daily_agg['Tonnase'],
                name='Realisasi',
                marker_color=colors, # Conditional Colors
                opacity=0.9,
                text=daily_agg['Tonnase'],
                texttemplate='%{text:,.0f}',
                textposition='auto',
                hovertemplate='<b>%{x|%d %b}</b>: %{y:,.0f} Ton<extra></extra>'
            ))
            
            # 2. Line: Main Target (Red Solid)
            fig.add_trace(go.Scatter(
                x=daily_agg['Date'],
                y=[DAILY_PRODUCTION_TARGET] * len(daily_agg),
                mode='lines',
                name=f'Target ({DAILY_PRODUCTION_TARGET:,.0f})',
                line=dict(color='#ef4444', width=3)
            ))

            # 3. Line: Internal Target (Yellow Dashed)
            fig.add_trace(go.Scatter(
                x=daily_agg['Date'],
                y=[DAILY_INTERNAL_TARGET] * len(daily_agg),
                mode='lines',
                name=f'Internal ({DAILY_INTERNAL_TARGET:,.0f})',
                line=dict(color='#f59e0b', width=2, dash='dash')
            ))
            
            # Find Best Day
            best_day = daily_agg.loc[daily_agg['Tonnase'].idxmax()]
            fig.add_annotation(
                x=best_day['Date'], y=best_day['Tonnase'],
                text=f"🏆 Max: {best_day['Tonnase']:,.0f}",
                showarrow=True, arrowhead=2, ax=0, ay=-40,
                font=dict(color="#10b981", size=12)
            )
            
            # Apply default layout first
            fig.update_layout(**get_chart_layout(height=450))

            # Apply specific customizations
            fig.update_layout(
                title="Pencapaian Produksi Harian",
                xaxis=dict(title="Tanggal", tickformat='%d %b'),
                yaxis=dict(title="Tonase (Ton)", showgrid=True, gridcolor='rgba(255, 255, 255, 0.1)'),
                legend=dict(orientation="h", y=-0.3, x=0.5, xanchor="center", bgcolor='rgba(0,0,0,0)'),
                hovermode="x unified",
                margin=dict(l=20, r=20, t=50, b=80)
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Legend Helper
            st.markdown(f"""
            <div style="display:flex; gap:15px; font-size:0.8rem; color:#cbd5e1; justify-content:center; margin-top:-10px;">
                <span>🔴 Di Bawah Target (< {DAILY_PRODUCTION_TARGET/1000}k)</span>
                <span>🔵 Mencapai Target (≥ {DAILY_PRODUCTION_TARGET/1000}k)</span>
                <span>🟢 Target Internal (≥ {DAILY_INTERNAL_TARGET/1000}k)</span>
            </div>
            """, unsafe_allow_html=True)
            
    # ROW 2: Hourly Rhythm & Shift (Split)
    c1, c2 = st.columns([2, 1])
    
    with c1:
        with st.container(border=True):
             st.markdown("##### ⏱️ **IRAMA PER JAM (HOURLY RHYTHM)**")
             st.markdown("---")

             if not df_prod_valid_time.empty:
                 hourly_sum = df_prod_valid_time.groupby('Hour')['Tonnase'].sum().reset_index()
                 hourly_sum['Avg'] = hourly_sum['Tonnase'] / total_days
                 
                 # INDUSTRIAL BLUE/GOLD COMBO
                 fig = px.bar(hourly_sum, x='Hour', y='Avg', 
                              labels={'Hour': 'Jam', 'Avg': 'Ton/Jam'},
                              text_auto='.0f',
                              color='Avg',
                              color_continuous_scale='cividis') # Professional Gradient
                 
                 fig.update_layout(xaxis=dict(tickmode='linear', dtick=1))
                 fig.update_layout(**get_chart_layout(height=350))
                 fig.update_layout(showlegend=False, margin=dict(t=20, b=0, l=0, r=0), coloraxis_showscale=False)
                 st.plotly_chart(fig, use_container_width=True)
             else:
                 st.warning("Data waktu tidak valid.")
    
    with c2:
        with st.container(border=True):
            st.markdown("##### 🌓 **SHIFT**")
            st.markdown("---")
            
            if 'Shift' in df_prod.columns:
                shift_prod = df_prod.groupby('Shift')['Tonnase'].sum().reset_index()
                shift_prod['Shift'] = 'Shift ' + shift_prod['Shift'].astype(str).str.replace('Shift ', '')
                
                # Standard Shift Colors
                SHIFT_COLORS = {'Shift 1': '#d4a84b', 'Shift 2': '#3b82f6', 'Shift 3': '#10b981'}
                
                fig_shift = px.pie(shift_prod, values='Tonnase', names='Shift', 
                                 hole=0.6,
                                 color='Shift',
                                 color_discrete_map=SHIFT_COLORS)
                fig_shift.update_traces(textposition='inside', textinfo='percent+label')
                fig_shift.update_layout(**get_chart_layout(height=350))
                fig_shift.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
                
                # Center Annotation
                fig_shift.add_annotation(text=f"Total<br>{total_prod/1000:,.0f}k", x=0.5, y=0.5, font_size=20, showarrow=False)
                
                st.plotly_chart(fig_shift, use_container_width=True)
            else:
                 st.warning("Data Shift tidak tersedia.")
            
    # ROW 3: Unit Performance & Source Analysis
    col_left, col_right = st.columns(2)
    with col_left:
        with st.container(border=True):
            st.markdown("##### 🚜 **PERFORMA UNIT** | Top Excavator")
            st.markdown("---")
            
            if not df_prod.empty:
                unit_perf = df_prod.groupby('Excavator')['Tonnase'].sum().reset_index().sort_values('Tonnase', ascending=True)
                
                # Solid Blue Bars
                fig = px.bar(unit_perf, y='Excavator', x='Tonnase', orientation='h', 
                             text_auto='.2s',
                             color_discrete_sequence=['#3b82f6']) 
                
                fig.update_layout(**get_chart_layout(height=380))
                fig.update_layout(showlegend=False, margin=dict(t=20, b=0, l=0, r=0))
                st.plotly_chart(fig, use_container_width=True)
    
    with col_right:
        with st.container(border=True):
            st.markdown("##### 📍 **SUMBER (FRONT)** | Distribusi Front")
            st.markdown("---")
            
            if 'Front' in df_prod.columns and not df_prod.empty:
                front_prod = df_prod.groupby('Front')['Tonnase'].sum().reset_index().sort_values('Tonnase', ascending=False)
                
                if len(front_prod) > 10:
                    front_prod = front_prod.head(10)
                
                # REVISED: Horizontal Bar Chart for clearer ranking (Professional Request)
                fig_front = px.bar(front_prod, x='Tonnase', y='Front', orientation='h',
                                   text_auto='.2s',
                                   color_discrete_sequence=['#3b82f6']) # Professional Blue
                
                fig_front.update_layout(**get_chart_layout(height=380))
                fig_front.update_layout(yaxis=dict(autorange="reversed", automargin=True), showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
                st.plotly_chart(fig_front, use_container_width=True)
    
    # ROW 4: Disposal Analysis
    with st.container(border=True):
        st.markdown("##### 🚛 **TUJUAN (DISPOSAL)** | Distribusi Disposal")
        st.markdown("---")
        
        if 'Dump Loc' in df_prod.columns and not df_prod.empty:
            dump_prod = df_prod.groupby('Dump Loc')['Tonnase'].sum().reset_index().sort_values('Tonnase', ascending=True)
            
            # Solid Green Bars
            fig_dump = px.bar(dump_prod, x='Tonnase', y='Dump Loc', orientation='h',
                              text_auto='.2s',
                              color_discrete_sequence=['#10b981'])                          
            fig_dump.update_layout(**get_chart_layout(height=380))
            fig_dump.update_layout(yaxis=dict(automargin=True), showlegend=False, margin=dict(t=20, b=0, l=0, r=0))
            st.plotly_chart(fig_dump, use_container_width=True)

    # 5. DETAIL DATA & DOWNLOAD
    # ----------------------------------------
    st.markdown("### 📋 Detail Data Produksi")
    with st.expander("Lihat Tabel Lengkap", expanded=False):
        df_display = df_prod.copy()
        df_display = df_display.iloc[::-1]
        
        if 'Date' in df_display.columns:
             df_display['Date'] = df_display['Date'].dt.strftime('%Y-%m-%d')
             
        display_cols = ['Date', 'Time', 'Shift', 'BLOK', 'Front', 'Commudity', 
                        'Excavator', 'Dump Truck', 'Dump Loc', 'Rit', 'Tonnase']
        df_display = df_display[[c for c in display_cols if c in df_display.columns]]
             
        st.dataframe(df_display, use_container_width=True)
        
        # Excel Download (Sort Ascending = Oldest Data First)
        # MATCHING TABLE COLUMNS EXACTLY
        # 1. Sort raw data first
        df_sorted = df_prod.sort_values(by=['Date', 'TimeStr'], ascending=True) if 'TimeStr' in df_prod.columns else df_prod.sort_values(by='Date', ascending=True)
        
        # 2. Format Date to match table string format
        if 'Date' in df_sorted.columns:
             df_sorted['Date'] = df_sorted['Date'].dt.strftime('%Y-%m-%d')
             
        # 3. Select ONLY the columns shown in table
        df_download = df_sorted[[c for c in display_cols if c in df_sorted.columns]]
        
        from utils.helpers import convert_df_to_excel
        excel_data = convert_df_to_excel(df_download)
        
        st.download_button(
            label="📥 Unduh Data (Excel)",
            data=excel_data,
            file_name=f"PTSP_Kinerja_Produksi_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )