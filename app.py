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
from collections import Counter

# SVG pur HD du logo Krea (cartes violet/cyan, k incliné, étoile rose)
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

# SVG dédié pour illustration d'article manquante (ratio 600x350 anti-rognage)
KREA_PLACEHOLDER_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 350">
  <defs>
    <linearGradient id="ph_g1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#8B5CF6"/>
      <stop offset="100%" stop-color="#2563EB"/>
    </linearGradient>
    <linearGradient id="ph_g2" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#06B6D4" stop-opacity="0.6"/>
      <stop offset="100%" stop-color="#3B82F6" stop-opacity="0.3"/>
    </linearGradient>
    <radialGradient id="ph_bg" cx="50%" cy="50%" r="75%">
      <stop offset="0%" stop-color="#1e293b"/>
      <stop offset="100%" stop-color="#0b0f19"/>
    </radialGradient>
  </defs>
  <rect width="600" height="350" fill="url(#ph_bg)"/>
  <g transform="translate(250, 125)">
    <rect x="18" y="18" width="62" height="62" rx="14" fill="url(#ph_g2)" transform="rotate(-6 49 49)"/>
    <rect x="12" y="12" width="62" height="62" rx="14" fill="url(#ph_g1)"/>
    <text x="43" y="56" font-family="sans-serif" font-weight="900" font-size="44" fill="#FFFFFF" text-anchor="middle" transform="rotate(-10 43 56)">k</text>
    <path d="M 72 6 Q 72 14 80 14 Q 72 14 72 22 Q 72 14 64 14 Q 72 14 72 6 Z" fill="#F472B6"/>
  </g>
