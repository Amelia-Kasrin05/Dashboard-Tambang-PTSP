# ============================================================
# DASHBOARD - Professional Mining Operations Overview
# ============================================================
# Industry-grade mining operations monitoring
# Version 2.0 - Enhanced with professional KPIs and charts

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from config import MINING_COLORS, CHART_SEQUENCE, DAILY_PRODUCTION_TARGET, DAILY_INTERNAL_TARGET
from utils import load_produksi, load_gangguan_all, get_gangguan_summary
from utils.helpers import get_chart_layout


def show_dashboard():
    """Professional Mining Operations Dashboard"""
    
    # Page Header
    st.markdown("""
    <div class="page-header">
        <div class="page-header-icon">📊</div>
        <div class="page-header-text">
            <h1>Operations Dashboard</h1>
            <p>Real-time mining production overview • """ + datetime.now().strftime("%d %b %Y, %H:%M") + """</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Load Data
    df_prod = load_produksi()
    df_gangguan = load_gangguan_all()
    gangguan_summary = get_gangguan_summary(df_gangguan)
    
    # ===== CALCULATE METRICS =====
    if not df_prod.empty:
        total_days = df_prod['Date'].nunique()
        total_rit = df_prod['Rit'].sum()
        total_ton = df_prod['Tonnase'].sum()
        total_exc = df_prod['Excavator'].nunique()
        total_dt = df_prod['Dump Truck'].nunique()
        
        # Calculate daily for target analysis
        daily_tonnage = df_prod.groupby('Date')['Tonnase'].sum()
        days_above_target = (daily_tonnage >= DAILY_PRODUCTION_TARGET).sum()
        
        target_total = DAILY_PRODUCTION_TARGET * total_days
        internal_total = DAILY_INTERNAL_TARGET * total_days
        achievement_pct = (total_ton / target_total * 100) if target_total > 0 else 0
        achievement_internal_pct = (total_ton / internal_total * 100) if internal_total > 0 else 0
        avg_daily = total_ton / total_days if total_days > 0 else 0
    else:
        total_days = total_rit = total_ton = total_exc = total_dt = 0
        target_total = achievement_pct = avg_daily = 0
        achievement_internal_pct = days_above_target = 0
    
    total_gangguan = gangguan_summary['total_incidents']
    total_downtime = gangguan_summary['total_downtime']
    
    # Achievement color - vs Target
    if achievement_pct >= 100:
        ach_color, ach_icon = "#10b981", "✓"
    elif achievement_pct >= 85:
        ach_color, ach_icon = "#f59e0b", "◆"
    else:
        ach_color, ach_icon = "#ef4444", "!"
    
    # Achievement color - vs Internal
    if achievement_internal_pct >= 100:
        int_color, int_icon = "#10b981", "✓"
    elif achievement_internal_pct >= 85:
        int_color, int_icon = "#f59e0b", "◆"
    else:
        int_color, int_icon = "#ef4444", "!"
    
    # ===== KPI CARDS =====
    st.markdown(f"""
    <div style="display:grid; grid-template-columns: repeat(6, 1fr); gap: 0.75rem; margin: 1rem 0;">
        <div class="kpi-card" style="--card-accent: #3b82f6;">
            <div class="kpi-icon">📊</div>
            <div class="kpi-label">Total Produksi</div>
            <div class="kpi-value">{total_ton:,.0f}</div>
            <div class="kpi-subtitle">ton ({total_days} hari)</div>
        </div>
        <div class="kpi-card" style="--card-accent: {ach_color};">
            <div class="kpi-icon">{ach_icon}</div>
            <div class="kpi-label">vs Target</div>
            <div class="kpi-value">{achievement_pct:.1f}%</div>
            <div class="kpi-subtitle">{DAILY_PRODUCTION_TARGET:,}/hari</div>
        </div>
        <div class="kpi-card" style="--card-accent: {int_color};">
            <div class="kpi-icon">{int_icon}</div>
            <div class="kpi-label">vs Internal</div>
            <div class="kpi-value">{achievement_internal_pct:.1f}%</div>
            <div class="kpi-subtitle">{DAILY_INTERNAL_TARGET:,}/hari</div>
        </div>
        <div class="kpi-card" style="--card-accent: #d4a84b;">
            <div class="kpi-icon">🚛</div>
            <div class="kpi-label">Total Ritase</div>
            <div class="kpi-value">{total_rit:,.0f}</div>
            <div class="kpi-subtitle">trips</div>
        </div>
        <div class="kpi-card" style="--card-accent: #10b981;">
            <div class="kpi-icon">🏗️</div>
            <div class="kpi-label">Unit Aktif</div>
            <div class="kpi-value">{total_exc + total_dt}</div>
            <div class="kpi-subtitle">{total_exc} EXC • {total_dt} DT</div>
        </div>
        <div class="kpi-card" style="--card-accent: #ef4444;">
            <div class="kpi-icon">🚨</div>
            <div class="kpi-label">Gangguan</div>
            <div class="kpi-value">{total_gangguan:,}</div>
            <div class="kpi-subtitle">{total_downtime:,.0f} jam downtime</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ===== PRODUCTION TREND =====
    st.markdown("""
    <div class="section-divider">
        <div class="section-divider-line"></div>
        <span class="section-divider-text">📈 Trend Produksi</span>
        <div class="section-divider-line"></div>
    </div>
    """, unsafe_allow_html=True)
    
    if not df_prod.empty:
        with st.container(border=True):
            daily = df_prod.groupby('Date').agg({'Tonnase': 'sum', 'Rit': 'sum'}).reset_index()
            
            # Bar colors: red < 18k, orange 18k-25k, green >= 25k
            colors = ['#10b981' if t >= DAILY_INTERNAL_TARGET else '#f59e0b' if t >= DAILY_PRODUCTION_TARGET else '#ef4444' 
                      for t in daily['Tonnase']]
            
            fig = go.Figure()
            fig.add_trace(go.Bar(x=daily['Date'], y=daily['Tonnase'], marker_color=colors,
                                hovertemplate='<b>%{x|%d %b}</b><br>%{y:,.0f} ton<extra></extra>'))
            fig.add_trace(go.Scatter(x=daily['Date'], y=[DAILY_PRODUCTION_TARGET]*len(daily),
                                    line=dict(color='#ef4444', width=2, dash='dash'), name='Target'))
            fig.add_trace(go.Scatter(x=daily['Date'], y=[DAILY_INTERNAL_TARGET]*len(daily),
                                    line=dict(color='#f59e0b', width=2, dash='dot'), name='Internal'))
            
            fig.update_layout(**get_chart_layout(height=300))
            fig.update_xaxes(tickformat='%d %b')
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # ===== DISTRIBUTION ANALYSIS =====
    st.markdown("""
    <div class="section-divider">
        <div class="section-divider-line"></div>
        <span class="section-divider-text">📊 Distribusi</span>
        <div class="section-divider-line"></div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        with st.container(border=True):
            st.markdown("**Per Excavator**")
            if not df_prod.empty:
                exc = df_prod.groupby('Excavator')['Tonnase'].sum().reset_index()
                exc = exc.sort_values('Tonnase', ascending=True).tail(6)
                fig = px.bar(exc, x='Tonnase', y='Excavator', orientation='h',
                            color='Tonnase', color_continuous_scale=[[0, '#1e3a5f'], [1, '#10b981']])
                fig.update_layout(**get_chart_layout(height=230, show_legend=False))
                fig.update_coloraxes(showscale=False)
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    with col2:
        with st.container(border=True):
            st.markdown("**Per Material**")
            if not df_prod.empty:
                mat = df_prod.groupby('Commudity')['Tonnase'].sum().reset_index()
                fig = px.pie(mat, values='Tonnase', names='Commudity', hole=0.5,
                            color_discrete_sequence=CHART_SEQUENCE)
                fig.update_layout(**get_chart_layout(height=230, show_legend=False))
                fig.update_traces(textposition='inside', textinfo='percent')
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    with col3:
        with st.container(border=True):
            st.markdown("**Per Shift**")
            if not df_prod.empty:
                shift = df_prod.groupby('Shift')['Tonnase'].sum().reset_index()
                fig = px.bar(shift, x='Shift', y='Tonnase', color='Shift',
                            color_discrete_sequence=['#3b82f6', '#10b981', '#d4a84b'])
                fig.update_layout(**get_chart_layout(height=230, show_legend=False))
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # ===== BOTTOM SECTION =====
    st.markdown("""
    <div class="section-divider">
        <div class="section-divider-line"></div>
        <span class="section-divider-text">🔍 Detail</span>
        <div class="section-divider-line"></div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container(border=True):
            st.markdown("**Top 10 BLOK**")
            if not df_prod.empty:
                blok = df_prod.groupby('BLOK')['Tonnase'].sum().reset_index()
                blok = blok.sort_values('Tonnase', ascending=False).head(10)
                fig = px.bar(blok, x='BLOK', y='Tonnase', color='Tonnase',
                            color_continuous_scale=[[0, '#1e3a5f'], [1, '#3b82f6']])
                fig.update_layout(**get_chart_layout(height=230, show_legend=False))
                fig.update_coloraxes(showscale=False)
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    with col2:
        with st.container(border=True):
            st.markdown("**Top Gangguan**")
            if not df_gangguan.empty:
                dg = df_gangguan.groupby('Gangguan').size().reset_index(name='Frekuensi')
                dg = dg.sort_values('Frekuensi', ascending=True).tail(5)
                fig = px.bar(dg, x='Frekuensi', y='Gangguan', orientation='h',
                            color_discrete_sequence=[MINING_COLORS['red']])
                fig.update_layout(**get_chart_layout(height=230, show_legend=False))
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("📊 No gangguan data available")