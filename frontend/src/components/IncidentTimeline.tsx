import React from 'react';
import { Clock } from 'lucide-react';

interface Event { time: string; label: string; type: string; }
interface Props { events: Event[]; }

const typeStyles: Record<string, string> = {
  create: 'border-blue-700 text-blue-400',
  memory: 'border-purple-700 text-purple-400',
  analysis: 'border-yellow-700 text-yellow-400',
  recommend: 'border-blue-600 text-blue-300',
  success: 'border-green-700 text-green-400',
  failed: 'border-red-700 text-red-400',
  warn: 'border-orange-700 text-orange-400',
  info: 'border-gray-700 text-gray-400',
};

export function IncidentTimeline({ events }: Props) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-800 flex items-center gap-2">
        <Clock className="w-4 h-4 text-gray-500" />
        <h3 className="text-white text-sm font-semibold">Investigation Timeline</h3>
      </div>
      <div className="p-4">
        {events.length === 0 ? (
          <p className="text-gray-600 text-xs text-center py-6">Timeline will populate during investigation</p>
        ) : (
          <div className="space-y-3">
            {events.map((e, i) => (
              <div key={i} className={`border-l-2 pl-3 ${typeStyles[e.type] || typeStyles.info}`}>
                <p className="text-xs font-mono text-gray-500">{e.time}</p>
                <p className="text-xs mt-0.5">{e.label}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
