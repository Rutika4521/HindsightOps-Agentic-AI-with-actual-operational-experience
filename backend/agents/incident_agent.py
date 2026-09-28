"""
Incident Analysis Agent — orchestrates the 8-stage investigation workflow.

Uses Groq LLM with tool calling and Hindsight memory to produce
evidence-based recommendations for incident response.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Optional

from groq import AsyncGroq

from backend.memory.hindsight_client import HindsightMemoryClient
from backend.memory.incident_memory import IncidentMemory
from backend.memory.memory_types import (
    AnalysisResult,
    Incident,
    IncidentMetrics,
)

logger = logging.getLogger(__name__)

GROQ_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")


def _build_analysis_prompt(incident: Incident, recalled_memories: str) -> str:
    """Build the full prompt for the incident analysis agent."""
    incident_desc = f"""
SERVICE: {incident.service}
ENVIRONMENT: {incident.environment}
SEVERITY: {incident.severity}
TIMESTAMP: {incident.timestamp.isoformat()}

SYMPTOMS:
{chr(10).join(f'- {s}' for s in incident.symptoms)}

METRICS:
{_format_metrics(incident.metrics)}

RECENT CHANGES:
{chr(10).join(f'- {c}' for c in incident.recent_changes) if incident.recent_changes else '- None reported'}

LOGS SUMMARY:
{incident.logs_summary or 'Not provided'}
"""

    if recalled_memories and recalled_memories.strip():
        memory_section = f"""
=== HISTORICAL INCIDENT MEMORY (from Hindsight) ===
The following is real historical experience recalled from memory.
Use this to inform your analysis — identify similarities, differences,
previously failed actions, and successful resolutions.

{recalled_memories}
=== END OF HISTORICAL MEMORY ===
"""
        memory_state = "WITH_MEMORY"
    else:
        memory_section = """
=== HISTORICAL INCIDENT MEMORY ===
No relevant historical incidents found in memory.
Provide a general investigation plan based on best practices.
Clearly note that this recommendation is NOT based on historical evidence.
=== END ===
"""
        memory_state = "NO_MEMORY"

    return f"""You are an expert SRE and incident response agent analyzing a production incident.
Your job is to:
1. Understand the current incident
2. Compare it against historical experiences (if available)
3. Identify matching signals and important differences
4. Generate hypotheses ranked by likelihood
5. Recommend the single most important next investigation step

{memory_section}

=== CURRENT INCIDENT ===
{incident_desc}
=== END CURRENT INCIDENT ===

MEMORY STATE: {memory_state}

Respond with a JSON object in EXACTLY this format:
{{
  "matching_signals": ["list of signals that match historical incidents"],
  "different_signals": ["list of important differences from historical incidents"],
  "hypotheses": [
    {{
      "hypothesis": "description",
      "supporting_evidence": "what supports this",
      "contradicting_evidence": "what contradicts this",
      "historical_evidence": "what historical memory says about this",
      "priority": "high|medium|low"
    }}
  ],
  "recommended_action": "The single most important next step",
  "recommendation_reason": "Why this step, using historical evidence where available",
  "historical_evidence_summary": "Summary of relevant historical incidents used (or 'No historical memory available')",
  "lessons_from_history": ["list of key lessons from historical incidents that apply here"],
  "has_historical_basis": true|false
}}

