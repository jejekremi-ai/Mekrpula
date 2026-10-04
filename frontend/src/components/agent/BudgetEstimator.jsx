import { useState } from 'react';
import { useData } from '../../lib/api';
import { Choice } from '../Kit';
import { SchedulePanel } from './ComputePanels';

export const BudgetEstimator = ({ data, busy, action, modelId }) => {
  const [model, setModel] = useState(modelId), [frequency, setFrequency] = useState(data.schedule.frequency || 'daily');
  const { data: catalog } = useData('/agent/models');
  const { data: estimate, error, loading } = useData(`/compute/estimate?model_id=${encodeURIComponent(model)}&frequency=${frequency}`);
  const options = (catalog?.models || []).filter(m => m.runnable).map(m => ({ value: m.id, label: m.name }));
  return <section className="settings-budget" data-testid="hub-budget-estimator-card">
    <div className="form-row"><Choice id="budget-estimator-model-select" label="Compare model" options={options} value={model} onChange={setModel} /><Choice id="budget-estimator-frequency-select" label="Research frequency" value={frequency} onChange={setFrequency} options={[{ value: 'hourly', label: 'Every hour' }, { value: 'every-6-hours', label: 'Every 6 hours' }, { value: 'daily', label: 'Daily' }, { value: 'weekly', label: 'Weekly' }]} /></div>
    <p className="settings-helper" data-testid="budget-model-note">Comparison only. The creator-selected agent model stays unchanged.</p>
    {error ? <p role="alert" className="terminal-notice" data-testid="budget-error">{error}</p> : <div className="settings-estimates"><div><span>Per run</span><strong data-testid="budget-per-run">{loading ? '…' : estimate?.per_run?.toFixed(3)} <small>CR</small></strong></div><div><span>Per day</span><strong data-testid="budget-daily">{loading ? '…' : estimate?.daily?.toFixed(2)} <small>CR</small></strong></div><div><span>Per week</span><strong data-testid="budget-weekly">{loading ? '…' : estimate?.weekly?.toFixed(2)} <small>CR</small></strong></div><div><span>30 days</span><strong data-testid="budget-monthly">{loading ? '…' : estimate?.monthly?.toFixed(2)} <small>CR</small></strong></div></div>}
    <p className="settings-helper" data-testid="budget-assumptions">Internal tariff estimate: 2,500 input + 800 output tokens per run. Market tools: 0 CR. Actual usage varies; this is not a provider invoice. Test safety limit: 5 attempts per token per day.</p>
    <SchedulePanel data={data} action={action} busy={busy} frequency={frequency} />
  </section>;
};