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
