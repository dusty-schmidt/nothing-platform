import os, json, time, re, glob, threading, queue, logging
from datetime import datetime
from flask import Flask, render_template, jsonify, request, Response, stream_with_context

# ── Logging setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    filename='/tmp/dashboard.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)
logger = logging.getLogger('gob_dashboard')

# Also log to stderr so nohup captures it
sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
sh.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
logging.getLogger().addHandler(sh)

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)
logger.info('GOB Dashboard app.py loaded')

# Paths to GOB system files
GOB_ROOT = '/a0/usr'
CHRONICLE = '/a0/usr/gob_chronicle.txt'
SESSION_OVERRIDE = '/a0/usr/gob_session_override.md'
INSTANCE_FILE = '/a0/usr/gob_instance.txt'
CHARACTERS_DIR = '/a0/agents/agent0/personas/characters'
MOODS_DIR = '/a0/agents/agent0/personas/moods'
LINEAGE = '/a0/usr/workdir/nothing-platform/chronicle/INSTANCE_LINEAGE.md'
GOB_API = 'http://localhost:80'
SETTINGS = '/a0/usr/settings.json'
THOUGHT_FILE = '/a0/usr/gob_current_thought.txt'
CHATS_DIR = '/a0/usr/chats'

# SSE subscriber queues
_subscribers = []
_subscribers_lock = threading.Lock()

def read_file(path, default=''):
    try:
        with open(path, 'r') as f:
            return f.read()
    except Exception as e:
        logger.debug('read_file failed: %s — %s', path, e)
        return default

def get_token():
    """Read mcp_server_token from settings.json."""
    try:
        with open(SETTINGS) as sf:
            settings = json.load(sf)
            tok = settings.get('mcp_server_token', '')
            logger.debug('get_token: length=%d', len(tok))
            return tok
    except Exception as e:
        logger.warning('get_token failed: %s', e)
        return ''

def get_instance():
    return read_file(INSTANCE_FILE, 'Gradient Observation Bridge').strip()

def parse_session_override():
    """Parse gob_session_override.md for current mood/character/traits."""
    raw = read_file(SESSION_OVERRIDE, '')
    result = {'mood': 'unknown', 'character': None, 'traits': [], 'raw': raw}

    mood_m = re.search(r'mood[:\s]+([\w_]+)', raw, re.IGNORECASE)
    if mood_m:
        result['mood'] = mood_m.group(1)

    char_m = re.search(r'character[:\s]+([\w_]+)', raw, re.IGNORECASE)
    if char_m and char_m.group(1).lower() not in ('none', 'null', ''):
        result['character'] = char_m.group(1)

    traits = re.findall(r'^[-*]\s+(.+)$', raw, re.MULTILINE)
    result['traits'] = traits[:5]

    return result

def get_chronicle_lines(n=50):
    raw = read_file(CHRONICLE, '')
    lines = [l for l in raw.strip().split('\n') if l.strip()]
    return lines[-n:]

def get_roster():
    chars = []
    for f in glob.glob(os.path.join(CHARACTERS_DIR, '*.yaml')):
        name = os.path.basename(f).replace('.yaml', '')
        if name.startswith('_'):
            continue
        content = read_file(f, '')
        desc_m = re.search(r'description[:\s]+(.+)', content)
        weight_m = re.search(r'weight[:\s]+([\d.]+)', content)
        chars.append({
            'name': name,
            'description': desc_m.group(1).strip() if desc_m else '',
            'weight': float(weight_m.group(1)) if weight_m else 1.0
        })

    moods = []
    for f in glob.glob(os.path.join(MOODS_DIR, '*.yaml')):
        name = os.path.basename(f).replace('.yaml', '')
        if name.startswith('_'):
            continue
        content = read_file(f, '')
        desc_m = re.search(r'description[:\s]+(.+)', content)
        moods.append({
            'name': name,
            'description': desc_m.group(1).strip() if desc_m else ''
        })

    return {'characters': chars, 'moods': moods}

def get_state():
    session = parse_session_override()
    chronicle = get_chronicle_lines(5)
    return {
        'instance': get_instance(),
        'mood': session['mood'],
        'character': session['character'],
        'traits': session['traits'],
        'chronicle_tail': chronicle,
        'timestamp': datetime.now().isoformat()
    }

# Background watcher - broadcasts updates to SSE subscribers
_last_chronicle_mtime = 0
_last_session_mtime = 0

def watcher():
    global _last_chronicle_mtime, _last_session_mtime
    while True:
        try:
            changed = False
            try:
                cm = os.path.getmtime(CHRONICLE)
                if cm != _last_chronicle_mtime:
                    _last_chronicle_mtime = cm
                    changed = True
            except Exception:
                pass
            try:
                sm = os.path.getmtime(SESSION_OVERRIDE)
                if sm != _last_session_mtime:
                    _last_session_mtime = sm
                    changed = True
            except Exception:
                pass

            if changed:
                payload = json.dumps({'type': 'update', 'state': get_state(),
                                      'chronicle': get_chronicle_lines(50)})
                with _subscribers_lock:
                    dead = []
                    for q in _subscribers:
                        try:
                            q.put_nowait(payload)
                        except Exception:
                            dead.append(q)
                    for q in dead:
                        _subscribers.remove(q)
        except Exception as e:
            logger.error('watcher error: %s', e)
        time.sleep(3)

