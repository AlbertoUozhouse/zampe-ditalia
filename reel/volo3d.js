// L'apertura 3D dei reel (Alberto, 10/11: «basta Thor, voglio reel diversi e sempre più belli»).
// Apre il paese 3D del sito (docs/mondo3d.js) sul comune della storia, di notte, e registra un volo della telecamera
// che scende dall'alto fino all'animale raccontato, con il suo nome sopra. Ogni reel ha così un'apertura diversa e vera.
//
// Uso: node reel/volo3d.js "<comune>" "<nome animale o vuoto>" <uscita.mp4> [secondi]
// regia.json (facoltativo): {"volo": "discesa|orbita|radente|rivelazione|spirale", "cielo_alto": "#…", "effetto": "foglie|lanterne|stelle_cadenti|fuochi|nessuno", …}
// TRE_LOCALE=<cartella node_modules> serve three.js e Leaflet da lì quando la rete non arriva ai CDN (prove in locale).

const { chromium } = require("playwright");
const http = require("http"), fs = require("fs"), path = require("path"), os = require("os"), { execFileSync } = require("child_process");
const [comune, nome, uscita, secArg = "3.6", regiaFile, opzArg] = process.argv.slice(2);
// opzioni (11/11, il duello del testa a testa): {"altezza": 480 (mezzo schermo), "titolo": "...", "sotto": "...", "badge": "VS"}
const OPZ = opzArg ? JSON.parse(opzArg) : {};
// la regia del reparto Innovazione (motore/agenzia.py regia): stile del paese e volo della telecamera, diversi a ogni reel
const REGIA = regiaFile && fs.existsSync(regiaFile) ? JSON.parse(fs.readFileSync(regiaFile, "utf8")) : {};
const sec = String(REGIA.secondi || secArg);
const DOCS = path.resolve(__dirname, "../docs"), FPS = 30, N = Math.round(parseFloat(sec) * FPS);
const TIPI = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".json": "application/json", ".jpg": "image/jpeg", ".png": "image/png", ".svg": "image/svg+xml", ".woff2": "font/woff2" };

const server = http.createServer((req, res) => {
  const p = path.join(DOCS, decodeURIComponent(req.url.split("?")[0]).replace(/\/$/, "/index.html"));
  if (!p.startsWith(DOCS) || !fs.existsSync(p)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { "Content-Type": TIPI[path.extname(p)] || "application/octet-stream" }); fs.createReadStream(p).pipe(res);
});

