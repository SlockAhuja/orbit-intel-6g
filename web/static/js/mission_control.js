/**
 * ORBIT-INTEL 6G: Global Network Intelligence & Mission Control Center
 * Three.js 3D Constellation, Orbital Telemetry, and Interactive Operations Engine.
 * Target: IEEE ComSoc STLC 2026 Showcase.
 */

// Global State
let scene, camera, renderer, controls;
let earthMesh, cloudMesh, atmosphereMesh;
let nodesGroup, orbitsGroup, beamsGroup, usersGroup;
let currentState = null;
let selectedEntityId = "SAT-01";
let selectedUserId = "UE-01";
let activeTab = "telemetry";
let raycaster, mouse;
let experimentChart = null;

const EARTH_RADIUS = 1.0;
const LEO_ALTITUDE = 600.0 / 6371.0;   // ~0.094
const HAPS_ALTITUDE = 20.0 / 6371.0;   // ~0.0031
const UAV_ALTITUDE = 0.3 / 6371.0;     // ~0.00005

// Color Palette
const COLORS = {
    LEO: 0x00e5ff,
    HAPS: 0xffd600,
    UAV: 0xff9100,
    TBS: 0x00e676,
    UE: 0xe040fb,
    BEAM_ACTIVE: 0x00e676,
    BEAM_CANDIDATE: 0xffab00,
};

// Map lat/lon to 3D Cartesian coordinates
function latLonToVector3(latDeg, lonDeg, radius = EARTH_RADIUS) {
    const phi = (90 - latDeg) * (Math.PI / 180);
    const theta = (lonDeg + 180) * (Math.PI / 180);
    const x = -(radius * Math.sin(phi) * Math.cos(theta));
    const z = (radius * Math.sin(phi) * Math.sin(theta));
    const y = (radius * Math.cos(phi));
    return new THREE.Vector3(x, y, z);
}

// -----------------------------------------------------------------------------
// 1. Initialize Three.js 3D SAGIN Earth & Viewport
// -----------------------------------------------------------------------------
function initThreeScene() {
    const container = document.getElementById("globe-canvas-container");
    const width = container.clientWidth;
    const height = container.clientHeight;

    // Scene & Camera
    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(45, width / height, 0.05, 100);
    camera.position.set(2.2, 1.4, 2.4);

    // Renderer
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;
    container.appendChild(renderer.domElement);

    // Orbit Controls
    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.minDistance = 1.25;
    controls.maxDistance = 5.5;

    // Lighting
    const ambientLight = new THREE.AmbientLight(0x1a2942, 1.2);
    scene.add(ambientLight);

    const sunLight = new THREE.DirectionalLight(0xffffff, 2.0);
    sunLight.position.set(5, 3, 5);
    scene.add(sunLight);

    const blueRimLight = new THREE.DirectionalLight(0x00e5ff, 0.8);
    blueRimLight.position.set(-5, -2, -4);
    scene.add(blueRimLight);

    // Starfield Background
    createStarfield();

    // Earth Sphere
    const textureLoader = new THREE.TextureLoader();
    const earthTexture = textureLoader.load("/static/assets/earth.jpg");
    
    const earthGeo = new THREE.SphereGeometry(EARTH_RADIUS, 64, 64);
    const earthMat = new THREE.MeshPhongMaterial({
        map: earthTexture,
        shininess: 15,
        specular: new THREE.Color(0x223344),
    });
    earthMesh = new THREE.Mesh(earthGeo, earthMat);
    scene.add(earthMesh);

    // Cloud Layer
    const cloudTexture = textureLoader.load("/static/assets/earth_clouds.jpg");
    const cloudGeo = new THREE.SphereGeometry(EARTH_RADIUS * 1.012, 64, 64);
    const cloudMat = new THREE.MeshPhongMaterial({
        map: cloudTexture,
        transparent: true,
        opacity: 0.35,
        blending: THREE.AdditiveBlending,
    });
    cloudMesh = new THREE.Mesh(cloudGeo, cloudMat);
    scene.add(cloudMesh);

    // Atmosphere Glow Shader
    createAtmosphereGlow();

    // Scene Groups
    orbitsGroup = new THREE.Group();
    nodesGroup = new THREE.Group();
    beamsGroup = new THREE.Group();
    usersGroup = new THREE.Group();

    scene.add(orbitsGroup);
    scene.add(nodesGroup);
    scene.add(beamsGroup);
    scene.add(usersGroup);

    // Raycaster for click selection
    raycaster = new THREE.Raycaster();
    mouse = new THREE.Vector2();
    renderer.domElement.addEventListener("click", onSceneClick, false);

    window.addEventListener("resize", onWindowResize, false);

    // Start Animation Loop
    animate();
}

