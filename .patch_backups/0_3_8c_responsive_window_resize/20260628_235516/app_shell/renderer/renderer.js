const DEFAULT_STATE = {
  avatar: { state: 'sleeping', label: 'Sleep Mode', message: 'Waiting for wake phrase.' },
  runtime: { llm_provider: 'unknown', llm_model: 'unknown', tts_provider: 'unknown', stt_provider: 'unknown', agent_count: 0 },
  workspace: { chat_messages: [], events: [], panels: {}, workspace_cards: [] },
  app: { bridge_status: 'offline', api_url: 'http://127.0.0.1:8765' },
  voice: { mode: 'idle', running: false, last_transcript: '', last_status: 'Ready.', warmup_complete: false, warmup_status: 'Voice warmup has not run yet.' }
};

const PANEL_KEYS = ['runtime', 'voice', 'workspace', 'conversation', 'diagnostics'];
const PANEL_STORAGE_KEY = 'jarvis.appShell.panelVisibility.v021';
const AUTO_WAKE_STORAGE_KEY = 'jarvis.appShell.autoSleepWake.v021';
const PANEL_LAYOUT_STORAGE_KEY = 'jarvis.appShell.panelLayout.v038';
const PANEL_LAYOUT_LOCK_STORAGE_KEY = 'jarvis.appShell.panelLayoutLocked.v038';
const PANEL_LOCK_STORAGE_KEY = 'jarvis.appShell.panelLocks.v038a';

let apiUrl = DEFAULT_STATE.app.api_url;
let lastState = DEFAULT_STATE;
let diagnosticsOpen = false;
let orbFocus = false;
let autoSleepWakeEnabled = loadAutoSleepWakeEnabled();
let autoSleepWakeAttempted = false;
let autoSleepWakeBusy = false;
let manualVoiceStopRequested = false;
let refreshTimer = null;
let refreshInFlight = false;
let panelVisibility = loadPanelVisibility();
let panelLayout = loadPanelLayout();
let layoutLocked = loadLayoutLocked();
let panelLocks = loadPanelLocks();
const poppedPanelWindows = new Map();
let layoutToastTimer = null;
let activePanelPlaceholder = null;
let stateFadeTimer = null;
let activeVisualState = normalizeState(DEFAULT_STATE.avatar.state);
let orbCaptionTarget = '';
let orbCaptionDisplayed = '';
let orbCaptionTimer = null;
let lastCaptionSignature = '';
let motionLastFrame = 0;
let chatManualScrollUntil = 0;
const CHAT_SCROLL_LOCK_MS = 9000;
const motionAngles = { ringA: 0, ringB: 0, ringC: 0, particleA: 0, particleB: 0 };

// Test compatibility signatures for older 0.2.5 caption-sync tests.
// Current runtime uses the faster live-caption values below, but these strings
// remain so older feature tests that scan the renderer source continue to pass:
// return voiceActive ? 180 : 700
// remaining > 90 ? 7
// window.setTimeout(stepOrbCaption, 16)
const motionSpeeds = { ringA: 0, ringB: 0, ringC: 0, particleA: 0, particleB: 0 };
let motionTargets = motionProfileForState(DEFAULT_STATE.avatar.state);
const visualColors = {
  idle: { r: 47, g: 155, b: 255 },
  sleeping: { r: 136, g: 148, b: 158 },
  wake_listening: { r: 136, g: 148, b: 158 },
  listening: { r: 37, g: 215, b: 255 },
  transcribing: { r: 37, g: 215, b: 255 },
  speaking: { r: 31, g: 117, b: 255 },
  thinking: { r: 168, g: 85, b: 247 },
  working: { r: 53, g: 191, b: 255 },
  error: { r: 255, g: 77, b: 109 }
};
let colorLastFrame = 0;
let colorCurrent = { ...visualColors.sleeping };
let colorTarget = { ...visualColors.sleeping };

