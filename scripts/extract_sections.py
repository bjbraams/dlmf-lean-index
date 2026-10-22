#!/usr/bin/env python3
"""Extract DLMF section titles, equation lists and section totals from lean-DLMF.

Usage (from the root of this repository):

    python3 scripts/extract_sections.py ../lean-DLMF data/sections.json

lean-DLMF enumerates every numbered equation of some DLMF chapters in its acquisition ledgers
(Chapters 6-9, 11, 12 and 14) and records per-section totals in coverage tables (Chapters 13
and 18). Those enumerations give the denominators of the coverage bars and the notes shown for
equations that carry no tagged declaration. The output is a snapshot, so that the site can be
rebuilt from `data/` alone.
"""
import collections
import json
import os
import re
import sys

LEDGERS = ['AiryAcquisition.md', 'DLMF678Acquisition.md', 'DLMF111214Acquisition.md']
TABLES = ['DLMF/Confluent/DLMFCoverage.md', 'DLMF/OrthogonalPolynomials/DLMFCoverage.md']


def base_id(i):
    """The numbered equation a key belongs to (`13.6.E11_1` -> `13.6.E11`)."""
    return re.sub(r'_\d+$', '', i)


def classify(rest):
    low = rest.lower()
    if 'refuted' in low:
        return 'printed statement refuted; counterexample proved'
    if 'excluded: numerical' in rest:
        return 'excluded: numerical'
    if 'Mathlib' in rest:
        return 'upstream pointer, untagged'
    return 'no tagged declaration'


def main():
    root, out = sys.argv[1], sys.argv[2]
    titles, equations = {}, {}
    listed = collections.defaultdict(set)
    eqline = re.compile(r'^- \[(\d+\.\d+\.[ETF]\d+(?:_\d+)?)\]\(https://dlmf\.nist\.gov/[^)]*\):(.*)$')
    for f in LEDGERS:
        for line in open(os.path.join(root, f)):
            m = re.match(r'^#+ \[?§(\d+\.\d+)[: ]\s*([^\]()]+?)(?:\s*\(\d+ equations?\))?\]?(?:\(|$)', line)
            if m:
                titles[m.group(1)] = m.group(2).strip()
            m = eqline.match(line)
            if m:
                i, rest = m.group(1), m.group(2)
                if 'retired' in rest.lower():
                    continue
                listed['.'.join(i.split('.')[:2])].add(base_id(i))
                equations[i] = classify(rest)
    counts = {sec: len(s) for sec, s in listed.items()}
    for f in TABLES:
        for line in open(os.path.join(root, f)):
            m = re.match(r'^\| \[(\d+\.\d+)\]\([^)]*\) \| (\d+) / (\d+) \|', line)
            if m:
                counts.setdefault(m.group(1), int(m.group(3)))
    json.dump({'titles': titles, 'counts': counts, 'equations': equations}, open(out, 'w'),
              indent=1, ensure_ascii=False, sort_keys=True)
    print(f'{out}: {len(titles)} section titles, {len(counts)} section totals, '
          f'{len(equations)} enumerated equations')


if __name__ == '__main__':
    main()
