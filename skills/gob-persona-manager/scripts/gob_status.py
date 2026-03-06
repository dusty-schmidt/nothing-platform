#!/usr/bin/env python3
"""
GOB Persona Manager — Status
Shows current instance identity, session override, character roster, and recent chronicle.
"""
import yaml
from pathlib import Path
from datetime import datetime

USR = Path("/a0/usr")
AGENT = Path("/a0/agents/agent0")

def section(title):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print('='*50)

def main():
    # Instance identity
    section("INSTANCE")
    inst_file = USR / "gob_instance.txt"
    if inst_file.exists():
        print(f"  {inst_file.read_text().strip()}")
    else:
        print("  [not set]")

    # Current session
    section("CURRENT SESSION OVERRIDE")
    override = USR / "gob_session_override.md"
    if override.exists():
        print(override.read_text().strip())
    else:
        print("  [no override active]")

    # Character roster
    section("CHARACTER ROSTER")
    chars_dir = AGENT / "personas" / "characters"
    chars = sorted([f for f in chars_dir.glob("*.yaml") if not f.name.startswith("_")])
    
    # Load CHAR_WEIGHTS from rotate_persona.py
    weights = {}
    rotate = AGENT / "scripts" / "rotate_persona.py"
    if rotate.exists():
        for line in rotate.read_text().splitlines():
            if line.strip().startswith('"') or line.strip().startswith("'"):
                parts = line.strip().split(":")
                if len(parts) == 2:
                    key = parts[0].strip().strip('"\'')
                    try:
                        weights[key] = int(parts[1].strip().rstrip(","))
                    except:
                        pass

    for char_file in chars:
        try:
            data = yaml.safe_load(char_file.read_text())
            name = data.get("name", char_file.stem)
            desc = data.get("description", "no description")
            temp = data.get("temperature", 1.0)
            w = weights.get(name, 1)
            print(f"  [{w}x] {name:<20} {desc}")
        except Exception as e:
            print(f"  {char_file.name} — parse error: {e}")

    # Mood roster
    section("MOOD ROSTER")
    moods_dir = AGENT / "personas" / "moods"
    moods = sorted([f for f in moods_dir.glob("*.yaml") if not f.name.startswith("_")])
    for mood_file in moods:
        try:
            data = yaml.safe_load(mood_file.read_text())
            desc = data.get("description", "no description")
            print(f"  {mood_file.stem:<20} {desc}")
        except Exception as e:
            print(f"  {mood_file.name} — parse error: {e}")

    # Recent chronicle
    section("RECENT CHRONICLE (last 15 entries)")
    chronicle = USR / "gob_chronicle.txt"
    if chronicle.exists():
        lines = chronicle.read_text().splitlines()
        for line in lines[-15:]:
            print(f"  {line}")
    else:
        print("  [no chronicle found]")

    print()

if __name__ == "__main__":
    main()
