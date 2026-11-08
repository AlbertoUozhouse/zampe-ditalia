// Centro Agenzia: l'ufficio visto dall'alto. Legge ../data/agenzia/ (scritti da motore/agenzia.py a ogni reel).
// Modalità operativa: solo scambi registrati davvero. Modalità dimostrativa: un esempio, sempre segnalato dalla fascia rossa.
(() => {
  const $ = s => document.querySelector(s);
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const BASE = "../data/agenzia/";
  let UFF = [], REG = [], S = null, DEMO = false;
  const ruolo = id => { for (const r of UFF) for (const p of r.postazioni) if (p.id === id) return { ...p, reparto: r.nome, rid: r.id }; return { id, ruolo: id, reparto: "" }; };
  const ora = t => t ? new Date(t).toLocaleString("it-IT", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }) : "";
  const TIPI = { proposta: "Proposta", risposta: "Risposta", correzione: "Correzione", decisione: "Decisione", nota: "Nota" };

  async function json(u) { const r = await fetch(u + "?t=" + Date.now()); if (!r.ok) throw new Error(u); return r.json(); }

  // ---------- la pianta: l'ufficio di notte visto dall'alto, stanze accese quando lavorano ----------
  const REP = { direzione: ["🎬", "#7C6CF0"], montaggio: ["✂️", "#E8795E"], copione: ["✍️", "#3B8FE0"], mappa: ["🗺️", "#1FB58F"], audio: ["🎧", "#E55A9B"],
    grafica: ["🎨", "#F2B23E"], pubblicazione: ["🚀", "#5AA9F5"], community: ["💬", "#3CCB9C"], coppa: ["🏆", "#E9A21A"], crescita: ["📈", "#35B864"],
    innovazione: ["💡", "#9B8CF7"], grafica3d: ["🧊", "#19BFC2"] };
  const PELLE = ["#F1C9A5", "#E0AC84", "#C68B62", "#9C6A45", "#F5D5B8", "#7A4E33"], CAPELLI = ["#2B2018", "#5A3A22", "#8C5A2B", "#C9A15A", "#1C1C24", "#A23E2A", "#D8D2C8", "#4A3426"];
  const h = s => [...s].reduce((a, c) => (a * 31 + c.charCodeAt(0)) >>> 0, 7);
  function pianta() {
    const col1 = innerWidth < 700, RW = 470, RH = 340, GX = 20, GY = 26, M = col1 ? 14 : 22, C = col1 ? 1 : 2, W = col1 ? RW + 2 * M : 1000,
      righe = Math.ceil(UFF.length / C), H = M * 2 + righe * RH + (righe - 1) * GY;
    const attivi = new Set((S?.scambi || []).flatMap(x => [x.da, x.a]));
    const parla = new Set((S?.scambi || []).filter(x => x.tipo === "proposta" || x.tipo === "decisione" || x.tipo === "correzione").map(x => x.da));
    let svg = `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg"><defs>
      <pattern id="parquet" width="60" height="24" patternUnits="userSpaceOnUse"><rect width="60" height="24" fill="#B98556"/><rect width="60" height="12" fill="#C4915F"/>
        <path d="M0 12H60M0 0H60M30 0V12M10 12V24M50 12V24" stroke="#9E6E44" stroke-width="1.2" opacity=".6"/></pattern>
      <pattern id="fuori" width="40" height="40" patternUnits="userSpaceOnUse"><rect width="40" height="40" fill="#161C2B"/><circle cx="8" cy="12" r="1" fill="#3A4560"/><circle cx="28" cy="30" r=".8" fill="#3A4560"/></pattern>
      <radialGradient id="luce" cx=".5" cy=".45" r=".7"><stop offset="0" stop-color="#FFE3A3" stop-opacity=".38"/><stop offset="1" stop-color="#FFE3A3" stop-opacity="0"/></radialGradient>
      <radialGradient id="lampada"><stop offset="0" stop-color="#FFE9B0" stop-opacity=".75"/><stop offset="1" stop-color="#FFE9B0" stop-opacity="0"/></radialGradient>
      <radialGradient id="schermo"><stop offset="0" stop-color="#8FDCFF" stop-opacity=".7"/><stop offset="1" stop-color="#8FDCFF" stop-opacity="0"/></radialGradient>
      <filter id="ombra" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="3" stdDeviation="3" flood-color="#000" flood-opacity=".35"/></filter></defs>
      <rect width="${W}" height="${H}" fill="url(#fuori)"/>
      ${col1 ? "" : `<rect x="${W / 2 - 9}" y="${M}" width="18" height="${H - 2 * M}" rx="4" fill="#8E2F3A" opacity=".85"/><path d="M${W / 2} ${M + 6}V${H - M - 6}" stroke="#E8A93A" stroke-width="1.5" stroke-dasharray="2 10" opacity=".7"/>`}`;
    UFF.forEach((r, i) => {
      const x = M + (i % C) * (RW + GX), y = M + Math.floor(i / C) * (RH + GY), [emo, col] = REP[r.id] || ["🏢", "#888"];
      const quanti = r.postazioni.filter(p => attivi.has(p.id)).length, acceso = quanti > 0;
      svg += `<g class="stanza${acceso ? " accesa" : ""}" data-r="${r.id}">
        <rect x="${x}" y="${y}" width="${RW}" height="${RH}" rx="10" fill="url(#parquet)"/>
        <rect x="${x + 18}" y="${y + 74}" width="${RW - 36}" height="${RH - 92}" rx="18" fill="${col}" opacity=".2"/>
        <rect x="${x + 26}" y="${y + 82}" width="${RW - 52}" height="${RH - 108}" rx="13" fill="none" stroke="${col}" stroke-opacity=".45" stroke-width="2" stroke-dasharray="1 7" stroke-linecap="round"/>
        ${acceso ? `<rect x="${x}" y="${y}" width="${RW}" height="${RH}" rx="10" fill="url(#luce)"/>` : ""}
        <rect x="${x}" y="${y}" width="${RW}" height="${RH}" rx="10" fill="none" stroke="#262D3F" stroke-width="12"/>
        ${[0.18, 0.5, 0.82].map(f => `<rect x="${x + RW * f - 34}" y="${y - 4}" width="68" height="8" rx="3" fill="${acceso ? "#FFD27A" : "#5C6A8A"}" opacity="${acceso ? .9 : .6}"/>`).join("")}
        <rect x="${x + RW - 150}" y="${y + RH - 8}" width="70" height="16" fill="#C4915F"/><path d="M${x + RW - 150} ${y + RH - 6}a70 70 0 0 1 70 -62" fill="none" stroke="#8C9BB8" stroke-width="2" stroke-dasharray="4 4" opacity=".7"/>
        <g filter="url(#ombra)"><rect x="${x + 16}" y="${y + 16}" width="${RW - 32}" height="46" rx="12" fill="#FFFBF4"/></g>
        <rect x="${x + 16}" y="${y + 16}" width="8" height="46" rx="4" fill="${col}"/>
        <text x="${x + 36}" y="${y + 47}" font-size="22">${emo}</text>
        <text class="targa" x="${x + 68}" y="${y + 47}">${esc(r.nome)}</text>
        <rect x="${x + RW - 128}" y="${y + 27}" width="98" height="24" rx="12" fill="${acceso ? col : "#C9C2B5"}"/>
        <text class="conta" x="${x + RW - 79}" y="${y + 44}" text-anchor="middle">${quanti}/10 ${acceso ? "al lavoro" : "in pausa"}</text>
        <g transform="translate(${x + RW - 34} ${y + RH - 34})"><circle r="15" fill="#8B5A3C"/><circle r="11" fill="#5C3A26"/>
          <circle cx="-7" cy="-6" r="9" fill="#3E9B57"/><circle cx="7" cy="-4" r="8" fill="#56B86C"/><circle cx="0" cy="6" r="8" fill="#2F8A4A"/><circle cx="2" cy="-1" r="5" fill="#7BD08A"/></g>
        <g transform="translate(${x + 36} ${y + RH - 34})"><rect x="-14" y="-14" width="28" height="28" rx="5" fill="#3B4255"/><rect x="-9" y="-9" width="18" height="12" rx="2" fill="#20263A"/>
          <circle cx="0" cy="8" r="3" fill="${acceso ? "#E8A93A" : "#666"}"/><text x="0" y="1" text-anchor="middle" font-size="9">☕</text></g>
        ${acceso ? "" : `<rect x="${x}" y="${y}" width="${RW}" height="${RH}" rx="10" fill="#0E1322" opacity=".42" pointer-events="none"/>`}</g>`;
      r.postazioni.forEach((p, k) => {
        const px = x + 40 + (k % 5) * 84, py = y + 96 + Math.floor(k / 5) * 112, on = attivi.has(p.id), hh = h(p.id);
        const tipo = p.id === "direzione-1" ? "openai" : p.id === "montaggio-1" ? "claude" : "";
        const maglia = tipo === "openai" ? "#10A37F" : tipo === "claude" ? "#D97757" : on ? col : "#8B92A3", cx = px + 32;
        svg += `<g class="post${on ? " attivo" : ""}" data-p="${p.id}">
          ${on ? `<circle cx="${cx}" cy="${py + 8}" r="44" fill="url(#lampada)" opacity=".55"/>` : ""}
          <g filter="url(#ombra)"><rect x="${px}" y="${py}" width="64" height="34" rx="6" fill="#E3C49B"/></g>
          <rect x="${px}" y="${py}" width="64" height="5" rx="3" fill="#CFA977"/>
          ${on ? `<ellipse cx="${cx}" cy="${py + 16}" rx="26" ry="14" fill="url(#schermo)"/>` : ""}
          <rect x="${px + 14}" y="${py + 6}" width="36" height="10" rx="2" fill="${on ? "#9BE2FF" : "#2B3140"}" stroke="#1E2430" stroke-width="2"/>
          ${on ? `<path class="righe" d="M${px + 18} ${py + 10}h14M${px + 18} ${py + 13}h22" stroke="#2E5AA8" stroke-width="1.4" style="animation-delay:-${hh % 30 / 10}s"/>` : ""}
          <rect x="${px + 20}" y="${py + 20}" width="24" height="6" rx="2" fill="#F7F3EC"/>
          <circle cx="${px + 54}" cy="${py + 24}" r="4" fill="${["#E55A5A", "#5AA9F5", "#F2B23E", "#FFFFFF"][hh % 4]}" stroke="#1E2430" stroke-width="1"/>
          <circle cx="${cx}" cy="${py + 58}" r="19" fill="#3B4255"/>
          <ellipse cx="${cx}" cy="${py + 54}" rx="19" ry="11" fill="${maglia}"/>
          <circle cx="${cx}" cy="${py + 50}" r="9.5" fill="${PELLE[hh % PELLE.length]}"/>
          <path d="M${cx - 9.5} ${py + 51}a9.5 9.5 0 0 1 19 0a9.5 6 0 0 0 -19 0" fill="${CAPELLI[(hh >> 3) % CAPELLI.length]}"/>
          ${tipo ? `<circle cx="${cx}" cy="${py + 52}" r="25" fill="none" stroke="${maglia}" stroke-width="3" class="aura"/><rect x="${cx - 26}" y="${py + 76}" width="52" height="15" rx="7" fill="${maglia}"/>
            <text class="nome-ia" x="${cx}" y="${py + 87}" text-anchor="middle">${tipo === "openai" ? "OpenAI" : "Claude"}</text>` : `<text class="num" x="${cx}" y="${py + 90}" text-anchor="middle">${k + 1}</text>`}
          ${on && parla.has(p.id) ? `<g class="fumetto" style="animation-delay:-${(hh % 70) / 10}s"><path d="M${cx + 12} ${py + 30}h26a6 6 0 0 1 6 6v10a6 6 0 0 1 -6 6h-18l-6 6v-6h-2a6 6 0 0 1 -6 -6v-10a6 6 0 0 1 6 -6z" fill="#FFFBF4" stroke="#1E2430" stroke-width="1.5"/>
            <circle cx="${cx + 21}" cy="${py + 41}" r="1.8" fill="#1E2430"/><circle cx="${cx + 27}" cy="${py + 41}" r="1.8" fill="#1E2430"/><circle cx="${cx + 33}" cy="${py + 41}" r="1.8" fill="#1E2430"/></g>` : ""}</g>`;
      });
    });
    $("#pianta").innerHTML = svg + "</svg>";
    $("#pianta").querySelectorAll(".post").forEach(g => g.onclick = e => { e.stopPropagation(); agente(g.dataset.p); });
    $("#pianta").querySelectorAll(".stanza").forEach(g => g.onclick = () => reparto(g.dataset.r));
  }

  // ---------- pannelli ----------
  const voce = x => `<div class="voce ${x.tipo}"><b>${TIPI[x.tipo] || x.tipo} · ${esc(ruolo(x.da).ruolo)} → ${esc(ruolo(x.a).ruolo)} · ${ora(x.t)}</b><p>${esc(x.testo)}</p>${
    x.dati?.difetti?.length ? `<ul class="difetti">${x.dati.difetti.map(d => `<li><b>${esc(d.secondo)} s</b> · ${esc(d.area || "")}: ${esc(d.problema)} → <i>${esc(d.correzione)}</i></li>`).join("")}</ul>` : ""}${
    x.dati?.azioni?.length ? `<ul class="difetti">${x.dati.azioni.map(a => `<li>${esc(JSON.stringify(a))}</li>`).join("")}</ul>` : ""}</div>`;
  function apri(html) { const p = $("#pannello"); p.hidden = false; p.innerHTML = `<button class="chiudi" type="button" aria-label="Chiudi">✕</button>` + html; p.querySelector(".chiudi").onclick = () => p.hidden = true; }
  function agente(id) {
    const r = ruolo(id), miei = (S?.scambi || []).filter(x => x.da === id || x.a === id);
    const ultimo = miei.filter(x => x.da === id).slice(-1)[0], con = [...new Set(miei.map(x => x.da === id ? x.a : x.da))].map(c => ruolo(c).ruolo);
    const dec = (S?.scambi || []).filter(x => x.tipo === "decisione" && (x.da === id || x.a === id || ruolo(x.da).rid === r.rid)).slice(-1)[0];
    apri(`<h2>${esc(r.ruolo)}</h2><p class="chi">${esc(r.reparto)} · postazione ${esc(id)}${id === "direzione-1" ? " · agente OpenAI" : id === "montaggio-1" ? " · Claude" : ""}</p>
      ${miei.length ? `<h3>Sta facendo</h3>${ultimo ? voce(ultimo) : `<p class="vuoto">Ascolta: riceve materiale da ${esc(con.join(", "))}.</p>`}
        <h3>Parla con</h3><p>${esc(con.join(", ") || "nessuno")}</p><h3>Decisione</h3>${dec ? voce(dec) : `<p class="vuoto">Nessuna decisione ancora.</p>`}
        <h3>Tutti i suoi scambi</h3>${miei.map(voce).join("")}`
        : `<p class="vuoto">In attesa di un compito: questa postazione si accende quando il flusso del reel le assegna un lavoro preciso.</p>`}`);
  }
  function reparto(rid) {
    const r = UFF.find(x => x.id === rid), ids = new Set(r.postazioni.map(p => p.id)), sc = (S?.scambi || []).filter(x => ids.has(x.da) || ids.has(x.a));
    apri(`<h2>${esc(r.nome)}</h2><p class="chi">10 postazioni · ${sc.length} scambi in questa sessione</p>
      <ol>${r.postazioni.map(p => `<li><a href="#" data-p="${p.id}">${esc(p.ruolo)}</a></li>`).join("")}</ol>${sc.length ? `<h3>Scambi</h3>${sc.map(voce).join("")}` : `<p class="vuoto">Nessun compito in questa sessione.</p>`}`);
    $("#pannello").querySelectorAll("a[data-p]").forEach(a => a.onclick = e => { e.preventDefault(); agente(a.dataset.p); });
  }
  function sessione() {
    if (!S) return;
    const v = S.versioni || [], v1 = v[0], v2 = v[1];
    let pd = "";
    if (v1) {
      const sec = f => f.match(/s(\d+\.\d)/)?.[1];
      const righe = v1.fotogrammi.map(f => [sec(f), f, v2?.fotogrammi.find(g => sec(g) === sec(f))]);
      pd = `<h3>${v2 ? "Prima e dopo" : "Fotogrammi"}</h3><div class="versioni"><span></span><span>Versione 1</span><span>${v2 ? "Versione 2" : ""}</span>${righe.map(([s, a, b]) =>
        `<span class="s">${s} s</span><img loading="lazy" src="${a.startsWith("http") ? a : "./" + a}" alt="secondo ${s}, versione 1">${b ? `<img loading="lazy" src="${b.startsWith("http") ? b : "./" + b}" alt="secondo ${s}, versione 2">` : "<span></span>"}`).join("")}</div>`;
    }
    apri(`<h2>Reel ${esc(S.id)}</h2><p class="chi">${esc(S.formato)} · ${esc(S.stato)}${S.direttore_modello ? " · Direttore: " + esc(S.direttore_modello) : ""}${S.modalita === "dimostrativa" ? " · SESSIONE DIMOSTRATIVA" : ""}</p>
      ${(S.scambi || []).map(voce).join("") || `<p class="vuoto">Nessuno scambio.</p>`}${pd}`);
  }

  // ---------- caricamento ----------
  async function carica() {
    UFF = await json(BASE + "ufficio.json").catch(() => []);
    REG = DEMO ? [] : await json(BASE + "registro.json").catch(() => []);
    const lista = DEMO ? [{ id: "demo", formato: "esempio", stato: "dimostrativa" }] : REG.filter(x => x.modalita !== "dimostrativa").slice().reverse();
    $("#sess").innerHTML = lista.length ? lista.map(x => `<option value="${esc(x.id)}">${esc(x.id)} · ${esc(x.stato)}</option>`).join("") : `<option>Nessun reel registrato ancora</option>`;
    $("#demoBanner").hidden = !DEMO;
    await scegli(lista[0]?.id);
  }
  async function scegli(id) {
    S = !id ? null : DEMO ? await json(BASE + "demo.json").catch(() => null) : await json(BASE + "sessioni/" + id + ".json").catch(() => null);
    const st = $("#stato"); st.textContent = S ? (S.modalita === "dimostrativa" ? "dimostrativa" : S.stato) : "—";
    st.className = "stato" + (S?.stato === "approvato" ? " ok" : S?.stato === "bozza" ? " ko" : "");
    pianta();
  }
  let largo = innerWidth < 700; addEventListener("resize", () => { if ((innerWidth < 700) !== largo) { largo = !largo; pianta(); } });
  $("#sess").onchange = e => scegli(e.target.value);
  $("#apriSess").onclick = sessione;
  // Cantieri dell'Innovazione: ogni idea scelta va online entro 48 ore (docs/data/agenzia/cantieri.json)
  $("#apriCan").onclick = async () => {
    const C = await json(BASE + "cantieri.json").catch(() => ({})), T = { gioco: "🎮 Gioco", reel: "🎬 Reel", realismo: "🌄 Realismo" };
    apri(`<h2>Cantieri Innovazione</h2><p class="chi">Ogni idea scelta va online entro 48 ore; finché il cantiere è aperto la traccia non sceglie idee nuove.</p>${Object.entries(C).map(([k, v]) =>
      `<div class="voce decisione"><b>${T[k] || esc(k)} · ${esc(v.stato)}${v.in_ritardo ? " · IN RITARDO" : ""} · aperto ${esc(v.aperto)} · scadenza ${esc(v.scadenza)}</b><p><b>${esc(v.idea)}</b>: ${esc(v.come_funziona)}</p>${
        v.nota ? `<p>${esc(v.nota)}</p>` : ""}${(v.passi_proposti || []).length ? `<ul class="difetti">${v.passi_proposti.map(x => `<li>${esc(x.ruolo)}: ${esc(x.passo)}</li>`).join("")}</ul>` : ""}</div>`).join("") || `<p class="vuoto">Nessun cantiere aperto.</p>`}`);
  };
  $("#mOp").onclick = () => { DEMO = false; $("#mOp").setAttribute("aria-selected", "true"); $("#mDemo").setAttribute("aria-selected", "false"); carica(); };
  $("#mDemo").onclick = () => { DEMO = true; $("#mDemo").setAttribute("aria-selected", "true"); $("#mOp").setAttribute("aria-selected", "false"); carica(); };
  carica();
})();
