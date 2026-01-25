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

# Import from config
try:
    from config import ONEDRIVE_LINKS, CACHE_TTL, LOCAL_FILE_NAMES
except ImportError:
    try:
        from config.onedrive import ONEDRIVE_LINKS, CACHE_TTL, LOCAL_FILE_NAMES
    except ImportError:
        ONEDRIVE_LINKS = {}
        CACHE_TTL = 300
        LOCAL_FILE_NAMES = {}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

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
    
    # Try OneDrive first
    if ONEDRIVE_LINKS.get("produksi"):
        file_buffer = download_from_onedrive(ONEDRIVE_LINKS["produksi"])
        if file_buffer:
            try:
                df = pd.read_excel(file_buffer, sheet_name='Tahun 2025')
            except Exception as e:
                st.warning(f"Failed to load from OneDrive: {e}")
    
    # Fallback to local
    if df is None:
        local_path = load_from_local("produksi")
        if local_path:
            try:
                df = pd.read_excel(local_path, sheet_name='Tahun 2025')
            except Exception as e:
                st.warning(f"Failed to load from local: {e}")
    
    if df is None:
        return pd.DataFrame()
    
    try:
        # Remove header rows
        df = df[df['Shift'] != 'Shift']
        valid_shifts = ['Shift 1', 'Shift 2', 'Shift 3']
        df = df[df['Shift'].isin(valid_shifts)]
        
        # ✅ FIX: Parse Excel Serial Date
        df['Date'] = safe_parse_date_column(df['Date'])
        
        # Remove invalid dates
        df = df[df['Date'].notna()]
        
        # Filter year range (be more lenient - 2020-2030)
        df = df[df['Date'].apply(lambda x: 2020 <= x.year <= 2030 if x else False)]
        
        # Parse Time
        if 'Time' in df.columns:
            df['Time'] = df['Time'].astype(str).fillna('')
        else:
            df['Time'] = ''
        
        # Check if BLOK column exists (if not, columns are shifted)
        if 'BLOK' not in df.columns:
            # Columns are shifted - need to fix
            df_fixed = pd.DataFrame()
            df_fixed['Date'] = df['Date']
            df_fixed['Time'] = df['Time']
            df_fixed['Shift'] = df['Shift']
            df_fixed['BLOK'] = df['Front'] if 'Front' in df.columns else ''
            df_fixed['Front'] = df['Commudity'] if 'Commudity' in df.columns else ''
            df_fixed['Commudity'] = df['Excavator'] if 'Excavator' in df.columns else ''
            df_fixed['Excavator'] = df['Dump Truck'] if 'Dump Truck' in df.columns else ''
            df_fixed['Dump Truck'] = df['Dump Loc'] if 'Dump Loc' in df.columns else ''
            df_fixed['Dump Loc'] = df['Rit'] if 'Rit' in df.columns else ''
            df_fixed['Rit'] = df['Tonnase'] if 'Tonnase' in df.columns else 0
            df_fixed['Tonnase'] = df['Unnamed: 10'] if 'Unnamed: 10' in df.columns else 0
            
            df = df_fixed
        
        # Alternative: Detect shifted rows by checking Excavator column
        if 'Excavator' in df.columns:
            mask_normal = df['Excavator'].astype(str).str.startswith('PC', na=False)
            df_normal = df[mask_normal].copy()
            df_shifted = df[~mask_normal].copy()
            
            if len(df_shifted) > 0 and len(df_normal) > 0:
                # Fix shifted rows
                df_shifted_fixed = pd.DataFrame()
                df_shifted_fixed['Date'] = df_shifted['Date']
                df_shifted_fixed['Time'] = df_shifted['Time']
                df_shifted_fixed['Shift'] = df_shifted['Shift']
                
                if 'BLOK' in df_shifted.columns:
                    df_shifted_fixed['BLOK'] = df_shifted['Front']
                    df_shifted_fixed['Front'] = df_shifted['Commudity']
                    df_shifted_fixed['Commudity'] = df_shifted['Excavator']
                    df_shifted_fixed['Excavator'] = df_shifted['Dump Truck']
                    df_shifted_fixed['Dump Truck'] = df_shifted['Dump Loc']
                    df_shifted_fixed['Dump Loc'] = df_shifted['Rit']
                    df_shifted_fixed['Rit'] = df_shifted['Tonnase']
                    df_shifted_fixed['Tonnase'] = df_shifted.get('Unnamed: 10', 0)
                else:
                    # Columns already shifted in original
                    df_shifted_fixed['BLOK'] = df_shifted['Front']
                    df_shifted_fixed['Front'] = df_shifted['Commudity']
                    df_shifted_fixed['Commudity'] = df_shifted['Excavator']
                    df_shifted_fixed['Excavator'] = df_shifted['Dump Truck']
                    df_shifted_fixed['Dump Truck'] = df_shifted['Dump Loc']
                    df_shifted_fixed['Dump Loc'] = df_shifted['Rit']
                    df_shifted_fixed['Rit'] = df_shifted['Tonnase']
                    df_shifted_fixed['Tonnase'] = df_shifted.get('Unnamed: 10', 0)
                
                df = pd.concat([df_normal, df_shifted_fixed], ignore_index=True)
        
        # Remove unnamed columns
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        
        # Filter only valid excavators (PC prefix)
        df = df[df['Excavator'].astype(str).str.startswith('PC', na=False)]
        
        # Normalize excavator names to consistent format (PC XXX-YY)
        df = normalize_excavator_column(df)
        
        # Convert numeric columns
        df['Rit'] = pd.to_numeric(df['Rit'], errors='coerce').fillna(0)
        df['Tonnase'] = pd.to_numeric(df['Tonnase'], errors='coerce').fillna(0)
        
        # Validate Dump Truck
        df['Dump Truck'] = df['Dump Truck'].astype(str)
        df = df[df['Dump Truck'].str.match(r'^\d+$', na=False)]
        
        # Final cleanup
        df = df[df['Tonnase'] > 0]
        df = df.reset_index(drop=True)
        
        # Ensure required columns exist
        for col in ['BLOK', 'Dump Loc']:
            if col not in df.columns:
                df[col] = ''
        
        return df
        
    except Exception as e:
        st.error(f"❌ Error processing produksi data: {e}")
        import traceback
        st.code(traceback.format_exc())
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
    Load data gangguan lengkap dari sheet 'All'
    Handles dual structure: data before Nov 2025 without Crusher, Nov 2025+ with Crusher
    Returns: DataFrame dengan semua data gangguan
    """
    file_path = None
    
    # Try local OneDrive folder first
    local_path = load_from_local("gangguan")
    if local_path:
        file_path = local_path
    
    if file_path is None:
        return pd.DataFrame()
    
    try:
        # Read raw data without header to handle multi-structure
        df_raw = pd.read_excel(file_path, sheet_name='All', header=None)
        
        # Find all header rows (where column 0 = 'Tanggal')
        header_mask = df_raw[0] == 'Tanggal'
        header_indices = df_raw[header_mask].index.tolist()
        
        if len(header_indices) == 0:
            return pd.DataFrame()
        
        # Define standard columns (with Crusher) - 27 columns 
        standard_cols = ['Tanggal', 'Bulan', 'Tahun', 'Week', 'Shift', 'Start', 'End', 
                        'Durasi', 'Crusher', 'Alat', 'Remarks', 'Kelompok Masalah', 'Gangguan', 
                        'Info CCR', 'Sub Komponen', 'Keterangan', 'Penyebab', 
                        'Identifikasi Masalah', 'Action', 'Plan', 'PIC', 'Status', 'Due Date',
                        'Spare Part', 'Info Spare Part', 'Link/Lampiran', 'Extra']
        
        # Columns without Crusher (old format) - 26 columns to match Excel
        old_cols = ['Tanggal', 'Bulan', 'Tahun', 'Week', 'Shift', 'Start', 'End', 
                   'Durasi', 'Alat', 'Remarks', 'Kelompok Masalah', 'Gangguan', 
                   'Info CCR', 'Sub Komponen', 'Keterangan', 'Penyebab', 
                   'Identifikasi Masalah', 'Action', 'Plan', 'PIC', 'Status', 'Due Date',
                   'Spare Part', 'Info Spare Part', 'Link/Lampiran', 'Extra']
        
        all_dfs = []
        
        for i, header_idx in enumerate(header_indices):
            # Determine end of this section
            if i + 1 < len(header_indices):
                end_idx = header_indices[i + 1]
            else:
                end_idx = len(df_raw)
            
            # Get header row
            header_row = df_raw.iloc[header_idx].tolist()
            
            # Check if this section has Crusher column
            has_crusher = 'Crusher' in header_row
            
            # Get data rows for this section
            section_data = df_raw.iloc[header_idx + 1:end_idx].copy()
            
            if section_data.empty:
                continue
            
            # Assign column names based on header
            if has_crusher:
                # New format with Crusher
                section_data.columns = header_row[:len(section_data.columns)]
            else:
                # Old format without Crusher - add Crusher column
                section_data.columns = old_cols[:len(section_data.columns)]
                section_data['Crusher'] = None
            
            # Ensure all standard columns exist
            for col in standard_cols:
                if col not in section_data.columns:
                    section_data[col] = None
            
            # Select only standard columns in order
            section_data = section_data[[c for c in standard_cols if c in section_data.columns]]
            
            all_dfs.append(section_data)
        
        if not all_dfs:
            return pd.DataFrame()
        
        # Combine all sections
        df = pd.concat(all_dfs, ignore_index=True)
        
        # Filter out any remaining header rows
        df = df[df['Bulan'] != 'Bulan'].copy()
        
        # Convert data types
        df['Bulan'] = pd.to_numeric(df['Bulan'], errors='coerce')
        df['Shift'] = pd.to_numeric(df['Shift'], errors='coerce')
        df['Durasi'] = pd.to_numeric(df['Durasi'], errors='coerce')
        df['Tahun'] = pd.to_numeric(df['Tahun'], errors='coerce')
        df['Week'] = pd.to_numeric(df['Week'], errors='coerce')
        
        # Parse Tanggal
        df['Tanggal'] = pd.to_datetime(df['Tanggal'], errors='coerce')
        
        # Remove rows with invalid data
        df = df[df['Bulan'].notna()]
        df = df[df['Durasi'].notna()]
        
        # Standardize Kelompok Masalah (fix case inconsistencies)
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
        df['Kelompok Masalah'] = df['Kelompok Masalah'].replace(kelompok_map)
        
        # Remove rows with missing Kelompok Masalah
        df = df[df['Kelompok Masalah'].notna()]
        
        # Map bulan number to name
        bulan_names = {
            1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
            5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
            9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
        }
        df['Bulan_Name'] = df['Bulan'].map(bulan_names)
        
        # Reset index
        df = df.reset_index(drop=True)
        
        return df
        
    except Exception as e:
        print(f"Error loading gangguan: {e}")
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
        # Assuming current year (2025) and month (January) from context or file
        current_year = 2025
        current_month = 1 
        
        # Note: In a real app, month should be inferred from filename or user input.
        # For now, we fix to Jan 2025 as per user context.
        
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
                df = pd.read_excel(file_buffer, sheet_name='W22 Scheduling', skiprows=1)
            except:
                pass
    
    if df is None:
        local_path = load_from_local("daily_plan")
        if local_path:
            try:
                df = pd.read_excel(local_path, sheet_name='W22 Scheduling', skiprows=1)
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
    df = load_bbm()
    
    if df.empty:
        return pd.DataFrame()
    
    try:
        # Add kategori alat
        df['Kategori'] = df['Alat Berat'].apply(lambda x: 
            'Excavator' if 'Excavator' in str(x) else 
            'Dump Truck' if 'Dump' in str(x) or 'SCANIA' in str(x).upper() else 
            'Support'
        )
        return df
    except:
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
    df = load_ritase_enhanced()
    
    if df.empty:
        return pd.DataFrame()
    
    try:
        front_cols = ['Front B LS', 'Front B Clay', 'Front B LS MIX', 
                      'Front C LS', 'Front C LS MIX', 'PLB LS', 'PLB SS', 
                      'PLT SS', 'PLT MIX', 'Timbunan', 'Stockpile 6  SS', 
                      'PLT LS MIX', 'Stockpile 6 ']
        
        available = [c for c in front_cols if c in df.columns]
        totals = df[available].sum().reset_index()
        totals.columns = ['Front', 'Total_Ritase']
        totals = totals[totals['Total_Ritase'] > 0]
        totals = totals.sort_values('Total_Ritase', ascending=False)
        
        return totals
    except:
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
        df = df.rename(columns={df.columns[0]: 'Tanggal', df.columns[1]: 'Ritase'})
        df['Tanggal'] = pd.to_datetime(df['Tanggal'], errors='coerce')
        df = df[df['Tanggal'].notna()]
        
        hour_cols = [col for col in df.columns if '-' in str(col) and col not in ['Tanggal', 'Ritase']]
        for col in hour_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        if 'Total' in df.columns:
            df['Total'] = pd.to_numeric(df['Total'], errors='coerce').fillna(0)
        
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
            try:
                df = pd.read_excel(local_path, sheet_name='Analisa Produksi')
            except:
                pass
    
    if df is None:
        return pd.DataFrame()
    
    all_data = []
    for bulan, start_col in bulan_map.items():
        try:
            df_bulan = df.iloc[1:32, start_col:start_col+4].copy()
            df_bulan.columns = ['Tanggal', 'Plan', 'Aktual', 'Ketercapaian']
            df_bulan['Tanggal'] = pd.to_numeric(df_bulan['Tanggal'], errors='coerce')
            df_bulan['Plan'] = pd.to_numeric(df_bulan['Plan'], errors='coerce')
            df_bulan['Aktual'] = pd.to_numeric(df_bulan['Aktual'], errors='coerce')
            df_bulan['Ketercapaian'] = pd.to_numeric(df_bulan['Ketercapaian'], errors='coerce')
            df_bulan = df_bulan.dropna(subset=['Tanggal'])
            if not df_bulan.empty:
                df_bulan['Bulan'] = bulan
                all_data.append(df_bulan)
        except:
            continue
    
    if all_data:
        return pd.concat(all_data, ignore_index=True)
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