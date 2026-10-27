// Zampe d'Italia: mappa notturna. Legge data/animali.json (scritto dal motore dei commenti) e accende una luce per ogni animale.
// Da lontano sono luci su un canvas (reggono decine di migliaia di punti); da vicino diventano cucce e tetti disegnati.
const CONFIG = { ig: "https://www.instagram.com/zampeditalia/", obiettivo: 10000 };
const D = window.Disegni;
const $ = s => document.querySelector(s);
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const fmt = n => n.toLocaleString("it-IT");
const ANTEPRIMA = new URLSearchParams(location.search).has("anteprima");
const COL = { cane: [255, 197, 92], gatto: [207, 227, 107], altro: [130, 220, 235], sogno: [190, 205, 255], stella: [255, 244, 222] };

// ---------- mappa ----------
const map = L.map("map", { zoomControl: false, attributionControl: false, minZoom: 5, maxZoom: 16, zoomSnap: 0.25,
  zoomAnimation: false, fadeAnimation: false, markerZoomAnimation: false });
const ITALY = L.latLngBounds([36.4, 6.4], [47.2, 18.7]);
const PAD = () => ({ paddingTopLeft: [0, innerWidth < 600 ? 175 : 165], paddingBottomRight: [0, innerWidth < 600 ? 160 : 150] });
map.fitBounds(ITALY, PAD());
map.setMaxBounds(ITALY.pad(0.4));
// Se la pagina si apre nascosta (anteprime, schede in background) la mappa nasce senza dimensioni: la reinquadro appena ne ha.
let fitted = map.getSize().y > 0;
new ResizeObserver(() => { map.invalidateSize(); if (!fitted && map.getSize().y > 0) { fitted = true; map.fitBounds(ITALY, PAD()); } redraw(); }).observe(map.getContainer());

// ---------- luci (canvas) ----------
const glow = document.createElement("canvas"); glow.id = "glow"; map.getContainer().appendChild(glow);
const gx = glow.getContext("2d");
const sprite = rgb => {
  const c = document.createElement("canvas"); c.width = c.height = 64; const x = c.getContext("2d");
  const g = x.createRadialGradient(32, 32, 0, 32, 32, 32);
  g.addColorStop(0, "rgba(255,255,255,1)"); g.addColorStop(0.18, `rgba(${rgb},1)`); g.addColorStop(0.45, `rgba(${rgb},.35)`); g.addColorStop(1, `rgba(${rgb},0)`);
  x.fillStyle = g; x.fillRect(0, 0, 64, 64); return c;
};
const SPR = { cane: sprite(COL.cane), gatto: sprite(COL.gatto), altro: sprite(COL.altro), sogno: sprite(COL.sogno), stella: sprite(COL.stella) };

let DATA = [], VISIBLE = [], recentCount = 0;
const DOM_ZOOM = 11.5; // da qui in su compaiono i disegni

function drawGlow(t = performance.now()) {
  const s = map.getSize(), dpr = Math.min(devicePixelRatio || 1, 2);
  if (glow.width !== s.x * dpr) { glow.width = s.x * dpr; glow.height = s.y * dpr; glow.style.width = s.x + "px"; glow.style.height = s.y + "px"; }
  gx.setTransform(dpr, 0, 0, dpr, 0, 0); gx.clearRect(0, 0, s.x, s.y); gx.globalCompositeOperation = "lighter";
  const z = map.getZoom(), base = Math.max(3.2, Math.min(26, 2.4 * Math.pow(1.36, z - 5))), near = z >= DOM_ZOOM;
  const far = Math.max(0.55, Math.min(0.95, 0.4 + (z - 5) * 0.11)); // da lontano luci più tenui, così non si impastano
  for (const d of DATA) {
    const p = map.latLngToContainerPoint(d.ll);
    if (p.x < -40 || p.y < -40 || p.x > s.x + 40 || p.y > s.y + 40) continue;
    let r = base * (d.k === "tifo" ? 0.6 : d.k === "stella" ? 0.6 : 1) * (1 + Math.min(0.7, d.pt / 250));
    if (d.recent) r *= 1 + 0.35 * Math.sin(t / 380 + d.seed);
    if (near && d.k !== "tifo") continue; // da vicino il disegno ha già il suo bagliore
    gx.globalAlpha = far;
    gx.drawImage(SPR[d.k === "tifo" ? d.t : d.k === "animale" ? d.t : d.k], p.x - r, p.y - r, r * 2, r * 2);
  }
  gx.globalAlpha = 1;
}
let raf = 0;
const loop = t => { drawGlow(t); raf = recentCount && !matchMedia("(prefers-reduced-motion: reduce)").matches ? requestAnimationFrame(loop) : 0; };
const redraw = () => { if (!raf) drawGlow(); };

