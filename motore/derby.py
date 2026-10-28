"""Il Derby della settimana: due province rivali, vince quella che accende più luci nuove fino alla domenica alle 21.

Vale tutta la provincia (Pozzuoli porta luci a Napoli). Si contano solo le luci accese durante il derby, così si parte 0 a 0.
Chi ha acceso la provincia che vince prende PREMIO punti (lo assegna commenti.py, una volta sola).
"""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

ROMA = ZoneInfo("Europe/Rome")
PREMIO = 20
ESCLUSI = {"thor_golden_life", "albertomarchesin"}

# (inizio, fine, (nome, sigla), (nome, sigla)); finisce sempre la domenica alle 21, prima della puntata
CALENDARIO = [
    ("2026-10-28 19:00", "2026-11-01 21:00", ("Napoli", "NA"), ("Roma", "RM")),
    ("2026-11-01 21:00", "2026-11-08 21:00", ("Milano", "MI"), ("Torino", "TO")),
    ("2026-11-08 21:00", "2026-11-15 21:00", ("Livorno", "LI"), ("Pisa", "PI")),
]
# dopo il calendario, una rivalità a settimana a giro
RIVALI = [(("Bergamo", "BG"), ("Brescia", "BS")), (("Treviso", "TV"), ("Venezia", "VE")), (("Bari", "BA"), ("Lecce", "LE")),
          (("Palermo", "PA"), ("Catania", "CT")), (("Padova", "PD"), ("Vicenza", "VI")), (("Firenze", "FI"), ("Siena", "SI")),
          (("Genova", "GE"), ("La Spezia", "SP")), (("Bologna", "BO"), ("Modena", "MO")), (("Napoli", "NA"), ("Salerno", "SA"))]

def _t(s): return datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=ROMA)

def derby_di(ora):
    """I derby fino a `ora` compreso quello in corso: lista di dict {inizio, fine, a, b}."""
    out = [{"inizio": _t(i), "fine": _t(f), "a": a, "b": b} for i, f, a, b in CALENDARIO]
    k = 0
    while out[-1]["fine"] <= ora:
        a, b = RIVALI[k % len(RIVALI)]; k += 1
        out.append({"inizio": out[-1]["fine"], "fine": out[-1]["fine"] + timedelta(days=7), "a": a, "b": b})
    return [d for d in out if d["inizio"] <= ora]

def _ts(a):
    try: return datetime.strptime(str(a.get("ts", "")), "%Y-%m-%dT%H:%M:%S%z")
    except ValueError: return None

def conta(animali, d):
    """Luci accese in ciascuna provincia durante il derby, e chi le ha accese."""
    luci = {d["a"][1]: [], d["b"][1]: []}
    for a in animali:
        t = _ts(a)
        if a.get("k") in ("animale", "sogno", "tifo") and a.get("p") in luci and t and d["inizio"] <= t < d["fine"] and a["u"].lower() not in ESCLUSI:
            luci[a["p"]].append(a)
    return luci

def riassunto(animali, ora=None):
    """Lo stato per il sito e per i reel: il derby in corso (o appena finito) e l'albo dei vincitori."""
    ora = ora or datetime.now(ROMA)
    tutti = derby_di(ora) or derby_di(_t(CALENDARIO[0][0]))  # prima del primo derby: si mostra quello che sta per partire
    albo = []
    for d in tutti:
        l = conta(animali, d)
        na, nb = len(l[d["a"][1]]), len(l[d["b"][1]])
        r = {"a": d["a"][0], "pa": d["a"][1], "b": d["b"][0], "pb": d["b"][1], "na": na, "nb": nb,
             "inizio": d["inizio"].isoformat(), "fine": d["fine"].isoformat(), "finito": d["fine"] <= ora, "partito": d["inizio"] <= ora}
        if r["finito"]:
            r["vince"] = d["a"][0] if na > nb else d["b"][0] if nb > na else None  # None = pareggio
        albo.append(r)
    return {"ora": albo[-1], "albo": [x for x in albo if x["finito"]]}

def premiati(animali, d):
    """Chi prende il premio di un derby finito: chi ha acceso la provincia vincente (con il pareggio, tutte e due)."""
    l = conta(animali, d)
    na, nb = len(l[d["a"][1]]), len(l[d["b"][1]])
    vincenti = [d["a"][1]] if na > nb else [d["b"][1]] if nb > na else [d["a"][1], d["b"][1]]
    return sorted({a["u"] for p in vincenti for a in l[p]})
