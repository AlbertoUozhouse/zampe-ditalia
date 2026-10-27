"""Copertina del reel 1080x1920: un testo grande diverso per ogni reel, così sul profilo non sembrano tutti uguali.

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
    "fondatore": ("#FFE08A", "#A8650E"), "puntata": ("#D9CCFF", "#3B1F8C"), "vetrina": ("#E3F58A", "#3C7A22"),
}

PAGINA = """<!doctype html><html lang="it"><head><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,800&family=Nunito:wght@800;900&display=swap">
<style>
*{{box-sizing:border-box;margin:0}}
html,body{{width:1080px;height:1920px;overflow:hidden;background:#060B1A}}
.s{{position:relative;width:1080px;height:1920px;overflow:hidden;color:#FFF4DE;
  background:radial-gradient(ellipse 85% 50% at 50% 48%,{fondo} 0,{fondo}CC 30%,#0B1430 75%,#060B1A 100%)}}
svg{{position:absolute;left:0;top:0;opacity:.55}}
.box{{position:absolute;left:70px;right:70px;top:300px;height:1320px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:40px;text-align:center}}
.sopra{{font:900 58px Nunito;letter-spacing:6px;color:{accento};background:rgba(6,11,26,.7);border:4px solid {accento};border-radius:999px;padding:14px 44px}}
.grande{{font:800 {fs}px/0.98 'Bricolage Grotesque';letter-spacing:-3px;color:#FFF4DE;text-shadow:0 0 60px {accento}AA,0 6px 0 rgba(0,0,0,.35)}}
.grande i{{font-style:normal;font-size:.5em;color:{accento};letter-spacing:4px}}
.sotto{{font:900 56px/1.15 Nunito;color:#FFF4DE;background:rgba(6,11,26,.72);border-radius:28px;padding:18px 34px}}
.marca{{position:absolute;bottom:330px;left:0;right:0;text-align:center;font:800 44px 'Bricolage Grotesque';color:#FFC55C;text-shadow:0 0 20px rgba(255,197,92,.6)}}
</style></head><body><div class="s">
<svg width="1080" height="1920" viewBox="0 0 1080 1920"><defs><radialGradient id="l"><stop offset="0" stop-color="#FFE7B0"/><stop offset="1" stop-color="#FFC55C" stop-opacity="0"/></radialGradient></defs>
<path d="{sagoma}" fill="#13224A" stroke="#5577C9" stroke-opacity=".6" stroke-width="2"/>{luci}</svg>
<div class="box"><div class="sopra">{sopra}</div><div class="grande">{grande}</div><div class="sotto">{sotto}</div></div>
<div class="marca">Zampe d'Italia</div>
</div></body></html>"""


def main():
    cop = json.loads(Path(sys.argv[1]).read_text())
    c = cop.get("copertina") or {"sopra": cop.get("testata", {}).get("titolo", "ZAMPE D'ITALIA"), "grande": "Accendi<br>la tua luce", "sotto": "Scrivi città, nome e animale 👇", "tema": "voto"}
    accento, fondo = TEMI.get(c.get("tema"), TEMI["voto"])
    righe = [p.strip() for p in c["grande"].split("<br>")]
    grande = "<br>".join("<i>vs</i>" if r == "<i>vs</i>" else html.escape(r) for r in righe)
    lungo = max(len(re.sub(r"<[^>]+>", "", r)) for r in righe)
    fs = 230 if lungo <= 5 else 180 if lungo <= 8 else 140 if lungo <= 11 else 110 if lungo <= 15 else 88
    if len(righe) >= 3: fs = min(fs, 150)
    tutti = json.loads((ROOT / "docs/data/animali.json").read_text())["animali"]
    luci = "".join(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="10" fill="url(#l)"/>' for x, y in (xy(a["lng"], a["lat"]) for a in tutti if a.get("k") != "stella" and "lng" in a))
    pagina = PAGINA.format(sagoma=sagoma(), luci=luci, accento=accento, fondo=fondo, fs=fs, sopra=html.escape(c["sopra"]), grande=grande, sotto=html.escape(c["sotto"]))
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
