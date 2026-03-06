# GOB Workflow

## Who works on this codebase

- **GOB** — primary AI developer, runs inside the system, works autonomously
- **Roo Code / VS Code** — occasional human-directed sessions from outside
- **Human (Dusty)** — reviews, directs, makes architectural decisions

All three follow the same workflow. No exceptions for "quick fixes".

## Branch structure

```
main      ← stable tagged releases ONLY. NEVER commit here directly.
develop   ← integration branch, default base for all work
feature/* ← new capabilities, branched from develop
fix/*     ← bug fixes, branched from develop
```

## Daily loop

```bash
git checkout develop
git checkout -b feature/my-thing
# work
git add -p   # interactive staging preferred
git commit -m 'feat: description'
# PR to develop → review → merge
```

## Commit conventions

```
feat:  new capability
fix:   bug fix
chore: maintenance, dependencies
docs:  documentation only
id:    identity/persona changes
arch:  architectural changes
```

## GOB manages this repo autonomously

GOB creates branches, opens PRs, writes devlogs, and merges when instructed.
Human reviews and approves. Human does not push directly to main.

## Devlogs

Significant sessions get a devlog in `devlogs/YYYY-MM-DD_description.md`.
Format: what changed, why, what broke, what survived.

## Context Management

_context.md is an **assembled** document, not an authored one. Do not edit it directly.

### The rule
When you build something new — a subsystem, persona, scheduled task, capability — write a snippet:
```
/a0/usr/workdir/nothing-platform/context-snippets/thing-name.md
```
One paragraph. Three questions answered:
1. What is it?
2. What does it do / why does it matter?
3. Where does full detail live? (path or pointer)

The weekly assembler task reads all snippets + recent newsletter editions and promotes changes to _context.md automatically.

### Manual update procedure (if needed between assembler runs)
```bash
cp /a0/usr/workdir/nothing-platform/agents/agent0/_context.md /a0/agents/agent0/_context.md
cd /a0/usr/workdir/nothing-platform
git add agents/agent0/_context.md context-snippets/
git commit -m 'id: update context index'
git push
```

### What belongs in _context.md vs. elsewhere
| Content | Where it lives |
|---|---|
| What a subsystem IS (2-3 lines) | _context.md via snippet |
| How a subsystem WORKS (full detail) | snippet file or the subsystem's own README |
| Session events, breakthroughs | chronicle/ or devlogs/ |
| Episodic facts, preferences | memory (memory_save tool) |
| Reference documents | knowledge base (user upload) |
| Executable capabilities | skills/ |
