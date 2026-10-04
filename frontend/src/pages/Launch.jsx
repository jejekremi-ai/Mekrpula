import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Rocket, ArrowUpRight, ShieldCheck, Store, CalendarDays, Users, Wallet, Bot } from 'lucide-react';
import { Buffer } from 'buffer';
import { toast } from 'sonner';
import { api } from '../lib/api';
import { Btn, Field, UploadImage, ErrorBox } from '../components/Kit';
import { useWallet } from '../components/WalletContext';
import { AgentCreatorFields } from '../components/agent/AgentCreatorFields';
import { createAgentProfile } from '../components/agent/agentData';

export default function Launch() {
  const { wallet, provider, requireWallet, openWallet } = useWallet();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: '', symbol: '', description: '', image: '', banner: '', website: '', twitter: '', telegram: '', amount: '0', slippage: '10' });
  const [agentEnabled, setAgentEnabled] = useState(false), [agentProfile, setAgentProfile] = useState(createAgentProfile);
  const [busy, setBusy] = useState(false), [phase, setPhase] = useState(''), [error, setError] = useState('');
  const [pending, setPending] = useState(() => localStorage.getItem('mart-pending-launch'));
  const set = (key, value) => setForm(f => ({ ...f, [key]: value }));
  async function launch(e) {
    e.preventDefault(); if (busy || !requireWallet()) return;
    setBusy(true); setError('');
    try {
      const agent = agentEnabled ? await api('/agent/validate', { method: 'POST', body: agentProfile }) : null;
      if (!form.image) throw new Error('Upload your token logo first.');
      const { Keypair, VersionedTransaction } = await import('@solana/web3.js');
      const mint = Keypair.generate(); setPhase('Preparing your Pump.fun launch…');
      const response = await api('/launch/prepare', { method: 'POST', body: { ...form, amount: Number(form.amount), slippage: Number(form.slippage), mint: mint.publicKey.toBase58(), agent } });
      const tx = VersionedTransaction.deserialize(Buffer.from(response.transaction, 'base64')); tx.sign([mint]);
      setPhase('Review and sign in your wallet…'); const signed = await provider.current.signTransaction(tx);
      localStorage.setItem('mart-pending-launch', response.id); setPending(response.id); setPhase('Submitting to Solana…');
      await api('/transactions/send', { method: 'POST', body: { kind: 'launch', id: response.id, transaction: Buffer.from(signed.serialize()).toString('base64') } });
      setPhase('Submitted. Check launch after Solana finalizes the transaction.');
      toast.info('Launch submitted. Your Token Hub and selected agent profile are attached only after confirmation.');
    } catch(e) { setError(e.message); setPhase(''); } finally { setBusy(false); }
  }
  async function confirm() {
    if (busy || !requireWallet()) return; setBusy(true); setError('');
    try { const result = await api(`/launch/${pending}/confirm`, { method: 'POST' }); localStorage.removeItem('mart-pending-launch'); setPending(null); toast.success('Token launched. Welcome to your MART Token Hub.'); navigate(`/token/${result.address}`); }
    catch(e) { setError(e.message); } finally { setBusy(false); }
  }
  return <main className="container page"><div className="page-heading"><span className="eyebrow">LAUNCH A TOKEN. START SOMETHING BIGGER.</span><h1 data-testid="launch-title">It starts with your token<span className="green">.</span></h1><p data-testid="launch-description-copy">Launch on Pump.fun. Your MART Token Hub comes with it.</p></div><div className="launch-layout"><section className="form-panel"><div className="panel-heading"><span className="step-badge">01</span><h2>Make it yours</h2><span className="network-label"><span className="live-dot" />MAINNET</span></div>
    {!wallet && <div className="creator-wallet-notice" data-testid="launch-wallet-notice"><Wallet size={18} /><p>Set up your token first. Connect your wallet to upload artwork and launch.</p><Btn secondary data-testid="launch-connect-wallet" onClick={openWallet}>Connect Wallet</Btn></div>}
    <form className="form-stack" onSubmit={launch} data-testid="launch-form"><fieldset className="creator-form-fields" disabled={busy || !!pending}>
      <div className="form-row"><Field id="launch-token-name" label="Token name" placeholder="The next big thing" required maxLength={32} value={form.name} onChange={e => set('name', e.target.value)} /><Field id="launch-token-symbol" label="Symbol" placeholder="TOKEN" pattern="[A-Za-z0-9]+" required maxLength={10} value={form.symbol} onChange={e => set('symbol', e.target.value.toUpperCase())} /></div>
      <Field textarea id="launch-description" label="Description" placeholder="Every token has a story. What’s yours?" required minLength={10} maxLength={1000} value={form.description} onChange={e => set('description', e.target.value)} />
      {wallet ? <div className="form-row"><UploadImage id="launch-logo" value={form.image} onChange={v => set('image', v)} label="Upload token logo" /><UploadImage id="launch-banner" value={form.banner} onChange={v => set('banner', v)} label="Upload banner (optional)" /></div> : <button type="button" className="creator-artwork-gate" data-testid="launch-artwork-connect" onClick={openWallet}><Wallet size={20} /><span>Connect wallet to upload token artwork</span><ArrowUpRight size={15} /></button>}
      <h3 className="form-section-title">Bring your community</h3><Field id="launch-website" label="Website (optional)" type="url" placeholder="https://your-world.com" value={form.website} onChange={e => set('website', e.target.value)} /><div className="form-row"><Field id="launch-twitter" label="X / Twitter (optional)" type="url" placeholder="https://x.com/yourtoken" value={form.twitter} onChange={e => set('twitter', e.target.value)} /><Field id="launch-telegram" label="Telegram (optional)" type="url" placeholder="https://t.me/yourtoken" value={form.telegram} onChange={e => set('telegram', e.target.value)} /></div>
      <AgentCreatorFields prefix="launch" enabled={agentEnabled} onToggle={value => { setAgentEnabled(value); if (value && !agentProfile.name) setAgentProfile(p => ({ ...p, name: `${form.symbol || form.name || 'Community'} Agent`.slice(0,60) })); }} profile={agentProfile} onChange={setAgentProfile} disabled={busy || !!pending} />
      <div className="form-row"><Field id="launch-initial-buy" label="Initial buy (SOL)" type="number" min="0" max="10" step="0.0001" value={form.amount} onChange={e => set('amount', e.target.value)} hint="Optional creator purchase. 0 means no initial buy." /><Field id="launch-slippage" label="Slippage tolerance (%)" type="number" min="1" max="50" value={form.slippage} onChange={e => set('slippage', e.target.value)} /></div>
      <div className="info-note warning"><ShieldCheck size={20} /><p data-testid="launch-mainnet-warning">Real mainnet transaction. You pay network and account-creation fees, plus any initial purchase and provider fees (0.5% per local trade). Priority fee: 0.00001 SOL. Review the full transaction in your wallet. Metadata is hosted on MART, not permanent decentralized storage.</p></div>
      <Btn data-testid="launch-submit" type="submit" busy={busy} disabled={!!pending || (wallet && !form.image)}>{wallet ? 'Launch through Pump.fun' : 'Connect wallet to launch'}<Rocket size={16} /></Btn>
    </fieldset></form>{phase && <p className="info-note" data-testid="launch-progress">{phase}</p>}{pending && <div className="pending-launch"><span data-testid="pending-launch-id">A launch is awaiting confirmation.</span><Btn secondary data-testid="check-launch" onClick={confirm} busy={busy}>Check launch</Btn><button className="text-link" data-testid="dismiss-pending-launch" onClick={() => { localStorage.removeItem('mart-pending-launch'); setPending(null); }}>Dismiss saved request</button></div>}<ErrorBox error={error} /></section>
    <aside className="launch-aside"><span className="eyebrow">ONE LAUNCH. AN ENTIRE WORLD.</span><h2>Your token deserves<br />more than a chart.</h2><p>Once your Pump.fun launch is confirmed, your Token Hub is created automatically.</p>{[[Store, 'A market of your own', 'Art, collectibles, and merch. Priced in your token.'], [CalendarDays, 'Moments that matter', 'Keep holders in the loop with official events.'], [Users, 'A place to belong', 'Give your community somewhere to build together.'], [Bot, 'An agent, if you choose', 'Set its role and AI model here. Its profile joins the chart and token breakdown.']].map(([Icon, title, text], i) => <div className="launch-benefit" key={title} data-testid={`launch-benefit-${i}`}><span><Icon size={20} /></span><div><strong>{title}</strong><p>{text}</p></div></div>)}<div className="launch-architecture"><span className="pump-badge"><span className="pump-pill" />pump.fun</span><ArrowUpRight size={20} /><strong>MART<span className="green">✳</span></strong></div><p className="small-text muted">One canonical Solana mint. No duplicate token. No custody of your funds.</p></aside></div></main>;
}