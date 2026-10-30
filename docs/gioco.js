// Zampe di corsa: il minigioco di Zampe d'Italia. Il tuo animale corre di notte per le vie del paese,
// salta idranti e vasi, raccoglie ossi. Si guadagna con la pubblicità facoltativa ("guarda un video e continua")
// e con quella tra una partita e l'altra; si cresce con le sfide tra amici (un link col punteggio da battere).
const D = window.Disegni;
const $ = s => document.querySelector(s);
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const salva = (k, v) => { try { localStorage.setItem(k, v); } catch (e) {} };
const leggi = k => { try { return localStorage.getItem(k); } catch (e) { return null; } };

// ---------- pubblicità (Google AdSense, annunci per giochi H5) ----------
// Finché CLIENT è vuoto il gioco va senza pubblicità e "Continua" è gratis una volta a partita.
// Quando Alberto ha l'account AdSense approvato: metti qui "ca-pub-…" e lo stesso numero in docs/ads.txt.
const PUB = { client: "ca-pub-9487085633840449", prova: false }; // prova: true mostra annunci finti di Google per collaudare
let adBreak = null;
if (PUB.client) {
  if (!document.querySelector('script[src*="adsbygoogle.js"]')) { // di solito c'è già nella <head>, per la verifica AdSense
  const s = document.createElement("script");
  s.async = true; s.crossOrigin = "anonymous";
  s.src = "https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=" + PUB.client;
  s.dataset.adFrequencyHint = "90s";
  if (PUB.prova) s.dataset.adbreakTest = "on";
  document.head.appendChild(s); }
  window.adsbygoogle = window.adsbygoogle || [];
  adBreak = o => window.adsbygoogle.push(o);
  adBreak({ preloadAdBreaks: "on", sound: "on" }); // è adConfig: stessa coda
}

// ---------- il tuo animale ----------
const RAZZA_BASE = { cane: "meticcio", gatto: "europeo" };
let PET = null; // { n, t, rk, seed }
function aspetto(p) { // i colori della razza, dalla stessa tabella della mappa
  if (p.t === "gatto") { const g = D.GATTI[p.rk] || D.GATTI.europeo; return { gatto: true, fur: g.fur, stripe: g.stripe, point: g.point, white: g.white, patches: g.patches, eye: g.eye || "#C9E36B", fluffy: g.fluffy }; }
  const c = D.CANI[p.rk] || D.CANI.meticcio;
  let fur = c.fur, earC = c.earC, muz = c.muz;
  if (c.mix) { const toni = ["#B98450", "#8A5A35", "#D9B07A", "#3C312B", "#E7D9C2", "#A0693A"]; fur = toni[p.seed % toni.length]; earC = scuro(fur, .25); muz = chiaro(fur, .45); }
  return { fur, ear: c.ear || "flop", earC: earC || scuro(fur, .25), muz: muz || chiaro(fur, .4), mask: c.mask, blaze: c.blaze, patch: c.patch, cap: c.cap, face: c.face, eye: c.eye, curly: c.curly, flat: c.flat };
}
const mescola = (hex, t, k) => { const n = parseInt(hex.slice(1), 16), c = [n >> 16, (n >> 8) & 255, n & 255];
  return "#" + c.map(v => Math.round(v + (t - v) * k).toString(16).padStart(2, "0")).join(""); };
const scuro = (hex, k) => mescola(hex, 0, k), chiaro = (hex, k) => mescola(hex, 255, k);

function scegliPet(p) {
  PET = { n: p.n || "Zampa", t: p.t === "gatto" ? "gatto" : "cane", rk: p.rk, seed: p.seed ?? D.hash(p.n || "zampa") };
  if (!PET.rk) PET.rk = RAZZA_BASE[PET.t];
  PET.look = aspetto(PET);
  salva("gioco:pet", JSON.stringify({ n: PET.n, t: PET.t, rk: PET.rk, seed: PET.seed }));
  mostraMio();
}
function mostraMio() {
  const nomeRazza = (PET.t === "gatto" ? D.GATTI : D.CANI)[PET.rk]?.n || "";
  $("#mio").innerHTML = `<canvas width="168" height="128" aria-hidden="true"></canvas><span class="chi"><b>${esc(PET.n)}</b><small>${esc(nomeRazza)}</small></span><button type="button" id="cambia">Cambia</button>`;
  const c = $("#mio canvas"), x = c.getContext("2d"); x.scale(2, 2);
  disegnaAnimale(x, 34, 58, 0, PET.look, false, 0.95);
  $("#cambia").onclick = () => { $("#scegli").hidden = false; $("#nome").value = PET.n; $("#tipo").value = PET.t; $("#razza").value = ""; $("#nome").focus(); };
}
$("#scegli").onsubmit = e => { e.preventDefault();
  const t = $("#tipo").value, testo = $("#razza").value.trim();
  scegliPet({ n: $("#nome").value.trim() || "Zampa", t, rk: testo ? D.razza(testo, t) : PET?.t === t ? PET.rk : RAZZA_BASE[t], seed: D.hash($("#nome").value + t) });
  $("#scegli").hidden = true; };

