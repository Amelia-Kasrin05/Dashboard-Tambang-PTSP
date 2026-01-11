import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
sys.path.append('.')
from utils.data_loader import *
from config import USERS, COLORS, CHART_COLORS

st.set_page_config(page_title="Dashboard Tambang Semen Padang", page_icon="⛏️", layout="wide")

# CSS
st.markdown(f"""
<style>
.stApp {{background: linear-gradient(135deg, #1a1a2e 0%, #0f0f23 100%);}}
.main-header {{font-size:2rem;font-weight:700;background:linear-gradient(90deg,#00C853,#2196F3);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-align:center;padding:1rem;}}
.sub-header {{font-size:1.1rem;color:#00C853;border-left:4px solid #00C853;padding-left:12px;margin:1rem 0;font-weight:600;}}
div[data-testid="stSidebar"] {{background:linear-gradient(180deg,#1a1a2e,#0a0a1a);}}
</style>
""", unsafe_allow_html=True)

# Session
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = st.session_state.role = st.session_state.name = None

def login(u, p):
    if u in USERS and USERS[u]['password'] == p:
        st.session_state.logged_in, st.session_state.username = True, u
        st.session_state.role, st.session_state.name = USERS[u]['role'], USERS[u]['name']
        return True
    return False

def logout():
    st.session_state.logged_in = False
    st.session_state.username = st.session_state.role = st.session_state.name = None

# LOGIN PAGE
def show_login():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown('<p class="main-header">⛏️ Dashboard Tambang</p>', unsafe_allow_html=True)
        st.markdown('<h4 style="text-align:center;color:#888;">Semen Padang Mining Operations</h4>', unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Login", use_container_width=True):
                if login(u, p): st.rerun()
                else: st.error("❌ Login gagal!")
        st.caption("Demo: supervisor/super123 | admin_produksi/prod123")

# SUPERVISOR DASHBOARD
def show_supervisor():
    st.markdown('<p class="main-header">📊 Dashboard Supervisor</p>', unsafe_allow_html=True)
    df = load_produksi()
    
    if df.empty: st.warning("⚠️ Data tidak tersedia"); return
    
    # KPI
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("🚛 Ritase", f"{df['Rit'].sum():,.0f}")
    c2.metric("⚖️ Tonase", f"{df['Tonnase'].sum():,.0f}")
    c3.metric("🏗️ Excavator", df['Excavator'].nunique())
    c4.metric("📅 Hari", df['Date'].nunique())
    c5.metric("📊 Avg/Hari", f"{df.groupby('Date')['Tonnase'].sum().mean():,.0f}")
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    with col1:
        daily = df.groupby('Date')['Tonnase'].sum().reset_index()
        fig = go.Figure(go.Scatter(x=daily['Date'], y=daily['Tonnase'], mode='lines+markers', fill='tozeroy',
                                   line=dict(color='#00E676',width=3), fillcolor='rgba(0,230,118,0.2)'))
        fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=320, title='Tren Produksi')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        exc = df.groupby('Excavator')['Tonnase'].sum().reset_index().sort_values('Tonnase')
        fig = px.bar(exc, x='Tonnase', y='Excavator', orientation='h', color_discrete_sequence=['#2979FF'])
        fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=320, title='Per Excavator')
        st.plotly_chart(fig, use_container_width=True)
    
    c1,c2,c3 = st.columns(3)
    with c1:
        mat = df.groupby('Commudity')['Tonnase'].sum().reset_index()
        fig = px.pie(mat, values='Tonnase', names='Commudity', color_discrete_sequence=CHART_COLORS)
        fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', height=280, title='Material')
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        shift = df.groupby('Shift')['Tonnase'].sum().reset_index()
        fig = px.bar(shift, x='Shift', y='Tonnase', color_discrete_sequence=['#00E676','#2979FF','#FF6D00'])
        fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=280, title='Per Shift')
        st.plotly_chart(fig, use_container_width=True)
    with c3:
        dg = load_gangguan("Januari")
        if not dg.empty:
            fig = px.bar(dg.head(5), x='Frekuensi', y='Row Labels', orientation='h', color_discrete_sequence=['#FF5252'])
            fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=280, title='Top 5 Gangguan', yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
    
    # Quick Access
    st.markdown("---")
    st.markdown("**🔗 Dashboard Admin**")
    c1,c2,c3,c4,c5 = st.columns(5)
    for c, (icon, name, status) in zip([c1,c2,c3,c4,c5], [("⚙️","Produksi","✅"),("🔧","Alat","🔒"),("⛽","BBM","🔒"),("📋","Planning","🔒"),("🛡️","Safety","🔒")]):
        color = "#1B5E20" if status=="✅" else "#424242"
        c.markdown(f'<div style="background:{color};padding:1rem;border-radius:10px;text-align:center;"><h3 style="color:#fff;margin:0;">{icon}</h3><p style="color:#fff;margin:0;">{name}</p><small style="color:#aaa;">{status}</small></div>', unsafe_allow_html=True)

