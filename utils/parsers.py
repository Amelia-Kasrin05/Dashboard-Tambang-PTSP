import pandas as pd
import re
from datetime import datetime, timedelta, time

# ============================================================
# PARSING HELPERS
# ============================================================

def parse_excel_date(date_value):
    try:
        if isinstance(date_value, (datetime, pd.Timestamp)):
            return pd.Timestamp(date_value).date()
        if isinstance(date_value, str):
            parsed = pd.to_datetime(date_value, errors='coerce')
            if pd.notna(parsed): return parsed.date()
            return None
        if isinstance(date_value, (int, float)):
            excel_epoch = datetime(1899, 12, 30)
            date_result = excel_epoch + timedelta(days=int(date_value))
            return date_result.date()
        return None
        return None
    except Exception:
        return None

def parse_excel_time(time_val):
    try:
        if pd.isna(time_val): return None
        # Handle Excel Serial Date (Float) -> Time/Datetime Object
        if isinstance(time_val, (int, float)):
             # Excel base date
             excel_epoch = datetime(1899, 12, 30)
             dt = excel_epoch + timedelta(days=float(time_val))
             return dt # Return datetime object (1899-...) which pandas handles fine
        
        # Handle Strings
        if isinstance(time_val, str):
             return time_val.strip()

        if isinstance(time_val, time):
             return time_val.strftime("%H:%M:%S")
             
        return time_val
    except: return None

def safe_parse_date_column(date_series):
    return date_series.apply(parse_excel_date)

def normalize_excavator_name(name):
    if pd.isna(name) or not isinstance(name, str):
        return name
    name = str(name).strip().upper()
    clean = re.sub(r'[^A-Z0-9]', '', name)
    match = re.match(r'^PC(\d{3})(\d{2})$', clean)
    if match: return f"PC {match.group(1)}-{match.group(2)}"
    match = re.match(r'^PC[-\s]*(\d{3})[-\s]*(\d{2})$', name)
    if match: return f"PC {match.group(1)}-{match.group(2)}"
    return name

def normalize_excavator_column(df):
    if 'Excavator' in df.columns:
        df['Excavator'] = df['Excavator'].apply(normalize_excavator_name)
    return df

# ============================================================
# 1. PRODUCTION PARSER
# ============================================================

