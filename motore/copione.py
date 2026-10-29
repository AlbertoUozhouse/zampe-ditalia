"""Scrive il copione di un reel automatico partendo dai dati veri della mappa.

Uso: python3 motore/copione.py <formato|auto> <uscita.json>
Formati: duello (9:00), vetrina (13:00), fondatore (18:00), puntata (21:00). "auto" sceglie in base all'ora italiana.
Regola: nessun numero inventato. I numeri e i nomi vengono dai dati; Claude (se c'è ANTHROPIC_API_KEY) può solo
riformulare le frasi, e la riformulazione si scarta se cambia numeri o nomi o allunga troppo il testo.
"""
import unicodedata, json, os, random, re, sys, urllib.request
from datetime import datetime, date, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
STORICO = ROOT / "motore/reel_fatti.json"
LANCIO = date(2026, 10, 26)
ORA = datetime.now(ZoneInfo("Europe/Rome"))
BOOST = ORA.date().isoformat() <= "2026-11-01"  # Settimana del follow: SEGUO vale +30 (come in commenti.py)
PS, PS_P = ("+30", "trenta punti") if BOOST else ("+10", "dieci punti")

# account di Alberto: restano sulla mappa ma non vengono mai nominati nei reel (la pagina cresce da sola)
ESCLUSI = {"thor_golden_life", "albertomarchesin"}
MASCOTTE = "thor_golden_life"  # Thor, il golden della pagina: fa l'arbitro del derby, ma non gareggia mai

CITTA = ["Milano", "Roma", "Napoli", "Torino", "Palermo", "Genova", "Bologna", "Firenze", "Bari", "Catania", "Venezia", "Verona",
         "Padova", "Trieste", "Brescia", "Parma", "Modena", "Reggio nell'Emilia", "Perugia", "Cagliari", "Pescara", "Lecce", "Bergamo",
         "Trento", "Bolzano", "Ancona", "Salerno", "Rimini", "Treviso", "Vicenza", "Como", "Monza", "Pisa", "Siena", "Sassari", "Udine"]
NOMI_CANI = ["Luna", "Kira", "Rocky", "Milo", "Nala", "Leo", "Maya", "Bruno", "Zoe", "Birba", "Oliver", "Romeo", "Lilly", "Ares", "Penny", "Toby"]
COMUNI_CANI = {"golden", "labrador_miele", "labrador_nero", "pastore_tedesco", "beagle", "bassotto", "jack_russell", "border_collie", "husky", "chihuahua",
               "barboncino", "bulldog_francese", "cavalier", "shih_tzu", "maltese", "cocker", "volpino", "boxer", "carlino", "amstaff", "lagotto", "cane_corso"}
COMUNI_GATTI = {"europeo", "nero", "rosso", "bianco", "bicolore", "calico", "siamese", "persiano", "maine_coon", "british", "certosino", "ragdoll"}
NOMI_GATTI = ["Micio", "Nina", "Tigro", "Pallina", "Briciola", "Salem", "Cleo", "Oscar", "Mia", "Pepe", "Luna", "Ginger"]

def carica(p, vuoto):
    try: return json.loads(Path(p).read_text())
    except (FileNotFoundError, json.JSONDecodeError): return vuoto

def dati():
    A = carica(ROOT / "docs/data/animali.json", {"animali": []})["animali"]
    R = json.loads((ROOT / "docs/data/razze.json").read_text())
    an = [a for a in A if a.get("k") in ("animale", "sogno")]
    tifo = [a for a in A if a.get("k") == "tifo"]
    per_citta = {}
    for a in an + tifo:
        if a.get("t") == "altro": continue  # gli altri animali non entrano nella sfida Cani contro Gatti
        per_citta.setdefault(a["c"], {"cani": 0, "gatti": 0})["gatti" if a.get("t") == "gatto" else "cani"] += 1
    oggi = ORA.date().isoformat()
    nuovi_fondatori = [a for a in an if a.get("ruolo", "").startswith("Fondatore") and str(a.get("ts", ""))[:10] == oggi and a["u"].lower() not in ESCLUSI]
    J = carica(ROOT / "docs/data/animali.json", {})
    voti = J.get("voti", {"cani": 0, "gatti": 0})
    stato = carica(ROOT / "motore/stato.json", {})
    seguono = {u for u, v in stato.get("seguono", {}).items() if v == "premiato"}
    inviti = J.get("inviti", {})
    return {"voti": voti, "seguono": seguono, "inviti": inviti, "capibranco": J.get("capibranco", {}), "piu_bello": J.get("piu_bello"), "follower": J.get("follower"), "animali": an, "tifo": tifo, "tutti": A, "razze": R, "per_citta": per_citta, "nuovi_fondatori": nuovi_fondatori,
            "cani": sum(1 for a in an + tifo if a.get("t", "cane") == "cane"), "gatti": sum(1 for a in an + tifo if a.get("t") == "gatto"),
            "altri": sum(1 for a in an if a.get("t") == "altro" and a.get("k") == "animale")}

SOGLIA_ALTRI = 15  # con 15 luci gli altri animali entrano nella sfida (come in commenti.py)

def luci(D):
    return [{"lng": a["lng"], "lat": a["lat"], "t": a.get("t", "cane")} for a in D["tutti"] if a.get("k") != "stella"]

def luci_n(n): return f"{n} {'luce' if n == 1 else 'luci'}"

def veri(D, tipo):
    """Animali veri della mappa, da mostrare nei reel col loro @ (mai gli account di Alberto)."""
    return [a for a in D["animali"] if a.get("k") == "animale" and a.get("t", "cane") == tipo and a["u"].lower() not in ESCLUSI]

def scena_vera(D, rng, tipo, gia=()):
    """Una scena cuccia/gatto con un animale vero: nome, @ e comune. None se non ce ne sono."""
    # chi ci segue va nei reel per primo: è la ricompensa promessa a chi scrive SEGUO
    cand = [a for a in veri(D, tipo) if a["u"] not in gia]
    cand = [a for a in cand if a["u"].lower() in D.get("seguono", ())] or cand or veri(D, tipo)
    if not cand: return None
    a = rng.choice(cand)
    return a, {"tipo": "gatto" if tipo == "gatto" else "cuccia", "nome": a["n"], "razza": a.get("razza_testo") or a.get("razza") or ("europeo" if tipo == "gatto" else "meticcio"),
               "seme": abs(hash(a.get("id", a["u"] + a["n"]))) % 997 + 1, "utente": a["u"], "comune": a["c"]}

def esempio(rng, D):
    # negli esempi solo razze che tutti conoscono
    cane = rng.choice([r for r in D["razze"]["cani"] if r[0] in COMUNI_CANI])
    gatto = rng.choice([r for r in D["razze"]["gatti"] if r[0] in COMUNI_GATTI])
    return ({"nome": rng.choice(NOMI_CANI), "razza": cane[0], "parola": cane[2][0], "seme": rng.randint(1, 999)},
            {"nome": rng.choice(NOMI_GATTI), "razza": gatto[0], "parola": "gatto " + gatto[2][0] if gatto[0] in ("nero", "rosso", "bianco", "grigio") else gatto[2][0], "seme": rng.randint(1, 999)})

# ---------------------------------------------------------------- formati

