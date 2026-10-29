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
const DOM_ZOOM = 12.5; // da qui in su compaiono i paesi disegnati

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
    if (near && d.k !== "tifo" && d.villa?.mostra) continue; // da vicino il paese disegnato ha già il suo bagliore
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
let PRENOTATE = {}; // posti prenotati dalle attività, per comune: {"Treviso|TV": {"veterinario": 1}}
let INVITI = null; // la Sfida degli inviti: chi porta più amici a commentare
let DERBY = null; // il Derby della settimana: {ora: {a, b, na, nb, fine, partito}, albo: [...]} (motore/derby.py)
let NEGOZIO = {}, SFILATA = [], BELLO = null; // la Sfilata degli accessori e «Il più bello d'Italia» della settimana (motore/commenti.py)
let _x = 0; // i link di pagamento degli accessori (motore/config.json → animali.json): {collare: "https://buy.stripe.com/…"}
let FOLLOW = null; // il traguardo di tutti: {n: follower veri, traguardo: 1000}; raggiunto, nevica sulla mappa
async function loadData() {
  if (ANTEPRIMA) return demo();
  try { const r = await fetch("data/animali.json?t=" + Math.floor(Date.now() / 60000)); if (r.ok) { const j = await r.json(); INVITI = j.inviti || null; PRENOTATE = j.prenotate || {}; FOLLOW = j.follower || null; NEGOZIO = j.negozio || {}; SFILATA = j.sfilata || []; BELLO = j.piu_bello || null; DERBY = j.derby || null; return j.animali || []; } } catch (e) {}
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
// da vicino ogni comune è un paese disegnato (paese.js): il terreno sta sotto le cucce, le cucce in cerchio attorno alla piazza
map.createPane("paesi").style.zIndex = 450;
const paeseLayer = L.layerGroup().addTo(map), paeseMarkers = new Map();
let VILLE = new Map();
const scala = z => Math.max(0.45, Math.min(1.25, Math.pow(2, (z - 14) * 0.6)));
function ville() {
  VILLE = new Map();
  for (const d of DATA) {
    if (d.k === "tifo") continue;
    const key = d.c + "|" + d.p; let v = VILLE.get(key);
    if (!v) VILLE.set(key, v = { key, nome: d.c, ll: L.latLng(d.lat, d.lng), lista: [], stelle: [] });
    (d.k === "stella" ? v.stelle : v.lista).push(d);
  }
  const ord = d => (d.capo ? 0 : d.fondatore ? 1 : d.vestito ? 2 : 3); // chi ci segue sta in prima fila, vicino alla piazza
  for (const v of VILLE.values()) {
    v.lista.sort((a, b) => ord(a) - ord(b) || b.pt - a.pt || (a.ts || "").localeCompare(b.ts || ""));
    const P = Paese.posti(v.lista.length), fondo = P.raggio * Paese.SQ; v.R = P.raggio + 110;
    v.lista.forEach((d, i) => { d.off = P.posti[i]; d.prof = 0.86 + 0.14 * (d.off[1] / fondo + 1) / 2; d.villa = v; });
    v.stelle.forEach(d => { d.off = [(d.seed % 240) - 120, -Math.round(fondo + 70 + (d.seed >>> 9) % 40)]; d.prof = 0.8; d.villa = v; });
    v.luci = STATS.city.find(c => c.c === v.nome && c.p === v.key.split("|")[1])?.tot || v.lista.length;
    v.html = null;
  }
}
function paeseIcon(v) {
  if (!v.html) {
    const g = Paese.suolo(v.nome, v.luci, v.lista.length, D.hash(v.key)), ox = g.w / 2, oy = g.h / 2 + g.dy;
    v.html = `<div class="paese" style="width:${g.w}px;height:${g.h}px;transform-origin:${ox}px ${oy}px;transform:translate(${-ox}px,${-oy}px) scale(var(--s,1))">${g.svg}</div>`;
  }
  return L.divIcon({ className: "", iconSize: [0, 0], html: v.html });
}
const posto = (d, z, s) => d.villa ? map.unproject(map.project(d.villa.ll, z).add([d.off[0] * s, d.off[1] * s]), z) : d.ll;
function petSvg(d) {
  let svg = d.k === "stella" ? D.stella() : d.k === "sogno" ? D.sogno(d.rk, d.seed) : d.t === "altro" ? D.altro(d.specie, d.seed) : d.t === "gatto" ? D.gatto(d.rk, d.seed) : D.cane(d.rk, d.seed);
  if (d.acc && d.k !== "stella") svg = D.accessori(svg, d.acc, d.k === "sogno" ? "sogno" : d.t, d.seed); // prima del costume: il costume si prende il segnaposto della testa
  if (d.vestito && d.k !== "stella") svg = D.vesti(svg, d.vestito, d.k === "sogno" ? "sogno" : d.t, d.seed);
  return svg;
}
function petIcon(d) {
  const svg = petSvg(d), cls = d.k === "animale" ? d.t : d.k;
  return L.divIcon({ className: "", iconSize: [0, 0], html: `<div class="pet ${cls}${d.recent ? " nuovo" : ""}" data-id="${esc(d.id)}" style="--k:${(d.prof || 1).toFixed(3)};--r:${((d.seed % 90) / 10).toFixed(1)}s">${svg}<span class="name">${d.k === "stella" ? "✦ " : ""}${d.k !== "stella" && livello(d.pt) ? livello(d.pt)[1] + " " : ""}${esc(d.n)}</span></div>` });
}
const EDIFICI = [[5, "Fontanella", "⛲"], [10, "Parco cani", "🌳"], [25, "Gattile", "🏠"], [50, "Clinica veterinaria", "🏥"], [100, "Piazza dei Fondatori", "🏛️"], [250, "Grande parco", "🎡"]]; // come in motore/commenti.py
const LIVELLI = [[30, "🌸", "Giardino"], [50, "🏡", "Villa"], [70, "🏰", "Castello"]]; // come in motore/copione.py: più punti, più la cuccia cresce
const livello = pt => [...LIVELLI].reverse().find(l => pt >= l[0]);
// come in un videogioco: il livello della cuccia e la barra verso il prossimo
const barra = pt => { const i = LIVELLI.findIndex(l => pt < l[0]), da = i > 0 ? LIVELLI[i - 1][0] : i < 0 ? LIVELLI.at(-1)[0] : 0, a = i < 0 ? null : LIVELLI[i];
  const ora = livello(pt) || [0, "🏠", "Cuccia"];
  return `<div class="liv">Livello ${LIVELLI.indexOf(livello(pt)) + 2} · ${ora[1]} ${ora[2]}${a ? ` → ${a[1]} a ${a[0]} punti` : " · livello massimo!"}</div>` +
    `<div class="xp"><i style="width:${a ? Math.round(((pt - da) / (a[0] - da)) * 100) : 100}%"></i></div>`; };
const prossimoLiv = pt => { const l = LIVELLI.find(l => pt < l[0]); return l ? ` · mancano ${l[0] - pt} punti per ${l[1]} ${l[2].toLowerCase()}` : ""; };
const ARTICOLI = [["osso", "Osso d'oro", "1 €", "Brilla accanto alla sua cuccia"], ["fiocco", "Fiocco", "1,49 €", "Rosa, sulla testa: il più tenero del paese"], ["collare", "Collare d'oro", "1,99 €", "Con la medaglietta che brilla"], ["corona", "Corona", "2,99 €", "Il re o la regina del paese"],
  ["fuochi", "Fuochi d'artificio", "3,99 €", "Esplodono sopra la sua cuccia, giorno e notte"]]; // come in motore/negozio.py
const codice = id => "z" + D.hash(id).toString(36); // come in motore/negozio.py: lega il pagamento all'animale senza dati personali
const ICONE = { osso: "🦴", fiocco: "🎀", collare: "📿", corona: "👑", fuochi: "🎆" };
let SCELTO = null; // il tuo animale, ricordato su questo telefono
function sfilata(scelto) {
  const righe = SFILATA.map(([id, n]) => DATA.find(d => d.id === id)).filter(Boolean).slice(0, 5);
  const pos = scelto ? SFILATA.findIndex(([id]) => id === scelto.id) : -1;
  const vinto = BELLO && DATA.find(d => d.id === BELLO.id);
  return `<div class="sfilata"><h3>🏆 La Sfilata: il più bello d'Italia</h3>
    <p class="sub">Vince chi ha più accessori. Ogni domenica alle 21 il primo diventa <b>Il più bello d'Italia</b>: piedistallo d'oro nel suo paese 3D e protagonista della puntata delle 21.</p>
    ${vinto ? `<p class="per">🏆 Questa settimana: <b>${icona(vinto)} ${esc(vinto.n)}</b> · ${esc(vinto.c)}</p>` : ""}
    ${righe.length ? `<ol class="list">` + righe.map((d, i) => `<li class="row"><span class="pos">${i === 0 ? "🏆" : i + 1}</span><span class="who">${icona(d)} ${esc(d.n)} · @${esc(d.u)}<small>${esc(d.c)}</small></span><span class="pts">${(d.acc || []).map(k => ICONE[k]).join("")}</span></li>`).join("") + `</ol>`
      : `<p class="empty">Nessuno ha ancora un accessorio: il primo che lo regala al suo animale è in testa alla Sfilata!</p>`}
    ${scelto ? `<p class="per">${pos >= 0 ? `${esc(scelto.n)} è ${pos + 1}° nella Sfilata${pos ? `: ${pos === 1 ? "un accessorio" : "qualche accessorio"} e passa avanti!` : " 🏆"}` : `${esc(scelto.n)} non è ancora nella Sfilata: basta 1 € per entrare.`}</p>` : ""}</div>`;
}
function hud(d) {
  const oggi = new Date() < new Date("2026-11-02");
  return `<div class="hud"><span class="ritratto">${petSvg(d)}</span><span class="dati"><b>${esc(d.n)}</b> · ${esc(d.c)}<br>
    <small>${fmt(d.pt)} punti${d.rank ? ` · ${d.rank}° in Italia` : ""}${d.fondatore ? " · 👑 Fondatore" : ""}</small>${barra(d.pt)}
    <button type="button" class="link" id="cambia">non è il tuo?</button></span></div>
    <button type="button" class="btn entra-qui" data-id="${esc(d.id)}" style="width:100%">🎮 Vai da ${esc(d.n)} nel paese in 3D</button>
    <h3>🎯 Missioni di oggi</h3><ul class="missioni">
    <li>💬 Commenta il reel di oggi<b>+5</b></li><li>👥 Tagga un amico che poi commenta<b>+3 ognuno</b></li>
    <li>➕ Seguici e scrivi SEGUO<b>${oggi ? "+30" : "+10"}</b></li><li>🏆 Regala un accessorio: sali nella Sfilata del più bello<b>da 1 €</b></li>${DERBY?.ora?.partito && !DERBY.ora.finito ? `<li>⚔️ Derby ${esc(DERBY.ora.a)}–${esc(DERBY.ora.b)}: accendi la tua provincia<b>+20</b></li>` : ""}</ul>`;
}
const edifici = n => EDIFICI.filter(e => n >= e[0]).map(e => e[2]).join("");
const prossimo = n => { const e = EDIFICI.find(e => n < e[0]); return e ? `mancano ${e[0] - n} ${e[0] - n === 1 ? "luce" : "luci"} per ${e[2]} ${e[1].toLowerCase()}` : ""; };
const POSTI = { veterinario: "🏥 clinica", toelettatura: "✂️ toelettatura", negozio: "🛍️ negozio", pensione: "🏡 pensione", educatore: "🎾 addestramento", altro: "🏪 bottega" };
const prenotati = c => Object.keys(PRENOTATE[c.c + "|" + c.p] || {}).map(t => POSTI[t] || POSTI.altro).join(", ");
const icona = d => d.t === "altro" ? D.emoji(d.specie) : d.t === "gatto" ? "🐱" : "🐶";
function popup(d) {
  const ruolo = d.ruolo || (d.fondatore ? "Fondatore di " + d.c : "");
  const tipo = d.k === "stella" ? "Una stella nel cielo" : d.k === "sogno" ? "Il sogno di @" + esc(d.u) : d.t === "altro" ? esc((d.razza_testo || d.specie || "Amico speciale").replace(/^./, c => c.toUpperCase())) : d.t === "gatto" ? (D.GATTI[d.rk]?.n || "Gatto") : (d.rk === "meticcio" && d.razza_testo && !/meticc|incrocio|mix/i.test(d.razza_testo) ? esc(d.razza_testo.replace(/^./, c => c.toUpperCase())) : D.CANI[d.rk]?.n || "Cane");
  return `<div class="pop"><h3>${d.k === "stella" ? "✦" : icona(d)} ${esc(d.n)}</h3><div class="k">${tipo}</div>
    <div>${esc(d.c)} (${esc(d.p)}) · ${esc(d.r)}</div>
    ${d.k === "stella" ? "" : `<div>${d.pt} ${d.pt === 1 ? "punto" : "punti"}${d.rank ? ` · ${d.rank}° in Italia` : ""}</div>${barra(d.pt)}`}
    ${d.capo ? `<span class="role">🐺 ${esc(d.capo)}</span>` : d.testa ? `<span class="role">🐺 In testa a ${esc(d.c)}: domenica alle 21 il Capobranco</span>` : ""}
    ${BELLO?.id === d.id ? `<span class="role">🏆 Il più bello d'Italia</span>` : ""}
    ${ruolo ? `<span class="role">👑 ${esc(ruolo)}</span>` : ""}
    ${d.k === "stella" ? "" : `<button type="button" class="regala" data-id="${esc(d.id)}">🛍️ ${d.acc?.length ? "Altri accessori" : "Regalagli un accessorio"}</button>`}
    ${d.villa && !document.querySelector(".mondo3d") ? `<button type="button" class="entra-qui" data-id="${esc(d.id)}">🎮 Entra nel suo paese in 3D</button>` : ""}
    ${d.u ? `<div style="margin-top:6px"><a href="https://www.instagram.com/${encodeURIComponent(d.u)}/" target="_blank" rel="noopener">@${esc(d.u)} ↗</a></div>` : ""}</div>`;
}
function syncPets() {
  const z = map.getZoom();
  $("#entra3d").hidden = z < DOM_ZOOM;
  if (z < DOM_ZOOM) { petLayer.clearLayers(); petMarkers.clear(); paeseLayer.clearLayers(); paeseMarkers.clear(); return; }
  const s = scala(z); map.getContainer().style.setProperty("--s", s);
  const b = map.getBounds().pad(0.15), vb = map.getBounds().pad(0.8), want = new Set(), ville = new Set();
  // due paesi che si toccano: si disegna il più grande, l'altro resta una luce finché non si ingrandisce
  const messi = [];
  for (const v of [...VILLE.values()].sort((a, b) => b.lista.length - a.lista.length)) {
    v.mostra = false; if (!vb.contains(v.ll)) continue;
    const p = map.project(v.ll, z);
    if (messi.some(([q, R]) => Math.hypot((p.x - q.x) / (R + v.R), (p.y - q.y) / ((R + v.R) * Paese.SQ)) < s * 0.95)) continue;
    messi.push([p, v.R]); v.mostra = true; ville.add(v.key);
  }
  for (const [k, m] of paeseMarkers) if (!ville.has(k) || m._luci !== VILLE.get(k).luci) { paeseLayer.removeLayer(m); paeseMarkers.delete(k); }
  for (const k of ville) if (!paeseMarkers.has(k)) {
    const v = VILLE.get(k), m = L.marker(v.ll, { icon: paeseIcon(v), pane: "paesi", interactive: false, keyboard: false });
    m._luci = v.luci; paeseMarkers.set(k, m); paeseLayer.addLayer(m);
  }
  for (const d of DATA) { if (d.k === "tifo" || !d.villa?.mostra) continue; d.qui = posto(d, z, s); if (!b.contains(d.qui)) continue; want.add(d.id); if (want.size > 500) break; }
  for (const [id, m] of petMarkers) if (!want.has(id)) { petLayer.removeLayer(m); petMarkers.delete(id); } else m.setLatLng(m._d.qui);
  for (const d of DATA) if (want.has(d.id) && !petMarkers.has(d.id)) {
    const m = L.marker(d.qui, { icon: petIcon(d), riseOnHover: true }).bindPopup(() => popup(d), { offset: [0, -70], autoPanPaddingTopLeft: L.point(20, 200), autoPanPaddingBottomRight: L.point(20, 190) });
    m._d = d; petMarkers.set(d.id, m); petLayer.addLayer(m); d.marker = m;
  }
}
function syncCities(cities) {
  cityLabels.clearLayers();
  const z = map.getZoom(), n = z < 6.5 ? 6 : z < 8 ? 14 : 40;
  (z < DOM_ZOOM ? cities : cities.filter(c => !VILLE.get(c.c + "|" + c.p)?.mostra)).slice(0, n).forEach(c => cityLabels.addLayer(L.marker([c.lat, c.lng], { interactive: false,
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
  const capi = new Map(), inGara = new Map(); // corsa a Capobranco: il primo per punti di ogni comune con almeno 3 luci
  for (const d of rank) { const key = d.c + "|" + d.p; inGara.set(key, (inGara.get(key) || 0) + 1); if (!capi.has(key)) capi.set(key, d); d.testa = false; }
  capi.forEach((d, key) => { d.testa = inGara.get(key) >= 3; });
  return STATS = { city, rank, cani, gatti, altri, luci };
}
function renderHeader() {
  const { cani, gatti, luci } = STATS, tot = cani + gatti, pc = tot ? (cani / tot) * 100 : 50;
  $("#versus").innerHTML = `<span class="side dog">🐶 <b>${fmt(cani)}</b> Cani</span><span class="bar" role="img" aria-label="Cani ${fmt(cani)}, Gatti ${fmt(gatti)}"><i style="width:${pc}%"></i></span><span class="side cat">Gatti <b>${fmt(gatti)}</b> 🐱</span>`;
  const goal = luci < CONFIG.obiettivo ? CONFIG.obiettivo : Math.ceil((luci + 1) / 25000) * 25000;
  // accanto alle luci un messaggio alla volta, a rotazione: su telefono non c'è posto per tutti
  const segui = `href="${CONFIG.ig}" target="_blank" rel="noopener" class="traguardo"`, oggi = new Date();
  const DO = DERBY && DERBY.ora, U = DERBY && DERBY.albo && DERBY.albo[DERBY.albo.length - 1];
  const msg = [
    U && U.vince && oggi - new Date(U.fine) < 864e5 && `🏆 ${U.vince} ha vinto il derby`,
    DO && (DO.partito ? `⚔️ Derby ${DO.a} <b>${fmt(DO.na)}</b> – <b>${fmt(DO.nb)}</b> ${DO.b}` : `⚔️ Stasera il derby ${DO.a}–${DO.b}`),
    FOLLOW && (FOLLOW.n >= FOLLOW.traguardo ? `❄️ ${fmt(FOLLOW.n)} follower: nevica sulla mappa!` : `<a ${segui} title="A ${fmt(FOLLOW.traguardo)} follower nevica su tutta la mappa">❄️ Mancano ${fmt(FOLLOW.traguardo - FOLLOW.n)} follower alla neve</a>`),
    oggi < new Date("2026-11-02") && `<a ${segui}>🔥 SEGUO vale +30 fino a dom.</a>`,
    oggi < new Date("2026-11-03") ? "🎃 Chi ci segue ha il costume" : "✨ Chi ci segue ha le lucine e la prima fila",
    recentCount && `✨ ${fmt(recentCount)} brillano ora`,
  ].filter(Boolean);
  $("#counter").innerHTML = `<span><b>${fmt(luci)}</b> / ${fmt(goal)} luci</span><span class="track"><i style="width:${Math.min(100, (luci / goal) * 100)}%"></i></span><span class="msg">${msg[0] || ""}</span>`;
  clearInterval(renderHeader.giro); let k = 0;
  if (msg.length > 1) renderHeader.giro = setInterval(() => { const el = $("#counter .msg"); if (el) { k = (k + 1) % msg.length; el.innerHTML = msg[k]; el.classList.remove("entra"); void el.offsetWidth; el.classList.add("entra"); } }, 4500);
  document.body.classList.toggle("neve", !!FOLLOW && FOLLOW.n >= FOLLOW.traguardo);
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
      STATS.city.slice(0, 40).map((c, i) => `<li class="row" data-i="${i}"><span class="pos">${i + 1}</span><span class="who">${esc(c.c)} <span class="edifici">${edifici(c.tot)}</span><small>${esc(c.r)}${prossimo(c.tot) ? " · " + prossimo(c.tot) : ""}${prenotati(c) ? " · prenotati: " + prenotati(c) : ""}</small>
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
  if (v === "negozio") {
    const scelto = SCELTO && DATA.includes(SCELTO) ? SCELTO : null;
    const prova = scelto ? (k, t) => D.accessori(t === "gatto" ? D.gatto(scelto.rk, scelto.seed) : t === "altro" ? D.altro(scelto.specie, scelto.seed) : D.cane(scelto.rk, scelto.seed), [k], t, scelto.seed) : null;
    s.innerHTML = `<h2>🎮 Il tuo animale</h2><p class="sub">Fai punti, sali di livello, fai crescere la cuccia. E regalagli un accessorio: per sempre sulla mappa, lo vede tutta Italia.</p>
      <form class="cerca-mio" id="cercaMio"><input id="mio" type="search" placeholder="Il tuo @ o il nome del tuo animale" autocomplete="off" value="${scelto ? esc("@" + scelto.u) : ""}"></form>
      <div id="miei">${scelto ? hud(scelto) : `<p class="empty">Cerca il tuo animale: vedi il suo livello, le missioni di oggi e i regali.</p>`}</div>
      ${scelto ? `<h3>🛍️ Regali per ${esc(scelto.n)}</h3>` : ""}
      <ul class="shop">${ARTICOLI.map(([k, nome, prezzo, testo]) => `<li class="art"><span class="anteprima">${prova ? prova(k, scelto.t) : `<span class="emo">${ICONE[k]}</span>`}</span>
        <span class="who"><b>${nome}</b><small>${testo}</small></span>
        ${scelto?.acc?.includes(k) ? `<span class="preso">✓ Ce l'ha</span>` : `<button type="button" class="btn compra" data-k="${k}" ${scelto && NEGOZIO[k] ? "" : "disabled"}>${prezzo}</button>`}</li>`).join("")}</ul>
      ${sfilata(scelto)}
      <p class="sub piccolo">${Object.keys(NEGOZIO).length ? "Pagamento sicuro con Stripe. L'accessorio compare sulla mappa entro 15 minuti, e il tuo regalo finisce nella storia di @zampeditalia 🎉" : "Il negozio apre a breve: gli accessori arrivano nei prossimi giorni."} Nessun abbonamento, si paga una volta sola.</p>`;
    const cerca = $("#mio"), lista = $("#miei");
    $("#cercaMio").onsubmit = e => e.preventDefault();
    cerca.oninput = () => { const q = cerca.value.trim().toLowerCase().replace(/^@/, ""); if (q.length < 2) return;
      const trovati = DATA.filter(d => d.k !== "stella" && d.k !== "tifo" && (d.u.toLowerCase().includes(q) || d.n.toLowerCase().includes(q))).slice(0, 6);
      lista.innerHTML = trovati.length ? `<ol class="list">` + trovati.map(d => `<li class="row" data-id="${esc(d.id)}"><span class="who">${icona(d)} ${esc(d.n)} · @${esc(d.u)}<small>${esc(d.c)}</small></span></li>`).join("") + `</ol>` : `<p class="empty">Non lo trovo: prima accendilo commentando un reel.</p>`;
      lista.querySelectorAll(".row").forEach(r => r.onclick = () => { SCELTO = DATA.find(d => d.id === r.dataset.id); try { localStorage.setItem("mio", SCELTO.id); } catch (e) {} show("negozio"); }); };
    if (scelto) { // sei salito di livello dall'ultima visita? festa
      let prima = null; try { prima = localStorage.getItem("liv:" + scelto.id); localStorage.setItem("liv:" + scelto.id, String(LIVELLI.indexOf(livello(scelto.pt)))); } catch (e) {}
      if (prima !== null && +prima < LIVELLI.indexOf(livello(scelto.pt))) { const f = document.createElement("div"); f.className = "levelup"; f.textContent = "LIVELLO SU! " + livello(scelto.pt)[1]; document.body.appendChild(f); setTimeout(() => f.remove(), 2500); }
    }
    if ($("#cambia")) $("#cambia").onclick = () => { SCELTO = null; try { localStorage.removeItem("mio"); } catch (e) {} show("negozio"); $("#mio").focus(); };
    s.querySelectorAll(".compra").forEach(b => b.onclick = () => { if (!scelto || !NEGOZIO[b.dataset.k]) return;
      location.href = NEGOZIO[b.dataset.k] + (NEGOZIO[b.dataset.k].includes("?") ? "&" : "?") + "client_reference_id=" + codice(scelto.id); });
  }
  if (v === "regole") {
    s.innerHTML = `<h2>Come si gioca</h2><p class="sub">Si gioca nei commenti dei reel di @zampeditalia. Entro 15 minuti la luce si accende.</p><ul class="rules">
      <li><b>🐶🐱 Il tuo animale · +10</b>Scrivi città, nome e razza: <code>Treviso, Luna, golden</code> oppure <code>Milano, Micio, gatto rosso</code>. Il primo del comune diventa Fondatore (+20).</li>
      <li><b>🐰🦎🐢 Tutti gli animali</b>Conigli, furetti, gechi, tartarughe, pappagalli…: <code>Padova, Ugo, furetto</code>. Accendono la città con una luce azzurra. Quando arrivano a 15 luci entrano nella sfida: Cani contro Gatti contro Altri animali!</li>
      <li><b>🐺 Capobranco</b>Ogni domenica alle 21 chi ha più punti nel suo comune (con almeno 3 luci) diventa Capobranco per una settimana. Commenta ogni giorno (+5) e tagga gli amici (+3) per salire.</li>
      <li><b>⛲ La tua città cresce</b>A 5 luci la fontanella, a 10 il parco cani, a 25 il gattile, a 50 la clinica veterinaria, a 100 la piazza dei Fondatori.</li>
      <li><b>➕ Seguici · ${new Date() < new Date("2026-11-02") ? "+30 fino a domenica 🔥" : "+10"}</b>Segui @zampeditalia e scrivi <code>SEGUO</code> in un commento. Nei reel mettiamo prima gli animali di chi ci segue. 🎃 Fino al 2 novembre il tuo animale ha anche il costume di Halloween sulla mappa; poi le lucine sulla cuccia e la prima fila nel suo paese, vicino alla piazza.</li>
      <li><b>📣 Fai il tifo · +5</b>Non hai animali? Scegli la squadra: <code>Tifo cani: Treviso</code> oppure <code>Tifo gatti: Milano</code>.</li>
      <li><b>☁️ Il tuo sogno · +10</b>L'animale che vorresti: <code>Sogno: Padova, Bruno, bassotto</code>.</li>
      <li><b>✦ Una stella</b>Per chi non c'è più: <code>Stella: Treviso, Max</code>. Una stella nel cielo col suo nome, mai in classifica.</li>
      <li><b>👑 I ruoli</b>Fondatore (primo del comune), Sindaco a 4 zampe (primo della città), Capobranco (primo della regione), Cane d'Italia e Gatto d'Italia, proclamati la domenica alle 21.</li>
      <li><b>🙋 Punti ogni giorno</b>+5 per un commento su un reel nuovo, +3 per ogni amico taggato che poi commenta. Chi porta più amici in un giorno è il Re degli inviti 👑</li>
      <li><b>Privacy</b>Sulla mappa ci sono solo il tuo @ pubblico, la città e quello che hai scritto. Per sparire, commenta <code>RIMUOVI</code>.</li></ul>`;
  }
}
document.querySelectorAll(".tab").forEach(t => t.onclick = () => { if (t.dataset.v === "negozio" && !SCELTO) { try { const id = localStorage.getItem("mio"); SCELTO = id && DATA.find(d => d.id === id) || null; } catch (e) {} } show(t.dataset.v); });
// ---------- il paese in 3D (mondo3d.js) ----------
const vicino = () => { const c = map.getCenter(); let best = null, bd = Infinity; for (const v of VILLE.values()) { const k = c.distanceTo(v.ll); if (k < bd) { bd = k; best = v; } } return best; };
const QUANTI = (v, k) => v.lista.filter(d => d.acc?.includes(k)).length;
function entra3d(v) {
  if (!v || !window.Mondo3D) return;
  map.closePopup(); $("#sheet").hidden = true;
  let mio = SCELTO; if (!mio) try { const id = localStorage.getItem("mio"); mio = id && DATA.find(d => d.id === id); } catch (e) {}
  window.Mondo3D.apri(v, { svg: petSvg, bello: BELLO?.id, mio: mio && mio.villa === v ? mio : null, scheda: d => {
    const manca = ARTICOLI.filter(a => !d.acc?.includes(a[0]));
    return popup(d).replace('<div class="pop">', '<div class="pop">') + (manca.length ? `<div class="m3-vetrina">${manca.map(([k, nome, prezzo]) =>
      `<button type="button" class="m3-art regala" data-id="${esc(d.id)}" data-k="${k}"><span>${ICONE[k]}</span><b>${nome}</b><small>${prezzo}${QUANTI(v, k) ? ` · ${QUANTI(v, k)} in ${esc(v.nome)}` : ""}</small></button>`).join("")}</div>` : `<div class="m3-tutto">✨ Ha già tutti gli accessori!</div>`);
  } });
}
$("#entra3d").onclick = () => entra3d(vicino());
document.addEventListener("click", e => { const t = e.target.closest(".entra-qui"); if (t) entra3d(DATA.find(d => d.id === t.dataset.id)?.villa); });
document.addEventListener("click", e => { const b = e.target.closest(".regala"); if (!b) return; SCELTO = DATA.find(d => d.id === b.dataset.id); map.closePopup(); window.Mondo3D?.chiudi(); show("negozio"); });
// ---------- il mondo è vivo: ogni tanto un animale manda un cuore, una lucciola passa, una stella cadente attraversa l'Italia ----------
if (!matchMedia("(prefers-reduced-motion: reduce)").matches) {
  setInterval(() => { const pets = [...document.querySelectorAll(".leaflet-marker-icon .pet:not(.stella)")]; if (!pets.length) return;
    const p = pets[Math.floor(Math.random() * pets.length)], c = document.createElement("span");
    c.className = "cuore"; c.textContent = ["❤️", "💛", "🐾", "✨", "💤", "🦴"][Math.floor(Math.random() * 6)]; p.appendChild(c); setTimeout(() => c.remove(), 2600); }, 1400);
  setInterval(() => { if (document.hidden || map.getZoom() > 9) return; const c = document.createElement("div"); c.className = "cometa";
    c.style.top = 8 + Math.random() * 40 + "%"; c.style.left = 20 + Math.random() * 60 + "%"; map.getContainer().appendChild(c); setTimeout(() => c.remove(), 1800); }, 9000);
}

// ---------- ricerca ----------
let COMUNI = null;
function focus(d) {
  if (!d) return;
  map.flyTo(posto(d, 14.5, scala(14.5)), 14.5, { duration: 1 });
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
  DATA = prepare(list); stats(); ville(); renderHeader(); syncPets(); syncCities(STATS.city);
  if (!raf && recentCount) raf = requestAnimationFrame(loop); else redraw();
  if (!$("#sheet").hidden) show(document.querySelector('.tab[aria-selected="true"]').dataset.v);
}
map.on("move zoom resize", redraw);
map.on("moveend zoomend", () => { syncPets(); syncCities(STATS.city || []); redraw(); });
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
