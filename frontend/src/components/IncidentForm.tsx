import React, { useState } from 'react';
import { CreateIncidentPayload, IncidentMetrics } from '../services/api';
import { Plus, X, Zap } from 'lucide-react';

interface Props { onSubmit: (p: CreateIncidentPayload) => void; }

const DEMO_INCIDENT: CreateIncidentPayload = {
  service: 'payments-api', environment: 'production', severity: 'SEV-1',
  symptoms: ['API latency increased from 240ms to 2100ms (p95)', 'HTTP 500 error rate at 18%', 'Payment processing timeouts increasing'],
  metrics: { latency_ms: 2100, error_rate: 0.18, cpu_percent: 70, memory_percent: 58, db_cpu_percent: 42, db_connections: 48 },
  recent_changes: ['payments-api v2.4.1 deployed 9 minutes ago'],
  logs_summary: 'ERROR: PaymentProcessor timeout | ERROR: Downstream handler exception',
};

export function IncidentForm({ onSubmit }: Props) {
  const [form, setForm] = useState<CreateIncidentPayload>({
    service: '', environment: 'production', severity: 'SEV-2',
    symptoms: [''], metrics: undefined, recent_changes: [''],
  });
  const [showMetrics, setShowMetrics] = useState(false);

  const set = (k: keyof CreateIncidentPayload, v: any) => setForm(f => ({ ...f, [k]: v }));

  const addSymptom = () => set('symptoms', [...form.symptoms, '']);
  const setSymptom = (i: number, v: string) => set('symptoms', form.symptoms.map((s, j) => j === i ? v : s));
  const removeSymptom = (i: number) => set('symptoms', form.symptoms.filter((_, j) => j !== i));

  const addChange = () => set('recent_changes', [...form.recent_changes, '']);
  const setChange = (i: number, v: string) => set('recent_changes', form.recent_changes.map((s, j) => j === i ? v : s));
  const removeChange = (i: number) => set('recent_changes', form.recent_changes.filter((_, j) => j !== i));

  const setMetric = (k: keyof IncidentMetrics, v: string) => {
    const num = v === '' ? undefined : parseFloat(v);
    set('metrics', { ...(form.metrics || {}), [k]: num });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      ...form,
      symptoms: form.symptoms.filter(Boolean),
      recent_changes: form.recent_changes.filter(Boolean),
    };
    onSubmit(payload);
  };

  const loadDemo = () => setForm({ ...DEMO_INCIDENT, symptoms: [...DEMO_INCIDENT.symptoms], recent_changes: [...DEMO_INCIDENT.recent_changes] });

  return (
    <form onSubmit={handleSubmit} className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-800 flex items-center justify-between">
        <div>
          <h3 className="text-white font-semibold">New Incident</h3>
          <p className="text-gray-400 text-xs mt-0.5">Fill in the incident details to start investigation</p>
        </div>
        <button type="button" onClick={loadDemo}
          className="flex items-center gap-1.5 text-xs bg-yellow-900/50 hover:bg-yellow-900 text-yellow-300 border border-yellow-800 px-3 py-1.5 rounded-lg transition-colors">
          <Zap className="w-3 h-3" /> Load Demo
        </button>
      </div>

      <div className="p-6 space-y-5">
        {/* Service + Env */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1.5">Service *</label>
            <input value={form.service} onChange={e => set('service', e.target.value)} required
              placeholder="payments-api"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1.5">Environment</label>
            <select value={form.environment} onChange={e => set('environment', e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500">
              {['production', 'staging', 'development'].map(v => <option key={v}>{v}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1.5">Severity</label>
            <select value={form.severity} onChange={e => set('severity', e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500">
              {['SEV-1', 'SEV-2', 'SEV-3', 'SEV-4'].map(v => <option key={v}>{v}</option>)}
            </select>
          </div>
        </div>

        {/* Symptoms */}
        <div>
          <label className="block text-xs text-gray-400 mb-1.5">Symptoms *</label>
          <div className="space-y-2">
            {form.symptoms.map((s, i) => (
              <div key={i} className="flex gap-2">
                <input value={s} onChange={e => setSymptom(i, e.target.value)}
                  placeholder={i === 0 ? 'API latency increased to 2100ms' : 'Add symptom…'}
                  className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500" />
                {form.symptoms.length > 1 && (
                  <button type="button" onClick={() => removeSymptom(i)} className="text-gray-600 hover:text-red-400 p-2">
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
            ))}
          </div>
          <button type="button" onClick={addSymptom} className="mt-2 flex items-center gap-1.5 text-xs text-blue-400 hover:text-blue-300">
            <Plus className="w-3.5 h-3.5" /> Add symptom
          </button>
        </div>

        {/* Recent Changes */}
        <div>
          <label className="block text-xs text-gray-400 mb-1.5">Recent Changes</label>
          <div className="space-y-2">
            {form.recent_changes.map((c, i) => (
              <div key={i} className="flex gap-2">
                <input value={c} onChange={e => setChange(i, e.target.value)}
                  placeholder="v2.4.1 deployed 9 minutes ago"
                  className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500" />
                {form.recent_changes.length > 1 && (
                  <button type="button" onClick={() => removeChange(i)} className="text-gray-600 hover:text-red-400 p-2">
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
            ))}
          </div>
          <button type="button" onClick={addChange} className="mt-2 flex items-center gap-1.5 text-xs text-blue-400 hover:text-blue-300">
            <Plus className="w-3.5 h-3.5" /> Add change
          </button>
        </div>

        {/* Logs */}
        <div>
          <label className="block text-xs text-gray-400 mb-1.5">Logs Summary</label>
          <textarea value={form.logs_summary || ''} onChange={e => set('logs_summary', e.target.value)}
            rows={2} placeholder="ERROR: PaymentProcessor timeout…"
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500 resize-none" />
        </div>

        {/* Metrics toggle */}
        <div>
          <button type="button" onClick={() => setShowMetrics(!showMetrics)}
            className="text-xs text-blue-400 hover:text-blue-300">
            {showMetrics ? '▲ Hide' : '▼ Add'} Metrics (optional)
          </button>
          {showMetrics && (
            <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { k: 'latency_ms', label: 'Latency (ms)', placeholder: '2100' },
                { k: 'error_rate', label: 'Error Rate (0-1)', placeholder: '0.18' },
                { k: 'cpu_percent', label: 'CPU %', placeholder: '70' },
                { k: 'db_cpu_percent', label: 'DB CPU %', placeholder: '42' },
              ].map(({ k, label, placeholder }) => (
                <div key={k}>
                  <label className="block text-xs text-gray-500 mb-1">{label}</label>
                  <input type="number" step="any" placeholder={placeholder}
                    value={(form.metrics as any)?.[k] ?? ''}
                    onChange={e => setMetric(k as any, e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500" />
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="px-6 pb-6">
        <button type="submit"
          className="w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold py-3 rounded-xl transition-colors text-sm">
          Analyze Incident →
        </button>
      </div>
    </form>
  );
}
