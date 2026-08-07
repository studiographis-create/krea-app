import streamlit as st
import feedparser
import re
import requests
import hashlib
import json
import urllib.parse
from datetime import datetime, timezone
import time

# Configuration de la page
st.set_page_config(
    page_title="Krea — L'Actu Créative & IA",
    page_icon="✨",
    layout="wide"
)

# Style CSS : Mesh gradient, Glassmorphism & Responsive Rules
st.markdown("""
<meta name="referrer" content="no-referrer">
<style>
    /* Masquer le header Streamlit et le footer */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    div[data-testid="stDecoration"] {display: none;}

    /* Réduction de la marge en haut de page */
    .main .block-container, div[data-testid="stMainBlockContainer"] {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
    }

    /* Fond d'écran général avec mesh gradient */
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
    
    /* Dynamic Loading Indicator / Status Widget (Fond sombre forcé) */
    div[data-testid="stStatusWidget"], 
    div[data-testid="stSpinner"], 
    div[data-testid="stNotification"],
    div[data-testid="stToast"],
    div[data-baseweb="toast"],
    div[data-testid="stStatusWidget"] > div,
    div[data-testid="stStatusWidget"] * {
        background-color: rgba(15, 23, 42, 0.95) !important;
        backdrop-filter: blur(12px) !important;
        color: #f8fafc !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 12px !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5) !important;
    }
    
    div[data-testid="stStatusWidget"] p, 
    div[data-testid="stStatusWidget"] span,
    div[data-testid="stSpinner"] p,
    div[data-testid="stSpinner"] span {
        color: #ffffff !important;
        font-weight: 600 !important;
    }

    /* Labels de tous les champs en blanc lisible */
    div[data-testid="stWidgetLabel"] p, label p, label {
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        opacity: 1 !important;
    }

    /* Radio Filter Bar (Catégories) */
    div[data-testid="stRadio"] {
        background-color: rgba(30, 41, 59, 0.75) !important;
        backdrop-filter: blur(12px) !important;
        padding: 14px 20px !important;
        border-radius: 14px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.25);
    }
    div[data-testid="stRadio"] label {
        color: #ffffff !important;
        font-weight: 700 !important;
    }

    div[data-testid="stRadio"] div[data-baseweb="radio"] div:first-child {
        background-color: transparent !important;
        border-color: #F472B6 !important;
    }
    div[data-testid="stRadio"] input:checked + div {
        background-color: #F472B6 !important;
        border-color: #F472B6 !important;
    }

    /* Input & Select Box styling */
    div[data-testid="stTextInput"] input {
        background-color: #f8fafc !important;
        color: #0f172a !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
    }
    div[data-baseweb="select"] > div {
        background-color: #f8fafc !important;
        color: #0f172a !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 10px !important;
    }
    div[data-baseweb="select"] * { color: #0f172a !important; }

    /* Button Styling */
    div[data-testid="stLinkButton"] a, div[data-testid="stButton"] button {
        background-color: rgba(30, 41, 59, 0.85) !important;
        color: #f1f5f9 !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.25s ease !important;
        text-decoration: none !important;
    }
    div[data-testid="stLinkButton"] a:hover, div[data-testid="stButton"] button:hover {
        border-color: #F472B6 !important;
        color: #F472B6 !important;
        background-color: rgba(30, 41, 59, 0.95) !important;
        box-shadow: 0 0 15px rgba(244, 114, 182, 0.3) !important;
    }

    /* Cards standard - Hover Lift & Glow Effect */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #161e2e !important;
        border: 1px solid #1e293b !important;
        border-radius: 14px !important;
        padding: 14px !important;
        transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-5px) !important;
        border-color: #8b5cf6 !important;
        box-shadow: 0 12px 28px -5px rgba(139, 92, 246, 0.25) !important;
    }

    /* Mise en évidence spécifique du bloc À LA UNE */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.hero-badge) {
        background-color: rgba(15, 23, 42, 0.92) !important;
        backdrop-filter: blur(16px) !important;
        border: 1.5px solid rgba(244, 114, 182, 0.35) !important;
        border-radius: 18px !important;
        padding: 20px !important;
        box-shadow: 0 12px 36px 0 rgba(0, 0, 0, 0.45) !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.hero-badge):hover {
        border-color: #F472B6 !important;
        box-shadow: 0 14px 40px rgba(244, 114, 182, 0.25) !important;
    }

    /* Masquer le bloc Affichage sur Smartphone */
    @media (max-width: 768px) {
        div[data-testid="stColumn"]:has(#view-mode-marker) {
            display: none !important;
        }

        /* FORCER 3 COLONNES SUR MOBILE POUR LES TENDANCES DU MOMENT */
        div.stApp div[data-testid="stHorizontalBlock"]:has(> div[data-testid="stColumn"]:nth-child(6)) {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: wrap !important;
            gap: 6px 4px !important;
        }

        div.stApp div[data-testid="stHorizontalBlock"]:has(> div[data-testid="stColumn"]:nth-child(6)) > div[data-testid="stColumn"] {
            width: calc(33.333% - 4px) !important;
            min-width: calc(33.333% - 4px) !important;
            max-width: calc(33.333% - 4px) !important;
            flex: 1 0 calc(33.333% - 4px) !important;
            margin: 0 !important;
            padding: 0 !important;
        }

        div.stApp div[data-testid="stHorizontalBlock"]:has(> div[data-testid="stColumn"]:nth-child(6)) button {
            padding: 6px 2px !important;
            width: 100% !important;
        }

        div.stApp div[data-testid="stHorizontalBlock"]:has(> div[data-testid="stColumn"]:nth-child(6)) button p {
            font-size: 0.76rem !important;
            white-space: nowrap !important;
            text-overflow: ellipsis !important;
            overflow: hidden !important;
        }
    }

    /* Category Badges Styling */
    .cat-badge {
        font-size: 0.70rem;
        font-weight: 800;
        padding: 3px 9px;
        border-radius: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #0f172a;
        display: inline-block;
        margin-bottom: 6px;
    }

    .hero-badge {
        background-color: #F472B6;
        color: #0f172a;
        font-weight: 800;
        font-size: 0.75rem;
        padding: 4px 12px;
        border-radius: 20px;
        text-transform: uppercase;
        display: inline-block;
        margin-bottom: 10px;
        letter-spacing: 0.5px;
    }
</style>
""", unsafe_allow_html=True)