# PRODUKSI DASHBOARD
def show_produksi():
    st.markdown('<p class="main-header">⚙️ Dashboard Produksi</p>', unsafe_allow_html=True)
    tab1,tab2,tab3,tab4 = st.tabs(["📊 Overview","🚨 Gangguan","📈 Monitoring","📋 Plan"])
    df = load_produksi()
    
    with tab1:
        if df.empty: st.warning("⚠️ Data tidak tersedia"); return
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("🚛 Ritase", f"{df['Rit'].sum():,.0f}")
        c2.metric("⚖️ Tonase", f"{df['Tonnase'].sum():,.0f}")
        c3.metric("📊 Avg", f"{df['Tonnase'].mean():.0f}")
        c4.metric("🏗️ Excavator", df['Excavator'].nunique())
        
        daily = df.groupby('Date')['Tonnase'].sum().reset_index()
        fig = go.Figure(go.Scatter(x=daily['Date'], y=daily['Tonnase'], mode='lines+markers', fill='tozeroy', line=dict(color='#00E676'), fillcolor='rgba(0,230,118,0.2)'))
        fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=350)
        st.plotly_chart(fig, use_container_width=True)
        
        c1,c2,c3 = st.columns(3)
        with c1:
            fig = px.pie(df.groupby('Shift')['Tonnase'].sum().reset_index(), values='Tonnase', names='Shift', color_discrete_sequence=['#00E676','#2979FF','#FF6D00'])
            fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', height=280)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            exc = df.groupby('Excavator')['Tonnase'].sum().reset_index().sort_values('Tonnase')
            fig = px.bar(exc, x='Tonnase', y='Excavator', orientation='h', color_discrete_sequence=['#2979FF'])
            fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=280)
            st.plotly_chart(fig, use_container_width=True)
        with c3:
            fig = px.pie(df.groupby('Commudity')['Tonnase'].sum().reset_index(), values='Tonnase', names='Commudity', color_discrete_sequence=CHART_COLORS)
            fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', height=280)
            st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(df[['Date','Shift','Front','Commudity','Excavator','Dump Truck','Rit','Tonnase']].sort_values('Date',ascending=False), use_container_width=True, height=300)
    
    with tab2:
        bulan = st.selectbox("Bulan", ["Januari","Februari","Maret","April","Mei","Juni","Juli","Agustus","September","Oktober","November","Desember"])
        dg = load_gangguan(bulan)
        if not dg.empty:
            c1,c2,c3 = st.columns(3)
            c1.metric("Jenis", len(dg))
            c2.metric("Total", f"{dg['Frekuensi'].sum():,.0f}")
            c3.metric("Top", dg.iloc[0]['Row Labels'])
            
            dp = dg.head(10).copy()
            dp['Kum'] = (dp['Frekuensi'].cumsum()/dg['Frekuensi'].sum()*100)
            fig = go.Figure()
            fig.add_trace(go.Bar(x=dp['Row Labels'], y=dp['Frekuensi'], marker_color='#FF5252'))
            fig.add_trace(go.Scatter(x=dp['Row Labels'], y=dp['Kum'], yaxis='y2', marker_color='#FFEA00', mode='lines+markers'))
            fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', yaxis2=dict(overlaying='y',side='right',range=[0,105]), height=400)
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(dg, use_container_width=True, height=300)
    
    with tab3:
        mon = st.radio("", ["⛽ BBM","📊 Plan vs Aktual","🚛 Ritase"], horizontal=True)
        if mon == "⛽ BBM":
            db = load_bbm()
            if not db.empty:
                c1,c2 = st.columns(2)
                with c1:
                    fig = px.pie(db.groupby('Alat Berat')['Total'].sum().reset_index(), values='Total', names='Alat Berat', color_discrete_sequence=['#FF6D00','#FFEA00'])
                    fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', height=300)
                    st.plotly_chart(fig, use_container_width=True)
                with c2:
                    fig = px.bar(db.nlargest(10,'Total'), x='Total', y='Tipe Alat', orientation='h', color_discrete_sequence=['#FF6D00'])
                    fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=300)
                    st.plotly_chart(fig, use_container_width=True)
        elif mon == "📊 Plan vs Aktual":
            bln = st.selectbox("Bulan", ["Januari","Februari"])
            da = load_analisa_produksi(bln)
            if not da.empty:
                fig = go.Figure()
                fig.add_trace(go.Bar(x=da['Tanggal'], y=da['Plan'], name='Plan', marker_color='#2979FF'))
                fig.add_trace(go.Bar(x=da['Tanggal'], y=da['Aktual'], name='Aktual', marker_color='#00E676'))
                fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', barmode='group', height=400)
                st.plotly_chart(fig, use_container_width=True)
        else:
            dr = load_ritase()
            if not dr.empty:
                rc = [c for c in dr.columns if c not in ['Tanggal','Shift','Pengawasan']]
                tot = dr[rc].sum().reset_index()
                tot.columns = ['Front','Total']
                fig = px.bar(tot.sort_values('Total',ascending=False), x='Front', y='Total', color_discrete_sequence=['#2979FF'])
                fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=350, xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        t1,t2 = st.tabs(["📅 Plan","✅ Realisasi"])
        with t1:
            dp = load_daily_plan()
            if not dp.empty: st.dataframe(dp, use_container_width=True, height=400)
        with t2:
            dr = load_realisasi()
            if not dr.empty: st.dataframe(dr, use_container_width=True, height=400)

# MAIN
def main():
    if not st.session_state.logged_in:
        show_login()
    else:
        with st.sidebar:
            st.markdown(f"### 👤 {st.session_state.name}")
            st.caption(f"Role: {st.session_state.role.title()}")
            st.markdown("---")
            if st.session_state.role == 'supervisor':
                menu = st.radio("Menu", ["🏠 Dashboard Utama","⚙️ Produksi Detail"])
            else:
                menu = "⚙️ Dashboard Produksi"
            st.markdown("---")
            if st.button("🚪 Logout", use_container_width=True): logout(); st.rerun()
            st.markdown("---")
            st.caption("Dashboard Tambang\nSemen Padang v2.0")
        
        if st.session_state.role == 'supervisor' and menu == "🏠 Dashboard Utama":
            show_supervisor()
        else:
            show_produksi()

if __name__ == "__main__":
    main()