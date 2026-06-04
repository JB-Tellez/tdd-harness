#!/usr/bin/env bash
# One-shot setup for a copied spec-tdd project.
#
# Creates the venv, installs dependencies (core + the spec MCP), and runs the
# MCP selftest so you can confirm the harness sees your feature files before
# starting. Safe to re-run -- it reuses an existing venv.
#
# Usage:  ./setup.sh        (from inside the copied project folder)
set -euo pipefail

# Always operate from the project root (this script's own dir), so it works no
# matter where it's invoked from.
cd "$(dirname "$0")"

PY=python3
VENV=.venv

echo "==> Setting up spec-tdd project in: $(pwd)"

# 1. venv (reuse if present)
if [ ! -d "$VENV" ]; then
  echo "==> Creating virtualenv ($VENV)"
  "$PY" -m venv "$VENV"
else
  echo "==> Reusing existing virtualenv ($VENV)"
fi

VPY="$VENV/bin/python"

# 2. dependencies
echo "==> Installing core requirements"
"$VPY" -m pip install --quiet --upgrade pip
"$VPY" -m pip install --quiet -r requirements.txt

if [ -f spec-mcp/requirements.txt ]; then
  echo "==> Installing spec MCP requirements"
  "$VPY" -m pip install --quiet -r spec-mcp/requirements.txt
fi

# 3. selftest: confirm the harness parses your feature files
echo "==> Spec MCP selftest (scenarios it can see right now):"
"$VPY" spec-mcp/spec_server.py --selftest || {
  echo "    (selftest failed -- check that features/*.feature exist)"
}

cat <<'NEXT'

==> Done.

Next:
  1. Replace features/example.feature with your own .feature files
     (re-run ./setup.sh afterward to confirm they're picked up).
  2. Open Claude Code WITH THIS FOLDER AS THE PROJECT ROOT
     - terminal:  claude        (from this directory)
     - VS Code:   open this folder as the workspace, then start Claude Code
  3. Run:  /auto-tdd

The hooks enforce RED-before-GREEN (see .claude/spec-tdd.json). Review
DEV_LOG.md and the generated code when the run finishes.
NEXT
