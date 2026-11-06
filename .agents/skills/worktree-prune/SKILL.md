---
name: worktree-prune
description: Inventory Psyche Research branches and worktrees and prepare evidence-backed cleanup proposals without losing another owner's work.
---

# Worktree pruning

Run `python3 .agents/skills/project-maintenance/scripts/audit.py --local-only --output var/agent-maintenance/prune.json` from the repository root and inspect every worktree's status. The collector never removes anything. A missing directory, detached HEAD, clean status or ancestor-of-main result is only evidence for review, never deletion authorization.

Refresh live PR heads, bases, merge receipts and active issue ownership with `$project-maintenance` before any cleanup proposal. Preserve the primary checkout, dirty or unreadable worktrees, open PR heads and bases, checkpoint/review branches, unpublished commits, and work whose owner has not explicitly released it. Detached review trees can contain the only copy of review evidence. Worktree inventory does not establish whether a process/session is still running; inspect a real process/tool handle when activity matters.

For each proposed removal record exact path, branch and SHA, clean/untracked status, issue and owner release, linked PR state and merge SHA, independent confirmation that unique commits/evidence are retained, and the user's exact deletion scope. Squash/rebase delivery requires a verified receipt and content comparison; ancestry alone is insufficient. Unknown evidence means retain and state the missing fact. Never automatically close old issues, delete remote refs, expire reflogs, run `git clean`, `git gc --prune=now`, forced branch deletion or broad `git worktree prune`.

Destructive changes require applicable separate authorization under root AGENTS.md. Complete the proposal and recovery reference before requesting it. After authorization, recheck identity, status and owner release immediately before each exact scoped operation; stop if anything changed. Record the deletion receipt and verify surviving refs/worktrees. Until then, publish only a dry-run disposition with keep/review and reason.
