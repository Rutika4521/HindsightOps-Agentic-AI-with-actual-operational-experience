import React, { useEffect, useState } from 'react';
import { listMemories, getMemoryStats } from '../services/api';
import { Brain, Database, RefreshCw, Clock } from 'lucide-react';

export default function MemoryExplorerPage() {
  const [memories, setMemories] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const [mem, st] = await Promise.all([listMemories(), getMemoryStats()]);
      setMemories(mem.memories || []);
      setStats(st);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e.message || 'Failed to load memories');
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <Brain className="w-7 h-7 text-blue-400" /> Memory Explorer
          </h2>
          <p className="text-gray-400 text-sm mt-1">
            Persistent incident knowledge stored in Hindsight
          </p>
        </div>
        <button
          onClick={load}
          disabled={loading}
          className="flex items-center gap-2 bg-gray-800 hover:bg-gray-700 text-white px-4 py-2 rounded-lg text-sm transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Stats */}
      {stats?.success && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: 'Memory Bank', value: stats.stats?.bank_id || stats.bank_id || '—', icon: Database },
            { label: 'Memories', value: stats.stats?.memory_count ?? '—', icon: Brain },
            { label: 'Documents', value: stats.stats?.document_count ?? '—', icon: Brain },
            { label: 'Entities', value: stats.stats?.entity_count ?? '—', icon: Brain },
          ].map(s => (
            <div key={s.label} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <p className="text-gray-400 text-xs mb-1">{s.label}</p>
              <p className="text-white font-bold text-lg">{String(s.value)}</p>
            </div>
          ))}
        </div>
      )}

      {error && (
        <div className="bg-red-950 border border-red-800 rounded-lg p-4 text-red-300 text-sm">
          {error}
        </div>
      )}

      {/* Memory list */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-800">
          <h3 className="text-white font-semibold">
            Stored Memories ({memories.length})
          </h3>
          <p className="text-gray-500 text-xs mt-0.5">Each entry is a resolved incident experience recalled by future investigations</p>
        </div>

        {loading && memories.length === 0 && (
          <div className="p-8 text-center text-gray-500 text-sm">Loading memories from Hindsight…</div>
        )}

        {!loading && memories.length === 0 && !error && (
          <div className="p-8 text-center">
            <Brain className="w-10 h-10 text-gray-700 mx-auto mb-3" />
            <p className="text-gray-500 text-sm">No memories stored yet.</p>
            <p className="text-gray-600 text-xs mt-1">Use Demo Controls to seed historical incidents.</p>
          </div>
        )}

        <div className="divide-y divide-gray-800">
          {memories.map((mem, i) => (
            <div key={mem.id || i} className="p-5 hover:bg-gray-800/40 transition-colors">
              <div className="flex items-start justify-between gap-3 mb-2">
                <div className="flex flex-wrap gap-1.5">
                  {(mem.tags || []).slice(0, 5).map((tag: string) => (
                    <span key={tag} className="text-xs bg-blue-950 text-blue-300 border border-blue-900 px-2 py-0.5 rounded-full">
                      {tag}
                    </span>
                  ))}
                </div>
                {mem.created_at && (
                  <div className="flex items-center gap-1 text-xs text-gray-500 flex-shrink-0">
                    <Clock className="w-3 h-3" />
                    {new Date(mem.created_at).toLocaleDateString()}
                  </div>
                )}
              </div>
              <pre className="text-xs text-gray-400 whitespace-pre-wrap font-mono leading-relaxed max-h-48 overflow-y-auto">
                {(mem.content || '').slice(0, 600)}{(mem.content || '').length > 600 ? '…' : ''}
              </pre>
            </div>
          ))}
        </div>
      </div>

      {/* Hindsight attribution */}
      <div className="text-center text-xs text-gray-600">
        Memory powered by{' '}
        <a href="https://hindsight.vectorize.io" target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:text-blue-400">
          Hindsight
        </a>
        {' '}— Agent Memory That Learns
      </div>
    </div>
  );
}