def duello(D, rng, st):
    usate = set(sum(st.get("duelli", [])[-6:], []))
    a, b = rng.sample([c for c in CITTA if c not in usate] or CITTA, 2)
    ca, cb = (sum(D["per_citta"].get(x, {}).values()) for x in (a, b))
    cane, gatto = esempio(rng, D)
    st.setdefault("duelli", []).append([a, b])
    frasi = [
        (f"{a} o {b}?", {"tipo": "duello", "sinistra": {"titolo": a, "valore": luci_n(ca)}, "destra": {"titolo": b, "valore": luci_n(cb)}}),
        ("Quale città si accende per prima?", {"tipo": "mappa", "luci": luci(D), "citta": [{"nome": a, "testo": a + "?", "colore": "d", "t": 0.5}, {"nome": b, "testo": b + "?", "colore": "c", "t": 1.0}]}),
        ("Scrivi città, nome e razza del tuo animale.", {"tipo": "commento", "testo": f"{a}, {cane['nome']}, {cane['parola']}"}),
    ]
    v = scena_vera(D, rng, rng.choice(["cane", "gatto"]))
    if v:
        frasi.append((f"Come {v[0]['n']}, che ha acceso la sua luce a {v[0]['c']}.", v[1]))
    else:
        frasi.append(("Si accende la sua cuccia, col suo nome.", {"tipo": "cuccia", "nome": cane["nome"], "razza": cane["razza"], "seme": cane["seme"]}))
    frasi.append((f"Allora: {a} o {b}? Scrivi la tua città!", {"tipo": "chiusura", "testo": "👇 Scrivi la tua città qui sotto"}))
    did = f"{a} o {b}: quale città si accende per prima? 🐶🐱\n\nScrivi qui sotto città, nome e razza (per esempio «{a}, {cane['nome']}, {cane['parola']}»): entro 15 minuti la luce del tuo animale si accende sulla mappa col tuo @. Il primo di ogni comune diventa il Fondatore 👑"
    st["copertina"] = {"sopra": "SFIDA TRA CITTÀ", "grande": f"{a}<br><i>vs</i><br>{b}", "sotto": "Quale si accende prima?", "tema": "duello"}
    return "CANI vs GATTI", frasi, did

def vetrina(D, rng, st):
    cani = rng.sample([r for r in D["razze"]["cani"] if r[0] != "meticcio" and not r[0].endswith("_mix")], 4)
    gatti = rng.sample(D["razze"]["gatti"][9:], 2)
    an = [{"t": "cane", "razza": r[0], "nome": r[1].split(" (")[0][:16], "seme": rng.randint(1, 999)} for r in cani] + \
         [{"t": "gatto", "razza": r[0], "nome": r[1].split(" (")[0][:16], "seme": rng.randint(1, 999)} for r in gatti]
    rng.shuffle(an)
    nc, ng = len(D["razze"]["cani"]), len(D["razze"]["gatti"])
    cane, gatto = esempio(rng, D)
    citta = rng.choice(CITTA)
    frasi = [
        ("Ogni razza ha la sua cuccia.", {"tipo": "vetrina", "animali": an}),
        (f"Ne abbiamo già disegnate {nc + ng}.", {"tipo": "numero", "grande": str(nc + ng), "sotto": "razze di cani e gatti disegnate"}),
        ("C'è anche la tua? Scrivi città, nome e razza.", {"tipo": "commento", "testo": f"{citta}, {cane['nome']}, {cane['parola']}"}),
    ]
    v = scena_vera(D, rng, "gatto" if rng.random() < 0.4 else "cane")
    frasi.append((f"Come {v[0]['n']}, a {v[0]['c']}." if v else "E il tuo animale si accende così, col suo nome.",
                  v[1] if v else {"tipo": "cuccia", "nome": cane["nome"], "razza": cane["razza"], "seme": cane["seme"]}))
    frasi.append(("Qual è la tua razza? Scrivila qui sotto!", {"tipo": "chiusura", "testo": "👇 Scrivi la tua razza qui sotto"}))
    did = f"Ogni razza ha la sua cuccia 🐾 Sulla mappa di Zampe d'Italia ci sono già {nc} razze di cani e {ng} di gatti disegnate, ognuna diversa.\n\nScrivi qui sotto città, nome e razza: il tuo animale si accende sulla mappa col tuo @."
    st["copertina"] = {"sopra": f"{nc + ng} RAZZE", "grande": "C'è anche<br>la tua?", "sotto": "Ogni razza ha la sua cuccia", "tema": "vetrina"}
    return "CANI vs GATTI", frasi, did

def fondatore(D, rng, st):
    libere = [c for c in CITTA if sum(D["per_citta"].get(c, {}).values()) == 0 and c not in st.get("fondatori", [])[-8:]]
    if not libere: return duello(D, rng, st)
    c = rng.choice(libere); st.setdefault("fondatori", []).append(c)
    cane, gatto = esempio(rng, D)
    frasi = [
        (f"{c} non ha ancora un Fondatore.", {"tipo": "mappa", "luci": luci(D), "citta": [{"nome": c, "testo": c + "?", "colore": "d", "t": 0.3}], "zoom": {"comune": c, "s": 2.2}}),
        (f"Il primo che scrive {c}, nome e razza", {"tipo": "commento", "testo": f"{c}, {cane['nome']}, {cane['parola']}"}),
        ("accende la prima cuccia della città e diventa Fondatore. Per sempre.", {"tipo": "cuccia", "nome": cane["nome"], "razza": cane["razza"], "seme": cane["seme"], "comune": "Fondatore di " + c}),
        (f"Chi sarà il Fondatore di {c}? Scrivilo qui sotto!", {"tipo": "chiusura", "testo": f"👑 Diventa il Fondatore di {c}"}),
    ]
    did = f"{c} non ha ancora un Fondatore 👑\n\nIl primo animale di {c} che arriva sulla mappa lo diventa per sempre. Scrivi qui sotto «{c}, nome e razza» (per esempio «{c}, {cane['nome']}, {cane['parola']}»): entro 15 minuti la sua luce si accende."
    st["copertina"] = {"sopra": "CERCASI FONDATORE", "grande": c, "sotto": "Il primo diventa Fondatore 👑", "tema": "fondatore", "citta": c}
    return "CANI vs GATTI", frasi, did

