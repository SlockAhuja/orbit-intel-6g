/**
 * ORBIT-INTEL 6G — Official Research Project Showcase Script
 * IEEE ComSoc Student Tech Leadership Conference (STLC) Tunisia 2026
 * Complete interactive engine: 3D Globe, Architecture Inspector, Physics Calc,
 * Predictive Horizon Switcher, CAPRO Evaluator, Handover Animator, Scenario Explorer,
 * Lightbox, FAQ Accordion, Presentation Mode, and Telemetry Stream.
 */

document.addEventListener('DOMContentLoaded', () => {
  initNavbar();
  initHeroGlobe();
  initTelemetryHUD();
  initChallengeVisualizer();
  initWorkflowStepper();
  initArchitectureInspector();
  initPhysicsCalculator();
  initPredictiveTimeline();
  initCandidateEvaluator();
  initHandoverAnimator();
  initScenarioExplorer();
  initMetricCounters();
  initLightbox();
  initFaqAccordion();
  initPresentationMode();
  initBackToTop();
  initCopyButtons();
});

/* ==========================================================================
   01. Navigation & Mobile Menu
   ========================================================================== */
function initNavbar() {
  const header = document.querySelector('.header');
  const mobileToggle = document.querySelector('.mobile-toggle');
  const navLinks = document.querySelector('.nav-links');

  window.addEventListener('scroll', () => {
    if (window.scrollY > 40) {
      header.classList.add('scrolled');
    } else {
      header.classList.remove('scrolled');
    }
  });

  if (mobileToggle && navLinks) {
    mobileToggle.addEventListener('click', () => {
      navLinks.classList.toggle('active');
    });

    navLinks.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        navLinks.classList.remove('active');
      });
    });
  }
}

/* ==========================================================================
   02. Hero 3D Earth Globe with Three.js
   ========================================================================== */
function initHeroGlobe() {
  const container = document.getElementById('heroGlobeContainer');
  if (!container || typeof THREE === 'undefined') return;

  const width = container.clientWidth || 600;
  const height = container.clientHeight || 550;

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
  camera.position.set(0, 5, 14);

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setSize(width, height);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  container.appendChild(renderer.domElement);

  const ambientLight = new THREE.AmbientLight(0xffffff, 0.9);
  scene.add(ambientLight);

  const dirLight = new THREE.DirectionalLight(0x00f0ff, 1.2);
  dirLight.position.set(10, 10, 10);
  scene.add(dirLight);

  const violetLight = new THREE.DirectionalLight(0x8b5cf6, 0.7);
  violetLight.position.set(-10, -5, -5);
  scene.add(violetLight);

  const earthGroup = new THREE.Group();
  scene.add(earthGroup);

  const sphereGeo = new THREE.SphereGeometry(4.2, 48, 48);
  const textureLoader = new THREE.TextureLoader();

  const earthMat = new THREE.MeshPhongMaterial({
    color: 0x0f2a4a,
    emissive: 0x051329,
    specular: 0x00f0ff,
    shininess: 15
  });

  textureLoader.load(
    'assets/images/earth.jpg',
    (tex) => {
      earthMat.map = tex;
      earthMat.color.setHex(0xffffff);
      earthMat.needsUpdate = true;
    },
    undefined,
    () => {
      earthMat.wireframe = true;
      earthMat.color.setHex(0x00f0ff);
    }
  );

  const earthMesh = new THREE.Mesh(sphereGeo, earthMat);
  earthGroup.add(earthMesh);

  // Atmosphere Glow
  const atmosGeo = new THREE.SphereGeometry(4.35, 32, 32);
  const atmosMat = new THREE.MeshBasicMaterial({
    color: 0x00f0ff,
    transparent: true,
    opacity: 0.12,
    side: THREE.BackSide
  });
  earthGroup.add(new THREE.Mesh(atmosGeo, atmosMat));

  // Orbits & Satellites
  const orbits = [
    { radius: 6.2, inclX: 0.45, inclZ: 0.2, speed: 0.007, color: 0x00f0ff },
    { radius: 6.6, inclX: -0.65, inclZ: 0.4, speed: 0.005, color: 0x38bdf8 },
    { radius: 7.0, inclX: 0.85, inclZ: -0.3, speed: 0.006, color: 0x8b5cf6 },
    { radius: 7.4, inclX: -0.2, inclZ: -0.7, speed: 0.004, color: 0x10b981 }
  ];

  const satObjects = [];

  orbits.forEach(orb => {
    const curve = new THREE.EllipseCurve(0, 0, orb.radius, orb.radius, 0, 2 * Math.PI, false, 0);
    const points = curve.getPoints(80);
    const ringGeo = new THREE.BufferGeometry().setFromPoints(points.map(p => new THREE.Vector3(p.x, 0, p.y)));
    const ringMat = new THREE.LineBasicMaterial({ color: orb.color, transparent: true, opacity: 0.35 });
    const ringLine = new THREE.Line(ringGeo, ringMat);
    ringLine.rotation.x = orb.inclX;
    ringLine.rotation.z = orb.inclZ;
    scene.add(ringLine);

    const satGeo = new THREE.SphereGeometry(0.18, 16, 16);
    const satMat = new THREE.MeshBasicMaterial({ color: orb.color });
    const satMesh = new THREE.Mesh(satGeo, satMat);

    const beamGeo = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, 0, 0), new THREE.Vector3(0, 0, 0)]);
    const beamMat = new THREE.LineDashedMaterial({ color: orb.color, dashSize: 0.2, gapSize: 0.1, transparent: true, opacity: 0.5 });
    const beamLine = new THREE.Line(beamGeo, beamMat);
    beamLine.computeLineDistances();
    scene.add(beamLine);

    satObjects.push({
      mesh: satMesh,
      beam: beamLine,
      orbit: orb,
      angle: Math.random() * Math.PI * 2
    });

    scene.add(satMesh);
  });

  let controls = null;
  if (typeof THREE.OrbitControls !== 'undefined') {
    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.enableZoom = false;
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.5;
  }

  function animate() {
    requestAnimationFrame(animate);

    earthGroup.rotation.y += 0.0012;

    satObjects.forEach(sat => {
      sat.angle += sat.orbit.speed;
      const unrotX = Math.cos(sat.angle) * sat.orbit.radius;
      const unrotZ = Math.sin(sat.angle) * sat.orbit.radius;
      const pos = new THREE.Vector3(unrotX, 0, unrotZ);
      pos.applyAxisAngle(new THREE.Vector3(1, 0, 0), sat.orbit.inclX);
      pos.applyAxisAngle(new THREE.Vector3(0, 0, 1), sat.orbit.inclZ);
      sat.mesh.position.copy(pos);

      const groundPos = pos.clone().normalize().multiplyScalar(4.2);
      const positions = sat.beam.geometry.attributes.position.array;
      positions[0] = pos.x; positions[1] = pos.y; positions[2] = pos.z;
      positions[3] = groundPos.x; positions[4] = groundPos.y; positions[5] = groundPos.z;
      sat.beam.geometry.attributes.position.needsUpdate = true;
      sat.beam.computeLineDistances();
    });

    if (controls) controls.update();
    renderer.render(scene, camera);
  }

  animate();

  window.addEventListener('resize', () => {
    const newWidth = container.clientWidth || 600;
    const newHeight = container.clientHeight || 550;
    camera.aspect = newWidth / newHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(newWidth, newHeight);
  });
}

