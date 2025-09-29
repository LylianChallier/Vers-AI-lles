# tools/get_next_passage.py
import requests
from langchain.tools import tool

BASE_URL = "https://api-ratp.pierre-grimaud.fr/v4"  # endpoint du projet ratp-api-rest

@tool
def get_next_passages(stop: str, line: str, transport_type: str = "bus") -> str:
    """
    Ex : stop="Châtelet", line="72", transport_type="bus"
    transport_type peut être "metro", "rer", "bus", "tram"
    Returns next formatted passages.
    """
    # Construire l’URL : /stop/{transport}/{line}/{stop}/next
    url = f"{BASE_URL}/schedules/{transport_type}/{line}/{stop}"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
    except Exception as e:
        return f"Erreur API RATP : {e}"

    data = resp.json()
    if "result" not in data or "schedules" not in data["result"]:
        return f"Aucun horaire disponible pour {transport_type} {line} à {stop}."

    schedules = data["result"]["schedules"]
    # Formater quelques passages
    formatted = []
    for s in schedules:
        # s contient typiquement {"message":"xx min", "destination":"..."}
        msg = s.get("message")
        dest = s.get("destination")
        formatted.append(f"{msg} vers {dest}")

    return f"Prochains passages pour {transport_type.upper()} ligne {line} à {stop} : " + "; ".join(formatted)
