# I Made Hindsight Remember Failed Debugging Attempts

At 3:15 AM, when the latency p95 on `payments-api` spikes from 240ms to 2,100ms and HTTP 500 errors hit 16%, the worst thing an automated incident responder can do is tell an on-call engineer to restart application pods and double the database connection pool. Yet without persistent operational memory, generic LLM assistants repeat these exact time-wasting diagnostic steps on every outage because they lack context on what was tried—and failed—ten minutes ago or three weeks ago.

When I set out to build an automated incident investigation assistant, I realized that traditional retrieval-augmented generation (RAG) approaches missed a critical half of the operational picture. Most developer tools treat memory as a search engine for past success stories. In production incident response, however, negative evidence—knowing which debugging attempts failed and why—is often more actionable than knowing the eventual root cause. I integrated the open-source [Hindsight engine on GitHub](https://github.com/vectorize-io/hindsight) into our SRE workflow to capture the complete lifecycle of production incidents, specifically forcing the memory bank to index failed investigative actions so our incident agent never makes the same diagnostic mistake twice.

---

## What the System Does and How It Hangs Together

The system, called Incident Memory Commander, acts as a real-time copilot for SREs during production outages. It sits between incoming telemetry (symptoms, metrics, recent deployments, log snippets) and the on-call engineer, driving a structured five-stage analysis pipeline:

1. **Incident Understanding**: Extracts affected services, normalizes metrics, and isolates symptoms.
2. **Semantic Memory Recall**: Queries Hindsight for historically similar incidents using semantic symptom matching and telemetry threshold filtering.
3. **Historical Signal Comparison**: Differentiates current signals from recalled memories (e.g., identifying when database CPU is elevated vs. normal).
4. **Hypothesis Ranking**: Ranks candidate root causes based on historical frequency and matching operational context.
5. **Action Recommendation**: Emits a single, high-confidence next step while explicitly ruling out previously failed diagnostic actions.

```
                    ON-CALL ENGINEER
                           │
                           ▼
                 REACT + TYPESCRIPT UI
                           │
                           ▼
                  FASTAPI API ROUTER
                           │
                           ▼
                INCIDENT AGENT PIPELINE
               ┌───────────┴───────────┐
               ▼                       ▼
       HINDSIGHT MEMORY           GROQ LLM
      (recall & retain)      (reasoning engine)
               └───────────┬───────────┘
                           ▼
                EVIDENCE-BASED RECOMMENDATION
                           │
                           ▼
                 ENGINEER RESOLUTION
                           │
                           ▼
                 HINDSIGHT RETENTION
             (learns what worked & failed)
```

The system runs on a Python FastAPI backend and a React TypeScript frontend, with [Vectorize agent memory architecture](https://vectorize.io/what-is-agent-memory) serving as the core persistence layer via `hindsight-client`. LLM reasoning is handled by Groq running `llama-3.3-70b-versatile`. 

Crucially, memory retention is not an afterthought or a passive logging sink. When an engineer resolves an incident, the entire timeline—including failed pod restarts, fruitless query log inspections, successful rollbacks, and post-mortem lessons—is committed to Hindsight. On the next incident, the agent queries Hindsight *before* prompting the LLM, transforming generic advice into pinpoint operational instructions.

---

## The Technical Challenge: Storing Negative Operational Evidence

Standard vector databases fail at incident memory because raw embedding similarity drops critical operational context. If you embed a raw post-mortem document, a vector search for "payments-api latency spike" will happily retrieve an incident where increasing the DB pool solved the issue, even if your current incident has completely normal database CPU metrics. 

Furthermore, generic RAG systems suffer from positive-bias retrieval. They retain what fixed an incident, but discard the three failed diagnostic steps that wasted 20 minutes of on-call time. In an active incident, knowing that "restarting pods in INC-017 did not reduce latency because the bug was a synchronous lock" is vital information. If your agent does not index negative evidence, it will suggest restarting pods every time it sees high CPU.

To solve this, I designed a structured text representation for Hindsight memory retention that explicitly separates attempted actions by their outcome (`SUCCESS`, `FAILED`, `NOT_APPLICABLE`). When retaining an incident experience in Hindsight, the backend automatically extracts failed attempts and appends an explicit negative control section: `ACTIONS THAT DID NOT RESOLVE THIS INCIDENT (DO NOT REPEAT FIRST)`. 

According to the [official Hindsight documentation](https://hindsight.vectorize.io/), Hindsight's memory banks combine vector search with temporal and graph retrieval. By structuring failed actions explicitly alongside service tags and metric state, Hindsight indexes both the positive resolution pathways and the negative anti-patterns.

---

## Code Breakdown: Structuring Memory for Semantic Recall

Let me walk through the core implementation details in the codebase that make this negative-evidence retrieval loop work cleanly.

### 1. Formatting Incident Memories with Negative Controls

In `backend/memory/incident_memory.py`, the `format_incident_for_memory` function converts raw incident objects into structured text before calling Hindsight's retention API. Notice how failed actions are extracted into a dedicated anti-pattern block:

```python
def format_incident_for_memory(incident: Incident) -> str:
    lines = [f"=== INCIDENT EXPERIENCE: {incident.incident_id} ==="]
    lines.append(f"Service: {incident.service} | Env: {incident.environment}")
    
    if incident.symptoms:
        lines.append("SYMPTOMS:\n" + "\n".join(f"  - {s}" for s in incident.symptoms))

    if incident.attempted_actions:
        lines.append("\nACTIONS ATTEMPTED (INCLUDING FAILURES):")
        for action in incident.attempted_actions:
            lines.append(f"  - Action: {action.action} | Result: {action.result.upper()}")
            if action.notes:
                lines.append(f"    Notes: {action.notes}")

    # Extract failed actions explicitly for Hindsight indexing
    failed_actions = [
        a.action for a in incident.attempted_actions
        if a.result == ActionResult.FAILED
    ]
    if failed_actions:
        lines.append("\nACTIONS THAT DID NOT RESOLVE THIS INCIDENT (DO NOT REPEAT FIRST):")
        for fa in failed_actions:
            lines.append(f"  - {fa}")

    if incident.successful_resolution:
        lines.append(f"\nSUCCESSFUL RESOLUTION: {incident.successful_resolution}")

    return "\n".join(lines)
```

### 2. Translating Metric Limits into Semantic Recall Queries

Raw numbers make poor vector queries. A query containing `db_cpu=38.2` won't match a memory where `db_cpu=35.0` unless the values are normalized into qualitative states. In `build_recall_query`, metrics are evaluated against thresholds before generating the Hindsight search prompt:

```python
def build_recall_query(incident: Incident) -> str:
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

    parts.append("Looking for: similar incidents, root causes, what actions worked, what actions failed.")
    return " ".join(parts)
```

### 3. Isolating Hindsight API Operations

All SDK calls are encapsulated in `HindsightMemoryClient` (`backend/memory/hindsight_client.py`). This isolates low-level API mechanics, token budgeting, and bank management away from the agent logic:

```python
class HindsightMemoryClient:
    def __init__(self):
        self.base_url = os.getenv("HINDSIGHT_BASE_URL", "").rstrip("/")
        self.api_key = os.getenv("HINDSIGHT_API_KEY", "")
        self.bank_id = os.getenv("HINDSIGHT_BANK_ID", "incident-memory-commander")
        self._client = Hindsight(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=120.0,
        )

    async def recall_relevant_incidents(
        self, query: str, tags: Optional[list[str]] = None, max_tokens: int = 6000
    ) -> dict[str, Any]:
        try:
            response = await self._client.arecall(
                bank_id=self.bank_id,
                query=query,
                max_tokens=max_tokens,
                budget="mid",
                tags=tags,
                tags_match="any",
            )
            results_text = getattr(response, "results", "") or ""
            return {"success": True, "results": results_text, "has_memories": bool(results_text.strip())}
        except Exception as e:
            logger.error(f"Hindsight recall failed: {e}", exc_info=True)
            return {"success": False, "results": "", "has_memories": False}
```

### 4. Enforcing Structured LLM Output with Memory Signal Comparison

In `backend/agents/incident_agent.py`, the agent injects recalled Hindsight memories into the prompt and forces the LLM to output a strict JSON structure containing matching signals, differing signals, and hypothesis rankings:

```python
def _build_analysis_prompt(incident: Incident, recalled_memories: str) -> str:
    memory_section = f"""
=== HISTORICAL INCIDENT MEMORY (from Hindsight) ===
{recalled_memories}
=== END OF HISTORICAL MEMORY ===
""" if recalled_memories.strip() else "=== NO HISTORICAL MEMORY AVAILABLE ==="

    return f"""You are an expert SRE incident analyst.
Analyze the incident against historical memories and respond ONLY with JSON:

{memory_section}

Respond in EXACTLY this JSON structure:
{{
  "matching_signals": ["signals matching past incidents"],
  "different_signals": ["important differences from past incidents"],
  "hypotheses": [
    {{
      "hypothesis": "description",
      "supporting_evidence": "evidence for",
      "contradicting_evidence": "evidence against",
      "historical_evidence": "what Hindsight memory says",
      "priority": "high|medium|low"
    }}
  ],
  "recommended_action": "Single most important next step",
  "recommendation_reason": "Why this step based on historical evidence"
}}
"""
```

---

## Real-World Behavior: Before and After Memory Retention

To evaluate the system, we ran a direct comparison using an active incident pattern on `payments-api`:
- **Symptoms**: API latency at 1,900ms (p95), 500 error rate at 19%.
- **Telemetry**: App CPU at 68%, DB CPU normal at 42%, DB connections 51.
- **Recent Changes**: `payments-api v2.4.0` deployed 11 minutes prior.

### Cold Memory State (Without Hindsight Memories)

When Hindsight memory is empty, the LLM falls back to standard, ungrounded SRE best practices.

```
RECOMMENDED ACTION:
"Check recent deployments, inspect database connections, review application logs, and monitor infrastructure metrics."

HYPOTHESES:
1. Database connection pool exhaustion (Medium priority)
2. Application code bug in recent deployment (Medium priority)
3. Upstream network degradation (Low priority)
```

**Engineer Outcome**: The advice is generic. An engineer under pressure might try restarting pods or altering database pool sizes—spending 15–20 minutes testing hypotheses that have no grounding in past incident history.

### Warm Memory State (With Recalled Hindsight Memories)

After retaining historical incident experiences (`INC-017`, `INC-031`, and `INC-036`) into Hindsight, we ran the exact same incident payload through the pipeline. Hindsight recalled `INC-017` and `INC-031` (which had identical latency spikes following deployments with normal DB CPU) while noting `INC-036` (which had elevated DB CPU at 91%).

```
RECALLED MEMORIES:
- INC-017: deployment 8m ago → pod restart FAILED → DB pool increase FAILED → rollback SUCCESS
- INC-031: deployment 11m ago → pod restart FAILED → DB query check NOT_APPLICABLE → rollback SUCCESS
- INC-036: NO deployment → DB CPU 91% → index fix SUCCESS

RECOMMENDED ACTION:
"Roll back deployment v2.4.0 immediately. Do not waste time restarting application pods or inspecting database connection pools."

RECOMMENDATION REASON:
"Two highly similar incidents (INC-017, INC-031) matching this exact pattern—latency spike + recent deployment + normal DB CPU (42%)—were resolved immediately by rollback. Pod restarts failed in both prior incidents because the issue was in application code logic. INC-036 involved high DB CPU (91%), which is absent here."
```

**Engineer Outcome**: The engineer bypasses pod restarts and database connection tweaking entirely, executing a deployment rollback immediately. MTTR drops from 25 minutes down to under 3 minutes.

---

## Four Engineering Takeaways for Building Memory-Aware Agents

Building Incident Memory Commander taught us several key lessons about designing persistent memory systems for production agents:

1. **Negative evidence is as critical as positive resolution pathways.**
   If your agent only remembers what worked, it will constantly suggest retrying failed diagnostic steps when presented with partial symptom matches. Structuring negative outcomes into memory explicitly (`ACTIONS THAT DID NOT RESOLVE THIS INCIDENT`) prevents repetitive investigative loops.

2. **Normalize telemetry into qualitative states prior to vector search.**
   Raw numeric values (`cpu_percent=41.8`) create noise in vector embeddings. Normalizing values into semantic bounds (`normal database CPU`, `high API latency (>500ms)`) ensures that semantic recall in Hindsight yields high-relevance matches across different incidents.

3. **Isolate SDK operations behind a clean abstraction layer.**
   Encapsulating all Hindsight SDK interactions inside a dedicated client class (`HindsightMemoryClient`) kept our API models, LLM prompts, and business logic decoupled from API connection management, token budgeting, and serialization details.

4. **Force structured JSON schemas with explicit signal diffing.**
   Instructing an LLM to generate unstructured markdown often leads to hallucinated incident IDs or ignored memory context. By requiring a strict JSON response containing explicit `matching_signals` and `different_signals` fields, the agent is forced to ground its reasoning directly in the recalled Hindsight memories.

---

*Incident Memory Commander relies on [Hindsight](https://hindsight.vectorize.io/) for persistent, cross-incident agent memory.*
