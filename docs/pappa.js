// Pappa al volo: il tuo animale corre a destra e a sinistra e prende al volo la pappa che cade dal cielo.
// Crocchette e ossi fanno punti; cioccolato, uva e cipolla tolgono una vita (fanno male davvero a cani e gatti).
const Z = window.Zampe, $ = Z.$;
const cv = $("#scena"), cx = cv.getContext("2d");
const LARGO = 400; let K = 1, DPR = 1, ALTO = 700, X0 = 0;
function misura() {
  DPR = Math.min(devicePixelRatio || 1, 2);
  cv.width = innerWidth * DPR; cv.height = innerHeight * DPR;
  K = Math.min(innerWidth / LARGO, innerHeight / 640); ALTO = innerHeight / K; X0 = (innerWidth / K - LARGO) / 2;
}
addEventListener("resize", misura); misura();
const TERRA = () => ALTO - 70;

// ---------- cosa cade ----------
const BUONI = [
  { k: "crocchetta", p: 5, peso: 50 }, { k: "osso", p: 10, peso: 30 }, { k: "pesce", p: 15, peso: 10 },
  { k: "oro", p: 25, peso: 3 }, { k: "cuore", p: 0, peso: 2 },
];
const CATTIVI = [{ k: "cioccolato" }, { k: "uva" }, { k: "cipolla" }];
const disegnaCosa = (c, o, t) => {
  c.save(); c.translate(o.x, o.y); c.rotate(Math.sin(t * 3 + o.x) * .25);
  const k = o.k;
  if (k === "crocchetta") { c.fillStyle = "#A8642A"; c.beginPath(); c.arc(0, 0, 8, 0, 7); c.fill(); c.fillStyle = "#C98545"; c.beginPath(); c.arc(-2, -2, 3, 0, 7); c.fill(); }
  else if (k === "osso" || k === "oro") {
    if (k === "oro") { const g = c.createRadialGradient(0, 0, 2, 0, 0, 26); g.addColorStop(0, "rgba(255,197,92,.7)"); g.addColorStop(1, "rgba(255,197,92,0)"); c.fillStyle = g; c.fillRect(-26, -26, 52, 52); }
    c.fillStyle = k === "oro" ? "#FFC55C" : "#FFF4DE"; c.strokeStyle = k === "oro" ? "#C2802F" : "#C8B89A"; c.lineWidth = 1.2;
    c.beginPath(); c.rect(-10, -3, 20, 6); for (const [a, b] of [[-10, -3.5], [-10, 3.5], [10, -3.5], [10, 3.5]]) { c.moveTo(a + 5, b); c.arc(a, b, 5, 0, 7); } c.fill(); c.stroke();
  }
  else if (k === "pesce") { c.fillStyle = "#7FB6E8"; c.beginPath(); c.ellipse(0, 0, 13, 7, 0, 0, 7); c.fill(); c.beginPath(); c.moveTo(11, 0); c.lineTo(20, -7); c.lineTo(20, 7); c.fill(); c.fillStyle = "#123"; c.beginPath(); c.arc(-7, -2, 1.6, 0, 7); c.fill(); }
  else if (k === "cuore") { c.fillStyle = "#FF6B7A"; c.beginPath(); c.moveTo(0, 8); c.bezierCurveTo(-16, -4, -6, -14, 0, -6); c.bezierCurveTo(6, -14, 16, -4, 0, 8); c.fill(); }
  else if (k === "cioccolato") { c.fillStyle = "#4A2614"; c.fillRect(-12, -9, 24, 18); c.strokeStyle = "#2E160A"; c.lineWidth = 1.5; c.strokeRect(-12, -9, 24, 18); c.beginPath(); c.moveTo(0, -9); c.lineTo(0, 9); c.moveTo(-12, 0); c.lineTo(12, 0); c.stroke(); c.fillStyle = "#C8C8D0"; c.fillRect(-12, 3, 24, 6); }
  else if (k === "uva") { c.fillStyle = "#7B3FA0"; for (const [a, b] of [[-6, -5], [0, -6], [6, -5], [-3, 1], [3, 1], [0, 7]]) { c.beginPath(); c.arc(a, b, 4.5, 0, 7); c.fill(); } c.strokeStyle = "#3E8E41"; c.lineWidth = 2; c.beginPath(); c.moveTo(0, -11); c.lineTo(2, -15); c.stroke(); }
  else if (k === "cipolla") { c.fillStyle = "#E8C9A0"; c.beginPath(); c.ellipse(0, 2, 10, 9, 0, 0, 7); c.fill(); c.strokeStyle = "#B88A5A"; c.lineWidth = 1; c.beginPath(); c.moveTo(-5, -4); c.quadraticCurveTo(0, 6, -2, 10); c.moveTo(5, -4); c.quadraticCurveTo(0, 6, 2, 10); c.stroke(); c.fillStyle = "#6FA34F"; c.fillRect(-1.5, -14, 3, 8); }
  if (o.male) { c.strokeStyle = "#FF6B5C"; c.lineWidth = 2; c.beginPath(); c.arc(0, 0, 17, 0, 7); c.stroke(); }
  c.restore();
};

