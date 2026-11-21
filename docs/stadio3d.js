// Zampe d'Italia: lo stadio della partita in corso del Campionato delle Zampe in 3D (21/11, Officina).
// Si entra dallo stadio sulla mappa (app.js): le due curve nei colori delle squadre, il campo con le righe, i fari,
// e sugli spalti i cani e i gatti veri dei tifosi con la sciarpa della loro squadra (gli stessi del paese 3D, mondo3d.js).
// Il tabellone in alto ha il punteggio dal vivo. three.js si carica solo quando si entra.
let S = null; // lo stadio aperto

const tela = (w, h, f) => { const c = document.createElement("canvas"); c.width = w; c.height = h; f(c.getContext("2d"), w, h); return c; };

function campo(THREE) { // l'erba a strisce con le righe bianche (texture disegnata al volo)
  const c = tela(512, 768, (x, w, h) => {
    for (let i = 0; i < 12; i++) { x.fillStyle = i % 2 ? "#3C9A48" : "#46A852"; x.fillRect(0, i * h / 12, w, h / 12); }
    x.strokeStyle = "#F4F4F4"; x.lineWidth = 6; x.strokeRect(20, 20, w - 40, h - 40);
    x.beginPath(); x.moveTo(20, h / 2); x.lineTo(w - 20, h / 2); x.stroke();
    x.beginPath(); x.arc(w / 2, h / 2, 64, 0, Math.PI * 2); x.stroke();
    for (const y of [20, h - 140]) x.strokeRect(w / 2 - 120, y, 240, 120);
  });
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; return t;
}

