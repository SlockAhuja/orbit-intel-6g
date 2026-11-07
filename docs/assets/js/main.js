/**
 * ORBIT-INTEL 6G — Official Showcase Script
 * Handles 3D Earth visualization, telemetry stream, interactive tabs,
 * metric animations, clipboard actions, and lightbox viewer.
 */

document.addEventListener('DOMContentLoaded', () => {
  initNavbar();
  initCounters();
  initTierTabs();
  initHeroGlobe();
  initTelemetryHUD();
  initLightbox();
  initCopyButtons();
});

/* ==========================================================================
   Navigation
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
   Metrics Counter Animation
   ========================================================================== */
function initCounters() {
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
        const duration = 1800; // ms
        const startTime = performance.now();

        function updateCounter(currentTime) {
          const elapsed = currentTime - startTime;
          const progress = Math.min(elapsed / duration, 1);
          // Ease out cubic
          const easeProgress = 1 - Math.pow(1 - progress, 3);
          const currentVal = easeProgress * target;

          el.textContent = `${prefix}${currentVal.toFixed(decimals)}${suffix}`;

          if (progress < 1) {
            requestAnimationFrame(updateCounter);
          } else {
            el.textContent = `${prefix}${target.toFixed(decimals)}${suffix}`;
          }
        }

        requestAnimationFrame(updateCounter);
        obs.unobserve(el);
      }
    });
  }, { threshold: 0.3 });

  counters.forEach(c => observer.observe(c));
}

/* ==========================================================================
   Architecture Multi-Tier Tabs
   ========================================================================== */
const tierData = {
  space: {
    title: 'Space Layer: Low Earth Orbit (LEO) Constellation',
    meta: 'ALTITUDE: 550 - 650 km | NODES: 6 Keplerian Satellites | BAND: Ka/S-Band (28 GHz / 2 GHz)',
    desc: 'Six distributed LEO satellite nodes operating in 86° inclined circular orbits. Features inter-satellite cross-links (ISLs), dynamic Doppler shift compensation (±37.4 kHz), and high-gain phased-array beamforming to provide resilient global coverage.',
    specs: [
      { k: 'Orbital Velocity', v: '7.56 km/s' },
      { k: 'Orbit Period', v: '96.2 min' },
      { k: 'Visibility Window', v: '8 - 14 min' },
      { k: 'Doppler Shift', v: '±37.4 kHz' }
    ],
    icon: '🛰️'
  },
  stratospheric: {
    title: 'Stratospheric Layer: High Altitude Platform Stations (HAPS)',
    meta: 'ALTITUDE: 20 km (Stratosphere) | NODES: 2 Super-Macro Relays | BAND: Sub-6 GHz / E-Band',
    desc: 'Quasi-stationary stratospheric airships positioned at 20 km altitude. Delivers persistent broad-area coverage (footprint radius > 80 km) acting as ultra-reliable aerial edge gateways between space assets and ground terminals.',
    specs: [
      { k: 'Footprint Radius', v: '~80 km' },
      { k: 'Propagation Latency', v: '0.067 ms' },
      { k: 'Wind Compensation', v: 'Dynamic 3D Vectoring' },
      { k: 'Role', v: 'Resilient Edge Gateway' }
    ],
    icon: '🎈'
  },
  aerial: {
    title: 'Aerial Layer: Tactical Unmanned Aerial Vehicles (UAVs)',
    meta: 'ALTITUDE: 300 m AGL | NODES: 4 Mobile UAV Hubs | BAND: Sub-6 GHz / mmWave',
    desc: 'Four mobile aerial edge compute nodes deployed dynamically in response to ground congestion or emergency clusters. Provides sub-millisecond line-of-sight (LoS) links and local queue buffering for terrestrial offloading.',
    specs: [
      { k: 'Deployment Speed', v: '18 m/s' },
      { k: 'LoS Probability', v: '> 92%' },
      { k: 'Local Processing Delay', v: '0.50 ms' },
      { k: 'Handover Margin', v: 'Adaptive RSSI' }
    ],
    icon: '🛸'
  },
  terrestrial: {
    title: 'Terrestrial Layer: Base Stations & Satellite Gateways',
    meta: 'ALTITUDE: Ground Surface (0-30 m) | NODES: Optical/RF Feeder Gateways & gNBs',
    desc: 'Ground network infrastructure incorporating high-capacity optical feeder gateways, terrestrial cellular gNodeBs, and centralized edge-datacenter orchestration controllers running the CAPRO inference pipeline.',
    specs: [
      { k: 'Feeder Link Capacity', v: '10 Gbps (Optical/Ka)' },
      { k: 'Feeder Latency', v: '1.20 ms' },
      { k: 'Central Pipeline Loop', v: '100 ms' },
      { k: 'Reliability Standard', v: '3GPP Rel-17/18 NTN' }
    ],
    icon: '🗼'
  },
  user: {
    title: 'User Layer: Heterogeneous 6G Terminal Clustered UEs',
    meta: 'POPULATION: 12 Active Scenario UEs | MOBILITY: 0 - 250 km/h | MODES: URLLC / eMBB',
    desc: 'Diverse ground mobile equipment spanning emergency search-and-rescue teams, autonomous connected vehicles (V2X), maritime vessels, smart wearables, and dense urban hot-spots demanding sub-10ms end-to-end latency.',
    specs: [
      { k: 'URLLC Latency Target', v: '≤ 10.0 ms' },
      { k: 'Minimum SINR Threshold', v: '3.0 dB' },
      { k: 'Packet Delivery Ratio', v: '99.41% (CAPRO)' },
      { k: 'Outage Probability', v: '0.59%' }
    ],
    icon: '📱'
  }
};

