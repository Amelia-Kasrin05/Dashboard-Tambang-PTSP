# ============================================================
# MONITORING - Operational Intelligence Dashboard V4.0
# ============================================================
# SIMPLIFIED VERSION - Direct Excel reading with defensive coding

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import io
import os

# Import colors and helpers
try:
    from config import MINING_COLORS
    from utils.helpers import get_chart_layout
except ImportError:
    MINING_COLORS = {'gold': '#d4a84b', 'blue': '#3b82f6', 'green': '#10b981', 'red': '#ef4444'}
    def get_chart_layout(height=350):
        return {'height': height, 'template': 'plotly_dark', 'paper_bgcolor': 'rgba(0,0,0,0)', 'plot_bgcolor': 'rgba(0,0,0,0)'}

# File path
MONITORING_FILE = r"C:\Users\user\OneDrive\Dashboard_Tambang\Monitoring_2025_.xlsx"

# ============================================================
# SIMPLE DATA LOADERS (Direct Excel Access)
# ============================================================

@st.cache_data(ttl=60)
def load_bbm_data():
    """Load BBM sheet - simple and direct"""
    try:
        if not os.path.exists(MONITORING_FILE):
            return pd.DataFrame()
        df = pd.read_excel(MONITORING_FILE, sheet_name='BBM')
        # Expected columns: No, Alat Berat, Tipe Alat, 1-31, Total
        return df
    except Exception as e:
        st.error(f"Error loading BBM: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_ritase_data():
    """Load Ritase sheet - simple and direct"""
    try:
        if not os.path.exists(MONITORING_FILE):
            return pd.DataFrame()
        df = pd.read_excel(MONITORING_FILE, sheet_name='Ritase')
        # Expected columns: Tanggal, Shift, Pengawasan, + Location columns
        return df
    except Exception as e:
        st.error(f"Error loading Ritase: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_analisa_produksi():
    """Load Analisa Produksi sheet"""
    try:
        if not os.path.exists(MONITORING_FILE):
            return pd.DataFrame()
        df = pd.read_excel(MONITORING_FILE, sheet_name='Analisa Produksi')
        return df
    except Exception as e:
        st.error(f"Error loading Analisa Produksi: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_gangguan_data():
    """Load Gangguan sheet"""
    try:
        if not os.path.exists(MONITORING_FILE):
            return pd.DataFrame()
        df = pd.read_excel(MONITORING_FILE, sheet_name='Gangguan')
        return df
    except Exception as e:
        st.error(f"Error loading Gangguan: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_tonase_data():
    """Load Tonase sheet"""
    try:
        if not os.path.exists(MONITORING_FILE):
            return pd.DataFrame()
        df = pd.read_excel(MONITORING_FILE, sheet_name='Tonase', header=1)
        return df
    except Exception as e:
        st.error(f"Error loading Tonase: {e}")
        return pd.DataFrame()


# ============================================================
# MAIN DASHBOARD
# ============================================================

def show_monitoring():
    """Render Professional Monitoring Dashboard V4.0"""
    
    # 1. Header
    st.markdown("""
    <div class="page-header">
        <div class="page-header-icon">📡</div>
        <div class="page-header-text">
            <h1>Operational Intelligence</h1>
            <p>Smart Monitoring: Fuel, Supply Chain & Planning Adherence</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 2. Load Data
    df_bbm = load_bbm_data()
    df_rit = load_ritase_data()
    df_prod = load_analisa_produksi()
    df_gang = load_gangguan_data()
    df_ton = load_tonase_data()
    
    # 3. Filters
    st.markdown('<div class="chart-container" style="padding:15px; margin-bottom:20px;">', unsafe_allow_html=True)
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        bulan_opts = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
                      'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
        selected_month = st.selectbox("📅 Periode Bulan", bulan_opts, index=0, key='mon_bulan_v4')
        
    with col_f2:
        selected_shift = st.selectbox("⏰ Shift", ['Semua', '1', '2', '3'], key='mon_shift_v4')
        
    with col_f3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ============================================================
    # KPI CALCULATIONS
    # ============================================================
    
    # BBM Total
    total_bbm = 0
    if not df_bbm.empty and 'Total' in df_bbm.columns:
        try:
            total_bbm = pd.to_numeric(df_bbm['Total'], errors='coerce').sum()
        except:
            pass
    
    # Ritase Total - Sum all location columns
    total_rit = 0
    if not df_rit.empty:
        try:
            # Location columns are everything except Tanggal, Shift, Pengawasan, and Unnamed columns
            exclude = ['Tanggal', 'Shift', 'Pengawasan']
            loc_cols = [c for c in df_rit.columns if c not in exclude and not str(c).startswith('Unnamed') and not str(c).startswith('Tanggal')]
            for col in loc_cols:
                total_rit += pd.to_numeric(df_rit[col], errors='coerce').sum()
        except:
            pass
    
    # Plan Adherence from Analisa Produksi (Januari block)
    plan_adherence = 0
    total_plan = 0
    total_aktual = 0
    if not df_prod.empty:
        try:
            # Structure: Row 0 has headers (Tanggal, Plan, Aktual, Ketercapaian)
            # Actual data starts row 1
            # For Januari, columns 0-3; Februari columns 5-8
            month_idx = bulan_opts.index(selected_month)
            start_col = month_idx * 5  # Approximate, adjust based on actual structure
            
            # Try to find Plan and Aktual columns
            cols = df_prod.columns.tolist()
            plan_col_idx = None
            aktual_col_idx = None
            
            # Search for 'Plan' and 'Aktual' in row 0
            for i, val in enumerate(df_prod.iloc[0]):
                if str(val).strip().lower() == 'plan':
                    plan_col_idx = i
                elif str(val).strip().lower() in ['aktual', 'aktual']:
                    aktual_col_idx = i
                    
            if plan_col_idx is not None and aktual_col_idx is not None:
                plan_data = pd.to_numeric(df_prod.iloc[1:, plan_col_idx], errors='coerce')
                aktual_data = pd.to_numeric(df_prod.iloc[1:, aktual_col_idx], errors='coerce')
                total_plan = plan_data.sum()
                total_aktual = aktual_data.sum()
                plan_adherence = (total_aktual / total_plan * 100) if total_plan > 0 else 0
        except Exception as e:
            pass
    
    # Gangguan Count - Count rows in first month block (columns 0-7)
    total_gangguan = 0
    total_downtime = 0
    if not df_gang.empty:
        try:
            # Column 5 is 'Durasi' for Januari
            if 'Durasi' in df_gang.columns:
                total_downtime = pd.to_numeric(df_gang['Durasi'], errors='coerce').sum()
                total_gangguan = df_gang['Durasi'].notna().sum()
        except:
            pass
    
    # Fuel Efficiency
    fuel_eff = 0
    if total_aktual > 0 and total_bbm > 0:
        fuel_eff = total_bbm / total_aktual
    
    # ============================================================
    # KPI DISPLAY
    # ============================================================
    
    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi-card" style="--card-accent: #3b82f6;">
            <div class="kpi-icon">🎯</div>
            <div class="kpi-label">Plan Adherence</div>
            <div class="kpi-value">{plan_adherence:.1f}%</div>
            <div class="kpi-subtitle">Aktual vs Plan</div>
        </div>
        <div class="kpi-card" style="--card-accent: #f59e0b;">
            <div class="kpi-icon">⛽</div>
            <div class="kpi-label">Total BBM</div>
            <div class="kpi-value">{total_bbm:,.0f}</div>
            <div class="kpi-subtitle">Liter</div>
        </div>
        <div class="kpi-card" style="--card-accent: #10b981;">
            <div class="kpi-icon">🏭</div>
            <div class="kpi-label">Total Produksi</div>
            <div class="kpi-value">{total_aktual:,.0f}</div>
            <div class="kpi-subtitle">Ton</div>
        </div>
        <div class="kpi-card" style="--card-accent: #8b5cf6;">
            <div class="kpi-icon">🚛</div>
            <div class="kpi-label">Total Ritase</div>
            <div class="kpi-value">{total_rit:,.0f}</div>
            <div class="kpi-subtitle">Trips</div>
        </div>
        <div class="kpi-card" style="--card-accent: #ef4444;">
            <div class="kpi-icon">🚨</div>
            <div class="kpi-label">Gangguan</div>
            <div class="kpi-value">{total_gangguan:,.0f}</div>
            <div class="kpi-subtitle">{total_downtime:.1f} jam downtime</div>
        </div>
        <div class="kpi-card" style="--card-accent: #06b6d4;">
            <div class="kpi-icon">📉</div>
            <div class="kpi-label">Fuel Efficiency</div>
            <div class="kpi-value">{fuel_eff:.2f}</div>
            <div class="kpi-subtitle">L/Ton</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ============================================================
    # SECTION 1: PRODUCTION S-CURVE
    # ============================================================
    st.markdown("""
    <div class="section-divider">
        <div class="section-divider-line"></div>
        <span class="section-divider-text">📈 Production S-Curve</span>
        <div class="section-divider-line"></div>
    </div>
    """, unsafe_allow_html=True)
    
    # Try to build S-Curve from Analisa Produksi
    if not df_prod.empty:
        try:
            # Find Tanggal, Plan, Aktual in header row
            header_row = df_prod.iloc[0].tolist()
            tanggal_idx = next((i for i, v in enumerate(header_row) if 'tanggal' in str(v).lower()), 0)
            plan_idx = next((i for i, v in enumerate(header_row) if 'plan' in str(v).lower()), 1)
            aktual_idx = next((i for i, v in enumerate(header_row) if 'aktual' in str(v).lower()), 2)
            
            # Extract data
            df_chart = df_prod.iloc[1:, [tanggal_idx, plan_idx, aktual_idx]].copy()
            df_chart.columns = ['Tanggal', 'Plan', 'Aktual']
            df_chart['Plan'] = pd.to_numeric(df_chart['Plan'], errors='coerce').fillna(0)
            df_chart['Aktual'] = pd.to_numeric(df_chart['Aktual'], errors='coerce').fillna(0)
            df_chart = df_chart[df_chart['Plan'] > 0]  # Filter valid rows
            
            # Cumulative
            df_chart['Cum_Plan'] = df_chart['Plan'].cumsum()
            df_chart['Cum_Aktual'] = df_chart['Aktual'].cumsum()
            
            fig_s = go.Figure()
            fig_s.add_trace(go.Scatter(
                x=list(range(1, len(df_chart)+1)), y=df_chart['Cum_Plan'],
                mode='lines', name='Cumulative Plan',
                line=dict(color='#d4a84b', width=3, dash='dash')
            ))
            fig_s.add_trace(go.Scatter(
                x=list(range(1, len(df_chart)+1)), y=df_chart['Cum_Aktual'],
                mode='lines+markers', name='Cumulative Aktual',
                line=dict(color='#10b981', width=4),
                fill='tonexty', fillcolor='rgba(16, 185, 129, 0.1)'
            ))
            fig_s.update_layout(
                **get_chart_layout(height=400),
                xaxis_title="Hari",
                yaxis_title="Tonase (Kumulatif)",
                legend=dict(orientation="h", y=1.1),
                hovermode="x unified"
            )
            st.plotly_chart(fig_s, use_container_width=True)
        except Exception as e:
            st.info(f"ℹ️ Data S-Curve tidak tersedia: {e}")
    else:
        st.info("ℹ️ Data Analisa Produksi tidak tersedia.")
    
    # ============================================================
    # SECTION 2: RITASE BY LOCATION
    # ============================================================
    st.markdown("""
    <div class="section-divider">
        <div class="section-divider-line"></div>
        <span class="section-divider-text">📍 Ritase Distribution</span>
        <div class="section-divider-line"></div>
    </div>
    """, unsafe_allow_html=True)
    
    col_r1, col_r2 = st.columns(2)
    
    if not df_rit.empty:
        try:
            # Aggregate by location
            exclude = ['Tanggal', 'Shift', 'Pengawasan']
            loc_cols = [c for c in df_rit.columns if c not in exclude 
                        and not str(c).startswith('Unnamed') 
                        and not str(c).startswith('Tanggal')
                        and 'Sum of' not in str(c)
                        and '(All)' not in str(c)]
            
            loc_data = []
            for col in loc_cols:
                total = pd.to_numeric(df_rit[col], errors='coerce').sum()
                if total > 0:
                    loc_data.append({'Location': col, 'Ritase': total})
            
            if loc_data:
                df_loc = pd.DataFrame(loc_data).sort_values('Ritase', ascending=True)
                
                with col_r1:
                    fig_loc = px.bar(
                        df_loc.tail(10), y='Location', x='Ritase',
                        orientation='h',
                        title='🏆 Top 10 Loading Points',
                        color='Ritase', color_continuous_scale='Viridis',
                        text_auto='.0f'
                    )
                    fig_loc.update_layout(**get_chart_layout(height=400))
                    st.plotly_chart(fig_loc, use_container_width=True)
                    
                with col_r2:
                    # Pie chart
                    fig_pie = px.pie(
                        df_loc, values='Ritase', names='Location',
                        title='📊 Ritase Proportion',
                        hole=0.4,
                        color_discrete_sequence=px.colors.qualitative.Bold
                    )
                    fig_pie.update_layout(**get_chart_layout(height=400))
                    fig_pie.update_traces(textposition='inside', textinfo='percent')
                    st.plotly_chart(fig_pie, use_container_width=True)
        except Exception as e:
            st.info(f"ℹ️ Error processing Ritase: {e}")
    else:
        st.info("ℹ️ Data Ritase tidak tersedia.")
    
    # ============================================================
    # SECTION 3: FUEL ANALYTICS
    # ============================================================
    st.markdown("""
    <div class="section-divider">
        <div class="section-divider-line"></div>
        <span class="section-divider-text">⛽ Fuel Analytics</span>
        <div class="section-divider-line"></div>
    </div>
    """, unsafe_allow_html=True)
    
    col_b1, col_b2 = st.columns(2)
    
    if not df_bbm.empty:
        try:
            with col_b1:
                # BBM by Unit Type
                if 'Tipe Alat' in df_bbm.columns and 'Total' in df_bbm.columns:
                    df_type = df_bbm.groupby('Tipe Alat')['Total'].sum().reset_index()
                    df_type['Total'] = pd.to_numeric(df_type['Total'], errors='coerce')
                    df_type = df_type[df_type['Total'] > 0]
                    
                    fig_type = px.pie(
                        df_type, values='Total', names='Tipe Alat',
                        title='⛽ BBM by Unit Type',
                        hole=0.4,
                        color_discrete_sequence=px.colors.qualitative.Bold
                    )
                    fig_type.update_layout(**get_chart_layout(height=350))
                    fig_type.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig_type, use_container_width=True)
                    
            with col_b2:
                # Top 10 BBM Consumers
                if 'Alat Berat' in df_bbm.columns and 'Total' in df_bbm.columns:
                    df_top = df_bbm[['Alat Berat', 'Tipe Alat', 'Total']].copy()
                    df_top['Total'] = pd.to_numeric(df_top['Total'], errors='coerce')
                    df_top = df_top.nlargest(10, 'Total')
                    
                    fig_top = px.bar(
                        df_top, x='Total', y='Alat Berat',
                        orientation='h', color='Tipe Alat',
                        title='🚨 Top 10 Fuel Consumers',
                        text_auto='.0f'
                    )
                    fig_top.update_layout(**get_chart_layout(height=350), yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_top, use_container_width=True)
        except Exception as e:
            st.info(f"ℹ️ Error processing BBM: {e}")
    else:
        st.info("ℹ️ Data BBM tidak tersedia.")
    
    # ============================================================
    # SECTION 4: GANGGUAN OVERVIEW
    # ============================================================
    st.markdown("""
    <div class="section-divider">
        <div class="section-divider-line"></div>
        <span class="section-divider-text">🚨 Gangguan Overview</span>
        <div class="section-divider-line"></div>
    </div>
    """, unsafe_allow_html=True)
    
    if not df_gang.empty:
        try:
            col_g1, col_g2 = st.columns(2)
            
            with col_g1:
                # Gangguan by Kendala
                if 'Kendala' in df_gang.columns:
                    df_kendala = df_gang.groupby('Kendala').size().reset_index(name='Frekuensi')
                    df_kendala = df_kendala[df_kendala['Kendala'].notna()]
                    
                    fig_kendala = px.bar(
                        df_kendala.nlargest(10, 'Frekuensi'), 
                        x='Frekuensi', y='Kendala',
                        orientation='h',
                        title='📊 Gangguan by Kendala',
                        color='Frekuensi',
                        color_continuous_scale='Reds'
                    )
                    fig_kendala.update_layout(**get_chart_layout(height=350))
                    st.plotly_chart(fig_kendala, use_container_width=True)
                    
            with col_g2:
                # Gangguan by Masalah
                if 'Masalah' in df_gang.columns:
                    df_masalah = df_gang.groupby('Masalah').size().reset_index(name='Frekuensi')
                    df_masalah = df_masalah[df_masalah['Masalah'].notna()]
                    
                    fig_masalah = px.pie(
                        df_masalah.nlargest(8, 'Frekuensi'),
                        values='Frekuensi', names='Masalah',
                        title='📊 Top Masalah',
                        hole=0.4
                    )
                    fig_masalah.update_layout(**get_chart_layout(height=350))
                    st.plotly_chart(fig_masalah, use_container_width=True)
        except Exception as e:
            st.info(f"ℹ️ Error processing Gangguan: {e}")
    else:
        st.info("ℹ️ Data Gangguan tidak tersedia.")
    
    # ============================================================
    # DATA TABLES & EXPORT
    # ============================================================
    st.markdown("### 📥 Data Export")
    
    col_exp1, col_exp2, col_exp3 = st.columns(3)
    
    with col_exp1:
        if not df_bbm.empty:
            buf = io.BytesIO()
            df_bbm.to_excel(buf, index=False, sheet_name='BBM')
            st.download_button("📥 Export BBM", buf.getvalue(), "BBM_Export.xlsx", use_container_width=True)
            
    with col_exp2:
        if not df_rit.empty:
            buf = io.BytesIO()
            df_rit.to_excel(buf, index=False, sheet_name='Ritase')
            st.download_button("📥 Export Ritase", buf.getvalue(), "Ritase_Export.xlsx", use_container_width=True)
            
    with col_exp3:
        if not df_gang.empty:
            buf = io.BytesIO()
            df_gang.to_excel(buf, index=False, sheet_name='Gangguan')
            st.download_button("📥 Export Gangguan", buf.getvalue(), "Gangguan_Export.xlsx", use_container_width=True)