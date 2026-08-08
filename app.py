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

st.markdown(f"""
<script>
(function() {{
    var svgUri = "{svg_data_uri}";
    var doc = window.parent ? window.parent.document : document;
    var links = doc.querySelectorAll("link[rel*='icon']");
    links.forEach(function(l) {{ l.href = svgUri; l.type = "image/svg+xml"; }});
}})();
</script>
<style>
    header {{visibility: hidden;}}
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    .stApp {{
        background-color: #0b0f19;
        background-image: radial-gradient(at 15% 10%, rgba(139, 92, 246, 0.22) 0px, transparent 40%),
                          radial-gradient(at 85% 5%, rgba(37, 99, 235, 0.20) 0px, transparent 45%);
        color: #f1f5f9;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #161e2e !important;
        border: 1px solid #1e293b !important;
        border-radius: 14px !important;
        padding: 14px !important;
        transition: transform 0.25s ease;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-4px) !important;
        border-color: #8b5cf6 !important;
    }
    .article-read { opacity: 0.65; filter: grayscale(15%); }
    .cat-badge { font-size: 0.70rem; font-weight: 800; padding: 3px 9px; border-radius: 12px; text-transform: uppercase; color: #0f172a; display: inline-block; margin-bottom: 6px; }
    .read-badge { font-size: 0.65rem; font-weight: 700; padding: 2px 7px; border-radius: 10px; color: #94a3b8; border: 1px solid rgba(148, 163, 184, 0.4); display: inline-block; margin-left: 6px; }
    .hero-badge { background-color: transparent; color: #F472B6; border: 1px solid #F472B6; font-weight: 800; font-size: 0.75rem; padding: 4px 12px; border-radius: 20px; text-transform: uppercase; display: inline-block; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

@st.dialog("⤓ Installer Krea sur votre appareil")
def show_install_instructions():
    st.write("Pour garder un accès rapide à Krea, ajoutez-le à votre écran d'accueil :")
    st.markdown("""
    **💻 Sur Ordinateur (Chrome/Edge/Brave)**:
    - Cliquez sur l'icône d'installation dans la barre d'adresse, ou dans le menu (⋮) -> **Installer Krea**.
    
    **🍎 Sur iPhone / iPad (Safari)**:
    - Appuyez sur le bouton de **Partage** (carré avec flèche) puis **"Sur l'écran d'accueil"**.
    
    **🤖 Sur Android (Chrome)**:
    - Appuyez sur les **trois points** (⋮) puis **"Installer l'application"**.
    """)

# --- ETAT DE SESSION ---
if "bookmarks" not in st.session_state: st.session_state.bookmarks = set()
if "read_articles" not in st.session_state: st.session_state.read_articles = set()
if "category_views" not in st.session_state: st.session_state.category_views = {}
if "articles_limit" not in st.session_state: st.session_state.articles_limit = 12
if "search_input" not in st.session_state: st.session_state.search_input = ""

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
    "Lightroom": ["lightroom", "raw", "developpement photo"],
    "InDesign": ["indesign", "mise en page", "typographie"],
    "Illustrator": ["illustrator", "vectoriel", "vecteur"],
    "Photo": ["photo", "photographie", "appareil photo", "objectif", "portrait"],
    "Expos photos": ["exposition", "expositions", "expo photo", "galerie"],
    "Graphisme": ["design graphique", "graphiste", "logo", "branding"],
    "Tutoriels": ["tuto", "tutoriel", "guide technique", "astuce"],
    "AI": ["ia", "intelligence artificielle", "midjourney", "firefly", "chatgpt"]
}

CATEGORY_COLORS = {
    "Photoshop": "#38BDF8", "Lightroom": "#60A5FA", "InDesign": "#F43F5E",
    "Illustrator": "#FB923C", "AI": "#A855F7", "Graphisme": "#EC4899",
    "Photo": "#F59E0B", "Tutoriels": "#10B981", "Expos photos": "#E11D48", "Général": "#64748B"
}

def clean_text(raw_html):
    if not raw_html: return ""
    return re.sub(r'\s+', ' ', re.sub(r'<.*?>', ' ', raw_html)).strip()

def clean_url(url):
    if not url: return None
    url = url.strip()
    if url.startswith("http") and not any(b in url.lower() for b in ["gravatar", "pixel", "icon", ".svg"]):
        return url
    return None

def extract_image_url(entry):
    if 'media_content' in entry:
        for m in entry.media_content:
            u = clean_url(m.get('url'))
            if u: return u
    for text_src in [entry.get('summary', ''), entry.get('description', '')]:
        matches = re.findall(r'<img [^>]*src=["\']([^"\']+)["\']', text_src)
        for src in matches:
            u = clean_url(src)
            if u: return u
    return None

def detect_category(title, summary, source_name):
    text = f"{title} {summary}".lower()
    for cat, kws in KEYWORDS.items():
        for kw in kws:
            if re.search(r'\b' + re.escape(kw) + r'\b', text): return cat
    if source_name in ["Phototrend", "Apprendre la Photo", "OuiOui Photo", "Graine de Photographe", "Blind Magazine"]:
        return "Photo"
    return "Général"

@st.dialog("▤ Aperçu de l'article")
def open_preview_modal(article):
    st.session_state.read_articles.add(article["id"])
    if article.get("image_url"):
        st.markdown(f'<img src="{article["image_url"]}" style="width:100%; max-height:280px; object-fit:cover; border-radius:10px; margin-bottom:10px;">', unsafe_allow_html=True)
    st.markdown(f"### {article['title']}")
    st.caption(f"⌖ **{article['source']}** • {article['relative_date']}")
    st.write(article['summary'])
    st.divider()
    st.link_button("↗ Ouvrir l'article complet", article['link'], use_container_width=True)

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
                    link = entry.get("link", "#")
                    title = clean_text(entry.get("title", ""))
                    summary = clean_text(entry.get("summary", entry.get("description", "")))
                    dt = datetime.now(timezone.utc)
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        dt = datetime.fromtimestamp(time.mktime(entry.published_parsed), tz=timezone.utc)
                    img = extract_image_url(entry)
                    cat = detect_category(title, summary, feed["name"])
                    articles.append({
                        "id": hashlib.md5((link + title).encode()).hexdigest(),
                        "title": title, "link": link, "source": feed["name"], "summary": summary,
                        "date": dt, "relative_date": "Récemment", "category": cat,
                        "image_url": img if img else f"https://picsum.photos/seed/{abs(hash(title))%1000}/600/350",
                        "summary_short": summary[:150] + "..." if len(summary) > 150 else summary
                    })
        except: continue
    articles.sort(key=lambda x: x["date"], reverse=True)
    return articles

all_fetched = fetch_all_feeds()

# --- EN-TÊTE PROPRE ---
col_logo, col_inst = st.columns([5, 1])
with col_logo:
    st.markdown("## 🎨 Krea — L'Actu Créative & IA")
with col_inst:
    st.write("")
    if st.button("⤓ Installer App", use_container_width=True):
        show_install_instructions()

categories = ["Tous", "Photoshop", "Lightroom", "InDesign", "Illustrator", "AI", "Graphisme", "Photo", "Tutoriels", "Expos photos", "☆ Favoris"]
selected_category = st.radio("Catégories :", categories, horizontal=True)

col_s, col_r, col_v, col_ref = st.columns([1.5, 2, 1, 0.6])
with col_s: selected_source = st.selectbox("Source :", ["Toutes les sources"] + [s["name"] for s in SOURCES])
with col_r: search_query = st.text_input("⌕ Recherche :", value=st.session_state.search_input, placeholder="Mot-clé...")
with col_v: view_mode = st.radio("Vue :", ["Grille", "Liste"], horizontal=True)
with col_ref:
    st.write("")
    if st.button("↻", use_container_width=True): st.cache_data.clear(); st.rerun()

st.divider()

# --- FILTRAGE ---
filtered = []
for art in all_fetched:
    txt = f"{art['title']} {art['summary']}".lower()
    if selected_category == "☆ Favoris" and art["link"] not in st.session_state.bookmarks: continue
    if selected_category != "Tous" and selected_category != "☆ Favoris" and art["category"] != selected_category: continue
    if selected_source != "Toutes les sources" and art["source"] != selected_source: continue
    if search_query.strip() and search_query.lower() not in txt: continue
    filtered.append(art)

# --- AFFICHAGE ---
if filtered:
    cols = st.columns(3) if view_mode == "Grille" else [st.container()]
    for idx, art in enumerate(filtered[:st.session_state.articles_limit]):
        col = cols[idx % 3] if view_mode == "Grille" else cols[0]
        is_read = art['id'] in st.session_state.read_articles
        is_fav = art['link'] in st.session_state.bookmarks
        
        with col:
            with st.container(border=True):
                st.markdown(f'<div class="{"article-read" if is_read else ""}">', unsafe_allow_html=True)
                if view_mode == "Grille":
                    st.markdown(f'<img src="{art["image_url"]}" style="width:100%; height:140px; object-fit:cover; border-radius:8px; margin-bottom:8px;">', unsafe_allow_html=True)
                
                cat_col = CATEGORY_COLORS.get(art['category'], "#64748B")
                st.markdown(f'<span class="cat-badge" style="background-color:{cat_col};">{art["category"]}</span>' + ('<span class="read-badge">✓ Lu</span>' if is_read else ''), unsafe_allow_html=True)
                st.caption(f"⌖ {art['source']}")
                st.markdown(f"**{art['title']}**")
                
                c1, c2, c3 = st.columns([1.2, 1, 0.8])
                with c1: st.link_button("Lire", art['link'], use_container_width=True)
                with c2:
                    if st.button("Aperçu", key=f"prev_{art['id']}", use_container_width=True):
                        open_preview_modal(art)
                with c3:
                    if st.button("★" if is_fav else "☆", key=f"fav_{art['id']}", use_container_width=True):
                        if is_fav: st.session_state.bookmarks.remove(art['link'])
                        else: st.session_state.bookmarks.add(art['link'])
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
    
    if len(filtered) > st.session_state.articles_limit:
        if st.button("⤓ Charger plus d'articles", use_container_width=True):
            st.session_state.articles_limit += 12
            st.rerun()
else:
    st.info("Aucun article trouvé.")

# --- FOOTER ---
st.markdown("""
<div style="text-align: center; margin-top: 50px; padding: 20px 0; border-top: 1px solid rgba(255,255,255,0.08);">
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 110 110" width="45" height="45"><rect x="15" y="12" width="76" height="76" rx="18" fill="#8B5CF6"/><text x="53" y="66" font-family="sans-serif" font-weight="900" font-size="54" fill="#FFFFFF" text-anchor="middle" transform="rotate(-10 53 66)">k</text></svg>
    <p style="color: #94A3B8; font-size: 0.8rem; margin-top: 5px;">Krea — by Graphis Studio</p>
</div>
""", unsafe_allow_html=True)
