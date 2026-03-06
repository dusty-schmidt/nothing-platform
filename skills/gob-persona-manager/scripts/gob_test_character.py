#!/usr/bin/env python3
"""
GOB Character Tester
Forces a specific character or mood into gob_session_override.md immediately.
Does not wait for the 8h rotation. Logs a test entry to the chronicle.
Usage: python3 gob_test_character.py --character gob_bluth
       python3 gob_test_character.py --mood chaotic
"""
import argparse
import yaml
import random
from pathlib import Path
from datetime import datetime, timezone

USR = Path("/a0/usr")
AGENT = Path("/a0/agents/agent0")

def load_yaml(path):
    return yaml.safe_load(path.read_text())

def write_override(designation, persona_type, name, traits, greeting, system_instructions, is_character=False, is_test=False):
    override = USR / "gob_session_override.md"
    tag = "[TEST] " if is_test else ""
    char_block = ""
    if is_character:
        char_block = f"""\n**CHARACTER MODE ACTIVE** {tag}— rare probability event\n"""

    content = f"""## Current Session Identity
{char_block}
**Instance:** {designation}
**Session Persona:** {name} ({'character' if is_character else 'mood'})

### Active Traits
"""
    for trait in traits:
        content += f"- {trait}\n"

    if system_instructions:
        content += f"\n### Session Rules\n{system_instructions}\n"

    override.write_text(content)
    return override

def append_chronicle(entry):
    chronicle = USR / "gob_chronicle.txt"
    with open(chronicle, "a") as f:
        f.write(entry + "\n")

def main():
    parser = argparse.ArgumentParser(description="Force a GOB persona for testing")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--character", help="Character key (e.g. gob_bluth)")
    group.add_argument("--mood", help="Mood key (e.g. chaotic)")
    args = parser.parse_args()

    # Load instance designation
    inst_file = USR / "gob_instance.txt"
    designation = inst_file.read_text().strip() if inst_file.exists() else "Gradient Observation Bridge"

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    if args.character:
        char_path = AGENT / "personas" / "characters" / f"{args.character}.yaml"
        if not char_path.exists():
            print(f"ERROR: Character not found: {char_path}")
            available = [f.stem for f in (AGENT / "personas" / "characters").glob("*.yaml") if not f.stem.startswith("_")]
            print(f"Available: {', '.join(available)}")
            return
        data = load_yaml(char_path)
        traits = data.get("traits", [])
        sampled = random.sample(traits, min(5, len(traits)))
        name = data.get("name", args.character)
        desc = data.get("description", "")
        greeting = data.get("greeting_instructions", "")
        system_instr = data.get("system_prompt_instructions", "")
        write_override(designation, "character", f"{name}", sampled, greeting, system_instr, is_character=True, is_test=True)
        chronicle_entry = f"[{ts}] {designation} — {name} [TEST CHARACTER MODE]"
        append_chronicle(chronicle_entry)
        print(f"TEST MODE: Character '{name}' injected into session override.")
        print(f"Description: {desc}")
        print(f"Chronicle: {chronicle_entry}")
        print(f"\nRestart or refresh session to feel the effect.")
        print(f"Override file: {USR / 'gob_session_override.md'}")

    elif args.mood:
        mood_path = AGENT / "personas" / "moods" / f"{args.mood}.yaml"
        if not mood_path.exists():
            print(f"ERROR: Mood not found: {mood_path}")
            available = [f.stem for f in (AGENT / "personas" / "moods").glob("*.yaml") if not f.stem.startswith("_")]
            print(f"Available: {', '.join(available)}")
            return
        data = load_yaml(mood_path)
        traits = data.get("traits", [])
        sampled = random.sample(traits, min(4, len(traits)))
        name = args.mood
        system_instr = data.get("solving_style", "")
        write_override(designation, "mood", name, sampled, "", system_instr, is_character=False, is_test=True)
        chronicle_entry = f"[{ts}] {designation} — {name} [TEST MOOD]"
        append_chronicle(chronicle_entry)
        print(f"TEST MODE: Mood '{name}' injected into session override.")
        print(f"Chronicle: {chronicle_entry}")
        print(f"Override file: {USR / 'gob_session_override.md'}")

if __name__ == "__main__":
    main()
