import { Activity, FileText, Download, ExternalLink, Loader2, Terminal, Check } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

export const timeLabel = at => new Date(at).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', timeZone: 'UTC' });
export const dateLabel = at => new Date(at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' });
export const TerminalHeader = ({ icon: Icon = Terminal, title, label, id }) => <header className="terminal-heading"><h2 data-testid={`${id}-title`}><Icon size={12} />{title}</h2>{label && <span data-testid={`${id}-label`}>{label}</span>}</header>;
export const TerminalMarkdown = ({ text, id }) => <div className="terminal-markdown" data-testid={id}><ReactMarkdown components={{ a: ({ node, ...props }) => <a {...props} data-testid={`${id}-link-${node.position?.start.offset}`} target="_blank" rel="noreferrer" /> }}>{text || ''}</ReactMarkdown></div>;

const kinds = { queued: 'QUEUED', observe: 'OBSERVED', research: 'RESEARCHING', proposal: 'DRAFTED', completed: 'COMPLETED', failed: 'INTERRUPTED', schedule: 'SCHEDULED', 'schedule-paused': 'PAUSED' };
const publicSummary = text => text?.split(/\n\s*\n/)[0].split(/(?<=[.!?])\s+(?=[A-Z])/).slice(0, 2).join(' ');
export const AgentActivityFeed = ({ data }) => {
  const items = (data?.activity || []).filter(item => item.run_id || item.kind === 'schedule-paused');
  const byRun = Object.fromEntries((data?.runs || []).map(run => [run.id, run]));
  return <section className="terminal-pane activity-pane" data-testid="activity-terminal-feed">
    <TerminalHeader icon={Activity} title="Agent activity" label={data?.active_run ? '● LIVE' : `${items.length} recorded`} id="terminal-activity" />
    <div className="terminal-activity-stream" role="log" aria-label="Agent activity" data-testid="terminal-event-log">
      {items.length ? items.map(item => <article className={`terminal-log-entry ${item.kind}`} key={item.id} data-testid={`activity-event-${item.id}`}><time dateTime={item.at} title={new Date(item.at).toUTCString()} data-testid={`activity-time-${item.id}`}><span>{dateLabel(item.at)}</span>{timeLabel(item.at)}</time><div><span className="terminal-stage" data-testid={`activity-stage-${item.id}`}><i />{kinds[item.kind] || 'UPDATED'}</span><p data-testid={`activity-title-${item.id}`}>{item.title}</p>{item.kind === 'completed' && byRun[item.run_id]?.sections?.summary && <TerminalMarkdown text={publicSummary(byRun[item.run_id].sections.summary)} id={`activity-summary-${item.id}`} />}{item.run_id && <small className="terminal-run-id" data-testid={`activity-run-${item.id}`}>run/{item.run_id.slice(0, 8)}</small>}</div></article>) : <div className="terminal-empty" data-testid="agent-activity-empty"><Activity size={19} /><strong>No activity yet</strong><p>This agent has not run research for this token.</p></div>}
    </div><footer className="terminal-footnote" data-testid="activity-feed-footer"><span><i />{data?.active_run ? 'Receiving live updates' : 'Waiting for the next run'}</span><span>UTC</span></footer>
  </section>;
};

const statusLabels = { queued: 'QUEUED', running: 'RESEARCHING', completed: 'COMPLETE', failed: 'INTERRUPTED', rejected: 'NOT STARTED' };
const save = (run, token) => { const file = new Blob([`# ${token.name} — Agent research\n\nModel: ${run.model_id}\nDate: ${run.created_at}\n\n${run.display_output}`], { type: 'text/markdown;charset=utf-8' }); const url = URL.createObjectURL(file); const a = document.createElement('a'); a.href = url; a.download = `${token.symbol}-research-${run.id.slice(0, 8)}.md`; a.click(); URL.revokeObjectURL(url); };

const Report = ({ run, token, latest = false }) => <article className={`inline-research-report ${latest ? 'latest' : ''}`} data-testid={`research-inline-report-${run.id}`}>
  <div className="inline-report-meta"><span data-testid={`research-report-meta-${run.id}`}>{dateLabel(run.created_at)} · {timeLabel(run.created_at)} UTC <b>/{run.trigger}</b></span><span className={`inline-report-status ${run.status}`} data-testid={`research-status-${run.id}`}>{run.status === 'running' && <Loader2 size={11} className="spin" />}{statusLabels[run.status]}</span>{run.display_output && <button title="Download research report" aria-label="Download research report" data-testid={`research-export-${run.id}`} onClick={() => save(run, token)}><Download size={12} /></button>}</div>
  {run.usage?.finish_reason === 'length' && <p className="terminal-notice" role="status" data-testid={`research-output-limit-${run.id}`}>Output limit reached. This report is partial; no automatic continuation was started.</p>}
  {run.error && <p className="terminal-notice" role="alert" data-testid={`research-error-${run.id}`}>{run.error}</p>}
  {run.display_output ? <TerminalMarkdown text={run.display_output} id={`research-output-${run.id}`} /> : <div className="terminal-research-wait" data-testid={`research-pending-${run.id}`}>{['queued', 'running'].includes(run.status) && <Loader2 size={15} className="spin" />}<p>{run.translation_pending ? 'English display is being prepared for this archived report.' : ['failed', 'rejected'].includes(run.status) ? 'No completed findings for this attempt.' : 'Collecting token context. Findings will appear here as they arrive.'}</p></div>}
  {run.status === 'running' && run.display_output && <span className="terminal-cursor" aria-label="Research streaming" data-testid={`research-streaming-${run.id}`} />}
  <div className="inline-report-footer"><span data-testid={`research-model-${run.id}`}>{run.model_id}</span><span data-testid={`research-id-${run.id}`}>run/{run.id.slice(0, 8)}</span></div>
</article>;

export const ResearchTerminal = ({ data, token, latest }) => {
  return <>
    <section className="terminal-pane research-pane" data-testid="research-terminal">
      <TerminalHeader icon={Terminal} title="Research terminal" label={latest ? `${latest.sources?.length || 0} sources` : 'STANDBY'} id="research-terminal" />
      <div className="terminal-source-bar" data-testid="research-source-bar"><span className="terminal-window-dots"><i /><i /><i /></span><span data-testid="research-source-kind">token/{token.symbol.toLowerCase()}</span><span className="terminal-source-state" data-testid="research-source-state">{latest?.status === 'running' ? '● WORKING' : latest?.status === 'completed' ? '✓ DONE' : '○ IDLE'}</span></div>
      <div className="terminal-source-links" data-testid="research-source-links">{latest?.sources?.map((source, i) => <a key={source.url} href={source.url} target="_blank" rel="noreferrer" data-testid={`research-source-${i}`}>{source.label.split(' · ')[0]}<ExternalLink size={10} /></a>)}{latest?.snapshot_at && <span data-testid="research-snapshot-time">snapshot {timeLabel(latest.snapshot_at)} UTC</span>}</div>
      <div className="research-terminal-body" data-testid="research-terminal-output">{latest ? <Report run={latest} token={token} latest /> : <div className="terminal-empty research-empty" data-testid="research-terminal-empty"><Terminal size={25} /><strong>Awaiting first research</strong><p>No research has been recorded for ${token.symbol}.</p><span className="terminal-idle-prompt">{token.symbol.toLowerCase()}<b> / ready</b><i /></span></div>}</div>
      <footer className="terminal-footnote" data-testid="research-terminal-footer"><span><Check size={10} />Source-grounded research</span><span>Public findings · read only</span></footer>
    </section>
  </>;
};

export const ResearchArchive = ({ data, token, latest }) => {
  const history = (data?.runs || []).filter(run => run.id !== latest?.id && (run.output || run.status === 'failed'));
  return history.length > 0 && <section className="terminal-pane archive-pane" data-testid="research-archive"><TerminalHeader icon={FileText} title="Research history" label={`${history.length} previous`} id="research-archive" /><div className="research-archive-body">{history.map(run => <Report key={run.id} run={run} token={token} />)}</div></section>;
};