function createStarfield() {
    const starsGeo = new THREE.BufferGeometry();
    const count = 1800;
    const positions = new Float32Array(count * 3);
    for (let i = 0; i < count * 3; i += 3) {
        positions[i] = (Math.random() - 0.5) * 80;
        positions[i + 1] = (Math.random() - 0.5) * 80;
        positions[i + 2] = (Math.random() - 0.5) * 80;
    }
    starsGeo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    const starsMat = new THREE.PointsMaterial({ color: 0x88bbff, size: 0.12, transparent: true, opacity: 0.8 });
    const starField = new THREE.Points(starsGeo, starsMat);
    scene.add(starField);
}

function createAtmosphereGlow() {
    const atmosGeo = new THREE.SphereGeometry(EARTH_RADIUS * 1.15, 48, 48);
    const atmosMat = new THREE.ShaderMaterial({
        vertexShader: `
            varying vec3 vNormal;
            void main() {
                vNormal = normalize(normalMatrix * normal);
                gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
            }
        `,
        fragmentShader: `
            varying vec3 vNormal;
            void main() {
                float intensity = pow(0.65 - dot(vNormal, vec3(0.0, 0.0, 1.0)), 2.5);
                gl_FragColor = vec4(0.0, 0.85, 1.0, 1.0) * intensity * 0.7;
            }
        `,
        blending: THREE.AdditiveBlending,
        side: THREE.BackSide,
        transparent: true,
    });
    atmosphereMesh = new THREE.Mesh(atmosGeo, atmosMat);
    scene.add(atmosphereMesh);
}

function animate() {
    requestAnimationFrame(animate);

    // Gentle axial rotation
    if (earthMesh) earthMesh.rotation.y += 0.0003;
    if (cloudMesh) cloudMesh.rotation.y += 0.00045;

    controls.update();
    renderer.render(scene, camera);
}

function onWindowResize() {
    const container = document.getElementById("globe-canvas-container");
    if (!container) return;
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
}

function onSceneClick(event) {
    const rect = renderer.domElement.getBoundingClientRect();
    mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    raycaster.setFromCamera(mouse, camera);
    const intersects = raycaster.intersectObjects(nodesGroup.children, true);

    if (intersects.length > 0) {
        let obj = intersects[0].object;
        while (obj.parent && !obj.userData.nodeId) {
            obj = obj.parent;
        }
        if (obj.userData.nodeId) {
            selectEntity(obj.userData.nodeId);
        }
    }
}


