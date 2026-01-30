# ============================================================
# DATA LOADER - FIXED FOR EXCEL SERIAL DATES
# ============================================================
# VERSION: 3.0 - Fixed Excel serial number date parsing

import pandas as pd
import streamlit as st
import requests
from io import BytesIO
import base64
import os
import sys
from datetime import datetime, timedelta

from datetime import datetime, timedelta

# Import Settings
try:
    from config.settings import MONITORING_EXCEL_PATH, PRODUKSI_FILE, GANGGUAN_FILE, CACHE_TTL
    # Backwards compatibility for other modules
    ONEDRIVE_LINKS = {} 
    LOCAL_FILE_NAMES = {
        "monitoring": [MONITORING_EXCEL_PATH, r"C:\Users\user\OneDrive\Dashboard_Tambang\Monitoring_2025_.xlsx"],
        "produksi": [PRODUKSI_FILE, r"C:\Users\user\OneDrive\Dashboard_Tambang\Produksi_UTSG_Harian.xlsx"],
        "gangguan": [GANGGUAN_FILE, r"C:\Users\user\OneDrive\Dashboard_Tambang\Gangguan_Produksi.xlsx"]
    }
except ImportError:
    # Fallback if config not found
    MONITORING_EXCEL_PATH = None
    PRODUKSI_FILE = None
    GANGGUAN_FILE = None
    CACHE_TTL = 300
    ONEDRIVE_LINKS = {}
    LOCAL_FILE_NAMES = {}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def apply_global_filters(df, date_col='Date', shift_col='Shift'):
    """Apply sidebar filters to any dataframe"""
    if df.empty:
        return df
        
    # Get filters from session state
    filters = st.session_state.get('global_filters', {})
    date_range = filters.get('date_range')
    selected_shift = filters.get('shift')
    
    # 1. Filter Date
    if date_range and len(date_range) == 2 and date_col in df.columns:
        start_date, end_date = date_range
        # Ensure date column is datetime
        if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            
        # Filter
        mask = (df[date_col].dt.date >= start_date) & (df[date_col].dt.date <= end_date)
        df = df[mask]
        
    # 2. Filter Shift
    if selected_shift and selected_shift != "All Displatch" and shift_col in df.columns:
        # Normalize shift values (some might be int 1, some 'Shift 1')
        target_shift = 1 if "1" in str(selected_shift) else (2 if "2" in str(selected_shift) else 3)
        
        # Check if column is numeric or string
        if pd.api.types.is_numeric_dtype(df[shift_col]):
             df = df[df[shift_col] == target_shift]
        else:
             df = df[df[shift_col].astype(str).str.contains(str(target_shift), case=False, na=False)]
             
    # 3. Filter Front
    selected_front = filters.get('front')
    if selected_front and 'Front' in df.columns:
        df = df[df['Front'].isin(selected_front)]
        
    # 4. Filter Excavator
    selected_exca = filters.get('excavator')
    if selected_exca and 'Excavator' in df.columns:
        df = df[df['Excavator'].isin(selected_exca)]

    # 5. Filter Material (Commodity)
    selected_material = filters.get('material')
    if selected_material:
        # Check for both spellings (Commudity vs Commodity)
        if 'Commudity' in df.columns:
            df = df[df['Commudity'].isin(selected_material)]
        elif 'Commodity' in df.columns:
            df = df[df['Commodity'].isin(selected_material)]
        elif 'Material' in df.columns:
             df = df[df['Material'].isin(selected_material)]
             
    return df


def convert_onedrive_link(share_link):
    """Convert OneDrive share link ke direct download link"""
    if not share_link or share_link.strip() == "":
        return None
    
    share_link = share_link.strip()
    
    try:
        encoded = base64.b64encode(share_link.encode()).decode()
        encoded = encoded.rstrip('=').replace('/', '_').replace('+', '-')
        return f"https://api.onedrive.com/v1.0/shares/u!{encoded}/root/content"
    except Exception:
        return None


