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

def poco_fa(ora, minuti=75):
    """True se è uscito un reel negli ultimi `minuti` (motore/pubblicati.json)."""
    try: reel = [x["ts"] for x in json.loads((ROOT / "motore/pubblicati.json").read_text()) if x["tipo"] == "REELS"]
    except (FileNotFoundError, json.JSONDecodeError): return False
    return bool(reel) and ora - datetime.fromisoformat(max(reel)) < timedelta(minutes=minuti)

def annulla():
    """Il lancio non è partito (GitHub ha risposto con un errore): l'ultimo orario segnato oggi torna libero per il prossimo giro."""
    st = json.loads(STORICO.read_text())
    fatti = st.get("lanciati", {}).get(datetime.now(ZoneInfo("Europe/Rome")).date().isoformat(), [])
    if fatti:
        fatti.pop()
        STORICO.write_text(json.dumps(st, ensure_ascii=False, indent=1))

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
            if poco_fa(ora):  # due reel troppo vicini sembrano uguali e si rubano le visualizzazioni: questo orario salta
                fatti.append(hhmm); STORICO.write_text(json.dumps(st, ensure_ascii=False, indent=1)); return
            fatti.append(hhmm)
            st["lanciati"] = {k: v for k, v in st["lanciati"].items() if k >= (ora.date() - timedelta(days=7)).isoformat()}
            STORICO.write_text(json.dumps(st, ensure_ascii=False, indent=1))
            if formato.startswith("attivita"):  # col negozio aperto, quello slot fa il reel degli accessori
                try:
                    if any(str(u).startswith("https://") for u in cfg.get("negozio", {}).values()): formato = "negozio" + formato[len("attivita"):]
                except AttributeError: pass
            print(formato)
            return

if __name__ == "__main__":
    import sys
    if sys.argv[1:2] == ["--poco-fa"]: sys.exit(0 if poco_fa(datetime.now(ZoneInfo("Europe/Rome")), int(sys.argv[2])) else 1)
    annulla() if sys.argv[1:] == ["--annulla"] else main()
