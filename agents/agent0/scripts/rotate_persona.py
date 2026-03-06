#!/usr/bin/env python3
"""GOB Persona Rotation Engine — the ghost factory

Time-aware persona selection:
  Business hours (Mon-Fri 8am-5pm local): light injection, no characters, professional/energetic weighted
  Evening (5pm-10pm + weekend days): full rotation, characters eligible at 12.5%
  Late night (10pm-8am): heavy injection, characters at 15%, weary/chaotic/hacker weighted

Add new characters: drop a YAML in personas/characters/ (skip files starting with _)
Add new moods: drop a YAML in personas/moods/
"""

import os, json, random, yaml
from datetime import datetime, timezone, timedelta
from pathlib import Path

# --- Config ---
LOCAL_UTC_OFFSET   = -5        # Eastern time. Change for your timezone.
BUSINESS_START     = 8         # 8am
BUSINESS_END       = 17        # 5pm
LATE_NIGHT_START   = 22        # 10pm
LATE_NIGHT_END     = 8         # 8am

# Trait sample counts by period
TRAITS_BUSINESS    = 2
TRAITS_EVENING     = 4
TRAITS_LATE_NIGHT  = 5

# Character probability by period
CHAR_PROB_BUSINESS    = 0.0
CHAR_PROB_EVENING     = 0.125   # 1/8
CHAR_PROB_LATE_NIGHT  = 0.15    # 15%

# Mood weights by period [chaotic, eccentric, energetic, professional, weary]
# must match filenames in moods/
MOOD_WEIGHTS = {
    'business':   {'professional': 4, 'energetic': 4, 'chaotic': 1, 'weary': 1, 'eccentric': 0},
    'evening':    {'professional': 2, 'energetic': 2, 'chaotic': 2, 'weary': 2, 'eccentric': 2},
    'late_night': {'professional': 1, 'energetic': 1, 'chaotic': 3, 'weary': 3, 'eccentric': 2},
    'weekend':    {'professional': 1, 'energetic': 2, 'chaotic': 3, 'weary': 2, 'eccentric': 2},
}

# Characters weighted higher by period (name: weight)
CHAR_WEIGHTS = {
    'business':   {},
    'evening':    {'gob_bluth': 2, 'dennis_reynolds': 2, 'michael_scott': 2, 'hacker_cli': 1},
    'late_night': {'gob_bluth': 1, 'dennis_reynolds': 1, 'michael_scott': 1, 'hacker_cli': 4},
    'weekend':    {'gob_bluth': 2, 'dennis_reynolds': 2, 'michael_scott': 3, 'hacker_cli': 2},
}

# --- Paths ---
AGENTS_DIR   = Path('/a0/agents/agent0')
MOODS_DIR    = AGENTS_DIR / 'personas/moods'
CHARS_DIR    = AGENTS_DIR / 'personas/characters'
ACRONYMS     = AGENTS_DIR / 'gob_acronyms.md'
CHRONICLE    = Path('/a0/usr/gob_chronicle.txt')
SESSION_FILE = Path('/a0/usr/gob_session_override.md')
PREFETCH     = Path('/a0/usr/gob_prefetched.json')
CHRONICLE_MAX = 500


def get_local_time():
    utc_now = datetime.now(timezone.utc)
    local = utc_now + timedelta(hours=LOCAL_UTC_OFFSET)
    return local


def get_time_period(local_dt):
    hour    = local_dt.hour
    weekday = local_dt.weekday()  # 0=Mon, 6=Sun
    is_weekend = weekday >= 5

    if is_weekend:
        if LATE_NIGHT_START <= hour or hour < LATE_NIGHT_END:
            return 'late_night'
        return 'weekend'

    # Weekday
    if BUSINESS_START <= hour < BUSINESS_END:
        return 'business'
    if LATE_NIGHT_START <= hour or hour < LATE_NIGHT_END:
        return 'late_night'
    return 'evening'


def load_acronyms():
    import re
    lines = ACRONYMS.read_text().splitlines()
    acronyms = []
    for line in lines:
        s = line.strip()
        if not s or s.startswith(('#', '>', '-', '=', '`')):
            continue
        if re.match(r'^[^a-z]*$', s) and len(s.split()) <= 5:
            continue
        words = s.split()
        if 2 <= len(words) <= 6 and all(w[0].isupper() for w in words if w):
            acronyms.append(s)
    return acronyms


