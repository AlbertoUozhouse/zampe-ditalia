// Zampe d'Italia: il paese in 3D, come un videogioco. Si entra da un paese della mappa (app.js chiama Mondo3D.apri).
// Cucce e casette vere in 3D (legno, tegole, porte illuminate), il muso disegnato di ogni animale nella sua porta o sul tetto,
// la piazza in pietra con gli edifici sbloccati, vie, bosco di pini, lampioni, ombre della luna, bagliori, lucciole e fuochi.
// three.js si carica solo quando si entra, così la mappa resta leggera.
const SQ = 0.58, U = 10; // posti di paese.js: pixel a zoom 14, schiacciati di SQ; 10 pixel = 1 unità
let M = null; // il mondo aperto

// ---------- texture disegnate al volo (niente file da scaricare) ----------
const tela = (w, h, f) => { const c = document.createElement("canvas"); c.width = w; c.height = h; f(c.getContext("2d"), w, h); return c; };
const rnd = s => () => (s = (s * 16807) % 2147483647) / 2147483647;
function texture(THREE, c, rep = 1) { const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(rep, rep); t.anisotropy = 8; return t; }
const ERBA = THREE => texture(THREE, tela(512, 512, (x, w, h) => { const r = rnd(7); x.fillStyle = "#2C5A3A"; x.fillRect(0, 0, w, h);
  for (let i = 0; i < 9000; i++) { const g = 70 + r() * 70; x.fillStyle = `rgba(${30 + r() * 40},${g},${40 + r() * 30},${0.35 + r() * 0.4})`; x.fillRect(r() * w, r() * h, 1 + r() * 2, 2 + r() * 5); }
  for (let i = 0; i < 40; i++) { x.fillStyle = `rgba(20,40,25,${0.15 + r() * 0.2})`; x.beginPath(); x.ellipse(r() * w, r() * h, 20 + r() * 60, 10 + r() * 40, r() * 3, 0, 7); x.fill(); } }), 14);
const PIETRA = THREE => texture(THREE, tela(512, 512, (x, w, h) => { const r = rnd(3); x.fillStyle = "#3A3A48"; x.fillRect(0, 0, w, h);
  for (let y = 0; y < h; y += 32) for (let i = -1; i < w / 40 + 1; i++) { const c = 110 + r() * 40, ox = (y / 32) % 2 ? 20 : 0;
    x.fillStyle = `rgb(${c},${c - 6},${c - 14})`; x.beginPath(); x.roundRect(i * 40 + ox + 2, y + 2, 36, 28, 7); x.fill();
    x.fillStyle = "rgba(255,255,255,.07)"; x.fillRect(i * 40 + ox + 6, y + 5, 26, 5); } }), 5);
const ASFALTO = THREE => texture(THREE, tela(256, 256, (x, w, h) => { const r = rnd(11); x.fillStyle = "#2E3346"; x.fillRect(0, 0, w, h);
  for (let i = 0; i < 4000; i++) { const c = 40 + r() * 40; x.fillStyle = `rgba(${c},${c},${c + 10},.5)`; x.fillRect(r() * w, r() * h, 1.5, 1.5); } }), 6);
const LEGNO = THREE => texture(THREE, tela(256, 256, (x, w, h) => { const r = rnd(5);
  for (let y = 0; y < h; y += 32) { const c = r() * 25; x.fillStyle = `rgb(${130 + c},${78 + c * 0.6},${40 + c * 0.3})`; x.fillRect(0, y, w, 32);
    for (let i = 0; i < 30; i++) { x.strokeStyle = `rgba(70,35,15,${0.15 + r() * 0.2})`; x.beginPath(); const yy = y + r() * 32; x.moveTo(0, yy); x.bezierCurveTo(w / 3, yy + r() * 6 - 3, w * 2 / 3, yy + r() * 6 - 3, w, yy); x.stroke(); }
    x.fillStyle = "rgba(40,20,8,.7)"; x.fillRect(0, y + 30, w, 2); } }));
const TEGOLE = (THREE, base) => texture(THREE, tela(256, 256, (x, w, h) => { const r = rnd(9); x.fillStyle = base; x.fillRect(0, 0, w, h);
  for (let y = 0; y < h; y += 24) for (let i = -1; i < w / 32 + 1; i++) { const ox = (y / 24) % 2 ? 16 : 0, k = r() * 0.25;
    x.fillStyle = `rgba(0,0,0,${0.15 + k})`; x.beginPath(); x.arc(i * 32 + ox + 16, y + 22, 16, Math.PI, 0); x.fill();
    x.fillStyle = `rgba(255,255,255,${0.06 + k / 3})`; x.fillRect(i * 32 + ox + 6, y + 8, 18, 3); } }));
const ETICHETTA = (THREE, t, { size = 44, fg = "#5A3417", bg = "#F3DDB0", bordo = "#5E3519" } = {}) => {
  const f = `800 ${size}px "Bricolage Grotesque", system-ui, sans-serif`, prova = document.createElement("canvas").getContext("2d"); prova.font = f;
  const w = Math.ceil(prova.measureText(t).width) + size, c = tela(w, size * 1.6, (x, W, H) => { x.font = f; x.fillStyle = bg; x.strokeStyle = bordo; x.lineWidth = size / 8;
    x.beginPath(); x.roundRect(x.lineWidth, x.lineWidth, W - 2 * x.lineWidth, H - 2 * x.lineWidth, size / 2.6); x.fill(); x.stroke();
    x.fillStyle = fg; x.textAlign = "center"; x.textBaseline = "middle"; x.fillText(t, W / 2, H / 2 + size * 0.05); });
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, depthWrite: false })); s.scale.set(w / c.height * 0.85, 0.85, 1); return s;
};
const EMOJI = (THREE, e, px = 96) => { const tex = new THREE.CanvasTexture(tela(px, px, x => { x.font = `${px * 0.8}px system-ui, "Apple Color Emoji", "Segoe UI Emoji"`;
  x.textAlign = "center"; x.textBaseline = "middle"; x.fillText(e, px / 2, px / 2 + px * 0.06); })); tex.colorSpace = THREE.SRGBColorSpace; return tex; };