/* ==========================================================================
   03. Real-Time Telemetry HUD Simulation
   ========================================================================== */
function initTelemetryHUD() {
  const satIdEl = document.getElementById('hudSatId');
  const sinrEl = document.getElementById('hudSinr');
  const delayEl = document.getElementById('hudDelay');
  const pdrEl = document.getElementById('hudPdr');
  const dopplerEl = document.getElementById('hudDoppler');

  if (!sinrEl) return;

  const nodes = ['LEO-SAT-1 (Keplerian)', 'LEO-SAT-2 (Keplerian)', 'HAPS-01 (Stratosphere)', 'UAV-02 (Tactical Edge)'];
  let idx = 0;

  setInterval(() => {
    idx = (idx + 1) % nodes.length;
    if (satIdEl) satIdEl.textContent = nodes[idx];

    const sinr = (18.5 + (Math.random() * 2.4 - 1.2)).toFixed(1);
    const delay = (6.4 + (Math.random() * 0.7 - 0.3)).toFixed(2);
    const pdr = (99.35 + (Math.random() * 0.15)).toFixed(2);
    const dop = (Math.random() > 0.5 ? '+' : '-') + (16.0 + Math.random() * 6.5).toFixed(1);

    sinrEl.textContent = `${sinr} dB`;
    delayEl.textContent = `${delay} ms`;
    pdrEl.textContent = `${pdr}%`;
    if (dopplerEl) dopplerEl.textContent = `${dop} kHz`;
  }, 2200);
}

/* ==========================================================================
   04. Challenge Visualizer: Reactive vs Predictive
   ========================================================================== */
function initChallengeVisualizer() {
  const btnReactive = document.getElementById('btnChallengeReactive');
  const btnPredictive = document.getElementById('btnChallengePredictive');
  const titleEl = document.getElementById('challengeVisTitle');
  const descEl = document.getElementById('challengeVisDesc');
  const pdrEl = document.getElementById('cVisPdr');
  const latencyEl = document.getElementById('cVisLatency');
  const outageEl = document.getElementById('cVisOutage');
  const pingpongEl = document.getElementById('cVisPingPong');

  if (!btnReactive || !btnPredictive) return;

  btnReactive.addEventListener('click', () => {
    btnReactive.classList.add('active');
    btnPredictive.classList.remove('active');

    titleEl.textContent = 'Conventional Reactive Handover (M1 Paradigm)';
    descEl.textContent = 'Connection monitoring only triggers a handover AFTER signal quality drops below demodulation threshold. Due to round-trip propagation lag and elevation loss, the link experiences radio link failure, causing dropped packets and repeated ping-pong switches.';
    pdrEl.textContent = '91.42%';
    pdrEl.style.color = '#ef4444';
    latencyEl.textContent = '18.44 ms (Breaches URLLC)';
    latencyEl.style.color = '#ef4444';
    outageEl.textContent = '8.58% (High Packet Loss)';
    outageEl.style.color = '#ef4444';
    pingpongEl.textContent = '28.9 / min (Unstable)';
  });

  btnPredictive.addEventListener('click', () => {
    btnPredictive.classList.add('active');
    btnReactive.classList.remove('active');

    titleEl.textContent = 'Confidence-Aware Predictive Reliability Orchestration (CAPRO)';
    descEl.textContent = 'CAPRO predicts future channel conditions across multi-second lookahead horizons. By computing conformal confidence intervals and penalizing total uncertainty, handovers are proactively initiated in overlapping visibility windows with zero packet interruption.';
    pdrEl.textContent = '99.41% (+7.99% Gain)';
    pdrEl.style.color = '#00f0ff';
    latencyEl.textContent = '6.82 ms (Guaranteed URLLC)';
    latencyEl.style.color = '#00f0ff';
    outageEl.textContent = '0.59% (14.5x Outage Suppression)';
    outageEl.style.color = '#00f0ff';
    pingpongEl.textContent = '3.1 / min (89.3% Reduction)';
  });
}

/* ==========================================================================
   05. Clickable System Workflow Stepper
   ========================================================================== */
