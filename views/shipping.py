# ============================================================
# SHIPPING - Sales & Shipping Dashboard
# ============================================================
# Industry-grade mining operations monitoring
# Version 3.0 - Executive Standard (No S-Curve)

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

from utils.data_loader import load_shipping_data, apply_global_filters
from utils.helpers import get_chart_layout

def show_shipping():
    """Sales & Shipping Analysis - Executive View"""
    
    # 1. LOAD DATA
    with st.spinner("Memuat Data Pengiriman..."):
        df_shipping = load_shipping_data()
        
        # Timestamp Info
        last_update = st.session_state.get('last_update_shipping', '-')
        st.caption(f"🕒 Data Downloaded At: **{last_update}** (Cloud Only Mode)")

        # Feedback for Force Sync
        if st.session_state.get('force_cloud_reload', False):
             if not df_shipping.empty:
                 st.toast("✅ Cloud Data Linked!", icon="☁️")
             else:
                 st.error("❌ Cloud Sync Failed - Data Empty/Connection Error")
        
        df = apply_global_filters(df_shipping, date_col='Date')
        
    if df.empty:
        st.warning("⚠️ Data Pengiriman tidak tersedia.")
        return

    # 2. DATA PROCESSING (Material Focus)
    # Ensure columns exist (loaded by updated loader)
    cols_check = ['AP_LS', 'AP_LS_MK3', 'AP_SS']
    for c in cols_check:
        if c not in df.columns: df[c] = 0
        
    # Metrics
    total_qty = df['Quantity'].sum() if 'Quantity' in df.columns else 0
    # Hitung Transaksi: Hanya hitung baris yang Volume-nya > 0 (Shift Aktif)
    # Jangan hitung baris tanggal yang isinya masih nol (pre-filled dates)
    total_rit = len(df[df['Quantity'] > 0])
    
    # Calculate Material Totals
    total_ls = df['AP_LS'].sum()
    total_mk3 = df['AP_LS_MK3'].sum()
    total_ss = df['AP_SS'].sum()
    
    # Determine Dominant Material
    materials = {'Limestone': total_ls, 'LS MK3': total_mk3, 'Silica Stone': total_ss}
    dominant_mat = max(materials, key=materials.get)
    dominant_val = materials[dominant_mat]
    
    avg_daily = total_qty / df['Date'].nunique() if df['Date'].nunique() > 0 else 0

    # 3. EXECUTIVE KPI CARDS
    st.markdown(f"""
    <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 2rem;">
        <div class="kpi-card" style="--card-accent: #3b82f6;">
            <div class="kpi-icon">🚢</div>
            <div class="kpi-label">Total Pengiriman</div>
            <div class="kpi-value">{total_qty:,.0f}</div>
            <div class="kpi-subtitle">Ton Material</div>
        </div>
        <div class="kpi-card" style="--card-accent: #10b981;">
            <div class="kpi-icon">📋</div>
            <div class="kpi-label">Total Transaksi</div>
            <div class="kpi-value">{total_rit:,}</div>
            <div class="kpi-subtitle">Jumlah Pengiriman</div>
        </div>
        <div class="kpi-card" style="--card-accent: #f59e0b;">
            <div class="kpi-icon">📅</div>
            <div class="kpi-label">Rata-rata Harian</div>
            <div class="kpi-value">{avg_daily:,.0f}</div>
            <div class="kpi-subtitle">Ton / Hari</div>
        </div>
        <div class="kpi-card" style="--card-accent: #8b5cf6;">
            <div class="kpi-icon">💎</div>
            <div class="kpi-label">Material Terbanyak</div>
            <div class="kpi-value" style="font-size: 1.5rem;">{dominant_mat}</div>
            <div class="kpi-subtitle">{dominant_val:,.0f} Ton</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 4. CHARTS SECTION
    c1, c2 = st.columns([1.5, 2.5])

    # Chart 1: Material Composition (Donut)
    with c1:
        with st.container(border=True):
            st.markdown("##### 📦 **KOMPOSISI MATERIAL** | Jenis Produk")
            st.markdown("---")
            
            mat_df = pd.DataFrame([
                {'Material': 'Limestone (LS)', 'Volume': total_ls},
                {'Material': 'LS MK3', 'Volume': total_mk3},
                {'Material': 'Silica Stone (SS)', 'Volume': total_ss}
            ])
            mat_df = mat_df[mat_df['Volume'] > 0] # Hide zero components
            
            fig_mat = px.pie(mat_df, values='Volume', names='Material', hole=0.6,
                              color='Material',
                              color_discrete_map={
                                  'Limestone (LS)': '#3b82f6', # Blue
                                  'LS MK3': '#60a5fa',        # Light Blue
                                  'Silica Stone (SS)': '#10b981' # Green
                              })
            
            # Fix Layout Merge
            layout_mat = get_chart_layout(height=350)
            layout_mat.update(dict(
                title="Proporsi Material",
                showlegend=True,
                legend=dict(orientation="h", y=-0.1)
            ))
            fig_mat.update_layout(**layout_mat)
            fig_mat.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_mat, use_container_width=True)

    # Chart 2: Shift Performance (Bar)
    with c2:
        with st.container(border=True):
            st.markdown("##### ⏱️ **PERFORMA SHIFT** | Produktivitas Kerja")
            st.markdown("---")
            
            shift_df = df.groupby('Shift')['Quantity'].sum().reset_index()
            # Sort by Quantity Ascending for Plotly (Largest at Top)
            shift_df = shift_df.sort_values('Quantity', ascending=True)
            # Ensure Shift is categorical/string
            shift_df['Shift'] = shift_df['Shift'].astype(str)
            
            fig_shift = px.bar(shift_df, x='Quantity', y='Shift', orientation='h',
                               text='Quantity',
                               color='Shift', color_discrete_sequence=['#f59e0b', '#8b5cf6', '#ec4899'])
            
            fig_shift.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
            
            # Fix Layout Merge
            layout_shift = get_chart_layout(height=350)
            layout_shift.update(dict(
                title="Total Pengiriman per Shift",
                xaxis=dict(showgrid=True, title="Volume (Ton)"),
                yaxis=dict(title="Shift"),
                showlegend=False
            ))
            fig_shift.update_layout(**layout_shift)
            # FORCE sort order: Largest at TOP
            fig_shift.update_yaxes(categoryorder='total ascending')
            st.plotly_chart(fig_shift, use_container_width=True)
    
    # Chart 3: Daily Trend (Stacked)
    with st.container(border=True):
        st.markdown("##### 📈 **TREN HARIAN** | Fluktuasi per Material")
        st.markdown("---")
        
        # Melt for Stacked Bar
        daily_melt = df.melt(id_vars=['Date'], value_vars=['AP_LS', 'AP_LS_MK3', 'AP_SS'], 
                             var_name='Material', value_name='Volume')
        daily_melt = daily_melt.groupby(['Date', 'Material'])['Volume'].sum().reset_index()
        
        # Rename for nice legend
        material_map = {'AP_LS': 'Limestone', 'AP_LS_MK3': 'LS MK3', 'AP_SS': 'Silica Stone'}
        daily_melt['Material'] = daily_melt['Material'].map(material_map)
        
        fig_trend = px.bar(daily_melt, x='Date', y='Volume', color='Material',
                           color_discrete_map={
                                  'Limestone': '#3b82f6', 
                                  'LS MK3': '#60a5fa',        
                                  'Silica Stone': '#10b981'
                           })
        
        # Add Moving Average Line (Total)
        total_series = df.groupby('Date')['Quantity'].sum().reset_index()
        total_series['MA7'] = total_series['Quantity'].rolling(window=7).mean()
        
        fig_trend.add_trace(go.Scatter(
            x=total_series['Date'], y=total_series['MA7'],
            name='Rata-rata 7 Hari',
            line=dict(color='#d4a84b', width=3)
        ))

        # Update Layout (Merge dicts to avoid duplicate 'legend' error)
        layout = get_chart_layout(height=400)
        layout.update(dict(
            title="Tren Harian breakdown Material",
            xaxis_title="Tanggal",
            yaxis_title="Volume (Ton)",
            hovermode="x unified",
            legend=dict(orientation="h", y=1.1)
        ))
        fig_trend.update_layout(**layout)
        st.plotly_chart(fig_trend, use_container_width=True)
            
    # 5. DATA TABLE
    with st.expander("📄 Lihat Detail Data Textual"):
        st.dataframe(
            df, 
            use_container_width=True,
            column_config={
                "Date": st.column_config.DateColumn("Date", format="YYYY-MM-DD")
            }
        )
        
        # Excel Download (Sort Ascending = Oldest First)
        df_download = df.sort_values(by='Date', ascending=True)
        
        # Format Date to String (Remove 00:00:00)
        if 'Date' in df_download.columns:
             try:
                df_download['Date'] = pd.to_datetime(df_download['Date']).dt.strftime('%Y-%m-%d')
             except:
                pass
        
        from utils.helpers import convert_df_to_excel
        excel_data = convert_df_to_excel(df_download)
        
        st.download_button(
             label="📥 Unduh Data (Excel)",
             data=excel_data,
             file_name=f"PTSP_Data_Pengiriman_{datetime.now().strftime('%Y%m%d')}.xlsx",
             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
             type="primary"
        )

