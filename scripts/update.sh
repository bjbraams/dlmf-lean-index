#!/usr/bin/env bash
# Refresh the data snapshot from a built lean-DLMF checkout and rebuild the site.
#
#   scripts/update.sh [path-to-lean-DLMF]     (default: ../lean-DLMF)
#
# lean-DLMF must be built (`lake build`) first: the dump reads the compiled environment.
# Commit and push lean-DLMF before refreshing, so that its source links resolve on GitHub.
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"
proj="$(cd "${1:-$here/../lean-DLMF}" && pwd)"
(cd "$proj" && DLMF_DUMP_OUT="$here/data/dlmf-tags.json" lake env lean scripts/DumpDLMF.lean)
python3 "$here/scripts/extract_sections.py" "$proj" "$here/data/sections.json"
python3 "$here/scripts/build.py"
