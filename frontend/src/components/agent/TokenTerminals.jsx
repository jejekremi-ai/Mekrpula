import { Link } from 'react-router-dom';
import { BarChart3, Radio, Sparkles, MessageSquare, ExternalLink } from 'lucide-react';
import { money, short } from '../../lib/api';
import { TokenPriceChart } from './TokenPriceChart';
import { TerminalHeader, TerminalMarkdown, timeLabel } from './ResearchActivity';

export const AgentMarketTerminal = ({ token }) => <section className="terminal-pane market-pane" data-testid="hub-chart-container">
  <TerminalHeader icon={BarChart3} title="Market" label={token.change == null ? '24H' : `${token.change >= 0 ? '+' : ''}${token.change.toFixed(2)}% · 24H`} id="terminal-market" />
  <TokenPriceChart token={token} />
  <footer className="terminal-footnote"><a href={token.dex_url} target="_blank" rel="noreferrer" data-testid="hub-overview-chart-link">Open full chart<ExternalLink size={10} /></a><span data-testid="terminal-market-source">Public price history</span></footer>
</section>;

export const EventRadar = ({ token, events, error }) => <section className="terminal-pane radar-pane" data-testid="event-radar-terminal">
  <TerminalHeader icon={Radio} title="Event radar" label={`${events?.length || 0} events`} id="event-radar" />
  <div className="radar-signals" data-testid="radar-signals">
    {token.change != null && <div data-testid="radar-price-signal"><i className={token.change < 0 ? 'down' : 'up'} /><p>Price {token.change < 0 ? 'down' : 'up'} <strong>{Math.abs(token.change).toFixed(2)}%</strong></p><span>24h</span></div>}
    {token.volume != null && <div data-testid="radar-volume-signal"><i /><p>Trading volume <strong>{money(token.volume)}</strong></p><span>24h</span></div>}
    {token.liquidity != null && <div data-testid="radar-liquidity-signal"><i /><p>Pool liquidity <strong>{money(token.liquidity)}</strong></p><span>snapshot</span></div>}
    <span className="radar-snapshot" data-testid="radar-snapshot">DexScreener · {token.market_updated ? `${timeLabel(token.market_updated * 1000)} UTC` : 'Snapshot time unavailable'}</span>
  </div>
  <div className="radar-events"><span className="terminal-subheading" data-testid="radar-events-label">OFFICIAL EVENTS</span>{error ? <p className="terminal-notice" data-testid="radar-event-error">{error}</p> : events?.length ? events.map(event => <article key={event.id} data-testid={`radar-event-${event.id}`}><div><span className="terminal-stage">{event.status.toUpperCase()}</span><Link to={`/events/${event.id}`} data-testid={`radar-event-link-${event.id}`} title="Open event details"><ExternalLink size={11} /></Link></div><strong data-testid={`radar-event-title-${event.id}`}>{event.title}</strong><p data-testid={`radar-event-description-${event.id}`}>{event.description}</p></article>) : <p className="terminal-muted" data-testid="radar-no-events">No official events announced.</p>}</div>
</section>;

export const EventIdeas = ({ run }) => <section className="terminal-pane ideas-pane" data-testid="event-ideas-terminal"><TerminalHeader icon={Sparkles} title="Event ideas" label="DRAFTS ONLY" id="event-ideas" />{run?.sections?.events ? <div className="terminal-idea-content"><TerminalMarkdown text={run.sections.events} id="event-ideas-content" /><p className="terminal-draft-note" data-testid="event-ideas-disclaimer">Proposals from research. Not published or scheduled events.</p></div> : <p className="terminal-muted terminal-padding" data-testid="event-ideas-empty">No event ideas recorded yet.</p>}</section>;

export const CommunityTerminal = ({ posts, error }) => <section className="terminal-pane community-pane" data-testid="community-terminal"><TerminalHeader icon={MessageSquare} title="Community" label={`${posts?.length || 0} posts`} id="terminal-community" /><div className="terminal-community-body">{error ? <p className="terminal-notice" data-testid="terminal-community-error">{error}</p> : posts?.length ? posts.map(post => <article key={post.id} data-testid={`terminal-post-${post.id}`}><div><strong>{short(post.author)}</strong><time data-testid={`terminal-post-time-${post.id}`}>{timeLabel(post.created_at)}</time></div><p data-testid={`terminal-post-text-${post.id}`}>{post.text}</p></article>) : <p className="terminal-muted" data-testid="terminal-community-empty">No community posts yet.</p>}</div></section>;