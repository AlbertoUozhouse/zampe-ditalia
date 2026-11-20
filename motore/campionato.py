"""Il Campionato delle Zampe (17/11, Alberto: «il torneo sta spingendo a manetta: facciamo un campionato dei cani, lo stadio dei cani,
a Roma lo stadio Olimpico, a Milano San Siro: sul calcio la gente è innamorata»).

Una partita alla volta, nello stadio della squadra di casa (motore/squadre.py STADI). Ogni commento che nomina una delle due squadre
(«forza Inter», «interista», «⚽ Milan») è un gol: uno a persona per partita, per la prima squadra che nomina. La partita finisce alle 12:30
del primo giorno col reel «partita» alle 13 (motore/config.json), così il reel delle 13 racconta il risultato e lancia la partita nuova.
Vittoria 3 punti, pareggio 1. Le squadre in campo sono quelle che hanno cani tifosi sulla mappa (la sciarpa, motore/commenti.py).
Tutto sta in stato.json «campionato»: niente spese, niente gol finti (solo commenti veri, uno a persona).
"""
import json, re, unicodedata
from datetime import datetime, timedelta, time
from pathlib import Path
from zoneinfo import ZoneInfo

import squadre

ROOT = Path(__file__).resolve().parent.parent
ROMA = ZoneInfo("Europe/Rome")
CAMBIO = time(12, 30)  # la partita si chiude mezz'ora prima del reel delle 13, così il reel trova il risultato già salvato
DERBY = [("inter", "milan"), ("roma", "lazio"), ("juventus", "torino"), ("genoa", "sampdoria"), ("napoli", "roma"), ("inter", "juventus"), ("milan", "juventus")]
ESCLUSI = {"thor_golden_life", "albertomarchesin"}
GIORNI = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]


def _cfg():
    try: return json.loads((ROOT / "motore/config.json").read_text())
    except (FileNotFoundError, json.JSONDecodeError): return {}


def _slot13(cfg, d):
    """Il reel delle 13 di quel giorno (come motore/orari.py: orari, poi settimanali, poi una tantum)."""
    v = cfg.get("orari", {}).get("13:00")
    v = cfg.get("settimanali", {}).get(f"{['lun', 'mar', 'mer', 'gio', 'ven', 'sab', 'dom'][d.weekday()]} 13:00", v)
    return cfg.get("una_tantum", {}).get(f"{d.isoformat()} 13:00", v)


def prossimo_cambio(cfg, ora):
    """Il prossimo momento (dopo ora) in cui finisce una partita: le 12:30 di un giorno col reel «partita» alle 13."""
    for k in range(0, 15):
        d = ora.date() + timedelta(days=k); t = datetime.combine(d, CAMBIO, ROMA)
        if t > ora and _slot13(cfg, d) == "partita": return t
    return datetime.combine(ora.date() + timedelta(days=1), CAMBIO, ROMA)


def _norm(s):
    s = unicodedata.normalize("NFD", (s or "").lower())
    return re.sub(r"[^a-z0-9 ]", " ", "".join(c for c in s if not unicodedata.combining(c)))


def squadra_nel_testo(testo, chiavi):
    """Quale delle due squadre nomina il commento (None se nessuna o tutte e due). I nomi che sono anche città (Roma, Napoli…) contano
    solo con una parola di tifo («forza», «tifo», ⚽…) o un soprannome («romanista»): «Roma, Kira, cane» è la città, non la squadra."""
    parole = set(_norm(testo).split()); trovate = []
    for k in chiavi:
        alias = {squadre._norm(x) for x in squadre.SQUADRE[k][3]}; nome = squadre._norm(squadre.SQUADRE[k][0])
        uniti = {a for a in alias | {nome} if " " not in a}
        dentro = uniti & parole or {a for a in alias | {nome} if " " in a and f" {a} " in f" {_norm(testo)} "}
        if not dentro: continue
        if squadre._citta(k) and dentro <= {nome} and not squadre.TIFO.search(testo or ""): continue
        trovate.append(k)
    return trovate[0] if len(trovate) == 1 else None


def tifosi(animali):
    conta = {}
    for a in animali:
        if a.get("sq") in squadre.SQUADRE and a.get("u", "").lower() not in ESCLUSI: conta[a["sq"]] = conta.get(a["sq"], 0) + 1
    return conta