function initTierTabs() {
  const tabs = document.querySelectorAll('.tier-tab');
  const titleEl = document.getElementById('tierTitle');
  const metaEl = document.getElementById('tierMeta');
  const descEl = document.getElementById('tierDesc');
  const specsEl = document.getElementById('tierSpecs');
  const iconEl = document.getElementById('tierIconCenter');

  if (!tabs.length || !titleEl) return;

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      const tierKey = tab.getAttribute('data-tier');
      const data = tierData[tierKey];
      if (!data) return;

      titleEl.textContent = data.title;
      metaEl.textContent = data.meta;
      descEl.textContent = data.desc;
      iconEl.textContent = data.icon;

      specsEl.innerHTML = data.specs.map(s => `
        <div class="spec-box">
          <div class="k">${s.k}</div>
          <div class="v">${s.v}</div>
        </div>
      `).join('');
    });
  });
}

/* ==========================================================================
   Three.js Hero 3D Earth Globe
   ========================================================================== */
function initHeroGlobe() {
  const container = document.getElementById('heroGlobeContainer');
  if (!container || typeof THREE === 'undefined') return;

  const width = container.clientWidth || 600;
  const height = container.clientHeight || 550;

  // Scene & Camera
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
  camera.position.set(0, 5, 14);

  // Renderer
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setSize(width, height);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  container.appendChild(renderer.domElement);

  // Lights
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.85);
  scene.add(ambientLight);

  const dirLight = new THREE.DirectionalLight(0x00f0ff, 1.2);
  dirLight.position.set(10, 10, 10);
  scene.add(dirLight);

  const violetLight = new THREE.DirectionalLight(0x8b5cf6, 0.8);
  violetLight.position.set(-10, -5, -5);
  scene.add(violetLight);

  // Earth Group
  const earthGroup = new THREE.Group();
  scene.add(earthGroup);

  // Earth Sphere
  const sphereGeo = new THREE.SphereGeometry(4.2, 48, 48);
  const textureLoader = new THREE.TextureLoader();

  // Try loading textures, with fallback material
  const earthMat = new THREE.MeshPhongMaterial({
    color: 0x0f2a4a,
    emissive: 0x051329,
    specular: 0x00f0ff,
    shininess: 15,
    wireframe: false
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
      // If image fails, switch to high-tech wireframe mode
      earthMat.wireframe = true;
      earthMat.color.setHex(0x00f0ff);
    }
  );

  const earthMesh = new THREE.Mesh(sphereGeo, earthMat);
  earthGroup.add(earthMesh);

  // Outer Atmosphere Glow
  const atmosGeo = new THREE.SphereGeometry(4.35, 32, 32);
  const atmosMat = new THREE.MeshBasicMaterial({
    color: 0x00f0ff,
    transparent: true,
    opacity: 0.12,
    side: THREE.BackSide
  });
  const atmosMesh = new THREE.Mesh(atmosGeo, atmosMat);
  earthGroup.add(atmosMesh);

  // Orbital Rings & Satellites
  const orbits = [
    { radius: 6.2, inclX: 0.45, inclZ: 0.2, speed: 0.008, color: 0x00f0ff, satName: 'LEO-SAT-1' },
    { radius: 6.6, inclX: -0.65, inclZ: 0.4, speed: 0.006, color: 0x38bdf8, satName: 'LEO-SAT-2' },
    { radius: 7.0, inclX: 0.85, inclZ: -0.3, speed: 0.007, color: 0x8b5cf6, satName: 'LEO-SAT-3' },
    { radius: 7.4, inclX: -0.2, inclZ: -0.7, speed: 0.005, color: 0x10b981, satName: 'LEO-SAT-4' }
  ];

  const satObjects = [];

  orbits.forEach(orb => {
    // Ring curve
    const curve = new THREE.EllipseCurve(
      0, 0,
      orb.radius, orb.radius,
      0, 2 * Math.PI,
      false, 0
    );
    const points = curve.getPoints(90);
    const ringGeo = new THREE.BufferGeometry().setFromPoints(
      points.map(p => new THREE.Vector3(p.x, 0, p.y))
    );
    const ringMat = new THREE.LineBasicMaterial({
      color: orb.color,
      transparent: true,
      opacity: 0.35
    });
    const ringLine = new THREE.Line(ringGeo, ringMat);
    ringLine.rotation.x = orb.inclX;
    ringLine.rotation.z = orb.inclZ;
    scene.add(ringLine);

    // Satellite marker
    const satGeo = new THREE.SphereGeometry(0.18, 16, 16);
    const satMat = new THREE.MeshBasicMaterial({ color: orb.color });
    const satMesh = new THREE.Mesh(satGeo, satMat);

    // Beam Line to Earth
    const beamGeo = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(0, 0, 0),
      new THREE.Vector3(0, 0, 0)
    ]);
    const beamMat = new THREE.LineDashedMaterial({
      color: orb.color,
      dashSize: 0.2,
      gapSize: 0.1,
      transparent: true,
      opacity: 0.5
    });
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

  // Mouse interaction controls
  let controls = null;
  if (typeof THREE.OrbitControls !== 'undefined') {
    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.enableZoom = false;
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.6;
  }

  // Animation Loop
  function animate() {
    requestAnimationFrame(animate);

    earthGroup.rotation.y += 0.0015;

    satObjects.forEach(sat => {
      sat.angle += sat.orbit.speed;

      // Position along rotated plane
      const unrotX = Math.cos(sat.angle) * sat.orbit.radius;
      const unrotZ = Math.sin(sat.angle) * sat.orbit.radius;
      const pos = new THREE.Vector3(unrotX, 0, unrotZ);

      // Apply rotations
      pos.applyAxisAngle(new THREE.Vector3(1, 0, 0), sat.orbit.inclX);
      pos.applyAxisAngle(new THREE.Vector3(0, 0, 1), sat.orbit.inclZ);

      sat.mesh.position.copy(pos);

      // Update beam down to Earth surface
      const groundPos = pos.clone().normalize().multiplyScalar(4.2);
      const positions = sat.beam.geometry.attributes.position.array;
      positions[0] = pos.x;
      positions[1] = pos.y;
      positions[2] = pos.z;
      positions[3] = groundPos.x;
      positions[4] = groundPos.y;
      positions[5] = groundPos.z;
      sat.beam.geometry.attributes.position.needsUpdate = true;
      sat.beam.computeLineDistances();
    });

    if (controls) {
      controls.update();
    } else {
      camera.lookAt(scene.position);
    }

    renderer.render(scene, camera);
  }

  animate();

  // Resize Handler
  window.addEventListener('resize', () => {
    const newWidth = container.clientWidth || 600;
    const newHeight = container.clientHeight || 550;
    camera.aspect = newWidth / newHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(newWidth, newHeight);
  });
}

