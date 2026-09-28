"""Memory Explorer API routes."""

import logging
from fastapi import APIRouter, HTTPException
from backend.api.deps import get_hindsight_client

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("")
async def list_memories():
    """List all memories stored in Hindsight (for Memory Explorer)."""
    client = get_hindsight_client()
    result = await client.list_all_memories(limit=200)
    if not result.get("success"):
        raise HTTPException(status_code=503, detail=f"Hindsight error: {result.get('error')}")
    return result


@router.get("/stats")
async def memory_stats():
    """Get Hindsight bank statistics."""
    client = get_hindsight_client()
    result = await client.get_bank_stats()
    return result