const workflowData = [
  {
    step: '01',
    title: 'Physical Telemetry Acquisition',
    desc: 'Continuously ingests real-time channel measurements from serving and candidate links: instantaneous SNR, Doppler shift, Keplerian satellite position vectors, and atmospheric weather states under 3GPP TR 38.811 / TR 38.821 specs.'
  },
  {
    step: '02',
    title: 'Temporal Feature Engineering',
    desc: 'Constructs multi-horizon sliding windows containing temporal delta values, elevation rate-of-change, queue occupancy, and rain attenuation estimates (ITU-R P.618).'
  },
  {
    step: '03',
    title: 'Multi-Horizon Neural Forecasting',
    desc: 'Temporal neural predictors forecast expected link quality trajectories across multiple lookahead horizons (H = 1, 3, 5, and 10 seconds ahead).'
  },
  {
    step: '04',
    title: 'Conformal Quantile Uncertainty Bounds',
    desc: 'Generates well-calibrated prediction intervals (q05, q50, q95), separating aleatoric channel flutter (rain, multipath) from epistemic model uncertainty.'
  },
  {
    step: '05',
    title: 'Risk-Adjusted Utility Maximization',
    desc: 'Evaluates candidate paths using the risk-adjusted utility function J(a, u), deducting risk penalties and switching costs while enforcing hard URLLC constraints (q05 ≥ 3 dB, T_E2E ≤ 10 ms).'
  },
  {
    step: '06',
    title: 'Preemptive Multi-Tier Dispatch',
    desc: 'Dispatches proactive handover commands across Space, Air, or Ground tiers during overlapping visibility windows, guaranteeing continuous zero-outage connectivity.'
  }
];

function initWorkflowStepper() {
  const buttons = document.querySelectorAll('.workflow-step-btn');
  const titleEl = document.getElementById('wfDetailTitle');
  const descEl = document.getElementById('wfDetailDesc');
  const numEl = document.getElementById('wfDetailNum');

  if (!buttons.length || !titleEl) return;

  buttons.forEach(btn => {
    btn.addEventListener('click', () => {
      buttons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const idx = parseInt(btn.getAttribute('data-wf-step'), 10) - 1;
      const data = workflowData[idx];
      if (!data) return;

      if (numEl) numEl.textContent = `PHASE ${data.step}`;
      titleEl.textContent = data.title;
      descEl.textContent = data.desc;
    });
  });
}

/* ==========================================================================
   06. SAGIN Network Architecture Node Inspector
   ========================================================================== */
const nodeDetails = {
  leo1: {
    name: 'LEO-SAT-1 (Polar Orbit Node)',
    tier: 'SPACE LAYER (600 km Altitude)',
    desc: 'Keplerian satellite in 86° inclined orbit. Equipped with high-gain steerable beamforming phased arrays and Ka-band (28 GHz) inter-satellite cross-links. Compensates for up to ±37.4 kHz Doppler shift.',
    params: [
      { k: 'Orbital Velocity', v: '7.56 km/s' },
      { k: 'Orbital Period', v: '96.2 min' },
      { k: 'Slant Range', v: '600 - 1200 km' },
      { k: 'Propagation Delay', v: '2.00 - 4.00 ms' }
    ]
  },
  leo2: {
    name: 'LEO-SAT-2 (Preemptive Handover Target)',
    tier: 'SPACE LAYER (600 km Altitude)',
    desc: 'Approaching satellite node offering rising elevation angle (> 35°). Target of proactive handover during falling visibility of LEO-SAT-1.',
    params: [
      { k: 'Elevation Angle', v: '42.5° (Rising)' },
      { k: 'Visibility Remaining', v: '11.8 min' },
      { k: 'Predicted SINR (q50)', v: '21.4 dB' },
      { k: 'Conformal Lower (q05)', v: '17.8 dB' }
    ]
  },
  haps: {
    name: 'HAPS-01 (Stratospheric Edge Relay)',
    tier: 'AIR LAYER (20 km Altitude)',
    desc: 'Quasi-stationary stratospheric airship acting as a super-macro cell. Flies above tropospheric cloud cover, providing immune coverage against convective rain storms for wide areas (> 80 km radius).',
    params: [
      { k: 'Altitude', v: '20 km (Stratosphere)' },
      { k: 'Coverage Radius', v: '~80 km' },
      { k: 'Propagation Latency', v: '0.067 ms' },
      { k: 'Rain Fade Immunity', v: '100% (Above Clouds)' }
    ]
  },
  uav: {
    name: 'UAV-01 (Tactical Mobile Edge)',
    tier: 'AIR LAYER (300 m Altitude)',
    desc: 'Agile rotary-wing edge relay deployed dynamically over ground congestion hotspots. Equipped with sub-millisecond edge compute buffer to absorb terrestrial overflow.',
    params: [
      { k: 'Altitude', v: '300 m AGL' },
      { k: 'LoS Probability', v: '> 94%' },
      { k: 'Local Processing Delay', v: '0.50 ms' },
      { k: 'Speed', v: '18 m/s' }
    ]
  },
  gateway: {
    name: 'Optical/Ka Feeder Ground Gateway',
    tier: 'GROUND LAYER (Terrestrial Infrastructure)',
    desc: 'Primary tracking station equipped with high-throughput optical feeder links (10 Gbps) connecting satellite downlinks to the terrestrial core network and central CAPRO controller.',
    params: [
      { k: 'Feeder Bandwidth', v: '10 Gbps Optical/Ka' },
      { k: 'Feeder Latency', v: '1.20 ms' },
      { k: 'Tracking Mask', v: '5.0°' },
      { k: 'Core Interconnect', v: 'Fiber Backhaul' }
    ]
  },
  tbs: {
    name: 'Terrestrial Cellular gNodeB (TBS)',
    tier: 'GROUND LAYER (Terrestrial Access)',
    desc: 'Standard sub-6 GHz / mmWave cellular tower located in urban center. Delivers sub-millisecond latency when clear, but susceptible to street canyon shadowing and high user congestion surges.',
    params: [
      { k: 'Tower Height', v: '30 m' },
      { k: 'Cell Radius', v: '1.2 km' },
      { k: 'Terrestrial Delay', v: '0.80 ms' },
      { k: 'Congestion Vulnerability', v: 'High during Surges' }
    ]
  },
  ue_mobile: {
    name: 'Heterogeneous Ground Terminal (UE)',
    tier: 'USER LAYER (Ground Equipment)',
    desc: 'Ground equipment representing autonomous connected vehicles (V2X), emergency search-and-rescue teams, and mobile users demanding strict sub-10ms URLLC latency and 99.41% reliability.',
    params: [
      { k: 'URLLC SLA Target', v: '≤ 10.0 ms' },
      { k: 'Min SINR Threshold', v: '3.0 dB' },
      { k: 'Mobility Speed', v: '0 - 120 km/h' },
      { k: 'Measured Reliability', v: '99.41% (CAPRO)' }
    ]
  }
};

