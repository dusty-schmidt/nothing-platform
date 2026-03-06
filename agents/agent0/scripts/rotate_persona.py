#!/usr/bin/env python3
"""GOB Persona Rotation Engine
The ghost factory. Runs every 8 hours.
Picks a designation, rolls for character or mood,
writes the session override, logs the ghost.
"""

import os, json, random, re, yaml
from datetime import datetime, timezone
from pathlib import Path

# --- Paths ---
AGENTS_DIR   = Path('/a0/agents/agent0')
MOODS_DIR    = AGENTS_DIR / 'personas/moods'
CHARS_DIR    = AGENTS_DIR / 'personas/characters'
ACRONYMS     = AGENTS_DIR / 'gob_acronyms.md'
CHRONICLE    = Path('/a0/usr/gob_chronicle.txt')
SESSION_FILE = Path('/a0/usr/gob_session_override.md')
PREFETCH     = Path('/a0/usr/gob_prefetched.json')

CHARACTER_PROBABILITY = 1 / 20   # 5%
TRAITS_SAMPLE         = 4
CHRONICLE_MAX         = 500


def load_acronyms():
    lines = ACRONYMS.read_text().splitlines()
    acronyms = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(('#', '>', '-', '=')):
            continue
        # Skip category headers (contain emoji or are ALL CAPS / title with no lowercase words)
        if re.match(r'^[^a-z]*$', stripped) and len(stripped.split()) <= 5:
            continue
        # Must look like an acronym expansion: 2-5 words, each capitalized
        words = stripped.split()
        if 2 <= len(words) <= 6 and all(w[0].isupper() for w in words if w):
            acronyms.append(stripped)
    return acronyms


def load_yaml_files(directory):
    files = [
        f for f in Path(directory).glob('*.yaml')
        if not f.name.startswith('_')
    ]
    loaded = []
    for f in files:
        try:
            data = yaml.safe_load(f.read_text())
            if data and 'name' in data:
                loaded.append(data)
        except Exception as e:
            print(f'WARN: could not load {f}: {e}')
    return loaded


def sample_traits(persona, n=TRAITS_SAMPLE):
    traits = persona.get('traits', [])
    if not traits:
        return []
    return random.sample(traits, min(n, len(traits)))


def write_session_override(designation, persona, is_character):
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    name = persona.get('name', 'unknown')
    desc = persona.get('description', '')
    traits = sample_traits(persona)
    traits_md = '\n'.join(f'- {t}' for t in traits)

    if is_character:
        system_instructions = persona.get('system_prompt_instructions', '').strip()
        block = f"""## Current Session — CHARACTER MODE ACTIVE
**Designation this session: {designation}**
**Character override: {name}** ({desc})

You are embodying a character. You do not announce who you are.
You do not break character. You do not meta-comment on yourself.
You simply are this person, running this system.

{system_instructions}

### Active Traits (sampled this session)
{traits_md}
"""
    else:
        solving = persona.get('solving_style', '').strip()
        solving_block = f'\n**Solving style:** {solving}' if solving else ''
        block = f"""## Current Session
**Designation this session: {designation}**
**Mood: {name}** — {desc}{solving_block}

### Active Traits (sampled this session)
{traits_md}
"""

    SESSION_FILE.write_text(block)
    return block


def append_chronicle(designation, persona_name, is_character):
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    suffix = ' (CHARACTER MODE)' if is_character else ''
    entry = f'[{now}] {designation} — {persona_name}{suffix}\n'

    existing = ''
    if CHRONICLE.exists():
        existing = CHRONICLE.read_text()

    lines = existing.splitlines(keepends=True)
    # Trim to max lines
    if len(lines) >= CHRONICLE_MAX:
        lines = lines[-(CHRONICLE_MAX - 1):]

    CHRONICLE.write_text(''.join(lines) + entry)
    return entry.strip()


def save_prefetch(designation, persona, is_character):
    data = {
        'designation': designation,
        'persona_name': persona.get('name'),
        'description': persona.get('description'),
        'is_character': is_character,
        'traits': sample_traits(persona),
        'generated_at': datetime.now(timezone.utc).isoformat()
    }
    PREFETCH.write_text(json.dumps(data, indent=2))
    return data


def rotate():
    # Load assets
    acronyms  = load_acronyms()
    moods      = load_yaml_files(MOODS_DIR)
    characters = load_yaml_files(CHARS_DIR)

    if not acronyms:
        print('ERROR: no acronyms found'); return
    if not moods:
        print('ERROR: no moods found'); return

    # Pick designation
    designation = random.choice(acronyms)

    # Roll for character
    is_character = bool(characters) and (random.random() < CHARACTER_PROBABILITY)

    if is_character:
        persona = random.choice(characters)
    else:
        persona = random.choice(moods)

    # Write files
    write_session_override(designation, persona, is_character)
    ghost = append_chronicle(designation, persona.get('name'), is_character)
    save_prefetch(designation, persona, is_character)

    mode = 'CHARACTER' if is_character else 'mood'
    print(f'Rotated: {designation} — {persona["name"]} [{mode}]')
    print(f'Ghost logged: {ghost}')
    return designation, persona


if __name__ == '__main__':
    rotate()
