import { Link, NavLink, Navigate, useParams } from 'react-router-dom';
import { ArrowLeft, Copy, BadgeCheck, ShieldCheck, Share2, BarChart3, Store, CalendarDays, Users } from 'lucide-react';
import { toast } from 'sonner';
import { api, useData, money, short } from '../lib/api';
import { TokenAvatar, Loading, ErrorBox, External } from '../components/Kit';
import { ManageHub } from '../components/OfficialTools';
import { useWallet } from '../components/WalletContext';
import Market from './Market';
import Community from './Community';
import { HubEvents, EventTicker } from './Events';
import Trade from './Trade';
import { HubOverview } from '../components/agent/HubOverview';

export default function Hub() {
  const { address, tab = 'market' } = useParams();
  const { data: token, loading, error, reload } = useData(`/tokens/${address}`);
  const { requireWallet } = useWallet();
  async function claim() { if (!requireWallet()) return; try { await api(`/tokens/${address}/claim`, { method: 'POST' }); toast.success('Token authority verified. This Hub is now yours to manage.'); reload(); } catch(e) { toast.error(e.message); } }
  const copy = async text => { try { await navigator.clipboard.writeText(text); toast.success('Copied to clipboard'); } catch { toast.error('Copy is unavailable in this browser.'); } };
  if (loading) return <main className="container page"><Loading /></main>;
  if (error) return <main className="container page"><ErrorBox error={error} /><Link to="/explore" className="text-link" data-testid="hub-back-error">Back to Explore</Link></main>;
  if (tab === 'agent') return <Navigate to={`/token/${address}`} replace />;
  return <main className="container hub-page">
    <div className="breadcrumbs"><Link to="/explore" data-testid="hub-back"><ArrowLeft size={14} />Explore tokens</Link><span>/</span><span data-testid="hub-breadcrumb">{token.name} Hub</span></div>
    <section className="hub-header">
      <div className="hub-identity"><TokenAvatar token={token} /><div><div className="hub-name"><h1 data-testid="hub-token-name">{token.name}</h1>{token.claimed_by ? <span className="verified-tag" data-testid="hub-verified"><BadgeCheck size={13} />Verified</span> : <span className="unclaimed-tag" data-testid="hub-unclaimed">Unclaimed</span>}</div><div className="hub-symbol"><strong data-testid="hub-symbol">${token.symbol}</strong><button onClick={() => copy(address)} data-testid="copy-token-address" title={address}>{short(address)}<Copy size={12} /></button><External href={token.explorer_url} id="token-solscan">Solscan</External></div></div></div>
      <div className="hub-actions"><ManageHub token={token} reload={reload} />{!token.claimed_by && <button className="text-link" onClick={claim} data-testid="claim-token-button"><ShieldCheck size={14} />Claim this Token</button>}<button className="icon-button" data-testid="share-token-hub" onClick={() => copy(window.location.href)} aria-label="Share token hub"><Share2 size={17} /></button><External className="btn btn-primary" id="hub-buy-token" href={token.pump_url}>Buy ${token.symbol}</External></div>
    </section>
    {token.description && <p className="hub-description" data-testid="hub-official-description">{token.description}</p>}
    <div className="hub-stat-grid">{[['Token price', money(token.price)], ['Market cap', money(token.market_cap)], ['24h volume', money(token.volume)], ['Liquidity', money(token.liquidity)]].map(([label, val]) => <div key={label}><span>{label}</span><strong data-testid={`hub-${label.replaceAll(' ', '-').toLowerCase()}`}>{val}{label === 'Token price' && token.change != null && <small className={token.change >= 0 ? 'positive' : 'negative'}>{token.change >= 0 ? '+' : ''}{token.change.toFixed(2)}%</small>}</strong></div>)}<div className="market-source-label"><span className="live-dot" /><span data-testid="hub-market-source">DexScreener snapshot<br />{token.market_updated ? new Date(token.market_updated * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Data not available'}</span></div></div>
    <EventTicker token={token} />
    <HubOverview key={address} token={token} />
    <nav className="hub-tabs" id="token-ecosystem">{[['trade', BarChart3], ['market', Store], ['events', CalendarDays], ['community', Users]].map(([name, Icon]) => <NavLink key={name} to={`/token/${address}/${name}#token-ecosystem`} className={() => name === tab ? 'active' : ''} data-testid={`hub-tab-${name}`}><Icon size={17} />{name[0].toUpperCase() + name.slice(1)}{name === 'market' && <span className="tab-dot" />}</NavLink>)}</nav>
    <section className="hub-content">{tab === 'market' ? <Market token={token} /> : tab === 'community' ? <Community token={token} /> : tab === 'events' ? <HubEvents token={token} /> : tab === 'trade' ? <Trade token={token} integrated /> : <ErrorBox error="This Token Hub section does not exist." />}</section>
  </main>;
}