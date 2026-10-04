import { useState } from 'react';
import { Bot, Check, Cpu, ChevronDown, ShieldCheck } from 'lucide-react';
import { useData } from '../../lib/api';
import { Choice, Field } from '../Kit';
import { Switch } from '../ui/switch';
import { ROLES, CAPABILITIES, providerMark } from './agentData';

export const AgentCreatorFields = ({ prefix, enabled, onToggle, profile, onChange, disabled = false }) => {
  const { data, loading, error, reload } = useData('/agent/models');
  const [advanced, setAdvanced] = useState(false);
  const models = data?.models || [];
  const selected = models.find(m => m.id === profile.model_id);
  const provider = selected?.provider || 'Anthropic';
  const set = (key, value) => onChange(p => ({ ...p, [key]: value }));
  return <section className="creator-agent-fields" data-testid={`${prefix}-agent-section`}>
    <div className="creator-agent-toggle"><span className="creator-agent-icon"><Bot size={23} /></span><label htmlFor={`${prefix}-agent-toggle`}><strong data-testid={`${prefix}-agent-title`}>Ecosystem agent <small>OPTIONAL</small></strong><span>Choose the role, model, and direction for your token.</span></label><Switch id={`${prefix}-agent-toggle`} data-testid={`${prefix}-agent-toggle`} checked={enabled} onCheckedChange={onToggle} disabled={disabled} /></div>
    {!enabled && <p className="creator-agent-off" data-testid={`${prefix}-agent-off`}>No agent. Your token still gets its own market, events, and community.</p>}
    {enabled && <fieldset className="creator-agent-inputs" disabled={disabled} data-testid={`${prefix}-agent-fields`}>
      <div className="form-row"><Field id={`${prefix}-agent-name`} label="Agent name" placeholder="Your ecosystem's representative" required minLength={2} maxLength={60} value={profile.name} onChange={e => set('name', e.target.value)} /><Choice id={`${prefix}-agent-role`} label="Role" value={profile.role} options={ROLES.map(r => r.name)} onChange={v => { set('role', v); set('mission', ROLES.find(r => r.name === v).mission); }} /></div>
      <div className="creator-model-heading"><span><Cpu size={15} />Choose an AI model</span><span>CREATOR SELECTED</span></div>
      {loading ? <p data-testid={`${prefix}-models-loading`} className="creator-agent-note">Loading model catalog…</p> : error ? <div role="alert" data-testid={`${prefix}-models-error`} className="creator-agent-note">{error}<button type="button" className="text-link" data-testid={`${prefix}-models-retry`} onClick={reload}>Retry</button></div> : <>
        <Choice id={`${prefix}-agent-provider`} label="Provider" value={provider} options={[...new Set(models.map(m => m.provider))]} onChange={v => set('model_id', models.find(m => m.provider === v).id)} />
        <div className="creator-model-grid" role="radiogroup" aria-label="AI model" data-testid={`${prefix}-agent-model-select`}>{models.filter(m => m.provider === provider).map(m => <button type="button" role="radio" aria-checked={profile.model_id === m.id} key={m.id} data-testid={`${prefix}-model-${m.id}`} onClick={() => set('model_id', m.id)} className={`creator-model-option ${profile.model_id === m.id ? 'selected' : ''}`}><span className={`provider-mark provider-${m.provider.toLowerCase()}`}>{providerMark(m.provider)}</span><strong>{m.name}</strong><span className="creator-model-check">{profile.model_id === m.id && <Check size={12} />}</span><p>{m.description}</p><small>{m.type} · {m.context} context</small></button>)}</div>
      </>}
      <Field textarea id={`${prefix}-agent-mission`} label="Mission" required minLength={10} maxLength={1200} value={profile.mission} onChange={e => set('mission', e.target.value)} />
      <button type="button" className="creator-agent-advanced" data-testid={`${prefix}-agent-advanced`} aria-expanded={advanced} aria-controls={`${prefix}-agent-advanced-fields`} onClick={() => setAdvanced(!advanced)}>Behavior & capabilities<ChevronDown size={16} className={advanced ? 'rotated' : ''} /></button>
      {advanced && <div className="creator-agent-advanced-fields" id={`${prefix}-agent-advanced-fields`}>
        <div className="form-row"><Choice id={`${prefix}-agent-risk`} label="Strategy posture" value={profile.risk} onChange={v => set('risk', v)} options={['Conservative', 'Balanced', 'Exploratory']} /><Field id={`${prefix}-agent-creativity`} label="Creativity (0–1)" type="number" min="0" max="1" step="0.1" required value={profile.creativity} onChange={e => set('creativity', Number(e.target.value))} /></div>
        <Field textarea id={`${prefix}-agent-instructions`} label="Private operating instructions (optional)" maxLength={4000} value={profile.instructions} onChange={e => set('instructions', e.target.value)} placeholder="Voice, boundaries, and details for your agent…" />
        <div className="creator-capabilities">{CAPABILITIES.map(c => <label key={c.id}><input type="checkbox" data-testid={`${prefix}-capability-${c.id}`} checked={profile.capabilities.includes(c.id)} onChange={e => set('capabilities', e.target.checked ? [...profile.capabilities, c.id] : profile.capabilities.filter(k => k !== c.id))} /><c.icon size={13} />{c.name}</label>)}</div>
      </div>}
      <p className="creator-agent-boundary" data-testid={`${prefix}-agent-notice`}><ShieldCheck size={16} />Model ditetapkan kreator. Riset menggunakan kredit uji per token; jalankan satu riset manual sebelum mengaktifkan jadwal. {selected && !selected.runnable ? 'Provider ini memerlukan API key terpisah dan belum dapat menjalankan riset.' : 'Model siap menjalankan riset.'}</p>
    </fieldset>}
  </section>;
};