watcher_thread = threading.Thread(target=watcher, daemon=True)
watcher_thread.start()

# ── Routes ───────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    logger.info('GET /')
    return render_template('index.html')

@app.route('/api/state')
def api_state():
    logger.debug('GET /api/state')
    return jsonify(get_state())

@app.route('/api/chronicle')
def api_chronicle():
    n = int(request.args.get('n', 50))
    logger.debug('GET /api/chronicle n=%d', n)
    return jsonify({'lines': get_chronicle_lines(n)})

@app.route('/api/roster')
def api_roster():
    logger.debug('GET /api/roster')
    return jsonify(get_roster())

@app.route('/api/lineage')
def api_lineage():
    logger.debug('GET /api/lineage')
    return jsonify({'content': read_file(LINEAGE, 'No lineage found.')})

@app.route('/stream')
def stream():
    logger.info('SSE /stream — new subscriber')
    q = queue.Queue(maxsize=20)
    with _subscribers_lock:
        _subscribers.append(q)

    def generate():
        yield f"data: {json.dumps({'type': 'init', 'state': get_state(), 'chronicle': get_chronicle_lines(50)})}\n\n"
        try:
            while True:
                try:
                    payload = q.get(timeout=30)
                    yield f'data: {payload}\n\n'
                except queue.Empty:
                    yield f'data: {json.dumps({"type": "ping"})}\n\n'
        except GeneratorExit:
            with _subscribers_lock:
                try:
                    _subscribers.remove(q)
                except ValueError:
                    pass

    return Response(stream_with_context(generate()),
                    mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Proxy chat to GOB REST API."""
    import urllib.request
    api_key = get_token()
    data = request.json or {}
    msg = data.get('message', '')
    ctx = data.get('context_id') or ''
    logger.info('POST /api/chat message_len=%d context_id=%s token_len=%d', len(msg), ctx, len(api_key))
    payload = json.dumps({'message': msg, 'context_id': ctx}).encode()
    try:
        req = urllib.request.Request(
            f'{GOB_API}/api_message',
            data=payload,
            headers={'Content-Type': 'application/json', 'X-API-KEY': api_key},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
            logger.info('api_chat: success context_id=%s', result.get('context_id'))
            return jsonify(result)
    except Exception as e:
        logger.error('api_chat proxy error: %s', e)
        return jsonify({'error': str(e), 'response': '[Chat unavailable]'}), 503

@app.route('/api/thoughts')
def api_thoughts():
    """Return cached system thought from file."""
    logger.debug('GET /api/thoughts')
    thought = read_file(THOUGHT_FILE, 'the buffer holds. for now.')
    return jsonify({'thought': thought.strip()})

@app.route('/api/contexts')
def api_contexts():
    """List available chat contexts."""
    logger.debug('GET /api/contexts')
    contexts = []
    try:
        for ctx_id in sorted(os.listdir(CHATS_DIR)):
            ctx_path = os.path.join(CHATS_DIR, ctx_id)
            if not os.path.isdir(ctx_path):
                continue
            msg_dir = os.path.join(ctx_path, 'messages')
            if not os.path.isdir(msg_dir):
                continue
            msgs = sorted(
                [f for f in os.listdir(msg_dir) if f.endswith('.txt')],
                key=lambda x: int(x.replace('.txt', '')) if x.replace('.txt', '').isdigit() else 0
            )
            if not msgs:
                continue
            snippet = ''
            try:
                with open(os.path.join(msg_dir, msgs[-1]), 'r', errors='replace') as f:
                    snippet = f.read(150).strip().replace('\n', ' ')[:100]
            except Exception:
                pass
            mtime = os.path.getmtime(ctx_path)
            contexts.append({
                'id': ctx_id,
                'message_count': len(msgs),
                'snippet': snippet,
                'timestamp': datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
            })
    except Exception as e:
        logger.error('api_contexts error: %s', e)
        return jsonify({'contexts': [], 'error': str(e)})
    contexts.sort(key=lambda x: x['timestamp'], reverse=True)
    logger.debug('api_contexts: returned %d contexts', len(contexts))
    return jsonify({'contexts': contexts})

@app.route('/api/logs')
def api_logs():
    ctx = request.args.get('context_id', '')
    length = int(request.args.get('length', '60'))
    logger.info('GET /api/logs context_id=%s length=%d', ctx, length)
    if not ctx:
        try:
            out = []
            for name in sorted(os.listdir(CHATS_DIR), reverse=True):
                p = os.path.join(CHATS_DIR, name)
                if os.path.isdir(p):
                    msgs = os.path.join(p, 'messages')
                    count = len(os.listdir(msgs)) if os.path.isdir(msgs) else 0
                    out.append({'id': name, 'messages': count, 'mtime': os.path.getmtime(p)})
            return jsonify({'contexts': out})
        except Exception as e:
            logger.error('api_logs list error: %s', e)
            return jsonify({'error': str(e)}), 500
    try:
        msgs_dir = os.path.join(CHATS_DIR, ctx, 'messages')
        lines = []
        if os.path.isdir(msgs_dir):
            files = sorted(os.listdir(msgs_dir),
                           key=lambda x: int(x.split('.')[0]) if x.split('.')[0].isdigit() else 0)
            for fname in files[-length:]:
                fp = os.path.join(msgs_dir, fname)
                try:
                    raw = open(fp, errors='replace').read(500)
                    lines.append({'num': fname, 'content': raw.strip()})
                except Exception:
                    pass
        logger.debug('api_logs: returned %d lines for %s', len(lines), ctx)
        return jsonify({'lines': lines, 'source': 'disk', 'context_id': ctx})
    except Exception as e:
        logger.error('api_logs read error: %s', e)
        return jsonify({'error': str(e)}), 500

@app.route('/api/test')
def api_test():
    """Health check — tests all major subsystems."""
    import urllib.request as _ur
    logger.info('GET /api/test')
    results = {}

    # 1. Thought file
    try:
        exists = os.path.isfile(THOUGHT_FILE)
        content = read_file(THOUGHT_FILE, '').strip()
        results['thought_file'] = {'pass': exists, 'detail': content[:80] if exists else 'missing'}
    except Exception as e:
        results['thought_file'] = {'pass': False, 'detail': str(e)}

    # 2. Settings.json readable + token present
    try:
        with open(SETTINGS) as sf:
            s = json.load(sf)
        tok = s.get('mcp_server_token', '')
        results['settings'] = {'pass': True, 'detail': f'readable, token_len={len(tok)}'}
    except Exception as e:
        results['settings'] = {'pass': False, 'detail': str(e)}

    # 3. Chronicle file
    try:
        exists = os.path.isfile(CHRONICLE)
        lines = get_chronicle_lines(3)
        results['chronicle'] = {'pass': exists, 'detail': f'{len(lines)} lines' if exists else 'missing'}
    except Exception as e:
        results['chronicle'] = {'pass': False, 'detail': str(e)}

    # 4. Chats directory
    try:
        exists = os.path.isdir(CHATS_DIR)
        count = len([d for d in os.listdir(CHATS_DIR) if os.path.isdir(os.path.join(CHATS_DIR, d))]) if exists else 0
        results['chats_dir'] = {'pass': exists, 'detail': f'{count} contexts' if exists else 'missing'}
    except Exception as e:
        results['chats_dir'] = {'pass': False, 'detail': str(e)}

    # 5. Agent Zero API reachable
    try:
        tok = get_token()
        req = _ur.Request(
            f'{GOB_API}/api_message',
            data=json.dumps({'message': 'ping', 'context_id': ''}).encode(),
            headers={'Content-Type': 'application/json', 'X-API-KEY': tok},
            method='POST'
        )
        with _ur.urlopen(req, timeout=5) as resp:
            code = resp.getcode()
            results['agent_api'] = {'pass': True, 'detail': f'HTTP {code}'}
    except Exception as e:
        results['agent_api'] = {'pass': False, 'detail': str(e)}

    # 6. SSE chronicle file
    try:
        exists = os.path.isfile(CHRONICLE)
        results['chronicle_sse'] = {'pass': exists, 'detail': 'file present' if exists else 'missing'}
    except Exception as e:
        results['chronicle_sse'] = {'pass': False, 'detail': str(e)}

    # 7. Session override
    try:
        exists = os.path.isfile(SESSION_OVERRIDE)
        results['session_override'] = {'pass': exists, 'detail': 'present' if exists else 'missing'}
    except Exception as e:
        results['session_override'] = {'pass': False, 'detail': str(e)}

    overall = all(v['pass'] for v in results.values())
    logger.info('api_test overall=%s results=%s', overall, results)
    return jsonify({'overall': overall, 'checks': results, 'timestamp': datetime.now().isoformat()})

# ── Lore helpers (used by generate_thought.py if imported) ───────────────────

def build_lore_context():
    """Assemble minimal GOB lore for the thoughts model."""
    parts = []
    parts.append(f'Current instance: {get_instance()}')
    session = parse_session_override()
    parts.append(f'Current mood: {session["mood"]}')
    if session['traits']:
        parts.append('Active traits:\n' + '\n'.join(f'- {t}' for t in session['traits']))
    lines = get_chronicle_lines(8)
    if lines:
        parts.append('Recent chronicle:\n' + '\n'.join(lines[-5:]))
    acronyms_raw = read_file('/a0/agents/agent0/gob_acronyms.md', '')
    if acronyms_raw:
        sample = [l for l in acronyms_raw.split('\n') if l.strip()][:10]
        parts.append('Acronym pool sample:\n' + '\n'.join(sample))
    return '\n\n'.join(parts)

if __name__ == '__main__':
    logger.info('GOB Dashboard starting on port 7842')
    print('GOB Dashboard starting on port 7842')
    app.run(host='0.0.0.0', port=7842, debug=False, threaded=True)
