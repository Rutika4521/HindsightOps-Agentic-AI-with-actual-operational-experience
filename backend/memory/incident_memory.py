"""
Incident Memory — high-level operations for storing and retrieving 
structured incident experiences via Hindsight.
"""

import json
import logging
from datetime import datetime
from typing import Any, Optional

from backend.memory.hindsight_client import HindsightMemoryClient
from backend.memory.memory_types import Incident, AttemptedAction, ActionResult

logger = logging.getLogger(__name__)


def format_incident_for_memory(incident: Incident) -> str:
    """
    Format a resolved incident into structured text for Hindsight memory.
    
    This produces a rich, semantically meaningful description that
    Hindsight can extract and recall effectively.
    """
    lines = []
    lines.append(f"=== INCIDENT EXPERIENCE: {incident.incident_id} ===")
    lines.append(f"Date: {incident.timestamp.isoformat()}")
    lines.append(f"Service: {incident.service}")
    lines.append(f"Environment: {incident.environment}")
    lines.append(f"Severity: {incident.severity}")
    lines.append("")

    if incident.symptoms:
        lines.append("SYMPTOMS:")
        for s in incident.symptoms:
            lines.append(f"  - {s}")
        lines.append("")

    if incident.metrics:
        lines.append("METRICS DURING INCIDENT:")
        m = incident.metrics
        if m.latency_ms is not None:
            lines.append(f"  - API latency: {m.latency_ms:.0f}ms")
        if m.error_rate is not None:
            lines.append(f"  - Error rate: {m.error_rate*100:.1f}%")
        if m.cpu_percent is not None:
            lines.append(f"  - CPU usage: {m.cpu_percent:.1f}%")
        if m.memory_percent is not None:
            lines.append(f"  - Memory usage: {m.memory_percent:.1f}%")
        if m.db_cpu_percent is not None:
            lines.append(f"  - Database CPU: {m.db_cpu_percent:.1f}%")
        if m.db_connections is not None:
            lines.append(f"  - DB connections: {m.db_connections}")
        lines.append("")

    if incident.recent_changes:
        lines.append("RECENT CHANGES BEFORE INCIDENT:")
        for c in incident.recent_changes:
            lines.append(f"  - {c}")
        lines.append("")

    if incident.hypotheses:
        lines.append("INITIAL HYPOTHESES:")
        for h in incident.hypotheses:
            lines.append(f"  - {h}")
        lines.append("")

    if incident.attempted_actions:
        lines.append("ACTIONS ATTEMPTED (INCLUDING FAILURES):")
        for action in incident.attempted_actions:
            result_label = action.result.upper()
            lines.append(f"  - Action: {action.action}")
            lines.append(f"    Result: {result_label}")
            if action.notes:
                lines.append(f"    Notes: {action.notes}")
        lines.append("")

    if incident.root_cause:
        lines.append(f"ROOT CAUSE: {incident.root_cause}")
        lines.append("")

    if incident.successful_resolution:
        lines.append(f"SUCCESSFUL RESOLUTION: {incident.successful_resolution}")
        lines.append("")

    if incident.resolution_time_minutes is not None:
        lines.append(f"RESOLUTION TIME: {incident.resolution_time_minutes} minutes")
        lines.append("")

    if incident.lessons_learned:
        lines.append("LESSONS LEARNED:")
        for lesson in incident.lessons_learned:
            lines.append(f"  - {lesson}")
        lines.append("")

    # Identify failed actions explicitly for future recall
    failed_actions = [
        a.action for a in incident.attempted_actions
        if a.result == ActionResult.FAILED
    ]
    if failed_actions:
        lines.append("ACTIONS THAT DID NOT RESOLVE THIS INCIDENT (DO NOT REPEAT FIRST):")
        for fa in failed_actions:
            lines.append(f"  - {fa}")
        lines.append("")

    return "\n".join(lines)


def build_recall_query(incident: Incident) -> str:
    """
    Build a rich semantic query for recalling relevant historical incidents.
    """
    parts = [f"Incident investigation for {incident.service} in {incident.environment}."]

    if incident.symptoms:
        parts.append("Symptoms: " + "; ".join(incident.symptoms) + ".")

    if incident.metrics:
        m = incident.metrics
        metric_parts = []
        if m.latency_ms and m.latency_ms > 500:
            metric_parts.append(f"high API latency ({m.latency_ms:.0f}ms)")
        if m.error_rate and m.error_rate > 0.05:
            metric_parts.append(f"elevated error rate ({m.error_rate*100:.1f}%)")
        if m.db_cpu_percent and m.db_cpu_percent > 70:
            metric_parts.append(f"high database CPU ({m.db_cpu_percent:.1f}%)")
        if m.db_cpu_percent and m.db_cpu_percent < 40:
            metric_parts.append("normal database CPU")
        if metric_parts:
            parts.append("Metrics indicate: " + ", ".join(metric_parts) + ".")

    if incident.recent_changes:
        parts.append("Recent changes: " + "; ".join(incident.recent_changes) + ".")

    parts.append(
        "Looking for: similar incidents, root causes, what actions worked, "
        "what actions failed, and lessons learned."
    )

    return " ".join(parts)


def get_incident_tags(incident: Incident) -> list[str]:
    """Generate tags for a stored incident memory."""
    tags = [
        f"service:{incident.service}",
        f"env:{incident.environment}",
        f"severity:{incident.severity}",
    ]
    if incident.root_cause:
        root_cause_tag = incident.root_cause.lower().replace(" ", "_")
        tags.append(f"root_cause:{root_cause_tag}")
    return tags


class IncidentMemory:
    """
    High-level incident memory operations.
    
    Wraps HindsightMemoryClient with incident-specific logic.
    """

    def __init__(self, client: HindsightMemoryClient):
        self.client = client

    async def retain_incident(self, incident: Incident) -> dict[str, Any]:
        """
        Store a resolved incident experience into Hindsight.
        
        Formats the incident data into rich structured text and
        uses appropriate tags for future retrieval.
        """
        content = format_incident_for_memory(incident)
        tags = get_incident_tags(incident)
        metadata = {
            "service": incident.service,
            "environment": incident.environment,
            "severity": incident.severity.value,
            "root_cause": incident.root_cause or "",
            "resolution": incident.successful_resolution or "",
        }

        logger.info(f"Retaining incident memory: {incident.incident_id}")
        result = await self.client.retain_incident_memory(
            content=content,
            incident_id=incident.incident_id,
            tags=tags,
            metadata=metadata,
        )
        return result

    async def recall_for_incident(
        self,
        incident: Incident,
    ) -> dict[str, Any]:
        """
        Recall relevant historical experiences for a current incident.
        """
        query = build_recall_query(incident)
        logger.info(
            f"Recalling memories for: {incident.incident_id} ({incident.service})"
        )
        result = await self.client.recall_relevant_incidents(
            query=query,
            tags=[f"service:{incident.service}"],
            max_tokens=6000,
        )
        return result