def scegli(C, conta):
    """La partita nuova: prima i derby (Inter–Milan per primo, come ha chiesto Alberto), poi le squadre con più tifosi che non si sono ancora
    incontrate. In casa gioca la squadra con più tifosi."""
    giocate = {frozenset((x["a"], x["b"])) for x in C.get("giocate", [])}
    pronte = [k for k, n in sorted(conta.items(), key=lambda x: -x[1]) if n >= 1]
    for a, b in DERBY:  # 20/11: un derby solo se tutte e due hanno almeno 5 tifosi (Genoa–Samp con 4 e 2 tifosi lasciava fuori la Juve con 24)
        if conta.get(a, 0) >= 5 and conta.get(b, 0) >= 5 and frozenset((a, b)) not in giocate:
            return (a, b) if conta[a] >= conta[b] else (b, a)
    coppie = [(a, b) for i, a in enumerate(pronte) for b in pronte[i + 1:] if frozenset((a, b)) not in giocate]
    if not coppie and len(pronte) >= 2: coppie = [(pronte[0], pronte[1])]  # tutte già giocate: si ricomincia dal girone di ritorno
    if not coppie: return None
    a, b = max(coppie, key=lambda p: conta[p[0]] + conta[p[1]])
    return (a, b) if conta[a] >= conta[b] else (b, a)


def aggiorna(stato, animali, ora=None):
    """A ogni giro della veglia: chiude la partita finita (risultato e classifica) e apre la nuova. Restituisce True se è cambiato qualcosa."""
    cfg = _cfg(); dal = (cfg.get("campionato") or {}).get("dal")
    if not dal: return False
    ora = ora or datetime.now(ROMA)
    C = stato.setdefault("campionato", {}); cambiato = False
    P = C.get("partita")
    if P and ora >= datetime.fromisoformat(P["fine"]):
        ga, gb = P["gol"].get(P["a"], 0), P["gol"].get(P["b"], 0)
        C.setdefault("giocate", []).append({"giornata": P["giornata"], "a": P["a"], "b": P["b"], "ga": ga, "gb": gb, "stadio": P["stadio"], "fine": P["fine"]})
        C["giocate"] = C["giocate"][-200:]
        T = C.setdefault("classifica", {})
        for k, gf, gs in ((P["a"], ga, gb), (P["b"], gb, ga)):
            r = T.setdefault(k, {"pt": 0, "g": 0, "v": 0, "n": 0, "p": 0, "gf": 0, "gs": 0})
            r["g"] += 1; r["gf"] += gf; r["gs"] += gs
            if gf > gs: r["v"] += 1; r["pt"] += 3
            elif gf == gs: r["n"] += 1; r["pt"] += 1
            else: r["p"] += 1
        C["partita"] = None; P = None; cambiato = True
    if "bomber" not in C and (C.get("giocate") or P):  # 19/11: i gol fatti prima della classifica marcatori (giornata 1 da motore/campionato_g1.json)
        B_ = C["bomber"] = {}
        try: vecchi = json.loads((ROOT / "motore/campionato_g1.json").read_text())
        except (FileNotFoundError, json.JSONDecodeError): vecchi = []
        sq_di = {a.get("u", "").lower(): a.get("sq") for a in animali if a.get("sq")}
        for u in vecchi + (P["marcatori"] if P else []):
            b = B_.setdefault(u, {"g": 0}); b["g"] += 1
            if sq_di.get(u): b["sq"] = sq_di[u]
        cambiato = True
    if not P and ora >= datetime.combine(datetime.fromisoformat(dal).date(), CAMBIO, ROMA):
        coppia = scegli(C, tifosi(animali))
        if coppia:
            a, b = coppia; st_, citta = squadre.stadio(a)
            C["partita"] = {"giornata": len(C.get("giocate", [])) + 1, "a": a, "b": b, "stadio": st_, "citta": citta, "gol": {a: 0, b: 0}, "marcatori": [],
                            "inizio": ora.isoformat(timespec="minutes"), "fine": prossimo_cambio(cfg, ora).isoformat(timespec="minutes")}
            cambiato = True
    return cambiato


def allo(stadio):
    """«a San Siro», «allo Stadio Olimpico», «all'Arena Garibaldi»."""
    t = stadio.title().replace("Dall'Ara", "Dall'Ara").replace("Via Del Mare", "Via del Mare")
    return f"allo {t}" if t.startswith("Stadio") else f"all'{t}" if t[:1] in "AEIOU" else f"a {t}"


def quando(fine, ora=None):
    ora = ora or datetime.now(ROMA); f = datetime.fromisoformat(fine)
    g = (f.date() - ora.date()).days
    return f"{'oggi' if g == 0 else 'domani' if g == 1 else GIORNI[f.weekday()]} alle {f.strftime('%H:%M')}"


