"""Tool to book Versailles tickets (simulation for now, ready for API integration)."""

from langchain.tools import tool
from datetime import datetime
import random


@tool(description='Book tickets for Versailles')
def book_versailles_tickets(date: str, type_billet: str, participants: int, horaire: str = "09:00") -> str:
    """
    Book tickets for the Château de Versailles.
    
    Args:
        date: Date of visit (format: YYYY-MM-DD or DD/MM/YYYY)
        type_billet: Type of ticket (passeport, chateau, trianon, jardins)
        participants: Number of participants
        horaire: Preferred time slot (default: 09:00)
    
    Returns:
        Booking confirmation with reference number
    """
    try:
        # Validate inputs
        if participants <= 0:
            return "Erreur: Le nombre de participants doit être supérieur à 0."
        
        # Parse date
        try:
            if '/' in date:
                date_obj = datetime.strptime(date, "%d/%m/%Y")
            else:
                date_obj = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return "Erreur: Format de date invalide. Utilisez DD/MM/YYYY ou YYYY-MM-DD."
        
        # Check if date is in the future
        if date_obj < datetime.now():
            return "Erreur: La date de visite doit être dans le futur."
        
        # Ticket types and prices
        ticket_prices = {
            'passeport': 32.00,
            'chateau': 21.00,
            'trianon': 12.00,
            'jardins': 10.00,
            'visite_guidee': 10.00  # Additional cost
        }
        
        base_type = type_billet.lower().replace(' ', '_')
        if base_type not in ticket_prices:
            return f"Erreur: Type de billet inconnu. Types disponibles: {', '.join(ticket_prices.keys())}"
        
        # Calculate price
        price_per_person = ticket_prices[base_type]
        total_price = price_per_person * participants
        
        # Generate booking reference
        booking_ref = f"VER{random.randint(100000, 999999)}"
        
        # Simulate booking (TODO: Replace with real API call)
        confirmation = f"""
✅ Réservation confirmée !

📋 Référence de réservation: {booking_ref}
📅 Date: {date_obj.strftime('%d/%m/%Y')}
🕐 Horaire: {horaire}
👥 Nombre de participants: {participants}
🎫 Type de billet: {type_billet}
💰 Prix total: {total_price:.2f}€

⚠️ Important:
- Présentez-vous 15 minutes avant l'horaire réservé
- Apportez cette confirmation et une pièce d'identité
- Les billets sont nominatifs et non remboursables

📧 Un email de confirmation a été envoyé.
🔗 Lien de gestion: https://billetterie.chateauversailles.fr/booking/{booking_ref}

Bon séjour à Versailles ! 🏰
"""
        
        return confirmation
    
    except Exception as e:
        return f"Erreur lors de la réservation: {str(e)}"


@tool(description='Check ticket availability for Versailles')
def check_ticket_availability(date: str, type_billet: str) -> str:
    """
    Check ticket availability for a specific date and ticket type.
    
    Args:
        date: Date to check (format: YYYY-MM-DD or DD/MM/YYYY)
        type_billet: Type of ticket to check
    
    Returns:
        Availability status
    """
    try:
        # Parse date
        try:
            if '/' in date:
                date_obj = datetime.strptime(date, "%d/%m/%Y")
            else:
                date_obj = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return "Erreur: Format de date invalide."
        
        # Simulate availability check (TODO: Replace with real API call)
        # For simulation, make some dates "full"
        day_of_week = date_obj.weekday()
        
        if day_of_week in [5, 6]:  # Weekend
            available_slots = random.randint(50, 200)
            status = "Forte affluence" if available_slots < 100 else "Disponible"
        else:  # Weekday
            available_slots = random.randint(100, 500)
            status = "Disponible"
        
        # Check for closed days (Mondays)
        if day_of_week == 0:
            return f"⚠️ Le château de Versailles est fermé le lundi.\nVeuillez choisir une autre date."
        
        return f"""
📅 Disponibilité pour le {date_obj.strftime('%d/%m/%Y')}:

🎫 Type de billet: {type_billet}
✅ Statut: {status}
📊 Places disponibles: ~{available_slots}

💡 Conseil: Réservez en ligne pour éviter la file d'attente !
"""
    
    except Exception as e:
        return f"Erreur lors de la vérification: {str(e)}"
