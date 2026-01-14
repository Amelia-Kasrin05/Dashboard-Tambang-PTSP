import pandas as pd
import streamlit as st
from datetime import datetime
import os

# ============================================================
# 1. LOAD PRODUKSI HARIAN
# ============================================================
@st.cache_data
def load_produksi():
    """Load data produksi harian dengan fix kolom bergeser"""
    possible_names = [
        'data/Produksi_UTSG_Harian.xlsx',
        'data/Produksi UTSG Harian.xlsx',
        'data/Produksi_UTSG_Harian .xlsx',
    ]
    
    df = None
    for file_path in possible_names:
        if os.path.exists(file_path):
            try:
                df = pd.read_excel(file_path, sheet_name='Tahun 2025')
                # File loaded successfully
                break
            except Exception as e:
                pass
                continue
    
    if df is None:
        # File not found
        return pd.DataFrame()
    
    try:
        # Hapus header berulang & validasi shift
        df = df[df['Shift'] != 'Shift']
        valid_shifts = ['Shift 1', 'Shift 2', 'Shift 3']
        df = df[df['Shift'].isin(valid_shifts)]
        
        # --- DATE: pastikan hanya tanggal ---
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date

        # --- TIME: biarkan terpisah (string / jam saja) ---
        if 'Time' in df.columns:
            df['Time'] = df['Time'].astype(str)
        else:
            df['Time'] = ''


        
        # Deteksi & perbaiki kolom bergeser (Sept+)
        mask_normal = df['Excavator'].astype(str).str.startswith('PC', na=False)
        df_normal = df[mask_normal].copy()
        df_shifted = df[~mask_normal].copy()
        
        if len(df_shifted) > 0:
            df_shifted_fixed = pd.DataFrame()
            df_shifted_fixed['Date'] = df_shifted['Date']
            df_shifted_fixed['Time'] = df_shifted['Time']
            df_shifted_fixed['Shift'] = df_shifted['Shift']

            # 🔥 BLOK DIAMBIL DARI KOLOM FRONT LAMA
            df_shifted_fixed['BLOK'] = df_shifted['Front']

            df_shifted_fixed['Front'] = df_shifted['Commudity']
            df_shifted_fixed['Commudity'] = df_shifted['Excavator']
            df_shifted_fixed['Excavator'] = df_shifted['Dump Truck']
            df_shifted_fixed['Dump Truck'] = df_shifted['Dump Loc']
            df_shifted_fixed['Dump Loc'] = df_shifted['Rit']
            df_shifted_fixed['Rit'] = df_shifted['Tonnase']
            df_shifted_fixed['Tonnase'] = df_shifted['Unnamed: 10']

            df = pd.concat([df_normal, df_shifted_fixed], ignore_index=True)
        
        # Hapus kolom Unnamed & validasi
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        df = df[df['Excavator'].astype(str).str.startswith('PC', na=False)]
        
        # Clean numeric
        df['Rit'] = pd.to_numeric(df['Rit'], errors='coerce')
        df['Tonnase'] = pd.to_numeric(df['Tonnase'], errors='coerce')
        
        # Clean Dump Truck
        df['Dump Truck'] = df['Dump Truck'].astype(str)
        df = df[df['Dump Truck'].str.match(r'^\d+$', na=False)]
        
        # Final cleanup
        df = df.dropna(subset=['Tonnase'])
        df = df[df['Tonnase'] > 0]
        df = df.reset_index(drop=True)
                # Pastikan kolom selalu ada (untuk bulan lama)
        for col in ['BLOK', 'Dump Loc']:
            if col not in df.columns:
                df[col] = ''

        return df
        
    except Exception as e:
        st.error(f"Error processing produksi: {e}")
        return pd.DataFrame()


