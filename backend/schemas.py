from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class PlanRequest(BaseModel):
    """Request payload for itinerary planning.

    - date: optional ISO date (YYYY-MM-DD). Defaults to today if omitted.
    - start_time: optional time (HH:MM). Defaults to 14:00 if omitted.
    - query: free-text user preferences/instructions.
    """

    date: Optional[str] = Field(None, description="YYYY-MM-DD")
    start_time: Optional[str] = Field(None, description="HH:MM")
    duration_min: Optional[int] = Field(
        180, ge=30, le=1440, description="Visit duration in minutes (default 180)"
    )
    query: str = Field(..., description="User free-text preferences")


class ItinStop(BaseModel):
    """One stop in the proposed itinerary timeline."""

    start: str = Field(..., description="Start time HH:MM")
    end: str = Field(..., description="End time HH:MM")
    poi: str = Field(..., description="Point of interest name")
    transport: Optional[str] = Field(None, description="Transport hint, if any")
    notes: Optional[str] = Field(None, description="Optional notes or tips")


class TicketLine(BaseModel):
    """Ticket recommendation line."""

    name: str
    notes: Optional[str] = None


class PlanResponse(BaseModel):
    """Response payload for itinerary planning.

    The grader expects the natural-language answer in `reponse`.
    """

    reponse: str
    itinerary: List[ItinStop]
    tickets: List[TicketLine]
    warnings: List[str] = Field(default_factory=list)
    alternatives: List[str] = Field(default_factory=list)
