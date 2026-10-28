"""Dal copione al video: voce, scene, sottotitoli, musica, controllo e rendering di un reel automatico.

Uso: python3 reel/costruisci.py <copione.json> <cartella-uscita>
Il copione (scritto da motore/copione.py) è:
  {"id": "...", "testata": {"titolo": "CANI vs GATTI"} | {"titolo": "GIORNO 2"}, "conteggio": {"cani": 2, "gatti": 0},
   "frasi": [{"testo": "Cani contro Gatti.", "scena": {"tipo": "duello", ...}}, ...],
   "banner": "📍 Scrivi città, nome e razza 👇", "didascalia": "..."}
Serve ELEVENLABS_API_KEY nell'ambiente (o nel Portachiavi del Mac). Esce con errore, senza video, se un controllo fallisce.
"""
import base64, inspect, json, math, os, re, shutil, subprocess, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "reel" / "modello"))
import scene as S  # noqa: E402

FONTS = ROOT / "reel/lancio-hf/assets/fonts"

def chiave_voce():
    k = os.environ.get("ELEVENLABS_API_KEY")
    if k: return k
    return subprocess.run(["security", "find-generic-password", "-a", "zampe", "-s", "zampe-elevenlabs", "-w"],
                          capture_output=True, text=True, check=True).stdout.strip()

def voce(testo, uscita):
    cfg = json.loads((ROOT / "reel/voce.json").read_text())
    body = {"text": testo, "model_id": cfg["model_id"], "voice_settings": cfg["voice_settings"]}
    r = urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{cfg["voice_id"]}/with-timestamps?output_format=mp3_44100_128',
                               data=json.dumps(body).encode(), headers={"xi-api-key": chiave_voce(), "Content-Type": "application/json"})
    d = json.loads(urllib.request.urlopen(r, timeout=180).read())
    Path(uscita).write_bytes(base64.b64decode(d["audio_base64"]))
    a = d["alignment"]; parole, cur, s, e = [], "", None, None
    for c, x, y in zip(a["characters"], a["character_start_times_seconds"], a["character_end_times_seconds"]):
        if c.isspace():
            if cur: parole.append({"p": cur, "s": round(s, 3), "e": round(e, 3)}); cur = ""
            continue
        if not cur: s = x
        cur += c; e = y
    if cur: parole.append({"p": cur, "s": round(s, 3), "e": round(e, 3)})
    return parole

# ---------- mappa: proiezione dell'Italia nel fotogramma (come nei reel di lancio) ----------
BOX, LON, LAT = (90, 330, 990, 1190), (6.6, 18.6), (36.6, 47.1)
_mx = lambda l: math.radians(l)
_my = lambda l: math.log(math.tan(math.pi / 4 + math.radians(l) / 2))
_k = min((BOX[2] - BOX[0]) / (_mx(LON[1]) - _mx(LON[0])), (BOX[3] - BOX[1]) / (_my(LAT[1]) - _my(LAT[0])))
_ox = (BOX[0] + BOX[2]) / 2 - _k * (_mx(LON[0]) + _mx(LON[1])) / 2
_oy = (BOX[1] + BOX[3]) / 2 + _k * (_my(LAT[0]) + _my(LAT[1])) / 2
def proietta(lng, lat): return round(_ox + _k * _mx(lng), 1), round(_oy - _k * _my(lat), 1)

def italia():
    G = json.loads((ROOT / "dati/regioni_s.json").read_text())
    ring = lambda r: "M" + "L".join(f"{a} {b}" for a, b in (proietta(*p) for p in r)) + "Z"
    return "".join("".join(ring(r) for r in poly) for f in G["features"]
                   for poly in ([f["geometry"]["coordinates"]] if f["geometry"]["type"] == "Polygon" else f["geometry"]["coordinates"]))

def comune(nome):
    for c, p, r, lat, lng in json.loads((ROOT / "dati/comuni_min.json").read_text()):
        if c.lower() == nome.lower(): return lng, lat
    raise SystemExit(f"Comune sconosciuto nel copione: {nome}")

