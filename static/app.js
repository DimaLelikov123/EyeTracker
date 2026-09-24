// EyeTracker Dashboard Application
let ws = null;
let reconnectTimer = null;
let soundEnabled = true;
let lastAlertSoundTime = 0;
let isCameraPreviewVisible = true;

// Audio Synthesizer for gentle notification chime
const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

function playGentleChime() {
  if (!soundEnabled) return;
  const now = Date.now();
  if (now - lastAlertSoundTime < 15000) return; // Cooldown 15 sec
  lastAlertSoundTime = now;

  try {
    if (audioCtx.state === 'suspended') {
      audioCtx.resume();
    }
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(587.33, audioCtx.currentTime); // D5
    osc.frequency.exponentialRampToValueAtTime(880.00, audioCtx.currentTime + 0.15); // A5

    gain.gain.setValueAtTime(0.001, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.25, audioCtx.currentTime + 0.05);
    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.7);

    osc.connect(gain);
    gain.connect(audioCtx.destination);

    osc.start();
    osc.stop(audioCtx.currentTime + 0.7);
  } catch (e) {
    console.warn("Audio chime error:", e);
  }
}

// Chart Instances
let timelineChart = null;
let activityChart = null;

const timelineData = {
  labels: [],
  datasets: [
    {
      label: 'Частота морганий (BPM)',
      borderColor: '#06b6d4',
      backgroundColor: 'rgba(6, 182, 212, 0.1)',
      borderWidth: 2,
      fill: true,
      tension: 0.35,
      data: []
    },
    {
      label: 'Здоровая норма (15)',
      borderColor: '#10b981',
      borderDash: [5, 5],
      borderWidth: 1.5,
      pointRadius: 0,
      fill: false,
      data: []
    }
  ]
};

const activityData = {
  labels: ['Игры', 'Работа', 'Видео', 'Браузинг', 'Общение', 'Другое'],
  datasets: [{
    label: 'Средний BPM',
    data: [0, 0, 0, 0, 0, 0],
    backgroundColor: [
      'rgba(239, 68, 68, 0.7)',
      'rgba(59, 130, 246, 0.7)',
      'rgba(245, 158, 11, 0.7)',
      'rgba(16, 185, 129, 0.7)',
      'rgba(139, 92, 246, 0.7)',
      'rgba(107, 114, 128, 0.7)'
    ],
    borderRadius: 8
  }]
};

function initCharts() {
  const ctxTimeline = document.getElementById('timelineChart').getContext('2d');
  timelineChart = new Chart(ctxTimeline, {
    type: 'line',
    data: timelineData,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          grid: { color: 'rgba(51, 65, 85, 0.3)' },
          ticks: { color: '#94a3b8', font: { size: 10 } }
        },
        y: {
          min: 0,
          suggestedMax: 25,
          grid: { color: 'rgba(51, 65, 85, 0.3)' },
          ticks: { color: '#94a3b8', font: { size: 10 } }
        }
      },
      plugins: {
        legend: {
          labels: { color: '#cbd5e1', font: { size: 11 } }
        }
      }
    }
  });

  const ctxActivity = document.getElementById('activityChart').getContext('2d');
  activityChart = new Chart(ctxActivity, {
    type: 'bar',
    data: activityData,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: '#94a3b8', font: { size: 11 } }
        },
        y: {
          min: 0,
          suggestedMax: 20,
          grid: { color: 'rgba(51, 65, 85, 0.3)' },
          ticks: { color: '#94a3b8', font: { size: 10 } }
        }
      },
      plugins: {
        legend: { display: false }
      }
    }
  });
}

// Format seconds into MM:SS
function formatTime(totalSeconds) {
  const mins = Math.floor(totalSeconds / 60);
  const secs = totalSeconds % 60;
  return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

// Connect to WebSocket
function connectWebSocket() {
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${proto}//${location.host}/ws`;

  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    console.log('[WS] Connected to EyeTracker');
    updateConnectionBadge(true);
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      handleTelemetry(data);
    } catch (e) {
      console.error('[WS Error]', e);
    }
  };

  ws.onclose = () => {
    console.warn('[WS] Disconnected. Reconnecting in 2s...');
    updateConnectionBadge(false);
    clearTimeout(reconnectTimer);
    reconnectTimer = setTimeout(connectWebSocket, 2000);
  };

  ws.onerror = (err) => {
    console.error('[WS Error]', err);
    ws.close();
  };
}

