# ============================================================
# GANGGUAN - Production Incident Analysis Page
# ============================================================
# VERSION: 3.0 - Professional Layout with Multi-Select Filters

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config import MINING_COLORS, CHART_SEQUENCE
from utils import load_gangguan_all, get_gangguan_summary
from utils.helpers import get_chart_layout


def show_gangguan():
    """Render production incident analysis page"""
    
    # Page Header
    st.markdown("""
    <div class="page-header">
        <div class="page-header-icon">🚨</div>
        <div class="page-header-text">
            <h1>Gangguan Produksi</h1>
            <p>Production incident analysis & downtime tracking</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Load Data
    df = load_gangguan_all()
    
    if df.empty:
        st.warning("⚠️ Data gangguan tidak tersedia. Pastikan file Excel sudah terhubung.")
        return
    
    # ===== FILTER SECTION =====
    st.markdown("""
    <div class="chart-container" style="padding: 1rem;">
        <div class="chart-header">
            <span class="chart-title">🔍 Filter & Analysis Period</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Row 1: Date range
    min_date = df['Tanggal'].min()
    max_date = df['Tanggal'].max()
    
    col_d1, col_d2, col_spacer = st.columns([2, 2, 4])
    
    with col_d1:
        start_date = st.date_input("Dari", min_date, min_value=min_date, max_value=max_date, key="gang_start")
    with col_d2:
        end_date = st.date_input("Sampai", max_date, min_value=min_date, max_value=max_date, key="gang_end")
    
    # Row 2: Multi-select filters
    col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)
    
    with col_f1:
        shifts = sorted([int(x) for x in df['Shift'].dropna().unique()])
        shifts = [str(s) for s in shifts]
        selected_shifts = st.multiselect("Shift", shifts, default=[], placeholder="Semua", key="gang_shift")
    
    with col_f2:
        kelompok_list = sorted(df['Kelompok Masalah'].dropna().unique().tolist())
        selected_kelompoks = st.multiselect("Kelompok Masalah", kelompok_list, default=[], placeholder="Semua", key="gang_kelompok")
    
    with col_f3:
        alat_list = sorted([str(a) for a in df['Alat'].dropna().unique().tolist()])
        selected_alats = st.multiselect("Alat", alat_list, default=[], placeholder="Semua", key="gang_alat")
    
    with col_f4:
        # Crusher filter - new column from November 2025
        if 'Crusher' in df.columns:
            crusher_list = sorted([str(c) for c in df['Crusher'].dropna().unique().tolist()])
            selected_crushers = st.multiselect("Crusher", crusher_list, default=[], placeholder="Semua", key="gang_crusher")
        else:
            selected_crushers = []
    
    with col_f5:
        gangguan_list = sorted(df['Gangguan'].dropna().unique().tolist())
        selected_gangguans = st.multiselect("Jenis Gangguan", gangguan_list, default=[], placeholder="Semua", key="gang_jenis")
    
    # Apply Filters
    df_filtered = df.copy()
    df_filtered = df_filtered[(df_filtered['Tanggal'] >= pd.Timestamp(start_date)) & 
                               (df_filtered['Tanggal'] <= pd.Timestamp(end_date))]
    
    if selected_shifts:
        df_filtered = df_filtered[df_filtered['Shift'].astype(str).isin(selected_shifts)]
    if selected_kelompoks:
        df_filtered = df_filtered[df_filtered['Kelompok Masalah'].isin(selected_kelompoks)]
    if selected_alats:
        df_filtered = df_filtered[df_filtered['Alat'].astype(str).isin(selected_alats)]
    if selected_crushers and 'Crusher' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['Crusher'].astype(str).isin(selected_crushers)]
    if selected_gangguans:
        df_filtered = df_filtered[df_filtered['Gangguan'].isin(selected_gangguans)]
    
    # ===== KPI CARDS =====
    total_incidents = len(df_filtered)
    total_downtime = df_filtered['Durasi'].sum() if not df_filtered.empty else 0
    mttr = df_filtered['Durasi'].mean() * 60 if not df_filtered.empty else 0  # Convert to minutes
    total_days = df_filtered['Tanggal'].nunique() if not df_filtered.empty else 1
    incident_rate = total_incidents / max(total_days, 1)
    total_alat = df_filtered['Alat'].nunique() if not df_filtered.empty else 0
    
    # Get availability (assuming 24 hours per day operation)
    total_hours = total_days * 24
    availability = ((total_hours - total_downtime) / total_hours * 100) if total_hours > 0 else 100
    
    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi-card" style="--card-accent: #ef4444;">
            <div class="kpi-icon">🚨</div>
            <div class="kpi-label">Total Incidents</div>
            <div class="kpi-value">{total_incidents:,}</div>
            <div class="kpi-subtitle">{total_days} hari</div>
        </div>
        <div class="kpi-card" style="--card-accent: #f59e0b;">
            <div class="kpi-icon">⏱️</div>
            <div class="kpi-label">Total Downtime</div>
            <div class="kpi-value">{total_downtime:,.1f}</div>
            <div class="kpi-subtitle">jam</div>
        </div>
        <div class="kpi-card" style="--card-accent: #3b82f6;">
            <div class="kpi-icon">📊</div>
            <div class="kpi-label">MTTR</div>
            <div class="kpi-value">{mttr:,.1f}</div>
            <div class="kpi-subtitle">menit/kejadian</div>
        </div>
        <div class="kpi-card" style="--card-accent: #10b981;">
            <div class="kpi-icon">✅</div>
            <div class="kpi-label">Availability</div>
            <div class="kpi-value">{availability:.1f}%</div>
            <div class="kpi-subtitle">uptime</div>
        </div>
        <div class="kpi-card" style="--card-accent: #8b5cf6;">
            <div class="kpi-icon">📈</div>
            <div class="kpi-label">Incident Rate</div>
            <div class="kpi-value">{incident_rate:,.1f}</div>
            <div class="kpi-subtitle">per hari</div>
        </div>
        <div class="kpi-card" style="--card-accent: #06b6d4;">
            <div class="kpi-icon">🔧</div>
            <div class="kpi-label">Alat Terdampak</div>
            <div class="kpi-value">{total_alat}</div>
            <div class="kpi-subtitle">unit</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Filter info
    st.markdown(f"""
    <p style="color:#64748b; font-size:0.85rem; margin:0.5rem 0 1.5rem 0; text-align:center;">
        📅 <strong>Periode:</strong> {start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')} ({total_days} hari) • 
        📋 <strong>{len(df_filtered):,}</strong> dari {len(df):,} kejadian
    </p>
    """, unsafe_allow_html=True)
    
    # ===== TREND CHART =====
    st.markdown("""
    <div class="section-divider">
        <div class="section-divider-line"></div>
        <span class="section-divider-text">📈 Trend Gangguan Harian</span>
        <div class="section-divider-line"></div>
    </div>
    """, unsafe_allow_html=True)
    
    # Daily trend
    daily = df_filtered.groupby('Tanggal').agg({
        'Durasi': ['count', 'sum']
    }).reset_index()
    daily.columns = ['Date', 'Frekuensi', 'Total_Downtime']
    
    with st.container(border=True):
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Bar for frequency
        fig.add_trace(
            go.Bar(
                x=daily['Date'],
                y=daily['Frekuensi'],
                name='Frekuensi',
                marker_color='rgba(239,68,68,0.7)',
                hovertemplate='<b>%{x|%d %b}</b><br>Frekuensi: %{y:,}<extra></extra>'
            ),
            secondary_y=False
        )
        
        # Line for downtime
        fig.add_trace(
            go.Scatter(
                x=daily['Date'],
                y=daily['Total_Downtime'],
                name='Downtime (jam)',
                line=dict(color='#d4a84b', width=2),
                mode='lines+markers',
                marker=dict(size=4),
                hovertemplate='Downtime: %{y:.1f} jam<extra></extra>'
            ),
            secondary_y=True
        )
        
        fig.update_layout(**get_chart_layout(height=350))
        fig.update_xaxes(tickformat='%d %b', gridcolor='rgba(255,255,255,0.05)')
        fig.update_yaxes(title_text="Frekuensi", secondary_y=False, showgrid=False)
        fig.update_yaxes(title_text="Downtime (jam)", secondary_y=True, gridcolor='rgba(30,58,95,0.3)')
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # ===== ANALYSIS SECTION =====
    st.markdown("""
    <div class="section-divider">
        <div class="section-divider-line"></div>
        <span class="section-divider-text">📊 Analisis Gangguan</span>
        <div class="section-divider-line"></div>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📊 Pareto Analysis", "🔧 Per Alat", "🔄 Per Shift"])
    
    with tab1:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            with st.container(border=True):
                st.markdown("""
                <div style="background: linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%); 
                            border-radius: 12px; padding: 1rem; margin-bottom: 1rem;
                            border: 1px solid rgba(239, 68, 68, 0.3);">
                    <h4 style="color: #ef4444; margin: 0; font-size: 0.9rem;">📊 Pareto Chart - Top 10 Gangguan</h4>
                </div>
                """, unsafe_allow_html=True)
                
                # Pareto data
                gangguan_count = df_filtered.groupby('Gangguan').agg({
                    'Durasi': ['count', 'sum']
                }).reset_index()
                gangguan_count.columns = ['Gangguan', 'Frekuensi', 'Total_Durasi']
                gangguan_count = gangguan_count.sort_values('Frekuensi', ascending=False).head(10)
                
                # Calculate cumulative percentage
                total = gangguan_count['Frekuensi'].sum()
                gangguan_count['Cumulative'] = gangguan_count['Frekuensi'].cumsum() / total * 100 if total > 0 else 0
                
                # Create Pareto chart
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                
                fig.add_trace(
                    go.Bar(
                        x=gangguan_count['Gangguan'],
                        y=gangguan_count['Frekuensi'],
                        name='Frekuensi',
                        marker_color='#ef4444',
                        hovertemplate='<b>%{x}</b><br>Frekuensi: %{y:,}<extra></extra>'
                    ),
                    secondary_y=False
                )
                
                fig.add_trace(
                    go.Scatter(
                        x=gangguan_count['Gangguan'],
                        y=gangguan_count['Cumulative'],
                        name='Kumulatif %',
                        line=dict(color='#d4a84b', width=3),
                        mode='lines+markers',
                        marker=dict(size=8),
                        hovertemplate='Kumulatif: %{y:.1f}%<extra></extra>'
                    ),
                    secondary_y=True
                )
                
                # Add 80% line
                fig.add_hline(y=80, line_dash="dash", line_color="#64748b", 
                              annotation_text="80%", secondary_y=True)
                
                fig.update_layout(**get_chart_layout(height=350))
                fig.update_xaxes(tickangle=45)
                fig.update_yaxes(title_text="Frekuensi", secondary_y=False, showgrid=False)
                fig.update_yaxes(title_text="Kumulatif %", secondary_y=True, 
                                 gridcolor='rgba(30,58,95,0.3)', range=[0, 105])
                
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        with col2:
            with st.container(border=True):
                st.markdown("""
                <div style="background: linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%); 
                            border-radius: 12px; padding: 1rem; margin-bottom: 1rem;
                            border: 1px solid rgba(59, 130, 246, 0.3);">
                    <h4 style="color: #3b82f6; margin: 0; font-size: 0.9rem;">📂 Kelompok Masalah</h4>
                </div>
                """, unsafe_allow_html=True)
                
                kelompok_data = df_filtered.groupby('Kelompok Masalah')['Durasi'].agg(['count', 'sum']).reset_index()
                kelompok_data.columns = ['Kelompok', 'Frekuensi', 'Total_Durasi']
                
                fig = px.pie(
                    kelompok_data, 
                    values='Frekuensi', 
                    names='Kelompok', 
                    hole=0.6,
                    color_discrete_sequence=CHART_SEQUENCE
                )
                fig.update_layout(**get_chart_layout(height=350, show_legend=False))
                fig.update_traces(textposition='inside', textinfo='percent', textfont_size=11,
                                hovertemplate='<b>%{label}</b><br>Frekuensi: %{value:,}<br>%{percent}<extra></extra>')
                
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                
                # Table
                st.dataframe(
                    kelompok_data.sort_values('Frekuensi', ascending=False),
                    use_container_width=True,
                    hide_index=True,
                    height=150
                )
    
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            with st.container(border=True):
                st.markdown("""
                <div style="background: linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%); 
                            border-radius: 12px; padding: 1rem; margin-bottom: 1rem;
                            border: 1px solid rgba(16, 185, 129, 0.3);">
                    <h4 style="color: #10b981; margin: 0; font-size: 0.9rem;">🔧 Top 10 Alat - Frekuensi</h4>
                </div>
                """, unsafe_allow_html=True)
                
                alat_data = df_filtered.groupby('Alat')['Durasi'].agg(['count', 'sum']).reset_index()
                alat_data.columns = ['Alat', 'Frekuensi', 'Total_Durasi']
                alat_data = alat_data.sort_values('Frekuensi', ascending=True).tail(10)
                
                fig = px.bar(
                    alat_data,
                    x='Frekuensi',
                    y='Alat',
                    orientation='h',
                    color='Frekuensi',
                    color_continuous_scale=[[0, '#1e3a5f'], [1, '#10b981']]
                )
                fig.update_layout(**get_chart_layout(height=320, show_legend=False))
                fig.update_coloraxes(showscale=False)
                fig.update_traces(hovertemplate='<b>%{y}</b><br>Frekuensi: %{x:,}<extra></extra>')
                
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        with col2:
            with st.container(border=True):
                st.markdown("""
                <div style="background: linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%); 
                            border-radius: 12px; padding: 1rem; margin-bottom: 1rem;
                            border: 1px solid rgba(245, 158, 11, 0.3);">
                    <h4 style="color: #f59e0b; margin: 0; font-size: 0.9rem;">⏱️ Top 10 Alat - Downtime</h4>
                </div>
                """, unsafe_allow_html=True)
                
                alat_downtime = df_filtered.groupby('Alat')['Durasi'].sum().reset_index()
                alat_downtime.columns = ['Alat', 'Total_Durasi']
                alat_downtime = alat_downtime.sort_values('Total_Durasi', ascending=True).tail(10)
                
                fig = px.bar(
                    alat_downtime,
                    x='Total_Durasi',
                    y='Alat',
                    orientation='h',
                    color='Total_Durasi',
                    color_continuous_scale=[[0, '#1e3a5f'], [1, '#f59e0b']]
                )
                fig.update_layout(**get_chart_layout(height=320, show_legend=False))
                fig.update_coloraxes(showscale=False)
                fig.update_traces(hovertemplate='<b>%{y}</b><br>Downtime: %{x:,.1f} jam<extra></extra>')
                
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    with tab3:
        col1, col2 = st.columns(2)
        
        with col1:
            with st.container(border=True):
                st.markdown("""
                <div style="background: linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%); 
                            border-radius: 12px; padding: 1rem; margin-bottom: 1rem;
                            border: 1px solid rgba(59, 130, 246, 0.3);">
                    <h4 style="color: #3b82f6; margin: 0; font-size: 0.9rem;">🔄 Distribusi per Shift</h4>
                </div>
                """, unsafe_allow_html=True)
                
                shift_data = df_filtered.groupby('Shift')['Durasi'].agg(['count', 'sum']).reset_index()
                shift_data.columns = ['Shift', 'Frekuensi', 'Total_Durasi']
                shift_data['Shift'] = 'Shift ' + shift_data['Shift'].astype(int).astype(str)
                
                fig = px.bar(
                    shift_data,
                    x='Shift',
                    y='Frekuensi',
                    color='Shift',
                    text=shift_data['Frekuensi'].apply(lambda x: f'{x:,}'),
                    color_discrete_sequence=['#3b82f6', '#10b981', '#d4a84b']
                )
                fig.update_layout(**get_chart_layout(height=300, show_legend=False))
                fig.update_traces(textposition='outside')
                
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        with col2:
            with st.container(border=True):
                st.markdown("""
                <div style="background: linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%); 
                            border-radius: 12px; padding: 1rem; margin-bottom: 1rem;
                            border: 1px solid rgba(139, 92, 246, 0.3);">
                    <h4 style="color: #8b5cf6; margin: 0; font-size: 0.9rem;">⏱️ Downtime per Shift</h4>
                </div>
                """, unsafe_allow_html=True)
                
                fig = px.bar(
                    shift_data,
                    x='Shift',
                    y='Total_Durasi',
                    color='Shift',
                    text=shift_data['Total_Durasi'].apply(lambda x: f'{x:,.1f}'),
                    color_discrete_sequence=['#3b82f6', '#10b981', '#d4a84b']
                )
                fig.update_layout(**get_chart_layout(height=300, show_legend=False))
                fig.update_traces(textposition='outside')
                fig.update_yaxes(title_text='Downtime (jam)')
                
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        # Separator
        st.markdown("<hr style='border: none; border-top: 1px solid rgba(255,255,255,0.1); margin: 1.5rem 0;'>", unsafe_allow_html=True)
        
        # Heatmap
        with st.container(border=True):
            st.markdown("""
            <div style="background: linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%); 
                        border-radius: 12px; padding: 1rem; margin-bottom: 1rem;
                        border: 1px solid rgba(239, 68, 68, 0.3);">
                <h4 style="color: #ef4444; margin: 0; font-size: 0.9rem;">🔥 Heatmap: Shift × Kelompok Masalah</h4>
            </div>
            """, unsafe_allow_html=True)
            
            heatmap_data = df_filtered.copy()
            heatmap_data['Shift'] = 'Shift ' + heatmap_data['Shift'].astype(int).astype(str)
            
            pivot = heatmap_data.pivot_table(
                values='Durasi', 
                index='Shift', 
                columns='Kelompok Masalah', 
                aggfunc='count', 
                fill_value=0
            )
            
            if not pivot.empty:
                fig = px.imshow(
                    pivot,
                    color_continuous_scale=[[0, '#0f2744'], [0.3, '#1e3a5f'], [0.6, '#ef4444'], [1, '#fbbf24']],
                    aspect='auto',
                    text_auto=True
                )
                fig.update_layout(**get_chart_layout(height=250, show_legend=False))
                fig.update_traces(textfont=dict(size=12, color='white'))
                
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # ===== DATA TABLE =====
    st.markdown("""
    <div class="section-divider">
        <div class="section-divider-line"></div>
        <span class="section-divider-text">📋 DATA DETAIL</span>
        <div class="section-divider-line"></div>
    </div>
    """, unsafe_allow_html=True)
    
    # Summary bar
    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; padding:0.75rem 1rem; 
                background:linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%); border-radius:8px; margin-bottom:1rem;
                border: 1px solid rgba(100,116,139,0.3);">
        <span style="color:#94a3b8;">Total Records: <strong style="color:#ef4444;">{len(df_filtered):,}</strong></span>
        <span style="color:#94a3b8;">Total Downtime: <strong style="color:#f59e0b;">{total_downtime:,.1f} jam</strong></span>
        <span style="color:#94a3b8;">Avg/Kejadian: <strong style="color:#3b82f6;">{(total_downtime/max(total_incidents,1)*60):,.1f} menit</strong></span>
    </div>
    """, unsafe_allow_html=True)
    
    col_spacer, col_btn = st.columns([5, 1])
    with col_btn:
        # Export all columns from Excel (including Crusher from Nov 2025)
        import io
        buffer = io.BytesIO()
        cols_export = ['Tanggal', 'Bulan', 'Tahun', 'Week', 'Shift', 'Start', 'End', 
                       'Durasi', 'Crusher', 'Alat', 'Remarks', 'Kelompok Masalah', 'Gangguan', 
                       'Info CCR']
        # Prepare data for export
        # User requested: "dari tanggal yang terlama ke tanggal yang terbaru" (Ascending)
        # Fix for TypeError: Create temp columns with enforced types for sorting
        
        try:
            df_for_sort = df_filtered.copy()
            # Create explicit sort columns
            df_for_sort['__sort_date'] = pd.to_datetime(df_for_sort['Tanggal'], errors='coerce')
            df_for_sort['__sort_start'] = df_for_sort['Start'].astype(str)
            
            # Sort
            df_sorted = df_for_sort.sort_values(by=['__sort_date', '__sort_start'], ascending=[True, True])
        except Exception as e:
            # Fallback: Sort by index if specific sort fails
            st.error(f"Sorting error (fallback used): {e}")
            df_sorted = df_filtered.sort_index(ascending=True).copy()
            
        df_export = df_sorted[cols_export].copy()
        
        # Format Date to DD/MM/YYYY
        if 'Tanggal' in df_export.columns:
            df_export['Tanggal'] = pd.to_datetime(df_export['Tanggal']).apply(lambda x: x.strftime('%d/%m/%Y') if pd.notnull(x) else '')
            
        # Format Duration to 2 decimal places
        if 'Durasi' in df_export.columns:
            df_export['Durasi'] = df_export['Durasi'].round(2)
            
        # Ensure Start and End are properly formatted strings
        for col in ['Start', 'End']:
            if col in df_export.columns:
                df_export[col] = df_export[col].astype(str)

        try:
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_export.to_excel(writer, index=False, sheet_name='Gangguan')
            
            st.download_button(
                label="📥 Export Excel",
                data=buffer.getvalue(),
                file_name=f"gangguan_filtered_N{len(df_filtered)}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        except Exception as e:
            st.warning("⚠️ Export tidak tersedia saat ini (Disk Full/Error).")
            print(f"Export Error Gangguan: {e}")
    
    # Show dataframe - ALL columns from Excel with exact headers (including Crusher from Nov 2025)
    cols_show = ['Tanggal', 'Bulan', 'Tahun', 'Week', 'Shift', 'Start', 'End', 
                 'Durasi', 'Crusher', 'Alat', 'Remarks', 'Kelompok Masalah', 'Gangguan', 
                 'Info CCR']
    cols_show = [c for c in cols_show if c in df_filtered.columns]
    
    display_df = df_filtered[cols_show].copy()
    
    # Format tanggal
    if 'Tanggal' in display_df.columns:
        display_df['Tanggal'] = pd.to_datetime(display_df['Tanggal']).dt.strftime('%d/%m/%Y')
    
    # Format durasi
    if 'Durasi' in display_df.columns:
        display_df['Durasi'] = display_df['Durasi'].round(2)
    
    st.dataframe(
        display_df.sort_index(ascending=False),
        use_container_width=True,
        height=450
    )