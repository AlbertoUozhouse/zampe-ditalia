// Zampe d'Italia: il paese disegnato. Da vicino ogni comune diventa un paesino visto di sbieco:
// la piazza al centro con gli edifici sbloccati dalle luci, le cucce in cerchio sulle vie, alberi e lampioni intorno.
// Tutte le misure sono in "pixel del paese" (a zoom 14); app.js le scala con lo zoom.
(function () {
  const SQ = 0.58;               // schiacciamento verticale: il paese si vede di sbieco
  const RING0 = 136, STEP = 100, SLOT = 92;

  const rng = s => () => (s = (s * 16807) % 2147483647) / 2147483647;

  // posti delle cucce: anelli attorno alla piazza, il primo posto davanti al centro, poi a destra e sinistra
  function posti(n) {
    const out = []; let r = RING0, anelli = [];
    while (out.length < n) {
      const giro = [], N = 720; let L = 0, px = r, py = 0;
      for (let j = 0; j <= N; j++) { const a = Math.PI / 2 + (j / N) * 2 * Math.PI, x = r * Math.cos(a), y = r * Math.sin(a) * SQ; if (j) L += Math.hypot(x - px, (y - py) * 1.5); giro.push([L, x, y]); px = x; py = y; }
      const k = Math.max(5, Math.floor(L / SLOT)), m = Math.min(k, n - out.length);
      for (let i = 0; i < m; i++) { // dal davanti al centro, poi a destra e sinistra alternati
        const t = ((i % 2 ? 1 : -1) * Math.ceil(i / 2) / k + 1) % 1 * L, p = giro.find(g => g[0] >= t) || giro[0];
        out.push([Math.round(p[1]), Math.round(p[2])]);
      }
      anelli.push(r); r += STEP;
    }
    return { posti: out, anelli, raggio: anelli.length ? anelli[anelli.length - 1] : RING0 };
  }

  // ---------- edifici della piazza (si sbloccano con le luci, come in motore/commenti.py) ----------
  const E = {
    fontanella: () => `<g class="fontana"><ellipse cx="0" cy="6" rx="22" ry="9" fill="#2A3558"/><ellipse cx="0" cy="3" rx="22" ry="9" fill="#6F7FA8"/>
      <ellipse cx="0" cy="3" rx="17" ry="6.4" fill="#4FB4E8"/><ellipse cx="0" cy="3" rx="17" ry="6.4" fill="url(#acqua)" opacity=".8"/>
      <rect x="-3" y="-16" width="6" height="19" rx="2" fill="#8E9CC2"/><ellipse cx="0" cy="-16" rx="8" ry="3" fill="#8E9CC2"/>
      <g class="zampillo" fill="#BFEFFF"><circle cx="-4" cy="-20" r="1.6"/><circle cx="4" cy="-22" r="1.4"/><circle cx="0" cy="-26" r="1.8"/></g></g>`,
    parco: () => `<g><ellipse cx="0" cy="4" rx="30" ry="12" fill="#2E6B3C"/><ellipse cx="0" cy="4" rx="30" ry="12" fill="none" stroke="#C99A5B" stroke-width="2" stroke-dasharray="3 3"/>
      <g class="albero"><rect x="-17" y="-12" width="3" height="12" fill="#5A3417"/><circle cx="-15.5" cy="-15" r="8" fill="#3E9A52"/></g>
      <g class="albero b"><rect x="12" y="-8" width="3" height="10" fill="#5A3417"/><circle cx="13.5" cy="-11" r="6.5" fill="#56B36A"/></g>
      <path d="M-4 6 h8 m-9 -1.4 a1.4 1.4 0 1 0 0 2.8 m10 -2.8 a1.4 1.4 0 1 1 0 2.8" stroke="#FFF4DE" stroke-width="1.6" fill="none"/></g>`,
    gattile: () => `<g><rect x="-17" y="-14" width="34" height="22" fill="#B35C7A"/><path d="M-21 -13 L0 -30 L21 -13Z" fill="#6B2440"/>
      <path d="M-12 -21 l-3 -9 l7 5Z M12 -21 l3 -9 l-7 5Z" fill="#6B2440"/>
      <rect x="-5" y="-4" width="10" height="12" rx="5" fill="#FFD27A"/><circle cx="-11" cy="-6" r="2.6" fill="#FFE9A8"/><circle cx="11" cy="-6" r="2.6" fill="#FFE9A8"/></g>`,
    clinica: () => `<g><rect x="-20" y="-24" width="40" height="32" fill="#EEF2FA"/><rect x="-20" y="-28" width="40" height="5" fill="#C9D3E8"/>
      <rect x="-5" y="-20" width="10" height="3.4" fill="#E2394B"/><rect x="-1.7" y="-23.4" width="3.4" height="10" fill="#E2394B"/>
      <g fill="#FFE38A"><rect x="-16" y="-10" width="7" height="6"/><rect x="9" y="-10" width="7" height="6"/></g><rect x="-4" y="-3" width="8" height="11" fill="#7FA6D9"/></g>`,
    piazza: () => `<g><rect x="-22" y="-4" width="44" height="6" fill="#D8C9A8"/><path d="M-24 -26 L0 -36 L24 -26Z" fill="#E8DCC0"/><rect x="-22" y="-27" width="44" height="3" fill="#CDBB94"/>
      <g fill="#F1E7D0"><rect x="-18" y="-24" width="4" height="20"/><rect x="-8" y="-24" width="4" height="20"/><rect x="4" y="-24" width="4" height="20"/><rect x="14" y="-24" width="4" height="20"/></g>
      <path d="M-5 -42 l2.4 3.4 l2.6 -4.4 l2.6 4.4 l2.4 -3.4 l-1 6 h-8Z" fill="#FFC55C"/></g>`,
    ruota: () => `<g><path d="M-14 6 L0 -18 L14 6" stroke="#8E9CC2" stroke-width="2.4" fill="none"/>
      <g class="ruota"><circle cx="0" cy="-18" r="20" fill="none" stroke="#FFC55C" stroke-width="1.6"/>
      <path d="M0 -38 V2 M-20 -18 H20 M-14 -32 L14 -4 M14 -32 L-14 -4" stroke="#FFC55C" stroke-width=".9" opacity=".8"/>
      <g fill="#FF8A9A"><circle cx="0" cy="-38" r="3"/><circle cx="20" cy="-18" r="3"/><circle cx="0" cy="2" r="3"/><circle cx="-20" cy="-18" r="3"/></g></g></g>`,
  };
  const SOGLIE = [[5, "fontanella", "la fontanella"], [10, "parco", "il parco cani"], [25, "gattile", "il gattile"], [50, "clinica", "la clinica"], [100, "piazza", "la piazza dei Fondatori"], [250, "ruota", "il grande parco"]];
  const DOVE = { fontanella: [0, 2], parco: [-62, -10], gattile: [60, -14], clinica: [-38, 26], piazza: [0, -36], ruota: [44, 28] };

  const albero = (x, y, k, c) => `<g transform="translate(${x} ${y}) scale(${k})"><ellipse cx="0" cy="1" rx="7" ry="2.6" fill="#0B1530" opacity=".55"/>
    <g class="albero" style="animation-delay:${(-Math.abs(x * 7 + y * 3) % 40) / 10}s"><rect x="-1.4" y="-10" width="2.8" height="11" fill="#4A2C17"/>
    <path d="M0 -30 L9 -10 H-9Z" fill="${c}"/><path d="M0 -36 L7 -19 H-7Z" fill="${c}" opacity=".9"/></g></g>`;
  const lampione = (x, y) => `<g transform="translate(${x} ${y})"><circle cx="0" cy="-22" r="10" fill="url(#luce)" class="alone"/>
    <rect x="-.9" y="-21" width="1.8" height="21" fill="#2B3556"/><circle cx="0" cy="-22" r="2.6" fill="#FFE3A0"/></g>`;

  // il terreno del paese: un unico SVG sotto le cucce
  function suolo(nome, luci, n, seme) {
    const { anelli, raggio } = posti(n), R = raggio + 96, W = 2 * R + 40, H = Math.round(R * SQ * 2 + 120), r = rng(seme || 1);
    let s = `<svg width="${W}" height="${H}" viewBox="${-W / 2} ${-H / 2 - 30} ${W} ${H}" aria-hidden="true"><defs>
      <radialGradient id="erba"><stop offset="0" stop-color="#2B5246"/><stop offset=".72" stop-color="#20403F"/><stop offset=".92" stop-color="#1E3654" stop-opacity=".7"/><stop offset="1" stop-color="#1E3266" stop-opacity="0"/></radialGradient>
      <radialGradient id="luce"><stop offset="0" stop-color="#FFD27A" stop-opacity=".75"/><stop offset="1" stop-color="#FFD27A" stop-opacity="0"/></radialGradient>
      <radialGradient id="piaz"><stop offset="0" stop-color="#5A5F86"/><stop offset="1" stop-color="#3B4068"/></radialGradient>
      <linearGradient id="acqua" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".5"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>
      <ellipse cx="0" cy="0" rx="${R + 16}" ry="${(R + 16) * SQ}" fill="url(#erba)"/>`;
    // strade: un anello tra un giro di cucce e l'altro, e sei vie dalla piazza verso fuori
    for (let i = 0; i < 6; i++) { const a = (i / 6) * 2 * Math.PI + 0.26;
      s += `<path d="M${Math.round(96 * Math.cos(a))} ${Math.round(96 * Math.sin(a) * SQ)} L${Math.round((raggio + 50) * Math.cos(a))} ${Math.round((raggio + 50) * Math.sin(a) * SQ)}" stroke="#3E4C72" stroke-width="13" stroke-linecap="round" opacity=".75"/>`; }
    for (const a of anelli) s += `<ellipse cx="0" cy="0" rx="${a}" ry="${Math.round(a * SQ)}" fill="none" stroke="#3E4C72" stroke-width="15" opacity=".75"/>
      <ellipse cx="0" cy="0" rx="${a}" ry="${Math.round(a * SQ)}" fill="none" stroke="#FFC55C" stroke-width="1" stroke-dasharray="2 9" opacity=".35"/>`;
    s += `<ellipse cx="0" cy="0" rx="100" ry="58" fill="url(#piaz)"/><ellipse cx="0" cy="0" rx="100" ry="58" fill="none" stroke="#FFC55C" stroke-width="1.4" opacity=".4"/>
      <ellipse cx="0" cy="0" rx="78" ry="45" fill="none" stroke="#6E74A0" stroke-width="1" stroke-dasharray="4 4"/>`;
    // edifici sbloccati e il prossimo in costruzione
    const fatti = SOGLIE.filter(e => luci >= e[0]), dopo = SOGLIE.find(e => luci < e[0]);
    for (const [, k] of [...fatti].sort((a, b) => DOVE[a[1]][1] - DOVE[b[1]][1])) s += `<g transform="translate(${DOVE[k][0]} ${DOVE[k][1]})">${E[k]()}</g>`;
    if (dopo) s += `<g transform="translate(${DOVE[dopo[1]][0]} ${DOVE[dopo[1]][1]})" opacity=".55"><ellipse cx="0" cy="4" rx="22" ry="8" fill="none" stroke="#FFC55C" stroke-width="1.4" stroke-dasharray="3 3"/>
      <text y="-4" text-anchor="middle" font-size="15">🚧</text></g>`;
    // lampioni all'imbocco delle vie e un bosco tutto intorno
    for (let i = 0; i < 6; i++) { const a = (i / 6) * 2 * Math.PI + 0.26 + 0.2; s += lampione(Math.round(108 * Math.cos(a)), Math.round(108 * Math.sin(a) * SQ)); }
    const bosco = [];
    for (let a = 0; a < 2 * Math.PI; a += 34 / (R - 20)) {
      const rr = R - 26 + r() * 30; bosco.push([Math.round(rr * Math.cos(a)), Math.round(rr * Math.sin(a) * SQ), 0.75 + r() * 0.5, r() < 0.5 ? "#2F7A4A" : "#246340"]);
    }
    bosco.sort((p, q) => p[1] - q[1]).forEach(p => { if (!(p[1] > 0 && Math.abs(p[0]) < 70)) s += albero(...p); }); // davanti resta il varco con il cartello
    // il cartello d'ingresso
    const y = Math.round((R - 4) * SQ), testo = String(nome).toUpperCase(), w = Math.max(90, testo.length * 10 + 34);
    s += `<g transform="translate(0 ${y})"><rect x="-2" y="-8" width="4" height="26" fill="#4A2C17"/>
      <rect x="${-w / 2}" y="-30" width="${w}" height="26" rx="6" fill="#F3DDB0" stroke="#5E3519" stroke-width="2.4"/>
      <text y="-12" text-anchor="middle" font-family="Baloo 2, system-ui, sans-serif" font-weight="800" font-size="15" fill="#5A3417" letter-spacing=".8">${testo.replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]))}</text>
      <text y="${dopo ? 14 : 12}" text-anchor="middle" font-family="Nunito, system-ui, sans-serif" font-weight="800" font-size="11.5" fill="#FFE9B8" style="paint-order:stroke" stroke="#0B1530" stroke-width="3">${luci} ${luci === 1 ? "luce" : "luci"}${dopo ? ` · mancano ${dopo[0] - luci} per ${dopo[2]}` : ""}</text></g>`;
    return { svg: s + "</svg>", w: W, h: H, dy: 30 };
  }

  window.Paese = { posti, suolo, SQ };
})();
