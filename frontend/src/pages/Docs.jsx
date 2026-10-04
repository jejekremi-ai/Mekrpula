import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, ArrowRight, ArrowUpRight, BookOpen, ChevronDown, Plus } from 'lucide-react';
import { DOCS } from '../content/mart';
import { Empty } from '../components/Kit';
import { openAddToken } from '../lib/navigation';

export default function Docs() {
  const { topic = 'introduction' } = useParams();
  const index = DOCS.findIndex(doc => doc.slug === topic), doc = DOCS[index];
  const [menu, setMenu] = useState(false);
  if (!doc) return <main className="container page"><Empty title="This guide could not be found." text="Find the practical MART guides in the documentation."><Link className="btn btn-primary" to="/docs" data-testid="docs-not-found-home">Open MART Docs</Link></Empty></main>;
  return <main className="container mart-docs-page" data-testid="docs-page">
    <div className="breadcrumbs"><Link to="/" data-testid="docs-back-home"><ArrowLeft size={13} />MART</Link><span>/</span><Link to="/docs" data-testid="docs-breadcrumb">Docs</Link><span>/</span><span data-testid="docs-current-topic">{doc.title}</span></div>
    <div className="mart-docs-layout">
      <aside className="mart-docs-sidebar"><Link className="mart-docs-brand" to="/docs" data-testid="docs-sidebar-home"><BookOpen size={21} /><strong>MART Docs</strong></Link><p>The practical guide to your token’s ecosystem.</p><button className="mart-docs-topic-toggle" aria-expanded={menu} aria-controls="docs-topic-navigation" onClick={() => setMenu(!menu)} data-testid="docs-topic-toggle"><span>Browse topics<span>{doc.title}</span></span><ChevronDown size={17} /></button><nav className={menu ? 'mart-docs-navigation open' : 'mart-docs-navigation'} id="docs-topic-navigation" aria-label="Documentation topics">{DOCS.map((item, i) => <Link className={item.slug === topic ? 'active' : ''} aria-current={item.slug === topic ? 'page' : undefined} to={`/docs/${item.slug}`} onClick={() => setMenu(false)} key={item.slug} data-testid={`docs-nav-${item.slug}`}><span className="mono">{String(i + 1).padStart(2, '0')}</span>{item.title}{item.slug === topic && <span className="live-dot" />}</Link>)}</nav><Link className="text-link mart-docs-back" to="/explore" data-testid="docs-explore">Back to the ecosystem<ArrowUpRight size={13} /></Link></aside>
      <article className="mart-docs-article" data-testid={`docs-content-${doc.slug}`}>
        <header className="mart-docs-article-heading"><span className="eyebrow">{doc.label}</span><h1 data-testid="docs-topic-title">{doc.title}<span className="green">.</span></h1><p data-testid="docs-topic-summary">{doc.summary}</p></header>
        <div className="mart-docs-contents"><span className="mini-label">IN THIS GUIDE</span><nav aria-label="Sections in this guide">{doc.sections.map((section, i) => <Link key={section.title} to={`/docs/${topic}#guide-section-${i}`} data-testid={`docs-section-link-${i}`}>{section.title}<ArrowUpRight size={11} /></Link>)}</nav></div>
        {doc.sections.map((section, i) => <section className="mart-docs-section" id={`guide-section-${i}`} key={`${topic}-${i}`} data-testid={`docs-section-${i}`}><h2>{section.title}</h2>{section.paragraphs?.map((p, n) => <p key={n} data-testid={`docs-paragraph-${i}-${n}`}>{p}</p>)}{section.items && <ul>{section.items.map((item, n) => <li key={item} data-testid={`docs-list-item-${i}-${n}`}>{item}</li>)}</ul>}{section.notice && <div className="mart-docs-notice" data-testid={`docs-notice-${i}`}>{section.notice}</div>}</section>)}
        {topic === 'add-token' && <button className="btn btn-primary" onClick={openAddToken} data-testid="docs-add-token"><Plus size={16} />Add a token</button>}
        {topic === 'introduction' && <div className="mart-docs-start-actions"><Link className="btn btn-primary" to="/explore" data-testid="docs-start-explore">Explore MART<ArrowUpRight size={15} /></Link><Link className="btn btn-secondary" to="/launch" data-testid="docs-start-launch">Launch Token<ArrowUpRight size={15} /></Link></div>}
        <nav className="mart-docs-pagination" aria-label="Previous and next guides"><Link to={index > 0 ? `/docs/${DOCS[index - 1].slug}` : '/#about'} data-testid="docs-previous"><ArrowLeft size={16} /><span><small>{index > 0 ? 'PREVIOUS GUIDE' : 'BACK TO MART'}</small><strong>{index > 0 ? DOCS[index - 1].title : 'About MART'}</strong></span></Link><Link to={index < DOCS.length - 1 ? `/docs/${DOCS[index + 1].slug}` : '/explore'} data-testid="docs-next"><span><small>{index < DOCS.length - 1 ? 'NEXT GUIDE' : 'PUT IT INTO PRACTICE'}</small><strong>{index < DOCS.length - 1 ? DOCS[index + 1].title : 'Explore MART'}</strong></span><ArrowRight size={16} /></Link></nav>
      </article>
    </div>
  </main>;
}