# Initialisation de la session
if "bookmarks" not in st.session_state:
    st.session_state.bookmarks = set()
if "search_input" not in st.session_state:
    st.session_state.search_input = ""

# Logo SVG Krea
st.markdown("""
<div style="margin-top: 0px; margin-bottom: 15px; filter: drop-shadow(0px 8px 24px rgba(139, 92, 246, 0.25));">
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 450 110" width="440" style="max-width: 100%; height: auto;">
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
      <text x="110" y="46" font-family="sans-serif" font-weight="800" font-size="25" fill="#FFFFFF">L'Actu Créative &amp; IA</text>
      <text x="110" y="70" font-family="sans-serif" font-weight="500" font-size="14.5" fill="#94A3B8">Toute l'actu du design, de la photo et de l'IA.</text>
    </svg>
</div>
""", unsafe_allow_html=True)

# Sources RSS 100% fiables
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

# Liste des sous-rubriques hors-sujet à filtrer obligatoirement
EXCLUDED_CATEGORIES = [
    "developpement-personnel", "sante", "bien-etre", "politique", 
    "fait-divers", "societe", "lifestyle", "psycho", "sante-bien-etre"
]

KEYWORDS = {
    "Photoshop": ["photoshop", "psd", "retouche"],
    "Lightroom": ["lightroom", "raw", "developpement photo"],
    "InDesign": ["indesign", "mise en page", "typographie", "edition"],
    "Illustrator": ["illustrator", "vectoriel", "vecteur", "dessin"],
    "AI": ["ia", "ai", "intelligence artificielle", "midjourney", "firefly", "chatgpt"],
    "Graphisme": ["design graphique", "graphiste", "logo", "branding", "typographie", "charte graphique"],
    "Photo": ["photo", "photographie", "appareil photo", "objectif photo", "capteur", "shooting", "portrait photo", "paysage photo"],
    "Tutoriels": ["tuto", "tutoriel", "guide technique", "astuce photoshop", "formation design", "cours photo"],
    "Expos photos": [
        "exposition", "expositions", "expo photo", "galerie", "vernissage", "retrospective"
    ]
}

