#!/bin/bash
# Claude Code status line — shows PII routing status from the proxy
LOG="$(dirname "$0")/pii-events.jsonl"

if [ ! -f "$LOG" ]; then
  echo "PII Proxy: No events yet"
  exit 0
fi

latest=$(tail -1 "$LOG" 2>/dev/null)
if [ -z "$latest" ]; then
  echo "PII Proxy: No events yet"
  exit 0
fi

pii=$(echo "$latest" | python3 -c "import sys,json; print(json.load(sys.stdin).get('pii_detected',False))" 2>/dev/null)

if [ "$pii" = "True" ]; then
  model=$(echo "$latest" | python3 -c "import sys,json; print(json.load(sys.stdin).get('routed_model','?'))" 2>/dev/null)
  entities=$(echo "$latest" | python3 -c "import sys,json; print(json.load(sys.stdin).get('entities',''))" 2>/dev/null)
  echo "PII DETECTED — routed to $model ($entities)"
else
  model=$(echo "$latest" | python3 -c "import sys,json; print(json.load(sys.stdin).get('routed_model','?'))" 2>/dev/null)
  echo "Clean — $model"
fi
