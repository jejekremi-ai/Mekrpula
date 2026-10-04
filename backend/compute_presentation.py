"""English public projections; never rewrite original reports or billing history."""
import re

LEGACY_TITLES = {
    'queued': 'Research queued', 'observe': 'Market and ecosystem snapshot captured',
    'research': 'Research in progress', 'proposal': 'Event ideas drafted; not published',
    'completed': 'Research completed', 'failed': 'Research interrupted',
    'credit': 'Test credits added', 'settings': 'Operating settings updated',
    'schedule': 'Research schedule updated', 'schedule-paused': 'Research schedule paused',
}

def public_activity(items):
    return [{**item, 'title': item['title'] if item.get('language') == 'en' and not re.search(r'\b(riset|jadwal|kreator|berakhir|dijeda)\b', item['title'], re.I)
             else LEGACY_TITLES.get(item['kind'], 'Agent status updated')} for item in items]

def sections(text):
    result = {}
    chunks = re.split(r'^##\s+(.+?)\s*$', text or '', flags=re.MULTILINE)
    for index in range(1, len(chunks) - 1, 2):
        title = chunks[index].strip().lower()
        key = {'summary': 'summary', 'market signals': 'market', 'ecosystem activity': 'ecosystem',
               'event ideas': 'events', 'risks & next steps': 'next_steps'}.get(title)
        if key: result[key] = chunks[index + 1].strip()
    return result

def public_run(row):
    text = row.get('output', '') if row.get('language') == 'en' else row.get('output_en', '')
    sources = [{**source, 'label': 'DexScreener · market snapshot' if 'dexscreener' in source['url']
                else 'Solscan · token identity' if 'solscan' in source['url'] else source['label']}
               for source in row.get('sources', [])]
    return {**row, 'display_output': text, 'sections': sections(text), 'sources': sources,
            'display_language': 'en', 'translation_pending': bool(row.get('output') and not text),
            'error': (row.get('error') if row.get('language') == 'en' else
                      'This research attempt did not complete. Its original record has been preserved.') if row.get('error') else None}