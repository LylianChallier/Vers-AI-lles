from __future__ import annotations
from datetime import datetime, timedelta, time
from typing import List, Tuple
from .schemas import PlanRequest, ItinStop, TicketLine, PlanResponse
from .rules import (
    is_monday, chateau_allowed, trianon_allowed, clip_for_early_gardens,
    passeport_visit_order, gardens_paid_day, gardens_two_entries_note,
    LITTLE_TRAIN_FIRST, TRIANON_OPEN
)

# Minimal POI seed (extend from JSONL later)
POIS = {
    "Gardens – Parterres & Orangery": {"indoor": False, "dwell": 35},
    "Grand Trianon": {"indoor": True, "dwell": 40},
    "Petit Trianon": {"indoor": True, "dwell": 30},
    "Queen’s Hamlet": {"indoor": False, "dwell": 35},
    "Palace – Highlights (Hall of Mirrors etc.)": {"indoor": True, "dwell": 60},
    "Gallery of Coaches (free)": {"indoor": True, "dwell": 30},
    "Gallery of Sculptures & Mouldings (free)": {"indoor": True, "dwell": 25},
    "Salle du Jeu de Paume (free)": {"indoor": True, "dwell": 25},
}

def _parse_dt(date_str: str|None, hm: str|None) -> Tuple[datetime, datetime]:
    now = datetime.now()
    d = datetime.strptime(date_str, "%Y-%m-%d") if date_str else now
    start = datetime.combine(d.date(), datetime.strptime(hm or "14:00", "%H:%M").time())
    end = start + timedelta(minutes=180)  # default 3h
    return start, end

def _kw(req: PlanRequest) -> dict:
    q = req.query.lower()
    return {
        "family": any(k in q for k in ["child","kids","enfant","famille"]),
        "outdoor": any(k in q for k in ["garden","jardin","outside","dehors"]),
        "photo": any(k in q for k in ["photo","instagram","spot"]),
        "low_budget": any(k in q for k in ["budget","cheap","économique","pas cher","low budget"]),
        "visited_hall": "hall of mirrors" in q or "galerie des glaces" in q,
        "stroller": any(k in q for k in ["stroller","poussette"]),
        "passport": "passeport" in q or "passport" in q,
        "chateau_slot": None,  # could parse e.g. "entry 15:00"
    }