// ---------- partita ----------
let S = null, giro = null, ultimo = 0, verso = 0, mira = null;
const scegliBuono = r => { let t = r * BUONI.reduce((a, b) => a + b.peso, 0); for (const b of BUONI) { t -= b.peso; if (t <= 0) return b; } return BUONI[0]; };
function nuova(daCapo) {
  if (daCapo || !S) S = { x: LARGO / 2, dir: 1, vite: 3, punti: 0, cose: [], t: 0, prossimo: .6, doppio: 0, fase: 0, presi: 0, scintille: [], finita: false, colpito: 0 };
  else { S.vite = 1; S.finita = false; S.cose = []; S.colpito = 1.2; }
  ultimo = performance.now(); cancelAnimationFrame(giro); giro = requestAnimationFrame(passo); aggiornaHud();
}
function passo(ora) {
  const dt = Math.min((ora - ultimo) / 1000, 1 / 20); ultimo = ora;
  if (!S.finita) {
    S.t += dt; S.doppio = Math.max(0, S.doppio - dt); S.colpito = Math.max(0, S.colpito - dt);
    // movimento: verso il dito, o con le frecce
    const vel = 340, prima = S.x;
    if (mira !== null) S.x += Math.max(-vel * dt, Math.min(vel * dt, mira - S.x)); else S.x += verso * vel * dt;
    S.x = Math.max(30, Math.min(LARGO - 30, S.x));
    const mosso = S.x - prima; if (Math.abs(mosso) > .3) { S.dir = Math.sign(mosso); S.fase += Math.abs(mosso) / 6; }
    // pioggia: sempre più fitta e veloce
    S.prossimo -= dt;
    if (S.prossimo <= 0) {
      const male = Math.random() < Math.min(.15 + S.t * .006, .38);
      const tipo = male ? CATTIVI[Math.floor(Math.random() * CATTIVI.length)] : scegliBuono(Math.random());
      S.cose.push({ ...tipo, male, x: 20 + Math.random() * (LARGO - 40), y: -20, v: 120 + Math.min(S.t * 5, 220) + Math.random() * 40 });
      S.prossimo = Math.max(.28, .85 - S.t * .012) * (.7 + Math.random() * .6);
    }
    const bocca = { x: S.x + S.dir * 26, y: TERRA() - 42 };
    S.cose = S.cose.filter(o => {
      o.y += o.v * dt;
      if (Math.abs(o.x - bocca.x) < 30 && Math.abs(o.y - bocca.y) < 28) {
        if (o.male) { if (S.colpito <= 0) { S.vite--; S.colpito = 1; scintille(o.x, o.y, "#FF6B5C"); if (navigator.vibrate) try { navigator.vibrate(60); } catch (e) {} } }
        else if (o.k === "cuore") { S.vite = Math.min(S.vite + 1, 5); scintille(o.x, o.y, "#FF6B7A"); }
        else { S.punti += o.p * (S.doppio > 0 ? 2 : 1); S.presi++; if (o.k === "oro") S.doppio = 6; scintille(o.x, o.y, o.k === "oro" ? "#FFC55C" : "#FFF4DE"); }
        aggiornaHud(); return false;
      }
      return o.y < ALTO + 30;
    });
    if (S.vite <= 0) { S.finita = true; T.fine(S.punti, "Lo sapevi? Cioccolato, uva e cipolla fanno male davvero a cani e gatti."); }
  }
  disegna(ora / 1000);
  if (!S.finita || S.scintille.length) giro = requestAnimationFrame(passo);
}
function scintille(x, y, col) { for (let i = 0; i < 10; i++) S.scintille.push({ x, y, vx: (Math.random() - .5) * 200, vy: -Math.random() * 180, v: .5, col }); }

