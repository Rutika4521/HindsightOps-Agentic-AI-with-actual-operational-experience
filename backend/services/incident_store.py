"""
In-memory incident store (no external database needed).
Incidents are stored in memory during the session.
"""

import logging
from datetime import datetime
from typing import Optional
from backend.memory.memory_types import Incident, IncidentStatus

logger = logging.getLogger(__name__)

# In-memory store: incident_id -> Incident
_incidents: dict[str, Incident] = {}
_counter = 0


def _generate_id() -> str:
    global _counter
    _counter += 1
    return f"INC-{_counter:03d}"


def create_incident(incident: Incident) -> Incident:
    if not incident.incident_id:
        incident.incident_id = _generate_id()
    _incidents[incident.incident_id] = incident
    logger.info(f"Created incident: {incident.incident_id}")
    return incident


def get_incident(incident_id: str) -> Optional[Incident]:
    return _incidents.get(incident_id)


def update_incident(incident: Incident) -> Incident:
    _incidents[incident.incident_id] = incident
    return incident


def list_incidents() -> list[Incident]:
    return sorted(_incidents.values(), key=lambda i: i.timestamp, reverse=True)


def clear_active_incidents():
    """Clear all current-session incidents (for demo reset)."""
    _incidents.clear()
    global _counter
    _counter = 0
    logger.info("Cleared all incidents from session store")