// solo il muso del cane (con collare, corona, costume) o solo il gatto: la cuccia e la casetta sono in 3D
function soloAnimale(svg, tipo) {
  const doc = new DOMParser().parseFromString(svg.includes("xmlns=") ? svg : svg.replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" '), "image/svg+xml");
  const g = doc.querySelector(tipo === "gatto" ? "g.micio" : "g.muso"); if (!g) return { svg };
  const ser = new XMLSerializer(), defs = [...doc.querySelectorAll("defs")].map(d => ser.serializeToString(d)).join("");
  const volo = tipo === "gatto" ? "" : [...doc.querySelectorAll("g.vola")].map(d => ser.serializeToString(d)).join(""); // pipistrelli e fantasmi del costume
  const box = tipo === "gatto" ? [6, -2, 52, 46] : [12, 18, 40, 40];
  return { svg: `<svg xmlns="http://www.w3.org/2000/svg" width="${box[2] * 4}" height="${box[3] * 4}" viewBox="${box.join(" ")}">${defs}${ser.serializeToString(g)}${volo}</svg>` };
}
const svgTex = (THREE, svg) => new Promise(ok => {
  const s = svg.includes("xmlns=") ? svg : svg.replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" ');
  const m = s.match(/width="(\d+)" height="(\d+)"/), w = +(m?.[1] || 80), h = +(m?.[2] || 75), k = w < 120 ? 3 : 1.5;
  const img = new Image(); img.onload = () => { const c = tela(w * k, h * k, x => x.drawImage(img, 0, 0, w * k, h * k));
    const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 4; ok({ tex, a: w / h }); };
  img.onerror = () => ok(null); img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(s);
});

// ---------- animali in 3D: forme semplici, colori della razza (Disegni.CANI / GATTI), pelo che riflette la luce ----------
const TONI = ["#B98450", "#8A5A35", "#D9B07A", "#3C312B", "#E7D9C2", "#A0693A"];
const schiarisci = (THREE, c, k) => { const x = new THREE.Color(c); return k > 0 ? x.lerp(new THREE.Color("#FFFFFF"), k) : x.lerp(new THREE.Color("#000000"), -k); };
const pelo = (THREE, c) => new THREE.MeshPhysicalMaterial({ color: c, roughness: 0.78, sheen: 0.35, sheenRoughness: 0.6, sheenColor: schiarisci(THREE, c, 0.2) });
const lucido = (THREE, c) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.25, metalness: 0.1 });
const oro = THREE => new THREE.MeshStandardMaterial({ color: "#FFC93C", metalness: 0.9, roughness: 0.25, emissive: "#6B4A00", emissiveIntensity: 0.4 });
function sfera(THREE, r, m, x, y, z, sx = 1, sy = 1, sz = 1) { const o = new THREE.Mesh(new THREE.SphereGeometry(r, 24, 18), m); o.position.set(x, y, z); o.scale.set(sx, sy, sz); o.castShadow = true; return o; }
function cane3d(THREE, d) {
  const b = window.Disegni?.CANI?.[d.rk] || { fur: "#B98450", ear: "semi" }, r = rnd((d.seed % 2147483646) + 1);
  const fur = b.mix ? TONI[Math.floor(r() * TONI.length)] : b.fur, earC = b.mix ? schiarisci(THREE, fur, -0.25) : b.earC || schiarisci(THREE, fur, -0.25), muz = b.mix ? schiarisci(THREE, fur, 0.45) : b.muz || schiarisci(THREE, fur, 0.42);
  const P = pelo(THREE, fur), Pm = pelo(THREE, muz), Pe = pelo(THREE, earC), nero = lucido(THREE, "#120A06"), g = new THREE.Group();
  const torace = new THREE.Group(); g.add(torace); g.userData.torace = torace;
  const corpo = new THREE.Mesh(new THREE.CapsuleGeometry(0.3, 0.42, 8, 18), P); corpo.position.set(0, 0.5, -0.12); corpo.rotation.x = -0.42; corpo.castShadow = true; torace.add(corpo);
  torace.add(sfera(THREE, 0.24, Pm, 0, 0.62, 0.1, 1, 1.25, 0.75)); // il petto chiaro
  for (const s of [-1, 1]) { g.add(sfera(THREE, 0.22, P, s * 0.2, 0.26, -0.28, 0.9, 1, 1.25)); // le cosce
    const zampa = new THREE.Mesh(new THREE.CylinderGeometry(0.065, 0.075, 0.48, 12), P); zampa.position.set(s * 0.13, 0.25, 0.12); zampa.castShadow = true; g.add(zampa);
    g.add(sfera(THREE, 0.085, Pm, s * 0.13, 0.04, 0.17, 1, 0.65, 1.3)); g.add(sfera(THREE, 0.09, P, s * 0.24, 0.05, -0.12, 1, 0.6, 1.5)); }
  const testa = new THREE.Group(); testa.position.set(0, 1.0, 0.08); g.add(testa); g.userData.testa = testa;
  testa.add(sfera(THREE, 0.25, P, 0, 0, 0, 1, b.flat ? 0.9 : 0.95, 0.95));
  if (b.cap) testa.add(sfera(THREE, 0.255, pelo(THREE, b.cap), 0, 0.05, -0.02, 1, 0.8, 0.95));
  const muso = new THREE.Mesh(new THREE.CapsuleGeometry(b.flat ? 0.12 : 0.1, b.flat ? 0.04 : 0.16, 6, 14), Pm); muso.rotation.x = Math.PI / 2; muso.position.set(0, -0.07, b.flat ? 0.22 : 0.27); testa.add(muso);
  if (b.mask) testa.add(sfera(THREE, 0.1, pelo(THREE, b.mask), 0, -0.04, b.flat ? 0.26 : 0.32, 1, 0.8, 1));
  testa.add(sfera(THREE, 0.05, nero, 0, -0.03, b.flat ? 0.33 : 0.42, 1.2, 0.85, 0.9)); // il naso lucido
  for (const s of [-1, 1]) { const occhio = sfera(THREE, 0.04, lucido(THREE, b.eye || "#1E120A"), s * 0.1, 0.06, 0.21); testa.add(occhio);
    testa.add(sfera(THREE, 0.013, new THREE.MeshBasicMaterial({ color: "#FFFFFF" }), s * 0.1 + 0.012, 0.075, 0.245)); }
  if (b.patch) testa.add(sfera(THREE, 0.08, pelo(THREE, b.patch), (r() < 0.5 ? -1 : 1) * 0.1, 0.07, 0.17, 1, 1, 0.5));
  if (b.curly) for (let i = 0; i < 5; i++) testa.add(sfera(THREE, 0.08, pelo(THREE, schiarisci(THREE, fur, 0.12)), (i - 2) * 0.07, 0.22 - Math.abs(i - 2) * 0.03, -0.02));
  const ear = b.mix ? ["flop", "semi", "up"][Math.floor(r() * 3)] : b.ear || "semi";
  for (const s of [-1, 1]) {
    if (ear === "up") { const o = new THREE.Mesh(new THREE.ConeGeometry(0.085, 0.22, 12), Pe); o.position.set(s * 0.14, 0.25, -0.02); o.rotation.z = -s * 0.25; o.castShadow = true; testa.add(o); }
    else { const o = sfera(THREE, 0.1, Pe, s * (ear === "semi" ? 0.2 : 0.24), ear === "semi" ? 0.1 : -0.06, -0.02, 0.45, 1.5, 0.75); o.rotation.z = s * (ear === "semi" ? 0.7 : 0.2); testa.add(o); }
  }
  const collare = new THREE.Mesh(new THREE.TorusGeometry(0.17, 0.035, 8, 28), lucido(THREE, ["#E2394B", "#2F7FE0", "#2FB36B", "#8A3FE0"][Math.floor(r() * 4)])); collare.position.set(0, 0.82, 0.07); collare.rotation.x = Math.PI / 2 - 0.35; g.add(collare); g.userData.collare = collare;
  const coda = new THREE.Group(); coda.position.set(0, 0.2, -0.42); const cc = new THREE.Mesh(new THREE.CapsuleGeometry(0.045, 0.32, 6, 10), P); cc.position.y = 0.18; cc.rotation.x = -0.5; coda.add(cc); g.add(coda); g.userData.coda = coda;
  if (r() < 0.45) { const lingua = sfera(THREE, 0.04, lucido(THREE, "#E8707E"), 0, -0.16, b.flat ? 0.28 : 0.34, 1, 0.5, 1.3); testa.add(lingua); }
  return g;
}
function micio3d(THREE, d) {
  const b = window.Disegni?.GATTI?.[d.rk] || { fur: "#C88A4A" }, r = rnd((d.seed % 2147483646) + 1), k = b.fluffy ? 1.12 : 1;
  const fur = b.fur, P = pelo(THREE, fur), Pp = pelo(THREE, b.point || fur), W = pelo(THREE, b.white || schiarisci(THREE, fur, 0.35)), g = new THREE.Group();
  const torace = new THREE.Group(); g.add(torace); g.userData.torace = torace;
  const corpo = new THREE.Mesh(new THREE.CapsuleGeometry(0.24 * k, 0.26, 8, 18), P); corpo.position.set(0, 0.36, -0.04); corpo.rotation.x = -0.25; corpo.castShadow = true; torace.add(corpo);
  torace.add(sfera(THREE, 0.17 * k, W, 0, 0.42, 0.13, 1, 1.2, 0.7));
  if (b.stripe) for (let i = 0; i < 3; i++) { const st = new THREE.Mesh(new THREE.TorusGeometry(0.245 * k, 0.02, 6, 24, Math.PI), pelo(THREE, b.stripe)); st.position.set(0, 0.28 + i * 0.12, -0.08); st.rotation.set(-0.25, 0, Math.PI / 2 + Math.PI / 2); st.rotation.y = Math.PI / 2; torace.add(st); }
  if (b.patches) b.patches.forEach((c, i) => torace.add(sfera(THREE, 0.12, pelo(THREE, c), (i ? 1 : -1) * 0.12, 0.42 + i * 0.08, -0.12, 1, 0.8, 0.6)));
  for (const s of [-1, 1]) g.add(sfera(THREE, 0.07, W, s * 0.09, 0.04, 0.16, 1, 0.6, 1.3));
  const testa = new THREE.Group(); testa.position.set(0, 0.76, 0.06); g.add(testa); g.userData.testa = testa;
  testa.add(sfera(THREE, 0.2 * k, P, 0, 0, 0, 1.08, 0.95, 1));
  testa.add(sfera(THREE, 0.09, W, 0, -0.07, 0.15, 1.3, 0.8, 0.8));
  testa.add(sfera(THREE, 0.025, lucido(THREE, "#E8828E"), 0, -0.03, 0.22));
  const eye = new THREE.MeshStandardMaterial({ color: b.eye || "#CFE36B", emissive: b.eye || "#CFE36B", emissiveIntensity: 0.9, roughness: 0.2 }); // occhi che brillano nella notte
  for (const s of [-1, 1]) { testa.add(sfera(THREE, 0.04, eye, s * 0.08, 0.03, 0.17, 1, 1.25, 0.6)); testa.add(sfera(THREE, 0.018, lucido(THREE, "#000"), s * 0.08, 0.03, 0.19, 0.5, 1.4, 0.4));
    const o = new THREE.Mesh(new THREE.ConeGeometry(b.bigEars ? 0.09 : 0.07, b.bigEars ? 0.2 : 0.15, 4), Pp); o.position.set(s * 0.12, b.fold ? 0.14 : 0.18, 0); o.rotation.z = -s * 0.3; if (b.fold) o.rotation.x = 0.9; o.castShadow = true; testa.add(o);
    for (const q of [-1, 1]) { const baffo = new THREE.Mesh(new THREE.CylinderGeometry(0.003, 0.003, 0.2, 3), new THREE.MeshBasicMaterial({ color: "#F4F1E8" })); baffo.rotation.z = Math.PI / 2 + q * 0.12; baffo.position.set(s * 0.13, -0.06 + q * 0.015, 0.17); testa.add(baffo); } }
  const curva = new THREE.CatmullRomCurve3([new THREE.Vector3(0, 0, 0), new THREE.Vector3(0.12, 0.18, -0.12), new THREE.Vector3(0.2, 0.48, -0.1), new THREE.Vector3(0.12, 0.7, -0.02)]);
  const coda = new THREE.Group(); coda.position.set(0, 0.16, -0.26); const cm = new THREE.Mesh(new THREE.TubeGeometry(curva, 20, b.fluffy ? 0.06 : 0.04, 8), Pp); cm.castShadow = true; coda.add(cm); g.add(coda); g.userData.coda = coda;
  return g;
}
// gli accessori del negozio e il costume, in 3D sulla testa e davanti alla cuccia
function accessori3d(THREE, g, d) {
  const testa = g.userData.testa, gatto = d.t === "gatto", top = gatto ? 0.2 : 0.24, a = d.acc || [];
  if (a.includes("corona")) { const c = new THREE.Group(), O = oro(THREE), base = new THREE.Mesh(new THREE.CylinderGeometry(0.13, 0.14, 0.08, 18, 1, true), O); base.material.side = THREE.DoubleSide; c.add(base);
    for (let i = 0; i < 6; i++) { const p = new THREE.Mesh(new THREE.ConeGeometry(0.03, 0.09, 6), O), an = (i / 6) * Math.PI * 2; p.position.set(Math.cos(an) * 0.13, 0.08, Math.sin(an) * 0.13); c.add(p); }
    c.add(sfera(THREE, 0.025, new THREE.MeshStandardMaterial({ color: "#E2394B", emissive: "#E2394B", emissiveIntensity: 1.2 }), 0, 0.01, 0.14));
    c.position.set(0, top + 0.02, 0); c.rotation.z = 0.12; testa.add(c); }
  if (a.includes("fiocco")) { const m = lucido(THREE, "#FF5A9E"), f = new THREE.Group();
    for (const s of [-1, 1]) { const o = new THREE.Mesh(new THREE.ConeGeometry(0.06, 0.12, 10), m); o.rotation.z = s * Math.PI / 2; o.position.x = s * 0.06; f.add(o); }
    f.add(sfera(THREE, 0.03, m, 0, 0, 0)); f.position.set(0.13, top - 0.04, 0.05); f.rotation.z = -0.4; testa.add(f); }
  if (a.includes("collare") && g.userData.collare) { g.userData.collare.material = oro(THREE); const med = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.015, 18), oro(THREE));
    med.rotation.x = Math.PI / 2; med.position.set(0, 0.74, 0.25); g.add(med); }
  if (a.includes("osso")) { const O = oro(THREE), o = new THREE.Group(), c = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, 0.3, 10), O); c.rotation.z = Math.PI / 2; o.add(c);
    for (const s of [-1, 1]) for (const q of [-1, 1]) o.add(sfera(THREE, 0.045, O, s * 0.16, 0, q * 0.035)); o.position.set(0.28, 0.04, 0.3); o.rotation.y = 0.5; g.add(o); }
  if (d.vestito === "halloween") { const m = new THREE.MeshStandardMaterial({ color: "#3A1F57", roughness: 0.7 }), h = new THREE.Group();
    const falda = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.22, 0.015, 24), m), cono = new THREE.Mesh(new THREE.ConeGeometry(0.12, 0.3, 18), m), nastro = new THREE.Mesh(new THREE.CylinderGeometry(0.115, 0.12, 0.04, 18), lucido(THREE, "#FF8A1F"));
    cono.position.y = 0.15; cono.rotation.z = -0.25; nastro.position.y = 0.03; h.add(falda, cono, nastro); h.position.set(-0.03, top - 0.01, 0); h.rotation.z = 0.15;
    if (!a.includes("corona")) testa.add(h); }
  if (d.vestito === "lucine") { const cols = ["#FF5A6E", "#FFD23F", "#5BE37D", "#4FB4FF"]; for (let i = 0; i < 6; i++) { const c = cols[i % 4];
    const l = sfera(THREE, 0.025, new THREE.MeshStandardMaterial({ color: c, emissive: c, emissiveIntensity: 2.5 }), Math.cos(i) * 0.17, 0.82 + Math.sin(i * 2) * 0.01, 0.07 + Math.sin(i) * 0.17); g.add(l); } }
}