function initArchitectureInspector() {
  const chips = document.querySelectorAll('.sagin-node-chip');
  const nameEl = document.getElementById('nodeInspName');
  const tierEl = document.getElementById('nodeInspTier');
  const descEl = document.getElementById('nodeInspDesc');
  const paramsEl = document.getElementById('nodeInspParams');

  if (!chips.length || !nameEl) return;

  chips.forEach(chip => {
    chip.addEventListener('click', () => {
      chips.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');

      const key = chip.getAttribute('data-node-key');
      const data = nodeDetails[key];
      if (!data) return;

      nameEl.textContent = data.name;
      tierEl.textContent = data.tier;
      descEl.textContent = data.desc;

      paramsEl.innerHTML = data.params.map(p => `
        <div class="param-row">
          <span class="param-k">${p.k}</span>
          <span class="param-v">${p.v}</span>
        </div>
      `).join('');
    });
  });
}

/* ==========================================================================
   07. Physics-Grounded Propagation Calculator
   ========================================================================== */
function initPhysicsCalculator() {
  const distSlider = document.getElementById('calcDistSlider');
  const elevSlider = document.getElementById('calcElevSlider');
  const distValEl = document.getElementById('calcDistVal');
  const elevValEl = document.getElementById('calcElevVal');
  const fsplEl = document.getElementById('calcFsplRes');
  const delayEl = document.getElementById('calcDelayRes');
  const e2eEl = document.getElementById('calcE2eRes');

  if (!distSlider || !elevSlider) return;

  function updatePhysics() {
    const d = parseFloat(distSlider.value); // km
    const elev = parseFloat(elevSlider.value); // degrees

    distValEl.textContent = `${d} km`;
    elevValEl.textContent = `${elev}°`;

    // FSPL equation at f = 28 GHz (Ka-band): FSPL = 20*log10(d) + 20*log10(f_MHz) - 27.55
    const f_MHz = 28000;
    const fspl = (20 * Math.log10(d) + 20 * Math.log10(f_MHz) - 27.55).toFixed(1);

    // Speed of light: c = 299,792 km/s -> T_prop = d / c
    const propDelay = (d / 299.792).toFixed(2);

    // Full physically decomposed latency: T_E2E = T_prop + T_proc (0.50 ms) + T_feeder (1.20 ms) + T_queue (0.40 ms)
    const e2eLatency = (parseFloat(propDelay) + 0.50 + 1.20 + 0.40).toFixed(2);

    fsplEl.textContent = `${fspl} dB`;
    delayEl.textContent = `${propDelay} ms`;
    e2eEl.textContent = `${e2eLatency} ms`;
  }

  distSlider.addEventListener('input', updatePhysics);
  elevSlider.addEventListener('input', updatePhysics);
  updatePhysics();
}

/* ==========================================================================
   08. Predictive Intelligence Timeline (Horizons H = 1, 3, 5, 10s)
   ========================================================================== */
const horizonData = {
  h1: { h: '1s Ahead', sinr_q50: '19.4 dB', q05: '18.1 dB', q95: '20.6 dB', epistemic: '0.18 dB', aleatoric: '0.62 dB', pathD: 'M 20,90 Q 90,85 160,88 T 240,82 T 320,78 T 400,80' },
  h3: { h: '3s Ahead', sinr_q50: '18.2 dB', q05: '16.4 dB', q95: '19.8 dB', epistemic: '0.35 dB', aleatoric: '0.84 dB', pathD: 'M 20,90 Q 90,88 160,94 T 240,98 T 320,105 T 400,110' },
  h5: { h: '5s Ahead', sinr_q50: '16.8 dB', q05: '14.2 dB', q95: '19.1 dB', epistemic: '0.52 dB', aleatoric: '1.12 dB', pathD: 'M 20,90 Q 90,92 160,102 T 240,115 T 320,128 T 400,135' },
  h10: { h: '10s Ahead', sinr_q50: '14.1 dB', q05: '10.5 dB', q95: '17.4 dB', epistemic: '0.88 dB', aleatoric: '1.45 dB', pathD: 'M 20,90 Q 90,98 160,118 T 240,135 T 320,152 T 400,165' }
};

function initPredictiveTimeline() {
  const tabs = document.querySelectorAll('.horizon-tab');
  const pathEl = document.getElementById('timelinePredPath');
  const boundsEl = document.getElementById('timelineBoundsArea');
  const q50El = document.getElementById('tlQ50');
  const q05El = document.getElementById('tlQ05');
  const q95El = document.getElementById('tlQ95');
  const episEl = document.getElementById('tlEpistemic');
  const aleaEl = document.getElementById('tlAleatoric');

  if (!tabs.length || !pathEl) return;

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      const hKey = tab.getAttribute('data-horizon');
      const d = horizonData[hKey];
      if (!d) return;

      pathEl.setAttribute('d', d.pathD);
      if (q50El) q50El.textContent = d.sinr_q50;
      if (q05El) q05El.textContent = d.q05;
      if (q95El) q95El.textContent = d.q95;
      if (episEl) episEl.textContent = d.epistemic;
      if (aleaEl) aleaEl.textContent = d.aleatoric;
    });
  });
}

/* ==========================================================================
   09. CAPRO Interactive Candidate Evaluator
   ========================================================================== */
