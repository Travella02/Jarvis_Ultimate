const DEFAULT_STATE = {
  avatar: { state: 'sleeping', label: 'Sleep Mode', message: 'Waiting for wake phrase.' },
  runtime: { llm_provider: 'unknown', llm_model: 'unknown', tts_provider: 'unknown', stt_provider: 'unknown', agent_count: 0 },
  workspace: { chat_messages: [], events: [], panels: {} },
  app: { bridge_status: 'offline', api_url: 'http://127.0.0.1:8765' },
  voice: { mode: 'idle', running: false, last_transcript: '', last_status: 'Ready.' }
};

let apiUrl = DEFAULT_STATE.app.api_url;
let lastState = DEFAULT_STATE;

const els = {
  bridgeStatus: document.getElementById('bridgeStatus'),
  stateLabel: document.getElementById('stateLabel'),
  stateMessage: document.getElementById('stateMessage'),
  llmStatus: document.getElementById('llmStatus'),
  sttStatus: document.getElementById('sttStatus'),
  ttsStatus: document.getElementById('ttsStatus'),
  agentStatus: document.getElementById('agentStatus'),
  panelList: document.getElementById('panelList'),
  chatLog: document.getElementById('chatLog'),
  eventsLog: document.getElementById('eventsLog'),
  commandForm: document.getElementById('commandForm'),
  commandInput: document.getElementById('commandInput'),
  refreshButton: document.getElementById('refreshButton'),
  voiceOnceButton: document.getElementById('voiceOnceButton'),
  sleepWakeButton: document.getElementById('sleepWakeButton'),
  stopVoiceButton: document.getElementById('stopVoiceButton'),
  voiceMode: document.getElementById('voiceMode'),
  voiceTranscript: document.getElementById('voiceTranscript'),
  voiceStatus: document.getElementById('voiceStatus')
};

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function normalizeState(state) {
  return String(state || 'idle').trim().toLowerCase().replaceAll(' ', '_');
}

function readable(value) {
  return String(value || 'idle').replaceAll('_', ' ');
}

function setVisualState(state, message, label) {
  const next = normalizeState(state);
  document.body.className = `state-${next}`;
  els.stateLabel.textContent = label || readable(next);
  els.stateMessage.textContent = message || 'Ready, sir.';
}

function renderVoice(voice) {
  const session = voice || DEFAULT_STATE.voice;
  const running = Boolean(session.running || session.thread_alive);
  els.voiceMode.textContent = running ? `${readable(session.mode)} running` : readable(session.mode || 'idle');
  els.voiceTranscript.textContent = session.last_transcript || 'none yet';
  els.voiceStatus.textContent = session.last_error || session.last_status || 'Ready.';
  els.voiceOnceButton.disabled = running;
  els.sleepWakeButton.disabled = running;
  els.stopVoiceButton.disabled = !running;
}

function renderState(snapshot) {
  lastState = snapshot || DEFAULT_STATE;
  const avatar = lastState.avatar || DEFAULT_STATE.avatar;
  const runtime = lastState.runtime || DEFAULT_STATE.runtime;
  const workspace = lastState.workspace || DEFAULT_STATE.workspace;
  const app = lastState.app || DEFAULT_STATE.app;
  const voice = lastState.voice || DEFAULT_STATE.voice;

  setVisualState(avatar.state, avatar.message, avatar.label || avatar.profile?.label);
  renderVoice(voice);

  const online = app.bridge_status === 'online';
  els.bridgeStatus.textContent = online ? 'Bridge Online' : 'Bridge Offline';
  els.bridgeStatus.title = app.api_url || apiUrl;
  els.llmStatus.textContent = `${runtime.llm_provider || 'unknown'} / ${runtime.llm_model || 'unknown'}`;
  els.sttStatus.textContent = runtime.stt_provider || 'unknown';
  els.ttsStatus.textContent = runtime.tts_provider || 'unknown';
  els.agentStatus.textContent = String(runtime.agent_count || runtime.agents?.length || 0);

  const panels = workspace.panels ? Object.values(workspace.panels) : [];
  els.panelList.innerHTML = panels.length
    ? panels.map(panel => `<li><strong>${escapeHtml(panel.title)}</strong><br>${escapeHtml(panel.panel_id)} · ${panel.is_open ? 'open' : 'ready'}</li>`).join('')
    : '<li>No panels registered yet.</li>';

  const chats = workspace.chat_messages || [];
  els.chatLog.innerHTML = chats.length
    ? chats.map(msg => `<div class="chat-message"><strong>${escapeHtml(msg.role || 'jarvis')}:</strong> ${escapeHtml(msg.text || '')}</div>`).join('')
    : '<div class="chat-message"><strong>jarvis:</strong> App shell ready. Waiting for the local bridge.</div>';
  els.chatLog.scrollTop = els.chatLog.scrollHeight;

  const events = workspace.events || [];
  els.eventsLog.innerHTML = events.length
    ? events.slice(-24).map(event => `${escapeHtml(event.timestamp || '')} | ${escapeHtml(event.event_type || '')} | ${escapeHtml(event.message || '')}`).join('<br>')
    : 'No events yet.';
  els.eventsLog.scrollTop = els.eventsLog.scrollHeight;
}

