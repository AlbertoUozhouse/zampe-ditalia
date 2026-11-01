"""Un reel già montato a mano (docs/media/<nome>.mp4 + docs/contenuti/<nome>.txt) passato a reel.yml come se fosse automatico.

Uso: python3 reel/pronto.py <nome> /tmp/copione.json /tmp/reel   (in config.json: "una_tantum": {"AAAA-MM-GG HH:MM": "pronto-<nome>"})
Se c'è anche docs/contenuti/<nome>.voce.txt, sopra il video va la voce che spiega (come nei reel automatici), con la musica più bassa:
un gioco nuovo senza nessuno che dica cosa fare non si capisce (Alberto, 1/11).
"""
import json, shutil, subprocess, sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
nome, copione, out = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
out.mkdir(parents=True, exist_ok=True)
shutil.copy(ROOT / f"docs/media/{nome}.mp4", out / "reel.mp4")
shutil.copy(ROOT / f"docs/contenuti/{nome}.txt", out / "didascalia.txt")
testo_voce = ROOT / f"docs/contenuti/{nome}.voce.txt"
if testo_voce.exists():
    try:
        sys.path.insert(0, str(ROOT / "reel"))
        from costruisci import voce  # noqa: E402
        voce(testo_voce.read_text().strip(), out / "voce.mp3")
        muto = out / "senza_voce.mp4"; (out / "reel.mp4").rename(muto)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(muto), "-i", str(out / "voce.mp3"), "-filter_complex",
                        "[0:a]volume=0.3[m];[1:a]adelay=300|300,volume=1.0[v];[m][v]amix=inputs=2:duration=first:normalize=0[a]",
                        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(out / "reel.mp4")], check=True)
        print("voce aggiunta")
    except Exception as e:  # senza voce il reel esce lo stesso, con la sua musica
        print(f"voce non aggiunta ({type(e).__name__}): reel con la sola musica")
        if not (out / "reel.mp4").exists(): (out / "senza_voce.mp4").rename(out / "reel.mp4")
ora = datetime.now(ZoneInfo("Europe/Rome"))
copione.write_text(json.dumps({"id": ora.strftime("%Y-%m-%d-%H%M") + "-" + nome, "formato": "pronto", "testata": {"titolo": nome}, "tag": []}))
print(f"reel pronto: {nome}")
