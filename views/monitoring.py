# ============================================================
# MONITORING - BBM & Ritase Monitoring Page (COMPLETE)
# ============================================================

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

# Import colors
try:
    from config import MINING_COLORS, CHART_SEQUENCE
except ImportError:
    MINING_COLORS = {
        'gold': '#d4a84b', 'blue': '#3b82f6', 'green': '#10b981',
        'red': '#ef4444', 'orange': '#f59e0b', 'purple': '#8b5cf6',
        'cyan': '#06b6d4', 'slate': '#64748b'
    }
    CHART_SEQUENCE = ['#d4a84b', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4', '#ef4444', '#ec4899']

# Import data loaders
try:
    from utils import (
        load_bbm_enhanced, load_bbm_detail, load_ritase_enhanced, load_ritase_by_front,
        load_tonase, load_tonase_hourly, load_analisa_produksi, load_analisa_produksi_all,
        load_gangguan_monitoring, get_bbm_summary, get_ritase_summary, get_production_summary
    )
except ImportError:
    from utils.data_loader import (
        load_bbm_enhanced, load_bbm_detail, load_ritase_enhanced, load_ritase_by_front,
        load_tonase, load_tonase_hourly, load_analisa_produksi, load_analisa_produksi_all,
        load_gangguan_monitoring, get_bbm_summary, get_ritase_summary, get_production_summary
    )

try:
    from utils.helpers import get_chart_layout
except ImportError:
    def get_chart_layout(height=350, show_legend=True):
        return dict(
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=height,
            margin=dict(l=20, r=20, t=40, b=40),
            font=dict(family='Inter', color='#94a3b8'),
            xaxis=dict(showgrid=False, zeroline=False, showline=True, linecolor='#1e3a5f'),
            yaxis=dict(showgrid=True, gridcolor='rgba(30,58,95,0.5)', zeroline=False),
            legend=dict(orientation='h', yanchor='bottom', y=-0.2, xanchor='center', x=0.5) if show_legend else dict(visible=False),
            hoverlabel=dict(bgcolor='#122a46', font_size=12)
        )


def show_monitoring():
    """Render monitoring page - BBM & Ritase"""
    
    # Page Header
    st.markdown("""
    <div class="page-header">
        <div class="page-header-icon">⛽</div>
        <div class="page-header-text">
            <h1>Monitoring BBM & Ritase</h1>
            <p>Fuel consumption and trip monitoring • Last updated: """ + datetime.now().strftime("%d %b %Y, %H:%M") + """</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Load Data
    df_bbm = load_bbm_enhanced()
    df_ritase = load_ritase_enhanced()
    df_tonase = load_tonase()
    df_produksi = load_analisa_produksi_all()
    df_gangguan = load_gangguan_monitoring()
    
    # Filters
    with st.container():
        col_f1, col_f2, col_f3, col_f4 = st.columns([2, 2, 2, 1])
        
        with col_f1:
            bulan_options = ['Semua', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                           'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
            selected_bulan = st.selectbox("📅 Bulan", bulan_options, index=0)
        
        with col_f2:
            shift_options = ['Semua', '1', '2', '3']
            selected_shift = st.selectbox("⏰ Shift", shift_options, index=0)
        
        with col_f3:
            kategori_options = ['Semua']
            if not df_bbm.empty and 'Kategori' in df_bbm.columns:
                kategori_options += df_bbm['Kategori'].unique().tolist()
            selected_kategori = st.selectbox("🚜 Tipe Alat", kategori_options, index=0)
        
        with col_f4:
            if st.button("🔄 Refresh", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
    
    # Apply filters
    df_ritase_filtered = df_ritase.copy() if not df_ritase.empty else pd.DataFrame()
    if not df_ritase_filtered.empty:
        if selected_bulan != 'Semua':
            bulan_map = {'Januari': 1, 'Februari': 2, 'Maret': 3, 'April': 4, 'Mei': 5, 'Juni': 6,
                        'Juli': 7, 'Agustus': 8, 'September': 9, 'Oktober': 10, 'November': 11, 'Desember': 12}
            if 'Bulan' in df_ritase_filtered.columns:
                df_ritase_filtered = df_ritase_filtered[df_ritase_filtered['Bulan'] == bulan_map.get(selected_bulan, 0)]
        
        if selected_shift != 'Semua':
            df_ritase_filtered = df_ritase_filtered[df_ritase_filtered['Shift'] == int(selected_shift)]
    
    df_bbm_filtered = df_bbm.copy() if not df_bbm.empty else pd.DataFrame()
    if not df_bbm_filtered.empty and selected_kategori != 'Semua':
        df_bbm_filtered = df_bbm_filtered[df_bbm_filtered['Kategori'] == selected_kategori]
    
    # Get summaries
    bbm_summary = get_bbm_summary(df_bbm_filtered)
    ritase_summary = get_ritase_summary(df_ritase_filtered)
    prod_summary = get_production_summary(df_produksi)
    
    # Calculate metrics
    total_bbm = bbm_summary['total_bbm']
    total_ritase = ritase_summary['total_ritase']
    avg_ritase = ritase_summary['avg_per_shift']
    total_tonase = df_tonase['Total'].sum() if not df_tonase.empty and 'Total' in df_tonase.columns else 1
    fuel_eff = total_bbm / total_tonase if total_tonase > 0 else 0
    achievement = prod_summary['achievement_pct']
    total_downtime = df_gangguan['Durasi'].sum() if not df_gangguan.empty and 'Durasi' in df_gangguan.columns else 0
    
    # KPI Cards
    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi-card" style="--card-accent: #ef4444;">
            <div class="kpi-icon">⛽</div>
            <div class="kpi-label">Total BBM</div>
            <div class="kpi-value">{total_bbm:,.0f}</div>
            <div class="kpi-subtitle">liter</div>
        </div>
        <div class="kpi-card" style="--card-accent: #3b82f6;">
            <div class="kpi-icon">🚛</div>
            <div class="kpi-label">Total Ritase</div>
            <div class="kpi-value">{total_ritase:,.0f}</div>
            <div class="kpi-subtitle">trips</div>
        </div>
        <div class="kpi-card" style="--card-accent: #10b981;">
            <div class="kpi-icon">📊</div>
            <div class="kpi-label">Avg Ritase/Shift</div>
            <div class="kpi-value">{avg_ritase:,.0f}</div>
            <div class="kpi-subtitle">trips/shift</div>
        </div>
        <div class="kpi-card" style="--card-accent: #f59e0b;">
            <div class="kpi-icon">⚡</div>
            <div class="kpi-label">Fuel Efficiency</div>
            <div class="kpi-value">{fuel_eff:.2f}</div>
            <div class="kpi-subtitle">L/ton</div>
        </div>
        <div class="kpi-card" style="--card-accent: #d4a84b;">
            <div class="kpi-icon">🎯</div>
            <div class="kpi-label">Achievement</div>
            <div class="kpi-value">{achievement:.1f}%</div>
            <div class="kpi-subtitle">vs target</div>
        </div>
        <div class="kpi-card" style="--card-accent: #8b5cf6;">
            <div class="kpi-icon">⏱️</div>
            <div class="kpi-label">Downtime</div>
            <div class="kpi-value">{total_downtime:.1f}</div>
            <div class="kpi-subtitle">jam</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # BBM Analysis Section
    st.markdown("""
    <div class="section-divider">
        <div class="section-divider-line"></div>
        <span class="section-divider-text">⛽ BBM Analysis</span>
        <div class="section-divider-line"></div>
    </div>
    """, unsafe_allow_html=True)
    
    col_bbm1, col_bbm2 = st.columns([2, 1])
    
    with col_bbm1:
        st.markdown('<div class="chart-container"><div class="chart-header"><span class="chart-title">📊 Konsumsi BBM per Alat</span><span class="chart-badge">Top 15</span></div></div>', unsafe_allow_html=True)
        
        if not df_bbm_filtered.empty and 'Total' in df_bbm_filtered.columns:
            df_bbm_chart = df_bbm_filtered.nlargest(15, 'Total')
            
            color_col = 'Kategori' if 'Kategori' in df_bbm_chart.columns else None
            fig = px.bar(
                df_bbm_chart,
                x='Total',
                y='Tipe Alat',
                orientation='h',
                color=color_col,
                color_discrete_map={'Excavator': MINING_COLORS['gold'], 'Dump Truck': MINING_COLORS['blue'], 'Support': MINING_COLORS['green']}
            )
            fig.update_layout(**get_chart_layout(height=400))
            fig.update_traces(hovertemplate='<b>%{y}</b><br>BBM: %{x:,.0f} L<extra></extra>')
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("📊 Data BBM tidak tersedia")
    
    with col_bbm2:
        st.markdown('<div class="chart-container"><div class="chart-header"><span class="chart-title">🥧 Distribusi BBM</span></div></div>', unsafe_allow_html=True)
        
        if not df_bbm_filtered.empty and 'Kategori' in df_bbm_filtered.columns:
            bbm_by_kategori = df_bbm_filtered.groupby('Kategori')['Total'].sum().reset_index()
            
            fig = px.pie(bbm_by_kategori, values='Total', names='Kategori', hole=0.6,
                        color_discrete_sequence=[MINING_COLORS['gold'], MINING_COLORS['blue'], MINING_COLORS['green']])
            fig.update_layout(**get_chart_layout(height=400, show_legend=True))
            fig.update_traces(textposition='inside', textinfo='percent+label', textfont_size=11)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("📊 Data tidak tersedia")
    
    # BBM Trend
    st.markdown('<div class="chart-container"><div class="chart-header"><span class="chart-title">📈 Tren Konsumsi BBM Harian</span></div></div>', unsafe_allow_html=True)
    
    if not df_bbm_filtered.empty:
        day_cols = [col for col in df_bbm_filtered.columns if str(col).isdigit()]
        if day_cols:
            daily_bbm = df_bbm_filtered[day_cols].sum()
            daily_df = pd.DataFrame({'Tanggal': [int(x) for x in daily_bbm.index], 'BBM': daily_bbm.values})
            daily_df = daily_df[daily_df['BBM'] > 0]
            
            if not daily_df.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=daily_df['Tanggal'], y=daily_df['BBM'],
                    mode='lines+markers', name='BBM',
                    line=dict(color=MINING_COLORS['red'], width=2),
                    fill='tozeroy', fillcolor='rgba(239,68,68,0.1)',
                    hovertemplate='Tanggal %{x}<br>BBM: %{y:,.0f} L<extra></extra>'
                ))
                avg_bbm = daily_df['BBM'].mean()
                fig.add_hline(y=avg_bbm, line_dash="dash", line_color=MINING_COLORS['gold'],
                             annotation_text=f"Avg: {avg_bbm:,.0f} L")
                fig.update_layout(**get_chart_layout(height=300))
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # Ritase Analysis Section
    st.markdown("""
    <div class="section-divider">
        <div class="section-divider-line"></div>
        <span class="section-divider-text">🚛 Ritase Analysis</span>
        <div class="section-divider-line"></div>
    </div>
    """, unsafe_allow_html=True)
    
    col_rit1, col_rit2 = st.columns([2, 1])
    
    with col_rit1:
        st.markdown('<div class="chart-container"><div class="chart-header"><span class="chart-title">📊 Ritase per Front/Lokasi</span></div></div>', unsafe_allow_html=True)
        
        if not df_ritase_filtered.empty:
            front_cols = ['Front B LS', 'Front B Clay', 'Front B LS MIX', 'Front C LS', 'Front C LS MIX',
                         'PLB LS', 'PLB SS', 'PLT SS', 'PLT MIX', 'Timbunan']
            available_fronts = [c for c in front_cols if c in df_ritase_filtered.columns]
            
            if available_fronts:
                front_totals = df_ritase_filtered[available_fronts].sum()
                front_df = pd.DataFrame({'Front': front_totals.index, 'Ritase': front_totals.values})
                front_df = front_df[front_df['Ritase'] > 0].sort_values('Ritase', ascending=True)
                
                fig = px.bar(front_df, x='Ritase', y='Front', orientation='h',
                            color='Ritase', color_continuous_scale=[[0, MINING_COLORS['blue']], [1, MINING_COLORS['gold']]])
                fig.update_layout(**get_chart_layout(height=400, show_legend=False))
                fig.update_coloraxes(showscale=False)
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("📊 Data Ritase tidak tersedia")
    
    with col_rit2:
        st.markdown('<div class="chart-container"><div class="chart-header"><span class="chart-title">📊 Ritase per Shift</span></div></div>', unsafe_allow_html=True)
        
        if not df_ritase_filtered.empty and 'Shift' in df_ritase_filtered.columns and 'Total_Ritase' in df_ritase_filtered.columns:
            shift_data = df_ritase_filtered.groupby('Shift')['Total_Ritase'].sum().reset_index()
            shift_data['Shift'] = shift_data['Shift'].astype(str)
            
            fig = px.bar(shift_data, x='Shift', y='Total_Ritase', color='Shift',
                        color_discrete_sequence=[MINING_COLORS['blue'], MINING_COLORS['green'], MINING_COLORS['orange']])
            fig.update_layout(**get_chart_layout(height=400, show_legend=False))
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("📊 Data tidak tersedia")
    
    # Plan vs Actual Section
    st.markdown("""
    <div class="section-divider">
        <div class="section-divider-line"></div>
        <span class="section-divider-text">🎯 Plan vs Actual</span>
        <div class="section-divider-line"></div>
    </div>
    """, unsafe_allow_html=True)
    
    df_prod_month = load_analisa_produksi(selected_bulan) if selected_bulan != 'Semua' else df_produksi
    
    col_prod1, col_prod2 = st.columns([2, 1])
    
    with col_prod1:
        st.markdown('<div class="chart-container"><div class="chart-header"><span class="chart-title">📊 Plan vs Aktual Produksi</span></div></div>', unsafe_allow_html=True)
        
        if not df_prod_month.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=df_prod_month['Tanggal'], y=df_prod_month['Aktual'],
                                name='Aktual', marker_color=MINING_COLORS['blue']))
            fig.add_trace(go.Scatter(x=df_prod_month['Tanggal'], y=df_prod_month['Plan'],
                                    name='Plan', mode='lines', line=dict(color=MINING_COLORS['red'], width=2, dash='dash')))
            fig.update_layout(**get_chart_layout(height=350))
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("📊 Data Produksi tidak tersedia")
    
    with col_prod2:
        st.markdown('<div class="chart-container"><div class="chart-header"><span class="chart-title">🎯 Ketercapaian</span></div></div>', unsafe_allow_html=True)
        
        if not df_prod_month.empty:
            total_plan = df_prod_month['Plan'].sum()
            total_aktual = df_prod_month['Aktual'].sum()
            pct = (total_aktual / total_plan * 100) if total_plan > 0 else 0
            
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta", value=pct,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Achievement %", 'font': {'size': 14, 'color': '#94a3b8'}},
                delta={'reference': 100, 'increasing': {'color': MINING_COLORS['green']}},
                gauge={
                    'axis': {'range': [None, 120], 'tickcolor': '#94a3b8'},
                    'bar': {'color': MINING_COLORS['gold']},
                    'bgcolor': 'rgba(0,0,0,0)',
                    'steps': [
                        {'range': [0, 80], 'color': 'rgba(239,68,68,0.3)'},
                        {'range': [80, 100], 'color': 'rgba(245,158,11,0.3)'},
                        {'range': [100, 120], 'color': 'rgba(16,185,129,0.3)'}
                    ],
                    'threshold': {'line': {'color': MINING_COLORS['red'], 'width': 4}, 'thickness': 0.75, 'value': 100}
                }
            ))
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': '#94a3b8'}, height=350, margin=dict(l=20, r=20, t=60, b=20))
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("📊 Data tidak tersedia")
    
    # Tonase per Jam Section
    if not df_tonase.empty:
        st.markdown("""
        <div class="section-divider">
            <div class="section-divider-line"></div>
            <span class="section-divider-text">⏰ Tonase per Jam</span>
            <div class="section-divider-line"></div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="chart-container"><div class="chart-header"><span class="chart-title">📊 Distribusi Tonase per Jam (24 Jam)</span></div></div>', unsafe_allow_html=True)
        
        hour_cols = [col for col in df_tonase.columns if '-' in str(col) and col not in ['Tanggal', 'Ritase', 'Total']]
        if hour_cols:
            hourly_avg = df_tonase[hour_cols].mean()
            hourly_df = pd.DataFrame({'Jam': hourly_avg.index, 'Avg_Tonase': hourly_avg.values})
            
            fig = px.bar(hourly_df, x='Jam', y='Avg_Tonase', color='Avg_Tonase',
                        color_continuous_scale=[[0, '#1e3a5f'], [0.5, MINING_COLORS['blue']], [1, MINING_COLORS['gold']]])
            fig.update_layout(**get_chart_layout(height=300, show_legend=False))
            fig.update_coloraxes(showscale=False)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # Data Tables
    st.markdown("""
    <div class="section-divider">
        <div class="section-divider-line"></div>
        <span class="section-divider-text">📋 Data Tables</span>
        <div class="section-divider-line"></div>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📊 BBM Data", "🚛 Ritase Data", "🎯 Produksi Data"])
    
    with tab1:
        if not df_bbm_filtered.empty:
            display_cols = ['Tipe Alat', 'Kategori', 'Total'] if 'Kategori' in df_bbm_filtered.columns else ['Tipe Alat', 'Total']
            display_cols = [c for c in display_cols if c in df_bbm_filtered.columns]
            st.dataframe(df_bbm_filtered[display_cols].sort_values('Total', ascending=False), use_container_width=True, hide_index=True)
            csv = df_bbm_filtered.to_csv(index=False)
            st.download_button("📥 Export BBM (CSV)", csv, f"bbm_data_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
        else:
            st.info("Data tidak tersedia")
    
    with tab2:
        if not df_ritase_filtered.empty:
            display_cols = ['Tanggal', 'Shift', 'Total_Ritase']
            display_cols = [c for c in display_cols if c in df_ritase_filtered.columns]
            st.dataframe(df_ritase_filtered[display_cols].sort_values('Tanggal', ascending=False).head(50), use_container_width=True, hide_index=True)
            csv = df_ritase_filtered.to_csv(index=False)
            st.download_button("📥 Export Ritase (CSV)", csv, f"ritase_data_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
        else:
            st.info("Data tidak tersedia")
    
    with tab3:
        if not df_prod_month.empty:
            st.dataframe(df_prod_month, use_container_width=True, hide_index=True)
            csv = df_prod_month.to_csv(index=False)
            st.download_button("📥 Export Produksi (CSV)", csv, f"produksi_data_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
        else:
            st.info("Data tidak tersedia")