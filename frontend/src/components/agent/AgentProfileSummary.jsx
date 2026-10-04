import { Bot, Cpu, ShieldCheck, Check, ScanSearch, LockKeyhole } from 'lucide-react';
import { providerMark } from './agentData';

export const AgentProfileSummary = ({ agent, compute }) => {
  const profile = agent?.profile;
  if (!profile) return null;
  return <aside className="token-agent-summary" data-testid="hub-agent-breakdown-card">
    <div className="token-panel-title"><span><Bot size={15} /> ECOSYSTEM AGENT</span><small data-testid="hub-agent-status">{compute?.active_run ? 'RESEARCHING' : compute?.paused ? 'PAUSED' : 'READY'}</small></div>
    <div className="token-agent-identity"><span className={`provider-mark provider-${agent.model?.provider?.toLowerCase()}`}>{providerMark(agent.model?.provider)}</span><div><h2 data-testid="hub-agent-name">{profile.name}</h2><span data-testid="hub-agent-role">{profile.role}</span></div></div>
    <div className="token-agent-model"><Cpu size={13} /><strong data-testid="hub-agent-model-badge">{agent.model?.name || profile.model_id}</strong><span data-testid="hub-agent-provider-badge">{agent.model?.provider}</span></div>
    <span className="token-panel-eyebrow" data-testid="hub-agent-mission-label">{agent.published ? 'MISI KREATOR' : 'MISI RISET KOMUNITAS'}</span><p className="token-agent-mission" data-testid="hub-agent-mission">{profile.mission}</p>
    <div className="agent-capability-list" data-testid="hub-agent-capabilities">{[[ScanSearch, 'Data pasar & ekosistem'], [Cpu, 'Analisis dan ide event'], [ShieldCheck, 'Tanpa eksekusi transaksi']].map(([Icon, label], i) => <div key={label} data-testid={`hub-agent-capability-${i}`}><Icon size={13} /><span>{label}</span><Check size={12} /></div>)}</div>
    <div className="agent-origin-note" data-testid="hub-agent-origin"><LockKeyhole size={13} /><p>{agent.published ? 'Model dipilih dan dikunci oleh kreator.' : 'Agent uji komunitas. Bukan perwakilan resmi kreator token.'}</p></div>
    <div className="agent-ecosystem-mini" data-testid="hub-ecosystem-counts">{[['listings', 'Listing'], ['events', 'Event'], ['posts', 'Post']].map(([k, v]) => <div key={k}><strong data-testid={`hub-count-${k}`}>{agent.ecosystem[k] || 0}</strong><span>{v}</span></div>)}</div>
  </aside>;
};