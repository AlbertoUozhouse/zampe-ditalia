"""Copertina del reel 1080x1920: un testo grande diverso per ogni reel, così sul profilo non sembrano tutti uguali.
Dal 30/10 testo giallo enorme con bordo scuro e una domanda a chi guarda, come le copertine che rendono di più sul feed.

Uso: python3 reel/copertina.py <copione.json> <uscita.jpg>
Il profilo mostra il reel ritagliato in 3:4 al centro (1080x1440): tutto il testo sta lì dentro.
"""
import html, json, re, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "reel"))
from cartolina import CHROME, sagoma, xy  # noqa: E402

TEMI = {  # accento, sfondo
    "voto": ("#FFC55C", "#7A3FB8"), "duello": ("#9CC6FF", "#1E5BC6"), "benvenuti": ("#9FF0FA", "#0F7C80"),
    "fondatore": ("#FFE08A", "#A8650E"), "puntata": ("#D9CCFF", "#3B1F8C"), "vetrina": ("#E3F58A", "#3C7A22"), "attivita": ("#FFB3C1", "#8C1F45"), "buio": ("#FFE9B8", "#0E1A40"),
}

PAGINA = """<!doctype html><html lang="it"><head><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,800&family=Nunito:wght@800;900&display=swap">
<style>
*{{box-sizing:border-box;margin:0}}
html,body{{width:1080px;height:1920px;overflow:hidden;background:#060B1A}}
.s{{position:relative;width:1080px;height:1920px;overflow:hidden;color:#FFF4DE;
  background:radial-gradient(ellipse 95% 60% at 50% 46%,{fondo} 0,{fondo} 35%,#1A3478 80%,#122659 100%)}}
svg{{position:absolute;left:0;top:0;opacity:.45}}
.box{{position:absolute;left:50px;right:50px;top:280px;height:1360px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:34px;text-align:center}}
.sopra{{font:900 58px Nunito;letter-spacing:6px;color:{accento};background:rgba(6,11,26,.7);border:4px solid {accento};border-radius:999px;padding:14px 44px}}
.grande{{font:800 {fs}px/0.98 'Bricolage Grotesque';letter-spacing:-3px;color:#FFD23F;-webkit-text-stroke:10px #2A1606;paint-order:stroke fill;text-shadow:0 12px 0 #2A1606,0 0 70px rgba(255,210,63,.55)}}
.grande i{{font-style:normal;font-size:.5em;color:#FFF4DE;letter-spacing:4px}}
.sotto{{font:900 60px/1.12 Nunito;color:#FFF4DE;-webkit-text-stroke:6px #2A1606;paint-order:stroke fill;text-shadow:0 6px 0 #2A1606}}
.domanda{{font:900 64px/1.1 Nunito;color:#2A1606;background:#FFD23F;border:6px solid #2A1606;border-radius:30px;padding:16px 36px;box-shadow:0 10px 0 #2A1606}}
.marca{{position:absolute;bottom:330px;left:0;right:0;text-align:center;font:800 44px 'Bricolage Grotesque';color:#FFC55C;text-shadow:0 0 20px rgba(255,197,92,.6)}}
</style></head><body><div class="s">
<svg width="1080" height="1920" viewBox="0 0 1080 1920"><defs><radialGradient id="l"><stop offset="0" stop-color="#FFE7B0"/><stop offset="1" stop-color="#FFC55C" stop-opacity="0"/></radialGradient></defs>
<path d="{sagoma}" fill="#13224A" stroke="#5577C9" stroke-opacity=".6" stroke-width="2"/>{luci}</svg>
<div class="box"><div class="sopra">{sopra}</div><div class="grande">{grande}</div><div class="sotto">{sotto}</div><div class="domanda">{domanda}</div></div>
<div class="marca">Zampe d'Italia</div>
</div></body></html>"""