def parse_production_data(source):
    try:
        try:
            xls = pd.ExcelFile(source, engine='openpyxl')
        except:
            if hasattr(source, 'seek'): source.seek(0)
            xls = pd.ExcelFile(source)
        valid_dfs = []
        target_sheets = [s for s in xls.sheet_names if '2026' in str(s)]
        if not target_sheets:
            target_sheets = [s for s in xls.sheet_names if s.lower() not in ['menu', 'dashboard', 'summary', 'ref', 'config']]
            
        for sheet in target_sheets:
            try:
                # Header Scanning - Reading Full Sheet (Match Stockpile Logic)
                df_raw = pd.read_excel(xls, sheet_name=sheet, header=None)
                header_idx = 0
                for i in range(len(df_raw)):
                    row_str = df_raw.iloc[i].astype(str).str.cat(sep=' ').lower()
                    if ('date' in row_str or 'tanggal' in row_str) and \
                       ('shift' in row_str or 'dump truck' in row_str or 'unit' in row_str):
                        header_idx = i; break
                
                temp_df = pd.read_excel(xls, sheet_name=sheet, header=header_idx)
                temp_df.columns = [str(c).strip() for c in temp_df.columns]
                
                # Column Rename to Standard (for DB Mapping)
                # We map raw Excel headers to our Strict DB Model keys
                # DB Keys: Date, Shift, Time, Excavator, Commudity, Dump Truck, Rit, Tonnase, Front, Dump Loc
                
                col_map = {}
                for c in temp_df.columns:
                    cl = c.lower()
                    if 'date' in cl or 'tanggal' in cl: col_map[c] = 'Date'
                    elif 'shift' in cl: col_map[c] = 'Shift'
                    elif 'excavator' in cl: col_map[c] = 'Excavator'
                    elif 'commodity' in cl or 'commudity' in cl: col_map[c] = 'Commodity' # Fixed
                    elif 'unit' in cl or 'dump truck' in cl: col_map[c] = 'Dump Truck'
                    elif 'ritase' in cl or 'rit' == cl: col_map[c] = 'Rit'
                    elif 'tonnase' in cl or 'tonase' in cl: col_map[c] = 'Tonase' # User pref: Tonase
                    elif 'front' in cl: col_map[c] = 'Front'
                    elif 'dump' in cl and 'loc' in cl: col_map[c] = 'Dump Loc'
                    elif 'blok' in cl: col_map[c] = 'BLOK'
                    elif 'time' in cl or 'jam' in cl: col_map[c] = 'Time'
                
                temp_df = temp_df.rename(columns=col_map)
                
                if 'Date' not in temp_df.columns: continue
                
                temp_df['Date'] = safe_parse_date_column(temp_df['Date'])
                temp_df = temp_df.dropna(subset=['Date'])
                temp_df = normalize_excavator_column(temp_df)
                
                # Fill missing columns
                for req in ['Excavator', 'Front', 'Commodity', 'Dump Truck', 'Dump Loc', 'BLOK', 'Time', 'Shift']:
                    if req not in temp_df.columns: temp_df[req] = None

                # FILTER EMPTY ROWS (User Request)
                # Remove rows where Date is present but other keys are empty or '-'
                # Critical columns: Time, Shift, Excavator, Dump Truck
                def is_valid_row(row):
                    # Check if at least one critical column has real data (not None, NaN, or '-')
                    # Broadened check to include ALL data columns so we don't accidentally drop sparse rows
                    # EXCLUDE SHIFT: Shift alone is not enough to keep a row (User Bug Report)
                    criticals = [
                        row['Time'], row['Excavator'], row['Dump Truck'], 
                        row['Front'], row['Commodity'], row['Dump Loc'], row['BLOK'],
                        row.get('Rit', 0), row.get('Tonnase', 0)
                    ]
                    for val in criticals:
                        s = str(val).strip()
                        # Allow 0 for Rit/Tonase if explicitly valid? No, usually 0 means empty in this excel
                        if pd.notna(val) and s != '' and s != '-' and s != 'nan' and s != 'None':
                            # Special check for numerics 0
                            try:
                                if float(val) == 0: continue 
                            except: pass
                            
                            return True # Found something valid
                    return False

                valid_mask = temp_df.apply(is_valid_row, axis=1)
                temp_df = temp_df[valid_mask]
                    
                # Numerics
                for n in ['Rit', 'Tonnase']:
                    if n in temp_df.columns: 
                        temp_df[n] = pd.to_numeric(temp_df[n], errors='coerce').fillna(0)
                
                valid_dfs.append(temp_df)
            except: continue
                
        if valid_dfs: return pd.concat(valid_dfs, ignore_index=True)
        return pd.DataFrame()
    except: return pd.DataFrame()

# ============================================================
# 2. DOWNTIME PARSER (Indonesian)
# ============================================================