async function caricaPet() {
  try { const r = await fetch("data/razze.json"); if (r.ok) D.carica(await r.json()); } catch (e) {}
  const mio = leggi("mio"); // lo sceglie chi si cerca nella mappa, scheda «Il mio»
  if (mio) try {
    const r = await fetch("data/animali.json?t=" + Math.floor(Date.now() / 60000)); const j = await r.json();
    const d = (j.animali || []).find(a => (a.id || "") === mio && a.t !== "altro");
    if (d) return scegliPet({ n: d.n, t: d.t, rk: D.razza(d.razza_testo || d.razza, d.t), seed: D.hash(d.id) });
  } catch (e) {}
  try { const p = JSON.parse(leggi("gioco:pet")); if (p && p.n) return scegliPet(p); } catch (e) {}
  scegliPet(SFIDA ? { n: "Zampa", t: SFIDA.t, rk: null } : { n: "Zampa", t: "cane" });
  $("#scegli").hidden = false;
}

// ---------- la sfida tra amici: ?sfida=Luna&p=1234&t=cane&a=golden ----------
const Q = new URLSearchParams(location.search);
const OGGI = new Date().toLocaleDateString("sv-SE"); // AAAA-MM-GG
const GIORNO = /^\d{4}-\d{2}-\d{2}$/.test(Q.get("giorno") || "") ? Q.get("giorno") : null; // percorso del giorno arrivato con una sfida
const generatore = seme => { let x = (seme % 2147483646) + 1; return () => (x = (x * 16807) % 2147483647) / 2147483647; };
const SFIDA = Q.has("sfida") && +Q.get("p") > 0 ? { n: Q.get("sfida").slice(0, 20), p: Math.floor(+Q.get("p")), t: Q.get("t") === "gatto" ? "gatto" : "cane" } : null;
if (SFIDA) { $("#sfidaBanner").hidden = false; $("#sfidaBanner").innerHTML = `⚔️ <b>${esc(SFIDA.n)}</b> ti sfida: batti <b>${SFIDA.p.toLocaleString("it-IT")}</b> punti!`; }
// il record entra nella classifica settimanale commentando un reel: il motore dei commenti sa chi scrive (motore/commenti.py)
const codiceCorsa = p => D.hash("zampe-corsa|" + p).toString(36).slice(-2).toUpperCase();
const testoCorsa = p => `CORSA ${p} ${codiceCorsa(p)}`;
async function caricaPodio() {
  try { const r = await fetch("data/animali.json?t=" + Math.floor(Date.now() / 60000)); const j = await r.json(); const c = j.corsa;
    if (!c || !(c.classifica.length || c.scorsa.length)) return;
    const riga = ([u, p], i) => `<li>${["🥇", "🥈", "🥉"][i] || i + 1 + "."}<span>@${esc(u)}</span><b>${(+p).toLocaleString("it-IT")}</b></li>`;
    $("#podio").innerHTML = (c.classifica.length ? `<h3>🏆 Classifica della settimana</h3><ol>${c.classifica.slice(0, 10).map(riga).join("")}</ol>` : "")
      + (c.scorsa.length ? `<small>Settimana scorsa: ${c.scorsa.map(([u]) => "@" + esc(u)).join(" · ")}</small>` : "")
      + `<small>Per entrare: a fine partita copia il codice e commentalo sotto un reel.</small>`;
    $("#podio").hidden = false;
  } catch (e) {}
}
caricaPodio();
const RECORD = () => +leggi("gioco:record") || 0;
const scriviRecord = () => { $("#recordInizio").textContent = RECORD() ? `Il tuo record: ${RECORD().toLocaleString("it-IT")} punti` : ""; };
scriviRecord();

