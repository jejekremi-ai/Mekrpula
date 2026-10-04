import { Eye, ScanSearch, Brain, Waypoints, Zap, Activity, BookOpen } from 'lucide-react';
export const CAPABILITIES = [
  { id: 'observe', name: 'Observe', icon: Eye, text: 'Market & ecosystem signals' },
  { id: 'research', name: 'Research', icon: ScanSearch, text: 'Context & community insights' },
  { id: 'think', name: 'Analyze', icon: Brain, text: 'Reasoning within your brief' },
  { id: 'strategy', name: 'Plan', icon: Waypoints, text: 'Proposals with a purpose' },
  { id: 'act', name: 'Propose', icon: Zap, text: 'Actions for human approval' },
  { id: 'monitor', name: 'Monitor', icon: Activity, text: 'Outcomes & feedback' },
  { id: 'learn', name: 'Learn', icon: BookOpen, text: 'Memory & lessons' },
];
export const ROLES = [
  { name: 'Community steward', mission: 'Bring the community together with meaningful events, thoughtful updates, and creative ideas that give holders a place to belong.' },
  { name: 'Market analyst', mission: 'Research market signals and ecosystem activity. Present transparent observations and proposals, without promising returns or executing trades.' },
  { name: 'Creative director', mission: 'Shape a distinctive creative identity through artwork concepts, stories, and community drops that build a culture beyond the chart.' },
];
export const providerMark = name => ({ Anthropic: 'A', OpenAI: '◎', Google: 'G', DeepSeek: 'D', Qwen: 'Q', Mistral: 'M' }[name] || 'AI');
export const createAgentProfile = () => ({ name: '', role: ROLES[0].name, mission: ROLES[0].mission,
  model_id: 'claude-sonnet-4-5', creativity: 0.7, risk: 'Conservative', instructions: '',
  capabilities: CAPABILITIES.map(c => c.id) });