async function apri(v, opz = {}) {
  if (M) chiudi();
  const THREE = await import("three");
  const [{ OrbitControls }, { EffectComposer }, { RenderPass }, { UnrealBloomPass }, { OutputPass }] = await Promise.all([
    import("three/addons/controls/OrbitControls.js"), import("three/addons/postprocessing/EffectComposer.js"), import("three/addons/postprocessing/RenderPass.js"),
    import("three/addons/postprocessing/UnrealBloomPass.js"), import("three/addons/postprocessing/OutputPass.js")]);
  const box = document.createElement("div"); box.className = "mondo3d";
  box.innerHTML = `<div class="m3-top"><b>🎮 ${v.nome.replace(/[&<>]/g, "")}</b><span>${v.luci} ${v.luci === 1 ? "luce" : "luci"} · trascina per girare, pizzica per avvicinarti, tocca un animale</span></div>
    <button type="button" class="m3-esci" aria-label="Esci dal 3D">✕</button><div class="m3-scheda" hidden></div>`;
  document.body.appendChild(box);
  const piccolo = innerWidth < 700;
  const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" }); renderer.setPixelRatio(Math.min(devicePixelRatio, piccolo ? 1.5 : 2));
  renderer.setSize(innerWidth, innerHeight); renderer.outputColorSpace = THREE.SRGBColorSpace; renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.55;
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  box.prepend(renderer.domElement);
  const scene = new THREE.Scene(); scene.fog = new THREE.FogExp2("#0E1A3E", 0.0085);
  const lista = v.lista.slice(0, 220), R = Math.max(26, (v.R || 200) / U);
  const camera = new THREE.PerspectiveCamera(48, innerWidth / innerHeight, 0.3, 900);
  camera.position.set(0, R * 0.55 + 9, R * 1.0 + 12);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true; controls.dampingFactor = 0.07; controls.maxPolarAngle = 1.36; controls.minDistance = 6; controls.maxDistance = R * 2.4 + 30;
  controls.autoRotate = true; controls.autoRotateSpeed = 0.35; controls.target.set(0, 1.5, 0); controls.enablePan = false;
  renderer.domElement.addEventListener("pointerdown", () => { controls.autoRotate = false; }, { once: true });

  // cielo: sfumato dal blu notte all'orizzonte più chiaro, stelle e luna
  const cielo = new THREE.Mesh(new THREE.SphereGeometry(600, 32, 16), new THREE.ShaderMaterial({ side: THREE.BackSide, depthWrite: false, fog: false,
    vertexShader: "varying vec3 p; void main(){ p = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.); }",
    fragmentShader: "varying vec3 p; void main(){ float h = clamp(normalize(p).y, 0., 1.); vec3 c = mix(vec3(.13,.2,.42), vec3(.02,.04,.12), pow(h,.55)); gl_FragColor = vec4(c,1.); }" }));
  scene.add(cielo);
  const sp = []; for (let i = 0; i < 1400; i++) { const a = Math.random() * Math.PI * 2, e = 0.08 + Math.random() * 1.4, r = 560; sp.push(r * Math.cos(a) * Math.cos(e), r * Math.sin(e), r * Math.sin(a) * Math.cos(e)); }
  scene.add(new THREE.Points(new THREE.BufferGeometry().setAttribute("position", new THREE.Float32BufferAttribute(sp, 3)), new THREE.PointsMaterial({ color: "#FFFFFF", size: 1.6, sizeAttenuation: false, fog: false })));
  const lunaM = new THREE.Mesh(new THREE.SphereGeometry(14, 32, 16), new THREE.MeshBasicMaterial({ color: new THREE.Color("#FFF4DE").multiplyScalar(2.2), fog: false })); lunaM.position.set(-230, 190, -360); scene.add(lunaM);

  // luci: cielo e luna fredda con le ombre, lampioni caldi
  scene.add(new THREE.HemisphereLight("#8FA6EE", "#2A3A2C", 1.5));
  const luna = new THREE.DirectionalLight("#C8D6FF", 2.2); luna.position.set(-50, 80, -60); luna.castShadow = true;
  luna.shadow.mapSize.set(piccolo ? 1024 : 2048, piccolo ? 1024 : 2048); const sc = luna.shadow.camera; sc.left = sc.bottom = -R - 20; sc.right = sc.top = R + 20; sc.near = 1; sc.far = 300; luna.shadow.bias = -0.0005; luna.shadow.normalBias = 0.04;
  scene.add(luna);

  const mat = (c, o = {}) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.8, ...o });
  const ombre = m => { m.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } }); return m; };
  const tErba = ERBA(THREE), tPietra = PIETRA(THREE), tAsf = ASFALTO(THREE), tLegno = LEGNO(THREE), tTegRosse = TEGOLE(THREE, "#9C3E2A"), tTegScure = TEGOLE(THREE, "#4A2A14");

  // terreno: prato, vie, piazza in pietra
  const prato = new THREE.Mesh(new THREE.CircleGeometry(R + 70, 96), mat("#FFFFFF", { map: tErba, roughness: 1 })); prato.rotation.x = -Math.PI / 2; prato.receiveShadow = true; scene.add(prato);
  const fuori = new THREE.Mesh(new THREE.CircleGeometry(800, 48), mat("#14261E", { roughness: 1 })); fuori.rotation.x = -Math.PI / 2; fuori.position.y = -0.06; scene.add(fuori);
  const strada = mat("#FFFFFF", { map: tAsf, roughness: 0.95 });
  const anelli = [...new Set(lista.map(d => Math.round(Math.hypot(d.off[0], d.off[1] / SQ) / 10) * 10))];
  for (const a of anelli) { const r = a / U, m = new THREE.Mesh(new THREE.RingGeometry(r - 1.1, r + 1.1, 128), strada); m.rotation.x = -Math.PI / 2; m.position.y = 0.02; m.receiveShadow = true; scene.add(m);
    const riga = new THREE.Mesh(new THREE.RingGeometry(r - 0.05, r + 0.05, 128), new THREE.MeshBasicMaterial({ color: "#C9B98A", transparent: true, opacity: 0.35 })); riga.rotation.x = -Math.PI / 2; riga.position.y = 0.03; scene.add(riga); }
  for (let i = 0; i < 6; i++) { const a = (i / 6) * Math.PI * 2 + 0.26, L = R - 6; const m = new THREE.Mesh(new THREE.PlaneGeometry(2.2, L), strada); m.rotation.x = -Math.PI / 2; m.rotation.z = -a + Math.PI / 2;
    m.position.set(Math.cos(a) * (L / 2 + 6), 0.015, Math.sin(a) * (L / 2 + 6)); m.receiveShadow = true; scene.add(m); }
  const piazza = new THREE.Mesh(new THREE.CylinderGeometry(10.5, 10.8, 0.3, 72), [mat("#5A5A66"), mat("#FFFFFF", { map: tPietra, roughness: 0.85 }), mat("#5A5A66")]);
  piazza.position.y = 0.15; piazza.receiveShadow = true; scene.add(piazza);
  const cordolo = new THREE.Mesh(new THREE.TorusGeometry(10.6, 0.22, 8, 96), mat("#8A8A96")); cordolo.rotation.x = Math.PI / 2; cordolo.position.y = 0.3; scene.add(cordolo);

  // edifici della piazza, sbloccati dalle luci come in paese.js
  const gira = [], finestra = new THREE.MeshStandardMaterial({ color: "#FFD27A", emissive: "#FFB347", emissiveIntensity: 2.2 });
  const add = (g, x, z, ry = 0) => { g.position.set(x, 0.3, z); g.rotation.y = ry; scene.add(ombre(g)); return g; };
  if (v.luci >= 5) { const g = new THREE.Group(), pietra = mat("#FFFFFF", { map: tPietra });
    const vasca = new THREE.Mesh(new THREE.CylinderGeometry(2.6, 2.8, 0.9, 40), pietra); vasca.position.y = 0.45;
    const acqua = new THREE.Mesh(new THREE.CylinderGeometry(2.3, 2.3, 0.08, 40), new THREE.MeshStandardMaterial({ color: "#3C8CC8", emissive: "#1B5FA8", emissiveIntensity: 0.9, roughness: 0.1, metalness: 0.2 })); acqua.position.y = 0.86;
    const col = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.45, 2.8, 16), pietra); col.position.y = 1.7;
    const coppa = new THREE.Mesh(new THREE.CylinderGeometry(1, 0.4, 0.4, 24), pietra); coppa.position.y = 3.1; g.add(vasca, acqua, col, coppa); add(g, 0, 0);
    const N = 80, gp = new THREE.Points(new THREE.BufferGeometry().setAttribute("position", new THREE.Float32BufferAttribute(new Float32Array(N * 3), 3)), new THREE.PointsMaterial({ color: "#CFF2FF", size: 0.14, transparent: true, opacity: 0.85 }));
    g.add(gp); gira.push(t => { const p = gp.geometry.attributes.position; for (let i = 0; i < N; i++) { const f = ((t / 1100 + i / N) % 1), a = i * 2.4; p.setXYZ(i, Math.cos(a) * f * 1.9, 3.3 + f * 1.8 - f * f * 4.3, Math.sin(a) * f * 1.9); } p.needsUpdate = true; }); }
  const casa = (w, h, d, muro, tegole, alto = 2) => { const g = new THREE.Group(), b = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat(muro)); b.position.y = h / 2;
    const tetto = new THREE.Mesh(new THREE.CylinderGeometry(0.01, w * 0.78, alto, 4, 1), mat("#FFFFFF", { map: tegole })); tetto.position.y = h + alto / 2; tetto.rotation.y = Math.PI / 4; tetto.scale.z = d / w;
    for (const s of [-1, 1]) { const f = new THREE.Mesh(new THREE.PlaneGeometry(0.7, 0.8), finestra); f.position.set(s * w * 0.27, h * 0.58, d / 2 + 0.01); g.add(f); }
    const porta = new THREE.Mesh(new THREE.PlaneGeometry(0.8, 1.3), mat("#5A3417")); porta.position.set(0, 0.65, d / 2 + 0.01); g.add(b, tetto, porta); return g; };
  if (v.luci >= 25) add(casa(4.2, 2.8, 3.2, "#C77A8E", tTegRosse), 6.5, -2, -0.9);
  if (v.luci >= 50) { const g = casa(5, 3.6, 3.6, "#EEF2FA", tTegScure, 1.4), c1 = new THREE.Mesh(new THREE.BoxGeometry(1.4, 0.42, 0.05), new THREE.MeshStandardMaterial({ color: "#E2394B", emissive: "#E2394B", emissiveIntensity: 1.6 })), c2 = c1.clone();
    c2.rotation.z = Math.PI / 2; c1.position.set(0, 4.4, 1.82); c2.position.copy(c1.position); g.add(c1, c2); add(g, -5, 3.5, 0.6); }
  if (v.luci >= 100) { const g = new THREE.Group(), marmo = mat("#EDE4D0", { roughness: 0.5 }); for (let i = 0; i < 4; i++) { const c = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.34, 3.4, 16), marmo); c.position.set(-2.4 + i * 1.6, 1.7, 0); g.add(c); }
    const t = new THREE.Mesh(new THREE.BoxGeometry(6.2, 0.5, 1.6), marmo); t.position.y = 3.6; const fr = new THREE.Mesh(new THREE.CylinderGeometry(0.01, 3.6, 1.1, 3), marmo); fr.rotation.z = Math.PI / 2; fr.rotation.y = Math.PI / 2; fr.scale.set(1, 1, 0.45); fr.position.y = 4.3; g.add(t, fr); add(g, 0, -6); }
  if (v.luci >= 250) { const ruota = new THREE.Mesh(new THREE.TorusGeometry(3, 0.14, 8, 48), new THREE.MeshStandardMaterial({ color: "#FFC55C", emissive: "#FF9A3C", emissiveIntensity: 1.4 }));
    ruota.position.set(6, 3.8, 5); scene.add(ruota); gira.push(t => { ruota.rotation.z = t / 2600; }); }

  // bosco di pini e cespugli tutto intorno
  const nAlb = Math.round((R + 30) * 2.2), o = new THREE.Object3D(), r0 = rnd(v.nome.length * 977 + 13);
  const tron = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.16, 0.26, 1.6, 6), mat("#3E2716"), nAlb);
  const pino = [0, 1, 2].map(k => new THREE.InstancedMesh(new THREE.ConeGeometry(1.7 - k * 0.42, 2.2 - k * 0.2, 9), mat("#FFFFFF", { roughness: 0.95 }), nAlb));
  for (let i = 0; i < nAlb; i++) { const a = r0() * Math.PI * 2, r = R + 3 + Math.pow(r0(), 0.7) * 40, k = 0.8 + r0() * 1.1;
    if (Math.abs(((a + Math.PI * 2) % (Math.PI * 2)) - Math.PI / 2) < 0.12 && r < R + 20) { o.scale.setScalar(0.0001); } else o.scale.setScalar(k);
    o.position.set(Math.cos(a) * r, 0.8 * k, Math.sin(a) * r); o.rotation.set(0, r0() * 6, 0); o.updateMatrix(); tron.setMatrixAt(i, o.matrix);
    const col = new THREE.Color().setHSL(0.36 + r0() * 0.04, 0.42, 0.2 + r0() * 0.1);
    pino.forEach((p, j) => { o.position.y = (1.9 + j * 1.25) * k; o.updateMatrix(); p.setMatrixAt(i, o.matrix); p.setColorAt(i, col); }); }
  for (const m of [tron, ...pino]) { m.castShadow = true; m.receiveShadow = true; scene.add(m); }
  const nCes = Math.round(R * 2.5), ces = new THREE.InstancedMesh(new THREE.IcosahedronGeometry(0.6, 1), mat("#FFFFFF", { roughness: 1 }), nCes);
  for (let i = 0; i < nCes; i++) { const a = r0() * Math.PI * 2, r = 12 + r0() * (R - 8), k = 0.5 + r0() * 0.9; o.position.set(Math.cos(a) * r, 0.25 * k, Math.sin(a) * r); o.scale.set(k * 1.3, k, k * 1.3); o.updateMatrix();
    ces.setMatrixAt(i, o.matrix); ces.setColorAt(i, new THREE.Color().setHSL(0.3 + r0() * 0.08, 0.45, 0.17 + r0() * 0.08)); }
  ces.castShadow = ces.receiveShadow = true; scene.add(ces);

  // lampioni: palo in ghisa, lanterna che brilla, pozza di luce calda
  const lam = [], bulbo = new THREE.MeshStandardMaterial({ color: "#FFE3A0", emissive: "#FFC060", emissiveIntensity: 4 });
  for (let i = 0; i < 6; i++) { const a = (i / 6) * Math.PI * 2 + 0.46, x = Math.cos(a) * 12.2, z = Math.sin(a) * 12.2, g = new THREE.Group();
    const palo = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.12, 3.8, 8), mat("#1E2436", { metalness: 0.6, roughness: 0.4 })); palo.position.y = 1.9;
    const lan = new THREE.Mesh(new THREE.CylinderGeometry(0.28, 0.2, 0.55, 6), bulbo); lan.position.y = 3.95;
    const cap = new THREE.Mesh(new THREE.ConeGeometry(0.42, 0.35, 6), mat("#1E2436", { metalness: 0.6 })); cap.position.y = 4.4;
    g.add(palo, lan, cap); g.position.set(x, 0.3, z); scene.add(ombre(g));
    const l = new THREE.PointLight("#FFB862", 22, 18, 1.7); l.position.set(x, 4, z); scene.add(l); lam.push(l); }

  // cartello d'ingresso in legno
  const cart = new THREE.Group(), tav = new THREE.Mesh(new THREE.BoxGeometry(Math.max(5, v.nome.length * 0.62 + 2), 1.5, 0.18), mat("#FFFFFF", { map: tLegno }));
  tav.position.y = 2.2; for (const s of [-1, 1]) { const p = new THREE.Mesh(new THREE.BoxGeometry(0.22, 2.6, 0.22), mat("#4A2C17")); p.position.set(s * (tav.geometry.parameters.width / 2 - 0.4), 1.3, -0.12); cart.add(p); }
  const scritta = ETICHETTA(THREE, v.nome.toUpperCase(), { size: 60, bg: "rgba(0,0,0,0)", bordo: "rgba(0,0,0,0)", fg: "#FFE9B8" }); scritta.position.set(0, 2.2, 0.2); scritta.scale.multiplyScalar(1.4);
  cart.add(tav, scritta); cart.position.set(0, 0, R + 4); scene.add(ombre(cart));

  // gli animali: cuccia vera per i cani, casetta col tetto per i gatti, il muso disegnato al suo posto
  const LIV = [[70, "castello"], [50, "villa"], [30, "giardino"]];
  const PIANO = new THREE.PlaneGeometry(1, 1).translate(0, 0.5, 0), pet = [], toccabili = [], muro = mat("#FFFFFF", { map: tLegno }), muroGatto = mat("#E9D9BE"), tettoC = mat("#FFFFFF", { map: tTegScure }), tettoG = mat("#FFFFFF", { map: tTegRosse });
  const portaLuce = new THREE.MeshStandardMaterial({ color: "#120802", emissive: "#7A3A10", emissiveIntensity: 0.35 });
  const arco = new THREE.ShapeGeometry((() => { const s = new THREE.Shape(); s.moveTo(-0.85, 0); s.lineTo(-0.85, 1.1); s.absarc(0, 1.1, 0.85, Math.PI, 0, true); s.lineTo(0.85, 0); s.lineTo(-0.85, 0); return s; })());
  const fiore = ["#FF5A6E", "#FFD23F", "#FF8AB6", "#7FC8FF", "#FFFFFF"].map(c => new THREE.MeshStandardMaterial({ color: c, emissive: c, emissiveIntensity: 0.25 }));
  for (const d of lista) {
    const x = d.off[0] / U, z = d.off[1] / SQ / U, liv = LIV.find(l => d.pt >= l[0])?.[1], k = liv === "castello" ? 1.35 : liv === "villa" ? 1.18 : 1;
    const g = new THREE.Group(); g.position.set(x, 0, z); g.rotation.y = Math.atan2(-x, -z) + Math.PI; scene.add(g); // la porta guarda fuori, verso chi arriva dalle vie
    const cane = d.t !== "gatto" && d.t !== "altro";
    if (cane) { // cuccia: pareti di legno, tetto a capanna con tegole scure, porta ad arco illuminata dentro
      const W = 2.6 * k, H = 1.9 * k, D = 2.4 * k, c = new THREE.Group();
      const corpo = new THREE.Mesh(new THREE.BoxGeometry(W, H, D), muro); corpo.position.y = H / 2;
      const Hr = W * 0.5, tri = new THREE.Shape(); tri.moveTo(-W / 2, 0); tri.lineTo(W / 2, 0); tri.lineTo(0, Hr); tri.lineTo(-W / 2, 0);
      const timpano = new THREE.Mesh(new THREE.ExtrudeGeometry(tri, { depth: D, bevelEnabled: false }), muro); timpano.position.set(0, H, -D / 2);
      const ang = Math.atan2(Hr, W / 2), lato = Math.hypot(Hr, W / 2) + 0.35;
      for (const q of [-1, 1]) { const falda = new THREE.Mesh(new THREE.BoxGeometry(lato, 0.14, D + 0.5), tettoC); falda.position.set(q * W / 4, H + Hr / 2 + 0.07, 0); falda.rotation.z = -q * ang; c.add(falda); }
      const porta = new THREE.Mesh(arco, portaLuce); porta.scale.setScalar(k * 0.9); porta.position.set(0, 0.02, D / 2 + 0.01);
      c.add(corpo, timpano, porta); g.add(ombre(c));
    } else if (d.t === "gatto") { // casetta: muri chiari, tetto rosso, comignolo, finestre accese; il gatto sta sul tetto
      const W = 2.8 * k, H = 2 * k, D = 2.6 * k, c = casa(W, H, D, "#E9D9BE", tTegRosse, 1.5 * k);
      const com = new THREE.Mesh(new THREE.BoxGeometry(0.4, 1, 0.4), mat("#A9533A")); com.position.set(W * 0.28, H + 1, -D * 0.15); c.add(com); g.add(ombre(c));
    } else { const ped = new THREE.Mesh(new THREE.CylinderGeometry(1.1, 1.3, 0.8, 24), mat("#FFFFFF", { map: tPietra })); ped.position.y = 0.4; g.add(ombre(ped)); }
    if (liv) { // il giardino: steccato e fiori; la villa e il castello: lanterne e torri
      const n = 14, rr = 2.4 * k + 0.6; for (let i = 0; i < n; i++) { const a = (i / n) * Math.PI * 2; if (Math.abs(Math.sin(a / 2)) < 0.2) continue;
        const p = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.55, 0.1), mat("#EDE4D0")); p.position.set(Math.sin(a) * rr, 0.28, Math.cos(a) * rr); g.add(p);
        const f = new THREE.Mesh(new THREE.SphereGeometry(0.14, 8, 6), fiore[i % 5]); f.position.set(Math.sin(a + 0.2) * (rr - 0.35), 0.16, Math.cos(a + 0.2) * (rr - 0.35)); g.add(f); }
      if (liv !== "giardino") for (const s of [-1, 1]) { const l = new THREE.Mesh(new THREE.SphereGeometry(0.16, 10, 8), bulbo); l.position.set(s * 1.7 * k, 1.5 * k, 1.5 * k); g.add(l); }
      if (liv === "castello") for (const s of [-1, 1]) { const pietra = mat("#FFFFFF", { map: tPietra }), tor = new THREE.Mesh(new THREE.CylinderGeometry(0.55, 0.62, 4, 14), pietra); tor.position.set(s * 2.6 * k, 2, -0.6);
        const tet = new THREE.Mesh(new THREE.ConeGeometry(0.85, 1.6, 14), mat("#8C1F45")); tet.position.set(s * 2.6 * k, 4.8, -0.6);
        const ban = new THREE.Mesh(new THREE.PlaneGeometry(0.7, 0.42), new THREE.MeshStandardMaterial({ color: "#FFD23F", side: THREE.DoubleSide, emissive: "#FFB000", emissiveIntensity: 0.5 })); ban.position.set(s * 2.6 * k + 0.36, 6, -0.6);
        const asta = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 1, 6), mat("#222")); asta.position.set(s * 2.6 * k, 5.9, -0.6); g.add(ombre(tor), tet, ban, asta); gira.push(t => { ban.rotation.y = Math.sin(t / 400 + s) * 0.4; }); }
    }
    // l'animale in 3D, coi colori della sua razza: il cane seduto davanti alla porta, il gatto sul tetto; gli altri restano medaglioni
    let s, base;
    if (d.t === "altro") {
      s = new THREE.Mesh(PIANO, new THREE.MeshBasicMaterial({ transparent: true, alphaTest: 0.08, toneMapped: false, side: THREE.DoubleSide })); base = new THREE.Vector3(0, 0.8, 0);
      svgTex(THREE, opz.svg(d)).then(r => { if (!r || !M) return; s.material.map = r.tex; s.material.needsUpdate = true; s.scale.set(2.6 * r.a, 2.6, 1); });
    } else {
      s = d.t === "gatto" ? micio3d(THREE, d) : cane3d(THREE, d); s.scale.setScalar((d.t === "gatto" ? 1.25 : 1.35) * k);
      base = cane ? new THREE.Vector3(0, 0, 1.25 * k + 0.75 * k) : new THREE.Vector3(0, 2 * k + 0.62 * k, 0.55 * k);
      accessori3d(THREE, s, d);
    }
    s.position.copy(base); g.add(s); s.userData.d = d; toccabili.push(s);
    const nome = ETICHETTA(THREE, (d.acc?.includes("corona") ? "👑 " : "") + d.n, d.t === "gatto" ? { fg: "#2F3A10", bg: "#E9F2C4", bordo: "#3D4A18" } : {});
    nome.position.set(0, (cane ? 3.6 : 4.8) * k + 0.4, 0); g.add(nome);
    pet.push({ d, g, s, base, cane, fase: (d.seed % 628) / 100 });
  }
  // il tuo animale: una freccia che rimbalza
  const mio = opz.mio && pet.find(p => p.d === opz.mio); let freccia = null;
  if (mio) { freccia = ETICHETTA(THREE, "⬇ TU", { size: 52, fg: "#4A2C04", bg: "#FFD23F", bordo: "#8C4A00" }); freccia.scale.multiplyScalar(1.3); mio.g.add(freccia);
    const { x, z } = mio.g.position, L = Math.hypot(x, z) || 1; controls.target.set(x, 2, z); camera.position.set(x + (x / L) * 11, 8, z + (Math.hypot(x, z) ? z / L : 1) * 11); controls.autoRotate = false; }

  // lucciole, cuori e fuochi d'artificio
  const NL = 90, lp = new Float32Array(NL * 3), ls = [...Array(NL)].map(() => [Math.random() * Math.PI * 2, 6 + Math.random() * (R + 14), 0.5 + Math.random() * 3, Math.random() * 10]);
  const lucc = new THREE.Points(new THREE.BufferGeometry().setAttribute("position", new THREE.BufferAttribute(lp, 3)),
    new THREE.PointsMaterial({ color: new THREE.Color("#FFF3A0").multiplyScalar(3), size: 0.22, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false }));
  scene.add(lucc);
  const CUORI = ["❤️", "💛", "🐾", "✨", "🦴"].map(e => EMOJI(THREE, e)), volanti = [], fuochi = pet.filter(p => p.d.acc?.includes("fuochi")), scoppi = [];
  const scoppio = p => { const n = 60, pos = new Float32Array(n * 3), dir = [...Array(n)].map(() => new THREE.Vector3().randomDirection().multiplyScalar(0.7 + Math.random() * 0.5));
    const col = new THREE.Color(["#FF5A6E", "#FFD23F", "#4FB4FF", "#5BE37D", "#FF9A3C"][Math.floor(Math.random() * 5)]).multiplyScalar(3);
    const pts = new THREE.Points(new THREE.BufferGeometry().setAttribute("position", new THREE.BufferAttribute(pos, 3)), new THREE.PointsMaterial({ color: col, size: 0.28, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false }));
    pts.position.set(p.g.position.x + (Math.random() - 0.5) * 2, 10 + Math.random() * 4, p.g.position.z); scene.add(pts); scoppi.push({ pts, dir, t0: performance.now() }); };
  const cuore = p => { const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: CUORI[Math.floor(Math.random() * CUORI.length)], transparent: true, depthWrite: false }));
    s.scale.set(0.9, 0.9, 1); const w = p.s.getWorldPosition(new THREE.Vector3()); s.position.set(w.x, w.y + 2, w.z); scene.add(s); volanti.push({ s, t0: performance.now() }); };

  // tocca un animale: salta, manda cuori, si apre la sua scheda
  const ray = new THREE.Raycaster(), mouse = new THREE.Vector2(), scheda = box.querySelector(".m3-scheda"); let giu = null;
  renderer.domElement.addEventListener("pointerdown", e => { giu = [e.clientX, e.clientY]; });
  renderer.domElement.addEventListener("pointerup", e => {
    if (!giu || Math.hypot(e.clientX - giu[0], e.clientY - giu[1]) > 6) return;
    mouse.set((e.clientX / innerWidth) * 2 - 1, -(e.clientY / innerHeight) * 2 + 1); ray.setFromCamera(mouse, camera);
    const hit = ray.intersectObjects(toccabili, true)[0]; if (!hit) { scheda.hidden = true; return; }
    let o = hit.object; while (o && !o.userData.d) o = o.parent;
    const d = o.userData.d, p = pet.find(q => q.d === d); scheda.innerHTML = opz.scheda(d); scheda.hidden = false; p.salto = performance.now();
    for (let i = 0; i < 3; i++) setTimeout(() => cuore(p), i * 160);
  });

  const composer = new EffectComposer(renderer); composer.addPass(new RenderPass(scene, camera));
  const bloom = new UnrealBloomPass(new THREE.Vector2(innerWidth, innerHeight), 0.9, 0.5, 1.0); composer.addPass(bloom); composer.addPass(new OutputPass());
  let uC = 0, uF = 0, raf = 0;
  const giro = t => {
    raf = requestAnimationFrame(giro);
    for (const p of pet) { let y = p.base.y + Math.max(0, Math.sin(t / 900 + p.fase)) * 0.06;
      if (p.salto) { const q = (t - p.salto) / 650; if (q < 1) y += Math.sin(q * Math.PI) * 1.1; else p.salto = 0; } else if (Math.random() < 0.0006) p.salto = t;
      p.s.position.y = y;
      const w = p.g.position, yaw = Math.atan2(camera.position.x - w.x, camera.position.z - w.z) - p.g.rotation.y, a = Math.atan2(Math.sin(yaw), Math.cos(yaw));
      if (p.d.t === "altro") p.s.rotation.y = a;
      else { const u = p.s.userData; if (u.testa) u.testa.rotation.y += (Math.max(-0.7, Math.min(0.7, a)) - u.testa.rotation.y) * 0.05; // ti guarda
        if (u.coda) u.coda.rotation.z = Math.sin(t / (p.d.t === "gatto" ? 700 : 140) + p.fase) * (p.d.t === "gatto" ? 0.25 : 0.55); // il cane scodinzola, il gatto muove piano la coda
        if (u.torace) u.torace.scale.y = 1 + Math.sin(t / 700 + p.fase) * 0.025; } }
    if (freccia) freccia.position.y = (mio.d.t === "gatto" ? 7 : 5.6) + Math.abs(Math.sin(t / 280)) * 0.7;
    for (let i = 0; i < NL; i++) { const [a, r, h, f] = ls[i], w = t / 4200 + f; lp[i * 3] = Math.cos(a + w * 0.25) * r + Math.sin(w * 1.7) * 1.4; lp[i * 3 + 1] = h + Math.sin(w * 2.3) * 0.5; lp[i * 3 + 2] = Math.sin(a + w * 0.25) * r + Math.cos(w * 1.3) * 1.4; }
    lucc.geometry.attributes.position.needsUpdate = true;
    if (t - uC > 1100 && pet.length) { uC = t; cuore(pet[Math.floor(Math.random() * pet.length)]); }
    if (fuochi.length && t - uF > 1200) { uF = t; scoppio(fuochi[Math.floor(Math.random() * fuochi.length)]); }
    for (let i = volanti.length - 1; i >= 0; i--) { const q = volanti[i], k = (t - q.t0) / 2400; q.s.position.y += 0.022; q.s.material.opacity = 1 - k; if (k >= 1) { scene.remove(q.s); q.s.material.dispose(); volanti.splice(i, 1); } }
    for (let i = scoppi.length - 1; i >= 0; i--) { const b = scoppi[i], k = (t - b.t0) / 1700, p = b.pts.geometry.attributes.position;
      b.dir.forEach((dv, j) => p.setXYZ(j, dv.x * k * 5, dv.y * k * 5 - k * k * 2.5, dv.z * k * 5)); p.needsUpdate = true; b.pts.material.opacity = 1 - k * k;
      if (k >= 1) { scene.remove(b.pts); b.pts.geometry.dispose(); scoppi.splice(i, 1); } }
    for (const f of gira) f(t);
    lam.forEach((l, i) => l.intensity = 20 + Math.sin(t / 470 + i * 1.7) * 2.5);
    controls.update(); composer.render();
  };
  raf = requestAnimationFrame(giro);
  const resize = () => { camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); renderer.setSize(innerWidth, innerHeight); composer.setSize(innerWidth, innerHeight); };
  addEventListener("resize", resize);
  box.querySelector(".m3-esci").onclick = chiudi;
  M = { renderer, box, scene, pet, stop: () => { cancelAnimationFrame(raf); removeEventListener("resize", resize); } };
}

function chiudi() {
  if (!M) return;
  M.stop(); M.renderer.dispose(); M.renderer.forceContextLoss?.(); M.box.remove(); M = null;
}

window.Mondo3D = { apri, chiudi, get mondo() { return M; } };
