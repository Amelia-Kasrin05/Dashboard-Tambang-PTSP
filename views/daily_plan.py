# ============================================================
# DAILY PLAN - Interactive Mining Grid Map
# ============================================================
# VERSION: 1.0 - Peta Grid Interaktif dengan Data dari Excel OneDrive

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from PIL import Image
import os
from datetime import datetime, timedelta
import base64

# Import dari config
try:
    from config import ONEDRIVE_LINKS, CACHE_TTL, LOCAL_FILE_NAMES
except ImportError:
    try:
        from config.onedrive import ONEDRIVE_LINKS, CACHE_TTL, LOCAL_FILE_NAMES
    except ImportError:
        ONEDRIVE_LINKS = {}
        CACHE_TTL = 30
        LOCAL_FILE_NAMES = {}

# Import helper dari data_loader
try:
    from utils.data_loader import download_from_onedrive, load_from_local
except ImportError:
    # Fallback functions jika import gagal
    def download_from_onedrive(link, timeout=30):
        return None
    def load_from_local(file_key):
        if file_key not in LOCAL_FILE_NAMES:
            return None
        for file_path in LOCAL_FILE_NAMES[file_key]:
            if os.path.exists(file_path):
                return file_path
        return None


# ============================================================
# KONFIGURASI GRID PETA
# ============================================================

# Grid layout berdasarkan peta (A-P rows, 1-17 columns)
GRID_ROWS = list('ABCDEFGHIJKLMNOP')  # 16 baris
GRID_COLS = list(range(1, 18))         # 17 kolom

# Warna untuk blok penambangan
BLOCK_COLORS = {
    'KRP': 'rgba(0, 150, 255, 0.7)',      # Biru - Karang Putih
    'TJR': 'rgba(255, 80, 80, 0.7)',      # Merah - Tajarang  
    'DEFAULT': 'rgba(255, 200, 0, 0.7)',  # Kuning - Default
}

# Warna untuk jenis material/keterangan
MATERIAL_COLORS = {
    'Batu Kapur': '#4CAF50',
    'Silika': '#2196F3',
    'Clay': '#FF9800',
    'Development': '#9C27B0',
    'Batu Kapur (Bersih)': '#66BB6A',
    'Batu Kapur (Mix)': '#81C784',
}

# Path gambar peta (sesuaikan dengan lokasi di project Anda)
MAP_IMAGE_PATHS = [
    'assets/peta_grid_tambang.jpeg',
    'assets/peta_grid_tambang.jpg',
    'assets/peta_grid_tambang.png',
    'peta_grid_tambang.jpeg',
    'static/peta_grid_tambang.jpeg',
]


# ============================================================
# FUNGSI LOAD DATA DAILY PLAN
# ============================================================

@st.cache_data(ttl=CACHE_TTL)
def load_daily_plan_data():
    """
    Load data daily plan dari Excel (OneDrive atau Local)
    Returns: DataFrame dengan data scheduling
    """
    df = None
    
    # Try OneDrive first
    if ONEDRIVE_LINKS.get("daily_plan"):
        file_buffer = download_from_onedrive(ONEDRIVE_LINKS["daily_plan"])
        if file_buffer:
            try:
                df = pd.read_excel(file_buffer, sheet_name='W22 Scheduling', header=None)
            except Exception as e:
                st.warning(f"Gagal load dari OneDrive: {e}")
    
    # Fallback to local
    if df is None:
        local_path = load_from_local("daily_plan")
        if local_path:
            try:
                df = pd.read_excel(local_path, sheet_name='W22 Scheduling', header=None)
            except Exception as e:
                st.warning(f"Gagal load dari local: {e}")
    
    if df is None:
        return pd.DataFrame()
    
    # Parse data - cari baris header
    header_row = None
    for idx, row in df.iterrows():
        row_values = [str(v).strip() for v in row.values if pd.notna(v)]
        if 'Hari' in row_values or 'Tanggal' in row_values:
            header_row = idx
            break
    
    if header_row is None:
        st.warning("Format Excel tidak dikenali")
        return pd.DataFrame()
    
    # Set header
    df.columns = df.iloc[header_row]
    df = df.iloc[header_row + 1:].reset_index(drop=True)
    
    # Bersihkan nama kolom
    df.columns = [str(col).strip() if pd.notna(col) else f'Col_{i}' 
                  for i, col in enumerate(df.columns)]
    
    # Konversi tanggal
    if 'Tanggal' in df.columns:
        df['Tanggal'] = pd.to_datetime(df['Tanggal'], errors='coerce')
    
    # Filter baris yang punya data Grid
    if 'Grid' in df.columns:
        df = df[df['Grid'].notna() & (df['Grid'].astype(str).str.strip() != '')]
    
    # Konversi Shift ke numeric
    if 'Shift' in df.columns:
        df['Shift'] = pd.to_numeric(df['Shift'], errors='coerce')
    
    return df


