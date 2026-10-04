import { ArrowUpRight, Box, ShoppingBag, Store, Users, Radio, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';
import { HOODIE } from '../lib/api';
import { TokenAvatar } from './Kit';

const GREEN_ART = 'https://images.unsplash.com/photo-1667373509687-4c4574541218?auto=format&fit=crop&w=650&q=85';
export const TokenHubPreview = ({ tokens }) => {
  const token = tokens?.find(t => t.address === '9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump');
  const display = token || { name: 'Your token', symbol: 'TOKEN' };
  const destination = token ? `/token/${token.address}/market` : '/explore';
  return <div className="hero-art hub-preview-art" data-testid="hero-market-preview">
    <div className="art-grid" /><div className="orbit orbit-one" /><div className="orbit orbit-two" />
    <span className="hub-preview-top floating-label" data-testid="preview-built-on-mart"><Sparkles size={14} />A whole world. Built on MART.<ArrowUpRight size={12} /></span>
    <div className="hub-preview-window" data-testid="illustrative-token-hub">
      <div className="preview-window-bar"><strong>MART</strong><span>/ TOKEN HUB</span><span className="live-dot" /></div>
      <div className="preview-token-heading"><TokenAvatar token={display} /><div><strong data-testid="preview-token-name">{display.name}</strong><span data-testid="preview-token-symbol">${display.symbol} ecosystem</span></div><Link to={destination} aria-label="Explore this Token Hub" data-testid="preview-open-token-hub"><ArrowUpRight size={20} /></Link></div>
      <div className="preview-token-tabs" aria-hidden="true"><span>Trade</span><span className="preview-active"><Store size={11} />Market</span><span>Events</span><span>Community</span></div>
      <div className="preview-products">
        <div className="preview-product"><div className="preview-product-image"><img src={GREEN_ART} alt="Green sculptural digital artwork, illustrative market concept" /><span><Box size={9} />DIGITAL</span></div><strong>Build your culture.</strong><small>Art for your community</small></div>
        <div className="preview-product"><div className="preview-product-image"><img src={HOODIE} alt="Black community streetwear, illustrative market concept" /><span><ShoppingBag size={9} />PHYSICAL</span></div><strong>Wear your conviction.</strong><small>Made for your people</small></div>
      </div>
      <div className="preview-window-bottom"><span className="live-dot" /><span>Your token. Its own market.</span><Store size={11} /></div>
    </div>
    <span className="hub-preview-community floating-label"><span className="check-box"><Users size={20} /></span><span>Not just holders.<strong>A whole community.</strong></span></span>
    <Link to="/explore" className="hub-preview-explore floating-label" data-testid="preview-explore"><Radio size={15} /><span>Big things start here.</span><span className="preview-explore-tag">EXPLORE<ArrowUpRight size={10} /></span></Link>
    <span className="hub-preview-caption" data-testid="hero-preview-disclaimer">ILLUSTRATIVE HUB · SAMPLE PRODUCTS, NOT LIVE LISTINGS</span>
    <span className="art-spark spark-one">+</span><span className="art-spark spark-two">+</span>
  </div>;
};