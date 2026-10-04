import { useState } from 'react';
import { Button } from './ui/button';
import { Dialog, DialogContent, DialogTitle, DialogDescription } from './ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { ArrowUpRight, Loader2, Upload, PackageOpen, AlertCircle } from 'lucide-react';
import { api, slug } from '../lib/api';
import { toast } from 'sonner';

export const Btn = ({ children, secondary, className = '', busy, disabled, ...props }) => <Button className={`btn ${secondary ? 'btn-secondary' : 'btn-primary'} ${className}`} disabled={!!busy || disabled} {...props}>{busy && <Loader2 className="spin" size={16} />}{children}</Button>;
export const Modal = ({ open, onClose, title, description, children, id }) => <Dialog open={open} onOpenChange={v => !v && onClose()}><DialogContent className="mart-modal" data-testid={`${id}-modal`}><DialogTitle data-testid={`${id}-modal-title`} className="modal-title">{title}</DialogTitle><DialogDescription className="muted" data-testid={`${id}-modal-description`}>{description}</DialogDescription>{children}</DialogContent></Dialog>;
export const Field = ({ label, id, textarea, hint, ...props }) => <label className="field" htmlFor={id}><span>{label}</span>{textarea ? <textarea id={id} data-testid={id} {...props} /> : <input id={id} data-testid={id} {...props} />}{hint && <small>{hint}</small>}</label>;
export const Choice = ({ id, label, value, onChange, options }) => <label className="field" htmlFor={id}><span>{label}</span><Select value={value} onValueChange={onChange}><SelectTrigger id={id} data-testid={id}><SelectValue /></SelectTrigger><SelectContent data-testid={`${id}-options`} className="mart-select">{options.map(o => <SelectItem data-testid={`${id}-${slug(typeof o === 'string' ? o : o.value)}`} value={typeof o === 'string' ? o : o.value} key={typeof o === 'string' ? o : o.value}>{typeof o === 'string' ? o : o.label}</SelectItem>)}</SelectContent></Select></label>;
export const Empty = ({ title, text, children, icon: Icon = PackageOpen }) => <div className="empty" data-testid="empty-state"><span className="empty-icon"><Icon size={27} /></span><h3 data-testid="empty-title">{title}</h3><p data-testid="empty-description">{text}</p>{children}</div>;
export const Loading = () => <div className="loading" data-testid="loading-state"><Loader2 className="spin" /> Loading MART…</div>;
export const ErrorBox = ({ error }) => error ? <div className="error-box" role="alert" data-testid="error-message"><AlertCircle size={17} />{error}</div> : null;
export const External = ({ href, children, id, className = '' }) => <a className={`external ${className}`} href={href} target="_blank" rel="noopener noreferrer" data-testid={id}>{children}<ArrowUpRight size={16} /></a>;
export const TokenAvatar = ({ token, small }) => <div className={`token-avatar ${small ? 'small' : ''}`}>{token.logo ? <img src={token.logo} alt={`${token.symbol} token`} onError={e => { e.currentTarget.style.display = 'none'; }} /> : <span>{token.symbol?.slice(0, 2)}</span>}</div>;
export const UploadImage = ({ id, label = 'Upload image', value, onChange }) => {
  const [busy, setBusy] = useState(false);
  async function upload(e) { const file = e.target.files[0]; if (!file) return; setBusy(true); try { const form = new FormData(); form.append('file', file); onChange((await api('/uploads', { method: 'POST', body: form })).url); } catch(e) { toast.error(e.message); } finally { setBusy(false); } }
  return <label className={`upload-box ${value ? 'has-image' : ''}`} data-testid={`${id}-area`}>{value ? <img src={value} alt="Uploaded preview" /> : busy ? <Loader2 className="spin" /> : <Upload size={22} />}<span>{busy ? 'Uploading…' : value ? 'Change image' : label}</span><small>PNG, JPG or WebP · up to 5 MB</small><input data-testid={id} type="file" accept="image/png,image/jpeg,image/webp" onChange={upload} disabled={busy} aria-label={label} /></label>;
};