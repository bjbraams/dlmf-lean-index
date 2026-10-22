#!/usr/bin/env python3
"""Build the site in docs/ from the data snapshot in data/.

Usage (from the root of this repository):

    python3 scripts/build.py

Inputs:
  data/dlmf-tags.json  the `@[dlmf]` dump written by lean-DLMF's scripts/DumpDLMF.lean
  data/sections.json   section titles and totals, from scripts/extract_sections.py
  templates/*.html     page templates; the data is substituted for `/*DATA*/null`

Outputs: docs/index.html (the index by DLMF chapter) and docs/mathlib.html (Mathlib and
TauCeti declarations, tagged or matched by a checked pointer, grouped by source file).
"""
import collections
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CHAPTERS = {
    1: 'Algebraic and Analytic Methods', 2: 'Asymptotic Approximations', 3: 'Numerical Methods',
    4: 'Elementary Functions', 5: 'Gamma Function',
    6: 'Exponential, Logarithmic, Sine, and Cosine Integrals',
    7: "Error Functions, Dawson's and Fresnel Integrals",
    8: 'Incomplete Gamma and Related Functions', 9: 'Airy and Related Functions',
    10: 'Bessel Functions', 11: 'Struve and Related Functions', 12: 'Parabolic Cylinder Functions',
    13: 'Confluent Hypergeometric Functions', 14: 'Legendre and Related Functions',
    15: 'Hypergeometric Function', 16: 'Generalized Hypergeometric Functions and Meijer G-Function',
    17: 'q-Hypergeometric and Related Functions', 18: 'Orthogonal Polynomials',
    19: 'Elliptic Integrals', 20: 'Theta Functions', 21: 'Multidimensional Theta Functions',
    22: 'Jacobian Elliptic Functions', 23: 'Weierstrass Elliptic and Modular Functions',
    24: 'Bernoulli and Euler Polynomials', 25: 'Zeta and Related Functions',
    26: 'Combinatorial Analysis', 27: 'Functions of Number Theory',
    28: "Mathieu Functions and Hill's Equation", 29: 'Lamé Functions',
    30: 'Spheroidal Wave Functions', 31: 'Heun Functions', 32: 'Painlevé Transcendents',
    33: 'Coulomb Functions', 34: '3j, 6j, 9j Symbols', 35: 'Functions of Matrix Argument',
    36: 'Integrals with Coalescing Saddles',
}
# Display order: upstream libraries first, lean-DLMF last.
PROJECTS = ['Mathlib', 'TauCeti', 'lean-DLMF']
STATUS = {'proved': 0, 'admitted': 1, 'proved from admissions': 2, 'nonstandard': 3}
RELATIONS = ['exact', 'stronger', 'special case', 'partial', 'different convention']


def natkey(s):
    return [int(x) if x.isdigit() else x for x in re.split(r'(\d+)', s)]


def repo_path(e):
    """Path of the declaration's file inside its own repository."""
    if not e['sourceUrl']:
        return ''
    return e['sourceUrl'].split('/blob/', 1)[1].split('/', 1)[1].split('#')[0]


def status(e):
    st = e['status']
    if st == 'admitted' and e.get('sorryDirect') is False:
        st = 'proved from admissions'
    return st


def meta_for(dump):
    info = dump['projects']
    return {p: {'url': re.sub(r'\.git$', '', (info.get(p) or {}).get('url') or ''),
                'rev': (info.get(p) or {}).get('rev') or '',
                'dirty': bool((info.get(p) or {}).get('dirty'))} for p in PROJECTS}


