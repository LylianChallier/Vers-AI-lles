import streamlit as st
import requests

# Adresse de ton backend FastAPI
API_URL = "http://localhost:1234"  # adapte si besoin

st.set_page_config(page_title="Agent IA", page_icon="🤖", layout="centered")

st.title("🤖 Agent IA")
st.write("Discutez avec votre agent IA.")

# Initialiser l'historique de la conversation
if "messages" not in st.session_state:
    st.session_state.messages = []

# Afficher l'historique
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"🧑 **Vous :** {msg['content']}")
    else:
        st.markdown(f"🤖 **Agent :** {msg['content']}")

# Champ de saisie
user_input = st.text_area("Votre message :", placeholder="Écrivez ici...")

if st.button("Envoyer"):
    if user_input.strip() == "":
        st.warning("Veuillez entrer un message avant d’envoyer.")
    else:
        # Ajouter le message utilisateur à l'historique
        st.session_state.messages.append({"role": "user", "content": user_input})

        try:
            # Appel à ton backend FastAPI
            response = requests.post(f"{API_URL}/chat", json={"message": user_input})
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

        # Vider le champ texte après envoi
        st.rerun()

st.markdown("---")
st.caption("Interface Streamlit avec historique de discussion.")
