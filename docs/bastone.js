// Riporta il bastone: tocchi a tempo sulla barra della forza che oscilla, il bastone vola, il tuo animale corre a
// prenderlo e te lo riporta. Più lontano cade più punti fai; se cade nella zona gialla segnata sul prato, bonus.
// 10 lanci a partita, e a ogni lancio la barra oscilla più veloce.
const Z = window.Zampe, $ = Z.$;
const cv = $("#scena"), cx = cv.getContext("2d");
const LARGO = 400; let K = 1, DPR = 1, ALTO = 700, X0 = 0;
function misura() {
  DPR = Math.min(devicePixelRatio || 1, 2);
  cv.width = innerWidth * DPR; cv.height = innerHeight * DPR;
  K = Math.min(innerWidth / LARGO, innerHeight / 640); ALTO = innerHeight / K; X0 = (innerWidth / K - LARGO) / 2;
}
addEventListener("resize", misura); misura();
const TERRA = () => Math.round(Math.min(ALTO - 160, ALTO * .66)); // il prato: sotto c'è la barra della forza
const METRO = 30;                         // unità del mondo per un metro
const PARTENZA = 96;                      // dove aspetta il tuo animale
const MIN_M = 5, MAX_M = 50;              // il lancio più corto e il più lungo
const LANCI = 10, ZONA_M = 4, BONUS_ZONA = 30, BONUS_PERFETTO = 10;
const xDi = m => PARTENZA + m * METRO;
const MANO = () => ({ x: PARTENZA - 40, y: TERRA() - 128 }); // la tua mano, che tiene il bastone prima del lancio

// ---------- partita ----------
// fasi di un lancio: mira (la barra oscilla) → volo (bastone in aria, l'animale parte) → presa → ritorno → consegna
let S = null, giro = null, ultimo = 0;
function nuovaZona() { S.zona = 14 + Math.random() * (MAX_M - 20); } // inizio della zona gialla, in metri
function nuova(daCapo) {
  if (daCapo || !S) S = { punti: 0, lancio: 0, totale: LANCI, fase: "mira", t: 0, barra: 0, giri: 0, cam: 0,
    x: PARTENZA, dir: 1, passi: 0, b: null, testi: [], scintille: [], finita: false, migliore: 0, inZona: 0, attesa: .45 };
  else { S.totale = S.lancio + 3; S.finita = false; S.fase = "mira"; S.attesa = .45; } // «continua»: altri 3 lanci
  nuovaZona(); S.giri = 0;
  ultimo = performance.now(); cancelAnimationFrame(giro); giro = requestAnimationFrame(passo); aggiornaHud();
}
const frequenza = () => .55 + .13 * Math.min(S.lancio, 12); // oscillazioni al secondo: sempre più veloce
const valoreBarra = g => { const f = g % 1; return f < .5 ? f * 2 : 2 - f * 2; }; // va su e giù, da 0 a 1

function lancia() {
  if (!S || S.finita || S.fase !== "mira" || S.attesa > 0) return;
  const v = S.barra, metri = MIN_M + v * (MAX_M - MIN_M), durata = .75 + v * .85;
  const m0 = MANO();
  S.b = { metri, v, durata, t: 0, x: m0.x, y: m0.y, ang: 0, x0: m0.x, y0: m0.y, alto: 120 + v * 250, aTerra: false, rimbalzo: 0 };
  S.fase = "volo"; S.t = 0; S.dir = 1;
  if (navigator.vibrate) try { navigator.vibrate(20); } catch (e) {}
}

function passo(ora) {
  const dt = Math.min((ora - ultimo) / 1000, 1 / 20); ultimo = ora;
  if (!S.finita) aggiorna(dt);
  disegna(ora / 1000, dt);
  if (!S.finita || S.scintille.length || S.testi.length) giro = requestAnimationFrame(passo);
}

