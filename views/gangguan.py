# ============================================================
# GANGGUAN - Production Incident Page
# ============================================================

import streamlit as st


def show_gangguan():
    """Render production incident page"""
    
    st.markdown("""
    <div class="page-header">
        <div class="page-header-icon">🚨</div>
        <div class="page-header-text">
            <h1>Gangguan Produksi</h1>
            <p>Production incident analysis</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.info("🚧 Halaman ini akan di-redesign di tahap berikutnya")
