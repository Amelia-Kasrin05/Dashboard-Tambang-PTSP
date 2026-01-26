# ============================================================
# PRODUKSI - Professional Mining Production Dashboard
# ============================================================
# Industry-grade mining operations monitoring
# Version 2.0 - Enhanced with professional KPIs and charts

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import timedelta

from config import CHART_SEQUENCE, DAILY_PRODUCTION_TARGET, DAILY_INTERNAL_TARGET, SHIFT_HOURS, SHIFTS_PER_DAY
from utils import load_produksi
from utils.helpers import get_chart_layout


def show_produksi():
    """Professional Mining Production Dashboard"""
    
    # Page Header
    st.markdown("""
    <div class="page-header">
        <div class="page-header-icon">⛏️</div>
        <div class="page-header-text">
            <h1>Production Analytics</h1>
            <p>Real-time production monitoring and performance analysis</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    df = load_produksi()
    
    if df.empty:
        st.warning("⚠️ Data produksi tidak tersedia. Pastikan file Excel sudah terhubung.")
        return
    
    # ===== FILTER SECTION =====
    min_date, max_date = df['Date'].min(), df['Date'].max()
    
    st.markdown("""
    <div class="chart-container" style="padding: 1rem;">
        <div class="chart-header">
            <span class="chart-title">🔍 Filter & Analysis Period</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Row 1: Date range
    col_d1, col_d2, col_spacer = st.columns([2, 2, 4])
    
    with col_d1:
        start_date = st.date_input("Dari", min_date, min_value=min_date, max_value=max_date, key="prod_start_input")
    with col_d2:
        end_date = st.date_input("Sampai", max_date, min_value=min_date, max_value=max_date, key="prod_end_input")
    
    # Row 2: Main filters - MULTI-SELECT
    col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)
    
    with col_f1:
        shifts = sorted(df['Shift'].dropna().unique().tolist())
        selected_shifts = st.multiselect("Shift", shifts, default=[], placeholder="Semua", key="prod_shift")
    with col_f2:
        materials = sorted(df['Commudity'].dropna().unique().tolist())
        selected_mats = st.multiselect("Material", materials, default=[], placeholder="Semua", key="prod_mat")
    with col_f3:
        excavators = sorted(df['Excavator'].dropna().unique().tolist())
        selected_excs = st.multiselect("Excavator", excavators, default=[], placeholder="Semua", key="prod_exc")
    with col_f4:
        bloks = sorted(df['BLOK'].dropna().unique().tolist())
        selected_bloks = st.multiselect("BLOK", bloks, default=[], placeholder="Semua", key="prod_blok")
    with col_f5:
        fronts = sorted(df['Front'].dropna().unique().tolist())
        selected_fronts = st.multiselect("Front", fronts, default=[], placeholder="Semua", key="prod_front")
    
    # Apply all filters (empty list = show all)
    mask = (df['Date'] >= start_date) & (df['Date'] <= end_date)
    if selected_shifts:
        mask &= df['Shift'].isin(selected_shifts)
    if selected_mats:
        mask &= df['Commudity'].isin(selected_mats)
    if selected_excs:
        mask &= df['Excavator'].isin(selected_excs)
    if selected_bloks:
        mask &= df['BLOK'].isin(selected_bloks)
    if selected_fronts:
        mask &= df['Front'].isin(selected_fronts)
    
    df_filtered = df[mask].copy()
    
    # ===== CALCULATE METRICS =====
    total_days = df_filtered['Date'].nunique()
    total_rit = df_filtered['Rit'].sum()
    total_ton = df_filtered['Tonnase'].sum()
    total_exc = df_filtered['Excavator'].nunique()
    total_dt = df_filtered['Dump Truck'].nunique()
    
    # Calculate daily tonnage for target analysis
    daily_tonnage = df_filtered.groupby('Date')['Tonnase'].sum()
    days_above_target = (daily_tonnage >= DAILY_PRODUCTION_TARGET).sum()
    days_above_internal = (daily_tonnage >= DAILY_INTERNAL_TARGET).sum()
    
    # Target calculations
    target_total = DAILY_PRODUCTION_TARGET * total_days if total_days > 0 else DAILY_PRODUCTION_TARGET
    internal_total = DAILY_INTERNAL_TARGET * total_days if total_days > 0 else DAILY_INTERNAL_TARGET
    achievement_pct = (total_ton / target_total * 100) if target_total > 0 else 0
    achievement_internal_pct = (total_ton / internal_total * 100) if internal_total > 0 else 0
    
    # Productivity
    avg_daily = total_ton / total_days if total_days > 0 else 0
    avg_per_trip = total_ton / total_rit if total_rit > 0 else 0
    
    # ===== KPI CARDS - 6 CARDS =====
    # Achievement color logic
    if achievement_pct >= 100:
        ach_color, ach_icon = "#10b981", "✓"
    elif achievement_pct >= 85:
        ach_color, ach_icon = "#f59e0b", "◆"
    else:
        ach_color, ach_icon = "#ef4444", "!"
    
    # Internal achievement color
    if achievement_internal_pct >= 100:
        int_color, int_icon = "#10b981", "✓"
    elif achievement_internal_pct >= 85:
        int_color, int_icon = "#f59e0b", "◆"
    else:
        int_color, int_icon = "#ef4444", "!"
    
    # Days achieved color
    days_pct = (days_above_target / total_days * 100) if total_days > 0 else 0
    if days_pct >= 80:
        days_color = "#10b981"
    elif days_pct >= 60:
        days_color = "#f59e0b"
    else:
        days_color = "#ef4444"
    
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
            <div class="kpi-label">vs Target ({DAILY_PRODUCTION_TARGET:,})</div>
            <div class="kpi-value">{achievement_pct:.1f}%</div>
            <div class="kpi-subtitle">target: {target_total:,.0f} ton</div>
        </div>
        <div class="kpi-card" style="--card-accent: {int_color};">
            <div class="kpi-icon">{int_icon}</div>
            <div class="kpi-label">vs Internal ({DAILY_INTERNAL_TARGET:,})</div>
            <div class="kpi-value">{achievement_internal_pct:.1f}%</div>
            <div class="kpi-subtitle">internal: {internal_total:,.0f} ton</div>
        </div>
        <div class="kpi-card" style="--card-accent: #8b5cf6;">
            <div class="kpi-icon">📈</div>
            <div class="kpi-label">Rata-rata Harian</div>
            <div class="kpi-value">{avg_daily:,.0f}</div>
            <div class="kpi-subtitle">ton/hari</div>
        </div>
        <div class="kpi-card" style="--card-accent: #d4a84b;">
            <div class="kpi-icon">🚛</div>
            <div class="kpi-label">Total Ritase</div>
            <div class="kpi-value">{total_rit:,.0f}</div>
            <div class="kpi-subtitle">{avg_per_trip:.1f} ton/trip</div>
        </div>
        <div class="kpi-card" style="--card-accent: {days_color};">
            <div class="kpi-icon">📅</div>
            <div class="kpi-label">Hari Tercapai</div>
            <div class="kpi-value">{days_above_target}/{total_days}</div>
            <div class="kpi-subtitle">{days_pct:.0f}% hari ≥ target</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Period info
    st.caption(f"📅 Periode: {start_date} - {end_date} ({total_days} hari) • 📋 {len(df_filtered):,} records • 🏗️ {total_exc} Excavator • 🚛 {total_dt} Dump Truck")
    
    # ===== MAIN CHART: PRODUCTION TREND =====
    st.markdown("""
    <div class="section-divider">
        <div class="section-divider-line"></div>
        <span class="section-divider-text">📈 Trend Produksi Harian</span>
        <div class="section-divider-line"></div>
    </div>
    """, unsafe_allow_html=True)
    
    daily = df_filtered.groupby('Date').agg({'Tonnase': 'sum', 'Rit': 'sum'}).reset_index()
    
    with st.container(border=True):
        # Create combined chart with secondary axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Bar colors: red < 18k, orange 18k-25k, green >= 25k
        colors = ['#10b981' if t >= DAILY_INTERNAL_TARGET else '#f59e0b' if t >= DAILY_PRODUCTION_TARGET else '#ef4444' 
                  for t in daily['Tonnase']]
        
        # Production bars
        fig.add_trace(
            go.Bar(x=daily['Date'], y=daily['Tonnase'], name='Produksi', marker_color=colors,
                   hovertemplate='<b>%{x|%d %b %Y}</b><br>Produksi: %{y:,.0f} ton<extra></extra>'),
            secondary_y=False
        )
        
        # Target line (Plan - 18k)
        fig.add_trace(
            go.Scatter(x=daily['Date'], y=[DAILY_PRODUCTION_TARGET]*len(daily), name=f'Target ({DAILY_PRODUCTION_TARGET:,})', 
                       line=dict(color='#ef4444', width=2, dash='dash'), mode='lines',
                       hovertemplate='Target: %{y:,} ton<extra></extra>'),
            secondary_y=False
        )
        
        # Internal target line (25k)
        fig.add_trace(
            go.Scatter(x=daily['Date'], y=[DAILY_INTERNAL_TARGET]*len(daily), name=f'Internal ({DAILY_INTERNAL_TARGET:,})', 
                       line=dict(color='#f59e0b', width=2, dash='dot'), mode='lines',
                       hovertemplate='Internal: %{y:,} ton<extra></extra>'),
            secondary_y=False
        )
        
        # Ritase line on secondary axis
        fig.add_trace(
            go.Scatter(x=daily['Date'], y=daily['Rit'], name='Ritase', 
                       line=dict(color='#8b5cf6', width=2), mode='lines+markers', marker=dict(size=4),
                       hovertemplate='Ritase: %{y:,.0f}<extra></extra>'),
            secondary_y=True
        )
        
        fig.update_layout(**get_chart_layout(height=380))
        fig.update_yaxes(title_text="Tonase (ton)", secondary_y=False, gridcolor='rgba(255,255,255,0.1)')
        fig.update_yaxes(title_text="Ritase", secondary_y=True, showgrid=False)
        fig.update_xaxes(tickformat='%d %b', gridcolor='rgba(255,255,255,0.05)')
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # ===== CUMULATIVE PRODUCTION CHART =====
    
    # ===== ANALYSIS SECTION =====
    st.markdown("""
    <div class="section-divider">
        <div class="section-divider-line"></div>
        <span class="section-divider-text">📊 Analisis Produksi</span>
        <div class="section-divider-line"></div>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["🏗️ Per Unit", "📍 Per Lokasi", "🔄 Per Shift"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            with st.container(border=True):
                st.markdown("""
                <div style="background: linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%); 
                            border-radius: 12px; padding: 1rem; margin-bottom: 1rem;
                            border: 1px solid rgba(16, 185, 129, 0.3);">
                    <h4 style="color: #10b981; margin: 0; font-size: 0.9rem;">🏗️ Excavator Performance</h4>
                </div>
                """, unsafe_allow_html=True)
                exc_data = df_filtered.groupby('Excavator').agg({
                    'Tonnase': 'sum', 
                    'Rit': 'sum'
                }).reset_index()
                exc_data['Avg_per_Rit'] = exc_data['Tonnase'] / exc_data['Rit'].replace(0, 1)
                exc_data = exc_data.sort_values('Tonnase', ascending=True)
                
                fig = px.bar(exc_data, x='Tonnase', y='Excavator', orientation='h',
                            color='Tonnase', color_continuous_scale=[[0, '#1e3a5f'], [1, '#10b981']],
                            hover_data={'Rit': ':,.0f', 'Avg_per_Rit': ':.1f'})
                fig.update_layout(**get_chart_layout(height=300, show_legend=False))
                fig.update_coloraxes(showscale=False)
                fig.update_traces(hovertemplate='<b>%{y}</b><br>Tonase: %{x:,.0f}<br>Ritase: %{customdata[0]:,.0f}<br>Avg/Rit: %{customdata[1]:.1f}<extra></extra>')
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        with col2:
            with st.container(border=True):
                st.markdown("""
                <div style="background: linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%); 
                            border-radius: 12px; padding: 1rem; margin-bottom: 1rem;
                            border: 1px solid rgba(212, 168, 75, 0.3);">
                    <h4 style="color: #d4a84b; margin: 0; font-size: 0.9rem;">🚛 Top 10 Dump Truck</h4>
                </div>
                """, unsafe_allow_html=True)
                dt_data = df_filtered.groupby('Dump Truck').agg({
                    'Tonnase': 'sum',
                    'Rit': 'sum'
                }).reset_index()
                dt_data = dt_data.sort_values('Tonnase', ascending=True).tail(10)
                
                fig = px.bar(dt_data, x='Tonnase', y='Dump Truck', orientation='h',
                            color='Tonnase', color_continuous_scale=[[0, '#1e3a5f'], [1, '#d4a84b']])
                fig.update_layout(**get_chart_layout(height=300, show_legend=False))
                fig.update_coloraxes(showscale=False)
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    with tab2:
        # Row 1: BLOK and Front charts
        col1, col2 = st.columns(2)
        with col1:
            with st.container(border=True):
                st.markdown("""
                <div style="background: linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%); 
                            border-radius: 12px; padding: 1rem; margin-bottom: 1rem;
                            border: 1px solid rgba(59, 130, 246, 0.3);">
                    <h4 style="color: #3b82f6; margin: 0 0 0.5rem 0; font-size: 0.9rem;">📊 Produksi per BLOK</h4>
                </div>
                """, unsafe_allow_html=True)
                blok_data = df_filtered.groupby('BLOK')['Tonnase'].sum().reset_index()
                blok_data = blok_data.sort_values('Tonnase', ascending=False).head(10)
                
                fig = px.bar(blok_data, x='BLOK', y='Tonnase', color='Tonnase',
                            color_continuous_scale=[[0, '#1e3a5f'], [1, '#3b82f6']])
                fig.update_layout(**get_chart_layout(height=280, show_legend=False))
                fig.update_coloraxes(showscale=False)
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        with col2:
            with st.container(border=True):
                st.markdown("""
                <div style="background: linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%); 
                            border-radius: 12px; padding: 1rem; margin-bottom: 1rem;
                            border: 1px solid rgba(139, 92, 246, 0.3);">
                    <h4 style="color: #8b5cf6; margin: 0 0 0.5rem 0; font-size: 0.9rem;">📍 Produksi per Front</h4>
                </div>
                """, unsafe_allow_html=True)
                front_data = df_filtered.groupby('Front')['Tonnase'].sum().reset_index()
                front_data = front_data.sort_values('Tonnase', ascending=False).head(10)
                
                fig = px.bar(front_data, x='Front', y='Tonnase', color='Tonnase',
                            color_continuous_scale=[[0, '#1e3a5f'], [1, '#8b5cf6']])
                fig.update_layout(**get_chart_layout(height=280, show_legend=False))
                fig.update_coloraxes(showscale=False)
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        # Separator
        st.markdown("<hr style='border: none; border-top: 1px solid rgba(255,255,255,0.1); margin: 1.5rem 0;'>", unsafe_allow_html=True)
        
        # Row 2: Material composition
        with st.container(border=True):
            st.markdown("""
            <div style="background: linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%); 
                        border-radius: 12px; padding: 1rem; margin-bottom: 1rem;
                        border: 1px solid rgba(212, 168, 75, 0.3);">
                <h4 style="color: #d4a84b; margin: 0; font-size: 0.9rem;">🪨 Komposisi Material</h4>
            </div>
            """, unsafe_allow_html=True)
            
            col_m1, col_m2 = st.columns([1, 2])
            
            with col_m1:
                mat_data = df_filtered.groupby('Commudity')['Tonnase'].sum().reset_index()
                mat_data['Percentage'] = mat_data['Tonnase'] / mat_data['Tonnase'].sum() * 100
                
                fig = px.pie(mat_data, values='Tonnase', names='Commudity', hole=0.5,
                            color_discrete_sequence=CHART_SEQUENCE)
                fig.update_layout(**get_chart_layout(height=300, show_legend=False))
                fig.update_traces(textposition='inside', textinfo='percent',
                                 hovertemplate='<b>%{label}</b><br>%{value:,.0f} ton<br>%{percent}<extra></extra>')
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
            with col_m2:
                # Material breakdown table with styling
                mat_table = mat_data.copy()
                mat_table = mat_table.sort_values('Tonnase', ascending=False)
                mat_table['Tonnase_fmt'] = mat_table['Tonnase'].apply(lambda x: f"{x:,.0f}")
                mat_table['Percentage_fmt'] = mat_table['Percentage'].apply(lambda x: f"{x:.1f}%")
                
                st.dataframe(
                    mat_table[['Commudity', 'Tonnase_fmt', 'Percentage_fmt']].rename(columns={
                        'Commudity': 'Material',
                        'Tonnase_fmt': 'Tonase',
                        'Percentage_fmt': 'Persentase'
                    }),
                    use_container_width=True,
                    hide_index=True,
                    height=240
                )
    
    with tab3:
        col1, col2 = st.columns(2)
        with col1:
            with st.container(border=True):
                st.markdown("""
                <div style="background: linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%); 
                            border-radius: 12px; padding: 1rem; margin-bottom: 1rem;
                            border: 1px solid rgba(59, 130, 246, 0.3);">
                    <h4 style="color: #3b82f6; margin: 0; font-size: 0.9rem;">📊 Produksi per Shift</h4>
                </div>
                """, unsafe_allow_html=True)
                shift_data = df_filtered.groupby('Shift')['Tonnase'].sum().reset_index()
                shift_data['Percentage'] = shift_data['Tonnase'] / shift_data['Tonnase'].sum() * 100
                
                fig = px.bar(shift_data, x='Shift', y='Tonnase', color='Shift',
                            text=shift_data['Percentage'].apply(lambda x: f'{x:.1f}%'),
                            color_discrete_sequence=['#3b82f6', '#10b981', '#d4a84b'])
                fig.update_layout(**get_chart_layout(height=280, show_legend=False))
                fig.update_traces(textposition='outside')
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        with col2:
            with st.container(border=True):
                st.markdown("""
                <div style="background: linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%); 
                            border-radius: 12px; padding: 1rem; margin-bottom: 1rem;
                            border: 1px solid rgba(16, 185, 129, 0.3);">
                    <h4 style="color: #10b981; margin: 0; font-size: 0.9rem;">📈 Rata-rata Harian per Shift</h4>
                </div>
                """, unsafe_allow_html=True)
                shift_daily = df_filtered.groupby(['Date', 'Shift'])['Tonnase'].sum().reset_index()
                shift_avg = shift_daily.groupby('Shift')['Tonnase'].mean().reset_index()
                shift_avg.columns = ['Shift', 'Avg_Daily']
                
                fig = px.bar(shift_avg, x='Shift', y='Avg_Daily', color='Shift',
                            text=shift_avg['Avg_Daily'].apply(lambda x: f'{x:,.0f}'),
                            color_discrete_sequence=['#3b82f6', '#10b981', '#d4a84b'])
                fig.update_layout(**get_chart_layout(height=280, show_legend=False))
                fig.update_traces(textposition='outside')
                fig.update_yaxes(title_text='Rata-rata Tonase/Hari')
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        # Separator
        st.markdown("<hr style='border: none; border-top: 1px solid rgba(255,255,255,0.1); margin: 1.5rem 0;'>", unsafe_allow_html=True)
        
        # Heatmap - full width for better visibility
        with st.container(border=True):
            st.markdown("""
            <div style="background: linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%); 
                        border-radius: 12px; padding: 1rem; margin-bottom: 1rem;
                        border: 1px solid rgba(139, 92, 246, 0.3);">
                <h4 style="color: #8b5cf6; margin: 0; font-size: 0.9rem;">🔥 Heatmap: Shift × Excavator</h4>
            </div>
            """, unsafe_allow_html=True)
            
            pivot = df_filtered.pivot_table(values='Tonnase', index='Excavator', columns='Shift', 
                                           aggfunc='sum', fill_value=0)
            
            if not pivot.empty:
                fig = px.imshow(pivot, aspect='auto', text_auto='.0f',
                               color_continuous_scale=[[0, '#0a1628'], [0.3, '#1e3a5f'], [0.6, '#3b82f6'], [1, '#10b981']])
                fig.update_layout(**get_chart_layout(height=350, show_legend=False))
                fig.update_traces(textfont=dict(size=10, color='white'))
                fig.update_coloraxes(showscale=True, colorbar=dict(title='Tonase', tickformat=','))
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # ===== DATA TABLE =====
    st.markdown("""
    <div class="section-divider">
        <div class="section-divider-line"></div>
        <span class="section-divider-text">📋 Data Detail</span>
        <div class="section-divider-line"></div>
    </div>
    """, unsafe_allow_html=True)
    
    # Summary row
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1e3a5f 0%, #0a1628 100%); border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
        <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 1rem;">
            <div><span style="color: #64748b;">Total Records:</span> <span style="color: #fff; font-weight: 600;">{len(df_filtered):,}</span></div>
            <div><span style="color: #64748b;">Total Tonase:</span> <span style="color: #10b981; font-weight: 600;">{total_ton:,.0f} ton</span></div>
            <div><span style="color: #64748b;">Total Ritase:</span> <span style="color: #d4a84b; font-weight: 600;">{total_rit:,.0f}</span></div>
            <div><span style="color: #64748b;">Avg/Trip:</span> <span style="color: #8b5cf6; font-weight: 600;">{avg_per_trip:.1f} ton</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Export button
    col1, col2 = st.columns([4, 1])
    with col2:
        import io
        buffer = io.BytesIO()
        # Export with original column names
        cols_export = ['Date', 'Time', 'Shift', 'BLOK', 'Front', 'Commudity', 'Excavator', 'Dump Truck', 'Dump Loc', 'Rit', 'Tonnase']
        cols_export = [c for c in cols_export if c in df_filtered.columns]
        
        try:
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_filtered[cols_export].sort_index(ascending=False).to_excel(writer, index=False, sheet_name='Produksi')
            
            st.download_button(
                label="📥 Export Excel",
                data=buffer.getvalue(),
                file_name=f"produksi_export_N{len(df_filtered)}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        except Exception as e:
            st.warning(f"⚠️ Export tidak tersedia saat ini (Disk Full/Error).")
            # Log error nicely without breaking app
            print(f"Export Error: {e}")
    
    # Table
    cols_show = ['Date', 'Time', 'Shift', 'BLOK', 'Front', 'Commudity', 'Excavator', 'Dump Truck', 'Dump Loc', 'Rit', 'Tonnase']
    cols_show = [c for c in cols_show if c in df_filtered.columns]
    
    st.dataframe(
        df_filtered[cols_show].sort_index(ascending=False),
        use_container_width=True,
        height=450,
        column_config={
            "Date": st.column_config.DateColumn(format="DD/MM/YYYY"),
            "Tonnase": st.column_config.NumberColumn(format="%.0f"),
            "Rit": st.column_config.NumberColumn(format="%.0f"),
        }
    )