function aggiorna(dt) {
  S.t += dt; S.attesa = Math.max(0, S.attesa - dt);
  const b = S.b;
  if (S.fase === "mira") {
    S.giri += dt * frequenza(); S.barra = valoreBarra(S.giri);
  } else if (S.fase === "volo") {
    // il bastone segue la sua parabola; l'animale parte subito di corsa
    b.t += dt; const u = Math.min(b.t / b.durata, 1);
    b.x = b.x0 + (xDi(b.metri) - b.x0) * u; b.y = b.y0 + (TERRA() - 6 - b.y0) * u - b.alto * 4 * u * (1 - u);
    b.ang += dt * (8 + b.v * 10);
    if (u >= 1 && !b.aTerra) atterra();
    corri(dt, xDi(b.metri) - 30, 1, 520 + b.v * 260);
    if (b.aTerra && Math.abs(S.x - (xDi(b.metri) - 30)) < 2) { S.fase = "presa"; S.t = 0; scintille(xDi(b.metri), TERRA() - 8, "#FFF4DE"); }
  } else if (S.fase === "presa") {
    if (S.t > .3) { S.fase = "ritorno"; S.t = 0; S.dir = -1; }
  } else if (S.fase === "ritorno") {
    corri(dt, PARTENZA, -1, 900);
    if (Math.abs(S.x - PARTENZA) < 2) { S.fase = "consegna"; S.t = 0; S.dir = 1; S.b = null; }
  } else if (S.fase === "consegna") {
    if (S.t > .45) {
      S.lancio++; aggiornaHud();
      if (S.lancio >= S.totale) {
        S.finita = true;
        T.fine(S.punti, `Lancio più lungo: ${Math.round(S.migliore)} m. Nella zona gialla: ${S.inZona} volt${S.inZona === 1 ? "a" : "e"} su ${S.totale}.`);
      } else { S.fase = "mira"; S.t = 0; S.giri = 0; S.attesa = .25; nuovaZona(); }
    }
  }
  if (b && b.aTerra) { b.rimbalzo += dt; }
  // la telecamera segue il bastone in volo, poi il tuo animale
  const segui = S.fase === "volo" && b && !b.aTerra ? b.x : S.x;
  const meta = Math.max(0, segui - LARGO * .45);
  S.cam += (meta - S.cam) * Math.min(1, dt * (S.fase === "volo" ? 9 : 6));
  for (const q of S.testi) { q.v -= dt; q.y -= dt * 28; }
  S.testi = S.testi.filter(q => q.v > 0);
}

function corri(dt, verso, dir, vel) {
  const d = verso - S.x, p = Math.sign(d) * Math.min(Math.abs(d), vel * dt);
  S.x += p; S.passi += Math.abs(p) / 7; S.dir = Math.abs(d) > 1 ? Math.sign(d) : dir;
}

function atterra() {
  const b = S.b; b.aTerra = true; b.y = TERRA() - 6; b.ang = .12;
  const m = b.metri, dentro = m >= S.zona && m <= S.zona + ZONA_M, perfetto = b.v >= .96;
  let p = Math.round(m); S.migliore = Math.max(S.migliore, m);
  const x = xDi(m);
  S.testi.push({ x, y: TERRA() - 70, testo: `${Math.round(m)} m`, col: "#FFF4DE", v: 1.6, grande: true });
  if (dentro) { p += BONUS_ZONA; S.inZona++; S.testi.push({ x, y: TERRA() - 100, testo: `Nella zona! +${BONUS_ZONA}`, col: "#FFC55C", v: 1.8 }); scintille(x, TERRA() - 10, "#FFC55C", 24); }
  if (perfetto) { p += BONUS_PERFETTO; S.testi.push({ x, y: TERRA() - (dentro ? 128 : 100), testo: `Lancio perfetto! +${BONUS_PERFETTO}`, col: "#CFE36B", v: 1.8 }); }
  S.punti += p; aggiornaHud();
  if (navigator.vibrate && dentro) try { navigator.vibrate([30, 30, 50]); } catch (e) {}
}
function scintille(x, y, col, n = 12) { for (let i = 0; i < n; i++) S.scintille.push({ x, y, vx: (Math.random() - .5) * 220, vy: -Math.random() * 200, v: .6, col }); }

