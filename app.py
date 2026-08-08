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

# --- CONFIGURATION & DESIGN ---
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

st.set_page_config(page_title="Krea — L'Actu Créative & IA", page_icon="🎨", layout="wide")

# Injection Favicon (f-string utilisée, donc on double les accolades {{ }} )
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

# CSS (Pas de f devant le """ car on n'injecte aucune variable Python ici)
st.markdown("""
<style>
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    div[data-testid="stDecoration"] {display: none;}
    .main .block-container {padding-top: 1rem !important;}
    .stApp {background-color: #0b0f19; color: #f1f5f9;}
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #161e2e !important;
        border: 1px solid #1e293b !important;
        border-radius: 14px !important;
        padding: 14px !important;
    }
    .cat-badge {font-size: 0.70rem; font-weight: 800; padding: 3px 9px; border-radius: 12px; text-transform: uppercase; color: #0f172a; display: inline-block; margin-bottom: 6px;}
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
    {"name": "ActuIA", "url": "https://www.actuia.com/feed/"}
]

# --- FONCTIONS ---
def clean_text(raw_html): return re.sub(r'<.*?>', ' ', raw_html).strip()

@st.cache_data(ttl=1800)
def fetch_all_feeds():
    articles = []
    headers = {"User-Agent": "Mozilla/5.0"}
    for feed in SOURCES:
        try:
            resp = requests.get(feed["url"], headers=headers, timeout=5)
            if resp.status_code == 200:
                parsed = feedparser.parse(resp.content)
                for entry in parsed.entries[:5]:
                    articles.append({
                        "title": entry.get("title", "Sans titre"),
                        "link": entry.get("link", "#"),
                        "source": feed["name"],
                        "summary": clean_text(entry.get("summary", ""))
                    })
        except: continue
    return articles

# --- UI ---
st.title("Krea - Dashboard Actu")
all_articles = fetch_all_feeds()

if not all_articles:
    st.warning("Chargement en cours...")
else:
    for art in all_articles:
        with st.container(border=True):
            st.subheader(art['title'])
            st.caption(f"Source: {art['source']}")
            st.link_button("Lire", art['link'])