def parse_downtime_data(source):
    try:
        try:
            xls = pd.ExcelFile(source, engine='openpyxl')
        except:
            if hasattr(source, 'seek'): source.seek(0)
            xls = pd.ExcelFile(source)
        sheet_names = xls.sheet_names
        
        target_sheets = []
        if 'All' in sheet_names: target_sheets = ['All']
        else:
            mon_sheets = [s for s in sheet_names if 'monitoring' in str(s).lower()]
            mon_sheets.sort(reverse=True)
            target_sheets = mon_sheets[:1] if mon_sheets else ([sheet_names[0]] if sheet_names else [])
            
        all_dfs = []
        # DB Keys correspond to these exactly
        standard_cols = ['Tanggal', 'Shift', 'Start', 'End', 'Durasi', 'Crusher', 
                         'Alat', 'Remarks', 'Kelompok Masalah', 'Gangguan', 'Info CCR', 
                         'Sub Komponen', 'Keterangan', 'Penyebab', 'Identifikasi Masalah',
                         'Action', 'Plan', 'PIC', 'Status', 'Due Date', 'Spare Part', 
                         'Info Spare Part', 'Link/Lampiran', 'Extra']
                         
        for sheet in target_sheets:
            try:
                df_sheet = pd.read_excel(xls, sheet_name=sheet)
                if df_sheet.empty: continue
                
                df_sheet.columns = [str(c).strip() for c in df_sheet.columns]
                
                # Map Date
                col_map = {c.lower(): c for c in df_sheet.columns}
                if 'tanggal' in col_map: df_sheet = df_sheet.rename(columns={col_map['tanggal']: 'Tanggal'})
                
                if 'Tanggal' not in df_sheet.columns: continue
                
                # Parse Date
                df_sheet['Tanggal'] = safe_parse_date_column(df_sheet['Tanggal'])
                df_sheet = df_sheet.dropna(subset=['Tanggal'])
                
                # Shifted Column Logic 2026
                if 'Alat' in df_sheet.columns:
                    mask_shifted = df_sheet['Alat'].astype(str).str.contains(r'LSC|MS |Batu', case=False, na=False)
                    if 'Tahun' in df_sheet.columns: mask_shifted = mask_shifted | (df_sheet['Tahun'] == 2026)
                    if mask_shifted.any():
                        shift_map = [
                            ('Crusher', 'Alat'), ('Alat', 'Remarks'), ('Remarks', 'Kelompok Masalah'),
                            ('Kelompok Masalah', 'Gangguan'), ('Gangguan', 'Info CCR'),
                            ('Info CCR', 'Sub Komponen'), ('Sub Komponen', 'Keterangan'),
                            ('Keterangan', 'Penyebab'), ('Penyebab', 'Identifikasi Masalah'),
                            ('Identifikasi Masalah', 'Action'), ('Action', 'Plan'),
                            ('Plan', 'PIC'), ('PIC', 'Status'), ('Status', 'Due Date'),
                            ('Due Date', 'Spare Part'), ('Spare Part', 'Info Spare Part'),
                            ('Info Spare Part', 'Link/Lampiran')
                        ]
                        for new_col, old_col in shift_map:
                            if old_col in df_sheet.columns:
                                if new_col not in df_sheet.columns: df_sheet[new_col] = None
                                df_sheet.loc[mask_shifted, new_col] = df_sheet.loc[mask_shifted, old_col]
                                
                # Ensure cols
                for col in standard_cols:
                    if col not in df_sheet.columns: df_sheet[col] = None
                
                # Numerics & Time
                df_sheet['Durasi'] = pd.to_numeric(df_sheet['Durasi'], errors='coerce').fillna(0.0)
                
                # Fix Time Parsing (Start/End)
                if 'Start' in df_sheet.columns:
                    df_sheet['Start'] = df_sheet['Start'].apply(parse_excel_time)
                if 'End' in df_sheet.columns:
                    df_sheet['End'] = df_sheet['End'].apply(parse_excel_time)
                
                all_dfs.append(df_sheet)
            except: continue
        
        if all_dfs: return pd.concat(all_dfs, ignore_index=True)
        return pd.DataFrame()
    except: return pd.DataFrame()

