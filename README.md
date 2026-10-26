# DLMF ↔ Lean formalization index

A static website that maps equations of the NIST
[Digital Library of Mathematical Functions](https://dlmf.nist.gov/) (DLMF) to Lean 4
declarations in [Mathlib](https://github.com/leanprover-community/mathlib4),
[TauCeti](https://github.com/TauCetiProject/TauCeti) and
[lean-DLMF](https://github.com/bjbraams/lean-DLMF) (other sources to follow),
and that lists Mathlib declarations which are candidates for Mathlib's `@[dlmf]`
cross-reference attribute.
It is unofficial and not affiliated with NIST.

Pages (published from `docs/` by GitHub Pages):

- `index.html`: the index by DLMF chapter and section, with proof status from a compiled axiom
  audit.
- `mathlib.html`: Mathlib and TauCeti declarations matched to DLMF equations, grouped by source
  file, with the relation between the two statements (exact, stronger, special case, partial,
  different convention) and a suggested `@[dlmf ...]` attribute line.

## Layout

- `data/dlmf-tags.json`: the dump of `@[dlmf]` tags and checked `dlmf_upstream` pointers, written
  by `scripts/DumpDLMF.lean` in lean-DLMF from the compiled environment (Mathlib, the imported
  TauCeti modules and lean-DLMF).
- `data/sections.json`: DLMF section titles, section totals of numbered equations, and the
  equations enumerated by lean-DLMF's acquisition ledgers (Chapters 6–9 and 11–14; section totals
  for 13 and 18).
- `templates/`: the page templates; `scripts/build.py` substitutes the data for `/*DATA*/null`.
- `docs/`: the generated site and its stylesheet `docs/assets/site.css`. `docs/.nojekyll` makes
  GitHub Pages serve the files as they are.
- `scripts/extract_sections.py`, `scripts/build.py`, `scripts/update.sh`: see below.

## Editing and rebuilding

Edit the templates or the stylesheet, then rebuild the pages from the data snapshot:

    python3 scripts/build.py

Open `docs/index.html` in a browser to check the result. The generated pages are committed, so
GitHub Pages needs no build step.

To refresh the data from a built lean-DLMF checkout next to this repository (`../lean-DLMF`):

    scripts/update.sh

This runs `DumpDLMF.lean` (lean-DLMF must have been built with `lake build`), re-extracts
`data/sections.json` and rebuilds the pages. Commit and push lean-DLMF first, so that the source
links of its declarations resolve on GitHub; the dump records the commit it was taken from and
whether the working tree had uncommitted changes.

## Publishing with GitHub Pages

1. Create an empty public repository `dlmf-lean-index` on GitHub (no README or license, so that
   the first push is clean).
2. Push this repository:

       git remote add origin https://github.com/bjbraams/dlmf-lean-index.git
       git push -u origin main

3. On GitHub, open Settings → Pages, choose "Deploy from a branch", branch `main`, folder
   `/docs`, and save. After a minute or two the site is at
   <https://bjbraams.github.io/dlmf-lean-index/>.

Later updates: rebuild, commit, push; Pages redeploys automatically.

## Data model

A record is a pair (DLMF key, Lean declaration). The key is the DLMF permalink id as parsed by
Mathlib's `@[dlmf]` attribute (`Mathlib/Tactic/CrossRefAttribute.lean`), for example `5.4.E1`
or `13.6.E11_1`. Status is taken from the compiled axiom audit: proved, proved from admitted
lemmas, statement only (depends on `sorryAx`), or definition. Untagged upstream declarations
enter through lean-DLMF's `dlmf_upstream` command, which fails to build if the declaration
disappears and records the relation to DLMF's statement. The design is described in
`DLMFIndex.md` in lean-DLMF.