def puntata(D, rng, st):
    n = (ORA.date() - LANCIO).days + 1
    tot = len([a for a in D["tutti"] if a.get("k") != "stella"])
    top = sorted(D["per_citta"].items(), key=lambda kv: -sum(kv[1].values()))[:5]
    cane, gatto = esempio(rng, D)
    # si apre sulla mappa con le luci vere già accese e la città in testa evidenziata
    pin = [{"nome": top[0][0], "testo": f"{top[0][0]} · {luci_n(sum(top[0][1].values()))}", "colore": "d"}] if top else []
    frasi = [(f"Giorno {n} della mappa: {tot} {'luce accesa' if tot == 1 else 'luci accese'} in Italia.", {"tipo": "mappa", "luci": luci(D), "citta": pin}),
             (f"Cani {D['cani']}, gatti {D['gatti']}.", {"tipo": "duello", "sinistra": {"titolo": "Cani", "valore": str(D["cani"])}, "destra": {"titolo": "Gatti", "valore": str(D["gatti"])}})]
    nf = [a["n"] for a in D["nuovi_fondatori"]][:3]
    if nf:
        frasi.append((f"Nuovi Fondatori di oggi: {', '.join(nf)}.", {"tipo": "classifica", "titolo": "Nuovi Fondatori 👑", "righe": [{"nome": a["n"], "valore": a["c"]} for a in D["nuovi_fondatori"][:5]]}))
    elif top:
        frasi.append(("Ecco le città più accese.", {"tipo": "classifica", "titolo": "Le città più accese", "righe": [{"nome": c, "valore": luci_n(sum(v.values()))} for c, v in top]}))
    cb = D.get("capibranco", {})
    if cb.get("giorno") == ORA.date().isoformat():  # domenica: l'elezione appena fatta apre la puntata dopo la mappa
        capi = [x for x in cb.get("lista", []) if x[0].lower() not in ESCLUSI][:5]
        if capi:
            frasi.insert(1, (f"Stasera si eleggono i Capibranco: {cb['quanti']} città hanno il loro capo!",
                             {"tipo": "classifica", "titolo": "I nuovi Capibranco 🐺", "righe": [{"nome": f"{x[1]} · @{x[0]}", "valore": x[2]} for x in capi], "utente": capi[0][0]}))
            st["tag_extra"] = [x[0] for x in capi]
    pb = D.get("piu_bello")
    vinto = pb and pb.get("giorno") == ORA.date().isoformat() and next((a for a in D["animali"] if a.get("id") == pb["id"]), None)
    if vinto:  # domenica: la Sfilata degli accessori ha il suo vincitore
        frasi.insert(1, (f"Il più bello d'Italia è {vinto['n']}, di {vinto['c']}, con {len(vinto.get('acc', []))} accessori!", {**scena_di(vinto, "🏆 Il più bello d'Italia")}))
        st.setdefault("tag_extra", []).append(vinto["u"])
    re_inv = [x for x in D.get("inviti", {}).get("oggi", []) if x[0].lower() not in ESCLUSI]
    if re_inv:
        u, n_inv = re_inv[0]
        frasi.append((f"Re degli inviti di oggi: {u}, con {n_inv} {'amico' if n_inv == 1 else 'amici'}!",
                      {"tipo": "classifica", "titolo": "Re degli inviti 👑", "righe": [{"nome": "@" + x[0], "valore": f"{x[1]} {'amico' if x[1] == 1 else 'amici'}"} for x in re_inv[:3]], "utente": u}))
    frasi += [("Ogni commento è una luce: scrivi città, nome e razza.", {"tipo": "commento", "testo": f"{rng.choice(CITTA)}, {cane['nome']}, {cane['parola']}"}),
              ("Scrivi qui sotto e accendi la tua luce!", {"tipo": "chiusura", "testo": "👇 Accendi la tua luce qui sotto"})]
    did = f"Giorno {n} della mappa di Zampe d'Italia 🌙 {tot} {'luce accesa' if tot == 1 else 'luci accese'}: cani {D['cani']}, gatti {D['gatti']}.\n\nScrivi qui sotto città, nome e razza del tuo animale e accendi la tua luce col tuo @. Il primo di ogni comune diventa il Fondatore 👑"
    st["copertina"] = {"sopra": f"GIORNO {n}", "grande": f"{tot}<br>luci", "sotto": "La mappa di stasera 🌙", "tema": "puntata"}
    return f"GIORNO {n}", frasi, did

def voto(D, rng, st):
    """Il commento più facile: un'emoji. Porta commenti, e i commenti portano distribuzione."""
    v = D.get("voti", {"cani": 0, "gatti": 0})
    cani, gatti = D["cani"] + v.get("cani", 0), D["gatti"] + v.get("gatti", 0)
    if D["altri"] >= SOGLIA_ALTRI:
        return voto_tre(D, rng, st, cani, gatti, D["altri"] + v.get("altri", 0))
    perde = "gatti" if gatti < cani else "cani"
    frasi = [(f"Cani {cani}, gatti {gatti}. I {perde} stanno perdendo!" if cani != gatti else "Cani o gatti? È pareggio!",
              {"tipo": "duello", "sinistra": {"titolo": "Cani", "valore": str(cani)}, "destra": {"titolo": "Gatti", "valore": str(gatti)}}),
             ("Commenta con un'emoji: cane o gatto.", {"tipo": "commento", "testo": "🐱" if perde == "gatti" else "🐶"})]
    x = scena_vera(D, rng, rng.choice(["cane", "gatto"]))
    if x:
        frasi.append((f"Vuoi la tua luce come {x[0]['n']}? Città, nome e razza.", x[1]))
    manca = SOGLIA_ALTRI - D["altri"]
    frasi.append((f"E arrivano gli altri: ancora {manca} {'luce' if manca == 1 else 'luci'} e conigli, furetti e tartarughe entrano nella sfida!",
                  {"tipo": "numero", "grande": str(D["altri"]), "sotto": f"altri animali accesi: a {SOGLIA_ALTRI} entrano nella sfida 🐰🐢🦎"}))
    frasi.append(("Cani o gatti? Vota qui sotto!", {"tipo": "chiusura", "testo": "👇 Scrivi 🐶 o 🐱"}))
    did = f"Cani {cani}, gatti {gatti} 🐶🐱 Commenta con un'emoji e vediamo chi vince!\n\n🐰 Hai un coniglio, un furetto, una tartaruga? Ancora {manca} {'luce' if manca == 1 else 'luci'} e gli altri animali entrano nella sfida: scrivi città, nome e specie.\n\nVuoi accendere la luce del tuo animale sulla mappa d'Italia? Scrivi città, nome e razza (per esempio «Treviso, Luna, golden»)."
    st["copertina"] = {"sopra": "CANI vs GATTI", "grande": f"{cani} – {gatti}", "sotto": f"I {perde} perdono! Vota 🐶🐱" if cani != gatti else "Pareggio! Vota 🐶🐱", "tema": "voto"}
    return "CANI vs GATTI", frasi, did

def voto_tre(D, rng, st, cani, gatti, altri):
    """Da 15 altri animali la sfida è a tre: cani, gatti e tutti gli altri."""
    squadre = sorted([("Cani", cani, "🐶"), ("Gatti", gatti, "🐱"), ("Altri animali", altri, "🐰")], key=lambda x: -x[1])
    ultimo = squadre[-1]
    frasi = [(f"Cani {cani}, gatti {gatti}, altri animali {altri}. La sfida ora è a tre!",
              {"tipo": "classifica", "titolo": "La sfida a tre 🏆", "righe": [{"nome": f"{e} {n}", "valore": luci_n(x)} for n, x, e in squadre]}),
             (f"Ultimi: {ultimo[0].lower()}! Commenta con un'emoji e falli risalire.", {"tipo": "commento", "testo": ultimo[2]})]
    x = scena_vera(D, rng, rng.choice(["cane", "gatto"]))
    if x:
        frasi.append((f"Vuoi la tua luce come {x[0]['n']}? Città, nome e animale.", x[1]))
    frasi.append(("Cani, gatti o altri? Vota qui sotto!", {"tipo": "chiusura", "testo": "👇 Scrivi 🐶 🐱 o 🐰"}))
    did = (f"Cani {cani}, gatti {gatti}, altri animali {altri} 🐶🐱🐰 La sfida è a tre: commenta con un'emoji e vediamo chi vince!\n\n"
           "Conigli, furetti, tartarughe, gechi: si accendono tutti. Scrivi città, nome e animale (per esempio «Treviso, Luna, coniglio»).")
    st["copertina"] = {"sopra": "CANI · GATTI · ALTRI", "grande": "Sfida<br>a tre", "sotto": f"Ultimi: {ultimo[0].lower()}! Vota 🐶🐱🐰", "tema": "voto"}
    return "SFIDA A TRE", frasi, did

