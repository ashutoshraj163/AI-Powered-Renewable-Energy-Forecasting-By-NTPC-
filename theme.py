def get_theme_colors(theme):
    if theme == 'dark':
        return {
            'bg_color': 'rgb(17,17,17)',
            'text_color': 'white',
            'plot_bg': 'rgb(17,17,17)',
            'paper_bg': 'rgb(17,17,17)',
            'grid_color': 'rgba(255,255,255,0.1)',
            'solar_color': 'rgba(255,127,14,0.8)',
            'wind_color': 'rgba(44,160,44,0.8)',
            'metric_text': 'white',
            'chart_text': 'white',
            'subplot_title': 'white',
            'axis_text': 'rgba(255,255,255,0.8)',
            'legend_text': 'rgba(255,255,255,0.9)'
        }
    else:  # light mode
        return {
            'bg_color': '#f8f9fa',  # Light gray background
            'text_color': '#2c3e50',  # Dark blue-gray text
            'plot_bg': '#ffffff',  # White plot background
            'paper_bg': '#ffffff',  # White paper background
            'grid_color': 'rgba(0,0,0,0.1)',  # Subtle grid
            'solar_color': 'rgba(255,127,14,1)',  # More vibrant solar
            'wind_color': 'rgba(44,160,44,1)',  # More vibrant wind
            'metric_text': '#2c3e50',  # Dark blue-gray for metrics
            'chart_text': '#2c3e50',  # Dark blue-gray for chart text
            'subplot_title': '#2c3e50',  # Dark blue-gray for subplot titles
            'axis_text': 'rgba(0,0,0,0.8)',  # Dark axis text
            'legend_text': 'rgba(0,0,0,0.9)'  # Dark legend text
        }

def get_streamlit_theme_css(theme_colors):
    return f"""
        .stApp {{
            background-color: {theme_colors['bg_color']};
            color: {theme_colors['text_color']};
        }}
        .stMarkdown, .stText {{
            color: {theme_colors['text_color']} !important;
        }}
        .stMetric {{
            color: {theme_colors['metric_text']} !important;
        }}
        .stSidebar {{
            background-color: {theme_colors['bg_color']};
        }}
        div[data-testid="stToolbar"] {{
            background-color: {theme_colors['bg_color']};
        }}
        .stDownloadButton {{
            background-color: transparent;
            color: {theme_colors['text_color']};
            border-color: {theme_colors['text_color']};
        }}
        .stDownloadButton:hover {{
            border-color: primary;
            color: primary;
        }}
        .stButton > button {{
            color: {theme_colors['text_color']};
            background-color: transparent;
            border-color: {theme_colors['text_color']};
        }}
        .stButton > button:hover {{
            border-color: primary;
            color: primary;
        }}
        .stDataFrame {{
            color: {theme_colors['text_color']};
        }}
        .stSelectbox {{
            color: {theme_colors['text_color']};
        }}
        .stNumberInput {{
            color: {theme_colors['text_color']};
        }}
    """