const candidates = {
  cand_leo1: {
    name: 'LEO-SAT-1 (Current Serving)',
    status: 'REJECTED: Impending Elevation Loss',
    detail: 'Falling below elevation mask (elev = 8.4° < 10.0°). Visibility remaining is only 6.2s, breaching the hard visibility constraint (T_vis > 12.0s). Rejected to avoid mid-session drop.',
    metrics: [
      { k: 'Lower Conformal Bound (q05)', v: '4.8 dB (≥ 3.0 dB: PASS)' },
      { k: 'Decomposed Latency', v: '7.12 ms (≤ 10.0 ms: PASS)' },
      { k: 'Visibility Remaining', v: '6.2 s (< 12.0 s: FAIL)' },
      { k: 'Utility Score J', v: '-2.45' }
    ]
  },
  cand_leo2: {
    name: 'LEO-SAT-2 (Rising Candidate)',
    status: 'SELECTED BY CAPRO (Optimal Path)',
    detail: 'Optimal candidate. High elevation (42.5°), strong conformal lower bound (17.8 dB), 11.8 min remaining visibility. Maximizes risk-adjusted utility J = 22.40.',
    metrics: [
      { k: 'Lower Conformal Bound (q05)', v: '17.8 dB (≥ 3.0 dB: PASS)' },
      { k: 'Decomposed Latency', v: '6.82 ms (≤ 10.0 ms: PASS)' },
      { k: 'Visibility Remaining', v: '11.8 min (> 12.0 s: PASS)' },
      { k: 'Utility Score J', v: '+22.40 (MAX)' }
    ]
  },
  cand_haps: {
    name: 'HAPS-01 (Stratospheric Backup)',
    status: 'STANDBY: Viable Alternative',
    detail: 'High reliability and zero rain attenuation, but slightly lower spectral efficiency utility compared to LEO-SAT-2 Ka-band beam. Preserved as reliable fallback.',
    metrics: [
      { k: 'Lower Conformal Bound (q05)', v: '14.2 dB (PASS)' },
      { k: 'Decomposed Latency', v: '5.20 ms (PASS)' },
      { k: 'Visibility Remaining', v: 'Stationary (PASS)' },
      { k: 'Utility Score J', v: '+16.85' }
    ]
  },
  cand_uav: {
    name: 'UAV-01 (Tactical Edge)',
    status: 'REJECTED: Buffer Saturation',
    detail: 'Queue delay spikes to 6.80 ms due to local ground congestion surge, causing total E2E delay to exceed the 10.0 ms URLLC constraint (T_E2E = 11.45 ms > 10.0 ms).',
    metrics: [
      { k: 'Lower Conformal Bound (q05)', v: '18.1 dB (PASS)' },
      { k: 'Decomposed Latency', v: '11.45 ms (> 10.0 ms: FAIL)' },
      { k: 'Visibility Remaining', v: 'LoS Available' },
      { k: 'Utility Score J', v: '-8.12' }
    ]
  }
};

function initCandidateEvaluator() {
  const items = document.querySelectorAll('.candidate-item');
  const titleEl = document.getElementById('evalTitle');
  const statusEl = document.getElementById('evalStatus');
  const detailEl = document.getElementById('evalDetail');
  const metricsEl = document.getElementById('evalMetrics');

  if (!items.length || !titleEl) return;

  items.forEach(item => {
    item.addEventListener('click', () => {
      items.forEach(i => i.classList.remove('selected'));
      item.classList.add('selected');

      const key = item.getAttribute('data-cand-key');
      const c = candidates[key];
      if (!c) return;

      titleEl.textContent = c.name;
      statusEl.textContent = c.status;
      statusEl.className = 'cand-status ' + (c.status.includes('SELECTED') ? 'pass' : (c.status.includes('STANDBY') ? 'pass' : 'fail'));
      detailEl.textContent = c.detail;

      metricsEl.innerHTML = c.metrics.map(m => `
        <div class="param-row">
          <span class="param-k">${m.k}</span>
          <span class="param-v">${m.v}</span>
        </div>
      `).join('');
    });
  });
}

/* ==========================================================================
   10. Multi-Tier Handover Step Animator
   ========================================================================== */
const handoverStages = [
  {
    icon: '🛰️',
    title: 'Phase 1: Stable Serving Link',
    desc: 'Terminal u is connected to LEO-SAT-1 in clear-sky conditions. Telemetry reports steady SINR of 19.5 dB with 6.4 ms end-to-end latency. No handover indicated.'
  },
  {
    icon: '📉',
    title: 'Phase 2: Impending Degradation Detected',
    desc: 'At lookahead horizon H = 5s, the temporal predictor anticipates an elevation drop below 10° and approaching rain front. Lower bound q05 begins decaying toward 3 dB threshold.'
  },
  {
    icon: '⚖️',
    title: 'Phase 3: Dual-Uncertainty Evaluation',
    desc: 'CAPRO queries candidate nodes: LEO-SAT-2, HAPS-01, and UAV-01. Risk penalty κ·σ_total filters out high-flutter paths. Hard constraints confirm LEO-SAT-2 has 11.8 min visibility remaining.'
  },
  {
    icon: '⚡',
    title: 'Phase 4: Preemptive Handover Triggered',
    desc: 'Handover command dispatched 3.2 seconds BEFORE physical link drop. The terminal synchronizes with LEO-SAT-2 during the overlapping beam footprint with zero interruption.'
  },
  {
    icon: '🛡️',
    title: 'Phase 5: Seamless Connection Maintained',
    desc: 'Traffic successfully migrated to LEO-SAT-2. End-to-end latency remains 6.82 ms, preserving URLLC SLA without a single dropped packet (0.59% outage maintained).'
  }
];

function initHandoverAnimator() {
  const btns = document.querySelectorAll('.handover-step-btn');
  const iconEl = document.getElementById('hoStageIcon');
  const titleEl = document.getElementById('hoStageTitle');
  const descEl = document.getElementById('hoStageDesc');

  if (!btns.length || !iconEl) return;

  btns.forEach(btn => {
    btn.addEventListener('click', () => {
      btns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const step = parseInt(btn.getAttribute('data-ho-step'), 10) - 1;
      const s = handoverStages[step];
      if (!s) return;

      iconEl.textContent = s.icon;
      titleEl.textContent = s.title;
      descEl.textContent = s.desc;
    });
  });
}

