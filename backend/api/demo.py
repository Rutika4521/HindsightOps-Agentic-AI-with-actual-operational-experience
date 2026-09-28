"""
Demo control endpoints.

POST /api/demo/reset  — clear all memories and active incidents
POST /api/demo/seed   — seed all synthetic historical incidents into Hindsight
POST /api/demo/create-incident — create a demo payments-api incident
"""

import asyncio
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from backend.api.deps import get_hindsight_client, get_incident_agent
from backend.data.synthetic_incidents import SYNTHETIC_INCIDENTS
from backend.memory.incident_memory import IncidentMemory
from backend.services import incident_store
from backend.memory.memory_types import (
    CreateIncidentRequest, Incident, IncidentMetrics, Severity, IncidentStatus,
)
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

_seed_status = {"seeding": False, "seeded_count": 0, "total": 0, "error": None}


@router.post("/reset")
async def demo_reset():
    """
    Reset the demo environment:
    - Clear all Hindsight memories
    - Clear all active incidents from session
    """
    global _seed_status
    client = get_hindsight_client()

    # Clear Hindsight memory
    clear_result = await client.clear_all_memories()
    if not clear_result.get("success"):
        raise HTTPException(
            status_code=503,
            detail=f"Failed to clear Hindsight: {clear_result.get('error')}"
        )

    # Clear session incidents
    incident_store.clear_active_incidents()

    # Reset seed status
    _seed_status = {"seeding": False, "seeded_count": 0, "total": 0, "error": None}

    logger.info("Demo reset complete — all memories cleared")
    return {
        "success": True,
        "message": "Demo reset complete. Hindsight memory cleared. Ready for before/after demo.",
        "hindsight": clear_result,
    }


async def _seed_incidents_background():
    """Background task that seeds all synthetic incidents into Hindsight."""
    global _seed_status
    client = get_hindsight_client()
    memory = IncidentMemory(client)

    _seed_status["seeding"] = True
    _seed_status["total"] = len(SYNTHETIC_INCIDENTS)
    _seed_status["seeded_count"] = 0
    _seed_status["error"] = None

    for incident in SYNTHETIC_INCIDENTS:
        try:
            result = await memory.retain_incident(incident)
            if result.get("success"):
                _seed_status["seeded_count"] += 1
                logger.info(f"Seeded: {incident.incident_id} ({_seed_status['seeded_count']}/{_seed_status['total']})")
            else:
                logger.warning(f"Seed failed for {incident.incident_id}: {result.get('error')}")
            # Small delay to avoid rate limiting
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.error(f"Error seeding {incident.incident_id}: {e}", exc_info=True)
            _seed_status["error"] = str(e)

    _seed_status["seeding"] = False
    logger.info(f"Seeding complete: {_seed_status['seeded_count']}/{_seed_status['total']} incidents stored in Hindsight")


@router.post("/seed")
async def demo_seed(background_tasks: BackgroundTasks):
    """
    Seed all synthetic historical incidents into Hindsight memory.
    This is the 'WITH MEMORY' state for the demo.
    
    Runs in the background — check /api/demo/seed-status for progress.
    """
    global _seed_status
    if _seed_status.get("seeding"):
        return {
            "success": False,
            "message": "Seeding already in progress",
            "status": _seed_status,
        }

    background_tasks.add_task(_seed_incidents_background)
    return {
        "success": True,
        "message": f"Seeding {len(SYNTHETIC_INCIDENTS)} historical incidents into Hindsight. Check /api/demo/seed-status for progress.",
        "total_incidents": len(SYNTHETIC_INCIDENTS),
    }


@router.get("/seed-status")
async def demo_seed_status():
    """Check the progress of incident seeding."""
    return _seed_status


@router.post("/create-incident")
async def demo_create_incident():
    """
    Create a demo payments-api incident for the before/after demonstration.
    
    This incident closely matches INC-017, INC-031, and INC-038 to show
    how historical memory influences recommendations.
    """
    incident = Incident(
        incident_id="",
        timestamp=datetime.utcnow(),
        service="payments-api",
        environment="production",
        severity=Severity.SEV1,
        status=IncidentStatus.ACTIVE,
        symptoms=[
            "API latency increased from 240ms to 2100ms (p95)",
            "HTTP 500 error rate at 18%",
            "Payment processing timeouts increasing",
            "Customer-facing payment failures reported",
        ],
        metrics=IncidentMetrics(
            latency_ms=2100,
            error_rate=0.18,
            cpu_percent=70,
            memory_percent=58,
            db_cpu_percent=42,
            db_connections=48,
        ),
        recent_changes=["payments-api v2.4.1 deployed 9 minutes ago"],
        logs_summary="ERROR: PaymentProcessor timeout after 2000ms | ERROR: Downstream payment handler exception",
    )
    created = incident_store.create_incident(incident)
    logger.info(f"Demo incident created: {created.incident_id}")
    return {
        "success": True,
        "incident": created.model_dump(mode="json"),
        "message": (
            "Demo incident created. Run POST /api/incidents/{id}/analyze to see "
            "how Hindsight memory influences the recommendation."
        ),
    }
