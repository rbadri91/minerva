#!/usr/bin/env bash
# Branch guard hook: enforces feature-branch discipline.
# Called by Claude Code as a PreToolUse hook on Write|Edit.
#
# Rules:
#   1. If on master                          → block (never edit files on master)
#   2. If branch has 0 commits ahead of origin/master AND has a remote tracking
#      branch (i.e. was pushed and merged)   → auto-create a new feature branch
#   3. Otherwise (fresh branch or WIP)       → allow

# Drain stdin (hook sends tool input JSON on stdin; we don't need it here)
cat > /dev/null

BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)

# ── Rule 1: never edit on master ──────────────────────────────────────────────
if [ "$BRANCH" = "master" ]; then
    printf '%s\n' '{"continue": false, "stopReason": "Branch guard: you are on master. Create a feature branch before editing files."}'
    exit 0
fi

# ── Rule 2: detect a merged/up-to-date pushed branch — block and ask for a name ─
AHEAD=$(git log origin/master..HEAD --oneline 2>/dev/null | wc -l | tr -d ' ')
TRACKING=$(git rev-parse --abbrev-ref --symbolic-full-name @{upstream} 2>/dev/null)
# Strip "origin/" prefix to get the remote branch name
REMOTE_BRANCH="${TRACKING#origin/}"

# Only trigger if the local name matches the remote name — a renamed local branch
# (local=feature/new-name, remote=origin/feature/old-name) should pass through as Rule 3.
if [ "$AHEAD" -eq 0 ] && [ -n "$TRACKING" ] && [ "$BRANCH" = "$REMOTE_BRANCH" ]; then
    printf '%s\n' '{"continue": false, "stopReason": "Branch guard: branch '"'"''"$BRANCH"''"'"' is fully merged into master. Run: git checkout -b feature/<description-of-your-change> — then retry."}'
    exit 0
fi

# ── Rule 3: WIP or fresh local branch — allow ─────────────────────────────────
exit 0
