"""L'apertura 3D del reel (reel.yml, passo «Apertura 3D»): un paese, oppure il DUELLO del testa a testa (11/11).

Nel duello i due paesi rivali stanno uno sopra l'altro, ognuno col suo nome e le sue luci, e il VS in mezzo:
si vede subito che è una gara tra due città vere. La regia (stile, effetto, volo) la sceglie il reparto Innovazione (motore/agenzia.py regia).

Uso: python3 reel/apertura3d.py <copione.json> <regia.json>   (scrive reel/assets/tmp/apertura3d.mp4 e aggiorna il copione)
"""
import json, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VOLO3D = str(ROOT / "reel/volo3d.js")
VOLI = ["discesa", "orbita", "radente", "rivelazione", "spirale"]


def main():
    cp, rp = Path(sys.argv[1]), Path(sys.argv[2])
    cop = json.loads(cp.read_text())
    regia = json.loads(rp.read_text()) if rp.exists() else {}
    i3 = cop.get("intro_3d")
    if not i3 or cop.get("intro"):
        print("nessuna apertura 3D per questo reel"); return
    out = ROOT / "reel/assets/tmp/apertura3d.mp4"; out.parent.mkdir(parents=True, exist_ok=True)
    sec = float(regia.get("secondi", 3.6))
    if i3.get("duello"):
        (a, na), (b, nb) = i3["duello"]
        tmp = Path(tempfile.mkdtemp())
        # sopra la città che guida, sotto quella che insegue; due voli diversi, così le due metà non si muovono uguali
        volo2 = VOLI[(VOLI.index(regia.get("volo", "orbita")) + 2) % len(VOLI)] if regia.get("volo") in VOLI else "spirale"
        pezzi = []
        for k, (c, n, volo, badge) in enumerate([(a, na, regia.get("volo", "orbita"), "VS"), (b, nb, volo2, None)]):
            r = tmp / f"r{k}.json"; r.write_text(json.dumps({**regia, "volo": volo}))
            opz = {"altezza": 480, "titolo": c.upper(), "sotto": f"{n} {'luce' if n == 1 else 'luci'}" + (" · in testa" if k == 0 and na > nb else " · pari" if na == nb else ""), **({"badge": badge} if badge else {})}
            subprocess.run(["node", VOLO3D, c, "", str(tmp / f"p{k}.mp4"), str(sec), str(r), json.dumps(opz)], check=True)
            pezzi.append(str(tmp / f"p{k}.mp4"))
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", pezzi[0], "-i", pezzi[1], "-filter_complex",
                        "[0:v][1:v]vstack=inputs=2,drawbox=x=0:y=958:w=1080:h=4:color=0xFFC55C@0.9:t=fill,format=yuv420p[v]", "-map", "[v]",
                        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-movflags", "+faststart", str(out)], check=True)
    else:
        subprocess.run(["node", VOLO3D, i3["comune"], i3.get("nome", ""), str(out), str(sec), str(rp)], check=True)
    cop.update({"intro": "reel/assets/tmp/apertura3d.mp4", "intro_durata": sec, "regia_3d": regia})
    cp.write_text(json.dumps(cop, ensure_ascii=False))
    print(f"apertura 3D pronta: {'duello ' + ' – '.join(x[0] for x in i3['duello']) if i3.get('duello') else i3['comune']}")


if __name__ == "__main__":
    main()
