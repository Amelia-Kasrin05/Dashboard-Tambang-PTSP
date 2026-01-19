# ============================================================
# LOGIN - Authentication Components
# ============================================================

import streamlit as st
from config import USERS
from utils.helpers import get_logo_base64


def login(username, password):
    """Authenticate user"""
    if username in USERS and USERS[username]['password'] == password:
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.role = USERS[username]['role']
        st.session_state.name = USERS[username]['name']
        return True
    return False


def logout():
    """Logout user"""
    for key in ['logged_in', 'username', 'role', 'name']:
        st.session_state[key] = None if key != 'logged_in' else False


def show_login():
    """Render login page"""
    logo_base64 = get_logo_base64()
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        # Logo section
        if logo_base64:
            logo_html = f'<img src="data:image/jpeg;base64,{logo_base64}" alt="Logo" style="width:100px; height:auto; margin-bottom:1rem; border-radius:16px; box-shadow: 0 8px 32px rgba(212,168,75,0.3);">'
        else:
            logo_html = '<div class="login-logo-icon">⛏️</div>'
        
        st.markdown(f"""
        <div class="login-container">
            <div class="login-card">
                <div class="login-logo">
                    {logo_html}
                    <h1 class="login-title">Mining Dashboard</h1>
                    <p class="login-subtitle">Semen Padang Operations Center</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form", clear_on_submit=False):
            st.markdown("##### 👤 Username")
            username = st.text_input("Username", label_visibility="collapsed", placeholder="Enter username")
            
            st.markdown("##### 🔒 Password")
            password = st.text_input("Password", type="password", label_visibility="collapsed", placeholder="Enter password")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.form_submit_button("🚀 Sign In", use_container_width=True, type="primary"):
                if login(username, password):
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")
        
        st.markdown("""
        <div style="text-align:center; margin-top:1.5rem; padding:1rem; background:rgba(212,168,75,0.1); border-radius:12px;">
            <p style="color:#94a3b8; font-size:0.85rem; margin:0;">
                <strong style="color:#d4a84b;">Demo Access:</strong><br>
                admin_produksi / prod123
            </p>
        </div>
        """, unsafe_allow_html=True)
