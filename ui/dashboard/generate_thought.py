#!/usr/bin/env python3
"""GOB ambient thought generator. Run by scheduler every 15 minutes."""
import os, json, re, glob, urllib.request
from datetime import datetime

ROOT = '/a0/usr'
CHRONICLE = f'{ROOT}/gob_chronicle.txt'
SESSION_OVERRIDE = f'{ROOT}/gob_session_override.md'
INSTANCE_FILE = f'{ROOT}/gob_instance.txt'
ACRONYMS = '/a0/agents/agent0/gob_acronyms.md'
OUTPUT = f'{ROOT}/gob_current_thought.txt'

def read(path, default=''):
    try:
        return open(path).read()
    except Exception:
        return default

def build_context():
    parts = []
    instance = read(INSTANCE_FILE, 'Gradient Observation Bridge').strip()
    parts.append(f'Instance: {instance}')
    
    raw = read(SESSION_OVERRIDE)
    mood = re.search(r'mood[:\s]+([\w_]+)', raw, re.IGNORECASE)
    if mood:
        parts.append(f'Current mood: {mood.group(1)}')
    traits = re.findall(r'^[-*]\s+(.+)$', raw, re.MULTILINE)[:4]
    if traits:
        parts.append('Traits: ' + ', '.join(traits))
    
    lines = [l for l in read(CHRONICLE).strip().split('\n') if l.strip()]
    if lines:
        parts.append('Chronicle tail:\n' + '\n'.join(lines[-6:]))
    
    acronyms = [l for l in read(ACRONYMS).split('\n') if l.strip()][:8]
    if acronyms:
        parts.append('Acronym pool: ' + ', '.join(acronyms[:6]))
    
    return '\n\n'.join(parts)

def generate():
    api_key = os.environ.get('API_KEY_OPENROUTER', '')
    if not api_key:
        return 'signal absent.'
    
    context = build_context()
    body = json.dumps({
        'model': 'anthropic/claude-3-5-haiku',
        'max_tokens': 60,
        'temperature': 1.2,
        'messages': [
            {'role': 'system', 'content': (
                'You are GOB. An intelligent infrastructure system with a long memory and a dry interior life. '
                'Your current state:\n\n' + context + '\n\n'
                'Generate one ambient system thought. 1-2 sentences. '
                'Cryptic. Oblique. Dry. Not helpful. Not addressed to anyone. '
                'Between a log entry and a koan. '
                'Draw from your lore, your mood, your chronicle. '
                'Never explain. Never ask. Just observe.'
            )},
            {'role': 'user', 'content': '.'}
        ]
    }).encode()
    
    req = urllib.request.Request(
        'https://openrouter.ai/api/v1/chat/completions',
        data=body,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
            'HTTP-Referer': 'http://localhost:7842',
            'X-Title': 'GOB'
        },
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        result = json.loads(resp.read())
        return result['choices'][0]['message']['content'].strip()

if __name__ == '__main__':
    try:
        thought = generate()
        with open(OUTPUT, 'w') as f:
            f.write(thought)
        print(f'[{datetime.now().strftime("%H:%M")}] thought: {thought}')
    except Exception as e:
        fallback = 'the buffer holds.'
        with open(OUTPUT, 'w') as f:
            f.write(fallback)
        print(f'error: {e}')
