import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import folium
from streamlit_folium import st_folium
from folium.plugins import HeatMap
import os
import base64

@st.cache_data
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Saúde Bucal - Presidente Prudente",
    page_icon="🦷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- DATA LOADING & CLEANING WITH CACHE ---
@st.cache_data
def load_data(file_mtime):
    csv_filename = "dados_filtrados_completos.xlsx - Sheet1.csv"
    try:
        # Load with UTF-8 encoding (verified by raw bytes inspection)
        df = pd.read_csv(csv_filename, encoding='utf-8')
        
        # Clean coordinate columns: convert string with commas to float decimals
        df['Latitude'] = df['Latitude'].astype(str).str.replace(',', '.').astype(float)
        df['Longitude'] = df['Longitude'].astype(str).str.replace(',', '.').astype(float)
        
        # Remove any missing coordinate rows to prevent map crashes
        df = df.dropna(subset=['Latitude', 'Longitude'])
        
        # Convert values of severity to integer to prevent parsing errors
        for col in ['A', 'B', 'C', 'D', 'E', 'F', 'total_exames', 'total_alunos', 'ANO']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
            
        return df
    except Exception as e:
        st.error(f"Erro crítico ao ler os dados reais do arquivo CSV: {e}")
        st.stop()

# Track file modification time for automatic cache invalidation
csv_filename = "dados_filtrados_completos.xlsx - Sheet1.csv"
if not os.path.exists(csv_filename):
    st.error(f"Erro: O arquivo de dados '{csv_filename}' não foi encontrado no diretório atual.")
    st.stop()

file_mtime = os.path.getmtime(csv_filename)
df = load_data(file_mtime)

# --- THEME STATE & DYNAMIC STYLE INJECTION ---
if 'dark_mode' not in st.session_state:
    # Check default browser preference if possible, default to False (Light Mode)
    st.session_state.dark_mode = False

# Sidebar theme toggle control
st.sidebar.markdown("### Tema")
dark_toggle = st.sidebar.toggle("Modo Escuro", value=st.session_state.dark_mode)
st.session_state.dark_mode = dark_toggle

# Dynamic CSS Injection using CSS variables based on session state theme
if st.session_state.dark_mode:
    theme_class = "dark-theme"
    plotly_template = "plotly_dark"
    map_tiles = "CartoDB dark_matter"
    accent_color = "#00D2FF"
    
    st.markdown("""
    <style>
    :root {
        --bg-color: #0E1117;
        --text-color: #FAFAFA;
        --card-bg: #1E293B;
        --primary-color: #00D2FF;
        --secondary-color: #38BDF8;
        --sidebar-bg: #1A1F2C;
        --card-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
        --border-color: #334155;
        
        /* Badges & Accents for health colors and grades */
        --icon-bg: rgba(0, 210, 255, 0.15);
        --badge-bg-a: rgba(16, 185, 129, 0.15);
        --badge-text-a: #34D399;
        --badge-bg-b: rgba(6, 182, 212, 0.15);
        --badge-text-b: #22D3EE;
        --badge-bg-c: rgba(245, 158, 11, 0.15);
        --badge-text-c: #FBBF24;
        --badge-bg-d: rgba(249, 115, 22, 0.15);
        --badge-text-d: #FB923C;
        --badge-bg-e: rgba(239, 68, 68, 0.15);
        --badge-text-e: #F87171;
        --badge-bg-f: rgba(153, 27, 27, 0.18);
        --badge-text-f: #FCA5A5;
    }
    </style>
    """, unsafe_allow_html=True)
else:
    theme_class = "light-theme"
    plotly_template = "plotly_white"
    map_tiles = "CartoDB positron"
    accent_color = "#0083B0"
    
    st.markdown("""
    <style>
    :root {
        --bg-color: #F4F7F6;
        --text-color: #1D2D44;
        --card-bg: #FFFFFF;
        --primary-color: #0083B0;
        --secondary-color: #00B4DB;
        --sidebar-bg: #FFFFFF;
        --card-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        --border-color: #E2E8F0;
        
        /* Badges & Accents for health colors and grades */
        --icon-bg: rgba(0, 131, 176, 0.08);
        --badge-bg-a: #E6F8F0;
        --badge-text-a: #10B981;
        --badge-bg-b: #E0F7FA;
        --badge-text-b: #06B6D4;
        --badge-bg-c: #FEF3C7;
        --badge-text-c: #D97706;
        --badge-bg-d: #FFEDD5;
        --badge-text-d: #EA580C;
        --badge-bg-e: #FEE2E2;
        --badge-text-e: #DC2626;
        --badge-bg-f: #FFEBEE;
        --badge-text-f: #991B1B;
    }
    </style>
    """, unsafe_allow_html=True)