// ---------- disegno dell'animale di profilo ----------
// x,y = punto a terra sotto il corpo; fase = ciclo della corsa; inAria = zampe raccolte.
function disegnaAnimale(c, x, y, fase, L, inAria, s = 1) {
  c.save(); c.translate(x, y); c.scale(s, s);
  const g = L.gatto, bob = inAria ? 0 : Math.abs(Math.sin(fase)) * -2.5;
  const bordo = "rgba(20,12,6,.45)";
  c.lineCap = "round"; c.lineJoin = "round";
  // ombra a terra
  c.fillStyle = "rgba(0,0,0,.28)"; c.beginPath(); c.ellipse(2, 0, 26, 4, 0, 0, Math.PI * 2); c.fill();
  c.translate(0, bob);
  const zampa = (hx, hy, ang, colore, lung) => { // una zampa: coscia e stinco
    const a = inAria ? ang * 0.3 + 0.6 * Math.sign(hx || 1) : ang;
    const kx = hx + Math.sin(a) * lung * .55, ky = hy + Math.cos(a) * lung * .55;
    const fx = kx + Math.sin(a - (inAria ? 1 : .35)) * lung * .5, fy = Math.min(ky + Math.cos(a - .35) * lung * .5, 0);
    c.strokeStyle = colore; c.lineWidth = g ? 5 : 6.5;
    c.beginPath(); c.moveTo(hx, hy); c.lineTo(kx, ky); c.lineTo(fx, fy); c.stroke();
    c.fillStyle = colore; c.beginPath(); c.ellipse(fx + 2, fy - 1, 4, 2.6, 0, 0, Math.PI * 2); c.fill();
  };
  const sw = Math.sin(fase), sw2 = Math.sin(fase + Math.PI);
  const zampeColore = L.point || L.cap ? (L.point || scuro(L.fur, .15)) : scuro(L.fur, .18);
  // zampe lontane (più scure)
  zampa(-14, -18, sw2 * .7, scuro(zampeColore, .25), 20); zampa(14, -18, sw * .7, scuro(zampeColore, .25), 20);
  // coda
  const coda = Math.sin(fase * 1.5) * 4;
  c.strokeStyle = L.point || L.fur; c.lineWidth = g ? 4.5 : (L.curly ? 8 : 6);
  c.beginPath();
  if (g) { c.moveTo(-22, -24); c.bezierCurveTo(-36, -26, -40, -44 + coda, -30, -50 + coda); }
  else { c.moveTo(-22, -26); c.quadraticCurveTo(-34, -32 + coda, -36, -42 + coda); }
  c.stroke();
  // corpo
  const corpo = c.createLinearGradient(0, -38, 0, -12);
  corpo.addColorStop(0, chiaro(L.fur, .12)); corpo.addColorStop(1, scuro(L.fur, .12));
  c.fillStyle = corpo; c.strokeStyle = bordo; c.lineWidth = 1.2;
  c.beginPath(); c.ellipse(0, -25, g ? 22 : 25, g ? 10.5 : 12.5, -0.04, 0, Math.PI * 2); c.fill(); c.stroke();
  if (L.cap) { c.fillStyle = L.cap; c.beginPath(); c.ellipse(-2, -31, 19, 6.5, -0.05, Math.PI, Math.PI * 2); c.fill(); }
  if (L.patch) { c.fillStyle = L.patch; c.beginPath(); c.ellipse(-8, -29, 8, 6, .3, 0, Math.PI * 2); c.fill(); }
  if (L.white) { c.fillStyle = L.white; c.beginPath(); c.ellipse(4, -19, 15, 5, 0, 0, Math.PI * 2); c.fill(); }
  if (L.patches) { L.patches.forEach((col, i) => { c.fillStyle = col; c.beginPath(); c.ellipse(-10 + i * 12, -28 + i * 3, 6, 4.5, i, 0, Math.PI * 2); c.fill(); }); }
  if (L.stripe) { c.strokeStyle = L.stripe; c.lineWidth = 2.2; for (let i = -12; i <= 8; i += 6) { c.beginPath(); c.moveTo(i, -35); c.quadraticCurveTo(i + 2, -29, i - 1, -24); c.stroke(); } }
  if (L.curly) { c.fillStyle = chiaro(L.fur, .2); for (let i = -18; i <= 16; i += 7) { c.beginPath(); c.arc(i, -33, 3.2, 0, Math.PI * 2); c.fill(); } }
  // zampe vicine
  zampa(-14, -18, sw * .7, zampeColore, 20); zampa(14, -18, sw2 * .7, zampeColore, 20);
  // collo e testa
  const hx = g ? 22 : 25, hy = g ? -38 : -42;
  c.fillStyle = L.fur; c.beginPath(); c.ellipse(17, -31, 8, 10, .6, 0, Math.PI * 2); c.fill();
  c.fillStyle = L.face || L.fur; c.strokeStyle = bordo; c.lineWidth = 1.2;
  c.beginPath(); c.arc(hx, hy, g ? 10 : 11.5, 0, Math.PI * 2); c.fill(); c.stroke();
  if (L.mask) { c.fillStyle = L.mask; c.beginPath(); c.arc(hx + 3, hy + 1, 7.5, -0.6, 1.8); c.fill(); }
  if (L.blaze) { c.fillStyle = L.blaze; c.beginPath(); c.ellipse(hx + 6, hy - 3, 2.5, 7, .4, 0, Math.PI * 2); c.fill(); }
  // muso
  if (g) { c.fillStyle = L.white || chiaro(L.fur, .35); c.beginPath(); c.ellipse(hx + 8, hy + 3, 5, 4, 0, 0, Math.PI * 2); c.fill(); }
  else { c.fillStyle = L.mask ? scuro(L.mask, .1) : L.muz; c.strokeStyle = bordo;
    c.beginPath(); c.ellipse(hx + 11, hy + 3, L.flat ? 5 : 9, 6, 0.08, 0, Math.PI * 2); c.fill(); c.stroke(); }
  // naso, bocca, lingua
  c.fillStyle = g ? "#E88A9A" : "#1A120E";
  c.beginPath(); c.ellipse(hx + (g ? 12.5 : L.flat ? 15 : 19), hy + (g ? 1.5 : 0), g ? 1.8 : 3.2, g ? 1.4 : 2.6, 0, 0, Math.PI * 2); c.fill();
  if (!g && !inAria) { c.fillStyle = "#E86B7A"; c.beginPath(); c.ellipse(hx + 12, hy + 10, 2.6, 4 + Math.abs(sw) * 1.5, .2, 0, Math.PI * 2); c.fill(); }
  // occhio con riflesso
  c.fillStyle = L.eye || "#1E120A"; c.beginPath(); c.ellipse(hx + 4, hy - 3, g ? 2.4 : 2.6, g ? 3 : 2.8, 0, 0, Math.PI * 2); c.fill();
  if (g) { c.fillStyle = "#111"; c.beginPath(); c.ellipse(hx + 4.4, hy - 3, .8, 2.4, 0, 0, Math.PI * 2); c.fill(); }
  c.fillStyle = "#fff"; c.beginPath(); c.arc(hx + 4.8, hy - 4, .9, 0, Math.PI * 2); c.fill();
  // orecchie
  const ec = g ? (L.point || L.fur) : L.earC, sb = Math.sin(fase) * (inAria ? 0 : 2);
  c.fillStyle = ec; c.strokeStyle = bordo; c.beginPath();
  if (g) { c.moveTo(hx - 7, hy - 6); c.lineTo(hx - 5, hy - 18); c.lineTo(hx + 1, hy - 9); c.closePath(); c.moveTo(hx, hy - 9); c.lineTo(hx + 4, hy - 19); c.lineTo(hx + 7, hy - 8); c.closePath(); }
  else if (L.ear === "up" || L.ear === "big" || L.ear === "bat") { const k = L.ear === "up" ? 1 : 1.35; c.moveTo(hx - 8, hy - 6); c.lineTo(hx - 6 - 2 * k, hy - 8 - 12 * k); c.lineTo(hx + 1, hy - 9); c.closePath(); }
  else if (L.ear === "semi") { c.moveTo(hx - 8, hy - 6); c.lineTo(hx - 4, hy - 17); c.lineTo(hx + 3, hy - 13 + sb * .5); c.lineTo(hx + 1, hy - 8); c.closePath(); }
  else { const lg = L.ear === "long" ? 15 : 10; c.moveTo(hx - 4, hy - 9); c.quadraticCurveTo(hx - 10, hy - 6, hx - 8 + sb, hy - 2 + lg); c.quadraticCurveTo(hx - 3, hy + lg, hx - 2, hy - 4); c.closePath(); }
  c.fill(); c.stroke();
  // collare
  if (!g) { c.strokeStyle = "#E0453A"; c.lineWidth = 3; c.beginPath(); c.arc(hx - 1, hy + 2, 10, 1.4, 2.6); c.stroke();
    c.fillStyle = "#FFC55C"; c.beginPath(); c.arc(hx - 4, hy + 12, 2, 0, Math.PI * 2); c.fill(); }
  else { c.strokeStyle = "rgba(255,244,222,.6)"; c.lineWidth = .6; c.beginPath(); c.moveTo(hx + 10, hy + 3); c.lineTo(hx + 20, hy + 1); c.moveTo(hx + 10, hy + 4.5); c.lineTo(hx + 20, hy + 5); c.stroke(); }
  c.restore();
}

