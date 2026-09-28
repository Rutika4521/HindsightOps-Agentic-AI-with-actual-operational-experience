import React, { useState } from 'react';
import { Incident } from '../services/api';

interface Props {
  incident: Incident;
  onRecord: (action: string, result: string, notes: string) => void;
  onResolve: () => void;
  disabled?: boolean;
}

const RESULT_OPTIONS = [
  { value: 'success', label: 'Resolved', color: 'bg-green-700 hover:bg-green-600 text-white' },
  { value: 'failed', label: 'Failed', color: 'bg-red-700 hover:bg-red-600 text-white' },
  { value: 'partial', label: 'Partial', color: 'bg-yellow-700 hover:bg-yellow-600 text-white' },
  { value: 'not_applicable', label: 'N/A', color: 'bg-gray-700 hover:bg-gray-600 text-white' },
];

export function ActionPanel({ incident, onRecord, onResolve, disabled }: Props) {
  const [action, setAction] = useState('');
  const [notes, setNotes] = useState('');
  const [pendingResult, setPendingResult] = useState('');

  const handleRecord = (result: string) => {
    if (!action.trim()) return;
    setPendingResult(result);
    onRecord(action.trim(), result, notes.trim());
    setAction('');
    setNotes('');
    setPendingResult('');
  };

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
      <div className="px-5 py-4 border-b border-gray-800">
        <h3 className="text-white font-semibold">Record Action</h3>
        <p className="text-gray-400 text-xs mt-0.5">
          <span className="text-yellow-400 text-xs font-medium">SIMULATED ACTION</span>
          {' '} — no real infrastructure is modified
        </p>
      </div>

      {incident.attempted_actions.length > 0 && (
        <div className="px-5 py-3 border-b border-gray-800">
          <p className="text-xs text-gray-500 mb-2 uppercase tracking-wide">Actions Taken</p>
          <div className="space-y-1.5">
            {incident.attempted_actions.map((a, i) => (
              <div key={i} className="flex items-center gap-2 text-sm">
                <span className={`text-xs px-2 py-0.5 rounded font-medium ${
                  a.result === 'success' ? 'bg-green-900 text-green-300' :
                  a.result === 'failed' ? 'bg-red-900 text-red-300' :
                  a.result === 'partial' ? 'bg-yellow-900 text-yellow-300' :
                  'bg-gray-800 text-gray-400'
                }`}>{a.result.toUpperCase()}</span>
                <span className="text-gray-300">{a.action}</span>
                {a.notes && <span className="text-gray-500 text-xs">— {a.notes}</span>}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="p-5 space-y-3">
        <div>
          <label className="block text-xs text-gray-400 mb-1.5">Action Taken</label>
          <input
            value={action}
            onChange={e => setAction(e.target.value)}
            disabled={disabled}
            placeholder="e.g. Rollback deployment to v2.4.0"
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500 disabled:opacity-50"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1.5">Notes (optional)</label>
          <input
            value={notes}
            onChange={e => setNotes(e.target.value)}
            disabled={disabled}
            placeholder="Latency returned to normal within 60 seconds"
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500 disabled:opacity-50"
          />
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {RESULT_OPTIONS.map(r => (
            <button
              key={r.value}
              onClick={() => handleRecord(r.value)}
              disabled={disabled || !action.trim()}
              className={`text-sm px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed ${r.color}`}
            >
              {r.label}
            </button>
          ))}
        </div>
        <div className="pt-2 border-t border-gray-800">
          <button
            onClick={onResolve}
            disabled={disabled}
            className="text-sm text-green-400 hover:text-green-300 border border-green-800 hover:border-green-600 px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
          >
            Mark as Resolved & Learn →
          </button>
        </div>
      </div>
    </div>
  );
}
