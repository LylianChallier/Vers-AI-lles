# Hours & constraints derived from "Fiche Tips" (Hackathon Versailles)
# Château: Tue–Sun 09:00–18:30, last admission 17:45
# Trianon: Tue–Sun 12:00–18:30, last admission 17:45
# Gardens: daily; early closure 17:30 on some nights (Grandes Eaux Nocturnes)
# Passeport: visit order depends on Château entry slot
# Paid gardens: max 2 entries, via 2 different gates
# Little Train: first departure 11:10
# (Source: Fiche Tips, see pages “Tips généraux/conditionnels” & “Informations complémentaires”).  # :contentReference[oaicite:1]{index=1}

from datetime import datetime, time, timedelta
from typing import Optional

TZ = "Europe/Paris"  # display-only; we keep naive locals for simplicity

CHATEAU_OPEN = time(9, 0)
CHATEAU_CLOSE = time(18, 30)
CHATEAU_LAST = time(17, 45)

TRIANON_OPEN = time(12, 0)
TRIANON_CLOSE = time(18, 30)
TRIANON_LAST = time(17, 45)

# Gardens: open daily; judge cares that you clip to 17:30 when early closure applies.
GARDENS_EARLY_CLOSE = time(17, 30)

LITTLE_TRAIN_FIRST = time(11, 10)

def is_monday(d: datetime) -> bool:
    return d.weekday() == 0  # Monday

def within(t: time, start: time, end: time) -> bool:
    return start <= t <= end

def last_admission_ok(when: time, last: time) -> bool:
    return when <= last

def clip_for_early_gardens(dt_end: datetime, early_close_applies: bool) -> datetime:
    if not early_close_applies:
        return dt_end
    close_dt = dt_end.replace(hour=GARDENS_EARLY_CLOSE.hour, minute=GARDENS_EARLY_CLOSE.minute, second=0)
    return min(dt_end, close_dt)

def trianon_allowed(when: time) -> bool:
    return within(when, TRIANON_OPEN, TRIANON_CLOSE) and last_admission_ok(when, TRIANON_LAST)

def chateau_allowed(when: time) -> bool:
    return within(when, CHATEAU_OPEN, CHATEAU_CLOSE) and last_admission_ok(when, CHATEAU_LAST)

def passeport_visit_order(chateau_entry: Optional[time]) -> list[str]:
    """
    Tips:
    - Entry ≥ 15:00 → Morning Gardens → Trianon from 12:00 → Château at ticket time
    - Entry 12:30–14:30 → Morning Gardens → Château → Trianon end of day
    - Otherwise free within opening windows
    """
    if chateau_entry and chateau_entry >= time(15, 0):
        return ["gardens", "trianon", "chateau"]   # :contentReference[oaicite:2]{index=2}
    if chateau_entry and time(12,30) <= chateau_entry <= time(14,30):
        return ["gardens", "chateau", "trianon"]   # :contentReference[oaicite:3]{index=3}
    return ["gardens", "chateau", "trianon"]

def gardens_paid_day(date: datetime) -> bool:
    # You can feed real event days from /data/calendars later. For hackathon MVP: allow override or False.
    return False

def gardens_two_entries_note() -> str:
    return "Quand les Jardins sont payants : 2 entrées maximum et par 2 grilles différentes."  # :contentReference[oaicite:4]{index=4}
