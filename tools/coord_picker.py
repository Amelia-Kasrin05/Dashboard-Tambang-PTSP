# ============================================================
# GRID COORDINATE PICKER TOOL
# ============================================================
# Interactive tool to help map grid IDs to pixel coordinates
# Run this separately: streamlit run tools/coord_picker.py

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import base64
import os
import json
from PIL import Image

st.set_page_config(page_title="Grid Coordinate Picker", layout="wide")

MAP_IMAGE_PATH = r"D:\Dashboard-Tambang-PTSP\assets\peta_grid_tambang.jpg"
COORDS_FILE = r"d:\Dashboard-Tambang-PTSP\config\grid_coords_data.json"

# Load existing coordinates
def load_saved_coords():
    if os.path.exists(COORDS_FILE):
        with open(COORDS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_coords(coords):
    with open(COORDS_FILE, 'w') as f:
        json.dump(coords, f, indent=2)

def get_image_base64(image_path):
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return None

# Title
st.title("🗺️ Grid Coordinate Picker")
st.markdown("**Cara Penggunaan:** Klik pada peta untuk mendapatkan koordinat, lalu masukkan Grid ID dan simpan.")

# Load existing
saved_coords = load_saved_coords()

# Get image
img_base64 = get_image_base64(MAP_IMAGE_PATH)

if not img_base64:
    st.error("Map image not found!")
    st.stop()

# Get actual image dimensions
try:
    img = Image.open(MAP_IMAGE_PATH)
    MAP_WIDTH, MAP_HEIGHT = img.size
except:
    MAP_WIDTH = 770
    MAP_HEIGHT = 560

col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("📍 Klik pada Peta untuk Mendapatkan Koordinat")
    
    fig = go.Figure()
    
    # Add invisible scatter trace for click detection - FULL COVERAGE
    # Create a dense grid of invisible points for better click detection
    x_points = list(range(0, MAP_WIDTH + 1, 10))
    y_points = list(range(0, MAP_HEIGHT + 1, 10))
    all_x = []
    all_y = []
    for x in x_points:
        for y in y_points:
            all_x.append(x)
            all_y.append(y)
    
    fig.add_trace(go.Scatter(
        x=all_x,
        y=all_y,
        mode='markers',
        marker=dict(size=15, color='rgba(0,0,0,0)'),  # Invisible but clickable
        hovertemplate='X: %{x}<br>Y: %{customdata}<extra>Klik untuk memilih</extra>',
        customdata=[MAP_HEIGHT - y for y in all_y],  # Convert to image coords for display
        showlegend=False,
        name='click_area'
    ))
    
    # Add map image
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
    
    # Add saved points
    for grid_id, coord in saved_coords.items():
        x, y = coord[0], coord[1]
        fig.add_trace(go.Scatter(
            x=[x],
            y=[MAP_HEIGHT - y],  # Convert from image coords to plot coords
            mode='markers+text',
            marker=dict(size=12, color='#FFD700', symbol='diamond', 
                       line=dict(width=2, color='black')),
            text=grid_id,
            textposition='top center',
            textfont=dict(size=11, color='white', family='Arial Black'),
            hovertemplate=f'{grid_id}<br>X: {x}<br>Y: {y}<extra></extra>',
            showlegend=False
        ))
    
    # Add preview marker if coordinates are entered
    x_input = st.session_state.get('x_coord', 0)
    y_input = st.session_state.get('y_coord', 0)
    if x_input > 0 or y_input > 0:
        fig.add_trace(go.Scatter(
            x=[x_input],
            y=[MAP_HEIGHT - y_input],
            mode='markers',
            marker=dict(size=20, color='red', symbol='x', 
                       line=dict(width=3, color='white')),
            hovertemplate=f'Preview<br>X: {x_input}<br>Y: {y_input}<extra></extra>',
            showlegend=False,
            name='preview'
        ))
    
    fig.update_layout(
        xaxis=dict(
            range=[-20, MAP_WIDTH + 20], 
            showgrid=True, 
            gridwidth=1, 
            gridcolor='rgba(255,255,255,0.15)', 
            dtick=50,
            title="X Coordinate"
        ),
        yaxis=dict(
            range=[-20, MAP_HEIGHT + 20], 
            showgrid=True, 
            gridwidth=1, 
            gridcolor='rgba(255,255,255,0.15)', 
            dtick=50, 
            scaleanchor="x",
            title="Y Coordinate (dari bawah)"
        ),
        margin=dict(l=50, r=10, t=10, b=50),
        height=650,
        template='plotly_dark',
        hovermode='closest',
        dragmode='pan'  # Allow panning
    )
    
    # Capture click events using on_select
    event = st.plotly_chart(
        fig, 
        use_container_width=True, 
        key="map_click",
        on_select="rerun",
        selection_mode="points"
    )
    
    # Process click/selection event
    if event and event.selection and event.selection.points:
        point = event.selection.points[0]
        clicked_x = int(point['x'])
        clicked_y = MAP_HEIGHT - int(point['y'])  # Convert back to image coords
        
        # Clamp values
        clicked_x = max(0, min(MAP_WIDTH, clicked_x))
        clicked_y = max(0, min(MAP_HEIGHT, clicked_y))
        
        st.session_state['x_coord'] = clicked_x
        st.session_state['y_coord'] = clicked_y
        st.success(f"✅ Koordinat terpilih: X={clicked_x}, Y={clicked_y}")
    
    st.markdown("""
    **Instruksi:**
    1. **Klik/Select** titik pada peta untuk mendapatkan koordinat
    2. Koordinat akan otomatis terisi di panel sebelah kanan
    3. Masukkan Grid ID (contoh: E9, M10)
    4. Klik "💾 Simpan Koordinat"
    
    💡 **Tips:** Gunakan scroll untuk zoom, drag untuk pan
    """)

with col2:
    st.subheader("📝 Input Koordinat")
    
    # Manual input
    grid_id = st.text_input("Grid ID (contoh: E9, M10)", key="grid_id")
    x_coord = st.number_input("X Coordinate", min_value=0, max_value=MAP_WIDTH, value=0, key="x_coord")
    y_coord = st.number_input("Y Coordinate", min_value=0, max_value=MAP_HEIGHT, value=0, key="y_coord")
    
    if st.button("💾 Simpan Koordinat", use_container_width=True):
        if grid_id:
            saved_coords[grid_id.upper()] = [int(x_coord), int(y_coord)]
            save_coords(saved_coords)
            st.success(f"✅ Tersimpan: {grid_id} = ({x_coord}, {y_coord})")
            st.rerun()
        else:
            st.warning("Mohon masukkan Grid ID!")
    
    st.divider()
    
    # Show saved coordinates
    st.subheader("📋 Koordinat Tersimpan")
    st.markdown(f"**Total: {len(saved_coords)} grid**")
    
    if saved_coords:
        df_coords = pd.DataFrame([
            {"Grid": k, "X": v[0], "Y": v[1]} 
            for k, v in sorted(saved_coords.items())
        ])
        st.dataframe(df_coords, use_container_width=True, hide_index=True, height=300)
        
        # Delete option
        del_grid = st.selectbox("Hapus Grid:", [""] + list(saved_coords.keys()))
        if del_grid and st.button("🗑️ Hapus"):
            del saved_coords[del_grid]
            save_coords(saved_coords)
            st.rerun()
    
    st.divider()
    
    # Export to Python
    if st.button("📤 Export ke Python", use_container_width=True):
        code = "GRID_COORDS_OVERRIDE = {\n"
        for k, v in sorted(saved_coords.items()):
            code += f"    '{k}': ({v[0]}, {v[1]}),\n"
        code += "}"
        st.code(code, language="python")
        st.info("Copy code di atas ke config/grid_coords.py")