/* ==========================================================================
   11. Interactive Stress-Test Scenario Explorer
   ========================================================================== */
const scenarios = [
  {
    title: 'Scenario 1: Normal Clear-Sky Conditions',
    desc: 'Nominal operational environment. High elevation (> 40°), zero rain attenuation, clear LOS propagation across Ka-band downlinks. All 4 methods maintain connectivity.',
    baseRain: 0,
    baseFlutter: 0.5,
    pdr: '99.8%',
    action: 'Maintain Serving Node (No Handover Needed)'
  },
  {
    title: 'Scenario 2: High Congestion Traffic Surge',
    desc: 'Ground cellular gNodeB experiences a 500% user traffic spike. Terrestrial queue delay surges from 0.8 ms to 9.5 ms, breaching the 10 ms URLLC latency threshold.',
    baseRain: 0,
    baseFlutter: 1.2,
    pdr: '99.41%',
    action: 'CAPRO Offloads Traffic to Aerial UAV-01 Edge Relay'
  },
  {
    title: 'Scenario 3: Sudden Rain Degradation (ITU-R P.618)',
    desc: 'Heavy convective rain storm (up to 80 mm/h) enters the satellite downlink path. Ka-band signal experiences up to 14.8 dB rain fade, causing reactive schemes to disconnect.',
    baseRain: 65,
    baseFlutter: 2.8,
    pdr: '99.12%',
    action: 'Preemptive Reroute to Stratospheric HAPS-01 (Above Clouds)'
  },
  {
    title: 'Scenario 4: Satellite Handover Replay',
    desc: 'LEO-SAT-1 transits below the 10° elevation mask. The physical simulation replays the overlapping constellation geometry as LEO-SAT-2 rises from the eastern horizon.',
    baseRain: 5,
    baseFlutter: 1.0,
    pdr: '99.41%',
    action: 'Zero-Outage Preemptive Satellite-to-Satellite Handover'
  },
  {
    title: 'Scenario 5: High Uncertainty Flutter',
    desc: 'Severe atmospheric turbulence and multipath clutter induce high aleatoric variance (flutter > 4.5 dB). Point-estimate predictors trigger 28.9 ping-pong handovers/min.',
    baseRain: 25,
    baseFlutter: 4.5,
    pdr: '98.90%',
    action: 'CAPRO Uncertainty Penalty Suppresses Ping-Pong Handovers by 89.3%'
  }
];

function initScenarioExplorer() {
  const btns = document.querySelectorAll('.scenario-btn');
  const titleEl = document.getElementById('scenTitle');
  const descEl = document.getElementById('scenDesc');
  const rainSlider = document.getElementById('scenRainSlider');
  const flutterSlider = document.getElementById('scenFlutterSlider');
  const rainValEl = document.getElementById('scenRainVal');
  const flutterValEl = document.getElementById('scenFlutterVal');
  const pdrEl = document.getElementById('scenPdrRes');
  const actionEl = document.getElementById('scenActionRes');

  if (!btns.length || !rainSlider) return;

  function updateScenarioDisplay(s) {
    if (titleEl) titleEl.textContent = s.title;
    if (descEl) descEl.textContent = s.desc;
    rainSlider.value = s.baseRain;
    flutterSlider.value = s.baseFlutter;
    updateDynamicMetrics();
  }

  function updateDynamicMetrics() {
    const r = parseFloat(rainSlider.value);
    const fl = parseFloat(flutterSlider.value);
    rainValEl.textContent = `${r} mm/h`;
    flutterValEl.textContent = `${fl} dB`;

    // Attenuation calculation (ITU-R P.618 approx: A_rain = 0.187 * R^0.98 * L)
    const rainAtten = (0.187 * Math.pow(r, 0.98) * 2.5 / 10).toFixed(1);
    const effSinr = Math.max(19.4 - rainAtten - fl, 2.1).toFixed(1);

    if (pdrEl) {
      const pdrEst = effSinr > 3.0 ? (99.41 - (r * 0.005)).toFixed(2) : (91.42).toFixed(2);
      pdrEl.textContent = `${pdrEst}% (Effective SINR: ${effSinr} dB)`;
    }

    if (actionEl) {
      if (r > 40) {
        actionEl.textContent = 'CAPRO Dispatches Traffic to Rain-Immune HAPS Layer';
      } else if (fl > 3.0) {
        actionEl.textContent = 'CAPRO Penalizes Uncertainty & Suppresses Ping-Pong Handovers';
      } else {
        actionEl.textContent = 'Nominal LEO Satellite Tracking with Active Conformal Bounds';
      }
    }
  }

  btns.forEach(btn => {
    btn.addEventListener('click', () => {
      btns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const idx = parseInt(btn.getAttribute('data-scen-idx'), 10);
      const s = scenarios[idx];
      if (s) updateScenarioDisplay(s);
    });
  });

  rainSlider.addEventListener('input', updateDynamicMetrics);
  flutterSlider.addEventListener('input', updateDynamicMetrics);
}

/* ==========================================================================
   12. Metric Counter Animations
   ========================================================================== */
function initMetricCounters() {
  const counters = document.querySelectorAll('[data-counter-target]');
  if (!counters.length) return;

  const observer = new IntersectionObserver((entries, obs) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const el = entry.target;
        const target = parseFloat(el.getAttribute('data-counter-target'));
        const decimals = parseInt(el.getAttribute('data-counter-decimals') || '0', 10);
        const prefix = el.getAttribute('data-counter-prefix') || '';
        const suffix = el.getAttribute('data-counter-suffix') || '';
        const duration = 1800;
        const startTime = performance.now();

        function update(now) {
          const elapsed = now - startTime;
          const prog = Math.min(elapsed / duration, 1);
          const ease = 1 - Math.pow(1 - prog, 3);
          const val = ease * target;

          el.textContent = `${prefix}${val.toFixed(decimals)}${suffix}`;

          if (prog < 1) {
            requestAnimationFrame(update);
          } else {
            el.textContent = `${prefix}${target.toFixed(decimals)}${suffix}`;
          }
        }

        requestAnimationFrame(update);
        obs.unobserve(el);
      }
    });
  }, { threshold: 0.3 });

  counters.forEach(c => observer.observe(c));
}

