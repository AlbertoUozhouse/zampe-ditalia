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

  // ---------- la pianta: 10 stanze in due colonne, 10 scrivanie ciascuna ----------
  function pianta() {
    const W = 1000, RW = 480, RH = 330, G = 20, righe = Math.ceil(UFF.length / 2), H = righe * (RH + G) + G;
    const attivi = new Set((S?.scambi || []).flatMap(x => [x.da, x.a]));
    let svg = `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg"><rect width="${W}" height="${H}" fill="#CFC6B5"/>`;
    UFF.forEach((r, i) => {
      const x = G + (i % 2) * (RW + G), y = G + Math.floor(i / 2) * (RH + G);
      svg += `<g class="stanza" data-r="${r.id}"><rect class="pav" x="${x}" y="${y}" width="${RW}" height="${RH}" rx="6"/>
        <path class="muri" d="M${x} ${y + 60} V${y} H${x + RW} V${y + RH} H${x + 200} M${x + 270} ${y + RH} H${x} V${y + 110}"/>
        <rect x="${x + 12}" y="${y + 12}" width="${RW - 24}" height="40" rx="8" fill="rgba(255,255,255,.75)"/>
        <text class="targa" x="${x + 24}" y="${y + 40}">${esc(r.nome)}</text>
        <text class="sotto" x="${x + RW - 24}" y="${y + 40}" text-anchor="end">${r.postazioni.filter(p => attivi.has(p.id)).length}/10 al lavoro</text>
        <circle cx="${x + RW - 30}" cy="${y + RH - 30}" r="16" fill="#5E9C63"/><circle cx="${x + RW - 36}" cy="${y + RH - 36}" r="9" fill="#78B97D"/></g>`;
      r.postazioni.forEach((p, k) => {
        const px = x + 30 + (k % 5) * 88, py = y + 80 + Math.floor(k / 5) * 120, on = attivi.has(p.id);
        const tipo = p.id === "direzione-1" ? " openai" : p.id === "montaggio-1" ? " claude" : "";
        svg += `<g class="post${on ? " attivo" : ""}${tipo}" data-p="${p.id}">
          <rect class="scrivania" x="${px}" y="${py}" width="72" height="40" rx="5"/><rect class="schermo" x="${px + 22}" y="${py + 5}" width="28" height="8" rx="2"/>
          <circle class="sedia" cx="${px + 36}" cy="${py + 62}" r="17"/>${on ? `<circle class="alone" cx="${px + 36}" cy="${py + 60}" r="22"/>` : ""}
          <ellipse class="corpo" cx="${px + 36}" cy="${py + 62}" rx="15" ry="10"/><circle class="testa-p" cx="${px + 36}" cy="${py + 58}" r="8"/>
          <text x="${px + 36}" y="${py + 98}" text-anchor="middle">${k + 1}</text></g>`;
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
  $("#sess").onchange = e => scegli(e.target.value);
  $("#apriSess").onclick = sessione;
  $("#mOp").onclick = () => { DEMO = false; $("#mOp").setAttribute("aria-selected", "true"); $("#mDemo").setAttribute("aria-selected", "false"); carica(); };
  $("#mDemo").onclick = () => { DEMO = true; $("#mDemo").setAttribute("aria-selected", "true"); $("#mOp").setAttribute("aria-selected", "false"); carica(); };
  carica();
})();
