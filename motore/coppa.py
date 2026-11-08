"""La Coppa delle Zampe (Alberto, 7/11/2026): un campionato settimanale tra comuni.

Ogni persona gioca per un comune per tutta la settimana: quello del suo animale sulla mappa (il primo che ha acceso).
La prova del giorno si fa sul sito (docs/coppa.js): alla fine dà il codice «COPPA XY», che si commenta sotto un reel.
Qui il bot lo controlla e dà UN punto al giorno per persona alla sua squadra (ricaricare la pagina o commentare due volte non cambia nulla).
I comuni sono abbinati a coppie con un numero simile di giocatori attivi, così anche i paesi piccoli possono vincere.
Domenica alle 20 si chiude: chi vince la sua sfida prende il trofeo (sulla mappa e nell'albo). Lunedì a mezzanotte parte il turno dopo.
La Staffetta: tre persone diverse dello stesso comune nella stessa settimana accendono l'anello dorato attorno alla città.
La Staffetta di quartiere (test di crescita, 8/11): tre persone diverse dello stesso comune, ognuna col suo animale, commentano
«città, nome, cane o gatto» mentre il comune è in sfida. A 3/3 la prova è chiusa: un punto della Coppa al comune e l'anello dorato.
Ogni commento e ogni persona contano una volta sola per comune e per turno (un commento riletto o un giro ripetuto non cambia nulla).

Nel repository pubblico (docs/data/coppa.json) solo comuni e numeri; i nomi utente restano in motore/stato.json come per il resto del gioco.
"""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROMA = ZoneInfo("Europe/Rome")
STAFFETTA = 3
CHIUSURA_ORA = 20  # domenica alle 20: poi il verdetto delle 21


def giorno(t=None):
    """Il giorno della prova, ora italiana (come sul sito)."""
    return (t or datetime.now(ROMA)).astimezone(ROMA).date().isoformat()


def codice(g):
    """Due caratteri legati al giorno, come in docs/coppa.js (stesso hash FNV dei giochi): il codice di ieri non vale oggi."""
    h = 2166136261
    for ch in f"zampe-coppa|{g}":
        h = ((h ^ ord(ch)) * 16777619) & 0xFFFFFFFF
    cifre, out = "0123456789abcdefghijklmnopqrstuvwxyz", ""
    while h: h, r = divmod(h, 36); out = cifre[r] + out
    return out[-2:].upper()