// ---------- scena ----------
const cv = $("#scena"), cx = cv.getContext("2d");
const H = 400; let W = 800, K = 1, DPR = 1;
const TERRA = 330;
function misura() {
  DPR = Math.min(devicePixelRatio || 1, 2);
  cv.width = innerWidth * DPR; cv.height = innerHeight * DPR;
  K = innerHeight / H; W = innerWidth / K;
  if (W < 420) { K = innerWidth / 420; W = 420; } // telefono in verticale: cane grande, ma abbastanza strada davanti per reagire
  costruisciCitta();
}
addEventListener("resize", misura);

let RNG = 1; const rnd = () => (RNG = (RNG * 16807) % 2147483647) / 2147483647;
let CITTA = [], STELLE = [];
function costruisciCitta() { // due file di case con campanili e cupole, finestre accese a caso
  RNG = 7; CITTA = []; STELLE = [];
  for (let i = 0; i < 90; i++) STELLE.push([rnd() * 1600, rnd() * 220, rnd() * 1.4 + .3, rnd() * 6]);
  for (const [fila, par, base, hMin, hMax, col] of [[0, .15, TERRA - 40, 60, 150, "#101C3E"], [1, .4, TERRA - 8, 40, 110, "#172756"]]) {
    let x = 0; const lista = [];
    while (x < 1600) {
      const w = 40 + rnd() * 60, h = hMin + rnd() * (hMax - hMin), tipo = rnd();
      const fin = []; for (let fy = base - h + 14; fy < base - 16; fy += 18) for (let fx = x + 8; fx < x + w - 10; fx += 14) if (rnd() < (fila ? .35 : .18)) fin.push([fx, fy, rnd() < .15]);
      lista.push({ x, w, h, tipo: tipo < .08 ? "campanile" : tipo < .13 ? "cupola" : tipo < .5 ? "tetto" : "piatto", fin });
      x += w + (fila ? 2 : rnd() * 10);
    }
    CITTA.push({ par, base, col, lista, larg: x });
  }
}

