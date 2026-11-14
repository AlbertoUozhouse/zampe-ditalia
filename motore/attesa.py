"""I reel in attesa del token (14/11: Instagram ha invalidato il token e il reel delle 13 è stato l'ultimo a uscire).

Se al momento di pubblicare il token non funziona, reel.yml non butta il reel: lo mette in coda qui (motore/in_attesa.json)
e non lancia la riserva. La veglia (commenti.py, a ogni giro) prova la coda: appena il token torna valido pubblica
il reel più recente ancora fresco (al massimo 3 ore), se nell'ultima ora non è uscito altro. I più vecchi restano sul sito.
La coda non si svuota mai a mano: un reel conta come fatto quando il suo video è in motore/pubblicati.json.

Uso: python3 motore/attesa.py controlla              (esce 1 se il token non va, e stampa l'errore di Instagram)
     python3 motore/attesa.py aggiungi -- <argomenti di pubblica.py>
     python3 motore/attesa.py pubblica
"""
import json, os, subprocess, sys, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CODA = ROOT / "motore/in_attesa.json"
PUBBLICATI = ROOT / "motore/pubblicati.json"
FRESCO = timedelta(hours=3)


def token_ok():
    """(True, "") se Instagram accetta il token, altrimenti (False, messaggio di Instagram, che non contiene il token)."""
    sys.path.insert(0, str(ROOT / "motore"))
    from pubblica import chiama
    token = os.environ.get("IG_TOKEN")
    if not token: return False, "manca IG_TOKEN"
    try:
        chiama("GET", "me", token, fields="id")
        return True, ""
    except SystemExit as e:
        return False, str(e)


def _leggi(p, vuoto):
    try: return json.loads(p.read_text())
    except (FileNotFoundError, json.JSONDecodeError): return vuoto


def _media(args):
    return args[args.index("--media") + 1] if "--media" in args else ""


def pubblica():
    coda = _leggi(CODA, [])
    if not coda: return
    ora = datetime.now(timezone.utc)
    usciti = _leggi(PUBBLICATI, [])
    fatti = {x.get("media") for x in usciti}
    freschi = [x for x in coda if _media(x["args"]) not in fatti and ora - datetime.fromisoformat(x["ts"]) < FRESCO]
    if not freschi: return
    ok, err = token_ok()
    if not ok:
        print(f"attesa: {len(freschi)} reel in coda, il token non va ancora ({err})"); return
    if any(ora - datetime.fromisoformat(x["ts"]) < timedelta(hours=1) for x in usciti if x.get("tipo") == "REELS"):
        print("attesa: è uscito un reel meno di un'ora fa, il reel in coda aspetta"); return
    x = max(freschi, key=lambda x: x["ts"])
    sito = os.environ.get("SITO_MEDIA") or "https://zampeditalia.it/"
    try:
        if urllib.request.urlopen(urllib.request.Request(sito + _media(x["args"]), method="HEAD"), timeout=20).status != 200: raise OSError
    except Exception:
        print(f"attesa: il video {_media(x['args'])} non è ancora sul sito"); return
    print(f"attesa: il token è tornato valido, pubblico {_media(x['args'])}")
    subprocess.run([sys.executable, "-I", str(ROOT / "motore/pubblica.py"), *x["args"]], check=True)


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "controlla":
        ok, err = token_ok()
        if not ok: sys.exit(f"Token di Instagram non valido: {err}")
        print("token di Instagram valido")
    elif cmd == "aggiungi":
        args = sys.argv[sys.argv.index("--") + 1:]
        coda = _leggi(CODA, [])
        coda.append({"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "args": args})
        CODA.write_text(json.dumps(coda[-20:], ensure_ascii=False, indent=1) + "\n")
        print(f"attesa: {_media(args)} in coda, parte appena il token torna valido")
    elif cmd == "pubblica":
        pubblica()
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
