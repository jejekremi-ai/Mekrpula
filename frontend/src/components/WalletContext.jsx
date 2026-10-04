import { createContext, useContext, useState, useEffect, useRef } from 'react';
import bs58 from 'bs58';
import { Wallet, ArrowUpRight, ShieldCheck, LogOut } from 'lucide-react';
import { toast } from 'sonner';
import { api, short } from '../lib/api';
import { Modal, Btn, ErrorBox } from './Kit';

const Context = createContext(null);
export const useWallet = () => useContext(Context);
export const WalletProvider = ({ children }) => {
  const [wallet, setWallet] = useState(null), [open, setOpen] = useState(false), [busy, setBusy] = useState(''), [error, setError] = useState('');
  const provider = useRef(null);
  const reset = () => { sessionStorage.removeItem('mart-session'); setWallet(null); provider.current = null; };
  useEffect(() => { sessionStorage.removeItem('mart-session'); }, []);
  useEffect(() => {
    const p = provider.current; if (!p) return;
    const change = () => { reset(); toast.info('Wallet changed. Please sign in again.'); };
    p.on?.('accountChanged', change); p.on?.('disconnect', reset);
    return () => { p.removeListener?.('accountChanged', change); p.removeListener?.('disconnect', reset); };
  }, [wallet]);
  async function connect(name) {
    setError(''); const p = name === 'Phantom' ? window.phantom?.solana || (window.solana?.isPhantom ? window.solana : null) : window.solflare;
    if (!p) { setError(`${name} was not detected. Open MART in the ${name} app browser or install its browser extension.`); return; }
    setBusy(name);
    try { await p.connect(); const address = p.publicKey.toString(); const challenge = await api('/auth/challenge', { method: 'POST', body: { wallet: address } }); const signed = await p.signMessage(new TextEncoder().encode(challenge.message), 'utf8'); const result = await api('/auth/verify', { method: 'POST', body: { nonce: challenge.nonce, signature: bs58.encode(signed.signature || signed) } }); sessionStorage.setItem('mart-session', result.token); provider.current = p; setWallet(address); setOpen(false); toast.success('Wallet connected. Welcome to MART.'); }
    catch(e) { setError(e.message || 'Wallet connection was cancelled.'); } finally { setBusy(''); }
  }
  async function disconnect() { await api('/auth/logout', { method: 'POST' }).catch(() => {}); const p = provider.current; reset(); await p?.disconnect?.(); setOpen(false); }
  const requireWallet = () => { if (wallet) return true; setOpen(true); return false; };
  return <Context.Provider value={{ wallet, provider, requireWallet, openWallet: () => { setError(''); setOpen(true); }, disconnect }}>
    {children}<Modal open={open} onClose={() => setOpen(false)} title={wallet ? 'Your wallet' : 'Connect your wallet'} description="Your keys. Your tokens. Always in your control." id="wallet">
      <div className="wallet-network"><span className="live-dot" /> Solana mainnet <span>Real assets · real network fees</span></div>
      {wallet ? <><code className="break-address" data-testid="connected-address">{wallet}</code><Btn secondary data-testid="disconnect-wallet" onClick={disconnect}><LogOut size={16} />Disconnect {short(wallet)}</Btn></> : <>{['Phantom', 'Solflare'].map((name, i) => <button className="wallet-option" data-testid={`connect-${name.toLowerCase()}`} onClick={() => connect(name)} disabled={!!busy} key={name}><span className={`wallet-icon wallet-${i}`}><Wallet size={22} /></span><strong>{name}</strong><span>{busy === name ? 'Waiting for wallet…' : 'Connect'}<ArrowUpRight size={16} /></span></button>)}<ErrorBox error={error} /><div className="wallet-install"><a data-testid="install-phantom" target="_blank" rel="noreferrer" href={process.env.REACT_APP_PHANTOM_URL}>Get Phantom ↗</a><a data-testid="install-solflare" target="_blank" rel="noreferrer" href={process.env.REACT_APP_SOLFLARE_URL}>Get Solflare ↗</a></div></>}
      <p className="security-note"><ShieldCheck size={17} />Signing in is free. MART never asks for your seed phrase.</p>
    </Modal>
  </Context.Provider>;
};