def gol(stato, u, testi):
    """Un commento che nomina una delle due squadre in campo è un gol (uno a persona per partita). Restituisce la riga per la risposta."""
    P = (stato.get("campionato") or {}).get("partita")
    if not P or u.lower() in ESCLUSI or u.lower() in P["marcatori"]: return None
    k = next((x for x in (squadra_nel_testo(t, (P["a"], P["b"])) for t in testi) if x), None)
    if not k: return None
    P["gol"][k] = P["gol"].get(k, 0) + 1; P["marcatori"].append(u.lower())
    # 19/11 (Officina): i capocannonieri del Campionato, partita dopo partita; il primo ha il Pallone d'Oro sul suo cane (solo gloria)
    B_ = stato["campionato"].setdefault("bomber", {}); b = B_.setdefault(u.lower(), {"g": 0}); b["g"] += 1; b["sq"] = k
    pos = 1 + sum(1 for x in B_.values() if x["g"] > b["g"]); pari = sum(1 for x in B_.values() if x["g"] == b["g"]) > 1
    A, B = squadre.nome(P["a"]), squadre.nome(P["b"])
    return (f"⚽ GOL per {squadre.nome(k)}! {(lambda x: x[0].upper() + x[1:])(allo(P['stadio']))}: {A} {P['gol'][P['a']]} – {P['gol'][P['b']]} {B}. "
            + (f"Sei a {b['g']} gol nel Campionato: {pos}° tra i marcatori{' a pari merito' if pari else ''}{' e hai il Pallone d’Oro 🏆' if pos == 1 and not pari else ''}! " if b["g"] >= 2 else "")
            + f"Si gioca fino a {quando(P['fine'])}: fai segnare i tuoi amici tifosi, taggali 👥")


def classifica(stato):
    T = (stato.get("campionato") or {}).get("classifica", {})
    return sorted(T.items(), key=lambda x: (-x[1]["pt"], -(x[1]["gf"] - x[1]["gs"]), -x[1]["gf"], x[0]))


def sito(stato, animali):
    """Per il sito (docs/app.js): la partita in corso, l'ultima giocata, la classifica, i tifosi per squadra (solo numeri, nessun nome)."""
    C = stato.get("campionato") or {}; P = C.get("partita")
    pub = lambda k: {"k": k, "nome": squadre.nome(k), "c": squadre.colori(k)["c"]}
    out = {"tifosi": tifosi(animali), "classifica": [{**pub(k), **r} for k, r in classifica(stato)][:20]}
    if P:
        out["partita"] = {"giornata": P["giornata"], "a": pub(P["a"]), "b": pub(P["b"]), "ga": P["gol"].get(P["a"], 0), "gb": P["gol"].get(P["b"], 0),
                          "stadio": P["stadio"], "citta": P["citta"], "fine": P["fine"]}
        ll = squadre.STADI_LL.get(P["stadio"])
        if ll: out["partita"]["lat"], out["partita"]["lng"] = ll  # 18/11: lo stadio sulla mappa del sito, nel posto vero
    bomber = sorted(C.get("bomber", {}).items(), key=lambda x: -x[1]["g"])[:10]
    out["bomber"] = [{"u": u, "g": x["g"], **({"sq": pub(x["sq"])} if x.get("sq") in squadre.SQUADRE else {})} for u, x in bomber]
    if C.get("giocate"):
        x = C["giocate"][-1]; out["ultima"] = {"a": pub(x["a"]), "b": pub(x["b"]), "ga": x["ga"], "gb": x["gb"], "stadio": x["stadio"]}
    return out


if __name__ == "__main__":  # prova a secco: python3 motore/campionato.py
    st = {}; an = [{"u": f"p{i}", "sq": s} for i, s in enumerate(["inter"] * 8 + ["roma"] * 4 + ["napoli"] * 4 + ["milan", "juventus", "juventus"])]
    t0 = datetime(2026, 11, 18, 12, 31, tzinfo=ROMA)
    print("apre:", aggiorna(st, an, t0), st["campionato"]["partita"]["a"], st["campionato"]["partita"]["b"], st["campionato"]["partita"]["fine"])
    for u, t in [("a1", "Forza Inter!!"), ("a2", "Milano, Rex, cane, milanista"), ("a3", "Roma, Kira, gatto"), ("a1", "inter"), ("a4", "⚽ Milan")]:
        print(u, t, "→", gol(st, u, [t]))
    print("chiude:", aggiorna(st, an, datetime(2026, 11, 19, 12, 35, tzinfo=ROMA)), st["campionato"]["giocate"][-1], st["campionato"]["partita"])
    print(classifica(st)); print(json.dumps(sito(st, an))[:300])
