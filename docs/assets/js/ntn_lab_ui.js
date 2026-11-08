/**
 * ORBIT-INTEL 6G — Interactive Live NTN Laboratory UI Controller
 * Manages 60 FPS Canvas rendering, scenario controls, AI vs Baseline switching,
 * subcarrier grid visualization, power budget tracking, Gymnasium PPO traces,
 * side-by-side metric updates, and 14-step conference presentation mode.
 */

document.addEventListener('DOMContentLoaded', () => {
  if (typeof NTNLabEngine === 'undefined') {
    console.warn('NTNLabEngine not loaded.');
    return;
  }

  const { NTNSimulationEngine, SCENARIO_PROFILES, ZONE_RANGES } = NTNLabEngine;

  // Canvas & Engine References
  const canvas = document.getElementById('ntnLabCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  let engine = new NTNSimulationEngine({
    numUsers: 36,
    numSatellites: 4,
    numChannels: 16,
    trafficLoad: 'medium',
    userMobility: 'medium',
    isAiEnabled: true
  });

  let isRunning = true;
  let speedMultiplier = 1;
  let selectedEntity = null; // { type: 'sat' | 'user', id: string }

  // Baseline comparison engine (runs in parallel with identical seed for fair comparison)
  let baselineEngine = new NTNSimulationEngine({
    numUsers: 36,
    numSatellites: 4,
    numChannels: 16,
    trafficLoad: 'medium',
    userMobility: 'medium',
    isAiEnabled: false
  });

  // UI Element References
  const btnPlay = document.getElementById('btnLabTogglePlay');
  const btnStep = document.getElementById('btnLabStep');
  const btnReset = document.getElementById('btnLabReset');
  const btnExport = document.getElementById('btnLabExportCsv');
  const speedSelect = document.getElementById('labSpeedSelect');
  const btnModeAi = document.getElementById('btnLabModeAi');
  const btnModeBaseline = document.getElementById('btnLabModeBaseline');

  // Popup Inspector
  const popup = document.getElementById('entityInspectorPopup');
  const popupTitle = document.getElementById('inspectorEntityName');
  const popupBadge = document.getElementById('inspectorEntityBadge');
  const popupBody = document.getElementById('inspectorEntityBody');
  const popupClose = document.getElementById('inspectorPopupClose');

  // Decision Panels Elements
  const subcarrierGridEl = document.getElementById('subcarrierGridDisplay');
  const powerMeterFill = document.getElementById('powerMeterFill');
  const powerUsedText = document.getElementById('powerUsedText');
  const decisionFeedEl = document.getElementById('decisionFeedList');
  const gymTraceEl = document.getElementById('gymTraceContent');
  const assocSummaryEl = document.getElementById('assocSummaryText');

  // Side-by-Side Comparison Readouts
  const compThroughputAi = document.getElementById('compThroughputAi');
  const compThroughputBase = document.getElementById('compThroughputBase');
  const compThroughputDelta = document.getElementById('compThroughputDelta');

  const compSinrAi = document.getElementById('compSinrAi');
  const compSinrBase = document.getElementById('compSinrBase');
  const compSinrDelta = document.getElementById('compSinrDelta');

  const compLossAi = document.getElementById('compLossAi');
  const compLossBase = document.getElementById('compLossBase');
  const compLossDelta = document.getElementById('compLossDelta');

  const compLatencyAi = document.getElementById('compLatencyAi');
  const compLatencyBase = document.getElementById('compLatencyBase');
  const compLatencyDelta = document.getElementById('compLatencyDelta');

  // Sliders
  const sliderSats = document.getElementById('sliderLabSats');
  const sliderUsers = document.getElementById('sliderLabUsers');
  const sliderChannels = document.getElementById('sliderLabChannels');
  const sliderPower = document.getElementById('sliderLabPower');
  const sliderRain = document.getElementById('sliderLabRain');

  const valSats = document.getElementById('valLabSats');
  const valUsers = document.getElementById('valLabUsers');
  const valChannels = document.getElementById('valLabChannels');
  const valPower = document.getElementById('valLabPower');
  const valRain = document.getElementById('valLabRain');

  // Canvas High-DPI Resizing
  function resizeCanvas() {
    const rect = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
  }
  window.addEventListener('resize', resizeCanvas);
  resizeCanvas();

  // Draw Simulation Scene on Canvas
  function drawCanvas() {
    const rect = canvas.getBoundingClientRect();
    const width = rect.width;
    const height = rect.height;

    ctx.clearRect(0, 0, width, height);

    // 1. Atmosphere & Space Sky Gradient
    const skyGrad = ctx.createLinearGradient(0, 0, 0, height);
    skyGrad.addColorStop(0, '#040914');   // Deep Space
    skyGrad.addColorStop(0.35, '#0a1630'); // Upper Stratosphere
    skyGrad.addColorStop(0.75, '#13284f'); // Troposphere
    skyGrad.addColorStop(1, '#061024');    // Surface ground line
    ctx.fillStyle = skyGrad;
    ctx.fillRect(0, 0, width, height);

    // 2. Orbital Track Guideline Dashes
    ctx.strokeStyle = 'rgba(0, 240, 255, 0.15)';
    ctx.lineWidth = 1;
    ctx.setLineDash([6, 6]);
    [14, 22].forEach(yPct => {
      ctx.beginPath();
      ctx.moveTo(0, (yPct / 100) * height);
      ctx.lineTo(width, (yPct / 100) * height);
      ctx.stroke();
    });
    ctx.setLineDash([]);

    // 3. Terrain Geographical Zones
    const groundY = height * 0.82;
    const zones = [
      { key: 'urban', name: 'Urban City', minX: 0.05, maxX: 0.28, color: 'rgba(59, 130, 246, 0.15)' },
      { key: 'rural', name: 'Rural Agri', minX: 0.28, maxX: 0.48, color: 'rgba(16, 185, 129, 0.15)' },
      { key: 'maritime', name: 'Maritime Ocean', minX: 0.48, maxX: 0.68, color: 'rgba(6, 182, 212, 0.2)' },
      { key: 'remote', name: 'Remote Mtn', minX: 0.68, maxX: 0.84, color: 'rgba(139, 92, 246, 0.15)' },
      { key: 'disaster', name: 'Disaster Relief', minX: 0.84, maxX: 0.95, color: 'rgba(239, 68, 68, 0.2)' }
    ];

    zones.forEach(z => {
      ctx.fillStyle = z.color;
      ctx.fillRect(z.minX * width, groundY, (z.maxX - z.minX) * width, height - groundY);

      ctx.strokeStyle = 'rgba(255, 255, 255, 0.15)';
      ctx.beginPath();
      ctx.moveTo(z.minX * width, groundY);
      ctx.lineTo(z.minX * width, height);
      ctx.stroke();

      ctx.fillStyle = '#94a3b8';
      ctx.font = '10px "Inter", sans-serif';
      ctx.fillText(z.name, z.minX * width + 6, height - 10);
    });

    const satellites = engine.getSatellites();
    const users = engine.getUsers();
    const aerials = engine.getAerialPlatforms();
    const gNBs = engine.getBaseStations();

    // 4. Satellite Spot-Beam Cones
    satellites.forEach(sat => {
      const sx = (sat.x / 100) * width;
      const sy = (sat.y / 100) * height;
      const r = (sat.coverageRadius / 100) * width;

      const coneGrad = ctx.createRadialGradient(sx, sy, 8, sx, groundY, r);
      coneGrad.addColorStop(0, `${sat.beamColor}33`);
      coneGrad.addColorStop(0.7, `${sat.beamColor}12`);
      coneGrad.addColorStop(1, `${sat.beamColor}00`);

      ctx.fillStyle = coneGrad;
      ctx.beginPath();
      ctx.moveTo(sx, sy);
      ctx.lineTo(sx - r, groundY);
      ctx.lineTo(sx + r, groundY);
      ctx.closePath();
      ctx.fill();

      // Beam ground footprint ellipse
      ctx.strokeStyle = `${sat.beamColor}55`;
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.ellipse(sx, groundY + 6, r, 9, 0, 0, Math.PI * 2);
      ctx.stroke();
    });

    // 5. Active Communication Beams (Satellites -> Users)
    users.forEach(user => {
      if (user.connectedSatelliteId) {
        const sat = satellites.find(s => s.id === user.connectedSatelliteId);
        if (sat) {
          const sx = (sat.x / 100) * width;
          const sy = (sat.y / 100) * height;
          const ux = (user.x / 100) * width;
          const uy = (user.y / 100) * height;

          const isAi = engine.getParams().isAiEnabled;
          ctx.strokeStyle = isAi ? '#00f0ff' : '#f97316';
          ctx.lineWidth = user.priority === 'URLLC' ? 2.5 : 1.2;
          ctx.globalAlpha = user.handoverState === 'handoff_active' ? 0.9 : 0.55;

          if (user.handoverState === 'handoff_active') {
            ctx.setLineDash([4, 4]); // Pulsing dashed stroke for handover in progress
          } else {
            ctx.setLineDash([]);
          }

          ctx.beginPath();
          ctx.moveTo(sx, sy);
          ctx.lineTo(ux, uy);
          ctx.stroke();
          ctx.setLineDash([]);
          ctx.globalAlpha = 1.0;
        }
      }
    });

    // 6. Draw Aerial Platforms (HAPS & UAVs)
    aerials.forEach(a => {
      const ax = (a.x / 100) * width;
      const ay = (a.y / 100) * height;

      ctx.fillStyle = a.type === 'HAPS' ? '#c4b5fd' : '#60a5fa';
      ctx.beginPath();
      ctx.arc(ax, ay, 5, 0, Math.PI * 2);
      ctx.fill();

      ctx.fillStyle = '#cbd5e1';
      ctx.font = '9px "JetBrains Mono", monospace';
      ctx.fillText(a.name.split(' ')[0], ax + 7, ay + 3);
    });

    // 7. Draw Ground Base Stations
    gNBs.forEach(gnb => {
      const gx = (gnb.x / 100) * width;
      const gy = (gnb.y / 100) * height;

      ctx.fillStyle = '#34d399';
      ctx.beginPath();
      ctx.arc(gx, gy, 4, 0, Math.PI * 2);
      ctx.fill();
    });

    // 8. Draw Satellites
    satellites.forEach(sat => {
      const sx = (sat.x / 100) * width;
      const sy = (sat.y / 100) * height;

      // Solar Panel wings
      ctx.fillStyle = '#38bdf8';
      ctx.fillRect(sx - 16, sy - 3, 10, 6);
      ctx.fillRect(sx + 6, sy - 3, 10, 6);

      // Satellite Bus Body
      ctx.fillStyle = '#ffffff';
      ctx.beginPath();
      ctx.arc(sx, sy, 5, 0, Math.PI * 2);
      ctx.fill();

      // Selection Ring
      if (selectedEntity && selectedEntity.type === 'sat' && selectedEntity.id === sat.id) {
        ctx.strokeStyle = '#00f0ff';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(sx, sy, 12, 0, Math.PI * 2);
        ctx.stroke();
      }

      // Name & Doppler Tag
      ctx.fillStyle = '#00f0ff';
      ctx.font = '10px "JetBrains Mono", monospace';
      ctx.fillText(sat.name, sx - 20, sy - 10);

      ctx.fillStyle = '#94a3b8';
      ctx.font = '8px "JetBrains Mono", monospace';
      ctx.fillText(`${sat.dopplerShiftKhz > 0 ? '+' : ''}${sat.dopplerShiftKhz}kHz`, sx - 16, sy + 15);
    });

    // 9. Draw Ground Users
    users.forEach(user => {
      const ux = (user.x / 100) * width;
      const uy = (user.y / 100) * height;

      const isConnected = user.connectedSatelliteId !== null;
      let color = '#94a3b8';
      if (!isConnected) color = '#ef4444'; // Unassigned
      else if (user.priority === 'URLLC') color = '#f59e0b'; // Gold URLLC
      else if (user.priority === 'eMBB') color = '#00f0ff';  // Cyan eMBB
      else color = '#10b981'; // Green mMTC

      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(ux, uy, user.priority === 'URLLC' ? 4 : 3, 0, Math.PI * 2);
      ctx.fill();

      // Selection Ring
      if (selectedEntity && selectedEntity.type === 'user' && selectedEntity.id === user.id) {
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(ux, uy, 8, 0, Math.PI * 2);
        ctx.stroke();
      }
    });
  }

  // Animation Loop
  let lastTick = Date.now();
  function animate() {
    const now = Date.now();
    const interval = 50 / speedMultiplier;

    if (isRunning && now - lastTick >= interval) {
      lastTick = now;
      const aiMetrics = engine.step();
      const baseMetrics = baselineEngine.step();

      updateDecisionPanels(aiMetrics);
      updateComparisonMetrics(aiMetrics, baseMetrics);
      updateInspectorPopup();
    }

    drawCanvas();
    requestAnimationFrame(animate);
  }

  // Update Decision Panels (Subcarriers, Power, Trace, Decisions Feed)
  function updateDecisionPanels(metrics) {
    // 1. Subcarrier Grid
    if (subcarrierGridEl) {
      const totalChannels = engine.getParams().numChannels;
      let html = '';
      const isAi = engine.getParams().isAiEnabled;
      const assignedClass = isAi ? 'assigned-ai' : 'assigned-base';

      // Count used channels across satellites
      let usedChannels = 0;
      engine.getSatellites().forEach(s => {
        usedChannels += (s.totalChannels - s.availableChannels);
      });

      for (let ch = 0; ch < totalChannels; ch++) {
        const isAssigned = ch < usedChannels;
        html += `<div class="subcarrier-slot ${isAssigned ? assignedClass : ''}">SC-${ch + 1}</div>`;
      }
      subcarrierGridEl.innerHTML = html;
    }

    // 2. Power Meter
    if (powerMeterFill && powerUsedText) {
      const usedWatts = Math.min(metrics.totalPowerWatts, Math.max(0, metrics.usedPowerWatts));
      const totalWatts = Math.max(1, metrics.totalPowerWatts);
      const pct = Math.min(100, Math.max(0, (usedWatts / totalWatts) * 100));
      powerMeterFill.style.width = `${pct}%`;
      powerUsedText.textContent = `${usedWatts}W / ${totalWatts}W (${pct.toFixed(0)}%)`;
    }

    // 3. Association Summary
    if (assocSummaryEl) {
      assocSummaryEl.innerHTML = `
        Served Users: <b style="color:#00f0ff">${metrics.servedUsers}</b> / ${metrics.activeUsers} &nbsp;|&nbsp; 
        Active Handovers: <b style="color:#f59e0b">${metrics.totalHandovers}</b> &nbsp;|&nbsp; 
        Dropped: <b style="color:${metrics.unservedUsers > 0 ? '#ef4444' : '#10b981'}">${metrics.unservedUsers}</b>
      `;
    }

    // 4. PPO Gymnasium Trace Box
    if (gymTraceEl) {
      const trace = engine.getLastPpoTrace();
      if (trace && engine.getParams().isAiEnabled) {
        gymTraceEl.innerHTML = `
          <div><b>Observation Vector [h, &gamma;, B, P, Alt]:</b> [${trace.state.join(', ')}]</div>
          <div><b>PPO Selected Action:</b> <span style="color:#00f0ff; font-weight:700;">${trace.actionName}</span></div>
          <div><b>Computed Step Reward R:</b> <span style="color:#10b981; font-weight:700;">+${trace.reward}</span> (Throughput: ${trace.throughput} Mbps, Loss: ${trace.packetLoss}%)</div>
        `;
      } else {
        gymTraceEl.innerHTML = `
          <div style="color: #94a3b8;">Baseline Rule-Based Mode Active: Greedy Euclidean Matching (No Reinforcement Learning Policy).</div>
        `;
      }
    }

    // 5. Decision Feed Stream
    if (decisionFeedEl) {
      const recents = engine.getRecentDecisions().slice(0, 5);
      if (recents.length > 0) {
        let html = '';
        recents.forEach(d => {
          html += `
            <div class="decision-log-item">
              <span style="color:#00f0ff;">[${d.userName}]</span> &rarr; ${d.satelliteName} | Ch:${d.channelId} | ${d.powerDbm} dBm &bull; ${d.reason}
            </div>
          `;
        });
        decisionFeedEl.innerHTML = html;
      }
    }
  }

  // Update Side-by-Side Comparison Readouts
  function updateComparisonMetrics(ai, base) {
    if (compThroughputAi && compThroughputBase) {
      compThroughputAi.textContent = `${ai.avgThroughputMbps} Mbps`;
      compThroughputBase.textContent = `${base.avgThroughputMbps} Mbps`;
      const diff = ai.avgThroughputMbps - base.avgThroughputMbps;
      const pct = base.avgThroughputMbps > 0 ? ((diff / base.avgThroughputMbps) * 100).toFixed(1) : 0;
      compThroughputDelta.className = `comp-delta-badge ${diff >= 0 ? 'delta-positive' : 'delta-negative'}`;
      compThroughputDelta.textContent = `${diff >= 0 ? '+' : ''}${pct}%`;
    }

    if (compSinrAi && compSinrBase) {
      compSinrAi.textContent = `${ai.avgSinrDb} dB`;
      compSinrBase.textContent = `${base.avgSinrDb} dB`;
      const diff = (ai.avgSinrDb - base.avgSinrDb).toFixed(1);
      compSinrDelta.className = `comp-delta-badge ${diff >= 0 ? 'delta-positive' : 'delta-negative'}`;
      compSinrDelta.textContent = `${diff >= 0 ? '+' : ''}${diff} dB`;
    }

    if (compLossAi && compLossBase) {
      compLossAi.textContent = `${ai.avgPacketLossPercent}%`;
      compLossBase.textContent = `${base.avgPacketLossPercent}%`;
      const diff = (ai.avgPacketLossPercent - base.avgPacketLossPercent).toFixed(1);
      compLossDelta.className = `comp-delta-badge ${diff <= 0 ? 'delta-positive' : 'delta-negative'}`;
      compLossDelta.textContent = `${diff}%`;
    }

    if (compLatencyAi && compLatencyBase) {
      compLatencyAi.textContent = `${ai.avgLatencyMs} ms`;
      compLatencyBase.textContent = `${base.avgLatencyMs} ms`;
      const diff = (ai.avgLatencyMs - base.avgLatencyMs).toFixed(1);
      compLatencyDelta.className = `comp-delta-badge ${diff <= 0 ? 'delta-positive' : 'delta-negative'}`;
      compLatencyDelta.textContent = `${diff} ms`;
    }
  }

  // Canvas Click Detection (Hit-testing for entities)
  canvas.addEventListener('click', (e) => {
    const rect = canvas.getBoundingClientRect();
    const clickX = ((e.clientX - rect.left) / rect.width) * 100;
    const clickY = ((e.clientY - rect.top) / rect.height) * 100;

    // Check Satellites first
    let found = null;
    engine.getSatellites().forEach(s => {
      const dx = s.x - clickX;
      const dy = s.y - clickY;
      if (Math.sqrt(dx * dx + dy * dy) < 4.5) {
        found = { type: 'sat', id: s.id };
      }
    });

    // Check Users
    if (!found) {
      engine.getUsers().forEach(u => {
        const dx = u.x - clickX;
        const dy = u.y - clickY;
        if (Math.sqrt(dx * dx + dy * dy) < 3.5) {
          found = { type: 'user', id: u.id };
        }
      });
    }

    selectedEntity = found;
    updateInspectorPopup();
  });

  function updateInspectorPopup() {
    if (!selectedEntity || !popup) {
      if (popup) popup.classList.remove('active');
      return;
    }

    popup.classList.add('active');

    if (selectedEntity.type === 'sat') {
      const sat = engine.getSatellites().find(s => s.id === selectedEntity.id);
      if (!sat) return;

      popupTitle.textContent = sat.name;
      popupBadge.textContent = 'LEO SATELLITE';
      popupBadge.style.color = sat.beamColor;
      popupBody.innerHTML = `
        <div style="font-size:0.8rem; line-height:1.6; font-family:var(--font-mono);">
          <div>Orbital Altitude: <b>${sat.altitudeKm} km</b></div>
          <div>Velocity: <b>7.56 km/s</b> (Keplerian)</div>
          <div>Doppler Shift: <b style="color:#00f0ff;">${sat.dopplerShiftKhz > 0 ? '+' : ''}${sat.dopplerShiftKhz} kHz</b></div>
          <div>Channels Assigned: <b>${sat.totalChannels - sat.availableChannels} / ${sat.totalChannels}</b></div>
          <div>Transmit Power: <b>${sat.usedPowerWatts.toFixed(0)}W / ${sat.totalPowerWatts}W</b></div>
          <div>Connected Terminals: <b>${sat.connectedUserIds.length} users</b></div>
        </div>
      `;
    } else if (selectedEntity.type === 'user') {
      const user = engine.getUsers().find(u => u.id === selectedEntity.id);
      if (!user) return;

      popupTitle.textContent = user.name;
      popupBadge.textContent = `${user.priority} TERMINAL`;
      popupBadge.style.color = user.priority === 'URLLC' ? '#f59e0b' : '#00f0ff';
      popupBody.innerHTML = `
        <div style="font-size:0.8rem; line-height:1.6; font-family:var(--font-mono);">
          <div>Serving Node: <b style="color:#00f0ff;">${user.connectedSatelliteId || 'NONE (DROPPED)'}</b></div>
          <div>Assigned Channel: <b>${user.connectedChannelId !== null ? `SC-${user.connectedChannelId + 1}` : 'N/A'}</b></div>
          <div>Allocated Power: <b>${user.allocatedPowerDbm} dBm</b></div>
          <div>Allocated Bandwidth: <b>${user.allocatedBandwidthMhz} MHz</b></div>
          <div>Instantaneous SINR: <b style="color:#34d399;">${user.sinrDb} dB</b></div>
          <div>Throughput: <b>${user.throughputMbps} Mbps</b> (Req: ${user.trafficDemandMbps})</div>
          <div>Packet Loss: <b style="color:${user.packetLossPercent > 5 ? '#ef4444' : '#10b981'};">${user.packetLossPercent}%</b></div>
          <div>Handover Latency: <b>${user.latencyMs} ms</b></div>
        </div>
      `;
    }
  }

  if (popupClose) {
    popupClose.addEventListener('click', () => {
      selectedEntity = null;
      if (popup) popup.classList.remove('active');
    });
  }

  // Play / Pause Controls
  if (btnPlay) {
    btnPlay.addEventListener('click', () => {
      isRunning = !isRunning;
      btnPlay.innerHTML = isRunning ? '<span>⏸ Pause</span>' : '<span>▶ Resume</span>';
    });
  }

  if (btnStep) {
    btnStep.addEventListener('click', () => {
      isRunning = false;
      if (btnPlay) btnPlay.innerHTML = '<span>▶ Resume</span>';
      const aiMetrics = engine.step();
      const baseMetrics = baselineEngine.step();
      updateDecisionPanels(aiMetrics);
      updateComparisonMetrics(aiMetrics, baseMetrics);
      updateInspectorPopup();
      drawCanvas();
    });
  }

  if (btnReset) {
    btnReset.addEventListener('click', () => {
      engine.initializeEnvironment();
      baselineEngine.initializeEnvironment();
      selectedEntity = null;
      updateInspectorPopup();
      drawCanvas();
    });
  }

  if (speedSelect) {
    speedSelect.addEventListener('change', (e) => {
      speedMultiplier = Number(e.target.value) || 1;
    });
  }

  // Allocation Mode Switchers (AI vs Baseline)
  if (btnModeAi && btnModeBaseline) {
    btnModeAi.addEventListener('click', () => {
      engine.updateParams({ isAiEnabled: true });
      btnModeAi.classList.add('active', 'ai-mode');
      btnModeBaseline.classList.remove('active', 'baseline-mode');
    });

    btnModeBaseline.addEventListener('click', () => {
      engine.updateParams({ isAiEnabled: false });
      btnModeBaseline.classList.add('active', 'baseline-mode');
      btnModeAi.classList.remove('active', 'ai-mode');
    });
  }

  // Pre-configured Scenario Buttons
  const scenarioPills = document.querySelectorAll('.lab-scenario-pill');
  scenarioPills.forEach(pill => {
    pill.addEventListener('click', () => {
      scenarioPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');

      const scenKey = pill.getAttribute('data-scen');
      const profile = SCENARIO_PROFILES[scenKey];
      if (profile) {
        engine.updateParams(profile.params);
        baselineEngine.updateParams(profile.params);

        // Sync slider values
        if (sliderSats) { sliderSats.value = profile.params.numSatellites; valSats.textContent = profile.params.numSatellites; }
        if (sliderUsers) { sliderUsers.value = profile.params.numUsers; valUsers.textContent = profile.params.numUsers; }
        if (sliderChannels) { sliderChannels.value = profile.params.numChannels; valChannels.textContent = profile.params.numChannels; }
        if (sliderRain) { sliderRain.value = profile.params.rainRateMmHr; valRain.textContent = `${profile.params.rainRateMmHr} mm/h`; }

        const scenDescEl = document.getElementById('labScenarioDescText');
        if (scenDescEl) {
          scenDescEl.textContent = profile.desc;
        }
      }
    });
  });

  // Slider Listeners
  if (sliderSats) {
    sliderSats.addEventListener('input', (e) => {
      valSats.textContent = e.target.value;
      engine.updateParams({ numSatellites: Number(e.target.value) });
      baselineEngine.updateParams({ numSatellites: Number(e.target.value) });
    });
  }

  if (sliderUsers) {
    sliderUsers.addEventListener('input', (e) => {
      valUsers.textContent = e.target.value;
      engine.updateParams({ numUsers: Number(e.target.value) });
      baselineEngine.updateParams({ numUsers: Number(e.target.value) });
    });
  }

  if (sliderChannels) {
    sliderChannels.addEventListener('input', (e) => {
      valChannels.textContent = e.target.value;
      engine.updateParams({ numChannels: Number(e.target.value) });
      baselineEngine.updateParams({ numChannels: Number(e.target.value) });
    });
  }

  if (sliderPower) {
    sliderPower.addEventListener('input', (e) => {
      valPower.textContent = `${e.target.value}W`;
      engine.updateParams({ totalPowerWatts: Number(e.target.value) });
      baselineEngine.updateParams({ totalPowerWatts: Number(e.target.value) });
    });
  }

  if (sliderRain) {
    sliderRain.addEventListener('input', (e) => {
      valRain.textContent = `${e.target.value} mm/h`;
      engine.updateParams({ rainRateMmHr: Number(e.target.value) });
      baselineEngine.updateParams({ rainRateMmHr: Number(e.target.value) });
    });
  }

  // Export to CSV
  if (btnExport) {
    btnExport.addEventListener('click', () => {
      const csvData = engine.exportResultsToCsv();
      const blob = new Blob([csvData], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.setAttribute('href', url);
      link.setAttribute('download', `orbit_intel_6g_ntn_experiment_step_${engine.stepCount}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    });
  }

  // Main Laboratory Tabs (Tab 1: PPO Resource Management, Tab 2: CAPRO Predictive Reliability)
  const labTabs = document.querySelectorAll('.lab-tab-btn');
  const labTabContents = document.querySelectorAll('.lab-tab-content');
  labTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      labTabs.forEach(t => t.classList.remove('active'));
      labTabContents.forEach(c => c.classList.remove('active'));

      tab.classList.add('active');
      const targetId = tab.getAttribute('data-tab-target');
      const targetEl = document.getElementById(targetId);
      if (targetEl) targetEl.classList.add('active');
    });
  });

  // Start Animation
  animate();
});