/* ==========================================================================
   Real-Time Telemetry HUD Simulation
   ========================================================================== */
function initTelemetryHUD() {
  const satIdEl = document.getElementById('hudSatId');
  const sinrEl = document.getElementById('hudSinr');
  const delayEl = document.getElementById('hudDelay');
  const pdrEl = document.getElementById('hudPdr');
  const dopplerEl = document.getElementById('hudDoppler');

  if (!sinrEl) return;

  const sats = ['LEO-SAT-1 (Kepler)', 'LEO-SAT-2 (Kepler)', 'LEO-SAT-3 (Kepler)', 'HAPS-01 (Stratosphere)', 'UAV-02 (Tactical Edge)'];
  let satIdx = 0;

  setInterval(() => {
    satIdx = (satIdx + 1) % sats.length;
    if (satIdEl) satIdEl.textContent = sats[satIdx];

    // Dynamic telemetry fluctuations within verified physical ranges
    const sinr = (18.2 + (Math.random() * 2.8 - 1.4)).toFixed(1);
    const delay = (6.4 + (Math.random() * 0.8 - 0.4)).toFixed(2);
    const pdr = (99.3 + (Math.random() * 0.3)).toFixed(2);
    const dop = (Math.random() > 0.5 ? '+' : '-') + (14.2 + Math.random() * 8.5).toFixed(1);

    sinrEl.textContent = `${sinr} dB`;
    delayEl.textContent = `${delay} ms`;
    pdrEl.textContent = `${pdr}%`;
    if (dopplerEl) dopplerEl.textContent = `${dop} kHz`;
  }, 2200);
}

/* ==========================================================================
   Lightbox Image Viewer
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
    if (e.key === 'Escape' && modal.classList.contains('active')) {
      closeModal();
    }
  });
}

/* ==========================================================================
   Clipboard Copy Buttons
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