// ---------- regioni ----------
let regLayer;
fetch("data/regioni.json").then(r => r.json()).then(REG => {
  L.geoJSON(REG, { style: () => ({ color: "#5577C9", weight: 7, opacity: 0.22, fill: false }), interactive: false }).addTo(map);
  regLayer = L.geoJSON(REG, { style: () => ({ color: "#34508F", weight: 1.1, fillColor: "#1E3266", fillOpacity: 1 }), interactive: false }).addTo(map);
  L.geoJSON(REG, { style: () => ({ color: "#5577C9", weight: 1.6, opacity: 0.75, fill: false }), interactive: false }).addTo(map);
});

// ---------- dati ----------
let INVITI = null; // la Sfida degli inviti: chi porta più amici a commentare
async function loadData() {
  if (ANTEPRIMA) return demo();
  try { const r = await fetch("data/animali.json?t=" + Math.floor(Date.now() / 60000)); if (r.ok) { const j = await r.json(); INVITI = j.inviti || null; return j.animali || []; } } catch (e) {}
  return [];
}

function prepare(list) {
  const now = Date.now(), firstByCity = new Map(), perCity = new Map();
  list.forEach(d => { const key = d.c + "|" + d.p; perCity.set(key, (perCity.get(key) || 0) + 1); });
  list.forEach((d, i) => {
    d.k = d.k || "animale"; d.t = d.t || "cane"; d.pt = d.pt || 0; d.id = d.id || d.u + "|" + d.n + "|" + i;
    d.seed = D.hash(d.id); d.rk = d.t === "altro" ? null : D.razza(d.razza_testo || d.razza, d.t); // il testo scritto vince: le razze nuove si disegnano anche per chi è già sulla mappa
    d.recent = d.ts && now - Date.parse(d.ts) < 3600e3;
    // sparso su un disco attorno al centro del comune, più largo dove ci sono più animali; sempre uguale per lo stesso animale
    const spread = Math.min(0.09, 0.006 + 0.0028 * Math.sqrt(perCity.get(d.c + "|" + d.p)));
    const a = (d.seed % 6283) / 1000, rad = 0.002 + Math.sqrt(((d.seed >>> 13) % 1000) / 1000) * spread;
    d.ll = L.latLng(d.lat + rad * Math.sin(a) + (d.k === "stella" ? 0.03 : 0), d.lng + rad * Math.cos(a) * 1.35);
    if (d.k === "animale") { const key = d.c + "|" + d.p; const f = firstByCity.get(key); if (!f || (d.ts || "") < (f.ts || "")) firstByCity.set(key, d); }
  });
  firstByCity.forEach(d => { d.fondatore = true; });
  recentCount = list.filter(d => d.recent).length;
  return list;
}

