"""Carosello "Le prime luci d'Italia": una slide 1080x1350 per animale vero, più copertina, classifica e chiusura.

Uso: python3 reel/carosello.py <cartella-uscita> [massimo animali]
Gli animali sono disegnati con lo stesso seme della mappa (Disegni.hash dell'id), quindi sono identici a quelli sul sito.
Gli account di Alberto (ESCLUSI in motore/copione.py) non compaiono.
"""
import html, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "motore"))
from copione import ESCLUSI  # noqa: E402

E = html.escape
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

TESTA = """<!doctype html><html lang="it"><head><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,800&family=Nunito:wght@700;800;900&display=swap">
<style>
:root{--night:#060B1A;--gold:#FFC55C;--cream:#FFF4DE;--cat:#CFE36B}
*{box-sizing:border-box;margin:0}
html,body{width:1080px;height:1350px;overflow:hidden;background:var(--night)}
.s{position:relative;width:1080px;height:1350px;overflow:hidden;color:var(--cream);font-family:Nunito,sans-serif;
  background:radial-gradient(ellipse 75% 50% at 50% 48%,#1A2D63 0,#0E1A3A 48%,var(--night) 100%)}
.stelle{position:absolute;inset:0;background:radial-gradient(2px 2px at 12% 14%,#fff8 50%,transparent 51%),radial-gradient(2px 2px at 82% 22%,#fff6 50%,transparent 51%),
  radial-gradient(3px 3px at 66% 8%,#fff9 50%,transparent 51%),radial-gradient(2px 2px at 28% 34%,#fff5 50%,transparent 51%),radial-gradient(2px 2px at 90% 60%,#fff6 50%,transparent 51%),
  radial-gradient(3px 3px at 7% 70%,#fff7 50%,transparent 51%),radial-gradient(2px 2px at 50% 92%,#fff5 50%,transparent 51%)}
.marca{position:absolute;top:56px;left:0;right:0;text-align:center;font:800 32px 'Bricolage Grotesque';color:var(--gold);text-shadow:0 0 18px rgba(255,197,92,.55)}
.num{position:absolute;top:56px;right:56px;font:900 26px Nunito;color:var(--cream);opacity:.6}
h1{font:800 96px/.98 'Bricolage Grotesque';letter-spacing:-2px;text-align:center}
.d{color:var(--gold);text-shadow:0 0 30px rgba(255,197,92,.5)} .c{color:var(--cat);text-shadow:0 0 30px rgba(207,227,107,.45)}
.sub{font:800 40px/1.25 Nunito;text-align:center;opacity:.92}
.centro{position:absolute;left:60px;right:60px;top:0;bottom:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:26px}
.targa{font:800 82px/1 'Bricolage Grotesque';letter-spacing:6px;padding:12px 38px;border-radius:18px;border:8px solid;margin-top:-30px}
.targa.d{color:#5A3417;background:#F3DDB0;border-color:#5E3519;box-shadow:0 0 50px rgba(255,197,92,.6);text-shadow:none}
.targa.c{color:#2F3A10;background:#E9F2C4;border-color:#3D4A18;box-shadow:0 0 50px rgba(207,227,107,.55);text-shadow:none}
.chi{font:900 44px Nunito}.dove{font:800 38px Nunito;opacity:.85}
.corona{display:inline-block;font:900 34px Nunito;color:#3A1E08;background:linear-gradient(#FFD77A,#FFB347);border-radius:999px;padding:8px 26px;box-shadow:0 0 30px rgba(255,197,92,.6)}
.eroe{width:620px;height:auto}
.eroe.d{filter:drop-shadow(0 0 70px rgba(255,179,71,.7))} .eroe.c{filter:drop-shadow(0 0 60px rgba(207,227,107,.5))}
ol{list-style:none;padding:0;width:860px;display:flex;flex-direction:column;gap:18px}
li{display:grid;grid-template-columns:80px 1fr auto;align-items:center;gap:20px;background:rgba(20,36,77,.92);border:3px solid rgba(85,119,201,.6);border-radius:26px;padding:22px 30px;font:900 50px Nunito}
li:first-child{border-color:var(--gold);box-shadow:0 0 40px rgba(255,197,92,.3)}
li b{font:800 56px 'Bricolage Grotesque';color:var(--gold);text-align:center} li span:last-child{color:var(--gold)}
.esempio{background:#fff;color:#111;border-radius:30px;padding:26px 34px;font:900 52px Nunito;box-shadow:0 20px 60px rgba(0,0,0,.45)}
.bottone{font:900 46px Nunito;color:#2A1606;background:var(--gold);border-radius:24px;padding:20px 40px;box-shadow:0 0 50px rgba(255,197,92,.7)}
</style></head><body><div class="s"><div class="stelle"></div><div class="marca">Zampe d'Italia</div>"""
CODA = "</div></body></html>"