// -----------------------------------------------------------------------------
// 2. Build 3D Constellation Nodes & Orbit Rings
// -----------------------------------------------------------------------------
function update3DConstellation(state) {
    if (!state || !state.nodes) return;

    // Clear previous dynamic meshes
    while (nodesGroup.children.length > 0) nodesGroup.remove(nodesGroup.children[0]);
    while (orbitsGroup.children.length > 0) orbitsGroup.remove(orbitsGroup.children[0]);
    while (beamsGroup.children.length > 0) beamsGroup.remove(beamsGroup.children[0]);
    while (usersGroup.children.length > 0) usersGroup.remove(usersGroup.children[0]);

    // 1. Orbital Rings for LEO Satellites
    const rOrbit = EARTH_RADIUS + LEO_ALTITUDE;
    ["SAT-01", "SAT-02"].forEach((satId, idx) => {
        const ringGeo = new THREE.RingGeometry(rOrbit - 0.002, rOrbit + 0.002, 90);
        const ringMat = new THREE.MeshBasicMaterial({
            color: 0x00e5ff,
            side: THREE.DoubleSide,
            transparent: true,
            opacity: 0.28,
        });
        const ring = new THREE.Mesh(ringGeo, ringMat);
        ring.rotation.x = Math.PI / 2;
        ring.rotation.y = (53.0 * Math.PI) / 180; // 53° inclination
        ring.rotation.z = (idx * 45.0 * Math.PI) / 180;
        orbitsGroup.add(ring);
    });

    // 2. Add Network Nodes
    Object.values(state.nodes).forEach(node => {
        let rPos = EARTH_RADIUS;
        let color = COLORS.TBS;
        let size = 0.02;

        if (node.tier === "LEO") {
            rPos = EARTH_RADIUS + LEO_ALTITUDE;
            color = COLORS.LEO;
            size = 0.035;
        } else if (node.tier === "HAPS") {
            rPos = EARTH_RADIUS + (HAPS_ALTITUDE * 12); // scale slightly for visibility
            color = COLORS.HAPS;
            size = 0.028;
        } else if (node.tier === "UAV") {
            rPos = EARTH_RADIUS + (UAV_ALTITUDE * 40);
            color = COLORS.UAV;
            size = 0.024;
        }

        const pos = latLonToVector3(node.lat_deg, node.lon_deg, rPos);

        // Satellite / Node Mesh
        const nodeObj = new THREE.Group();
        nodeObj.position.copy(pos);
        nodeObj.userData = { nodeId: node.id, tier: node.tier, name: node.name };

        // Center Marker Core
        const coreGeo = new THREE.SphereGeometry(size, 16, 16);
        const coreMat = new THREE.MeshBasicMaterial({ color: color });
        const coreMesh = new THREE.Mesh(coreGeo, coreMat);
        nodeObj.add(coreMesh);

        // If LEO Satellite: add solar panel wings
        if (node.tier === "LEO") {
            const panelGeo = new THREE.BoxGeometry(size * 2.8, size * 0.1, size * 0.8);
            const panelMat = new THREE.MeshPhongMaterial({ color: 0x1e3a8a, specular: 0x00e5ff });
            const panels = new THREE.Mesh(panelGeo, panelMat);
            nodeObj.add(panels);
        }

        // Selection highlight ring
        if (node.id === selectedEntityId) {
            const auraGeo = new THREE.RingGeometry(size * 1.5, size * 2.2, 24);
            const auraMat = new THREE.MeshBasicMaterial({ color: 0x00e5ff, side: THREE.DoubleSide });
            const auraMesh = new THREE.Mesh(auraGeo, auraMat);
            auraMesh.lookAt(camera.position);
            nodeObj.add(auraMesh);
        }

        nodesGroup.add(nodeObj);
    });

    // 3. Add User Terminals
    Object.values(state.users).forEach(ue => {
        const uePos = latLonToVector3(ue.lat_deg, ue.lon_deg, EARTH_RADIUS * 1.002);
        const ueGeo = new THREE.SphereGeometry(0.012, 12, 12);
        const ueMat = new THREE.MeshBasicMaterial({ color: COLORS.UE });
        const ueMesh = new THREE.Mesh(ueGeo, ueMat);
        ueMesh.position.copy(uePos);
        ueMesh.userData = { userId: ue.id, service: ue.service_type };
        usersGroup.add(ueMesh);
    });

    // 4. Render Active Serving Beam
    if (state.users && state.users[selectedUserId]) {
        const ue = state.users[selectedUserId];
        const srvId = ue.serving_node_id;
        if (srvId && state.nodes[srvId]) {
            const srvNode = state.nodes[srvId];
            let rSrv = EARTH_RADIUS + (srvNode.tier === "LEO" ? LEO_ALTITUDE : (srvNode.tier === "HAPS" ? HAPS_ALTITUDE * 12 : 0.005));
            const uePos = latLonToVector3(ue.lat_deg, ue.lon_deg, EARTH_RADIUS * 1.002);
            const srvPos = latLonToVector3(srvNode.lat_deg, srvNode.lon_deg, rSrv);

            const lineGeo = new THREE.BufferGeometry().setFromPoints([uePos, srvPos]);
            const lineMat = new THREE.LineBasicMaterial({ color: COLORS.BEAM_ACTIVE, linewidth: 3 });
            const beam = new THREE.Line(lineGeo, lineMat);
            beamsGroup.add(beam);
        }
    }

    // Draw Mini 2D Ground-Track Map
    drawGroundTrack(state);
}

