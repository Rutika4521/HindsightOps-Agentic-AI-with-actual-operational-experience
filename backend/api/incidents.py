"""Incident API routes."""

import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException
from backend.api.deps import get_incident_agent
from backend.memory.memory_types import (
    CreateIncidentRequest, Incident, ResolveIncidentRequest,
    RecordActionRequest, AttemptedAction, IncidentStatus, IncidentMetrics,
)
from backend.services import incident_store

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", status_code=201)
async def create_incident(req: CreateIncidentRequest):
    """Create a new incident."""
    incident = Incident(
        incident_id="",  # Will be auto-assigned
        timestamp=datetime.utcnow(),
        service=req.service,
        environment=req.environment,
        severity=req.severity,
        status=IncidentStatus.ACTIVE,
        symptoms=req.symptoms,
        metrics=req.metrics,
        logs_summary=req.logs_summary,
        recent_changes=req.recent_changes,
    )
    created = incident_store.create_incident(incident)
    return created.model_dump(mode="json")


@router.get("")
async def list_incidents():
    """List all incidents."""
    incidents = incident_store.list_incidents()
    return [i.model_dump(mode="json") for i in incidents]


@router.get("/{incident_id}")
async def get_incident(incident_id: str):
    """Get a single incident by ID."""
    incident = incident_store.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    return incident.model_dump(mode="json")


@router.post("/{incident_id}/analyze")
async def analyze_incident(incident_id: str):
    """
    Run full incident analysis:
    1. Recall historical memories from Hindsight
    2. Compare with current incident
    3. Generate hypotheses
    4. Produce evidence-based recommendation
    """
    incident = incident_store.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    agent = get_incident_agent()
    try:
        result = await agent.analyze_incident(incident)
        # Store generated hypotheses back on the incident
        incident.hypotheses = [h.get("hypothesis", "") for h in result.hypotheses]
        incident.status = IncidentStatus.INVESTIGATING
        incident_store.update_incident(incident)
        return result.model_dump(mode="json")
    except Exception as e:
        logger.error(f"Analysis failed for {incident_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/{incident_id}/actions")
async def record_action(incident_id: str, req: RecordActionRequest):
    """Record an action taken during incident investigation."""
    incident = incident_store.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    action = AttemptedAction(
        action=req.action,
        result=req.result,
        notes=req.notes,
        timestamp=datetime.utcnow(),
    )
    incident.attempted_actions.append(action)
    incident_store.update_incident(incident)
    return {"success": True, "action": action.model_dump(mode="json")}


@router.post("/{incident_id}/resolve")
async def resolve_incident(incident_id: str, req: ResolveIncidentRequest):
    """
    Mark incident as resolved and store experience in Hindsight.
    This is the LEARN step — new memory for future incidents.
    """
    incident = incident_store.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    incident.root_cause = req.root_cause
    incident.successful_resolution = req.successful_resolution
    incident.resolution_time_minutes = req.resolution_time_minutes
    incident.lessons_learned = req.lessons_learned
    incident.status = IncidentStatus.RESOLVED
    incident_store.update_incident(incident)

    # Store in Hindsight — the core learning loop
    agent = get_incident_agent()
    try:
        retain_result = await agent.retain_resolved_incident(incident)
        incident.memory_retained = retain_result.get("success", False)
        incident_store.update_incident(incident)
        return {
            "success": True,
            "incident": incident.model_dump(mode="json"),
            "memory_retained": retain_result,
        }
    except Exception as e:
        logger.error(f"Failed to retain memory for {incident_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Incident resolved but memory retention failed: {str(e)}"
        )


@router.get("/{incident_id}/memory")
async def get_incident_memory(incident_id: str):
    """Get the Hindsight memory for a specific incident."""
    from backend.memory.incident_memory import build_recall_query
    incident = incident_store.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    hindsight = get_incident_agent().incident_memory.client
    query = build_recall_query(incident)
    result = await hindsight.recall_relevant_incidents(query=query)
    return result
