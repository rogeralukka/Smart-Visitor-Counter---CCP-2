/**
 * Smart Visitor Counter - Frontend Client Logic
 * Minimalist 2D monochrome controls, dynamic theme adaptation, SSE real-time stream
 * Supports BOTH Localhost FastAPI server AND 100% Serverless AWS Cloud hosting (S3 + Lambda Function URL)
 */

let visitorChart = null;

// Determine environment: Localhost vs AWS S3 Static Website
const IS_LOCAL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const LAMBDA_ENDPOINT = 'https://twhjx4fahvna4mpy5aeahvz4nm0mpgsr.lambda-url.us-east-1.on.aws/';

// Natural number formatting (0, 1, 2, 14, 1,250)
function formatCounter(num) {
  if (num === null || num === undefined) return '0';
  return Number(num).toLocaleString('en-US');
}

// Update all UI elements from state
function updateDashboardState(state) {
  if (!state) return;

  // Digital Counter
  const counterEl = document.getElementById('digital-counter');
  if (counterEl) {
    counterEl.textContent = formatCounter(state.total_visitors !== undefined ? state.total_visitors : 0);
    counterEl.classList.add('pulse');
    setTimeout(() => counterEl.classList.remove('pulse'), 120);
  }

  // Submetrics
  const todayEl = document.getElementById('today-visitors');
  if (todayEl) todayEl.textContent = formatCounter(state.today_visitors !== undefined ? state.today_visitors : 0);

  const rateEl = document.getElementById('current-rate');
  if (rateEl) rateEl.textContent = `${formatCounter(state.current_hour_visitors || 0)} / hr`;

  const peakEl = document.getElementById('peak-hour-stat');
  if (peakEl) {
    if (state.peak_count && state.peak_count > 0) {
      peakEl.textContent = `${state.peak_hour} (${state.peak_count})`;
    } else {
      peakEl.textContent = '--';
    }
  }

  const lastTimeEl = document.getElementById('last-entry-time');
  if (lastTimeEl) {
    if (state.total_visitors > 0 && state.last_visit_timestamp) {
      const d = new Date(state.last_visit_timestamp);
      lastTimeEl.textContent = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } else {
      lastTimeEl.textContent = '--:--:--';
    }
  }

  // Update Chart
  if (state.hourly_distribution && visitorChart) {
    const labels = Object.keys(state.hourly_distribution);
    const data = Object.values(state.hourly_distribution);
    visitorChart.data.labels = labels;
    visitorChart.data.datasets[0].data = data;
    visitorChart.update('none');
  }

  // Update Table
  if (state.recent_events) {
    updateRecentEventsTable(state.recent_events);
  }
}

function updateRecentEventsTable(events) {
  const tbody = document.getElementById('log-table-tbody');
  if (!tbody) return;

  tbody.innerHTML = '';
  if (!events || events.length === 0) {
    const tr = document.createElement('tr');
    tr.innerHTML = '<td colspan="4" style="text-align:center; color:var(--text-muted); padding:1rem;">No visitors recorded yet. Click the round button in the simulation or press Spacebar.</td>';
    tbody.appendChild(tr);
    return;
  }

  events.slice(0, 10).forEach(ev => {
    const tr = document.createElement('tr');
    const timeStr = new Date(ev.timestamp).toLocaleTimeString();
    tr.innerHTML = `
      <td class="badge-visitor-num">#${ev.visitor_number}</td>
      <td>${timeStr}</td>
      <td>${ev.device_id || 'ESP32-NODE-01'}</td>
      <td style="color:var(--accent-emerald); font-size:0.7rem;">${ev.verification_hash || 'SHA256'}</td>
    `;
    tbody.appendChild(tr);
  });
}

// Button press action
async function pressPhysicalButton(delta = 1) {
  if (window.pulseCircuit) {
    window.pulseCircuit();
  }

  try {
    if (IS_LOCAL) {
      const res = await fetch('/api/button/press', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ count_delta: delta })
      });
      const data = await res.json();
      if (data.body && data.body.current_state) {
        updateDashboardState(data.body.current_state);
      }
    } else {
      // Direct AWS Lambda Function URL invocation from S3
      const res = await fetch(LAMBDA_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ count_delta: delta })
      });
      const data = await res.json();
      if (data.current_state) {
        updateDashboardState(data.current_state);
      }
    }
  } catch (err) {
    console.error('Failed to dispatch button press:', err);
  }
}

// Reset counter
async function resetCounter() {
  if (!confirm('Reset visitor counter?')) return;
  try {
    if (IS_LOCAL) {
      const res = await fetch('/api/visitor/reset', { method: 'POST' });
      const data = await res.json();
      if (data.state) {
        updateDashboardState(data.state);
      }
    } else {
      const res = await fetch(LAMBDA_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'reset' })
      });
      const state = await fetchCloudState();
      if (state) updateDashboardState(state);
    }
  } catch (err) {
    console.error('Reset failed:', err);
  }
}