// ---------- disegni da vicino ----------
const petLayer = L.layerGroup().addTo(map), cityLabels = L.layerGroup().addTo(map);
let petMarkers = new Map();
function petIcon(d) {
  const svg = d.k === "stella" ? D.stella() : d.k === "sogno" ? D.sogno(d.rk, d.seed) : d.t === "altro" ? D.altro(d.specie, d.seed) : d.t === "gatto" ? D.gatto(d.rk, d.seed) : D.cane(d.rk, d.seed);
  const cls = d.k === "animale" ? d.t : d.k;
  return L.divIcon({ className: "", iconSize: [0, 0], html: `<div class="pet ${cls}" data-id="${esc(d.id)}">${svg}<span class="name">${d.k === "stella" ? "✦ " : ""}${esc(d.n)}</span></div>` });
}
const icona = d => d.t === "altro" ? D.emoji(d.specie) : d.t === "gatto" ? "🐱" : "🐶";
function popup(d) {
  const ruolo = d.ruolo || (d.fondatore ? "Fondatore di " + d.c : "");
  const tipo = d.k === "stella" ? "Una stella nel cielo" : d.k === "sogno" ? "Il sogno di @" + esc(d.u) : d.t === "altro" ? esc((d.razza_testo || d.specie || "Amico speciale").replace(/^./, c => c.toUpperCase())) : d.t === "gatto" ? (D.GATTI[d.rk]?.n || "Gatto") : (d.rk === "meticcio" && d.razza_testo && !/meticc|incrocio|mix/i.test(d.razza_testo) ? esc(d.razza_testo.replace(/^./, c => c.toUpperCase())) : D.CANI[d.rk]?.n || "Cane");
  return `<div class="pop"><h3>${d.k === "stella" ? "✦" : icona(d)} ${esc(d.n)}</h3><div class="k">${tipo}</div>
    <div>${esc(d.c)} (${esc(d.p)}) · ${esc(d.r)}</div>
    ${d.k === "stella" ? "" : `<div>${d.pt} ${d.pt === 1 ? "punto" : "punti"}${d.rank ? ` · ${d.rank}° in Italia` : ""}</div>`}
    ${ruolo ? `<span class="role">👑 ${esc(ruolo)}</span>` : ""}
    ${d.u ? `<div style="margin-top:6px"><a href="https://www.instagram.com/${encodeURIComponent(d.u)}/" target="_blank" rel="noopener">@${esc(d.u)} ↗</a></div>` : ""}</div>`;
}
function syncPets() {
  const z = map.getZoom();
  if (z < DOM_ZOOM) { petLayer.clearLayers(); petMarkers.clear(); return; }
  const b = map.getBounds().pad(0.15), want = new Set();
  for (const d of DATA) { if (d.k === "tifo" || !b.contains(d.ll)) continue; want.add(d.id); if (want.size > 500) break; }
  for (const [id, m] of petMarkers) if (!want.has(id)) { petLayer.removeLayer(m); petMarkers.delete(id); }
  for (const d of DATA) if (want.has(d.id) && !petMarkers.has(d.id)) {
    const m = L.marker(d.ll, { icon: petIcon(d), riseOnHover: true }).bindPopup(() => popup(d), { offset: [0, -70], autoPanPaddingTopLeft: L.point(20, 200), autoPanPaddingBottomRight: L.point(20, 190) });
    petMarkers.set(d.id, m); petLayer.addLayer(m); d.marker = m;
  }
}
function syncCities(cities) {
  cityLabels.clearLayers();
  const z = map.getZoom(), n = z < 6.5 ? 6 : z < 8 ? 14 : z < DOM_ZOOM ? 40 : 0;
  cities.slice(0, n).forEach(c => cityLabels.addLayer(L.marker([c.lat, c.lng], { interactive: false,
    icon: L.divIcon({ className: "", iconSize: [0, 0], html: `<div class="city">${esc(c.c)} · ${fmt(c.tot)}</div>` }) })));
}

