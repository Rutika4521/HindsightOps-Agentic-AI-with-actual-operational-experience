"""Shared dependency injection for API routes."""

import os
from functools import lru_cache

from groq import AsyncGroq
from backend.memory.hindsight_client import HindsightMemoryClient
from backend.agents.incident_agent import IncidentAgent


@lru_cache(maxsize=1)
def get_hindsight_client() -> HindsightMemoryClient:
    return HindsightMemoryClient()


@lru_cache(maxsize=1)
def get_groq_client() -> AsyncGroq:
    return AsyncGroq(api_key=os.getenv("GROQ_API_KEY", ""))


@lru_cache(maxsize=1)
def get_incident_agent() -> IncidentAgent:
    return IncidentAgent(
        hindsight_client=get_hindsight_client(),
        groq_client=get_groq_client(),
    )
