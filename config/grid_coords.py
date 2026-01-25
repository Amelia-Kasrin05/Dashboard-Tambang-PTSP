# ============================================================
# GRID COORDINATES MAPPING
# ============================================================
# Maps grid IDs (from Excel) to pixel positions on the map image
# Coordinates calibrated from grid_reference_points.txt (199 points)
#
# Coordinate system: (x, y) where (0,0) is top-left
# Image size: 1400x990 pixels (optimized image)

import os
import re

# Image dimensions
MAP_WIDTH = 1400
MAP_HEIGHT = 990

# ============================================================
# LOAD COORDINATES FROM REFERENCE FILE
# ============================================================

def load_grid_coords_from_file():
    """Load grid coordinates from grid_reference_points.txt"""
    coords = {}
    
    # Path to reference file
    file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'grid_reference_points.txt')
    
    if not os.path.exists(file_path):
        return coords
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#') or line.startswith('='):
                    continue
                
                # Parse format: "G2: x=206, y=473"
                match = re.match(r'^([A-Z]\d+):\s*x=(\d+),\s*y=(\d+)', line)
                if match:
                    grid_id = match.group(1)
                    x = int(match.group(2))
                    y = int(match.group(3))
                    coords[grid_id] = (x, y)
    except Exception as e:
        print(f"Error loading grid coords: {e}")
    
    return coords

# Load coordinates at module init
GRID_COORDS = load_grid_coords_from_file()

# ============================================================
# SPECIAL LOCATIONS (for blocks without grid ID)
# ============================================================

SPECIAL_LOCATIONS = {
    'SP6': (50, 50),      # Top-left corner (Stockpile 6)
    'SP3': None,          # Will use K3 grid position
}

# ============================================================
# ZONE COLORS
# ============================================================

ZONE_COLORS = {
    'TJR': '#FFA500',     # Orange - TAJARANG
    'KRP': '#00BFFF',     # Cyan/Light Blue - KAPUR PUTIH
    'SP6': '#00AA00',     # Green - Stockpile 6
    'SP3': '#AA00AA',     # Purple - Stockpile 3
}

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_grid_position(grid_id, blok=None):
    """
    Get pixel position for a grid ID
    
    Args:
        grid_id: Grid ID like 'E9', 'M10', 'O12', etc.
        blok: Block/zone ID like 'KRP', 'TJR', 'SP6', 'SP3'
    
    Returns:
        (x, y) tuple for pixel coordinates, or None if not found
    """
    # Handle special cases where grid is empty but blok is set
    if not grid_id or str(grid_id).lower() in ['nan', 'none', '']:
        if blok:
            blok_upper = str(blok).upper().strip()
            if blok_upper == 'SP6':
                return SPECIAL_LOCATIONS['SP6']
            elif blok_upper == 'SP3':
                # SP3 uses K3 position
                return GRID_COORDS.get('K3', (251, 660))
        return None
    
    grid_id = str(grid_id).strip().upper()
    
    # Handle compound grids like 'F5/C5' - use first one
    if '/' in grid_id:
        grid_id = grid_id.split('/')[0].strip()
    
    # Look up in loaded coordinates
    if grid_id in GRID_COORDS:
        return GRID_COORDS[grid_id]
    
    # Fallback: try to calculate from grid pattern
    return calculate_grid_position(grid_id)


def calculate_grid_position(grid_id):
    """
    Calculate approximate grid position if not in reference file.
    Uses average spacing from known coordinates.
    """
    if not grid_id:
        return None
    
    # Parse grid ID: letter + number
    match = re.match(r'^([A-P])(\d+)$', grid_id.upper())
    if not match:
        return None
    
    row_letter = match.group(1)
    col_number = int(match.group(2))
    
    # Calculate based on average patterns from reference data
    # Row A starts around y=200, each row ~47 pixels apart
    # Column 1 starts around x=155, each column ~47 pixels apart
    
    row_index = ord(row_letter) - ord('A')  # A=0, B=1, etc.
    
    # Approximate calculations based on reference data
    GRID_START_X = 155
    GRID_START_Y = 200
    CELL_WIDTH = 47
    CELL_HEIGHT = 47
    
    x = GRID_START_X + (col_number - 1) * CELL_WIDTH
    y = GRID_START_Y + row_index * CELL_HEIGHT
    
    return (x, y)


def get_zone_color(blok):
    """Get color for a mining block/zone"""
    if not blok:
        return '#00BFFF'  # Default cyan
    
    blok = str(blok).upper().strip()
    return ZONE_COLORS.get(blok, '#00BFFF')


def get_all_grid_coords():
    """Return all loaded grid coordinates"""
    return GRID_COORDS.copy()


# ============================================================
# DEBUG: Print loaded coordinates count
# ============================================================

if __name__ == "__main__":
    print(f"Loaded {len(GRID_COORDS)} grid coordinates")
    for grid_id in sorted(GRID_COORDS.keys())[:10]:
        print(f"  {grid_id}: {GRID_COORDS[grid_id]}")
    print("  ...")
