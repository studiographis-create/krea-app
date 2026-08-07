import streamlit as st
import feedparser
import re
import requests
import hashlib
from datetime import datetime, timezone
import time

# Configuration de la page
st.set_page_config(
    page_title="Krea — L'Actu Créative & IA",
    page_icon="✨",
    layout="wide"
)

# Style CSS : Fond graphique, thématique sombre et forçage du rose (#F472B6)
st.markdown("""
<meta name="referrer" content="no-referrer">
<style>
    /* Masquer le header Streamlit (Stop, Fork, GitHub) et le footer */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    div[data-testid="stDecoration"] {display: none;}

    /* Fond d'écran général avec effet mesh gradient créatif en haut de page */
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
    
    /* Personnalisation de l'indicateur de chargement (Spinner / Running) */
    div[data-testid="stStatusWidget"], [data-testid="stSpinner"], div[data-testid="stStatusWidget"] > div {
        background-color: rgba(30, 41, 59, 0.85) !important;
        backdrop-filter: blur(8px) !important;
        color: #f1f5f9 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
    }
    div[data-testid="stStatusWidget"] * {
        color: #cbd5e1 !important;
        background-color: transparent !important;
    }

    /* Bloc de sélection des catégories avec fond glassmorphism */
    div[data-testid="stRadio"] {
        background-color: rgba(30, 41, 59, 0.75) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        padding: 14px 20px !important;
        border-radius: 14px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.25);
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

    /* FORÇAGE DE LA COULEUR DU BOUTON RADIO ACTIF */
    div[data-testid="stRadio"] div[data-baseweb="radio"] div:first-child {
        background-color: transparent !important;
        border-color: #F472B6 !important;
    }
    div[data-testid="stRadio"] input:checked + div {
        background-color: #F472B6 !important;
        border-color: #F472B6 !important;
    }
    div[data-testid="stRadio"] div[role="radiogroup"] label div[aria-checked="true"] {
        background-color: #F472B6 !important;
        border-color: #F472B6 !important;
    }
    div[data-testid="stRadio"] [data-baseweb="radio"] [aria-checked="true"] {
        background-color: #F472B6 !important;
        border-color: #F472B6 !important;
    }

    /* UNIFORMISATION BLANCHE LISIBLE DES CHAMPS "Source" ET "Mot-clé" */
    div[data-testid="stTextInput"] input {
        background-color: #f8fafc !important;
        color: #0f172a !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
    }
    div[data-testid="stTextInput"] input::placeholder {
        color: #64748b !important;
        opacity: 1 !important;
    }
    div[data-baseweb="select"] > div {
        background-color: #f8fafc !important;
        color: #0f172a !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 10px !important;
    }
    div[data-baseweb="select"] * {
        color: #0f172a !important;
    }
    div[data-testid="stTextInput"] label p, div[data-testid="stSelectbox"] label p {
        color: #cbd5e1 !important;
        font-weight: 600 !important;
    }

    /* UNIFORMISATION SOMBRE DE TOUS LES BOUTONS ("Lire", "Favori", "Actualiser") */
    div[data-testid="stLinkButton"] a, div[data-testid="stButton"] button {
        background-color: rgba(30, 41, 59, 0.85) !important;
        color: #f1f5f9 !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
        text-decoration: none !important;
    }
    div[data-testid="stLinkButton"] a p, div[data-testid="stButton"] button p {
        color: #f1f5f9 !important;
    }
    div[data-testid="stLinkButton"] a:hover, div[data-testid="stButton"] button:hover {
        border-color: #F472B6 !important;
        color: #F472B6 !important;
        background-color: rgba(30, 41, 59, 0.95) !important;
        box-shadow: 0 0 15px rgba(244, 114, 182, 0.3) !important;
    }
    div[data-testid="stLinkButton"] a:hover p, div[data-testid="stButton"] button:hover p {
        color: #F472B6 !important;
    }

    /* Style des cartes d'articles */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #161e2e !important;
        border: 1px solid #1e293b !important;
        border-radius: 14px !important;
        padding: 14px !important;
        transition: all 0.2s ease-in-out;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: #8b5cf6 !important;
        box-shadow: 0 6px 20px rgba(139, 92, 246, 0.15);
    }

    /* Badges Meta */
    .hero-badge {
        background-color: #F472B6;
        color: #0f172a;
        font-weight: 800;
        font-size: 0.75rem;
        padding: 3px 10px;
        border-radius: 20px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        display: inline-block;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Initialisation de la session pour les favoris
if "bookmarks" not in st.session_state:
    st.session_state.bookmarks = set()

# Logo SVG Krea (avec 'k' descendu et incliné)
st.markdown("""
<div style="margin-bottom: 20px; filter: drop-shadow(0px 8px 24px rgba(139, 92, 246, 0.25));">
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
      <g font-family="sans-serif" font-weight="900" fill="#FFFFFF">
        <text x="33" y="65" font-size="35" transform="rotate(-10 33 65)" text-anchor="middle">k</text>
        <text x="61" y="60" font-size="26" text-anchor="middle">rea</text>
      </g>
      <path d="M 88 4 Q 88 14 98 14 Q 88 14 88 24 Q 88 14 78 14 Q 88 14 88 4 Z" fill="#F472B6" />
      <text x="110" y="46" font-family="sans-serif" font-weight="800" font-size="22" fill="#FFFFFF">L'Actu Créative &amp; IA</text>
      <text x="110" y="68" font-family="sans-serif" font-weight="500" font-size="13" fill="#94A3B8">Toute l'actu du design, de la photo et de l'IA.</text>
    </svg>
</div>
""", unsafe_allow_html=True)

# Sources RSS 100% fiables et structurées
SOURCES = [
    {"name": "Info-Lux", "url": "https://www.info-lux.com/feed/"},
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
    "Lightroom": ["lightroom", "raw", "developpement"],
    "InDesign": ["indesign", "mise en page", "typographie", "edition"],
    "Illustrator": ["illustrator", "vectoriel", "vecteur", "dessin"],
    "AI": ["ia", "ai", "intelligence artificielle", "midjourney", "firefly", "chatgpt"],
    "Graphisme": ["design", "graphiste", "logo", "branding", "couleur", "typographie", "création"],
    "Photo": ["photo", "photographie", "appareil", "objectif", "capteur", "shooting", "portrait", "paysage"],
    "Tutoriels": ["tuto", "tutoriel", "guide", "astuce", "formation", "apprendre", "cours", "technique"],
    "Expos photos": [
        "exposition", "expositions", "expo", "expos", "galerie", "galeries",
        "musee", "musée", "vernissage", "evenement", "événement", "festival",
        "artiste", "artistes", "photos", "photographies", "photographe", "photographes",
        "retrospective", "rétrospective"
    ]
}

def clean_text(raw_html):
    if not raw_html:
        return ""
    text = re.sub(r'<.*?>', ' ', raw_html)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def clean_url(url):
    if not url:
        return None
    url = url.strip()
    if url.startswith("http://") or url.startswith("https://"):
        if any(bad in url.lower() for bad in ["gravatar", "1x1", "pixel", "icon", "logo", "emoji", ".svg", "feedburner"]):
            return None
        return url
    return None

def extract_image_url(entry):
    if 'media_content' in entry and len(entry.media_content) > 0:
        for item in entry.media_content:
            url = clean_url(item.get('url'))
            if url: return url
            
    if 'media_thumbnail' in entry and len(entry.media_thumbnail) > 0:
        for item in entry.media_thumbnail:
            url = clean_url(item.get('url'))
            if url: return url

    if 'enclosures' in entry and len(entry.enclosures) > 0:
        for enc in entry.enclosures:
            if enc.get('type', '').startswith('image/'):
                url = clean_url(enc.get('href'))
                if url: return url

    html_sources = [
        entry.get('summary', ''),
        entry.get('description', '')
    ]
    if 'content' in entry and isinstance(entry.content, list):
        for c in entry.content:
            if isinstance(c, dict) and 'value' in c:
                html_sources.append(c['value'])

    for html_text in html_sources:
        if html_text:
            matches = re.findall(r'<img [^>]*src=["\']([^"\']+)["\']', html_text)
            for src in matches:
                url = clean_url(src)
                if url: return url

    return None

def parse_entry_date(entry):
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        return datetime.fromtimestamp(time.mktime(entry.published_parsed), tz=timezone.utc)
    if hasattr(entry, 'updated_parsed') and entry.updated_parsed:
        return datetime.fromtimestamp(time.mktime(entry.updated_parsed), tz=timezone.utc)
    return datetime.now(timezone.utc)

def format_relative_date(dt):
    now = datetime.now(timezone.utc)
    diff = now - dt
    seconds = int(diff.total_seconds())
    if seconds < 0 or seconds < 60:
        return "À l'instant"
    minutes = seconds // 60
    if minutes < 60:
        return f"Il y a {minutes} min"
    hours = minutes // 60
    if hours < 24:
        return f"Il y a {hours} h"
    days = hours // 24
    if days < 7:
        return f"Il y a {days} j"
    return dt.strftime("%d/%m/%Y")

def estimate_reading_time(text):
    words = len(text.split())
    mins = max(1, round(words / 35))
    return f"⏱️ {mins} min"

def get_unique_fallback(title):
    seed = int(hashlib.md5(title.encode('utf-8')).hexdigest(), 16) % 1000
    return f"https://picsum.photos/seed/{seed}/600/350"

@st.cache_data(ttl=1800, show_spinner="Chargement de l'actualité Krea...")
def fetch_all_feeds():
    articles = []
    for feed in SOURCES:
        try:
            parsed = feedparser.parse(feed["url"])
            for entry in parsed.entries[:8]:
                title = clean_text(entry.get("title", ""))
                summary = clean_text(entry.get("summary", entry.get("description", "")))
                dt = parse_entry_date(entry)
                extracted_url = extract_image_url(entry)
                
                articles.append({
                    "id": hashlib.md5((entry.get("link", "#") + title).encode('utf-8')).hexdigest(),
                    "title": title,
                    "link": entry.get("link", "#"),
                    "source": feed["name"],
                    "summary": summary,
                    "date": dt,
                    "relative_date": format_relative_date(dt),
                    "reading_time": estimate_reading_time(summary),
                    "image_url": extracted_url if extracted_url else get_unique_fallback(title)
                })
        except Exception:
            pass
            
    articles.sort(key=lambda x: x["date"], reverse=True)
    return articles

# Charger tous les articles
all_fetched = fetch_all_feeds()

# Filtres de catégories + Onglet Favoris
categories = ["Tous", "Photoshop", "Lightroom", "InDesign", "Illustrator", "AI", "Graphisme", "Photo", "Tutoriels", "Expos photos", "⭐ Favoris"]
selected_category = st.radio("Filtrer par catégorie :", categories, horizontal=True)

# Barre d'outils : Source, Recherche, Bouton Actualiser
col_source, col_search, col_refresh = st.columns([1.5, 2.5, 1])

with col_source:
    source_options = ["Toutes les sources"] + [s["name"] for s in SOURCES]
    selected_source = st.selectbox("Source :", source_options)

with col_search:
    search_query = st.text_input("🔍 Mot-clé :", "", placeholder="ex: tutoriel, mise à jour, portrait...")

with col_refresh:
    st.write("")
    st.write("")
    if st.button("🔄 Actualiser", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.divider()

# Filtrage des articles
filtered_articles = []
for art in all_fetched:
    text_to_check = f"{art['title']} {art['summary']}".lower()
    
    # Filtre Favoris
    if selected_category == "⭐ Favoris":
        if art["link"] not in st.session_state.bookmarks:
            continue
        cat_match = True
    elif selected_category == "Tous":
        cat_match = True
    elif selected_category == "Expos photos":
        expos_sources = ["L'Œil de la Photographie", "Blind Magazine", "Graine de Photographe", "Info-Lux"]
        is_expos_source = any(src in art["source"] for src in expos_sources)
        kw_list = KEYWORDS.get("Expos photos", [])
        kw_match = any(kw in text_to_check for kw in kw_list)
        cat_match = is_expos_source or kw_match
    else:
        kw_list = KEYWORDS.get(selected_category, [])
        cat_match = any(kw in text_to_check for kw in kw_list)
        
    # Filtre Source
    if selected_source != "Toutes les sources" and art["source"] != selected_source:
        source_match = False
    else:
        source_match = True

    # Filtre Recherche
    if not search_query.strip():
        search_match = True
    else:
        search_match = search_query.lower().strip() in text_to_check
        
    if cat_match and search_match and source_match:
        art_copy = art.copy()
        art_copy["summary_short"] = art["summary"][:160] + "..." if len(art["summary"]) > 160 else art["summary"]
        filtered_articles.append(art_copy)

# AFFICHAGE
if filtered_articles:
    # 1. BANNIÈRE "À LA UNE" (Hero)
    show_hero = (selected_category == "Tous" and selected_source == "Toutes les sources" and not search_query.strip())
    
    start_idx = 0
    if show_hero and len(filtered_articles) > 0:
        hero = filtered_articles[0]
        start_idx = 1
        
        with st.container(border=True):
            st.markdown('<span class="hero-badge">🔥 À LA UNE</span>', unsafe_allow_html=True)
            col_hero_img, col_hero_text = st.columns([1.2, 1])
            with col_hero_img:
                st.markdown(
                    f'<img src="{hero["image_url"]}" style="width:100%; height:260px; object-fit:cover; border-radius:12px; display:block;">', 
                    unsafe_allow_html=True
                )
            with col_hero_text:
                st.caption(f"📍 **{hero['source']}** • 🕒 {hero['relative_date']} • {hero['reading_time']}")
                st.markdown(f"### {hero['title']}")
                st.write(hero['summary'][:240] + "..." if len(hero['summary']) > 240 else hero['summary'])
                
                col_btn1, col_btn2 = st.columns([2, 1])
                with col_btn1:
                    st.link_button("Lire l'article complet", hero['link'], use_container_width=True)
                with col_btn2:
                    is_fav = hero['link'] in st.session_state.bookmarks
                    fav_label = "⭐ Retirer" if is_fav else "☆ Favori"
                    if st.button(fav_label, key=f"fav_hero_{hero['id']}", use_container_width=True):
                        if is_fav:
                            st.session_state.bookmarks.remove(hero['link'])
                        else:
                            st.session_state.bookmarks.add(hero['link'])
                        st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

    # 2. GRILLE D'ARTICLES (3 colonnes)
    grid_articles = filtered_articles[start_idx:]
    if grid_articles:
        cols = st.columns(3)
        for idx, article in enumerate(grid_articles):
            col = cols[idx % 3]
            with col:
                with st.container(border=True):
                    st.markdown(
                        f'<img src="{article["image_url"]}" style="width:100%; height:180px; object-fit:cover; border-radius:10px; margin-bottom:10px; display:block;">', 
                        unsafe_allow_html=True
                    )
                    st.caption(f"📍 **{article['source']}** • {article['relative_date']}")
                    st.markdown(f"**{article['title']}**")
                    st.write(article['summary_short'])
                    
                    c_read, c_fav = st.columns([2, 1])
                    with c_read:
                        st.link_button("Lire", article['link'], use_container_width=True)
                    with c_fav:
                        is_fav = article['link'] in st.session_state.bookmarks
                        fav_icon = "⭐" if is_fav else "☆"
                        if st.button(fav_icon, key=f"fav_{article['id']}", use_container_width=True):
                            if is_fav:
                                st.session_state.bookmarks.remove(article['link'])
                            else:
                                st.session_state.bookmarks.add(article['link'])
                            st.rerun()
elif selected_category == "⭐ Favoris":
    st.info("Vous n'avez pas encore d'articles enregistrés dans vos favoris. Cliquez sur le bouton ☆ sous un article pour l'ajouter ici.")
else:
    st.info("Aucun article trouvé pour ces critères.")