def benvenuti(D, rng, st):
    """Le nuove luci di oggi con i loro @: chi è nel reel viene taggato, riceve la notifica e di solito lo ricondivide."""
    oggi = ORA.date().isoformat()
    nuovi, visti = [], set()
    for a in sorted((a for a in D["animali"] if str(a.get("ts", ""))[:10] >= (ORA.date() - timedelta(days=1)).isoformat() and a["u"].lower() not in ESCLUSI),
                    key=lambda a: (a["u"].lower() not in D.get("seguono", ()), -(a.get("pt") or 0))):
        if a["u"] not in visti:
            visti.add(a["u"]); nuovi.append(a)
    if len(nuovi) < 3:
        return voto(D, rng, st)
    nuovi = nuovi[:5]
    cane, gatto = esempio(rng, D)
    frasi = [("Nuove luci accese sulla mappa!", {"tipo": "classifica", "titolo": "Benvenuti sulla mappa 🐾",
                                                "righe": [{"nome": a["n"], "valore": a["c"]} for a in nuovi]})]
    star = next((a for a in nuovi if a.get("t") in ("cane", "gatto")), None)
    if star:
        sc = scena_vera({**D, "animali": [star]}, rng, star["t"])
        if sc: frasi.append((f"Benvenuto {star['n']}, da {star['c']}!", sc[1]))
    frasi += [("Domani nel reel ci sei tu: scrivi città, nome e animale.", {"tipo": "commento", "testo": f"{rng.choice(CITTA)}, {cane['nome']}, {cane['parola']}"}),
              ("Scrivi qui sotto e accendi la tua luce!", {"tipo": "chiusura", "testo": "👇 Domani nel reel ci sei tu"})]
    did = ("Nuove luci accese sulla mappa di Zampe d'Italia 🐾 Benvenuti " + ", ".join(f"{a['n']} di {a['c']} (@{a['u']})" for a in nuovi) +
           "!\n\nVuoi esserci nel prossimo reel? Scrivi qui sotto città, nome e animale: la luce si accende entro 15 minuti col tuo @.")
    st["tag_extra"] = [a["u"] for a in nuovi]
    st["copertina"] = {"sopra": "NUOVE LUCI", "grande": "<br>".join(a["n"] for a in nuovi[:3]), "sotto": "Benvenuti sulla mappa 🐾", "tema": "benvenuti"}
    return "NUOVE LUCI", frasi, did

def attivita(D, rng, st):
    """Per le attività legate agli animali: prenotano gratis il posto sulla mappa, con il -20%. Ci dice se c'è mercato prima di vendere."""
    tot = len([a for a in D["tutti"] if a.get("k") in ("animale", "sogno")])
    top = sorted(D["per_citta"].items(), key=lambda kv: -sum(kv[1].values()))[:5]
    c0 = top[0][0] if top else "Roma"
    frasi = [("Hai un'attività per animali? Veterinario, toelettatura, negozio, pensione.", {"tipo": "mappa", "luci": luci(D), "citta": [{"nome": c0, "testo": c0, "colore": "d"}]}),
             (f"Sulla mappa ci sono già {tot} animali, ognuno con la sua città.", {"tipo": "numero", "grande": str(tot), "sotto": "proprietari di animali, città per città"}),
             ("Ecco dove si accendono di più.", {"tipo": "classifica", "titolo": "Le città più accese", "righe": [{"nome": c, "valore": luci_n(sum(v.values()))} for c, v in top]}),
             (f"Presto ogni città avrà la sua clinica, la sua toelettatura e il suo negozio. Uno solo per tipo.", {"tipo": "commento", "testo": f"🏥 Clinica veterinaria di {c0}: posto libero"}),
             ("Chi prenota adesso ha la precedenza e il venti per cento di sconto.", {"tipo": "numero", "grande": "-20%", "sotto": "per chi prenota adesso il suo posto"}),
             ("Scrivici PRENOTA in privato!", {"tipo": "chiusura", "testo": "📩 Scrivi PRENOTA in DM"})]
    did = (f"Hai un'attività per animali? 🐾 Sulla mappa di Zampe d'Italia ci sono già {tot} animali, ognuno con il suo @ e la sua città.\n\n"
           "Presto ogni comune avrà la sua clinica veterinaria, la sua toelettatura, il suo negozio per animali e la sua pensione, uno solo per tipo: "
           "chi gioca li vede vicino a casa e ti scrive con un tocco.\n\n"
           "📩 Scrivici PRENOTA in privato con il tipo di attività e il comune: ti teniamo il posto, con la precedenza e il -20% per i primi 6 mesi. Prenotare è gratis e senza impegno.")
    st["copertina"] = {"sopra": "PER LE ATTIVITÀ", "grande": "La clinica<br>del paese", "sotto": "Prenota gratis: -20% 🐾", "tema": "attivita"}
    st["senza_bonus"] = True
    return "PER LE ATTIVITÀ", frasi, did

# capoluogo e articolo di ogni regione, per il formato «buio»
REGIONI = {"Abruzzo": ("L'Aquila", "l'"), "Basilicata": ("Potenza", "la "), "Calabria": ("Catanzaro", "la "), "Campania": ("Napoli", "la "),
           "Emilia-Romagna": ("Bologna", "l'"), "Friuli-Venezia Giulia": ("Trieste", "il "), "Lazio": ("Roma", "il "), "Liguria": ("Genova", "la "),
           "Lombardia": ("Milano", "la "), "Marche": ("Ancona", "le "), "Molise": ("Campobasso", "il "), "Piemonte": ("Torino", "il "),
           "Puglia": ("Bari", "la "), "Sardegna": ("Cagliari", "la "), "Sicilia": ("Palermo", "la "), "Toscana": ("Firenze", "la "),
           "Trentino-Alto Adige": ("Trento", "il "), "Umbria": ("Perugia", "l'"), "Valle d'Aosta": ("Aosta", "la "), "Veneto": ("Venezia", "il ")}

