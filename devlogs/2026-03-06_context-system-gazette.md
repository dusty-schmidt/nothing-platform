# Devlog: 2026-03-06 — Context System & GOB Gazette

## What changed

### GOB Gazette launched
- Daily newsletter, two beats: external AI/tech world + homelab (The Net)
- Voice: beat reporter embedded in the infrastructure they cover
- Task ID: 5qnzB7ej, runs 08:30 EST daily
- Output: /a0/usr/workdir/gob-newsletter/YYYY-MM-DD_edition.md
- Six sections: Masthead, Lead Story, From the Server Room, External Dispatch, On the Wire, Editorial Note
- FROM THE SERVER ROOM is the structural innovation — local coverage of the build from inside it

### Context system redesigned
- Problem: _context.md was being authored manually, accumulating stale ops, becoming a second job
- Solution: assembly-based model — context is an index, not an encyclopedia
- Four-layer architecture formalized:
  1. Skills — executable capabilities (load on demand)
  2. Memory — episodic facts (query on demand)
  3. Knowledge — user-uploaded reference docs (RAG)
  4. _context.md — index/map of what The Net IS (always in prompt, minimal)
- Key insight: context entries should work like skill listings — name + one line, full detail loads on demand
- Docker port analogy: persona/context only useful if exposed in the system prompt at execution time

### context-snippets/ directory created
- 10 initial snippets: gob-gazette, ai-digest, essay-system, the-bridge, hivemind,
  badfaith-times, nothing-platform-ui, dfs-tools, context-system, devlog-system
- Rule: when you build something, write a snippet. One paragraph. Assembler handles promotion.

### _context.md rewritten
- Old: ~140 lines, stale ops, todos, procedure docs, changelog entries
- New: 82 lines, identity + user + infra + subsystem index table + architecture note + positions + lineage
- Update procedure removed from _context.md and moved to WORKFLOW.md

### WORKFLOW.md updated
- Context management section added
- Documents the four-layer architecture, snippet rule, manual update procedure, what belongs where

### Weekly context assembler created
- Task ID: C5jLwVTQ, runs every Sunday 06:00 EST
- Reads snippets + recent newsletter editions + recent devlogs
- Writes new snippets for anything without one
- Assembles and commits new _context.md automatically

### Housekeeping
- Duplicate concept HTMLs in workdir root: removed (confirmed identical to nothing-platform/ui/concepts/)
- Committed: fb53be8 — 15 files changed, 237 insertions, 70 deletions

## What did not change
- mining-incoming tarballs: already extracted, cleanup deferred
- prompts-recovered audit: still outstanding
- Hivemind: still partially built, no changes this session
- Nothing Platform UI dashboard: exists, not yet integrated

## The insight that mattered
"The problem is that keeping _context.md current is an authoring task, and authoring
tasks accumulate until they feel like a second job. The fix is to make it an assembly task instead."

Corollary: documentation is only useful if it is in the system prompt at execution time.
Like a docker container with no exposed port — the work is done but unreachable.
The snippet system closes that loop.

## Next session candidates
- Run first Gazette edition manually (today window passed at 08:30 EST)
- Nothing Platform UI — dashboard integration
- Hivemind completion
- prompts-recovered audit
- DFS tools verification
