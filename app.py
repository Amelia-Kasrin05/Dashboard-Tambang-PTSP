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
        else:
            show_dashboard()


if __name__ == "__main__":
    main()
