"""Il verbale dei 7 giorni (Alberto, 7/11): per ogni reel arrivato a 7 giorni dalla pubblicazione,
follower attribuiti (in totale e ogni 1.000 account raggiunti), confronto coi reel organici simili alla stessa distanza dall'uscita,
e quale scelta creativa vale la pena riprovare, con il dato su cui si basa. Se il dato sui follower manca, si scrive «indisponibile».

Dati: motore/rendimento.json (rendimento.py: reach, follower_dopo, sponsorizzato), motore/rendimento_storia.json (numeri per giorno dall'uscita),
docs/contenuti/auto/<reel>.json (le scelte creative del copione). Scrive docs/data/agenzia/verbali.json, la riga nella stanza e il registro decisioni.
"""
import json, statistics
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GIORNI = 7

def carica(p, vuoto):
    try: return json.loads(Path(p).read_text())
    except (FileNotFoundError, json.JSONDecodeError): return vuoto

def scelte(file):
    """Le scelte creative di un reel, dal copione salvato."""
    c = carica(ROOT / f"docs/contenuti/auto/{file}.json", None)
    if not c: return None
    fr = c.get("frasi", [])
    return {"formato": c.get("formato"), "apertura": "video vero" if c.get("intro") else "mappa", "voce": bool(c.get("voce")),
            "gancio": fr[0]["testo"] if fr else None, "chiusura": fr[-1]["testo"] if fr else None}

def a7(r, storia):
    """I numeri del reel a 7 giorni dall'uscita (la fotografia del giorno 7, o la più vicina dopo)."""
    s = storia.get(r.get("id"), {})
    for g in range(GIORNI, GIORNI + 4):
        if f"g{g}" in s: return s[f"g{g}"]
    return None

def per_mille(f, reach):
    return round(1000 * f / reach, 1) if f is not None and reach else None

def main():
    R = carica(ROOT / "motore/rendimento.json", [])
    storia = carica(ROOT / "motore/rendimento_storia.json", {})
    out_p = ROOT / "docs/data/agenzia/verbali.json"
    verbali = carica(out_p, [])
    fatti = {v["id"] for v in verbali}
    ora = datetime.now(timezone.utc)
    nuovi = []
    for r in R:
        if not r.get("id") or r["id"] in fatti or r.get("sponsorizzato"): continue
        if (ora - datetime.fromisoformat(r["ts"])).days < GIORNI: continue
        n7 = a7(r, storia)
        if not n7: continue  # senza la fotografia del giorno 7 il confronto non è alla stessa distanza: si aspetta
        f = r.get("follower_dopo")
        mio = per_mille(f, n7.get("reach"))
        sc = scelte(r.get("file", ""))
        # simili: organici, stesso formato (o, se non ce ne sono, tutti gli organici), presi anche loro a 7 giorni
        pari = [(x, a7(x, storia)) for x in R if x is not r and not x.get("sponsorizzato") and a7(x, storia)]
        simili = [(x, n) for x, n in pari if x.get("formato") == r.get("formato")] or pari
        valori = [per_mille(x.get("follower_dopo"), n.get("reach")) for x, n in simili]
        valori = [v for v in valori if v is not None]
        mediana = round(statistics.median(valori), 1) if valori else None
        if f is None:
            esito = "Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel)."
            riprova = None
        elif mediana is None:
            esito = f"{f} follower in totale, {mio} ogni 1.000 account raggiunti a 7 giorni. Nessun reel organico simile con dati sui follower da confrontare."
            riprova = None
        else:
            meglio = mio is not None and mio > mediana
            esito = (f"{f} follower in totale, {mio} ogni 1.000 account raggiunti a 7 giorni; i reel organici simili ({len(valori)}) hanno una mediana di {mediana}.")
            riprova = (f"Riprovare: apertura «{sc['apertura']}», gancio «{sc['gancio']}», chiusura «{sc['chiusura']}» (formato {sc['formato']})." if meglio and sc else
                       "Non riprovare così com'è: è sotto la mediana dei reel simili." if sc else None)
        v = {"id": r["id"], "file": r.get("file"), "formato": r.get("formato"), "uscita": r["ts"], "follower": f, "reach_7g": n7.get("reach"),
             "follower_ogni_1000": mio, "mediana_simili": mediana, "simili": len(valori), "scelte": sc, "esito": esito, "riprovare": riprova,
             "dato": "follower arrivati dopo l'uscita fino al reel successivo (max 6 ore), su reach a 7 giorni; mediana dei reel organici dello stesso formato a 7 giorni"}
        verbali.append(v); nuovi.append(v)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out_p.write_text(json.dumps(verbali[-300:], ensure_ascii=False, indent=1) + "\n")
    for v in nuovi:  # nella stanza: il verbale va nella sessione del reel, dalla Crescita al Direttore
        sp = ROOT / f"docs/data/agenzia/sessioni/{v['file']}.json"
        if sp.exists():
            s = json.loads(sp.read_text())
            s["scambi"].append({"t": ora.isoformat(timespec="seconds"), "da": "crescita-10", "a": "direzione-1", "tipo": "decisione",
                                "testo": f"Verbale dei 7 giorni: {v['esito']}" + (f" {v['riprovare']}" if v["riprovare"] else ""), "dati": v})
            sp.write_text(json.dumps(s, ensure_ascii=False, indent=1) + "\n")
    if nuovi:
        righe = "\n".join(f"- {v['file']}: {v['esito']}" + (f" {v['riprovare']}" if v["riprovare"] else "") for v in nuovi)
        with open(ROOT / "motore/decisioni-reel.md", "a") as fh:
            fh.write(f"\n\n## {ora.date().isoformat()} — verbale dei 7 giorni (automatico, motore/verbale.py)\n\n{righe}\n")
    print(f"verbali nuovi: {len(nuovi)}")

if __name__ == "__main__":
    main()