# ============================================================
# 3. BBM PARSER
# ============================================================
# ============================================================
# 3. STOCKPILE PARSER (Monitoring.xlsx -> Sheet Stockpile Hopper)
# ============================================================
def parse_stockpile_hopper(source):
    try:
        try:
            xls = pd.ExcelFile(source, engine='openpyxl')
        except:
            if hasattr(source, 'seek'): source.seek(0)
            xls = pd.ExcelFile(source)
        # Use exact sheet name
        if 'Stockpile Hopper' not in xls.sheet_names:
            return pd.DataFrame()

        # Read header scan - READING FULL SHEET to find 2026 header
        df_raw = pd.read_excel(xls, sheet_name='Stockpile Hopper', header=None)
            
        # Header Scanning - Strict Match based on User User and Debug Findings (Row ~3399)
        # looking for: Date, Time, Shift, Dumping, Unit, Ritase
        header_idx = None
        
        # Header Scanning: User confirmed header is at Row 3399 for 2026 data
        # We must scan the FULL sheet again.
        header_idx = None
        df_raw = pd.read_excel(xls, sheet_name='Stockpile Hopper', header=None)
        
        # Optimization: Start scanning from row 3000 to save time and avoid old headers (2025 data)
        # User confirmed 2026 data starts at 3399.
        start_scan = 3000 if len(df_raw) > 3000 else 0
        
        for i in range(start_scan, len(df_raw)):
            row_str = df_raw.iloc[i].astype(str).str.cat(sep=' ').lower()
            # Strict check again because we know where it is roughly
            # Row 3399: Date, Time, Shift, Dumping, Unit, Rit
            if 'date' in row_str and 'dumping' in row_str and 'unit' in row_str:
                header_idx = i
                print(f"Found Stockpile Header at row {i}")
                break
        
        if header_idx is None:
            print("Stockpile Header not found.")
            return pd.DataFrame() 

        df = pd.read_excel(xls, sheet_name='Stockpile Hopper', header=header_idx)
        
        # Standardize Columns
        # Excel: Date/Tanggal, Time/Jam, Shift, Dumping, Unit, Ritase
        rename_dict = {}
        for col in df.columns:
            lower_col = str(col).lower().strip()
            if 'date' == lower_col or 'tanggal' == lower_col: rename_dict[col] = 'Tanggal'
            elif 'time' == lower_col or 'jam' == lower_col: rename_dict[col] = 'Jam'
            elif 'shift' == lower_col: rename_dict[col] = 'Shift'
            elif 'dumping' == lower_col or 'loader' == lower_col: rename_dict[col] = 'Loader'
            elif 'unit' == lower_col: rename_dict[col] = 'Unit'
            elif 'ritase' == lower_col: rename_dict[col] = 'Ritase'
            elif 'total' == lower_col: rename_dict[col] = 'Ritase' 
            elif 'rit' == lower_col: rename_dict[col] = 'Ritase' # Added 'Rit'

        df = df.rename(columns=rename_dict)
        
        if 'Tanggal' not in df.columns: 
            return pd.DataFrame()

        # Parse Date
        df['Tanggal'] = safe_parse_date_column(df['Tanggal'])
        df = df.dropna(subset=['Tanggal'])
        
        # FILTER EMPTY ROWS (Stockpile) - MOVED UP
        # Remove rows where Date is present but other keys are empty or '-'
        # Critical columns: Loader, Unit, Ritase, Jam, Shift
        def is_valid_stockpile_row(row):
            # Check Ritase
            rit = row['Ritase'] if 'Ritase' in row else 0
            try:
                if float(rit) > 0: return True
            except: pass
            
            # Check Text Cols
            # Use safe get
            loader = row.get('Loader', '')
            unit = row.get('Unit', '')
            jam = row.get('Jam', '')
            # EXCLUDE SHIFT: Shift alone is not enough (User Bug Report)
            
            criticals = [loader, unit, jam]
            for val in criticals:
                s = str(val).strip().lower()
                if pd.notna(val) and s != '' and s != '-' and s != 'nan' and s != 'unknown' and s != 'none':
                    return True
            return False

        valid_mask = df.apply(is_valid_stockpile_row, axis=1)
        df = df[valid_mask]

        if 'Jam' in df.columns:
            # Just clean whitespace, keep text
            df['Jam'] = df['Jam'].astype(str).str.strip()
        else:
            df['Jam'] = "Unknown"
            
        # Parse Shift (Format: "Shift 2" -> 2)
        def extract_shift(val):
            if pd.isna(val): return 1
            s = str(val).strip().lower()
            # Extract first digit found
            import re
            match = re.search(r'\d+', s)
            if match:
                return int(match.group())
            return 1 # Default
            
        if 'Shift' in df.columns:
            df['Shift'] = df['Shift'].apply(extract_shift)
        else:
            df['Shift'] = 1

        # Numerics
        if 'Ritase' in df.columns:
            df['Ritase'] = pd.to_numeric(df['Ritase'], errors='coerce').fillna(0)
            
        # Defaults
        if 'Loader' not in df.columns: df['Loader'] = 'Unknown'
        if 'Unit' not in df.columns: df['Unit'] = 'Unknown'
        
        # FILTER EMPTY ROWS (Stockpile)
        # Remove rows where Date is present but other keys are empty or '-'
        # Critical columns: Loader, Unit, Ritase, Jam, Shift
        def is_valid_stockpile_row(row):
            # Check if at least one critical column has real data
            # Ritase must be > 0 or Loader/Unit/Jam/Shift must be valid text
            
            # Check Ritase
            rit = row['Ritase'] if 'Ritase' in row else 0
            try:
                if float(rit) > 0: return True
            except: pass
            
            # Check Text Cols
            # Broader check: include Jam and Shift
            criticals = [row['Loader'], row['Unit'], row['Jam'], row['Shift']]
            for val in criticals:
                s = str(val).strip().lower()
                # 0 is considered "data" for Shift (e.g. Shift 0?) unlikely but safe.
                # But 'unknown' is default filler, so ignore that.
                if pd.notna(val) and s != '' and s != '-' and s != 'nan' and s != 'unknown':
                    return True
            return False

        valid_mask = df.apply(is_valid_stockpile_row, axis=1)
        df = df[valid_mask]

        return df[['Tanggal', 'Jam', 'Shift', 'Loader', 'Unit', 'Ritase']]
    except: return pd.DataFrame()