</svg>"""

krea_ph_b64 = base64.b64encode(KREA_PLACEHOLDER_SVG.encode('utf-8')).decode('utf-8')
placeholder_data_uri = f"data:image/svg+xml;base64,{krea_ph_b64}"

# Configuration de la page Streamlit
st.set_page_config(
    page_title="Krea — L'Actu Créative & IA",
    page_icon="🎨",
    layout="wide"
)

# Injection du favicon Krea et détection du mode PWA
st.markdown(
    f"""<head><link rel="icon" type="image/svg+xml" href="{svg_data_uri}"><link rel="shortcut icon" type="image/svg+xml" href="{svg_data_uri}"><link rel="apple-touch-icon" href="{svg_data_uri}"></head><script>(function(){{var svgUri="{svg_data_uri}";function setFavicon(){{var doc=window.parent?window.parent.document:document;if(!doc)return;var links=doc.querySelectorAll("link[rel*='icon']");links.forEach(function(l){{l.href=svgUri;l.type="image/svg+xml";}});if(links.length===0){{var link=doc.createElement('link');link.rel='shortcut icon';link.type="image/svg+xml";link.href=svgUri;doc.head.appendChild(link);}}}}if(window.matchMedia('(display-mode: standalone)').matches||window.navigator.standalone||document.referrer.includes('android-app://')){{document.documentElement.classList.add('pwa-standalone');}}setFavicon();setTimeout(setFavicon,300);setTimeout(setFavicon,1000);}})();</script>""",
    unsafe_allow_html=True
)

# Style CSS (chaîne brute non-f-string pour éviter les conflits de syntaxe Python)
custom_css = """<style>
    html {
        scroll-behavior: smooth;
    }
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    div[data-testid="stDecoration"] {display: none;}

    .main .block-container, div[data-testid="stMainBlockContainer"] {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
    }

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

    /* Masque le bouton d'installation si l'application est ouverte en mode PWA installé */
    @media (display-mode: standalone) {
        div[data-testid="stColumn"]:has(#pwa-install-btn) {
            display: none !important;
        }
    }
    .pwa-standalone div[data-testid="stColumn"]:has(#pwa-install-btn) {
        display: none !important;
    }
    
    div[data-testid="stWidgetLabel"] p, label p, label {
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
    }

    div[data-testid="stRadio"] {
        background-color: rgba(30, 41, 59, 0.75) !important;
        backdrop-filter: blur(12px) !important;
        padding: 14px 20px !important;
        border-radius: 14px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.25);
    }
    div[data-testid="stRadio"] label { color: #ffffff !important; font-weight: 700 !important; }

    div[data-testid="stTextInput"] input {
        background-color: #f8fafc !important;
        color: #0f172a !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
    }
    div[data-baseweb="select"] > div {
        background-color: #f8fafc !important;
        color: #0f172a !important;
        border-radius: 10px !important;
    }
    div[data-baseweb="select"] * { color: #0f172a !important; }

    div[data-testid="stLinkButton"] a, div[data-testid="stButton"] button {
        background-color: rgba(30, 41, 59, 0.85) !important;
        color: #f1f5f9 !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.25s ease !important;
    }
    div[data-testid="stLinkButton"] a:hover, div[data-testid="stButton"] button:hover {
        border-color: #F472B6 !important;
        color: #F472B6 !important;
        background-color: rgba(30, 41, 59, 0.95) !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #161e2e !important;
        border: 1px solid #1e293b !important;
        border-radius: 14px !important;
        padding: 14px !important;
        transition: transform 0.25s ease, box-shadow 0.25s ease !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-5px) !important;
        border-color: #8b5cf6 !important;
        box-shadow: 0 12px 28px -5px rgba(139, 92, 246, 0.25) !important;
    }

    div[data-testid="stSpinner"], .stSpinner {
        background-color: #161e2e !important;
        color: #f1f5f9 !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 14px !important;
        padding: 16px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3) !important;
    }
    div[data-testid="stSpinner"] *, .stSpinner * {
        color: #f1f5f9 !important;
        background-color: transparent !important;
        font-weight: 600 !important;
    }

    @media (max-width: 768px) {
        div[data-testid="stHorizontalBlock"]:has(> div[data-testid="stColumn"]:nth-child(6)) {
            flex-direction: row !important;
            flex-wrap: wrap !important;
            gap: 6px !important;
        }
        div[data-testid="stHorizontalBlock"]:has(> div[data-testid="stColumn"]:nth-child(6)) > div[data-testid="stColumn"] {
            flex: 1 1 31% !important;
            min-width: 31% !important;
        }
    }

    .article-read { opacity: 0.65; filter: grayscale(15%); }
    .cat-badge { font-size: 0.70rem; font-weight: 800; padding: 3px 9px; border-radius: 12px; text-transform: uppercase; color: #0f172a; display: inline-block; margin-bottom: 6px; }
    .read-badge { font-size: 0.65rem; font-weight: 700; padding: 2px 7px; border-radius: 10px; color: #94a3b8; border: 1px solid rgba(148, 163, 184, 0.4); display: inline-block; margin-left: 6px; }
    .hero-badge { background-color: transparent; color: #F472B6; border: 1px solid #F472B6; font-weight: 800; font-size: 0.75rem; padding: 4px 12px; border-radius: 20px; text-transform: uppercase; display: inline-block; margin-bottom: 10px; }
</style>"""

st.markdown(custom_css, unsafe_allow_html=True)

@st.dialog("⤓ Installer Krea sur votre appareil")
def show_install_instructions():
    st.write("Pour garder un accès rapide à Krea, installez-le sur votre appareil :")
    st.markdown("""
    **💻 Sur PC / Mac (Chrome, Edge, Brave)**:
    1. Cliquez sur l'icône d'installation (écran avec une flèche) ou le menu (⋮) dans la barre d'adresse.
    2. Sélectionnez **"Installer Krea"**.

    **🍎 Sur iPhone / iPad (Safari)**:
    1. Appuyez sur le bouton de **Partage** (carré avec une flèche).
    2. Choisissez **"Sur l'écran d'accueil"** puis validez.

    **🤖 Sur Android (Chrome)**:
    1. Appuyez sur les **trois points** (⋮) du menu.
    2. Sélectionnez **"Installer l'application"** ou **"Ajouter à l'écran d'accueil"**.
    """)

if "bookmarks" not in st.session_state: st.session_state.bookmarks = set()
if "read_articles" not in st.session_state: st.session_state.read_articles = set()
if "category_views" not in st.session_state: st.session_state.category_views = {}
if "articles_limit" not in st.session_state: st.session_state.articles_limit = 12
if "search_input" not in st.session_state: st.session_state.search_input = ""

st.markdown('<div id="top"></div>', unsafe_allow_html=True)

col_logo, col_inst = st.columns([6, 1])
with col_logo:
    st.markdown("""
    <div style="margin-top: 0px; margin-bottom: 10px;">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 450 110" width="440" style="max-width: 100%; height: auto;">
          <defs>
            <linearGradient id="kreaGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="#8B5CF6" /><stop offset="100%" stop-color="#2563EB" />
            </linearGradient>
            <linearGradient id="layerGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="#06B6D4" stop-opacity="0.5"/><stop offset="100%" stop-color="#3B82F6" stop-opacity="0.2"/>
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
    st.markdown('<div id="pwa-install-btn"></div>', unsafe_allow_html=True)
    st.write("")
    if st.button("⤓ Installer"):
        show_install_instructions()

st.markdown("<br>", unsafe_allow_html=True)

SOURCES = [
    {"name": "Numerama Tech", "url": "https://www.numerama.com/tech/feed/"},
    {"name": "01net", "url": "https://www.01net.com/actualites/feed/"},
    {"name": "Photo Actus", "url": "https://www.photoactus.com/blog-feed.xml"},
    {"name": "L'Art de la Photo", "url": "https://lartdelaphoto.fr/feed/"},
    {"name": "Le Monde Informatique - Adobe", "url": "https://www.lemondeinformatique.fr/rss/marque/adobe-68.xml"},
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

EXCLUDED_CATEGORIES = [
    "developpement-personnel", "sante", "bien-etre", "politique", "fait-divers", "societe", "lifestyle", "psycho", 
    "automobile", "automobiles", "voiture", "voitures", "véhicule", "vehicule", "véhicules", "vehicules", "auto", "tesla",
    "bons-plans", "soldes", "promo", "deals", "shopping", "forfaits", "telecom", "crypto", "bitcoin", "finance", "bourse", "immobilier", "electromenager",
    "cinema", "cinéma", "a la tv", "à la tv", "programme tv", "programme-tv", "a la tele", "à la télé", "netflix", "disney+", "prime video", "series", "série", "séries", "box-office"
]

KEYWORDS = {
    "Photoshop": ["photoshop", "psd", "retouche"],
    "Lightroom": ["lightroom", "raw", "developpement photo"],
    "Adobe": ["adobe", "creative cloud", "indesign", "illustrator", "acrobat", "premiere", "after effects", "xd", "lightroom", "photoshop"],
    "Photo": ["photo", "photographie", "appareil photo", "objectif", "portrait", "paysage"],
    "Expos photos": ["exposition", "expositions", "expo photo", "galerie", "vernissage"],
    "Graphisme": ["design graphique", "graphiste", "logo", "branding", "charte"],
    "Tutoriels": ["tuto", "tutoriel", "guide technique", "astuce", "formation"],
    "AI": ["ia", "intelligence artificielle", "midjourney", "firefly", "chatgpt", "dall-e", "stable diffusion"]
}

if "Illustrator" in KEYWORDS:
    del KEYWORDS["Illustrator"]
if "InDesign" in KEYWORDS:
    del KEYWORDS["InDesign"]

CATEGORY_COLORS = {
    "Photoshop": "#38BDF8", "Lightroom": "#60A5FA", "Adobe": "#FF0000",
    "Photo": "#F59E0B", "Graphisme": "#EC4899", "Tutoriels": "#10B981", 
    "Expos photos": "#E11D48", "AI": "#A855F7", "Général": "#64748B"
}

def clean_text(raw_html):
    if not raw_html: return ""
    return re.sub(r'\s+', ' ', re.sub(r'<.*?>', ' ', raw_html)).strip()

def clean_url(url):
    if not url: return None
    url = url.strip()
    if url.startswith("//"):
        url = "https:" + url
    if url.startswith("http"):
        u_low = url.lower()
        if any(b in u_low for b in ["gravatar.com", "pixel", "1x1", "blank.gif", "tracker", "default-avatar"]): 
            return None
        return url
    return None

def extract_image_url(entry):
    # 1. Vérification des structures d'enclos et contenus médias RSS
    if 'media_content' in entry:
        for m in entry.media_content:
            u = clean_url(m.get('url'))
            if u: return u
    if 'media_thumbnail' in entry:
        for m in entry.media_thumbnail:
            u = clean_url(m.get('url'))
            if u: return u
    if 'enclosures' in entry:
        for enc in entry.enclosures:
            u = clean_url(enc.get('href') or enc.get('url'))
            if u: return u
    if 'links' in entry:
        for link in entry.links:
            href = link.get('href')
            if href:
                u = clean_url(href)
                if u and any(ext in u.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                    return u

    # 2. Parsing de tout le contenu HTML présent dans le flux RSS
    html_sources = []
    for c in entry.get('content', []):
        if isinstance(c, dict):
            html_sources.append(c.get('value', ''))
        elif isinstance(c, str):
            html_sources.append(c)
            
    if hasattr(entry, 'content_encoded'):
        html_sources.append(entry.content_encoded)
    if 'summary_detail' in entry and isinstance(entry.summary_detail, dict):
        html_sources.append(entry.summary_detail.get('value', ''))

    html_sources.extend([entry.get('summary', ''), entry.get('description', '')])

    for text_src in html_sources:
        if not text_src: continue
        
        # Extraction depuis attributs d'images (standard, lazy-loading, WordPress Jetpack)
        img_attrs = re.findall(r'<img [^>]*(?:src|data-src|data-lazy-src|data-orig-file|data-large-file)=["\']([^"\']+)["\']', text_src, re.IGNORECASE)
        for src in img_attrs:
            u = clean_url(src)
            if u and not u.startswith("data:"):
                return u

        # Extraction depuis attributs srcset
        srcset_matches = re.findall(r'srcset=["\']([^"\']+)["\']', text_src, re.IGNORECASE)
        for srcset in srcset_matches:
            urls = [s.strip().split()[0] for s in srcset.split(',') if s.strip()]
            for src in urls:
                u = clean_url(src)
                if u and not u.startswith("data:"):
                    return u

        # Recherche directe d'URLs d'images dans le texte HTML
        url_matches = re.findall(r'https?://[^\s<>"\']+\.(?:jpg|jpeg|png|webp)(?:\?[^\s<>"\']*)?', text_src, re.IGNORECASE)
        for um in url_matches:
            u = clean_url(um)
            if u: return u

    return None

def parse_entry_date(entry):
    for field in ['published_parsed', 'updated_parsed']:
        if hasattr(entry, field) and getattr(entry, field):
            return datetime.fromtimestamp(time.mktime(getattr(entry, field)), tz=timezone.utc)
    return datetime.now(timezone.utc)

def format_relative_date(dt):
    diff = datetime.now(timezone.utc) - dt
    secs = int(diff.total_seconds())
    if secs < 60: return "À l'instant"
    mins = secs // 60
    if mins < 60: return f"Il y a {mins} min"
    hours = mins // 60
    if hours < 24: return f"Il y a {hours} h"
    days = hours // 24
    if days < 7: return f"Il y a {days} j"
    return dt.strftime("%d/%m/%Y")

def detect_category(title, summary, source_name):
    text = f"{title} {summary}".lower()
    for cat, kws in KEYWORDS.items():
        for kw in kws:
            if re.search(r'\b' + re.escape(kw) + r'\b', text):
                return cat
    if source_name in ["Phototrend", "Apprendre la Photo", "OuiOui Photo", "Graine de Photographe", "Blind Magazine", "L'Art de la Photo", "Photo Actus"]:
        return "Photo"
    return "Général"

@st.dialog("▤ Aperçu de l'article")
def open_preview_modal(article):
    st.session_state.read_articles.add(article["id"])
    cat = article.get("category", "Général")
    st.session_state.category_views[cat] = st.session_state.category_views.get(cat, 0) + 1

    if article.get("image_url"):
        st.markdown(f'<img src="{article["image_url"]}" referrerpolicy="no-referrer" style="width:100%; max-height:300px; object-fit:cover; border-radius:12px; margin-bottom:12px;">', unsafe_allow_html=True)
    st.markdown(f"### {article['title']}")
    st.caption(f"⌖ **{article['source']}** • {article['relative_date']} • 🕒 {max(1, len(article['summary'].split()) // 35)} min")
    st.write(article['summary'])
    
    st.caption("📋 Copier le lien de l'article :")
    st.code(article['link'], language="text")
    
    st.divider()
    
    encoded_url = urllib.parse.quote(article['link'])
    encoded_title = urllib.parse.quote(article['title'])
    
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: st.link_button("↗ Ouvrir le site", article['link'], use_container_width=True)
    with c2: st.link_button("✉ WhatsApp", f"https://api.whatsapp.com/send?text={encoded_title}%20{encoded_url}", use_container_width=True)
    with c3: st.link_button("↗ 𝕏", f"https://twitter.com/intent/tweet?text={encoded_title}&url={encoded_url}", use_container_width=True)

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_all_feeds():
    articles = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    for feed in SOURCES:
        try:
            resp = requests.get(feed["url"], headers=headers, timeout=4)
            if resp.status_code == 200:
                parsed = feedparser.parse(resp.content)
                for entry in parsed.entries[:4]:
                    link = entry.get("link", "#")
                    title = clean_text(entry.get("title", ""))
                    summary = clean_text(entry.get("summary", entry.get("description", "")))
                    
                    check_text = f"{link} {title}".lower()
                    if any(bad in check_text for bad in EXCLUDED_CATEGORIES): continue
                    
                    dt = parse_entry_date(entry)
                    img = extract_image_url(entry)
                    cat = detect_category(title, summary, feed["name"])
                    
                    articles.append({
                        "id": hashlib.md5((link + title).encode('utf-8')).hexdigest(),
                        "title": title,
                        "link": link,
                        "source": feed["name"],
                        "summary": summary,
                        "date": dt,
                        "relative_date": format_relative_date(dt),
                        "category": cat,
                        "image_url": img if img else placeholder_data_uri,
                        "summary_short": summary[:160] + "..." if len(summary) > 160 else summary
                    })
        except:
            continue
    articles.sort(key=lambda x: x["date"], reverse=True)
    return articles

with st.spinner("Chargement de l'actualité Krea..."):
    all_fetched = fetch_all_feeds()

fav_articles_data = [a for a in all_fetched if a["link"] in st.session_state.bookmarks]
read_articles_list = list(st.session_state.read_articles)
fav_json_str = json.dumps(json.dumps(fav_articles_data, default=str))
read_json_str = json.dumps(json.dumps(read_articles_list))

st.markdown(
    f"""<script>try{{localStorage.setItem('krea_offline_favorites',{fav_json_str});localStorage.setItem('krea_read_articles',{read_json_str});}}catch(e){{}}</script>""",
    unsafe_allow_html=True
)

categories = ["Tous", "Photoshop", "Lightroom", "Adobe", "Graphisme", "Photo", "Tutoriels", "Expos photos", "AI", "☆ Favoris"]
selected_category = st.radio("Filtrer par catégorie :", categories, horizontal=True)

col_source, col_search, col_view, col_refresh = st.columns([1.5, 2, 1.2, 0.8])
with col_source:
    source_options = ["Toutes les sources"] + [s["name"] for s in SOURCES]
    selected_source = st.selectbox("Source :", source_options)
with col_search:
    search_query = st.text_input("⌕ Mot-clé :", value=st.session_state.search_input, placeholder="ex: midjourney, portrait...")
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

all_text = " ".join([f"{art['title']} {art['summary']}" for art in all_fetched]).lower()
extracted_tags = []
for cat, kws in KEYWORDS.items():
    for kw in kws:
        if re.search(r'\b' + re.escape(kw) + r'\b', all_text):
            extracted_tags.append(kw.capitalize())

tag_counts = Counter(extracted_tags)
dynamic_tags = [tag for tag, count in tag_counts.most_common(6)]

fallback_pool = ["Photoshop", "Lightroom", "Adobe", "Graphisme", "Photo", "Tutoriel", "Midjourney", "AI"]
for tag in fallback_pool:
    if len(dynamic_tags) < 6 and tag not in dynamic_tags:
        dynamic_tags.append(tag)
dynamic_tags = dynamic_tags[:6]

tag_cols = st.columns(6)
for idx, tag in enumerate(dynamic_tags):
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
    elif selected_category == "Tous":
        cat_match = True
    else:
        kw_list = KEYWORDS.get(selected_category, [])
        cat_match = any(re.search(r'\b' + re.escape(kw) + r'\b', text_to_check) for kw in kw_list)

    source_match = True if selected_source == "Toutes les sources" else (art["source"] == selected_source)
    search_match = True if not search_query.strip() else (search_query.lower().strip() in text_to_check)

    if cat_match and source_match and search_match:
        filtered_articles.append(art)

if selected_category == "Tous" and not search_query.strip() and st.session_state.category_views:
    filtered_articles.sort(key=lambda x: (st.session_state.category_views.get(x["category"], 0), x["date"]), reverse=True)

if selected_category == "☆ Favoris" and filtered_articles:
    st.subheader(f"☆ Vos favoris ({len(filtered_articles)})")

if filtered_articles:
    show_hero = (selected_category == "Tous" and selected_source == "Toutes les sources" and not search_query.strip() and view_mode == "Grille")
    start_idx = 0
    if show_hero and len(filtered_articles) > 0:
        hero = filtered_articles[0]
        start_idx = 1
        cat_color = CATEGORY_COLORS.get(hero['category'], "#64748B")
        is_hero_read = hero['id'] in st.session_state.read_articles
        
        with st.container(border=True):
            st.markdown(f'<div class="{"article-read" if is_hero_read else ""}">', unsafe_allow_html=True)
            st.markdown('<span class="hero-badge">✦ À LA UNE</span>', unsafe_allow_html=True)
            if is_hero_read: st.markdown('<span class="read-badge">✓ Lu</span>', unsafe_allow_html=True)
            
            c_img, c_txt = st.columns([1.2, 1])
            with c_img: st.markdown(f'<img src="{hero["image_url"]}" referrerpolicy="no-referrer" style="width:100%; height:260px; object-fit:cover; border-radius:12px;">', unsafe_allow_html=True)
            with c_txt:
                st.markdown(f'<span class="cat-badge" style="background-color:{cat_color};">{hero["category"]}</span>', unsafe_allow_html=True)
                st.caption(f"⌖ **{hero['source']}** • {hero['relative_date']}")
                st.markdown(f"### {hero['title']}")
                st.write(hero['summary'][:200] + "...")
                
                c1, c2, c3 = st.columns([1.5, 1, 1])
                with c1: st.link_button("Lire", hero['link'], use_container_width=True)
                with c2:
                    if st.button("Aperçu", key=f"prev_hero_{hero['id']}", use_container_width=True): open_preview_modal(hero)
                with c3:
                    is_fav = hero['link'] in st.session_state.bookmarks
                    if st.button("☆ Retirer" if is_fav else "☆ Favori", key=f"fav_hero_{hero['id']}", use_container_width=True):
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
            
            with col:
                with st.container(border=True):
                    st.markdown(f'<div class="{"article-read" if is_read else ""}">', unsafe_allow_html=True)
                    st.markdown(f'<img src="{article["image_url"]}" referrerpolicy="no-referrer" style="width:100%; height:160px; object-fit:cover; border-radius:10px; margin-bottom:8px;">', unsafe_allow_html=True)
                    st.markdown(f'<span class="cat-badge" style="background-color:{cat_color};">{article["category"]}</span>' + ('<span class="read-badge">✓ Lu</span>' if is_read else ''), unsafe_allow_html=True)
                    st.caption(f"⌖ **{article['source']}** • {article['relative_date']}")
                    st.markdown(f"**{article['title']}**")
                    st.write(article['summary_short'])
                    
                    c_read, c_prev, c_fav = st.columns([1.5, 1, 0.8])
                    with c_read: st.link_button("Lire", article['link'], use_container_width=True)
                    with c_prev:
                        if st.button("Aperçu", key=f"prev_{article['id']}", use_container_width=True): open_preview_modal(article)
                    with c_fav:
                        is_fav = article['link'] in st.session_state.bookmarks
                        if st.button("★" if is_fav else "☆", key=f"fav_{article['id']}", use_container_width=True):
                            if is_fav: st.session_state.bookmarks.remove(article['link'])
                            else: st.session_state.bookmarks.add(article['link'])
                            st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
    else:
        for article in visible_articles:
            cat_color = CATEGORY_COLORS.get(article['category'], "#64748B")
            is_read = article['id'] in st.session_state.read_articles
            
            with st.container(border=True):
                st.markdown(f'<div class="{"article-read" if is_read else ""}">', unsafe_allow_html=True)
                c_img, c_content = st.columns([0.8, 3.2])
                with c_img: st.markdown(f'<img src="{article["image_url"]}" referrerpolicy="no-referrer" style="width:100%; height:100px; object-fit:cover; border-radius:8px;">', unsafe_allow_html=True)
                with c_content:
                    st.markdown(f'<span class="cat-badge" style="background-color:{cat_color};">{article["category"]}</span>' + ('<span class="read-badge">✓ Lu</span>' if is_read else ''), unsafe_allow_html=True)
                    st.caption(f"⌖ **{article['source']}** • {article['relative_date']}")
                    st.markdown(f"**{article['title']}**")
                    st.write(article['summary_short'])
                    
                    c_read, c_prev, c_fav = st.columns([1.5, 1, 0.8])
                    with c_read: st.link_button("Lire", article['link'], use_container_width=True)
                    with c_prev:
                        if st.button("Aperçu", key=f"prev_l_{article['id']}", use_container_width=True): open_preview_modal(article)
                    with c_fav:
                        is_fav = article['link'] in st.session_state.bookmarks
                        if st.button("★ Retirer" if is_fav else "☆ Favori", key=f"fav_l_{article['id']}", use_container_width=True):
                            if is_fav: st.session_state.bookmarks.remove(article['link'])
                            else: st.session_state.bookmarks.add(article['link'])
                            st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    if len(filtered_articles) > st.session_state.articles_limit:
        st.markdown("<br>", unsafe_allow_html=True)
        _, col_m, _ = st.columns([1, 1, 1])
        with col_m:
            if st.button("⤓ Charger plus d'articles", use_container_width=True):
                st.session_state.articles_limit += 12
                st.rerun()
else:
    st.info("Aucun article trouvé pour ces critères.")

st.markdown("""
<div style="text-align: center; margin-top: 60px; padding: 30px 0 10px 0; border-top: 1px solid rgba(255, 255, 255, 0.08);">
    <a href="#top" style="color: #A855F7; text-decoration: none; font-size: 0.85rem; font-weight: 700; display: inline-block; margin-bottom: 20px;">↑ Retour en haut</a>
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
