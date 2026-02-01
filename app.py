# ============================================================
# MINING DASHBOARD - Semen Padang
# ============================================================
# Main entry point - Minimal & Clean

import streamlit as st

# Page Config (must be first Streamlit command)
st.set_page_config(
    page_title="Mining Dashboard | Semen Padang",
    page_icon="assets/logo_semen_padang.jpg",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import components
# Import components
from components import inject_css, show_login, render_sidebar
from views import (
    show_dashboard, 
    show_produksi,
    show_ritase,
    show_gangguan,
    show_daily_plan,
    # show_monitoring # Deprecated
)

# Debug Helper
import requests
import pandas as pd
from config.settings import ONEDRIVE_LINKS
from utils.data_loader import convert_onedrive_link, download_from_onedrive

def show_debug_page():
    st.title("🔌 Connection Debugger")
    
    st.info("Halaman ini untuk mengecek status koneksi ke OneDrive.")
    
    for key, link in ONEDRIVE_LINKS.items():
        if not link:
            continue
            
        with st.expander(f"Test Link: {key.upper()}", expanded=True):
            st.code(link)
            direct_url = convert_onedrive_link(link)
            st.write(f"**Converted URL:** `{direct_url}`")
            
            if st.button(f"Test Download {key}", key=f"btn_{key}"):
                try:
                    r = requests.get(direct_url, timeout=10)
                    st.write(f"Status Code: `{r.status_code}`")
                    st.write(f"Content Type: `{r.headers.get('Content-Type')}`")
                    st.write(f"Size: `{len(r.content)} bytes`")
                    
                    if r.status_code == 200:
                        st.success("Download Successful!")
                        if len(r.content) > 1000:
                            try:
                                from io import BytesIO
                                df_check = pd.read_excel(BytesIO(r.content))
                                st.dataframe(df_check.head())
                            except Exception as e:
                                st.error(f"Excel Parse Error: {e}")
                        else:
                            st.warning("File too small, possibly an error HTML page?")
                            st.code(r.text[:500])
                    else:
                        st.error("Download Failed")
                except Exception as e:
                    st.error(f"Exception: {e}")
# Placeholder imports for new modules (create files next)
try:
    from views.process import show_process
except ImportError:
    def show_process(): st.title("⚙️ Stockpile & Process (Under Construction)")

try:
    from views.shipping import show_shipping
except ImportError:
    def show_shipping(): st.title("🚢 Sales & Shipping (Under Construction)")

# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.name = None

if 'current_menu' not in st.session_state:
    st.session_state.current_menu = "Ringkasan Eksekutif"


# ============================================================
# MAIN APPLICATION
# ============================================================
def main():
    # Inject CSS styling
    inject_css()
    
    if not st.session_state.logged_in:
        show_login()
    else:
        render_sidebar()
        
        # Route to pages
        menu = st.session_state.current_menu
        
        if menu == "Ringkasan Eksekutif" or menu == "Executive Summary":
            show_dashboard()
        elif menu == "Kinerja Produksi" or menu == "Produksi":
            show_produksi()
        elif menu == "Aktivitas Ritase" or menu == "Ritase":
            show_ritase()
        elif menu == "Stockpile & Pengolahan" or menu == "Stockpile & Proses":
            show_process()
        elif menu == "Analisa Kendala" or menu == "Gangguan Unit":
            show_gangguan()
        elif menu == "Pengiriman & Logistik":
            show_shipping()
        elif menu == "Rencana Harian" or menu == "Daily Plan":
            show_daily_plan()
        elif menu == "Debug Connection":
            show_debug_page()
        else:
            show_dashboard()


if __name__ == "__main__":
    main()