function updateConnectionBadge(connected) {
  const badge = document.getElementById('conn-badge');
  if (connected) {
    badge.className = "flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
    badge.innerHTML = `<span class="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span><span>Камера активна</span>`;
  } else {
    badge.className = "flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20";
    badge.innerHTML = `<span class="w-2 h-2 rounded-full bg-rose-400"></span><span>Переподключение...</span>`;
  }
}

// Process Real-time Telemetry Frame
function handleTelemetry(data) {
  const { telemetry, activity, alert } = data;

  // 1. Metric: BPM
  const bpmEl = document.getElementById('metric-bpm');
  const bpmBar = document.getElementById('bpm-bar');
  const healthLabel = document.getElementById('health-label');

  bpmEl.textContent = telemetry.bpm;
  healthLabel.textContent = telemetry.health_msg;
  healthLabel.style.color = telemetry.health_color;

  // Bar width (25 BPM is 100%)
  const barPercent = Math.min(100, Math.round((telemetry.bpm / 25) * 100));
  bpmBar.style.width = `${barPercent}%`;
  bpmBar.style.backgroundColor = telemetry.health_color;

  // 2. Metric: Total Blinks & Session
  document.getElementById('metric-total-blinks').textContent = telemetry.total_blinks;
  document.getElementById('metric-avg-bpm').textContent = telemetry.avg_bpm;
  document.getElementById('metric-session-time').textContent = formatTime(telemetry.session_duration_sec);

  // 3. Metric: Time Since Last Blink
  const sinceBlinkEl = document.getElementById('metric-since-blink');
  sinceBlinkEl.textContent = telemetry.seconds_since_blink.toFixed(1);
  if (telemetry.seconds_since_blink >= 12.0) {
    sinceBlinkEl.className = "text-4xl font-extrabold text-red-500 animate-pulse";
  } else if (telemetry.seconds_since_blink >= 8.0) {
    sinceBlinkEl.className = "text-4xl font-extrabold text-amber-400";
  } else {
    sinceBlinkEl.className = "text-4xl font-extrabold text-white";
  }

  // 4. Metric: EAR & State
  document.getElementById('metric-ear').textContent = telemetry.current_ear.toFixed(2);
  document.getElementById('metric-threshold-ear').textContent = telemetry.baseline_ear.toFixed(2);
  const eyeBadge = document.getElementById('eye-state-badge');
  if (telemetry.is_blinking) {
    eyeBadge.textContent = "Моргание";
    eyeBadge.className = "text-xs px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 font-semibold border border-cyan-500/30";
  } else {
    eyeBadge.textContent = "Открыты";
    eyeBadge.className = "text-xs px-2 py-0.5 rounded-full bg-slate-800 text-emerald-400 font-semibold border border-slate-700";
  }

  // 5. Activity Banner
  document.getElementById('activity-icon').textContent = activity.icon;
  document.getElementById('activity-label').textContent = activity.label;
  document.getElementById('activity-label').style.color = activity.color;
  document.getElementById('activity-window-title').textContent = activity.title || "Активное окно не определено";

  // Mode badge
  const modeBadge = document.getElementById('mode-badge');
  if (activity.manual_override) {
    modeBadge.textContent = `Ручной (${activity.manual_override})`;
    modeBadge.className = "text-[11px] px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 font-medium";
  } else {
    modeBadge.textContent = "Авто";
    modeBadge.className = "text-[11px] px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-medium";
  }

  // No face warning overlay
  const noFaceBadge = document.getElementById('no-face-badge');
  if (!telemetry.face_detected) {
    noFaceBadge.classList.remove('hidden');
  } else {
    noFaceBadge.classList.add('hidden');
  }

  // 6. Alerts & Sound
  const alertCard = document.getElementById('alert-card');
  const alertMsg = document.getElementById('alert-message');
  if (alert) {
    alertCard.classList.remove('hidden');
    alertMsg.textContent = alert.message;
    playGentleChime();
  } else {
    alertCard.classList.add('hidden');
  }
}

