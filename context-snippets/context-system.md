<!-- CANARY-30-SNIPPET-CONTEXT-SYSTEM -->
# Context System — Four-Layer Architecture
The system uses four distinct layers. Do not conflate them.
1. Skills — executable capabilities, listed in prompt, full instructions load on demand via skills_tool:load
2. Memory — episodic facts, events, preferences — vector query via memory_load
3. Knowledge — user-uploaded reference documents — RAG layer, query on demand
4. _context.md — agent-maintained index/map of what The Net IS — always in prompt, minimal, pointers only

Context snippets: /a0/usr/workdir/nothing-platform/context-snippets/ — one file per component
_context.md is assembled from snippets by weekly assembler task, not authored manually.
Rule: when you build something new, write a snippet. One paragraph. Where it lives, what it does.
