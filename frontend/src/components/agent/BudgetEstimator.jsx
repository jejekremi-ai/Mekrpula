import { useState } from 'react';
import { Calculator, ArrowUpRight, Info } from 'lucide-react';
import { useData } from '../../lib/api';
import { Choice } from '../Kit';
import { SchedulePanel } from './ComputePanels';

export const BudgetEstimator = ({ data, busy, action, modelId }) => {
  const [model, setModel] = useState(modelId), [frequency, setFrequency] = useState(data?.schedule?.frequency || 'daily');
  const { data: catalog } = useData('/agent/models');
  const { data: estimate, error, loading } = useData(`/compute/estimate?model_id=${encodeURIComponent(model)}&frequency=${frequency}`);
  const options = (catalog?.models || []).filter(m => m.runnable).map(m => ({ value: m.id, label: m.name }));
  return <section className="compute-budget" id="compute-budget" data-testid="hub-budget-estimator-card">
    <div className="compute-section-heading"><div><span className="compute-eyebrow"><Calculator size={14} />RENCANA OPERASIONAL</span><h2 data-testid="compute-budget-title">Estimasi anggaran<span>.</span></h2></div><span className="compute-outline-tag">30 HARI</span></div>
    <div className="budget-layout"><div className="budget-inputs"><Choice id="budget-estimator-model-select" label="Bandingkan model" options={options} value={model} onChange={setModel} /><Choice id="budget-estimator-frequency-select" label="Frekuensi riset" value={frequency} onChange={setFrequency} options={[{ value: 'hourly', label: 'Setiap jam' }, { value: 'every-6-hours', label: 'Setiap 6 jam' }, { value: 'daily', label: 'Setiap hari' }, { value: 'weekly', label: 'Setiap minggu' }]} /><p data-testid="budget-model-note">Perbandingan saja. Model agent tetap pilihan kreator.</p></div>
      <div className="budget-result">{error ? <p role="alert" className="compute-warning" data-testid="budget-error">{error}</p> : <><span className="budget-result-label">PERKIRAAN BULANAN</span><strong data-testid="budget-monthly">{loading ? '…' : estimate?.monthly?.toFixed(2)}<small>CR</small></strong><div className="budget-periods"><span data-testid="budget-daily">{estimate?.daily?.toFixed(2) || '—'} <small>CR / hari</small></span><span data-testid="budget-weekly">{estimate?.weekly?.toFixed(2) || '—'} <small>CR / minggu</small></span></div><div className="budget-per-run"><span data-testid="budget-per-run">≈ {estimate?.per_run?.toFixed(3) || '—'} CR / riset</span><ArrowUpRight size={15} /></div></>}
      </div>
    </div>
    <p className="budget-assumptions" data-testid="budget-assumptions"><Info size={13} />Tarif kredit internal · asumsi 2.500 token masuk + 800 keluar. Alat pasar: 0 CR. Bukan tagihan provider; penggunaan aktual dapat berbeda. Batas uji: 5 riset / token / hari.</p>
    <SchedulePanel data={data} action={action} busy={busy} frequency={frequency} />
  </section>;
};