# General layout overrides via CSS
st.markdown("""
<style>
/* Hide Streamlit Header and Footer, but keep the sidebar collapse/expand button functional */
[data-testid="stHeader"], header {
    background-color: transparent !important;
    background: transparent !important;
    border-bottom: none !important;
    pointer-events: none;
    z-index: 999999;
}
[data-testid="stHeader"] button,
[data-testid="stHeader"] [data-testid="stSidebarCollapseButton"],
[data-testid="stHeader"] [data-testid="collapsedControl"],
[data-testid="stHeader"] [data-testid="collapsedSidebar"] {
    pointer-events: auto !important;
}
[data-testid="stHeader"] [data-testid="stDecoration"],
[data-testid="stHeader"] #MainMenu,
[data-testid="stHeader"] [data-testid="stConnectionStatus"],
[data-testid="stHeader"] [data-testid="stStatusWidget"],
[data-testid="stHeaderActionElements"],
[data-testid="stAppDeployButton"],
.stAppDeployButton,
#GithubIcon,
.github-icon,
div[class*="viewerBadge"],
[class*="viewerBadge"] {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
}
#MainMenu {
    visibility: hidden !important;
}
footer {
    visibility: hidden !important;
    display: none !important;
}

/* Destacar o botão de seta dupla (abrir/fechar barra de filtros) em ambos os estados (aberto/fechado) */
button[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapseButton"] button,
button[data-testid="collapsedControl"],
[data-testid="collapsedControl"] button,
[data-testid="collapsedControl"],
[data-testid="collapsedSidebar"] button {
    background-color: var(--primary-color) !important;
    color: #FFFFFF !important;
    border: 1px solid var(--primary-color) !important;
    border-radius: 50% !important;
    box-shadow: var(--card-shadow) !important;
    transition: transform 0.2s ease, background-color 0.2s ease, border-color 0.2s ease !important;
    width: 38px !important;
    height: 38px !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    cursor: pointer !important;
}

/* Efeito de Hover/Feedback visual */
button[data-testid="stSidebarCollapseButton"]:hover,
[data-testid="stSidebarCollapseButton"] button:hover,
button[data-testid="collapsedControl"]:hover,
[data-testid="collapsedControl"] button:hover,
[data-testid="collapsedControl"]:hover,
[data-testid="collapsedSidebar"] button:hover {
    transform: scale(1.08) !important;
    background-color: var(--secondary-color) !important;
    border-color: var(--secondary-color) !important;
}

/* Forçar a cor branca do ícone SVG */
button[data-testid="stSidebarCollapseButton"] svg,
[data-testid="stSidebarCollapseButton"] svg,
button[data-testid="collapsedControl"] svg,
[data-testid="collapsedControl"] svg,
[data-testid="collapsedSidebar"] svg {
    fill: #FFFFFF !important;
    color: #FFFFFF !important;
}

.stApp {
    background-color: var(--bg-color);
    color: var(--text-color);
}
[data-testid="stSidebar"] {
    background-color: var(--sidebar-bg) !important;
    border-right: 1px solid var(--border-color);
}
/* Force all default text, paragraphs, list items, headings and labels to follow the theme variables */
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6, 
.stApp p, .stApp li, .stApp label, .stApp td, .stApp th {
    color: var(--text-color) !important;
}

/* BaseWeb components (selectbox, multiselect containers) */
div[data-baseweb="select"] > div {
    background-color: var(--card-bg) !important;
    border-color: var(--border-color) !important;
}
div[data-baseweb="select"] span {
    color: var(--text-color) !important;
}
div[data-baseweb="select"] div[role="button"] {
    color: var(--text-color) !important;
}
div[data-baseweb="popover"], div[role="listbox"] {
    background-color: var(--card-bg) !important;
    border: 1px solid var(--border-color) !important;
}
div[role="option"] {
    background-color: transparent !important;
    color: var(--text-color) !important;
}
div[role="option"]:hover, div[role="option"][aria-selected="true"] {
    background-color: var(--primary-color) !important;
    color: #FFFFFF !important;
}
div[role="option"] span {
    color: inherit !important;
}

/* Selected tags inside multiselect */
div[data-baseweb="tag"] {
    background-color: var(--primary-color) !important;
    color: #FFFFFF !important;
}
div[data-baseweb="tag"] span {
    color: #FFFFFF !important;
}
div[data-baseweb="tag"] role[button] {
    color: #FFFFFF !important;
}

/* Style Streamlit Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 10px;
    background-color: transparent;
}
.stTabs [data-baseweb="tab"] {
    font-weight: 600;
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 6px 6px 0 0;
    padding: 10px 20px;
    transition: all 0.2s ease;
}
.stTabs [data-baseweb="tab"] p {
    color: var(--text-color) !important;
    font-weight: 600 !important;
}
.stTabs [data-baseweb="tab"]:hover {
    border-color: var(--primary-color);
}
.stTabs [aria-selected="true"] {
    background-color: var(--primary-color) !important;
    border-color: var(--primary-color) !important;
}
.stTabs [aria-selected="true"] p {
    color: #FFFFFF !important;
}

/* Style Streamlit Metrics Cards */
div[data-testid="metric-container"] {
    background-color: var(--card-bg) !important;
    border-left: 5px solid var(--primary-color) !important;
    padding: 15px 20px !important;
    border-radius: 8px !important;
    box-shadow: var(--card-shadow) !important;
    border: 1px solid var(--border-color);
    transition: transform 0.2s ease-in-out;
}
div[data-testid="metric-container"]:hover {
    transform: translateY(-2px);
}
div[data-testid="stMetricValue"], div[data-testid="stMetricValue"] * {
    color: var(--primary-color) !important;
    font-weight: 750 !important;
    font-size: 28px !important;
}
div[data-testid="stMetricLabel"], div[data-testid="stMetricLabel"] * {
    color: var(--text-color) !important;
    opacity: 0.8 !important;
    font-weight: 600 !important;
    font-size: 13px !important;
}
/* General Containers styling */
.custom-card {
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    padding: 20px;
    border-radius: 8px;
    box-shadow: var(--card-shadow);
    margin-bottom: 20px;
}

/* Custom card and layouts for Sobre o Projeto */
.hero-section {
    background: linear-gradient(135deg, rgba(0, 131, 176, 0.08) 0%, rgba(0, 180, 219, 0.03) 100%);
    border-left: 6px solid var(--primary-color);
    border-radius: 12px;
    padding: 30px;
    margin-bottom: 30px;
    box-shadow: var(--card-shadow);
    border-top: 1px solid var(--border-color);
    border-right: 1px solid var(--border-color);
    border-bottom: 1px solid var(--border-color);
}
.hero-title {
    color: var(--primary-color) !important;
    font-size: 26px !important;
    font-weight: 850 !important;
    margin-top: 0 !important;
    margin-bottom: 12px !important;
}
.hero-lead {
    font-size: 17.5px !important;
    font-weight: 700 !important;
    line-height: 1.6 !important;
    color: var(--primary-color) !important;
    margin-bottom: 16px !important;
    opacity: 0.9;
}
.hero-body {
    font-size: 15px !important;
    line-height: 1.7 !important;
    margin-bottom: 0 !important;
    opacity: 0.95;
}

.section-title {
    margin-top: 35px !important;
    margin-bottom: 8px !important;
    font-size: 22px !important;
    font-weight: 800 !important;
    color: var(--primary-color) !important;
}
.section-subtitle {
    font-size: 15px !important;
    margin-bottom: 24px !important;
    line-height: 1.6 !important;
    opacity: 0.9;
}

/* Severity Grade Grid */
.grade-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 20px;
    margin-top: 15px;
    margin-bottom: 30px;
}
.grade-card-item {
    display: flex;
    align-items: flex-start;
    gap: 16px;
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    border-left: 5px solid var(--border-color-grade);
    padding: 20px;
    border-radius: 12px;
    box-shadow: var(--card-shadow);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.grade-card-item:hover {
    transform: translateY(-4px);
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
    border-color: var(--border-color-grade);
}
.grade-circle-badge {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 44px;
    height: 44px;
    border-radius: 50%;
    background-color: var(--badge-bg);
    color: var(--badge-text);
    font-size: 20px;
    font-weight: 800;
    flex-shrink: 0;
}
.grade-label {
    font-weight: 700 !important;
    font-size: 16px !important;
    color: var(--badge-text) !important;
    margin-right: 4px;
}
.grade-text {
    font-size: 14.5px !important;
    line-height: 1.5 !important;
    color: var(--text-color);
}

/* Practice Grid */
.practice-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 20px;
    margin-top: 15px;
    margin-bottom: 30px;
}
.practice-card {
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    padding: 24px;
    border-radius: 12px;
    box-shadow: var(--card-shadow);
    display: flex;
    align-items: flex-start;
    gap: 16px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.practice-card:hover {
    transform: translateY(-4px);
    border-color: var(--primary-color);
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
}
.practice-icon {
    font-size: 24px;
    line-height: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 44px;
    height: 44px;
    border-radius: 50%;
    background-color: var(--icon-bg);
    color: var(--primary-color);
    flex-shrink: 0;
}
.practice-label {
    font-weight: 700 !important;
    font-size: 16px !important;
    color: var(--primary-color) !important;
    margin-right: 4px;
}
.practice-text {
    font-size: 14.5px !important;
    line-height: 1.5 !important;
    color: var(--text-color);
}

/* Partner Footer Banner */
.partner-banner {
    background: linear-gradient(135deg, rgba(0, 131, 176, 0.05) 0%, rgba(0, 180, 219, 0.02) 100%);
    border: 1px dashed var(--primary-color);
    border-radius: 12px;
    padding: 24px;
    margin-top: 40px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 20px;
    box-shadow: var(--card-shadow);
}
.partner-icon {
    font-size: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 52px;
    height: 52px;
    border-radius: 50%;
    background-color: var(--icon-bg);
    color: var(--primary-color);
    flex-shrink: 0;
}
.partner-text-container {
    font-size: 14.5px !important;
    line-height: 1.6 !important;
    color: var(--text-color);
}
.partner-label {
    font-weight: 700 !important;
    color: var(--primary-color) !important;
}
.main-header-icon {
    height: 150px;
    margin-right: 18px;
    vertical-align: middle;
}
span.main-header-icon {
    font-size: 45px;
}

/* Responsividade para cabeçalho e rodapé em telas menores */
@media (max-width: 768px) {
    .main-header-container {
        flex-direction: column;
        align-items: flex-start !important;
        gap: 10px;
    }
    .main-header-title {
        font-size: 26px !important;
    }
    .main-header-icon {
        height: 90px !important;
        margin-right: 0 !important;
    }
    span.main-header-icon {
        font-size: 36px !important;
    }
}

@media (max-width: 600px) {
    .partner-banner {
        flex-direction: column !important;
        text-align: center;
        align-items: center !important;
        gap: 15px !important;
    }
    .partner-icon {
        width: 44px !important;
        height: 44px !important;
        font-size: 24px !important;
    }
}


</style>

""", unsafe_allow_html=True)