# ============================================================
# 4. SHIPPING PARSER (Monitoring.xlsx -> Sheet TONASE Pengiriman)
# ============================================================
def parse_shipping_data(source):
    try:
        if hasattr(source, 'seek'):
            source.seek(0)
        try:
            xls = pd.ExcelFile(source, engine='openpyxl')
        except:
            if hasattr(source, 'seek'): source.seek(0)
            xls = pd.ExcelFile(source)
            
        # Use exact sheet name with trailing space
        target_sheet = 'TONASE Pengiriman '
        if target_sheet not in xls.sheet_names:
            # Fallback check without space
            if 'TONASE Pengiriman' in xls.sheet_names:
                target_sheet = 'TONASE Pengiriman'
            else:
                return pd.DataFrame()
        
        # Read full sheet to scan horizontal blocks
        # Header is typically at row index 2 (Excel Row 3)
        df_raw = pd.read_excel(xls, sheet_name=target_sheet, header=None)
        
        header_row_idx = 2  # Confirmed by debug
        scan_limit_col = df_raw.shape[1]
        
        found_dfs = []
        
        for c in range(scan_limit_col):
            val = str(df_raw.iloc[header_row_idx, c]).strip().lower()
            if 'tanggal' == val:
                # Check data to confirm year 2026
                # Look ahead a few rows to confirm it's a valid data block
                is_valid_block = False
                try:
                    for r_offset in range(1, 4): # Check first 3 data rows
                        if header_row_idx + r_offset >= len(df_raw): break
                        sample_val = str(df_raw.iloc[header_row_idx+r_offset, c])
                        if '2026' in sample_val:
                             is_valid_block = True
                             break
                except: pass
                
                if is_valid_block:
                     # Extract Block (7 cols)
                     block_width = 7
                     if c + block_width > scan_limit_col: continue

                     df = df_raw.iloc[header_row_idx+1:, c : c+block_width].copy()
                     
                     # Rename Cols
                     cols = ['Date', 'Shift', 'AP_LS', 'AP_LS_MK3', 'AP_SS', 'Total_LS', 'Total_SS']
                     current_cols = len(df.columns)
                     df.columns = cols[:current_cols]
                     
                     # Clean Data
                     df = df.dropna(subset=['Date'])
                     
                     # Clean Numerics
                     num_cols = ['AP_LS', 'AP_LS_MK3', 'AP_SS', 'Total_LS', 'Total_SS']
                     for col in num_cols:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                     
                     # Drop if all numeric are 0 (Empty rows)
                     # Only keep rows with at least some data
                     # But be careful not to drop valid 0s if that's possible?
                     # User said "hilangkan saja klo datanya masih 0 semua"
                     mask = (df[num_cols].sum(axis=1) > 0)
                     df = df[mask]
                     
                     if not df.empty:
                        # Date Convert
                        df['Date'] = safe_parse_date_column(df['Date'])
                        df = df.dropna(subset=['Date'])
                        
                        # Shift Convert
                        if 'Shift' in df.columns:
                            def clean_shift(x):
                                x = str(x).lower().replace('shift', '').strip()
                                import re
                                m = re.search(r'\d+', x)
                                if m: return int(m.group())
                                if x == 'i': return 1
                                if x == 'ii': return 2
                                if x == 'iii': return 3
                                return 1
                            df['Shift'] = df['Shift'].apply(clean_shift)
                        
                        found_dfs.append(df)
        
        if found_dfs:
            final_df = pd.concat(found_dfs, ignore_index=True)
            return final_df
        else:
            return pd.DataFrame()

    except Exception as e:
        print(f"Error parsing Shipping: {e}")
        return pd.DataFrame()

# ============================================================
# 5. DAILY PLAN PARSER
# ============================================================
def parse_daily_plan_data(source):
    try:
        # Header is at Row 3 (Index 2)
        try:
            df = pd.read_excel(source, sheet_name='Scheduling', header=2, engine='openpyxl')
        except:
            if hasattr(source, 'seek'): source.seek(0)
            df = pd.read_excel(source, sheet_name='Scheduling', header=2)
        if df.empty: return pd.DataFrame()
        
        if 'Tanggal' in df.columns:
            df['Tanggal'] = safe_parse_date_column(df['Tanggal'])
            df = df.dropna(subset=['Tanggal'])
        else: return pd.DataFrame()
        
        # Map columns
        # User confirmed headers: Hari, Tanggal, Shift, Batu Kapur, Silika, Clay, Alat Muat, Alat Angkut, Blok, Grid, ROM, Keterangan
        col_map = {
            'Hari': 'Hari',
            'Batu Kapur': 'Batu Kapur', 'Silika': 'Silika', 'Clay': 'Clay',
            'Alat Muat': 'Alat Muat', 'Alat Angkut': 'Alat Angkut',
            'Blok': 'Blok', 'Grid': 'Grid', 'ROM': 'ROM', 'Keterangan': 'Keterangan'
        }
        
        # Clean numeric
        for c in ['Batu Kapur', 'Silika', 'Clay']:
            if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
            
        return df
    except: return pd.DataFrame()

