/**
 * Interactive Vector Circuit Schematic with Integrated Round 3D Push Button
 * Fully dynamic theme adaptation: Renders seamlessly in BOTH Dark & Light Modes
 * - Canvas background dynamically links to CSS variable var(--pcb-bg)
 * - Silk text & copper traces link to CSS theme variables
 * - Prominent Round 3D Push Button on GPIO 14 (Clickable & animates down on click)
 * - ESP32-WROOM-32 with metallic RF shield and gold Wi-Fi antenna
 * - Emerald Green Status LED (GPIO 2) that flashes on contact
 * - Animated electrical current pulses flowing from button into ESP32
 */

function renderCircuitSchematic(containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;

  container.innerHTML = `
    <svg viewBox="0 0 880 300" class="schematic-svg" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <!-- Emerald Glow Filters -->
        <filter id="pcb-glow-emerald" x="-30%" y="-30%" width="160%" height="160%">
          <feGaussianBlur stdDeviation="3.5" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        <filter id="pcb-glow-green" x="-40%" y="-40%" width="180%" height="180%">
          <feGaussianBlur stdDeviation="5.5" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>

        <!-- 3D Tactile Round Button Gradients -->
        <radialGradient id="btnPlungerGrad" cx="35%" cy="35%" r="65%">
          <stop offset="0%" stop-color="#f87171" />
          <stop offset="40%" stop-color="#ef4444" />
          <stop offset="75%" stop-color="#b91c1c" />
          <stop offset="100%" stop-color="#7f1d1d" />
        </radialGradient>

        <radialGradient id="btnBezelGrad" cx="35%" cy="35%" r="70%">
          <stop offset="0%" stop-color="#94a3b8" />
          <stop offset="40%" stop-color="#64748b" />
          <stop offset="85%" stop-color="#334155" />
          <stop offset="100%" stop-color="#1e293b" />
        </radialGradient>

        <!-- RF Shield Can Metal Gradient -->
        <linearGradient id="rfShieldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#64748b" />
          <stop offset="30%" stop-color="#475569" />
          <stop offset="70%" stop-color="#334155" />
          <stop offset="100%" stop-color="#1e293b" />
        </linearGradient>
      </defs>

      <!-- PCB Canvas Background (Dynamic for Light and Dark Modes) -->
      <rect width="100%" height="100%" fill="var(--pcb-bg)" rx="8" />

      <!-- Dot Grid Matrix -->
      <pattern id="pcbGrid" width="20" height="20" patternUnits="userSpaceOnUse">
        <circle cx="2" cy="2" r="1.2" fill="var(--pcb-dots)" />
      </pattern>
      <rect width="100%" height="100%" fill="url(#pcbGrid)" />

      <!-- ================= 1. PROMINENT ROUND TACTILE PUSH BUTTON (LEFT) ================= -->
      <g id="svg-btn-group" transform="translate(115, 145)">
        <!-- Outer Module Silkscreen Boundary -->
        <rect x="-95" y="-120" width="190" height="240" rx="8" fill="var(--pcb-module-bg)" stroke="var(--border)" stroke-width="1.5" />
        
        <text x="0" y="-98" fill="var(--pcb-text-secondary)" font-family="'IBM Plex Mono', monospace" font-size="10.5" font-weight="700" text-anchor="middle">PUSH BUTTON</text>
        <text x="0" y="-84" fill="var(--accent-emerald)" font-family="'IBM Plex Mono', monospace" font-size="8.5" font-weight="600" text-anchor="middle">GPIO 14 (ACTIVE-LOW)</text>

        <!-- Round Steel Bezel Housing -->
        <circle cx="0" cy="8" r="68" fill="url(#btnBezelGrad)" stroke="#475569" stroke-width="2.5" />
        <circle cx="0" cy="8" r="56" fill="var(--pcb-bg)" stroke="var(--border)" stroke-width="2" />

        <!-- 4 Corner Mounting Screws -->
        <circle cx="-50" cy="-42" r="3" fill="#64748b" />
        <circle cx="50" cy="-42" r="3" fill="#64748b" />
        <circle cx="-50" cy="58" r="3" fill="#64748b" />
        <circle cx="50" cy="58" r="3" fill="#64748b" />

        <!-- ROUND 3D RED PLUNGER (CLICKABLE) -->
        <g id="svg-round-button-target" style="cursor: pointer; user-select: none;">
          <!-- Drop Shadow Ring -->
          <circle id="svg-round-btn-shadow" cx="0" cy="11" r="48" fill="#450a0a" opacity="0.8" />
          <!-- Main Round 3D Dome -->
          <circle id="svg-round-btn-cap" cx="0" cy="8" r="46" fill="url(#btnPlungerGrad)" stroke="#991b1b" stroke-width="2" style="transition: all 0.08s ease;" />
          <!-- Inner Concentric Tactile Ring -->
          <circle id="svg-round-btn-ring" cx="0" cy="8" r="26" fill="none" stroke="#fca5a5" stroke-width="1.5" opacity="0.6" />
          <!-- Center Dot -->
          <circle id="svg-round-btn-dot" cx="0" cy="8" r="7" fill="#dc2626" />
        </g>

        <!-- User Hint underneath button -->
        <text x="0" y="94" fill="var(--pcb-text-secondary)" font-family="'IBM Plex Mono', monospace" font-size="9" text-anchor="middle">CLICK OR SPACEBAR</text>
        <text x="0" y="107" fill="var(--pcb-text-dim)" font-family="'IBM Plex Mono', monospace" font-size="7.5" text-anchor="middle">DEBOUNCE: 50ms</text>

        <!-- Solder Pad Output to Trace -->
        <circle cx="95" cy="8" r="3.5" fill="var(--accent-emerald)" />
        <text x="88" y="24" fill="var(--accent-emerald)" font-family="'IBM Plex Mono', monospace" font-size="8.5" font-weight="700">SIG</text>
      </g>

      <!-- ================= 2. PULL-UP RESISTOR & COPPER TRACES ================= -->
      <!-- Main Signal Copper Trace: Button Pin -> ESP32 IO14 Pin -->
      <path id="trace-main" d="M 210 153 L 340 153 L 440 153" fill="none" stroke="var(--pcb-trace)" stroke-width="3" stroke-linecap="round" />
      
      <!-- Branch to 10k Pull-Up Resistor -->
      <path d="M 310 153 L 310 75" fill="none" stroke="var(--pcb-trace)" stroke-width="2.5" />
      
      <!-- 10k Resistor Body & Bands -->
      <rect x="298" y="80" width="24" height="38" rx="3" fill="var(--pcb-module-bg)" stroke="var(--border)" stroke-width="1.5" />
      <line x1="298" y1="88" x2="322" y2="88" stroke="#f59e0b" stroke-width="2" />
      <line x1="298" y1="98" x2="322" y2="98" stroke="#10b981" stroke-width="2" />
      <line x1="298" y1="108" x2="322" y2="108" stroke="#ef4444" stroke-width="2" />
      <text x="330" y="103" fill="var(--pcb-text-secondary)" font-family="'IBM Plex Mono', monospace" font-size="9" font-weight="600">10kΩ</text>

      <!-- +3.3V Power Node -->
      <path d="M 310 80 L 310 45" fill="none" stroke="var(--pcb-trace)" stroke-width="2" />
      <circle cx="310" cy="45" r="3.5" fill="#f59e0b" />
      <text x="310" y="32" fill="#f59e0b" font-family="'IBM Plex Mono', monospace" font-size="9.5" font-weight="700" text-anchor="middle">+3.3V</text>

      <!-- Animated Signal Electron (Emerald pulse on press) -->
      <circle id="schematic-pulse-dot" cx="210" cy="153" r="5" fill="var(--accent-emerald)" opacity="0" filter="url(#pcb-glow-emerald)" />

      <!-- ================= 3. ESP32-WROOM-32 MODULE (CENTER) ================= -->
      <g id="schematic-esp32" transform="translate(440, 30)">
        <!-- Main ESP32 PCB (Dynamic for Light and Dark Modes) -->
        <rect x="0" y="0" width="240" height="235" rx="6" fill="var(--pcb-mcu-bg)" stroke="var(--accent-amber)" stroke-width="1.5" />
        
        <!-- Antenna Keepout Zone (Gold Meander Antenna) -->
        <rect x="15" y="12" width="210" height="36" rx="3" fill="var(--pcb-module-bg)" />
        <path d="M 28 38 L 28 20 L 45 20 L 45 38 L 62 38 L 62 20 L 79 20 L 79 38 L 96 38 L 96 20 L 113 20 L 113 38 L 130 38 L 130 20 L 147 20 L 147 38 L 164 38 L 164 20 L 181 20 L 181 38 L 202 20" fill="none" stroke="var(--accent-amber)" stroke-width="2.5" stroke-linecap="round" />
        <text x="120" y="60" fill="var(--pcb-text-dim)" font-family="'IBM Plex Mono', monospace" font-size="8" text-anchor="middle">2.4GHz Wi-Fi / MQTT QoS 1</text>

        <!-- Nickel RF Metal Shield Can -->
        <rect x="25" y="70" width="190" height="145" rx="4" fill="url(#rfShieldGrad)" stroke="#475569" stroke-width="1.5" />
        
        <!-- Silkscreen on Shield -->
        <text x="120" y="106" fill="#e2e8f0" font-family="'IBM Plex Mono', monospace" font-size="13" font-weight="700" text-anchor="middle">ESP32</text>
        <text x="120" y="124" fill="#94a3b8" font-family="'IBM Plex Mono', monospace" font-size="10" text-anchor="middle">WROOM-32D</text>
        <text x="120" y="142" fill="#cbd5e1" font-family="'IBM Plex Mono', monospace" font-size="8" text-anchor="middle">Tensilica Xtensa Dual-Core</text>
        <text x="120" y="160" fill="#94a3b8" font-family="'IBM Plex Mono', monospace" font-size="7.5" text-anchor="middle">FCC ID: 2AC7Z-ESPWROOM32</text>
        <text x="120" y="180" fill="var(--accent-emerald)" font-family="'IBM Plex Mono', monospace" font-size="8" text-anchor="middle">FreeRTOS Ingest Node</text>

        <!-- Left Solder Pins -->
        <text x="5" y="126" fill="var(--accent-emerald)" font-family="'IBM Plex Mono', monospace" font-size="9" font-weight="700">IO14</text>
        <circle cx="0" cy="123" r="3.5" fill="var(--accent-emerald)" />

        <text x="5" y="162" fill="var(--pcb-text-dim)" font-family="'IBM Plex Mono', monospace" font-size="8">GND</text>
        <circle cx="0" cy="159" r="3" fill="var(--pcb-text-dim)" />

        <!-- Right Solder Pins -->
        <text x="235" y="126" fill="var(--accent-emerald)" font-family="'IBM Plex Mono', monospace" font-size="9" font-weight="700" text-anchor="end">IO2 (LED)</text>
        <circle cx="240" cy="123" r="3.5" fill="var(--accent-emerald)" />

        <text x="235" y="162" fill="var(--accent-amber)" font-family="'IBM Plex Mono', monospace" font-size="8.5" text-anchor="end">Wi-Fi (MQTT)</text>
        <circle cx="240" cy="159" r="3" fill="var(--accent-amber)" />
      </g>

      <!-- ================= 4. EMERALD STATUS LED (RIGHT) ================= -->
      <!-- Copper Trace to Status LED -->
      <path d="M 680 153 L 755 153" fill="none" stroke="var(--pcb-trace)" stroke-width="3" stroke-linecap="round" />
      <circle id="schematic-led-pulse-dot" cx="680" cy="153" r="4.5" fill="var(--accent-emerald)" opacity="0" filter="url(#pcb-glow-emerald)" />

      <!-- Status LED Module -->
      <g id="schematic-led" transform="translate(755, 118)">
        <rect x="0" y="0" width="70" height="70" rx="8" fill="var(--pcb-module-bg)" stroke="var(--border)" stroke-width="1.5" />
        <circle id="svg-led-bezel" cx="35" cy="35" r="22" fill="var(--pcb-bg)" stroke="#475569" stroke-width="2" />
        <circle id="svg-led-lens" cx="35" cy="35" r="14" fill="var(--pcb-module-bg)" stroke="var(--border)" stroke-width="2" />
        <circle cx="35" cy="35" r="6" fill="#475569" />
        <text x="35" y="62" fill="var(--pcb-text-secondary)" font-family="'IBM Plex Mono', monospace" font-size="7.5" text-anchor="middle">STATUS LED</text>
      </g>

      <!-- Bottom Status Strip Labels -->
      <g transform="translate(115, 275)">
        <text x="0" y="14" fill="var(--pcb-text-dim)" font-family="'IBM Plex Mono', monospace" font-size="8.5" text-anchor="middle">TACTILE INPUT</text>
      </g>
      <g transform="translate(560, 275)">
        <text x="0" y="14" fill="var(--accent-emerald)" font-family="'IBM Plex Mono', monospace" font-size="8.5" text-anchor="middle">MICROCONTROLLER</text>
      </g>
      <g transform="translate(790, 275)">
        <text x="0" y="14" fill="var(--pcb-text-dim)" font-family="'IBM Plex Mono', monospace" font-size="8.5" text-anchor="middle">FEEDBACK</text>
      </g>
    </svg>
  `;

  // Attach click listener to the integrated Round Button inside the SVG
  const roundBtnTarget = document.getElementById('svg-round-button-target');
  if (roundBtnTarget) {
    roundBtnTarget.addEventListener('click', () => {
      if (window.pressPhysicalButton) {
        window.pressPhysicalButton(1);
      }
    });
  }
}

