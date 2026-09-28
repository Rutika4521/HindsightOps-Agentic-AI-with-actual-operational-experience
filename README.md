# Incident Memory Commander

> **"An AI incident investigator that learns from what actually happened."**

[![Hindsight](https://img.shields.io/badge/memory-Hindsight-blue)](https://hindsight.vectorize.io)
[![Groq](https://img.shields.io/badge/llm-Groq-orange)](https://groq.com)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-green)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/frontend-React%20+%20TypeScript-blue)](https://react.dev)

---

## What it does

Incident Memory Commander is an AI-powered incident-response assistant for software engineering and DevOps teams. Unlike generic AI tools, it **remembers every past incident** — what symptoms appeared, what engineers tried, what failed, what worked, and why — and uses that accumulated operational experience to give better recommendations on the next incident.

## The Problem

When a production incident occurs at 3AM, engineers are under pressure to diagnose and resolve quickly. They often:
- Repeat investigation steps that failed in similar past incidents
- Miss patterns that were discovered in previous incidents
- Have to manually search runbooks and post-mortems
- Give generic "check the logs" advice when historical evidence exists

## Why Memory Matters

The critical insight: **the difference between a generic recommendation and a targeted one is experience**.

| Without Memory | With Memory |
|---|---|
| "Check recent deployments, inspect logs, monitor metrics." | "Roll back the deployment. Two highly similar incidents with this exact pattern were caused by recent deployments. Database metrics were normal in both — which matches the current incident." |

## Why Hindsight

[Hindsight](https://hindsight.vectorize.io) is purpose-built persistent agent memory. It:
- Stores structured incident experiences, not just raw text
- Recalls semantically relevant memories using a query
- Learns from every resolved incident
- Enables the "accumulating operational experience" loop that makes this tool valuable

**Hindsight is not a database. It is not an optional feature. It is the core mechanism that makes recommendations improve over time.**

## Architecture

```
                    ENGINEER
                       │
                       ▼
               WEB INTERFACE (React)
                       │
                       ▼
               INCIDENT API (FastAPI)
                       │
                       ▼
              INCIDENT AGENT (Python)
              ┌────────┴────────┐
              ▼                 ▼
        HINDSIGHT           GROQ LLM
         MEMORY             REASONING
        (recall)             (analyze)
              └────────┬────────┘
                       ▼
               RECOMMENDATION
                       │
                       ▼
             ENGINEER TAKES ACTION
                       │
                       ▼
                   RESULT
                       │
                       ▼
              HINDSIGHT RETAIN
           (new memory for future)
```

## Memory Lifecycle

```
INCIDENT CREATED
      │
      ▼ Stage 1: Understand
EXTRACT: service, symptoms, metrics, changes

      ▼ Stage 2: Recall (Hindsight)
QUERY: "payments-api latency spike, recent deployment, normal DB"
RETRIEVE: INC-017, INC-031, INC-038 experiences

      ▼ Stage 3: Compare
MATCH: same symptom pattern, same service, same deployment signal
DIFF: INC-036 had high DB CPU (different root cause)

      ▼ Stage 4: Hypotheses
RANK: bad deployment (high) > DB issue (low) > network (low)

      ▼ Stage 5: Recommend
"Investigate the recent deployment — rollback first"

      ▼ Stage 6: Engineer acts
ACTION: Rollback deployment → RESOLVED

      ▼ Stage 7: Learn
RETAIN in Hindsight:
  - incident_id, service, symptoms, metrics
  - what failed: restart, DB pool increase
  - what worked: rollback
  - lessons learned

      ▼ Stage 8: Future
NEXT INCIDENT → recalls this + previous → even better recommendation
```

## Agent Workflow

The agent runs 5 explicit stages for every incident:

1. **Incident Understanding** — extract service, environment, symptoms, metrics, recent changes
2. **Hindsight Recall** — semantic search against historical incident memories
3. **Historical Comparison** — match signals, identify differences
4. **Hypothesis Generation** — ranked by likelihood using historical evidence
5. **Recommendation** — evidence-based, citing specific historical incidents

## Before vs After

### PART 1: No Memory (generic)

```
Incident: payments-api, latency +340%, 500 errors 18%, recent deployment, DB normal

Recommendation:
"Check recent deployments, inspect database connections,
 review application logs, and monitor infrastructure metrics."
```

### PART 2: With Historical Memory (specific)

```
Historical memories recalled:
  INC-017: deployment 8min ago → restart failed → rollback resolved
  INC-031: deployment 11min ago → DB check found nothing → rollback resolved
  INC-038: deployment 6min ago → DB normal → rollback resolved
  INC-036: NO deployment → DB CPU 91% → index fix resolved

Recommendation:
"Roll back the deployment immediately.

Three highly similar incidents (INC-017, INC-031, INC-038) with this
exact pattern — latency spike + recent deployment + normal DB metrics —
were all caused by bad deployments and resolved by rollback.

INC-036 had elevated DB CPU (91%), which is absent here,
making that root cause unlikely."
```

### PART 3: Learn

```
Engineer: Rollback → RESOLVED in 10 minutes
System: New incident experience retained in Hindsight ✓
```

### PART 4: Future incident recalls the new memory immediately.

## Tech Stack

| Layer | Technology |
|---|---|
| Memory | [Hindsight Cloud](https://hindsight.vectorize.io) (`hindsight-client==0.10.1`) |
| LLM | [Groq](https://groq.com) (`llama-3.3-70b-versatile`) |
| Backend | Python + FastAPI + uvicorn |
| Frontend | React + TypeScript + Vite + Tailwind CSS |
| HTTP client | Axios |

## Project Structure

```
incident-memory-commander/
├── backend/
│   ├── main.py                    # FastAPI app
│   ├── api/
│   │   ├── incidents.py           # CRUD + analyze + resolve
│   │   ├── memory.py              # Memory Explorer API
│   │   ├── demo.py                # Demo controls (reset/seed)
│   │   ├── health.py              # Health check
│   │   └── deps.py                # Dependency injection
│   ├── agents/
│   │   └── incident_agent.py      # Multi-stage analysis agent
│   ├── memory/                    # ← HINDSIGHT INTEGRATION (isolated)
│   │   ├── hindsight_client.py    # All Hindsight API calls
│   │   ├── incident_memory.py     # Incident-specific memory ops
│   │   └── memory_types.py        # Shared data models
│   ├── services/
│   │   └── incident_store.py      # In-memory session store
│   └── data/
│       └── synthetic_incidents.py # 21 realistic historical incidents
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── InvestigatePage.tsx   # Main investigation workflow
│       │   ├── MemoryExplorerPage.tsx
│       │   └── DemoPage.tsx          # Demo controls
│       ├── components/
│       │   ├── IncidentForm.tsx
│       │   ├── AnalysisPanel.tsx
│       │   ├── ActionPanel.tsx
│       │   ├── ResolutionPanel.tsx
│       │   ├── IncidentTimeline.tsx
│       │   └── MemoryBadge.tsx
│       └── services/
│           └── api.ts                # All backend calls
├── .env.example
├── requirements.txt
├── start_backend.bat
└── start_frontend.bat
```

## Environment Variables

```env
# Hindsight Cloud
HINDSIGHT_API_KEY=your_key_here
HINDSIGHT_BASE_URL=https://api.hindsight.vectorize.io/v1
HINDSIGHT_BANK_ID=incident-memory-commander

# Groq LLM
GROQ_API_KEY=your_key_here
LLM_MODEL=llama-3.3-70b-versatile
```

## Installation

```bash
# 1. Clone
git clone <repo>
cd incident-memory-commander

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install frontend dependencies
cd frontend
npm install
cd ..

# 4. Configure
cp .env.example .env
# Edit .env with your Hindsight and Groq API keys
```

## Running Locally

**Terminal 1 — Backend:**
```bash
# Windows
start_backend.bat

# or directly
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 — Frontend:**
```bash
# Windows
start_frontend.bat

# or directly
cd frontend
npm run dev
```

**Open browser:** http://localhost:5173

## Seeding Incidents

Navigate to **Demo Controls** tab and click **"Seed Historical Incidents"**.

This loads 21 realistic incidents into Hindsight memory. Progress is shown in real time.

Alternatively via API:
```bash
curl -X POST http://localhost:8000/api/demo/seed
```

## Demo Scenario (2-3 minutes)

1. **Demo Controls** → Reset (clears all memory)
2. **Demo Controls** → Create Demo Incident
3. **Investigate** → select the incident → **Analyze** → observe *generic* recommendation
4. **Demo Controls** → Seed Historical Incidents (wait ~30s)
5. **Demo Controls** → Create Demo Incident (new one)
6. **Investigate** → **Analyze** → observe *specific* recommendation citing INC-017, INC-031
7. Record action: "Rollback deployment" → Resolved
8. Resolve incident → **Save to Hindsight**
9. Create another incident → Analyze → newly learned experience appears in recall

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/incidents` | Create incident |
| GET | `/api/incidents` | List incidents |
| POST | `/api/incidents/{id}/analyze` | Run full analysis |
| POST | `/api/incidents/{id}/actions` | Record action |
| POST | `/api/incidents/{id}/resolve` | Resolve + retain memory |
| GET | `/api/memory` | List all Hindsight memories |
| GET | `/api/memory/stats` | Memory bank stats |
| POST | `/api/demo/reset` | Clear all memory |
| POST | `/api/demo/seed` | Seed historical incidents |
| GET | `/api/demo/seed-status` | Seed progress |
| POST | `/api/demo/create-incident` | Create demo incident |
| GET | `/api/health` | System health check |

## Limitations

- Hindsight recall quality depends on how incidents were originally described
- Session incidents are in-memory only (restart clears them; Hindsight memories persist)
- Actions are simulated — no real infrastructure is modified

## Future Improvements

- Persistent incident storage (PostgreSQL/SQLite)
- Slack/PagerDuty integration for real alert ingestion
- Automated root cause classification
- Runbook attachment to memory
- Multi-team memory banks
- Incident similarity scoring display

---

*Powered by [Hindsight](https://hindsight.vectorize.io) — Agent Memory That Learns*