# ============================================================
# 6. TARGET PARSER (Analisa Produksi -> RKAP)
# ============================================================
def parse_target_data(source):
    try:
        try:
            xls = pd.ExcelFile(source, engine='openpyxl')
        except:
            if hasattr(source, 'seek'): source.seek(0)
            xls = pd.ExcelFile(source)
        if 'Analisa Produksi' not in xls.sheet_names:
            return pd.DataFrame()
            
        df = pd.read_excel(xls, sheet_name='Analisa Produksi', header=0)
        
        # Structure is dynamic: "Januari 2025", "Februari 2025" columns
        # We need to unpivot (melt) this.
        
        # 1. Identify Month Columns
        # Regex for 'Month Year' (Bahasa or English)
        # e.g. "Januari 2025", "Feb 2026"
        month_cols = []
        for c in df.columns:
            if re.match(r'.*\d{4}', str(c)):
                month_cols.append(c)
                
        if not month_cols: return pd.DataFrame()
        
        # 2. Extract values
        # Rows might be dates (1, 2, 3...) or Full Dates
        # Based on previous code in loader, it seemed to just grab the column?
        # Let's assume the rows 1..31 correspond to days.
        # But wait, looking at the previous loader attempt:
        # It relies on 'Unnamed: 0' or similar being the day?
        # Actually, let's assume the first column is Day (1-31).
        
        # Let's Inspect Row 0-35
        # Usually: Col 0 = Date/Day. Other Cols = Plan values.
        
        # Safe strategy: Melt everything
        df_melted = df.melt(var_name='MonthYear', value_name='Plan')
        
        # But we need the Day info.
        # Let's assume Index is Day-1? Or Column 0 is Day?
        # Re-read with header=None to check structure?
        # Let's stick to the previous loader logic which seemed to work (lines 1840+)
        # Wait, the previous loader FAILED or was slow.
        # Let's assume simple structure:
        # Col 0: "Tanggal" (1, 2, ..., 31)
        # Col 1: "Januari 2025"
        # Col 2: "Februari 2025"...
        
        if 'Tanggal' not in df.columns and 'Date' not in df.columns:
            # Maybe the first column is implicitly Date
            df = df.rename(columns={df.columns[0]: 'Day'})
        else:
            col = 'Tanggal' if 'Tanggal' in df.columns else 'Date'
            df = df.rename(columns={col: 'Day'})
            
        # Clean Day
        df['Day'] = pd.to_numeric(df['Day'], errors='coerce')
        df = df.dropna(subset=['Day'])
        df = df[(df['Day'] >= 1) & (df['Day'] <= 31)]
        
        records = []
        for _, row in df.iterrows():
            day = int(row['Day'])
            for m_col in month_cols:
                # Parse Month Year from Header
                try:
                    # m_col: "Januari 2025"
                    # Translate ID -> EN
                    m_str = m_col.lower().replace('januari', 'january').replace('februari', 'february') \
                                         .replace('maret', 'march').replace('mei', 'may') \
                                         .replace('juni', 'june').replace('juli', 'july') \
                                         .replace('agustus', 'august').replace('oktober', 'october') \
                                         .replace('desember', 'december')
                    
                    dt_month = pd.to_datetime(m_str, format='%B %Y')
                    
                    # Construct valid date
                    try:
                        full_date = datetime(dt_month.year, dt_month.month, day).date()
                        plan_val = pd.to_numeric(row[m_col], errors='coerce')
                        if pd.notna(plan_val):
                            records.append({'Date': full_date, 'Plan': float(plan_val)})
                    except ValueError:
                        continue # Dayout of range (e.g. Feb 30)
                except:
                    continue
                    
        return pd.DataFrame(records)
    except: return pd.DataFrame()

