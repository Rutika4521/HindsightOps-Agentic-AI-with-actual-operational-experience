import React, { useState, useCallback } from 'react';
import {
  createIncident, analyzeIncident, recordAction, resolveIncident,
  CreateIncidentPayload, Incident, AnalysisResult, ResolveIncidentPayload,
} from '../services/api';
import { IncidentForm } from '../components/IncidentForm';
import { AnalysisPanel } from '../components/AnalysisPanel';
import { ActionPanel } from '../components/ActionPanel';
import { ResolutionPanel } from '../components/ResolutionPanel';
import { IncidentTimeline } from '../components/IncidentTimeline';
import { MemoryBadge } from '../components/MemoryBadge';
import { Loader2, AlertTriangle } from 'lucide-react';

type Stage = 'form' | 'analyzing' | 'analyzed' | 'action' | 'resolving' | 'resolved';

export default function InvestigatePage() {
  const [stage, setStage] = useState<Stage>('form');
  const [incident, setIncident] = useState<Incident | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string>('');
  const [timelineEvents, setTimelineEvents] = useState<Array<{ time: string; label: string; type: string }>>([]);

  const addEvent = (label: string, type: string = 'info') => {
    const time = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    setTimelineEvents(prev => [...prev, { time, label, type }]);
  };

  const handleCreate = useCallback(async (payload: CreateIncidentPayload) => {
    setError('');
    try {
      setStage('analyzing');
      const created = await createIncident(payload);
      setIncident(created);
      addEvent(`Incident ${created.incident_id} created`, 'create');
      addEvent('Querying Hindsight memory…', 'memory');

      const result = await analyzeIncident(created.incident_id);
      setAnalysis(result);

      if (result.has_historical_memories) {
        addEvent(`Hindsight recalled historical memories`, 'memory');
        addEvent(`Analysis: ${result.hypotheses.length} hypotheses generated`, 'analysis');
        addEvent(`Recommendation: ${result.recommended_action.slice(0, 60)}…`, 'recommend');
      } else {
        addEvent('No historical memories found — generic recommendation', 'warn');
        addEvent(`Recommendation: ${result.recommended_action.slice(0, 60)}…`, 'recommend');
      }

      setStage('analyzed');
    } catch (e: any) {
      setError(e?.response?.data?.detail || e.message || 'Analysis failed');
      setStage('form');
    }
  }, []);

  const handleRecordAction = useCallback(async (action: string, result: string, notes: string) => {
    if (!incident) return;
    try {
      await recordAction(incident.incident_id, action, result, notes);
      addEvent(`Action recorded: ${action} → ${result.toUpperCase()}`, result === 'success' ? 'success' : 'failed');
      const updated = { ...incident, attempted_actions: [...incident.attempted_actions, { action, result: result as any, notes }] };
      setIncident(updated);
      setStage('action');
    } catch (e: any) {
      setError(e?.response?.data?.detail || e.message);
    }
  }, [incident]);

  const handleResolve = useCallback(async (payload: ResolveIncidentPayload) => {
    if (!incident) return;
    setStage('resolving');
    try {
      addEvent('Resolving incident…', 'info');
      const result = await resolveIncident(incident.incident_id, payload);
      addEvent('Incident resolved', 'success');
      addEvent('Retaining experience in Hindsight…', 'memory');

      if (result.memory_retained?.success) {
        addEvent('✓ New memory stored in Hindsight', 'success');
        addEvent('Future incidents will benefit from this experience', 'memory');
      }

      setIncident(result.incident);
      setStage('resolved');
    } catch (e: any) {
      setError(e?.response?.data?.detail || e.message);
      setStage('action');
    }
  }, [incident]);

  const handleReset = () => {
    setStage('form');
    setIncident(null);
    setAnalysis(null);
    setError('');
    setTimelineEvents([]);
  };

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Incident Investigation</h2>
          <p className="text-gray-400 text-sm mt-1">
            AI-powered root cause analysis with persistent memory
          </p>
        </div>
        {incident && (
          <div className="flex items-center gap-3">
            <MemoryBadge memoryState={analysis?.memory_state || 'empty'} />
            <button
              onClick={handleReset}
              className="text-sm text-gray-400 hover:text-white border border-gray-700 hover:border-gray-500 px-3 py-1.5 rounded-lg transition-colors"
            >
              New Incident
            </button>
          </div>
        )}
      </div>

      {error && (
        <div className="flex items-center gap-3 bg-red-950 border border-red-800 rounded-lg p-4 text-red-300">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span className="text-sm">{error}</span>
          <button onClick={() => setError('')} className="ml-auto text-red-400 hover:text-red-200">✕</button>
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
        {/* Main content */}
        <div className="xl:col-span-3 space-y-6">
          {/* Stage: Form */}
          {stage === 'form' && (
            <IncidentForm onSubmit={handleCreate} />
          )}

          {/* Stage: Analyzing */}
          {stage === 'analyzing' && (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-12 flex flex-col items-center gap-4">
              <Loader2 className="w-10 h-10 text-blue-500 animate-spin" />
              <p className="text-white font-semibold">Analyzing incident…</p>
              <p className="text-gray-400 text-sm">Querying Hindsight memory → LLM analysis → Generating recommendation</p>
            </div>
          )}

          {/* Stage: Analyzed / Action / Resolving / Resolved */}
          {(stage === 'analyzed' || stage === 'action' || stage === 'resolving' || stage === 'resolved') && analysis && incident && (
            <>
              <AnalysisPanel analysis={analysis} incident={incident} />
              <ActionPanel
                incident={incident}
                onRecord={handleRecordAction}
                onResolve={() => setStage('action')}
                disabled={stage === 'resolving' || stage === 'resolved'}
              />
              {(stage === 'action' || stage === 'resolving') && (
                <ResolutionPanel
                  incident={incident}
                  onResolve={handleResolve}
                  loading={stage === 'resolving'}
                />
              )}
              {stage === 'resolved' && incident.memory_retained && (
                <div className="bg-green-950 border border-green-800 rounded-xl p-6">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-2xl">✓</span>
                    <h3 className="text-green-300 font-bold text-lg">Incident Experience Retained in Hindsight</h3>
                  </div>
                  <p className="text-green-400 text-sm">
                    This resolved incident is now stored as persistent memory.
                    Future similar incidents will benefit from this experience —
                    what was tried, what failed, and what resolved it.
                  </p>
                </div>
              )}
            </>
          )}
        </div>

        {/* Sidebar: Timeline */}
        <div className="xl:col-span-1">
          <IncidentTimeline events={timelineEvents} />
        </div>
      </div>
    </div>
  );
}