// -----------------------------------------------------------------------------
// 3. Mini 2D Ground Track Inset Canvas
// -----------------------------------------------------------------------------
function drawGroundTrack(state) {
    const canvas = document.getElementById("ground-track-canvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const w = canvas.width = canvas.clientWidth;
    const h = canvas.height = canvas.clientHeight;

    // Clear background
    ctx.fillStyle = "#070f1e";
    ctx.fillRect(0, 0, w, h);

    // Draw grid lines
    ctx.strokeStyle = "rgba(0, 229, 255, 0.12)";
    ctx.lineWidth = 1;
    for (let x = 0; x < w; x += 35) {
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
    }
    for (let y = 0; y < h; y += 20) {
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
    }

    // Equator & Greenwich Meridian
    ctx.strokeStyle = "rgba(0, 229, 255, 0.3)";
    ctx.beginPath(); ctx.moveTo(0, h / 2); ctx.lineTo(w, h / 2); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(w / 2, 0); ctx.lineTo(w / 2, h); ctx.stroke();

    if (!state || !state.nodes) return;

    // Draw Satellites Ground Tracks
    ["SAT-01", "SAT-02"].forEach((satId, idx) => {
        const sat = state.nodes[satId];
        if (!sat) return;

        // Sub-satellite point
        const sx = ((sat.lon_deg + 180) / 360) * w;
        const sy = ((-sat.lat_deg + 90) / 180) * h;

        // Sine ground-track wave
        ctx.strokeStyle = idx === 0 ? "rgba(0, 229, 255, 0.6)" : "rgba(255, 214, 0, 0.6)";
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        for (let t = -180; t <= 180; t += 5) {
            const gx = ((t + 180) / 360) * w;
            const gy = ((-53.0 * Math.sin((t - sat.lon_deg) * (Math.PI / 180)) + 90) / 180) * h;
            if (t === -180) ctx.moveTo(gx, gy);
            else ctx.lineTo(gx, gy);
        }
        ctx.stroke();

        // Satellite position dot
        ctx.fillStyle = idx === 0 ? "#00e5ff" : "#ffd600";
        ctx.beginPath();
        ctx.arc(sx, sy, 3.5, 0, 2 * Math.PI);
        ctx.fill();

        // Label
        ctx.fillStyle = "#ffffff";
        ctx.font = "9px monospace";
        ctx.fillText(sat.id, sx + 5, sy - 3);
    });
}


// -----------------------------------------------------------------------------
// 4. Telemetry Panels & HUD Update
// -----------------------------------------------------------------------------
function updateTelemetryPanels(state) {
    if (!state) return;

    // 1. Update Top Bar Badges
    document.getElementById("top-scenario-badge").textContent = state.scenario ? state.scenario.name : "Normal";
    document.getElementById("top-epoch-text").textContent = `T+${String(state.epoch_seconds).padStart(2, '0')}s`;
    
    // UTC Clock
    const now = new Date();
    document.getElementById("top-utc-clock").textContent = `${now.toISOString().substring(11, 19)} UTC`;

    // 2. Update HUD Overlay
    const targetNode = state.nodes[selectedEntityId] || state.nodes["SAT-01"];
    if (targetNode) {
        document.getElementById("hud-entity-name").textContent = `${targetNode.id} [${targetNode.name}]`;
        document.getElementById("hud-alt-val").textContent = `${targetNode.alt_km.toFixed(1)} km`;
        document.getElementById("hud-vel-val").textContent = `${targetNode.speed_km_s.toFixed(2)} km/s`;
        document.getElementById("hud-lat-val").textContent = `${targetNode.lat_deg.toFixed(2)}°`;
        document.getElementById("hud-lon-val").textContent = `${targetNode.lon_deg.toFixed(2)}°`;
    }

    // 3. Update Right Telemetry Tabs
    const lKey = `${selectedUserId}_${selectedEntityId}`;
    const link = state.links ? state.links[lKey] : null;

    if (activeTab === "telemetry") {
        document.getElementById("telem-alt").textContent = `${targetNode.alt_km.toFixed(1)} km`;
        document.getElementById("telem-vel").textContent = `${targetNode.speed_km_s.toFixed(2)} km/s`;
        document.getElementById("telem-incl").textContent = "53.0°";
        document.getElementById("telem-load").textContent = `${(targetNode.current_load * 100).toFixed(1)}%`;
        
        if (link) {
            document.getElementById("telem-elev").textContent = `${link.elevation_deg.toFixed(2)}°`;
            document.getElementById("telem-slant").textContent = `${link.slant_distance_km.toFixed(1)} km`;
            document.getElementById("telem-dop").textContent = `${link.doppler_shift_khz > 0 ? '+' : ''}${link.doppler_shift_khz.toFixed(2)} kHz`;
            document.getElementById("telem-vis").textContent = `${link.remaining_visibility_s.toFixed(0)} s (${link.is_visible ? 'LoS OK' : 'CUTOFF'})`;
        }
    } else if (activeTab === "qos") {
        if (link) {
            document.getElementById("qos-sinr").textContent = `${link.sinr_db.toFixed(1)} dB`;
            document.getElementById("qos-prop-delay").textContent = `${link.propagation_delay_ms.toFixed(2)} ms`;
            document.getElementById("qos-total-lat").textContent = `${link.total_latency_ms.toFixed(2)} ms`;
            document.getElementById("qos-fspl").textContent = `${link.path_loss_db.toFixed(1)} dB`;
            document.getElementById("qos-sla").textContent = link.total_latency_ms <= 10.0 ? "✅ PASS (<10ms)" : "⚠️ VIOLATION";
        }
    } else if (activeTab === "ai") {
        fetchAIPrediction(selectedUserId, selectedEntityId);
    }

    // 4. Update Bottom Event Log
    if (state.recent_events) {
        const logContainer = document.getElementById("event-log-list");
        logContainer.innerHTML = "";
        state.recent_events.forEach(evt => {
            const item = document.createElement("div");
            item.className = `log-entry ${evt.severity}`;
            item.innerHTML = `<span class="log-ts">[${evt.timestamp}]</span> <span class="log-src">[${evt.source}]</span> <span class="log-msg">${evt.message}</span>`;
            logContainer.appendChild(item);
        });
        logContainer.scrollTop = logContainer.scrollHeight;
    }
}

function fetchAIPrediction(userId, nodeId) {
    fetch(`/api/predict?user_id=${userId}&node_id=${nodeId}&horizon=5`)
        .then(r => r.json())
        .then(data => {
            document.getElementById("ai-pred-sinr").textContent = `${data.current_pred.toFixed(2)} dB`;
            document.getElementById("ai-qlow").textContent = `${data.current_ql.toFixed(2)} dB`;
            document.getElementById("ai-qupp").textContent = `${data.current_qu.toFixed(2)} dB`;
            document.getElementById("ai-aleatoric").textContent = `${data.aleatoric_width.toFixed(2)} dB`;
            document.getElementById("ai-epistemic").textContent = `${data.epistemic_std.toFixed(2)} dB`;
            
            const hazardPill = document.getElementById("ai-hazard-pill");
            if (data.is_outage_hazard) {
                hazardPill.textContent = "⚠️ OUTAGE HAZARD DETECTED";
                hazardPill.className = "hazard-alert-pill active";
            } else {
                hazardPill.textContent = "✅ CHANNEL STABLE";
                hazardPill.className = "hazard-alert-pill safe";
            }
        });
}

function selectEntity(nodeId) {
    selectedEntityId = nodeId;
    document.querySelectorAll(".nav-entity-item").forEach(el => el.classList.remove("active"));
    const el = document.getElementById(`nav-node-${nodeId}`);
    if (el) el.classList.add("active");
    if (currentState) update3DConstellation(currentState);
    updateTelemetryPanels(currentState);
}


// -----------------------------------------------------------------------------
// 5. REST API Control Actions
// -----------------------------------------------------------------------------
function stepSimulation(steps = 1) {
    fetch("/api/step", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ steps: steps })
    })
    .then(r => r.json())
    .then(state => {
        currentState = state;
        update3DConstellation(state);
        updateTelemetryPanels(state);
    });
}