(async () => {
  await new Promise(r => server.listen(0, r));
  const porta = server.address().port;
  const browser = await chromium.launch({ args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
  const ALTO = OPZ.altezza || 960;
  const page = await browser.newPage({ viewport: { width: 540, height: ALTO }, deviceScaleFactor: 2 });
  const loc = process.env.TRE_LOCALE;
  if (loc) {
    await page.route(/cdn\.jsdelivr\.net\/npm\/three@[^/]+\/(.*)$/, (r, q) => r.fulfill({ path: path.join(loc, "three", q.url().split(/three@[^/]+\//)[1]), contentType: "text/javascript" }));
    await page.route(/cdnjs\.cloudflare\.com\/ajax\/libs\/leaflet\/[^/]+\/(.*)$/, (r, q) => r.fulfill({ path: path.join(loc, "leaflet/dist", q.url().split(/leaflet\/[^/]+\//)[1]) }));
    await page.route(/fonts\.(googleapis|gstatic)\.com/, r => r.abort());
  }
  page.on("pageerror", e => console.error("pagina:", e.message));
  await page.goto(`http://localhost:${porta}/index.html`, { waitUntil: "domcontentloaded" });
  await page.waitForFunction(() => typeof VILLE !== "undefined" && VILLE.size > 0 && window.Mondo3D, null, { timeout: 90000 });
  await page.waitForFunction(() => window.coppaPronta && window.coppaPronta(), null, { timeout: 20000 }).catch(() => console.error("Coppa non caricata: niente tabellone"));
  const ok = await page.evaluate(async ([comune, nome, meteo, regia, opz]) => {
    const v = [...VILLE.values()].find(v => v.nome.toLowerCase() === comune.toLowerCase());
    if (!v) return "comune non trovato";
    const mio = nome ? v.lista.find(d => (d.n || "").toLowerCase() === nome.toLowerCase()) : null;
    await window.Mondo3D.apri(v, { svg: petSvg, mio, cattura: { nome: mio ? mio.n : "" }, scheda: () => "", stile: regia, coppa: window.coppaDi?.(v.key), ...(meteo ? { meteo } : {}), ...(opz.quando ? { quando: opz.quando } : {}) });
    const cielo = window.Mondo3D.mondo.cieloBreve;  // su una riga: «⛅ 10° · 🌑 luna nuova»  // il tempo vero di adesso nel comune e la luna di stanotte (mondo3d.js)
    const t = document.createElement("div");
    if (opz.titolo) {  // il duello: nome della città, le sue luci, e il VS in fondo alla metà di sopra
      t.innerHTML = `<b>${opz.titolo}</b><span>${opz.sotto || ""}</span>`;
      if (opz.badge) { const b = document.createElement("div"); b.textContent = opz.badge;
        b.style.cssText = "position:fixed;left:50%;bottom:10px;transform:translateX(-50%);z-index:6001;width:86px;height:86px;border-radius:50%;display:flex;align-items:center;justify-content:center;font:900 34px 'Bricolage Grotesque',system-ui,sans-serif;color:#2A1606;background:#FFC55C;border:5px solid #FFF4DE;box-shadow:0 0 30px rgba(255,197,92,.8)";
        document.body.appendChild(b); }
    } else t.innerHTML = `<b>${comune.toUpperCase()}</b><span>${mio ? "la casa di " + mio.n : "di notte"} · ${v.luci} ${v.luci === 1 ? "luce" : "luci"}</span>${cielo ? `<span>${new Date().toLocaleDateString("it-IT", { day: "numeric", month: "long", timeZone: "Europe/Rome" })} · ${cielo}</span>` : ""}`;
    t.style.cssText = "position:fixed;left:0;right:0;top:8%;z-index:6000;display:flex;flex-direction:column;align-items:center;gap:8px;text-align:center;font-family:'Bricolage Grotesque',system-ui,sans-serif;color:#FFF4DE;text-shadow:0 4px 0 #060B1A,0 0 24px rgba(6,11,26,.9)";
    t.firstChild.style.cssText = "font-size:58px;line-height:1;font-weight:800;letter-spacing:-1px;color:#FFC55C";
    [...t.children].slice(1).forEach(x => x.style.cssText = "font-size:22px;font-weight:800;background:rgba(6,11,26,.6);border:2px solid rgba(255,197,92,.6);border-radius:999px;padding:6px 16px");
    document.body.appendChild(t);
    return mio ? "ok" : "ok senza animale";
  }, [comune, nome || "", process.env.METEO_PROVA ? JSON.parse(process.env.METEO_PROVA) : null, REGIA, OPZ]);
  if (!ok.startsWith("ok")) { console.error(ok); process.exit(2); }
  await page.evaluate(b => { const M = window.Mondo3D.mondo; M.bloom.strength = M.diurno ? 0.2 : b; M.bloom.threshold = 0.85; }, Math.max(0.3, Math.min(1, REGIA.bloom || 0.5)));  // da vicino i lampioni abbagliavano
  const cartella = fs.mkdtempSync(path.join(os.tmpdir(), "volo3d-"));
  for (let i = 0; i < N; i++) {
    await page.evaluate(([i, N, volo]) => {
      const M = window.Mondo3D.mondo, T = M.THREE, k = i / (N - 1), e = k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
      const meta = M.camera.userData.meta || (M.camera.userData.meta = (() => {
        const sel = !!M.mio, pos = sel ? M.mio.g.position.clone() : new T.Vector3(0, 0, 0);
        return { pos, sel, a0: Math.atan2(pos.x || 0.001, pos.z || 1) + 0.9 };
      })());
      const { pos, a0, sel } = meta, R = M.R, L = (x, y) => x + (y - x) * e;
      const fine = sel ? { r: 11, h: 6.5, a: a0 - 0.9 } : { r: R * 0.75 + 8, h: R * 0.32 + 5, a: a0 - 0.9 };
      let r, h, ang, f = e;  // f: quanto la telecamera guarda l'animale invece del centro del paese
      if (volo === "orbita") { r = L(R * 1.1 + 16, fine.r); h = L(R * 0.45 + 10, fine.h); ang = fine.a + (1 - e) * 5.2; }
      else if (volo === "radente") { r = L(R * 0.85 + 8, fine.r); h = 5.6 + Math.sin(k * Math.PI) * 1.2 + e * (fine.h - 5.6); ang = fine.a + (1 - e) * 2.6; }  // appena sopra i tetti: più in basso i lampioni abbagliavano
      else if (volo === "rivelazione") { const q = 1 - e; r = fine.r + (R * 1.5 + 26 - fine.r) * (1 - q); h = fine.h + (R * 0.95 + 22 - fine.h) * (1 - q); ang = fine.a + e * 1.2; f = 1 - e; }
      else if (volo === "spirale") { r = L(R * 0.7 + 10, fine.r); h = L(R * 2.2 + 40, fine.h); ang = fine.a + (1 - e) * 7.5; }
      else { r = L(R * 1.5 + 26, fine.r); h = L(R * 0.95 + 22, fine.h); ang = L(a0, fine.a); }  // discesa
      const cx = (sel ? pos.x : 0) * f, cz = (sel ? pos.z : 0) * f;
      M.camera.position.set(cx + Math.sin(ang) * r, h, cz + Math.cos(ang) * r);
      M.controls.target.set(cx, 1.5 + 1.1 * f, cz);  // guardando l'animale un po' più in alto, il suo nome resta sotto il titolo
      M.passo(1000 + i * 1000 / 30);
    }, [i, N, REGIA.volo || "discesa"]);
    await page.screenshot({ path: path.join(cartella, `f${String(i).padStart(4, "0")}.jpg`), type: "jpeg", quality: 92 });
  }
  await browser.close(); server.close();
  execFileSync("ffmpeg", ["-loglevel", "error", "-y", "-framerate", String(FPS), "-i", path.join(cartella, "f%04d.jpg"), "-vf", `scale=1080:${ALTO * 2}:flags=lanczos,format=yuv420p`,
    "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-movflags", "+faststart", uscita], { stdio: "inherit" });
  fs.rmSync(cartella, { recursive: true, force: true });
  console.log(`apertura 3D: ${uscita} (${comune}${nome ? ", " + nome : ""}, ${N} fotogrammi)`);
})().catch(e => { console.error(e); process.exit(1); });