def download_from_onedrive(share_link, timeout=30):
    """Download file dari OneDrive"""
    direct_url = convert_onedrive_link(share_link)
    
    if not direct_url:
        return None
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(direct_url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return BytesIO(response.content)
    except:
        return None


def load_from_local(file_key):
    """Load file dari lokasi lokal"""
    if file_key not in LOCAL_FILE_NAMES:
        return None
    
    for file_path in LOCAL_FILE_NAMES[file_key]:
        normalized_path = os.path.normpath(file_path)
        
        if os.path.exists(normalized_path):
            try:
                if os.path.getsize(normalized_path) > 0:
                    return normalized_path
            except Exception:
                continue
    
    return None


def check_onedrive_status():
    """Enhanced status check"""
    status = {}
    
    for name, link in ONEDRIVE_LINKS.items():
        if link and link.strip() != "":
            try:
                file_buffer = download_from_onedrive(link, timeout=10)
                if file_buffer:
                    status[name] = "✅ OneDrive"
                    continue
            except:
                pass
        
        local_path = load_from_local(name)
        if local_path:
            try:
                file_size = os.path.getsize(local_path)
                size_kb = file_size // 1024
                status[name] = f"✅ Local ({size_kb}KB)"
            except Exception:
                status[name] = "⚠️ Local (error)"
        else:
            status[name] = "⚠️ No link" if not (link and link.strip()) else "❌ Not found"
    
    return status


# ============================================================
# EXCEL SERIAL DATE PARSER
# ============================================================

def parse_excel_date(date_value):
    """
    Parse Excel serial date to Python date
    Excel stores dates as number of days since 1900-01-01
    Example: 45870 = 2025-07-12
    """
    try:
        # If already a date/datetime, return as is
        if isinstance(date_value, (datetime, pd.Timestamp)):
            return pd.Timestamp(date_value).date()
        
        # If string, try to parse
        if isinstance(date_value, str):
            parsed = pd.to_datetime(date_value, errors='coerce')
            if pd.notna(parsed):
                return parsed.date()
            return None
        
        # If number (Excel serial date)
        if isinstance(date_value, (int, float)):
            # Excel epoch starts at 1899-12-30 (not 1900-01-01 due to Excel bug)
            excel_epoch = datetime(1899, 12, 30)
            date_result = excel_epoch + timedelta(days=int(date_value))
            return date_result.date()
        
        return None
        
    except Exception:
        return None


def safe_parse_date_column(date_series):
    """Apply Excel date parsing to entire column"""
    return date_series.apply(parse_excel_date)


def normalize_excavator_name(name):
    """
    Normalize excavator name to format: PC XXX-YY
    Example: 'PC 850 01' -> 'PC 850-01', 'PC850-01' -> 'PC 850-01', 'PC-400-05' -> 'PC 400-05'
    """
    import re
    
    if pd.isna(name) or not isinstance(name, str):
        return name
    
    name = str(name).strip().upper()
    
    # Remove all separators first to get pure digits
    # Handle formats: PC 850 01, PC850-01, PC 850-01, PC85001, PC-850-01, PC-400-05
    clean = re.sub(r'[^A-Z0-9]', '', name)  # Remove all non-alphanumeric
    
    # Match PC followed by exactly 5 digits (3 for model + 2 for number)
    match = re.match(r'^PC(\d{3})(\d{2})$', clean)
    if match:
        return f"PC {match.group(1)}-{match.group(2)}"
    
    # Try original pattern for edge cases
    match = re.match(r'^PC[-\s]*(\d{3})[-\s]*(\d{2})$', name)
    if match:
        return f"PC {match.group(1)}-{match.group(2)}"
    
    return name


def normalize_excavator_column(df):
    """Apply excavator name normalization to dataframe"""
    if 'Excavator' in df.columns:
        df['Excavator'] = df['Excavator'].apply(normalize_excavator_name)
    return df


# ============================================================
# LOAD PRODUKSI - FIXED VERSION
# ============================================================

@st.cache_data(ttl=CACHE_TTL)
def load_produksi():
    """Load data produksi - FIXED for Excel serial dates"""
    
    df = None
    
    # Helper to validate if sheet has minimum required columns
    def is_valid_prod(d):
        if d is None or d.empty: return False
        cols = [str(c).lower() for c in d.columns]
        # Check for essential columns (relaxed)
        return any('shift' in c for c in cols) and (any('date' in c or 'tanggal' in c for c in cols))

    # Generic loader that handles both Path and BytesIO
    def load_content(source):
        try:
            xls = pd.ExcelFile(source)
            valid_dfs = []
            
            # Prioritize "Tahun" sheets, but check all
            # User specific request: Focus PURELY on "2026" if available
            target_sheets = [s for s in xls.sheet_names if '2026' in str(s)]
            
            if target_sheets:
                sheets_to_process = target_sheets
            else:
                sheets_to_process = [s for s in xls.sheet_names if s.lower() not in ['menu', 'dashboard', 'summary', 'ref', 'config']]
                
            for sheet in sheets_to_process:
                # Skip obviously non-data sheets
                if sheet.lower() in ['menu', 'dashboard', 'summary', 'ref', 'config']:
                    continue
                    
                try:
                    # STRATEGY 2026: DIRECT READ (Since we verified format in debug)
                    if '2026' in str(sheet):
                        temp_df = pd.read_excel(xls, sheet_name=sheet) # Auto header (0)
                        
                        # Fix column names just in case
                        temp_df.columns = [str(c).strip() for c in temp_df.columns]
                        
                        # Ensure 'Date' exists
                        if 'Date' not in temp_df.columns:
                            # Fallback map
                             if 'Tanggal' in temp_df.columns:
                                 temp_df = temp_df.rename(columns={'Tanggal': 'Date'})
                        
                        if 'Date' in temp_df.columns:
                             # Basic validation
                             valid_dfs.append(temp_df)
                             continue # Success, move to next sheet
                    
                    # --- LEGACY SCANNER LOGIC (Maintained for older sheets) ---
                    # Smart Header Detection: Read first 30 rows
                    df_raw = pd.read_excel(xls, sheet_name=sheet, header=None, nrows=30)
                    
                    header_idx = -1
                    for i in range(len(df_raw)):
                        row_vals = [str(x).strip().lower() for x in df_raw.iloc[i].tolist()]
                        has_shift = 'shift' in row_vals
                        if has_shift:
                            header_idx = i
                            break
                    
                    if header_idx != -1:
                        temp_df = pd.read_excel(xls, sheet_name=sheet, header=header_idx)
                        temp_df.columns = [str(c).strip() for c in temp_df.columns]
                        
                        if 'Date' not in temp_df.columns:
                            for c in temp_df.columns:
                                c_str = str(c).lower()
                                if 'date' in c_str or 'tanggal' in c_str :
                                    temp_df = temp_df.rename(columns={c: 'Date'})
                                    break
                        
                        if 'Date' in temp_df.columns:
                            temp_df['Date'] = temp_df['Date'].ffill()

                        if is_valid_prod(temp_df):
                            valid_dfs.append(temp_df)
                            
                except Exception as e:
                    continue
            
            if valid_dfs:
                return pd.concat(valid_dfs, ignore_index=True)
            else:
                return None
                
        except Exception as e:
            return None
        return None


    # 1. Try OneDrive
    if ONEDRIVE_LINKS.get("produksi"):
        file_buffer = download_from_onedrive(ONEDRIVE_LINKS["produksi"])
        if file_buffer:
            df = load_content(file_buffer)
    
    # 2. Try Local if OneDrive failed
    if df is None:
        local_path = load_from_local("produksi")
        if local_path:
            df = load_content(local_path)
    
    if df is None:
        return pd.DataFrame()
    

    try:
        # Dynamic Header Detection
        # Search for row containing 'Excavator' or 'Tonnase'
        if 'Excavator' not in df.columns and 'Tonnase' not in df.columns:
            for i in range(min(10, len(df))):
                row_values = df.iloc[i].astype(str).values
                # Check for key keywords
                if any('Excavator' in v for v in row_values) or any('Tonnase' in v for v in row_values):
                    df.columns = df.iloc[i]
                    df = df.iloc[i+1:]
                    break
        
        # Cleanup Column Names
        df.columns = [str(c).strip() for c in df.columns]
        
        # Standardize Date Column
        col_date = next((c for c in df.columns if 'Date' in c or 'Tanggal' in c), 'Date')
        df = df.rename(columns={col_date: 'Date'})

        # Robust Shift Filtering
        if 'Shift' in df.columns:
            # Normalize whitespace and mixed types
            df['Shift'] = df['Shift'].astype(str).str.strip()
            # Catch "Shift 1", "1", "Shift 2", "2", etc.
            valid_shifts = ['Shift 1', 'Shift 2', 'Shift 3', '1', '2', '3']
            df = df[df['Shift'].isin(valid_shifts)]
        
        # ✅ FIX: Parse Excel Serial Date
        df['Date'] = safe_parse_date_column(df['Date'])
        
        # Remove invalid dates
        df = df[df['Date'].notna()]
        
        # Parse Time
        if 'Time' in df.columns:
            df['Time'] = df['Time'].astype(str).fillna('')
        else:
            df['Time'] = ''
        
        # Check if BLOK column exists (if not, columns are shifted)
        # Often occurs if 'No' column is missing or added
        if 'BLOK' not in df.columns and 'Front' in df.columns:
             # Try to map intelligently
             pass # Assume if Front exists it's okay for now, or map Front -> BLOK?
             
        # Column Mapping Safety
        # Ensure we have: BLOK, Front, Commudity, Excavator, Dump Truck, Dump Loc, Rit, Tonnase
        
        # Heuristic for shifted columns:
        # If 'Tonnase' is missing but we have 'Unnamed: X', it might be there.
        # But let's look for numeric columns at the end.
        
        # Rename common variations
        col_map = {}
        for c in df.columns:
            cl = c.lower()
            if 'excavator' in cl: col_map[c] = 'Excavator'
            elif 'commodity' in cl or 'commudity' in cl: col_map[c] = 'Commudity'
            elif 'tonnase' in cl or 'tonase' in cl: col_map[c] = 'Tonnase'
            elif 'rit' in cl: col_map[c] = 'Rit'
            elif 'dump truck' in cl or 'dt' == cl: col_map[c] = 'Dump Truck'
            
        df = df.rename(columns=col_map)
        
        # Filter only valid excavators (PC prefix)
        if 'Excavator' in df.columns:
            df = df[df['Excavator'].astype(str).str.startswith('PC', na=False)]
            # Normalize excavator names
            df = normalize_excavator_column(df)
        
        # Convert numeric columns
        if 'Rit' in df.columns:
            df['Rit'] = pd.to_numeric(df['Rit'], errors='coerce').fillna(0)
        else:
            df['Rit'] = 0
            
        if 'Tonnase' in df.columns:
            df['Tonnase'] = pd.to_numeric(df['Tonnase'], errors='coerce').fillna(0)
        else:
            df['Tonnase'] = 0
        
        # Final cleanup
        df = df[df['Tonnase'] > 0]
            
        df = df.reset_index(drop=True)
        
        # Format Date for Display (Remove 00:00:00)
        # KEEP AS DATETIME for filtering first!
        # The formatting to remove 00:00:00 should happen only at current view level OR we ensure it's string.
        # But apply_global_filters expects datetime.
        # FIX: We keep it as datetime. The user complained about 00:00:00 VISUALLY in the table.
        # We can handle visual formatting in the view (dataframe.style or convert to string AFTER filtering).
        # But here we are in loader. Let's convert to formatted string for now, 
        # BUT apply_global_filters needs to be smart enough to handle strings or we convert back.
        
        # ACTUALLY: dashboard view calls apply_global_filters immediately after load.
        # apply_global_filters expects datetime.
        # So we MUST return datetime from here.
        
        # WORKAROUND: We return datetime here. We will fix the VISUAL display in views/produksi.py instead.
        # Reverting the .dt.date change that broke the filter.
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])

        
        # Drop columns after Tonnase (Unnamed nonsense)
        # Keep only standard columns
        keep_cols = ['Date', 'Time', 'Shift', 'BLOK', 'Front', 'Commudity', 
                     'Excavator', 'Dump Truck', 'Dump Loc', 'Rit', 'Tonnase']
        
        # Add any missing standard columns as empty
        for col in keep_cols:
            if col not in df.columns:
                df[col] = ''
                
        # Select only kept columns
        df = df[[c for c in keep_cols if c in df.columns]]
        
        return df
        
    except Exception as e:
        print(f"Error processing production: {e}")
        return pd.DataFrame()


# ============================================================
# OTHER LOAD FUNCTIONS (GANGGUAN, BBM, etc)
# ============================================================

@st.cache_data(ttl=CACHE_TTL)
def load_gangguan(bulan):
    """Load data gangguan per bulan (ringkasan)"""
    sheet = f'Monitoring {bulan}'
    df = None
    
    if ONEDRIVE_LINKS.get("gangguan"):
        file_buffer = download_from_onedrive(ONEDRIVE_LINKS["gangguan"])
        if file_buffer:
            try:
                df = pd.read_excel(file_buffer, sheet_name=sheet, skiprows=1)
            except:
                pass
    
    if df is None:
        local_path = load_from_local("gangguan")
        if local_path:
            try:
                df = pd.read_excel(local_path, sheet_name=sheet, skiprows=1)
            except:
                pass
    
    if df is None:
        return pd.DataFrame()
    
    try:
        if len(df.columns) >= 3:
            df.columns = ['Row Labels', 'Frekuensi', 'Persentase']
        
        df = df[df['Row Labels'] != 'Row Labels']
        df = df[df['Row Labels'] != 'Grand Total']
        df['Frekuensi'] = pd.to_numeric(df['Frekuensi'], errors='coerce')
        df = df.dropna(subset=['Frekuensi'])
        df = df[df['Frekuensi'] > 0]
        df = df.reset_index(drop=True)
        
        return df
    except:
        return pd.DataFrame()


