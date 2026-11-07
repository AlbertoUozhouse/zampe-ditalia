// La Coppa delle Zampe: campionato settimanale tra comuni (motore/coppa.py tiene i punti, questo file fa giocare).
// Dalla mappa: «Gioca per la tua città» → scegli la tua città (quella del tuo animale) → prova del giorno → codice «COPPA XY» da commentare sotto un reel.
// Un punto al giorno per persona: lo decide il bot. Qui ricaricare la pagina mostra di nuovo lo stesso codice, mai una prova nuova.
(() => {
  const K = { squadra: "zampe.coppa.squadra", fatto: "zampe.coppa.fatto" };
  const salva = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };
  const leggi = k => { try { return JSON.parse(localStorage.getItem(k)); } catch (e) { return null; } };
  const oggi = () => new Intl.DateTimeFormat("sv-SE", { timeZone: "Europe/Rome" }).format(new Date()); // AAAA-MM-GG, ora italiana
  const fnv = s => { let h = 2166136261; for (const ch of s) h = Math.imul(h ^ ch.charCodeAt(0), 16777619) >>> 0; return h; };
  const codice = g => fnv(`zampe-coppa|${g}`).toString(36).slice(-2).toUpperCase(); // come motore/coppa.py
  const nome = k => (k || "").split("|")[0];
  const QS = new URLSearchParams(location.search);
  let C = null; // data/coppa.json

  // ---------- dati e mappa: trofei e anelli della Staffetta ----------
  const strato = L.layerGroup().addTo(map);
  const dove = k => { const [c, p] = k.split("|"); return (STATS.city || []).find(x => x.c === c && x.p === p); };
  function disegna() {
    strato.clearLayers(); if (!C) return;
    for (const k of C.anelli || []) { const x = dove(k); if (x) strato.addLayer(L.marker([x.lat, x.lng], { interactive: false, icon: L.divIcon({ className: "", iconSize: [0, 0], html: `<div class="anello" title="Staffetta: ${esc(nome(k))}"></div>` }) })); }
    for (const k of C.trofei || []) { const x = dove(k); if (x) strato.addLayer(L.marker([x.lat, x.lng], { interactive: false, icon: L.divIcon({ className: "", iconSize: [0, 0], html: `<div class="trofeo">🏆</div>` }) })); }
  }
  async function carica() {
    try { const r = await fetch("data/coppa.json?t=" + Math.floor(Date.now() / 60000)); if (r.ok) C = await r.json(); } catch (e) {}
    disegna(); if (!$("#sheet").hidden && $("#sheet").dataset.v === "coppa" && !$("#gioco")) apri();
  }
  setTimeout(carica, 1500); setInterval(carica, 5 * 60e3);
  map.on("zoomend", disegna);

  // ---------- la squadra: il comune del tuo animale, per tutto il turno ----------
  const squadra = () => { const s = leggi(K.squadra); return s && C && s.turno === C.turno ? s : null; };
  function scegli(testo) {
    const q = testo.trim().replace(/^@/, "").toLowerCase(); if (!q) return null;
    const mio = DATA.filter(d => d.k === "animale" && d.u?.toLowerCase() === q).sort((a, b) => (a.ts || "").localeCompare(b.ts || ""))[0];
    if (mio) return { k: mio.c + "|" + mio.p, u: mio.u };
    const c = (STATS.city || []).find(x => x.c.toLowerCase() === q) || (STATS.city || []).find(x => x.c.toLowerCase().startsWith(q));
    return c ? { k: c.c + "|" + c.p } : null;
  }
  function partita(k) {
    const s = (C?.sfide || []).find(x => x.a === k || x.b === k);
    if (!s) return { noi: 0, loro: 0, rivale: null, g: 0 };
    const a = s.a === k; return { noi: a ? s.pa : s.pb, loro: a ? s.pb : s.pa, rivale: a ? s.b : s.a, g: a ? s.ga : s.gb };
  }
  const chiude = () => C ? new Date(C.fine).toLocaleString("it-IT", { weekday: "long", hour: "2-digit", minute: "2-digit", timeZone: "Europe/Rome" }) : "";

  // ---------- la scheda della Coppa ----------
  function apri(pref) {
    if (typeof pref === "string") apri.pref = pref;
    const s = $("#sheet"); s.hidden = false; s.dataset.v = "coppa";
    document.querySelectorAll(".tab").forEach(t => t.setAttribute("aria-selected", "false"));
    if (!C) { s.innerHTML = `<h2>🏆 Coppa delle Zampe</h2><p class="sub">Sto caricando il campionato…</p>`; return; }
    const sq = squadra(), f = leggi(K.fatto), fattoOggi = f && f.g === oggi() && sq && f.k === sq.k;
    const prova = PROVE[provaDi(oggi())];
    let corpo = "";
    if (C.chiuso) corpo = `<p class="sub">Il turno ${C.turno} è chiuso: il verdetto è stasera alle 21 su Instagram. Lunedì a mezzanotte si riparte!</p>`;
    else if (!sq) corpo = `<h3>Per quale città giochi?</h3><p class="sub">Scrivi il tuo @ (giochi per il comune del tuo animale) oppure il nome della tua città. Resta la tua squadra fino a domenica.</p>
      <form class="cerca-mio" id="coppaForm"><input id="coppaSq" type="search" placeholder="@iltuonome o Treviso" autocomplete="off" value="${esc(nome(apri.pref || QS.get("c") || ""))}"><button class="btn" type="submit">Scegli</button></form><p class="sub" id="coppaErr"></p>`;
    else {
      const p = partita(sq.k), anello = (C.anelli || []).includes(sq.k);
      corpo = `<div class="coppa-match"><div><b>${esc(nome(sq.k))}</b><span>${p.noi}</span></div><i>vs</i><div><b>${esc(nome(p.rivale) || "in attesa")}</b><span>${p.loro}</span></div></div>
        <p class="sub">🔁 Staffetta: ${Math.min(p.g, C.staffetta)}/${C.staffetta} giocatori di ${esc(nome(sq.k))} questa settimana${anello ? " · <b>anello dorato acceso!</b> ✨" : ""}</p>
        ${fattoOggi ? risultatoHtml(sq.k, true) : `<button class="btn grande" id="coppaVia" type="button">▶ Prova di oggi: ${prova.titolo}</button><p class="sub">${prova.sotto}</p>`}
        <p class="sub piccolo">Giochi per ${esc(nome(sq.k))} fino a domenica · chiude ${chiude()}</p>`;
    }
    const albo = (C.albo || []).slice(-1)[0];
    s.innerHTML = `<h2>🏆 Coppa delle Zampe</h2><p class="sub">Turno ${C.turno}: ${fmt(C.tutte || C.sfide.length)} sfide tra comuni con un numero simile di giocatori. Un punto al giorno per chi gioca, gratis. Domenica il trofeo va sulla mappa.</p>${corpo}
      <h3>Come si gioca</h3><ol class="regole"><li>Scegli la tua città (quella del tuo animale sulla mappa).</li><li>Fai la prova del giorno: alla fine hai un codice <b>COPPA XY</b>.</li><li>Commentalo sotto l'ultimo reel di @zampeditalia: un punto alla tua città, uno al giorno.</li><li>Con 3 giocatori dello stesso comune si accende l'anello dorato 🔁.</li></ol>
      ${albo ? `<h3>Albo dei vincitori · turno ${albo.turno}</h3><ol class="list">` + albo.vincitori.slice(0, 10).map(v => `<li class="row"><span class="pos">🏆</span><span class="who">${esc(nome(v.c))}<small>${v.p} – ${v.pc} contro ${esc(nome(v.contro))}</small></span></li>`).join("") + `</ol>` : ""}`;
    const fm = $("#coppaForm"); if (fm) fm.onsubmit = e => { e.preventDefault(); const x = scegli($("#coppaSq").value);
      if (!x) { $("#coppaErr").textContent = "Non trovo né il tuo @ né la città: prima accendi il tuo animale commentando un reel con città e nome."; return; }
      salva(K.squadra, { ...x, turno: C.turno }); apri(); };
    const via = $("#coppaVia"); if (via) via.onclick = () => PROVE[provaDi(oggi())].gioca(squadra().k);
    legaRisultato(s);
  }
  window.apriCoppa = apri;
  window.coppaProva = nome => PROVE[nome].gioca(squadra().k); // per le prove automatiche da telefono

  // ---------- fine prova: codice, Instagram, cartolina ----------
  function risultatoHtml(k, gia) {
    const cod = "COPPA " + codice(oggi());
    return `<div class="coppa-fine"><b>${gia ? "Prova di oggi fatta ✅" : "Ce l'hai fatta! 🎉"}</b>
      <span>Commenta questo codice sotto l'ultimo reel: il punto va a <b>${esc(nome(k))}</b> (uno al giorno).</span>
      <button type="button" class="codice" id="coppaCod">${cod}</button>
      <a class="btn" id="coppaIg" href="${CONFIG.ig}" target="_blank" rel="noopener">Copia e commenta su Instagram</a>
      <button type="button" class="btn chiaro" id="coppaCart">📮 Condividi la cartolina «Io gioco per ${esc(nome(k))}»</button>
      <a class="link" href="${CONFIG.ig}" target="_blank" rel="noopener">➕ Segui @zampeditalia: domenica alle 21 il verdetto</a></div>`;
  }
  function legaRisultato(el) {
    const cod = el.querySelector("#coppaCod"); if (!cod) return;
    const copia = () => navigator.clipboard?.writeText(cod.textContent).catch(() => {});
    cod.onclick = copia; el.querySelector("#coppaIg").onclick = copia;
    el.querySelector("#coppaCart").onclick = () => cartolina(squadra().k);
  }
  function fatto(k) {
    salva(K.fatto, { g: oggi(), k }); // ricaricando la pagina si rivede questo codice, non una prova nuova
    $("#gioco")?.remove(); apri();
  }

  async function cartolina(k) {
    const W = 1080, H = 1350, cv = document.createElement("canvas"); cv.width = W; cv.height = H; const x = cv.getContext("2d");
    const img = new Image(); img.src = "tiles/6/34/23.jpg"; await img.decode().catch(() => {});
    x.fillStyle = "#040C24"; x.fillRect(0, 0, W, H); if (img.width) { x.globalAlpha = .55; x.drawImage(img, 0, 0, W, H); x.globalAlpha = 1; }
    const g = x.createRadialGradient(W / 2, 560, 10, W / 2, 560, 330); g.addColorStop(0, "rgba(255,230,170,1)"); g.addColorStop(.25, "rgba(255,190,90,.75)"); g.addColorStop(1, "rgba(255,160,40,0)");
    x.fillStyle = g; x.beginPath(); x.arc(W / 2, 560, 330, 0, 7); x.fill();
    x.strokeStyle = "#FFC35A"; x.lineWidth = 14; x.beginPath(); x.arc(W / 2, 560, 170, 0, 7); x.stroke();
    x.textAlign = "center"; x.fillStyle = "#FFF4DE"; x.font = "900 64px Nunito, sans-serif"; x.fillText("Io gioco per", W / 2, 170);
    x.font = `800 ${nome(k).length > 12 ? 92 : 128}px 'Bricolage Grotesque', sans-serif`; x.fillStyle = "#FFD27A"; x.fillText(nome(k), W / 2, 300);
    x.font = "900 54px Nunito, sans-serif"; x.fillStyle = "#FFF4DE"; x.fillText("🏆 Coppa delle Zampe", W / 2, 1000);
    x.font = "800 44px Nunito, sans-serif"; x.fillStyle = "#FFC35A"; x.fillText("Gioca anche tu per la tua città:", W / 2, 1110); x.fillText("zampeditalia.it · @zampeditalia", W / 2, 1180);
    const link = `${location.origin}${location.pathname}?coppa=1&c=${encodeURIComponent(k)}`;
    const testo = `Io gioco per ${nome(k)} nella Coppa delle Zampe! 🏆 Porta un punto anche tu: ${link}`;
    const blob = await new Promise(r => cv.toBlob(r, "image/png")), file = new File([blob], "io-gioco-per.png", { type: "image/png" });
    if (navigator.canShare?.({ files: [file] })) { try { await navigator.share({ files: [file], text: testo, url: link }); return; } catch (e) {} }
    const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "io-gioco-per.png"; a.click();
    navigator.clipboard?.writeText(testo).catch(() => {});
  }

  // ---------- le prove ----------
  const provaDi = g => fnv("prova|" + g) % 2 ? "luce" : "zampa"; // un giorno l'una, un giorno l'altra (stessa per tutta Italia)
  const PROVE = {
    luce: { titolo: "La Luce Misteriosa", sotto: "Due indizi su un comune: trovalo sulla mappa e toccalo.", gioca: luce },
    zampa: { titolo: "Indovina la Zampa", sotto: "Un dettaglio o una sagoma: di che animale è?", gioca: zampa },
  };
  const scheda = html => { $("#gioco")?.remove(); const d = document.createElement("div"); d.id = "gioco"; d.className = "gioco"; d.innerHTML = html; document.body.appendChild(d); return d; };

  // 1. La Luce Misteriosa: indizi veri dai dati della mappa
  function luce(k) {
    // lo stesso comune per tutta Italia e per tutto il giorno: vince il comune con l'hash più basso (non cambia se nel frattempo se ne aggiungono altri, salvo rarissimi casi)
    const g = oggi(), cand = (STATS.city || []).filter(c => c.tot >= 3);
    if (!cand.length) return fatto(k);
    const t = cand.reduce((m, c) => fnv(`luce|${g}|${c.c}|${c.p}`) < fnv(`luce|${g}|${m.c}|${m.p}`) ? c : m), primo = DATA.filter(d => d.c === t.c && d.p === t.p && d.k === "animale").sort((a, b) => (a.ts || "").localeCompare(b.ts || ""))[0];
    const razza = primo && (primo.razza_testo || primo.razza || "").replace(/_/g, " ");
    $("#sheet").hidden = true;
    let tentativi = 0;
    const el = scheda(`<b>🔦 La Luce Misteriosa</b><ol><li>È in ${esc(t.r)}, in provincia di ${esc(t.p)}.</li><li>Ha ${t.tot} luci accese${primo ? `: la prima è di <b>${esc(primo.n)}</b>${razza && !/^(cane|gatto)$/.test(razza) ? " (" + esc(razza) + ")" : ""}` : ""}.</li></ol>
      <span id="gMsg">Avvicinati e tocca il comune giusto sulla mappa.</span><button type="button" class="chiudi" aria-label="Chiudi">✕</button>`);
    el.querySelector(".chiudi").onclick = () => { window.coppaTocco = null; el.remove(); };
    map.flyToBounds(ITALY, { ...PAD(), duration: 0.6 });
    window.coppaTocco = e => {
      const p = map.latLngToContainerPoint(e.latlng); let best = null, bd = 40;
      for (const c of STATS.city || []) { const q = map.latLngToContainerPoint([c.lat, c.lng]), dd = Math.hypot(q.x - p.x, q.y - p.y) - 3 * Math.log1p(c.tot); if (dd < bd) { bd = dd; best = c; } }
      if (best && best.c === t.c && best.p === t.p) {
        window.coppaTocco = null;
        DATA.filter(d => d.c === t.c && d.p === t.p).forEach(d => { d.nato = performance.now(); }); requestAnimationFrame(loop); // il comune si illumina
        map.flyTo([t.lat, t.lng], Math.max(map.getZoom(), 10), { duration: 0.8 });
        el.innerHTML = `<b>✨ Era ${esc(t.c)}!</b><span>Il punto di oggi va alla tua squadra.</span>`;
        setTimeout(() => fatto(k), 2200);
      } else {
        tentativi++;
        const km = Math.round(map.distance(e.latlng, [t.lat, t.lng]) / 1000);
        el.querySelector("#gMsg").innerHTML = (best ? `${esc(best.c)}? No: ` : "") + `sei a ${km} km. ` + (km < 25 ? "Ci sei quasi! 🔥" : km < 80 ? "Fa caldo… 🌡️" : "Acqua… 🌊");
        if (tentativi === 3) { // aiuto: si inquadra la provincia
          const pr = (STATS.city || []).filter(c => c.p === t.p); if (pr.length) map.flyToBounds(L.latLngBounds(pr.map(c => [c.lat, c.lng])).pad(0.3), { duration: 0.8 });
        }
      }
      return true;
    };
  }

  // 2. Indovina la Zampa: sagoma o dettaglio di un disegno della mappa, tre risposte, poi si rivela. Specie diverse a rotazione.
  function zampa(k) {
    const g = oggi(), n = fnv("zampa|" + g), tipo = ["cane", "gatto", "altro"][Math.floor(n / 7) % 3];
    const ALTRI = [["coniglio", "Coniglio"], ["criceto", "Criceto"], ["tartaruga", "Tartaruga"], ["pappagallo", "Pappagallo"], ["furetto", "Furetto"], ["riccio", "Riccio"], ["cavallo", "Cavallo"], ["canarino", "Canarino"]];
    const lista = tipo === "cane" ? Object.entries(D.CANI).map(([k2, v]) => [k2, v.n]) : tipo === "gatto" ? Object.entries(D.GATTI).map(([k2, v]) => [k2, v.n]) : ALTRI;
    const uniq = lista.filter((x, i) => lista.findIndex(y => y[1] === x[1]) === i);
    const giusto = uniq[n % uniq.length], altri = uniq.filter(x => x !== giusto);
    const opz = [giusto, altri[(n >>> 5) % altri.length], altri[(n >>> 11) % altri.length]].filter((x, i, a) => a.indexOf(x) === i);
    while (opz.length < 3) opz.push(altri[(opz.length * 7 + n) % altri.length]);
    opz.sort((a, b) => fnv(a[0] + g) - fnv(b[0] + g));
    const svg = tipo === "cane" ? D.cane(giusto[0], n) : tipo === "gatto" ? D.gatto(giusto[0], n) : D.altro(giusto[0], n);
    const modo = (n >>> 3) % 2 ? "sagoma" : "dettaglio";
    $("#sheet").hidden = true;
    const el = scheda(`<b>🐾 Indovina la Zampa</b><span>${modo === "sagoma" ? "Di chi è questa sagoma?" : "Di chi è questo dettaglio?"} ${tipo === "cane" ? "È un cane." : tipo === "gatto" ? "È un gatto." : "Non è né un cane né un gatto!"}</span>
      <div class="zampa ${modo}" style="--x:${20 + (n % 50)}%;--y:${25 + ((n >>> 4) % 40)}%">${svg}</div>
      <div class="opzioni">${opz.map(o => `<button type="button" class="btn chiaro" data-k="${esc(o[0])}">${esc(o[1])}</button>`).join("")}</div><button type="button" class="chiudi" aria-label="Chiudi">✕</button>`);
    el.querySelector(".chiudi").onclick = () => el.remove();
    el.querySelectorAll(".opzioni button").forEach(b => b.onclick = () => {
      const ok = b.dataset.k === giusto[0];
      el.querySelector(".zampa").className = "zampa svelata";
      el.querySelectorAll(".opzioni button").forEach(x => { x.disabled = true; if (x.dataset.k === giusto[0]) x.classList.add("giusta"); });
      el.querySelector("span").innerHTML = ok ? `✨ Esatto: <b>${esc(giusto[1])}</b>!` : `Era <b>${esc(giusto[1])}</b>! La prova di oggi è fatta lo stesso.`;
      setTimeout(() => fatto(k), 2200);
    });
  }

  // ---------- il pulsante sulla mappa ----------
  const btn = document.createElement("button"); btn.type = "button"; btn.className = "gioca-citta"; btn.id = "giocaCitta"; btn.innerHTML = "🏆 Gioca per la tua città";
  btn.onclick = () => { if (!C) carica().then(apri); else apri(); };
  document.body.appendChild(btn);
  if (QS.has("coppa") || QS.has("c")) setTimeout(() => carica().then(apri), 1800);
})();
