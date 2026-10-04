import { Link } from 'react-router-dom';
import { ArrowUpRight, BookOpen } from 'lucide-react';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '../ui/accordion';
import { FAQ_ITEMS } from '../../content/mart';
import { AboutInformation } from './AboutInformation';
import { EcosystemInformation } from './EcosystemInformation';
import { ParticipationInformation } from './ParticipationInformation';
import { InfoSection } from './InfoSection';

export const MartInformation = () => <div className="mart-information" data-testid="mart-information">
  <div className="mart-content-index" data-testid="mart-content-index"><span className="mini-label">GET TO KNOW THE ECOSYSTEM</span><nav aria-label="About MART sections">{[['About', 'about'], ['How it works', 'mart-how-it-works'], ['Token Hubs', 'token-hubs'], ['Markets', 'markets'], ['FAQ', 'faq']].map(([label, id]) => <Link key={id} to={`/#${id}`} data-testid={`information-jump-${id}`}>{label}<ArrowUpRight size={11} /></Link>)}</nav></div>
  <AboutInformation /><EcosystemInformation /><ParticipationInformation />
  <InfoSection id="faq" kicker="A FEW THINGS YOU MIGHT BE WONDERING" title="FAQ" className="mart-faq-section" intro="The essentials, without the guesswork.">
    <Accordion type="single" collapsible className="mart-faq" data-testid="mart-faq">{FAQ_ITEMS.map((item, i) => <AccordionItem value={item.id} key={item.id} className="mart-faq-item"><AccordionTrigger className="mart-faq-question" data-testid={`faq-question-${item.id}`}><span className="mono">{String(i + 1).padStart(2, '0')}</span><span>{item.question}</span></AccordionTrigger><AccordionContent className="mart-faq-answer" data-testid={`faq-answer-${item.id}`}>{item.answer}</AccordionContent></AccordionItem>)}</Accordion>
  </InfoSection>
  <section className="mart-docs-callout" data-testid="docs-callout"><span className="mart-docs-icon"><BookOpen size={25} /></span><div><span className="eyebrow">GO FROM UNDERSTANDING TO DOING</span><h2 data-testid="docs-callout-title">The details are in the Docs.</h2><p>Practical guides to Token Hubs, listings, verification, fees, and staying safe.</p></div><Link className="btn btn-secondary" to="/docs" data-testid="open-docs-callout">Read the Docs<ArrowUpRight size={16} /></Link></section>
</div>;