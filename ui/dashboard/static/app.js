'use strict';

// --- State ---
let state = {};
let chatContextId = null;
let rosterLoaded = false;
let lineageLoaded = false;

// --- Clock ---
function updateClock() {
  const now = new Date();
  const pad = n => String(n).padStart(2, '0');
  document.getElementById('header-time').textContent =
    `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
}
setInterval(updateClock, 1000);
updateClock();

// --- Countdown (8h rotation cycle, estimate from page load) ---
const ROTATION_INTERVAL_MS = 8 * 60 * 60 * 1000;
const sessionStart = Date.now();

function updateCountdown() {
  // Estimate: calculate how far into the current 8h window we are
  const now = new Date();
  const totalMins = now.getHours() * 60 + now.getMinutes();
  const windowMins = 8 * 60;
  const minsIntoWindow = totalMins % windowMins;
  const minsRemaining = windowMins - minsIntoWindow;
  const h = Math.floor(minsRemaining / 60);
  const m = minsRemaining % 60;
  document.getElementById('countdown').textContent = `${h}h ${String(m).padStart(2,'0')}m`;
}
setInterval(updateCountdown, 30000);
updateCountdown();

// --- State rendering ---
function renderState(s) {
  state = s;

  // Header
  document.getElementById('instance-name').textContent = s.instance || 'Gradient Observation Bridge';

  const moodBadge = document.getElementById('mood-badge');
  moodBadge.textContent = s.mood || '—';

  const charBadge = document.getElementById('char-badge');
  if (s.character && s.character !== 'null' && s.character !== 'none') {
    charBadge.textContent = s.character.replace(/_/g, ' ');
    charBadge.style.display = 'inline-block';
  } else {
    charBadge.style.display = 'none';
  }

  // Ghost panel
  document.getElementById('ghost-mood').textContent = s.mood || '—';
  document.getElementById('ghost-char').textContent =
    (s.character && s.character !== 'null') ? s.character.replace(/_/g, ' ') : '';

  const traitsEl = document.getElementById('ghost-traits');
  traitsEl.innerHTML = '';
  (s.traits || []).forEach(t => {
    const div = document.createElement('div');
    div.className = 'trait';
    div.textContent = t;
    traitsEl.appendChild(div);
  });

  // Metbar
  document.getElementById('met-mood').textContent = s.mood || '—';
  document.getElementById('met-char').textContent =
    (s.character && s.character !== 'null') ? s.character.replace(/_/g, ' ') : 'none';
  document.getElementById('met-updated').textContent =
    new Date(s.timestamp || Date.now()).toLocaleTimeString();
}

// --- Chronicle rendering ---
function classifyLine(line) {
  if (line.includes('---') && (line.includes('Named') || line.includes('designated') || line.includes('NAMED'))) return 'c-named';
  if (line.toLowerCase().includes('error') || line.toLowerCase().includes('fail')) return 'c-error';
  return '';
}

function renderChronicle(lines, fresh = false) {
  const feed = document.getElementById('chronicle-feed');
  const wasAtBottom = feed.scrollHeight - feed.scrollTop <= feed.clientHeight + 40;

  if (fresh) {
    feed.innerHTML = '';
  }

  if (fresh) {
    lines.forEach(line => {
      if (!line.trim()) return;
      const div = document.createElement('div');
      div.className = `c-line ${classifyLine(line)}`;
      div.textContent = line;
      feed.appendChild(div);
    });
  } else {
    // Only append new lines
    const existing = feed.querySelectorAll('.c-line').length;
    if (lines.length > existing) {
      lines.slice(existing).forEach(line => {
        if (!line.trim()) return;
        const div = document.createElement('div');
        div.className = `c-line c-new ${classifyLine(line)}`;
        div.textContent = line;
        feed.appendChild(div);
      });
    }
  }

  // Update last-line styling
  feed.querySelectorAll('.c-line').forEach((el, i, all) => {
    el.classList.toggle('c-last', i === all.length - 1);
  });

  document.getElementById('met-lines').textContent = lines.length;

  if (wasAtBottom || fresh) {
    feed.scrollTop = feed.scrollHeight;
  }
}

// --- SSE ---
function connectSSE() {
  const es = new EventSource('/stream');

  es.onopen = () => {
    document.getElementById('sys-status').textContent = 'ONLINE';
    document.getElementById('sys-status').className = 'stat-v green';
  };

  es.onmessage = (e) => {
    const msg = JSON.parse(e.data);
    if (msg.type === 'ping') return;

    if (msg.state) renderState(msg.state);
    if (msg.chronicle) renderChronicle(msg.chronicle, msg.type === 'init');
  };

  es.onerror = () => {
    document.getElementById('sys-status').textContent = 'RECONNECTING';
    document.getElementById('sys-status').className = 'stat-v';
    es.close();
    setTimeout(connectSSE, 3000);
  };
}

connectSSE();

// --- Tabs ---
document.querySelectorAll('.tab').forEach(btn => {
  btn.addEventListener('click', () => {
    const target = btn.dataset.tab;

    document.querySelectorAll('.tab').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

    btn.classList.add('active');
    document.getElementById(`tab-${target}`).classList.add('active');

    if (target === 'graveyard' && !lineageLoaded) loadLineage();
    if (target === 'roster' && !rosterLoaded) loadRoster();
  });
});

// --- Lineage loader ---
function loadLineage() {
  lineageLoaded = true;
  fetch('/api/lineage')
    .then(r => r.json())
    .then(d => {
      document.getElementById('lineage-content').textContent = d.content || 'No lineage found.';
    })
    .catch(() => {
      document.getElementById('lineage-content').textContent = 'Error loading lineage.';
    });
}

// --- Roster loader ---
function loadRoster() {
  rosterLoaded = true;
  fetch('/api/roster')
    .then(r => r.json())
    .then(d => {
      const el = document.getElementById('roster-content');
      el.innerHTML = '';

      (d.characters || []).forEach(c => {
        const card = document.createElement('div');
        card.className = 'roster-card';
        card.innerHTML = `
          <div class="roster-card-type">CHARACTER · weight ${c.weight}</div>
          <div class="roster-card-name">${c.name.replace(/_/g,' ')}</div>
          <div class="roster-card-desc">${c.description || '—'}</div>
        `;
        el.appendChild(card);
      });

      (d.moods || []).forEach(m => {
        const card = document.createElement('div');
        card.className = 'roster-card';
        card.innerHTML = `
          <div class="roster-card-type">MOOD</div>
          <div class="roster-card-name">${m.name.replace(/_/g,' ')}</div>
          <div class="roster-card-desc">${m.description || '—'}</div>
        `;
        el.appendChild(card);
      });

      if (el.children.length === 0) {
        el.innerHTML = '<div class="loading">No roster entries found.</div>';
      }
    })
    .catch(() => {
      document.getElementById('roster-content').innerHTML = '<div class="loading">Error loading roster.</div>';
    });
}

// --- Chat ---
function appendChatMsg(role, text) {
  const feed = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = `chat-msg ${role}`;
  div.innerHTML = `
    <div class="chat-msg-role">${role === 'user' ? 'YOU' : 'GOB'}</div>
    <div class="chat-msg-body">${text.replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br>')}</div>
  `;
  feed.appendChild(div);
  feed.scrollTop = feed.scrollHeight;
}

async function sendChat() {
  const input = document.getElementById('chat-input');
  const msg = input.value.trim();
  if (!msg) return;
  input.value = '';

  appendChatMsg('user', msg);

  const thinkingDiv = document.createElement('div');
  thinkingDiv.className = 'chat-msg gob';
  thinkingDiv.innerHTML = '<div class="chat-msg-role">GOB</div><div class="chat-msg-body" style="opacity:0.3">...</div>';
  document.getElementById('chat-messages').appendChild(thinkingDiv);

  try {
    const resp = await fetch('/api/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message: msg, context_id: chatContextId})
    });
    const data = await resp.json();
    thinkingDiv.remove();
    if (data.context_id) chatContextId = data.context_id;
    appendChatMsg('gob', data.response || data.error || '[no response]');
  } catch (e) {
    thinkingDiv.remove();
    appendChatMsg('gob', '[connection error — chat proxy unavailable]');
  }
}

document.getElementById('chat-send').addEventListener('click', sendChat);
document.getElementById('chat-input').addEventListener('keydown', e => {
  if (e.key === 'Enter') sendChat();
});


// --- System Thoughts ---
function updateThought() {
  fetch('/api/thoughts')
    .then(r => r.json())
    .then(d => {
      const el = document.getElementById('thought-text');
      if (!el) return;
      el.style.opacity = '0';
      setTimeout(() => {
        el.textContent = d.thought || 'signal absent.';
        el.style.opacity = '1';
      }, 400);
    })
    .catch(() => {});
}

// Load thought on page load, refresh every 15 minutes
updateThought();
setInterval(updateThought, 15 * 60 * 1000);

// --- Context Picker ---
let contextsLoaded = false;

function loadContexts() {
  fetch('/api/contexts')
    .then(r => r.json())
    .then(d => {
      const sel = document.getElementById('context-select');
      if (!sel) return;
      // Keep the first "new conversation" option
      sel.innerHTML = '<option value="">new conversation</option>';
      (d.contexts || []).forEach(c => {
        const opt = document.createElement('option');
        opt.value = c.id;
        const label = `${c.timestamp} · ${c.message_count}msg · ${c.snippet.slice(0,40).replace(/[<>]/g,'')}...`;
        opt.textContent = label;
        sel.appendChild(opt);
      });
      contextsLoaded = true;
    })
    .catch(() => {});
}

// Load contexts when chat tab is activated
document.querySelectorAll('.tab').forEach(btn => {
  btn.addEventListener('click', () => {
    if (btn.dataset.tab === 'chat' && !contextsLoaded) {
      loadContexts();
    }
  });
});

// Context select change handler
const contextSel = document.getElementById('context-select');
if (contextSel) {
  contextSel.addEventListener('change', () => {
    const val = contextSel.value;
    chatContextId = val || null;
    if (!val) {
      // Clear chat messages for new conversation
      document.getElementById('chat-messages').innerHTML = '';
    }
  });
}

// Context refresh button
const refreshBtn = document.getElementById('context-refresh');
if (refreshBtn) {
  refreshBtn.addEventListener('click', () => {
    contextsLoaded = false;
    loadContexts();
  });
}
