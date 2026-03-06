#!/usr/bin/env python3
"""
GOB Character Creator
Scaffolds a new character YAML from the _sample.yaml template.
Usage: python3 gob_add_character.py --name <key> --description "<description>"
"""
import argparse
import shutil
import sys
from pathlib import Path

CHARS_DIR = Path("/a0/agents/agent0/personas/characters")
SAMPLE = CHARS_DIR / "_sample.yaml"

def main():
    parser = argparse.ArgumentParser(description="Scaffold a new GOB character YAML")
    parser.add_argument("--name", required=True, help="Character key (lowercase_underscores, matches filename)")
    parser.add_argument("--description", required=True, help="One-line description shown in chronicle")
    parser.add_argument("--temperature", type=float, default=1.0, help="LLM temperature 0.7-1.0")
    args = parser.parse_args()

    key = args.name.lower().replace("-", "_").replace(" ", "_")
    out_path = CHARS_DIR / f"{key}.yaml"

    if out_path.exists():
        print(f"ERROR: {out_path} already exists. Edit it directly or delete it first.")
        sys.exit(1)

    if not SAMPLE.exists():
        print(f"ERROR: Template not found at {SAMPLE}")
        sys.exit(1)

    # Read template and replace placeholders
    content = SAMPLE.read_text()
    content = content.replace('name: "sample"', f'name: "{key}"')
    content = content.replace('name: sample', f'name: {key}')
    content = content.replace(
        'description: "Character Name (Source) — one line description"',
        f'description: "{args.description}"'
    )
    content = content.replace(
        'description: Character Name (Source) — one line description',
        f'description: "{args.description}"'
    )
    content = content.replace('temperature: 1', f'temperature: {args.temperature}')

    out_path.write_text(content)

    print(f"""Character scaffolded: {out_path}

Next steps:
  1. Edit {out_path}
     - Fill in 'traits' (8-12 specific behavioral descriptors)
     - Fill in 'greeting_instructions' (what to include in session opening, under 40 words)
     - Fill in 'system_prompt_instructions' (behavioral rules injected every message)

  2. Optional: add weight to CHAR_WEIGHTS in rotate_persona.py
     Default weight for unlisted characters is 1.
     Use higher values (2-4) to increase selection frequency during character rolls.

  3. Sync to nothing-platform:
     cp {out_path} /a0/usr/workdir/nothing-platform/agents/agent0/personas/characters/
     cd /a0/usr/workdir/nothing-platform && git add -A && git commit -m "feat: add character {key}" && git push origin main
""")

if __name__ == "__main__":
    main()
