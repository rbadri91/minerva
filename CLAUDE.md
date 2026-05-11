# Minerva — Claude Code Instructions

## Branch naming

When creating a new git branch, name it to describe the work being done — not a generic timestamp or placeholder.

**Format:** `feature/<short-description>` or `fix/<short-description>`

Good: `feature/streamlit-status-panel`, `fix/chroma-embedding-dimension`, `feature/synthesis-streaming`

Bad: `feature/work-20260510-123456`, `feature/new-branch`, `feature/changes`

The branch-guard hook may auto-create a `feature/work-YYYYMMDD-HHMMSS` branch as a safety net when you are on a merged branch with no active feature branch. If that happens, immediately rename it to something descriptive before making any commits:

```bash
git branch -m feature/work-YYYYMMDD-HHMMSS feature/<description-of-work>
```