function resetSimulation() {
    fetch("/api/reset", { method: "POST" })
    .then(r => r.json())
    .then(state => {
        currentState = state;
        update3DConstellation(state);
        updateTelemetryPanels(state);
    });
}

function loadScenario(scId) {
    fetch(`/api/scenario/${scId}`, { method: "POST" })
    .then(r => r.json())
    .then(state => {
        currentState = state;
        update3DConstellation(state);
        updateTelemetryPanels(state);
    });
}

function pollState() {
    fetch("/api/state")
    .then(r => r.json())
    .then(state => {
        currentState = state;
        update3DConstellation(state);
        updateTelemetryPanels(state);
    })
    .catch(err => console.error("Poll state error:", err));
}


// -----------------------------------------------------------------------------
// 6. Interactive Experiment Modal & Chart.js
// -----------------------------------------------------------------------------
function openExperimentModal() {
    document.getElementById("experiment-modal-backdrop").classList.add("open");
    runExperimentEvaluation();
}

function closeExperimentModal() {
    document.getElementById("experiment-modal-backdrop").classList.remove("open");
}

function runExperimentEvaluation() {
    const scId = document.getElementById("exp-scenario-select").value;
    const rain = document.getElementById("exp-rain-slider").value;
    const flutter = document.getElementById("exp-flutter-slider").value;
    document.getElementById("exp-rain-val").textContent = `${rain} mm/h`;
    document.getElementById("exp-flutter-val").textContent = `${flutter} dB`;

    // Inject parameters
    fetch("/api/inject", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rain_rate_mm_h: rain, shadowing_flutter_std: flutter })
    });

    // Run prediction and orchestration
    fetch(`/api/predict?user_id=UE-01&node_id=SAT-01&horizon=5`)
        .then(r => r.json())
        .then(pData => {
            renderExperimentChart(pData);
        });

    fetch(`/api/orchestrate?user_id=UE-01`)
        .then(r => r.json())
        .then(decData => {
            document.getElementById("exp-capro-selected").textContent = `${decData.selected_node} (${decData.tier})`;
            document.getElementById("exp-capro-trigger").textContent = decData.trigger_code;
            document.getElementById("exp-capro-util").textContent = `J = ${decData.risk_adjusted_utility.toFixed(3)}`;
            document.getElementById("exp-capro-expl").textContent = decData.explanation;
        });
}

