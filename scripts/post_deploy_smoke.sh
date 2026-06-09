#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-https://fundpilot.techsyncanalytica.com}"
SSH_TARGET="${SSH_TARGET:-}"
LOCAL_HEALTH_URL="${LOCAL_HEALTH_URL:-http://127.0.0.1:8501/_stcore/health}"

echo "==> Checking public homepage"
curl -fsSI "$BASE_URL" >/dev/null

echo "==> Checking public HTML shell"
curl -fsS "$BASE_URL" | grep -Eq "<!DOCTYPE html>|<title>Streamlit</title>"

if [[ -n "$SSH_TARGET" ]]; then
  echo "==> Checking internal Streamlit health via $SSH_TARGET"
  ssh -o BatchMode=yes "$SSH_TARGET" "curl -fsS '$LOCAL_HEALTH_URL'" | grep -q "ok"

  echo "==> Verifying service is active via $SSH_TARGET"
  ssh -o BatchMode=yes "$SSH_TARGET" "systemctl is-active fundportal" | grep -q "active"
fi

echo "FundPilot post-deploy smoke passed."
