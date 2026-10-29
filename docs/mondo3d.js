// Zampe d'Italia: il paese in 3D, come un videogioco. Si entra da un paese della mappa (app.js chiama Mondo3D.apri).
// Gli animali sono i loro disegni (con costume e accessori) in piedi su una pedana che cresce col livello;
// intorno la piazza con gli edifici sbloccati, le vie, il bosco, i lampioni, le lucciole e il cielo di notte.
// three.js si carica solo quando si entra, così la mappa resta leggera.
const SQ = 0.58, U = 10; // posti di paese.js: pixel a zoom 14, schiacciati di SQ; 10 pixel = 1 unità
let M = null; // il mondo aperto: {renderer, scene, camera, controls, ...}

const testo = (THREE, t, { size = 46, fg = "#5A3417", bg = "#F3DDB0", bordo = "#5E3519" } = {}) => {
  const c = document.createElement("canvas"), x = c.getContext("2d"), f = `800 ${size}px "Bricolage Grotesque", system-ui, sans-serif`;
  x.font = f; const w = Math.ceil(x.measureText(t).width) + size; c.width = w; c.height = size * 1.6;
  x.font = f; x.fillStyle = bg; x.strokeStyle = bordo; x.lineWidth = size / 8;
  const r = size / 2.6; x.beginPath(); x.roundRect(x.lineWidth, x.lineWidth, w - 2 * x.lineWidth, c.height - 2 * x.lineWidth, r); x.fill(); x.stroke();
  x.fillStyle = fg; x.textAlign = "center"; x.textBaseline = "middle"; x.fillText(t, w / 2, c.height / 2 + size * 0.05);
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 4;
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, depthWrite: false })); s.scale.set(w / c.height * 1.1, 1.1, 1); return s;
};
const emoji = (THREE, e, px = 96) => {
  const c = document.createElement("canvas"); c.width = c.height = px; const x = c.getContext("2d");
  x.font = `${px * 0.8}px system-ui, "Apple Color Emoji", "Segoe UI Emoji"`; x.textAlign = "center"; x.textBaseline = "middle"; x.fillText(e, px / 2, px / 2 + px * 0.06);
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace; return tex;
};
// il disegno SVG dell'animale diventa una texture
const svgTex = (THREE, svg) => new Promise(ok => {
  const m = svg.match(/width="(\d+)" height="(\d+)"/), w = +(m?.[1] || 80), h = +(m?.[2] || 75), k = 3;
  const img = new Image(); img.onload = () => {
    const c = document.createElement("canvas"); c.width = w * k; c.height = (h + 24) * k; // spazio sopra per corona e fuochi
    c.getContext("2d").drawImage(img, 0, 24 * k, w * k, h * k);
    const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 4; ok({ tex, a: c.width / c.height });
  };
  img.onerror = () => ok(null);
  img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg.replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" ').replace(/viewBox="([^"]+)"/, (s, v) => { const [a, b, c, d] = v.split(" ").map(Number); return `viewBox="${a} ${b} ${c} ${d}" overflow="visible"`; }));
});