function disegnaSfondo(t, cam) {
  const c = cx;
  const cielo = c.createLinearGradient(0, 0, 0, TERRA);
  cielo.addColorStop(0, "#060B1A"); cielo.addColorStop(1, "#1A2D63");
  c.fillStyle = cielo; c.fillRect(0, -2000, W, TERRA + 2000);
  for (const [sx, sy, r, ph] of STELLE) { const x = ((sx - cam * .03) % 1600 + 1600) % 1600; if (x > W) continue;
    c.globalAlpha = .45 + .4 * Math.sin(t * 1.7 + ph); c.fillStyle = "#FFF4DE"; c.fillRect(x, sy, r, r); }
  c.globalAlpha = 1;
  // luna
  const lx = W - 110, g = c.createRadialGradient(lx, 80, 10, lx, 80, 90);
  g.addColorStop(0, "rgba(255,244,222,.35)"); g.addColorStop(1, "rgba(255,244,222,0)");
  c.fillStyle = g; c.fillRect(lx - 90, -10, 180, 180);
  c.fillStyle = "#FFF4DE"; c.beginPath(); c.arc(lx, 80, 26, 0, Math.PI * 2); c.fill();
  c.fillStyle = "rgba(200,190,170,.35)"; c.beginPath(); c.arc(lx - 8, 74, 5, 0, 7); c.arc(lx + 9, 88, 3.5, 0, 7); c.fill();
  for (const f of CITTA) {
    const off = -((cam * f.par) % f.larg);
    for (const rip of [0, f.larg]) for (const e of f.lista) {
      const x = e.x + off + rip; if (x > W || x + e.w < 0) continue;
      const top = f.base - e.h; c.fillStyle = f.col; c.beginPath();
      if (e.tipo === "tetto") { c.moveTo(x, f.base); c.lineTo(x, top); c.lineTo(x + e.w / 2, top - 16); c.lineTo(x + e.w, top); c.lineTo(x + e.w, f.base); }
      else if (e.tipo === "campanile") { c.rect(x + e.w / 2 - 10, top - 50, 20, e.h + 50); c.moveTo(x + e.w / 2 - 12, top - 50); c.lineTo(x + e.w / 2, top - 72); c.lineTo(x + e.w / 2 + 12, top - 50); c.rect(x, top + 20, e.w, e.h - 20); }
      else if (e.tipo === "cupola") { c.rect(x, top, e.w, e.h); c.moveTo(x + 6, top); c.arc(x + e.w / 2, top, e.w / 2 - 6, Math.PI, 0); c.rect(x + e.w / 2 - 2, top - e.w / 2 - 6, 4, 10); }
      else c.rect(x, top, e.w, e.h);
      c.fill();
      for (const [fx, fy, calda] of e.fin) { c.fillStyle = calda ? "#FFB347" : "rgba(255,197,92,.75)"; c.fillRect(fx + off + rip, fy, 7, 9); }
    }
  }
  // lampioni
  const passo = 260, o = -((cam * .85) % passo);
  for (let x = o; x < W + passo; x += passo) {
    const lg = c.createRadialGradient(x, TERRA - 88, 2, x, TERRA - 88, 70);
    lg.addColorStop(0, "rgba(255,197,92,.45)"); lg.addColorStop(1, "rgba(255,197,92,0)");
    c.fillStyle = lg; c.fillRect(x - 70, TERRA - 160, 140, 160);
    c.fillStyle = "#0B1430"; c.fillRect(x - 2, TERRA - 88, 4, 88); c.fillRect(x - 9, TERRA - 92, 18, 5);
    c.fillStyle = "#FFE0A0"; c.beginPath(); c.arc(x, TERRA - 84, 4, 0, 7); c.fill();
  }
  // strada a sampietrini
  c.fillStyle = "#2A3B70"; c.fillRect(0, TERRA, W, 6);
  c.fillStyle = "#1B2852"; c.fillRect(0, TERRA + 6, W, 2000);
  c.fillStyle = "rgba(85,119,201,.28)";
  const so = -(cam % 24);
  for (let r = 0; r < 4; r++) for (let x = so + (r % 2) * 12; x < W; x += 24) c.fillRect(x, TERRA + 12 + r * 16, 20, 12);
}

// ---------- ostacoli e ossi ----------
const OSTACOLI = {
  idrante: { w: 22, h: 34, d(c, x) { c.fillStyle = "#D8392E"; c.fillRect(x + 4, TERRA - 28, 14, 28); c.beginPath(); c.arc(x + 11, TERRA - 28, 8, Math.PI, 0); c.fill();
    c.fillStyle = "#A82820"; c.fillRect(x, TERRA - 20, 22, 6); c.fillRect(x + 2, TERRA - 4, 18, 4); c.fillStyle = "#FFC55C"; c.fillRect(x + 9, TERRA - 38, 4, 4); } },
  cono: { w: 24, h: 30, d(c, x) { c.fillStyle = "#FF8A2A"; c.beginPath(); c.moveTo(x + 4, TERRA - 2); c.lineTo(x + 12, TERRA - 30); c.lineTo(x + 20, TERRA - 2); c.fill();
    c.fillStyle = "#FFF4DE"; c.fillRect(x + 8, TERRA - 18, 8, 4); c.fillStyle = "#C2611B"; c.fillRect(x, TERRA - 3, 24, 3); } },
  vaso: { w: 30, h: 40, d(c, x) { c.fillStyle = "#3E8E41"; for (const [a, b] of [[6, 26], [15, 36], [24, 28], [10, 32], [20, 33]]) { c.beginPath(); c.ellipse(x + a, TERRA - b, 5, 7, a / 10, 0, 7); c.fill(); }
    c.fillStyle = "#C8673A"; c.beginPath(); c.moveTo(x + 2, TERRA - 22); c.lineTo(x + 28, TERRA - 22); c.lineTo(x + 24, TERRA); c.lineTo(x + 6, TERRA); c.fill(); c.fillStyle = "#A9512A"; c.fillRect(x, TERRA - 24, 30, 5); } },
  panchina: { w: 58, h: 26, d(c, x) { c.fillStyle = "#6B4027"; c.fillRect(x, TERRA - 22, 58, 5); c.fillRect(x, TERRA - 30, 58, 4); c.fillStyle = "#2A2F3E"; c.fillRect(x + 4, TERRA - 17, 4, 17); c.fillRect(x + 50, TERRA - 17, 4, 17); } },
  piccione: { w: 28, h: 18, volo: true, d(c, x, y, t) { const a = Math.sin(t * 14) * 7; c.fillStyle = "#8C96A3"; c.beginPath(); c.ellipse(x + 14, y + 9, 12, 7, 0, 0, 7); c.fill();
    c.fillStyle = "#6E7887"; c.beginPath(); c.moveTo(x + 10, y + 7); c.lineTo(x + 18, y + 7); c.lineTo(x + 14, y - 3 + a); c.fill();
    c.fillStyle = "#5C6B7A"; c.beginPath(); c.arc(x + 4, y + 6, 5, 0, 7); c.fill(); c.fillStyle = "#FFB347"; c.fillRect(x - 3, y + 6, 4, 2); c.fillStyle = "#111"; c.fillRect(x + 3, y + 4, 1.6, 1.6); } },
};
function disegnaOsso(c, x, y, oro, t) {
  c.save(); c.translate(x, y + Math.sin(t * 4 + x * .05) * 3); c.rotate(-.35);
  if (oro) { const g = c.createRadialGradient(0, 0, 2, 0, 0, 22); g.addColorStop(0, "rgba(255,197,92,.6)"); g.addColorStop(1, "rgba(255,197,92,0)"); c.fillStyle = g; c.fillRect(-22, -22, 44, 44); }
  c.fillStyle = oro ? "#FFC55C" : "#FFF4DE"; c.strokeStyle = oro ? "#C2802F" : "#C8B89A"; c.lineWidth = 1;
  c.beginPath(); c.rect(-8, -2.5, 16, 5); for (const [a, b] of [[-8, -3], [-8, 3], [8, -3], [8, 3]]) { c.moveTo(a + 4, b); c.arc(a, b, 4, 0, 7); }
  c.fill(); c.stroke(); c.restore();
}