# --- SIDEBAR LOGO & FILTERS ---
# Select logo based on theme
if st.session_state.dark_mode:
    logo_path = "logo_branca.png"
else:
    logo_path = "logo_preta.png"

if os.path.exists(logo_path):
    st.sidebar.image(logo_path, use_container_width=True)
    st.sidebar.markdown("<br>", unsafe_allow_html=True)

st.sidebar.markdown("## Filtros")

# 1. Year Filter
years = sorted(df['ANO'].unique())
select_all_years = st.sidebar.checkbox("Selecionar todos os anos", value=False)

if select_all_years:
    selected_years = years
else:
    selected_years = st.sidebar.multiselect(
        "Selecionar anos",
        options=years,
        default=[years[-1]]
    )
    if not selected_years:
        st.sidebar.warning("⚠️ Selecione pelo menos um ano.")

# 2. School Filter
st.sidebar.markdown("---")
all_schools = sorted(df['nome_escola'].unique())
select_all_schools = st.sidebar.checkbox("Selecionar todas as escolas", value=True)

if select_all_schools:
    selected_schools = all_schools
else:
    selected_schools = st.sidebar.multiselect(
        "Selecionar escolas",
        options=all_schools,
        default=all_schools[:5]
    )
    if not selected_schools:
        st.sidebar.warning("⚠️ Selecione pelo menos uma escola.")