// ---------- statistiche ----------
let STATS = {};
function stats() {
  const cities = new Map(); let cani = 0, gatti = 0, altri = 0, luci = 0;
  for (const d of DATA) {
    if (d.k === "stella") continue;
    luci++;
    const key = d.c + "|" + d.p; let c = cities.get(key);
    if (!c) cities.set(key, c = { c: d.c, p: d.p, r: d.r, lat: d.lat, lng: d.lng, cani: 0, gatti: 0, tot: 0 });
    c.tot++;
    if (d.t === "altro") { altri++; continue; } // gli altri animali accendono la città ma non entrano nella sfida Cani contro Gatti
    const team = d.t === "gatto" ? "gatti" : "cani"; c[team]++; team === "cani" ? cani++ : gatti++;
  }
  const city = [...cities.values()].sort((a, b) => b.tot - a.tot || a.c.localeCompare(b.c));
  const rank = DATA.filter(d => d.k === "animale" || d.k === "sogno").sort((a, b) => b.pt - a.pt || (a.ts || "").localeCompare(b.ts || ""));
  rank.forEach((d, i) => d.rank = i + 1);
  return STATS = { city, rank, cani, gatti, altri, luci };
}
function renderHeader() {
  const { cani, gatti, luci } = STATS, tot = cani + gatti, pc = tot ? (cani / tot) * 100 : 50;
  $("#versus").innerHTML = `<span class="side dog">🐶 <b>${fmt(cani)}</b> Cani</span><span class="bar" role="img" aria-label="Cani ${fmt(cani)}, Gatti ${fmt(gatti)}"><i style="width:${pc}%"></i></span><span class="side cat">Gatti <b>${fmt(gatti)}</b> 🐱</span>`;
  const goal = luci < CONFIG.obiettivo ? CONFIG.obiettivo : Math.ceil((luci + 1) / 25000) * 25000;
  $("#counter").innerHTML = `<span><b>${fmt(luci)}</b> / ${fmt(goal)} luci</span><span class="track"><i style="width:${Math.min(100, (luci / goal) * 100)}%"></i></span>${recentCount ? `<span>✨ ${fmt(recentCount)} brillano ora</span>` : ""}`;
  if (ANTEPRIMA) { $("#badge").hidden = false; $("#badge").textContent = "Anteprima con dati inventati"; }
}