def plan(req: PlanRequest, weather: dict | None = None) -> PlanResponse:
    start, end = _parse_dt(req.date, req.start_time)
    if is_monday(start):  # Palace & Trianon closed
        itinerary: List[ItinStop] = []
        t = start
        # Gardens + free indoor alternatives
        for name in ["Gardens – Parterres & Orangery", "Gallery of Coaches (free)", "Gallery of Sculptures & Mouldings (free)"]:
            dwell = POIS[name]["dwell"]
            itinerary.append(ItinStop(start=t.strftime("%H:%M"), end=(t:=t+timedelta(minutes=dwell)).strftime("%H:%M"), poi=name))
        txt = ("Le lundi, le Château et le Domaine de Trianon sont fermés. "
               "Je vous propose les Jardins et des espaces gratuits adaptés aux familles : "
               "Galerie des Carrosses, Galerie des Sculptures et des Moulages. ")
        warnings = ["Château/Trianon fermés le lundi."]
        return PlanResponse(reponse=txt, itinerary=itinerary, tickets=[], warnings=warnings, alternatives=[])

    k = _kw(req)
    weather_label = None
    flags = {}
    if weather:
        summary = weather.get("summary") or {}
        weather_label = summary.get("label")
        flags = summary.get("flags") or {}

    prefer_indoor = bool(flags.get("prefer_indoor"))
    heat_prec = bool(flags.get("heat_precautions"))

    # Choose order (Passeport logic if relevant)
    order = passeport_visit_order(k["chateau_slot"])
    if prefer_indoor:
        order = [item for item in ["chateau", "trianon", "gardens"] if item in order]

    # Build timeline respecting Trianon >= 12:00
    t = start
    itinerary: List[ItinStop] = []
    warnings: List[str] = []

    # 1) Gardens first when relevant
    skip_gardens = prefer_indoor and weather_label in {"heavy_rain", "rain_risk", "mixed"}
    if "gardens" in order and t < end and not skip_gardens:
        dwell = POIS["Gardens – Parterres & Orangery"]["dwell"]
        if heat_prec and dwell >= 25:
            dwell -= 10
        stop_end = t + timedelta(minutes=dwell)
        stop_end = clip_for_early_gardens(stop_end, early_close_applies=False)
        itinerary.append(ItinStop(start=t.strftime("%H:%M"), end=stop_end.strftime("%H:%M"),
                                  poi="Gardens – Parterres & Orangery",
                                  notes="Conseillé pour photos & espaces ouverts."))
        t = stop_end
    elif "gardens" in order and skip_gardens:
        warnings.append("Météo défavorable : jardins raccourcis/remplacés par des étapes indoor.")

    # 2) Trianon block if window allows (>= 12:00)
    if "trianon" in order and t.time() < TRIANON_OPEN:
        t = t.replace(hour=TRIANON_OPEN.hour, minute=TRIANON_OPEN.minute)

    def add_stop(name: str, transport: str|None=None, note: str|None=None):
        nonlocal t
        dwell = POIS[name]["dwell"]
        st, en = t, t + timedelta(minutes=dwell)
        itinerary.append(ItinStop(start=st.strftime("%H:%M"), end=en.strftime("%H:%M"), poi=name, transport=transport, notes=note))
        t = en

    if "trianon" in order and t < end and trianon_allowed(t.time()):
        # Suggest Little Train if start >= 11:10 (first departure)
        use_train = t.time() >= LITTLE_TRAIN_FIRST
        add_stop("Grand Trianon", transport="Petit train recommandé" if use_train else None)
        if t < end: add_stop("Queen’s Hamlet")
        if t < end: add_stop("Petit Trianon")

    # 3) Château highlight (respect last admission 17:45)
    if "chateau" in order and t < end and t.time() <= time(17,45):
        add_stop("Palace – Highlights (Hall of Mirrors etc.)")

    # Fill with family/free options if time remains or bad weather later
    if k["family"] and t < end:
        add_stop("Gallery of Coaches (free)")
    if k["low_budget"] and t < end:
        add_stop("Gallery of Sculptures & Mouldings (free)")

    # Tickets recommendation
    tickets = []
    if k["passport"]:
        tickets.append(TicketLine(name="Billet Passeport", notes="Accès Château, Jardins et Trianon."))
    else:
        tickets.append(TicketLine(name="Combinaison économique", notes="Jardins (si payants) + Trianon ou espaces gratuits selon météo."))

    # Mandatory notes for gardens paid days
    if gardens_paid_day(start):
        warnings.append(gardens_two_entries_note())

    # Natural-language response (FR/EN lite)
    intro = "Voici un parcours faisable et adapté à votre demande."
    tips = ("Rappel : Trianon ouvre à 12:00, dernières admissions Château/Trianon 17:45. "
            "Les Jardins peuvent fermer à 17:30 certains soirs (Grandes Eaux Nocturnes). ")  # :contentReference[oaicite:5]{index=5}
    wx_line = ""
    if weather_label == "heavy_rain":
        wx_line = "Météo: fortes pluies — parcours principalement indoor et sections courtes."
    elif weather_label == "rain_risk":
        wx_line = "Météo: risque d'averse — prévoir un plan pluie et étapes indoor proches."
    elif weather_label == "heat":
        wx_line = "Météo: chaleur — privilégier l’indoor, pauses et points d’eau."
    elif weather_label == "mixed":
        wx_line = "Météo: variable — alterner indoor/outdoor avec marges."
    elif weather_label == "windy":
        wx_line = "Météo: vent — privilégier des parcours abrités."

    reponse = " ".join(part for part in [intro, wx_line, tips] if part)

    # Simple alternatives
    alts = ["Plan pluie indoor : Galerie des Carrosses, Sculptures & Moulages, Château (si ouvert).",
            "Moins de marche : utiliser le Petit train pour le Trianon (1er départ 11:10)."]  # :contentReference[oaicite:6]{index=6}

    if heat_prec:
        warnings.append("Chaleur: pensez eau, casquettes, pauses ombragées.")

    return PlanResponse(reponse=reponse, itinerary=itinerary, tickets=tickets, warnings=warnings, alternatives=alts)
