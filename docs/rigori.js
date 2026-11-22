// I rigori delle Zampe (22/11, Officina): il gioco del Campionato delle Zampe. Il tuo animale tira i rigori con la sciarpa
// della tua squadra; in porta c'è un gatto che si tuffa e diventa più bravo a ogni gol. Tre parate e la partita finisce.
// A fine partita: il codice per la classifica (RIGORI 12 XY) e l'invito a segnare un gol vero nel Campionato (forza <squadra>).
const Z = window.Zampe, $ = Z.$;
const cv = $("#scena"), cx = cv.getContext("2d");
const LARGO = 400; let K = 1, DPR = 1, ALTO = 700, X0 = 0;
function misura() {
  DPR = Math.min(devicePixelRatio || 1, 2);
  cv.width = innerWidth * DPR; cv.height = innerHeight * DPR;
  K = Math.min(innerWidth / LARGO, innerHeight / 640); ALTO = innerHeight / K; X0 = (innerWidth / K - LARGO) / 2;
}
addEventListener("resize", misura); misura();

// ---------- la squadra: quelle coi tifosi sulla mappa, più le grandi; si ricorda l'ultima scelta ----------
const BASE = { inter: ["Inter", "#1B4FA0", "#111111"], milan: ["Milan", "#D2151C", "#111111"], juventus: ["Juventus", "#F4F4F4", "#111111"], roma: ["Roma", "#8E1F2F", "#F0BC42"],
  lazio: ["Lazio", "#87D8F7", "#F4F4F4"], napoli: ["Napoli", "#12A0D7", "#F4F4F4"], fiorentina: ["Fiorentina", "#5B2A86", "#F4F4F4"], atalanta: ["Atalanta", "#1E71B8", "#111111"],
  torino: ["Torino", "#8A1E03", "#F4F4F4"], bologna: ["Bologna", "#A21C26", "#1A2F48"], genoa: ["Genoa", "#A41E2F", "#1C2C5B"], sampdoria: ["Sampdoria", "#1B5497", "#F4F4F4"] };
let SQ = { ...BASE }, scelta = Z.leggi("rigori:squadra") || "roma";
const riempi = () => {
  $("#squadra").innerHTML = Object.entries(SQ).sort((a, b) => a[1][0].localeCompare(b[1][0])).map(([k, v]) => `<option value="${k}"${k === scelta ? " selected" : ""}>${Z.esc(v[0])}</option>`).join("");
};
riempi();
fetch("data/animali.json?t=" + Math.floor(Date.now() / 60000)).then(r => r.json()).then(j => {
  for (const [k, v] of Object.entries(j.squadre || {})) if (!SQ[k] && v && v.c) SQ[k] = [v.n, v.c[0], v.c[1]];
  const P = j.campionato && j.campionato.partita; if (P && !Z.leggi("rigori:squadra")) scelta = P.a.k; // la prima volta: la squadra di casa della partita in corso
  riempi();
}).catch(() => {});
$("#squadra").onchange = () => { scelta = $("#squadra").value; Z.salva("rigori:squadra", scelta); };
const colori = () => SQ[scelta] || BASE.roma;

// ---------- il portiere: un gatto nero ----------
const GATTO = Z.aspetto({ t: "gatto", rk: "nero", seed: 7 });
const PORTA = { x1: 80, x2: 320, y1: 150, y2: 262 }, MIRE = [125, 200, 275];