def get_available_dates(df):
    """Ambil daftar tanggal unik dari data"""
    if df.empty or 'Tanggal' not in df.columns:
        return []
    dates = df['Tanggal'].dropna().unique()
    return sorted([pd.to_datetime(d) for d in dates])


def get_data_for_date_shift(df, selected_date, selected_shift):
    """Filter data berdasarkan tanggal dan shift"""
    if df.empty:
        return pd.DataFrame()
    
    mask = (df['Tanggal'].dt.date == selected_date.date())
    if selected_shift != "Semua":
        mask &= (df['Shift'] == int(selected_shift))
    
    return df[mask].copy()


# ============================================================
# FUNGSI PARSING GRID
# ============================================================

def parse_grid(grid_str):
    """
    Parse string grid menjadi (row, col)
    Contoh: 'E9' -> ('E', 9), 'M10' -> ('M', 10)
    """
    if not grid_str or pd.isna(grid_str):
        return None, None
    
    grid_str = str(grid_str).strip().upper()
    row = ''
    col = ''
    
    for char in grid_str:
        if char.isalpha():
            row += char
        elif char.isdigit():
            col += char
    
    if row and col:
        try:
            return row[0], int(col)  # Ambil huruf pertama saja
        except:
            return None, None
    return None, None


def grid_to_position(row, col):
    """
    Konversi grid ke posisi x, y untuk plotting
    Berdasarkan layout peta: A=atas, P=bawah, 1=kiri, 17=kanan
    """
    if row not in GRID_ROWS or col not in GRID_COLS:
        return None, None
    
    row_idx = GRID_ROWS.index(row)
    col_idx = GRID_COLS.index(col)
    
    # Normalisasi ke 0-1
    x = (col_idx + 0.5) / len(GRID_COLS)
    y = 1 - (row_idx + 0.5) / len(GRID_ROWS)  # Invert karena y=0 di bawah
    
    return x, y


# ============================================================
# FUNGSI LOAD GAMBAR PETA
# ============================================================

def load_map_image():
    """Load gambar peta sebagai background"""
    for path in MAP_IMAGE_PATHS:
        if os.path.exists(path):
            try:
                return Image.open(path)
            except:
                continue
    return None


def image_to_base64(img):
    """Convert PIL Image ke base64 string"""
    import io
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    return base64.b64encode(buffer.getvalue()).decode()


# ============================================================
# FUNGSI BUAT PETA INTERAKTIF
# ============================================================

