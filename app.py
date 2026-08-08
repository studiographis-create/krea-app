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

# --- CONFIGURATION LOGO & FAVICON ---
KREA_SVG_ICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <defs>
    <linearGradient id="g1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#8B5CF6"/><stop offset="100%" stop-color="#2563EB"/>
    </linearGradient>
    <linearGradient id="g2" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#06B6D4" stop-opacity="0.6"/><stop offset="100%" stop-color="#3B82F6" stop-opacity="0.3"/>
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

# Injection Favicon & Scripts
st.markdown(f"""
<script>
(function() {{
    var svgUri = "{svg_data_uri}";
    var doc = window.parent ? window.parent.document : document;
    var links = doc.querySelectorAll("link[rel*='icon']");
    links.forEach(function(l) {{ l.href = svgUri; }});
}})();
</script>
""", unsafe_allow_html=True)

st.markdown("""
<style>
    header {visibility: hidden;}
    .stApp {background-color: #0b0f19; color: #f1f5f9;}
    div[data-testid="stVerticalBlockBorderWrapper"] {background-color: #161e2e !important; border: 1px solid #1e293b !important; border-radius: 14px !important; padding: 14px !important;}
    .article-read { opacity: 0.65; filter: grayscale(15%); }
    .cat-badge { font-size: 0.70rem; font-weight: 800; padding: 3px 9px; border-radius: 12px; text-transform: uppercase; color: #0f172a; display: inline-block; margin-bottom: 6px; }
    .read-badge { font-size: 0.65rem; font-weight: 700; padding: 2px 7px; border-radius: 10px; color: #94a3b8; border: 1px solid rgba(148, 163, 184, 0.4); display: inline-block; margin-left: 6px; }
</style>
""", unsafe_allow_html=True)

# --- ETAT DE SESSION ---
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

KEYWORDS = {
    "Photoshop": ["photoshop", "psd"], "AI": ["ia", "intelligence artificielle", "midjourney"],
    "Photo": ["photo", "photographie", "portrait"], "Graphisme": ["design", "logo", "branding"]
}
CATEGORY_COLORS = {"Photoshop": "#38BDF8", "AI": "#A855F7", "Photo": "#F59E0B", "Graphisme": "#EC4899", "Général": "#64748B"}

# --- FONCTIONS ---
def clean_text(text): return re.sub(r'<.*?>', ' ', text).strip()
def extract_image_url(entry): return "https://picsum.photos/600/350" # Simplifié pour la performance
def detect_category(title, summary, source_name):
    text = f"{title} {summary}".lower()
    for cat, kws in KEYWORDS.items():
        for kw in kws:
            if re.search(r'\b' + re.escape(kw) + r'\b', text): return cat
    return "Général"

@st.cache_data(ttl=1800)
def fetch_all_feeds():
    articles = []
    headers = {"User-Agent": "Mozilla/5.0"}
    for feed in SOURCES:
        try:
            resp = requests.get(feed["url"], headers=headers, timeout=4)
            if resp.status_code == 200:
                parsed = feedparser.parse(resp.content)
                for entry in parsed.entries[:4]:
                    articles.append({
                        "id": hashlib.md5((entry.get("link", "")).encode()).hexdigest(),
                        "title": clean_text(entry.get("title", "")),
                        "link": entry.get("link", "#"),
                        "source": feed["name"],
                        "summary": clean_text(entry.get("summary", "")),
                        "category": detect_category(entry.get("title", ""), entry.get("summary", ""), feed["name"]),
                        "image_url": "https://picsum.photos/600/350"
                    })
        except: continue
    return articles

all_fetched = fetch_all_feeds()

# --- UI ET FILTRES ---
st.title("Krea - Dashboard Actu")

# Multi-sélection des catégories
categories_list = ["Photoshop", "AI", "Graphisme", "Photo", "Général", "☆ Favoris"]
selected_categories = st.multiselect("Filtrer par catégorie(s) :", categories_list, default=[], placeholder="Toutes les catégories")

col_source, col_search = st.columns(2)
with col_source:
    selected_source = st.selectbox("Source :", ["Toutes les sources"] + [s["name"] for s in SOURCES])
with col_search:
    search_query = st.text_input("⌕ Recherche :", placeholder="Mot-clé...")

# LOGIQUE DE FILTRAGE
filtered_articles = []
for art in all_fetched:
    # Filtre Favoris
    if "☆ Favoris" in selected_categories and art["link"] not in st.session_state.bookmarks: continue
    
    # Filtre Catégorie (si rien sélectionné, on montre tout)
    cat_match = (not selected_categories or "☆ Favoris" in selected_categories and len(selected_categories)==1) or (art["category"] in selected_categories)
    
    source_match = (selected_source == "Toutes les sources" or art["source"] == selected_source)
    search_match = (not search_query.strip() or search_query.lower() in art["title"].lower())
    
    if cat_match and source_match and search_match:
        filtered_articles.append(art)

# AFFICHAGE
for art in filtered_articles[:st.session_state.articles_limit]:
    is_read = art['id'] in st.session_state.read_articles
    with st.container(border=True):
        st.markdown(f'<div class="{"article-read" if is_read else ""}">', unsafe_allow_html=True)
        st.markdown(f'<span class="cat-badge" style="background-color:{CATEGORY_COLORS.get(art["category"], "#64748B")};">{art["category"]}</span>', unsafe_allow_html=True)
        st.subheader(art['title'])
        if st.button("Lire", key=f"read_{art['id']}"):
            st.session_state.read_articles.add(art['id'])
            st.link_button("Go", art['link'])
        st.markdown('</div>', unsafe_allow_html=True)
