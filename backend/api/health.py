"""Health check endpoint."""

from fastapi import APIRouter
from backend.api.deps import get_hindsight_client

router = APIRouter()


@router.get("/health")
async def health():
    """Check backend and Hindsight connectivity."""
    client = get_hindsight_client()
    hindsight_status = await client.health_check()
    return {
        "status": "ok",
        "hindsight": hindsight_status,
    }
