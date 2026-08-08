import streamlit as st
import feedparser
import re
import requests
import hashlib
import json
import urllib.parse
from datetime import datetime, timezone
import time

# Configuration de la page Streamlit avec icône d'onglet
st.set_page_config(
    page_title="Krea — L'Actu Créative & IA",
    page_icon="☆",
    layout="wide"
)

# Style CSS : Mesh gradient, Glassmorphism & Responsive
st.markdown("""
<style>
    /* Masquer le header Streamlit et le footer par défaut */
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
    
    /* Dynamic Loading Indicator / Status Widget / Spinner */
    div[data-testid="stStatusWidget"], 
    div[data-testid="stSpinner"], 
    div[data-testid="stNotification"],
    div[data-testid="stToast"],
    div[data-baseweb="toast"],
    div[data-baseweb="spinner"],
    .stSpinner,
    div[data-testid="stStatusWidget"] > div {
        background-color: #0f172a !important;
        background: #0f172a !important;
        backdrop-filter: blur(12px) !important;
        color: #f8fafc !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 12px !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6) !important;
    }
    
    div[data-testid="stStatusWidget"] *, 
    div[data-testid="stSpinner"] *,
    .stSpinner *,
    div[data-testid="stSpinner"] p, 
    div[data-testid="stSpinner"] span {
        color: #ffffff !important;
        fill: #ffffff !important;
        font-weight: 600 !important;
        background-color: transparent !important;
    }

    /* Labels de tous les champs */
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

    /* Cards standard */
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

    /* Style spécifique pour les articles déjà lus */
    .article-read {
        opacity: 0.65;
        filter: grayscale(15%);
    }

    /* Mise en évidence bloc À LA UNE */
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

    /* Règles Smartphone */
    @media (max-width: 768px) {
        div[data-testid="stColumn"]:has(#view-mode-marker) {
            display: none !important;
        }

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

        div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            gap: 4px !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
            width: auto !important;
            flex: 1 1 0 !important;
            min-width: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        
        div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stHorizontalBlock"] button {
            font-size: 0.75rem !important;
            padding: 4px 2px !important;
            white-space: nowrap !important;
        }
    }

    /* Badges */
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

    .read-badge {
        font-size: 0.65rem;
        font-weight: 700;
        padding: 2px 7px;
        border-radius: 10px;
        background-color: transparent;
        color: #94a3b8;
        border: 1px solid rgba(148, 163, 184, 0.4);
        display: inline-block;
        margin-left: 6px;
    }

    .hero-badge {
        background-color: transparent;
        color: #F472B6;
        border: 1px solid #F472B6;
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

# Dialog pour installer l'application
@st.dialog("⤓ Installer Krea sur votre appareil")
def show_install_instructions():
    st.write("Pour garder un accès rapide à Krea, ajoutez-le à votre écran d'accueil :")
    st.markdown("""
    **🍎 Sur iPhone / iPad (Safari)**:
    1. Appuyez sur le bouton de **Partage** (carré avec une flèche vers le haut).
    2. Choisissez **"Sur l'écran d'accueil"**.
    3. Remplacez le nom par **"Krea"** puis validez avec **"Ajouter"**.

    **🖥️ Sur Mac (Safari)**:
    1. Dans Safari, cliquez sur le menu **Fichier** > **"Ajouter au Dock..."**.
    2. Remplacez le nom par **"Krea"** puis validez avec **"Ajouter"**.

    **🤖 Sur Android (Chrome)**:
    1. Appuyez sur les **trois points** ⋮ dans le coin supérieur droit.
    2. Sélectionnez **"Installer l'application"** ou **"Ajouter à l'écran d'accueil"**.

    **💻 Sur PC / Mac (Chrome / Edge)**:
    1. Cliquez sur les **trois points** ⋮ dans la barre d'adresse du navigateur.
    2. Cherchez **"Enregistrer et partager"** ou **"Applications"**.
    3. Choisissez **"Installer cette application"** ou **"Créer un raccourci"**.
    """)

# Initialisation des états de session
if "bookmarks" not in st.session_state:
    st.session_state.bookmarks = set()
if "read_articles" not in st.session_state:
    st.session_state.read_articles = set()
if "category_views" not in st.session_state:
    st.session_state.category_views = {}
if "articles_limit" not in st.session_state:
    st.session_state.articles_limit = 12
if "search_input" not in st.session_state:
    st.session_state.search_input = ""

# En-tête : Logo SVG Krea (étoile rose) + Bouton Installation
col_logo, col_inst = st.columns([6, 1])
with col_logo:
    st.markdown("""
    <div style="margin-top: 0px; margin-bottom: 10px; filter: drop-shadow(0px 8px 24px rgba(139, 92, 246, 0.25));">
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

with col_inst:
    st.write("")
    if st.button("⤓ Installer l'app"):
        show_install_instructions()

st.markdown("<br>", unsafe_allow_html=True)

# Sources RSS
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

EXCLUDED_CATEGORIES = [
    "developpement-personnel", "sante", "bien-etre", "politique", 
    "fait-divers", "societe", "lifestyle", "psycho", "sante-bien-etre"
]

KEYWORDS = {
    "Photoshop": ["photoshop", "psd", "retouche"],
    "Lightroom": ["lightroom", "raw", "developpement photo"],
    "InDesign": ["indesign", "mise en page", "typographie", "edition"],
    "Illustrator": ["illustrator", "vectoriel", "vecteur", "dessin"],
    "Photo": ["photo", "photographie", "appareil photo", "objectif photo", "capteur", "shooting", "portrait", "portraits", "paysage photo"],
    "Expos photos": ["exposition", "expositions", "expo photo", "galerie", "vernissage", "retrospective"],
    "Graphisme": ["design graphique", "graphiste", "logo", "branding", "charte graphique"],
    "Tutoriels": ["tuto", "tutoriel", "guide technique", "astuce photoshop", "formation design", "cours photo"],
    "AI": ["ia", "intelligence artificielle", "midjourney", "firefly", "chatgpt", "dall-e", "stable diffusion", "generative", "sora", "copilot"]
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
    return f"🕒 {mins} min"

def detect_article_category(title, summary, source_name=""):
    text = f"{title} {summary}".lower()
    
    for cat in ["Photoshop", "Lightroom", "InDesign", "Illustrator", "Expos photos", "Tutoriels", "Graphisme"]:
        for kw in KEYWORDS[cat]:
            if re.search(r'\b' + re.escape(kw) + r'\b', text):
                return cat

    for kw in KEYWORDS["AI"]:
        if re.search(r'\b' + re.escape(kw) + r'\b', text):
            return "AI"

    for kw in KEYWORDS["Photo"]:
        if re.search(r'\b' + re.escape(kw) + r'\b', text):
            return "Photo"

    photo_sources = ["L'Œil de la Photographie", "Phototrend", "Apprendre la Photo", "OuiOui Photo", "Graine de Photographe", "Blind Magazine", "Les Numériques (Photo)"]
    if source_name in photo_sources:
        return "Photo"

    return "Général"

def get_unique_fallback(title):
    seed = int(hashlib.md5(title.encode('utf-8')).hexdigest(), 16) % 1000
    return f"https://picsum.photos/seed/{seed}/600/350"

@st.dialog("▤ Aperçu de l'article")
def open_preview_modal(article):
    st.session_state.read_articles.add(article["id"])
    
    # Suivi des recommandations contextuelles
    cat = article.get("category", "Général")
    st.session_state.category_views[cat] = st.session_state.category_views.get(cat, 0) + 1

    if article.get("image_url"):
        st.markdown(
            f'<img src="{article["image_url"]}" style="width:100%; max-height:300px; object-fit:cover; border-radius:12px; margin-bottom:12px;">', 
            unsafe_allow_html=True
        )
    st.markdown(f"### {article['title']}")
    st.caption(f"⌖ **{article['source']}** • {article['relative_date']} • {article['reading_time']}")
    st.write(article['summary'])
    st.divider()
    
    st.markdown("**⎘ Copier le lien direct :**")
    st.code(article['link'], language=None)
    
    encoded_url = urllib.parse.quote(article['link'])
    encoded_title = urllib.parse.quote(article['title'])
    
    col_open, col_wa, col_x = st.columns([2, 1, 1])
    with col_open:
        st.link_button("↗ Ouvrir le site d'origine", article['link'], use_container_width=True)
    with col_wa:
        st.link_button("✉ WhatsApp", f"https://api.whatsapp.com/send?text={encoded_title}%20{encoded_url}", use_container_width=True)
    with col_x:
        st.link_button("↗ Share 𝕏", f"https://twitter.com/intent/tweet?text={encoded_title}&url={encoded_url}", use_container_width=True)

@st.cache_data(ttl=1800, show_spinner="Chargement de l'actualité Krea...")
def fetch_all_feeds():
    articles = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    for feed in SOURCES:
        try:
            resp = requests.get(feed["url"], headers=headers, timeout=5)
            if resp.status_code != 200:
                continue
            parsed = feedparser.parse(resp.content)
            for entry in parsed.entries[:8]:
                link = entry.get("link", "#")
                if any(bad_cat in link.lower() for bad_cat in EXCLUDED_CATEGORIES):
                    continue

                title = clean_text(entry.get("title", ""))
                summary = clean_text(entry.get("summary", entry.get("description", "")))
                dt = parse_entry_date(entry)
                extracted_url = extract_image_url(entry)
                
                cat = detect_article_category(title, summary, feed["name"])
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

all_fetched = fetch_all_feeds()

# Mise en cache offline des favoris dans le localStorage du navigateur
fav_articles_data = [a for a in all_fetched if a["link"] in st.session_state.bookmarks]
favs_json_str = json.dumps(fav_articles_data, default=str)
offline_cache_script = f"""
<script>
    try {{
        localStorage.setItem('krea_offline_favorites', {json.dumps(favs_json_str)});
    }} catch(e) {{}}
</script>
"""
st.markdown(offline_cache_script, unsafe_allow_html=True)

categories = ["Tous", "Photoshop", "Lightroom", "InDesign", "Illustrator", "AI", "Graphisme", "Photo", "Tutoriels", "Expos photos", "☆ Favoris"]
selected_category = st.radio("Filtrer par catégorie :", categories, horizontal=True)

col_source, col_search, col_view, col_refresh = st.columns([1.5, 2, 1.2, 0.8])
with col_source:
    source_options = ["Toutes les sources"] + [s["name"] for s in SOURCES]
    selected_source = st.selectbox("Source :", source_options)
with col_search:
    search_query = st.text_input("⌕ Mot-clé :", value=st.session_state.search_input, placeholder="ex: tutoriel, midjourney, portrait...")
with col_view:
    st.markdown('<div id="view-mode-marker"></div>', unsafe_allow_html=True)
    view_mode = st.radio("Affichage :", ["Grille", "Liste compacte"], horizontal=True)
with col_refresh:
    st.write("")
    st.write("")
    if st.button("↻ Actualiser", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.write("✦ **Tendances du moment :**")
tag_cols = st.columns(6)
tags = ["Midjourney", "Photoshop", "Tutoriel", "Portrait", "Lightroom", "Exposition"]
for idx, tag in enumerate(tags):
    with tag_cols[idx]:
        if st.button(f"#{tag}", key=f"trend_tag_{idx}", use_container_width=True):
            st.session_state.search_input = tag
            st.rerun()

st.divider()

filtered_articles = []
for art in all_fetched:
    text_to_check = f"{art['title']} {art['summary']}".lower()
    if selected_category == "☆ Favoris":
        if art["link"] not in st.session_state.bookmarks: continue
        cat_match = True
    elif selected_category == "Tous": cat_match = True
    elif selected_category == "Expos photos":
        expos_sources = ["L'Œil de la Photographie", "Blind Magazine", "Graine de Photographe"]
        is_expos_source = any(src in art["source"] for src in expos_sources)
        kw_list = KEYWORDS.get("Expos photos", [])
        kw_match = any(kw in text_to_check for kw in kw_list)
        cat_match = is_expos_source or kw_match
    else:
        kw_list = KEYWORDS.get(selected_category, [])
        cat_match = any(re.search(r'\b' + re.escape(kw) + r'\b', text_to_check) for kw in kw_list)
    if selected_source != "Toutes les sources" and art["source"] != selected_source: source_match = False
    else: source_match = True
    if not search_query.strip(): search_match = True
    else: search_match = search_query.lower().strip() in text_to_check
    if cat_match and search_match and source_match:
        art_copy = art.copy()
        art_copy["summary_short"] = art["summary"][:160] + "..." if len(art["summary"]) > 160 else art["summary"]
        filtered_articles.append(art_copy)

# Recommandations contextuelles : tri dynamique selon les centres d'intérêt récents
if selected_category == "Tous" and not search_query.strip() and st.session_state.category_views:
    filtered_articles.sort(
        key=lambda x: (st.session_state.category_views.get(x["category"], 0), x["date"]), 
        reverse=True
    )

if selected_category == "☆ Favoris" and filtered_articles:
    col_fav_title, col_fav_json, col_fav_md = st.columns([2, 1, 1])
    with col_fav_title: 
        st.subheader(f"☆ Vos articles favoris ({len(filtered_articles)})")
    with col_fav_json:
        json_favs = json.dumps(filtered_articles, indent=2, ensure_ascii=False)
        st.download_button("⤓ Exporter (JSON)", data=json_favs, file_name="favoris_krea.json", mime="application/json", use_container_width=True)
    with col_fav_md:
        md_content = "# ☆ Krea — Revue de Presse\n\n"
        for art in filtered_articles:
            md_content += f"### [{art['title']}]({art['link']})\n"
            md_content += f"**Source:** {art['source']} • **Catégorie:** {art['category']} • **Date:** {art['relative_date']}\n\n"
            md_content += f"> {art['summary']}\n\n---\n\n"
        st.download_button("⎘ Revue de Presse (MD)", data=md_content, file_name="revue_de_presse_krea.md", mime="text/markdown", use_container_width=True)

if filtered_articles:
    show_hero = (selected_category == "Tous" and selected_source == "Toutes les sources" and not search_query.strip() and view_mode == "Grille")
    start_idx = 0
    if show_hero and len(filtered_articles) > 0:
        hero = filtered_articles[0]
        start_idx = 1
        cat_color = CATEGORY_COLORS.get(hero['category'], "#64748B")
        is_hero_read = hero['id'] in st.session_state.read_articles
        hero_read_class = "article-read" if is_hero_read else ""
        
        with st.container(border=True):
            st.markdown(f'<div class="{hero_read_class}">', unsafe_allow_html=True)
            st.markdown('<span class="hero-badge">✦ À LA UNE</span>', unsafe_allow_html=True)
            if is_hero_read:
                st.markdown('<span class="read-badge">✓ Lu</span>', unsafe_allow_html=True)
            col_hero_img, col_hero_text = st.columns([1.2, 1])
            with col_hero_img:
                st.markdown(f'<img src="{hero["image_url"]}" style="width:100%; height:260px; object-fit:cover; border-radius:12px; display:block;">', unsafe_allow_html=True)
            with col_hero_text:
                st.markdown(f'<span class="cat-badge" style="background-color:{cat_color};">{hero["category"]}</span>', unsafe_allow_html=True)
                st.caption(f"⌖ **{hero['source']}** • {hero['relative_date']} • {hero['reading_time']}")
                st.markdown(f"### {hero['title']}")
                st.write(hero['summary'][:220] + "..." if len(hero['summary']) > 220 else hero['summary'])
                c1, c2, c3 = st.columns([1.5, 1, 1])
                with c1: 
                    st.link_button("Lire l'article", hero['link'], use_container_width=True)
                with c2:
                    if st.button("Aperçu", key=f"prev_hero_{hero['id']}", use_container_width=True): 
                        open_preview_modal(hero)
                with c3:
                    is_fav = hero['link'] in st.session_state.bookmarks
                    fav_icon = "☆ Retirer" if is_fav else "☆ Favori"
                    if st.button(fav_icon, key=f"fav_hero_{hero['id']}", use_container_width=True):
                        if is_fav: st.session_state.bookmarks.remove(hero['link'])
                        else: st.session_state.bookmarks.add(hero['link'])
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    grid_articles = filtered_articles[start_idx:]
    visible_articles = grid_articles[:st.session_state.articles_limit]
    
    if view_mode == "Grille":
        cols = st.columns(3)
        for idx, article in enumerate(visible_articles):
            col = cols[idx % 3]
            cat_color = CATEGORY_COLORS.get(article['category'], "#64748B")
            is_read = article['id'] in st.session_state.read_articles
            read_badge = '<span class="read-badge">✓ Lu</span>' if is_read else ''
            read_class = "article-read" if is_read else ""
            
            with col:
                with st.container(border=True):
                    st.markdown(f'<div class="{read_class}">', unsafe_allow_html=True)
                    st.markdown(f'<img src="{article["image_url"]}" style="width:100%; height:180px; object-fit:cover; border-radius:10px; margin-bottom:8px; display:block;">', unsafe_allow_html=True)
                    st.markdown(f'<span class="cat-badge" style="background-color:{cat_color};">{article["category"]}</span> {read_badge}', unsafe_allow_html=True)
                    st.caption(f"⌖ **{article['source']}** • {article['relative_date']}")
                    st.markdown(f"**{article['title']}**")
                    st.write(article['summary_short'])
                    c_read, c_prev, c_fav = st.columns([1.5, 1, 0.8])
                    with c_read: st.link_button("Lire", article['link'], use_container_width=True)
                    with c_prev:
                        if st.button("Aperçu", key=f"prev_{article['id']}", use_container_width=True): open_preview_modal(article)
                    with c_fav:
                        is_fav = article['link'] in st.session_state.bookmarks
                        fav_icon = "☆" if is_fav else "☆"
                        if st.button(fav_icon, key=f"fav_{article['id']}", use_container_width=True):
                            if is_fav: st.session_state.bookmarks.remove(article['link'])
                            else: st.session_state.bookmarks.add(article['link'])
                            st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
    else:
        for article in visible_articles:
            cat_color = CATEGORY_COLORS.get(article['category'], "#64748B")
            is_read = article['id'] in st.session_state.read_articles
            read_badge = '<span class="read-badge">✓ Lu</span>' if is_read else ''
            read_class = "article-read" if is_read else ""
            
            with st.container(border=True):
                st.markdown(f'<div class="{read_class}">', unsafe_allow_html=True)
                c_img, c_content = st.columns([0.8, 3.2])
                with c_img:
                    st.markdown(f'<img src="{article["image_url"]}" style="width:100%; height:110px; object-fit:cover; border-radius:8px; display:block;">', unsafe_allow_html=True)
                with c_content:
                    st.markdown(f'<span class="cat-badge" style="background-color:{cat_color};">{article["category"]}</span> {read_badge}', unsafe_allow_html=True)
                    st.caption(f"⌖ **{article['source']}** • {article['relative_date']} • {article['reading_time']}")
                    st.markdown(f"**{article['title']}**")
                    st.write(article['summary_short'])
                    c_read, c_prev, c_fav = st.columns([1.5, 1, 0.8])
                    with c_read: st.link_button("Lire l'article", article['link'], use_container_width=True)
                    with c_prev:
                        if st.button("Aperçu", key=f"prev_list_{article['id']}", use_container_width=True): open_preview_modal(article)
                    with c_fav:
                        is_fav = article['link'] in st.session_state.bookmarks
                        fav_icon = "☆ Retirer" if is_fav else "☆ Favori"
                        if st.button(fav_icon, key=f"fav_list_{article['id']}", use_container_width=True):
                            if is_fav: st.session_state.bookmarks.remove(article['link'])
                            else: st.session_state.bookmarks.add(article['link'])
                            st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    # Bouton de pagination "Charger plus"
    if len(grid_articles) > st.session_state.articles_limit:
        st.markdown("<br>", unsafe_allow_html=True)
        col_m1, col_m2, col_m3 = st.columns([1, 1, 1])
        with col_m2:
            if st.button("⤓ Charger plus d'articles", use_container_width=True):
                st.session_state.articles_limit += 12
                st.rerun()

elif selected_category == "☆ Favoris":
    st.info("Vous n'avez pas encore d'articles enregistrés dans vos favoris.")
else:
    st.info("Aucun article trouvé pour ces critères.")

# Footer centré avec grand k incliné et étoile rose conservée
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
    <p style="color: #94A3B8; font-size: 0.85rem; font-weight: 600; letter-spacing: 0.5px; margin: 0;">by Graphis Studio</p>
</div>
""", unsafe_allow_html=True)