def index_data(dump, sections):
    files, file_idx = [], {}
    ids = collections.defaultdict(list)
    for e in dump['entries']:
        path = repo_path(e)
        if path not in file_idx:
            file_idx[path] = len(files)
            files.append(path)
        proj = e['project'] if e['project'] in PROJECTS else 'lean-DLMF'
        ids[e['dlmf']].append([e['decl'], PROJECTS.index(proj), STATUS[status(e)],
                               0 if e['kind'] == 'theorem' else 1, file_idx[path], e['line'] or 0,
                               1 if e.get('source') == 'pointer' else 0,
                               e['comment'], e.get('recordedIn') or ''])
    notes = {i: n for i, n in sections['equations'].items() if i not in ids}
    counts, titles = sections['counts'], sections['titles']
    secs = collections.defaultdict(set)
    for i in list(ids) + list(notes):
        secs['.'.join(i.split('.')[:2])].add(i)
    for sec in counts:
        secs.setdefault(sec, set())
    chapters = []
    for n, title in CHAPTERS.items():
        keys = sorted((s for s in secs if s.split('.')[0] == str(n)), key=natkey)
        chapters.append({'n': n, 'title': title, 'sections': [
            {'key': s, 'title': titles.get(s, ''), 'count': counts.get(s),
             'ids': sorted(secs[s], key=natkey)} for s in keys]})
    meta = {
        'format': dump['format'], 'repos': meta_for(dump), 'summary': dump['summary'],
        'keys': len(ids),
        'byProject': collections.Counter(PROJECTS[r[1]] for v in ids.values() for r in v),
        'pointers': sum(r[6] for v in ids.values() for r in v),
    }
    return {'meta': meta, 'projects': PROJECTS, 'files': files, 'chapters': chapters,
            'ids': ids, 'notes': notes}


def relation(e):
    """Relation keyword and note of an upstream record (`tagged` for an existing tag)."""
    if e.get('source') != 'pointer':
        return 'tagged', e['comment']
    kw, _, rest = e['comment'].partition(':')
    kw = kw.strip()
    return (kw, rest.strip()) if kw in RELATIONS else ('partial', e['comment'])


def upstream_data(dump):
    groups = collections.defaultdict(list)
    for e in dump['entries']:
        if e['project'] not in ('Mathlib', 'TauCeti'):
            continue
        rel, note = relation(e)
        groups[(e['project'], repo_path(e))].append({
            'key': e['dlmf'], 'decl': e['decl'], 'kind': e['kind'], 'line': e['line'] or 0,
            'rel': rel, 'note': note, 'doc': e.get('docUrl') or '',
            'module': e.get('module') or ''})
    files = []
    for (proj, path), rows in sorted(groups.items(), key=lambda kv: (PROJECTS.index(kv[0][0]), kv[0][1])):
        rows.sort(key=lambda r: (r['line'], natkey(r['key'])))
        files.append({'project': proj, 'path': path, 'rows': rows})
    rels = collections.Counter(r['rel'] for f in files for r in f['rows'])
    return {'meta': {'repos': meta_for(dump), 'relations': rels,
                     'keys': len({r['key'] for f in files for r in f['rows']})},
            'relations': ['tagged'] + RELATIONS, 'files': files}


def render(template, data, out):
    tpl = open(os.path.join(ROOT, 'templates', template)).read()
    blob = json.dumps(data, separators=(',', ':'), ensure_ascii=False).replace('</', '<\\/')
    path = os.path.join(ROOT, 'docs', out)
    open(path, 'w').write(tpl.replace('/*DATA*/null', blob))
    print(f'docs/{out}: {os.path.getsize(path):,} bytes')


def main():
    dump = json.load(open(os.path.join(ROOT, 'data', 'dlmf-tags.json')))
    sections = json.load(open(os.path.join(ROOT, 'data', 'sections.json')))
    idx = index_data(dump, sections)
    render('index.html', idx, 'index.html')
    up = upstream_data(dump)
    render('mathlib.html', up, 'mathlib.html')
    print(f'{idx["meta"]["keys"]} keys, {sum(len(v) for v in idx["ids"].values())} records; '
          f'upstream: {sum(len(f["rows"]) for f in up["files"])} records in {len(up["files"])} files')


if __name__ == '__main__':
    main()
