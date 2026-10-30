"""Un reel già montato a mano (docs/media/<nome>.mp4 + docs/contenuti/<nome>.txt) passato a reel.yml come se fosse automatico.

Uso: python3 reel/pronto.py <nome> /tmp/copione.json /tmp/reel   (in config.json: "una_tantum": {"AAAA-MM-GG HH:MM": "pronto-<nome>"})
"""
import json, shutil, sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
nome, copione, out = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
out.mkdir(parents=True, exist_ok=True)
shutil.copy(ROOT / f"docs/media/{nome}.mp4", out / "reel.mp4")
shutil.copy(ROOT / f"docs/contenuti/{nome}.txt", out / "didascalia.txt")
ora = datetime.now(ZoneInfo("Europe/Rome"))
copione.write_text(json.dumps({"id": ora.strftime("%Y-%m-%d-%H%M") + "-" + nome, "formato": "pronto", "testata": {"titolo": nome}, "tag": []}))
print(f"reel pronto: {nome}")
