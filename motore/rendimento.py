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

def numeri(mid, token):
    out = {}
    try:  # prima tutte insieme; se Instagram ne rifiuta una, una alla volta
        dati = chiama("GET", f"{mid}/insights", token, metric=",".join(METRICHE))["data"]
    except SystemExit:  # chiama() esce con SystemExit sugli errori di Instagram
        dati = []
        for m in METRICHE:
            try: dati += chiama("GET", f"{mid}/insights", token, metric=m)["data"]
            except SystemExit: pass
    for d in dati:
        v = d.get("values", [{}])[0].get("value", d.get("total_value", {}).get("value"))
        if isinstance(v, (int, float)): out[d["name"]] = v
    return out

def main():
    token = os.environ.get("IG_TOKEN") or sys.exit("Manca IG_TOKEN.")
    reel = [x for x in json.loads((ROOT / "motore/pubblicati.json").read_text()) if x["tipo"] == "REELS"]
    righe = []
    for x in reel:
        m = re.search(r"(\d{4}-\d\d-\d\d)-(\d{4})-(\w+)\.mp4", x["media"])
        formato, quando = (m.group(3), f"{m.group(1)} {m.group(2)[:2]}:{m.group(2)[2:]}") if m else ("lancio", x["ts"][:16])
        righe.append({"quando": quando, "formato": formato, "ts": x["ts"], **numeri(x["id"], token)})
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