IMPORTANT RULES:
- Only cite historical incidents if they were actually in the recalled memory above
- Never fabricate historical incident IDs or statistics
- If no memory available, set has_historical_basis=false and explain you're using best practices
- Keep recommended_action concise and actionable
- Rank hypotheses by likelihood given available evidence
"""


def _format_metrics(metrics: Optional[IncidentMetrics]) -> str:
    if not metrics:
        return "- No metrics provided"
    parts = []
    if metrics.latency_ms is not None:
        parts.append(f"- API Latency: {metrics.latency_ms:.0f}ms")
    if metrics.error_rate is not None:
        parts.append(f"- Error Rate: {metrics.error_rate*100:.1f}%")
    if metrics.cpu_percent is not None:
        parts.append(f"- App CPU: {metrics.cpu_percent:.1f}%")
    if metrics.memory_percent is not None:
        parts.append(f"- App Memory: {metrics.memory_percent:.1f}%")
    if metrics.db_cpu_percent is not None:
        parts.append(f"- Database CPU: {metrics.db_cpu_percent:.1f}%")
    if metrics.db_connections is not None:
        parts.append(f"- DB Connections: {metrics.db_connections}")
    if metrics.throughput_rps is not None:
        parts.append(f"- Throughput: {metrics.throughput_rps:.0f} RPS")
    return "\n".join(parts) if parts else "- No metrics provided"


class IncidentAgent:
    """
    Multi-stage incident analysis agent.
    
    Stages:
    1. Incident Understanding
    2. Memory Recall (Hindsight)
    3. Historical Comparison
    4. Hypothesis Generation
    5. Recommendation
    """

    def __init__(
        self,
        hindsight_client: HindsightMemoryClient,
        groq_client: AsyncGroq,
    ):
        self.incident_memory = IncidentMemory(hindsight_client)
        self.groq = groq_client
        self.model = GROQ_MODEL

    async def analyze_incident(self, incident: Incident) -> AnalysisResult:
        """
        Run the full incident analysis pipeline.
        
        Returns AnalysisResult with hypotheses, recommendations,
        and historical evidence from Hindsight.
        """
        result = AnalysisResult(incident_id=incident.incident_id)
        stages = []

        # STAGE 1: Incident Understanding
        stages.append("incident_understanding")
        logger.info(f"Stage 1: Understanding incident {incident.incident_id}")

        # STAGE 2: Memory Recall from Hindsight
        stages.append("hindsight_recall")
        logger.info(f"Stage 2: Recalling historical memories for {incident.incident_id}")
        recall_result = await self.incident_memory.recall_for_incident(incident)

        has_memories = recall_result.get("has_memories", False)
        memories_text = recall_result.get("results", "") or ""
        result.has_historical_memories = has_memories
        result.historical_memories_text = memories_text

        if has_memories:
            result.memory_state = "historical"
            logger.info("Historical memories found — using for analysis")
        else:
            result.memory_state = "empty"
            logger.info("No historical memories found — generic analysis")

        # STAGE 3-5: Comparison, Hypotheses, Recommendation via LLM
        stages.append("llm_analysis")
        logger.info(f"Stage 3-5: LLM analysis with memory_state={result.memory_state}")

        prompt = _build_analysis_prompt(incident, memories_text)

        try:
            chat_response = await self.groq.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert SRE incident analyst. "
                            "Always respond with valid JSON only, no markdown."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=2000,
                response_format={"type": "json_object"},
            )

            raw = chat_response.choices[0].message.content or "{}"
            analysis = json.loads(raw)

            result.matching_signals = analysis.get("matching_signals", [])
            result.different_signals = analysis.get("different_signals", [])
            result.hypotheses = analysis.get("hypotheses", [])
            result.recommended_action = analysis.get("recommended_action", "")
            result.recommendation_reason = analysis.get("recommendation_reason", "")
            result.historical_evidence = analysis.get("historical_evidence_summary", "")

            # Update memory state if LLM confirms historical basis
            if analysis.get("has_historical_basis") and has_memories:
                result.memory_state = "historical"
            elif not has_memories:
                result.memory_state = "empty"

            stages.append("recommendation_generated")
            logger.info(
                f"Analysis complete: {len(result.hypotheses)} hypotheses, "
                f"recommended: '{result.recommended_action[:60]}...'"
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            result.recommended_action = "Check recent deployments, inspect logs, and monitor metrics."
            result.recommendation_reason = "Analysis failed to parse — providing standard investigation steps."
            stages.append("recommendation_failed_fallback")

        except Exception as e:
            logger.error(f"LLM analysis failed: {e}", exc_info=True)
            result.recommended_action = "Check recent deployments, inspect logs, and monitor metrics."
            result.recommendation_reason = f"LLM unavailable ({type(e).__name__}) — providing standard steps."
            stages.append("llm_error_fallback")

        result.stages_completed = stages
        return result

    async def retain_resolved_incident(self, incident: Incident) -> dict[str, Any]:
        """
        Store a resolved incident into Hindsight memory.
        Called after resolution to enable future learning.
        """
        logger.info(f"Retaining resolved incident memory: {incident.incident_id}")
        return await self.incident_memory.retain_incident(incident)