@st.cache_data(ttl=CACHE_TTL)
def load_gangguan_all():
    """
    Load data gangguan lengkap.
    Prioritizes 2026 data sheets (e.g., 'Monitoring Jan 2026').
    """
    file_path = None
    
    # Try local OneDrive folder first
    local_path = load_from_local("gangguan")
    if local_path:
        file_path = local_path
    
    if file_path is None:
        return pd.DataFrame()
    
    try:
        xls = pd.ExcelFile(file_path)
        sheet_names = xls.sheet_names
        
        # 0. User Override: Check for 'All' sheet first (Primary)
        if 'All' in sheet_names:
            target_sheets = ['All']
            # print("Loading from sheet: All")
        else:
            # 1. Try to find 2026 sheets (Secondary)
            target_sheets = [s for s in sheet_names if '2026' in str(s) and 'Monitoring' in str(s)]
            
            # 2. If no 2026 specific sheets, fallback to scanning
            if not target_sheets:
                # Fallback for 'Gangguan 2026', 'Data 2026', etc or generic 'Monitoring'
                candidates = [s for s in sheet_names if 'monitoring' in str(s).lower()]
                if candidates:
                    target_sheets = candidates
                else:
                     # Last resort: 'Sheet1' or first sheet
                     if 'Sheet1' in sheet_names:
                         target_sheets = ['Sheet1']
                     elif len(sheet_names) > 0:
                         target_sheets = [sheet_names[0]]

        if not target_sheets:
            return pd.DataFrame()
            
        all_dfs = []
        standard_cols = ['Tanggal', 'Bulan', 'Tahun', 'Week', 'Shift', 'Start', 'End', 
                        'Durasi', 'Crusher', 'Alat', 'Remarks', 'Kelompok Masalah', 'Gangguan', 
                        'Info CCR', 'Sub Komponen', 'Keterangan', 'Penyebab', 
                        'Identifikasi Masalah', 'Action', 'Plan', 'PIC', 'Status', 'Due Date',
                        'Spare Part', 'Info Spare Part', 'Link/Lampiran', 'Extra']

        for sheet in target_sheets:
            try:
                # Read sheet - Assume Row 0 is header
                df_sheet = pd.read_excel(file_path, sheet_name=sheet)
                
                if df_sheet.empty:
                    continue

                # Normalize columns
                df_sheet.columns = [str(c).strip() for c in df_sheet.columns]
                
                # Check critical column 'Tanggal'
                if 'Tanggal' not in df_sheet.columns:
                     # Maybe case sensitivity issue?
                     col_map = {c.lower(): c for c in df_sheet.columns}
                     if 'tanggal' in col_map:
                         df_sheet = df_sheet.rename(columns={col_map['tanggal']: 'Tanggal'})
                     else:
                         continue # Skip this sheet if no Tanggal
                
                # Ensure Crusher column exists
                if 'Crusher' not in df_sheet.columns:
                    df_sheet['Crusher'] = None

                # Keep only relevant columns if they exist (to avoid excessive junk), 
                # but also allow dynamic columns? 
                # Better to align with standard_cols for the app views
                # We simply ensure standard cols exist, but keep others? 
                # Safer: Only keep standard cols to avoid issues with concat if they differ
                # Actually, adding missing standard cols is enough
                for col in standard_cols:
                    if col not in df_sheet.columns:
                        df_sheet[col] = None
                        
                # Reorder to standard (optional but good for debugging)
                current_cols = [c for c in standard_cols if c in df_sheet.columns]
                df_sheet = df_sheet[current_cols]
                        
                all_dfs.append(df_sheet)
                
            except Exception as e:
                print(f"Error reading sheet {sheet}: {e}")
                continue
        
        if not all_dfs:
            return pd.DataFrame()
            
        df = pd.concat(all_dfs, ignore_index=True)
        
        # --- Post-Processing ---
        # Filter out potential repeats
        df = df[df['Bulan'] != 'Bulan'].copy()
        
        # Numeric conversions
        for col in ['Bulan', 'Shift', 'Durasi', 'Tahun', 'Week']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        # Date parsing
        # FIX: Use safe_parse_date_column to handle Excel serial numbers (45659 -> 2026)
        if 'Tanggal' in df.columns:
            df['Tanggal'] = safe_parse_date_column(df['Tanggal'])
            # CRITICAL: Convert to datetime64 to support .dt accessor and dashboard filtering
            df['Tanggal'] = pd.to_datetime(df['Tanggal'], errors='coerce')
        
        # Filter valid rows
        df = df[df['Bulan'].notna()]
        df = df[df['Durasi'].notna()]
        # Remove NaT dates 
        df = df[df['Tanggal'].notna()]
        
        # Enforce Start Date >= 2026-01-01 (Strict User Request)
        df = df[df['Tanggal'] >= pd.Timestamp('2026-01-01')]
        
        # FIX: Format Start/End Time to String (HH:MM) to avoid 1900-01-01 display
        def format_time_col(val):
            if pd.isna(val): return ""
            s_val = str(val)
            # If default datetime str "1900-01-01 04:30:00" -> extract "04:30"
            if " " in s_val:
                try:
                    return s_val.split(" ")[1][:5]
                except:
                    pass
            # If just a time "04:30:00" -> "04:30"
            if ":" in s_val and len(s_val) >= 5:
                return s_val[:5]
            return s_val

        if 'Start' in df.columns:
            df['Start'] = df['Start'].apply(format_time_col)
        if 'End' in df.columns:
            df['End'] = df['End'].apply(format_time_col)

        # -------------------------------------------------------------
        # CRITICAL FIX: HANDLE SHIFTED COLUMNS FOR 2026 (Missing Header)
        # -------------------------------------------------------------
        # Symptoms: 'Alat' contains Crusher names (LSC, MS), 'Remarks' contains Alat, etc.
        # This happens because 'Crusher' column is physically present in 2026 rows but missing in Header.
        
        # Check if shift is needed: Look for signatures in 'Alat'
        # Safely convert to string
        if 'Alat' in df.columns:
            mask_shifted = df['Alat'].astype(str).str.contains(r'LSC|MS |Batu', case=False, na=False) | (df['Tahun'] == 2026)
            
            if mask_shifted.any():
                # Define shift map: New_Column <- Current_Column
                # Based on Excel debug: Durasi -> [Crusher] -> Alat -> Remarks -> Kelompok...
                shift_map = [
                    ('Crusher', 'Alat'),
                    ('Alat', 'Remarks'),
                    ('Remarks', 'Kelompok Masalah'),
                    ('Kelompok Masalah', 'Gangguan'),
                    ('Gangguan', 'Info CCR'),
                    ('Info CCR', 'Sub Komponen'),
                    ('Sub Komponen', 'Keterangan'),
                    ('Keterangan', 'Penyebab'),
                    ('Penyebab', 'Identifikasi Masalah'),
                    ('Identifikasi Masalah', 'Action'),
                    ('Action', 'Plan'),
                    ('Plan', 'PIC'),
                    ('PIC', 'Status'),
                    ('Status', 'Due Date'),
                    ('Due Date', 'Spare Part'),
                    ('Spare Part', 'Info Spare Part'),
                    ('Info Spare Part', 'Link/Lampiran')
                ]
                
                # Apply shift ONLY to affected rows
                for new_col, old_col in shift_map:
                    if old_col in df.columns:
                        if new_col not in df.columns: df[new_col] = None
                        df.loc[mask_shifted, new_col] = df.loc[mask_shifted, old_col]

        # Standardize Kelompok Masalah
        kelompok_map = {
            'Delay Operational CC': 'Delay Operational CC',
            'Delay operational CC': 'Delay Operational CC',
            'delay Operational CC': 'Delay Operational CC',
            'Delay Operational DBLH': 'Delay Operational DBLH',
            'Downtime Belt Conveyor': 'Downtime Belt Conveyor',
            'Downtime belt conveyor': 'Downtime Belt Conveyor',
            'Downtime Crusher': 'Downtime Crusher',
            'downtime crusher': 'Downtime Crusher',
        }
        if 'Kelompok Masalah' in df.columns:
            df['Kelompok Masalah'] = df['Kelompok Masalah'].replace(kelompok_map)
            df = df[df['Kelompok Masalah'].notna()]
        
        # Map Bulan Names
        bulan_names = {
            1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
            5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
            9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
        }
        df['Bulan_Name'] = df['Bulan'].map(bulan_names)
        
        df = df.reset_index(drop=True)
        return df

    except Exception as e:
        print(f"Error loading gangguan: {e}")
        return pd.DataFrame()
        import traceback
        traceback.print_exc()
        return pd.DataFrame()


def get_gangguan_summary(df):
    """
    Generate summary statistics dari data gangguan
    Returns: dict dengan KPI metrics
    """
    if df.empty:
        return {
            'total_incidents': 0,
            'total_downtime': 0,
            'mttr': 0,
            'total_alat': 0,
            'top_gangguan': '-',
            'top_alat': '-'
        }
    
    return {
        'total_incidents': len(df),
        'total_downtime': df['Durasi'].sum(),
        'mttr': df['Durasi'].mean(),
        'total_alat': df['Alat'].nunique(),
        'top_gangguan': df['Gangguan'].value_counts().index[0] if len(df) > 0 else '-',
        'top_alat': df['Alat'].value_counts().index[0] if len(df) > 0 else '-'
    }


