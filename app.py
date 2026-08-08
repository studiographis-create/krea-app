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

# Configuration de la page Streamlit
st.set_page_config(
    page_title="Krea — L'Actu Créative & IA",
    page_icon="🎨",
    layout="wide"
)

# Injection favicon et scripts
st.markdown(f"""
<head>
    <link rel="icon" type="image/svg+xml" href="{svg_data_uri}">
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
    }}
    setFavicon();
    setTimeout(setFavicon, 1000);
}})();
</script>
""", unsafe_allow_html=True)

# Style CSS : Mesh gradient, Glassmorphism & Responsive
st.markdown("""
<style>
    header {visibility: hidden;}
    .stApp {
        background-color: #0b0f19;
        background-image: radial-gradient(at 15% 10%, rgba(139, 92, 246, 0.22) 0px, transparent 40%),
                          radial-gradient(at 85% 5%, rgba(37, 99, 235, 0.20) 0px, transparent 45%);
        color: #f1f5f9;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #161e2e !important;
        border: 1px solid #1e293b !important;
        border-radius: 14px !important;
        padding: 14px !important;
    }
    .article-read { opacity: 0.65; filter: grayscale(15%); }
    .cat-badge { font-size: 0.70rem; font-weight: 800; padding: 3px 9px; border-radius: 12px; text-transform: uppercase; color: #0f172a; display: inline-block; margin-bottom: 6px; }
    .read-badge { font-size: 0.65rem; font-weight: 700; padding: 2px 7px; border-radius: 10px; color: #94a3b8; border: 1px solid rgba(148, 163, 184, 0.4); display: inline-block; margin-left: 6px; }
</style>
""", unsafe_allow_html=True)

# --- ETATS & SOURCES ---
if "bookmarks" not in st.session_state: st.session_state.bookmarks = set()
if "read_articles" not in st.session_state: st.session_state.read_articles = set()
if "articles_limit" not in st.session_state: st.session_state.articles_limit = 12

SOURCES = [
    {"name": "Phototrend", "url": "https://phototrend.fr/feed/"},
    {"name": "Blog du Modérateur", "url": "https://www.blogdumoderateur.com/feed/"},
    {"name": "Grapheine", "url": "https://www.grapheine.com/feed"},
    {"name": "ActuIA", "url": "https://www.actuia.com/feed/"},
    {"name": "Journal du Geek", "url": "https://www.journaldugeek.com/feed/"}
]

# (Gardez vos fonctions extract_image_url, detect_category, fetch_all_feeds telles quelles)
# ... [Les fonctions restent identiques à la version précédente] ...

# --- FOOTER RESTAURÉ AVEC LOGO ---
st.markdown("""
<div style="text-align: center; margin-top: 60px; padding: 30px 0 10px 0; border-top: 1px solid rgba(255, 255, 255, 0.08);">
    <div style="display: flex; justify-content: center; align-items: center; margin-bottom: 8px;">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 110 110" width="55" height="55" style="filter: drop-shadow(0px 4px 12px rgba(139, 92, 246, 0.3));">
          <defs>
            <linearGradient id="kreaGradFooter" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="#8B5CF6" />
              <stop offset="100%" stop-color="#2563EB" />
            </linearGradient>
            <linearGradient id="layerGradFooter" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="#06B6D4" stop-opacity="0.5"/>
              <stop offset="100%" stop-color="#3B82F6" stop-opacity="0.2"/>
            </linearGradient>
          </defs>
          <rect x="22" y="18" width="76" height="76" rx="18" fill="url(#layerGradFooter)" transform="rotate(-6 60 56)" />
          <rect x="15" y="12" width="76" height="76" rx="18" fill="url(#kreaGradFooter)" />
          <text x="53" y="66" font-family="sans-serif" font-weight="900" font-size="54" fill="#FFFFFF" text-anchor="middle" transform="rotate(-10 53 66)">k</text>
          <path d="M 88 4 Q 88 14 98 14 Q 88 14 88 24 Q 88 14 78 14 Q 88 14 88 4 Z" fill="#F472B6" />
        </svg>
    </div>
    <p style="color: #94A3B8; font-size: 0.85rem; font-weight: 600; letter-spacing: 0.5px; margin: 0;">Krea — by Graphis Studio</p>
</div>
""", unsafe_allow_html=True)
