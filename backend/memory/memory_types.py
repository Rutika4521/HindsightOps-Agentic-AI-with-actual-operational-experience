"""
Incident Memory Types — shared data models for incident memory.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class Severity(str, Enum):
    SEV1 = "SEV-1"
    SEV2 = "SEV-2"
    SEV3 = "SEV-3"
    SEV4 = "SEV-4"


class ActionResult(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    NOT_APPLICABLE = "not_applicable"


class IncidentStatus(str, Enum):
    ACTIVE = "active"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"


class AttemptedAction(BaseModel):
    action: str
    result: ActionResult
    notes: Optional[str] = None
    timestamp: Optional[datetime] = None


class IncidentMetrics(BaseModel):
    latency_ms: Optional[float] = None
    error_rate: Optional[float] = None
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None
    db_cpu_percent: Optional[float] = None
    db_connections: Optional[int] = None
    throughput_rps: Optional[float] = None


class Incident(BaseModel):
    """Full incident data model."""
    incident_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    service: str
    environment: str = "production"
    severity: Severity = Severity.SEV2
    status: IncidentStatus = IncidentStatus.ACTIVE

    # Symptom information
    symptoms: list[str] = []
    metrics: Optional[IncidentMetrics] = None
    logs_summary: Optional[str] = None
    recent_changes: list[str] = []

    # Investigation
    hypotheses: list[str] = []
    attempted_actions: list[AttemptedAction] = []

    # Resolution
    root_cause: Optional[str] = None
    successful_resolution: Optional[str] = None
    resolution_time_minutes: Optional[int] = None
    lessons_learned: list[str] = []

    # Memory tracking
    memory_retained: bool = False


class CreateIncidentRequest(BaseModel):
    service: str
    environment: str = "production"
    severity: Severity = Severity.SEV2
    symptoms: list[str]
    metrics: Optional[IncidentMetrics] = None
    logs_summary: Optional[str] = None
    recent_changes: list[str] = []


class RecordActionRequest(BaseModel):
    action: str
    result: ActionResult
    notes: Optional[str] = None


class ResolveIncidentRequest(BaseModel):
    root_cause: str
    successful_resolution: str
    resolution_time_minutes: int
    lessons_learned: list[str] = []


class AnalysisResult(BaseModel):
    """Result of incident analysis."""
    incident_id: str
    
    # Memory recall
    has_historical_memories: bool = False
    historical_memories_text: str = ""
    
    # Comparison
    matching_signals: list[str] = []
    different_signals: list[str] = []
    
    # Hypotheses
    hypotheses: list[dict] = []
    
    # Recommendation
    recommended_action: str = ""
    recommendation_reason: str = ""
    historical_evidence: str = ""
    
    # Observability
    stages_completed: list[str] = []
    memory_state: str = "empty"  # "empty", "historical", "learned"
