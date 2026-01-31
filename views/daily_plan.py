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

# Import settings
try:
    from config.settings import CACHE_TTL
except ImportError:
    CACHE_TTL = 300

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
            df = pd.read_excel(ONEDRIVE_FILE, sheet_name='Scheduling', header=2, usecols=lambda x: x != 'Unnamed: 0')

            
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

@st.cache_data(ttl=CACHE_TTL)
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
        st.error("Gagal memuat gambar peta.")
        return go.Figure()
    
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
        
        # Normalize Blok for comparison (remove spaces)
        blok_clean = blok.replace(' ', '').replace('-', '').upper()
        
        # Rule: Blok SP6 / SP 6 overrides Grid choice -> Maps to K3
        # Match SP6, STOCKPILE6, etc.
        if 'SP6' in blok_clean or 'STOCKPILE6' in blok_clean:
            return 'K3'
            
        # Rule: Blok SP3 / SP 3 overrides -> Maps to SP3 (Top Left)
        if 'SP3' in blok_clean or 'STOCKPILE3' in blok_clean:
            return 'SP3'
        
        # Rule: Jika Grid terisi -> lokasi_id = Grid
        if grid and grid.lower() != 'nan':
            return grid
        
        # Rule: Jika Grid kosong dan Blok terisi -> lokasi_id = Blok
        if blok and blok.lower() != 'nan':
            return blok
        
        return None

    df_map['lokasi_id'] = df_map.apply(resolve_location_id, axis=1)
    # Remove rows where location couldn't be resolved
    df_map = df_map[df_map['lokasi_id'].notna()]

    # ------------------------------------------------------------
    # 3. GROUPING
    # ------------------------------------------------------------
    # Group fields
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
    
    # Store all annotations to perform collision adjustment
    annotations = []
    
    # COLOR SETTING: Lighter Blue (Reverted)
    BOX_COLOR = '#00BFFF' 
    
    for _, row in grouped.iterrows():
        loc_id = row['lokasi_id']
        alat_muat = row['Alat Muat']
        alat_angkut = row['Alat Angkut']
        rom_list = row['ROM'] # Now an array/list
        shifts = row['Shift']
        
        # Get Coordinates
        x, y = None, None
        
        # SP3 Logic: If loc_id is strictly SP3, use specific coordinates
        if loc_id == 'SP3':
            # SP3 in Top Left Corner - Hardcode if get_grid_position doesn't handle it
            pos = get_grid_position(loc_id, loc_id)
            if pos:
                x, y = pos
            else:
                 # Fallback for SP3 if not in config: Top Left corner near N8 area
                 x, y = 100, 100 
        else:
            # Use standard mapping
            pos = get_grid_position(loc_id)
            if pos:
                x, y = pos
        
        if x is None or y is None:
            continue
            
        # Flip Y for plotting (Map coords usually origin top-left, Plotly origin bottom-left)
        # Assuming MAP_HEIGHT is correct height
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
        valid_roms = [str(r) for r in rom_list if pd.notna(r) and str(r).strip() not in ['', 'nan', 'None']]
        unique_roms = sorted(list(set(valid_roms)))
        rom_str = " & ".join(unique_roms)
        line3 = f"LS> {rom_str}"
        
        # Combined Box Text
        box_text = f"{line1}<br>{line2}<br>{line3}"
        
        annotations.append({
            'x': x,
            'y': y_plot,
            'text': box_text,
            'loc_id': loc_id,
            'color': BOX_COLOR 
        })

    # COLLISION AVOIDANCE ALGORITHM (SPIRAL GREEDY SEARCH V3 - USABLE AREA)
    # ---------------------------------------------------------------------
    # 1. Flexible Spiral Search for Label Boxes
    # 2. Strict Usable Area Clamping (Exclude Legend/Borders)
    # 3. Enhanced Channel Allocator for Leader Lines (Anti-Overlap)
    
    # Define USABLE MAP AREA (Estimate from image)
    # Legend is on Right side. Bottom has labels.
    # Map Width 1400. Legend seems to take ~300px.
    USABLE_MIN_X = 50
    USABLE_MAX_X = MAP_WIDTH - 350 # Increased margin to avoid Legend
    USABLE_MIN_Y = 50
    USABLE_MAX_Y = MAP_HEIGHT - 60
    
    annotations.sort(key=lambda k: (-k['y'], k['x']))
    
    placed_boxes = [] # List of {x, y, w, h}
    
    # Parameters
    BOX_W = 140 
    BOX_H = 100 
    
    # Helper: Absolute Boundary Clamp
    def safe_clamp(val, min_val, max_val):
        return max(min_val, min(max_val, val))

    # Helper: Check collision
    def check_collision(cx, cy, boxes):
        # Strict margin check against USABLE AREA
        margin_w = BOX_W/2 + 10
        margin_h = BOX_H/2 + 10
        
        if cx < USABLE_MIN_X + margin_w or cx > USABLE_MAX_X - margin_w: return True
        if cy < USABLE_MIN_Y + margin_h or cy > USABLE_MAX_Y - margin_h: return True
        
        # Check vs other boxes
        for b in boxes:
            pad = 10 
            if (abs(cx - b['x']) * 2 < (BOX_W + b['w'] + pad) and 
                abs(cy - b['y']) * 2 < (BOX_H + b['h'] + pad)):
                return True
        return False

    final_placements = []

    for ann in annotations:
        t_x, t_y = ann['x'], ann['y']
        
        # Spiral Radii - start small, go big
        radii = [130, 160, 200, 250, 320, 400]
        
        # Determine logical center of usable area for biasing
        usable_center_x = (USABLE_MIN_X + USABLE_MAX_X) / 2
        
        # Angles
        # If target is left of center, prefer searching Left/Top/Bottom
        if t_x < usable_center_x:
            # Prefers Left (180)
            angles = [180, 150, 210, 120, 240, 90, 270, 0] 
        else:
            # Prefers Right (0) - but confined by legend
            angles = [0, 30, 330, 60, 300, 90, 270, 180]
            
        full_angles = angles
        
        # Specific overrides
        if ann.get('loc_id') == 'SP3': full_angles = [180, 150, 210] 
        if ann.get('loc_id') == 'N8': full_angles = [180, 150, 210] 
        
        best_x, best_y = t_x, t_y
        found = False
        import math
        
        for r in radii:
            for angle_deg in full_angles:
                angle_rad = math.radians(angle_deg)
                c_x = t_x + r * math.cos(angle_rad)
                c_y = t_y + r * math.sin(angle_rad)
                
                if not check_collision(c_x, c_y, placed_boxes):
                    best_x, best_y = c_x, c_y
                    found = True
                    break
            if found: break
        
        # Fallback: Push inwards to usable area
        if not found:
            # Just try to clamp target + some offset
            # Push towards center
            dir_to_center = 1 if t_x < usable_center_x else -1
            best_x = t_x + (dir_to_center * 150)
            best_y = t_y
        
        # STRICT FINAL CLAMP TO USABLE AREA
        margin_w = BOX_W/2 + 5
        margin_h = BOX_H/2 + 5
        best_x = safe_clamp(best_x, USABLE_MIN_X + margin_w, USABLE_MAX_X - margin_w)
        best_y = safe_clamp(best_y, USABLE_MIN_Y + margin_h, USABLE_MAX_Y - margin_h)
        
        placed_boxes.append({'x': best_x, 'y': best_y, 'w': BOX_W, 'h': BOX_H})
        final_placements.append({
            'ann': ann,
            'x': best_x,
            'y': best_y,
            'tx': t_x,
            'ty': t_y
        })

    # SMART L-SHAPE ROUTER
    # --------------------
    # Prioritizes simple 1-turn lines for maximum aesthetics ("Technical look").
    # Hybrid logic: Vertical First (Flagpole) vs Horizontal First (Shelf).
    
    for p in final_placements:
        ann = p['ann']
        l_x, l_y = p['x'], p['y']
        t_x, t_y = p['tx'], p['ty']
        
        visual_box_w = 110
        visual_box_h = 70 
        
        # Define Box Bounds
        box_left = l_x - visual_box_w/2
        box_right = l_x + visual_box_w/2
        box_top = l_y + visual_box_h/2 # Plotly Y is up? Need to verify. 
        # Assuming our coordinates: Y increases upwards.
        # box_top is higher Y value.
        box_bottom = l_y - visual_box_h/2
        
        path_svg = ""
        
        # LOGIC:
        # Check if Target X is "inside" the Box's X-shadow (column).
        # If Target is horizontally aligned with box -> Must go SIDEWAYS first (Horizontal First).
        # Else (Target is clearly Left/Right of box) -> Go VERTICAL first (Flagpole).
        
        is_target_in_x_shadow = (t_x >= box_left - 10) and (t_x <= box_right + 10)
        
        if not is_target_in_x_shadow:
            # FLAGPOLE STYLE (Vertical, then Horizontal)
            # 1. Start at Target
            # 2. Go Up/Down to Box Y-Level (use box side anchor)
            # 3. Turn Horizontal to Box Side
            
            # Determine connect side
            if l_x > t_x: # Box is Right
                anchor_x = box_left
            else: # Box is Left
                anchor_x = box_right
            
            # Corner Point
            corner_x = t_x
            corner_y = l_y
            
            # Draw: T(tx,ty) -> C(tx,ly) -> A(anchor_x,ly)
            path_svg = f"M {t_x},{t_y} L {t_x},{l_y} L {anchor_x},{l_y}"
            
        else:
            # SHELF STYLE (Horizontal, then Vertical)
            # Target is directly above/below box. Vertical line would cut through box.
            # So: Go Sideways out of target, then Up/Down to Box Side.
            # Or: Go Up/Down to Box Top/Bottom?
            
            # Let's try "Snap to Top/Bottom"
            is_target_above = t_y > l_y
            
            if is_target_above: # Target Above
                # Connect to Box Top
                anchor_y = box_top + 5
                # Path: T(tx,ty) -> (tx, anchor_y). Straight Vertical Line.
                # Simple and clean.
                path_svg = f"M {t_x},{t_y} L {t_x},{anchor_y}"
            else: # Target Below
                # Connect to Box Bottom
                anchor_y = box_bottom - 5
                path_svg = f"M {t_x},{t_y} L {t_x},{anchor_y}"
                
        # 1. Elbow Line
        fig.add_shape(
            type="path",
            path=path_svg,
            line=dict(color=ann['color'], width=2),
            layer="above" 
        )
        
        # 2. Box Annotation
        fig.add_annotation(
            x=l_x,
            y=l_y, 
            text=ann['text'],
            showarrow=False, 
            bgcolor=ann['color'], 
            bordercolor='white',
            borderwidth=1,
            borderpad=4,
            font=dict(size=9, color='black', family='Arial, sans-serif'), 
            opacity=0.9, 
            align='center',
            captureevents=True,
            width=visual_box_w
        )
        
        # 3. Target Dot
        fig.add_trace(go.Scatter(
            x=[t_x],
            y=[t_y],
            mode='markers',
            marker=dict(size=12, color=ann['color'], line=dict(color='white', width=2)),
            hoverinfo='text',
            hovertext=ann['loc_id'],
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
        st.warning("⚠️ Data Rencana Harian tidak tersedia. Pastikan file Excel ditutup.")
        return
    
    # ============================================================
    # HEADER
    # ============================================================
    # ============================================================
    # HEADER
    # ============================================================
    st.markdown("""
    <style>
    /* FORCE OVERRIDE FOR CONTAINERS */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        /* VISIBLE CONTRAST CARD STYLE */
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
    
    # DEBUG: Show data sample - REMOVED per user request

    
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
    
    # Retrieve Global Filters (if any)
    global_filters = st.session_state.get('global_filters', {})
    global_date_range = global_filters.get('date_range')
    global_shift = global_filters.get('shift')
    
    with filter_cols[0]:
        st.markdown("**📅 Tanggal**")
        # Default to Global Filter End Date if available and in list, else latest available
        default_date = available_dates[0] if available_dates else datetime.now().date()
        
        if global_date_range and isinstance(global_date_range, tuple) and len(global_date_range) > 1:
            # User usually wants to see the specific date they selected. 
            # Since Daily Plan is single-day, we pick the END date of the range (latest).
            target_date = global_date_range[1]
            if target_date in available_dates:
                default_date = target_date
                
        if len(available_dates) > 0:
            selected_date = st.date_input(
                "Tanggal",
                value=default_date,
                key='dp_date',
                label_visibility="collapsed"
            )
        else:
            selected_date = datetime.now().date()
    
    with filter_cols[1]:
        st.markdown("**⏰ Shift**")
        shift_options = ['Semua'] + available_shifts
        
        # Sync with Global Shift
        default_shifts = ['Semua']
        if global_shift and global_shift != "All Displatch":
            # Normalize Global Shift "Shift 1" -> "1"
            g_shift_str = str(global_shift).replace("Shift ", "").strip()
            if g_shift_str in available_shifts:
                default_shifts = [g_shift_str]
        
        selected_shifts = st.multiselect(
            "Shift",
            options=shift_options,
            default=default_shifts,
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
        
        # Sync with Global Front (which is often Grid)
        global_front = global_filters.get('front')
        default_grids = ['Semua']
        
        if global_front and len(global_front) > 0:
            # Filter valid grids from global selection
            valid_global_fronts = [g for g in global_front if str(g) in available_grid]
            if valid_global_fronts:
                default_grids = valid_global_fronts
        
        selected_grids = st.multiselect(
            "Grid",
            options=grid_options,
            default=default_grids,
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
        
        # Excel Download
        from utils.helpers import convert_df_to_excel
        excel_data = convert_df_to_excel(display_df)
        
        st.download_button(
            label="📥 Unduh Data Rencana (Excel)",
            data=excel_data,
            file_name=f"PTSP_Rencana_Harian_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
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