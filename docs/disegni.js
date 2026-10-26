// Fabbrica di cani e gatti: ogni animale, visto da vicino, è disegnato secondo la sua razza.
// Le varianti (tono del pelo, collare, lingua, posa della coda) nascono da un seme ricavato dall'id,
// così lo stesso animale è sempre uguale e diecimila animali sono tutti diversi.
(function () {
  const rng = seed => { let s = (seed % 2147483646) + 1; return () => (s = (s * 16807) % 2147483647) / 2147483647; };
  const hash = str => { let h = 2166136261; for (const ch of String(str)) { h ^= ch.charCodeAt(0); h = Math.imul(h, 16777619); } return h >>> 0; };

  // Schiarisce/scurisce un colore esadecimale di una quantità tra -1 e 1.
  const shade = (hex, k) => {
    const n = parseInt(hex.slice(1), 16), c = [n >> 16, (n >> 8) & 255, n & 255];
    const t = k < 0 ? 0 : 255, a = Math.abs(k);
    return "#" + c.map(v => Math.round(v + (t - v) * a).toString(16).padStart(2, "0")).join("");
  };

  // ---------- razze ----------
  // orecchie: flop (pendenti), long (lunghe), up (dritte), big (grandi dritte), bat (a pipistrello)
  const CANI = {
    golden:              { n: "Golden retriever",  fur: "#E2A350", ear: "flop", earC: "#C2802F", muz: "#F2CC8F" },
    labrador_nero:       { n: "Labrador nero",     fur: "#2B2420", ear: "flop", earC: "#1A1512", muz: "#3B322C" },
    labrador_miele:      { n: "Labrador miele",    fur: "#E8C27A", ear: "flop", earC: "#D2A65C", muz: "#F3DAA6" },
    labrador_cioccolato: { n: "Labrador cioccolato", fur: "#6B4027", ear: "flop", earC: "#53301C", muz: "#7E5034" },
    meticcio:            { n: "Meticcio",          fur: "#B98450", ear: "semi", earC: "#8E5F33", muz: "#E3C29A", mix: true },
    pastore_tedesco:     { n: "Pastore tedesco",   fur: "#C98A45", ear: "up",   earC: "#2A1D14", muz: "#D9A466", mask: "#2A1D14", cap: "#2A1D14" },
    border_collie:       { n: "Border collie",     fur: "#1F1A18", ear: "semi", earC: "#1F1A18", muz: "#F4EFE6", blaze: "#F4EFE6" },
    husky:               { n: "Husky",             fur: "#7D8796", ear: "up",   earC: "#5F6876", muz: "#F4F2EE", face: "#F4F2EE", eye: "#7FD3FF" },
    beagle:              { n: "Beagle",            fur: "#C47A35", ear: "long", earC: "#7A4520", muz: "#F4EFE6", blaze: "#F4EFE6" },
    jack_russell:        { n: "Jack Russell",      fur: "#F4EFE6", ear: "semi", earC: "#B8763A", muz: "#F4EFE6", patch: "#B8763A" },
    bassotto:            { n: "Bassotto",          fur: "#8A4B22", ear: "long", earC: "#6A3618", muz: "#9C5A2C" },
    chihuahua:           { n: "Chihuahua",         fur: "#D9A86A", ear: "big",  earC: "#C48E50", muz: "#EAC796" },
    barboncino:          { n: "Barboncino",        fur: "#F1E6D2", ear: "long", earC: "#E2D3B8", muz: "#F7EFE2", curly: true },
    bulldog_francese:    { n: "Bulldog francese",  fur: "#CDBA9C", ear: "bat",  earC: "#B49F80", muz: "#E2D5BF", mask: "#3A2F27", flat: true },
    cavalier:            { n: "Cavalier King",     fur: "#F4EFE6", ear: "long", earC: "#B5582A", muz: "#F4EFE6", patch: "#B5582A", blaze: "#F4EFE6" },
    shih_tzu:            { n: "Shih tzu",          fur: "#E9DCC4", ear: "long", earC: "#8A6A4A", muz: "#F4ECDD", patch: "#8A6A4A", curly: true, flat: true },
    amstaff:             { n: "Amstaff",           fur: "#6E7480", ear: "semi", earC: "#5A606B", muz: "#7E8490", blaze: "#EDEBE6" },
    samoiedo:            { n: "Samoiedo",          fur: "#F6F3EC", ear: "up",   earC: "#E9E3D6", muz: "#FFFFFF", curly: true },
    volpino:             { n: "Volpino",           fur: "#E8913A", ear: "up",   earC: "#C9742A", muz: "#F6D2A6", curly: true },
    boxer:               { n: "Boxer",             fur: "#C27A3E", ear: "semi", earC: "#9A5B2A", muz: "#D69A62", mask: "#2A1D14", flat: true, blaze: "#F4EFE6" },
    carlino:             { n: "Carlino",           fur: "#D9BE94", ear: "semi", earC: "#2A2220", muz: "#E3CDA8", mask: "#2A2220", flat: true },
    rottweiler:          { n: "Rottweiler",        fur: "#1E1A18", ear: "flop", earC: "#141110", muz: "#9A5B2A" },
    cocker:              { n: "Cocker",            fur: "#D9A24E", ear: "long", earC: "#B98232", muz: "#E8BE7A", curly: true },
    australian:          { n: "Australian shepherd", fur: "#8E949C", ear: "semi", earC: "#3A3634", muz: "#F4EFE6", blaze: "#F4EFE6", patch: "#3A3634", eye: "#7FD3FF" },
    corgi:               { n: "Corgi",             fur: "#E39A4C", ear: "big",  earC: "#C97E36", muz: "#F4EFE6", blaze: "#F4EFE6" },
    shiba:               { n: "Shiba / Akita",     fur: "#E0904A", ear: "up",   earC: "#C47534", muz: "#F6E6CF", face: "#F6E6CF" },
    maltese:             { n: "Maltese",           fur: "#FBF8F2", ear: "long", earC: "#EFE9DD", muz: "#FFFFFF", curly: true },
  };
  // motivo: tabby (striato), points (estremità scure), bicolor, solid
  const GATTI = {
    europeo:    { n: "Europeo tigrato", fur: "#9A7B55", pat: "tabby", stripe: "#5E4A31" },
    nero:       { n: "Gatto nero",      fur: "#1E1C22", pat: "solid" },
    rosso:      { n: "Gatto rosso",     fur: "#E08A3C", pat: "tabby", stripe: "#B8652A" },
    bianco:     { n: "Gatto bianco",    fur: "#F3EFE7", pat: "solid", eye: "#8FD1FF" },
    bicolore:   { n: "Bicolore",        fur: "#232025", pat: "bicolor", white: "#F3EFE7" },
    siamese:    { n: "Siamese",         fur: "#EADBC2", pat: "points", point: "#5A4232", eye: "#7FC8FF" },
    persiano:   { n: "Persiano",        fur: "#E8DCC8", pat: "solid", fluffy: true, eye: "#FFB347" },
    maine_coon: { n: "Maine coon",      fur: "#7A5A3A", pat: "tabby", stripe: "#4A3522", fluffy: true, tufts: true },
    british:    { n: "British shorthair", fur: "#8C96A3", pat: "solid", eye: "#FFB347", round: true },
    ragdoll:    { n: "Ragdoll",         fur: "#F1E8DA", pat: "points", point: "#8A7766", fluffy: true, eye: "#7FC8FF" },
    sphynx:     { n: "Sphynx",          fur: "#E5B9A8", pat: "solid", bigEars: true },
  };

  // Parole che i giocatori scrivono nei commenti → chiave della razza.
  const SINONIMI = [
    [/golden|retriever/, "golden"], [/labrador.*(nero|black)|lab.*nero/, "labrador_nero"],
    [/labrador.*(cioccolat|marrone|choco)/, "labrador_cioccolato"], [/labrador|^lab\b/, "labrador_miele"],
    [/pastore tedesco|tedesco|german|lupo/, "pastore_tedesco"], [/border|collie/, "border_collie"],
    [/husky|siberian/, "husky"], [/beagle/, "beagle"], [/jack|russel/, "jack_russell"],
    [/bassott|dachs|salsicc/, "bassotto"], [/chihuahua|chiuaua|chihuaua/, "chihuahua"],
    [/barbon|poodle|toy/, "barboncino"], [/bulldog|frenchie|bouledogue/, "bulldog_francese"],
    [/cavalier|king charles/, "cavalier"], [/maltes/, "maltese"], [/shih|tzu|yorkshire|yorkie/, "shih_tzu"],
    [/samoied|samoyed/, "samoiedo"], [/volpin|pomer|spitz/, "volpino"], [/boxer/, "boxer"], [/carlin|pug/, "carlino"],
    [/rottweil|rotweil/, "rottweiler"], [/cocker|spaniel/, "cocker"], [/australian|aussie|pastore australiano/, "australian"],
    [/corgi/, "corgi"], [/shiba|akita/, "shiba"],
    [/amstaff|pitbull|pit bull|staffordshire|staffy/, "amstaff"], [/meticc|incrocio|bastardin|mix/, "meticcio"],
    [/siames/, "siamese"], [/persian/, "persiano"], [/maine|coon/, "maine_coon"], [/british|certosin/, "british"],
    [/ragdoll/, "ragdoll"], [/sphynx|sfinge|nudo/, "sphynx"], [/bicolor|bianco e nero|bianconer|tuxedo/, "bicolore"],
    [/gatto nero|nera?$/, "nero"], [/rosso|rossa|arancion|fulv/, "rosso"], [/bianc/, "bianco"],
    [/tigrat|soriano|europeo|grigio/, "europeo"],
  ];
  function razza(testo, tipo) {
    const t = String(testo || "").toLowerCase().trim();
    for (const [re, k] of SINONIMI) if (re.test(t) && (tipo === "gatto" ? GATTI[k] : CANI[k])) return k;
    return tipo === "gatto" ? "europeo" : "meticcio";
  }

  // ---------- il cane nella cuccia ----------
  const EARS = {
    flop: (c) => `<ellipse cx="24.6" cy="44" rx="2.7" ry="5" fill="${c}" transform="rotate(16 24.6 44)"/><ellipse cx="39.4" cy="44" rx="2.7" ry="5" fill="${c}" transform="rotate(-16 39.4 44)"/>`,
    long: (c) => `<ellipse cx="24.4" cy="46" rx="2.8" ry="6.6" fill="${c}" transform="rotate(10 24.4 46)"/><ellipse cx="39.6" cy="46" rx="2.8" ry="6.6" fill="${c}" transform="rotate(-10 39.6 46)"/>`,
    up:   (c) => `<path d="M25 40 L25.6 31.5 L30.2 37Z M39 40 L38.4 31.5 L33.8 37Z" fill="${c}" stroke="${c}" stroke-width="1" stroke-linejoin="round"/>`,
    semi: (c) => `<path d="M25 40 L25.4 34 L28.6 34.6 L30.2 37.4Z M39 40 L38.6 34 L35.4 34.6 L33.8 37.4Z" fill="${c}" stroke="${c}" stroke-width="1" stroke-linejoin="round"/>`,
    big:  (c) => `<path d="M26 40 L21.6 31 L30.4 36.6Z M38 40 L42.4 31 L33.6 36.6Z" fill="${c}" stroke="${c}" stroke-width="1" stroke-linejoin="round"/><path d="M26 38.6 L23.6 33.6 L28.6 36.6Z M38 38.6 L40.4 33.6 L35.4 36.6Z" fill="#E9A38F" opacity=".7"/>`,
    bat:  (c) => `<path d="M25.4 40 Q21.8 31 26.4 31.4 Q29.4 33 30.6 37Z M38.6 40 Q42.2 31 37.6 31.4 Q34.6 33 33.4 37Z" fill="${c}"/><path d="M26 38 Q24.4 33.4 26.8 33.6 Q28.4 34.6 29.2 37Z M38 38 Q39.6 33.4 37.2 33.6 Q35.6 34.6 34.8 37Z" fill="#E9A38F" opacity=".75"/>`,
  };
  const COLLARI = ["#E2553F", "#3FA7E2", "#5BC27A", "#B06BE0", "#FFC55C", "#F07FB1"];

  function cane(key, seed) {
    const R = rng(seed), b = CANI[key] || CANI.meticcio;
    let fur = b.fur, earC = b.earC, muz = b.muz;
    if (b.mix) { const tones = ["#B98450", "#8A5A35", "#D9B07A", "#3C312B", "#E7D9C2", "#A0693A"]; fur = tones[Math.floor(R() * tones.length)]; earC = shade(fur, -0.25); muz = shade(fur, 0.45); }
    const j = (R() - 0.5) * 0.12; fur = shade(fur, j); earC = shade(earC, j);
    const eye = b.eye || "#1E120A", collar = COLLARI[Math.floor(R() * COLLARI.length)];
    const tongue = R() < 0.45, earKind = b.mix ? ["flop", "semi", "up"][Math.floor(R() * 3)] : b.ear;
    const headRy = b.flat ? 7 : 7.6, door = `M21 57 V41 A11 11 0 0 1 43 41 V57Z`;
    const id = "c" + seed.toString(36);
    return `<svg width="80" height="75" viewBox="0 0 64 60" aria-hidden="true">
<defs><radialGradient id="${id}" cx=".5" cy=".7" r=".8"><stop offset="0" stop-color="#FFE0A0"/><stop offset=".5" stop-color="#F09A3A"/><stop offset="1" stop-color="#5A2A0C"/></radialGradient></defs>
<ellipse cx="32" cy="57.5" rx="26" ry="3" fill="#FFB347" opacity=".35"/>
<rect x="10" y="26" width="44" height="31" rx="1.5" fill="#8A5228"/>
<path d="M10 33.5H54M10 41H54M10 48.5H54" stroke="#5E3519" stroke-width="1" opacity=".55"/>
<path d="M4 29 L32 6.5 L60 29 L56.5 31.5 L32 11.6 L7.5 31.5Z" fill="#4A2A14"/>
<path d="M4 29 L32 6.5 L60 29" fill="none" stroke="#FFC55C" stroke-width="1.4" stroke-linejoin="round" opacity=".7"/>
<path d="${door}" fill="url(#${id})"/>
${EARS[earKind](earC)}
<ellipse cx="32" cy="45" rx="8" ry="${headRy}" fill="${fur}"/>
${b.cap ? `<path d="M24.6 42 Q32 34.8 39.4 42 Q32 39.6 24.6 42Z" fill="${b.cap}" opacity=".85"/>` : ""}
${b.face ? `<path d="M25 46 Q26 41.2 29.6 42.6 L32 40 L34.4 42.6 Q38 41.2 39 46 Q38 52 32 52.4 Q26 52 25 46Z" fill="${b.face}"/>` : ""}
${b.patch ? `<ellipse cx="${R() < 0.5 ? 28.4 : 35.6}" cy="41.6" rx="3.4" ry="3.6" fill="${b.patch}" opacity=".95"/>` : ""}
${b.blaze ? `<path d="M31 37.6 h2 v6 h-2z" fill="${b.blaze}"/>` : ""}
${b.curly ? `<g fill="${shade(fur, 0.12)}"><circle cx="28" cy="38.6" r="2.4"/><circle cx="32" cy="37.4" r="2.6"/><circle cx="36" cy="38.6" r="2.4"/></g>` : ""}
<ellipse cx="32" cy="${b.flat ? 48 : 48.8}" rx="${b.flat ? 5 : 4.6}" ry="3.4" fill="${muz}"/>
${b.mask ? `<ellipse cx="32" cy="${b.flat ? 47.6 : 48.4}" rx="3.4" ry="2.4" fill="${b.mask}" opacity=".9"/>` : ""}
<ellipse cx="32" cy="${b.flat ? 46.6 : 47}" rx="1.7" ry="1.15" fill="#1A100A"/>
${tongue ? `<path d="M30.8 51 Q32 54.6 33.2 51Z" fill="#E8707E"/>` : `<path d="M30 50.6 Q32 51.8 34 50.6" stroke="#1A100A" stroke-width=".7" fill="none" stroke-linecap="round"/>`}
<circle cx="28.8" cy="43.2" r="1.25" fill="${eye}"/><circle cx="35.2" cy="43.2" r="1.25" fill="${eye}"/>
<circle cx="29.2" cy="42.8" r=".42" fill="#fff"/><circle cx="35.6" cy="42.8" r=".42" fill="#fff"/>
<path d="M25.4 52.6 Q32 55.4 38.6 52.6" stroke="${collar}" stroke-width="1.8" fill="none" stroke-linecap="round"/>
<path d="${door}" fill="none" stroke="#5E3519" stroke-width="2.2"/>
</svg>`;
  }

  // ---------- il gatto sul tetto ----------
  function gatto(key, seed) {
    const R = rng(seed), b = GATTI[key] || GATTI.europeo;
    const fur = shade(b.fur, (R() - 0.5) * 0.12), eye = b.eye || "#CFE36B";
    const flip = R() < 0.5 ? 1 : -1, tail = 6 + R() * 6;
    const head = b.fluffy ? 7.6 : b.round ? 7.4 : 6.6;
    const pt = b.point, wh = b.white, st = b.stripe;
    const earC = pt || fur, ear = b.bigEars ? 6.5 : 4.4;
    const id = "g" + seed.toString(36);
    return `<svg width="80" height="75" viewBox="0 0 64 60" aria-hidden="true">
<defs><radialGradient id="${id}"><stop offset="0" stop-color="${eye}" stop-opacity=".9"/><stop offset="1" stop-color="${eye}" stop-opacity="0"/></radialGradient></defs>
<path d="M0 60 V48 L32 38 L64 48 V60Z" fill="#162650"/>
<path d="M0 48 L32 38 L64 48" fill="none" stroke="#5577C9" stroke-width="1.2" opacity=".7"/>
<path d="M8 52 L24 47 M8 56 L30 49.5 M40 49.5 L60 56 M42 47 L58 52" stroke="#0E1A3A" stroke-width="1.1" opacity=".8"/>
<rect x="47" y="34" width="7" height="12" fill="#1E3266"/><rect x="46" y="32.6" width="9" height="2.4" fill="#2A4180"/>
<g transform="translate(32 0) scale(${flip} 1) translate(-32 0)">
<path d="M37 37 Q${44 + tail} 36 ${42 + tail} ${26 - tail / 3}" stroke="${pt || fur}" stroke-width="${b.fluffy ? 4 : 2.8}" fill="none" stroke-linecap="round"/>
${st ? `<path d="M${40 + tail * 0.5} 36 l1.6 -2.4 M${42 + tail * 0.8} 33 l1.8 -1.6" stroke="${st}" stroke-width="1.4"/>` : ""}
</g>
<ellipse cx="32" cy="32" rx="${b.fluffy ? 9.4 : 8.2}" ry="8.6" fill="${fur}"/>
${wh ? `<ellipse cx="32" cy="34" rx="4.4" ry="6" fill="${wh}"/>` : ""}
${st ? `<path d="M25 29 q2 1 3 3 M39 29 q-2 1 -3 3 M26 34 q2 .6 3 2 M38 34 q-2 .6 -3 2" stroke="${st}" stroke-width="1.3" fill="none" stroke-linecap="round"/>` : ""}
<ellipse cx="27.6" cy="39.4" rx="2.6" ry="1.5" fill="${pt || wh || fur}"/><ellipse cx="36.4" cy="39.4" rx="2.6" ry="1.5" fill="${pt || wh || fur}"/>
<path d="M${26.2 - (ear - 4.4)} 17.6 L${25.4 - (ear - 4.4) * 0.6} ${16 - ear} L30 15.4Z M${37.8 + (ear - 4.4)} 17.6 L${38.6 + (ear - 4.4) * 0.6} ${16 - ear} L34 15.4Z" fill="${earC}" stroke="${earC}" stroke-width="1" stroke-linejoin="round"/>
${b.tufts ? `<path d="M25.4 ${12 - ear + 4} l-.8 -2.4 M38.6 ${12 - ear + 4} l.8 -2.4" stroke="${fur}" stroke-width="1"/>` : ""}
<ellipse cx="32" cy="20.6" rx="${head + (b.fluffy ? 0.6 : 0)}" ry="${head - 0.6}" fill="${fur}"/>
${pt ? `<ellipse cx="32" cy="23" rx="4.4" ry="3.4" fill="${pt}" opacity=".9"/>` : ""}
${wh ? `<path d="M32 15.6 L29.6 25.4 Q32 27 34.4 25.4Z" fill="${wh}"/>` : ""}
${st ? `<path d="M30 15 l.6 2.6 M32 14.6 v2.8 M34 15 l-.6 2.6" stroke="${st}" stroke-width="1.1" stroke-linecap="round"/>` : ""}
<circle cx="28.8" cy="20.4" r="4.2" fill="url(#${id})"/><circle cx="35.2" cy="20.4" r="4.2" fill="url(#${id})"/>
<ellipse cx="28.8" cy="20.4" rx="1.9" ry="1.7" fill="${eye}"/><ellipse cx="35.2" cy="20.4" rx="1.9" ry="1.7" fill="${eye}"/>
<ellipse cx="28.8" cy="20.4" rx=".55" ry="1.5" fill="#0A0F06"/><ellipse cx="35.2" cy="20.4" rx=".55" ry="1.5" fill="#0A0F06"/>
<path d="M31.2 23.4 h1.6 l-.8 1Z" fill="#E88A9A"/>
<path d="M25 23.6 l-4 -.8 M25 24.6 l-4 .6 M39 23.6 l4 -.8 M39 24.6 l4 .6" stroke="#FFF4DE" stroke-width=".45" opacity=".7"/>
</svg>`;
  }

  // ---------- sogno e stella ----------
  function sogno(key, seed) {
    const inner = cane(key, seed).replace(/^<svg[^>]*>/, "").replace(/<\/svg>$/, "");
    return `<svg width="86" height="68" viewBox="0 0 76 60" aria-hidden="true">
<path d="M14 46 Q2 46 4 36 Q6 26 16 28 Q18 14 32 16 Q40 6 52 14 Q66 12 68 26 Q76 30 72 40 Q70 48 60 46Z" fill="#DCE5FF" opacity=".95"/>
<circle cx="12" cy="54" r="3" fill="#DCE5FF" opacity=".8"/><circle cx="5" cy="58" r="1.6" fill="#DCE5FF" opacity=".6"/>
<g transform="translate(15 -4) scale(.72)" opacity=".92">${inner}</g>
</svg>`;
  }
  const stella = () => `<svg width="34" height="34" viewBox="0 0 40 40" aria-hidden="true">
<circle cx="20" cy="20" r="18" fill="#FFF4DE" opacity=".14"/>
<path d="M20 6 L23.4 15.6 L33.4 15.8 L25.4 21.8 L28.4 31.6 L20 25.8 L11.6 31.6 L14.6 21.8 L6.6 15.8 L16.6 15.6Z" fill="#FFF4DE"/>
</svg>`;

  window.Disegni = { CANI, GATTI, razza, cane, gatto, sogno, stella, hash };
})();
