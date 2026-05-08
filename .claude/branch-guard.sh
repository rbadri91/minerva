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

# ── Rule 2: detect a merged branch and spin up a new one ──────────────────────
AHEAD=$(git log origin/master..HEAD --oneline 2>/dev/null | wc -l | tr -d ' ')
TRACKING=$(git rev-parse --abbrev-ref --symbolic-full-name @{upstream} 2>/dev/null)

if [ "$AHEAD" -eq 0 ] && [ -n "$TRACKING" ]; then
    NEW_BRANCH="feature/work-$(date +%Y%m%d-%H%M%S)"
    git checkout -b "$NEW_BRANCH" 2>/dev/null
    printf '{"systemMessage": "Branch guard: auto-created branch %s (branch %s appears to be fully merged into master)."}\n' "$NEW_BRANCH" "$BRANCH"
    exit 0
fi

# ── Rule 3: WIP or fresh local branch — allow ─────────────────────────────────
exit 0