def disegna(animali):
    js = f"""const fs=require("fs"); global.window={{}}; eval(fs.readFileSync({json.dumps(str(ROOT / "docs/disegni.js"))},"utf8"));
const D=window.Disegni; D.carica(JSON.parse(fs.readFileSync({json.dumps(str(ROOT / "docs/data/razze.json"))},"utf8")));
const out={{}}; for (const a of {json.dumps(animali)}) {{ const k=D.razza(a.razza_testo||a.razza,a.t); const s=D.hash(a.id);
  out[a.id]={{svg:(a.t==="gatto"?D.gatto(k,s):D.cane(k,s)).replace(/width="\\d+" height="\\d+" /,"class=\\"eroe "+(a.t==="gatto"?"c":"d")+"\\" "), nome:(a.t==="gatto"?D.GATTI[k]:D.CANI[k]).n, k}}; }}
console.log(JSON.stringify(out));"""
    return json.loads(subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True).stdout)

def etichetta(a, dis):
    k, n = dis["k"], dis["nome"]
    if k == "meticcio": return "Meticcio"
    if a["t"] == "gatto" and k == "europeo" and "meticc" in (a.get("razza_testo") or ""): return "Gatto meticcio"
    return n

def main():
    out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    massimo = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    A = [a for a in json.loads((ROOT / "docs/data/animali.json").read_text())["animali"] if a.get("k") == "animale"]
    tutti = len([a for a in json.loads((ROOT / "docs/data/animali.json").read_text())["animali"] if a.get("k") != "stella"])
    for a in A: a.setdefault("id", f'{a["u"]}|{a["k"]}|{a["n"].lower()}')
    scelti = [a for a in A if a["u"].lower() not in ESCLUSI][:massimo]
    D = disegna(scelti)
    citta = {}
    for a in A: citta[a["c"]] = citta.get(a["c"], 0) + 1
    top = sorted(citta.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
    tot_slide = len(scelti) + 3
    slide = []
    luci = "".join(f'<span style="position:absolute;left:{x}%;top:{y}%;width:90px;height:90px;border-radius:50%;background:radial-gradient(circle,#fff 0,{c} 28%,transparent 70%)"></span>'
                   for x, y, c in [(12, 18, "#FFC55C"), (80, 14, "#CFE36B"), (8, 76, "#FFC55C"), (82, 80, "#FFC55C"), (46, 86, "#FFC55C"), (30, 9, "#FFC55C")][:max(3, len(scelti))])
    slide.append(f"""{luci}<div class="centro"><h1>Le prime <span class="d">luci</span><br>d'Italia 🌙</h1>
      <p class="sub">{tutti} animali hanno già acceso<br>la loro luce sulla mappa.<br>Eccone {len(scelti)} →</p></div>""")
    for i, a in enumerate(scelti):
        cls = "c" if a["t"] == "gatto" else "d"
        corona = f'<span class="corona">👑 {E(a["ruolo"])}</span>' if a.get("ruolo") else ""
        slide.append(f"""<span class="num">{i + 2}/{tot_slide}</span><div class="centro">{D[a["id"]]["svg"]}<span class="targa {cls}">{E(a["n"].upper())}</span>
          <span class="chi">@{E(a["u"])}</span><span class="dove">{E(etichetta(a, D[a["id"]]))} · {E(a["c"])} ({E(a["p"])})</span>{corona}</div>""")
    righe = "".join(f'<li><b>{i + 1}</b><span>{E(c)}</span><span>{n} {"luce" if n == 1 else "luci"}</span></li>' for i, (c, n) in enumerate(top))
    slide.append(f"""<span class="num">{tot_slide - 1}/{tot_slide}</span><div class="centro"><h1 style="font-size:84px"><span class="d">{E(top[0][0])}</span> è in testa</h1><ol>{righe}</ol>
      <p class="sub">La tua città dov'è?</p></div>""")
    slide.append(f"""<span class="num">{tot_slide}/{tot_slide}</span><div class="centro"><h1 style="font-size:88px">Accendi<br>la <span class="d">tua</span> luce</h1>
      <p class="sub">Commenta con città, nome e razza:</p><span class="esempio">Treviso, Luna, golden</span>
      <p class="sub">👥 Tagga un amico: <b class="d">+3 punti</b><br>per ognuno che commenta</p><span class="bottone">👇 Commenta qui sotto</span></div>""")
    fatti = []
    for n, corpo in enumerate(slide, 1):
        h = out / f"slide-{n}.html"; h.write_text(TESTA + corpo + CODA)
        png = out / f"slide-{n}.png"
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1", "--window-size=1080,1350",
                        "--virtual-time-budget=6000", f"--user-data-dir={out / '.chrome'}", f"--screenshot={png}", h.as_uri()],
                       capture_output=True, check=True)
        jpg = out / f"slide-{n}.jpg"
        subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "90", str(png), "--out", str(jpg)], capture_output=True, check=True)
        png.unlink(); fatti.append(jpg.name)
    tag = " ".join("@" + a["u"] for a in scelti)
    (out / "didascalia.txt").write_text(
        f"Le prime luci d'Italia 🌙 {tutti} animali hanno già acceso la loro luce sulla mappa di Zampe d'Italia.\n\n"
        f"Grazie ai primi giocatori: {tag} 🐾\n\n{E(top[0][0])} è in testa. La tua città dov'è?\n"
        "Commenta con città, nome e razza (per esempio «Treviso, Luna, golden») e accendi la tua luce col tuo @.\n"
        "👥 Tagga un amico: per ognuno che commenta, +3 punti per te.\n\n#cani #gatti #italia #canicontrogatti\n")
    print(" ".join(fatti))

if __name__ == "__main__":
    main()