// ---------- partita ----------
const ANIMALE_X = 120;
let S = null, ultimo = 0, giro = null, premuto = false, continuato = false, giorno = null;
function nuovaPartita(daCapo = true, delGiorno = giorno) {
  if (daCapo) { giorno = delGiorno; S = { rnd: giorno ? generatore(D.hash("zampe" + giorno)) : Math.random, cam: 0, vel: 330, y: 0, vy: 0, salti: 0, tenuto: 0, ostacoli: [], ossi: [], ossiPresi: 0, puntiOssi: 0, doppio: 0, prossimo: 500, fase: 0, t: 0, finita: false, battuto: false, scintille: [] }; continuato = false; }
  else { S.finita = false; S.y = 0; S.vy = 0; S.salti = 0; S.ostacoli = S.ostacoli.filter(o => o.x - S.cam > W * .9); }
  $("#inizio").hidden = true; $("#fine").hidden = true; $("#hud").hidden = false;
  if (SFIDA) { $("#bersaglio").hidden = false; }
  ultimo = performance.now(); cancelAnimationFrame(giro); giro = requestAnimationFrame(passo);
}
const punti = () => Math.floor(S.cam / 40) + S.puntiOssi;

function genera() {
  const rand = S.rnd;
  const x = S.cam + W + 40, vel = S.vel;
  const tipi = vel > 420 ? ["idrante", "cono", "vaso", "panchina", "piccione", "idrante"] : ["idrante", "cono", "vaso", "cono"];
  const k = tipi[Math.floor(rand() * tipi.length)], o = OSTACOLI[k];
  S.ostacoli.push({ k, x, y: o.volo ? TERRA - 92 - rand() * 18 : 0 });
  if (rand() < .25 && vel > 480 && !o.volo) S.ostacoli.push({ k: "cono", x: x + o.w + 4, y: 0 }); // coppia: serve il doppio salto o un salto lungo
  // ossi: in fila a terra o ad arco sopra l'ostacolo
  const oro = rand() < .07;
  if (rand() < .55) { const n = 3 + Math.floor(rand() * 3), arco = rand() < .5;
    for (let i = 0; i < n; i++) S.ossi.push({ x: x + (arco ? -40 + i * 26 : 120 + i * 26), y: arco ? TERRA - 70 - Math.sin((i / (n - 1)) * Math.PI) * 50 : TERRA - 22, oro: oro && i === n - 1 }); }
  const minimo = vel * .62 + 110; // spazio sufficiente per atterrare e risaltare
  S.prossimo = S.cam + W + 40 + minimo + rand() * (220 + vel * .4);
}

function salta() {
  if (!S || S.finita) return;
  if (S.y === 0) { S.vy = -620; S.salti = 1; S.tenuto = .22; }
  else if (S.salti < 2) { S.vy = -540; S.salti = 2; S.tenuto = .12; scintille(ANIMALE_X, TERRA + S.y, "#FFF4DE"); }
}
function scintille(x, y, col) { for (let i = 0; i < 10; i++) S.scintille.push({ x, y, vx: (Math.random() - .5) * 220, vy: -Math.random() * 200, v: .5, col }); }

