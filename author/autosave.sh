#!/usr/bin/env bash
set -euo pipefail
echo "Autosave running. Ctrl+C to stop."
while true; do
  if ! git diff --quiet; then
    git add -A
    git commit -m "autosave $(date -u +%FT%TZ)"
    echo "Committed at $(date -u +%T)"
  fi
  sleep 60
done