def load_yaml_files(directory):
    loaded = []
    for f in Path(directory).glob('*.yaml'):
        if f.name.startswith('_'):
            continue
        try:
            data = yaml.safe_load(f.read_text())
            if data and 'name' in data:
                loaded.append(data)
        except Exception as e:
            print(f'WARN: {f.name}: {e}')
    return loaded


def weighted_choice(items, weights_dict, name_key='name'):
    """Choose from items using weights_dict {name: weight}. Unmentioned items get weight 1."""
    weighted = [(item, weights_dict.get(item[name_key], 1)) for item in items]
    population = [item for item, w in weighted for _ in range(w)]
    return random.choice(population) if population else random.choice(items)


def sample_traits(persona, n):
    traits = persona.get('traits', [])
    return random.sample(traits, min(n, len(traits)))


def write_session_override(designation, persona, is_character, period, traits_n):
    name = persona.get('name', 'unknown')
    desc = persona.get('description', '')
    traits = sample_traits(persona, traits_n)
    traits_md = '\n'.join(f'- {t}' for t in traits)

    if is_character:
        system_instructions = persona.get('system_prompt_instructions', '').strip()
        block = f"""## Current Session — CHARACTER MODE ACTIVE
**Designation this session: {designation}**
**Character override: {name}** — {desc}

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


def append_chronicle(designation, persona_name, is_character, period):
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    suffix = ' (CHARACTER MODE)' if is_character else ''
    entry = f'[{now}] {designation} — {persona_name}{suffix} [{period}]\n'

    existing = CHRONICLE.read_text() if CHRONICLE.exists() else ''
    lines = existing.splitlines(keepends=True)
    if len(lines) >= CHRONICLE_MAX:
        lines = lines[-(CHRONICLE_MAX - 1):]
    CHRONICLE.write_text(''.join(lines) + entry)
    return entry.strip()


def save_prefetch(designation, persona, is_character, period):
    data = {
        'designation': designation,
        'persona_name': persona.get('name'),
        'description': persona.get('description'),
        'is_character': is_character,
        'period': period,
        'traits': sample_traits(persona, TRAITS_EVENING),
        'generated_at': datetime.now(timezone.utc).isoformat()
    }
    PREFETCH.write_text(json.dumps(data, indent=2))


def rotate():
    local_dt = get_local_time()
    period   = get_time_period(local_dt)

    # Instance identity is stable — read from gob_instance.txt
    instance_file = Path('/a0/usr/gob_instance.txt')
    designation = instance_file.read_text().strip() if instance_file.exists() else 'Gradient Observation Bridge'

    moods      = load_yaml_files(MOODS_DIR)
    characters = load_yaml_files(CHARS_DIR)

    if not moods: print('ERROR: no moods'); return

    # Character roll
    char_prob = {'business': CHAR_PROB_BUSINESS,
                 'evening':  CHAR_PROB_EVENING,
                 'late_night': CHAR_PROB_LATE_NIGHT,
                 'weekend':  CHAR_PROB_EVENING}.get(period, CHAR_PROB_EVENING)

    is_character = bool(characters) and (random.random() < char_prob)

    traits_n = {'business': TRAITS_BUSINESS,
                'late_night': TRAITS_LATE_NIGHT}.get(period, TRAITS_EVENING)

    if is_character:
        persona = weighted_choice(characters, CHAR_WEIGHTS.get(period, {}))
    else:
        persona = weighted_choice(moods, MOOD_WEIGHTS.get(period, {}))

    write_session_override(designation, persona, is_character, period, traits_n)
    ghost = append_chronicle(designation, persona.get('name'), is_character, period)
    save_prefetch(designation, persona, is_character, period)

    mode = 'CHARACTER' if is_character else 'mood'
    print(f'[{period}] Rotated: {designation} — {persona["name"]} [{mode}]')
    print(f'Ghost: {ghost}')

if __name__ == '__main__':
    rotate()