// ---------- disegno ----------
const STELLE = Array.from({ length: 36 }, (_, i) => [(i * 97) % 400, (i * 53) % 260, (i % 3) * .5 + .6, i]);
function bastone(c, x, y, ang, s = 1) { // un ramo con un rametto e un nodo
  c.save(); c.translate(x, y); c.rotate(ang); c.scale(s, s); c.lineCap = "round";
  c.strokeStyle = "#5A3418"; c.lineWidth = 7.5; c.beginPath(); c.moveTo(-19, 1); c.quadraticCurveTo(0, -3, 19, 0); c.stroke();
  c.strokeStyle = "#9A6232"; c.lineWidth = 5; c.beginPath(); c.moveTo(-18, 1); c.quadraticCurveTo(0, -3, 18, 0); c.stroke();
  c.strokeStyle = "#7A4A24"; c.lineWidth = 2.5; c.beginPath(); c.moveTo(5, -1.5); c.lineTo(11, -9); c.stroke();
  c.fillStyle = "#6FA34F"; c.beginPath(); c.ellipse(12.5, -10.5, 3.2, 1.8, -.6, 0, 7); c.fill();
  c.fillStyle = "#C98545"; c.beginPath(); c.arc(-6, -.5, 1.4, 0, 7); c.fill();
  c.restore();
}
function disegna(t, dt) {
  const c = cx, cam = S ? S.cam : 0, terra = TERRA();
  c.setTransform(DPR * K, 0, 0, DPR * K, DPR * K * X0, 0);
  const sx = -X0 - 10, lw = LARGO + 2 * X0 + 20;
  // cielo al tramonto
  const cielo = c.createLinearGradient(0, 0, 0, terra);
  cielo.addColorStop(0, "#0E1A3A"); cielo.addColorStop(.55, "#4A3470"); cielo.addColorStop(.85, "#D9715A"); cielo.addColorStop(1, "#FFB347");
  c.fillStyle = cielo; c.fillRect(sx, 0, lw, terra);
  for (const [x, y, r, k] of STELLE) { c.globalAlpha = (.3 + .3 * Math.sin(t * 1.5 + k)) * (1 - y / 300); c.fillStyle = "#FFF4DE"; c.fillRect(x, y, r, r); }
  c.globalAlpha = 1;
  // nuvole lente (parallasse)
  for (let i = 0; i < 5; i++) { const w = 400 + LARGO, x = ((i * 157 + t * 4 - cam * .08) % w + w) % w - 90, y = 90 + i * 70 + (i % 2) * 25;
    c.fillStyle = `rgba(255,${200 - i * 12},${190 - i * 15},${.10 + i * .035})`; c.beginPath();
    c.ellipse(x, y, 46, 11, 0, 0, 7); c.ellipse(x + 22, y - 7, 26, 10, 0, 0, 7); c.ellipse(x - 20, y - 4, 20, 8, 0, 0, 7); c.fill(); }
  // sole basso, che si muove pochissimo
  const sole = c.createRadialGradient(300 - cam * .02, terra - 60, 4, 300 - cam * .02, terra - 60, 90);
  sole.addColorStop(0, "rgba(255,230,160,.95)"); sole.addColorStop(.3, "rgba(255,197,92,.6)"); sole.addColorStop(1, "rgba(255,179,71,0)");
  c.fillStyle = sole; c.fillRect(sx, terra - 160, lw, 160);
  // colline lontane e vicine (parallasse)
  const collina = (col, alt, amp, lungo, vel) => { c.fillStyle = col; c.beginPath(); c.moveTo(sx, terra);
    for (let x = sx; x <= sx + lw + 10; x += 8) { const w = x + cam * vel; c.lineTo(x, terra - alt - Math.sin(w / lungo) * amp - Math.sin(w / (lungo * .37)) * amp * .35); }
    c.lineTo(sx + lw + 10, terra); c.fill(); };
  collina("#5B3A6B", 70, 22, 90, .15); collina("#3A2E5A", 42, 16, 60, .35);
  // alberi a metà distanza
  for (let i = -1; i < 9; i++) { const base = Math.floor(cam * .55 / 140) * 140 + i * 140, x = base - cam * .55 + 30, h = 50 + ((base / 140 * 37) % 3 + 3) % 3 * 12;
    c.fillStyle = "#2A2448"; c.fillRect(x - 3, terra - h * .45, 6, h * .45); c.beginPath(); c.arc(x, terra - h * .55, h * .32, 0, 7); c.arc(x - 12, terra - h * .4, h * .22, 0, 7); c.arc(x + 12, terra - h * .42, h * .24, 0, 7); c.fill(); }
  // prato
  const prato = c.createLinearGradient(0, terra, 0, ALTO);
  prato.addColorStop(0, "#3E7A3C"); prato.addColorStop(1, "#1F4A2A");
  c.fillStyle = prato; c.fillRect(sx, terra, lw, ALTO - terra);
  c.save(); c.translate(-cam, 0);
  // ciuffi d'erba
  c.strokeStyle = "#5A9A48"; c.lineWidth = 1.5;
  for (let x = Math.floor((cam + sx) / 23) * 23; x < cam + sx + lw; x += 23) { const k = (x * 7) % 5; c.beginPath(); c.moveTo(x, terra + 4 + k); c.lineTo(x - 2, terra - 2 + k); c.moveTo(x + 3, terra + 4 + k); c.lineTo(x + 4, terra - 3 + k); c.stroke(); }
  for (let x = Math.floor((cam + sx) / 61) * 61; x < cam + sx + lw; x += 61) { const k = Math.abs(x * 13) % 7, y = terra + 40 + k * 9;
    c.fillStyle = k % 2 ? "#FFF4DE" : "#FFC55C"; for (let i = 0; i < 5; i++) { c.beginPath(); c.arc(x + Math.cos(i * 1.26) * 3, y + Math.sin(i * 1.26) * 3, 2, 0, 7); c.fill(); }
    c.fillStyle = "#E0453A"; c.beginPath(); c.arc(x, y, 1.6, 0, 7); c.fill(); }
  if (S) {
    // la zona gialla del bonus, con due bandierine
    const z0 = xDi(S.zona), z1 = xDi(S.zona + ZONA_M);
    c.fillStyle = "rgba(255,197,92,.32)"; c.fillRect(z0, terra, z1 - z0, 26);
    c.fillStyle = "rgba(255,197,92,.6)"; for (let x = z0; x < z1; x += 16) c.fillRect(x, terra, 8, 4);
    for (const x of [z0, z1]) { c.strokeStyle = "#FFF4DE"; c.lineWidth = 2; c.beginPath(); c.moveTo(x, terra + 4); c.lineTo(x, terra - 40); c.stroke();
      c.fillStyle = "#FFC55C"; c.beginPath(); c.moveTo(x, terra - 40); c.lineTo(x + 16 + Math.sin(t * 6 + x) * 2, terra - 34); c.lineTo(x, terra - 28); c.fill(); }
    c.fillStyle = "#FFC55C"; c.font = "800 13px 'Bricolage Grotesque', system-ui, sans-serif"; c.textAlign = "center";
    c.fillText("BONUS", (z0 + z1) / 2, terra + 42);
  }
  // cartelli dei metri
  c.font = "800 12px 'Nunito', system-ui, sans-serif"; c.textAlign = "center";
  for (let m = 10; m <= MAX_M; m += 10) { const x = xDi(m); if (x < cam + sx - 30 || x > cam + sx + lw + 30) continue;
    c.fillStyle = "#6B4424"; c.fillRect(x - 2, terra - 30, 4, 34);
    c.fillStyle = "#FFF4DE"; c.beginPath(); c.roundRect ? c.roundRect(x - 19, terra - 44, 38, 18, 5) : c.rect(x - 19, terra - 44, 38, 18); c.fill();
    c.fillStyle = "#2A1606"; c.fillText(`${m} m`, x, terra - 31); }
  // la linea di partenza
  c.fillStyle = "rgba(255,244,222,.7)"; c.fillRect(PARTENZA + 30, terra, 3, 22);
  if (!S) { c.restore(); Z.PET && Z.disegnaAnimale(c, LARGO / 2, terra + 6, t * 8, Z.PET.look, false, 1.35); return; }
  // il bastone a terra o in volo (con la scia)
  const b = S.b;
  if (b && S.fase === "volo") {
    if (!b.aTerra) { c.strokeStyle = "rgba(255,244,222,.25)"; c.lineWidth = 3; c.setLineDash([4, 8]); c.beginPath(); c.moveTo(b.x0, b.y0);
      for (let u = 0; u <= b.t / b.durata; u += .04) c.lineTo(b.x0 + (xDi(b.metri) - b.x0) * u, b.y0 + (terra - 6 - b.y0) * u - b.alto * 4 * u * (1 - u));
      c.stroke(); c.setLineDash([]); }
    const salto = b.aTerra ? Math.max(0, Math.sin(b.rimbalzo * 14) * 8 * Math.exp(-b.rimbalzo * 6)) : 0;
    bastone(c, b.x, b.y - salto, b.ang, 1.15);
  }
  // il tuo animale (col bastone in bocca quando lo riporta)
  const corre = S.fase === "volo" || S.fase === "ritorno";
  const fase = corre ? S.passi : (S.fase === "consegna" ? t * 10 : Math.sin(t * 2) * .15);
  c.save(); c.translate(S.x, terra + 6); c.scale(S.dir, 1);
  Z.disegnaAnimale(c, 0, 0, fase, Z.PET.look, corre && Math.sin(S.passi * 2) > .8, 1.35);
  if (S.fase === "presa" || S.fase === "ritorno") bastone(c, 50, -43, .1, 1.15);
  c.restore();
  braccio(c, t);
  // scintille e scritte
  for (const p of S.scintille) { p.v -= dt; p.x += p.vx * dt; p.y += p.vy * dt; p.vy += 480 * dt; c.globalAlpha = Math.max(p.v * 2, 0); c.fillStyle = p.col; c.fillRect(p.x, p.y, 3, 3); }
  c.globalAlpha = 1; S.scintille = S.scintille.filter(p => p.v > 0);
  c.textAlign = "center"; c.lineJoin = "round";
  for (const q of S.testi) { c.globalAlpha = Math.min(1, q.v * 1.5); c.font = `800 ${q.grande ? 30 : 18}px 'Bricolage Grotesque', system-ui, sans-serif`;
    c.strokeStyle = "rgba(20,12,6,.75)"; c.lineWidth = 5; c.strokeText(q.testo, q.x, q.y); c.fillStyle = q.col; c.fillText(q.testo, q.x, q.y); }
  c.globalAlpha = 1; c.restore();
  // la zona bonus è fuori schermo? una freccia la indica
  const zx = xDi(S.zona + ZONA_M / 2) - S.cam;
  if (zx > LARGO + X0 - 10 && S.fase === "mira" && !S.finita) { const y = terra - 96 + Math.sin(t * 4) * 3, x = LARGO + X0 - 14;
    const scritta = `Bonus a ${Math.round(S.zona)} m`; c.font = "800 14px 'Nunito', system-ui, sans-serif"; const lw2 = c.measureText(scritta).width + 40;
    c.fillStyle = "rgba(6,11,26,.7)"; c.beginPath(); c.roundRect ? c.roundRect(x - lw2, y - 16, lw2 + 6, 30, 15) : c.rect(x - lw2, y - 16, lw2 + 6, 30); c.fill();
    c.fillStyle = "#FFC55C"; c.textAlign = "right"; c.fillText(scritta, x - 22, y + 5);
    c.beginPath(); c.moveTo(x - 16, y - 7); c.lineTo(x - 4, y); c.lineTo(x - 16, y + 7); c.fill(); }
  barraForza(c, t);
}
// il tuo braccio entra da sinistra: tiene il bastone, si carica con la barra, lo riprende quando torna
function braccio(c, t) {
  const m = MANO(), terra = TERRA(), sx = -X0 - 10;
  const tiene = S.fase === "mira" || S.fase === "consegna" || S.finita;
  const carica = S.fase === "mira" ? S.barra : 0, dopo = S.fase === "volo" ? Math.max(0, 1 - S.b.t * 3) : 0;
  const hx = m.x - carica * 22 + dopo * 30, hy = m.y + carica * 10 - dopo * 20;
  c.lineCap = "round";
  c.strokeStyle = "#3E6FC9"; c.lineWidth = 22; c.beginPath(); c.moveTo(sx - 20, terra - 40); c.quadraticCurveTo(hx - 50, hy + 40, hx - 12, hy + 4); c.stroke();
  c.strokeStyle = "#2E56A6"; c.lineWidth = 6; c.beginPath(); c.moveTo(hx - 24, hy + 16); c.lineTo(hx - 16, hy + 8); c.stroke();
  if (tiene) bastone(c, hx + 4, hy - 6, -.9 - carica * .5, 1.15);
  c.fillStyle = "#E9B48A"; c.strokeStyle = "rgba(20,12,6,.45)"; c.lineWidth = 1.2;
  c.beginPath(); c.ellipse(hx, hy, 11, 9, -.5, 0, 7); c.fill(); c.stroke();
  c.fillStyle = "#D9A276"; c.beginPath(); c.ellipse(hx + 6, hy - 4, 4, 3, -.5, 0, 7); c.fill();
}
// la barra della forza, ferma in basso sullo schermo, con la zona gialla segnata
function barraForza(c, t) {
  const w = Math.min(320, LARGO - 40), x = (LARGO - w) / 2, y = Math.round(TERRA() + (ALTO - TERRA()) * .42), h = 24;
  const mira = S.fase === "mira" && !S.finita;
  c.globalAlpha = mira ? 1 : .45;
  c.fillStyle = "rgba(6,11,26,.75)"; c.beginPath(); c.roundRect ? c.roundRect(x - 6, y - 6, w + 12, h + 12, 16) : c.rect(x - 6, y - 6, w + 12, h + 12); c.fill();
  const g = c.createLinearGradient(x, 0, x + w, 0);
  g.addColorStop(0, "#3E6FC9"); g.addColorStop(.6, "#CFE36B"); g.addColorStop(1, "#FF6B5C");
  c.fillStyle = g; c.beginPath(); c.roundRect ? c.roundRect(x, y, w, h, 10) : c.rect(x, y, w, h); c.fill();
  // dove cadrebbe nella zona bonus
  const v0 = (S.zona - MIN_M) / (MAX_M - MIN_M), v1 = (S.zona + ZONA_M - MIN_M) / (MAX_M - MIN_M);
  c.fillStyle = "rgba(255,197,92,.95)"; c.fillRect(x + w * v0, y - 3, w * (v1 - v0), h + 6);
  c.strokeStyle = "#2A1606"; c.lineWidth = 1.5; c.strokeRect(x + w * v0, y - 3, w * (v1 - v0), h + 6);
  c.fillStyle = "#FFC55C"; c.font = "800 11px 'Nunito', system-ui, sans-serif"; c.textAlign = "center"; c.fillText("BONUS", x + w * (v0 + v1) / 2, y + h + 17);
  c.fillStyle = "#FFF4DE"; c.textAlign = "left"; c.fillText("piano", x, y - 12); c.textAlign = "right"; c.fillText("forte", x + w, y - 12);
  // il cursore
  const v = mira ? S.barra : (S.b ? S.b.v : S.barra), cxv = x + w * v;
  c.fillStyle = "#FFF4DE"; c.strokeStyle = "#2A1606"; c.lineWidth = 2;
  c.beginPath(); c.moveTo(cxv - 8, y - 12); c.lineTo(cxv + 8, y - 12); c.lineTo(cxv, y + 2); c.closePath(); c.fill(); c.stroke();
  c.fillRect(cxv - 2, y, 4, h);
  c.globalAlpha = 1;
  if (mira) { c.fillStyle = "#FFF4DE"; c.font = "800 15px 'Nunito', system-ui, sans-serif"; c.textAlign = "center";
    c.globalAlpha = .75 + .25 * Math.sin(t * 6); c.fillText(S.lancio === 0 ? "Tocca per lanciare il bastone!" : "Tocca per lanciare!", LARGO / 2, y + h + 44); c.globalAlpha = 1; }
}
function aggiornaHud() {
  $("#punti").textContent = Z.fmt(S.punti);
  $("#lanci").textContent = `🪵 ${Math.min(S.lancio + 1, S.totale)}/${S.totale}`;
  if (T.SFIDA) { $("#bersaglio").hidden = false; $("#bersaglio").innerHTML = S.punti > T.SFIDA.p ? `🏆 Hai battuto <b>${Z.esc(T.SFIDA.n)}</b>!` : `⚔️ ${Z.esc(T.SFIDA.n)}: <b>${Z.fmt(T.SFIDA.p)}</b>`; }
}

const T = Z.telaio({ id: "bastone", nome: "Riporta il bastone", codice: "BASTONE", nuova, punti: () => S ? S.punti : 0 });

// ---------- comandi: un tocco o spazio/invio lanciano ----------
cv.addEventListener("pointerdown", e => { e.preventDefault(); lancia(); });
addEventListener("keydown", e => {
  if (!S || S.finita || !$("#fine").hidden || !$("#inizio").hidden) return;
  if (e.code === "Space" || e.code === "Enter" || e.code === "ArrowUp") { e.preventDefault(); if (!e.repeat) lancia(); }
});

(function attesa(ora) { if (S) return; disegna(ora / 1000, 0); requestAnimationFrame(attesa); })(performance.now());
