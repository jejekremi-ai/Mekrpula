import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, useLocation, Link } from 'react-router-dom';
import { Toaster } from 'sonner';
import { Buffer } from 'buffer';
import { WalletProvider } from './components/WalletContext';
import { Header, Footer } from './components/Shell';
import Home from './pages/Home';
import Explore from './pages/Explore';
import Hub from './pages/Hub';
import Events, { EventDetail } from './pages/Events';
import Launch from './pages/Launch';
import AddToken from './pages/AddToken';
import Wallet from './pages/Wallet';
import Docs from './pages/Docs';
import { Empty } from './components/Kit';
import './App.css';
import './content.css';
import './agent.css';
import './compute.css';
window.Buffer = Buffer;
const Scroll = () => {
  const { pathname, hash, key } = useLocation();
  // A fresh history entry also handles clicking an already-selected anchor.
  // Ordinary search/filter query changes retain their existing scroll behavior.
  const anchorVisit = hash ? key : '';
  useEffect(() => {
    document.title = pathname.startsWith('/docs') ? 'MART Docs — Your token ecosystem guide.' : 'MART — A market built around every token.';
    const frame = requestAnimationFrame(() => {
      let id = hash.slice(1);
      try { id = decodeURIComponent(id); } catch { /* Invalid URL encoding is not an app error. */ }
      const target = hash ? document.getElementById(id) : null;
      if (target) target.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' });
      else window.scrollTo(0, 0);
    });
    return () => cancelAnimationFrame(frame);
  }, [pathname, hash, anchorVisit]);
  return null;
};
function App() { return <BrowserRouter><WalletProvider><Scroll /><Header /><Routes><Route path="/" element={<Home />} /><Route path="/explore" element={<Explore />} /><Route path="/token/:address/:tab?" element={<Hub />} /><Route path="/events" element={<Events />} /><Route path="/events/:id" element={<EventDetail />} /><Route path="/launch" element={<Launch />} /><Route path="/add-token" element={<AddToken />} /><Route path="/wallet" element={<Wallet />} /><Route path="/docs/:topic?" element={<Docs />} /><Route path="*" element={<main className="container page"><Empty title="This corner of MART doesn’t exist." text="Let’s get you back to the ecosystem."><Link className="btn btn-primary" to="/" data-testid="not-found-home">Back to MART</Link></Empty></main>} /></Routes><Footer /><Toaster theme="dark" position="bottom-right" richColors closeButton /></WalletProvider></BrowserRouter>; }
export default App;