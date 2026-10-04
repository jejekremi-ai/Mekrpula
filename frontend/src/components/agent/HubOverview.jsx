import { useEffect, useState } from 'react';
import { Play, Loader2, Settings2, RefreshCw, Radio } from 'lucide-react';
import { toast } from 'sonner';
import { api, useData } from '../../lib/api';
import { useWallet } from '../WalletContext';
import { AgentProfileSummary } from './AgentProfileSummary';
import { AgentActivityFeed, ResearchTerminal, ResearchArchive } from './ResearchActivity';
import { AgentMarketTerminal, EventRadar, EventIdeas, CommunityTerminal } from './TokenTerminals';
import { AgentSettings } from './AgentSettings';

export const HubOverview = ({ token }) => {
  const { data: agent, error, reload } = useData(`/tokens/${token.address}/agent`);
  const { data: compute, error: computeError, reload: reloadCompute } = useData(`/tokens/${token.address}/compute`);
  const { data: events, error: eventError, reload: reloadEvents } = useData(`/events?token=${token.address}`);
  const { data: posts, error: postError, reload: reloadPosts } = useData(`/tokens/${token.address}/posts`);
  const [busy, setBusy] = useState(''), [actionError, setActionError] = useState(''), [settings, setSettings] = useState(false);
  const { wallet } = useWallet();
  useEffect(() => { reloadCompute(); }, [wallet, reloadCompute]);
  useEffect(() => { const timer = setInterval(() => { if (!document.hidden) reloadCompute(); }, compute?.active_run ? 1500 : 10000); return () => clearInterval(timer); }, [compute?.active_run, reloadCompute]);
  useEffect(() => { const timer = setInterval(() => { if (!document.hidden) { reloadEvents(); reloadPosts(); } }, 30000); return () => clearInterval(timer); }, [reloadEvents, reloadPosts]);
  async function action(path, body, method = 'POST') {
    setBusy(path); setActionError('');
    try { await api(`/tokens/${token.address}/compute/${path}`, { method, body }); reloadCompute(); reload(); toast.success(({ topup: 'Test credits added', runs: 'Research started', limits: 'Operating settings saved', schedule: 'Research schedule updated' })[path]); return true; }
    catch (e) { setActionError(e.message); toast.error(e.message); return false; }
    finally { setBusy(''); }
  }
  const running = !!compute?.active_run;
  const run = () => {
    if (!compute?.balance || compute?.paused) { setSettings(true); return; }
    action('runs', { request_id: crypto.randomUUID() });
  };
  const latest = compute?.runs.find(r => r.id === compute.active_run) || compute?.runs.find(r => r.status === 'completed') || compute?.runs[0];
  return <section className="agent-workspace" data-testid="hub-integrated-overview">
    <header className="agent-workspace-bar"><div><Radio size={13} /><span data-testid="agent-workspace-heading">AGENT WORKSPACE</span><span className="workspace-mode" data-testid="hub-compute-mode">{compute?.mode === 'creator' ? 'CREATOR AGENT' : 'COMMUNITY AGENT'}</span></div><div className="workspace-actions"><span className={`workspace-status ${running ? 'active' : ''}`} data-testid="agent-workspace-status"><i />{running ? 'RESEARCHING' : compute?.paused ? 'PAUSED' : 'STANDBY'}</span><button className="agent-run-button" data-testid="run-research-button" disabled={!compute?.can_manage || !compute?.runnable || running || !!busy || !compute?.remaining_daily_runs} title={!compute?.remaining_daily_runs ? 'Daily research limit reached' : !compute?.can_manage ? 'Only the token creator can run this agent' : 'Start a token research run'} onClick={run}>{running || busy === 'runs' ? <Loader2 size={12} className="spin" /> : <Play size={11} />}<span>{running ? 'Researching' : 'Run research'}</span></button><button className="agent-settings-button" data-testid="agent-settings-trigger" title="Agent settings" aria-label="Agent settings" onClick={() => setSettings(true)}><Settings2 size={15} /></button></div></header>
    {(actionError || computeError || error) && <div className="terminal-error" role="alert" data-testid="compute-action-error"><p>{actionError || computeError || error}</p><button data-testid="compute-error-retry" onClick={() => { setActionError(''); reloadCompute(); reload(); }}><RefreshCw size={12} />Retry</button></div>}
    <div className="agent-terminal-grid">
      <div className="agent-identity-column"><AgentProfileSummary agent={agent} compute={compute} /><AgentActivityFeed data={compute} /><CommunityTerminal posts={posts} error={postError} /></div>
      <div className="agent-research-column"><ResearchTerminal data={compute} token={token} latest={latest} /><EventIdeas run={latest} /><ResearchArchive data={compute} token={token} latest={latest} /></div>
      <div className="agent-market-column"><AgentMarketTerminal token={token} /><EventRadar token={token} events={events} error={eventError} /></div>
    </div>
    <AgentSettings open={settings} onClose={() => setSettings(false)} data={compute} busy={busy} action={action} token={token} error={actionError} />
  </section>;
};