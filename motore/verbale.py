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

# ---------------------------------------------------------------- il test di crescita (Alberto, 8/11)

def _med(v):
    v = [x for x in v if x is not None]
    return round(statistics.median(v), 1) if v else None

def secondaria(caso, uscita, fine):
    """La metrica secondaria a 7 giorni, con la sua fonte. None se non si può calcolare."""
    if not caso: return None
    if caso.get("tipo") == "paese_al_buio":  # iscrizioni valide del comune raccontato
        A = carica(ROOT / "docs/data/animali.json", {"animali": []})["animali"]
        n = sum(1 for a in A if a.get("k") == "animale" and a.get("c") == caso["comune"] and a.get("p", "") == caso["p"]
                and uscita <= str(a.get("ts", "")) < fine)
        return {"nome": f"iscrizioni valide di {caso['comune']}", "valore": n, "fonte": "docs/data/animali.json (animali col comune e la data del commento)"}
    if caso.get("tipo") == "campanile_rivale":  # staffette chiuse dai due comuni della sfida
        L = carica(ROOT / "motore/stato.json", {}).get("staffette_log", [])
        n = sum(1 for x in L if x["k"] in (caso["a"], caso["b"]) and uscita[:16] <= x["t"][:16] < fine[:16])
        return {"nome": "staffette valide completate (i due comuni)", "valore": n, "fonte": "motore/stato.json, staffette_log (motore/coppa.py)"}
    return None

def verbale_test():
    """Ogni episodio del test a 7 giorni dall'uscita: follower attribuiti, account raggiunti, follower ogni 1.000, metrica secondaria, fonte e dati mancanti.
    Base: la mediana dei reel organici comparabili (13 e 18, non sponsorizzati, nei 14 giorni prima del test). Il sponsorizzato resta fuori."""
    from datetime import timedelta
    cfg = carica(ROOT / "motore/config.json", {}).get("test_crescita") or {}
    if not cfg.get("dal"): return None
    R = carica(ROOT / "motore/rendimento.json", [])
    storia = carica(ROOT / "motore/rendimento_storia.json", {})
    ora = datetime.now(timezone.utc)
    dal = datetime.fromisoformat(cfg["dal"] + "T00:00:00+01:00")
    def cop(r): return carica(ROOT / f"docs/contenuti/auto/{r.get('file', '')}.json", {}) or {}
    base = [r for r in R if not r.get("sponsorizzato") and not cop(r).get("test") and r.get("quando", "")[11:13] in ("13", "18")
            and dal - timedelta(days=14) <= datetime.fromisoformat(r["ts"]) < dal]
    base_righe = [{"file": r.get("file"), "follower": r.get("follower_dopo"), "reach": (a7(r, storia) or {}).get("reach") or r.get("reach")} for r in base]
    base_val = [per_mille(x["follower"], x["reach"]) for x in base_righe]
    mediana_base = _med(base_val)
    episodi = []
    for r in R:
        c = cop(r); t = c.get("test")
        if not t or r.get("sponsorizzato"): continue
        uscita = datetime.fromisoformat(r["ts"]); maturo = (ora - uscita).days >= GIORNI
        n7 = a7(r, storia); mancano = []
        reach = (n7 or {}).get("reach")
        if reach is None: mancano.append("account raggiunti a 7 giorni" + (" (uso quelli di adesso)" if r.get("reach") else "")); reach = r.get("reach")
        if r.get("follower_dopo") is None: mancano.append("follower attribuiti")
        sec = secondaria(t.get("caso"), r["ts"], (uscita + timedelta(days=GIORNI)).isoformat())
        if t.get("caso") and t["caso"].get("tipo") in ("paese_al_buio", "campanile_rivale") and sec is None: mancano.append("metrica secondaria")
        episodi.append({"file": r.get("file"), "formato": t["formato"], "variante": t["variante"], "slot": t.get("slot"), "uscita": r["ts"], "a_7_giorni": maturo,
                        "follower": r.get("follower_dopo"), "reach": reach, "follower_ogni_1000": per_mille(r.get("follower_dopo"), reach),
                        "sopra_la_base": (per_mille(r.get("follower_dopo"), reach) or 0) > mediana_base if mediana_base is not None and r.get("follower_dopo") is not None else None,
                        "secondaria": sec, "mancano": mancano, "views": r.get("views"),
                        "fonte": "follower: motore/rendimento.py (follower arrivati dopo l'uscita fino al reel successivo, max 6 ore, da stato follower_ore); reach: Instagram Insights a 7 giorni (rendimento_storia.json)"})
    def riassunto(chiave):
        out = {}
        for e in episodi:
            k = e[chiave] if chiave != "formato_variante" else f"{e['formato']} · {e['variante']}"
            g = out.setdefault(k, {"episodi": 0, "a_7_giorni": 0, "follower_totali": 0, "reach_totale": 0, "valori": [], "sopra_la_base": 0})
            g["episodi"] += 1; g["a_7_giorni"] += e["a_7_giorni"]
            if e["follower"] is not None: g["follower_totali"] += e["follower"]
            if e["reach"]: g["reach_totale"] += e["reach"]
            g["valori"].append(e["follower_ogni_1000"]); g["sopra_la_base"] += bool(e["sopra_la_base"])
        for g in out.values():
            g["mediana_ogni_1000"] = _med(g.pop("valori"))
            g["tenere"] = ("sì: sopra la base in più episodi" if g["sopra_la_base"] >= 2 and (g["mediana_ogni_1000"] or 0) > (mediana_base or 0)
                           else "non ancora: servono più episodi a 7 giorni" if g["a_7_giorni"] < 2 else "no: non migliora la base su più episodi")
        return out
    res = {"aggiornato": ora.isoformat(timespec="minutes"), "dal": cfg["dal"], "stato": cfg.get("stato"),
           "base": {"regola": "mediana dei follower ogni 1.000 account raggiunti dei reel organici delle 13 e delle 18 nei 14 giorni prima del test (il sponsorizzato da 57.400 visualizzazioni è escluso)",
                    "mediana_ogni_1000": mediana_base, "reel_con_dati": len([v for v in base_val if v is not None]), "reel_totali": len(base_righe), "conteggi_grezzi": base_righe},
           "episodi": episodi, "per_formato": riassunto("formato"), "per_versione": riassunto("variante"), "per_formato_e_versione": riassunto("formato_variante"),
           "saltati": carica(ROOT / "motore/reel_fatti.json", {}).get("test_saltati", [])[-30:]}
    (ROOT / "docs/data/agenzia").mkdir(parents=True, exist_ok=True)
    (ROOT / "docs/data/agenzia/test_crescita.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n")
    print(f"test di crescita: {len(episodi)} episodi, base {mediana_base} ogni 1.000 ({res['base']['reel_con_dati']} reel con dati)")
    return res

if __name__ == "__main__":
    main()
    verbale_test()
