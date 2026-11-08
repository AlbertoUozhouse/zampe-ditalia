"""Dice alla guardia se è l'ora di un reel automatico. Stampa il formato da lanciare, oppure niente.

Un orario vale per 50 minuti dopo l'ora prevista (la guardia gira ogni 10 minuti) e si lancia una volta sola al giorno.
Legge motore/config.json (interruttore e orari) e segna i lanci in motore/reel_fatti.json.
"""
import json, os
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
    orari = dict(cfg["orari"])
    giorno_sett = ["lun", "mar", "mer", "gio", "ven", "sab", "dom"][ora.weekday()]  # i reel di ogni settimana (la Coppa delle Zampe): «lun 13:00»
    orari.update({k[4:]: v for k, v in cfg.get("settimanali", {}).items() if k[:3] == giorno_sett})
    orari.update({k[11:]: v for k, v in cfg.get("una_tantum", {}).items() if k[:10] == oggi})  # reel di un giorno solo, «AAAA-MM-GG HH:MM»
    orari.update(piano_test(cfg, ora, giorno_sett))
    for hhmm, formato in sorted(orari.items()):
        h, m = map(int, hhmm.split(":"))
        inizio = ora.replace(hour=h, minute=m, second=0, microsecond=0)
        if hhmm not in fatti and inizio <= ora < inizio + timedelta(minutes=50):
            if poco_fa(ora):  # due reel troppo vicini sembrano uguali e si rubano le visualizzazioni: questo orario salta
                fatti.append(hhmm); STORICO.write_text(json.dumps(st, ensure_ascii=False, indent=1)); return
            fatti.append(hhmm)
            # 4/11: senza foto nuove la star non salta più: copione.py fa il fondatore (con 2 reel al giorno i commenti nuovi sono crollati, da 711 a 91)
            st["lanciati"] = {k: v for k, v in st["lanciati"].items() if k >= (ora.date() - timedelta(days=7)).isoformat()}
            STORICO.write_text(json.dumps(st, ensure_ascii=False, indent=1))
            if formato.startswith("attivita"):  # col negozio aperto, quello slot fa il reel degli accessori
                try:
                    if os.environ.get("STRIPE_KEY") and any(str(u).startswith("https://") for u in cfg.get("negozio", {}).values()): formato = ("presidente" if ora.toordinal() % 2 else "negozio") + formato[len("attivita"):]  # un giorno i Presidenti, uno il negozio
                except AttributeError: pass
            print(formato)
            return
    f = festa(ora, st, fatti)
    if f: print(f)

def piano_test(cfg, ora, giorno_sett):
    """Test di crescita (config «test_crescita», 8/11): per 7 giorni dal giorno «dal», alle 13 e alle 18 un reel di scoperta e uno di aggiornamento
    (si alternano gli slot), alle 21 un reel solo se c'è una storia con un motivo per uscire. I reel della Coppa delle 21 (giovedì, domenica) restano."""
    t = cfg.get("test_crescita") or {}
    if t.get("stato") != "attivo" or not t.get("dal"): return {}
    g = (ora.date() - datetime.fromisoformat(t["dal"]).date()).days
    if not 0 <= g < len(t.get("piano", [])): return {}
    out = dict(t["piano"][g])
    if t.get("sera") and f"{giorno_sett} 21:00" not in cfg.get("settimanali", {}): out["21:00"] = t["sera"]
    return out

def foto_nuove(st):
    """Ci sono foto della star (stato «ugc», col SÌ di chi le ha mandate) non ancora usate in un reel?"""
    try: ugc = json.loads((ROOT / "motore/stato.json").read_text()).get("ugc", [])
    except (FileNotFoundError, json.JSONDecodeError): return False
    fatte = set(st.get("star_fatte", []))
    return any(x["f"] not in fatte and (ROOT / "docs/media/ugc" / x["f"]).exists() for x in ugc)

def festa(ora, st, fatti):
    """Un nuovo Presidente di regione (stato «feste_presidente», scritto da commenti.py) ha il suo reel di festa appena c'è spazio:
    tra le 10 e le 22, mai a meno di 75 minuti da un altro reel. Ogni acquisto che fa un Presidente diventa una vetrina."""
    if not 10 <= ora.hour < 22 or poco_fa(ora): return None
    try:  # 2/11: niente reel in più fuori orario (neopresidente 1.342 views); i Presidenti li festeggia il reel delle 11:30
        if not json.loads((ROOT / "motore/config.json").read_text()).get("feste_reel", True): return None
    except (FileNotFoundError, json.JSONDecodeError): pass
    try: feste = json.loads((ROOT / "motore/stato.json").read_text()).get("feste_presidente", [])
    except (FileNotFoundError, json.JSONDecodeError): return None
    nuove = [f for f in feste if f not in st.setdefault("feste_fatte", [])]
    if not nuove: return None
    st["feste_fatte"] = (st["feste_fatte"] + [nuove[0]])[-30:]
    st["presidente_festa"] = nuove[0].split("|")[0]  # copione.py → neopresidente
    fatti.append(ora.strftime("%H:%M"))
    STORICO.write_text(json.dumps(st, ensure_ascii=False, indent=1))
    return "neopresidente"

if __name__ == "__main__":
    import sys
    if sys.argv[1:2] == ["--poco-fa"]: sys.exit(0 if poco_fa(datetime.now(ZoneInfo("Europe/Rome")), int(sys.argv[2])) else 1)
    annulla() if sys.argv[1:] == ["--annulla"] else main()
