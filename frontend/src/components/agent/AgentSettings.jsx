import { useState } from 'react';
import { Modal } from '../Kit';
import { CreditPanel } from './ComputePanels';
import { BudgetEstimator } from './BudgetEstimator';

export const AgentSettings = ({ open, onClose, data, busy, action, token, error }) => {
  const [tab, setTab] = useState('operation');
  return <Modal open={open} onClose={onClose} title="Agent settings" description={`Operating settings for ${token.symbol}. Test credits are not money or token assets.`} id="compute-settings">
    <div className="agent-settings-tabs" role="tablist" aria-label="Agent settings">{[['operation', 'Operation'], ['budget', 'Budget & schedule'], ['usage', 'Usage history']].map(([key, label]) => <button role="tab" aria-selected={tab === key} key={key} data-testid={`agent-settings-tab-${key}`} onClick={() => setTab(key)}>{label}</button>)}</div>
    {error && <p className="terminal-notice" role="alert" data-testid="agent-settings-error">{error}</p>}
    {!data ? <p data-testid="agent-settings-loading">Loading agent settings…</p> : <div className="agent-settings-body" role="tabpanel" data-testid={`agent-settings-panel-${tab}`}>
      {tab === 'operation' && <CreditPanel data={data} busy={busy} action={action} onEstimate={() => setTab('budget')} />}
      {tab === 'budget' && <BudgetEstimator data={data} busy={busy} action={action} modelId={data.model_id} />}
      {tab === 'usage' && <div className="settings-ledger" data-testid="compute-usage-history">{data.ledger.length ? data.ledger.map(item => <article key={item.id} data-testid={`ledger-${item.id}`}><div><strong>{item.kind === 'topup' ? 'Test credits added' : item.kind === 'usage' ? 'Research usage' : 'Reservation released'}</strong><span>{new Date(item.at).toLocaleString('en-US')} {item.model_id && `· ${item.model_id}`}</span>{item.usage?.total_tokens > 0 && <span data-testid={`ledger-tokens-${item.id}`}>{item.usage.input_tokens} input / {item.usage.output_tokens} output tokens · tools 0 CR</span>}{item.released > 0 && <span>Unused reservation released: {item.released.toFixed(4)} CR</span>}</div><strong data-testid={`ledger-amount-${item.id}`}>{item.amount > 0 ? '+' : ''}{item.amount.toFixed(4)} CR</strong></article>) : <p className="terminal-muted" data-testid="compute-ledger-empty">No usage recorded yet.</p>}</div>}
    </div>}
  </Modal>;
};