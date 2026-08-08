import streamlit as st
import feedparser
import re
import requests
from datetime import datetime, timezone

# --- CONFIGURATION ---
st.set_page_config(page_title="Krea — L'Actu Créative", page_icon="🎨", layout="wide")

st.markdown("""
<style>
    header {visibility: hidden;}
    .stApp {background-color: #0b0f19; color: #f1f5f9;}
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #161e2e !important;
        border: 1px solid #1e293b !important;
        border-radius: 14px !important;
        padding: 15px !important;
    }
    h1 { color: #ffffff !important; }
</style>
""", unsafe_allow_html=True)

# --- SOURCES RSS ---
SOURCES = [
    {"name": "Phototrend", "url": "https://phototrend.fr/feed/"},
    {"name": "Blog du Modérateur", "url": "https://www.blogdumoderateur.com/feed/"},
    {"name": "Grapheine", "url": "https://www.grapheine.com/feed"},
    {"name": "ActuIA", "url": "https://www.actuia.com/feed/"},
    {"name": "Journal du Geek", "url": "https://www.journaldugeek.com/feed/"}
]

def clean_text(text):
    return re.sub(r'<.*?>', ' ', text).strip()

@st.cache_data(ttl=60)
def fetch_articles():
    articles = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    for feed in SOURCES:
        try:
            resp = requests.get(feed["url"], headers=headers, timeout=4)
            if resp.status_code == 200:
                parsed = feedparser.parse(resp.content)
                for entry in parsed.entries[:3]:
                    articles.append({
                        "title": entry.get("title", "Sans titre"),
                        "link": entry.get("link", "#"),
                        "source": feed["name"],
                        "summary": clean_text(entry.get("summary", ""))
                    })
        except Exception:
            continue
            
    return articles

# --- INTERFACE ---
st.title("Krea - Dashboard Actu")

col1, col2 = st.columns([1, 4])
with col1:
    if st.button("↻ Vider le cache & Actualiser", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

all_articles = fetch_articles()

if not all_articles:
    st.warning("⚠️ Aucun article n'a pu être récupéré.")
else:
    st.success(f"✅ {len(all_articles)} articles chargés avec succès !")
    cols = st.columns(3)
    for i, art in enumerate(all_articles):
        with cols[i % 3]:
            with st.container(border=True):
                st.markdown(f"**{art['source']}**")
                st.subheader(art['title'])
                st.write(art['summary'][:100] + "...")
                st.link_button("Lire l'article", art['link'], use_container_width=True)