function passo(ora) {
  const dt = Math.min((ora - ultimo) / 1000, 1 / 20); ultimo = ora;
  if (!S.finita) {
    S.t += dt; S.vel = Math.min(330 + S.t * 9, W < 600 ? 640 : 760); S.cam += S.vel * dt; S.fase += dt * S.vel / 26;
    // salto: tenendo premuto la gravità è più leggera per un attimo
    const g = premuto && S.tenuto > 0 && S.vy < 0 ? 900 : 2300; S.tenuto -= dt;
    S.vy += g * dt; S.y += S.vy * dt; if (S.y >= 0) { S.y = 0; S.vy = 0; S.salti = 0; }
    if (S.cam + W > S.prossimo) genera();
    S.doppio = Math.max(0, S.doppio - dt);
    const ay = TERRA + S.y, box = [ANIMALE_X - 22, ay - 40, ANIMALE_X + 30, ay - 4]; // il corpo, un po' perdonato
    for (const o of S.ostacoli) { const d = OSTACOLI[o.k], ox = o.x - S.cam, oy = d.volo ? o.y : TERRA - d.h;
      if (box[2] > ox + 4 && box[0] < ox + d.w - 4 && box[3] > oy + 4 && box[1] < oy + d.h) { fine(); break; } }
    S.ossi = S.ossi.filter(b => { const bx = b.x - S.cam; if (bx < -30) return false;
      if (Math.abs(bx - ANIMALE_X - 6) < 26 && Math.abs(b.y - (ay - 24)) < 30) {
        S.ossiPresi++; S.puntiOssi += 10 * (S.doppio > 0 ? 2 : 1);
        if (b.oro) { S.doppio = 6; scintille(bx, b.y, "#FFC55C"); } else scintille(bx, b.y, "#FFF4DE");
        if (navigator.vibrate) try { navigator.vibrate(8); } catch (e) {}
        return false; }
      return true; });
    S.ostacoli = S.ostacoli.filter(o => o.x - S.cam > -80);
    if (SFIDA && !S.battuto && punti() > SFIDA.p) { S.battuto = true; scintille(ANIMALE_X, TERRA - 60, "#FFC55C"); }
  }
  disegna(ora / 1000);
  aggiornaHud();
  if (!S.finita || S.scintille.length) giro = requestAnimationFrame(passo);
}

function disegna(t) {
  cx.setTransform(DPR * K, 0, 0, DPR * K, 0, 0);
  cx.translate(0, Math.max(0, innerHeight / K - H) * .6); // telefono in verticale: la strada scende, sopra resta cielo
  disegnaSfondo(t, S ? S.cam : t * 60);
  if (!S) { disegnaAnimale(cx, ANIMALE_X, TERRA, t * 12, PET?.look || aspetto({ t: "cane", rk: "meticcio", seed: 1 }), false, 1.1); return; }
  for (const b of S.ossi) disegnaOsso(cx, b.x - S.cam, b.y, b.oro, t);
  for (const o of S.ostacoli) OSTACOLI[o.k].d(cx, o.x - S.cam, o.y, t);
  if (SFIDA && !S.battuto) { const fx = SFIDA.p * 40 - (S.puntiOssi * 40) - S.cam + ANIMALE_X; // il traguardo dell'amico, sulla strada
    if (fx > -10 && fx < W + 10) { cx.fillStyle = "rgba(255,197,92,.85)"; cx.fillRect(fx, TERRA - 120, 3, 120);
      cx.fillStyle = "#FFC55C"; cx.fillRect(fx + 3, TERRA - 120, 34, 20); cx.fillStyle = "#2A1606"; cx.font = "800 11px Nunito,sans-serif"; cx.fillText(SFIDA.n.slice(0, 6), fx + 6, TERRA - 106); } }
  disegnaAnimale(cx, ANIMALE_X, TERRA + S.y, S.fase, PET.look, S.y < 0, 1.1);
  for (const p of S.scintille) { p.v -= 1 / 60; p.x += p.vx / 60; p.y += p.vy / 60; p.vy += 8; cx.globalAlpha = Math.max(p.v * 2, 0); cx.fillStyle = p.col; cx.fillRect(p.x, p.y, 3, 3); }
  cx.globalAlpha = 1; S.scintille = S.scintille.filter(p => p.v > 0);
}

let hudPrima = "";
function aggiornaHud() {
  const p = punti(), chiave = p + "|" + S.ossiPresi + "|" + (S.doppio > 0) + "|" + S.battuto; if (chiave === hudPrima) return; hudPrima = chiave;
  $("#punti").textContent = p.toLocaleString("it-IT"); $("#ossi").textContent = S.ossiPresi; $("#doppio").hidden = !(S.doppio > 0);
  if (SFIDA) $("#bersaglio").innerHTML = S.battuto ? `🏆 Hai battuto <b>${esc(SFIDA.n)}</b>!` : `⚔️ ${esc(SFIDA.n)}: <b>${SFIDA.p.toLocaleString("it-IT")}</b><br>mancano ${(SFIDA.p - p + 1).toLocaleString("it-IT")}`;
}

function fine() {
  S.finita = true; scintille(ANIMALE_X + 20, TERRA + S.y - 30, "#FF6B5C");
  if (navigator.vibrate) try { navigator.vibrate([40, 30, 60]); } catch (e) {}
  const p = punti(), nuovo = p > RECORD(), kg = "gioco:giorno:" + giorno, primaOggi = +leggi(kg) || 0;
  if (nuovo) salva("gioco:record", String(p));
  if (giorno && p > primaOggi) salva(kg, String(p));
  setTimeout(() => {
    $("#hud").hidden = true; $("#fine").hidden = false; $("#copiato").textContent = "";
    $("#finePunti").textContent = p.toLocaleString("it-IT");
    $("#fineTitolo").textContent = nuovo ? "Nuovo record!" : ["Che corsa!", "Ahia!", "Quasi!", "Bella corsa!"][Math.floor(Math.random() * 4)];
    $("#esito").textContent = SFIDA ? (p > SFIDA.p ? `Hai battuto ${SFIDA.n}! Ora sfida qualcun altro.` : `Ti mancano ${(SFIDA.p - p + 1).toLocaleString("it-IT")} punti per battere ${SFIDA.n}.`)
      : giorno ? (p > primaOggi ? `Il tuo migliore nella sfida del giorno! Mandalo agli amici: stesso percorso per tutti.` : `Nella sfida del giorno il tuo migliore è ${primaOggi.toLocaleString("it-IT")}.`)
      : nuovo ? (S.ossiPresi ? `${PET.n} ha ${S.ossiPresi} ossi in bocca.` : `Prendi gli ossi: ognuno vale 10 punti.`) : `Il tuo record è ${RECORD().toLocaleString("it-IT")}.`;
    $("#codice").textContent = testoCorsa(p);
    offriContinua();
    $("#rigioca").focus();
  }, 650);
}