async function apri(P, animali = []) {
  if (S) chiudi();
  if (!P) return;
  const THREE = await import("three");
  const { OrbitControls } = await import("three/addons/controls/OrbitControls.js");
  const M3 = window.Mondo3D || {};
  const box = document.createElement("div"); box.className = "mondo3d stadio3d";
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  box.innerHTML = `<div class="m3-top"><b>🏟️ ${esc(P.stadio)}</b><span>${esc(P.citta || "")} · trascina per girare, tocca un tifoso</span></div>
    <div class="s3-tab"><b style="background:linear-gradient(90deg,${P.a.c[0]} 0 50%,${P.a.c[1]} 50% 100%)">${esc(P.a.nome)}</b><em>${P.ga} – ${P.gb}</em><b style="background:linear-gradient(90deg,${P.b.c[0]} 0 50%,${P.b.c[1]} 50% 100%)">${esc(P.b.nome)}</b></div>
    <div class="s3-giu">⚽ Ogni commento è un gol: scrivi <b>forza ${esc(P.a.nome)}</b> o <b>forza ${esc(P.b.nome)}</b> sotto un nostro post</div>
    <button type="button" class="m3-esci" aria-label="Esci dallo stadio">✕</button><div class="m3-scheda" hidden></div>`;
  document.body.appendChild(box);
  const piccolo = innerWidth < 700;
  const renderer = new THREE.WebGLRenderer({ antialias: true }); renderer.setPixelRatio(Math.min(devicePixelRatio, piccolo ? 1.5 : 2));
  renderer.setSize(innerWidth, innerHeight); renderer.outputColorSpace = THREE.SRGBColorSpace; renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.35;
  renderer.shadowMap.enabled = true; box.prepend(renderer.domElement);
  const scene = new THREE.Scene(); scene.background = new THREE.Color("#0B1638"); scene.fog = new THREE.Fog("#0B1638", 70, 160);
  const camera = new THREE.PerspectiveCamera(50, innerWidth / innerHeight, 0.3, 400); camera.position.set(0, 26, 44);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true; controls.maxPolarAngle = 1.35; controls.minDistance = 10; controls.maxDistance = 80; controls.enablePan = false;
  controls.autoRotate = true; controls.autoRotateSpeed = 0.6; controls.target.set(0, 2, 0);
  renderer.domElement.addEventListener("pointerdown", () => { controls.autoRotate = false; }, { once: true });

  // luci: la notte, e i quattro fari dello stadio che illuminano il campo
  scene.add(new THREE.HemisphereLight("#9FB2F0", "#1E3A22", 1.2));
  const torri = [[-22, -28], [22, -28], [-22, 28], [22, 28]];
  for (const [x, z] of torri) {
    const palo = new THREE.Mesh(new THREE.CylinderGeometry(0.35, 0.45, 22, 10), new THREE.MeshStandardMaterial({ color: "#5A6472", metalness: 0.6, roughness: 0.4 })); palo.position.set(x, 11, z); scene.add(palo);
    const pannello = new THREE.Mesh(new THREE.BoxGeometry(4.5, 2.4, 0.5), new THREE.MeshStandardMaterial({ color: "#FFF3B0", emissive: "#FFF3B0", emissiveIntensity: 2.2 }));
    pannello.position.set(x, 22.5, z); pannello.lookAt(0, 0, 0); scene.add(pannello);
    const faro = new THREE.SpotLight("#FFF6D8", 900, 120, 0.55, 0.5, 1.6); faro.position.set(x, 22, z); faro.target.position.set(0, 0, 0);
    faro.castShadow = !piccolo; scene.add(faro); scene.add(faro.target);
  }

  // il campo (16 × 24) e la pista attorno
  const erba = new THREE.Mesh(new THREE.PlaneGeometry(16, 24), new THREE.MeshStandardMaterial({ map: campo(THREE), roughness: 0.9 }));
  erba.rotation.x = -Math.PI / 2; erba.receiveShadow = true; scene.add(erba);
  const pista = new THREE.Mesh(new THREE.PlaneGeometry(60, 70), new THREE.MeshStandardMaterial({ color: "#2B2F3E", roughness: 1 })); pista.rotation.x = -Math.PI / 2; pista.position.y = -0.02; scene.add(pista);
  for (const z of [-12, 12]) { // le due porte
    const porta = new THREE.Group(), bianco = new THREE.MeshStandardMaterial({ color: "#FFFFFF" });
    for (const x of [-1.8, 1.8]) { const p = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 1.6, 8), bianco); p.position.set(x, 0.8, 0); porta.add(p); }
    const tr = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 3.6, 8), bianco); tr.rotation.z = Math.PI / 2; tr.position.y = 1.6; porta.add(tr);
    const rete = new THREE.Mesh(new THREE.PlaneGeometry(3.6, 1.6), new THREE.MeshStandardMaterial({ color: "#FFFFFF", transparent: true, opacity: 0.25, side: THREE.DoubleSide })); rete.position.set(0, 0.8, z > 0 ? 0.6 : -0.6); porta.add(rete);
    porta.position.z = z; scene.add(porta);
  }

  // gli spalti: un anello ellittico a tre gradoni, metà coi colori della squadra di casa e metà con quelli degli ospiti
  const N = 72, posti = { a: [], b: [] };
  for (let i = 0; i < N; i++) {
    const t = (i / N) * Math.PI * 2, t2 = ((i + 1) / N) * Math.PI * 2, casa = Math.cos((t + t2) / 2) < 0, col = casa ? P.a.c : P.b.c;
    for (let g = 0; g < 3; g++) {
      const rx = 13 + g * 2.2, rz = 18 + g * 2.2, x1 = Math.cos(t) * rx, z1 = Math.sin(t) * rz, x2 = Math.cos(t2) * rx, z2 = Math.sin(t2) * rz;
      const lung = Math.hypot(x2 - x1, z2 - z1) + 0.05, gradino = new THREE.Mesh(new THREE.BoxGeometry(lung, 1 + g * 1.2, 2.2),
        new THREE.MeshStandardMaterial({ color: col[(i + g) % 2], roughness: 0.85 }));
      gradino.position.set((x1 + x2) / 2, (1 + g * 1.2) / 2, (z1 + z2) / 2); gradino.rotation.y = -Math.atan2(z2 - z1, x2 - x1);
      gradino.castShadow = gradino.receiveShadow = true; scene.add(gradino);
      if (g === 0 && i % 2 === 0) (casa ? posti.a : posti.b).push({ x: (x1 + x2) / 2, z: (z1 + z2) / 2, y: 1.0 });
    }
  }
  // i tifosi veri: cani e gatti con la sciarpa, seduti in prima fila, rivolti verso il campo
  const scheda = box.querySelector(".m3-scheda"), presi = [];
  const metti = (lista, pos) => lista.slice(0, pos.length).forEach((d, i) => {
    const g = d.t === "gatto" && M3.micio3d ? M3.micio3d(THREE, d) : M3.cane3d ? M3.cane3d(THREE, d) : null; if (!g) return;
    if (M3.sciarpa3d) M3.sciarpa3d(THREE, g, d);
    const p = pos[Math.floor(i * pos.length / Math.max(1, Math.min(lista.length, pos.length)))];
    g.position.set(p.x * 0.93, p.y, p.z * 0.93); g.scale.setScalar(1.5); g.lookAt(0, p.y, 0); g.userData.d = d; g.userData.salto = Math.random() * 6;
    g.traverse(o => { if (o.isMesh) o.userData.radice = g; }); scene.add(g); presi.push(g);
  });
  metti(animali.filter(d => d.sq === P.a.k), posti.a); metti(animali.filter(d => d.sq === P.b.k), posti.b);

  // il pallone che rimbalza a centrocampo
  const pallone = new THREE.Mesh(new THREE.SphereGeometry(0.45, 24, 16), new THREE.MeshStandardMaterial({ color: "#FFFFFF", roughness: 0.4 })); pallone.castShadow = true; scene.add(pallone);

  // tocca un tifoso: il suo nome e la sua squadra
  const ray = new THREE.Raycaster(), pt = new THREE.Vector2();
  renderer.domElement.addEventListener("click", e => {
    pt.set((e.clientX / innerWidth) * 2 - 1, -(e.clientY / innerHeight) * 2 + 1); ray.setFromCamera(pt, camera);
    const hit = ray.intersectObjects(presi, true)[0]; if (!hit) { scheda.hidden = true; return; }
    const d = hit.object.userData.radice?.userData.d; if (!d) return;
    scheda.innerHTML = `<b>${esc(d.n)}</b> · @${esc(d.u)}<br>${esc(d.c)} · ⚽ tifa ${esc(d.sq === P.a.k ? P.a.nome : P.b.nome)}`; scheda.hidden = false;
  });

  let fermo = false, t0 = performance.now();
  const giro = () => {
    if (fermo) return;
    const t = (performance.now() - t0) / 1000;
    pallone.position.set(Math.sin(t * 0.7) * 3, 0.45 + Math.abs(Math.sin(t * 3)) * 2.2, Math.cos(t * 0.5) * 5); pallone.rotation.x = t * 4;
    for (const g of presi) g.position.y = 1.0 + Math.max(0, Math.sin(t * 4 + g.userData.salto)) * 0.35; // i tifosi saltano
    controls.update(); renderer.render(scene, camera); requestAnimationFrame(giro);
  };
  giro();
  const ridim = () => { camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); renderer.setSize(innerWidth, innerHeight); };
  addEventListener("resize", ridim);
  box.querySelector(".m3-esci").onclick = chiudi;
  S = { box, renderer, ferma: () => { fermo = true; removeEventListener("resize", ridim); } };
}

function chiudi() {
  if (!S) return;
  S.ferma(); S.renderer.dispose(); S.box.remove(); S = null;
}

window.Stadio3D = { apri, chiudi };