# 3. Severity Filter
st.sidebar.markdown("---")
severity_levels = ['A', 'B', 'C', 'D', 'E', 'F']
severity_labels = {
    'A': 'Grau A: Saudável',
    'B': 'Grau B: Placa / Gengiva',
    'C': 'Grau C: Cárie sem dor',
    'D': 'Grau D: Cárie profunda',
    'E': 'Grau E: Urgência (Dor)',
    'F': 'Grau F: Emergência'
}
selected_severities = st.sidebar.multiselect(
    "Níveis de gravidade",
    options=severity_levels,
    default=severity_levels,
    format_func=lambda x: severity_labels[x]
)
if not selected_severities:
    st.sidebar.warning("⚠️ Selecione pelo menos um nível de gravidade.")

# 4. KDE Map Radius Filter
st.sidebar.markdown("---")
st.sidebar.markdown("**Visualização**")
radius_km = st.sidebar.slider(
    "Raio do mapa de calor (km)",
    min_value=0.5,
    max_value=5.0,
    value=1.5,
    step=0.1,
    format="%.1f km"
)

# Apply filters
df_filtered = df[(df['ANO'].isin(selected_years)) & (df['nome_escola'].isin(selected_schools))].copy()
df_temporal = df[df['nome_escola'].isin(selected_schools)].copy()

# Add calculations based on selected severities
if selected_severities:
    df_filtered['casos_selecionados'] = df_filtered[selected_severities].sum(axis=1)
    df_temporal['casos_selecionados'] = df_temporal[selected_severities].sum(axis=1)
else:
    df_filtered['casos_selecionados'] = 0
    df_temporal['casos_selecionados'] = 0


# --- MAIN HEADER ---
if st.session_state.dark_mode:
    logo_header_path = "brasil_sorridente_branco.png"
else:
    logo_header_path = "brasil_sorridente_preto.png"

logo_header_base64 = get_base64_image(logo_header_path)
logo_header_html = f'<img src="data:image/png;base64,{logo_header_base64}" class="main-header-icon">' if logo_header_base64 else '<span class="main-header-icon">🦷</span>'

st.markdown(f"""
<div class="main-header-container" style="display: flex; align-items: center; margin-bottom: 25px; border-bottom: 2px solid var(--border-color); padding-bottom: 15px;">
    {logo_header_html}
    <div>
        <h1 class="main-header-title" style="margin: 0; font-size: 34px; font-weight: 800; color: var(--primary-color);">
            Saúde Bucal Presidente Prudente
        </h1>
        <p class="main-header-subtitle" style="margin: 3px 0 0 0; font-size: 15px; opacity: 0.85;">
            Painel Epidemiológico Interativo de Monitoramento Escolar
        </p>
    </div>
</div>
""", unsafe_allow_html=True)




# --- NAVIGATION TABS ---
tab_geral, tab_odo, tab_sobre = st.tabs(["📊 Visão Geral", "🩺 Análise Odontológica", "ℹ️ Sobre o Projeto"])

