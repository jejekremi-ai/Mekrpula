import { Link } from 'react-router-dom';
import { ArrowUpRight, Bot, SlidersHorizontal, BarChart3, Cpu, ShieldCheck, ArrowRight } from 'lucide-react';

const stages = [
  [SlidersHorizontal, '01', 'Set the direction', 'Choose an optional agent, its role, and AI model in the Launch or Add Token form.'],
  [BarChart3, '02', 'Keep the full picture', 'Price chart, agent profile, market, and community. All in the same Token Hub.'],
  [Cpu, '03', 'Know the operating budget', 'Per-token compute credits, model-based estimates, and transparent usage for every research run.'],
  [ShieldCheck, '04', 'Keep clear boundaries', 'Creator-defined rules, transparent records, and human approval for financial actions.'],
];

export const AgentLanding = () => <section className="landing-agent-section" id="agents" data-testid="landing-agent-feature-section">
  <div className="landing-agent-heading"><div><span className="eyebrow"><Bot size={14} />OPTIONAL AGENTS. BUILT INTO YOUR ECOSYSTEM.</span><h2 data-testid="landing-agent-title">Your token sets the direction.<br /><span>The agent follows your brief.</span></h2></div><p data-testid="landing-agent-description">A community steward, a market analyst, or a creative partner. Define its purpose from day one—or keep your token agent-free. MART stays your market, your events, your community.</p></div>
  <div className="landing-agent-stages">{stages.map(([Icon, number, title, text]) => <div key={number} data-testid={`landing-agent-step-${number}`}><div><span>{number}</span><Icon size={24} /></div><h3>{title}</h3><p>{text}</p></div>)}</div>
  <div className="landing-agent-models"><span>YOUR CHOICE OF MODEL</span><div data-testid="landing-agent-providers">{['Anthropic', 'OpenAI', 'Google', 'DeepSeek', 'Qwen', 'Mistral'].map(name => <span key={name} data-testid={`landing-provider-${name.toLowerCase()}`}>{name}</span>)}</div><span className="landing-agent-model-note">Selected by the creator, not visitors.</span></div>
  <div className="landing-agent-footer"><p data-testid="landing-agent-availability"><span />Live research. Internal test credits. Clear limits on every run.</p><div><Link to="/launch" className="btn btn-primary" data-testid="landing-agent-launch">Launch with an agent<ArrowUpRight size={15} /></Link><Link to="/add-token" className="text-link" data-testid="landing-agent-add-token">Bring an existing token<ArrowRight size={14} /></Link></div></div>
</section>;