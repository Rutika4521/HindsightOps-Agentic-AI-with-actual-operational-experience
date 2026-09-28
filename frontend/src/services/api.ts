// API service — all backend communication
import axios from 'axios';

const BASE = 'http://localhost:8000/api';
const api = axios.create({ baseURL: BASE, timeout: 60000 });

// ─── Types ────────────────────────────────────────────────────────────────────

export interface IncidentMetrics {
  latency_ms?: number;
  error_rate?: number;
  cpu_percent?: number;
  memory_percent?: number;
  db_cpu_percent?: number;
  db_connections?: number;
  throughput_rps?: number;
}

export interface AttemptedAction {
  action: string;
  result: 'success' | 'failed' | 'partial' | 'not_applicable';
  notes?: string;
  timestamp?: string;
}

export interface Incident {
  incident_id: string;
  timestamp: string;
  service: string;
  environment: string;
  severity: string;
  status: string;
  symptoms: string[];
  metrics?: IncidentMetrics;
  logs_summary?: string;
  recent_changes: string[];
  hypotheses: string[];
  attempted_actions: AttemptedAction[];
  root_cause?: string;
  successful_resolution?: string;
  resolution_time_minutes?: number;
  lessons_learned: string[];
  memory_retained: boolean;
}

export interface Hypothesis {
  hypothesis: string;
  supporting_evidence: string;
  contradicting_evidence: string;
  historical_evidence: string;
  priority: 'high' | 'medium' | 'low';
}

export interface AnalysisResult {
  incident_id: string;
  has_historical_memories: boolean;
  historical_memories_text: string;
  matching_signals: string[];
  different_signals: string[];
  hypotheses: Hypothesis[];
  recommended_action: string;
  recommendation_reason: string;
  historical_evidence: string;
  stages_completed: string[];
  memory_state: 'empty' | 'historical' | 'learned';
}

export interface CreateIncidentPayload {
  service: string;
  environment: string;
  severity: string;
  symptoms: string[];
  metrics?: IncidentMetrics;
  logs_summary?: string;
  recent_changes: string[];
}

export interface ResolveIncidentPayload {
  root_cause: string;
  successful_resolution: string;
  resolution_time_minutes: number;
  lessons_learned: string[];
}

export interface SeedStatus {
  seeding: boolean;
  seeded_count: number;
  total: number;
  error?: string;
}

// ─── Incidents ────────────────────────────────────────────────────────────────

export const createIncident = (data: CreateIncidentPayload) =>
  api.post<Incident>('/incidents', data).then(r => r.data);

export const listIncidents = () =>
  api.get<Incident[]>('/incidents').then(r => r.data);

export const getIncident = (id: string) =>
  api.get<Incident>(`/incidents/${id}`).then(r => r.data);

export const analyzeIncident = (id: string) =>
  api.post<AnalysisResult>(`/incidents/${id}/analyze`).then(r => r.data);

export const recordAction = (id: string, action: string, result: string, notes?: string) =>
  api.post(`/incidents/${id}/actions`, { action, result, notes }).then(r => r.data);

export const resolveIncident = (id: string, data: ResolveIncidentPayload) =>
  api.post(`/incidents/${id}/resolve`, data).then(r => r.data);

// ─── Memory ──────────────────────────────────────────────────────────────────

export const listMemories = () =>
  api.get('/memory').then(r => r.data);

export const getMemoryStats = () =>
  api.get('/memory/stats').then(r => r.data);

// ─── Demo Controls ───────────────────────────────────────────────────────────

export const demoReset = () =>
  api.post('/demo/reset').then(r => r.data);

export const demoSeed = () =>
  api.post('/demo/seed').then(r => r.data);

export const demoSeedStatus = () =>
  api.get<SeedStatus>('/demo/seed-status').then(r => r.data);

export const demoCreateIncident = () =>
  api.post('/demo/create-incident').then(r => r.data);

// ─── Health ──────────────────────────────────────────────────────────────────

export const healthCheck = () =>
  api.get('/health').then(r => r.data);