// ---------- pannelli ----------
function show(v) {
  document.querySelectorAll(".tab").forEach(t => t.setAttribute("aria-selected", t.dataset.v === v));
  const s = $("#sheet");
  if (v === "mappa") { s.hidden = true; return; }
  s.hidden = false;
  const empty = `<p class="empty">Ancora nessuna luce. Commenta il reel e accendi la prima!</p>`;
  if (v === "sfida") {
    s.innerHTML = `<h2>Cani contro Gatti</h2><p class="sub">Quale città d'Italia vince? Conta ogni animale e ogni tifo.</p>` + (STATS.city.length ? `<ol class="list">` +
      STATS.city.slice(0, 40).map((c, i) => `<li class="row" data-i="${i}"><span class="pos">${i + 1}</span><span class="who">${esc(c.c)}<small>${esc(c.r)}</small>
        <span class="split"><i style="width:${(c.cani / c.tot) * 100}%"></i></span></span><span class="vs"><span class="d">${fmt(c.cani)}</span> – <span class="c">${fmt(c.gatti)}</span></span></li>`).join("") + `</ol>` : empty);
    s.querySelectorAll(".row").forEach(r => r.onclick = () => { const c = STATS.city[r.dataset.i]; show("mappa"); map.flyTo([c.lat, c.lng], 13, { duration: 0.9 }); });
  }
  if (v === "classifica") {
    const oggi = (INVITI && INVITI.oggi) || [];
    const sfida = `<div class="sfida-inviti"><h3>👥 Sfida degli inviti di oggi</h3><p class="sub">Tagga gli amici nei commenti: ogni amico che commenta vale +3. Chi ne porta di più è il <b>Re degli inviti</b> 👑 e finisce nella puntata delle 21.</p>` +
      (oggi.length ? `<ol class="list">` + oggi.slice(0, 5).map(([u, n], i) => `<li class="row"><span class="pos">${i === 0 ? "👑" : i + 1}</span><span class="who">@${esc(u)}</span><span class="pts">${n}<small>${n === 1 ? "amico" : "amici"}</small></span></li>`).join("") + `</ol>`
        : `<p class="empty">Nessun invito ancora oggi: il primo amico che porti ti mette in testa!</p>`) + `</div>`;
    s.innerHTML = `<h2>Classifica</h2><p class="sub">Più punti fai, più la tua luce cresce: cuccia, lucine, giardino, villa, castello.</p>` + sfida + (STATS.rank.length ? `<ol class="list">` +
      STATS.rank.slice(0, 50).map(d => `<li class="row" data-id="${esc(d.id)}"><span class="pos">${d.rank}</span><span class="who">${icona(d)} ${esc(d.n)} · @${esc(d.u)}<small>${esc(d.c)} · ${esc(d.r)}</small></span><span class="pts">${fmt(d.pt)}<small>pt</small></span></li>`).join("") + `</ol>` : empty);
    s.querySelectorAll(".row").forEach(r => r.onclick = () => { show("mappa"); focus(DATA.find(d => d.id === r.dataset.id)); });
  }
  if (v === "regole") {
    s.innerHTML = `<h2>Come si gioca</h2><p class="sub">Si gioca nei commenti dei reel di @zampeditalia. Entro 15 minuti la luce si accende.</p><ul class="rules">
      <li><b>🐶🐱 Il tuo animale · +10</b>Scrivi città, nome e razza: <code>Treviso, Luna, golden</code> oppure <code>Milano, Micio, gatto rosso</code>. Il primo del comune diventa Fondatore (+20).</li>
      <li><b>🐰🦎🐢 Tutti gli animali</b>Conigli, furetti, gechi, tartarughe, pappagalli…: <code>Padova, Ugo, furetto</code>. Accendono la città con una luce azzurra. Quando arrivano a 15 luci entrano nella sfida: Cani contro Gatti contro Altri animali!</li>
      <li><b>➕ Seguici · +10</b>Segui @zampeditalia e scrivi <code>SEGUO</code> in un commento. Nei reel mettiamo prima gli animali di chi ci segue.</li>
      <li><b>📣 Fai il tifo · +5</b>Non hai animali? Scegli la squadra: <code>Tifo cani: Treviso</code> oppure <code>Tifo gatti: Milano</code>.</li>
      <li><b>☁️ Il tuo sogno · +10</b>L'animale che vorresti: <code>Sogno: Padova, Bruno, bassotto</code>.</li>
      <li><b>✦ Una stella</b>Per chi non c'è più: <code>Stella: Treviso, Max</code>. Una stella nel cielo col suo nome, mai in classifica.</li>
      <li><b>👑 I ruoli</b>Fondatore (primo del comune), Sindaco a 4 zampe (primo della città), Capobranco (primo della regione), Cane d'Italia e Gatto d'Italia, proclamati la domenica alle 21.</li>
      <li><b>🙋 Punti ogni giorno</b>+5 per un commento su un reel nuovo, +3 per ogni amico taggato che poi commenta. Chi porta più amici in un giorno è il Re degli inviti 👑</li>
      <li><b>Privacy</b>Sulla mappa ci sono solo il tuo @ pubblico, la città e quello che hai scritto. Per sparire, commenta <code>RIMUOVI</code>.</li></ul>`;
  }
}
document.querySelectorAll(".tab").forEach(t => t.onclick = () => show(t.dataset.v));

// ---------- ricerca ----------
let COMUNI = null;
function focus(d) {
  if (!d) return;
  map.flyTo(d.ll, 14.5, { duration: 1 });
  map.once("moveend", () => { syncPets(); const m = petMarkers.get(d.id); if (m) { m.openPopup(); const el = m.getElement()?.querySelector(".pet"); el?.classList.add("hit"); } });
}
$("#searchForm").addEventListener("submit", async e => {
  e.preventDefault();
  const q = $("#q").value.trim().replace(/^@/, "").toLowerCase(); if (!q) return;
  show("mappa");
  const u = DATA.find(d => d.u?.toLowerCase() === q) || DATA.find(d => d.n?.toLowerCase() === q);
  if (u) return focus(u);
  const c = STATS.city.find(c => c.c.toLowerCase() === q);
  if (c) return map.flyTo([c.lat, c.lng], 13, { duration: 0.9 });
  COMUNI ||= await fetch("data/comuni.json").then(r => r.json()).catch(() => []);
  const k = COMUNI.find(x => x[0].toLowerCase() === q) || COMUNI.find(x => x[0].toLowerCase().startsWith(q));
  if (k) return map.flyTo([k[3], k[4]], 12.5, { duration: 0.9 });
  const p = DATA.find(d => d.u?.toLowerCase().includes(q) || d.n?.toLowerCase().includes(q));
  if (p) return focus(p);
  $("#q").value = ""; $("#q").placeholder = "Nessuna luce trovata: commenta il reel!";
});
$("#zin").onclick = () => map.zoomIn(); $("#zout").onclick = () => map.zoomOut();
$("#zall").onclick = () => map.flyToBounds(ITALY, { ...PAD(), duration: 0.8 });

