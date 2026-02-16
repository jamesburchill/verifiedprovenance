#!/usr/bin/env bash
set -euo pipefail

echo "Running public boundary checks..."

# 1) Secret pattern scan (simple denylist for obvious leaks)
if rg -n --hidden --glob '!.git' --glob '!scripts/check-public-boundary.sh' \
  -e 'BEGIN [A-Z ]*PRIVATE KEY' \
  -e 'AKIA[0-9A-Z]{16}' \
  -e 'AIza[0-9A-Za-z\-_]{35}' \
  -e 'xox[baprs]-' \
  -e 'SECRET_ACCESS_KEY' \
  -e 'webhook_secret' \
  .; then
  echo "Failed: possible secret material found."
  exit 1
fi

# 2) Internal-only private surface references should not leak here.
if rg -n --hidden --glob '!.git' --glob '!scripts/check-public-boundary.sh' \
  -e 'verifiedprovenance-core' \
  -e 'internal-only' \
  -e 'non-public domain' \
  .; then
  echo "Failed: internal/private boundary markers found in public repo."
  exit 1
fi

echo "Public boundary checks passed."