# ---------- disegni dalla fabbrica ----------
def disegni(chiavi, cartella):
    """chiavi: [("cane"|"gatto", razza, seme)] → assets/svg/<razza>-<seme>.svg"""
    js = f"""const fs=require("fs"); global.window={{}}; eval(fs.readFileSync({json.dumps(str(ROOT / "docs/disegni.js"))},"utf8"));
const D=window.Disegni; D.carica(JSON.parse(fs.readFileSync({json.dumps(str(ROOT / "docs/data/razze.json"))},"utf8")));
for (const [t,k,s] of {json.dumps(chiavi)}) {{ const svg=(t==="gatto"?D.gatto(k,s):D.cane(k,s)).replace("<svg ","<svg xmlns=\\"http://www.w3.org/2000/svg\\" ");
  fs.writeFileSync({json.dumps(str(cartella))}+"/"+k+"-"+s+".svg", svg); }}"""
    subprocess.run(["node", "-e", js], check=True)

def svg_di(t, razza, seme, serve):
    serve.add((t, razza, seme)); return f"{razza}-{seme}.svg"

# ---------- sottotitoli: 1–3 parole per gruppo, spezzate su virgole e punti ----------
def gruppi_sottotitoli(frasi):
    out = []
    for f in frasi:
        w, cur = f.split(), []
        for x in w:
            cur.append(x)
            if len(cur) == 3 or re.search(r"[,.!?:…]$", x):
                out.append(" ".join(cur)); cur = []
        if cur: out.append(" ".join(cur))
    return out

INDEX = """<!doctype html>
<html lang="it" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" /><meta name="viewport" content="width=1080, height=1920" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      /* Reel automatico di Zampe d'Italia: {nota} */
      @font-face {{ font-family: "Bricolage Grotesque"; font-weight: 800; src: url("assets/fonts/bric800.woff2") format("woff2"); }}
      @font-face {{ font-family: "Bricolage Grotesque"; font-weight: 700; src: url("assets/fonts/bric700.woff2") format("woff2"); }}
      :root {{ --night: #060B1A; --night2: #0E1A3A; --gold: #FFC55C; --warm: #FFB347; --cream: #FFF4DE; --cat: #CFE36B;
        --font-display: "Bricolage Grotesque", "Nunito", sans-serif; --font-body: "Nunito", sans-serif; }}
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: var(--night); }}
      #root {{ position: relative; width: 100%; height: 100%; font-family: var(--font-body); color: var(--cream); }}
      .bg {{ position: absolute; inset: 0; background: radial-gradient(ellipse 80% 55% at 50% 42%, #18295A 0, var(--night2) 45%, var(--night) 100%); }}
      #testata {{ position: absolute; left: 0; right: 0; top: 186px; z-index: 5; display: flex; justify-content: center; }}
      #testata .pill {{ display: flex; align-items: center; gap: 22px; padding: 14px 34px; border-radius: 999px; background: rgba(6,11,26,.82);
        border: 3px solid rgba(255,197,92,.75); box-shadow: 0 0 40px rgba(255,197,92,.25); }}
      #testata .t {{ font: 800 46px/1 var(--font-display); color: var(--gold); letter-spacing: -.5px; }}
      #testata .n {{ font: 900 40px/1 var(--font-body); padding-left: 22px; border-left: 3px solid rgba(255,244,222,.25); }}
      #banner {{ position: absolute; left: 0; right: 0; top: 298px; z-index: 5; display: flex; justify-content: center; }}
      #banner span {{ font: 900 34px/1 var(--font-body); padding: 14px 28px; border-radius: 18px; background: var(--gold); color: #2A1606; box-shadow: 0 0 34px rgba(255,197,92,.55); }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{durata}" data-width="1080" data-height="1920">
      <div class="bg"></div>
{host}
      <div id="testata" class="clip" data-start="0" data-duration="{durata}" data-track-index="2" data-track-kind="graphics">
        <div class="pill" id="testata-pill"><span class="t">{titolo}</span><span class="n">🐶 {cani} – {gatti} 🐱</span></div>
      </div>
      <div id="banner" class="clip" data-start="{b0}" data-duration="{bd}" data-track-index="3" data-track-kind="graphics"><span id="banner-t">{banner}</span></div>
      <div id="sottotitoli" data-composition-id="sottotitoli" data-composition-src="compositions/sottotitoli.html" data-start="0" data-duration="{durata}" data-track-index="4" data-track-kind="captions" data-width="1080" data-height="1920" style="z-index:6"></div>
      <audio id="voce" class="clip" src="assets/audio/voce.mp3" data-start="0" data-duration="{dvoce}" data-track-index="5" data-volume="1"></audio>
      <audio id="musica" class="clip" src="assets/audio/musica.wav" data-start="0" data-duration="{durata}" data-track-index="6" data-volume="0.22" data-fade-out="0.8"></audio>
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      tl.fromTo("#testata-pill", {{ y: -30, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.35, ease: "back.out(2)" }}, 0.05);
      tl.fromTo("#banner-t", {{ scale: 0.6, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.3, ease: "back.out(2.4)" }}, {b0});
      window.__timelines["main"] = tl;
      tl.seek(0);
    </script>
  </body>
</html>
"""