// ---------- partita ----------
let S = null, giro = null;
function nuova(daCapo) {
  if (daCapo || !S) S = { gol: 0, parate: 0, fase: 0, tiro: null, scritta: null, t0: performance.now() };
  else S.parate = 2; // «continua da qui»: un'ultima parata a disposizione
  S.tiro = null; S.scritta = null; aggiornaHud();
  if (!giro) giro = requestAnimationFrame(passo);
}
const aggiornaHud = () => { $("#punti").textContent = S.gol; $("#vite").textContent = "🧤".repeat(Math.max(0, 3 - S.parate)) || "—"; };
const T = cfgTelaio();
function cfgTelaio() {
  return Z.telaio({ id: "rigori", nome: "I rigori delle Zampe", codice: "RIGORI", nuova, punti: () => (S ? S.gol : 0), pronto: () => {} });
}
function tira(i) {
  if (!S || S.tiro || S.scritta || $("#inizio").hidden === false || !$("#fine").hidden) return;
  // il gatto indovina più spesso a ogni gol (dal 30% fino al 60%)
  const bravo = Math.min(0.6, 0.3 + S.gol * 0.025), dove = Math.random() < bravo ? i : [0, 1, 2].filter(x => x !== i)[Math.floor(Math.random() * 2)];
  S.tiro = { i, dove, t: 0 };
}
cv.addEventListener("pointerdown", e => { const x = e.clientX / K - X0; tira(x < 160 ? 0 : x > 240 ? 2 : 1); });
addEventListener("keydown", e => { const m = { ArrowLeft: 0, ArrowUp: 1, ArrowDown: 1, ArrowRight: 2 }[e.key]; if (m !== undefined) { e.preventDefault(); tira(m); } });

let prima = performance.now();
function passo(ora) {
  const dt = Math.min(0.05, (ora - prima) / 1000); prima = ora;
  if (S && S.tiro) {
    S.tiro.t += dt / 0.55;
    if (S.tiro.t >= 1) {
      const preso = S.tiro.dove === S.tiro.i;
      if (preso) S.parate++; else S.gol++;
      S.scritta = { t: preso ? "PARATA!" : "GOL!", c: preso ? "#FF6B5C" : "#FFD23F", fino: ora + 900 }; S.ultimo = { ...S.tiro }; S.tiro = null; aggiornaHud();
      if (navigator.vibrate) try { navigator.vibrate(preso ? 60 : [30, 30, 30]); } catch (e) {}
    }
  }
  if (S && S.scritta && ora > S.scritta.fino) {
    S.scritta = null; S.ultimo = null;
    if (S.parate >= 3) { const g = S.gol, v = colori()[0]; S = null; T.fine(g, `Ora segna un gol vero nel Campionato delle Zampe: scrivi «forza ${v}» sotto il reel di oggi di @zampeditalia!`); }
  }
  if (S) S.fase += dt * 8;
  disegna(ora);
  giro = requestAnimationFrame(passo);
}