def buio(D, rng, st):
    """Come il reel che ha reso di più («Questa è l'Italia di notte… e non c'è ancora nemmeno un cane»):
    la mappa al buio fa venire voglia di accendere. Ogni volta la regione con meno luci, senza ripetere le ultime 4."""
    conta = {r: 0 for r in REGIONI}
    for a in D["tutti"]:
        if a.get("k") != "stella" and a.get("r") in conta: conta[a["r"]] += 1
    giro = [r for r in sorted(conta, key=lambda r: (conta[r], r)) if r not in st.get("buio", [])[-4:]]
    r = giro[0]; st.setdefault("buio", []).append(r)
    cap, art = REGIONI[r]; n = conta[r]; Art = art[0].upper() + art[1:]
    cane, gatto = esempio(rng, D)
    stato = "è ancora al buio: nemmeno un cane." if n == 0 else f"è quasi al buio: {luci_n(n)} in tutta la regione."
    sono = "sono" if art == "le " else "è"
    stato = stato.replace("è ", sono + " ", 1)
    frasi = [
        ("Questa è l'Italia di notte.", {"tipo": "mappa", "luci": luci(D)}),
        (f"{Art}{r} {stato}", {"tipo": "mappa", "luci": luci(D), "citta": [{"nome": cap, "testo": f"{r}: {n}", "colore": "d", "t": 0.3}], "zoom": {"comune": cap, "s": 2.0}}),
        ("Ogni commento accende una luce: città, nome e razza.", {"tipo": "commento", "testo": f"{cap}, {cane['nome']}, {cane['parola']}"}),
        (f"Accendiamo {art}{r}? Scrivilo qui sotto!", {"tipo": "chiusura", "testo": f"🌙 Accendi {art}{r}"}),
    ]
    did = (f"Questa è l'Italia di notte 🌙 e {art}{r} {stato}\n\nOgni commento accende una luce: scrivi qui sotto città, nome e razza "
           f"(per esempio «{cap}, {cane['nome']}, {cane['parola']}» o «{cap}, {gatto['nome']}, {gatto['parola']}») e la cuccia del tuo cane o gli occhi del tuo gatto si accendono sulla mappa col tuo @.\n\n"
           "👑 Il primo di ogni comune diventa il Fondatore.\nMappa nel link in bio.")
    st["copertina"] = {"sopra": "L'ITALIA DI NOTTE", "grande": f"{r}<br>al buio", "sotto": "Accendi la prima luce 🌙", "tema": "buio"}
    return "L'ITALIA DI NOTTE", frasi, did

def altri(D, rng, st):
    """Un reel diretto a chi ha un coniglio, una tartaruga, un pappagallo…: anche loro accendono una luce."""
    brutti = re.compile(r"(?i)cogl|cazz|merd|stronz|fig[ao]|puttan|troi|culo|minchi")  # nomi che in un reel non vanno
    veri_altri = [a for a in D["animali"] if a.get("t") == "altro" and a.get("k") == "animale" and a["u"].lower() not in ESCLUSI and not brutti.search(a["n"])]
    veri_altri.sort(key=lambda a: a["u"].lower() not in D.get("seguono", ()))  # prima chi ci segue
    an, specie = [], set()
    for a in veri_altri:
        sp = (a.get("specie") or "").split()[0]
        if sp and sp not in specie and len(an) < 6: specie.add(sp); an.append({"t": "altro", "razza": sp, "nome": f"{a['n']}"[:14], "seme": rng.randint(1, 999), "u": a["u"]})
    for sp, nome in [("coniglio", "Coniglio"), ("tartaruga", "Tartaruga"), ("pappagallo", "Pappagallo"), ("criceto", "Criceto"), ("furetto", "Furetto"), ("geco", "Geco")]:
        if len(an) >= 4: break
        if sp not in specie: specie.add(sp); an.append({"t": "altro", "razza": sp, "nome": nome, "seme": rng.randint(1, 999)})
    na, citta = D["altri"], rng.choice(CITTA)
    nome = rng.choice(["Ugo", "Briciola", "Nocciola", "Pepe", "Kiwi", "Tito"])
    frasi = [
        ("Non solo cani e gatti.", {"tipo": "vetrina", "animali": [{k: v for k, v in x.items() if k != "u"} for x in an]}),
        (f"Sulla mappa ci sono già {na} altri animali: conigli, tartarughe, pappagalli.", {"tipo": "numero", "grande": str(na), "sotto": "altri animali già accesi 🐰🐢🦜"}),
        ("Hai un coniglio, un criceto o una tartaruga? Scrivi città, nome e animale.", {"tipo": "commento", "testo": f"{citta}, {nome}, coniglio"}),
        (("Ora la sfida è a tre: cani, gatti e altri animali!" if na >= SOGLIA_ALTRI else f"Ancora {SOGLIA_ALTRI - na} e anche loro entrano nella sfida!"),
         {"tipo": "numero", "grande": "3", "sotto": "squadre: cani, gatti e altri animali 🐰"}),
        ("Scrivilo qui sotto e accendi la sua luce!", {"tipo": "chiusura", "testo": "🐰 Accendi il tuo animale qui sotto"}),
    ]
    st["tag_extra"] = [x["u"] for x in an if x.get("u")]
    did = (f"Non solo cani e gatti 🐰🐢🦜 Sulla mappa di Zampe d'Italia ci sono già {na} altri animali: conigli, tartarughe, pappagalli, criceti, furetti.\n\n"
           f"Hai un animale speciale? Scrivi qui sotto città, nome e animale (per esempio «{citta}, {nome}, coniglio»): entro 15 minuti si accende la sua luce sulla mappa col tuo @. "
           "E la sfida ora è a tre: cani contro gatti contro altri animali!")
    st["hashtag"] = "#conigli #tartarughe #pappagalli #criceti #furetti #animalidomestici "
    st["copertina"] = {"sopra": "NON SOLO CANI E GATTI", "grande": "Hai un<br>coniglio?", "sotto": "Anche lui accende una luce 🐰", "tema": "benvenuti"}
    return "CANI vs GATTI vs ALTRI", frasi, did

