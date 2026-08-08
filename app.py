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

# --- CONFIGURATION & SVG ---
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

# CSS
st.markdown("""
<style>
    header {visibility: hidden;} #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    .stApp {background-color: #0b0f19; color: #f1f5f9; background-image: radial-gradient(at 15% 10%, rgba(139, 92, 246, 0.22) 0px, transparent 40%), radial-gradient(at 85% 5%, rgba(37, 99, 235, 0.20) 0px, transparent 45%);}
    div[data-testid="stVerticalBlockBorderWrapper"] {background-color: #161e2e !important; border: 1px solid #1e293b !important; border-radius: 14px !important; padding: 14px !important;}
    .cat-badge {font-size: 0.70rem; font-weight: 800; padding: 3px 9px; border-radius: 12px; text-transform: uppercase; color: #0f172a; display: inline-block; margin-bottom: 6px;}
    div[data-testid="stRadio"] {background-color: rgba(30, 41, 59, 0.75) !important; padding: 14px 20px !important; border-radius: 14px !important;}
</style>
""", unsafe_allow_html=True)

# --- ÉTATS ---
if "bookmarks" not in st.session_state: st.session_state.bookmarks = set()
if "read_articles" not in st.session_state: st.session_state.read_articles = set()
if "category_views" not in st.session_state: st.session_state.category_views = {}
if "articles_limit" not in st.session_state: st.session_state.articles_limit = 12
if "search_input" not in st.session_state: st.session_state.search_input = ""

# --- SOURCES ---
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
    "Photoshop": ["photoshop", "psd", "retouche"],
    "Photo": ["photo", "photographie", "appareil photo"],
    "AI": ["ia", "intelligence artificielle", "midjourney", "firefly"]
}

# --- FONCTIONS ---
def clean_text(text): return re.sub(r'<.*?>', ' ', text).strip()
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
                        "summary": clean_text(entry.get("summary", "")),
                        "date": datetime.now(timezone.utc)
                    })
        except: continue
    return articles

# --- UI ---
st.title("Krea - Dashboard Actu")
all_articles = fetch_all_feeds()

if not all_articles:
    st.warning("Impossible de charger les flux. Vérifiez votre connexion ou les URLs.")
else:
    for art in all_articles:
        with st.container():
            st.subheader(art['title'])
            st.write(f"Source: {art['source']}")
            st.link_button("Lire", art['link'])