// Fetch cloud state
async function fetchCloudState() {
  try {
    const url = IS_LOCAL ? '/api/visitor/state' : LAMBDA_ENDPOINT;
    const res = await fetch(url);
    return await res.json();
  } catch (e) {
    console.error('Failed fetching state:', e);
    return null;
  }
}

// Initialize Chart.js
function initChart() {
  const ctx = document.getElementById('visitorHourlyChart');
  if (!ctx) return;

  const isLight = document.documentElement.getAttribute('data-theme') === 'light';
  const gridColor = isLight ? 'rgba(0, 0, 0, 0.06)' : 'rgba(241, 243, 245, 0.06)';
  const textColor = isLight ? '#626a78' : '#9ba3af';

  visitorChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: [],
      datasets: [{
        label: "Footfall",
        data: [],
        backgroundColor: 'rgba(16, 185, 129, 0.45)',
        borderColor: '#10b981',
        borderWidth: 1.5,
        borderRadius: 3,
        hoverBackgroundColor: '#059669'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: {
          grid: { color: gridColor },
          ticks: { color: textColor, font: { size: 9, family: "'IBM Plex Mono', monospace" } }
        },
        y: {
          beginAtZero: true,
          grid: { color: gridColor },
          ticks: { color: textColor, font: { size: 9, family: "'IBM Plex Mono', monospace" }, stepSize: 1 }
        }
      }
    }
  });
}

function updateThemeToggleIcon(theme) {
  const iconMoon = document.getElementById('theme-icon-moon');
  const iconSun = document.getElementById('theme-icon-sun');
  if (iconMoon && iconSun) {
    if (theme === 'dark') {
      iconMoon.style.display = 'block';
      iconSun.style.display = 'none';
    } else {
      iconMoon.style.display = 'none';
      iconSun.style.display = 'block';
    }
  }
}

// Server-Sent Events setup (Localhost) & Cloud Polling (S3)
function initLiveSync() {
  if (IS_LOCAL) {
    const eventSource = new EventSource('/api/stream');

    eventSource.addEventListener('init', (e) => {
      try {
        const payload = JSON.parse(e.data);
        if (payload.state) updateDashboardState(payload.state);
      } catch (err) {}
    });

    eventSource.addEventListener('visitor_counted', (e) => {
      try {
        const payload = JSON.parse(e.data);
        if (payload.current_state) updateDashboardState(payload.current_state);
        if (window.pulseCircuit) window.pulseCircuit();
      } catch (err) {}
    });

    eventSource.addEventListener('visitor_reset', (e) => {
      try {
        const payload = JSON.parse(e.data);
        updateDashboardState(payload);
      } catch (err) {}
    });
  } else {
    // S3 Cloud Hosting: Poll Lambda URL every 3.5s for real-time multiplayer updates
    setInterval(async () => {
      const state = await fetchCloudState();
      if (state) updateDashboardState(state);
    }, 3500);
  }
}

document.addEventListener('DOMContentLoaded', async () => {
  if (window.renderCircuitSchematic) {
    window.renderCircuitSchematic('circuit-schematic-mount');
  }

  initChart();

  // Load initial state
  const initialState = await fetchCloudState();
  if (initialState) {
    updateDashboardState(initialState);
  }

  initLiveSync();

  // Top Nav Reset Button
  const navResetBtn = document.getElementById('nav-reset-btn');
  if (navResetBtn) {
    navResetBtn.addEventListener('click', resetCounter);
  }

  // Keyboard shortcut Spacebar
  window.addEventListener('keydown', (e) => {
    if (e.code === 'Space' && e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
      e.preventDefault();
      pressPhysicalButton(1);
    }
  });

  // Theme Toggle Button
  const themeBtn = document.getElementById('theme-toggle-btn');
  if (themeBtn) {
    const savedTheme = localStorage.getItem('svc-theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeToggleIcon(savedTheme);

    themeBtn.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme') || 'dark';
      const next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('svc-theme', next);
      updateThemeToggleIcon(next);

      if (window.renderCircuitSchematic) {
        window.renderCircuitSchematic('circuit-schematic-mount');
      }

      if (visitorChart) {
        const gridColor = next === 'light' ? 'rgba(0, 0, 0, 0.06)' : 'rgba(241, 243, 245, 0.06)';
        const textColor = next === 'light' ? '#626a78' : '#9ba3af';
        visitorChart.options.scales.x.grid.color = gridColor;
        visitorChart.options.scales.x.ticks.color = textColor;
        visitorChart.options.scales.y.grid.color = gridColor;
        visitorChart.options.scales.y.ticks.color = textColor;
        visitorChart.update();
      }
    });
  }
});
