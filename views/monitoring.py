# ============================================================
# MONITORING - BBM & Ritase Monitoring Page
# ============================================================

import streamlit as st


def show_monitoring():
    """Render monitoring page"""
    
    st.markdown("""
    <div class="page-header">
        <div class="page-header-icon">⛽</div>
        <div class="page-header-text">
            <h1>Monitoring BBM & Ritase</h1>
            <p>Fuel consumption and trip monitoring</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.info("🚧 Halaman ini akan di-redesign di tahap berikutnya")
