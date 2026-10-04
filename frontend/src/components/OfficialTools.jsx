import { useState } from 'react';
import { Settings2 } from 'lucide-react';
import { toast } from 'sonner';
import { api } from '../lib/api';
import { Btn, Modal, Field, UploadImage, ErrorBox } from './Kit';
import { useWallet } from './WalletContext';

export const ManageHub = ({ token, reload }) => {
  const { wallet } = useWallet(); const [open, setOpen] = useState(false), [description, setDescription] = useState(token.description || ''), [banner, setBanner] = useState(token.banner || ''), [busy, setBusy] = useState(false), [error, setError] = useState('');
  if (!wallet || token.claimed_by !== wallet) return null;
  async function submit(e) { e.preventDefault(); setBusy(true); setError(''); try { await api(`/tokens/${token.address}`, { method: 'PATCH', body: { description, banner } }); setOpen(false); reload(); toast.success('Official Hub information updated.'); } catch(e) { setError(e.message); } finally { setBusy(false); } }
  return <><button className="text-link" data-testid="manage-token-hub" onClick={() => setOpen(true)}><Settings2 size={15} />Manage Hub</button><Modal open={open} onClose={() => setOpen(false)} title="Make this Hub your own" description="Your on-chain metadata authority is re-verified when you save." id="manage-hub"><form className="form-stack" onSubmit={submit}><Field textarea id="hub-edit-description" label="Official description" value={description} onChange={e => setDescription(e.target.value)} maxLength={2000} /><UploadImage id="hub-edit-banner" value={banner} onChange={setBanner} label="Update Hub banner" /><ErrorBox error={error} /><Btn busy={busy} data-testid="hub-profile-save" type="submit">Save Hub</Btn></form></Modal></>;
};
export const ManageEvent = ({ event, reload }) => {
  const { wallet } = useWallet(); const [busy, setBusy] = useState(false);
  if (!wallet || event.creator !== wallet) return null;
  async function change(status) { setBusy(true); try { await api(`/events/${event.id}`, { method: 'PATCH', body: { status } }); toast.success('Event status updated.'); reload(); } catch(e) { toast.error(e.message); } finally { setBusy(false); } }
  return <div className="event-status-actions" data-testid="manage-event-status">{[['live', 'Mark Live'], ['upcoming', 'Mark Coming Soon'], ['past', 'Mark Past']].map(([status, title]) => <button key={status} disabled={busy || event.status === status} onClick={() => change(status)} data-testid={`event-set-${status}`}>{title}</button>)}</div>;
};