def create_interactive_map(df_filtered, map_image=None):
    """
    Buat peta interaktif dengan Plotly
    - Background: gambar peta
    - Overlay: grid aktif dengan info
    """
    
    fig = go.Figure()
    
    # Ukuran peta
    img_width = 1000
    img_height = 700
    
    # Tambah background image jika ada
    if map_image:
        fig.add_layout_image(
            dict(
                source=map_image,
                xref="x",
                yref="y",
                x=0,
                y=1,
                sizex=1,
                sizey=1,
                sizing="stretch",
                opacity=1,
                layer="below"
            )
        )
    
    # Jika tidak ada data, tampilkan peta kosong
    if df_filtered.empty:
        fig.add_annotation(
            x=0.5, y=0.5,
            text="Tidak ada data untuk tanggal/shift yang dipilih",
            showarrow=False,
            font=dict(size=16, color="white"),
            bgcolor="rgba(0,0,0,0.7)",
            borderpad=10
        )
    else:
        # Group data by Grid untuk menghindari duplikasi
        grid_data = {}
        for _, row in df_filtered.iterrows():
            grid = str(row.get('Grid', '')).strip()
            if not grid:
                continue
            
            parsed_row, parsed_col = parse_grid(grid)
            if parsed_row is None:
                continue
            
            key = f"{parsed_row}{parsed_col}"
            if key not in grid_data:
                grid_data[key] = {
                    'row': parsed_row,
                    'col': parsed_col,
                    'blok': row.get('Blok', 'DEFAULT'),
                    'alat_muat': [],
                    'alat_angkut': [],
                    'rom': [],
                    'keterangan': [],
                    'shift': []
                }
            
            # Append data
            if pd.notna(row.get('Alat Muat')):
                grid_data[key]['alat_muat'].append(str(row['Alat Muat']))
            if pd.notna(row.get('Alat Angkut')):
                grid_data[key]['alat_angkut'].append(str(row['Alat Angkut']))
            if pd.notna(row.get('ROM')):
                grid_data[key]['rom'].append(str(row['ROM']))
            if pd.notna(row.get('Keterangan')):
                grid_data[key]['keterangan'].append(str(row['Keterangan']))
            if pd.notna(row.get('Shift')):
                grid_data[key]['shift'].append(int(row['Shift']))
        
        # Plot setiap grid aktif
        for grid_key, data in grid_data.items():
            x, y = grid_to_position(data['row'], data['col'])
            if x is None:
                continue
            
            # Tentukan warna berdasarkan blok
            blok = str(data['blok']).upper().strip()
            if 'KRP' in blok:
                color = BLOCK_COLORS['KRP']
                border_color = 'rgba(0, 100, 200, 1)'
            elif 'TJR' in blok:
                color = BLOCK_COLORS['TJR']
                border_color = 'rgba(200, 50, 50, 1)'
            else:
                color = BLOCK_COLORS['DEFAULT']
                border_color = 'rgba(200, 150, 0, 1)'
            
            # Buat hover text
            alat_muat = ', '.join(set(data['alat_muat'])) or '-'
            alat_angkut = ', '.join(set(data['alat_angkut'])) or '-'
            rom = ', '.join(set(data['rom'])) or '-'
            keterangan = ', '.join(set(data['keterangan'])) or '-'
            shifts = ', '.join([str(s) for s in sorted(set(data['shift']))]) or '-'
            
            hover_text = (
                f"<b>Grid: {grid_key}</b><br>"
                f"Blok: {blok}<br>"
                f"Shift: {shifts}<br>"
                f"─────────────<br>"
                f"Alat Muat: {alat_muat}<br>"
                f"Alat Angkut: {alat_angkut}<br>"
                f"ROM: {rom}<br>"
                f"Keterangan: {keterangan}"
            )
            
            # Tambah marker untuk grid
            fig.add_trace(go.Scatter(
                x=[x],
                y=[y],
                mode='markers+text',
                marker=dict(
                    size=35,
                    color=color,
                    line=dict(width=2, color=border_color),
                    symbol='square'
                ),
                text=grid_key,
                textposition='middle center',
                textfont=dict(size=10, color='white', family='Arial Black'),
                hovertemplate=hover_text + "<extra></extra>",
                name=f"{blok} - {grid_key}"
            ))
            
            # Tambah label alat di bawah grid
            if data['alat_muat']:
                label_text = data['alat_muat'][0][:6]  # Ambil 6 karakter pertama
                fig.add_annotation(
                    x=x, y=y - 0.04,
                    text=f"<b>{label_text}</b>",
                    showarrow=False,
                    font=dict(size=8, color='white'),
                    bgcolor='rgba(0,0,0,0.6)',
                    borderpad=2
                )
    
    # Layout
    fig.update_layout(
        title=dict(
            text="",
            x=0.5,
            font=dict(size=16)
        ),
        xaxis=dict(
            range=[0, 1],
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            fixedrange=True
        ),
        yaxis=dict(
            range=[0, 1],
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            scaleanchor="x",
            scaleratio=0.7,
            fixedrange=True
        ),
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=600,
        hoverlabel=dict(
            bgcolor="rgba(0,0,0,0.8)",
            font_size=12,
            font_family="Arial"
        )
    )
    
    return fig