function pulseCircuit() {
  const p1 = document.getElementById('schematic-pulse-dot');
  const p2 = document.getElementById('schematic-led-pulse-dot');
  const ledLens = document.getElementById('svg-led-lens');
  const btnCap = document.getElementById('svg-round-btn-cap');
  const btnShadow = document.getElementById('svg-round-btn-shadow');
  const btnRing = document.getElementById('svg-round-btn-ring');
  const btnDot = document.getElementById('svg-round-btn-dot');

  // Depress the 3D round button visually
  if (btnCap) {
    btnCap.setAttribute('cy', '11');
    btnCap.setAttribute('r', '43');
    if (btnRing) {
      btnRing.setAttribute('cy', '11');
      btnRing.setAttribute('r', '24');
    }
    if (btnDot) btnDot.setAttribute('cy', '11');
    if (btnShadow) btnShadow.setAttribute('opacity', '0.4');

    setTimeout(() => {
      btnCap.setAttribute('cy', '8');
      btnCap.setAttribute('r', '46');
      if (btnRing) {
        btnRing.setAttribute('cy', '8');
        btnRing.setAttribute('r', '26');
      }
      if (btnDot) btnDot.setAttribute('cy', '8');
      if (btnShadow) btnShadow.setAttribute('opacity', '0.8');
    }, 110);
  }

  // Animate pulse from Round Button (x=210) to ESP32 IO14 (x=440)
  if (p1) {
    p1.setAttribute('opacity', '1');
    p1.setAttribute('cx', '210');
    let x = 210;
    const interval1 = setInterval(() => {
      x += 18;
      p1.setAttribute('cx', x);
      if (x >= 440) {
        clearInterval(interval1);
        p1.setAttribute('opacity', '0');
        triggerLedPulse();
      }
    }, 12);
  }

  function triggerLedPulse() {
    if (p2) {
      p2.setAttribute('opacity', '1');
      p2.setAttribute('cx', '680');
      let x2 = 680;
      const interval2 = setInterval(() => {
        x2 += 12;
        p2.setAttribute('cx', x2);
        if (x2 >= 755) {
          clearInterval(interval2);
          p2.setAttribute('opacity', '0');
          flashLed();
        }
      }, 12);
    }
  }

  function flashLed() {
    if (ledLens) {
      ledLens.setAttribute('fill', '#10b981');
      ledLens.setAttribute('stroke', '#a7f3d0');
      ledLens.setAttribute('filter', 'url(#pcb-glow-green)');
      setTimeout(() => {
        ledLens.setAttribute('fill', 'var(--pcb-module-bg)');
        ledLens.setAttribute('stroke', 'var(--border)');
        ledLens.removeAttribute('filter');
      }, 200);
    }
  }
}

window.renderCircuitSchematic = renderCircuitSchematic;
window.pulseCircuit = pulseCircuit;
