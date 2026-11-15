// Zampa intero, in 3D, per la serie «Zampa ha 30 giorni per trovare casa» (15/11, Alberto: «deve essere un cane che si vede, intero»).
// È lo stesso cane 3D del paese (docs/mondo3d.js cane3d): meticcio, sempre lo stesso seme. Si fotografa con lo sfondo trasparente
// in una posa (triste, felice, sorpreso, base), da un lato (davanti, sinistra, destra), sporco (fango e ciuffi) o pulito.
// Uso: node reel/zampa3d.js <cartella> '[{"posa":"triste","lato":"davanti","sporco":true,"file":"zampa-triste-davanti-s.png"}]'
// TRE_LOCALE=<node_modules> serve three.js da lì (prove senza rete).
const { chromium } = require("playwright");
const http = require("http"), fs = require("fs"), path = require("path");
const [cartella, listaArg] = process.argv.slice(2);
const LISTA = JSON.parse(listaArg || "[]");
const DOCS = path.resolve(__dirname, "../docs");
const TIPI = { ".html": "text/html", ".js": "text/javascript", ".json": "application/json" };
const server = http.createServer((req, res) => {
  const u = decodeURIComponent(req.url.split("?")[0]);
  if (u === "/__zampa.html") { res.writeHead(200, { "Content-Type": "text/html" }); return res.end(PAGINA); }
  const p = path.join(DOCS, u);
  if (!p.startsWith(DOCS) || !fs.existsSync(p)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { "Content-Type": TIPI[path.extname(p)] || "application/octet-stream" }); fs.createReadStream(p).pipe(res);
});
const PAGINA = `<!doctype html><html><head><meta charset="utf-8">
<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"}}</script>
<script src="disegni.js"></script><script type="module" src="mondo3d.js"></script></head><body style="margin:0;background:transparent"></body></html>`;

(async () => {
  await new Promise(r => server.listen(0, r));
  const porta = server.address().port;
  const browser = await chromium.launch({ args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
  const page = await browser.newPage({ viewport: { width: 900, height: 1000 }, deviceScaleFactor: 1 });
  const loc = process.env.TRE_LOCALE;
  if (loc) await page.route(/cdn\.jsdelivr\.net\/npm\/three@[^/]+\/(.*)$/, (r, q) => r.fulfill({ path: path.join(loc, "three", q.url().split(/three@[^/]+\//)[1]), contentType: "text/javascript" }));
  page.on("pageerror", e => console.error("pagina:", e.message));
  await page.goto(`http://localhost:${porta}/__zampa.html`);
  await page.waitForFunction(() => window.Mondo3D && window.Mondo3D.cane3d && window.Disegni, null, { timeout: 60000 });
  await page.evaluate(async () => { window.Disegni.carica(await (await fetch("data/razze.json")).json()); });
  fs.mkdirSync(cartella, { recursive: true });
  for (const x of LISTA) {
    const png = await page.evaluate(async x => {
      const THREE = await import("three");
      const r = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true });
      r.setSize(900, 1000); r.setClearColor(0x000000, 0); r.outputColorSpace = THREE.SRGBColorSpace; r.toneMapping = THREE.ACESFilmicToneMapping; r.toneMappingExposure = 1.15;
      const sc = new THREE.Scene();
      sc.add(new THREE.HemisphereLight("#FFF4E0", "#6B5A4A", 1.6));
      const sole = new THREE.DirectionalLight("#FFFFFF", 2.4); sole.position.set(2.5, 4, 3); sc.add(sole);
      const retro = new THREE.DirectionalLight("#FFD9A0", 1.2); retro.position.set(-3, 2, -3); sc.add(retro);
      const d = { id: "zampa", rk: "meticcio", seed: 23, t: "cane" };
      const g = window.Mondo3D.cane3d(THREE, d), U = g.userData;
      const testa = U.testa, coda = U.coda;
      if (x.posa === "triste") { testa.rotation.x = 0.38; testa.rotation.z = -0.12; coda.rotation.x = 1.0; }
      if (x.posa === "felice") { testa.rotation.z = 0.22; testa.rotation.x = -0.08; coda.rotation.x = -0.5; coda.rotation.z = 0.6; }
      if (x.posa === "sorpreso") { testa.rotation.x = -0.3; coda.rotation.x = -0.2; }
      if (x.sporco) { // fango e ciuffi: è un cane di canile
        const fango = new THREE.MeshStandardMaterial({ color: "#4A3320", roughness: 1 });
        [[0.18, 0.55, 0.12, 0.09], [-0.2, 0.42, -0.05, 0.08], [0.05, 0.3, -0.35, 0.1], [-0.14, 1.05, 0.22, 0.05], [0.22, 0.2, 0.15, 0.06]].forEach(([px, py, pz, rr]) => {
          const m = new THREE.Mesh(new THREE.SphereGeometry(rr, 12, 10), fango); m.position.set(px, py, pz); m.scale.set(1, 0.55, 1); g.add(m); });
        const pelo = new THREE.MeshStandardMaterial({ color: "#6E4A2A", roughness: 1 });
        for (let i = 0; i < 6; i++) { const t = new THREE.Mesh(new THREE.ConeGeometry(0.035, 0.14, 6), pelo); t.position.set((i - 2.5) * 0.06, 0.24 + (i % 2) * 0.04, -0.02); t.rotation.z = (i - 2.5) * 0.35; testa.add(t); }
      }
      sc.add(g);
      const ang = { davanti: 0.35, sinistra: -0.75, destra: 1.1 }[x.lato || "davanti"];
      const cam = new THREE.PerspectiveCamera(30, 0.9, 0.1, 50);
      cam.position.set(Math.sin(ang) * 3.5, 1.05, Math.cos(ang) * 3.5); cam.lookAt(0, 0.62, 0);
      r.render(sc, cam);
      const url = r.domElement.toDataURL("image/png"); r.dispose();
      return url;
    }, x);
    fs.writeFileSync(path.join(cartella, x.file), Buffer.from(png.split(",")[1], "base64"));
    console.log("zampa 3D:", x.file);
  }
  await browser.close(); server.close();
})().catch(e => { console.error(e); process.exit(1); });