async function apri(v, opz = {}) {
  if (M) chiudi();
  const THREE = await import("three"), { OrbitControls } = await import("three/addons/controls/OrbitControls.js");
  const box = document.createElement("div"); box.className = "mondo3d";
  box.innerHTML = `<div class="m3-top"><b>🎮 ${v.nome.replace(/[&<>]/g, "")}</b><span>${v.luci} ${v.luci === 1 ? "luce" : "luci"} · trascina per girare, tocca un animale</span></div>
    <button type="button" class="m3-esci" aria-label="Esci dal 3D">✕</button><div class="m3-scheda" hidden></div>`;
  document.body.appendChild(box);
  const renderer = new THREE.WebGLRenderer({ antialias: true }); renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.setSize(innerWidth, innerHeight); renderer.outputColorSpace = THREE.SRGBColorSpace; renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.15;
  box.prepend(renderer.domElement);
  const scene = new THREE.Scene(); scene.background = new THREE.Color("#0B1638"); scene.fog = new THREE.Fog("#0B1638", 60, 190);
  const lista = v.lista.slice(0, 260), R = Math.max(26, (v.R || 200) / U);
  const camera = new THREE.PerspectiveCamera(50, innerWidth / innerHeight, 0.5, 600);
  camera.position.set(0, R * 0.62 + 10, R * 1.05 + 14);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true; controls.maxPolarAngle = 1.32; controls.minDistance = 8; controls.maxDistance = R * 2.6 + 30; controls.autoRotate = true; controls.autoRotateSpeed = 0.45;
  controls.target.set(0, 1.5, 0); controls.enablePan = false;
  renderer.domElement.addEventListener("pointerdown", () => { controls.autoRotate = false; }, { once: true });

  // luce: luna fredda, cielo blu, e i lampioni caldi
  scene.add(new THREE.HemisphereLight("#9DB4FF", "#2A3A30", 1.3));
  const luna = new THREE.DirectionalLight("#C9D6FF", 1.1); luna.position.set(-40, 70, -30); scene.add(luna);
  const lunaM = new THREE.Mesh(new THREE.SphereGeometry(7, 32, 16), new THREE.MeshBasicMaterial({ color: "#FFF4DE" })); lunaM.position.set(-110, 95, -170); scene.add(lunaM);
  const alone = new THREE.Sprite(new THREE.SpriteMaterial({ map: emoji(THREE, "⚪", 64), color: "#FFE9B8", transparent: true, opacity: 0.25, depthWrite: false })); alone.scale.set(40, 40, 1); alone.position.copy(lunaM.position); scene.add(alone);
  // stelle
  const sp = []; for (let i = 0; i < 900; i++) { const a = Math.random() * Math.PI * 2, e = 0.12 + Math.random() * 1.3, r = 260; sp.push(r * Math.cos(a) * Math.cos(e), r * Math.sin(e), r * Math.sin(a) * Math.cos(e)); }
  const stelle = new THREE.Points(new THREE.BufferGeometry().setAttribute("position", new THREE.Float32BufferAttribute(sp, 3)), new THREE.PointsMaterial({ color: "#FFFFFF", size: 1.4, sizeAttenuation: false, fog: false }));
  scene.add(stelle);

  // terreno: prato, piazza, anelli di strade, vie
  const prato = new THREE.Mesh(new THREE.CircleGeometry(R + 30, 96), new THREE.MeshStandardMaterial({ color: "#244A3C", roughness: 1 }));
  prato.rotation.x = -Math.PI / 2; scene.add(prato);
  const lontano = new THREE.Mesh(new THREE.CircleGeometry(420, 64), new THREE.MeshStandardMaterial({ color: "#132A2A", roughness: 1 })); lontano.rotation.x = -Math.PI / 2; lontano.position.y = -0.05; scene.add(lontano);
  const strada = new THREE.MeshStandardMaterial({ color: "#3E4C72", roughness: 0.9 });
  const anelli = [...new Set(lista.map(d => Math.round(Math.hypot(d.off[0], d.off[1] / SQ) / 10) * 10))];
  for (const a of anelli) { const r = a / U; const m = new THREE.Mesh(new THREE.RingGeometry(r - 0.9, r + 0.9, 96), strada); m.rotation.x = -Math.PI / 2; m.position.y = 0.02; scene.add(m); }
  for (let i = 0; i < 6; i++) { const a = (i / 6) * Math.PI * 2 + 0.26, L = R - 7; const m = new THREE.Mesh(new THREE.PlaneGeometry(1.6, L), strada); m.rotation.x = -Math.PI / 2; m.rotation.z = -a + Math.PI / 2;
    m.position.set(Math.cos(a) * (L / 2 + 5), 0.015, Math.sin(a) * (L / 2 + 5)); scene.add(m); }
  const piazza = new THREE.Mesh(new THREE.CylinderGeometry(9.5, 10, 0.4, 64), new THREE.MeshStandardMaterial({ color: "#5A5F86", roughness: 0.8 })); piazza.position.y = 0.2; scene.add(piazza);

  // edifici della piazza, sbloccati dalle luci come in paese.js
  const mat = c => new THREE.MeshStandardMaterial({ color: c, roughness: 0.7 }), gira = [];
  const add = (g, x, z) => { g.position.set(x, 0.4, z); scene.add(g); return g; };
  if (v.luci >= 5) { const g = new THREE.Group(); const vasca = new THREE.Mesh(new THREE.CylinderGeometry(2.4, 2.6, 0.8, 32), mat("#6F7FA8")); vasca.position.y = 0.4;
    const acqua = new THREE.Mesh(new THREE.CylinderGeometry(2.1, 2.1, 0.1, 32), new THREE.MeshStandardMaterial({ color: "#4FB4E8", emissive: "#1B6FA8", emissiveIntensity: 0.6 })); acqua.position.y = 0.8;
    const col = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.4, 2.6, 12), mat("#8E9CC2")); col.position.y = 1.6; g.add(vasca, acqua, col); add(g, 0, 0);
    const gocce = []; for (let i = 0; i < 40; i++) gocce.push(0, 3, 0); const gp = new THREE.Points(new THREE.BufferGeometry().setAttribute("position", new THREE.Float32BufferAttribute(gocce, 3)), new THREE.PointsMaterial({ color: "#BFEFFF", size: 0.25 }));
    g.add(gp); gira.push(t => { const p = gp.geometry.attributes.position; for (let i = 0; i < 40; i++) { const f = ((t / 1000 + i / 40) % 1), a = i * 2.4; p.setXYZ(i, Math.cos(a) * f * 1.8, 3 + f * 2.2 - f * f * 4.6, Math.sin(a) * f * 1.8); } p.needsUpdate = true; }); }
  if (v.luci >= 25) { const g = new THREE.Group(), b = new THREE.Mesh(new THREE.BoxGeometry(4, 2.6, 3), mat("#B35C7A")); b.position.y = 1.3;
    const t = new THREE.Mesh(new THREE.ConeGeometry(3.2, 1.8, 4), mat("#6B2440")); t.position.y = 3.5; t.rotation.y = Math.PI / 4; g.add(b, t); add(g, 6, -1.5).rotation.y = -0.6; }
  if (v.luci >= 50) { const g = new THREE.Group(), b = new THREE.Mesh(new THREE.BoxGeometry(4.6, 3.6, 3.4), mat("#EEF2FA")); b.position.y = 1.8;
    const c1 = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.5, 0.1), new THREE.MeshBasicMaterial({ color: "#E2394B" })), c2 = c1.clone(); c2.rotation.z = Math.PI / 2; c1.position.set(0, 2.8, 1.75); c2.position.copy(c1.position);
    g.add(b, c1, c2); add(g, -4, 3).rotation.y = 0.5; }
  if (v.luci >= 100) { const g = new THREE.Group(); for (let i = 0; i < 4; i++) { const c = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.3, 3.2, 12), mat("#F1E7D0")); c.position.set(-2.4 + i * 1.6, 1.6, 0); g.add(c); }
    const t = new THREE.Mesh(new THREE.BoxGeometry(6, 0.5, 1.6), mat("#E8DCC0")); t.position.y = 3.4; g.add(t); add(g, 0, -4.5); }
  if (v.luci >= 250) { const ruota = new THREE.Mesh(new THREE.TorusGeometry(2.6, 0.15, 8, 40), new THREE.MeshStandardMaterial({ color: "#FFC55C", emissive: "#FF9A3C", emissiveIntensity: 0.6 }));
    ruota.position.set(5, 3.4, 4); scene.add(ruota); gira.push(t => { ruota.rotation.z = t / 2400; }); }

  // bosco tutto intorno e lampioni
  const tronco = new THREE.CylinderGeometry(0.18, 0.24, 1.2, 6), chioma = new THREE.ConeGeometry(1.3, 3.4, 7);
  const nAlberi = Math.round((R + 18) * 1.6), alb1 = new THREE.InstancedMesh(chioma, new THREE.MeshStandardMaterial({ color: "#3E9A5C", emissive: "#0E2A1A", roughness: 0.9 }), nAlberi), alb0 = new THREE.InstancedMesh(tronco, mat("#4A2C17"), nAlberi), o = new THREE.Object3D();
  for (let i = 0; i < nAlberi; i++) { const a = (i / nAlberi) * Math.PI * 2 + Math.random() * 0.05, r = R + 4 + Math.random() * 22, k = 0.7 + Math.random() * 0.8;
    if (Math.abs(a - Math.PI / 2) < 0.16) continue; // davanti resta il varco d'ingresso
    o.position.set(Math.cos(a) * r, 0.6 * k, Math.sin(a) * r); o.scale.setScalar(k); o.rotation.set(0, Math.random() * 6, 0); o.updateMatrix(); alb0.setMatrixAt(i, o.matrix);
    o.position.y = 2.6 * k; o.updateMatrix(); alb1.setMatrixAt(i, o.matrix); alb1.setColorAt(i, new THREE.Color(Math.random() < 0.5 ? "#4FA86A" : "#3A8A55")); }
  scene.add(alb0, alb1);
  const lam = []; for (let i = 0; i < 6; i++) { const a = (i / 6) * Math.PI * 2 + 0.46, x = Math.cos(a) * 11.5, z = Math.sin(a) * 11.5;
    const palo = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.1, 3.4, 6), mat("#2B3556")); palo.position.set(x, 1.7, z);
    const bulbo = new THREE.Mesh(new THREE.SphereGeometry(0.32, 12, 8), new THREE.MeshBasicMaterial({ color: "#FFE3A0" })); bulbo.position.set(x, 3.5, z);
    const l = new THREE.PointLight("#FFC873", 18, 16, 1.6); l.position.set(x, 3.4, z); scene.add(palo, bulbo, l); lam.push(l); }

  // il cartello d'ingresso
  const cart = testo(THREE, v.nome.toUpperCase(), { size: 56 }); cart.scale.multiplyScalar(2.2); cart.position.set(0, 2.6, R + 2); scene.add(cart);

  // gli animali: disegno in piedi su una pedana; la pedana cresce col livello (giardino, villa, castello)
  const LIV = [[70, "#FFD23F", 1.6], [50, "#FF9A3C", 1.35], [30, "#FF8AB6", 1.15]];
  const pet = [], toccabili = [];
  const ombra = new THREE.MeshBasicMaterial({ color: "#000", transparent: true, opacity: 0.35, depthWrite: false });
  for (const d of lista) {
    const x = d.off[0] / U, z = d.off[1] / SQ / U, liv = LIV.find(l => d.pt >= l[0]);
    const g = new THREE.Group(); g.position.set(x, 0, z); scene.add(g);
    const ped = new THREE.Mesh(new THREE.CylinderGeometry(2.7 * (liv?.[2] || 1), 2.9 * (liv?.[2] || 1), 0.35, 28), mat(liv ? "#3D6B4A" : "#2E5640")); ped.position.y = 0.18; g.add(ped);
    if (liv) { const bordo = new THREE.Mesh(new THREE.TorusGeometry(2.8 * liv[2], 0.11, 6, 40), new THREE.MeshBasicMaterial({ color: liv[1] })); bordo.rotation.x = Math.PI / 2; bordo.position.y = 0.38; g.add(bordo); }
    if (liv && liv[0] >= 70) for (const s of [-1, 1]) { const tor = new THREE.Mesh(new THREE.CylinderGeometry(0.45, 0.5, 3.4, 10), mat("#C9B48A")); tor.position.set(s * 2.9, 1.7, -1);
      const tet = new THREE.Mesh(new THREE.ConeGeometry(0.7, 1.4, 10), mat("#8C1F45")); tet.position.set(s * 2.9, 4.1, -1); g.add(tor, tet); }
    if (liv && liv[0] >= 30 && liv[0] < 70) for (let i = 0; i < 5; i++) { const f = new THREE.Mesh(new THREE.SphereGeometry(0.16, 8, 6), new THREE.MeshBasicMaterial({ color: ["#FF5A6E", "#FFD23F", "#FF8AB6", "#4FB4FF", "#FFFFFF"][i] }));
      const a = i * 1.25 + 0.4; f.position.set(Math.cos(a) * 2.3 * liv[2], 0.45, Math.sin(a) * 2.3 * liv[2]); g.add(f); }
    const sh = new THREE.Mesh(new THREE.CircleGeometry(1.5, 20), ombra); sh.rotation.x = -Math.PI / 2; sh.position.y = 0.37; g.add(sh);
    const s = new THREE.Sprite(new THREE.SpriteMaterial({ transparent: true, alphaTest: 0.05 })); s.center.set(0.5, 0); s.position.y = 0.36; g.add(s);
    s.userData.d = d; toccabili.push(s);
    const nome = testo(THREE, (d.acc?.includes("corona") ? "👑 " : "") + d.n, d.t === "gatto" ? { fg: "#2F3A10", bg: "#E9F2C4", bordo: "#3D4A18" } : {}); nome.position.y = 7.2; g.add(nome);
    pet.push({ d, g, s, nome, fase: (d.seed % 628) / 100 });
    svgTex(THREE, opz.svg(d)).then(r => { if (!r || !M) return; s.material.map = r.tex; s.material.needsUpdate = true; const h = d.t === "altro" ? 4 : 6.4; s.scale.set(h * r.a, h, 1); nome.position.y = h + 0.9; });
  }
  // il tuo animale: una freccia che rimbalza
  const mio = opz.mio && pet.find(p => p.d === opz.mio);
  let freccia = null;
  if (mio) { freccia = testo(THREE, "⬇ TU", { size: 52, fg: "#4A2C04", bg: "#FFD23F", bordo: "#8C4A00" }); freccia.position.y = 9; mio.g.add(freccia);
    const { x, z } = mio.g.position, L = Math.hypot(x, z) || 1; controls.target.set(x, 3, z); camera.position.set(x + (x / L) * 13, 20, z + (Math.hypot(x, z) ? z / L : 1) * 13); controls.autoRotate = false; }

  // lucciole
  const NL = 70, lp = new Float32Array(NL * 3), lseed = [...Array(NL)].map(() => [Math.random() * Math.PI * 2, 6 + Math.random() * (R + 8), 0.6 + Math.random() * 3, Math.random() * 10]);
  const lucc = new THREE.Points(new THREE.BufferGeometry().setAttribute("position", new THREE.BufferAttribute(lp, 3)),
    new THREE.PointsMaterial({ color: "#FFF3A0", size: 0.45, transparent: true, opacity: 0.95, blending: THREE.AdditiveBlending, depthWrite: false }));
  scene.add(lucc);
  // cuori e fuochi d'artificio
  const CUORI = ["❤️", "💛", "🐾", "✨", "🦴"].map(e => emoji(THREE, e)), volanti = [];
  const fuochi = pet.filter(p => p.d.acc?.includes("fuochi")), scoppi = [];
  const scoppio = p => { const n = 36, pos = new Float32Array(n * 3), dir = [...Array(n)].map(() => new THREE.Vector3().randomDirection());
    const pts = new THREE.Points(new THREE.BufferGeometry().setAttribute("position", new THREE.BufferAttribute(pos, 3)),
      new THREE.PointsMaterial({ color: ["#FF5A6E", "#FFD23F", "#4FB4FF", "#5BE37D", "#FF9A3C"][Math.floor(Math.random() * 5)], size: 0.4, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false }));
    pts.position.set(p.g.position.x + (Math.random() - 0.5) * 2, 9 + Math.random() * 3, p.g.position.z); scene.add(pts); scoppi.push({ pts, dir, t0: performance.now() }); };

  // tocca un animale: la sua scheda
  const ray = new THREE.Raycaster(), mouse = new THREE.Vector2(), scheda = box.querySelector(".m3-scheda");
  let giu = null;
  renderer.domElement.addEventListener("pointerdown", e => { giu = [e.clientX, e.clientY]; });
  renderer.domElement.addEventListener("pointerup", e => {
    if (!giu || Math.hypot(e.clientX - giu[0], e.clientY - giu[1]) > 6) return;
    mouse.set((e.clientX / innerWidth) * 2 - 1, -(e.clientY / innerHeight) * 2 + 1); ray.setFromCamera(mouse, camera);
    const hit = ray.intersectObjects(toccabili)[0];
    if (!hit) { scheda.hidden = true; return; }
    const d = hit.object.userData.d; scheda.innerHTML = opz.scheda(d); scheda.hidden = false;
    const p = pet.find(q => q.d === d); p.salto = performance.now();
    for (let i = 0; i < 3; i++) setTimeout(() => cuore(p), i * 180);
  });
  const cuore = p => { const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: CUORI[Math.floor(Math.random() * CUORI.length)], transparent: true, depthWrite: false }));
    s.scale.set(1.3, 1.3, 1); s.position.set(p.g.position.x + (Math.random() - 0.5), 4.6, p.g.position.z); scene.add(s); volanti.push({ s, t0: performance.now() }); };

  let ultimoCuore = 0, ultimoFuoco = 0, raf = 0;
  const giro = t => {
    raf = requestAnimationFrame(giro);
    for (const p of pet) { // respirano e ogni tanto saltano
      let y = 0.36 + Math.max(0, Math.sin(t / 900 + p.fase)) * 0.12;
      if (p.salto) { const k = (t - p.salto) / 600; if (k < 1) y += Math.sin(k * Math.PI) * 1.6; else p.salto = 0; }
      else if (Math.random() < 0.0008) p.salto = t;
      p.s.position.y = y;
    }
    if (freccia) freccia.position.y = 9 + Math.abs(Math.sin(t / 280)) * 0.8;
    for (let i = 0; i < NL; i++) { const [a, r, h, f] = lseed[i], w = t / 4000 + f; lp[i * 3] = Math.cos(a + w * 0.3) * r + Math.sin(w * 1.7) * 1.5; lp[i * 3 + 1] = h + Math.sin(w * 2.3) * 0.6; lp[i * 3 + 2] = Math.sin(a + w * 0.3) * r + Math.cos(w * 1.3) * 1.5; }
    lucc.geometry.attributes.position.needsUpdate = true; lucc.material.opacity = 0.65 + Math.sin(t / 300) * 0.3;
    if (t - ultimoCuore > 900 && pet.length) { ultimoCuore = t; cuore(pet[Math.floor(Math.random() * pet.length)]); }
    if (fuochi.length && t - ultimoFuoco > 1300) { ultimoFuoco = t; scoppio(fuochi[Math.floor(Math.random() * fuochi.length)]); }
    for (let i = volanti.length - 1; i >= 0; i--) { const v2 = volanti[i], k = (t - v2.t0) / 2400; v2.s.position.y += 0.03; v2.s.material.opacity = 1 - k; if (k >= 1) { scene.remove(v2.s); v2.s.material.dispose(); volanti.splice(i, 1); } }
    for (let i = scoppi.length - 1; i >= 0; i--) { const b = scoppi[i], k = (t - b.t0) / 1600, p = b.pts.geometry.attributes.position;
      b.dir.forEach((dv, j) => p.setXYZ(j, dv.x * k * 4, dv.y * k * 4 - k * k * 2, dv.z * k * 4)); p.needsUpdate = true; b.pts.material.opacity = 1 - k;
      if (k >= 1) { scene.remove(b.pts); b.pts.geometry.dispose(); scoppi.splice(i, 1); } }
    for (const f of gira) f(t);
    lam.forEach((l, i) => l.intensity = 16 + Math.sin(t / 500 + i) * 2);
    controls.update(); renderer.render(scene, camera);
  };
  raf = requestAnimationFrame(giro);
  const resize = () => { camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); renderer.setSize(innerWidth, innerHeight); };
  addEventListener("resize", resize);
  box.querySelector(".m3-esci").onclick = chiudi;
  M = { renderer, box, stop: () => { cancelAnimationFrame(raf); removeEventListener("resize", resize); } };
}

function chiudi() {
  if (!M) return;
  M.stop(); M.renderer.dispose(); M.renderer.forceContextLoss?.(); M.box.remove(); M = null;
}

window.Mondo3D = { apri, chiudi };
