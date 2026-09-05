"""Conservative matching against an installed-app allowlist."""
import difflib
import re
import unicodedata


def normalize(text):
    text = ''.join(c for c in unicodedata.normalize('NFKD', text.casefold()) if not unicodedata.combining(c))
    return ' '.join(re.findall(r'[a-z0-9]+', text))


ALIASES = {
    'foot.desktop': ['terminal', 'terminalul', 'command line'],
    'chromium.desktop': ['browser', 'web browser', 'internet', 'browserul'],
    'org.gnome.Nautilus.desktop': ['file manager', 'files', 'fisiere', 'fisierele', 'manager de fisiere'],
    'btop.desktop': ['activity', 'system monitor', 'b top', 'bee top', 'btop', 'monitor de sistem'],
    'uconsole-keys.desktop': ['keybindings', 'keyboard guide', 'shortcuts', 'taste', 'scurtaturi'],
    'uconsole-theme-editor.desktop': ['theme colors', 'theme editor', 'culori', 'teme'],
    'uconsole-dictation.desktop': ['dictation settings', 'setari dictare'],
}


def match_apps(text, apps):
    query = normalize(text)
    query = re.sub(r'^(?:(?:please|open|launch|start|run|the|app|application|deschide|porneste|aplicatia|te rog)\s+)+', '', query)
    query = re.sub(r'\s+(?:please|te rog)$', '', query).strip()
    if not query:
        return [], None
    matches = []
    for app in apps:
        terms = [normalize(app['name']), *ALIASES.get(app['id'], [])]
        scores = [1.0 if query == term else difflib.SequenceMatcher(None, query, term).ratio() for term in terms]
        score = max(scores)
        if score >= .45:
            matches.append(dict(app, score=round(score, 3)))
    matches.sort(key=lambda a: (-a['score'], a['name'].casefold()))
    confident = bool(matches and matches[0]['score'] >= .94 and
                     (len(matches) == 1 or matches[0]['score']-matches[1]['score'] >= .12))
    return matches[:6], matches[0]['id'] if confident else None
