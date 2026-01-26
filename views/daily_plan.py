# ============================================================
# DAILY PLAN - Interactive Mining Map Visualization
# ============================================================
# Displays daily plan from Excel with excavator positions on satellite map
# Layout matches reference image: map + data table + legend

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import os
import base64
from PIL import Image

# Import grid coordinates
try:
    from config.grid_coords import get_grid_position, get_zone_color, MAP_WIDTH, MAP_HEIGHT
except ImportError:
    MAP_WIDTH, MAP_HEIGHT = 1400, 990
    def get_grid_position(g, b=None): return None
    def get_zone_color(b): return '#00BFFF'

# Import data loader as fallback
try:
    from utils.data_loader import load_daily_plan as load_daily_plan_fallback
except ImportError:
    def load_daily_plan_fallback(): return pd.DataFrame()

# File paths
ONEDRIVE_FILE = r"C:\Users\user\OneDrive\Dashboard_Tambang\DAILY_PLAN.xlsx"
MAP_IMAGE_PATH = r"D:\Dashboard-Tambang-PTSP\assets\peta_grid_tambang_opt.jpg"

# ============================================================
# DATA LOADER
# ============================================================

@st.cache_data(ttl=5)  # Reduced TTL to force frequent reload
def load_daily_plan_data():
    """Load daily plan data from OneDrive Excel file"""
    df = None
    
    # Try to read directly from OneDrive file first
    try:
        if os.path.exists(ONEDRIVE_FILE):
            # Read with header=2 (row 3 contains the actual headers)
            # CRITICAL FIX: Skip first column (column 0) which is empty/row numbers
            # Read all columns EXCEPT the first one to prevent column misalignment
            df = pd.read_excel(ONEDRIVE_FILE, sheet_name='W22 Scheduling', header=2, usecols=lambda x: x != 'Unnamed: 0')

            
    except PermissionError:
        st.warning("⚠️ File Excel sedang dibuka. Silakan tutup Excel dan refresh halaman.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error membaca file: {e}")
        # Try fallback
        df = load_daily_plan_fallback()
    
    if df is None or df.empty:
        # Try fallback
        df = load_daily_plan_fallback()
        if df is not None and not df.empty:
            # Standardize column names from fallback
            col_mapping = {
                'Batu Kapur': 'Batu Kapur',
                'Alat Muat': 'Alat Muat',
                'Alat Angkut': 'Alat Angkut'
            }
            df = df.rename(columns=col_mapping)
    
    if df is None or df.empty:
        return pd.DataFrame()
    
    try:
        # Indonesian day names mapping
        day_names_id = {
            0: 'Senin',    # Monday
            1: 'Selasa',   # Tuesday
            2: 'Rabu',     # Wednesday
            3: 'Kamis',    # Thursday
            4: 'Jumat',    # Friday
            5: 'Sabtu',    # Saturday
            6: 'Minggu'    # Sunday
        }
        
        # Parse dates first (needed for Hari conversion)
        if 'Tanggal' in df.columns:
            df['Tanggal'] = pd.to_datetime(df['Tanggal'], errors='coerce')
        
        # Fix Hari column - handle both string day names and datetime values
        if 'Hari' in df.columns:
            def convert_hari(val, tanggal_val=None):
                """Convert Hari value to proper day name"""
                if pd.isna(val):
                    # If Hari is empty, derive from Tanggal
                    if pd.notna(tanggal_val):
                        try:
                            return day_names_id[pd.to_datetime(tanggal_val).dayofweek]
                        except:
                            return ''
                    return ''
                
                val_str = str(val).strip()
                
                # Check if it's already a valid day name
                if val_str in ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']:
                    return val_str
                
                # Check if it looks like a datetime (contains date pattern)
                if '-' in val_str and len(val_str) > 8:
                    try:
                        dt = pd.to_datetime(val_str)
                        return day_names_id[dt.dayofweek]
                    except:
                        pass
                
                # Return cleaned value
                return val_str
            
            # Apply conversion with Tanggal as fallback
            if 'Tanggal' in df.columns:
                df['Hari'] = df.apply(lambda row: convert_hari(row['Hari'], row['Tanggal']), axis=1)
            else:
                df['Hari'] = df['Hari'].apply(convert_hari)
        
        # Keep Shift as is (clean string)
        if 'Shift' in df.columns:
            df['Shift'] = df['Shift'].astype(str).str.strip()
            # Remove rows where Shift is 'nan' or empty
            df = df[df['Shift'].notna() & (df['Shift'] != 'nan') & (df['Shift'] != '')]
        
        # Filter valid rows (has date or equipment or grid)
        valid_cols = ['Tanggal', 'Grid', 'Alat Muat', 'Blok']
        mask = pd.Series(False, index=df.index)
        for col in valid_cols:
            if col in df.columns:
                mask = mask | df[col].notna()
        df = df[mask]
        
        # Remove header rows that got included
        if 'Hari' in df.columns:
            df = df[df['Hari'] != 'Hari']
        if 'Shift' in df.columns:
            df = df[df['Shift'] != 'Shift']
        
        # Reset index
        df = df.reset_index(drop=True)
        
        return df
        
    except Exception as e:
        st.error(f"Error processing Daily Plan: {e}")
        return pd.DataFrame()



