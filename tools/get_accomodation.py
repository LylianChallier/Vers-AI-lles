# tools/get_accomodation.py
import requests
from langchain.tools import tool

# 6️⃣ Airbnb recherche logement
@tool
def search_airbnb(city: str, checkin: str, checkout: str, guests: int) -> str:
    return f"Logements Airbnb disponibles à {city} du {checkin} au {checkout} pour {guests} personnes."

# 7️⃣ Réservation Airbnb
@tool
def book_airbnb(listing_id: str) -> str:
    return f"Réservation Airbnb {listing_id} confirmée !"
