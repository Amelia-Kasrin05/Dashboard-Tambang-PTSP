# ============================================================
# DASHBOARD - Main Overview Page
# ============================================================

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from config import MINING_COLORS, CHART_SEQUENCE
from utils import load_produksi, load_bbm, load_gangguan, load_daily_plan
from utils.helpers import get_chart_layout


def show_dashboard():
    """Render main dashboard overview"""
    
    # Page Header
    st.markdown("""
    <div class="page-header">
        <div class="page-header-icon">📊</div>
        <div class="page-header-text">
            <h1>Operations Dashboard</h1>
            <p>Real-time mining production overview • Last updated: """ + datetime.now().strftime("%d %b %Y, %H:%M") + """</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Load Data
    df_prod = load_produksi()
    df_bbm = load_bbm()
    df_gangguan = load_gangguan("Januari")
    df_daily = load_daily_plan()
    
    # ===== KPI CARDS =====
    total_rit = df_prod['Rit'].sum() if not df_prod.empty else 0
    total_ton = df_prod['Tonnase'].sum() if not df_prod.empty else 0
    total_exc = df_prod['Excavator'].nunique() if not df_prod.empty else 0
    total_bbm = df_bbm['Total'].sum() if not df_bbm.empty else 0
    total_gangguan = len(df_gangguan) if not df_gangguan.empty else 0
    
    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi-card" style="--card-accent: #d4a84b;">
            <div class="kpi-icon">🚛</div>
            <div class="kpi-label">Total Ritase</div>
            <div class="kpi-value">{total_rit:,.0f}</div>
            <div class="kpi-subtitle">trips completed</div>
        </div>
        <div class="kpi-card" style="--card-accent: #3b82f6;">
            <div class="kpi-icon">⚖️</div>
            <div class="kpi-label">Total Tonase</div>
            <div class="kpi-value">{total_ton:,.0f}</div>
            <div class="kpi-subtitle">metric tons</div>
        </div>
        <div class="kpi-card" style="--card-accent: #10b981;">
            <div class="kpi-icon">🏗️</div>
            <div class="kpi-label">Active Units</div>
            <div class="kpi-value">{total_exc}</div>
            <div class="kpi-subtitle">excavators</div>
        </div>
        <div class="kpi-card" style="--card-accent: #f59e0b;">
            <div class="kpi-icon">⛽</div>
            <div class="kpi-label">Fuel Usage</div>
            <div class="kpi-value">{total_bbm:,.0f}</div>
            <div class="kpi-subtitle">liters consumed</div>
        </div>
        <div class="kpi-card" style="--card-accent: #ef4444;">
            <div class="kpi-icon">🚨</div>
            <div class="kpi-label">Incidents</div>
            <div class="kpi-value">{total_gangguan}</div>
            <div class="kpi-subtitle">reported issues</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ===== MAIN CHARTS ROW =====
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        <div class="chart-container">
            <div class="chart-header">
                <span class="chart-title">📈 Production Trend</span>
                <span class="chart-badge">Daily</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if not df_prod.empty:
            daily = df_prod.groupby('Date').agg({'Tonnase': 'sum', 'Rit': 'sum'}).reset_index()
            
            fig = go.Figure()
            
            # Area chart for tonnage
            fig.add_trace(go.Scatter(
                x=daily['Date'],
                y=daily['Tonnase'],
                name='Tonase',
                fill='tozeroy',
                line=dict(color=MINING_COLORS['gold'], width=2),
                fillcolor='rgba(212,168,75,0.15)',
                hovertemplate='<b>%{x}</b><br>Tonase: %{y:,.0f}<extra></extra>'
            ))
            
            # Line for ritase
            fig.add_trace(go.Scatter(
                x=daily['Date'],
                y=daily['Rit'] * 50,  # Scale for visibility
                name='Ritase (scaled)',
                line=dict(color=MINING_COLORS['blue'], width=2, dash='dot'),
                hovertemplate='<b>%{x}</b><br>Ritase: %{customdata:,.0f}<extra></extra>',
                customdata=daily['Rit']
            ))
            
            fig.update_layout(**get_chart_layout(height=320))
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("📊 Production data not available")
    
    with col2:
        st.markdown("""
        <div class="chart-container">
            <div class="chart-header">
                <span class="chart-title">🏗️ By Excavator</span>
                <span class="chart-badge">Top 6</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if not df_prod.empty:
            exc = df_prod.groupby('Excavator')['Tonnase'].sum().reset_index()
            exc = exc.sort_values('Tonnase', ascending=True).tail(6)
            
            fig = px.bar(
                exc,
                x='Tonnase',
                y='Excavator',
                orientation='h',
                color='Tonnase',
                color_continuous_scale=[[0, '#1e3a5f'], [0.5, '#3b82f6'], [1, '#d4a84b']]
            )
            fig.update_layout(**get_chart_layout(height=320, show_legend=False))
            fig.update_coloraxes(showscale=False)
            fig.update_traces(hovertemplate='<b>%{y}</b><br>Tonase: %{x:,.0f}<extra></extra>')
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("📊 Data not available")
    
    # ===== SECTION DIVIDER =====
    st.markdown("""
    <div class="section-divider">
        <div class="section-divider-line"></div>
        <span class="section-divider-text">Distribution Analysis</span>
        <div class="section-divider-line" style="background: linear-gradient(90deg, transparent 0%, #1e3a5f 100%);"></div>
    </div>
    """, unsafe_allow_html=True)
    
    # ===== DISTRIBUTION CHARTS =====
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.markdown('<div class="chart-container"><div class="chart-header"><span class="chart-title">🪨 Material</span></div></div>', unsafe_allow_html=True)
        if not df_prod.empty:
            mat = df_prod.groupby('Commudity')['Tonnase'].sum().reset_index()
            fig = px.pie(mat, values='Tonnase', names='Commudity', hole=0.6, color_discrete_sequence=CHART_SEQUENCE)
            fig.update_layout(**get_chart_layout(height=220, show_legend=False))
            fig.update_traces(textposition='inside', textinfo='percent', textfont_size=11)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    with c2:
        st.markdown('<div class="chart-container"><div class="chart-header"><span class="chart-title">🔄 By Shift</span></div></div>', unsafe_allow_html=True)
        if not df_prod.empty:
            shift = df_prod.groupby('Shift')['Tonnase'].sum().reset_index()
            fig = px.bar(shift, x='Shift', y='Tonnase', color='Shift', color_discrete_sequence=CHART_SEQUENCE[:3])
            fig.update_layout(**get_chart_layout(height=220, show_legend=False))
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    with c3:
        st.markdown('<div class="chart-container"><div class="chart-header"><span class="chart-title">🚨 Top Issues</span></div></div>', unsafe_allow_html=True)
        if not df_gangguan.empty:
            dg = df_gangguan.head(5)
            fig = px.bar(dg, x='Frekuensi', y='Row Labels', orientation='h', color_discrete_sequence=[MINING_COLORS['red']])
            fig.update_layout(**get_chart_layout(height=220, show_legend=False))
            fig.update_yaxes(categoryorder='total ascending')
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("No data")
    
    with c4:
        st.markdown('<div class="chart-container"><div class="chart-header"><span class="chart-title">⛽ Fuel by Type</span></div></div>', unsafe_allow_html=True)
        if not df_bbm.empty:
            bbm = df_bbm.groupby('Alat Berat')['Total'].sum().reset_index().head(5)
            fig = px.pie(bbm, values='Total', names='Alat Berat', hole=0.6, color_discrete_sequence=CHART_SEQUENCE)
            fig.update_layout(**get_chart_layout(height=220, show_legend=False))
            fig.update_traces(textposition='inside', textinfo='percent', textfont_size=11)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("No data")
    
    # ===== HEATMAP =====
    if not df_prod.empty:
        st.markdown("""
        <div class="section-divider">
            <div class="section-divider-line"></div>
            <span class="section-divider-text">Productivity Heatmap</span>
            <div class="section-divider-line" style="background: linear-gradient(90deg, transparent 0%, #1e3a5f 100%);"></div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="chart-container"><div class="chart-header"><span class="chart-title">🔥 Shift × Excavator Performance</span></div></div>', unsafe_allow_html=True)
        
        pivot = df_prod.pivot_table(values='Tonnase', index='Excavator', columns='Shift', aggfunc='sum', fill_value=0)
        
        fig = px.imshow(
            pivot,
            color_continuous_scale=[[0, '#0f2744'], [0.3, '#1e3a5f'], [0.6, '#3b82f6'], [1, '#d4a84b']],
            aspect='auto',
            labels=dict(x="Shift", y="Excavator", color="Tonase")
        )
        fig.update_layout(**get_chart_layout(height=300, show_legend=False))
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
