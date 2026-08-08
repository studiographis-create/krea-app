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

# --- CONFIGURATION LOGO ---
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

st.markdown("""
<style>
    header {visibility: hidden;}
    .stApp {background-color: #0b0f19; color: #f1f5f9;}
    div[data-testid="stVerticalBlockBorderWrapper"] {background-color: #161e2e !important; border: 1px solid #1e293b !important; border-radius: 14px !important; padding: 14px !important;}
    .article-read { opacity: 0.65; filter: grayscale(15%); }
    .cat-badge { font-size: 0.70rem; font-weight: 800; padding: 3px 9px; border-radius: 12px; text-transform: uppercase; color: #0f172a; display: inline-block; margin-bottom: 6px; }
    .read-badge { font-size: 0.65rem; font-weight: 700; padding: 2px 7px; border-radius: 10px; color: #94a3b8; border: 1px solid rgba(148, 163, 184, 0.4); display: inline-block; margin-left: 6px; }
    div[data-testid="stButton"] > button { border-radius: 12px !important; font-size: 0.75rem !important; }
</style>
""", unsafe_allow_html=True)

# --- ETAT ---
if "bookmarks" not in st.session_state: st.session_state.bookmarks = set()
if "read_articles" not in st.session_state: st.session_state.read_articles = set()
if "articles_limit" not in st.session_state: st.session_state.articles_limit = 12
if "selected_cats" not in st.session_state: st.session_state.selected_cats = []

SOURCES = [
    {"name": "Phototrend", "url": "https://phototrend.fr/feed/"},
    {"name": "Blog du Modérateur", "url": "https://www.blogdumoderateur.com/feed/"},
    {"name": "Grapheine", "url": "https://www.grapheine.com/feed"},
    {"name": "Apprendre la Photo", "url": "https://apprendre-la-photo.fr/feed/"},
    {"name": "Créapills", "url": "https://creapills.com/feed"},
    {"name": "Webdesignertrends", "url": "https://www.webdesignertrends.com/feed/"},
    {"name": "Les Numériques (Photo)", "url": "https://www.lesnumeriques.com/photo/rss.xml"},
    {"name": "Korben", "url": "https://korben.info/feed"},
    {"name": "Journal du Geek", "url": "https://www.journaldugeek.com/feed/"},
    {"name": "Mac4Ever", "url": "https://www.mac4ever.com/rss"},
    {"name": "Olivier Rocq", "url": "https://www.olivier-rocq.com/feed/"},
    {"name": "ZDNet FR", "url": "https://www.zdnet.fr/rss/news/"},
    {"name": "Le Monde Informatique", "url": "https://www.lemondeinformatique.fr/rss/rss.xml"},
    {"name": "ActuIA", "url": "https://www.actuia.com/feed/"},
    {"name": "L'Usine Digitale", "url": "https://www.usine-digitale.fr/rss"},
    {"name": "RTBF - IA", "url": "https://www.rtbf.be/rss/tag_intelligence-artificielle.xml"},
    {"name": "L'Œil de la Photographie", "url": "https://loeildelaphotographie.com/fr/feed/"},
    {"name": "Graine de Photographe", "url": "https://blog.grainedephotographe.com/feed/"},
    {"name": "Blind Magazine", "url": "https://www.blind-magazine.com/fr/feed/"},
    {"name": "OuiOui Photo", "url": "https://blog.ouiouiphoto.fr/feed/"},
]

KEYWORDS = {
    "Photoshop": ["photoshop", "psd"], "AI": ["ia", "intelligence artificielle"],
    "Photo": ["photo", "photographie"], "Graphisme": ["design", "logo"], "Général": []
}
CATEGORY_COLORS = {"Photoshop": "#38BDF8", "AI": "#A855F7", "Photo": "#F59E0B", "Graphisme": "#EC4899", "Général": "#64748B"}

# --- FONCTIONS ---
def clean_text(raw_html): return re.sub(r'\s+', ' ', re.sub(r'<.*?>', ' ', raw_html)).strip()

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

# --- UI ---
st.title("Krea - Dashboard Actu")

# Filtres catégories (Pastilles sur une ligne)
st.write("Catégories :")
cat_cols = st.columns(len(CATEGORY_COLORS))
for i, cat in enumerate(CATEGORY_COLORS.keys()):
    with cat_cols[i]:
        is_active = cat in st.session_state.selected_cats
        if st.button(f"{'●' if is_active else '○'} {cat}", key=f"cat_{cat}", use_container_width=True):
            if is_active: st.session_state.selected_cats.remove(cat)
            else: st.session_state.selected_cats.append(cat)
            st.rerun()

col_s, col_r = st.columns(2)
with col_s: selected_source = st.selectbox("Source :", ["Toutes les sources"] + [s["name"] for s in SOURCES])
with col_r: search_query = st.text_input("⌕ Recherche :", placeholder="Mot-clé...")

# Filtrage
filtered = [
    a for a in all_fetched 
    if (not st.session_state.selected_cats or a["category"] in st.session_state.selected_cats) and
       (selected_source == "Toutes les sources" or a["source"] == selected_source) and
       (not search_query.strip() or search_query.lower() in a["title"].lower())
]

# Affichage
for art in filtered[:st.session_state.articles_limit]:
    with st.container(border=True):
        st.markdown(f'<span class="cat-badge" style="background-color:{CATEGORY_COLORS.get(art["category"], "#64748B")};">{art["category"]}</span>', unsafe_allow_html=True)
        st.subheader(art['title'])
        if st.button("Lire", key=f"btn_{art['id']}"):
            st.session_state.read_articles.add(art['id'])
            st.link_button("Lien", art['link'])

# FOOTER LOGO
st.markdown("""
<div style="text-align: center; margin-top: 60px; padding: 30px 0 10px 0; border-top: 1px solid rgba(255, 255, 255, 0.08);">
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 110 110" width="55" height="55"><rect x="15" y="12" width="76" height="76" rx="18" fill="#8B5CF6"/><text x="53" y="66" font-family="sans-serif" font-weight="900" font-size="54" fill="#FFFFFF" text-anchor="middle" transform="rotate(-10 53 66)">k</text></svg>
    <p style="color: #94A3B8; font-size: 0.85rem;">Krea — by Graphis Studio</p>
</div>
""", unsafe_allow_html=True)
