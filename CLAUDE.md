# Minerva — Claude Code Instructions

## Branch naming

When creating a new git branch, name it to describe the work being done — not a generic timestamp or placeholder.

**Format:** `feature/<short-description>` or `fix/<short-description>`

Good: `feature/streamlit-status-panel`, `fix/chroma-embedding-dimension`, `feature/synthesis-streaming`

Bad: `feature/work-20260510-123456`, `feature/new-branch`, `feature/changes`

The branch-guard hook will **block** any Write/Edit if you are on a merged branch with no active feature branch. When that happens, create a descriptively-named branch first, then retry:

```bash
git checkout -b feature/<description-of-work>
```
    