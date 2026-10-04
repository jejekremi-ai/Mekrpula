import { Bot, ShieldCheck } from 'lucide-react';
import { providerMark } from './agentData';

export const AgentProfileSummary = ({ agent, compute }) => {
  const profile = agent?.profile;
  if (!profile) return <section className="agent-identity terminal-pane" data-testid="hub-agent-loading"><Bot size={18} /><p>Connecting to agent…</p></section>;
  return <section className="agent-identity terminal-pane" data-testid="agent-profile-summary">
    <div className="agent-identity-top"><span className={`provider-mark provider-${agent.model?.provider?.toLowerCase()}`}>{providerMark(agent.model?.provider)}</span><div><h2 data-testid="hub-agent-name">{profile.name}</h2><p data-testid="hub-agent-model-badge">{agent.model?.provider} · {agent.model?.name || profile.model_id}</p></div><span className="agent-identity-status" data-testid="hub-agent-status"><i />{compute?.active_run ? 'AWAKE' : compute?.paused ? 'PAUSED' : 'READY'}</span></div>
    <div className="agent-identity-body"><strong className="agent-role" data-testid="hub-agent-role">{profile.role}</strong><span className="agent-personality" data-testid="hub-agent-posture">{profile.risk.toLowerCase()} · evidence-led · transparent</span><div className="agent-mission"><span data-testid="hub-agent-mission-label">MISSION</span><p data-testid="hub-agent-mission">{profile.mission}</p></div><p className="agent-origin" data-testid="hub-agent-origin"><ShieldCheck size={11} />{agent.published ? 'Creator-configured · model locked' : 'Community research · not the official token team'}</p></div>
  </section>;
};