def derby(D, rng, st):
    """Il Derby della settimana (motore/derby.py): due province rivali, vince chi accende più luci nuove entro domenica alle 21.
    Il campanilismo fa taggare gli amici della propria città: è il reel delle condivisioni."""
    import derby as DB
    R = DB.riassunto(D["tutti"], ORA)
    d = R["ora"]; a, b, na, nb = d["a"], d["b"], d["na"], d["nb"]
    fine = datetime.fromisoformat(d["fine"]); giorni = (fine.date() - ORA.date()).days
    quando = "stasera alle 21" if giorni == 0 else "domani sera" if giorni == 1 else "domenica alle 21"
    cane, gatto = esempio(rng, D)
    frasi = []
    ult = R["albo"][-1] if R["albo"] else None
    if ult and (ORA - datetime.fromisoformat(ult["fine"])).days < 2:  # il derby appena finito apre il reel nuovo
        if ult["vince"]:
            perde, pv, pp = (ult["b"], ult["na"], ult["nb"]) if ult["vince"] == ult["a"] else (ult["a"], ult["nb"], ult["na"])
            frasi.append((f"{ult['vince']} ha vinto il derby contro {perde}, {pv} a {pp}!", {"tipo": "duello", "sinistra": {"titolo": ult["a"], "valore": str(ult["na"])}, "destra": {"titolo": ult["b"], "valore": str(ult["nb"])}}))
        else:
            frasi.append((f"{ult['a']} e {ult['b']}: pareggio, {ult['na']} a {ult['nb']}!", {"tipo": "duello", "sinistra": {"titolo": ult["a"], "valore": str(ult["na"])}, "destra": {"titolo": ult["b"], "valore": str(ult["nb"])}}))
        frasi.append((f"Nuovo derby: {a} contro {b}!", {"tipo": "mappa", "luci": luci(D), "citta": [{"nome": a, "testo": a, "colore": "d", "t": 0.3}, {"nome": b, "testo": b, "colore": "c", "t": 0.8}]}))
    else:
        if na == nb:
            stato = f"Derby {a} contro {b}: {na} a {nb}, tutto aperto!" if na else f"Parte il derby: {a} contro {b}!"
        else:
            avanti, dietro = (a, b) if na > nb else (b, a)
            stato = f"Derby {a} contro {b}: {max(na, nb)} a {min(na, nb)}. {dietro}, ci sei?"
        frasi.append((stato, {"tipo": "duello", "sinistra": {"titolo": a, "valore": luci_n(na)}, "destra": {"titolo": b, "valore": luci_n(nb)}}))
        frasi.append(("Vale tutta la provincia: ogni animale è una luce.",
                      {"tipo": "mappa", "luci": luci(D), "citta": [{"nome": a, "testo": f"{a} · {na}", "colore": "d", "t": 0.3}, {"nome": b, "testo": f"{b} · {nb}", "colore": "c", "t": 0.8}]}))
    thor = next((x for x in D["tutti"] if x["u"] == MASCOTTE and x.get("k") == "animale"), None)
    if thor:
        frasi.append(("L'arbitro è Thor: il primo cane acceso sulla mappa.", {"tipo": "cuccia", "nome": thor["n"], "razza": thor.get("razza") or "golden", "seme": sum(map(ord, thor["id"])) % 997 + 1,
                                                             "utente": MASCOTTE, "comune": "Arbitro del derby ⚖️"}))
    frasi += [
        (f"Scrivi città, nome e razza: {a}, {cane['nome']}, {cane['parola']}.", {"tipo": "commento", "testo": f"{a}, {cane['nome']}, {cane['parola']}"}),
        (f"E tagga un amico della tua città: si chiude {quando}.", {"tipo": "numero", "grande": f"+{DB.PREMIO}", "sotto": f"punti a chi accende la provincia che vince il derby 🏆"}),
        (f"{a} o {b}? Scrivi la tua città!", {"tipo": "chiusura", "testo": f"⚔️ {a} o {b}? Scrivilo qui sotto"}),
    ]
    # nel reel i primi che hanno acceso ciascuna città: ricevono la notifica e chiamano gli amici
    per = DB.conta(D["tutti"], {"inizio": datetime.fromisoformat(d["inizio"]), "fine": fine, "a": (a, d["pa"]), "b": (b, d["pb"])})
    st["tag_extra"] = [x["u"] for p in (d["pa"], d["pb"]) for x in per[p][:3]]
    did = (f"⚔️ Il Derby della settimana: {a} contro {b}! " + (f"Ora siamo {na} a {nb}." if na + nb else "Si parte da 0 a 0.") + "\n\n"
           f"Vale tutta la provincia: scrivi qui sotto città, nome e razza del tuo animale (per esempio «{a}, {cane['nome']}, {cane['parola']}» o «{b}, {gatto['nome']}, {gatto['parola']}») "
           f"e la sua luce si accende per la tua città. Si chiude {quando}: chi ha acceso la provincia che vince prende +{DB.PREMIO} punti 🏆\n\n"
           f"👥 Tagga un amico di {a} o di {b}: ogni amico che commenta è una luce in più.\n\n⚖️ L'arbitro del derby è Thor, il primo cane che si è acceso sulla mappa: seguilo su @{MASCOTTE} 🐾")
    st["hashtag"] = "#derby #cani #gatti #animalidomestici #italia "
    st["copertina"] = {"sopra": "⚔️ IL DERBY", "grande": f"{a}<br><i>vs</i><br>{b}", "sotto": f"{na} – {nb} · chi si accende di più? ⚔️", "tema": "duello"}
    return "IL DERBY", frasi, did

def _ts(a):
    try: return datetime.strptime(str(a.get("ts", "")), "%Y-%m-%dT%H:%M:%S%z")
    except ValueError: return None

def scena_di(a, comune=None):
    return {"tipo": "gatto" if a.get("t") == "gatto" else "cuccia", "nome": a["n"], "razza": a.get("razza_testo") or a.get("razza") or ("europeo" if a.get("t") == "gatto" else "meticcio"),
            "seme": abs(hash(a.get("id", a["u"] + a["n"]))) % 997 + 1, "utente": a["u"], "comune": comune or a["c"]}

LIVELLI = [(30, "giardino"), (50, "villa"), (70, "castello")]  # come in docs/app.js: più punti, più la cuccia cresce

def gara(D, rng, st):
    """Come i reel che rendono di più nelle pagine simili: persone vere e gare vere, con un numero grande in apertura.
    «A Livorno Chicco ha battuto Kira di 6 secondi» + chi è in testa ai punti. I nomi e i secondi vengono dai dati."""
    an = [a for a in D["animali"] if a.get("k") == "animale" and _ts(a) and a["u"].lower() not in ESCLUSI]
    tot = len([a for a in D["tutti"] if a.get("k") != "stella"])
    nc = len({a["c"] for a in D["tutti"] if a.get("k") != "stella"})
    g = (ORA.date() - LANCIO).days + 1
    cane, gatto = esempio(rng, D)
    frasi = [(f"In {g} giorni si sono accesi {tot} animali, in {nc} città.", {"tipo": "numero", "grande": str(tot), "sotto": f"animali accesi in {g} giorni · {nc} città 🐾"})]
    # la gara per diventare Fondatore più tirata, senza ripetere le ultime 10
    per = {}
    for a in sorted(an, key=_ts): per.setdefault(a["c"], []).append(a)
    gare = []
    for c, l in per.items():
        sec = next((l[i] for i in range(1, len(l)) if l[i]["u"] != l[0]["u"]), None)
        if sec and c not in st.get("gare", [])[-10:]:
            gare.append(((_ts(sec) - _ts(l[0])).total_seconds(), c, l[0], sec))
    gare = [x for x in sorted(gare, key=lambda x: x[0]) if x[0] <= 900]
    tag = []
    if gare:
        s, c, p, q = gare[0]; st.setdefault("gare", []).append(c)
        quanto = f"{int(s)} {'secondo' if int(s) == 1 else 'secondi'}" if s < 120 else f"{round(s / 60)} minuti"
        frasi.append((f"A {c} {p['n']} ha battuto {q['n']} di {quanto}: è il Fondatore!", {**scena_di(p, f"Fondatore di {c} 👑")}))
        tag += [p["u"], q["u"]]
        st["copertina"] = {"sopra": f"⏱️ {quanto.upper()}", "grande": c, "sotto": "Fondatore per un soffio 👑", "tema": "fondatore", "citta": c}
    top = sorted(an, key=lambda a: -a.get("pt", 0))[:3]
    if top and top[0].get("pt"):
        cast = sum(1 for a in an if a.get("pt", 0) >= LIVELLI[-1][0])
        frasi.append(((f"Solo {cast} animali hanno il castello. " if 1 < cast < 30 else "") + f"In testa c'è {top[0]['n']}, di {top[0]['c']}, con {top[0]['pt']} punti.",
                      {"tipo": "classifica", "titolo": "In testa 🏆", "righe": [{"nome": f"{a['n']} · @{a['u']}", "valore": f"{a.get('pt', 0)} pt"} for a in top], "utente": top[0]["u"]}))
        tag += [a["u"] for a in top]
    frasi += [("E la tua città? Scrivi città, nome e razza.", {"tipo": "commento", "testo": f"{rng.choice(CITTA)}, {cane['nome']}, {cane['parola']}"}),
              ("Arriva primo nel tuo comune: scrivilo qui sotto!", {"tipo": "chiusura", "testo": "👑 Arriva primo nella tua città"})]
    st["tag_extra"] = list(dict.fromkeys(tag))
    did = f"In {g} giorni sulla mappa di Zampe d'Italia si sono accesi {tot} animali, in {nc} città 🐾\n\n"
    if gare:
        did += f"⏱️ A {c} @{p['u']} ({p['n']}) ha commentato {quanto} prima di @{q['u']} ({q['n']}): Fondatore per sempre 👑\n"
    if top and top[0].get("pt"):
        did += "🏰 Più punti fai, più la cuccia cresce: 🌸 giardino a 30 punti, 🏡 villa a 50, 🏰 castello a 70\n"
        did += "🏆 In testa: " + ", ".join(f"@{a['u']} ({a['c']}) {a.get('pt', 0)} punti" for a in top) + "\n"
    did += (f"\nScrivi qui sotto città, nome e razza del tuo animale (per esempio «{rng.choice(CITTA)}, {gatto['nome']}, {gatto['parola']}»): entro 15 minuti si accende sulla mappa col tuo @. "
            "Chi arriva primo nel suo comune diventa il Fondatore, prima che qualcuno arrivi prima di te 👀")
    st.setdefault("copertina", {"sopra": f"{tot} ANIMALI", "grande": f"{g} giorni", "sotto": "Chi arriva primo nella tua città? 👑", "tema": "fondatore"})
    return "LA GARA", frasi, did