async function fetchJson(path, options = {}) {
  const response = await fetch(`${apiUrl}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options
  });
  const data = await response.json();
  if (!response.ok || data.success === false) {
    throw new Error(data.message || `HTTP ${response.status}`);
  }
  return data;
}

async function refreshState() {
  try {
    const payload = await fetchJson('/api/state');
    renderState(payload.data);
  } catch (error) {
    renderState({
      ...lastState,
      app: { ...(lastState.app || {}), bridge_status: 'offline', api_url: apiUrl },
      avatar: { state: 'error', label: 'Bridge Offline', message: `Local API unavailable: ${error.message}` }
    });
  }
}

async function sendCommand(command) {
  setVisualState('thinking', 'Sending command through local API...', 'Thinking');
  try {
    const payload = await fetchJson('/api/command', {
      method: 'POST',
      body: JSON.stringify({ command })
    });
    renderState(payload.data.state || payload.data);
  } catch (error) {
    renderState({
      ...lastState,
      app: { ...(lastState.app || {}), bridge_status: 'offline', api_url: apiUrl },
      avatar: { state: 'error', label: 'Command Error', message: error.message }
    });
  }
}

async function postVoice(path, body = {}) {
  try {
    const payload = await fetchJson(path, {
      method: 'POST',
      body: JSON.stringify(body)
    });
    renderState(payload.data.state || payload.data);
    return payload;
  } catch (error) {
    renderState({
      ...lastState,
      avatar: { state: 'error', label: 'Voice Error', message: error.message }
    });
    return null;
  }
}

async function startVoiceOnce() {
  setVisualState('listening', 'Listening for one real microphone turn...', 'Listening');
  await postVoice('/api/voice/once', { speak: true });
  setTimeout(refreshState, 350);
}

async function startSleepWake() {
  setVisualState('wake_listening', 'Starting sleep/wake voice mode...', 'Listening for Wake Word');
  await postVoice('/api/voice/sleep-wake/start', { max_turns: 0, speak: true });
  setTimeout(refreshState, 350);
}

async function stopVoice() {
  await postVoice('/api/voice/stop', {});
  setTimeout(refreshState, 350);
}

async function boot() {
  if (window.jarvisNative?.getConfig) {
    const config = await window.jarvisNative.getConfig();
    apiUrl = config.apiUrl || apiUrl;
  }

  document.querySelectorAll('[data-state]').forEach(button => {
    button.addEventListener('click', () => {
      const demoState = button.getAttribute('data-state');
      setVisualState(demoState, `Demo preview: ${demoState}`, demoState.replaceAll('_', ' '));
    });
  });

  els.refreshButton.addEventListener('click', refreshState);
  els.voiceOnceButton.addEventListener('click', startVoiceOnce);
  els.sleepWakeButton.addEventListener('click', startSleepWake);
  els.stopVoiceButton.addEventListener('click', stopVoice);
  els.commandForm.addEventListener('submit', event => {
    event.preventDefault();
    const command = els.commandInput.value.trim();
    if (!command) return;
    els.commandInput.value = '';
    sendCommand(command);
  });

  renderState(DEFAULT_STATE);
  refreshState();
  setInterval(refreshState, 900);
}

boot();
