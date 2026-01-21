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
from components import inject_css, show_login, render_sidebar
from views import (
    show_dashboard, 
    show_produksi, 
    show_gangguan, 
    show_monitoring, 
    show_daily_plan
)

# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.name = None

if 'current_menu' not in st.session_state:
    st.session_state.current_menu = "Dashboard"


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
        if st.session_state.current_menu == "Dashboard":
            show_dashboard()
        elif st.session_state.current_menu == "Produksi":
            show_produksi()
        elif st.session_state.current_menu == "Gangguan":
            show_gangguan()
        elif st.session_state.current_menu == "Monitoring":
            show_monitoring()
        elif st.session_state.current_menu == "Daily Plan":
            show_daily_plan()


if __name__ == "__main__":
    main()
