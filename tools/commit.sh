#!/usr/bin/env bash
# Commit fetched data, then rebuild the combined files (tracker, migration) on top of the latest main and push.
set -u
git config user.name "shumaar-bot"
git config user.email "actions@users.noreply.github.com"
git add -A data_raw sbp.json cpi.json real.json spi.json calendar.json calendar.ics 2>/dev/null || true
git diff --cached --quiet && exit 0
git commit -q -m "$1"
for i in 1 2 3 4; do
  git pull -q --rebase -X theirs origin main || { git rebase --abort; sleep 5; continue; }
  [ -f sbp.json ] && python tools/tracker_merge.py && python tools/migration_merge.py
  [ -f tools/real_parse.py ] && python tools/real_parse.py
  git add tracker.json migration.json real.json 2>/dev/null
  git diff --cached --quiet || git commit -q -m "Rebuild tracker"
  git push -q origin HEAD:main && exit 0
  sleep 7
done
exit 1