# ============================================================
# FUNGSI BUAT TABEL RINGKASAN
# ============================================================

def create_summary_table(df_filtered):
    """Buat tabel ringkasan aktivitas"""
    if df_filtered.empty:
        return None
    
    # Kolom yang ditampilkan
    display_cols = ['Shift', 'Blok', 'Grid', 'Alat Muat', 'Alat Angkut', 'ROM', 'Keterangan']
    available_cols = [c for c in display_cols if c in df_filtered.columns]
    
    if not available_cols:
        return None
    
    return df_filtered[available_cols].fillna('-')


# ============================================================
# FUNGSI UTAMA - SHOW DAILY PLAN
# ============================================================

def show_daily_plan():
    """Render halaman Daily Plan dengan peta interaktif"""
    
    # Header
    st.markdown("""
    <div class="page-header">
        <div class="page-header-icon">🗺️</div>
        <div class="page-header-text">
            <h1>Daily Plan - Peta Grid Tambang</h1>
            <p>Visualisasi rencana harian penambangan per grid</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data
    with st.spinner("Memuat data dari Excel..."):
        df = load_daily_plan_data()
    
    if df.empty:
        st.error("❌ Data Daily Plan tidak ditemukan. Pastikan file DAILY_PLAN.xlsx tersedia di OneDrive.")
        st.info("""
        **Checklist:**
        1. File `DAILY_PLAN.xlsx` ada di folder OneDrive/Dashboard_Tambang
        2. Sheet bernama `W22 Scheduling` 
        3. Kolom: Hari, Tanggal, Shift, Blok, Grid, Alat Muat, Alat Angkut, ROM, Keterangan
        """)
        return
    
    # Ambil daftar tanggal
    available_dates = get_available_dates(df)
    
    if not available_dates:
        st.warning("⚠️ Tidak ada data tanggal yang valid dalam file Excel")
        return
    
    # ============================================================
    # FILTER SECTION
    # ============================================================
    
    col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
    
    with col1:
        # Date picker
        min_date = min(available_dates).date()
        max_date = max(available_dates).date()
        selected_date = st.date_input(
            "📅 Pilih Tanggal",
            value=max_date,
            min_value=min_date,
            max_value=max_date,
            help="Pilih tanggal untuk melihat rencana harian"
        )
    
    with col2:
        # Shift selector
        shift_options = ["Semua", "1", "2", "3"]
        selected_shift = st.selectbox(
            "⏰ Shift",
            options=shift_options,
            help="Filter berdasarkan shift"
        )
    
    with col3:
        # Refresh button
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    with col4:
        # Info tanggal data
        st.markdown(f"""
        <div style="background: rgba(212,168,75,0.1); padding: 10px; border-radius: 8px; border-left: 3px solid #d4a84b;">
            <small style="color: #94a3b8;">Data tersedia:</small><br>
            <strong style="color: #f1f5f9;">{min_date.strftime('%d %b %Y')} - {max_date.strftime('%d %b %Y')}</strong>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ============================================================
    # FILTER DATA
    # ============================================================
    
    selected_datetime = pd.to_datetime(selected_date)
    df_filtered = get_data_for_date_shift(df, selected_datetime, selected_shift)
    
    # ============================================================
    # KPI CARDS
    # ============================================================
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    with kpi1:
        total_grid = df_filtered['Grid'].nunique() if not df_filtered.empty else 0
        st.markdown(f"""
        <div class="kpi-card" style="--card-accent: #3b82f6;">
            <div class="kpi-icon">📍</div>
            <div class="kpi-label">Grid Aktif</div>
            <div class="kpi-value">{total_grid}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi2:
        total_alat = df_filtered['Alat Muat'].nunique() if not df_filtered.empty and 'Alat Muat' in df_filtered.columns else 0
        st.markdown(f"""
        <div class="kpi-card" style="--card-accent: #10b981;">
            <div class="kpi-icon">🚜</div>
            <div class="kpi-label">Alat Muat</div>
            <div class="kpi-value">{total_alat}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi3:
        krp_count = len(df_filtered[df_filtered['Blok'].astype(str).str.upper().str.contains('KRP', na=False)]) if not df_filtered.empty and 'Blok' in df_filtered.columns else 0
        st.markdown(f"""
        <div class="kpi-card" style="--card-accent: #3b82f6;">
            <div class="kpi-icon">🔵</div>
            <div class="kpi-label">Aktivitas KRP</div>
            <div class="kpi-value">{krp_count}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi4:
        tjr_count = len(df_filtered[df_filtered['Blok'].astype(str).str.upper().str.contains('TJR', na=False)]) if not df_filtered.empty and 'Blok' in df_filtered.columns else 0
        st.markdown(f"""
        <div class="kpi-card" style="--card-accent: #ef4444;">
            <div class="kpi-icon">🔴</div>
            <div class="kpi-label">Aktivitas TJR</div>
            <div class="kpi-value">{tjr_count}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ============================================================
    # PETA DAN TABEL
    # ============================================================
    
    tab1, tab2 = st.tabs(["🗺️ Peta Grid", "📋 Tabel Detail"])
    
    with tab1:
        st.markdown("""
        <div class="chart-container">
            <div class="chart-header">
                <span class="chart-title">📍 Peta Lokasi Penambangan</span>
                <span class="chart-badge">LIVE</span>
            </div>
        """, unsafe_allow_html=True)
        
        # Load gambar peta
        map_img = load_map_image()
        if map_img:
            map_source = f"data:image/jpeg;base64,{image_to_base64(map_img)}"
        else:
            map_source = None
            st.info("💡 Gambar peta tidak ditemukan. Letakkan file `peta_grid_tambang.jpeg` di folder `assets/`")
        
        # Buat peta interaktif
        fig = create_interactive_map(df_filtered, map_source)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        # Legend
        st.markdown("""
        <div style="display: flex; gap: 20px; justify-content: center; margin-top: 10px;">
            <div style="display: flex; align-items: center; gap: 5px;">
                <div style="width: 20px; height: 20px; background: rgba(0,150,255,0.7); border: 2px solid rgba(0,100,200,1);"></div>
                <span style="color: #94a3b8; font-size: 12px;">KRP (Karang Putih)</span>
            </div>
            <div style="display: flex; align-items: center; gap: 5px;">
                <div style="width: 20px; height: 20px; background: rgba(255,80,80,0.7); border: 2px solid rgba(200,50,50,1);"></div>
                <span style="color: #94a3b8; font-size: 12px;">TJR (Tajarang)</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with tab2:
        st.markdown("""
        <div class="chart-container">
            <div class="chart-header">
                <span class="chart-title">📋 Detail Rencana Harian</span>
            </div>
        """, unsafe_allow_html=True)
        
        summary_df = create_summary_table(df_filtered)
        if summary_df is not None and not summary_df.empty:
            st.dataframe(
                summary_df,
                use_container_width=True,
                hide_index=True,
                height=400
            )
            
            # Download button
            csv = summary_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"daily_plan_{selected_date}.csv",
                mime="text/csv"
            )
        else:
            st.info("Tidak ada data untuk ditampilkan")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # ============================================================
    # FOOTER INFO
    # ============================================================
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="text-align: center; color: #64748b; font-size: 12px;">
        Data diperbarui otomatis dari OneDrive setiap {CACHE_TTL} detik<br>
        Klik tombol Refresh untuk memuat data terbaru
    </div>
    """, unsafe_allow_html=True)