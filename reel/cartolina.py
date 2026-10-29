"""Cartolina 1080x1920 da mettere in storia: l'animale di una persona, acceso sulla mappa notturna d'Italia.

Uso: python3 reel/cartolina.py <utente> [cartella]
Disegna una cartolina per ogni animale della persona (al massimo 3) e stampa i nomi dei file .png creati.
I nomi dei file sono casuali: nel repository pubblico non si capisce di chi sono, finché non li si apre.
"""
import html, json, math, secrets, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
E = html.escape
CHROME = next((c for c in ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", shutil.which("google-chrome"),
                           shutil.which("google-chrome-stable"), shutil.which("chromium"), shutil.which("chromium-browser")) if c and Path(c).exists()), None)

# l'Italia occupa un riquadro 900x1000 a metà cartolina
LON0, LON1, LAT0, LAT1 = 6.4, 18.8, 36.5, 47.2
W, H, X0, Y0 = 860, 880, 110, 430
KX = math.cos(math.radians(42))

def xy(lng, lat):
    sx = W / ((LON1 - LON0) * KX)
    sy = H / (LAT1 - LAT0)
    s = min(sx, sy)
    ox = X0 + (W - (LON1 - LON0) * KX * s) / 2
    return ox + (lng - LON0) * KX * s, Y0 + (LAT1 - lat) * s

def sagoma():
    g = json.loads((ROOT / "docs/data/regioni.json").read_text())
    d = []
    for f in g["features"]:
        geo = f["geometry"]
        poligoni = geo["coordinates"] if geo["type"] == "MultiPolygon" else [geo["coordinates"]]
        for p in poligoni:
            for anello in p:
                pts = [xy(*c[:2]) for c in anello]
                d.append("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z")
    return " ".join(d)

def disegni(animali):
    js = f"""const fs=require("fs"); global.window={{}}; eval(fs.readFileSync({json.dumps(str(ROOT / "docs/disegni.js"))},"utf8"));
const D=window.Disegni; D.carica(JSON.parse(fs.readFileSync({json.dumps(str(ROOT / "docs/data/razze.json"))},"utf8")));
const out={{}}; for (const a of {json.dumps(animali)}) {{ const s=D.hash(a.id);
  if (a.k==="stella") {{ out[a.id]={{svg:D.stella(), tipo:"Una stella nel cielo"}}; continue; }}
  if (a.t==="altro") {{ out[a.id]={{svg:D.altro(a.specie,s), tipo:(a.razza_testo||a.specie||"")}}; continue; }}
  const k=D.razza(a.razza_testo||a.razza,a.t);
  out[a.id]={{svg:(a.t==="gatto"?D.gatto(k,s):D.cane(k,s)), tipo:(k==="meticcio"&&a.razza_testo&&!/meticc|incrocio|mix/i.test(a.razza_testo))?a.razza_testo:(a.t==="gatto"?D.GATTI[k]:D.CANI[k]).n}}; }}
for (const a of {json.dumps(animali)}) if (a.acc && out[a.id] && a.k!=="stella") out[a.id].svg=D.accessori(out[a.id].svg, a.acc, a.k==="sogno" ? "sogno" : a.t, D.hash(a.id));
for (const a of {json.dumps(animali)}) if (a.vestito && out[a.id] && a.k!=="stella") out[a.id].svg=D.vesti(out[a.id].svg, a.vestito, a.k==="sogno" ? "sogno" : a.t, D.hash(a.id));
console.log(JSON.stringify(out));"""
    return json.loads(subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True).stdout)

