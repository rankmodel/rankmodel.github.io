#!/usr/bin/env bash
# agency/marathon.sh — ModelRank 4-Hour Launch Marathon (autonomous runner)
# Keeps the launch loops alive for 4 hours: runs the Agency safe heartbeats,
# polls NotebookLM artifacts and downloads finished ones, and logs a scoreboard.
set -u
cd "$(dirname "$0")/.."

LOG=outputs/marathon.log
OUT=outputs/notebooklm_marathon
mkdir -p "$OUT"

AUDIO=5762d6a0-f22f-4c7a-b4c9-450f667fb0c3
REPORT=f7495ef9-d42a-4d16-9837-3eb248f222b5
SLIDE=47349904-ec88-41c0-9d44-fe6c886f7d97
MIND=cd609a9e

START=$(date +%s)
END=$((START + 4*3600))
tick=0

echo "MARATHON START $(date -u)  (ends $(date -u -r $END 2>/dev/null))" | tee -a "$LOG"

while [ "$(date +%s)" -lt "$END" ]; do
  ts=$(date -u +%H:%M:%S)
  echo "========================================" >> "$LOG"
  echo "[$ts] tick#$tick" >> "$LOG"

  # --- Agency safe heartbeats (no network, no spend) ---
  ./venv/bin/python agency/agency.py --run --routine hourly_badge_sync >> "$LOG" 2>&1
  ./venv/bin/python agency/agency.py --run --agent cmo >> "$LOG" 2>&1
  ./venv/bin/python agency/agency.py --run --agent analyst >> "$LOG" 2>&1
  ./venv/bin/python agency/agency.py --run --agent ceo >> "$LOG" 2>&1

  # --- Poll + download NotebookLM marathon artifacts (idempotent) ---
  timeout 90 ./venv/bin/notebooklm download audio -a "$AUDIO" "$OUT/marathon_audio.m4a" --no-clobber >> "$LOG" 2>&1 || true
  timeout 90 ./venv/bin/notebooklm download report -a "$REPORT" "$OUT/marathon_report.md" --no-clobber >> "$LOG" 2>&1 || true
  timeout 90 ./venv/bin/notebooklm download slide-deck -a "$SLIDE" "$OUT/marathon_slides.pdf" --no-clobber >> "$LOG" 2>&1 || true
  timeout 90 ./venv/bin/notebooklm download mind-map -a "$MIND" "$OUT/marathon_mindmap.json" --no-clobber >> "$LOG" 2>&1 || true

  # --- Scoreboard ---
  badges=$(find static_output/badges -name '*.svg' 2>/dev/null | wc -l | tr -d ' ')
  drafts=$(find outputs/agency_drafts -name '*.md' 2>/dev/null | wc -l | tr -d ' ')
  echo "[$ts] scoreboard: badge_assets=$badges drafts=$drafts" >> "$LOG"

  tick=$((tick+1))
  sleep 300
done

echo "MARATHON END $(date -u)" >> "$LOG"