PAGINA_LUCE = """<!doctype html><html lang="it"><head><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,800&family=Nunito:wght@800;900&display=swap">
<style>*{{box-sizing:border-box;margin:0}} html,body{{width:1080px;height:1920px;overflow:hidden;background:#040C24}}
.s{{position:relative;width:1080px;height:1920px;background:url('{fondo}') center/cover}}
.box{{position:absolute;left:50px;right:50px;top:330px;display:flex;flex-direction:column;align-items:center;gap:22px;text-align:center}}
.sopra{{font:900 56px Nunito;letter-spacing:6px;color:#FFC35A;background:rgba(4,12,36,.8);border:4px solid #FFC35A;border-radius:999px;padding:12px 40px}}
.grande{{font:800 {fs}px/1 'Bricolage Grotesque';letter-spacing:-2px;color:#FFF4DE;-webkit-text-stroke:8px #040C24;paint-order:stroke fill;text-shadow:0 0 60px rgba(255,195,90,.6)}}
.sotto{{position:absolute;left:0;right:0;top:1130px;text-align:center;font:900 64px Nunito;color:#FFD27A;-webkit-text-stroke:6px #040C24;paint-order:stroke fill}}
.marca{{position:absolute;bottom:330px;left:0;right:0;text-align:center;font:800 44px 'Bricolage Grotesque';color:#FFC55C}}
</style></head><body><div class="s"><div class="box"><div class="sopra">{sopra}</div><div class="grande">{grande}</div></div><div class="sotto">{sotto}</div><div class="marca">Zampe d'Italia</div></div></body></html>"""

PAGINA_PAOLINO = """<!doctype html><html lang="it"><head><meta charset="utf-8"><style>
@font-face{{font-family:Anton;src:url('{anton}') format('woff2')}}
*{{box-sizing:border-box;margin:0}} html,body{{width:1080px;height:1920px;overflow:hidden;background:#34436E}}
.s{{position:relative;width:1080px;height:1920px;overflow:hidden}} svg{{position:absolute;inset:0}}
.g{{position:absolute;left:0;right:0;top:220px;text-align:center;font:400 340px/0.92 Anton;color:#FFC93C;-webkit-text-stroke:14px #1A1206;paint-order:stroke fill;text-shadow:0 16px 0 #1A1206}}
.g i{{display:block;font-style:normal;font-size:96px;color:#fff;-webkit-text-stroke:9px #1A1206;text-shadow:0 9px 0 #1A1206;margin-top:6px}}
.t{{position:absolute;left:0;right:0;top:720px;text-align:center}}
.t span{{display:inline-block;font:400 120px/1.05 Anton;color:#1A1206;background:#FFF1C9;border:9px solid #1A1206;border-radius:24px;padding:4px 40px 12px;transform:rotate(-3deg);box-shadow:0 12px 0 rgba(0,0,0,.35)}}
.n{{position:absolute;left:40px;top:1010px}} .n span{{display:inline-block;font:400 76px/1.05 Anton;color:#fff;background:#E2432F;border:7px solid #1A1206;border-radius:14px;padding:4px 24px 8px;transform:rotate(-6deg);box-shadow:0 9px 0 rgba(0,0,0,.35)}}
.p{{position:absolute;left:0;right:0;top:940px;height:760px;display:flex;justify-content:center;align-items:flex-end}} .p img{{height:100%;filter:drop-shadow(0 16px 0 rgba(0,0,0,.2))}}
.f{{position:absolute;right:30px;top:1230px}} .f span{{display:inline-block;font:400 60px/1.05 Anton;color:#1A1206;background:#5BD07A;border:7px solid #1A1206;border-radius:14px;padding:4px 20px 8px;transform:rotate(5deg);box-shadow:0 9px 0 rgba(0,0,0,.35)}}
</style></head><body><div class="s"><svg viewBox="0 0 1080 1920">{sfondo}</svg>
<div class="p"><img src="{posa}"></div><div class="g">{giorno}<i>GIORNO {giorno} DI 30</i></div><div class="t"><span>{titolo}</span></div>
<div class="n"><span>PAOLINO</span></div><div class="f"><span>VOTA TU 👇</span></div></div></body></html>"""