function disegna(ora) {
  const c = cx, [nome, c1, c2] = colori();
  c.setTransform(K * DPR, 0, 0, K * DPR, X0 * K * DPR, 0);
  // il cielo e le curve coi colori della tua squadra
  c.fillStyle = "#16204A"; c.fillRect(-X0, 0, LARGO + 2 * X0, ALTO);
  c.fillStyle = "#2C3960"; c.fillRect(-X0, 40, LARGO + 2 * X0, 120);
  for (let y = 52; y < 155; y += 13) for (let x = -X0 + ((y / 13) % 2) * 7; x < LARGO + X0; x += 14) { c.fillStyle = (Math.floor(x / 14) + Math.floor(y / 13)) % 2 ? c1 : c2; c.beginPath(); c.arc(x, y, 4.2, 0, 7); c.fill(); }
  for (const x of [20, 380]) { c.fillStyle = "#5A6472"; c.fillRect(x - 3, 0, 6, 40); c.fillStyle = "#FFF3B0"; c.fillRect(x - 18, 2, 36, 12); }
  // il campo
  for (let i = 0; i * 40 < ALTO; i++) { c.fillStyle = i % 2 ? "#3C9A48" : "#46A852"; c.fillRect(-X0, 160 + i * 40, LARGO + 2 * X0, 40); }
  c.strokeStyle = "#F4F4F4"; c.lineWidth = 3; c.strokeRect(40, 262, 320, 120); c.beginPath(); c.arc(200, ALTO - 140, 4, 0, 7); c.fillStyle = "#F4F4F4"; c.fill();
  // la porta con la rete
  c.strokeStyle = "rgba(255,255,255,.35)"; c.lineWidth = 1;
  for (let x = PORTA.x1; x <= PORTA.x2; x += 12) { c.beginPath(); c.moveTo(x, PORTA.y1); c.lineTo(x, PORTA.y2); c.stroke(); }
  for (let y = PORTA.y1; y <= PORTA.y2; y += 12) { c.beginPath(); c.moveTo(PORTA.x1, y); c.lineTo(PORTA.x2, y); c.stroke(); }
  c.strokeStyle = "#FFFFFF"; c.lineWidth = 7; c.beginPath(); c.moveTo(PORTA.x1, PORTA.y2); c.lineTo(PORTA.x1, PORTA.y1); c.lineTo(PORTA.x2, PORTA.y1); c.lineTo(PORTA.x2, PORTA.y2); c.stroke();
  // il gatto portiere: al centro, poi si tuffa
  const tf = S && S.tiro ? Math.min(1, S.tiro.t * 1.6) : S && S.ultimo ? 1 : 0, dove = S && (S.tiro || S.ultimo) ? (S.tiro || S.ultimo).dove : 1;
  c.save(); c.translate(200 + (MIRE[dove] - 200) * tf, PORTA.y2 - 6 - Math.sin(tf * Math.PI) * 18); c.rotate((dove - 1) * 1.1 * tf);
  Z.disegnaAnimale(c, 0, 0, S ? S.fase : ora / 120, GATTO, tf > 0, 1.35); c.restore();
  // il pallone: dal dischetto alla mira
  const tt = S && S.tiro ? S.tiro.t : S && S.ultimo ? 1 : 0, mira = S && (S.tiro || S.ultimo) ? MIRE[(S.tiro || S.ultimo).i] : 200;
  const bx = 200 + (mira - 200) * tt, by = (ALTO - 150) + ((PORTA.y1 + 50) - (ALTO - 150)) * tt, br = 11 - 5 * tt;
  if (!(S && S.ultimo && S.ultimo.dove === S.ultimo.i)) { c.fillStyle = "#FFFFFF"; c.strokeStyle = "#1A1206"; c.lineWidth = 2; c.beginPath(); c.arc(bx, by, br, 0, 7); c.fill(); c.stroke();
    c.fillStyle = "#1A1206"; c.beginPath(); c.arc(bx, by, br * 0.35, 0, 7); c.fill(); }
  // il tuo animale con la sciarpa della squadra, di spalle al tiro
  if (Z.PET) {
    const px = 200 - 28 + (S && S.tiro ? 18 * Math.min(1, S.tiro.t * 3) : 0), py = ALTO - 70;
    Z.disegnaAnimale(c, px, py, S ? S.fase : ora / 120, Z.PET.look, false, 1.5);
    c.fillStyle = c1; c.fillRect(px - 16, py - 58, 16, 9); c.fillStyle = c2; c.fillRect(px, py - 58, 16, 9); // la sciarpa
  }
  // la scritta del tiro
  if (S && S.scritta) {
    c.save(); c.translate(200, 340); const k = 1 + Math.max(0, 0.4 - (ora - (S.scritta.fino - 900)) / 600);
    c.scale(k, k); c.font = "900 54px 'Bricolage Grotesque', sans-serif"; c.textAlign = "center"; c.lineWidth = 8; c.strokeStyle = "#1A1206"; c.strokeText(S.scritta.t, 0, 0); c.fillStyle = S.scritta.c; c.fillText(S.scritta.t, 0, 0); c.restore();
  }
  // come si tira (prima del primo tiro)
  if (S && !S.tiro && !S.scritta && S.gol + S.parate === 0) {
    c.font = "800 15px Nunito, sans-serif"; c.textAlign = "center"; c.fillStyle = "#FFF4DE"; c.fillText("Tocca a sinistra, al centro o a destra della porta", 200, 300);
  }
}
