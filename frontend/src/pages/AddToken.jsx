import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, ArrowUpRight, ShieldCheck, Bot, Store } from 'lucide-react';
import { toast } from 'sonner';
import { api } from '../lib/api';
import { Btn, Field, ErrorBox } from '../components/Kit';
import { useWallet } from '../components/WalletContext';
import { AgentCreatorFields } from '../components/agent/AgentCreatorFields';
import { createAgentProfile } from '../components/agent/agentData';

export default function AddToken() {
  const navigate = useNavigate(); const { wallet, requireWallet } = useWallet();
  const [address, setAddress] = useState(''), [agentEnabled, setAgentEnabled] = useState(false);
  const [profile, setProfile] = useState(createAgentProfile), [busy, setBusy] = useState(false), [error, setError] = useState('');
  async function submit(e) {
    e.preventDefault(); if (busy) return;
    if (agentEnabled && !requireWallet()) return;
    setBusy(true); setError('');
    try {
      const agent = agentEnabled ? await api('/agent/validate', { method: 'POST', body: profile }) : null;
      const result = await api('/tokens', { method: 'POST', body: { address: address.trim(), agent } });
      toast.success(result.agent_configured ? 'Token Hub ready. Your verified agent profile is attached.' : result.created ? 'Your Token Hub is ready. Adding a token does not grant ownership.' : 'This token already has a Hub. Welcome back.');
      navigate(`/token/${result.token.address}`);
    } catch(e) { setError(e.message); } finally { setBusy(false); }
  }
  return <main className="container page"><div className="breadcrumbs"><Link to="/explore" data-testid="add-token-back"><ArrowLeft size={13} />Explore tokens</Link><span>/</span><span>Add Token</span></div><div className="page-heading"><span className="eyebrow">YOUR TOKEN. A NEW CHAPTER.</span><h1 data-testid="add-token-title">Bring your token to MART<span className="green">.</span></h1><p data-testid="add-token-intro">Already on Solana? Give it a market, a community, and an optional ecosystem agent.</p></div><div className="launch-layout"><section className="form-panel"><div className="panel-heading"><span className="step-badge">01</span><h2>Your existing token</h2><span className="network-label">SOLANA</span></div><form className="form-stack" onSubmit={submit} data-testid="add-token-form"><fieldset className="creator-form-fields" disabled={busy}>
    <Field id="token-address-input" label="Solana token mint address" placeholder="Paste the token mint address" required maxLength={44} minLength={32} value={address} onChange={e => { setAddress(e.target.value); setError(''); }} />
    <p className="creator-agent-note" data-testid="add-token-identity-note">One mint, one Token Hub. An existing Hub opens instead of creating a duplicate.</p>
    <AgentCreatorFields prefix="add-token" enabled={agentEnabled} onToggle={v => { setAgentEnabled(v); if (v && !profile.name) setProfile(p => ({ ...p, name: 'Community Agent' })); setError(''); }} profile={profile} onChange={setProfile} disabled={busy} />
    <div className="info-note" data-testid="add-token-authority-note"><ShieldCheck size={19} /><p>{agentEnabled ? 'Attaching an agent requires the connected wallet to be the current on-chain metadata update authority. Existing agent profiles cannot be overwritten. Tokens with renounced or program-controlled authority cannot attach an agent through this import flow.' : 'Anyone can add a compatible token without an agent. Adding it does not transfer ownership or give control of its Hub.'}</p></div>
    <ErrorBox error={error} /><Btn data-testid="add-token-submit" type="submit" busy={busy}>{agentEnabled && !wallet ? 'Connect wallet to continue' : agentEnabled ? 'Verify & add token with agent' : 'Find & open Token Hub'}<ArrowUpRight size={16} /></Btn>
    </fieldset></form></section><aside className="launch-aside"><span className="eyebrow">NO RELAUNCH. NO DUPLICATE TOKEN.</span><h2>Same token.<br />More possibilities.</h2><p>Your existing Solana mint remains the only token identity.</p>{[[Store, 'Your market comes with it', 'Token-denominated listings, events, and community all stay together.'], [Bot, 'Choose an agent here', 'Pick the role, provider, model, and mission before adding the token. Or leave it off.'], [ShieldCheck, 'Authority checked on-chain', 'Only a verified metadata authority can attach an agent to an imported token.']].map(([Icon, title, text], i) => <div className="launch-benefit" key={title} data-testid={`add-token-benefit-${i}`}><span><Icon size={20} /></span><div><strong>{title}</strong><p>{text}</p></div></div>)}<Link className="text-link" to="/launch" data-testid="add-token-new-launch">Creating a new token? Launch here<ArrowUpRight size={14} /></Link></aside></div></main>;
}