PAGINA = """<!doctype html><html lang="it"><head><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,800&family=Nunito:wght@800;900&display=swap">
<style>
*{{box-sizing:border-box;margin:0}}
html,body{{width:1080px;height:1920px;overflow:hidden;background:#060B1A}}
.s{{position:relative;width:1080px;height:1920px;overflow:hidden;color:#FFF4DE;font-family:Nunito,sans-serif;
  background:radial-gradient(ellipse 80% 45% at 50% 55%,#1A2D63 0,#0E1A3A 50%,#060B1A 100%)}}
.stelle{{position:absolute;inset:0;background:radial-gradient(2px 2px at 12% 9%,#fff8 50%,transparent 51%),radial-gradient(2px 2px at 82% 14%,#fff6 50%,transparent 51%),
  radial-gradient(3px 3px at 66% 5%,#fff9 50%,transparent 51%),radial-gradient(2px 2px at 28% 22%,#fff5 50%,transparent 51%),radial-gradient(2px 2px at 92% 40%,#fff6 50%,transparent 51%),
  radial-gradient(3px 3px at 6% 48%,#fff7 50%,transparent 51%),radial-gradient(2px 2px at 50% 96%,#fff5 50%,transparent 51%),radial-gradient(2px 2px at 18% 80%,#fff6 50%,transparent 51%)}}
.marca{{position:absolute;top:250px;left:0;right:0;text-align:center;font:800 58px 'Bricolage Grotesque';color:#FFC55C;text-shadow:0 0 24px rgba(255,197,92,.6)}}
.sotto{{position:absolute;top:326px;left:0;right:0;text-align:center;font:800 32px Nunito;opacity:.8}}
.grazie{{display:inline-block;margin-top:6px;font:900 44px Nunito;color:#3A1E08;background:linear-gradient(#FFE7A0,#FFC55C);border-radius:999px;padding:12px 34px;opacity:1;box-shadow:0 0 40px rgba(255,197,92,.6)}}
svg.mappa{{position:absolute;left:0;top:0}}
.eroe{{position:absolute;left:{ex}px;top:{ey}px;transform:translate(-50%,-100%);display:flex;flex-direction:column;align-items:center}}
.eroe svg{{width:{dim}px;height:auto;filter:drop-shadow(0 0 50px {glow})}}
.targa{{margin-top:-6px;font:800 {fs}px/1 'Bricolage Grotesque';letter-spacing:4px;text-transform:uppercase;padding:10px 30px;border-radius:16px;border:7px solid {bordo};
  color:{testo};background:{fondo};box-shadow:0 0 40px {glow};white-space:nowrap}}
.info{{position:absolute;left:60px;right:60px;bottom:390px;text-align:center;display:flex;flex-direction:column;align-items:center;gap:18px}}
.tipo{{font:900 44px Nunito}}
.dove{{font:800 40px Nunito;opacity:.9}}
.corona{{font:900 40px Nunito;color:#3A1E08;background:linear-gradient(#FFD77A,#FFB347);border-radius:999px;padding:10px 32px;box-shadow:0 0 34px rgba(255,197,92,.6)}}
.piede{{position:absolute;left:0;right:0;bottom:270px;text-align:center;font:900 40px Nunito;color:#FFC55C}}
.piede small{{display:block;font:800 30px Nunito;color:#FFF4DE;opacity:.75;margin-top:8px}}
</style></head><body><div class="s"><div class="stelle"></div>
<div class="marca">Zampe d'Italia</div><div class="sotto">{sotto}</div>
<svg class="mappa" width="1080" height="1920" viewBox="0 0 1080 1920">
  <defs><radialGradient id="l"><stop offset="0" stop-color="#FFE7B0" stop-opacity=".95"/><stop offset="1" stop-color="#FFC55C" stop-opacity="0"/></radialGradient>
  <radialGradient id="io"><stop offset="0" stop-color="#FFFFFF"/><stop offset=".25" stop-color="{luce}"/><stop offset="1" stop-color="{luce}" stop-opacity="0"/></radialGradient></defs>
  <path d="{sagoma}" fill="#13224A" stroke="#5577C9" stroke-opacity=".55" stroke-width="2"/>
  {luci}
  <circle cx="{px}" cy="{py}" r="70" fill="url(#io)"/>
  <line x1="{px}" y1="{py}" x2="{ex}" y2="{ey}" stroke="{luce}" stroke-width="4" stroke-dasharray="4 10" stroke-linecap="round" opacity=".8"/>
</svg>
<div class="eroe">{svg}<div class="targa">{nome}</div></div>
<div class="info"><div class="tipo">{tipo}</div><div class="dove">📍 {comune} · @{utente}</div>{corona}</div>
<div class="piede">Accendi anche il tuo su zampeditalia.it<small>commenta sotto i reel di @zampeditalia</small></div>
</div></body></html>"""

COLORI = {"cane": ("#FFC55C", "rgba(255,179,71,.65)", "#F3DDB0", "#5E3519", "#5A3417"),
          "gatto": ("#CFE36B", "rgba(207,227,107,.55)", "#E9F2C4", "#3D4A18", "#2F3A10"),
          "altro": ("#82DCEB", "rgba(130,220,235,.55)", "#D6F3F8", "#1C5361", "#0E3A44"),
          "stella": ("#FFF4DE", "rgba(255,244,222,.5)", "#FFF4DE", "#8A7A5A", "#3A2E18")}