PAGINA_STADIO = """<!doctype html><html lang="it"><head><meta charset="utf-8"><style>
@font-face{{font-family:Anton;src:url('{anton}') format('woff2')}}
*{{box-sizing:border-box;margin:0}} html,body{{width:1080px;height:1920px;overflow:hidden;background:#16204A}}
.s{{position:relative;width:1080px;height:1920px;overflow:hidden}} svg{{position:absolute;inset:0}}
.k{{position:absolute;left:0;right:0;top:300px;text-align:center}} .k span{{display:inline-block;font:400 64px/1.05 Anton;color:#1A1206;background:#FFD23F;border:7px solid #1A1206;border-radius:14px;padding:6px 26px 10px;transform:rotate(-3deg);box-shadow:0 10px 0 rgba(0,0,0,.35)}}
.t{{position:absolute;left:30px;right:30px;top:470px;text-align:center;font:400 {fs}px/0.98 Anton;color:#fff;-webkit-text-stroke:14px #1A1206;paint-order:stroke fill;text-shadow:0 14px 0 #1A1206}}
.t i{{display:block;font-style:normal;font-size:110px;color:#FFD23F;margin:6px 0}}
.st{{position:absolute;left:0;right:0;top:1270px;text-align:center}} .st span{{display:inline-block;font:400 70px/1.05 Anton;color:#fff;background:#E2432F;border:7px solid #1A1206;border-radius:14px;padding:6px 26px 10px;transform:rotate(2deg);box-shadow:0 10px 0 rgba(0,0,0,.35)}}
.g{{position:absolute;left:0;right:0;top:1440px;text-align:center}} .g span{{display:inline-block;font:400 60px/1.05 Anton;color:#1A1206;background:#5BD07A;border:7px solid #1A1206;border-radius:14px;padding:6px 24px 10px;transform:rotate(-2deg);box-shadow:0 10px 0 rgba(0,0,0,.35)}}
</style></head><body><div class="s"><svg viewBox="0 0 1080 1920">{sfondo}</svg>
<div class="k"><span>⚽ CAMPIONATO DELLE ZAMPE</span></div><div class="t">{a}<i>VS</i>{b}</div><div class="st"><span>{stadio}</span></div><div class="g"><span>OGNI COMMENTO È UN GOL 👇</span></div></div></body></html>"""


def html_stadio(p):
    """18/11: la copertina della partita del Campionato, nello stadio coi colori delle due squadre."""
    sys.path.insert(0, str(ROOT / "reel/modello")); import scene
    n = max(len(p["a"]), len(p["b"])); fs = 230 if n <= 5 else 190 if n <= 7 else 150 if n <= 10 else 120
    return PAGINA_STADIO.format(anton=(ROOT / "reel/lancio-hf/assets/fonts/anton.woff2").as_uri(), sfondo=scene.sfondo_stadio(p["ca"], p["cb"]), fs=fs,
                                a=html.escape(p["a"]), b=html.escape(p["b"]), stadio=html.escape(p["stadio"]))


def copertina_stadio(p, uscita):
    tmp = Path(tempfile.mkdtemp()); (tmp / "c.html").write_text(html_stadio(p)); png = tmp / "c.png"
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1", "--window-size=1080,1920", "--allow-file-access-from-files",
                    "--virtual-time-budget=6000", f"--user-data-dir={tmp / '.chrome'}", f"--screenshot={png}", (tmp / "c.html").as_uri()], capture_output=True, timeout=120)
    if not png.exists(): sys.exit("copertina non creata")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(png), "-q:v", "3", str(uscita)], check=True)
    print(f"copertina dello stadio: {uscita}")


def copertina_paolino(p, uscita):
    """16/11, Alberto: «dovevi fare la copertina di Paolino». Ogni puntata la sua: il numero del giorno gigante, il titolo, Paolino a cartone.
    Sul profilo si vede il centro 3:4 (da 240 a 1680): numero, titolo e Paolino stanno lì dentro."""
    tmp = Path(tempfile.mkdtemp())
    (tmp / "c.html").write_text(html_paolino(p))
    png = tmp / "c.png"
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1", "--window-size=1080,1920", "--allow-file-access-from-files",
                    "--virtual-time-budget=6000", f"--user-data-dir={tmp / '.chrome'}", f"--screenshot={png}", (tmp / "c.html").as_uri()], capture_output=True, timeout=120)
    if not png.exists(): sys.exit("copertina non creata")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(png), "-q:v", "3", str(uscita)], check=True)
    print(f"copertina di Paolino: {uscita}")


def html_paolino(p):
    sys.path.insert(0, str(ROOT / "reel/modello")); import scene
    return (PAGINA_PAOLINO.format(anton=(ROOT / "reel/lancio-hf/assets/fonts/anton.woff2").as_uri(), sfondo=scene.CARTONE_SFONDI["canile"],
                                  posa=(ROOT / "reel/assets/paolino" / f"{p.get('posa', 'triste')}.png").as_uri(), giorno=int(p["giorno"]), titolo=html.escape(p["titolo"])))