// ---------- scena: il giardino di notte ----------
const STELLE = Array.from({ length: 50 }, (_, i) => [(i * 97) % 400, (i * 53) % 420, (i % 3) * .5 + .6, i]);
function disegna(t) {
  cx.setTransform(DPR * K, 0, 0, DPR * K, DPR * K * X0, 0);
  const c = cx, cielo = c.createLinearGradient(0, 0, 0, ALTO);
  cielo.addColorStop(0, "#060B1A"); cielo.addColorStop(1, "#1A2D63");
  c.fillStyle = cielo; c.fillRect(-X0 - 10, 0, LARGO + 2 * X0 + 20, ALTO);
  for (const [x, y, r, k] of STELLE) { c.globalAlpha = .4 + .4 * Math.sin(t * 1.5 + k); c.fillStyle = "#FFF4DE"; c.fillRect(x, y, r, r); }
  c.globalAlpha = 1; c.fillStyle = "#FFF4DE"; c.beginPath(); c.arc(330, 80, 22, 0, 7); c.fill();
  // siepe e prato
  c.fillStyle = "#17354A"; for (let x = -X0 - 20; x < LARGO + X0 + 20; x += 34) { c.beginPath(); c.arc(x, TERRA() - 18, 24, Math.PI, 0); c.fill(); }
  c.fillStyle = "#1F4A3A"; c.fillRect(-X0 - 10, TERRA(), LARGO + 2 * X0 + 20, ALTO);
  // la ciotola, per ricordare che è ora di pappa
  c.fillStyle = "#E0453A"; c.beginPath(); c.ellipse(LARGO - 40, TERRA() + 22, 22, 7, 0, 0, 7); c.fill();
  if (!S) { Z.PET && Z.disegnaAnimale(c, LARGO / 2, TERRA() + 6, t * 8, Z.PET.look, false, 1.25); return; }
  for (const o of S.cose) disegnaCosa(c, o, t);
  c.save(); c.translate(S.x, TERRA() + 6); c.scale(S.dir, 1);
  if (S.colpito > 0 && Math.floor(S.colpito * 10) % 2) c.globalAlpha = .4;
  Z.disegnaAnimale(c, 0, 0, S.fase, Z.PET.look, false, 1.25); c.restore(); c.globalAlpha = 1;
  for (const p of S.scintille) { p.v -= 1 / 60; p.x += p.vx / 60; p.y += p.vy / 60; p.vy += 8; c.globalAlpha = Math.max(p.v * 2, 0); c.fillStyle = p.col; c.fillRect(p.x, p.y, 3, 3); }
  c.globalAlpha = 1; S.scintille = S.scintille.filter(p => p.v > 0);
}
function aggiornaHud() {
  $("#punti").textContent = Z.fmt(S.punti);
  $("#vite").textContent = "❤️".repeat(Math.max(S.vite, 0)) || "💔";
  $("#doppio").hidden = !(S.doppio > 0);
  if (T.SFIDA) { $("#bersaglio").hidden = false; $("#bersaglio").innerHTML = S.punti > T.SFIDA.p ? `🏆 Hai battuto <b>${Z.esc(T.SFIDA.n)}</b>!` : `⚔️ ${Z.esc(T.SFIDA.n)}: <b>${Z.fmt(T.SFIDA.p)}</b>`; }
}

const T = Z.telaio({ id: "pappa", nome: "Pappa al volo", codice: "PAPPA", nuova, punti: () => S ? S.punti : 0 });

// ---------- comandi: il dito trascina, le frecce spostano ----------
const dove = e => (e.clientX / K) - X0;
cv.addEventListener("pointerdown", e => { if (!S || S.finita) return; mira = dove(e); cv.setPointerCapture?.(e.pointerId); });
cv.addEventListener("pointermove", e => { if (mira !== null || e.pointerType === "mouse" && S && !S.finita) mira = dove(e); });
addEventListener("pointerup", () => { if (!matchMedia("(pointer:fine)").matches) mira = null; });
addEventListener("keydown", e => { if (e.code === "ArrowLeft" || e.code === "KeyA") { verso = -1; mira = null; } if (e.code === "ArrowRight" || e.code === "KeyD") { verso = 1; mira = null; } });
addEventListener("keyup", e => { if (["ArrowLeft", "KeyA", "ArrowRight", "KeyD"].includes(e.code)) verso = 0; });

(function attesa(ora) { if (S) return; disegna(ora / 1000); requestAnimationFrame(attesa); })(performance.now());
