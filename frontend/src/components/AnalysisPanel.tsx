import React, { useState } from 'react';
import { AnalysisResult, Incident } from '../services/api';
import { Brain, CheckCircle, XCircle, ChevronDown, ChevronUp, Lightbulb } from 'lucide-react';

interface Props { analysis: AnalysisResult; incident: Incident; }

export function AnalysisPanel({ analysis, incident }: Props) {
  const [showMemory, setShowMemory] = useState(false);

  const priorityColor = (p: string) =>
    p === 'high' ? 'text-red-400 bg-red-950 border-red-900' :
    p === 'medium' ? 'text-yellow-400 bg-yellow-950 border-yellow-900' :
    'text-gray-400 bg-gray-800 border-gray-700';

  return (
    <div className="space-y-4">
      {/* Memory state banner */}
      {analysis.has_historical_memories ? (
        <div className="flex items-center gap-3 bg-blue-950 border border-blue-800 rounded-xl p-4">
          <Brain className="w-5 h-5 text-blue-400 flex-shrink-0" />
          <div>
            <p className="text-blue-300 font-semibold text-sm">Historical Memory Retrieved</p>
            <p className="text-blue-400 text-xs mt-0.5">
              Hindsight recalled relevant incident experiences — recommendation is based on historical evidence.
            </p>
          </div>
          <button onClick={() => setShowMemory(!showMemory)}
            className="ml-auto text-blue-400 hover:text-blue-200 flex-shrink-0">
            {showMemory ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      ) : (
        <div className="flex items-center gap-3 bg-gray-800 border border-gray-700 rounded-xl p-4">
          <Brain className="w-5 h-5 text-gray-500 flex-shrink-0" />
          <div>
            <p className="text-gray-300 font-semibold text-sm">No Historical Memory Found</p>
            <p className="text-gray-500 text-xs mt-0.5">Recommendation is based on best practices, not historical evidence.</p>
          </div>
        </div>
      )}

      {/* Raw memory text */}
      {showMemory && analysis.historical_memories_text && (
        <div className="bg-gray-900 border border-blue-900 rounded-xl p-4">
          <p className="text-xs text-blue-400 font-medium mb-2 uppercase tracking-wide">Raw Hindsight Recall</p>
          <pre className="text-xs text-gray-300 whitespace-pre-wrap font-mono leading-relaxed max-h-64 overflow-y-auto">
            {analysis.historical_memories_text}
          </pre>
        </div>
      )}

      {/* Signals */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {analysis.matching_signals.length > 0 && (
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <p className="text-xs text-green-400 font-semibold uppercase tracking-wide mb-3 flex items-center gap-1.5">
              <CheckCircle className="w-3.5 h-3.5" /> Matching Signals
            </p>
            <ul className="space-y-1.5">
              {analysis.matching_signals.map((s, i) => (
                <li key={i} className="text-sm text-gray-300 flex items-start gap-2">
                  <span className="text-green-500 mt-0.5">✓</span> {s}
                </li>
              ))}
            </ul>
          </div>
        )}
        {analysis.different_signals.length > 0 && (
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <p className="text-xs text-orange-400 font-semibold uppercase tracking-wide mb-3 flex items-center gap-1.5">
              <XCircle className="w-3.5 h-3.5" /> Differences
            </p>
            <ul className="space-y-1.5">
              {analysis.different_signals.map((s, i) => (
                <li key={i} className="text-sm text-gray-300 flex items-start gap-2">
                  <span className="text-orange-500 mt-0.5">✗</span> {s}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Hypotheses */}
      {analysis.hypotheses.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <div className="px-5 py-3 border-b border-gray-800">
            <p className="text-xs text-gray-400 font-semibold uppercase tracking-wide flex items-center gap-1.5">
              <Lightbulb className="w-3.5 h-3.5" /> Hypotheses
            </p>
          </div>
          <div className="divide-y divide-gray-800">
            {analysis.hypotheses.map((h, i) => (
              <div key={i} className="p-4">
                <div className="flex items-start justify-between gap-3 mb-2">
                  <p className="text-white text-sm font-medium">{h.hypothesis}</p>
                  <span className={`text-xs px-2 py-0.5 rounded-full border font-medium flex-shrink-0 ${priorityColor(h.priority)}`}>
                    {h.priority}
                  </span>
                </div>
                {h.supporting_evidence && (
                  <p className="text-xs text-gray-400 mt-1">
                    <span className="text-green-400">Supporting:</span> {h.supporting_evidence}
                  </p>
                )}
                {h.historical_evidence && (
                  <p className="text-xs text-blue-400 mt-1">
                    <span className="text-blue-300">History:</span> {h.historical_evidence}
                  </p>
                )}
                {h.contradicting_evidence && (
                  <p className="text-xs text-gray-500 mt-1">
                    <span className="text-orange-400">Against:</span> {h.contradicting_evidence}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendation */}
      <div className="bg-blue-950 border border-blue-800 rounded-xl p-5">
        <p className="text-xs text-blue-400 font-semibold uppercase tracking-wide mb-2">Recommended Next Step</p>
        <p className="text-white font-bold text-lg mb-3">{analysis.recommended_action}</p>
        <div className="border-t border-blue-900 pt-3">
          <p className="text-xs text-blue-300 font-medium mb-1">WHY?</p>
          <p className="text-blue-200 text-sm leading-relaxed">{analysis.recommendation_reason}</p>
        </div>
        {analysis.historical_evidence && analysis.historical_evidence !== 'No historical memory available' && (
          <div className="mt-3 border-t border-blue-900 pt-3">
            <p className="text-xs text-blue-300 font-medium mb-1">HISTORICAL EVIDENCE</p>
            <p className="text-blue-300 text-xs leading-relaxed opacity-90">{analysis.historical_evidence}</p>
          </div>
        )}
      </div>
    </div>
  );
}
