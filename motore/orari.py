"""Dice alla guardia se è l'ora di un reel automatico. Stampa il formato da lanciare, oppure niente.

Un orario vale per 50 minuti dopo l'ora prevista (la guardia gira ogni 10 minuti) e si lancia una volta sola al giorno.
Legge motore/config.json (interruttore e orari) e segna i lanci in motore/reel_fatti.json.
"""
import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
CONFIG, STORICO = ROOT / "motore/config.json", ROOT / "motore/reel_fatti.json"

def main():
    cfg = json.loads(CONFIG.read_text())
    if not cfg.get("reel_automatici"):
        return
    ora = datetime.now(ZoneInfo("Europe/Rome"))
    try:
        st = json.loads(STORICO.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        st = {}
    oggi = ora.date().isoformat()
    fatti = st.setdefault("lanciati", {}).setdefault(oggi, [])
    for hhmm, formato in sorted(cfg["orari"].items()):
        h, m = map(int, hhmm.split(":"))
        inizio = ora.replace(hour=h, minute=m, second=0, microsecond=0)
        if hhmm not in fatti and inizio <= ora < inizio + timedelta(minutes=50):
            fatti.append(hhmm)
            st["lanciati"] = {k: v for k, v in st["lanciati"].items() if k >= (ora.date() - timedelta(days=7)).isoformat()}
            STORICO.write_text(json.dumps(st, ensure_ascii=False, indent=1))
            print(formato)
            return

if __name__ == "__main__":
    main()