@st.cache_data(ttl=CACHE_TTL)
def load_bbm_enhanced():
    """
    Load and transform BBM data to Long Format [Date, Unit, Category, Liters]
    Handles dynamic date columns (1-31)
    """
    df = None
    sheet_name = 'BBM'
    
    # Try OneDrive then Local
    if ONEDRIVE_LINKS.get("monitoring"):
        file_buffer = download_from_onedrive(ONEDRIVE_LINKS["monitoring"])
        if file_buffer:
            try:
                df = pd.read_excel(file_buffer, sheet_name=sheet_name)
            except: pass
            
    if df is None:
        local_path = load_from_local("monitoring")
        if local_path:
            try:
                df = pd.read_excel(local_path, sheet_name=sheet_name)
            except: pass
            
    if df is None or df.empty:
        return pd.DataFrame()
        
    try:
        # Cleanup
        if 'Total' in df.columns:
            df = df[df['Total'] != 'Total'] # Remove footer rows if any
            
        # Identify Metadata columns vs Date columns
        # Based on debug: ['No', 'Alat Berat', 'Tipe Alat', 'Kategori', '1', '2', ... 'Total']
        meta_cols = ['No', 'Alat Berat', 'Tipe Alat', 'Kategori', 'Total']
        
        # Ensure regex/type matching for '1', '2', '31' columns
        # Force columns to string for easier matching, but keep original for melt
        df.columns = [str(c) for c in df.columns]
        
        # Re-identify date columns (digits 1-31)
        date_cols = [c for c in df.columns if c.isdigit() and 1 <= int(c) <= 31]
        
        # Melt (Unpivot) to Long Format
        # id_vars are the metadata columns that exist
        current_meta = [c for c in meta_cols if c in df.columns]
        
        if not date_cols:
            return pd.DataFrame() # No date columns found
            
        df_melted = df.melt(id_vars=current_meta, 
                           value_vars=date_cols,
                           var_name='Day', value_name='Liters')
        
        # Validation & Formatting
        df_melted['Liters'] = pd.to_numeric(df_melted['Liters'], errors='coerce').fillna(0)
        df_melted = df_melted[df_melted['Liters'] > 0]  # Optimize: remove zero records
        
        # Create full Date column
        # Assuming current year (2026) and month (January) from context or file
        current_year = 2026
        current_month = 1 
        
        # Note: In a real app, month should be inferred from filename or user input.
        # For now, we fix to Jan 2026 as per user context.
        
        dates = []
        for day in df_melted['Day']:
            try:
                dates.append(pd.Timestamp(year=current_year, month=current_month, day=int(day)))
            except:
                dates.append(pd.NaT)
        df_melted['Date'] = dates
        df_melted = df_melted.dropna(subset=['Date'])
        
        # Standardize columns
        final_cols = {
            'Alat Berat': 'Unit',
            'Tipe Alat': 'Type',
            'Kategori': 'Category' 
        }
        df_melted = df_melted.rename(columns=final_cols)
        
        # Ensure required columns exist
        required_cols = ['Date', 'Unit', 'Type', 'Category', 'Liters']
        for col in required_cols:
            if col not in df_melted.columns:
                 df_melted[col] = None
                 
        return df_melted[required_cols].reset_index(drop=True)
        
    except Exception as e:
        print(f"Error loading BBM enhanced: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=CACHE_TTL)
def load_ritase_enhanced():
    """
    Load and transform Ritase data to Long Format [Date, Shift, Location, Ritase]
    """
    df = None
    sheet_name = 'Ritase'
    
    # Try OneDrive then Local
    if ONEDRIVE_LINKS.get("monitoring"):
        file_buffer = download_from_onedrive(ONEDRIVE_LINKS["monitoring"])
        if file_buffer:
            try:
                df = pd.read_excel(file_buffer, sheet_name=sheet_name)
            except: pass
            
    if df is None:
        local_path = load_from_local("monitoring")
        if local_path:
            try:
                df = pd.read_excel(local_path, sheet_name=sheet_name)
            except: pass
            
    if df is None or df.empty:
        return pd.DataFrame()
        
    try:
        # Standardize Date
        if 'Tanggal' not in df.columns:
             # Try finding date column by type
             for col in df.columns:
                 if pd.api.types.is_datetime64_any_dtype(df[col]):
                     df = df.rename(columns={col: 'Tanggal'})
                     break
                     
        if 'Tanggal' in df.columns:
            df['Tanggal'] = safe_parse_date_column(df['Tanggal'])
            df = df[df['Tanggal'].notna()]
        else:
             return pd.DataFrame() # Parsing failed
        
        # Clean Shift
        if 'Shift' in df.columns:
            df = df[df['Shift'].isin([1, 2, 3, '1', '2', '3'])]
            df['Shift'] = pd.to_numeric(df['Shift'], errors='coerce').astype('Int64')
        else:
            df['Shift'] = 1 # Default if missing
            
        # Identify Location columns (Fronts, Stockpiles, etc.)
        # Exclude metadata columns and 'Unnamed' junk
        exclude_cols = ['Tanggal', 'Shift', 'Pengawasan', 'Total', 'No', 'Day', 'Date']
        
        # Filter columns that are NOT metadata AND NOT Unnamed
        loc_cols = [c for c in df.columns if c not in exclude_cols and not str(c).startswith('Unnamed') and 'Total' not in str(c)]
        
        if not loc_cols:
            return pd.DataFrame()
            
        # Melt to Long Format
        df_melted = df.melt(id_vars=['Tanggal', 'Shift'], 
                           value_vars=loc_cols,
                           var_name='Location', value_name='Ritase')
        
        # Filter valid data
        df_melted['Ritase'] = pd.to_numeric(df_melted['Ritase'], errors='coerce').fillna(0)
        df_melted = df_melted[df_melted['Ritase'] > 0]
        
        # Clean Location Names (remove 'Sum of' if present)
        df_melted['Location'] = df_melted['Location'].astype(str).str.replace('Sum of ', '', regex=False)
        
        return df_melted[['Tanggal', 'Shift', 'Location', 'Ritase']].reset_index(drop=True)
        
    except Exception as e:
        print(f"Error loading Ritase enhanced: {e}")
        return pd.DataFrame()


# ==========================================
# BACKWARD COMPATIBILITY ALIASES
# ==========================================
# These functions are kept to prevent ImportErrors in other modules
# that might still reference the old names.
load_bbm = load_bbm_enhanced
load_ritase = load_ritase_enhanced

@st.cache_data(ttl=CACHE_TTL)
def load_gangguan():
    """Legacy wrapper for load_gangguan_all or load_gangguan_monitoring"""
    return load_gangguan_monitoring() # Basic fallback

@st.cache_data(ttl=CACHE_TTL)
def load_analisa_produksi(bulan='Januari'):
    """Legacy wrapper for backward compatibility"""
    # Load all data first
    df_all = load_analisa_produksi_all()
    if df_all.empty:
        return pd.DataFrame()
        
    # Filter by month name
    # Ensure bulan matches the new format or map it if necessary
    # The new function returns 'Month' column with full names (Januari, Februari, etc.)
    if 'Month' in df_all.columns:
        return df_all[df_all['Month'] == bulan]
    
    return pd.DataFrame()


@st.cache_data(ttl=CACHE_TTL)
def load_analisa_produksi_all():
    """Load Analisa Produksi for S-Curve (Plan vs Actual)"""
    df = None
    sheet_name = 'Analisa Produksi'
    
    # Try OneDrive then Local
    if ONEDRIVE_LINKS.get("monitoring"):
        file_buffer = download_from_onedrive(ONEDRIVE_LINKS["monitoring"])
        if file_buffer:
            try:
                df = pd.read_excel(file_buffer, sheet_name=sheet_name)
            except: pass
            
    if df is None:
        local_path = load_from_local("monitoring")
        if local_path:
            try:
                df = pd.read_excel(local_path, sheet_name=sheet_name)
            except: pass
            
    if df is None or df.empty:
        return pd.DataFrame()
    
    try:
        # The sheet has multiple months horizontally.
        # Structure: [Januari] [Februari] side by side
        # Need to iterate and extract
        
        processed_data = []
        months = {'Januari': 0, 'Februari': 5, 'Maret': 10, 'April': 15, 'Mei': 20, 'Juni': 25, 
                  'Juli': 30, 'Agustus': 35, 'September': 40, 'Oktober': 45, 'November': 50, 'Desember': 55}
                  
        for month_name, start_col in months.items():
            try:
                if start_col + 3 >= len(df.columns):
                    continue
                    
                # Extract block
                df_month = df.iloc[1:33, start_col:start_col+4].copy() # Assuming 31 days max + 1 header
                df_month.columns = ['Day', 'Plan', 'Actual', 'Ach']
                
                # Clean
                df_month = df_month.dropna(subset=['Day'])
                df_month = df_month[pd.to_numeric(df_month['Day'], errors='coerce').notna()]
                
                # Add Metadata
                df_month['Month'] = month_name
                
                # Convert numbers
                df_month['Plan'] = pd.to_numeric(df_month['Plan'], errors='coerce').fillna(0)
                df_month['Actual'] = pd.to_numeric(df_month['Actual'], errors='coerce').fillna(0)
                
                # Create Date (Assuming Year 2025)
                # Need mapping for month number
                month_num = list(months.keys()).index(month_name) + 1
                dates = []
                for day in df_month['Day']:
                    try:
                        dates.append(pd.Timestamp(year=2025, month=month_num, day=int(day)))
                    except:
                        dates.append(pd.NaT)
                df_month['Date'] = dates
                df_month = df_month.dropna(subset=['Date'])
                
                processed_data.append(df_month[['Date', 'Month', 'Plan', 'Actual']])
                
            except Exception as e:
                continue
                
        if not processed_data:
            return pd.DataFrame()
            
        return pd.concat(processed_data, ignore_index=True)
        
    except Exception as e:
        print(f"Error loading Analisa Produksi: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=CACHE_TTL)
def load_ritase():
    """Load data ritase"""
    df = None
    
    if ONEDRIVE_LINKS.get("monitoring"):
        file_buffer = download_from_onedrive(ONEDRIVE_LINKS["monitoring"])
        if file_buffer:
            try:
                df = pd.read_excel(file_buffer, sheet_name='Ritase')
            except:
                pass
    
    if df is None:
        local_path = load_from_local("monitoring")
        if local_path:
            try:
                df = pd.read_excel(local_path, sheet_name='Ritase')
            except:
                pass
    
    if df is None:
        return pd.DataFrame()
    
    try:
        cols_keep = ['Tanggal', 'Shift', 'Pengawasan', 'Front B LS', 'Front B Clay', 
                    'Front B LS MIX', 'Front C LS', 'Front C LS MIX', 'PLB LS', 
                    'PLB SS', 'PLT SS', 'PLT MIX', 'Timbunan', 'Stockpile 6  SS', 
                    'PLT LS MIX', 'Stockpile 6 ']
        
        available_cols = [col for col in cols_keep if col in df.columns]
        df = df[available_cols].copy()
        
        df['Tanggal'] = safe_parse_date_column(df['Tanggal'])
        df = df[df['Tanggal'].notna()]
        
        df = df[df['Shift'].isin([1, 2, 3, '1', '2', '3'])]
        df['Shift'] = df['Shift'].astype(str)
        
        numeric_cols = [col for col in df.columns if col not in ['Tanggal', 'Shift', 'Pengawasan']]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        df = df.reset_index(drop=True)
        return df
    except:
        return pd.DataFrame()


@st.cache_data(ttl=CACHE_TTL)
def load_daily_plan():
    """Load data daily plan scheduling"""
    df = None
    
    if ONEDRIVE_LINKS.get("daily_plan"):
        file_buffer = download_from_onedrive(ONEDRIVE_LINKS["daily_plan"])
        if file_buffer:
            try:
                df = pd.read_excel(file_buffer, sheet_name='Scheduling', skiprows=1)
            except:
                pass
    
    if df is None:
        local_path = load_from_local("daily_plan")
        if local_path:
            try:
                df = pd.read_excel(local_path, sheet_name='Scheduling', skiprows=1)
            except:
                pass
    
    if df is None:
        return pd.DataFrame()
    
    try:
        new_cols = ['No', 'Hari', 'Tanggal', 'Shift', 'Batu Kapur', 'Silika', 
                    'Clay', 'Alat Muat', 'Alat Angkut', 'Blok', 'Grid', 'ROM', 'Keterangan']
        
        if len(df.columns) >= len(new_cols):
            df.columns = new_cols + list(df.columns[len(new_cols):])
        
        df = df.iloc[1:].copy()
        df['Tanggal'] = safe_parse_date_column(df['Tanggal'])
        
        df = df[df['Hari'].notna()]
        df = df[df['Hari'] != 'Hari']
        
        cols_keep = ['Hari', 'Tanggal', 'Shift', 'Batu Kapur', 'Silika', 'Clay', 
                     'Alat Muat', 'Alat Angkut', 'Blok', 'Grid', 'ROM', 'Keterangan']
        available = [c for c in cols_keep if c in df.columns]
        df = df[available].copy()
        
        df = df.dropna(how='all')
        df = df.reset_index(drop=True)
        
        return df
    except:
        return pd.DataFrame()


@st.cache_data(ttl=CACHE_TTL)
def load_realisasi():
    """Load data realisasi"""
    df = None
    
    if ONEDRIVE_LINKS.get("daily_plan"):
        file_buffer = download_from_onedrive(ONEDRIVE_LINKS["daily_plan"])
        if file_buffer:
            try:
                df = pd.read_excel(file_buffer, sheet_name='W22 realisasi', skiprows=1)
            except:
                pass
    
    if df is None:
        local_path = load_from_local("daily_plan")
        if local_path:
            try:
                df = pd.read_excel(local_path, sheet_name='W22 realisasi', skiprows=1)
            except:
                pass
    
    if df is None:
        return pd.DataFrame()
    
    try:
        new_cols = ['No', 'Hari', 'Tanggal', 'Week', 'Shift', 'Batu Kapur', 'Silika', 
                    'Timbunan', 'Alat Bor', 'Alat Muat', 'Alat Angkut', 'Blok', 'Grid', 
                    'ROM', 'Keterangan']
        
        if len(df.columns) >= len(new_cols):
            df.columns = new_cols + list(df.columns[len(new_cols):])
        
        df = df.iloc[1:].copy()
        df['Tanggal'] = safe_parse_date_column(df['Tanggal'])
        
        df = df[df['Hari'].notna()]
        df = df[df['Hari'] != 'Hari']
        
        cols_keep = ['Hari', 'Tanggal', 'Week', 'Shift', 'Batu Kapur', 'Silika', 
                     'Timbunan', 'Alat Bor', 'Alat Muat', 'Alat Angkut', 'Blok', 
                     'Grid', 'ROM', 'Keterangan']
        available = [c for c in cols_keep if c in df.columns]
        df = df[available].copy()
        
        df = df.dropna(how='all')
        df = df.reset_index(drop=True)
        
        return df
    except:
        return pd.DataFrame()

# ============================================================
# NEW MONITORING FUNCTIONS (ADDED)
# ============================================================

@st.cache_data(ttl=CACHE_TTL)
def load_bbm_enhanced():
    """Load data BBM dengan kategori alat"""
    with open(os.devnull, "w") as f:
        f.write("Starting load_bbm_enhanced\n")
        
        df = load_bbm_raw() # Use raw loader foundation
        f.write(f"Raw Shape: {df.shape}\n")
        f.write(f"Raw Columns: {list(df.columns)}\n")
        
        if df.empty:
            return pd.DataFrame()
        
        try:
            # 1. Clean Headers (Search for 'Alat Berat' row)
            if 'Alat Berat' not in df.columns:
                # Try to find header row
                for i in range(min(5, len(df))):
                    row_str = df.iloc[i].astype(str).str.cat(sep=' ')
                    if 'Alat Berat' in row_str:
                        df.columns = df.iloc[i]
                        df = df.iloc[i+1:].reset_index(drop=True)
                        f.write(f"Found header at row {i}\n")
                        break
            
            # 2. Standardize Columns
            # Rename 'Alat Berat' to 'Unit'
            col_map = {c: c for c in df.columns}
            for c in df.columns:
                if 'Alat Berat' in str(c): col_map[c] = 'Unit'
                if 'Tipe' in str(c): col_map[c] = 'Type'
                if 'Kategori' in str(c): col_map[c] = 'Kategori'
                
            df = df.rename(columns=col_map)
            f.write(f"Renamed Columns: {list(df.columns)}\n")
            
            # 3. Add Kategori if missing
            if 'Kategori' not in df.columns and 'Unit' in df.columns:
                df['Kategori'] = df['Unit'].apply(lambda x: 
                    'Excavator' if 'Excavator' in str(x) else 
                    'Dump Truck' if 'Dump' in str(x) or 'SCANIA' in str(x).upper() else 
                    'Support'
                )
            
            # 4. Melt Date Columns for Analysis
            # Identify date columns (1-31)
            date_cols = [c for c in df.columns if str(c).strip().isdigit() and 1 <= int(str(c).strip()) <= 31]
            f.write(f"Date Cols Found: {date_cols}\n")
            
            if date_cols and 'Unit' in df.columns:
                id_vars = ['Unit']
                if 'Kategori' in df.columns: id_vars.append('Kategori')
                
                df_melted = df.melt(id_vars=id_vars, value_vars=date_cols, var_name='Day', value_name='Liters')
                f.write(f"Melted Shape: {df_melted.shape}\n")
                
                df_melted['Liters'] = pd.to_numeric(df_melted['Liters'], errors='coerce').fillna(0)
                df_melted = df_melted[df_melted['Liters'] > 0]
                f.write(f"Final Filtered Shape: {df_melted.shape}\n")
                
                return df_melted
            
            f.write("Returning original DF (Melting failed or no date cols)\n")
            return df
        except Exception as e:
            f.write(f"Error: {e}\n")
            # st.error(f"Error in load_bbm_enhanced: {e}")
            return df


@st.cache_data(ttl=CACHE_TTL)
def load_bbm_detail():
    """Load BBM dengan detail per hari (melted format)"""
    df = load_bbm_enhanced()
    
    if df.empty:
        return pd.DataFrame()
    
    try:
        day_cols = [col for col in df.columns if str(col).isdigit()]
        if not day_cols:
            return pd.DataFrame()
        
        id_vars = ['No', 'Alat Berat', 'Tipe Alat']
        if 'Kategori' in df.columns:
            id_vars.append('Kategori')
        
        df_melted = df.melt(
            id_vars=id_vars,
            value_vars=day_cols,
            var_name='Tanggal',
            value_name='BBM_Liter'
        )
        
        df_melted['Tanggal'] = pd.to_numeric(df_melted['Tanggal'], errors='coerce')
        df_melted['BBM_Liter'] = pd.to_numeric(df_melted['BBM_Liter'], errors='coerce').fillna(0)
        df_melted = df_melted[df_melted['BBM_Liter'] > 0]
        
        return df_melted
    except:
        return pd.DataFrame()


@st.cache_data(ttl=CACHE_TTL)
def load_ritase_enhanced():
    """Load data ritase dengan Total_Ritase dan Bulan"""
    df = load_ritase()
    
    if df.empty:
        return pd.DataFrame()
    
    try:
        df['Shift'] = pd.to_numeric(df['Shift'], errors='coerce').fillna(1).astype(int)
        
        front_cols = ['Front B LS', 'Front B Clay', 'Front B LS MIX', 
                     'Front C LS', 'Front C LS MIX', 'PLB LS', 'PLB SS', 
                     'PLT SS', 'PLT MIX', 'Timbunan', 'Stockpile 6  SS', 
                     'PLT LS MIX', 'Stockpile 6 ']
        
        available_fronts = [c for c in front_cols if c in df.columns]
        df['Total_Ritase'] = df[available_fronts].sum(axis=1)
        
        if 'Tanggal' in df.columns:
            df['Tanggal'] = pd.to_datetime(df['Tanggal'], errors='coerce')
            df['Bulan'] = df['Tanggal'].dt.month
            df['Bulan_Nama'] = df['Tanggal'].dt.strftime('%B')
        
        return df
    except:
        return df


@st.cache_data(ttl=CACHE_TTL)
def load_ritase_by_front():
    """Load ritase aggregated by front/location"""
    df = load_ritase_raw() # Use raw
    
    if df.empty:
        return pd.DataFrame()
    
    try:
        # 1. Header Detection
        if 'Front' not in str(df.columns):
            for i in range(min(5, len(df))):
                row_str = df.iloc[i].astype(str).str.cat(sep=' ')
                if 'Front' in row_str or 'Shift' in row_str:
                    df.columns = df.iloc[i]
                    df = df.iloc[i+1:].reset_index(drop=True)
                    break
                    
        # 2. Identify Front Columns
        # Filter out metadata
        exclude = ['Tanggal', 'Shift', 'Pengawasan', 'Total', 'No', 'Day', 'Date', 'Month', 'Year', 'Bulan']
        front_cols = [c for c in df.columns if c not in exclude and not str(c).startswith('Unnamed')]
        
        # 3. Aggregate
        # Convert to numeric first
        for c in front_cols:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
            
        totals = df[front_cols].sum().reset_index()
        totals.columns = ['Front', 'Total_Ritase']
        totals = totals[totals['Total_Ritase'] > 0]
        totals = totals.sort_values('Total_Ritase', ascending=False)
        
        return totals
    except Exception as e:
        # st.error(f"Error in Ritase: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=CACHE_TTL)
def load_tonase():
    """Load data tonase per jam"""
    df = None
    
    if ONEDRIVE_LINKS.get("monitoring"):
        file_buffer = download_from_onedrive(ONEDRIVE_LINKS["monitoring"])
        if file_buffer:
            try:
                df = pd.read_excel(file_buffer, sheet_name='Tonase', header=1)
            except:
                pass
    
    if df is None:
        local_path = load_from_local("monitoring")
        if local_path:
            try:
                df = pd.read_excel(local_path, sheet_name='Tonase', header=1)
            except:
                pass
    
    if df is None:
        return pd.DataFrame()
    
    try:
        # Safety: Rename first column to Tanggal
        if len(df.columns) > 0:
             df = df.rename(columns={df.columns[0]: 'Tanggal', df.columns[1]: 'Ritase'})

        # Filter repeated headers (Fix DateParseError)
        # Filter repeated headers (Fix DateParseError)
        if 'Tanggal' in df.columns:
            df = df[df['Tanggal'].astype(str).str.strip() != 'Tanggal']
            
            # Handle Excel Serial Dates
            # Force numeric first
            df['Tanggal_Num'] = pd.to_numeric(df['Tanggal'], errors='coerce')
            
            # If successful (not all NaNs), use it
            if df['Tanggal_Num'].notna().any():
                df['Tanggal'] = pd.to_datetime(df['Tanggal_Num'], unit='D', origin='1899-12-30')
            else:
                df['Tanggal'] = pd.to_datetime(df['Tanggal'], errors='coerce')
                
            df = df[df['Tanggal'].notna()]
        
        hour_cols = [col for col in df.columns if '-' in str(col) and col not in ['Tanggal', 'Ritase']]
        for col in hour_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        if 'Total' in df.columns:
            df['Total'] = pd.to_numeric(df['Total'], errors='coerce').fillna(0)
        
        if 'Tanggal' in df.columns:
            df['Bulan'] = df['Tanggal'].dt.month
            
        df = df.reset_index(drop=True)
        return df
    except:
        return pd.DataFrame()


@st.cache_data(ttl=CACHE_TTL)
def load_tonase_hourly():
    """Load tonase in hourly format (melted)"""
    df = load_tonase()
    if df.empty:
        return pd.DataFrame()
    
    try:
        hour_cols = [col for col in df.columns if '-' in str(col) and col not in ['Tanggal', 'Ritase', 'Total']]
        if not hour_cols:
            return pd.DataFrame()
        
        df_melted = df.melt(
            id_vars=['Tanggal', 'Bulan'],
            value_vars=hour_cols,
            var_name='Jam',
            value_name='Tonase'
        )
        df_melted['Tonase'] = pd.to_numeric(df_melted['Tonase'], errors='coerce').fillna(0)
        return df_melted
    except:
        return pd.DataFrame()


@st.cache_data(ttl=CACHE_TTL)
def load_analisa_produksi_all():
    """Load semua data analisa produksi (Jan-Des)"""
    bulan_map = {
        'Januari': 0, 'Februari': 5, 'Maret': 10, 'April': 15,
        'Mei': 20, 'Juni': 25, 'Juli': 30, 'Agustus': 35,
        'September': 40, 'Oktober': 45, 'November': 50, 'Desember': 55
    }
    
    df = None
    if ONEDRIVE_LINKS.get("monitoring"):
        file_buffer = download_from_onedrive(ONEDRIVE_LINKS["monitoring"])
        if file_buffer:
            try:
                df = pd.read_excel(file_buffer, sheet_name='Analisa Produksi')
            except:
                pass
    
    if df is None:
        local_path = load_from_local("monitoring")
        if local_path:
            print(f"DEBUG Loading Analisa from: {local_path}")
            try:
                df = pd.read_excel(local_path, sheet_name='Analisa Produksi')
            except Exception as e:
                print(f"DEBUG Error loading Analisa: {e}")
                pass
    
    if df is None:
        print("DEBUG Analisa df is None")
        return pd.DataFrame()
    
    try:
        with open(os.devnull, "w") as f:
            f.write("Starting load_analisa_produksi_all\n")
            f.write(f"Columns: {list(df.columns)}\n")
            
            # Dynamic Header Scanning for Analysis Production
            # Row 0 contains headers like 'Januari 2025', 'Februari 2025', ... 'Januari 2026'
            
            # Read header row (Row 0) to identify blocks
            df_header = df.iloc[0:1]
            f.write(f"Row 0 samples: {df_header.iloc[0, :10].tolist()}\n")
            
            block_starts = []
            # Typo handling
            months_indo = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
                           'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
            months_indo_extended = months_indo + ['Februai']
        
            for col_idx, col_name in enumerate(df.columns):
                val = str(col_name).strip()
                f.write(f"Scanning col {col_idx}: {val}\n")
                # Check matches
                for m in months_indo_extended:
                    if m in val:
                        f.write(f"Match found: {m} in {val}\n")
                        year = 2026
                        if '2025' in val: year = 2025
                        
                        # Map typo to real month
                        real_month = 'Februari' if m == 'Februai' else m
                        block_starts.append((col_idx, real_month, val, year))
                        break
        
            f.write(f"Block Starts: {block_starts}\n")
            all_data = []
            
            for start_col, month_name, header_name, year in block_starts:
                try:
                    if start_col + 3 >= len(df.columns):
                        continue
                        
                    # Skip sub-header row (Row 0 is sub-header 'Tanggal')
                    # DF Index 0: Subheader
                    # DF Index 1: Data
                    # Use iloc[1:33] to capture data starting from Row 1
                    df_block = df.iloc[1:33, start_col:start_col+4].copy()
                    df_block.columns = ['Day', 'Plan', 'Actual', 'Ach']
                    
                    # Check if Day column is empty or contains "Tanggal"
                    df_block = df_block[df_block['Day'].astype(str) != 'Tanggal']
                    df_block = df_block[df_block['Day'].notna()]
                    
                    f.write(f"Block shape after filter: {df_block.shape}\n")
                    if not df_block.empty:
                        f.write(f"Head: {df_block.head().to_string()}\n")
                    else:
                        f.write(f"Block empty after filter. Raw head: {df.iloc[1:5, start_col].tolist()}\n")
                        
                    if df_block.empty:
                        continue
                    
                    # Determine parsing strategy
                    first_val = df_block['Day'].iloc[0]
                    is_full_date = False
                    
                    if isinstance(first_val, (pd.Timestamp, datetime)):
                        is_full_date = True
                    elif isinstance(first_val, (int, float)) and first_val > 31:
                        is_full_date = True
                    
                    dates = []
                    if is_full_date:
                        # Use the column directly, parse if needed
                        if pd.api.types.is_numeric_dtype(df_block['Day']):
                            dates = pd.to_datetime(df_block['Day'], unit='D', origin='1899-12-30').tolist()
                        else:
                            dates = pd.to_datetime(df_block['Day'], errors='coerce').tolist()
                    else:
                        # Construct from Day number
                        month_num = months_indo.index(month_name) + 1
                        for day in df_block['Day']:
                            try:
                                d = int(day)
                                dates.append(pd.Timestamp(year=year, month=month_num, day=d))
                            except:
                                dates.append(pd.NaT)
                    
                    df_block['Date'] = dates
                    df_block['Month'] = month_name
                    df_block['Year'] = year
                    
                    df_block = df_block.rename(columns={
                        'Date': 'Tanggal',
                        'Plan': 'Plan', 
                        'Actual': 'Aktual',
                        'Ach': 'Ketercapaian'
                    })
                    
                    df_block = df_block.dropna(subset=['Tanggal'])
                    
                    # Convert numerics
                    for col in ['Plan', 'Aktual', 'Ketercapaian']:
                        df_block[col] = pd.to_numeric(df_block[col], errors='coerce').fillna(0)
                    
                    all_data.append(df_block[['Tanggal', 'Bulan', 'Tahun', 'Plan', 'Aktual', 'Ketercapaian']] 
                                    if 'Bulan' in df_block.columns else 
                                    df_block[['Tanggal', 'Month', 'Year', 'Plan', 'Aktual', 'Ketercapaian']])
                    
                except Exception as e:
                    # print(f"Error processing block {header_name}: {e}")
                    continue
                    
            if all_data:
                final_df = pd.concat(all_data, ignore_index=True)
                # Rename Month/Year to standard if needed or keep helper cols
                final_df = final_df.rename(columns={'Month': 'Bulan', 'Year': 'Tahun'})
                return final_df
                
            return pd.DataFrame()

    except Exception as e:
        print(f"Error loading Analisa Produksi: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=CACHE_TTL)
def load_pengiriman():
    """Load data tonase pengiriman LS & SS"""
    df = None
    
    if ONEDRIVE_LINKS.get("monitoring"):
        file_buffer = download_from_onedrive(ONEDRIVE_LINKS["monitoring"])
        if file_buffer:
            try:
                df = pd.read_excel(file_buffer, sheet_name='TONASE Pengiriman ')
            except:
                pass
    
    if df is None:
        local_path = load_from_local("monitoring")
        if local_path:
            try:
                df = pd.read_excel(local_path, sheet_name='TONASE Pengiriman ')
            except:
                pass
    
    if df is None:
        return pd.DataFrame()
    
    try:
        all_data = []
        bulan_sections = {
            'Juni': (1, 7), 'Juli': (8, 16), 'Agustus': (21, 29),
            'September': (30, 38), 'Oktober': (39, 47), 
            'November': (48, 56), 'Desember': (57, 64)
        }
        
        for bulan, (start, end) in bulan_sections.items():
            try:
                section = df.iloc[2:, start:end].copy()
                if section.shape[1] >= 6:
                    section.columns = ['Tanggal', 'Shift', 'AP_LS', 'AP_LS_MK3', 'AP_SS', 'Total_LS'][:section.shape[1]]
                    section['Bulan'] = bulan
                    section = section[section['Tanggal'].notna()]
                    all_data.append(section)
            except:
                continue
        
        if all_data:
            result = pd.concat(all_data, ignore_index=True)
            for col in ['Shift', 'AP_LS', 'AP_LS_MK3', 'AP_SS', 'Total_LS']:
                if col in result.columns:
                    result[col] = pd.to_numeric(result[col], errors='coerce').fillna(0)
            return result
        return pd.DataFrame()
    except:
        return pd.DataFrame()


def parse_durasi_value(value):
    """
    Parse Durasi column - handle various formats safely.
    Durasi can be: numeric hours, timedelta, datetime, or time string.
    Returns hours as float, capped at reasonable max (24 hours).
    """
    MAX_DURASI_HOURS = 24  # Maximum reasonable downtime per incident
    
    if pd.isna(value):
        return 0.0
    
    try:
        # If already numeric (float/int)
        if isinstance(value, (int, float)):
            hours = float(value)
            # Check if it looks like an Excel serial time (0-1 range = fraction of day)
            if 0 < hours < 1:
                hours = hours * 24  # Convert fraction of day to hours
            # Cap at max reasonable value
            return min(abs(hours), MAX_DURASI_HOURS)
        
        # If it's a timedelta
        if isinstance(value, pd.Timedelta):
            hours = value.total_seconds() / 3600
            return min(abs(hours), MAX_DURASI_HOURS)
        
        # If it's a datetime/time (interpret as duration from midnight)
        if isinstance(value, (datetime, pd.Timestamp)):
            # Extract hours and minutes as duration
            hours = value.hour + value.minute / 60
            return min(hours, MAX_DURASI_HOURS)
        
        # If it's a string like "2:30" or "02:30:00"
        if isinstance(value, str):
            value = value.strip()
            if ':' in value:
                parts = value.split(':')
                hours = int(parts[0]) + int(parts[1]) / 60
                return min(hours, MAX_DURASI_HOURS)
            # Try parsing as float
            hours = float(value)
            if 0 < hours < 1:
                hours = hours * 24
            return min(abs(hours), MAX_DURASI_HOURS)
        
        return 0.0
    except:
        return 0.0


@st.cache_data(ttl=CACHE_TTL)
def load_gangguan_monitoring():
    """Load gangguan dari sheet Gangguan di file Monitoring"""
    df = None
    
    if ONEDRIVE_LINKS.get("monitoring"):
        file_buffer = download_from_onedrive(ONEDRIVE_LINKS["monitoring"])
        if file_buffer:
            try:
                df = pd.read_excel(file_buffer, sheet_name='Gangguan')
            except:
                pass
    
    if df is None:
        local_path = load_from_local("monitoring")
        if local_path:
            try:
                df = pd.read_excel(local_path, sheet_name='Gangguan')
            except:
                pass
    
    if df is None:
        return pd.DataFrame()
    
    try:
        all_data = []
        bulan_cols = ['Tanggal', 'Week', 'Shift', 'Start', 'End', 'Durasi', 'Kendala', 'Masalah']
        
        for i in range(12):
            start_col = i * 9
            try:
                section = df.iloc[:, start_col:start_col+8].copy()
                if section.shape[1] < 8:
                    continue
                section.columns = bulan_cols
                section = section[section['Tanggal'].notna()]
                section = section[section['Durasi'].notna()]
                section['Tanggal'] = pd.to_datetime(section['Tanggal'], errors='coerce')
                
                # FIX: Use safe Durasi parser to prevent overflow
                section['Durasi'] = section['Durasi'].apply(parse_durasi_value)
                
                section['Shift'] = pd.to_numeric(section['Shift'], errors='coerce').fillna(1)
                section = section[section['Tanggal'].notna()]
                section = section[section['Durasi'] > 0]
                if not section.empty:
                    all_data.append(section)
            except:
                continue
        
        if all_data:
            result = pd.concat(all_data, ignore_index=True)
            result['Bulan'] = result['Tanggal'].dt.month
            return result
        return pd.DataFrame()
    except:
        return pd.DataFrame()


# ============================================================
# SUMMARY FUNCTIONS FOR MONITORING
# ============================================================

def get_bbm_summary(df_bbm):
    """Calculate BBM summary statistics"""
    if df_bbm is None or df_bbm.empty:
        return {'total_bbm': 0, 'avg_per_unit': 0, 'excavator_total': 0, 'dt_total': 0}
    
    total_bbm = df_bbm['Total'].sum() if 'Total' in df_bbm.columns else 0
    avg_per_unit = df_bbm['Total'].mean() if 'Total' in df_bbm.columns else 0
    
    excavator_total = dt_total = 0
    if 'Kategori' in df_bbm.columns:
        excavator_total = df_bbm[df_bbm['Kategori'] == 'Excavator']['Total'].sum()
        dt_total = df_bbm[df_bbm['Kategori'] == 'Dump Truck']['Total'].sum()
    
    return {'total_bbm': total_bbm, 'avg_per_unit': round(avg_per_unit, 0), 
            'excavator_total': excavator_total, 'dt_total': dt_total}


def get_ritase_summary(df_ritase):
    """Calculate ritase summary statistics"""
    if df_ritase is None or df_ritase.empty:
        return {'total_ritase': 0, 'avg_per_shift': 0, 'avg_per_day': 0}
    
    total_ritase = df_ritase['Total_Ritase'].sum() if 'Total_Ritase' in df_ritase.columns else 0
    avg_per_shift = df_ritase['Total_Ritase'].mean() if 'Total_Ritase' in df_ritase.columns else 0
    
    avg_per_day = 0
    if 'Tanggal' in df_ritase.columns and 'Total_Ritase' in df_ritase.columns:
        daily = df_ritase.groupby('Tanggal')['Total_Ritase'].sum()
        avg_per_day = daily.mean() if len(daily) > 0 else 0
    
    return {'total_ritase': total_ritase, 'avg_per_shift': round(avg_per_shift, 0), 
            'avg_per_day': round(avg_per_day, 0)}


def get_production_summary(df_prod):
    """Calculate production achievement summary"""
    if df_prod is None or df_prod.empty:
        return {'total_plan': 0, 'total_aktual': 0, 'achievement_pct': 0, 'days_achieved': 0}
    
    total_plan = df_prod['Plan'].sum() if 'Plan' in df_prod.columns else 0
    total_aktual = df_prod['Aktual'].sum() if 'Aktual' in df_prod.columns else 0
    achievement_pct = (total_aktual / total_plan * 100) if total_plan > 0 else 0
    
    days_achieved = 0
    if 'Ketercapaian' in df_prod.columns:
        days_achieved = len(df_prod[df_prod['Ketercapaian'] >= 1.0])
    
    return {'total_plan': total_plan, 'total_aktual': total_aktual,
            'achievement_pct': round(achievement_pct, 1), 'days_achieved': days_achieved}

# ============================================================
# STANDARDIZED RAW LOADERS (FOR MONITORING VIEW)
# ============================================================
# These functions provide direct access to Excel sheets
# Used by views/monitoring.py to maintain 0% visual change

@st.cache_data(ttl=CACHE_TTL)
def load_stockpile_hopper():
    """
    Load and process Stockpile Hopper data based on Transactional Structure.
    Scans for header row containing 'Date', 'Time', 'Shift', 'Dumping', 'Ritase', 'Rit'.
    """
    try:
        path = None
        if MONITORING_EXCEL_PATH and os.path.exists(MONITORING_EXCEL_PATH):
            path = MONITORING_EXCEL_PATH
        elif ONEDRIVE_LINKS.get("monitoring"):
             # Fallback to OneDrive buffer if implemented
             pass
        else:
            # Fallback local check
            local_path = load_from_local("monitoring")
            if local_path: path = local_path
        
        if path:
            # 1. Read a chunk of rows to find the header (e.g., first 5000 rows)
            # User screenshot shows header at ~3400, so we need a deep scan.
            df_raw = pd.read_excel(path, sheet_name='Stockpile Hopper', header=None, nrows=5000)
            
            header_idx = None
            for i in range(len(df_raw)):
                row_str = df_raw.iloc[i].astype(str).str.cat(sep=' ').lower()
                # Look for signature columns
                if 'date' in row_str and 'dumping' in row_str and 'ritase' in row_str:
                    header_idx = i
                    break
            
            if header_idx is not None:
                # Reload with correct header (Read FULL file)
                # Note: header_idx is 0-based.
                df = pd.read_excel(path, sheet_name='Stockpile Hopper', header=header_idx)
                
                # Preserve Excel Row Order
                df['Row_Order'] = df.index
                
                # Standardize Column Names
                rename_dict = {}
                for col in df.columns:
                    lower_col = str(col).lower().strip()
                    if 'date' == lower_col or 'tanggal' == lower_col:
                        rename_dict[col] = 'Tanggal'
                    elif 'time' in lower_col or 'jam' in lower_col:
                        rename_dict[col] = 'Jam_Range'
                    elif 'shift' in lower_col:
                        rename_dict[col] = 'Shift'
                    
                    # Mapping based on User Request
                    # Dumping -> Loader
                    elif 'dumping' in lower_col: 
                        rename_dict[col] = 'Loader'
                    
                    # Old "Ritase" (Hauler) -> Now "Unit"
                    # If header says "Unit", map to Unit. If header says "Ritase" but contains text, map to Unit?
                    # Safer: Look for specific keywords if header is ambiguous, but user said header CHANGED.
                    # Let's assume user renamed header to "Unit" for Hauler.
                    elif 'unit' == lower_col: 
                        rename_dict[col] = 'Unit'
                    
                    # Old "Rit" -> Now "Ritase"
                    elif 'ritase' == lower_col:
                        # Ambiguity: Old file "Ritase" was Hauler. New file "Ritase" is Count.
                        # We need to distinguish based on content or context?
                        # User said "Ritase di ganti menjadi Unit" (so old Ritase is gone/renamed)
                        # "Rit diganti menjadi Ritase" (so Ritase is now the count)
                        # So if we see "Ritase", it is likely the COUNT.
                        rename_dict[col] = 'Ritase'
                    
                    elif 'rit' == lower_col:
                        rename_dict[col] = 'Ritase'
                    
                    # Legacy Fallback (if user didn't actually change file yet or mixed)
                    elif 'hauler' in lower_col:
                         rename_dict[col] = 'Unit'

                df = df.rename(columns=rename_dict)
                
                # Check for "Ritase vs Unit" swap ambiguity
                # If we mapped 'Ritase' -> 'Ritase' (Count), verify it's numeric.
                # If we mapped 'Unit' -> 'Unit', verify it's text.
                
                # Filter valid rows
                if 'Tanggal' in df.columns:

                    # 1. Parse Date (Excel Serial or String)
                    df['Tanggal'] = safe_parse_date_column(df['Tanggal'])
                    df = df[df['Tanggal'].notna()]
                    
                    # Convert to datetime for filtering
                    df['Tanggal'] = pd.to_datetime(df['Tanggal'])

                    # CRITICAL: Filter for 2026 data and beyond
                    # User request: "semua data yang dari 2026 dan seterusnya"
                    df = df[df['Tanggal'] >= pd.Timestamp('2026-01-01')]
                    
                    # 2. Parse Time (Jam_Range like "07:00-08:00") -> Extract Starting Hour
                    def extract_hour(val):
                        if pd.isna(val): return 0
                        s = str(val).strip()
                        if '-' in s:
                            start_time = s.split('-')[0]
                            if ':' in start_time:
                                try:
                                    return int(start_time.split(':')[0])
                                except:
                                    return 0
                        return 0
                        
                    if 'Jam_Range' in df.columns:
                        df['Jam'] = df['Jam_Range'].apply(extract_hour)
                    else:
                        df['Jam'] = 0
                        
                    # 3. Numeric Ritase (Volume)
                    if 'Ritase' in df.columns:
                        df['Ritase'] = pd.to_numeric(df['Ritase'], errors='coerce').fillna(0)
                        # Ensure no legacy 'Rit' column confuses things
                        df['Rit'] = df['Ritase'] # Keep alias for backward compatibility or rename throughout? 
                        # Better to rename 'Rit' to 'Ritase' throughout the app. 
                        # But views/process.py uses 'Rit'. I should update that too.
                    else:
                        df['Ritase'] = 0
                        df['Rit'] = 0 # Fallback
                    
                    # 4. Fill text defaults
                    if 'Loader' in df.columns: df['Loader'] = df['Loader'].fillna('Unknown') # Was Unit
                    if 'Unit' in df.columns: df['Unit'] = df['Unit'].fillna('Unknown') # Was Hauler

                    return df

            return pd.DataFrame()
            
    except Exception as e:
        print(f"Error loading Stockpile Hopper: {e}")
        return pd.DataFrame()
    return pd.DataFrame()


@st.cache_data(ttl=CACHE_TTL)
def load_bbm_raw():
    """Load BBM sheet directly (Raw)"""
    try:
        if MONITORING_EXCEL_PATH and os.path.exists(MONITORING_EXCEL_PATH):
            return pd.read_excel(MONITORING_EXCEL_PATH, sheet_name='BBM')
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading BBM: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=CACHE_TTL)
def load_ritase_raw():
    """Load Ritase sheet directly (Raw)"""
    try:
        if MONITORING_EXCEL_PATH and os.path.exists(MONITORING_EXCEL_PATH):
            return pd.read_excel(MONITORING_EXCEL_PATH, sheet_name='Ritase')
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading Ritase: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=CACHE_TTL)
def load_analisa_produksi_raw():
    """Load Analisa Produksi sheet directly"""
    try:
        if MONITORING_EXCEL_PATH and os.path.exists(MONITORING_EXCEL_PATH):
            return pd.read_excel(MONITORING_EXCEL_PATH, sheet_name='Analisa Produksi')
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading Analisa: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=CACHE_TTL)
def load_gangguan_raw():
    """Load Gangguan sheet directly"""
    try:
        if MONITORING_EXCEL_PATH and os.path.exists(MONITORING_EXCEL_PATH):
            return pd.read_excel(MONITORING_EXCEL_PATH, sheet_name='Gangguan')
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading Gangguan: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=CACHE_TTL)
def load_tonase_raw():
    """Load Tonase sheet directly"""
    try:
        if MONITORING_EXCEL_PATH and os.path.exists(MONITORING_EXCEL_PATH):
            df = pd.read_excel(MONITORING_EXCEL_PATH, sheet_name='Tonase', header=1)
            
            # Safety: Rename first column to Tanggal if needed
            if len(df.columns) > 0:
                df = df.rename(columns={df.columns[0]: 'Tanggal'})
                
            # Filter repeated headers
            if 'Tanggal' in df.columns:
                df = df[df['Tanggal'].astype(str).str.strip() != 'Tanggal']
                df = df[df['Tanggal'].notna()]
                
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading Tonase: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=CACHE_TTL)
def load_shipping_data():
    """
    Load data pengiriman from 'TONASE PENGIRIMAN ' sheet.
    Enhanced to handle horizontal month blocks (Jan, Feb, etc. side-by-side).
    """
    df = None
    
    # Path Resolution
    path = None
    # 1. Try Config Path
    if MONITORING_EXCEL_PATH and os.path.exists(MONITORING_EXCEL_PATH):
        path = MONITORING_EXCEL_PATH
    # 2. Try User Specific Path (Hardcoded override for this specific user request)
    elif os.path.exists(r"C:\Users\user\OneDrive\Dashboard_Tambang\Monitoring.xlsx"):
        path = r"C:\Users\user\OneDrive\Dashboard_Tambang\Monitoring.xlsx"
    # 3. Try Local Cache
    else:
        local_path = load_from_local("monitoring")
        if local_path: path = local_path

    if not path:
        return pd.DataFrame()

    try:
        xls = pd.ExcelFile(path)
        
        # Fuzzy Match Sheet Name
        sheet_name = None
        candidates = ['TONASE PENGIRIMAN ', 'TONASE PENGIRIMAN', 'PENGIRIMAN', 'SHIPPING']
        for s in xls.sheet_names:
            if s.strip().upper() in [c.strip().upper() for c in candidates]:
                sheet_name = s
                break
        
        if not sheet_name:
            return pd.DataFrame()

        # Read Header Row (Row 2 in specific file, Index 2)
        # But let's read a chunk to be safe
        df_raw = pd.read_excel(path, sheet_name=sheet_name, header=None, nrows=5)
        
        # Find Header Row Index (Looking for 'Tanggal' and 'Shift')
        header_idx = -1
        for i in range(len(df_raw)):
            row_str = df_raw.iloc[i].astype(str).str.cat(sep=' ').lower()
            if 'tanggal' in row_str and 'shift' in row_str:
                header_idx = i
                break
        
        if header_idx == -1: return pd.DataFrame() # Header not found

        # Read Full Data with correct header
        df_full = pd.read_excel(path, sheet_name=sheet_name, header=header_idx)
        
        # IDENTIFY BLOCKS
        # Pattern: [Tanggal, Shift, ..., Total LS, Total SS] repeated
        # We look for all columns named 'Tanggal' (pandas handles duplicate cols by appending .1, .2)
        
        all_blocks = []
        
        # Iterate columns to find 'Tanggal' starts
        # Since pandas dedups names, we check the original content or just fuzzy match columns
        # Easier: Iterate by index
        
        # Reload without header to map indices accurately
        df_nheader = pd.read_excel(path, sheet_name=sheet_name, header=None, skiprows=header_idx)
        # Row 0 is now the header
        header_row = df_nheader.iloc[0]
        
        # Indices where header is 'Tanggal'
        block_starts = []
        for c in range(len(header_row)):
            val = str(header_row.iloc[c]).strip().lower()
            if val == 'tanggal':
                block_starts.append(c)
        
        for start_col in block_starts:
            try:
                # Extract Block (Assuming standard width ~7-8 cols)
                # Look for 'Total SS' or 'Total_SS' to end? Or just take fixed width 7
                # Based on debug: Tanggal, Shift, AP LS, AP LS(MK3), AP SS, Total LS, Total SS.
                # Width = 7
                
                block = df_nheader.iloc[1:, start_col:start_col+7].copy()
                
                # Assign Standard Names
                # We expect 7 columns. If fewer, pad.
                if block.shape[1] < 7: continue
                
                block.columns = ['Date', 'Shift', 'AP_LS', 'AP_LS_MK3', 'AP_SS', 'Total_LS', 'Total_SS']
                
                # Clean Data
                block = block.dropna(subset=['Date'])
                block['Date'] = safe_parse_date_column(block['Date'])
                block = block[block['Date'].notna()]
                block['Date'] = pd.to_datetime(block['Date'])
                
                # Filter Valid Shifts
                block = block[block['Shift'].astype(str).str.contains(r'1|2|3')]
                
                # Numeric Conversion
                cols_num = ['AP_LS', 'AP_LS_MK3', 'AP_SS', 'Total_LS', 'Total_SS']
                for c in cols_num:
                    block[c] = pd.to_numeric(block[c], errors='coerce').fillna(0)
                
                # Calculate Total Quantity (Sum of Components, not usage of sparse Total columns)
                # Note: Some blocks might not have MK3, but we normalized to 0
                block['Quantity'] = block['AP_LS'] + block['AP_LS_MK3'] + block['AP_SS']
                
                # Append
                all_blocks.append(block[['Date', 'Shift', 'AP_LS', 'AP_LS_MK3', 'AP_SS', 'Quantity']])
                
            except Exception as e:
                continue
        
        if all_blocks:
            final_df = pd.concat(all_blocks, ignore_index=True)
            
            # FILTER: ONLY 2026+
            final_df = final_df[final_df['Date'] >= pd.Timestamp('2026-01-01')]
            
            # SORT: DESCENDING (Latest Input First)
            final_df = final_df.sort_values(['Date', 'Shift'], ascending=False)
            
            return final_df
            
            return final_df
            
        return pd.DataFrame()

    except Exception as e:
        print(f"Error loading shipping: {e}")
        return pd.DataFrame()