function renderExperimentChart(predData) {
    const ctx = document.getElementById("experiment-chart-canvas").getContext("2d");
    if (experimentChart) experimentChart.destroy();

    experimentChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: predData.epochs.map(e => `t+${e}s`),
            datasets: [
                {
                    label: "Actual Simulated SINR (dB)",
                    data: predData.actual_sinrs,
                    borderColor: "#ffffff",
                    borderWidth: 2,
                    pointRadius: 2,
                },
                {
                    label: "Predicted Median SINR (dB)",
                    data: predData.predicted_sinrs,
                    borderColor: "#00e676",
                    borderDash: [5, 5],
                    borderWidth: 2,
                    pointRadius: 0,
                },
                {
                    label: "90% Conformal Upper Bound (q_95)",
                    data: predData.q_uppers,
                    borderColor: "rgba(0, 229, 255, 0.4)",
                    borderWidth: 1,
                    pointRadius: 0,
                    fill: false,
                },
                {
                    label: "90% Conformal Lower Bound (q_05)",
                    data: predData.q_lowers,
                    borderColor: "rgba(0, 229, 255, 0.8)",
                    backgroundColor: "rgba(0, 229, 255, 0.15)",
                    borderWidth: 1,
                    pointRadius: 0,
                    fill: "-1", // fill to upper bound
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { grid: { color: "#142845" }, ticks: { color: "#94a3b8" } },
                y: { grid: { color: "#142845" }, ticks: { color: "#94a3b8" }, title: { display: true, text: "SINR (dB)", color: "#00e5ff" } }
            },
            plugins: {
                legend: { labels: { color: "#cbd5e1", boxWidth: 12, font: { size: 10 } } }
            }
        }
    });
}


// -----------------------------------------------------------------------------
// 7. Page Initialization
// -----------------------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
    initThreeScene();
    pollState();

    // Auto-poll state every 2 seconds for live clock & ephemeris
    setInterval(pollState, 2000);

    // Tab Switching
    document.querySelectorAll(".tab-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            activeTab = btn.dataset.tab;
            document.querySelectorAll(".tab-pane").forEach(p => p.style.display = "none");
            document.getElementById(`tab-pane-${activeTab}`).style.display = "flex";
            if (currentState) updateTelemetryPanels(currentState);
        });
    });

    // Camera control buttons
    document.getElementById("btn-zoom-in").addEventListener("click", () => { camera.position.multiplyScalar(0.85); });
    document.getElementById("btn-zoom-out").addEventListener("click", () => { camera.position.multiplyScalar(1.15); });
    document.getElementById("btn-reset-cam").addEventListener("click", () => { camera.position.set(2.2, 1.4, 2.4); controls.target.set(0,0,0); });
});