# ============================================================
# 2. LOAD GANGGUAN
# ============================================================
@st.cache_data
def load_gangguan(bulan):
    """Load data gangguan per bulan"""
    possible_names = [
        'data/Gangguan_Produksi_2025_baru.xlsx',
        'data/Gangguan Produksi 2025 baru.xlsx',
    ]
    
    sheet = f'Monitoring {bulan}'
    
    for file_path in possible_names:
        if os.path.exists(file_path):
            try:
                df = pd.read_excel(file_path, sheet_name=sheet, skiprows=1)
                
                # Rename kolom
                if len(df.columns) >= 3:
                    df.columns = ['Row Labels', 'Frekuensi', 'Persentase']
                
                # Clean data
                df = df[df['Row Labels'] != 'Row Labels']
                df = df[df['Row Labels'] != 'Grand Total']
                df['Frekuensi'] = pd.to_numeric(df['Frekuensi'], errors='coerce')
                df = df.dropna(subset=['Frekuensi'])
                df = df[df['Frekuensi'] > 0]
                df = df.reset_index(drop=True)
                
                return df
            except Exception as e:
                continue
    
    return pd.DataFrame()


# ============================================================
# 3. LOAD BBM
# ============================================================
@st.cache_data
def load_bbm():
    """Load data BBM"""
    possible_names = [
        'data/Monitoring_2025_.xlsx',
        'data/Monitoring 2025_.xlsx',
    ]
    
    for file_path in possible_names:
        if os.path.exists(file_path):
            try:
                df = pd.read_excel(file_path, sheet_name='BBM')
                
                # Hapus baris header yang ikut terbaca
                if 'Total' in df.columns:
                    df = df[df['Total'] != 'Total']
                    df['Total'] = pd.to_numeric(df['Total'], errors='coerce').fillna(0)
                
                # Convert kolom tanggal (1-31) ke numerik
                for col in df.columns:
                    if col not in ['No', 'Alat Berat', 'Tipe Alat', 'Total']:
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
                # Filter data valid
                df = df[df['No'].notna()]
                df = df[df['Alat Berat'].notna()]
                df = df.reset_index(drop=True)
                
                return df
            except Exception as e:
                continue
    
    return pd.DataFrame()


# ============================================================
# 4. LOAD ANALISA PRODUKSI (Plan vs Aktual)
# ============================================================
@st.cache_data
def load_analisa_produksi(bulan='Januari'):
    """Load data analisa produksi per bulan"""
    possible_names = [
        'data/Monitoring_2025_.xlsx',
        'data/Monitoring 2025_.xlsx',
    ]
    
    # Mapping bulan ke index kolom
    bulan_map = {
        'Januari': 0,
        'Februari': 5,
    }
    
    if bulan not in bulan_map:
        return pd.DataFrame()
    
    start_col = bulan_map[bulan]
    
    for file_path in possible_names:
        if os.path.exists(file_path):
            try:
                df = pd.read_excel(file_path, sheet_name='Analisa Produksi')
                
                # Ambil kolom untuk bulan tertentu
                df_bulan = df.iloc[1:32, start_col:start_col+4].copy()
                df_bulan.columns = ['Tanggal', 'Plan', 'Aktual', 'Ketercapaian']
                
                # Clean data
                df_bulan['Tanggal'] = pd.to_numeric(df_bulan['Tanggal'], errors='coerce')
                df_bulan['Plan'] = pd.to_numeric(df_bulan['Plan'], errors='coerce')
                df_bulan['Aktual'] = pd.to_numeric(df_bulan['Aktual'], errors='coerce')
                df_bulan['Ketercapaian'] = pd.to_numeric(df_bulan['Ketercapaian'], errors='coerce')
                
                df_bulan = df_bulan.dropna(subset=['Tanggal'])
                df_bulan['Bulan'] = bulan
                df_bulan = df_bulan.reset_index(drop=True)
                
                return df_bulan
            except Exception as e:
                continue
    
    return pd.DataFrame()


