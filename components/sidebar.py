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
            
        # Unified Sync Button (Professional Single-Click Action)
        if st.button("🔄 Sync & Refresh Data", use_container_width=True, type="primary", help="Ambil data terbaru dari OneDrive dan perbarui tampilan"):
            with st.status("🔄 Sinkronisasi Data OneDrive...", expanded=True) as status:
                st.write("Menghubungkan ke Database...")
                st.cache_data.clear()
                st.cache_resource.clear()
                
                try:
                    from utils.sync_manager import sync_all_data
                    st.write("📥 Mengunduh & Memperbarui Data...")
                    
                    report = sync_all_data()
                    
                    for module, result in report.items():
                        if "✅" in result:
                            st.write(f"{module}: {result}")
                        else:
                            st.write(f"{module}: {result}")
                            
                    status.update(label="✅ Sinkronisasi Selesai!", state="complete", expanded=False)
                    st.toast("Data Berhasil Diperbarui!", icon="✅")
                    
                    import time
                    time.sleep(1)
                    st.rerun()
                    
                except Exception as e:
                    status.update(label="❌ Sinkronisasi Gagal", state="error")
                    st.error(f"Error: {str(e)}")
            
        try:
            from datetime import datetime
            current_time = datetime.now().strftime("%H:%M")
        except:
            current_time = "--:--"
        st.markdown(f'<p style="color:#64748b; font-size:0.75rem; text-align:center; margin-top:0.5rem;">Last Update: {current_time}</p>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # ============================================================
        # GLOBAL FILTERS (NEW)
        # ============================================================
        # ============================================================
        # GLOBAL FILTERS (NEW)
        # ============================================================
        # st.markdown('<p class="nav-label">🔍 Global Filters</p>', unsafe_allow_html=True) # Replaced by Expander

        # 1. Date Range
        from datetime import date
        today = date.today()
        # Default start date: Jan 1, 2026 (Safe default since data ends in Jan 26)
        # Optimized loaders handle this range easily now.
        default_start = date(2026, 1, 1)
        
        # Initialize session state for filters if not exists
        if 'global_filters' not in st.session_state:
            st.session_state.global_filters = {
                'date_range': (default_start, today),
                'shift': 'All Displatch',
                'front': [],
                'excavator': [],
                'material': []
            }

        with st.expander("🔍 Global Filters", expanded=True):
            # Reset Button
            if st.button("♻️ Reset Filter (Jan 26+)", use_container_width=True, help="Kembalikan filter ke Awal Tahun 2026"):
                 st.session_state.global_filters = {
                    'date_range': (date(2026, 1, 1), today),
                    'shift': 'All Displatch',
                    'front': [],
                    'excavator': [],
                    'material': []
                }
                 st.rerun()

            date_range = st.date_input(
                "📅 Rentang Tanggal",
                value=st.session_state.global_filters.get('date_range', (default_start, today)),
                key="filter_date_range"
            )
            
            
            
            # Load filter options from session_state (preloaded at login)
            # Falls back to loader only if not preloaded
            filter_options = st.session_state.get('filter_options', None)
            if not filter_options:
                from utils.data_loader import get_filter_options
                filter_options = get_filter_options()
                st.session_state['filter_options'] = filter_options
    
            # 2. Shift Filter (Dynamic from SQL)
            shift_options = ["All Displatch"]
            shift_options.extend(filter_options.get('shift', []))
                
            # Get current shift value safely
            current_shift = st.session_state.global_filters.get('shift', 'All Displatch')
            if current_shift not in shift_options:
                current_shift = 'All Displatch'
                
            shift_select = st.selectbox(
                "🕒 Shift Operasional",
                shift_options,
                index=shift_options.index(current_shift),
                key="filter_shift"
            )
            
            # 3. Dynamic Filters (Front & Excavator from SQL)
            
            # Front Filter
            front_select = st.multiselect(
                "📍 Lokasi Kerja (Front)",
                options=filter_options.get('front', []),
                default=st.session_state.global_filters.get('front', []),
                placeholder="Pilih Front (Opsional)",
                key="filter_front"
            )
            
            # Excavator Filter
            exca_select = st.multiselect(
                "🚜 Unit Excavator",
                options=filter_options.get('excavator', []),
                default=st.session_state.global_filters.get('excavator', []),
                placeholder="Pilih Unit (Opsional)",
                key="filter_exca"
            )
            
            # Material Filter
            mat_select = st.multiselect(
                "🪨 Jenis Material",
                options=filter_options.get('material', []),
                default=st.session_state.global_filters.get('material', []),
                placeholder="Pilih Material (Opsional)",
                key="filter_mat"
            )
            
            # Store in session state
            st.session_state.global_filters['date_range'] = date_range
            st.session_state.global_filters['shift'] = shift_select
            st.session_state.global_filters['front'] = front_select
            st.session_state.global_filters['excavator'] = exca_select
            st.session_state.global_filters['material'] = mat_select
        
        st.markdown("---")
        
        # Navigation
        st.markdown('<p class="nav-label">📋 Navigation</p>', unsafe_allow_html=True)
        
        menus = [
            ("🏠", "Ringkasan Eksekutif"),
            ("⛏️", "Kinerja Produksi"),
            ("🚛", "Aktivitas Ritase"),
            ("⚙️", "Stockpile & Pengolahan"),
            ("🚨", "Analisa Kendala"),
            ("🚢", "Pengiriman & Logistik"),
            ("📋", "Rencana Harian")
        ]
        
        def set_menu(menu_name):
            st.session_state.current_menu = menu_name
            
        for icon, menu in menus:
            # Map old menu names if needed or handle routing in app.py
            btn_type = "primary" if st.session_state.current_menu == menu else "secondary"
            st.button(
                f"{icon}  {menu}", 
                key=f"nav_{menu}", 
                use_container_width=True, 
                type=btn_type,
                on_click=set_menu,
                args=(menu,)
            )
        
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
