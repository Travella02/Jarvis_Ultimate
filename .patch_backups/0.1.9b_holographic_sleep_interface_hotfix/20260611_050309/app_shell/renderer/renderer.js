const DEFAULT_STATE = {
  avatar: { state: 'sleeping', label: 'Sleep Mode', message: 'Waiting for wake phrase.' },
  runtime: { llm_provider: 'unknown', llm_model: 'unknown', tts_provider: 'unknown', stt_provider: 'unknown', agent_count: 0 },
  workspace: { chat_messages: [], events: [], panels: {} },
  app: { bridge_status: 'offline', api_url: 'http://127.0.0.1:8765' },
  voice: { mode: 'idle', running: false, last_transcript: '', last_status: 'Ready.', warmup_complete: false, warmup_status: 'Voice warmup has not run yet.' }
};

const PANEL_KEYS = ['runtime', 'voice', 'workspace', 'conversation', 'diagnostics'];
const PANEL_STORAGE_KEY = 'jarvis.appShell.panelVisibility.v019a';
const AUTO_WAKE_STORAGE_KEY = 'jarvis.appShell.autoSleepWake.v019a';

let apiUrl = DEFAULT_STATE.app.api_url;
let lastState = DEFAULT_STATE;
let diagnosticsOpen = false;
let orbFocus = false;
let autoSleepWakeEnabled = loadAutoSleepWakeEnabled();
let autoSleepWakeAttempted = false;
let autoSleepWakeBusy = false;
let manualVoiceStopRequested = false;
let panelVisibility = loadPanelVisibility();