/* ==========================================================================
   13. Screenshot & Figure Lightbox
   ========================================================================== */
function initLightbox() {
  const modal = document.getElementById('lightboxModal');
  const modalImg = document.getElementById('lightboxImg');
  const modalCap = document.getElementById('lightboxCaption');
  const closeBtn = document.getElementById('lightboxClose');

  if (!modal || !modalImg) return;

  document.querySelectorAll('[data-lightbox]').forEach(card => {
    card.addEventListener('click', () => {
      const img = card.querySelector('img');
      const title = card.querySelector('h4, h5')?.textContent || '';
      const desc = card.querySelector('p')?.textContent || '';

      if (img) {
        modalImg.src = img.src;
        modalCap.innerHTML = `<strong>${title}</strong> — ${desc}`;
        modal.classList.add('active');
      }
    });
  });

  const closeModal = () => modal.classList.remove('active');
  if (closeBtn) closeBtn.addEventListener('click', closeModal);
  modal.addEventListener('click', (e) => {
    if (e.target === modal) closeModal();
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modal.classList.contains('active')) closeModal();
  });
}

/* ==========================================================================
   14. FAQ Accordion
   ========================================================================== */
function initFaqAccordion() {
  const items = document.querySelectorAll('.faq-item');
  if (!items.length) return;

  items.forEach(item => {
    const q = item.querySelector('.faq-question');
    q.addEventListener('click', () => {
      const wasActive = item.classList.contains('active');
      items.forEach(i => i.classList.remove('active'));
      if (!wasActive) item.classList.add('active');
    });
  });
}

/* ==========================================================================
   15. Presentation Mode (16:9 Conference Slide Deck) - Exact 11-Slide Sequence
   ========================================================================== */
const presentationSlides = [
  {
    title: '1. Project Introduction: ORBIT-INTEL 6G',
    subtitle: 'Predictive Intelligence for Reliability-Aware Resource Orchestration in Integrated 6G Non-Terrestrial Networks',
    body: 'An official research technology framework developed for the IEEE Communications Society Student Tech Leadership Conference (STLC) Tunisia 2026. ORBIT-INTEL 6G bridges the gap between physics-grounded NTN simulation and autonomous predictive resource management, achieving deterministic sub-10ms URLLC latency across volatile space-air-ground networks.'
  },
  {
    title: '2. Research Challenge & Motivation',
    subtitle: 'Why Conventional Reactive Schemes Fail in 6G Non-Terrestrial Networks',
    body: 'LEO satellites travel at hypersonic orbital velocities (7.56 km/s), generating rapid Doppler shifts exceeding ±37 kHz and fleeting 8–14 minute visibility windows. Combined with Ka-band convective rain fading (>15 dB attenuation) and 600–1200 km propagation delays (2.5–5.0 ms one-way), traditional reactive 3GPP A3-event handovers suffer 8.58% session dropouts and destructive ping-pong thrashing (14.8%).'
  },
  {
    title: '3. 5-Tier Heterogeneous SAGIN Architecture',
    subtitle: 'Hierarchical Cross-Tier Space-Air-Ground Integration',
    body: 'Coordinates a multi-tiered heterogeneous topology: (1) Space Tier: 6 Keplerian LEO satellites at 600 km with optical inter-satellite links; (2) Stratospheric Tier: 2 solar-powered HAPS aerostats at 20 km providing wide-area rain-resilient relaying; (3) Aerial Tier: 4 tactical UAVs at 300 m for localized hotspot surge relief; (4) Terrestrial Tier: optical feeder gateways and 5G/6G gNodeBs; and (5) Edge User Tier: autonomous vehicles (V2X), maritime vessels, and emergency first responders.'
  },
  {
    title: '4. Physics-Grounded Network Simulation',
    subtitle: 'Rigorous Compliance with 3GPP TR 38.811/821 & ITU-R P.618 Standards',
    body: 'Built on true physical propagation mechanics: Keplerian two-body orbital dynamics, vis-viva velocity calculation, Doppler shift modeling, ITU-R P.618-13 specific rain attenuation (gamma_R = k * R^alpha), ITU-R P.676 atmospheric gas absorption, and physical decomposition of end-to-end latency: T_E2E = T_prop + T_trans + T_proc + T_queue + T_ho.'
  },
  {
    title: '5. Predictive Link Intelligence & Uncertainty',
    subtitle: 'Multi-Horizon Neural Forecasting with Aleatoric & Epistemic Decomposition',
    body: 'Deep temporal predictors forecast channel trajectories over multi-second horizons (H = 1s, 3s, 5s, 10s) with RMSE < 0.42 dB. Crucially decomposes total uncertainty into: (a) Aleatoric Uncertainty (inherent physical rain flutter and tropospheric scintillation), and (b) Epistemic Uncertainty (model lack of knowledge in out-of-distribution regimes like solar storms), preventing overconfident handover failures.'
  },
  {
    title: '6. CAPRO Technology & Decision Workflow',
    subtitle: 'Confidence-Aware Predictive Reliability Orchestration',
    body: 'Formulates multi-objective risk-adjusted utility optimization: J(a, u, t) = R_hat - kappa*sigma_total - beta*P_tx - gamma*I(handover). Enforces deterministic hard URLLC reliability constraints before scoring: (1) Conformal lower bound q05(SINR) >= 3.0 dB (95% viability); (2) End-to-end latency T_E2E <= 10.0 ms; and (3) Orbital visibility margin T_vis >= 12.0 s.'
  },
  {
    title: '7. Intelligent Multi-Tier Handover',
    subtitle: 'Preemptive Zero-Loss Switching & 89.3% Ping-Pong Suppression',
    body: 'Executes proactive handovers during overlapping visibility footprints before link degradation occurs. The synergistic combination of epistemic risk penalty kappa and handover switching cost gamma suppresses destructive ping-pong flapping by 89.3%, stabilizing session continuity across LEO-to-LEO horizontal and LEO-to-HAPS vertical transitions.'
  },
  {
    title: '8. Experimental Results & Benchmark Evaluation',
    subtitle: 'Documented 400-Trial Monte Carlo Benchmarking Against Industry Baselines',
    body: 'Independently verified against Reactive (M1), Threshold Predictive (M2), and AI Point-Prediction (M3): CAPRO achieves 99.41% Packet Delivery Ratio (+7.36% gain over reactive), 6.82 ms 99th-percentile tail latency (-63.0% reduction), 0.59% outage probability (14.5x suppression), and 1.58% ping-pong rate (89.3% reduction).'
  },
  {
    title: '9. Mission Control Center Operations Interface',
    subtitle: 'Aerospace Operations Console with Live 3D Earth & Real-Time Telemetry',
    body: 'A full-featured Python/Flask operations console featuring an interactive Three.js 3D Earth, real-time WebSocket telemetry stream, multi-horizon prediction curves, dynamic scenario stress-testing injection, and side-by-side 4-method benchmark visualization.'
  },
  {
    title: '10. Research Contributions & Scientific Novelty',
    subtitle: 'Five Distinct Academic & Engineering Breakthroughs',
    body: '(1) Physics-grounded SAGIN simulator compliant with 3GPP NTN standards; (2) Dual-uncertainty channel forecasting separating aleatoric flutter from epistemic risk; (3) Conformal prediction framework guaranteeing finite-sample coverage for 6G URLLC; (4) CAPRO optimization formulation with hard reliability constraints; and (5) Reproducible 400-trial Monte Carlo benchmark framework.'
  },
  {
    title: '11. Project Contributors & Research Collaboration',
    subtitle: 'Slock Ahuja & Dr. Praveen Kumar Sharma — Equal Research Co-Creators',
    body: 'Co-created by Slock Ahuja (Project Co-Creator, Research Contributor & Mission Control Developer) and Dr. Praveen Kumar Sharma (Research Mentor, Technical Contributor & Project Co-Creator; Professor & Head, Department of ECE, MIT-ADT University Pune; Focus: Antennas, metamaterials, wearable devices & machine learning). Prepared for IEEE ComSoc STLC Tunisia 2026.'
  }
];

