# ============================================================
# HELPERS - Utility Functions
# ============================================================

import os
import base64

# ============================================================
# LOGO LOADER
# ============================================================

def get_logo_base64():
    """Load logo dan convert ke base64"""
    logo_paths = [
        "assets/logo_semen_padang.jpg",
        "logo_semen_padang.jpg",
        "logo.jpg", 
        "assets/logo.jpg",
        "static/logo.jpg",
        "images/logo.jpg"
    ]
    for path in logo_paths:
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    return base64.b64encode(f.read()).decode()
            except:
                continue
    return None


# ============================================================
# CHART LAYOUT
# ============================================================

def get_chart_layout(height=350, show_legend=True):
    """Professional chart layout for mining dashboard"""
    return dict(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=height,
        margin=dict(l=20, r=20, t=40, b=40),
        font=dict(family='Inter', color='#94a3b8'),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=True,
            linecolor='#1e3a5f',
            tickfont=dict(size=11)
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(30,58,95,0.5)',
            zeroline=False,
            showline=False,
            tickfont=dict(size=11)
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=-0.2,
            xanchor='center',
            x=0.5,
            bgcolor='rgba(0,0,0,0)'
        ) if show_legend else dict(visible=False),
        hoverlabel=dict(
            bgcolor='#122a46',
            font_size=12,
            font_family='Inter'
        )
    )


# ============================================================
# EXCEL HELPER
# ============================================================

def convert_df_to_excel(df):
    """Convert dataframe to excel bytes"""
    import io
    import pandas as pd
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()