// ---------- avvio ----------
function refresh(list) {
  DATA = prepare(list); stats(); renderHeader(); syncCities(STATS.city); syncPets();
  if (!raf && recentCount) raf = requestAnimationFrame(loop); else redraw();
  if (!$("#sheet").hidden) show(document.querySelector('.tab[aria-selected="true"]').dataset.v);
}
map.on("move zoom resize", redraw);
map.on("moveend zoomend", () => { syncPets(); syncCities(STATS.city || []); });
$("#igLink").href = CONFIG.ig;
// prima l'elenco completo delle razze, poi gli animali
fetch("data/razze.json").then(r => r.json()).then(D.carica).catch(() => {}).finally(() => loadData().then(refresh));
// Il motore dei commenti aggiorna i dati ogni 10-15 minuti: la pagina li ricarica da sola.
if (!ANTEPRIMA) setInterval(() => loadData().then(refresh), 5 * 60e3);

// ---------- anteprima (solo con ?anteprima nell'indirizzo, mai sul sito vero) ----------
async function demo() {
  const C = await fetch("data/comuni.json").then(r => r.json());
  const big = ["Roma", "Milano", "Napoli", "Torino", "Palermo", "Bologna", "Firenze", "Bari", "Venezia", "Verona", "Treviso", "Padova", "Genova", "Catania", "Cagliari"];
  const pick = big.map(n => C.find(x => x[0] === n)).filter(Boolean);
  const NOMI = ["Luna", "Thor", "Milo", "Kira", "Rocky", "Nala", "Leo", "Maya", "Bruno", "Zoe", "Oliver", "Micio", "Birba", "Pallina", "Romeo", "Gigio", "Stella", "Briciola"];
  const rc = Object.keys(D.CANI), rg = Object.keys(D.GATTI);
  let s = 7; const R = () => (s = (s * 16807) % 2147483647) / 2147483647;
  const out = [];
  for (let i = 0; i < 3200; i++) {
    const k = R() < 0.55 ? pick[Math.floor(Math.pow(R(), 1.6) * pick.length)] : C[Math.floor(R() * C.length)];
    const gatto = R() < 0.44, kind = R() < 0.82 ? "animale" : R() < 0.5 ? "tifo" : R() < 0.6 ? "sogno" : "stella";
    out.push({ u: "utente" + i, n: NOMI[Math.floor(R() * NOMI.length)], t: gatto ? "gatto" : "cane", k: kind,
      razza: gatto ? rg[Math.floor(R() * rg.length)] : rc[Math.floor(R() * rc.length)],
      c: k[0], p: k[1], r: k[2], lat: k[3], lng: k[4], pt: Math.floor(Math.pow(R(), 3) * 200),
      ts: new Date(Date.now() - R() * 86400e3 * (R() < 0.05 ? 0.03 : 3)).toISOString() });
  }
  out.push({ u: "thorgoldenlife", n: "Thor", t: "cane", k: "animale", razza: "golden", c: "Altivole", p: "TV", r: "Veneto", lat: 45.754, lng: 11.9558, pt: 250, ts: new Date(Date.now() - 86400e3 * 4).toISOString() });
  return out;
}