// Periodic Historical Data Refresh
async function refreshChartsData() {
  try {
    // 1. Timeline
    const resTimeline = await fetch('/api/stats/timeline');
    const dataTimeline = await resTimeline.json();
    if (dataTimeline.timeline && dataTimeline.timeline.length > 0) {
      timelineData.labels = dataTimeline.timeline.map(t => t.time_str);
      timelineData.datasets[0].data = dataTimeline.timeline.map(t => t.bpm);
      timelineData.datasets[1].data = dataTimeline.timeline.map(() => 15);
      timelineChart.update('none');
    }

    // 2. Activity comparison
    const resActs = await fetch('/api/stats/activities');
    const dataActs = await resActs.json();
    if (dataActs.activities) {
      const actMap = {
        'GAMING': 0,
        'WORK': 1,
        'VIDEO': 2,
        'BROWSING': 3,
        'SOCIAL': 4,
        'OTHER': 5
      };
      const values = [0, 0, 0, 0, 0, 0];
      dataActs.activities.forEach(item => {
        const idx = actMap[item.activity];
        if (idx !== undefined) {
          values[idx] = Math.round(item.avg_bpm * 10) / 10;
        }
      });
      activityData.datasets[0].data = values;
      activityChart.update('none');
    }
  } catch (e) {
    console.warn("Chart data refresh failed:", e);
  }
}

// Setup Event Listeners
function setupEvents() {
  // Activity buttons
  document.querySelectorAll('.act-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const act = btn.getAttribute('data-act');
      const target = act === 'AUTO' ? null : act;
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'override_activity', activity: target }));
      }
    });
  });

  // Reset button
  document.getElementById('btn-reset').addEventListener('click', () => {
    if (confirm('Сбросить текущую сессию и счетчик морганий?')) {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'reset_session' }));
      }
      setTimeout(refreshChartsData, 500);
    }
  });

  // Sound toggle button
  const soundBtn = document.getElementById('btn-sound-toggle');
  soundBtn.addEventListener('click', () => {
    soundEnabled = !soundEnabled;
    soundBtn.innerHTML = soundEnabled ? '<i class="fa-solid fa-volume-high"></i>' : '<i class="fa-solid fa-volume-xmark text-slate-500"></i>';
    soundBtn.className = soundEnabled 
      ? "p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-cyan-400 border border-slate-700 transition"
      : "p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-500 border border-slate-700 transition";
  });

  // Toggle Camera View (Privacy Mode)
  const toggleCamBtn = document.getElementById('btn-toggle-camera-view');
  const camStream = document.getElementById('camera-stream');
  const camOverlay = document.getElementById('camera-hidden-overlay');

  toggleCamBtn.addEventListener('click', () => {
    isCameraPreviewVisible = !isCameraPreviewVisible;
    if (isCameraPreviewVisible) {
      camStream.classList.remove('hidden');
      camOverlay.classList.add('hidden');
      toggleCamBtn.innerHTML = '<i class="fa-regular fa-eye-slash mr-1"></i> Скрыть видео';
    } else {
      camStream.classList.add('hidden');
      camOverlay.classList.remove('hidden');
      toggleCamBtn.innerHTML = '<i class="fa-regular fa-eye mr-1"></i> Показать видео';
    }
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: 'toggle_preview' }));
    }
  });

  // Dismiss alert
  document.getElementById('btn-dismiss-alert').addEventListener('click', () => {
    document.getElementById('alert-card').classList.add('hidden');
  });

  // Refresh charts button
  document.getElementById('btn-refresh-stats').addEventListener('click', refreshChartsData);

  // Settings Modal
  const modal = document.getElementById('settings-modal');
  document.getElementById('btn-settings').addEventListener('click', () => {
    modal.classList.remove('hidden');
  });
  document.getElementById('btn-close-settings').addEventListener('click', () => {
    modal.classList.add('hidden');
  });

  const delayInput = document.getElementById('setting-delay');
  const delayVal = document.getElementById('setting-delay-val');
  delayInput.addEventListener('input', (e) => {
    delayVal.textContent = `${e.target.value} с`;
  });

  const bpmInput = document.getElementById('setting-bpm');
  const bpmVal = document.getElementById('setting-bpm-val');
  bpmInput.addEventListener('input', (e) => {
    bpmVal.textContent = e.target.value;
  });

  document.getElementById('btn-save-settings').addEventListener('click', async () => {
    const payload = {
      sound_alerts: document.getElementById('setting-sound').checked,
      blink_delay_threshold: parseFloat(delayInput.value),
      low_bpm_threshold: parseFloat(bpmInput.value),
      rule_20_20_20: document.getElementById('setting-rule').checked
    };
    soundEnabled = payload.sound_alerts;
    await fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    modal.classList.add('hidden');
  });
}

// Initialize on DOM load
window.addEventListener('DOMContentLoaded', () => {
  initCharts();
  setupEvents();
  connectWebSocket();
  refreshChartsData();

  // Refresh charts every 15 seconds
  setInterval(refreshChartsData, 15000);
});
