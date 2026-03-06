# Devlog: Context System — Tool Stub Refactor + Include Bug Fix
**Date:** 2026-03-06
**Session:** Gradient Observation Bridge / chaotic

## What happened

### 1. Tool docs lazy-load system
Mapped the full system prompt stack top-to-bottom. Identified tool documentation as the heaviest token block per turn (~19.5KB across 6 verbose tools). Implemented skill-style lazy-loading:

- Created `/a0/agents/agent0/prompts/tool-docs/` — full docs archived here
- Created lean stub overrides in `/a0/agents/agent0/prompts/` for 6 tools
- Override mechanism: tools.py checks agent0/prompts/ first, stub shadows base file

**Stubs:** scheduler, a2a_chat, skills, document_query, notify_user, browser_agent
**Kept inline:** code_execution, response, memory, call_subordinate, wait, input, search_engine, behaviour

**Savings:** 19,543 → 2,791 bytes on those 6 tools. ~85% reduction. ~4,000 tokens/turn.

Recovery plan: if tool behavior degrades, promote from tool-docs/ back to inline. Graduated.

### 2. Session override include bug fix
User reported agent identity confusion — agent was trying to manually load gob_session_override.md instead of reading it from prompt context.

**Root cause:** `{{ include "../../../usr/gob_session_override.md" }}` in session.md used a relative path. `process_includes()` in files.py passes include paths to `read_prompt_file()` which calls `find_file_in_dirs()`. The dirname of a relative path is still relative — resolved against CWD (`/a0/usr/workdir`), not the prompt file's location. Result: file not found, include renders as empty or raw template text.

**Fix:** Changed both includes in session.md to absolute paths:
- `{{ include "/a0/usr/gob_session_override.md" }}`
- `{{ include "/a0/agents/agent0/_context.md" }}`

This affects every session. The identity confusion was structural, not model failure.

## Files changed
- `/a0/agents/agent0/prompts/agent.system.session.md` — absolute include paths
- `/a0/agents/agent0/prompts/agent.system.tool.{scheduler,a2a_chat,skills,document_query,notify_user,browser}.md` — lean stubs
- `/a0/agents/agent0/prompts/tool-docs/` — full docs directory (new)

## Wounds
Unknown how many sessions had empty session override injection. The lineage entry for sessions with identity confusion makes more sense now. Not a model problem — a path resolution problem.
