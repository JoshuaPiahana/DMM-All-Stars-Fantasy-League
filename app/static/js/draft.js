const managerToken = localStorage.getItem('manager_token');
const commToken = localStorage.getItem('commissioner_token');

// ── Start draft ───────────────────────────────────────────────────────────────
const startBtn = document.getElementById('start-btn');
if (startBtn) {
  startBtn.addEventListener('click', async () => {
    if (!commToken) {
      showError('start-error', 'No commissioner token in localStorage. Visit /create first.');
      return;
    }
    startBtn.disabled = true;
    const resp = await fetch('/draft/start', {
      method: 'POST',
      headers: {'X-Commissioner-Token': commToken},
    });
    if (resp.ok) {
      window.location.reload();
    } else {
      const data = await resp.json();
      showError('start-error', data.error || 'Failed to start draft');
      startBtn.disabled = false;
    }
  });
}

// ── Make a pick ───────────────────────────────────────────────────────────────
async function makePick(playerId) {
  if (!managerToken) {
    showError('pick-error', 'No manager token found. Visit your league page to claim your token.');
    return;
  }
  const resp = await fetch('/draft/pick', {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'X-Manager-Token': managerToken},
    body: JSON.stringify({player_id: playerId}),
  });
  const data = await resp.json();
  if (!resp.ok) {
    showError('pick-error', data.error || 'Pick failed');
    return;
  }
  window.location.reload();
}

// ── SSE connection ────────────────────────────────────────────────────────────
if (typeof EventSource !== 'undefined') {
  const src = new EventSource('/draft/stream');
  src.addEventListener('pick', () => window.location.reload());
  src.addEventListener('start', () => window.location.reload());
  src.addEventListener('complete', () => window.location.reload());
  src.onerror = () => {
    // Silently reconnect — browser does this automatically
  };
}

function showError(id, msg) {
  const el = document.getElementById(id);
  if (el) { el.textContent = msg; el.style.display = 'block'; }
}