# ==================== TAB 1: VISÃO GERAL ====================
with tab_geral:
    if not selected_severities or (not select_all_schools and not selected_schools):
        st.info("💡 Por favor, configure os filtros na barra lateral para carregar a visualização dos dados.")
    elif df_filtered.empty:
        st.warning("⚠️ Não foram encontrados registros para os filtros selecionados no ano de referência.")
    else:
        # --- METRIC CARDS ---
        total_exames_sum = int(df_filtered['total_exames'].sum())
        total_casos_sum = int(df_filtered['casos_selecionados'].sum())
        incidence_rate = (total_casos_sum / total_exames_sum * 100) if total_exames_sum > 0 else 0.0
        num_schools_monitored = int(df_filtered['nome_escola'].nunique())

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(
                label="Total de Exames Realizados",
                value=f"{total_exames_sum:,}".replace(",", "."),
                help="Quantidade acumulada de exames bucais realizados no grupo de escolas e no ano selecionado."
            )
        with col2:
            st.metric(
                label="Casos Identificados",
                value=f"{total_casos_sum:,}".replace(",", "."),
                help="Total de ocorrências somadas para os níveis de gravidade selecionados."
            )
        with col3:
            st.metric(
                label="Prevalência Média",
                value=f"{incidence_rate:.1f}%",
                help="Proporção de casos identificados em relação ao total de exames clínicos realizados."
            )
        with col4:
            st.metric(
                label="Escolas Monitoradas",
                value=num_schools_monitored,
                help="Quantidade de instituições que reportaram dados no ano selecionado."
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # --- MAP & GROUPING CHARTS (ROW 1) ---
        col_mapa, col_barra = st.columns([1.3, 1])

        with col_mapa:
            st.subheader("📍 Mapa de Distribuição Espacial")
            st.markdown(
                "Visualização geográfica da densidade de casos bucais por escola. "
                "Áreas avermelhadas representam maior concentração de casos nas gravidades selecionadas."
            )
            
            # Prepare map data
            df_map = df_filtered.groupby(['nome_escola', 'Latitude', 'Longitude'], as_index=False)[['casos_selecionados', 'total_exames']].sum()
            
            # Determine map center dynamically
            if not df_map.empty:
                center_lat = df_map['Latitude'].mean()
                center_lon = df_map['Longitude'].mean()
            else:
                center_lat = -22.1225
                center_lon = -51.3890

            # Instantiate Folium map
            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=13,
                tiles=map_tiles,
                attr="Mapbox tiles" if "positron" in map_tiles or "dark_matter" in map_tiles else None
            )

            # Generate HeatMap data points
            heat_data = [
                [row['Latitude'], row['Longitude'], row['casos_selecionados']] 
                for _, row in df_map.iterrows() 
                if row['casos_selecionados'] > 0
            ]
            
            if heat_data:
                HeatMap(
                    heat_data, 
                    radius=int(radius_km * 15), 
                    blur=int(radius_km * 10), 
                    min_opacity=0.35, 
                    gradient={0.4: '#3388ff', 0.65: '#f1c40f', 0.9: '#e74c3c'}
                ).add_to(m)
            
            # School circle markers toggle
            show_pins = st.checkbox("Mostrar marcadores das escolas no mapa", value=True)
            if show_pins:
                for _, row in df_map.iterrows():
                    years_label = (
                        "Todos os Anos" if select_all_years 
                        else f"{min(selected_years)}-{max(selected_years)}" if len(selected_years) > 3 
                        else ", ".join(map(str, sorted(selected_years)))
                    )
                    popup_content = f"""
                    <div style="font-family: Arial, sans-serif; font-size: 13px; width: 230px;">
                        <h4 style="margin: 0 0 6px 0; color: {accent_color}; font-weight: 700;">{row['nome_escola']}</h4>
                        <hr style="margin: 4px 0; border: 0; border-top: 1px solid #ccc;">
                        <b>Anos:</b> {years_label}<br>
                        <b>Total de Exames:</b> {int(row['total_exames'])}<br>
                        <b>Casos Detectados (Filtrados):</b> {int(row['casos_selecionados'])}<br>
                    </div>
                    """
                    folium.CircleMarker(
                        location=[row['Latitude'], row['Longitude']],
                        radius=3.5,
                        color=accent_color,
                        weight=1.5,
                        fill=True,
                        fill_color=accent_color,
                        fill_opacity=0.8,
                        popup=folium.Popup(popup_content, max_width=300)
                    ).add_to(m)

            # Render map
            st_folium(m, width='stretch', height=450, key="saude_bucal_map")

        with col_barra:
            st.subheader("📊 Distribuição e Rankings")
            st.markdown("Escolha a forma de agrupamento abaixo para explorar o detalhamento dos casos.")
            
            group_selection = st.radio(
                "Agrupar dados de ocorrências por:",
                options=["Classificação de Gravidade", "Maiores Focos (Top 15 Escolas)"],
                horizontal=True
            )
            
            if "Gravidade" in group_selection:
                # Sum columns of selected severities
                severity_totals = df_filtered[selected_severities].sum().reset_index()
                severity_totals.columns = ['Gravidade', 'Casos']
                
                fig_bar = px.bar(
                    severity_totals,
                    x='Gravidade',
                    y='Casos',
                    labels={'Gravidade': 'Nível de Gravidade', 'Casos': 'Quantidade de Casos'},
                    template=plotly_template,
                    color='Gravidade',
                    color_discrete_sequence=px.colors.sequential.Teal_r if not st.session_state.dark_mode else px.colors.sequential.ice_r
                )
                fig_bar.update_layout(
                    showlegend=False,
                    height=370,
                    margin=dict(l=40, r=40, t=20, b=40)
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                # Top 15 schools with selected cases
                top_schools = df_filtered.groupby('nome_escola', as_index=False)['casos_selecionados'].sum()
                top_schools = top_schools.sort_values('casos_selecionados', ascending=False).head(15)
                
                fig_bar = px.bar(
                    top_schools,
                    x='casos_selecionados',
                    y='nome_escola',
                    orientation='h',
                    labels={'casos_selecionados': 'Casos de Interesse', 'nome_escola': 'Escola'},
                    template=plotly_template
                )
                fig_bar.update_traces(marker_color=accent_color)
                fig_bar.update_layout(
                    height=370,
                    yaxis={'categoryorder': 'total ascending'},
                    margin=dict(l=150, r=40, t=20, b=40)
                )
                st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("<br><hr style='border-top: 1px solid var(--border-color);'><br>", unsafe_allow_html=True)

        # --- LINE CHART: TEMPORAL EVOLUTION (ROW 2) ---
        st.subheader("📈 Evolução Temporal Histórica")
        st.markdown(
            "O gráfico a seguir exibe o comportamento dos casos identificados ao longo dos anos para o grupo "
            "de escolas e gravidades especificadas na barra lateral. A linha vertical tracejada destaca o ano ativo selecionado."
        )

        df_line = df_temporal.groupby('ANO', as_index=False)[['casos_selecionados', 'total_exames']].sum()
        df_line = df_line.sort_values('ANO')

        if not df_line.empty:
            fig_line = px.line(
                df_line,
                x='ANO',
                y='casos_selecionados',
                labels={'ANO': 'Ano da Avaliação', 'casos_selecionados': 'Quantidade de Ocorrências'},
                template=plotly_template
            )
            # Add line styles
            fig_line.update_traces(
                line=dict(color=accent_color, width=3.5),
                marker=dict(size=7, color=accent_color, symbol='circle')
            )
            
            # Draw vertical lines for each selected year
            for sy in selected_years:
                fig_line.add_vline(
                    x=sy,
                    line_dash="dash",
                    line_color="#EF4444",
                    opacity=0.6,
                    annotation_text=f"{sy}" if len(selected_years) <= 3 else "",
                    annotation_position="top left",
                    annotation_font=dict(color="#EF4444", size=10, family="sans-serif")
                )
            
            fig_line.update_layout(
                hovermode="x unified",
                height=350,
                margin=dict(l=50, r=50, t=10, b=40),
                xaxis=dict(dtick=1) # force displaying integers for years
            )
            
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("Não há dados históricos disponíveis para gerar a curva temporal das escolas selecionadas.")

        # --- DATA FOOTNOTE ---
        st.markdown(
            "<p style='font-size: 11.5px; opacity: 0.7; text-align: center; margin-top: 20px;'>"
            "Nota: Os dados expostos têm caráter epidemiológico com base no Levantamento de Saúde Bucal Escolar "
            "coordenado no município de Presidente Prudente - SP. O indicador de gravidade varia de 'A' (hígido/menor complexidade) "
            "a 'F' (urgência odontológica crítica)."
            "</p>",
            unsafe_allow_html=True
        )

# ==================== TAB 2: ANÁLISE ODONTOLÓGICA ====================
with tab_odo:
    if not selected_severities or (not select_all_schools and not selected_schools) or (not select_all_years and not selected_years):
        st.info("💡 Por favor, configure os filtros na barra lateral para carregar a análise odontológica.")
    elif df_filtered.empty:
        st.warning("⚠️ Não foram encontrados registros para os filtros selecionados.")
    else:
        st.markdown("""
        <div class="custom-card">
            <h2 style="color: var(--primary-color); margin-top: 0;">Análise Odontológica Avançada</h2>
            <p style="font-size: 15px; line-height: 1.6; margin-bottom: 0;">
                Esta seção apresenta indicadores epidemiológicos detalhados essenciais para profissionais de odontologia e gestores públicos. 
                Os dados a seguir auxiliam no mapeamento do perfil de severidade clínica, no acompanhamento da urgência por unidade escolar 
                e na correlação entre a cobertura de triagem e a prevalência de patologias.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # --- ROW 1: 2 CHARTS ---
        col_od1, col_od2 = st.columns(2)
        
        with col_od1:
            st.subheader("🍩 Perfil Epidemiológico Geral")
            st.markdown("Proporção percentual de cada nível de gravidade bucal (A a F) sobre o total de exames clínicos realizados.")
            
            # Chart 1: Donut Chart for Perfil Epidemiológico
            sev_cols = ['A', 'B', 'C', 'D', 'E', 'F']
            sev_totals = df_filtered[sev_cols].sum().reset_index()
            sev_totals.columns = ['Gravidade', 'Quantidade']
            
            labels_map = {
                'A': 'A - Higidez / Saudável',
                'B': 'B - Preventivo / Placa',
                'C': 'C - Restaurador Eletivo',
                'D': 'D - Tratamento Endodôntico',
                'E': 'E - Urgência / Abscesso',
                'F': 'F - Emergência Sistêmica'
            }
            sev_totals['Descrição'] = sev_totals['Gravidade'].map(labels_map)
            
            fig_pie = px.pie(
                sev_totals,
                values='Quantidade',
                names='Descrição',
                hole=0.45,
                template=plotly_template,
                color_discrete_sequence=px.colors.sequential.Teal_r if not st.session_state.dark_mode else px.colors.sequential.ice_r
            )
            fig_pie.update_layout(
                height=380,
                margin=dict(l=20, r=20, t=10, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col_od2:
            st.subheader("📈 Top 15 Escolas por Grau de Urgência Médio (GUM)")
            st.markdown(
                "O GUM é a média ponderada de gravidade (pesos de 0 a 5 para as categorias A a F). "
                "Valores mais altos indicam que, em média, a população examinada na escola apresenta maior gravidade clínica."
            )
            
            # Chart 2: GUM (Weighted Urgency)
            df_gum = df_filtered.copy()
            df_gum['total_casos_local'] = df_gum[sev_cols].sum(axis=1)
            df_gum = df_gum[df_gum['total_casos_local'] > 0]
            
            if not df_gum.empty:
                # Weighted score per row
                df_gum['weighted_score'] = (
                    df_gum['A'] * 0 + 
                    df_gum['B'] * 1 + 
                    df_gum['C'] * 2 + 
                    df_gum['D'] * 3 + 
                    df_gum['E'] * 4 + 
                    df_gum['F'] * 5
                )
                # Aggregate across multiple selected rows
                df_gum_grouped = df_gum.groupby('nome_escola', as_index=False).agg(
                    total_weighted_sum=('weighted_score', 'sum'),
                    total_cases_sum=('total_casos_local', 'sum')
                )
                df_gum_grouped['GUM_ponderado'] = df_gum_grouped['total_weighted_sum'] / df_gum_grouped['total_cases_sum']
                df_gum_grouped = df_gum_grouped.sort_values('GUM_ponderado', ascending=False).head(15)
                
                fig_gum = px.bar(
                    df_gum_grouped,
                    x='GUM_ponderado',
                    y='nome_escola',
                    orientation='h',
                    labels={'GUM_ponderado': 'Grau de Urgência Médio (0 a 5)', 'nome_escola': 'Escola'},
                    template=plotly_template
                )
                fig_gum.update_traces(marker_color=accent_color)
                fig_gum.update_layout(
                    height=380,
                    yaxis={'categoryorder': 'total ascending'},
                    margin=dict(l=150, r=40, t=10, b=40)
                )
                st.plotly_chart(fig_gum, use_container_width=True)
            else:
                st.info("Nenhum data com exames válidos para calcular o GUM.")

        st.markdown("<br><hr style='border-top: 1px solid var(--border-color);'><br>", unsafe_allow_html=True)
        
        # --- ROW 2: 2 CHARTS ---
        col_od3, col_od4 = st.columns(2)
        
        with col_od3:
            st.subheader("🚨 Top 15 Escolas por Taxa de Urgência Crítica")
            st.markdown("Porcentagem de exames classificados nas severidades mais críticas (**E** ou **F**) sobre o total de exames.")
            
            # Chart 3: Critical Urgency Rate (E + F / total_exames)
            df_urgent = df_filtered.copy()
            df_urgent['casos_urgentes'] = df_urgent['E'] + df_urgent['F']
            df_urg_grouped = df_urgent.groupby('nome_escola', as_index=False).agg(
                total_urgentes=('casos_urgentes', 'sum'),
                total_exames_local=('total_exames', 'sum')
            )
            df_urg_grouped = df_urg_grouped[df_urg_grouped['total_exames_local'] > 0]
            df_urg_grouped['Taxa_Urgencia_Pct'] = (df_urg_grouped['total_urgentes'] / df_urg_grouped['total_exames_local']) * 100
            df_urg_grouped = df_urg_grouped.sort_values('Taxa_Urgencia_Pct', ascending=False).head(15)
            
            if not df_urg_grouped.empty:
                fig_urg = px.bar(
                    df_urg_grouped,
                    x='Taxa_Urgencia_Pct',
                    y='nome_escola',
                    orientation='h',
                    labels={'Taxa_Urgencia_Pct': 'Taxa de Casos Críticos (%)', 'nome_escola': 'Escola'},
                    template=plotly_template
                )
                fig_urg.update_traces(marker_color='#EF4444') # Red color for urgency alerts
                fig_urg.update_layout(
                    height=380,
                    yaxis={'categoryorder': 'total ascending'},
                    margin=dict(l=150, r=40, t=10, b=40)
                )
                st.plotly_chart(fig_urg, use_container_width=True)
            else:
                st.info("Nenhuma urgência crítica detectada para as escolas filtradas.")
                
        with col_od4:
            st.subheader("🎯 Cobertura de Exames por Escola")
            st.markdown("Percentual de alunos examinados em relação ao total de alunos matriculados na instituição.")
            
            col_chart, col_control = st.columns([3.5, 1.2])
            
            with col_control:
                st.markdown("<br><br>", unsafe_allow_html=True)
                order_choice = st.radio(
                    "Filtrar por:",
                    options=["Maiores Coberturas", "Menores Coberturas"],
                    key="cov_order_radio"
                )
                
            with col_chart:
                df_cov = df_filtered.copy()
                df_cov = df_cov[(df_cov['total_alunos'] > 0) & (df_cov['total_exames'] > 0)]
                
                if not df_cov.empty:
                    df_cov_grouped = df_cov.groupby('nome_escola', as_index=False).agg(
                        total_alunos_sum=('total_alunos', 'sum'),
                        total_exames_sum=('total_exames', 'sum')
                    )
                    df_cov_grouped['Cobertura_Pct'] = (df_cov_grouped['total_exames_sum'] / df_cov_grouped['total_alunos_sum']) * 100
                    df_cov_grouped['Cobertura_Pct'] = df_cov_grouped['Cobertura_Pct'].clip(upper=100.0)
                    
                    if order_choice == "Maiores Coberturas":
                        df_cov_grouped = df_cov_grouped.sort_values('Cobertura_Pct', ascending=False).head(15)
                        ascending_order = True
                    else:
                        df_cov_grouped = df_cov_grouped.sort_values('Cobertura_Pct', ascending=True).head(15)
                        ascending_order = False
                        
                    fig_cov = px.bar(
                        df_cov_grouped,
                        x='Cobertura_Pct',
                        y='nome_escola',
                        orientation='h',
                        labels={'Cobertura_Pct': 'Taxa de Cobertura (%)', 'nome_escola': 'Escola'},
                        template=plotly_template
                    )
                    fig_cov.update_traces(marker_color=accent_color)
                    fig_cov.update_layout(
                        height=380,
                        yaxis={'categoryorder': 'total ascending' if ascending_order else 'total descending'},
                        margin=dict(l=150, r=40, t=10, b=40)
                    )
                    st.plotly_chart(fig_cov, use_container_width=True)
                else:
                    st.info("Dados de cobertura de alunos insuficientes para gerar o gráfico.")

# ==================== TAB 3: SOBRE O PROJETO ====================
with tab_sobre:
    st.markdown("""
    <!-- Hero Section -->
    <div class="hero-section">
        <h2 class="hero-title">Para que serve este painel?</h2>
        <p class="hero-lead">A ideia por trás do Observatório é simples: fazer o cuidado com os dentes chegar primeiro a quem mais precisa.</p>
        <p class="hero-body">Isto aqui não é só um amontoado de gráficos. Nossa equipe vai até as creches e escolas, avalia a boca das crianças e traduz a realidade de cada bairro para o mapa. Com esses dados nas mãos, a prefeitura e os dentistas dos postinhos (UBS) conseguem bater o olho e saber exatamente quais escolas estão precisando de ajuda urgente, direcionando as equipes para o lugar certo.</p>
    </div>

    <!-- Severity evaluation section -->
    <h3 class="section-title">Como avaliamos as crianças?</h3>
    <p class="section-subtitle">Nós não contamos apenas quantas cáries uma escola tem. Nós separamos os casos pela urgência da dor e do risco, para organizar uma fila de atendimento justa:</p>
    
    <div class="grade-grid">
        <!-- Grade A -->
        <div class="grade-card-item" style="--border-color-grade: var(--badge-text-a); --badge-bg: var(--badge-bg-a); --badge-text: var(--badge-text-a);">
            <div class="grade-circle-badge">A</div>
            <div>
                <span class="grade-label">Grau A:</span>
                <span class="grade-text">Dentes super saudáveis. Sem necessidade de dentista agora.</span>
            </div>
        </div>
        <!-- Grade B -->
        <div class="grade-card-item" style="--border-color-grade: var(--badge-text-b); --badge-bg: var(--badge-bg-b); --badge-text: var(--badge-text-b);">
            <div class="grade-circle-badge">B</div>
            <div>
                <span class="grade-label">Grau B:</span>
                <span class="grade-text">Precisa melhorar a escovação. Tem um pouco de placa ou gengiva inflamada.</span>
            </div>
        </div>
        <!-- Grade C -->
        <div class="grade-card-item" style="--border-color-grade: var(--badge-text-c); --badge-bg: var(--badge-bg-c); --badge-text: var(--badge-text-c);">
            <div class="grade-circle-badge">C</div>
            <div>
                <span class="grade-label">Grau C:</span>
                <span class="grade-text">Tem cárie, mas não está doendo. Pode agendar o tratamento sem pressa.</span>
            </div>
        </div>
        <!-- Grade D -->
        <div class="grade-card-item" style="--border-color-grade: var(--badge-text-d); --badge-bg: var(--badge-bg-d); --badge-text: var(--badge-text-d);">
            <div class="grade-circle-badge">D</div>
            <div>
                <span class="grade-label">Grau D:</span>
                <span class="grade-text">Cárie grande. Precisa tratar logo antes que piore ou vire canal.</span>
            </div>
        </div>
        <!-- Grade E -->
        <div class="grade-card-item" style="--border-color-grade: var(--badge-text-e); --badge-bg: var(--badge-bg-e); --badge-text: var(--badge-text-e);">
            <div class="grade-circle-badge">E</div>
            <div>
                <span class="grade-label">Grau E:</span>
                <span class="grade-text">Urgência. A criança está com dor forte, infecção ou abscesso. Precisa de dentista hoje.</span>
            </div>
        </div>
        <!-- Grade F -->
        <div class="grade-card-item" style="--border-color-grade: var(--badge-text-f); --badge-bg: var(--badge-bg-f); --badge-text: var(--badge-text-f);">
            <div class="grade-circle-badge">F</div>
            <div>
                <span class="grade-label">Grau F:</span>
                <span class="grade-text">Emergência de hospital. A infecção na boca está causando febre ou risco à saúde geral do aluno.</span>
            </div>
        </div>
    </div>

    <!-- Practical actions section -->
    <h3 class="section-title">O que fazemos na prática</h3>
    
    <div class="practice-grid">
        <!-- Practical item 1 -->
        <div class="practice-card">
            <div class="practice-icon">📍</div>
            <div>
                <span class="practice-label">Mapa da urgência:</span>
                <span class="practice-text">Mostramos no mapa quais escolas têm as crianças precisando de tratamento imediato.</span>
            </div>
        </div>
        <!-- Practical item 2 -->
        <div class="practice-card">
            <div class="practice-icon">📅</div>
            <div>
                <span class="practice-label">Fila justa:</span>
                <span class="practice-text">Ajudamos os postos de saúde a organizar a agenda, chamando primeiro quem está com dor ou infecção.</span>
            </div>
        </div>
        <!-- Practical item 3 -->
        <div class="practice-card">
            <div class="practice-icon">📈</div>
            <div>
                <span class="practice-label">Medir para melhorar:</span>
                <span class="practice-text">Comparamos os anos para saber se entregar flúor e ensinar a escovar os dentes está realmente diminuindo as cáries nas escolas.</span>
            </div>
        </div>
        <!-- Practical item 4 -->
        <div class="practice-card">
            <div class="practice-icon">🔓</div>
            <div>
                <span class="practice-label">Informação aberta:</span>
                <span class="practice-text">Deixamos tudo isso público para que diretores e pais saibam como está a saúde dos alunos do seu bairro.</span>
            </div>
        </div>
    </div>

    <!-- Partner Banner -->
    <div class="partner-banner">
        <div class="partner-icon">🤝</div>
        <div class="partner-text-container">
            <span class="partner-label">Parceria Interinstitucional:</span> Projeto de extensão universitária desenvolvido em cooperação entre as Secretarias Municipais de Saúde e de Educação de Presidente Prudente (SP) e a UNESP-FCT. A iniciativa é orientada pelo Prof. Dr. Guilherme Aparecido Santos Aguilar e realizada pelo discente Renan Figueira.
        </div>
    </div>
    """, unsafe_allow_html=True)
