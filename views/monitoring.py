
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

from config import MINING_COLORS, CHART_SEQUENCE
from utils.data_loader import (
    load_bbm_raw, load_ritase_raw, load_stockpile_hopper, 
    load_tonase_raw, load_analisa_produksi_all
)
from utils.helpers import get_chart_layout

def show_monitoring():
    """
    Professional Monitoring Dashboard (Command Center)
    Pillars:
    1. Command Center (Summary)
    2. Logistics & Fuel (BBM + Ritase)
    3. Inventory (Stockpile)
    4. Real-time Ops (Hourly Tonase)
    """
    
    # Header Style Override (Consistency)
    st.markdown("""
    <style>
    /* FORCE OVERRIDE FOR CONTAINERS */
    div[data-testid="stVerticalBlockBorderWrapper"] {
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
        <div class="page-header-icon">📡</div>
        <div class="page-header-text">
            <h1>Pusat Monitoring</h1>
            <p>Kontrol Operasional & Logistik Terpadu • """ + datetime.now().strftime("%d %b %Y, %H:%M") + """</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Ringkasan Utama", 
        "⛽ Logistik & BBM", 
        "⛰️ Stockpile & Hopper", 
        "⏱️ Produksi Per Jam"
    ])
    
    # =========================================================================
    # TAB 1: RINGKASAN UTAMA (S-CURVE & KPI)
    # =========================================================================
    # =========================================================================
    # TAB 1: RINGKASAN UTAMA (S-CURVE & KPI)
    # =========================================================================
    with tab1:
        st.markdown("### 📅 Analisis Rencana vs Aktual (Bulanan)")
        df_analisa = load_analisa_produksi_all()
        
        if not df_analisa.empty:
            # 1. Filter Year
            if 'Tahun' in df_analisa.columns:
                years = sorted(df_analisa['Tahun'].unique(), reverse=True)
                selected_year = st.selectbox("Pilih Tahun", years, index=0) # Default to latest (2026)
                df_analisa = df_analisa[df_analisa['Tahun'] == selected_year]
            
            # 2. Filter Month
            months = df_analisa['Bulan'].unique()
            if len(months) > 0:
                selected_month = st.selectbox("Pilih Bulan", months, index=len(months)-1)
                df_m = df_analisa[df_analisa['Bulan'] == selected_month].copy()
            else:
                df_m = pd.DataFrame()
            
            if not df_m.empty:
                # Calculate Cumulative
                df_m['Plan_Cum'] = df_m['Plan'].cumsum()
                df_m['Aktual_Cum'] = df_m['Aktual'].cumsum()
                
                # Metrics
                total_plan = df_m['Plan'].sum()
                total_akt = df_m['Aktual'].sum()
                ach = (total_akt / total_plan * 100) if total_plan > 0 else 0
                
                # Determine Color
                if ach >= 100: status_c, status_i = "#10b981", "✅"
                elif ach >= 90: status_c, status_i = "#3b82f6", "🔵"
                else: status_c, status_i = "#ef4444", "🔻"

                # KPI Cards (HTML Style for consistency)
                st.markdown(f"""
                <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 2rem;">
                    <div class="kpi-card" style="--card-accent: #ef4444;">
                        <div class="kpi-icon">📋</div>
                        <div class="kpi-label">Total Rencana</div>
                        <div class="kpi-value">{total_plan:,.0f}</div>
                        <div class="kpi-subtitle">Target Bulanan</div>
                    </div>
                    <div class="kpi-card" style="--card-accent: #d4a84b;">
                        <div class="kpi-icon">⛏️</div>
                        <div class="kpi-label">Total Aktual</div>
                        <div class="kpi-value">{total_akt:,.0f}</div>
                        <div class="kpi-subtitle">Realisasi Bulanan</div>
                    </div>
                    <div class="kpi-card" style="--card-accent: {status_c};">
                        <div class="kpi-icon">{status_i}</div>
                        <div class="kpi-label">Pencapaian</div>
                        <div class="kpi-value">{ach:.1f}%</div>
                        <div class="kpi-subtitle">Rencana vs Aktual</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # S-Curve Chart (Professional)
                with st.container(border=True):
                    fig = go.Figure()
                    
                    # 1. Bar: Daily Actual (Gold)
                    fig.add_trace(go.Bar(
                        x=df_m['Tanggal'], y=df_m['Aktual'], 
                        name='Harian',
                        marker_color='#d4a84b', opacity=0.6,
                        yaxis='y2'
                    ))
                    
                    # 2. Line: Plan Cum (Red Dashed)
                    fig.add_trace(go.Scatter(
                        x=df_m['Tanggal'], y=df_m['Plan_Cum'], 
                        name='Rencana (Kumulatif)',
                        mode='lines',
                        line=dict(color='#ef4444', width=2, dash='dash')
                    ))
                    
                    # 3. Line: Actual Cum (Blue Solid)
                    fig.add_trace(go.Scatter(
                        x=df_m['Tanggal'], y=df_m['Aktual_Cum'], 
                        name='Realisasi (Kumulatif)',
                        mode='lines+markers',
                        line=dict(color='#3b82f6', width=3),
                        marker=dict(size=6)
                    ))
                    
                    fig.update_layout(
                        **get_chart_layout(height=450),
                        title=f"Kurva-S Produksi: {selected_month}",
                        xaxis=dict(title="Tanggal"),
                        yaxis=dict(title="Kumulatif (ton)", side="left", showgrid=True),
                        yaxis2=dict(title="Harian (ton)", side="right", overlaying="y", showgrid=False),
                        legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"),
                        hovermode="x unified"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with st.expander("Lihat Data Detail"):
                    st.dataframe(df_m, use_container_width=True)
            else:
                st.info("Data bulan ini kosong.")
        else:
            st.warning("Data Analisa Produksi belum tersedia.")

    # =========================================================================
    # TAB 2: LOGISTIK & BBM
    # =========================================================================
    with tab2:
        col_bbm, col_rit = st.columns([1, 1])
        
        # --- BBM SECTION ---
        with col_bbm:
            with st.container(border=True):
                st.markdown("##### ⛽ **KONSUMSI BAHAN BAKAR (FUEL)** | BBM per Unit")
                st.markdown("---")
                from utils.data_loader import load_bbm_enhanced
                df_bbm = load_bbm_enhanced()
                
                if not df_bbm.empty and 'Kategori' in df_bbm.columns:
                    # Chart 1: Consumption by Category (Pie)
                    summ = df_bbm.groupby('Kategori')['Liters'].sum().reset_index()
                    
                    fig = px.pie(summ, values='Liters', names='Kategori', hole=0.5,
                                 color_discrete_sequence=px.colors.sequential.Bluered_r)
                    fig.update_layout(**get_chart_layout(height=300), title="Proporsi BBM per Kategori")
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                    fig.update_layout(showlegend=False, margin=dict(t=30, b=0, l=0, r=0))
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Chart 2: Top Units (Bar)
                    top_units = df_bbm.groupby('Unit')['Liters'].sum().nlargest(5).reset_index()
                    
                    fig2 = px.bar(top_units, x='Liters', y='Unit', orientation='h',
                                  text_auto='.0f',
                                  color='Liters', color_continuous_scale='Reds')
                                  
                    fig2.update_layout(**get_chart_layout(height=350), title="Top 5 Unit Boros BBM")
                    fig2.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig2, use_container_width=True)
    
                else:
                    st.info("Data BBM tidak tersedia atau belum diformat dengan benar.")

        # --- RITASE SECTION ---
        with col_rit:
            with st.container(border=True):
                st.markdown("##### 🚛 **PERFORMA HAULING** | Top Front")
                st.markdown("---")
                from utils.data_loader import load_ritase_by_front
                df_rit = load_ritase_by_front()
                
                if not df_rit.empty:
                    top_fronts = df_rit.head(10)
                    
                    # Industrial Colors
                    fig = px.bar(top_fronts, x='Total_Ritase', y='Front', orientation='h',
                                 text='Total_Ritase',
                                 color='Total_Ritase', color_continuous_scale='Oranges')
                                 
                    fig.update_traces(texttemplate='%{text:.0f}', textposition='outside')
                    fig.update_layout(**get_chart_layout(height=650))
                    fig.update_layout(
                        title="Top Produksi per Front (Ritase)",
                        yaxis={'categoryorder':'total ascending', 'title': None},
                        xaxis={'title': 'Total Ritase'},
                        coloraxis_showscale=False
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Data Ritase tidak tersedia.")

    # =========================================================================
    # TAB 3: STOCKPILE & HOPPER
    # =========================================================================
    with tab3:
        st.markdown("### ⛰️ Level Stok & Hopper")
        with st.container(border=True):
            df_stock = load_stockpile_hopper()
            
            if not df_stock.empty:
                # Time Series of Stockpile
                numeric_cols = df_stock.select_dtypes(include=['float64', 'int64']).columns.tolist()
                if 'Tanggal' in numeric_cols: numeric_cols.remove('Tanggal')
                
                if numeric_cols:
                    selected_items = st.multiselect("Pilih Item:", numeric_cols, default=numeric_cols[:3])
                    
                    if selected_items:
                        # Professional Line Chart
                        fig = go.Figure()
                        colors = ['#d4a84b', '#3b82f6', '#10b981', '#ef4444']
                        
                        for i, col in enumerate(selected_items):
                            c = colors[i % len(colors)]
                            fig.add_trace(go.Scatter(
                                x=df_stock['Tanggal'], y=df_stock[col],
                                name=col, mode='lines+markers',
                                line=dict(width=3, color=c)
                            ))
                            
                        fig.update_layout(**get_chart_layout(height=400), title="Tren Stok Material")
                        fig.update_layout(hovermode="x unified")
                        st.plotly_chart(fig, use_container_width=True)
                
                # Latest Status
                latest = df_stock.iloc[-1]
                st.markdown(f"**Status Terakhir: {latest['Tanggal']}**")
                
                # KPI Grid for Stock
                cols = st.columns(4)
                for i, col in enumerate(numeric_cols[:4]):
                    val = latest[col]
                    with cols[i]:
                        st.markdown(f"""
                        <div class="kpi-card" style="padding: 1rem; text-align:center; --card-accent: #3b82f6;">
                            <div class="kpi-label">{col}</div>
                            <div class="kpi-value" style="font-size: 1.5rem;">{val:,.0f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                with st.expander("Lihat Data Lengkap"):
                    st.dataframe(df_stock, use_container_width=True)
            else:
                st.warning("Data Stockpile tidak ditemukan / Format belum sesuai.")

    # =========================================================================
    # TAB 4: HOURLY TRACKING
    # =========================================================================
    with tab4:
        st.markdown("### ⏱️ Peta Panas (Heatmap) Produksi Per Jam")
        with st.container(border=True):
            from utils.data_loader import load_tonase_hourly
            df_hourly = load_tonase_hourly()
            
            if not df_hourly.empty:
                df_hourly['Tanggal'] = pd.to_datetime(df_hourly['Tanggal'])
                min_date = df_hourly['Tanggal'].min().date()
                max_date = df_hourly['Tanggal'].max().date()
                
                default_start = pd.Timestamp("2026-01-01").date()
                if default_start < min_date: default_start = min_date
                if default_start > max_date: default_start = max_date 

                c1, c2, c3 = st.columns([1, 1, 2])
                d1 = c1.date_input("Dari", default_start, min_value=min_date, max_value=max_date)
                d2 = c2.date_input("Sampai", max_date, min_value=min_date, max_value=max_date)
                
                mask = (df_hourly['Tanggal'].dt.date >= d1) & (df_hourly['Tanggal'].dt.date <= d2)
                df_filtered = df_hourly[mask].copy()
                
                if not df_filtered.empty:
                    # Clean Hour
                    try:
                        df_filtered['Jam_Num'] = df_filtered['Jam'].astype(str).apply(
                            lambda x: int(x.split('-')[0]) if '-' in x else (int(x) if x.isdigit() else 99)
                        )
                        df_filtered = df_filtered.sort_values('Jam_Num')
                    except: pass
                    
                    pivot_data = df_filtered.pivot_table(index='Jam', columns='Tanggal', values='Tonase', aggfunc='sum')
                    
                    # Professional Heatmap (Red-Yellow-Green -> Viridis or similar)
                    fig = go.Figure(data=go.Heatmap(
                        z=pivot_data.values,
                        x=pivot_data.columns,
                        y=pivot_data.index,
                        colorscale='Viridis', # Professional Mining Scale
                        colorbar=dict(title='Tonase')
                    ))
                    
                    fig.update_layout(
                        **get_chart_layout(height=600),
                        title=f"Intensitas Produksi ({d1} s/d {d2})",
                        xaxis_title="Tanggal",
                        yaxis_title="Jam Operasional"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Daily Total Overlay
                    daily_total = df_filtered.groupby('Tanggal')['Tonase'].sum().reset_index()
                    fig2 = px.bar(daily_total, x='Tanggal', y='Tonase', text='Tonase',
                                  color='Tonase', color_continuous_scale='Cividis')
                    fig2.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
                    fig2.update_layout(**get_chart_layout(height=300), title="Total Produksi Harian")
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.info("Tidak ada data pada rentang tanggal ini.")
            else:
                st.info("Data Produksi Per Jam tidak tersedia.")