def negozio(D, rng, st):
    """Il reel del negozio: accessori da 1 euro, per sempre sulla mappa, e la Sfilata del più bello d'Italia ogni domenica."""
    J = carica(ROOT / "docs/data/animali.json", {})
    top = [next((a for a in D["animali"] if a.get("id") == i), None) for i, _ in J.get("sfilata", [])][:3]
    top = [a for a in top if a and a["u"].lower() not in ESCLUSI]
    cane, gatto = esempio(rng, D)
    frasi = [("Da oggi puoi regalare un accessorio al tuo animale sulla mappa.", {"tipo": "numero", "grande": "👑", "sotto": "corona · fiocco · collare d'oro · fuochi d'artificio"}),
             ("Si parte da 1 euro, ed è per sempre.", {"tipo": "numero", "grande": "1 €", "sotto": "🦴 1 € · 🎀 1,49 · 📿 1,99 · 👑 2,99 · 🎆 3,99"})]
    if top:
        frasi.append((f"In testa alla Sfilata c'è {top[0]['n']}, di {top[0]['c']}.", {"tipo": "classifica", "titolo": "La Sfilata 🏆", "righe": [{"nome": f"{a['n']} · @{a['u']}", "valore": f"{len(a.get('acc', []))} accessori"} for a in top], "utente": top[0]["u"]}))
        st["tag_extra"] = [a["u"] for a in top]
    frasi += [("Ogni domenica il più accessoriato diventa il più bello d'Italia.", {"tipo": "numero", "grande": "🏆", "sotto": "il più bello d'Italia: piedistallo d'oro e la puntata delle 21"}),
              ("Non sei ancora sulla mappa? Scrivi città, nome e razza.", {"tipo": "commento", "testo": f"{rng.choice(CITTA)}, {cane['nome']}, {cane['parola']}"}),
              ("Il negozio è nel link in bio!", {"tipo": "chiusura", "testo": "🛍️ Negozio nel link in bio"})]
    did = ("👑 Da oggi sulla mappa di Zampe d'Italia puoi regalare un accessorio al tuo animale, per sempre: 🦴 osso d'oro 1 €, 🎀 fiocco 1,49 €, 📿 collare d'oro 1,99 €, 👑 corona 2,99 €, 🎆 fuochi d'artificio 3,99 €.\n\n"
           "Ogni regalo finisce nella nostra storia 🎉 e ogni domenica alle 21 il più accessoriato diventa 🏆 Il più bello d'Italia.\n\n"
           "🛍️ Negozio su zampeditalia.it (link in bio) → «Il mio» → cerca il tuo @.\n\n"
           f"Non sei ancora sulla mappa? Scrivi qui sotto città, nome e razza (per esempio «{rng.choice(CITTA)}, {gatto['nome']}, {gatto['parola']}»).")
    st["copertina"] = {"sopra": "🛍️ IL NEGOZIO", "grande": "Da 1 €", "sotto": "Il più bello d'Italia? 🏆", "tema": "attivita"}
    return "IL NEGOZIO", frasi, did

FORMATI = {"negozio": negozio, "gara": gara, "derby": derby, "altri": altri, "buio": buio, "attivita": attivita, "benvenuti": benvenuti, "voto": voto, "duello": duello, "vetrina": vetrina, "fondatore": fondatore, "puntata": puntata}
ORARI = [(9, "duello"), (11, "voto"), (13, "benvenuti"), (16, "voto"), (18, "fondatore"), (21, "puntata"), (22, "voto")]

# ---------------------------------------------------------------- variazione con Claude, entro regole rigide

def numeri(s): return re.findall(r"\d+", s)

MAX_PAROLE = 70  # circa 30 secondi di voce: oltre, il reel perde chi guarda (e costruisci.py scarta sopra i 40)

def taglia(frasi):
    """Troppe parole (la domenica, con Capobranco, Re degli inviti e bonus insieme): via le scene di mezzo, dalla più vicina alla fine.
    Restano sempre l'apertura, il bonus e la chiusura."""
    frasi = list(frasi)
    while sum(len(t.split()) for t, _ in frasi) > MAX_PAROLE and len(frasi) > 4:
        via = next((i for i in range(len(frasi) - 3, 0, -1) if frasi[i][1]["tipo"] == "commento"), len(frasi) - 3)
        print("scena tolta per stare nei tempi:", frasi.pop(via)[0])
    return frasi

def varia(frasi, didascalia, D):
    k = os.environ.get("ANTHROPIC_API_KEY")
    if not k: return frasi, didascalia
    # parole che non si possono toccare: città, nomi degli animali e razze presenti nelle frasi
    protette = set(CITTA) | set(NOMI_CANI) | set(NOMI_GATTI) | {r[2][0] for r in D["razze"]["cani"] + D["razze"]["gatti"]}
    def intoccabili(t): return {w for w in protette if re.search(r"(?<![\w])" + re.escape(w) + r"(?![\w])", t, re.I)}
    richiesta = {"frasi": [t for t, _ in frasi], "didascalia": didascalia}
    prompt = ("Sei l'autore dei reel di Zampe d'Italia, gioco Instagram in cui ogni animale commentato accende una luce sulla mappa d'Italia. "
              "Riscrivi in italiano naturale, caldo ed entusiasta le frasi della voce e la didascalia qui sotto, per non ripetere sempre le stesse parole. "
              "Regole obbligatorie: stesso numero di frasi e stesso ordine; ogni frase dice la stessa cosa e resta lunga al massimo come l'originale più 15 caratteri; "
              "non aggiungere né cambiare numeri, città, nomi o razze; niente link, niente emoji nelle frasi della voce; la didascalia può avere 1-3 emoji e niente hashtag. "
              "Rispondi solo con JSON: {\"frasi\": [...], \"didascalia\": \"...\"}.\n\n" + json.dumps(richiesta, ensure_ascii=False))
    body = {"model": "claude-sonnet-5-5", "max_tokens": 1200, "messages": [{"role": "user", "content": prompt}]}
    try:
        r = urllib.request.Request("https://api.anthropic.com/v1/messages", data=json.dumps(body).encode(),
                                   headers={"x-api-key": k, "anthropic-version": "2023-06-01", "content-type": "application/json"})
        blocchi = json.loads(urllib.request.urlopen(r, timeout=60).read())["content"]
        testo = next(b["text"] for b in blocchi if b.get("type") == "text")
        try:
            nuovo = json.loads(testo[testo.find("{"):testo.rfind("}") + 1])
        except json.JSONDecodeError:
            print("risposta di Claude non in JSON:", testo[:300].replace("\n", " ")); return frasi, didascalia
        nf = nuovo["frasi"]
        ok = len(nf) == len(frasi) and all(
            sorted(numeri(a)) == sorted(numeri(b)) and len(b) <= len(a) + 15 and intoccabili(a) <= intoccabili(b) and "http" not in b
            for (a, _), b in zip(frasi, nf))
        ok = ok and sorted(numeri(didascalia)) == sorted(numeri(nuovo["didascalia"])) and "http" not in nuovo["didascalia"]
        if not ok:
            print("variazione di Claude scartata: non rispetta le regole"); return frasi, didascalia
        return [(b, sc) for (_, sc), b in zip(frasi, nf)], nuovo["didascalia"]
    except Exception as e:
        print(f"variazione di Claude non disponibile ({e}): uso il modello fisso"); return frasi, didascalia

