import streamlit as st
import feedparser
import re
import requests
import hashlib
import json
import urllib.parse
from datetime import datetime, timezone
import time
import base64

# SVG pur HD du logo Krea
KREA_SVG_ICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <defs>
    <linearGradient id="g1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#8B5CF6"/>
      <stop offset="100%" stop-color="#2563EB"/>
    </linearGradient>
    <linearGradient id="g2" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#06B6D4" stop-opacity="0.6"/>
      <stop offset="100%" stop-color="#3B82F6" stop-opacity="0.3"/>
    </linearGradient>
  </defs>
  <rect x="0" y="0" width="100" height="100" rx="22" fill="#0b0f19"/>
  <rect x="18" y="18" width="62" height="62" rx="14" fill="url(#g2)" transform="rotate(-6 49 49)"/>
  <rect x="12" y="12" width="62" height="62" rx="14" fill="url(#g1)"/>
  <text x="43" y="56" font-family="sans-serif" font-weight="900" font-size="44" fill="#FFFFFF" text-anchor="middle" transform="rotate(-10 43 56)">k</text>
  <path d="M 72 6 Q 72 14 80 14 Q 72 14 72 22 Q 72 14 64 14 Q 72 14 72 6 Z" fill="#F472B6"/>
</svg>"""

krea_b64_svg = base64.b64encode(KREA_SVG_ICON.encode('utf-8')).decode('utf-8')
svg_data_uri = f"data:image/svg+xml;base64,{krea_b64_svg}"

st.set_page_config(
    page_title="Krea — L'Actu Créative & IA",
    page_icon="🎨",
    layout="wide"
)

# Injection favicon (avec f-string pour insérer svg_data_uri)
st.markdown(f"""
<head>
    <link rel="icon" type="image/svg+xml" href="{svg_data_uri}">
    <link rel="shortcut icon" type="image/svg+xml" href="{svg_data_uri}">
    <link rel="apple-touch-icon" href="{svg_data_uri}">
</head>
<script>
(function() {{
    var svgUri = "{svg_data_uri}";
    function setFavicon() {{
        var doc = window.parent ? window.parent.document : document;
        if (!doc) return;
        var links = doc.querySelectorAll("link[rel*='icon']");
        links.forEach(function(l) {{
            l.href = svgUri;
            l.type = "image/svg+xml";
        }});
        if (links.length === 0) {{
            var link = doc.createElement('link');
            link.rel = 'shortcut icon';
            link.type = 'image/svg+xml';
            link.href = svgUri;
            doc.head.appendChild(link);
        }}
    }}
    setFavicon();
    setTimeout(setFavicon, 300);
    setTimeout(setFavicon, 1000);
}})();
</script>
""", unsafe_allow_html=True)

# Style CSS (sans le 'f' devant les """ pour éviter les erreurs d'accolades)
st.markdown("""
<style>
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    div[data-testid="stDecoration"] {display: none;}
    .main .block-container, div[data-testid="stMainBlockContainer"] {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
    }
    .stApp {
        background-color: #0b0f19;
        background-image: 
            radial-gradient(at 15% 10%, rgba(139, 92, 246, 0.22) 0px, transparent 40%),
            radial-gradient(at 85% 5%, rgba(37, 99, 235, 0.20) 0px, transparent 45%),
            radial-gradient(at 50% 18%, rgba(244, 114, 182, 0.15) 0px, transparent 40%),
            radial-gradient(at 70% 25%, rgba(6, 182, 212, 0.12) 0px, transparent 35%);
        background-repeat: no-repeat;
        color: #f1f5f9;
    }
    div[data-testid="stRadio"] {
        background-color: rgba(30, 41, 59, 0.75) !important;
        backdrop-filter: blur(12px) !important;
        padding: 14px 20px !important;
        border-radius: 14px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #161e2e !important;
        border: 1px solid #1e293b !important;
        border-radius: 14px !important;
        padding: 14px !important;
    }
    .cat-badge { font-size: 0.70rem; font-weight: 800; padding: 3px 9px; border-radius: 12px; text-transform: uppercase; color: #0f172a; display: inline-block; margin-bottom: 6px; }
    .hero-badge { background-color: transparent; color: #F472B6; border: 1px solid #F472B6; font-weight: 800; font-size: 0.75rem; padding: 4px 12px; border-radius: 20px; text-transform: uppercase; display: inline-block; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# --- RESTE DU CODE ---
@st.dialog("⤓ Installer Krea sur votre appareil")
def show_install_instructions():
    st.write("Pour garder un accès rapide à Krea, ajoutez-le à votre écran d'accueil.")

# Initialisation
if "bookmarks" not in st.session_state: st.session_state.bookmarks = set()
if "read_articles" not in st.session_state: st.session_state.read_articles = set()
if "category_views" not in st.session_state: st.session_state.category_views = {}
if "articles_limit" not in st.session_state: st.session_state.articles_limit = 12
if "search_input" not in st.session_state: st.session_state.search_input = ""

# ... (le reste de votre logique reste identique)
# Note : Pour des raisons de longueur, veillez à garder toutes vos fonctions
# (clean_text, fetch_all_feeds, etc.) après ces lignes.
st.success("Configuration chargée avec succès.")