def get_image_base64(image_path):
    """Convert image to base64 for Plotly"""
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return None


# ============================================================
# MAP VISUALIZATION
# ============================================================

def create_mining_map(df_filtered, selected_date, selected_shifts_label):
    """
    Create the mining map with strict logic matching user requirements:
    1. Filter: Must have Tanggal, Shift, Alat Muat, Alat Angkut, ROM, and (Grid or Blok)
    2. Location: Grid > Blok. Custom: SP6 (no grid) -> Top Left, SP3 -> K3
    3. Grouping: Same Location, Equipment, ROM -> Merge Shifts
    4. Format: 3 lines (Equipment, Shift, ROM) in Blue Box
    """
    
    # Get image as base64
    img_base64 = get_image_base64(MAP_IMAGE_PATH)
    
    if not img_base64:
        return None
    
    # Create figure
    fig = go.Figure()
    
    # Add background map image
    fig.add_layout_image(
        dict(
            source=f"data:image/jpeg;base64,{img_base64}",
            xref="x",
            yref="y",
            x=0,
            y=MAP_HEIGHT,
            sizex=MAP_WIDTH,
            sizey=MAP_HEIGHT,
            sizing="stretch",
            opacity=1,
            layer="below"
        )
    )
    
    # ------------------------------------------------------------
    # 1. FILTERING DATA
    # ------------------------------------------------------------
    if df_filtered.empty:
        return fig

    # Filter rules:
    # - Must have: Tanggal, Shift, Alat Muat, Alat Angkut, ROM
    # - Must have Grid OR Blok
    mask = (
        df_filtered['Tanggal'].notna() &
        df_filtered['Shift'].notna() & df_filtered['Shift'].astype(str).str.strip().ne('') &
        df_filtered['Alat Muat'].notna() &
        df_filtered['Alat Angkut'].notna() &
        df_filtered['ROM'].notna() &
        (df_filtered['Grid'].notna() | df_filtered['Blok'].notna())
    )
    df_map = df_filtered[mask].copy()
    
    if df_map.empty:
        return fig

    # ------------------------------------------------------------
    # 2. DETERMINE LOCATION ID (MAPPING)
    # ------------------------------------------------------------
    def resolve_location_id(row):
        grid = str(row['Grid']).strip() if pd.notna(row['Grid']) else ''
        blok = str(row['Blok']).strip().upper() if pd.notna(row['Blok']) else ''
        
        # Rule: Jika Grid terisi -> lokasi_id = Grid
        if grid and grid.lower() != 'nan':
            return grid
        
        # Rule: Jika Grid kosong dan Blok terisi -> lokasi_id = Blok
        if blok and blok.lower() != 'nan':
            # Mapping Khusus: Blok SP6 -> Grid K3
            if blok == 'SP6':
                return 'K3'
            # SP3 tetap SP3 (nanti dihandle get_grid_position)
            return blok
        
        return None

    df_map['lokasi_id'] = df_map.apply(resolve_location_id, axis=1)
    # Remove rows where location couldn't be resolved
    df_map = df_map[df_map['lokasi_id'].notna()]

    # ------------------------------------------------------------
    # 3. GROUPING
    # ------------------------------------------------------------
    # Gabungkan baris jika sama pada: Tanggal, lokasi_id, Alat Muat, Alat Angkut, ROM
    # (Note: Filter Tanggal already applied upstream or in mask, assuming df_filtered is usually single day or we group by date too)
    
    # Group fields
    # USER REQUEST: Merge same equipment labels. Removed 'ROM' from grouping keys.
    group_cols = ['lokasi_id', 'Alat Muat', 'Alat Angkut']
    if 'Tanggal' in df_map.columns:
         group_cols.insert(0, 'Tanggal')

    # Aggregation: Shift AND ROM -> Combine unique sorted
    grouped = df_map.groupby(group_cols).agg({
        'Shift': 'unique',
        'ROM': 'unique'
    }).reset_index()

    # ------------------------------------------------------------
    # 4. PLOTTING & FORMATTING
    # ------------------------------------------------------------
    
    # Track offset for collision handling
    # Key: "x_y" -> count
    offset_counter = {}

    for _, row in grouped.iterrows():
        loc_id = row['lokasi_id']
        alat_muat = row['Alat Muat']
        alat_angkut = row['Alat Angkut']
        rom_list = row['ROM'] # Now an array/list
        shifts = row['Shift']
        
        # Get Coordinates
        x, y = None, None
        
        if loc_id == 'SP3':
            # SP3 in Top Left Corner - FORCE POSITION overrides
            pos = get_grid_position(loc_id, loc_id)
            if pos:
                x, y = pos
        else:
            # Use standard mapping
            pos = get_grid_position(loc_id)
            if pos:
                x, y = pos
        
        if x is None or y is None:
            continue
            
        # Flip Y for plotting
        y_plot = MAP_HEIGHT - y
        
        # Format Text
        # Line 1: <Alat Muat> + <Alat Angkut>
        line1 = f"<b>{alat_muat} + {alat_angkut}</b>"
        
        # Line 2: Shift <hasil gabungan>
        try:
            sorted_shifts = sorted(shifts, key=lambda x: int(str(x)) if str(x).isdigit() else str(x))
        except:
            sorted_shifts = sorted(shifts.astype(str))
            
        shift_str = " & ".join([str(s) for s in sorted_shifts])
        line2 = f"Shift {shift_str}"
        
        # Line 3: LS> <ROM> (Combined)
        # Filter empty ROMs just in case
        valid_roms = [str(r) for r in rom_list if pd.notna(r) and str(r).strip() not in ['', 'nan', 'None']]
        # Unique ROMs only (set) then sort
        unique_roms = sorted(list(set(valid_roms)))
        
        rom_str = " & ".join(unique_roms)
        line3 = f"LS> {rom_str}"
        
        # Combined Box Text
        box_text = f"{line1}<br>{line2}<br>{line3}"
        
        # --------------------------------------------------------
        # NATURAL OFFSET LOGIC WITH BOUNDARY CLAMPING
        # --------------------------------------------------------
        
        target_x, target_y = x, y_plot
        
        # Determine Direction preference
        
        # SPECIAL OVERRIDES
        if loc_id == 'N8':
            direction = -1 # Force LEFT for N8 as requested
            
        # GENERAL LOGIC
        elif x < 100: direction = 1
        elif x > MAP_WIDTH - 100: direction = -1
        else: 
            # User requested Grid 7+ (A7..P7, x approx 437) to face RIGHT.
            # Grid 6 is x approx 390.
            # So split at 410 ensures Col 1-6 (Space for SP6/K3) are LEFT, and Col 7+ are RIGHT.
            direction = -1 if x < 410 else 1
        
        # Calculate Label Position
        # Reduced offset to keep labels tieter and fit better
        offset_dist = 120 
        label_x = x + (direction * offset_dist)
        
        # CLAMP X to be inside map
        # Reduced box width to 100px (half 50) + Margin 10 = 60
        BOX_HALF_WIDTH = 50 
        X_MARGIN = 10
        MIN_X = BOX_HALF_WIDTH + X_MARGIN     # 60
        MAX_X = MAP_WIDTH - BOX_HALF_WIDTH - X_MARGIN # 1340
        
        if label_x < MIN_X: label_x = MIN_X
        if label_x > MAX_X: label_x = MAX_X
        
        # Vertical Stacking Logic
        y_bucket = round(y_plot / 50) * 50
        y_key = f"{direction}_{y_bucket}"
        
        offset_counter[y_key] = offset_counter.get(y_key, 0) + 1
        stack_idx = offset_counter[y_key] - 1
        
        # Default Y behavior
        label_y = y_plot - (stack_idx * 55)
        
        # SPECIAL HANDLING FOR CORNERS (e.g. SP3 Top Left)
        if y_plot > MAP_HEIGHT - 100: # Very close to TOP
             # Force label DOWN
             label_y = y_plot - 80 - (stack_idx * 55)
             
        # Clamp Y
        # Box height approx 50-60px -> Half height 30px -> Buffer 10px
        Y_MARGIN = 10
        BOX_HALF_HEIGHT = 30 
        
        MIN_Y = BOX_HALF_HEIGHT + Y_MARGIN
        MAX_Y = MAP_HEIGHT - BOX_HALF_HEIGHT - Y_MARGIN
        
        if label_y < MIN_Y: label_y = MIN_Y
        if label_y > MAX_Y: label_y = MAX_Y
        
        # Elbow Path construction
        elbow_x = x + (direction * 30) # Short stub reduced
        
        # Path: Dot -> Stub -> Vertical -> Label
        path_svg = f"M {target_x},{target_y} L {elbow_x},{target_y} L {elbow_x},{label_y} L {label_x},{label_y}"
        
        # Draw Elbow Line (Blue)
        fig.add_shape(
            type="path",
            path=path_svg,
            line=dict(color='#00BFFF', width=2),
            layer="above"
        )
        
        # Add Annotation Box
        fig.add_annotation(
            x=label_x,
            y=label_y, 
            text=box_text,
            showarrow=False, 
            bgcolor='#00BFFF', 
            bordercolor='white',
            borderwidth=1,
            borderpad=4,
            # Reduced font size to 8 as requested
            font=dict(size=8, color='black', family='Arial, sans-serif'),
            opacity=1.0, 
            align='center',
            captureevents=True,
            width=100
        )
        
        # Add Marker Dot
        fig.add_trace(go.Scatter(
            x=[target_x],
            y=[target_y],
            mode='markers',
            marker=dict(size=10, color='#00BFFF', line=dict(color='white', width=2)),
            hoverinfo='skip',
            showlegend=False
        ))
    
    # Configure layout
    fig.update_layout(
        xaxis=dict(range=[-20, MAP_WIDTH + 20], showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(range=[-20, MAP_HEIGHT + 20], showgrid=False, zeroline=False, showticklabels=False, scaleanchor="x", scaleratio=1),
        margin=dict(l=0, r=0, t=0, b=0),
        height=1000,
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        dragmode='pan'
    )
    
    return fig


def create_data_table(df_filtered):
    """Create data table with ALL columns from Excel"""
    # Only keep relevant columns and formatting
    cols = ['Hari', 'Tanggal', 'Shift', 'Batu Kapur', 'Silika', 'Clay', 'Alat Muat', 'Alat Angkut', 'Blok', 'Grid', 'ROM', 'Keterangan']
    # Filter columns that exist
    cols = [c for c in cols if c in df_filtered.columns]
    
    display_df = df_filtered[cols].copy()
    
    # Format date
    if 'Tanggal' in display_df.columns:
        display_df['Tanggal'] = pd.to_datetime(display_df['Tanggal']).dt.strftime('%d-%m-%Y')
        
    return display_df


def show_daily_plan():
    # ... header setup ...
    st.markdown("""
    <style>
    .date-header {
        font-size: 24px;
        font-weight: bold;
        color: white;
        text-align: center;
        background: #1a1a2e;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        border: 1px solid #333;
    }
    </style>
    """, unsafe_allow_html=True)
    
    active_filters = {}
    
    # Load data
    df = load_daily_plan_data()
    if df is None:
        st.error("Gagal memuat data Daily Plan.")
        return

    # Sidebar Filters (Re-integrated cleanly if needed, assuming existing code handles it)
    # ...
    
    # Processing Logic (Simplified for replacement context)
    # ...
    # Assume we have filtered df -> df_filtered, selected_date, selected_shifts etc.
    
    # For replacement, we need to match the View rendering block
    
    return # Placeholder



# ============================================================
# DATA TABLE
# ============================================================
# ... (create_data_table function stays same) ...


# ============================================================
# MAIN VIEW
# ============================================================

def show_daily_plan():
    # ... (header code same) ... 
    
    # Load data
    df = load_daily_plan_data()
    # ... (error handling same) ...
    
    # ... (header html removed or kept minimal) ...
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                padding: 20px; border-radius: 12px; margin-bottom: 20px;
                border-left: 4px solid #00D4FF;">
        <h1 style="margin: 0; color: white; font-size: 28px;">
            🗺️ Daily Plan - Peta Penambangan
        </h1>
    </div>
    """, unsafe_allow_html=True)
    
    # ... (filters code same) ... (omitted for brevity, assume filters exist)
    # Re-inserting filters section and processing logic would be huge diff
    # I will focus replacing the MAP DISPLAY part below
    
    # ... (apply filters logic same) ...



# ============================================================
# DATA TABLE
# ============================================================

def create_data_table(df_filtered):
    """Create data table with ALL columns from Excel"""
    if df_filtered.empty:
        return pd.DataFrame()
    
    # Show ALL relevant columns from Excel (using exact Excel column names)
    cols_to_show = ['Hari', 'Tanggal', 'Shift', 'Batu Kapur', 'Silika', 'Clay',
                    'Alat Muat', 'Alat Angkut', 'Blok', 'Grid', 'ROM', 'Keterangan']
    
    # Only include columns that exist in dataframe
    available_cols = [col for col in cols_to_show if col in df_filtered.columns]
    display_df = df_filtered[available_cols].copy()
    
    # Format Tanggal if present
    if 'Tanggal' in display_df.columns:
        display_df['Tanggal'] = pd.to_datetime(display_df['Tanggal'], errors='coerce').dt.strftime('%Y-%m-%d')
    
    # Format numerical columns
    for col in ['Batu Kapur', 'Silika', 'Clay']:
        if col in display_df.columns:
            # Convert to numeric and format
            display_df[col] = pd.to_numeric(display_df[col], errors='coerce')
            # Replace NaN with empty string for display
            display_df[col] = display_df[col].apply(lambda x: '' if pd.isna(x) else f'{int(x):,}' if x == int(x) else f'{x:,.1f}')
    
    return display_df


# ============================================================
# MAIN VIEW
# ============================================================

def show_daily_plan():
    """Render Daily Plan Dashboard with professional multi-select filters"""
    
    # Load data
    df = load_daily_plan_data()
    
    if df.empty:
        st.warning("⚠️ Data Daily Plan tidak tersedia. Pastikan file Excel tidak sedang dibuka.")
        return
    
    # ============================================================
    # HEADER
    # ============================================================
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                padding: 20px; border-radius: 12px; margin-bottom: 20px;
                border-left: 4px solid #00D4FF;">
        <h1 style="margin: 0; color: white; font-size: 28px;">
            🗺️ Daily Plan - Peta Penambangan
        </h1>
        <p style="margin: 5px 0 0 0; color: #B0B0B0; font-size: 14px;">
            Visualisasi rencana harian penambangan bahan baku
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # DEBUG: Show data sample
    with st.expander("🔧 Debug Info - Klik untuk lihat"):
        st.write("**Kolom Hari (5 baris pertama):**")
        if 'Hari' in df.columns:
            st.write(df['Hari'].head().tolist())
            st.write(f"Tipe data: {df['Hari'].dtype}")
        st.write("\n**Kolom Tanggal (5 baris pertama):**")
        if 'Tanggal' in df.columns:
            st.write(df['Tanggal'].head().tolist())
        st.write(f"\n**Total rows:** {len(df)}")
        st.write(f"**Kolom:** {df.columns.tolist()}")

    
    # ============================================================
    # FILTERS SECTION
    # ============================================================
    st.markdown("""
    <div style="background: #1a1a2e; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
        <h3 style="margin: 0 0 10px 0; color: #00D4FF; font-size: 16px;">🔍 Filter Data</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Get unique values for filters
    available_dates = sorted(df['Tanggal'].dropna().dt.date.unique(), reverse=True)
    available_shifts = sorted(df['Shift'].dropna().unique().astype(str).tolist())
    available_blok = sorted([str(b) for b in df['Blok'].dropna().unique() if pd.notna(b)])
    available_alat = sorted([str(a) for a in df['Alat Muat'].dropna().unique() if pd.notna(a)])
    available_hari = sorted([str(h) for h in df['Hari'].dropna().unique() if pd.notna(h)])
    available_grid = sorted([str(g) for g in df['Grid'].dropna().unique() if pd.notna(g)])
    
    # Filter row - MORE FILTERS
    filter_cols = st.columns([2, 2, 2, 2, 1])
    
    with filter_cols[0]:
        st.markdown("**📅 Tanggal**")
        if len(available_dates) > 0:
            selected_date = st.date_input(
                "Tanggal",
                value=available_dates[0],
                min_value=min(available_dates),
                max_value=max(available_dates),
                key='dp_date',
                label_visibility="collapsed"
            )
        else:
            selected_date = datetime.now().date()
    
    with filter_cols[1]:
        st.markdown("**⏰ Shift**")
        shift_options = ['Semua'] + available_shifts
        selected_shifts = st.multiselect(
            "Shift",
            options=shift_options,
            default=['Semua'],
            key='dp_shift',
            label_visibility="collapsed"
        )
        if len(selected_shifts) == 0:
            selected_shifts = ['Semua']
    
    with filter_cols[2]:
        st.markdown("**📍 Blok**")
        blok_options = ['Semua'] + available_blok
        selected_bloks = st.multiselect(
            "Blok",
            options=blok_options,
            default=['Semua'],
            key='dp_blok',
            label_visibility="collapsed"
        )
        if len(selected_bloks) == 0:
            selected_bloks = ['Semua']
    
    with filter_cols[3]:
        st.markdown("**🚜 Alat Muat**")
        alat_options = ['Semua'] + available_alat
        selected_alat = st.multiselect(
            "Alat Muat",
            options=alat_options,
            default=['Semua'],
            key='dp_alat',
            label_visibility="collapsed"
        )
        if len(selected_alat) == 0:
            selected_alat = ['Semua']
    
    with filter_cols[4]:
        st.markdown("**🔄 Refresh**")
        if st.button("🔄 Refresh", use_container_width=True, key='dp_refresh'):
            st.cache_data.clear()
            st.rerun()
    
    # Second row of filters
    filter_cols2 = st.columns([2, 2, 2, 2, 2, 1])
    
    with filter_cols2[0]:
        st.markdown("**📅 Hari**")
        hari_options = ['Semua'] + available_hari
        selected_hari = st.multiselect(
            "Hari",
            options=hari_options,
            default=['Semua'],
            key='dp_hari',
            label_visibility="collapsed"
        )
        if len(selected_hari) == 0:
            selected_hari = ['Semua']
    
    with filter_cols2[1]:
        st.markdown("**📍 Grid**")
        grid_options = ['Semua'] + available_grid[:20]  # Limit to first 20
        selected_grids = st.multiselect(
            "Grid",
            options=grid_options,
            default=['Semua'],
            key='dp_grid',
            label_visibility="collapsed"
        )
        if len(selected_grids) == 0:
            selected_grids = ['Semua']
    
    with filter_cols2[2]:
        st.markdown("**🪨 Material**")
        material_options = ['Semua', 'Batu Kapur', 'Silika', 'Clay']
        selected_material = st.multiselect(
            "Material",
            options=material_options,
            default=['Semua'],
            key='dp_material',
            label_visibility="collapsed"
        )
    
    # ============================================================
    # APPLY FILTERS
    # ============================================================
    df_filtered = df.copy()
    
    # Date filter
    if 'Tanggal' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['Tanggal'].dt.date == selected_date]
    
    # Shift filter
    if selected_shifts and 'Semua' not in selected_shifts:
        df_filtered = df_filtered[df_filtered['Shift'].astype(str).isin(selected_shifts)]
    
    # Blok filter
    if selected_bloks and 'Semua' not in selected_bloks and 'Blok' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['Blok'].astype(str).isin(selected_bloks)]
    
    # Hari filter
    if selected_hari and 'Semua' not in selected_hari and 'Hari' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['Hari'].astype(str).isin(selected_hari)]
    
    # Grid filter
    if selected_grids and 'Semua' not in selected_grids and 'Grid' in df_filtered.columns:
        # Convert both to string for comparison and handle potential NaNs
        df_filtered = df_filtered[df_filtered['Grid'].fillna('').astype(str).isin(selected_grids)]
    
    # Alat Muat filter
    if selected_alat and 'Semua' not in selected_alat and 'Alat Muat' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['Alat Muat'].astype(str).isin(selected_alat)]
    
    # Material filter
    if 'Semua' not in selected_material and selected_material:

        material_mask = pd.Series(False, index=df_filtered.index)
        for mat in selected_material:
            if mat == 'Batu Kapur' and 'Batu Kapur' in df_filtered.columns:
                material_mask = material_mask | df_filtered['Batu Kapur'].notna()
            elif mat == 'Silika' and 'Silika' in df_filtered.columns:
                material_mask = material_mask | df_filtered['Silika'].notna()
            elif mat == 'Clay' and 'Clay' in df_filtered.columns:
                material_mask = material_mask | df_filtered['Clay'].notna()
        df_filtered = df_filtered[material_mask]
    
    # ============================================================
    # KPI METRICS
    # ============================================================
    st.markdown("---")
    
    kpi_cols = st.columns(5)
    
    with kpi_cols[0]:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #00D4FF22, #00D4FF11); 
                    padding: 15px; border-radius: 10px; text-align: center;
                    border: 1px solid #00D4FF44;">
            <div style="font-size: 28px; font-weight: bold; color: #00D4FF;">{}</div>
            <div style="font-size: 12px; color: #B0B0B0;">Total Operasi</div>
        </div>
        """.format(len(df_filtered)), unsafe_allow_html=True)
    
    with kpi_cols[1]:
        active_exc = df_filtered['Alat Muat'].dropna().nunique()
        st.markdown("""
        <div style="background: linear-gradient(135deg, #FFD70022, #FFD70011); 
                    padding: 15px; border-radius: 10px; text-align: center;
                    border: 1px solid #FFD70044;">
            <div style="font-size: 28px; font-weight: bold; color: #FFD700;">{}</div>
            <div style="font-size: 12px; color: #B0B0B0;">Excavator Aktif</div>
        </div>
        """.format(active_exc), unsafe_allow_html=True)
    
    with kpi_cols[2]:
        active_grids = df_filtered['Grid'].dropna().nunique()
        st.markdown("""
        <div style="background: linear-gradient(135deg, #00FF8822, #00FF8811); 
                    padding: 15px; border-radius: 10px; text-align: center;
                    border: 1px solid #00FF8844;">
            <div style="font-size: 28px; font-weight: bold; color: #00FF88;">{}</div>
            <div style="font-size: 12px; color: #B0B0B0;">Lokasi Aktif</div>
        </div>
        """.format(active_grids), unsafe_allow_html=True)
    
    with kpi_cols[3]:
        krp_count = len(df_filtered[df_filtered['Blok'].astype(str).str.upper() == 'KRP']) if 'Blok' in df_filtered.columns else 0
        st.markdown("""
        <div style="background: linear-gradient(135deg, #00BFFF22, #00BFFF11); 
                    padding: 15px; border-radius: 10px; text-align: center;
                    border: 1px solid #00BFFF44;">
            <div style="font-size: 28px; font-weight: bold; color: #00BFFF;">{}</div>
            <div style="font-size: 12px; color: #B0B0B0;">KRP (Kapur)</div>
        </div>
        """.format(krp_count), unsafe_allow_html=True)
    
    with kpi_cols[4]:
        tjr_count = len(df_filtered[df_filtered['Blok'].astype(str).str.upper() == 'TJR']) if 'Blok' in df_filtered.columns else 0
        st.markdown("""
        <div style="background: linear-gradient(135deg, #FFA50022, #FFA50011); 
                    padding: 15px; border-radius: 10px; text-align: center;
                    border: 1px solid #FFA50044;">
            <div style="font-size: 28px; font-weight: bold; color: #FFA500;">{}</div>
            <div style="font-size: 12px; color: #B0B0B0;">TJR (Tajarang)</div>
        </div>
        """.format(tjr_count), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ============================================================
    # MAIN CONTENT: FULL-WIDTH MAP ON TOP, TABLE BELOW
    # ============================================================
    
    # ============================================================
    # MAIN CONTENT: DATE ON LEFT, MAP ON RIGHT (MATCHING REFERENCE)
    # ============================================================
    
    # Date formatting for display
    day_names = {
        'Monday': 'Senin', 'Tuesday': 'Selasa', 'Wednesday': 'Rabu',
        'Thursday': 'Kamis', 'Friday': 'Jumat', 'Saturday': 'Sabtu', 'Sunday': 'Minggu'
    }
    month_names = {
        1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April', 5: 'Mei', 6: 'Juni',
        7: 'Juli', 8: 'Agustus', 9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
    }
    
    day_name_en = pd.Timestamp(selected_date).strftime('%A')
    day_id = day_names.get(day_name_en, day_name_en)
    month_id = month_names.get(selected_date.month, str(selected_date.month))
    date_str = f"{selected_date.day} {month_id} {selected_date.year}"
    
    # Generate Map
    shift_label = ', '.join(selected_shifts) if len(selected_shifts) <= 3 else f"{len(selected_shifts)} shifts"
    fig = create_mining_map(df_filtered, pd.Timestamp(selected_date), shift_label)
    
    # 2-Column Layout
    with st.container(border=True):
        # DATE HEADER (Full Width Top)
        st.markdown(f"""
        <div style="background: white; border-radius: 8px; padding: 15px; text-align: center; margin-bottom: 10px; border: 1px solid #ccc;">
            <span style="font-size: 24px; font-weight: bold; color: black; margin-right: 15px;">{day_id},</span>
            <span style="font-size: 24px; color: black;">{date_str}</span>
        </div>
        """, unsafe_allow_html=True)
        
        # MAP (Full Width)
        if fig:
            st.plotly_chart(fig, use_container_width=True, config={
                'displayModeBar': True,
                'modeBarButtonsToRemove': ['lasso2d'], 
                'scrollZoom': False, 
                'displaylogo': False,
                'toImageButtonOptions': {
                    'format': 'jpeg',
                    'filename': f'Daily Scheduling {date_str}',
                    'height': MAP_HEIGHT,
                    'width': MAP_WIDTH,
                    'scale': 3 
                }
            })
            
            st.markdown("""
            <div style="text-align: right; color: #666; font-size: 11px; margin-top: -5px;">
                🔍 Gunakan tombol di atas kanan peta untuk Zoom/Pan | 📷 Ikon Kamera: Download PNG
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("ℹ️ Tidak ada data untuk ditampilkan pada filter yang dipilih.")
    
    # ============================================================
    # TABLE SECTION (FULL WIDTH BELOW MAP)
    # ============================================================
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                padding: 15px; border-radius: 10px; margin-bottom: 15px; margin-top: 20px;
                border-left: 4px solid #00D4FF;">
        <h3 style="margin: 0; color: white; font-size: 18px;">📋 Detail Rencana Operasi Harian</h3>
    </div>
    """, unsafe_allow_html=True)
    
    if not df_filtered.empty:
        display_df = create_data_table(df_filtered)
        st.dataframe(display_df, use_container_width=True, hide_index=True, height=400)
    else:
        st.info("Tidak ada data operasi untuk filter yang dipilih.")
    
    # Production targets (below table)
    # ... (Keep existing target code if needed or just end here)
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 12px;">
        Mining Dashboard v4.0 &copy; 2025 Semen Padang
    </div>
    """, unsafe_allow_html=True)