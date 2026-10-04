import { Link } from 'react-router-dom';
import { ArrowUpRight } from 'lucide-react';
import { openAddToken } from '../../lib/navigation';

export const FooterInformation = () => <div className="mart-footer-content" data-testid="expanded-footer-content">
  <div className="mart-footer-context"><span className="eyebrow">THE TOKEN IS ONLY THE BEGINNING.</span><p>Trading. Commerce. Events. Community.<br />Everything around your token, together.</p><Link className="text-link" to="/docs" data-testid="footer-docs-introduction">Get to know MART<ArrowUpRight size={13} /></Link></div>
  <nav aria-label="Product links"><h3>Product</h3><Link to="/explore" data-testid="footer-product-explore">Explore</Link><Link to="/launch" data-testid="footer-product-launch">Launch</Link><button onClick={openAddToken} data-testid="footer-product-add-token">Add Token</button><Link to="/#markets" data-testid="footer-product-market">Market</Link><Link to="/events" data-testid="footer-product-events">Events</Link><Link to="/#community" data-testid="footer-product-community">Community</Link></nav>
  <nav aria-label="Resource links"><h3>Resources</h3><Link to="/docs" data-testid="footer-resource-docs">Docs</Link><Link to="/#faq" data-testid="footer-resource-faq">FAQ</Link><Link to="/#about" data-testid="footer-resource-about">About</Link><Link to="/docs/security" data-testid="footer-resource-security">Security</Link></nav>
  <div className="mart-footer-social" aria-label="Social channels"><h3>Social</h3><span data-testid="footer-social-x">X</span><span data-testid="footer-social-discord">Discord</span><span data-testid="footer-social-telegram">Telegram</span><small>Official links are not listed yet.</small></div>
</div>;