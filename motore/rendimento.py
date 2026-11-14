"""Quanto rende ogni reel: legge da Instagram i numeri dei reel in motore/pubblicati.json e li confronta per formato.

Uso: python3 motore/rendimento.py   (serve IG_TOKEN)
Scrive motore/rendimento.json (solo numeri, nessun nome) e stampa una tabella per formato.
"""
import json, os, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pubblica import chiama  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
METRICHE = ["views", "reach", "likes", "comments", "shares", "saved", "total_interactions", "ig_reels_avg_watch_time", "follows", "profile_visits"]

ERRORI = []  # i messaggi d'errore di Instagram (non contengono il token): si stampano alla fine

class Limite(Exception):
    """Instagram ha detto basta chiamate per ora: si smette subito, così non si peggiora."""

def _chiama(mid, token, metriche):
    try:
        return chiama("GET", f"{mid}/insights", token, metric=metriche)["data"]
    except SystemExit as e:  # chiama() esce con SystemExit sugli errori di Instagram
        ERRORI.append(str(e))
        if re.search(r"limit|too many|troppe", str(e), re.I): raise Limite(str(e))
        raise

def numeri(mid, token):
    out = {}
    try:  # prima tutte insieme; se Instagram ne rifiuta una, una alla volta
        dati = _chiama(mid, token, ",".join(METRICHE))
    except SystemExit:
        dati = []
        for m in METRICHE:
            try: dati += _chiama(mid, token, m)
            except SystemExit: pass
    for d in dati:
        v = d.get("values", [{}])[0].get("value", d.get("total_value", {}).get("value"))
        if isinstance(v, (int, float)): out[d["name"]] = v
    return out

def attribuisci(righe, reel):
    """Follower portati da ogni reel (7/11): quelli arrivati tra la sua uscita e il reel dopo (al massimo 6 ore), dai cambi registrati
    da commenti.py (stato «follower_ore»), e quanti ogni 1.000 account raggiunti. È una stima: chi segue per un reel vecchio conta per l'ultimo.
    I reel sponsorizzati (config.json «sponsorizzati») si tengono a parte."""
    from datetime import datetime, timedelta
    ore = [(datetime.fromisoformat(t), n) for t, n in json.loads((ROOT / "motore/stato.json").read_text()).get("follower_ore", [])]
    spons = set(json.loads((ROOT / "motore/config.json").read_text()).get("sponsorizzati", []))
    def n_a(t):
        prima = [n for tt, n in ore if tt <= t]
        return prima[-1] if prima else None
    tempi = [datetime.fromisoformat(x["ts"]) for x in reel]
    for i, (r, x) in enumerate(zip(righe, reel)):
        r["sponsorizzato"] = x["id"] in spons
        if not ore or tempi[i] < ore[0][0]: continue  # prima del 7/11 i follower si contavano solo una volta al giorno
        fine = min(tempi[i + 1] if i + 1 < len(tempi) else tempi[i] + timedelta(hours=6), tempi[i] + timedelta(hours=6))
        if fine > ore[-1][0] + timedelta(minutes=30): continue  # finestra non ancora chiusa
        a, b = n_a(tempi[i]), n_a(fine)
        if a is None or b is None: continue
        r["follower_dopo"] = b - a
        if r.get("reach"): r["follower_ogni_1000"] = round(1000 * (b - a) / r["reach"], 1)

def fotografa(righe):
    """Una fotografia al giorno dei numeri di ogni reel, per giorni dalla pubblicazione (motore/rendimento_storia.json):
    il verbale dei 7 giorni confronta reel diversi alla stessa distanza dall'uscita."""
    from datetime import datetime, timezone
    p = ROOT / "motore/rendimento_storia.json"
    st = json.loads(p.read_text()) if p.exists() else {}
    ora = datetime.now(timezone.utc)
    for r in righe:
        d = int((ora - datetime.fromisoformat(r["ts"])).total_seconds() // 86400)
        if d > 14 or r.get("views") is None or r.get("numeri_vecchi"): continue  # 14/11: mai una fotografia vuota o di numeri non riletti
        g = st.setdefault(r["id"], {})
        if g.get(f"g{d}", {}).get("views") is None: g[f"g{d}"] = {k: r.get(k) for k in ("views", "reach", "comments", "shares", "follower_dopo")}
    p.write_text(json.dumps(st, ensure_ascii=False, indent=0) + "\n")

def main():
    token = os.environ.get("IG_TOKEN") or sys.exit("Manca IG_TOKEN.")
    reel = [x for x in json.loads((ROOT / "motore/pubblicati.json").read_text()) if x["tipo"] == "REELS"]
    # 14/11: il giro delle 14:30 ha avuto errore da Instagram su tutti i reel e ha scritto righe vuote sopra i numeri buoni.
    # Ora un reel senza numeri nuovi tiene gli ultimi letti (numeri_vecchi), e se nessun reel ha numeri nuovi non si salva niente.
    vecchi = {r["id"]: r for r in json.loads((ROOT / "motore/rendimento.json").read_text())} if (ROOT / "motore/rendimento.json").exists() else {}
    righe, nuovi, fermo = [], 0, None
    for x in reel:
        m = re.search(r"(\d{4}-\d\d-\d\d)-(\d{4})-(\w+)\.mp4", x["media"])
        formato, quando = (m.group(3), f"{m.group(1)} {m.group(2)[:2]}:{m.group(2)[2:]}") if m else ("lancio", x["ts"][:16])
        n = {}
        if not fermo:
            try: n = numeri(x["id"], token)
            except Limite as e: fermo = str(e)
        if n: nuovi += 1
        elif not nuovi and len(righe) >= 2 and not fermo: fermo = "tre reel di fila senza numeri: errore di Instagram, non dei reel"
        else: n = {**{k: v for k, v in vecchi.get(x["id"], {}).items() if k in METRICHE}, "numeri_vecchi": True} if vecchi.get(x["id"], {}).get("views") is not None else {}
        righe.append({"quando": quando, "formato": formato, "ts": x["ts"], "id": x["id"], "file": Path(x["media"]).stem, **n})
    print(f"numeri nuovi da Instagram: {nuovi} reel su {len(reel)}" + (f" (fermato: {fermo})" if fermo else ""))
    for e in sorted(set(ERRORI))[:5]: print("  errore:", e, f"(×{ERRORI.count(e)})")
    if not nuovi: sys.exit("Nessun numero nuovo da Instagram: rendimento.json resta com'era.")
    attribuisci(righe, reel)
    fotografa(righe)
    (ROOT / "motore/rendimento.json").write_text(json.dumps(righe, ensure_ascii=False, indent=1) + "\n")
    chiavi = [k for k in METRICHE if any(k in r for r in righe)]
    print("quando            formato     " + " ".join(f"{k[:9]:>9}" for k in chiavi))
    for r in righe:
        print(f"{r['quando']:<17} {r['formato']:<11} " + " ".join(f"{r.get(k, '-'):>9}" for k in chiavi))
    print("\nmedia per formato:")
    for f in sorted({r["formato"] for r in righe}):
        g = [r for r in righe if r["formato"] == f]
        print(f"{f:<11} n={len(g):<2} " + " ".join(f"{k[:9]}={sum(r.get(k, 0) for r in g) / len(g):.0f}" for k in chiavi))

if __name__ == "__main__":
    main()
