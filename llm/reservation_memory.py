# reservation_memory.py
from pydantic import BaseModel
from typing import List, Optional

class ReservationPlan(BaseModel):
    date: Optional[str] = None
    participants: Optional[int] = None
    type_billet: Optional[str] = None
    horaire: Optional[str] = None
    options_speciales: List[str] = []
    transport_info: Optional[str] = None
    parking_info: Optional[str] = None
    covid_restrictions: Optional[str] = None
