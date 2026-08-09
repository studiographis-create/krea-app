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
import html
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

# Placement d'Adobe en 1re position pour capturer en priorité toute actualité de la marque
KEYWORDS = {
    "Adobe": ["adobe", "creative cloud", "firefly", "acrobat", "premiere", "after effects", "substance", "adobe express"],
    "Photoshop": ["photoshop", "psd", "retouche"],
    "Lightroom": ["lightroom", "raw", "developpement photo"],
    "Photo": ["photo", "photographie", "appareil photo", "objectif", "portrait", "paysage"],
    "Expos photos": ["exposition", "expositions", "expo photo", "galerie", "vernissage"],
    "Graphisme": ["design graphique", "graphiste", "logo", "branding", "charte"],
    "Tutoriels": ["tuto", "tutoriel", "guide technique", "astuce", "formation"],
    "AI": ["ia", "intelligence artificielle", "midjourney", "chatgpt", "dall-e", "stable diffusion"]
}

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

def get_og_image(link):
    if not link or not link.startswith("http"): return None
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        resp = requests.get(link, headers=headers, timeout=3)
        if resp.status_code == 200:
            og = re.search(r'<metaCe décalage entre la forte actualité de la marque Adobe et l'absence d'article général sur votre site s'explique par des choix de ligne éditoriale et de structure SEO fréquents, mais faciles à corriger.

---

### Pourquoi ce phénomène se produit-il ?

1. **L'intention de recherche est centrée sur les outils, pas sur la marque**
   Les utilisateurs cherchent rarement « Adobe » de façon générique. Ils cherchent des solutions à des besoins précis : *« comment détourer sur Photoshop »*, *« meilleur réglage Lightroom »* ou *« alternative à Premiere Pro »*. La rédaction s'oriente donc naturellement vers les logiciels individuels.
2. **L'actualité d'Adobe est souvent transversale**
   Les grandes annonces d'Adobe (l'intégration de l'IA **Firefly**, les changements de tarifs du Creative Cloud, la révision des conditions d'utilisation ou les conférences Adobe MAX) touchent plusieurs logiciels à la fois. Sans catégorie ou page chapeau dédiée, ces sujets tombent dans un "no man's land" éditorial.
3. **Une taxonomie CMS en silos**
   Dans la plupart des sites (WordPress, Ghost, etc.), *Photoshop* et *Lightroom* sont créés comme des catégories indépendantes. Faute d'une catégorie mère « Adobe » ou d'une page pilier (*Pillar Page*), le contenu reste fragmenté par outil.

---

### Comment y remédier ?

#### 1. Créer une Page Pilier (*Pillar Page*) « Écosystème Adobe »
Rédigez un article encyclopédique et structuré qui sert de hub central pour la marque.
* **Contenu à inclure :** Présentation du groupe, panorama de la suite Creative Cloud, modèle d'abonnement, stratégie autour de l'IA (Adobe Firefly) et actualités majeures.
* **Maillage interne :** Faites pointer cette page vers vos guides spécifiques (*Photoshop*, *Lightroom*) et, inversement, ajoutez un lien vers cette page pilier depuis vos articles spécialisés.

#### 2. Restructurer la taxonomie de votre site
Organisez vos catégories selon une hiérarchie claire :
* **Parent :** `Adobe` (ou `Écosystème Adobe`)
  * **Enfants :** `Photoshop`, `Lightroom`, `Creative Cloud`, `Adobe Firefly / IA`

Ainsi, un article traitant uniquement de retouche photo va dans `Photoshop`, tandis qu'un article sur la hausse des prix des abonnements ou l'annonce de nouvelles fonctions IA transversales va directement dans la catégorie mère `Adobe`.

#### 3. Élargir votre ligne éditoriale aux sujets « Macro »
Pour alimenter cette rubrique générale, couvrez des thématiques qui dépassent le simple tutoriel :
* **Innovations & IA :** Les évolutions d'Adobe Firefly et son intégration globale.
* **Modèle économique :** Analyses des tarifs Creative Cloud, offres étudiants, alternatives.
* **Événements & Annonces :** Résumés de la conférence annuelle **Adobe MAX**.
* **Légal & Usage :** Politiques de confidentialité, propriété intellectuelle des contenus générés par IA, droits d'auteur.

<ElicitationsGroup message="Pour mettre en place cette stratégie :">
  <Elicitation label="Rédiger le plan détaillé d'une page pilier Adobe" query="Propose-moi le plan détaillé d'une page pilier (Pillar Page) optimisée SEO sur l'écosystème Adobe et le Creative Cloud." />
  <Elicitation label="Proposer 5 idées d'articles d'actualité transversale Adobe" query="Donne-moi 5 idées d'articles d'actualité ou d'analyse transversale sur la marque Adobe (IA, modèles économiques, écosystème)." />
</ElicitationsGroup>
