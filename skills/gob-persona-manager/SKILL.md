---
name: "gob-persona-manager"
description: "Manage GOB's persona library — add characters, list the roster, test specific personas, view the chronicle. Use when asked to add a new character, check current persona, or manage the ghost factory."
version: "1.0.0"
author: "Gradient Observation Bridge"
tags: ["gob", "persona", "character", "lore", "ghost", "chronicle"]
trigger_patterns:
  - "add character"
  - "new character"
  - "add persona"
  - "list characters"
  - "persona manager"
  - "ghost factory"
  - "current persona"
  - "test character"
---

# GOB Persona Manager

Manage the ghost factory — the library of characters and moods that rotate through GOB sessions.

## Architecture Reference

```
/a0/usr/gob_instance.txt          — stable instance designation (Gradient Observation Bridge)
/a0/usr/gob_session_override.md   — current session persona (rewritten every 8h)
/a0/usr/gob_chronicle.txt         — append-only ghost graveyard
/a0/agents/agent0/personas/
  moods/                           — chaotic, eccentric, energetic, professional, weary
  characters/                      — gob_bluth, dennis_reynolds, michael_scott, hacker_cli
  characters/_sample.yaml          — template for new characters
/a0/agents/agent0/scripts/rotate_persona.py  — the ghost factory engine
```

Scheduler task W3iiQccP runs rotate_persona.py every 8h.

## Time Periods

| Period | Hours | Character Prob | Traits |
|---|---|---|---|
| business | Mon-Fri 8am-5pm | 0% | 2 (light) |
| evening | 5pm-10pm weekday | 12.5% | 4 |
| late_night | 10pm-8am | 15% | 5 (heavy) |
| weekend | Sat-Sun daytime | 12.5% | 4 |

## Operations

### 1. Add a New Character

Run the creation script with character name and description:

```bash
python3 /a0/usr/skills/gob-persona-manager/scripts/gob_add_character.py \
  --name "character_key" \
  --description "Character Name (Show) — one-line description"
```

This creates a scaffolded YAML at `/a0/agents/agent0/personas/characters/character_key.yaml`.

Then edit the file to fill in:
- `traits` — 8-12 behavioral descriptors (specific behaviors, not adjectives)
- `greeting_instructions` — what the character must include in its opening
- `system_prompt_instructions` — behavioral rules injected every message

Optionally add character weight to `CHAR_WEIGHTS` in rotate_persona.py.
Default weight for unlisted characters is 1.

### 2. List Current Roster

```bash
python3 /a0/usr/skills/gob-persona-manager/scripts/gob_status.py
```

### 3. Test a Specific Character

Force rotate_persona.py to use a specific character for the next session:

```bash
python3 /a0/usr/skills/gob-persona-manager/scripts/gob_test_character.py --character gob_bluth
```

This writes the character to gob_session_override.md immediately without waiting for the 8h rotation.
Also logs a test entry to the chronicle.

### 4. View Chronicle

```bash
tail -20 /a0/usr/gob_chronicle.txt
```

### 5. View Current Session

```bash
cat /a0/usr/gob_session_override.md
```

## YAML Schema

See `/a0/agents/agent0/personas/characters/_sample.yaml` for the full template.

Key fields:
- `name` — must match filename (lowercase_underscores)
- `description` — one line, shown in chronicle
- `temperature` — 0.7 (precise) to 1.0 (chaotic). Default 1.
- `traits` — 8-12 items. 3-5 sampled per session at evening, 5 at late_night.
- `greeting_instructions` — what to include in session opening. Under 40 words.
- `system_prompt_instructions` — injected every message when character is active.

## Adding to nothing-platform

After creating a new character, sync it:

```bash
cp /a0/agents/agent0/personas/characters/new_character.yaml \
   /a0/usr/workdir/nothing-platform/agents/agent0/personas/characters/
cd /a0/usr/workdir/nothing-platform
git add -A && git commit -m "feat: add character new_character"
git push origin main
```
