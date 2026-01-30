# ============================================================
# SIDEBAR - Navigation Component
# ============================================================

import streamlit as st
from config import CACHE_TTL
from utils import check_onedrive_status
from utils.helpers import get_logo_base64
from .login import logout


def render_sidebar():
    """Render sidebar navigation"""
    logo_base64 = get_logo_base64()
    
    with st.sidebar:
        # Logo & Brand
        if logo_base64:
            logo_html = f'<img src="data:image/jpeg;base64,{logo_base64}" alt="Logo" style="width:60px; height:auto; border-radius:10px; margin-bottom:0.5rem; box-shadow: 0 4px 16px rgba(0,0,0,0.3);">'
        else:
            logo_html = '<span style="font-size:2rem;">⛏️</span>'
        
        st.markdown(f"""
        <div style="text-align:center; padding:1rem 0 0.5rem 0;">
            {logo_html}
            <p style="color:#d4a84b; font-weight:700; font-size:1.1rem; margin:0.5rem 0 0 0;">
                MINING OPS
            </p>
            <p style="color:#64748b; font-size:0.7rem; margin:0;">Semen Padang</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # User Card
        st.markdown(f"""
        <div class="user-card">
            <div class="user-avatar">👤</div>
            <p class="user-name">{st.session_state.name}</p>
            <p class="user-role">{st.session_state.role}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Connection Status
        st.markdown('<p class="nav-label">📡 Data Status</p>', unsafe_allow_html=True)
        
        status = check_onedrive_status()
        status_html = '<div class="status-grid">'
        for name, stat in status.items():
            if "✅" in stat:
                status_class = "status-ok"
            elif "⚠️" in stat:
                status_class = "status-warn"
            else:
                status_class = "status-err"
            status_html += f'<div class="status-item"><span class="status-name">{name}</span><span class="status-value {status_class}">{stat}</span></div>'
        status_html += '</div>'
        st.markdown(status_html, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
        with col2:
            st.markdown(f'<p style="color:#64748b; font-size:0.75rem; text-align:center; margin-top:0.5rem;">Cache: {CACHE_TTL}s</p>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # ============================================================
        # GLOBAL FILTERS (NEW)
        # ============================================================
        st.markdown('<p class="nav-label">🔍 Global Filters</p>', unsafe_allow_html=True)
        
        # 1. Date Range
        from datetime import date
        today = date.today()
        # Default start date: Jan 1, 2026 as per user request
        default_start = date(2026, 1, 1)
        
        # Initialize session state for filters if not exists
        if 'global_filters' not in st.session_state:
            st.session_state.global_filters = {
                'date_range': (default_start, today),
                'shift': 'All Displatch'
            }
            
        date_range = st.date_input(
            "📅 Rentang Tanggal",
            value=(default_start, today),
            key="filter_date_range"
        )
        
        
        # Load data ONCE for all filters
        from utils.data_loader import load_produksi
        df_prod = load_produksi()

        # 2. Shift Filter (Dynamic)
        # Load unique shifts
        shift_options = ["All Displatch"]
        if not df_prod.empty and 'Shift' in df_prod.columns:
            # Get unique shifts, convert to string, sort
            unique_shifts = sorted(df_prod['Shift'].astype(str).unique().tolist())
            shift_options.extend(unique_shifts)
        else:
            shift_options.extend(["Shift 1", "Shift 2"]) # Fallback
            
        shift_select = st.selectbox(
            "🕒 Shift Operasional",
            shift_options,
            index=0,
            key="filter_shift"
        )
        
        # 3. Dynamic Filters (Front & Excavator)
        # Data already loaded above
        
        # Front Filter
        
        # Front Filter
        front_options = sorted(df_prod['Front'].dropna().unique().tolist()) if not df_prod.empty and 'Front' in df_prod.columns else []
        front_select = st.multiselect(
            "📍 Lokasi Kerja (Front)",
            options=front_options,
            default=[],
            placeholder="Pilih Front (Opsional)",
            key="filter_front"
        )
        
        # Excavator Filter
        exca_options = sorted(df_prod['Excavator'].dropna().unique().tolist()) if not df_prod.empty and 'Excavator' in df_prod.columns else []
        exca_select = st.multiselect(
            "🚜 Unit Excavator",
            options=exca_options,
            default=[],
            placeholder="Pilih Unit (Opsional)",
            key="filter_exca"
        )
        
        # Store in session state
        st.session_state.global_filters['date_range'] = date_range
        st.session_state.global_filters['shift'] = shift_select
        st.session_state.global_filters['front'] = front_select
        st.session_state.global_filters['excavator'] = exca_select
        
        st.markdown("---")
        
        # Navigation
        st.markdown('<p class="nav-label">📋 Navigation</p>', unsafe_allow_html=True)
        
        menus = [
            ("🏠", "Ringkasan Eksekutif"),
            ("⛏️", "Produksi"),
            ("🚛", "Ritase"),
            ("⚙️", "Stockpile & Proses"),
            ("🚨", "Gangguan Unit"),
            ("🚢", "Pengiriman & Logistik"),
            ("📋", "Daily Plan")
        ]
        
        for icon, menu in menus:
            # Map old menu names if needed or handle routing in app.py
            btn_type = "primary" if st.session_state.current_menu == menu else "secondary"
            if st.button(f"{icon}  {menu}", key=f"nav_{menu}", use_container_width=True, type=btn_type):
                st.session_state.current_menu = menu
                st.rerun()
        
        st.markdown("---")
        
        # Logout
        if st.button("🚪 Sign Out", use_container_width=True):
            logout()
            st.rerun()
        
        # Footer
        st.markdown("""
        <div style="text-align:center; margin-top:2rem; padding-top:1rem; border-top:1px solid #1e3a5f;">
            <p style="color:#64748b; font-size:0.7rem; margin:0;">
                Mining Dashboard v4.0<br>
                © 2025 Semen Padang
            </p>
        </div>
        """, unsafe_allow_html=True)