def main():
    formato, uscita = sys.argv[1].split(":")[0], sys.argv[2]  # «fondatore:prova» è un Trial Reel: il copione è lo stesso
    if formato == "auto":
        formato = min(ORARI, key=lambda o: abs(o[0] - ORA.hour))[1]
    st = carica(STORICO, {})
    rng = random.Random(ORA.strftime("%Y%m%d%H") + formato)
    D = dati()
    titolo, frasi, did = FORMATI[formato](D, rng, st)
    # in ogni reel, prima della chiusura, un bonus a rotazione: tagga un amico (+3) oppure seguici (+5)
    x = rng.random()
    per_attivita = st.pop("senza_bonus", False)
    if per_attivita:
        pass  # il reel per le attività ha già la sua azione: niente bonus per i giocatori
    elif ORA.date().isoformat() <= "2026-11-02":  # Halloween: il follow regala il costume, lo diciamo in ogni reel
        frasi.insert(len(frasi) - 1, (rng.choice([f"Seguici e scrivi seguo: {PS_P} e il costume di Halloween per il tuo animale sulla mappa!",
                                                   "Chi ci segue ha il costume di Halloween sulla mappa: seguici e scrivi seguo!"]),
                                      {"tipo": "numero", "grande": "🎃" if not BOOST else PS, "sotto": f"seguici e scrivi SEGUO: {PS} punti e il costume di Halloween"}))
    elif x < 0.35:
        frasi.insert(len(frasi) - 1, (rng.choice(["Sfida degli inviti: chi porta più amici oggi finisce nel reel delle 21.",
                                                   "Tagga i tuoi amici: chi ne porta di più oggi è il Re degli inviti."]),
                                      {"tipo": "numero", "grande": "+3", "sotto": "per ogni amico taggato che commenta · il primo è Re degli inviti 👑"}))
    else:
        frasi.insert(len(frasi) - 1, (rng.choice(["Seguici e scrivi seguo: dieci punti e le lucine sulla cuccia del tuo animale!",
                                                   "Chi ci segue sta in prima fila nel suo paese, con le lucine: scrivi seguo!"]),
                                      {"tipo": "numero", "grande": "+10", "sotto": "seguici e scrivi SEGUO: lucine sulla cuccia e prima fila nel tuo paese ✨"}))
    if per_attivita:
        did = did.strip() + "\n\n"
    else:
        did = did.strip() + ("\n\n🎃 Fino al 2 novembre chi ci segue ha il costume di Halloween sulla mappa" if ORA.date().isoformat() <= "2026-11-02" else "\n\n✨ Chi ci segue ha le lucine sulla cuccia e sta in prima fila nel suo paese sulla mappa") + (("\n\n🔥 Settimana del follow: fino a domenica chi ci segue e scrive SEGUO prende +30 punti" if BOOST else "") + "\n\n➕ Seguici e scrivi SEGUO: " + PS + " punti, e nei reel mettiamo prima gli animali di chi ci segue. Il paese della tua città è su zampeditalia.it"
                             "\n👥 Sfida degli inviti: +3 per ogni amico taggato che commenta. Chi ne porta di più oggi è il Re degli inviti 👑 e va nella puntata delle 21")
    if not per_attivita:  # nel reel per le attività la parola PRENOTA non si tocca
        frasi, did = varia(frasi, did, D)
    frasi = taglia(frasi)
    fw = D.get("follower")
    if fw and fw["n"] < fw["traguardo"] and not per_attivita:  # il traguardo di tutti, come sul sito
        did = did.strip() + f"\n\n❄️ Siamo a {fw['n']} follower: a {fw['traguardo']} nevica su tutta la mappa d'Italia. Mancano {fw['traguardo'] - fw['n']}: seguici e dillo agli amici!"
    bg = carica(ROOT / "docs/data/animali.json", {}).get("boost")
    if bg and not per_attivita:  # il Boost del giorno: oggi conviene commentare e taggare
        did = did.strip() + f"\n\n⚡ Boost di oggi: {bg['frase']}. Missioni del giorno su zampeditalia.it: commenta + porta un amico = +10 extra"
    mostrati = sorted({sc.get("utente") for _, sc in frasi if sc.get("utente")} | set(st.pop("tag_extra", [])))
    if mostrati:
        did = did.strip() + "\n\n🐾 In questo reel: " + " ".join("@" + u for u in mostrati)
    # gli hashtag delle città nel reel: chi cerca la propria città lo trova
    citta = []
    for _, sc in frasi:
        for c in [sc.get("comune")] + [r.get("valore") for r in sc.get("righe", [])] + [x.get("nome") for x in sc.get("citta", [])] + \
                 [sc.get(k, {}).get("titolo") for k in ("sinistra", "destra") if isinstance(sc.get(k), dict)]:
            if c and isinstance(c, str) and not c.startswith(("Fondatore", "Arbitro")) and c not in ("Cani", "Gatti") and not re.search(r"\d", c):
                h = re.sub(r"[^a-z]", "", unicodedata.normalize("NFD", c.lower()).encode("ascii", "ignore").decode())
                if 2 < len(h) < 25 and h not in citta: citta.append(h)
    tag_citta = " ".join("#" + h for h in citta[:5])
    did = did.strip() + "\n\nVoce generata con IA.\n\n" + ("#veterinario #toelettatura #petshop #pensioneperanimali #animalidomestici " if per_attivita else st.pop("hashtag", "#cani #gatti #italia #canicontrogatti #animalidomestici ")) + tag_citta
    intro = st.pop("intro", None)
    copione = {"id": ORA.strftime("%Y-%m-%d-%H%M") + "-" + formato, "formato": formato, "testata": {"titolo": titolo},
               "conteggio": {"cani": D["cani"], "gatti": D["gatti"]}, "frasi": [{"testo": t, "scena": sc} for t, sc in frasi],
               "banner": f"📍 Scrivi città, nome, razza · ➕ Seguici {PS} 👇", "didascalia": did,
               "tag": [u for u in mostrati if u.lower() not in ESCLUSI or u == MASCOTTE], "copertina": st.pop("copertina", None), **({"intro": intro} if intro else {})}
    Path(uscita).write_text(json.dumps(copione, ensure_ascii=False, indent=1))
    STORICO.write_text(json.dumps(st, ensure_ascii=False, indent=1))
    print(f"copione {copione['id']}: " + " / ".join(t for t, _ in frasi))

if __name__ == "__main__":
    main()