def main():
    copione = json.loads(Path(sys.argv[1]).read_text())
    out = Path(sys.argv[2]); prog = out / "hf"
    if prog.exists(): shutil.rmtree(prog)
    for d in ("compositions", "assets/audio", "assets/svg", "assets/fonts"): (prog / d).mkdir(parents=True, exist_ok=True)
    for f in FONTS.glob("*.woff2"): shutil.copy(f, prog / "assets/fonts" / f.name)
    shutil.copy(ROOT / "reel/lancio-hf/hyperframes.json", prog / "hyperframes.json")
    shutil.copy(ROOT / "reel/lancio-hf/package.json", prog / "package.json")
    (prog / "meta.json").write_text(json.dumps({"id": copione["id"], "name": copione["id"]}))

    frasi = [f["testo"].strip() for f in copione["frasi"]]
    parole = voce(" ".join(frasi), prog / "assets/audio/voce.mp3")
    (out / "parole.json").write_text(json.dumps({"parole": parole}, ensure_ascii=False))

    # inizio di ogni frase = prima parola della frase nella voce
    inizi, i = [], 0
    for f in frasi:
        inizi.append(0.0 if not inizi else max(0.0, parole[i]["s"] - 0.08)); i += len(f.split())
    if i != len(parole): raise SystemExit(f"La voce ha {len(parole)} parole, il copione {i}: controllo fallito")
    fine_voce = parole[-1]["e"]; durata = round(fine_voce + 0.95, 2)
    if not 12 <= durata <= 40: raise SystemExit(f"Durata {durata}s fuori dai limiti (12–40 s)")

    serve, host, effetti = set(), [], {"durata": durata, "whoosh": [], "pop": [], "chime": []}
    ita = italia() if any(f["scena"]["tipo"] == "mappa" for f in copione["frasi"]) else ""
    for n, f in enumerate(copione["frasi"]):
        sc = dict(f["scena"]); tipo = sc.pop("tipo"); cid = f"s{n}"
        a = round(inizi[n], 2); b = round(inizi[n + 1], 2) if n + 1 < len(inizi) else durata; d = round(b - a, 2)
        if tipo in ("cuccia", "gatto"):
            sc["svg"] = svg_di("gatto" if tipo == "gatto" else "cane", sc.pop("razza"), sc.pop("seme", n + 3), serve)
        if tipo == "vetrina":
            sc["animali"] = [{"svg": svg_di(x["t"], x["razza"], x.get("seme", k + 1), serve), "nome": x["nome"], "t": x["t"]} for k, x in enumerate(sc["animali"])]
        if tipo in ("duello", "chiusura"):
            sc.setdefault("svg_su", svg_di("cane", "golden", 7, serve)); sc.setdefault("svg_giu", svg_di("gatto", "rosso", 5, serve))
        if tipo == "mappa":
            sc["italia"] = ita
            sc["subito"] = n == 0  # mai aprire sul buio
            sc["citta"] = [{**c, **dict(zip(("x", "y"), proietta(*comune(c["nome"]))))} for c in sc.get("citta", [])]
            sc["luci"] = [{"x": x, "y": y, "t": l["t"]} for l in sc.get("luci", []) for x, y in [proietta(l["lng"], l["lat"])]]
            if sc.get("zoom"): x, y = proietta(*comune(sc["zoom"]["comune"])); sc["zoom"] = {"s": sc["zoom"].get("s", 1.8), "x": x, "y": y}
        firma = inspect.signature(S.TIPI[tipo]).parameters  # i campi solo per la didascalia (utente, comune…) non arrivano alla scena
        if not any(x.kind == x.VAR_KEYWORD for x in firma.values()):
            sc = {k: v for k, v in sc.items() if k in firma}
        pagina = S.TIPI[tipo](cid, d, **sc)
        if n == 0 and tipo != "mappa":  # mai aprire sul buio (la mappa ha già la sua versione "subito")
            testa, js = pagina.split("<script>", 1)
            pagina = testa + "<script>" + S._primo_fotogramma(js)
        (prog / "compositions" / f"{cid}.html").write_text(pagina)
        host.append(f'      <div id="{cid}" data-composition-id="{cid}" data-composition-src="compositions/{cid}.html" data-start="{a}" data-duration="{d}" data-track-index="1" data-track-kind="graphics" data-width="1080" data-height="1920" style="z-index:1"></div>')
        if n: effetti["whoosh"].append(a)
        effetti["pop"].append(round(a + 0.45, 2))
    effetti["riser"] = round(inizi[-1], 2)
    disegni(sorted(serve), prog / "assets/svg")

    c = copione.get("conteggio", {"cani": 0, "gatti": 0})
    b0 = round(inizi[1] if len(inizi) > 1 else 0.5, 2)
    (prog / "index.html").write_text(INDEX.format(nota=copione.get("formato", ""), durata=durata, host="\n".join(host), titolo=S.ESC(copione["testata"]["titolo"]),
        cani=c["cani"], gatti=c["gatti"], b0=b0, bd=round(inizi[-1] - b0, 2), banner=S.ESC(copione.get("banner", "📍 Scrivi città, nome e razza 👇")),
        dvoce=round(fine_voce + 0.1, 2)))
    subprocess.run([sys.executable, str(ROOT / "reel/sottotitoli.py"), str(out / "parole.json"), str(prog), str(durata), *gruppi_sottotitoli(frasi)], check=True)
    (out / "effetti.json").write_text(json.dumps(effetti))
    subprocess.run([sys.executable, str(ROOT / "reel/musica.py"), str(out / "effetti.json"), str(prog / "assets/audio/musica.wav")], check=True)

    # controlli: nessun errore di HyperFrames, poi rendering e volume per Instagram
    chk = subprocess.run(["npx", "hyperframes", "check", "--json"], cwd=prog, capture_output=True, text=True)
    raw = chk.stdout[chk.stdout.find("{"):]
    errori = [m for m in re.findall(r'"severity":\s*"error"[^}]*', raw)]
    if errori: raise SystemExit("Controllo HyperFrames fallito:\n" + "\n".join(errori[:5]))
    subprocess.run(["npx", "hyperframes", "render", "--output", str(out / "render.mp4")], cwd=prog, check=True)
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(out / "render.mp4"), "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.0:LRA=7",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", str(out / "reel.mp4")], check=True)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out / "reel.mp4")], capture_output=True, text=True).stdout)
    if abs(dur - durata) > 0.5: raise SystemExit(f"Il video dura {dur}s invece di {durata}s")
    (out / "didascalia.txt").write_text(copione["didascalia"].strip() + "\n")
    print(f"reel pronto: {out / 'reel.mp4'} · {dur:.1f} s")

if __name__ == "__main__":
    main()