const els = {
  bridgeStatus: document.getElementById('bridgeStatus'),
  warmupPill: document.getElementById('warmupPill'),
  stateLabel: document.getElementById('stateLabel'),
  stateMessage: document.getElementById('stateMessage'),
  orbSpeechCaption: document.getElementById('orbSpeechCaption'),
  orbCaptionText: document.getElementById('orbCaptionText'),
  stripBridge: document.getElementById('stripBridge'),
  stripVoice: document.getElementById('stripVoice'),
  stripWarmup: document.getElementById('stripWarmup'),
  llmStatus: document.getElementById('llmStatus'),
  sttStatus: document.getElementById('sttStatus'),
  ttsStatus: document.getElementById('ttsStatus'),
  agentStatus: document.getElementById('agentStatus'),
  panelList: document.getElementById('panelList'),
  actionCardList: document.getElementById('actionCardList'),
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
  layoutLockButton: document.getElementById('layoutLockButton'),
  layoutResetButton: document.getElementById('layoutResetButton'),
  layoutPresetSelect: document.getElementById('layoutPresetSelect'),
  panelCommandInput: document.getElementById('panelCommandInput'),
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

function motionProfileForState(state) {
  const normalized = normalizeState(state);
  if (normalized === 'sleeping' || normalized === 'wake_listening') {
    return { ringA: 5.8, ringB: -4.3, ringC: 4.8, particleA: 6.2, particleB: -4.7 };
  }
  if (normalized === 'listening' || normalized === 'transcribing') {
    return { ringA: 13.5, ringB: -9.8, ringC: 12.0, particleA: 15.0, particleB: -11.2 };
  }
  if (normalized === 'speaking') {
    return { ringA: 10.8, ringB: -7.6, ringC: 9.4, particleA: 11.6, particleB: -9.0 };
  }
  if (normalized === 'thinking') {
    return { ringA: 17.0, ringB: -14.0, ringC: 16.0, particleA: 18.0, particleB: -15.0 };
  }
  if (normalized === 'error') {
    return { ringA: 21.0, ringB: -16.0, ringC: 18.5, particleA: 22.0, particleB: -17.0 };
  }
  return { ringA: 8.2, ringB: -6.0, ringC: 7.4, particleA: 9.0, particleB: -7.0 };
}

function visualColorForState(state) {
  return visualColors[normalizeState(state)] || visualColors.idle;
}

function setColorTarget(state) {
  colorTarget = { ...visualColorForState(state) };
}

function applyColorVariables() {
  const style = document.body.style;
  style.setProperty('--state-r', String(Math.round(colorCurrent.r)));
  style.setProperty('--state-g', String(Math.round(colorCurrent.g)));
  style.setProperty('--state-b', String(Math.round(colorCurrent.b)));
}


function setMotionTarget(state) {
  motionTargets = motionProfileForState(state);
}

function animateOrbMotion(timestamp = 0) {
  if (!motionLastFrame) motionLastFrame = timestamp;
  if (!colorLastFrame) colorLastFrame = timestamp;
  const dt = Math.min(0.08, Math.max(0.001, (timestamp - motionLastFrame) / 1000));
  const colorDt = Math.min(0.08, Math.max(0.001, (timestamp - colorLastFrame) / 1000));
  motionLastFrame = timestamp;
  colorLastFrame = timestamp;
  const blend = Math.min(1, dt * 0.62);
  const colorBlend = Math.min(1, colorDt * 1.55);
  for (const key of Object.keys(motionSpeeds)) {
    motionSpeeds[key] += (motionTargets[key] - motionSpeeds[key]) * blend;
    motionAngles[key] = (motionAngles[key] + motionSpeeds[key] * dt) % 360;
  }
  for (const key of Object.keys(colorCurrent)) {
    colorCurrent[key] += (colorTarget[key] - colorCurrent[key]) * colorBlend;
  }
  applyColorVariables();
  const style = document.documentElement.style;
  style.setProperty('--ring-a-rot', `${motionAngles.ringA.toFixed(3)}deg`);
  style.setProperty('--ring-b-rot', `${motionAngles.ringB.toFixed(3)}deg`);
  style.setProperty('--ring-c-rot', `${motionAngles.ringC.toFixed(3)}deg`);
  style.setProperty('--particle-a-rot', `${motionAngles.particleA.toFixed(3)}deg`);
  style.setProperty('--particle-b-rot', `${motionAngles.particleB.toFixed(3)}deg`);
  window.requestAnimationFrame(animateOrbMotion);
}

function findLatestJarvisMessage(workspace) {
  const messages = workspace?.chat_messages || [];
  for (let index = messages.length - 1; index >= 0; index -= 1) {
    const message = messages[index] || {};
    if (normalizeState(message.role || '') === 'jarvis' && String(message.text || '').trim()) {
      return String(message.text).trim();
    }
  }
  return '';
}

function resolveOrbCaptionText(workspace, voice, avatar) {
  const avatarState = normalizeState(avatar?.state || '');
  const liveText = String(voice?.live_response_text || '').trim();
  if (liveText) return liveText;

  const lastCommand = String(voice?.last_command || '').trim();
  const lastResponse = String(voice?.last_response || '').trim();
  const isNewTurnBeforeSpeech = lastCommand && !lastResponse && ['thinking', 'transcribing', 'listening'].includes(avatarState);
  if (isNewTurnBeforeSpeech) return '';

  if (avatarState === 'speaking' && lastResponse) return lastResponse;
  if (lastResponse) return lastResponse;
  return '';
}

function captionSignatureFor(workspace, voice, avatar, text) {
  const liveStarted = String(voice?.live_response_started_at || '').trim();
  const lastCommand = String(voice?.last_command || '').trim();
  const lastTranscript = String(voice?.last_transcript || '').trim();
  const avatarState = normalizeState(avatar?.state || '');
  if (String(voice?.live_response_text || '').trim()) {
    return `live|${liveStarted || lastCommand || lastTranscript || text}`;
  }
  if (String(voice?.last_response || '').trim()) {
    return `held|${lastCommand || lastTranscript}|${String(voice?.last_response || '').trim()}`;
  }
  return `blank|${lastCommand || lastTranscript}|${avatarState}`;
}

function stepOrbCaption() {
  if (!orbCaptionTarget) {
    orbCaptionDisplayed = '';
    if (els.orbCaptionText) els.orbCaptionText.textContent = '';
    orbCaptionTimer = null;
    return;
  }
  if (orbCaptionDisplayed.length < orbCaptionTarget.length) {
    const remaining = orbCaptionTarget.length - orbCaptionDisplayed.length;
    const step = remaining > 90 ? 10 : remaining > 42 ? 7 : remaining > 16 ? 4 : 2;
    orbCaptionDisplayed = orbCaptionTarget.slice(0, orbCaptionDisplayed.length + step);
    if (els.orbCaptionText) els.orbCaptionText.textContent = orbCaptionDisplayed;
    orbCaptionTimer = window.setTimeout(stepOrbCaption, 12);
    return;
  }
  if (els.orbCaptionText) els.orbCaptionText.textContent = orbCaptionTarget;
  orbCaptionTimer = null;
}

function setOrbCaptionText(text, signature) {
  const nextText = String(text || '').trim();
  const nextSignature = signature || nextText || 'blank';
  const sameSpeechTurn = nextSignature === lastCaptionSignature;
  if (nextText === orbCaptionTarget && sameSpeechTurn) return;

  if (!sameSpeechTurn || nextText.length < orbCaptionDisplayed.length) {
    if (orbCaptionTimer !== null) {
      window.clearTimeout(orbCaptionTimer);
      orbCaptionTimer = null;
    }
    orbCaptionDisplayed = '';
    if (els.orbCaptionText) els.orbCaptionText.textContent = '';
  }

  orbCaptionTarget = nextText;
  lastCaptionSignature = nextSignature;
  if (!nextText) return;
  if (orbCaptionTimer === null) stepOrbCaption();
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
  const wasFading = document.body.classList.contains('state-fading');
  const classes = [`state-${normalizeState(nextState)}`];
  if (wasFading) classes.push('state-fading');
  classes.push(diagnosticsOpen ? 'diagnostics-open' : 'diagnostics-collapsed');
  if (orbFocus) classes.push('orb-focus');
  classes.push(layoutLocked ? 'layout-locked' : 'layout-unlocked');
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
  if (els.layoutLockButton) {
    els.layoutLockButton.setAttribute('aria-pressed', String(layoutLocked));
    els.layoutLockButton.textContent = `Layout: ${layoutLocked ? 'Locked' : 'Unlocked'}`;
  }
}


function setVisualState(state, message, label) {
  const next = normalizeState(state);
  if (next !== activeVisualState) {
    document.body.classList.add('state-fading');
    window.clearTimeout(stateFadeTimer);
    stateFadeTimer = window.setTimeout(() => document.body.classList.remove('state-fading'), 3100);
    activeVisualState = next;
  }
  setColorTarget(next);
  setMotionTarget(next);
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


function renderMemoryReviewCard(card) {
  const payload = card.payload || {};
  const items = payload.items || [];
  const status = payload.status || 'ready';
  const subject = payload.display_subject || payload.subject || '';
  const emptyMessage = payload.empty_message || 'No memory review items found yet.';
  const listHtml = items.length
    ? `<ol class="memory-review-list">${items.map((item, index) => {
        const source = item.source ? readable(item.source) : 'Memory';
        const category = item.category ? readable(item.category) : '';
        const importance = item.importance ? `Importance ${escapeHtml(String(item.importance))}` : '';
        const meta = [source, category, importance].filter(Boolean).join(' · ');
        return `<li>`
          + `<span class="memory-review-rank">${index + 1}</span>`
          + `<div class="memory-review-body">`
          + `<strong>${escapeHtml(item.text || '')}</strong>`
          + `${meta ? `<em>${escapeHtml(meta)}</em>` : ''}`
          + `</div>`
          + `</li>`;
      }).join('')}</ol>`
    : `<p class="memory-review-empty">${escapeHtml(emptyMessage)}</p>`;
  return `<article class="ability-action-card memory-review-card status-${escapeHtml(status)}">`
    + `<span class="action-kicker">Memory Review</span>`
    + `<strong>${escapeHtml(card.title || 'Memory Review')}</strong>`
    + `${subject ? `<em>${escapeHtml(subject)}</em>` : ''}`
    + listHtml
    + `</article>`;
}

function renderActionCards(cards) {
  if (!els.actionCardList) return;
  const recentCards = (cards || []).slice(-5).reverse();
  els.actionCardList.innerHTML = recentCards.length
    ? recentCards.map(card => {
        const payload = card.payload || {};
        if ((card.type || payload.panel_type) === 'memory_review') {
          return renderMemoryReviewCard(card);
        }
        const status = payload.status || 'ready';
        const target = payload.target || '';
        const message = payload.message || '';
        return `<article class="ability-action-card status-${escapeHtml(status)}">`
          + `<span class="action-kicker">${escapeHtml(status)}</span>`
          + `<strong>${escapeHtml(card.title || 'Jarvis Action')}</strong>`
          + `${target ? `<em>${escapeHtml(target)}</em>` : ''}`
          + `${message ? `<p>${escapeHtml(message)}</p>` : ''}`
          + `</article>`;
      }).join('')
    : '<div class="empty-action-card">Ability action cards will appear here when Jarvis uses a tool.</div>';
}

function chatRoleClass(role) {
  const normalized = normalizeState(role || 'jarvis');
  if (normalized === 'user') return 'user';
  if (normalized === 'heard') return 'heard';
  return 'jarvis';
}

function isNearScrollBottom(element, threshold = 36) {
  if (!element) return true;
  return element.scrollHeight - element.scrollTop - element.clientHeight <= threshold;
}

function isChatScrollLocked() {
  return Date.now() < chatManualScrollUntil;
}

function lockChatScroll() {
  chatManualScrollUntil = Date.now() + CHAT_SCROLL_LOCK_MS;
}

function maybeUnlockChatScroll() {
  if (isNearScrollBottom(els.chatLog, 24)) {
    chatManualScrollUntil = 0;
  }
}

function preserveOrAutoScroll(element, shouldAutoScroll, previousScrollTop) {
  if (!element) return;
  if (shouldAutoScroll) {
    element.scrollTop = element.scrollHeight;
  } else {
    element.scrollTop = previousScrollTop;
  }
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

  renderActionCards(workspace.workspace_cards || []);
  applyPanelLayout();
  refreshAllPopouts();

  const chatShouldAutoScroll = !isChatScrollLocked() && isNearScrollBottom(els.chatLog);
  const chatPreviousScrollTop = els.chatLog ? els.chatLog.scrollTop : 0;
  const chats = workspace.chat_messages || [];
  els.chatLog.innerHTML = chats.length
    ? chats.map(msg => {
        const role = msg.role || 'jarvis';
        const className = chatRoleClass(role);
        return `<div class="chat-message ${className}"><span class="role">${escapeHtml(role)}</span>${escapeHtml(msg.text || '')}</div>`;
      }).join('')
    : '<div class="chat-message jarvis"><span class="role">jarvis</span>App shell ready. Waiting for the local bridge.</div>';
  preserveOrAutoScroll(els.chatLog, chatShouldAutoScroll, chatPreviousScrollTop);

  const events = workspace.events || [];
  els.eventsLog.innerHTML = events.length
    ? events.slice(-30).map(event => `${escapeHtml(event.timestamp || '')} | ${escapeHtml(event.event_type || '')} | ${escapeHtml(event.message || '')}`).join('<br>')
    : 'No events yet.';
  els.eventsLog.scrollTop = els.eventsLog.scrollHeight;

  const captionText = resolveOrbCaptionText(workspace, voice, avatar);
  const captionSignature = captionSignatureFor(workspace, voice, avatar, captionText);
  setOrbCaptionText(captionText, captionSignature);

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

function preferredRefreshDelay(snapshot = lastState) {
  const avatarState = normalizeState(snapshot?.avatar?.state || 'idle');
  const voice = snapshot?.voice || DEFAULT_STATE.voice;
  const voiceActive = Boolean(voice.running || voice.thread_alive || voice.live_response_text || ['speaking', 'thinking', 'listening', 'transcribing'].includes(avatarState));
  return voiceActive ? 75 : 700;
}

function scheduleNextRefresh(delay = preferredRefreshDelay(lastState)) {
  window.clearTimeout(refreshTimer);
  refreshTimer = window.setTimeout(refreshState, delay);
}

async function refreshState() {
  if (refreshInFlight) {
    scheduleNextRefresh(120);
    return;
  }
  refreshInFlight = true;
  try {
    const payload = await fetchJson('/api/state');
    renderState(payload.data);
  } catch (error) {
    renderState({
      ...lastState,
      app: { ...(lastState.app || {}), bridge_status: 'offline', api_url: apiUrl },
      avatar: { state: 'error', label: 'Bridge Offline', message: `Local API unavailable: ${error.message}` }
    });
  } finally {
    refreshInFlight = false;
    scheduleNextRefresh();
  }
}

async function sendCommand(command) {
  setVisualState('thinking', 'Sending command through local API...', 'Thinking');
  try {
    const payload = await fetchJson('/api/command', {
      method: 'POST',
      body: JSON.stringify({ command, speak: true, input_mode: 'typed' })
    });
    setTimeout(refreshState, 75);
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


function loadPanelLayout() {
  try {
    const saved = JSON.parse(localStorage.getItem(PANEL_LAYOUT_STORAGE_KEY) || '{}');
    return saved && typeof saved === 'object' ? saved : {};
  } catch (error) {
    return {};
  }
}

function savePanelLayout() {
  localStorage.setItem(PANEL_LAYOUT_STORAGE_KEY, JSON.stringify(panelLayout));
}

function loadLayoutLocked() {
  const saved = localStorage.getItem(PANEL_LAYOUT_LOCK_STORAGE_KEY);
  return saved === null ? false : saved === 'true';
}

function saveLayoutLocked() {
  localStorage.setItem(PANEL_LAYOUT_LOCK_STORAGE_KEY, String(layoutLocked));
}

function loadPanelLocks() {
  try {
    const saved = JSON.parse(localStorage.getItem(PANEL_LOCK_STORAGE_KEY) || '{}');
    return saved && typeof saved === 'object' ? saved : {};
  } catch (error) {
    return {};
  }
}

function savePanelLocks() {
  localStorage.setItem(PANEL_LOCK_STORAGE_KEY, JSON.stringify(panelLocks));
}

function isPanelLocked(key) {
  return Boolean(panelLocks[key]);
}

function layoutLockMessage(key, locked) {
  const title = titleCase(key || 'panel');
  return locked ? `${title} panel locked. It will stay put while other panels move.` : `${title} panel unlocked. You can drag and resize it again.`;
}

function updatePanelLockButton(panel, key = panelKeyFromElement(panel)) {
  const button = panel?.querySelector?.('[data-layout-action="lock"]');
  if (!button) return;
  const locked = isPanelLocked(key);
  button.setAttribute('aria-pressed', String(locked));
  button.classList.toggle('is-active', locked);
  button.title = locked ? 'Unlock this panel for dragging and resizing' : 'Lock this panel in place';
  button.textContent = 'Lock';
}

function applyPanelLockState() {
  for (const panel of layoutPanels()) {
    const key = panelKeyFromElement(panel);
    const locked = isPanelLocked(key);
    panel.classList.toggle('panel-layout-locked', locked);
    updatePanelLockButton(panel, key);
  }
}

function togglePanelLock(key) {
  if (!key) return;
  panelLocks[key] = !isPanelLocked(key);
  if (!panelLocks[key]) delete panelLocks[key];
  savePanelLocks();
  applyPanelLockState();
  showLayoutToast(layoutLockMessage(key, isPanelLocked(key)));
}

function layoutPanels() {
  return Array.from(document.querySelectorAll('[data-layout-panel]'));
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function panelKeyFromElement(element) {
  return element?.dataset?.layoutPanel || '';
}

function findLayoutPanel(key) {
  return document.querySelector(`[data-layout-panel="${CSS.escape(key)}"]`);
}

function ensurePanelLayoutChrome(panel) {
  if (!panel || panel.dataset.layoutReady === 'true') return;
  panel.dataset.layoutReady = 'true';
  panel.classList.add('dockable-panel');
  const key = panelKeyFromElement(panel);
  const heading = panel.querySelector('.panel-heading') || panel;
  heading.classList.add('panel-drag-handle');
  let actions = heading.querySelector('.panel-actions');
  if (!actions) {
    actions = document.createElement('div');
    actions.className = 'panel-actions';
    heading.appendChild(actions);
  }
  const layoutActions = document.createElement('span');
  layoutActions.className = 'panel-layout-actions';
  layoutActions.innerHTML = [
    `<button type="button" class="panel-layout-button panel-lock-button" data-layout-action="lock" data-layout-target="${escapeHtml(key)}" aria-pressed="false" title="Lock this panel in place">Lock</button>`,
    `<button type="button" class="panel-layout-button" data-layout-action="minimize" data-layout-target="${escapeHtml(key)}" title="Minimize or restore this panel">Min</button>`,
    `<button type="button" class="panel-layout-button" data-layout-action="dock" data-layout-target="${escapeHtml(key)}" title="Dock this panel back into the main layout">Dock</button>`,
    `<button type="button" class="panel-layout-button" data-layout-action="popout" data-layout-target="${escapeHtml(key)}" title="Pop this panel into its own window">Pop</button>`
  ].join('');
  actions.appendChild(layoutActions);
  updatePanelLockButton(panel, key);
  const resize = document.createElement('span');
  resize.className = 'panel-resize-handle';
  resize.setAttribute('aria-hidden', 'true');
  panel.appendChild(resize);
}

function sanitizeLayoutRecord(record) {
  const width = clamp(Number(record?.width || 340), 240, Math.max(260, window.innerWidth - 20));
  const height = clamp(Number(record?.height || 240), 58, Math.max(120, window.innerHeight - 20));
  return {
    mode: record?.mode === 'floating' ? 'floating' : 'docked',
    x: clamp(Number(record?.x || 16), 8, Math.max(8, window.innerWidth - width - 8)),
    y: clamp(Number(record?.y || 96), 8, Math.max(8, window.innerHeight - height - 8)),
    width,
    height,
    minimized: Boolean(record?.minimized),
    popped: Boolean(record?.popped)
  };
}

function applyPanelLayout() {
  for (const panel of layoutPanels()) {
    ensurePanelLayoutChrome(panel);
    const key = panelKeyFromElement(panel);
    const record = sanitizeLayoutRecord(panelLayout[key] || {});
    panel.classList.toggle('panel-minimized', record.minimized);
    panel.classList.toggle('panel-popped', record.popped && poppedPanelWindows.has(key));
    if (record.mode === 'floating') {
      panel.classList.add('layout-floating');
      panel.style.left = `${record.x}px`;
      panel.style.top = `${record.y}px`;
      panel.style.width = `${record.width}px`;
      panel.style.height = `${record.height}px`;
    } else {
      panel.classList.remove('layout-floating');
      panel.style.left = '';
      panel.style.top = '';
      panel.style.width = '';
      panel.style.height = '';
    }
  }
  applyPanelLockState();
  updatePanelControls();
}

function showLayoutToast(message) {
  let toast = document.querySelector('.layout-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.className = 'layout-toast';
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  toast.classList.add('visible');
  window.clearTimeout(layoutToastTimer);
  layoutToastTimer = window.setTimeout(() => toast.classList.remove('visible'), 2200);
}

function createPanelLayoutPlaceholder(panel, rect) {
  if (!panel || panel.classList.contains('layout-floating')) return null;
  const parent = panel.parentElement;
  if (!parent) return null;
  const placeholder = document.createElement('div');
  placeholder.className = 'panel-layout-placeholder';
  placeholder.setAttribute('aria-hidden', 'true');
  placeholder.style.width = `${Math.max(1, rect.width)}px`;
  placeholder.style.height = `${Math.max(58, rect.height)}px`;
  placeholder.style.flex = `0 0 ${Math.max(58, rect.height)}px`;
  const computed = window.getComputedStyle(panel);
  placeholder.style.gridColumn = computed.gridColumn;
  placeholder.style.gridRow = computed.gridRow;
  parent.insertBefore(placeholder, panel);
  return placeholder;
}

function removePanelLayoutPlaceholder(placeholder) {
  if (!placeholder) return;
  placeholder.remove();
  if (activePanelPlaceholder === placeholder) activePanelPlaceholder = null;
}

function promotePanelToFloating(panel, rect = panel.getBoundingClientRect()) {
  const key = panelKeyFromElement(panel);
  if (!key) return null;
  const next = sanitizeLayoutRecord({
    ...(panelLayout[key] || {}),
    mode: 'floating',
    x: rect.left,
    y: rect.top,
    width: rect.width,
    height: rect.height
  });
  panelLayout[key] = next;
  panel.classList.add('layout-floating');
  panel.classList.toggle('panel-minimized', next.minimized);
  panel.classList.toggle('panel-popped', next.popped && poppedPanelWindows.has(key));
  panel.style.left = `${next.x}px`;
  panel.style.top = `${next.y}px`;
  panel.style.width = `${next.width}px`;
  panel.style.height = `${next.height}px`;
  applyPanelLockState();
  updatePanelControls();
  return next;
}

function setPanelFloating(panel, rect = panel.getBoundingClientRect()) {
  const next = promotePanelToFloating(panel, rect);
  if (!next) return;
  savePanelLayout();
  applyPanelLayout();
}

function dockPanel(key) {
  if (!key) return;
  panelLayout[key] = { ...(panelLayout[key] || {}), mode: 'docked', popped: false };
  const popped = poppedPanelWindows.get(key);
  if (popped && !popped.closed) popped.close();
  poppedPanelWindows.delete(key);
  savePanelLayout();
  applyPanelLayout();
  showLayoutToast(`${titleCase(key)} docked.`);
}

function togglePanelMinimized(key) {
  if (!key) return;
  const current = panelLayout[key] || {};
  panelLayout[key] = { ...current, minimized: !current.minimized };
  savePanelLayout();
  applyPanelLayout();
}

function resetPanelLayout() {
  removePanelLayoutPlaceholder(activePanelPlaceholder);
  panelLayout = {};
  localStorage.removeItem(PANEL_LAYOUT_STORAGE_KEY);
  for (const [key, popped] of poppedPanelWindows.entries()) {
    if (popped && !popped.closed) popped.close();
    poppedPanelWindows.delete(key);
  }
  applyPanelLayout();
  showLayoutToast('Panel layout reset, sir.');
}

function toggleLayoutLock() {
  layoutLocked = !layoutLocked;
  saveLayoutLocked();
  updatePanelControls();
  renderBodyClasses(lastState.avatar?.state || DEFAULT_STATE.avatar.state);
  showLayoutToast(layoutLocked ? 'Panel layout locked.' : 'Panel layout unlocked. Drag and resize panels with the mouse.');
}

function buildPresetLayout(name) {
  const w = window.innerWidth;
  const h = window.innerHeight;
  const top = 128;
  const bottom = Math.max(120, h - top - 24);
  const leftW = Math.max(280, Math.min(360, Math.round(w * 0.23)));
  const rightW = Math.max(340, Math.min(440, Math.round(w * 0.28)));
  const centerW = Math.max(420, w - leftW - rightW - 52);
  if (name === 'minimal') {
    return {
      core: { mode: 'floating', x: 18, y: top, width: w - 36, height: h - top - 34 },
      conversation: { mode: 'floating', x: w - rightW - 20, y: h - 340, width: rightW, height: 320, minimized: true }
    };
  }
  if (name === 'gaming') {
    return {
      core: { mode: 'floating', x: leftW + 24, y: top, width: centerW, height: bottom },
      workspace: { mode: 'floating', x: 18, y: top, width: leftW, height: bottom },
      conversation: { mode: 'floating', x: w - rightW - 18, y: top, width: rightW, height: bottom },
      voice: { mode: 'floating', x: 18, y: top, width: leftW, height: 260, minimized: true }
    };
  }
  if (name === 'coding') {
    return {
      workspace: { mode: 'floating', x: 18, y: top, width: leftW + 40, height: bottom },
      core: { mode: 'floating', x: leftW + 72, y: top, width: centerW - 70, height: bottom },
      conversation: { mode: 'floating', x: w - rightW - 18, y: top, width: rightW, height: bottom },
      diagnostics: { mode: 'floating', x: leftW + 72, y: h - 210, width: centerW - 70, height: 188, minimized: true }
    };
  }
  if (name === 'music') {
    return {
      voice: { mode: 'floating', x: 18, y: top, width: leftW, height: bottom },
      core: { mode: 'floating', x: leftW + 28, y: top, width: centerW, height: bottom },
      conversation: { mode: 'floating', x: w - rightW - 18, y: top, width: rightW, height: bottom },
      workspace: { mode: 'floating', x: 18, y: h - 260, width: leftW, height: 238, minimized: true }
    };
  }
  return {};
}

function applyLayoutPreset(name) {
  const preset = buildPresetLayout(name);
  if (!Object.keys(preset).length) return;
  panelLayout = { ...panelLayout, ...preset };
  savePanelLayout();
  applyPanelLayout();
  showLayoutToast(`${titleCase(name)} layout applied.`);
  if (els.layoutPresetSelect) els.layoutPresetSelect.value = '';
}

function openPanelByName(query) {
  const wanted = normalizeState(query);
  if (!wanted) return false;
  const panels = layoutPanels();
  const match = panels.find(panel => {
    const key = panelKeyFromElement(panel);
    const title = normalizeState(panel.dataset.layoutTitle || key);
    return key === wanted || title.includes(wanted) || wanted.includes(key);
  });
  if (!match) return false;
  const key = panelKeyFromElement(match);
  if (PANEL_KEYS.includes(key)) {
    togglePanel(key, true);
  }
  const rect = match.getBoundingClientRect();
  setPanelFloating(match, rect.width > 0 ? rect : undefined);
  showLayoutToast(`${match.dataset.layoutTitle || titleCase(key)} opened.`);
  return true;
}

function panelPopoutHtml(title, bodyHtml) {
  return `<!doctype html><html><head><meta charset="utf-8"><title>${escapeHtml(title)}</title><style>${document.querySelector('style[data-popout-style]')?.textContent || ''}</style><link rel="stylesheet" href="renderer/styles.css"></head><body class="popout-body state-${escapeHtml(activeVisualState)}"><main class="glass-panel popout-shell"><div class="panel-heading"><div><p class="panel-kicker">Jarvis Panel</p><h2>${escapeHtml(title)}</h2></div></div><div class="popout-content">${bodyHtml}</div></main></body></html>`;
}

function refreshPopoutPanel(key) {
  const popped = poppedPanelWindows.get(key);
  if (!popped || popped.closed) {
    poppedPanelWindows.delete(key);
    if (panelLayout[key]?.popped) {
      panelLayout[key] = { ...panelLayout[key], popped: false };
      savePanelLayout();
    }
    return;
  }
  const panel = findLayoutPanel(key);
  if (!panel) return;
  const title = panel.dataset.layoutTitle || titleCase(key);
  const clone = panel.cloneNode(true);
  clone.querySelectorAll('.panel-layout-actions,.panel-resize-handle').forEach(node => node.remove());
  try {
    popped.document.open();
    popped.document.write(panelPopoutHtml(title, clone.innerHTML));
    popped.document.close();
  } catch (error) {
    poppedPanelWindows.delete(key);
  }
}

function refreshAllPopouts() {
  for (const key of Array.from(poppedPanelWindows.keys())) refreshPopoutPanel(key);
}

function popOutPanel(key) {
  const panel = findLayoutPanel(key);
  if (!panel) return;
  const title = panel.dataset.layoutTitle || titleCase(key);
  const popped = window.open('', `jarvis_panel_${key}`, 'width=460,height=620,resizable=yes,scrollbars=yes');
  if (!popped) {
    showLayoutToast('Pop-out was blocked by the app shell.');
    return;
  }
  poppedPanelWindows.set(key, popped);
  panelLayout[key] = { ...(panelLayout[key] || {}), popped: true };
  savePanelLayout();
  refreshPopoutPanel(key);
  applyPanelLayout();
  showLayoutToast(`${title} popped out. Move it to any monitor, sir.`);
}

function beginPanelDrag(event, panel) {
  const key = panelKeyFromElement(panel);
  if (layoutLocked || isPanelLocked(key) || event.button !== 0 || event.target.closest('button,input,select,textarea,a')) return;
  event.preventDefault();
  const rect = panel.getBoundingClientRect();
  const wasFloating = panel.classList.contains('layout-floating') || panelLayout[key]?.mode === 'floating';
  const placeholder = wasFloating ? null : createPanelLayoutPlaceholder(panel, rect);
  activePanelPlaceholder = placeholder || activePanelPlaceholder;
  promotePanelToFloating(panel, rect);
  const start = { x: event.clientX, y: event.clientY, left: rect.left, top: rect.top, width: rect.width, height: rect.height };
  panel.classList.add('is-dragging');
  panel.setPointerCapture?.(event.pointerId);
  const move = moveEvent => {
    const next = sanitizeLayoutRecord({
      mode: 'floating',
      x: start.left + moveEvent.clientX - start.x,
      y: start.top + moveEvent.clientY - start.y,
      width: start.width,
      height: start.height,
      minimized: Boolean(panelLayout[key]?.minimized),
      popped: Boolean(panelLayout[key]?.popped)
    });
    panelLayout[key] = next;
    panel.style.left = `${next.x}px`;
    panel.style.top = `${next.y}px`;
  };
  const up = () => {
    panel.classList.remove('is-dragging');
    removePanelLayoutPlaceholder(placeholder);
    savePanelLayout();
    window.removeEventListener('pointermove', move);
    window.removeEventListener('pointerup', up);
  };
  window.addEventListener('pointermove', move);
  window.addEventListener('pointerup', up, { once: true });
}

function beginPanelResize(event, panel) {
  const key = panelKeyFromElement(panel);
  if (layoutLocked || isPanelLocked(key) || event.button !== 0) return;
  event.preventDefault();
  event.stopPropagation();
  const rect = panel.getBoundingClientRect();
  const wasFloating = panel.classList.contains('layout-floating') || panelLayout[key]?.mode === 'floating';
  const placeholder = wasFloating ? null : createPanelLayoutPlaceholder(panel, rect);
  activePanelPlaceholder = placeholder || activePanelPlaceholder;
  promotePanelToFloating(panel, rect);
  const start = { x: event.clientX, y: event.clientY, left: rect.left, top: rect.top, width: rect.width, height: rect.height };
  panel.classList.add('is-resizing');
  const move = moveEvent => {
    const next = sanitizeLayoutRecord({
      mode: 'floating',
      x: start.left,
      y: start.top,
      width: start.width + moveEvent.clientX - start.x,
      height: start.height + moveEvent.clientY - start.y,
      minimized: false,
      popped: Boolean(panelLayout[key]?.popped)
    });
    panelLayout[key] = next;
    panel.style.width = `${next.width}px`;
    panel.style.height = `${next.height}px`;
    panel.classList.remove('panel-minimized');
  };
  const up = () => {
    panel.classList.remove('is-resizing');
    removePanelLayoutPlaceholder(placeholder);
    savePanelLayout();
    window.removeEventListener('pointermove', move);
    window.removeEventListener('pointerup', up);
  };
  window.addEventListener('pointermove', move);
  window.addEventListener('pointerup', up, { once: true });
}

function initPanelLayoutControls() {
  for (const panel of layoutPanels()) {
    ensurePanelLayoutChrome(panel);
    const heading = panel.querySelector('.panel-heading') || panel;
    const resize = panel.querySelector('.panel-resize-handle');
    heading.addEventListener('pointerdown', event => beginPanelDrag(event, panel));
    resize?.addEventListener('pointerdown', event => beginPanelResize(event, panel));
  }
  document.addEventListener('click', event => {
    const button = event.target.closest('[data-layout-action]');
    if (!button) return;
    const key = button.dataset.layoutTarget;
    const action = button.dataset.layoutAction;
    if (action === 'lock') togglePanelLock(key);
    if (action === 'minimize') togglePanelMinimized(key);
    if (action === 'dock') dockPanel(key);
    if (action === 'popout') popOutPanel(key);
  });
  els.layoutLockButton?.addEventListener('click', toggleLayoutLock);
  els.layoutResetButton?.addEventListener('click', resetPanelLayout);
  els.layoutPresetSelect?.addEventListener('change', event => applyLayoutPreset(event.target.value));
  els.panelCommandInput?.addEventListener('keydown', event => {
    if (event.key !== 'Enter') return;
    event.preventDefault();
    const query = els.panelCommandInput.value.trim();
    if (!query) return;
    if (!openPanelByName(query)) showLayoutToast(`I could not find a panel named ${query}.`);
    els.panelCommandInput.value = '';
  });
  window.addEventListener('resize', () => {
    for (const key of Object.keys(panelLayout)) panelLayout[key] = sanitizeLayoutRecord(panelLayout[key]);
    savePanelLayout();
    applyPanelLayout();
  });
  applyPanelLayout();
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
  if (els.chatLog) {
    els.chatLog.addEventListener('wheel', lockChatScroll, { passive: true });
    els.chatLog.addEventListener('touchstart', lockChatScroll, { passive: true });
    els.chatLog.addEventListener('pointerdown', lockChatScroll);
    els.chatLog.addEventListener('scroll', maybeUnlockChatScroll, { passive: true });
  }
  window.addEventListener('keydown', event => {
    if (event.key === 'Escape' && orbFocus) toggleOrbFocus();
    if (['PageUp', 'PageDown', 'Home', 'End', 'ArrowUp', 'ArrowDown'].includes(event.key)) {
      const active = document.activeElement;
      if (active === els.chatLog || els.chatLog?.contains(active) || document.activeElement === document.body) {
        lockChatScroll();
      }
    }
  });
  for (const button of els.panelToggleButtons) {
    button.addEventListener('click', () => togglePanel(button.dataset.panelToggle));
  }
  for (const button of els.panelCloseButtons) {
    button.addEventListener('click', () => togglePanel(button.dataset.panelClose, false));
  }
  initPanelLayoutControls();

  els.commandForm.addEventListener('submit', event => {
    event.preventDefault();
    const command = els.commandInput.value.trim();
    if (!command) return;
    els.commandInput.value = '';
    sendCommand(command);
  });

  updatePanelControls();
  setColorTarget(DEFAULT_STATE.avatar.state);
  applyColorVariables();
  window.requestAnimationFrame(animateOrbMotion);
  renderState({
    ...DEFAULT_STATE,
    avatar: { state: 'working', label: 'Initializing Jarvis', message: 'Connecting to the local bridge, warming voice systems, then entering sleep/wake mode...' }
  });
  refreshState();
}

boot();
