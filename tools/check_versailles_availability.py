# tools/check_versailles_availability.py
import requests
from langchain.tools import tool

# 1️⃣ Versailles
@tool
def check_versailles_availability(date: str, type_billet: str) -> str:
    # API réelle ou simulation
    if date == "2025-10-01":
        return "Indisponible"
    return "Disponible"