const els = {
  bridgeStatus: document.getElementById('bridgeStatus'),
  warmupPill: document.getElementById('warmupPill'),
  stateLabel: document.getElementById('stateLabel'),
  stateMessage: document.getElementById('stateMessage'),
  stripBridge: document.getElementById('stripBridge'),
  stripVoice: document.getElementById('stripVoice'),
  stripWarmup: document.getElementById('stripWarmup'),
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
  diagnosticsToggle: document.getElementById('diagnosticsToggle'),
  voiceOnceButton: document.getElementById('voiceOnceButton'),
  sleepWakeButton: document.getElementById('sleepWakeButton'),
  stopVoiceButton: document.getElementById('stopVoiceButton'),
  voiceMode: document.getElementById('voiceMode'),
  voiceTranscript: document.getElementById('voiceTranscript'),
  voiceStatus: document.getElementById('voiceStatus'),
  voiceWarmup: document.getElementById('voiceWarmup'),
  autoWakeToggle: document.getElementById('autoWakeToggle'),
  orbFocusButton: document.getElementById('orbFocusButton'),
  panelToggleButtons: Array.from(document.querySelectorAll('[data-panel-toggle]')),
  panelCloseButtons: Array.from(document.querySelectorAll('[data-panel-close]'))
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

function titleCase(value) {
  return readable(value).replace(/\b\w/g, character => character.toUpperCase());
}

function loadPanelVisibility() {
  const defaults = {
    runtime: true,
    voice: true,
    workspace: true,
    conversation: true,
    diagnostics: true
  };
  try {
    const saved = JSON.parse(localStorage.getItem(PANEL_STORAGE_KEY) || '{}');
    return { ...defaults, ...saved };
  } catch (error) {
    return defaults;
  }
}

function savePanelVisibility() {
  localStorage.setItem(PANEL_STORAGE_KEY, JSON.stringify(panelVisibility));
}

function loadAutoSleepWakeEnabled() {
  const saved = localStorage.getItem(AUTO_WAKE_STORAGE_KEY);
  return saved === null ? true : saved === 'true';
}

function saveAutoSleepWakeEnabled() {
  localStorage.setItem(AUTO_WAKE_STORAGE_KEY, String(autoSleepWakeEnabled));
}

function leftRailEmpty() {
  return !panelVisibility.runtime && !panelVisibility.voice && !panelVisibility.workspace;
}

function renderBodyClasses(nextState = lastState.avatar?.state || DEFAULT_STATE.avatar.state) {
  const classes = [`state-${normalizeState(nextState)}`];
  classes.push(diagnosticsOpen ? 'diagnostics-open' : 'diagnostics-collapsed');
  if (orbFocus) classes.push('orb-focus');
  if (leftRailEmpty()) classes.push('left-rail-empty');
  for (const key of PANEL_KEYS) {
    if (!panelVisibility[key]) classes.push(`panel-${key}-hidden`);
  }
  document.body.className = classes.join(' ');
}

function updatePanelControls() {
  for (const button of els.panelToggleButtons) {
    const key = button.dataset.panelToggle;
    const visible = Boolean(panelVisibility[key]);
    button.setAttribute('aria-pressed', String(visible));
    button.classList.toggle('panel-off', !visible);
  }
  if (els.orbFocusButton) {
    els.orbFocusButton.setAttribute('aria-pressed', String(orbFocus));
  }
  if (els.autoWakeToggle) {
    els.autoWakeToggle.setAttribute('aria-pressed', String(autoSleepWakeEnabled));
    els.autoWakeToggle.textContent = `Auto Wake: ${autoSleepWakeEnabled ? 'On' : 'Off'}`;
  }
}

function setVisualState(state, message, label) {
  const next = normalizeState(state);
  renderBodyClasses(next);
  els.stateLabel.textContent = label || titleCase(next);
  els.stateMessage.textContent = message || 'Ready, sir.';
}

function renderVoice(voice) {
  const session = voice || DEFAULT_STATE.voice;
  const running = Boolean(session.running || session.thread_alive);
  const warmed = session.warmup_complete !== false;
  const modeText = running ? `${titleCase(session.mode)} Running` : titleCase(session.mode || 'idle');
  const warmupText = warmed ? 'ready' : (session.warmup_status || 'warming');
  const statusText = session.last_error || session.last_status || (warmed ? 'Ready.' : 'Warming voice systems...');
  els.voiceMode.textContent = modeText;
  els.voiceTranscript.textContent = session.last_transcript || 'none yet';
  els.voiceStatus.textContent = statusText;
  els.voiceWarmup.textContent = warmupText;
  els.warmupPill.textContent = `Voice Warmup: ${warmed ? 'Ready' : 'Warming'}`;
  els.stripVoice.textContent = `voice: ${running ? readable(session.mode) : 'idle'}`;
  els.stripWarmup.textContent = `warmup: ${warmed ? 'ready' : 'warming'}`;
  els.voiceOnceButton.disabled = !warmed || running;
  els.sleepWakeButton.disabled = !warmed || running;
  els.stopVoiceButton.disabled = !running;
}

function chatRoleClass(role) {
  const normalized = normalizeState(role || 'jarvis');
  if (normalized === 'user') return 'user';
  if (normalized === 'heard') return 'heard';
  return 'jarvis';
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
  updatePanelControls();

  const online = app.bridge_status === 'online';
  els.bridgeStatus.textContent = online ? 'Bridge Online' : 'Bridge Offline';
  els.bridgeStatus.title = app.api_url || apiUrl;
  els.stripBridge.textContent = `bridge: ${online ? 'online' : 'offline'}`;
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
    ? chats.map(msg => {
        const role = msg.role || 'jarvis';
        const className = chatRoleClass(role);
        return `<div class="chat-message ${className}"><span class="role">${escapeHtml(role)}</span>${escapeHtml(msg.text || '')}</div>`;
      }).join('')
    : '<div class="chat-message jarvis"><span class="role">jarvis</span>App shell ready. Waiting for the local bridge.</div>';
  els.chatLog.scrollTop = els.chatLog.scrollHeight;

  const events = workspace.events || [];
  els.eventsLog.innerHTML = events.length
    ? events.slice(-30).map(event => `${escapeHtml(event.timestamp || '')} | ${escapeHtml(event.event_type || '')} | ${escapeHtml(event.message || '')}`).join('<br>')
    : 'No events yet.';
  els.eventsLog.scrollTop = els.eventsLog.scrollHeight;

  maybeAutoStartSleepWake(lastState);
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
  manualVoiceStopRequested = false;
  setVisualState('listening', 'Listening for one real microphone turn...', 'Listening');
  await postVoice('/api/voice/once', { speak: true });
  setTimeout(refreshState, 350);
}

async function startSleepWake({ automatic = false } = {}) {
  if (!automatic) {
    manualVoiceStopRequested = false;
    autoSleepWakeAttempted = true;
  }
  setVisualState('sleeping', automatic ? 'Auto sleep/wake is starting. Say the wake phrase when ready.' : 'Starting sleep/wake voice mode...', 'Sleep Mode');
  await postVoice('/api/voice/sleep-wake/start', { max_turns: 0, speak: true });
  setTimeout(refreshState, 350);
}

async function stopVoice() {
  manualVoiceStopRequested = true;
  await postVoice('/api/voice/stop', {});
  setTimeout(refreshState, 350);
}

function maybeAutoStartSleepWake(snapshot) {
  const app = snapshot.app || DEFAULT_STATE.app;
  const voice = snapshot.voice || DEFAULT_STATE.voice;
  const warmed = voice.warmup_complete !== false;
  const running = Boolean(voice.running || voice.thread_alive);
  const mode = normalizeState(voice.mode || 'idle');
  if (!autoSleepWakeEnabled || autoSleepWakeAttempted || autoSleepWakeBusy || manualVoiceStopRequested) return;
  if (app.bridge_status !== 'online' || !warmed || running || mode !== 'idle') return;
  autoSleepWakeAttempted = true;
  autoSleepWakeBusy = true;
  startSleepWake({ automatic: true }).finally(() => {
    autoSleepWakeBusy = false;
  });
}

function toggleDiagnostics() {
  diagnosticsOpen = !diagnosticsOpen;
  els.diagnosticsToggle.textContent = diagnosticsOpen ? 'Hide Diagnostics' : 'Show Diagnostics';
  const avatar = lastState.avatar || DEFAULT_STATE.avatar;
  setVisualState(avatar.state, avatar.message, avatar.label || avatar.profile?.label);
}

function togglePanel(key, visible = undefined) {
  if (!PANEL_KEYS.includes(key)) return;
  panelVisibility[key] = visible === undefined ? !panelVisibility[key] : Boolean(visible);
  if (key === 'diagnostics' && !panelVisibility[key]) diagnosticsOpen = false;
  savePanelVisibility();
  updatePanelControls();
  const avatar = lastState.avatar || DEFAULT_STATE.avatar;
  setVisualState(avatar.state, avatar.message, avatar.label || avatar.profile?.label);
}

function toggleOrbFocus() {
  orbFocus = !orbFocus;
  updatePanelControls();
  const avatar = lastState.avatar || DEFAULT_STATE.avatar;
  setVisualState(avatar.state, avatar.message, avatar.label || avatar.profile?.label);
}

function toggleAutoSleepWake() {
  autoSleepWakeEnabled = !autoSleepWakeEnabled;
  autoSleepWakeAttempted = false;
  manualVoiceStopRequested = false;
  saveAutoSleepWakeEnabled();
  updatePanelControls();
  maybeAutoStartSleepWake(lastState);
}

async function boot() {
  if (window.jarvisNative?.getConfig) {
    const config = await window.jarvisNative.getConfig();
    apiUrl = config.apiUrl || apiUrl;
  }

  els.refreshButton.addEventListener('click', refreshState);
  els.diagnosticsToggle.addEventListener('click', toggleDiagnostics);
  els.voiceOnceButton.addEventListener('click', startVoiceOnce);
  els.sleepWakeButton.addEventListener('click', () => startSleepWake({ automatic: false }));
  els.stopVoiceButton.addEventListener('click', stopVoice);
  if (els.autoWakeToggle) els.autoWakeToggle.addEventListener('click', toggleAutoSleepWake);
  if (els.orbFocusButton) els.orbFocusButton.addEventListener('click', toggleOrbFocus);
  for (const button of els.panelToggleButtons) {
    button.addEventListener('click', () => togglePanel(button.dataset.panelToggle));
  }
  for (const button of els.panelCloseButtons) {
    button.addEventListener('click', () => togglePanel(button.dataset.panelClose, false));
  }
  els.commandForm.addEventListener('submit', event => {
    event.preventDefault();
    const command = els.commandInput.value.trim();
    if (!command) return;
    els.commandInput.value = '';
    sendCommand(command);
  });

  updatePanelControls();
  renderState({
    ...DEFAULT_STATE,
    avatar: { state: 'working', label: 'Initializing Jarvis', message: 'Connecting to the local bridge, warming voice systems, then entering sleep/wake mode...' }
  });
  refreshState();
  setInterval(refreshState, 900);
}

boot();
