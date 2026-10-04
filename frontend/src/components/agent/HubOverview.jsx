import { useEffect, useState } from 'react';
import { BarChart3, ArrowUpRight, Radio, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';
import { api, useData } from '../../lib/api';
import { External } from '../Kit';
import { useWallet } from '../WalletContext';
import { AgentProfileSummary } from './AgentProfileSummary';
import { TokenPriceChart } from './TokenPriceChart';
import { CreditPanel } from './ComputePanels';
import { BudgetEstimator } from './BudgetEstimator';
import { ResearchActivity } from './ResearchActivity';

export const HubOverview = ({ token }) => {
  const { data: agent, loading, error, reload } = useData(`/tokens/${token.address}/agent`);
  const { data: compute, error: computeError, reload: reloadCompute } = useData(`/tokens/${token.address}/compute`);
  const [busy, setBusy] = useState(''), [actionError, setActionError] = useState('');
  const { wallet } = useWallet();
  useEffect(() => { reloadCompute(); }, [wallet, reloadCompute]);
  useEffect(() => { const timer = setInterval(() => { if (!document.hidden) reloadCompute(); }, compute?.active_run ? 1500 : 10000); return () => clearInterval(timer); }, [compute?.active_run, reloadCompute]);
  async function action(path, body, method = 'POST') {
    setBusy(path); setActionError('');
    try { await api(`/tokens/${token.address}/compute/${path}`, { method, body }); reloadCompute(); reload(); toast.success(({ topup: '100 kredit uji ditambahkan', runs: 'Agent mulai mengumpulkan data token', limits: 'Batas operasional disimpan', schedule: 'Jadwal riset diperbarui' })[path]); return true; }
    catch (e) { setActionError(e.message); toast.error(e.message); return false; }
    finally { setBusy(''); }
  }
  const toBudget = () => document.getElementById('compute-budget')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  return <section className="token-overview" data-testid="hub-integrated-overview">
    <div className="compute-overview-heading"><span><Radio size={14} />AGENT WORKSPACE</span><span data-testid="hub-compute-mode">{compute?.mode === 'creator' ? 'KONFIGURASI KREATOR' : 'RISET KOMUNITAS · MODE UJI'}<i />{compute?.active_run ? 'RISET BERJALAN' : compute?.paused ? 'DIJEDA' : 'SIAP'}</span></div>
    {(actionError || computeError) && <div className="compute-inline-error" role="alert" data-testid="compute-action-error"><p>{actionError || computeError}</p><button data-testid="compute-error-retry" onClick={() => { setActionError(''); reloadCompute(); }}><RefreshCw size={14} />Coba lagi</button></div>}
    <div className="token-overview-grid">
      {loading ? <div className="token-agent-summary token-panel-loading" data-testid="hub-agent-loading">Loading agent profile…</div> : error ? <div className="token-agent-summary token-panel-loading" role="alert" data-testid="hub-agent-error"><p>{error}</p><button className="text-link" data-testid="hub-agent-retry" onClick={reload}>Retry agent profile</button></div> : <AgentProfileSummary agent={agent} compute={compute} />}
      <div className="token-chart-section" data-testid="hub-chart-container"><div className="token-panel-title"><span><BarChart3 size={15} /> PRICE CHART</span><External id="hub-overview-chart-link" href={token.dex_url}>Open chart</External></div><TokenPriceChart token={token} /><div className="token-chart-summary"><span data-testid="hub-chart-source">24H change · DexScreener snapshot</span><span data-testid="hub-chart-change" className={token.change >= 0 ? 'positive' : 'negative'}>{token.change == null ? '—' : `${token.change >= 0 ? '+' : ''}${token.change.toFixed(2)}%`} <small>24H</small></span></div><div className="token-trade-actions"><External href={token.pump_url} className="btn btn-primary" id="hub-overview-buy">Buy ${token.symbol}<ArrowUpRight size={13} /></External><External href={token.pump_url} className="btn btn-secondary" id="hub-overview-sell">Sell ${token.symbol}</External><span data-testid="hub-chart-disclaimer">Public price history, not a streaming execution price.</span></div></div>
      <CreditPanel data={compute} busy={busy} action={action} onEstimate={toBudget} />
    </div>
    <div className="compute-bottom-grid"><ResearchActivity data={compute} token={token} />{compute && <BudgetEstimator key={compute.model_id} data={compute} modelId={compute.model_id} action={action} busy={busy} />}</div>
  </section>;
};