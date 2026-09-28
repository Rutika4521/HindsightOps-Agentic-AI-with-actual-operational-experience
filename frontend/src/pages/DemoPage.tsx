import React, { useState, useEffect, useCallback } from 'react';
import { demoReset, demoSeed, demoSeedStatus, demoCreateIncident, healthCheck, SeedStatus } from '../services/api';
import { Trash2, Database, Plus, CheckCircle, AlertCircle, Loader2, Zap, Brain, Activity } from 'lucide-react';

export default function DemoPage() {
  const [seedStatus, setSeedStatus] = useState<SeedStatus | null>(null);
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState<Record<string, boolean>>({});
  const [messages, setMessages] = useState<Array<{ text: string; type: 'success' | 'error' | 'info' }>>([]);
  const [polling, setPolling] = useState(false);

  const addMsg = (text: string, type: 'success' | 'error' | 'info' = 'info') => {
    setMessages(prev => [{ text, type }, ...prev].slice(0, 8));
  };

  const setLoad = (key: string, val: boolean) => setLoading(prev => ({ ...prev, [key]: val }));

  // Check health on mount
  useEffect(() => {
    healthCheck()
      .then(h => setHealth(h))
      .catch(e => setHealth({ status: 'error', error: e.message }));
    demoSeedStatus().then(s => setSeedStatus(s)).catch(() => {});
  }, []);

  // Poll seed status while seeding
  useEffect(() => {
    if (!seedStatus?.seeding) { setPolling(false); return; }
    setPolling(true);
    const interval = setInterval(async () => {
      try {
        const s = await demoSeedStatus();
        setSeedStatus(s);
        if (!s.seeding) {
          setPolling(false);
          addMsg(`✓ Seeded ${s.seeded_count}/${s.total} incidents into Hindsight`, 'success');
          clearInterval(interval);
        }
      } catch {
        setPolling(false);
        clearInterval(interval);
      }
    }, 1500);
    return () => clearInterval(interval);
  }, [seedStatus?.seeding]);

  const handleReset = async () => {
    setLoad('reset', true);
    try {
      await demoReset();
      setSeedStatus({ seeding: false, seeded_count: 0, total: 0 });
      addMsg('✓ Demo reset — Hindsight memory cleared, incidents cleared', 'success');
    } catch (e: any) {
      addMsg(`✗ Reset failed: ${e?.response?.data?.detail || e.message}`, 'error');
    } finally { setLoad('reset', false); }
  };

  const handleSeed = async () => {
    setLoad('seed', true);
    try {
      await demoSeed();
      const s = await demoSeedStatus();
      setSeedStatus(s);
      addMsg(`Seeding ${s.total} historical incidents into Hindsight…`, 'info');
    } catch (e: any) {
      addMsg(`✗ Seed failed: ${e?.response?.data?.detail || e.message}`, 'error');
    } finally { setLoad('seed', false); }
  };

  const handleCreateIncident = async () => {
    setLoad('incident', true);
    try {
      const res = await demoCreateIncident();
      addMsg(`✓ Demo incident created: ${res.incident?.incident_id}`, 'success');
    } catch (e: any) {
      addMsg(`✗ Create failed: ${e?.response?.data?.detail || e.message}`, 'error');
    } finally { setLoad('incident', false); }
  };

  const hindsightOk = health?.hindsight?.success;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">Demo Controls</h2>
        <p className="text-gray-400 text-sm mt-1">
          Control the before/after memory demonstration
        </p>
      </div>

      {/* Connection Status */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
          <Activity className="w-4 h-4" /> System Status
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <StatusItem
            label="Backend API"
            ok={!!health}
            value={health?.status === 'ok' ? 'Connected' : health ? 'Error' : 'Checking…'}
          />
          <StatusItem
            label="Hindsight Memory"
            ok={hindsightOk}
            value={hindsightOk ? `Connected (v${health?.hindsight?.api_version || '?'})` : health ? 'Not connected' : 'Checking…'}
          />
        </div>
        {!hindsightOk && health && (
          <p className="mt-3 text-xs text-red-400">
            ⚠ Hindsight not connected. Set HINDSIGHT_API_KEY and HINDSIGHT_BASE_URL in .env
          </p>
        )}
      </div>

      {/* Demo Scenario Steps */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
          <Zap className="w-4 h-4 text-yellow-400" /> Before/After Demo Scenario
        </h3>
        <ol className="space-y-3 text-sm text-gray-300">
          {[
            { n: 1, title: 'Reset', desc: 'Clear all memories → "no memory" state', action: 'Reset', handler: handleReset, key: 'reset', color: 'red' },
            { n: 2, title: 'Create demo incident', desc: 'payments-api latency spike + recent deployment', action: 'Create Demo Incident', handler: handleCreateIncident, key: 'incident', color: 'blue' },
            { n: 3, title: 'Analyze (WITHOUT memory)', desc: 'Go to Investigate → select the incident → Analyze → see generic recommendation', action: null, handler: null, key: null, color: 'gray' },
            { n: 4, title: 'Seed historical incidents', desc: 'Load 30+ incidents into Hindsight memory', action: 'Seed Historical Incidents', handler: handleSeed, key: 'seed', color: 'green' },
            { n: 5, title: 'Create another demo incident', desc: 'Same type of incident', action: 'Create Demo Incident', handler: handleCreateIncident, key: 'incident2', color: 'blue' },
            { n: 6, title: 'Analyze (WITH memory)', desc: 'Agent recalls INC-017, INC-031, INC-038 → targeted rollback recommendation', action: null, handler: null, key: null, color: 'gray' },
            { n: 7, title: 'Resolve + Learn', desc: 'Record "Rollback → resolved" → stored in Hindsight', action: null, handler: null, key: null, color: 'gray' },
            { n: 8, title: 'Future incident benefits', desc: 'New incident recalls the newly learned experience', action: null, handler: null, key: null, color: 'gray' },
          ].map(step => (
            <li key={step.n} className="flex items-start gap-3">
              <span className="flex-shrink-0 w-6 h-6 rounded-full bg-gray-800 border border-gray-700 text-xs text-gray-400 flex items-center justify-center font-bold">
                {step.n}
              </span>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-white">{step.title}</p>
                <p className="text-gray-500 text-xs mt-0.5">{step.desc}</p>
              </div>
              {step.action && step.handler && (
                <button
                  onClick={step.handler}
                  disabled={loading[step.key!] || polling}
                  className={`flex-shrink-0 text-xs px-3 py-1.5 rounded-lg font-medium disabled:opacity-50 transition-colors ${
                    step.color === 'red' ? 'bg-red-700 hover:bg-red-600 text-white' :
                    step.color === 'green' ? 'bg-green-700 hover:bg-green-600 text-white' :
                    'bg-blue-700 hover:bg-blue-600 text-white'
                  }`}
                >
                  {loading[step.key!] ? <Loader2 className="w-3 h-3 animate-spin" /> : step.action}
                </button>
              )}
            </li>
          ))}
        </ol>
      </div>

      {/* Seed Progress */}
      {(seedStatus?.seeding || (seedStatus?.seeded_count ?? 0) > 0) && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
            <Brain className="w-4 h-4 text-blue-400" /> Hindsight Seeding Progress
          </h3>
          <div className="flex items-center gap-3 mb-2">
            {seedStatus?.seeding && <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />}
            <span className="text-sm text-gray-300">
              {seedStatus?.seeded_count ?? 0} / {seedStatus?.total ?? 0} incidents stored
            </span>
          </div>
          {(seedStatus?.total ?? 0) > 0 && (
            <div className="w-full bg-gray-800 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                style={{ width: `${((seedStatus?.seeded_count ?? 0) / (seedStatus?.total ?? 1)) * 100}%` }}
              />
            </div>
          )}
          {seedStatus?.error && (
            <p className="mt-2 text-xs text-red-400">Error: {seedStatus.error}</p>
          )}
        </div>
      )}

      {/* Action log */}
      {messages.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-gray-400 text-sm font-medium mb-3">Action Log</h3>
          <div className="space-y-2">
            {messages.map((m, i) => (
              <div key={i} className={`text-sm px-3 py-2 rounded-lg ${
                m.type === 'success' ? 'bg-green-950 text-green-300' :
                m.type === 'error' ? 'bg-red-950 text-red-300' :
                'bg-gray-800 text-gray-300'
              }`}>
                {m.text}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function StatusItem({ label, ok, value }: { label: string; ok?: boolean; value: string }) {
  return (
    <div className="flex items-center gap-3 bg-gray-800 rounded-lg px-4 py-3">
      {ok === undefined ? (
        <Loader2 className="w-4 h-4 text-gray-500 animate-spin" />
      ) : ok ? (
        <CheckCircle className="w-4 h-4 text-green-500" />
      ) : (
        <AlertCircle className="w-4 h-4 text-red-500" />
      )}
      <div>
        <p className="text-xs text-gray-400">{label}</p>
        <p className="text-sm text-white font-medium">{value}</p>
      </div>
    </div>
  );
}
