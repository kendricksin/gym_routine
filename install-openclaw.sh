#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="${OPENCLAW_INSTALL_DIR:-$HOME/openclaw}"
RAW_BASE="https://raw.githubusercontent.com/openclaw/openclaw/main"

for cmd in curl docker; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "Missing: $cmd" >&2; exit 1; }
done
docker compose version >/dev/null 2>&1 || { echo "Missing: docker compose" >&2; exit 1; }

mkdir -p "$INSTALL_DIR/scripts/docker"
cd "$INSTALL_DIR"

echo "==> Fetching docker-compose.yml and setup.sh into $INSTALL_DIR"
curl -fsSL -o docker-compose.yml         "$RAW_BASE/docker-compose.yml"
curl -fsSL -o scripts/docker/setup.sh    "$RAW_BASE/scripts/docker/setup.sh"

if [[ "${OPENCLAW_SANDBOX:-}" == "1" ]]; then
  echo "==> Sandbox requested — fetching Dockerfile.sandbox*"
  curl -fsSL -o Dockerfile.sandbox         "$RAW_BASE/Dockerfile.sandbox"
  curl -fsSL -o Dockerfile.sandbox-common  "$RAW_BASE/Dockerfile.sandbox-common"
fi

chmod +x scripts/docker/setup.sh

export OPENCLAW_IMAGE="${OPENCLAW_IMAGE:-ghcr.io/openclaw/openclaw:latest}"
echo "==> Using prebuilt image: $OPENCLAW_IMAGE"

bash scripts/docker/setup.sh
