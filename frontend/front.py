import streamlit as st
import requests
from pathlib import Path
from components import get_header, get_user_message, get_assistant_message, get_loading_spinner

# Adresse de ton backend FastAPI
API_URL = "http://backend:8001"

# Configuration de la page
st.set_page_config(page_title="Château de Versailles - Agent IA", page_icon="🏰", layout="wide")

# Charger le CSS
css_file = Path(__file__).parent / "styles.css"
with open(css_file) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Afficher le header
st.markdown(get_header(), unsafe_allow_html=True)

st.title("🤖 Agent IA")
st.write("Discutez avec votre agent IA.")

# Initialiser l'historique de la conversation
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialiser l'état de traitement
if "processing" not in st.session_state:
    st.session_state.processing = False

# Si en cours de traitement, appeler l'IA
if st.session_state.processing:
    # Afficher le spinner
    spinner_placeholder = st.empty()
    spinner_placeholder.markdown(get_loading_spinner(), unsafe_allow_html=True)

    # Récupérer le dernier message utilisateur
    last_user_message = st.session_state.messages[-1]["content"]

    try:
        # Appel à ton backend FastAPI
        response = requests.post(f"{API_URL}/chat/conversation", json={"message": last_user_message})
        if response.status_code == 200:
            answer = response.json().get("response", "Pas de réponse.")
            # Ajouter la réponse de l'IA à l'historique
            st.session_state.messages.append({"role": "assistant", "content": answer})
        else:
            st.session_state.messages.append(
                {"role": "assistant", "content": f"Erreur {response.status_code} : {response.text}"}
            )
    except Exception as e:
        st.session_state.messages.append(
            {"role": "assistant", "content": f"Impossible de joindre le backend : {e}"}
        )

    # Arrêter le traitement
    st.session_state.processing = False
    spinner_placeholder.empty()
    st.rerun()

# Afficher l'historique avec des conteneurs stylisés
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(get_user_message(msg['content']), unsafe_allow_html=True)
    else:
        st.markdown(get_assistant_message(msg['content']), unsafe_allow_html=True)

# Formulaire pour gérer l'envoi avec Entrée
with st.form(key="chat_form", clear_on_submit=True):
    col1, col2 = st.columns([6, 1])
    with col1:
        user_input = st.text_input("Votre message :", placeholder="Écrivez ici...", key="user_input", label_visibility="collapsed")
    with col2:
        submitted = st.form_submit_button("📤 Envoyer", use_container_width=True)

if submitted:
    if user_input.strip() == "":
        st.warning("Veuillez entrer un message avant d'envoyer.")
    else:
        # Ajouter immédiatement le message utilisateur à l'historique
        st.session_state.messages.append({"role": "user", "content": user_input})
        # Activer le traitement
        st.session_state.processing = True
        # Recharger pour afficher le message utilisateur et lancer le traitement
        st.rerun()