# ============================================================
# 5. LOAD RITASE
# ============================================================
@st.cache_data
def load_ritase():
    """Load data ritase dengan cleaning"""
    possible_names = [
        'data/Monitoring_2025_.xlsx',
        'data/Monitoring 2025_.xlsx',
    ]
    
    for file_path in possible_names:
        if os.path.exists(file_path):
            try:
                df = pd.read_excel(file_path, sheet_name='Ritase')
                
                # Kolom yang dibutuhkan (sampai kolom 16)
                cols_keep = ['Tanggal', 'Shift', 'Pengawasan', 'Front B LS', 'Front B Clay', 
                            'Front B LS MIX', 'Front C LS', 'Front C LS MIX', 'PLB LS', 
                            'PLB SS', 'PLT SS', 'PLT MIX', 'Timbunan', 'Stockpile 6  SS', 
                            'PLT LS MIX', 'Stockpile 6 ']
                
                available_cols = [col for col in cols_keep if col in df.columns]
                df = df[available_cols].copy()
                
                # Convert Tanggal
                df['Tanggal'] = pd.to_datetime(df['Tanggal'], errors='coerce')
                df = df[df['Tanggal'].notna()]
                
                # Hapus baris dengan Shift bukan angka
                df = df[df['Shift'].isin([1, 2, 3, '1', '2', '3'])]
                df['Shift'] = df['Shift'].astype(str)
                
                # Convert kolom numerik
                numeric_cols = [col for col in df.columns if col not in ['Tanggal', 'Shift', 'Pengawasan']]
                for col in numeric_cols:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
                df = df.reset_index(drop=True)
                return df
            except Exception as e:
                continue
    
    return pd.DataFrame()


# ============================================================
# 6. LOAD DAILY PLAN
# ============================================================
@st.cache_data
def load_daily_plan():
    """Load data daily plan scheduling"""
    try:
        df = pd.read_excel('data/DAILY_PLAN.xlsx', sheet_name='W22 Scheduling', skiprows=1)
        
        # Rename kolom dari baris pertama
        new_cols = ['No', 'Hari', 'Tanggal', 'Shift', 'Batu Kapur', 'Silika', 
                    'Clay', 'Alat Muat', 'Alat Angkut', 'Blok', 'Grid', 'ROM', 'Keterangan']
        
        if len(df.columns) >= len(new_cols):
            df.columns = new_cols + list(df.columns[len(new_cols):])
        
        # Skip header row
        df = df.iloc[1:].copy()
        
        # Clean Tanggal
        df['Tanggal'] = pd.to_datetime(df['Tanggal'], errors='coerce')
        
        # Filter data valid
        df = df[df['Hari'].notna()]
        df = df[df['Hari'] != 'Hari']
        
        # Ambil kolom yang dibutuhkan
        cols_keep = ['Hari', 'Tanggal', 'Shift', 'Batu Kapur', 'Silika', 'Clay', 
                     'Alat Muat', 'Alat Angkut', 'Blok', 'Grid', 'ROM', 'Keterangan']
        available = [c for c in cols_keep if c in df.columns]
        df = df[available].copy()
        
        df = df.dropna(how='all')
        df = df.reset_index(drop=True)
        
        return df
    except Exception as e:
        pass
        return pd.DataFrame()


# ============================================================
# 7. LOAD REALISASI
# ============================================================
@st.cache_data
def load_realisasi():
    """Load data realisasi dari W22 realisasi"""
    try:
        df = pd.read_excel('data/DAILY_PLAN.xlsx', sheet_name='W22 realisasi', skiprows=1)
        
        # Rename kolom
        new_cols = ['No', 'Hari', 'Tanggal', 'Week', 'Shift', 'Batu Kapur', 'Silika', 
                    'Timbunan', 'Alat Bor', 'Alat Muat', 'Alat Angkut', 'Blok', 'Grid', 
                    'ROM', 'Keterangan']
        
        if len(df.columns) >= len(new_cols):
            df.columns = new_cols + list(df.columns[len(new_cols):])
        
        # Skip header row
        df = df.iloc[1:].copy()
        
        # Clean Tanggal
        df['Tanggal'] = pd.to_datetime(df['Tanggal'], errors='coerce')
        
        # Filter valid
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
    except Exception as e:
        pass
        return pd.DataFrame()