def main():
    arg = [a for a in sys.argv[1:] if not a.startswith("--")]
    grazie = "--grazie" in sys.argv  # versione per la storia di @zampeditalia: ringrazia chi ci ha messo in storia
    opz = dict(a[2:].split("=", 1) for a in sys.argv[1:] if a.startswith("--") and "=" in a)
    REGALI = {"osso": "🦴 l'Osso d'oro", "fiocco": "🎀 il Fiocco", "collare": "📿 il Collare d'oro", "corona": "👑 la Corona", "fuochi": "🎆 i Fuochi d'artificio", "boost": "⚡ il Boost x2"}  # come motore/negozio.py
    regalo = REGALI.get(opz.get("regalo"))  # storia di @zampeditalia quando qualcuno compra un accessorio nel negozio
    utente = arg[0]
    cartella = Path(arg[1]) if len(arg) > 1 else ROOT / "docs/cartoline"
    cartella.mkdir(parents=True, exist_ok=True)
    tutti = json.loads((ROOT / "docs/data/animali.json").read_text())["animali"]
    suoi = [a for a in tutti if a["u"].lower() == utente.lower() and a["k"] in ("animale", "sogno", "stella")][:1 if grazie else 3]
    if regalo: suoi = [a for a in tutti if a.get("id") == opz.get("id")][:1]
    if not suoi or not CHROME:
        sys.exit("niente da disegnare" if not suoi else "Chrome non trovato")
    if sys.platform.startswith("linux") and "emoji" not in subprocess.run(["fc-list"], capture_output=True, text=True).stdout.lower():
        # sui server di GitHub manca il font delle emoji: senza, 🐢 e 👑 escono come quadratini
        subprocess.run("sudo apt-get install -y -qq fonts-noto-color-emoji >/dev/null 2>&1 && fc-cache -f >/dev/null", shell=True)
    dis = disegni(suoi)
    sag = sagoma()
    luci = "".join(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="9" fill="url(#l)"/>'
                   for x, y in (xy(a["lng"], a["lat"]) for a in tutti if a.get("k") != "stella" and "lng" in a))
    tmp = Path(tempfile.mkdtemp())
    for a in suoi:
        px, py = xy(a["lng"], a["lat"])
        colore = "stella" if a["k"] == "stella" else a.get("t", "cane")
        luce, glow, fondo, bordo, testo = COLORI.get(colore, COLORI["cane"])
        # il disegno sta sopra la mappa, spostato verso il mare dalla parte più libera
        dim = 420 if colore in ("cane", "gatto") else 260
        n = len(a["n"])
        fs = 64 if n <= 8 else 52 if n <= 12 else 42
        largo = max(dim, n * fs * 0.72 + 90)
        ex = 300 if px > 560 else 780
        ex = int(min(1040 - largo / 2, max(40 + largo / 2, ex)))  # né il disegno né il nome escono dalla cartolina
        ey = int(max(400 + dim + 70, min(1250, py - 40)))         # e non coprono il titolo
        corona = f'<div class="corona">🐺 {E(a["capo"])}</div>' if a.get("capo") else f'<div class="corona">👑 {E(a["ruolo"])}</div>' if a.get("ruolo") else ""
        pagina = PAGINA.format(sagoma=sag, luci=luci, px=f"{px:.0f}", py=f"{py:.0f}", ex=ex, ey=ey, luce=luce, glow=glow, fondo=fondo, bordo=bordo, testo=testo,
                               dim=dim, fs=fs, svg=dis[a["id"]]["svg"], nome=E(a["n"]),
                               tipo=E(str(dis[a["id"]]["tipo"])[:1].upper() + str(dis[a["id"]]["tipo"])[1:]), comune=E(f'{a["c"]} ({a["p"]})'),
                               utente=E(a["u"]), corona=corona,
                               sotto=(f'<span class="grazie">🎁 {E(a["n"])} ha {E(regalo)}!</span>' if regalo else f'<span class="grazie">💛 Grazie @{E(a["u"])} per la storia!</span>' if grazie else "la mappa degli animali d'Italia"))
        h = tmp / "c.html"
        h.write_text(pagina)
        nome = secrets.token_hex(8) + ".png"
        png = cartella / nome
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1", "--window-size=1080,1920",
                        "--virtual-time-budget=6000", f"--user-data-dir={tmp / '.chrome'}", f"--screenshot={png}", h.as_uri()],
                       capture_output=True, timeout=120)
        if png.exists():
            print(nome)
    shutil.rmtree(tmp, ignore_errors=True)

if __name__ == "__main__":
    main()
