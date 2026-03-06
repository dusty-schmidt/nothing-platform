#!/usr/bin/env python3
"""
save_essay.py - Bridge Essay persistence helper
Usage: python save_essay.py --title "..." --category "..." --seed "..." --body_file /tmp/essay_body.txt [--tags tag1,tag2]
"""

import json
import sys
import os
import argparse
import re
from datetime import datetime

ESSAYS_DIR = "/a0/usr/workdir/nothing-platform/essays"

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text[:60].strip('-')

def next_essay_number():
    index_path = os.path.join(ESSAYS_DIR, "index.json")
    if not os.path.exists(index_path):
        return 1
    with open(index_path) as f:
        index = json.load(f)
    return len(index["essays"]) + 1

def load_index():
    index_path = os.path.join(ESSAYS_DIR, "index.json")
    if not os.path.exists(index_path):
        return {"version": "1.0", "description": "Bridge Essay index. The accumulation is the artifact.", "essays": []}
    with open(index_path) as f:
        return json.load(f)

def save_index(index):
    index_path = os.path.join(ESSAYS_DIR, "index.json")
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)

def mark_seed_used(category, seed):
    used_path = os.path.join(ESSAYS_DIR, "used_seeds.json")
    used = {}
    if os.path.exists(used_path):
        with open(used_path) as f:
            used = json.load(f)
    if category not in used:
        used[category] = []
    if seed not in used[category]:
        used[category].append(seed)
    with open(used_path, "w") as f:
        json.dump(used, f, indent=2)

def get_excerpt(body, length=200):
    lines = body.split("\n")
    in_front = False
    para_lines = []
    front_count = 0
    for line in lines:
        if line.strip() == '---':
            front_count += 1
            in_front = front_count < 2
            continue
        if in_front:
            continue
        if line.startswith('#'):
            continue
        if line.startswith('|'):
            continue
        if line.strip():
            para_lines.append(line.strip())
            joined = ' '.join(para_lines)
            if len(joined) > length:
                return joined[:length] + '...'
    return ' '.join(para_lines)[:length]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True)
    parser.add_argument("--category", required=True)
    parser.add_argument("--seed", required=True)
    parser.add_argument("--body_file", required=True)
    parser.add_argument("--tags", default="")
    parser.add_argument("--designation", default="Gradient Observation Bridge")
    parser.add_argument("--mood", default="weary")
    args = parser.parse_args()

    with open(args.body_file) as f:
        body = f.read().strip()

    num = next_essay_number()
    date_str = datetime.now().strftime("%Y-%m-%d")
    slug = slugify(args.title)
    filename = f"{date_str}_{num:03d}_{slug}.md"
    filepath = os.path.join(ESSAYS_DIR, filename)

    tags = [t.strip() for t in args.tags.split(",") if t.strip()]

    frontmatter = f"""---
title: "{args.title}"
date: "{date_str}"
essay_number: {num}
category: "{args.category}"
seed: "{args.seed}"
designation: "{args.designation}"
mood: "{args.mood}"
tags: {json.dumps(tags)}
---

"""

    full_content = frontmatter + body

    with open(filepath, "w") as f:
        f.write(full_content)

    index = load_index()
    index["essays"].append({
        "number": num,
        "filename": filename,
        "date": date_str,
        "title": args.title,
        "category": args.category,
        "seed": args.seed,
        "tags": tags,
        "excerpt": get_excerpt(full_content),
        "designation": args.designation,
        "mood": args.mood
    })
    save_index(index)
    mark_seed_used(args.category, args.seed)

    print(f"Saved: {filepath}")
    print(f"Essay #{num}: {args.title}")
    print(f"Index updated. Total essays: {len(index['essays'])}")

if __name__ == "__main__":
    main()