def fondo_luce(lng, lat, uscita):
    """L'immagine protagonista: la mappa vera dell'Italia di notte attorno al comune, con la sua luce accesa al centro."""
    import math
    from PIL import Image, ImageDraw, ImageFilter
    M = json.loads((ROOT / "reel/assets/italia-notte.json").read_text())
    x = (lng + 180) / 360 * 256 * 2 ** M["z"] - M["x0"]; y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * 256 * 2 ** M["z"] - M["y0"]
    im = Image.open(ROOT / "reel/assets/italia-notte.jpg").convert("RGB")
    w, h = 1080 / 1.6, 1920 / 1.6  # ingrandimento 1,6: si vedono coste e rilievi attorno al comune
    cx, cy = x, y + h * 0.04  # la luce un po' sopra il centro, il testo sotto ha spazio
    im = im.crop((int(cx - w / 2), int(cy - h * 0.55), int(cx + w / 2), int(cy + h * 0.45))).resize((1080, 1920), Image.LANCZOS)
    px, py = 540, int(1920 * 0.55 - 1920 * 0.04)
    alone = Image.new("RGB", im.size, (0, 0, 0)); d = ImageDraw.Draw(alone)
    for r, c in ((220, (90, 55, 10)), (120, (190, 120, 30)), (55, (255, 190, 90)), (22, (255, 240, 210))):
        d.ellipse((px - r, py - r, px + r, py + r), fill=c)
    alone = alone.filter(ImageFilter.GaussianBlur(40))
    from PIL import ImageChops
    im = ImageChops.add(im, alone)
    ImageDraw.Draw(im).ellipse((px - 12, py - 12, px + 12, py + 12), fill=(255, 248, 230))
    im.save(uscita, quality=90)

def main():
    cop = json.loads(Path(sys.argv[1]).read_text())
    c = cop.get("copertina") or {"sopra": cop.get("testata", {}).get("titolo", "ZAMPE D'ITALIA"), "grande": "Accendi<br>la tua luce", "sotto": "Scrivi città, nome e animale 👇", "tema": "voto"}
    if c.get("paolino"): return copertina_paolino(c["paolino"], sys.argv[2])
    if c.get("stadio"): return copertina_stadio(c["stadio"], sys.argv[2])
    if c.get("luce"):  # la serie della mappa (7/11): un'immagine protagonista e poche parole, per esempio «La prima luce di Atri»
        tmp = Path(tempfile.mkdtemp()); fondo_luce(*c["luce"], tmp / "fondo.jpg")
        n = len(c["grande"]); fs = 150 if n <= 9 else 120 if n <= 13 else 96 if n <= 18 else 78
        (tmp / "c.html").write_text(PAGINA_LUCE.format(fondo=(tmp / "fondo.jpg").as_uri(), fs=fs, sopra=html.escape(c["sopra"]), grande=html.escape(c["grande"]), sotto=html.escape(c.get("sotto", ""))))
        png = tmp / "c.png"
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1", "--window-size=1080,1920", "--allow-file-access-from-files",
                        "--virtual-time-budget=6000", f"--user-data-dir={tmp / '.chrome'}", f"--screenshot={png}", (tmp / "c.html").as_uri()], capture_output=True, timeout=120)
        if not png.exists(): sys.exit("copertina non creata")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(png), "-q:v", "3", sys.argv[2]], check=True)
        return print(f"copertina: {sys.argv[2]}")
    accento, fondo = TEMI.get(c.get("tema"), TEMI["voto"])
    righe = [p.strip() for p in c["grande"].split("<br>")]
    grande = "<br>".join("<i>vs</i>" if r == "<i>vs</i>" else html.escape(r) for r in righe)
    lungo = max(len(re.sub(r"<[^>]+>", "", r)) for r in righe)
    fs = 230 if lungo <= 5 else 180 if lungo <= 8 else 140 if lungo <= 11 else 110 if lungo <= 15 else 88
    if len(righe) >= 3: fs = min(fs, 150)
    tutti = json.loads((ROOT / "docs/data/animali.json").read_text())["animali"]
    luci = "".join(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="10" fill="url(#l)"/>' for x, y in (xy(a["lng"], a["lat"]) for a in tutti if a.get("k") != "stella" and "lng" in a))
    pagina = PAGINA.format(sagoma=sagoma(), luci=luci, accento=accento, fondo=fondo, fs=fs, sopra=html.escape(c["sopra"]), grande=grande, sotto=html.escape(c["sotto"]), domanda=html.escape(c.get("domanda") or "Il tuo animale c'è? 👇"))
    tmp = Path(tempfile.mkdtemp())
    (tmp / "c.html").write_text(pagina)
    png = tmp / "c.png"
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1", "--window-size=1080,1920",
                    "--virtual-time-budget=6000", f"--user-data-dir={tmp / '.chrome'}", f"--screenshot={png}", (tmp / "c.html").as_uri()], capture_output=True, timeout=120)
    if not png.exists():
        sys.exit("copertina non creata")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(png), "-q:v", "3", sys.argv[2]], check=True)  # Instagram vuole JPG
    print(f"copertina: {sys.argv[2]}")


if __name__ == "__main__":
    main()
