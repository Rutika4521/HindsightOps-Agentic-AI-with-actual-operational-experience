import React, { useState } from 'react';
import { Incident, ResolveIncidentPayload } from '../services/api';
import { Loader2, Plus, X } from 'lucide-react';

interface Props { incident: Incident; onResolve: (p: ResolveIncidentPayload) => void; loading?: boolean; }

export function ResolutionPanel({ incident, onResolve, loading }: Props) {
  const [rootCause, setRootCause] = useState('');
  const [resolution, setResolution] = useState('');
  const [time, setTime] = useState('');
  const [lessons, setLessons] = useState(['']);

  const addLesson = () => setLessons(l => [...l, '']);
  const setLesson = (i: number, v: string) => setLessons(l => l.map((x, j) => j === i ? v : x));
  const removeLesson = (i: number) => setLessons(l => l.filter((_, j) => j !== i));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onResolve({
      root_cause: rootCause,
      successful_resolution: resolution,
      resolution_time_minutes: parseInt(time) || 0,
      lessons_learned: lessons.filter(Boolean),
    });
  };

  return (
    <form onSubmit={handleSubmit} className="bg-green-950 border border-green-800 rounded-xl overflow-hidden">
      <div className="px-5 py-4 border-b border-green-900">
        <h3 className="text-green-300 font-semibold">Resolve & Learn</h3>
        <p className="text-green-600 text-xs mt-0.5">
          This will store the incident experience into Hindsight memory for future investigations
        </p>
      </div>
      <div className="p-5 space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-green-400 mb-1.5">Root Cause *</label>
            <input value={rootCause} onChange={e => setRootCause(e.target.value)} required
              placeholder="Bad deployment — v2.4.1 introduced…"
              className="w-full bg-green-900/30 border border-green-800 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-green-500" />
          </div>
          <div>
            <label className="block text-xs text-green-400 mb-1.5">Successful Resolution *</label>
            <input value={resolution} onChange={e => setResolution(e.target.value)} required
              placeholder="Rollback deployment to v2.4.0"
              className="w-full bg-green-900/30 border border-green-800 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-green-500" />
          </div>
        </div>
        <div className="w-32">
          <label className="block text-xs text-green-400 mb-1.5">Resolution Time (min)</label>
          <input type="number" value={time} onChange={e => setTime(e.target.value)}
            placeholder="12"
            className="w-full bg-green-900/30 border border-green-800 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-green-500" />
        </div>
        <div>
          <label className="block text-xs text-green-400 mb-1.5">Lessons Learned (will be stored in Hindsight)</label>
          <div className="space-y-2">
            {lessons.map((l, i) => (
              <div key={i} className="flex gap-2">
                <input value={l} onChange={e => setLesson(i, e.target.value)}
                  placeholder="Recent deployment was the key signal"
                  className="flex-1 bg-green-900/30 border border-green-800 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-green-500" />
                {lessons.length > 1 && (
                  <button type="button" onClick={() => removeLesson(i)} className="text-green-700 hover:text-red-400 p-2">
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
            ))}
          </div>
          <button type="button" onClick={addLesson} className="mt-2 flex items-center gap-1.5 text-xs text-green-400 hover:text-green-300">
            <Plus className="w-3.5 h-3.5" /> Add lesson
          </button>
        </div>
        <button type="submit" disabled={loading}
          className="w-full bg-green-700 hover:bg-green-600 text-white font-semibold py-3 rounded-xl transition-colors flex items-center justify-center gap-2 disabled:opacity-60">
          {loading && <Loader2 className="w-4 h-4 animate-spin" />}
          Save Incident Experience to Hindsight →
        </button>
      </div>
    </form>
  );
}
