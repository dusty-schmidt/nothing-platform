import os, json, time, re, glob, threading, queue
from datetime import datetime
from flask import Flask, render_template, jsonify, request, Response, stream_with_context

app = Flask(__name__)

# Paths to GOB system files
GOB_ROOT = '/a0/usr'
CHRONICLE = '/a0/usr/gob_chronicle.txt'
SESSION_OVERRIDE = '/a0/usr/gob_session_override.md'
INSTANCE_FILE = '/a0/usr/gob_instance.txt'
CHARACTERS_DIR = '/a0/agents/agent0/personas/characters'
MOODS_DIR = '/a0/agents/agent0/personas/moods'
LINEAGE = '/a0/usr/workdir/nothing-platform/chronicle/INSTANCE_LINEAGE.md'
GOB_API = 'http://localhost:8383'

# SSE subscriber queues
_subscribers = []
_subscribers_lock = threading.Lock()

def read_file(path, default=''):
    try:
        with open(path, 'r') as f:
            return f.read()
    except Exception:
        return default

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
        except Exception:
            pass
        time.sleep(3)

watcher_thread = threading.Thread(target=watcher, daemon=True)
watcher_thread.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/state')
def api_state():
    return jsonify(get_state())

@app.route('/api/chronicle')
def api_chronicle():
    n = int(request.args.get('n', 50))
    return jsonify({'lines': get_chronicle_lines(n)})

@app.route('/api/roster')
def api_roster():
    return jsonify(get_roster())

@app.route('/api/lineage')
def api_lineage():
    return jsonify({'content': read_file(LINEAGE, 'No lineage found.')})

@app.route('/stream')
def stream():
    q = queue.Queue(maxsize=20)
    with _subscribers_lock:
        _subscribers.append(q)
    
    def generate():
        # Send initial state immediately
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
    data = request.json or {}
    payload = json.dumps({
        'message': data.get('message', ''),
        'context_id': data.get('context_id')
    }).encode()
    try:
        req = urllib.request.Request(
            f'{GOB_API}/api/message',
            data=payload,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
            return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e), 'response': '[Chat unavailable]'}), 503

if __name__ == '__main__':
    print('GOB Dashboard starting on port 7842')
    app.run(host='0.0.0.0', port=7842, debug=False, threaded=True)