// ---------- continua: guardando un video (con pubblicità attiva) o gratis una volta (senza) ----------
let mostraVideo = null;
function offriContinua() {
  const b = $("#continua"); b.hidden = true; mostraVideo = null;
  if (continuato) return;
  if (!adBreak) { b.hidden = false; b.querySelector("small").textContent = "una volta a partita"; return; }
  setTimeout(() => { if (!mostraVideo && !continuato && !$("#fine").hidden) { b.hidden = false; b.querySelector("small").textContent = "una volta a partita"; } }, 2500); // Google non risponde: continua gratis
  adBreak({ type: "reward", name: "continua",
    beforeAd: () => { $("#velo").hidden = false; },
    afterAd: () => { $("#velo").hidden = true; },
    beforeReward: show => { mostraVideo = show; b.hidden = false; b.querySelector("small").textContent = "guarda un breve video"; },
    adDismissed: () => { b.hidden = true; },
    adViewed: () => { continuato = true; nuovaPartita(false); },
    adBreakDone: () => { $("#velo").hidden = true; // nessun video disponibile (es. account non ancora approvato): continua gratis
      if (!mostraVideo && !continuato) { b.hidden = false; b.querySelector("small").textContent = "una volta a partita"; } } });
}
$("#continua").onclick = () => { if (mostraVideo) mostraVideo(); else { continuato = true; nuovaPartita(false); } };
$("#rigioca").onclick = () => {
  if (adBreak) adBreak({ type: "next", name: "rigioca", beforeAd: () => { $("#velo").hidden = false; }, afterAd: () => { $("#velo").hidden = true; }, adBreakDone: () => { $("#velo").hidden = true; nuovaPartita(); } });
  else nuovaPartita();
};
$("#gioca").onclick = () => nuovaPartita(true, GIORNO && SFIDA ? GIORNO : null);
$("#oggi").onclick = () => nuovaPartita(true, OGGI);
const oggiMio = +leggi("gioco:giorno:" + OGGI) || 0;
if (oggiMio) $("#oggi").querySelector("small").textContent = `stesso percorso per tutti · il tuo migliore: ${oggiMio.toLocaleString("it-IT")}`;
if (GIORNO && SFIDA) $("#sfidaBanner").innerHTML += `<br><small>Sul percorso del giorno ${GIORNO.split("-").reverse().join("/")}</small>`;

// ---------- sfida un amico ----------
$("#sfida").onclick = async () => {
  const p = punti(), u = new URL("gioco.html", location.href);
  u.search = new URLSearchParams({ sfida: PET.n, p, t: PET.t, ...(giorno ? { giorno } : {}) }).toString();
  const testo = `🐾 ${PET.n} ha fatto ${p.toLocaleString("it-IT")} punti ${giorno ? "nella sfida del giorno " : ""}a Zampe di corsa! Riesci a battermi?`;
  if (navigator.share) { try { await navigator.share({ title: "Zampe di corsa", text: testo, url: u.href }); return; } catch (e) { if (e.name === "AbortError") return; } }
  try { await navigator.clipboard.writeText(testo + " " + u.href); $("#copiato").textContent = "Link copiato: incollalo su WhatsApp o in un DM."; }
  catch (e) { $("#copiato").textContent = u.href; }
};

const copiaCodice = async () => { try { await navigator.clipboard.writeText($("#codice").textContent); $("#copiato").textContent = "Codice copiato: incollalo in un commento sotto l'ultimo reel."; }
  catch (e) { const r = document.createRange(); r.selectNodeContents($("#codice")); getSelection().removeAllRanges(); getSelection().addRange(r); $("#copiato").textContent = "Copia il codice e incollalo in un commento."; } };
$("#codice").onclick = copiaCodice;
$("#vaiIg").onclick = () => { copiaCodice(); }; // il link si apre comunque: il codice è già negli appunti

// ---------- comandi ----------
const giu = e => { if (e.target.closest && e.target.closest("button,a,input,select,.schermo")) return; premuto = true; salta(); e.preventDefault?.(); };
const su = () => { premuto = false; };
cv.addEventListener("pointerdown", giu); addEventListener("pointerup", su); addEventListener("pointercancel", su);
addEventListener("keydown", e => { if (e.repeat) return;
  if (e.code === "Space" || e.code === "ArrowUp" || e.code === "KeyW") { if (!S || S.finita) { if (!$("#inizio").hidden && !e.target.closest("input,select,button")) { e.preventDefault(); nuovaPartita(); } return; } premuto = true; salta(); e.preventDefault(); } });
addEventListener("keyup", e => { if (e.code === "Space" || e.code === "ArrowUp" || e.code === "KeyW") premuto = false; });

// schermata iniziale: la strada scorre dietro il menu
misura();
(function attesa(ora) { if (S) return; disegna(ora / 1000); requestAnimationFrame(attesa); })(performance.now());
caricaPet();