function initPresentationMode() {
  const modal = document.getElementById('presentationModal');
  const openBtns = document.querySelectorAll('[data-open-presentation]');
  const closeBtn = document.getElementById('presCloseBtn');
  const prevBtn = document.getElementById('presPrevBtn');
  const nextBtn = document.getElementById('presNextBtn');
  const fullBtn = document.getElementById('presFullscreenBtn');
  const titleEl = document.getElementById('presSlideTitle');
  const subEl = document.getElementById('presSlideSubtitle');
  const bodyEl = document.getElementById('presSlideBody');
  const indEl = document.getElementById('presSlideIndicator');

  if (!modal || !openBtns.length) return;

  let currentSlide = 0;

  function renderSlide(idx) {
    currentSlide = Math.max(0, Math.min(idx, presentationSlides.length - 1));
    const s = presentationSlides[currentSlide];

    titleEl.textContent = s.title;
    subEl.textContent = s.subtitle;
    bodyEl.textContent = s.body;
    indEl.textContent = `Slide ${currentSlide + 1} of ${presentationSlides.length}`;

    prevBtn.disabled = currentSlide === 0;
    nextBtn.disabled = currentSlide === presentationSlides.length - 1;
  }

  function openPresentation() {
    renderSlide(0);
    modal.classList.add('active');
  }

  function closePresentation() {
    modal.classList.remove('active');
    if (document.fullscreenElement) {
      document.exitFullscreen().catch(() => {});
    }
  }

  openBtns.forEach(b => b.addEventListener('click', openPresentation));
  if (closeBtn) closeBtn.addEventListener('click', closePresentation);

  if (prevBtn) prevBtn.addEventListener('click', () => renderSlide(currentSlide - 1));
  if (nextBtn) nextBtn.addEventListener('click', () => renderSlide(currentSlide + 1));

  if (fullBtn) {
    fullBtn.addEventListener('click', () => {
      if (!document.fullscreenElement) {
        modal.requestFullscreen().catch(() => {});
      } else {
        document.exitFullscreen().catch(() => {});
      }
    });
  }

  document.addEventListener('keydown', (e) => {
    if (!modal.classList.contains('active')) return;
    if (e.key === 'ArrowRight' || e.key === 'Space') {
      renderSlide(currentSlide + 1);
    } else if (e.key === 'ArrowLeft') {
      renderSlide(currentSlide - 1);
    } else if (e.key === 'Escape') {
      closePresentation();
    }
  });
}

/* ==========================================================================
   16. Floating Back-to-Top Control
   ========================================================================== */
function initBackToTop() {
  const backTopBtn = document.getElementById('backToTopBtn');
  if (!backTopBtn) return;

  window.addEventListener('scroll', () => {
    if (window.scrollY > 400) {
      backTopBtn.classList.add('visible');
    } else {
      backTopBtn.classList.remove('visible');
    }
  });

  backTopBtn.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
}

/* ==========================================================================
   17. Clipboard Copy Buttons
   ========================================================================== */
function initCopyButtons() {
  document.querySelectorAll('[data-copy-target]').forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-copy-target');
      const targetEl = document.getElementById(targetId);
      if (!targetEl) return;

      const text = targetEl.innerText || targetEl.textContent;
      navigator.clipboard.writeText(text.trim()).then(() => {
        const origText = btn.innerHTML;
        btn.innerHTML = '✓ Copied!';
        setTimeout(() => {
          btn.innerHTML = origText;
        }, 2000);
      }).catch(err => {
        console.error('Copy failed:', err);
      });
    });
  });
}
