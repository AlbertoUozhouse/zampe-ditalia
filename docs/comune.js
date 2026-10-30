// Base comune dei minigiochi di Zampe d'Italia (giochi.html): il tuo animale disegnato con i colori della sua razza,
// le schermate di inizio e di fine, la pubblicità facoltativa («guarda un video e continua»), il codice per la classifica
// col @ (commento «PAPPA 123 XY» sotto un reel, letto da motore/commenti.py) e la sfida agli amici con un link.
// Zampe di corsa (gioco.js) è nato prima e ha ancora la sua copia di queste parti.
(function () {
const D = window.Disegni;
const $ = s => document.querySelector(s);
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const salva = (k, v) => { try { localStorage.setItem(k, v); } catch (e) {} };
const leggi = k => { try { return localStorage.getItem(k); } catch (e) { return null; } };
const fmt = n => (+n).toLocaleString("it-IT");

// ---------- pubblicità (Google AdSense, annunci per giochi H5: il codice sta nella <head> di ogni pagina) ----------
window.adsbygoogle = window.adsbygoogle || [];
const adBreak = document.querySelector('script[src*="adsbygoogle.js"]') ? o => window.adsbygoogle.push(o) : null;
if (adBreak) adBreak({ preloadAdBreaks: "on", sound: "on" });

// ---------- il tuo animale ----------
const RAZZA_BASE = { cane: "meticcio", gatto: "europeo" };
const mescola = (hex, t, k) => { const n = parseInt(hex.slice(1), 16), c = [n >> 16, (n >> 8) & 255, n & 255];
  return "#" + c.map(v => Math.round(v + (t - v) * k).toString(16).padStart(2, "0")).join(""); };
const scuro = (hex, k) => mescola(hex, 0, k), chiaro = (hex, k) => mescola(hex, 255, k);
function aspetto(p) { // i colori della razza, dalla stessa tabella della mappa
  if (p.t === "gatto") { const g = D.GATTI[p.rk] || D.GATTI.europeo; return { gatto: true, fur: g.fur, stripe: g.stripe, point: g.point, white: g.white, patches: g.patches, eye: g.eye || "#C9E36B", fluffy: g.fluffy }; }
  const c = D.CANI[p.rk] || D.CANI.meticcio;
  let fur = c.fur, earC = c.earC, muz = c.muz;
  if (c.mix) { const toni = ["#B98450", "#8A5A35", "#D9B07A", "#3C312B", "#E7D9C2", "#A0693A"]; fur = toni[p.seed % toni.length]; earC = scuro(fur, .25); muz = chiaro(fur, .45); }
  return { fur, ear: c.ear || "flop", earC: earC || scuro(fur, .25), muz: muz || chiaro(fur, .4), mask: c.mask, blaze: c.blaze, patch: c.patch, cap: c.cap, face: c.face, eye: c.eye, curly: c.curly, flat: c.flat };
}
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

const Z = { D, $, esc, salva, leggi, fmt, scuro, chiaro, aspetto, disegnaAnimale, adBreak, PET: null };

function scegliPet(p, dopo) {
  const P = { n: p.n || "Zampa", t: p.t === "gatto" ? "gatto" : "cane", rk: p.rk, seed: p.seed ?? D.hash(p.n || "zampa") };
  if (!P.rk) P.rk = RAZZA_BASE[P.t];
  P.look = aspetto(P); Z.PET = P;
  salva("gioco:pet", JSON.stringify({ n: P.n, t: P.t, rk: P.rk, seed: P.seed }));
  if (dopo) dopo(P);
}
// Il tuo animale: quello scelto nella mappa (scheda «Il mio»), o l'ultimo usato in un gioco, o uno da scegliere.
Z.caricaPet = async function (dopo) {
  try { const r = await fetch("data/razze.json"); if (r.ok) D.carica(await r.json()); } catch (e) {}
  const mio = leggi("mio");
  if (mio) try {
    const j = await (await fetch("data/animali.json?t=" + Math.floor(Date.now() / 60000))).json();
    const d = (j.animali || []).find(a => (a.id || "") === mio && a.t !== "altro");
    if (d) return scegliPet({ n: d.n, t: d.t, rk: D.razza(d.razza_testo || d.razza, d.t), seed: D.hash(d.id) }, dopo);
  } catch (e) {}
  try { const p = JSON.parse(leggi("gioco:pet")); if (p && p.n) return scegliPet(p, dopo); } catch (e) {}
  scegliPet({ n: "Zampa", t: "cane" }, dopo); return "nuovo";
};
Z.scegli = (p, dopo) => scegliPet(p, dopo);
Z.ritratto = function (canvas, P = Z.PET) { const x = canvas.getContext("2d"); x.setTransform(2, 0, 0, 2, 0, 0); x.clearRect(0, 0, canvas.width, canvas.height); disegnaAnimale(x, 34, 58, 0, P.look, false, .95); };

// ---------- il telaio di un gioco: schermata iniziale, fine partita, classifica, sfida ----------
// cfg: { id: "pappa", nome: "Pappa al volo", codice: "PAPPA", nuova(daCapo), punti() }
Z.telaio = function (cfg) {
  const Q = new URLSearchParams(location.search);
  const SFIDA = Q.has("sfida") && +Q.get("p") > 0 ? { n: Q.get("sfida").slice(0, 20), p: Math.floor(+Q.get("p")) } : null;
  const kRec = "gioco:record:" + cfg.id, RECORD = () => +leggi(kRec) || 0;
  let continuato = false, mostraVideo = null;
  if (SFIDA) { $("#sfidaBanner").hidden = false; $("#sfidaBanner").innerHTML = `⚔️ <b>${esc(SFIDA.n)}</b> ti sfida: batti <b>${fmt(SFIDA.p)}</b> punti!`; }
  const scriviRecord = () => { $("#recordInizio").textContent = RECORD() ? `Il tuo record: ${fmt(RECORD())} punti` : ""; };
  scriviRecord();
  const mostraMio = () => {
    const P = Z.PET, razza = (P.t === "gatto" ? D.GATTI : D.CANI)[P.rk]?.n || "";
    $("#mio").innerHTML = `<canvas width="168" height="128" aria-hidden="true"></canvas><span class="chi"><b>${esc(P.n)}</b><small>${esc(razza)}</small></span><button type="button" id="cambia">Cambia</button>`;
    Z.ritratto($("#mio canvas"));
    $("#cambia").onclick = () => { $("#scegli").hidden = false; $("#nome").value = P.n; $("#tipo").value = P.t; $("#razza").value = ""; $("#nome").focus(); };
  };
  $("#scegli").onsubmit = e => { e.preventDefault();
    const t = $("#tipo").value, testo = $("#razza").value.trim();
    scegliPet({ n: $("#nome").value.trim() || "Zampa", t, rk: testo ? D.razza(testo, t) : Z.PET?.t === t ? Z.PET.rk : RAZZA_BASE[t], seed: D.hash($("#nome").value + t) }, mostraMio);
    $("#scegli").hidden = true; cfg.pronto && cfg.pronto(); };
  Z.caricaPet(mostraMio).then(r => { if (r === "nuovo") $("#scegli").hidden = false; cfg.pronto && cfg.pronto(); });
  // classifica della settimana dal motore dei commenti
  fetch("data/animali.json?t=" + Math.floor(Date.now() / 60000)).then(r => r.json()).then(j => {
    const c = (j.giochi || {})[cfg.id]; if (!c || !(c.classifica.length || c.scorsa.length)) return;
    const riga = ([u, p], i) => `<li>${["🥇", "🥈", "🥉"][i] || i + 1 + "."}<span>@${esc(u)}</span><b>${fmt(p)}</b></li>`;
    $("#podio").innerHTML = (c.classifica.length ? `<h3>🏆 Classifica della settimana</h3><ol>${c.classifica.slice(0, 10).map(riga).join("")}</ol>` : "")
      + (c.scorsa.length ? `<small>Settimana scorsa: ${c.scorsa.map(([u]) => "@" + esc(u)).join(" · ")}</small>` : "")
      + `<small>Per entrare: a fine partita copia il codice e commentalo sotto un reel.</small>`;
    $("#podio").hidden = false;
  }).catch(() => {});
  const inizia = daCapo => { if (daCapo) continuato = false; $("#inizio").hidden = true; $("#fine").hidden = true; $("#hud").hidden = false; cfg.nuova(daCapo); };
  $("#gioca").onclick = () => inizia(true);
  $("#rigioca").onclick = () => {
    if (adBreak) adBreak({ type: "next", name: "rigioca", beforeAd: () => { $("#velo").hidden = false; }, afterAd: () => { $("#velo").hidden = true; }, adBreakDone: () => { $("#velo").hidden = true; inizia(true); } });
    else inizia(true);
  };
  const offriContinua = () => {
    const b = $("#continua"); b.hidden = true; mostraVideo = null;
    if (continuato) return;
    const gratis = () => { if (!mostraVideo && !continuato && !$("#fine").hidden) { b.hidden = false; b.querySelector("small").textContent = "una volta a partita"; } };
    if (!adBreak) return gratis();
    setTimeout(gratis, 2500); // Google non risponde: continua gratis
    adBreak({ type: "reward", name: "continua",
      beforeAd: () => { $("#velo").hidden = false; }, afterAd: () => { $("#velo").hidden = true; },
      beforeReward: show => { mostraVideo = show; b.hidden = false; b.querySelector("small").textContent = "guarda un breve video"; },
      adDismissed: () => { b.hidden = true; }, adViewed: () => { continuato = true; inizia(false); },
      adBreakDone: () => { $("#velo").hidden = true; gratis(); } });
  };
  $("#continua").onclick = () => { if (mostraVideo) mostraVideo(); else { continuato = true; inizia(false); } };
  const codice = p => D.hash(`zampe-${cfg.id}|${p}`).toString(36).slice(-2).toUpperCase(); // come codice_gioco() in motore/commenti.py
  const copia = async () => { try { await navigator.clipboard.writeText($("#codice").textContent); $("#copiato").textContent = "Codice copiato: incollalo in un commento sotto l'ultimo reel."; }
    catch (e) { const r = document.createRange(); r.selectNodeContents($("#codice")); getSelection().removeAllRanges(); getSelection().addRange(r); $("#copiato").textContent = "Copia il codice e incollalo in un commento."; } };
  $("#codice").onclick = copia; $("#vaiIg").onclick = () => { copia(); };
  $("#sfida").onclick = async () => {
    const p = cfg.punti(), u = new URL(location.pathname.split("/").pop() || "giochi.html", location.href);
    u.search = new URLSearchParams({ sfida: Z.PET.n, p }).toString();
    const testo = `🐾 ${Z.PET.n} ha fatto ${fmt(p)} punti a ${cfg.nome}! Riesci a battermi?`;
    if (navigator.share) { try { await navigator.share({ title: cfg.nome, text: testo, url: u.href }); return; } catch (e) { if (e.name === "AbortError") return; } }
    try { await navigator.clipboard.writeText(testo + " " + u.href); $("#copiato").textContent = "Link copiato: incollalo su WhatsApp o in un DM."; }
    catch (e) { $("#copiato").textContent = u.href; }
  };
  // la partita è finita: il gioco passa punti e una riga da dire (facoltativa)
  return { SFIDA, fine(p, riga) {
    const nuovo = p > RECORD(); if (nuovo) salva(kRec, String(p));
    if (navigator.vibrate) try { navigator.vibrate([40, 30, 60]); } catch (e) {}
    setTimeout(() => {
      $("#hud").hidden = true; $("#fine").hidden = false; $("#copiato").textContent = "";
      $("#finePunti").textContent = fmt(p); $("#fineTitolo").textContent = nuovo ? "Nuovo record!" : ["Che partita!", "Quasi!", "Bravo!"][Math.floor(Math.random() * 3)];
      $("#esito").textContent = SFIDA ? (p > SFIDA.p ? `Hai battuto ${SFIDA.n}! Ora sfida qualcun altro.` : `Ti mancano ${fmt(SFIDA.p - p + 1)} punti per battere ${SFIDA.n}.`) : (riga || (nuovo ? "" : `Il tuo record è ${fmt(RECORD())}.`));
      $("#codice").textContent = `${cfg.codice} ${p} ${codice(p)}`;
      scriviRecord(); offriContinua(); $("#rigioca").focus();
    }, 600);
  } };
};

// I giochi del gruppo, per la pagina giochi.html: il più nuovo in alto.
Z.GIOCHI = [
  { id: "pappa", nome: "Pappa al volo", pagina: "pappa.html", uscito: "2026-10-31", testo: "Prendi crocchette e ossi al volo. Attento a cioccolato, uva e cipolla!" },
  { id: "corsa", nome: "Zampe di corsa", pagina: "gioco.html", uscito: "2026-10-30", testo: "Corri di notte per il paese, salta gli ostacoli, raccogli gli ossi." },
];
window.Zampe = Z;
})();
