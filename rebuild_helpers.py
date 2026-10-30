"""Helpers for rebuilding csm_dashboard.html. Attach this file with the runbook and the dashboard.
Usage in a rebuild session:  from rebuild_helpers import *
Every function here was checked against the data already in the Oct 29, 2026 build."""
import json, re, collections

# ---- reading what the Salesforce connector stored when a result was too large for the chat ----
def sf_records(path):
    d = json.load(open(path)); inner = json.loads(d[0]['text'])
    return json.loads(inner[0]['outputValues']['resultJson'])['records']

# ---- replacing a data constant in the dashboard file ----
def _end_of_literal(s, i):
    """s[i] is [ or {. Returns the index just past the matching bracket, skipping strings."""
    depth = 0; q = None; esc = False
    for j in range(i, len(s)):
        c = s[j]
        if q:
            if esc: esc = False
            elif c == '\\': esc = True
            elif c == q: q = None
        elif c in '"\'`': q = c
        elif c in '[{': depth += 1
        elif c in ']}':
            depth -= 1
            if depth == 0: return j + 1
    raise ValueError('unbalanced literal')

def get_const(html, name):
    m = re.search(r'\b(?:const|let) %s\s*=\s*' % re.escape(name), html)
    i = m.end(); j = _end_of_literal(html, i)
    return json.loads(html[i:j].replace('null', 'null')), i, j

def patch_const(html, name, value):
    """Replace the JSON-style literal assigned to `name`. Returns the new html."""
    m = re.search(r'\b(?:const|let) %s\s*=\s*' % re.escape(name), html)
    i = m.end(); j = _end_of_literal(html, i)
    return html[:i] + json.dumps(value, separators=(',', ':'), ensure_ascii=False) + html[j:]

# ---- the dashboard's names differ from Salesforce/Gainsight for these 10 accounts ----
ALIAS = {'Marin Health Ventures, LLC': 'Marin Health Ventures, LLC (Formerly #0553)',
 'Sharp Surgery Center of San Diego': 'Sharp Surgery Center of San Diego (formerly Coast Surgery Center)',
 'Regional Hand Center of Central California': 'Regional Hand Center of Central California, Inc.',
 'The Orthopedic Surgical Center of Montana': 'The Orthopedic Surgical Center of Montana (formerly #622)',
 'Creekside Surgery Center': 'Creekside Surgery Center (formerly Providence Surgery Center)',
 'Wisconsin Institute of Surgical Excellence': 'Wisconsin Institute of Surgical Excellence, LLC',
 'Marina Orthopedic & Spine Institute, LLC': 'Marina Orthopedic & Spine Institute, LLC (Formerly 1000)',
 'Calabasas Surgery Center, LLC': 'Calabasas Surgery Center, LLC (Formerly #2692)',
 'Cheyenne Surgical Center': 'Cheyenne Surgical Center (Formerly #0233)',
 'Cedars-Sinai Surgery Center at Torrance': 'Cedars-Sinai Surgery Center at Torrance, LLC'}
REV_ALIAS = {v: k for k, v in ALIAS.items()}

def sf_id(ids, name):
    """ACCT_IDS maps the Gainsight name to [gainsight id, salesforce id]."""
    return (ids.get(name) or ids.get(ALIAS.get(name, name)) or [None, None])[1]

# ---- support: open cases, closed in the last 91 days, urgent flags, and the 90-day trend ----
def support_counts(l90_cases, p90_cases):
    """l90_cases/p90_cases: Case records created in the last 91 days / the 91 before.
    Returns (created L90, closed among them, created P90, urgent closed, open High/Urgent) by AccountId."""
    L = collections.Counter(); LC = collections.Counter(); P = collections.Counter(); UC = collections.Counter()
    HI = collections.defaultdict(collections.Counter); OP = collections.Counter()
    for r in l90_cases:
        k = r['AccountId']; L[k] += 1
        if r['IsClosed']:
            LC[k] += 1
            if r['Priority'] == 'Urgent': UC[k] += 1
        else:
            OP[k] += 1
            if r['Priority'] in ('High', 'Urgent'): HI[k][r['Priority']] += 1
    for r in p90_cases:
        k = r['AccountId']; P[k] += 1
        if not r['IsClosed']:
            OP[k] += 1
            if r['Priority'] in ('High', 'Urgent'): HI[k][r['Priority']] += 1
    return L, LC, P, UC, HI, OP

def case_trend(counter, accounts_by_id):
    return sorted(([accounts_by_id[k], c] for k, c in counter.items() if k in accounts_by_id), key=lambda x: (-x[1], x[0]))

# ---- engagement: last logged call, meeting or email ----
def engagement(rows, dashboard_names, cutoff_date):
    """rows: Gainsight activity_timeline grouped by company [{CompanyName, LastTouch, ActivityCount}], all pages.
    Keeps accounts whose last touch is before cutoff_date (today minus 30 days); accounts with no row at all get [None, 0]."""
    out = {}; seen = set()
    for r in rows:
        n = REV_ALIAS.get(r['CompanyName'], r['CompanyName'])
        if n not in dashboard_names: continue
        seen.add(n)
        if r['LastTouch'][:10] < cutoff_date: out[n] = [r['LastTouch'][:10], r['ActivityCount']]
    for n in dashboard_names:
        if n not in seen: out[n] = [None, 0]
    return out

if __name__ == '__main__':      # self-check against the dashboard already built
    import sys
    html = open(sys.argv[1] if len(sys.argv) > 1 else 'csm_dashboard.html', encoding='utf-8').read()
    for nm in ('CASES_L90', 'CASES_P90', 'SUPPORT', 'ENG', 'ACCT_BILL', 'CSM_SUM'):
        v, i, j = get_const(html, nm); print(nm, 'parsed', len(v), 'entries')
    assert patch_const(html, 'ACCT_OPPS', get_const(html, 'ACCT_OPPS')[0]).count('const ACCT_OPPS=') == 1
    print('helpers OK')