CATEGORY_COLORS = {
    "Photoshop": "#38BDF8",
    "Lightroom": "#60A5FA",
    "InDesign": "#F43F5E",
    "Illustrator": "#FB923C",
    "AI": "#A855F7",
    "Graphisme": "#EC4899",
    "Photo": "#F59E0B",
    "Tutoriels": "#10B981",
    "Expos photos": "#E11D48",
    "Général": "#64748B"
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

def detect_article_category(title, summary):
    text = f"{title} {summary}".lower()
    for cat, kws in KEYWORDS.items():
        if any(kw in text for kw in kws):
            return cat
    return "Général"

def get_unique_fallback(title):
    seed = int(hashlib.md5(title.encode('utf-8')).hexdigest(), 16) % 1000
    return f"https://picsum.photos/seed/{seed}/600/350"

@st.dialog("📖 Aperçu de l'article")
def open_preview_modal(article):
    if article.get("image_url"):
        st.markdown(
            f'<img src="{article["image_url"]}" style="width:100%; max-height:300px; object-fit:cover; border-radius:12px; margin-bottom:12px;">', 
            unsafe_allow_html=True
        )
    st.markdown(f"### {article['title']}")
    st.caption(f"📍 **{article['source']}** • 🕒 {article['relative_date']} • {article['reading_time']}")
    st.write(article['summary'])
    st.divider()
    
    encoded_url = urllib.parse.quote(article['link'])
    encoded_title = urllib.parse.quote(article['title'])
    
    col_open, col_wa, col_x = st.columns([2, 1, 1])
    with col_open:
        st.link_button("🌐 Ouvrir le site d'origine", article['link'], use_container_width=True)
    with col_wa:
        st.link_button("💬 WhatsApp", f"https://api.whatsapp.com/send?text={encoded_title}%20{encoded_url}", use_container_width=True)
    with col_x:
        st.link_button("𝕏 Share", f"https://twitter.com/intent/tweet?text={encoded_title}&url={encoded_url}", use_container_width=True)

@st.cache_data(ttl=1800, show_spinner="Chargement de l'actualité Krea...")
def fetch_all_feeds():
    articles = []
    for feed in SOURCES:
        try:
            parsed = feedparser.parse(feed["url"])
            for entry in parsed.entries[:8]:
                link = entry.get("link", "#")
                
                # Filtrer les articles issus de rubriques non créatives
                if any(bad_cat in link.lower() for bad_cat in EXCLUDED_CATEGORIES):
                    continue

                title = clean_text(entry.get("title", ""))
                summary = clean_text(entry.get("summary", entry.get("description", "")))
                dt = parse_entry_date(entry)
                extracted_url = extract_image_url(entry)
                
                cat = detect_article_category(title, summary)
                articles.append({
                    "id": hashlib.md5((link + title).encode('utf-8')).hexdigest(),
                    "title": title,
                    "link": link,
                    "source": feed["name"],
                    "summary": summary,
                    "date": dt,
                    "relative_date": format_relative_date(dt),
                    "reading_time": estimate_reading_time(summary),
                    "category": cat,
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

# Barre d'outils : Source, Recherche, Mode Affichage, Bouton Actualiser
col_source, col_search, col_view, col_refresh = st.columns([1.5, 2, 1.2, 0.8])

with col_source:
    source_options = ["Toutes les sources"] + [s["name"] for s in SOURCES]
    selected_source = st.selectbox("Source :", source_options)

with col_search:
    search_query = st.text_input("🔍 Mot-clé :", value=st.session_state.search_input, placeholder="ex: tutoriel, midjourney, portrait...")

with col_view:
    st.markdown('<div id="view-mode-marker"></div>', unsafe_allow_html=True)
    view_mode = st.radio("Affichage :", ["Grille", "Liste compacte"], horizontal=True)

with col_refresh:
    st.write("")
    st.write("")
    if st.button("Actualiser", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Mots-clés Tendances (Trending Tags)
st.write("🔥 **Tendances du moment :**")

tag_cols = st.columns(6)
tags = ["Midjourney", "Photoshop", "Tutoriel", "Portrait", "Lightroom", "Exposition"]
for idx, tag in enumerate(tags):
    with tag_cols[idx]:
        if st.button(f"#{tag}", key=f"trend_tag_{idx}", use_container_width=True):
            st.session_state.search_input = tag
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
        expos_sources = ["L'Œil de la Photographie", "Blind Magazine", "Graine de Photographe"]
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

# Exportation des favoris si on est dans l'onglet favoris
if selected_category == "⭐ Favoris" and filtered_articles:
    col_fav_title, col_fav_exp = st.columns([3, 1])
    with col_fav_title:
        st.subheader(f"📌 Vos articles favoris ({len(filtered_articles)})")
    with col_fav_exp:
        json_favs = json.dumps(filtered_articles, indent=2, ensure_ascii=False)
        st.download_button(
            "📥 Exporter les favoris (JSON)",
            data=json_favs,
            file_name="favoris_krea.json",
            mime="application/json",
            use_container_width=True
        )

# AFFICHAGE
if filtered_articles:
    # 1. BANNIÈRE "À LA UNE" (Hero - uniquement en mode Grille)
    show_hero = (selected_category == "Tous" and selected_source == "Toutes les sources" and not search_query.strip() and view_mode == "Grille")
    
    start_idx = 0
    if show_hero and len(filtered_articles) > 0:
        hero = filtered_articles[0]
        start_idx = 1
        cat_color = CATEGORY_COLORS.get(hero['category'], "#64748B")
        
        with st.container(border=True):
            st.markdown('<span class="hero-badge">🔥 À LA UNE</span>', unsafe_allow_html=True)
            col_hero_img, col_hero_text = st.columns([1.2, 1])
            with col_hero_img:
                st.markdown(
                    f'<img src="{hero["image_url"]}" style="width:100%; height:260px; object-fit:cover; border-radius:12px; display:block;">', 
                    unsafe_allow_html=True
                )
            with col_hero_text:
                st.markdown(f'<span class="cat-badge" style="background-color:{cat_color};">{hero["category"]}</span>', unsafe_allow_html=True)
                st.caption(f"📍 **{hero['source']}** • 🕒 {hero['relative_date']} • {hero['reading_time']}")
                st.markdown(f"### {hero['title']}")
                st.write(hero['summary'][:220] + "..." if len(hero['summary']) > 220 else hero['summary'])
                
                c1, c2, c3 = st.columns([1.5, 1, 1])
                with c1:
                    st.link_button("Lire l'article", hero['link'], use_container_width=True)
                with c2:
                    if st.button("📖 Aperçu", key=f"prev_hero_{hero['id']}", use_container_width=True):
                        open_preview_modal(hero)
                with c3:
                    is_fav = hero['link'] in st.session_state.bookmarks
                    fav_icon = "⭐ Retirer" if is_fav else "☆ Favori"
                    if st.button(fav_icon, key=f"fav_hero_{hero['id']}", use_container_width=True):
                        if is_fav:
                            st.session_state.bookmarks.remove(hero['link'])
                        else:
                            st.session_state.bookmarks.add(hero['link'])
                        st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

    # 2. AFFICHAGE DES ARTICLES (Grille vs Liste Compacte)
    grid_articles = filtered_articles[start_idx:]
    
    if view_mode == "Grille":
        cols = st.columns(3)
        for idx, article in enumerate(grid_articles):
            col = cols[idx % 3]
            cat_color = CATEGORY_COLORS.get(article['category'], "#64748B")
            with col:
                with st.container(border=True):
                    st.markdown(
                        f'<img src="{article["image_url"]}" style="width:100%; height:180px; object-fit:cover; border-radius:10px; margin-bottom:8px; display:block;">', 
                        unsafe_allow_html=True
                    )
                    st.markdown(f'<span class="cat-badge" style="background-color:{cat_color};">{article["category"]}</span>', unsafe_allow_html=True)
                    st.caption(f"📍 **{article['source']}** • {article['relative_date']}")
                    st.markdown(f"**{article['title']}**")
                    st.write(article['summary_short'])
                    
                    c_read, c_prev, c_fav = st.columns([1.5, 1, 0.8])
                    with c_read:
                        st.link_button("Lire", article['link'], use_container_width=True)
                    with c_prev:
                        if st.button("📖", key=f"prev_{article['id']}", use_container_width=True):
                            open_preview_modal(article)
                    with c_fav:
                        is_fav = article['link'] in st.session_state.bookmarks
                        fav_icon = "⭐" if is_fav else "☆"
                        if st.button(fav_icon, key=f"fav_{article['id']}", use_container_width=True):
                            if is_fav:
                                st.session_state.bookmarks.remove(article['link'])
                            else:
                                st.session_state.bookmarks.add(article['link'])
                            st.rerun()

    else: # MODE LISTE COMPACTE
        for article in grid_articles:
            cat_color = CATEGORY_COLORS.get(article['category'], "#64748B")
            with st.container(border=True):
                c_img, c_content = st.columns([0.8, 3.2])
                with c_img:
                    st.markdown(
                        f'<img src="{article["image_url"]}" style="width:100%; height:110px; object-fit:cover; border-radius:8px; display:block;">', 
                        unsafe_allow_html=True
                    )
                with c_content:
                    st.markdown(f'<span class="cat-badge" style="background-color:{cat_color};">{article["category"]}</span>', unsafe_allow_html=True)
                    st.caption(f"📍 **{article['source']}** • {article['relative_date']} • {article['reading_time']}")
                    st.markdown(f"**{article['title']}**")
                    st.write(article['summary_short'])
                    
                    c_read, c_prev, c_fav = st.columns([1.5, 1, 0.8])
                    with c_read:
                        st.link_button("Lire l'article", article['link'], use_container_width=True)
                    with c_prev:
                        if st.button("📖 Aperçu", key=f"prev_list_{article['id']}", use_container_width=True):
                            open_preview_modal(article)
                    with c_fav:
                        is_fav = article['link'] in st.session_state.bookmarks
                        fav_icon = "⭐ Retirer" if is_fav else "☆ Favori"
                        if st.button(fav_icon, key=f"fav_list_{article['id']}", use_container_width=True):
                            if is_fav:
                                st.session_state.bookmarks.remove(article['link'])
                            else:
                                st.session_state.bookmarks.add(article['link'])
                            st.rerun()

elif selected_category == "⭐ Favoris":
    st.info("Vous n'avez pas encore d'articles enregistrés dans vos favoris. Cliquez sur le bouton ☆ sous un article pour l'ajouter ici.")
else:
    st.info("Aucun article trouvé pour ces critères.")
