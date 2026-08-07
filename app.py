import streamlit as st
import feedparser
import re

# Configuration de la page
st.set_page_config(
    page_title="Krea — L'Actu Créative & IA",
    page_icon="✨",
    layout="wide"
)

# Style CSS : Lisibilité, pastille rose (#F472B6) et champ de recherche stylisé
st.markdown("""
<style>
    .stApp {
        background-color: #0b0f19;
        color: #f1f5f9;
    }
    
    /* Bloc de sélection des catégories */
    div[data-testid="stRadio"] {
        background-color: #1e293b !important;
        padding: 14px 20px !important;
        border-radius: 14px !important;
        border: 1px solid #334155 !important;
    }
    div[data-testid="stRadio"] label {
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
    }
    div[data-testid="stRadio"] p {
        color: #cbd5e1 !important;
        font-size: 0.95rem !important;
        font-weight: 700 !important;
    }

    /* Pastille de sélection de catégorie en rose (#F472B6) */
    div[data-testid="stRadio"] div[role="radiogroup"] [aria-checked="true"] {
        border-color: #F472B6 !important;
    }
    div[data-testid="stRadio"] div[role="radiogroup"] [aria-checked="true"] div {
        background-color: #F472B6 !important;
    }
    div[data-baseweb="radio"] [aria-checked="true"] {
        border-color: #F472B6 !important;
    }
    div[data-baseweb="radio"] [aria-checked="true"] div {
        background-color: #F472B6 !important;
    }

    /* Style du champ de recherche */
    div[data-testid="stTextInput"] input {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
    }
    div[data-testid="stTextInput"] label p {
        color: #cbd5e1 !important;
        font-weight: 600 !important;
    }

    /* Style des cartes d'articles */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #161e2e !important;
        border: 1px solid #1e293b !important;
        border-radius: 14px !important;
        padding: 10px !important;
        transition: all 0.2s ease-in-out;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: #8b5cf6 !important;
        box-shadow: 0 6px 20px rgba(139, 92, 246, 0.15);
    }
</style>
""", unsafe_allow_html=True)

# Logo SVG Krea
st.markdown("""
<div style="margin-bottom: 25px;">
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 100" width="340" style="max-width: 100%; height: auto;">
      <defs>
        <linearGradient id="kreaGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#8B5CF6" />
          <stop offset="100%" stop-color="#2563EB" />
        </linearGradient>
        <linearGradient id="layerGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#06B6D4" stop-opacity="0.5"/>
          <stop offset="100%" stop-color="#3B82F6" stop-opacity="0.2"/>
        </linearGradient>
      </defs>
      <rect x="22" y="18" width="76" height="76" rx="18" fill="url(#layerGrad)" transform="rotate(-6 60 56)" />
      <rect x="15" y="12" width="76" height="76" rx="18" fill="url(#kreaGrad)" />
      <text x="53" y="60" font-family="sans-serif" font-weight="900" font-size="28" fill="#FFFFFF" text-anchor="middle">krea</text>
      <path d="M 88 4 Q 88 14 98 14 Q 88 14 88 24 Q 88 14 78 14 Q 88 14 88 4 Z" fill="#F472B6" />
      <text x="110" y="46" font-family="sans-serif" font-weight="800" font-size="22" fill="#FFFFFF">L'Actu Créative &amp; IA</text>
      <text x="110" y="68" font-family="sans-serif" font-weight="500" font-size="13" fill="#94A3B8">Toute l'actu du design, de la photo et de l'IA.</text>
    </svg>
</div>
""", unsafe_allow_html=True)

# Sources enrichies (10 flux RSS créatifs)
SOURCES = [
    {"name": "Adobe Blog FR", "url": "https://blog.adobe.com/fr/feed.xml"},
    {"name": "Graphiste.com", "url": "https://blog.graphiste.com/feed"},
    {"name": "Phototrend", "url": "https://phototrend.fr/feed/"},
    {"name": "Blog du Modérateur", "url": "https://www.blogdumoderateur.com/im-outils/intelligence-artificielle/feed/"},
    {"name": "Grapheine", "url": "https://www.grapheine.com/feed"},
    {"name": "Apprendre la Photo", "url": "https://apprendre-la-photo.fr/feed/"},
    {"name": "Créapills", "url": "https://creapills.com/feed"},
    {"name": "Webdesignertrends", "url": "https://www.webdesignertrends.com/feed/"},
    {"name": "Les Numériques (Photo)", "url": "https://www.lesnumeriques.com/photo/rss.xml"},
    {"name": "Korben", "url": "https://korben.info/feed"},
]

KEYWORDS = {
    "Photoshop": ["photoshop", "psd", "retouche"],
    "Lightroom": ["lightroom", "raw", "developpement"],
    "InDesign": ["indesign", "mise en page", "typographie", "edition"],
    "Illustrator": ["illustrator", "vectoriel", "vecteur", "dessin"],
    "AI": ["ia", "ai", "intelligence artificielle", "midjourney", "firefly", "chatgpt"],
    "Graphisme": ["design", "graphiste", "logo", "branding", "couleur", "typographie", "création"],
    "Photo": ["photo", "photographie", "appareil", "objectif", "capteur", "shooting", "portrait", "paysage"]
}

def clean_text(raw_html):
    return re.sub(r'<.*?>', '', raw_html)

# Barre des filtres de catégories
categories = ["Tous", "Photoshop", "Lightroom", "InDesign", "Illustrator", "AI", "Graphisme", "Photo"]
selected_category = st.radio("Filtrer par catégorie :", categories, horizontal=True)

# Barre de recherche par mot-clé
search_query = st.text_input("🔍 Rechercher par mot-clé (ex: tutoriel, mise à jour, portrait...) :", "")

st.divider()

all_articles = []

with st.spinner("Chargement des articles de Krea..."):
    for feed in SOURCES:
        parsed = feedparser.parse(feed["url"])
        for entry in parsed.entries[:6]:
            title = entry.get("title", "")
            summary = clean_text(entry.get("summary", entry.get("description", "")))
            text_to_check = f"{title} {summary}".lower()
            
            # 1. Filtre catégorie
            if selected_category == "Tous":
                cat_match = True
            else:
                kw_list = KEYWORDS.get(selected_category, [])
                cat_match = any(kw in text_to_check for kw in kw_list)
            
            # 2. Filtre recherche textuelle
            if not search_query.strip():
                search_match = True
            else:
                search_match = search_query.lower().strip() in text_to_check
                
            if cat_match and search_match:
                all_articles.append({
                    "title": title,
                    "link": entry.get("link", "#"),
                    "source": feed["name"],
                    "summary": summary[:200] + "..." if len(summary) > 200 else summary,
                })

if all_articles:
    cols = st.columns(3)
    for idx, article in enumerate(all_articles):
        col = cols[idx % 3]
        with col:
            with st.container(border=True):
                st.caption(f"📍 {article['source']}")
                st.markdown(f"**{article['title']}**")
                st.write(article['summary'])
                st.link_button("Lire l'article", article['link'], use_container_width=True)
else:
    st.info("Aucun article trouvé pour ces critères.")