def _lunedi(t):
    t = t.astimezone(ROMA)
    return (t - timedelta(days=t.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)


def chiave(a):
    return f"{a['c']}|{a.get('p', '')}"


def _taglia(animali, giocatori_prima):
    """Quanto è grande ogni squadra: prima i giocatori attivi del turno scorso, poi gli animali sulla mappa (per chi non ha ancora giocato).
    Così si abbinano comuni con un numero simile di giocatori attivi, e i paesi piccoli sfidano paesi piccoli."""
    t = {}
    for a in animali:
        if a.get("k") == "animale": t[chiave(a)] = t.get(chiave(a), 0) + 1
    return {k: (len(giocatori_prima.get(k, [])), n) for k, n in t.items()}


def abbina(taglia):
    """Coppie di comuni con un numero simile di giocatori: in ordine di grandezza, a due a due. Il dispari resta in attesa."""
    ordine = sorted(taglia, key=lambda k: tuple(-x for x in (taglia[k] if isinstance(taglia[k], tuple) else (taglia[k],))) + (k,))
    coppie = [[ordine[i], ordine[i + 1]] for i in range(0, len(ordine) - 1, 2)]
    return coppie, (ordine[-1] if len(ordine) % 2 else None)


def nuovo_turno(stato, animali, ora):
    C = stato.setdefault("coppa", {})
    prima = C.get("giocatori", {})
    inizio = _lunedi(ora) if C else ora.astimezone(ROMA)
    fine = _lunedi(ora) + timedelta(days=6, hours=CHIUSURA_ORA)
    if not C and ora.astimezone(ROMA) > fine - timedelta(days=3):  # il primissimo turno parte a fine settimana: dura fino alla domenica dopo
        fine += timedelta(days=7)
    coppie, attesa = abbina(_taglia(animali, prima))
    C.update({"turno": C.get("turno", 0) + 1, "inizio": inizio.isoformat(), "fine": fine.isoformat(), "coppie": coppie, "attesa": attesa,
              "punti": {}, "giocatori": {}, "squadra": {}, "giorni": {}, "storia": [], "chiuso": False, "quartiere": {}})
    C["prima"] = sorted({u for v in prima.values() for u in v})  # chi aveva giocato il turno scorso: per contare chi torna
    return C


def chiudi(stato, animali, ora):
    """Domenica sera: chi vince la sua sfida prende il trofeo; misure della settimana."""
    C = stato["coppa"]
    if C.get("chiuso"): return
    P, vinti = C["punti"], []
    for a, b in C["coppie"]:
        pa, pb = P.get(a, 0), P.get(b, 0)
        if pa == pb == 0: continue
        if pa == pb:  # pari nei punti: vince chi ha più giocatori diversi; se anche quelli sono pari, trofeo a tutti e due
            ga, gb = len(C["giocatori"].get(a, [])), len(C["giocatori"].get(b, []))
            vinc = [a] if ga > gb else [b] if gb > ga else [a, b]
        else:
            vinc = [a if pa > pb else b]
        for v in vinc:
            vinti.append({"c": v, "p": P.get(v, 0), "contro": b if v == a else a, "pc": P.get(b if v == a else a, 0)})
    giocatori = {u for v in C["giocatori"].values() for u in v}
    primi_ts = {}
    for x in animali:
        if x.get("u") and x.get("ts"): primi_ts[x["u"].lower()] = min(primi_ts.get(x["u"].lower(), "9"), str(x["ts"]))
    inizio = C["inizio"][:10]
    misura = {"turno": C["turno"], "inizio": C["inizio"][:10], "fine": C["fine"][:10], "giocatori": len(giocatori),
              "tornano": len(giocatori & set(C.get("prima", []))),
              "piu_giorni": sum(1 for u in giocatori if len(C["giorni"].get(u, [])) >= 2),
              "nuovi_da_instagram": sum(1 for u in giocatori if primi_ts.get(u, "") >= inizio),  # arrivati sulla mappa (da un commento) durante il turno
              "punti": sum(P.values()), "comuni": len([k for k in P if P[k]]), "staffette": len(staffette(C)),
              "staffette_quartiere": sum(v.get("chiuse", 0) for v in C.get("quartiere", {}).values()),
              "partecipanti_quartiere": sum(len(v.get("u", [])) for v in C.get("quartiere", {}).values())}
    stato.setdefault("coppa_albo", []).append({"turno": C["turno"], "fine": C["fine"][:10], "vincitori": sorted(vinti, key=lambda v: -v["p"])})
    stato.setdefault("coppa_misure", []).append(misura)
    C["chiuso"] = True


def aggiorna(stato, animali, ora=None):
    """A ogni giro del motore: apre il primo turno, chiude la domenica alle 20, riparte il lunedì a mezzanotte."""
    ora = ora or datetime.now(timezone.utc)
    C = stato.get("coppa")
    if not C:
        return nuovo_turno(stato, animali, ora)
    fine = datetime.fromisoformat(C["fine"])
    if ora >= fine and not C.get("chiuso"):
        chiudi(stato, animali, ora)
    if ora >= fine + timedelta(hours=4):  # lunedì 00:00
        nuovo_turno(stato, animali, ora)
    return stato["coppa"]


def avversario(C, k):
    for a, b in C["coppie"]:
        if k == a: return b
        if k == b: return a
    return None


def staffette(C):
    return sorted({k for k, v in C.get("giocatori", {}).items() if len(v) >= STAFFETTA} | {k for k, v in C.get("quartiere", {}).items() if v.get("chiuse")})


def quartiere(C, k):
    """A che punto è la Staffetta di quartiere di un comune: {"n": 0-3 della prova in corso, "chiuse": prove chiuse nel turno}."""
    q = C.get("quartiere", {}).get(k) or {}
    n, ch = len(q.get("u", [])), q.get("chiuse", 0)
    return {"n": n - ch * STAFFETTA, "chiuse": ch}


def partecipa(stato, animali, utente, k, id_commento, ora=None):
    """Un commento valido «città, nome, cane o gatto» di chi ha il suo animale nel comune k (chiave «Comune|PR»).
    Conta solo se il comune è in sfida nel turno aperto. Restituisce (esito, dettagli): ok, gia, fuori."""
    ora = ora or datetime.now(timezone.utc)
    C = aggiorna(stato, animali, ora)
    if C.get("chiuso") or not avversario(C, k): return "fuori", {}
    u = utente.lower()
    if not any(a.get("u", "").lower() == u and a.get("k") == "animale" and chiave(a) == k for a in animali): return "fuori", {}
    q = C.setdefault("quartiere", {}).setdefault(k, {"u": [], "c": [], "chiuse": 0, "log": []})
    if id_commento in q["c"] or u in q["u"]:
        return "gia", {**dettagli(C, k), **quartiere(C, k)}
    q["u"].append(u); q["c"].append(id_commento)
    prima = dettagli(C, k)
    fatte = len(q["u"]) // STAFFETTA
    chiusa = fatte > q["chiuse"]
    if chiusa:  # 3/3: il punto della Coppa, una volta sola per prova
        C["punti"][k] = C["punti"].get(k, 0) + (fatte - q["chiuse"]); q["chiuse"] = fatte
        q["log"].append({"t": ora.isoformat(timespec="minutes"), "prova": fatte})
        stato["staffette_log"] = (stato.get("staffette_log", []) + [{"k": k, "t": ora.isoformat(timespec="minutes"), "turno": C["turno"]}])[-500:]  # per il verbale del test
        d = dettagli(C, k)
        if prima.get("rivale") and prima["noi"] <= prima["loro"] and d["noi"] > d["loro"]:
            C["storia"].append({"t": ora.isoformat(timespec="minutes"), "sorpasso": k, "su": d["rivale"], "punti": [d["noi"], d["loro"]]})
            C["storia"] = C["storia"][-200:]
    st = quartiere(C, k)
    if chiusa: st["n"] = STAFFETTA  # appena chiusa si mostra 3/3
    return "ok", {**dettagli(C, k), **st, "chiusa": chiusa}


def punto(stato, animali, utente, codice_scritto, ora=None):
    """Un commento «COPPA XY». Restituisce (esito, dettagli): esito tra ok, gia, codice, chiuso, senza_luce."""
    ora = ora or datetime.now(timezone.utc)
    C = aggiorna(stato, animali, ora)
    u = utente.lower()
    oggi, ieri = giorno(ora), giorno(ora - timedelta(days=1))
    g = oggi if codice_scritto.upper() == codice(oggi) else ieri if codice_scritto.upper() == codice(ieri) else None
    if not g: return "codice", {}
    if C.get("chiuso") or g < C["inizio"][:10]: return "chiuso", {}
    k = C["squadra"].get(u)
    if not k:  # la squadra è il comune del suo primo animale, e resta quella per tutta la settimana
        suoi = sorted((a for a in animali if a.get("u", "").lower() == u and a.get("k") == "animale"), key=lambda a: str(a.get("ts", "")))
        if not suoi: return "senza_luce", {}
        k = C["squadra"][u] = chiave(suoi[0])
    if not avversario(C, k):  # un comune nuovo nel turno: sfida chi è in attesa, oppure aspetta il prossimo
        if C.get("attesa") and C["attesa"] != k: C["coppie"].append([C["attesa"], k]); C["attesa"] = None
        elif not C.get("attesa"): C["attesa"] = k
    giorni = C["giorni"].setdefault(u, [])
    if g in giorni:
        return "gia", dettagli(C, k)
    giorni.append(g)
    prima = dettagli(C, k)
    C["punti"][k] = C["punti"].get(k, 0) + 1
    gioc = C["giocatori"].setdefault(k, [])
    if u not in gioc: gioc.append(u)
    d = dettagli(C, k)
    if prima.get("rivale") and prima["noi"] <= prima["loro"] and d["noi"] > d["loro"]:  # sorpasso: per il reel di metà settimana
        C["storia"].append({"t": ora.isoformat(timespec="minutes"), "sorpasso": k, "su": d["rivale"], "punti": [d["noi"], d["loro"]]})
        C["storia"] = C["storia"][-200:]
    d["staffetta_nuova"] = len(gioc) == STAFFETTA
    return "ok", d


def dettagli(C, k):
    r = avversario(C, k)
    return {"comune": k, "noi": C["punti"].get(k, 0), "rivale": r, "loro": C["punti"].get(r, 0) if r else 0,
            "giocatori": len(C["giocatori"].get(k, [])), "fine": C["fine"]}


def pubblica(stato, out):
    """docs/data/coppa.json per il sito: le sfide coi punti, le staffette, i trofei dell'ultimo turno e l'albo. Niente nomi utente."""
    C = stato.get("coppa")
    if not C: return
    P, G = C["punti"], C["giocatori"]
    sfide = [{"a": a, "b": b, "pa": P.get(a, 0), "pb": P.get(b, 0), "ga": len(G.get(a, [])), "gb": len(G.get(b, []))} for a, b in C["coppie"]]
    albo = stato.get("coppa_albo", [])
    dati = {"turno": C["turno"], "inizio": C["inizio"], "fine": C["fine"], "chiuso": C.get("chiuso", False), "staffetta": STAFFETTA,
            "sfide": sfide,
            "anelli": staffette(C), "trofei": [v["c"] for v in (albo[-1]["vincitori"] if albo else [])], "albo": albo[-12:],
            "sorpassi": C.get("storia", [])[-10:],
            "quartiere": {k: quartiere(C, k) for k in C.get("quartiere", {})}}
    Path(out).write_text(json.dumps(dati, ensure_ascii=False, separators=(",", ":")) + "\n")
