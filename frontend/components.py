"""
Composants HTML pour l'interface Streamlit
"""
import base64
from pathlib import Path

def get_header():
    """Retourne le HTML du header Versailles avec logo blanc"""
    # Charger et encoder le logo blanc en base64
    logo_path = Path(__file__).parent / "img" / "logo-blanc.png"
    with open(logo_path, "rb") as f:
        logo_base64 = base64.b64encode(f.read()).decode()

    return f"""
    <div class="versailles-header">
        <div class="header-container">
            <div class="header-top">
                <div class="header-logo">
                    <img src="data:image/png;base64,{logo_base64}" alt="Château de Versailles">
                </div>
                <div class="header-utils">
                    <a href="https://boutique-chateauversailles.fr/" class="search-icon">🛍️ Boutique</a>
                    <a href="#" class="lang-toggle">🇫🇷 FR / 🇬🇧 EN</a>
                </div>
            </div>
            <nav class="header-nav">
                <a href="https://www.chateauversailles.fr/" class="nav-link">Découvrir</a>
                <a href="https://www.chateauversailles.fr/accessibilite-pour-tous" class="nav-link">Accèssibilité</a>
                <a href="https://billetterie.chateauversailles.fr/index-css5-chateauversailles-lgfr-pg1.html" class="nav-link">Billeterie officielle</a>
                <a href="https://www.chateauversailles.fr/actualites/agenda-chateau-versailles" class="nav-link">Agenda & Evénements</a>
            </nav>
        </div>
    </div>
    """

def get_user_message(content):
    """Retourne le HTML d'un message utilisateur"""
    return f"""
    <div class="chat-message user-message">
        <div class="message-label">🙋 Vous</div>
        <div class="message-content">{content}</div>
    </div>
    """

def get_assistant_message(content):
    """Retourne le HTML d'un message de l'assistant"""
    return f"""
    <div class="chat-message assistant-message">
        <div class="message-label">🤖 Versailles IA</div>
        <div class="message-content">{content}</div>
    </div>
    """

def get_loading_spinner():
    """Retourne le HTML du spinner de chargement"""
    return '<div class="loading-spinner"></div>'