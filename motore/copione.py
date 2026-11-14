"""Scrive il copione di un reel automatico partendo dai dati veri della mappa.

Uso: python3 motore/copione.py <formato|auto> <uscita.json>
Formati: duello (9:00), vetrina (13:00), fondatore (18:00), puntata (21:00). "auto" sceglie in base all'ora italiana.
Regola: nessun numero inventato. I numeri e i nomi vengono dai dati; Claude (se c'è ANTHROPIC_API_KEY) può solo
riformulare le frasi, e la riformulazione si scarta se cambia numeri o nomi o allunga troppo il testo.
"""
import math, unicodedata, json, os, random, re, sys, urllib.request
from datetime import datetime, date, timedelta
from collections import Counter
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
STORICO = ROOT / "motore/reel_fatti.json"
LANCIO = date(2026, 10, 26)
ORA = datetime.now(ZoneInfo("Europe/Rome"))
BOOST = ORA.date().isoformat() <= "2026-11-08"  # Settimana del follow: SEGUO vale +30 (come in commenti.py)
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
        ("Scrivi città e nome del tuo animale.", {"tipo": "commento", "testo": f"{a}, {cane['nome']}, {cane['parola']}"}),
    ]
    v = scena_vera(D, rng, rng.choice(["cane", "gatto"]))
    if v:
        frasi.append((f"Come {v[0]['n']}, che ha acceso la sua luce a {v[0]['c']}.", v[1]))
    else:
        frasi.append(("Si accende la sua cuccia, col suo nome.", {"tipo": "cuccia", "nome": cane["nome"], "razza": cane["razza"], "seme": cane["seme"]}))
    frasi.append((f"Allora: {a} o {b}? Scrivi la tua città!", {"tipo": "chiusura", "testo": "👇 Scrivi la tua città qui sotto"}))
    did = f"{a} o {b}: quale città si accende per prima? 🐶🐱\n\nScrivi qui sotto città e nome (per esempio «{a}, {cane['nome']}, {cane['parola']}»): la luce del tuo animale si accende sulla mappa col tuo @. Il primo di ogni comune diventa il Fondatore 👑"
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
        ("C'è anche la tua? Scrivi città e nome.", {"tipo": "commento", "testo": f"{citta}, {cane['nome']}, {cane['parola']}"}),
    ]
    v = scena_vera(D, rng, "gatto" if rng.random() < 0.4 else "cane")
    frasi.append((f"Come {v[0]['n']}, a {v[0]['c']}." if v else "E il tuo animale si accende così, col suo nome.",
                  v[1] if v else {"tipo": "cuccia", "nome": cane["nome"], "razza": cane["razza"], "seme": cane["seme"]}))
    frasi.append(("Qual è la tua razza? Scrivila qui sotto!", {"tipo": "chiusura", "testo": "👇 Scrivi la tua razza qui sotto"}))
    did = f"Ogni razza ha la sua cuccia 🐾 Sulla mappa di Zampe d'Italia ci sono già {nc} razze di cani e {ng} di gatti disegnate, ognuna diversa.\n\nScrivi qui sotto città e nome: il tuo animale si accende sulla mappa col tuo @."
    st["copertina"] = {"sopra": f"{nc + ng} RAZZE", "grande": "C'è anche<br>la tua?", "sotto": "Ogni razza ha la sua cuccia", "tema": "vetrina"}
    return "CANI vs GATTI", frasi, did

def fondatore(D, rng, st):
    libere = [c for c in CITTA if sum(D["per_citta"].get(c, {}).values()) == 0 and c not in st.get("fondatori", [])[-8:]]
    if not libere: return duello(D, rng, st)
    c = rng.choice(libere); st.setdefault("fondatori", []).append(c)
    cane, gatto = esempio(rng, D)
    frasi = [
        (f"{c} non ha ancora un Fondatore.", {"tipo": "mappa", "luci": luci(D), "citta": [{"nome": c, "testo": c + "?", "colore": "d", "t": 0.3}], "zoom": {"comune": c, "s": 2.2}}),
        (f"Il primo che scrive {c} e il nome", {"tipo": "commento", "testo": f"{c}, {cane['nome']}, {cane['parola']}"}),
        ("accende la prima cuccia della città e diventa Fondatore. Per sempre.", {"tipo": "cuccia", "nome": cane["nome"], "razza": cane["razza"], "seme": cane["seme"], "comune": "Fondatore di " + c}),
        (f"Chi sarà il Fondatore di {c}? Scrivilo qui sotto!", {"tipo": "chiusura", "testo": f"👑 Diventa il Fondatore di {c}"}),
    ]
    did = f"{c} non ha ancora un Fondatore 👑\n\nIl primo animale di {c} che arriva sulla mappa lo diventa per sempre. Scrivi qui sotto «{c}, nome, cane o gatto» (per esempio «{c}, {cane['nome']}, {cane['parola']}»): la sua luce si accende."
    st["copertina"] = {"sopra": "CERCASI FONDATORE", "grande": c, "sotto": "Il primo diventa Fondatore 👑", "tema": "fondatore", "citta": c}
    return "CANI vs GATTI", frasi, did

def puntata(D, rng, st):
    n = (ORA.date() - LANCIO).days + 1
    tot = len([a for a in D["tutti"] if a.get("k") != "stella"])
    top = sorted(D["per_citta"].items(), key=lambda kv: -sum(kv[1].values()))[:5]
    cane, gatto = esempio(rng, D)
    # si apre sulla mappa con le luci vere già accese e la città in testa evidenziata
    pin = [{"nome": top[0][0], "testo": f"{top[0][0]} · {luci_n(sum(top[0][1].values()))}", "colore": "d"}] if top else []
    frasi = [(f"Il tuo animale è già su questa mappa? {tot} {'luce accesa' if tot == 1 else 'luci accese'} in Italia.", {"tipo": "mappa", "luci": luci(D), "citta": pin}),
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
    frasi += [("Ogni commento è una luce: scrivi città e nome.", {"tipo": "commento", "testo": f"{rng.choice(CITTA)}, {cane['nome']}, {cane['parola']}"}),
              ("Scrivi qui sotto e accendi la tua luce!", {"tipo": "chiusura", "testo": "👇 Accendi la tua luce qui sotto"})]
    did = f"Giorno {n} della mappa di Zampe d'Italia 🌙 {tot} {'luce accesa' if tot == 1 else 'luci accese'}: cani {D['cani']}, gatti {D['gatti']}.\n\nScrivi qui sotto città e nome del tuo animale e accendi la tua luce col tuo @. Il primo di ogni comune diventa il Fondatore 👑"
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
        frasi.append((f"Vuoi la tua luce come {x[0]['n']}? Città e nome.", x[1]))
    manca = SOGLIA_ALTRI - D["altri"]
    frasi.append((f"E arrivano gli altri: ancora {manca} {'luce' if manca == 1 else 'luci'} e conigli, furetti e tartarughe entrano nella sfida!",
                  {"tipo": "numero", "grande": str(D["altri"]), "sotto": f"altri animali accesi: a {SOGLIA_ALTRI} entrano nella sfida 🐰🐢🦎"}))
    frasi.append(("Cani o gatti? Vota qui sotto!", {"tipo": "chiusura", "testo": "👇 Scrivi 🐶 o 🐱"}))
    did = f"Cani {cani}, gatti {gatti} 🐶🐱 Commenta con un'emoji e vediamo chi vince!\n\n🐰 Hai un coniglio, un furetto, una tartaruga? Ancora {manca} {'luce' if manca == 1 else 'luci'} e gli altri animali entrano nella sfida: scrivi città, nome e specie.\n\nVuoi accendere la luce del tuo animale sulla mappa d'Italia? Scrivi città e nome (per esempio «Treviso, Luna, golden»)."
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
           "!\n\nVuoi esserci nel prossimo reel? Scrivi qui sotto città, nome e animale: la luce si accende col tuo @.")
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
        ("Trova la tua città: è accesa o ancora al buio?", {"tipo": "mappa", "luci": luci(D)}),
        (f"{Art}{r} {stato}", {"tipo": "mappa", "luci": luci(D), "citta": [{"nome": cap, "testo": f"{r}: {n}", "colore": "d", "t": 0.3}], "zoom": {"comune": cap, "s": 2.0}}),
        ("Ogni commento accende una luce: città e nome.", {"tipo": "commento", "testo": f"{cap}, {cane['nome']}, {cane['parola']}"}),
        (f"Accendiamo {art}{r}? Scrivilo qui sotto!", {"tipo": "chiusura", "testo": f"🌙 Accendi {art}{r}"}),
    ]
    did = (f"Questa è l'Italia di notte 🌙 e {art}{r} {stato}\n\nOgni commento accende una luce: scrivi qui sotto città e nome "
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
           f"Hai un animale speciale? Scrivi qui sotto città, nome e animale (per esempio «{citta}, {nome}, coniglio»): si accende la sua luce sulla mappa col tuo @. "
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
    # niente Thor nei reel (Alberto, 30/10): la pagina va avanti senza di lui
    frasi += [
        (f"Scrivi città e nome: {a}, {cane['nome']}, {cane['parola']}.", {"tipo": "commento", "testo": f"{a}, {cane['nome']}, {cane['parola']}"}),
        (f"E tagga un amico della tua città: si chiude {quando}.", {"tipo": "numero", "grande": f"+{DB.PREMIO}", "sotto": f"punti a chi accende la provincia che vince il derby 🏆"}),
        (f"{a} o {b}? Scrivi la tua città!", {"tipo": "chiusura", "testo": f"⚔️ {a} o {b}? Scrivilo qui sotto"}),
    ]
    # nel reel i primi che hanno acceso ciascuna città: ricevono la notifica e chiamano gli amici
    per = DB.conta(D["tutti"], {"inizio": datetime.fromisoformat(d["inizio"]), "fine": fine, "a": (a, d["pa"]), "b": (b, d["pb"])})
    st["tag_extra"] = [x["u"] for p in (d["pa"], d["pb"]) for x in per[p][:3]]
    did = (f"⚔️ Il Derby della settimana: {a} contro {b}! " + (f"Ora siamo {na} a {nb}." if na + nb else "Si parte da 0 a 0.") + "\n\n"
           f"Vale tutta la provincia: scrivi qui sotto città e nome del tuo animale (per esempio «{a}, {cane['nome']}, {cane['parola']}» o «{b}, {gatto['nome']}, {gatto['parola']}») "
           f"e la sua luce si accende per la tua città. Si chiude {quando}: chi ha acceso la provincia che vince prende +{DB.PREMIO} punti 🏆\n\n"
           f"👥 Tagga un amico di {a} o di {b}: ogni amico che commenta è una luce in più.")
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
    frasi = [(f"La tua città è in gara? {tot} animali accesi in {nc} città.", {"tipo": "numero", "grande": str(tot), "sotto": f"animali accesi in {g} giorni · {nc} città 🐾"})]
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
        # la gara vera apre il reel, come «Ha fondato Firenze per 31 secondi» (198.000 views in una pagina simile): niente statistica in testa
        frasi[0] = (f"{p['n']} ha fondato {c} per {quanto}!", {**scena_di(p, f"Fondatore di {c} 👑")})
        frasi.insert(1, (f"Secondo posto per {q['n']}, per un soffio.", {**scena_di(q, f"secondo a {c}")}))
        tag += [p["u"], q["u"]]
        n, unita = quanto.split(" ", 1)
        st["copertina"] = {"sopra": f"HA FONDATO {c.upper()}", "grande": f"per {n}<br>{unita}", "sotto": f"{p['n']} è il Fondatore 👑", "domanda": "Nella tua città chi arriva primo? 👇", "tema": "fondatore", "citta": c}
    top = sorted(an, key=lambda a: -a.get("pt", 0))[:3]
    if top and top[0].get("pt"):
        cast = sum(1 for a in an if a.get("pt", 0) >= LIVELLI[-1][0])
        frasi.append(((f"Solo {cast} animali hanno il castello. " if 1 < cast < 30 else "") + f"In testa c'è {top[0]['n']}, di {top[0]['c']}, con {top[0]['pt']} punti.",
                      {"tipo": "classifica", "titolo": "In testa 🏆", "righe": [{"nome": f"{a['n']} · @{a['u']}", "valore": f"{a.get('pt', 0)} pt"} for a in top], "utente": top[0]["u"]}))
        tag += [a["u"] for a in top]
    frasi += [("E la tua città? Scrivi città e nome.", {"tipo": "commento", "testo": f"{rng.choice(CITTA)}, {cane['nome']}, {cane['parola']}"}),
              ("Arriva primo nel tuo comune: scrivilo qui sotto!", {"tipo": "chiusura", "testo": "👑 Arriva primo nella tua città"})]
    st["tag_extra"] = list(dict.fromkeys(tag))
    did = f"In {g} giorni sulla mappa di Zampe d'Italia si sono accesi {tot} animali, in {nc} città 🐾\n\n"
    if gare:
        did += f"⏱️ A {c} @{p['u']} ({p['n']}) ha commentato {quanto} prima di @{q['u']} ({q['n']}): Fondatore per sempre 👑\n"
    if top and top[0].get("pt"):
        did += "🏰 Più punti fai, più la cuccia cresce: 🌸 giardino a 30 punti, 🏡 villa a 50, 🏰 castello a 70\n"
        did += "🏆 In testa: " + ", ".join(f"@{a['u']} ({a['c']}) {a.get('pt', 0)} punti" for a in top) + "\n"
    did += (f"\nScrivi qui sotto città e nome del tuo animale (per esempio «{rng.choice(CITTA)}, {gatto['nome']}, {gatto['parola']}»): si accende sulla mappa col tuo @. "
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
              ("Non sei ancora sulla mappa? Scrivi città e nome.", {"tipo": "commento", "testo": f"{rng.choice(CITTA)}, {cane['nome']}, {cane['parola']}"}),
              ("Il negozio è nel link in bio!", {"tipo": "chiusura", "testo": "🛍️ Negozio nel link in bio"})]
    did = ("👑 Da oggi sulla mappa di Zampe d'Italia puoi regalare un accessorio al tuo animale, per sempre: 🦴 osso d'oro 1 €, 🎀 fiocco 1,49 €, 📿 collare d'oro 1,99 €, 👑 corona 2,99 €, 🎆 fuochi d'artificio 3,99 €.\n\n"
           "Ogni regalo finisce nella nostra storia 🎉 e ogni domenica alle 21 il più accessoriato diventa 🏆 Il più bello d'Italia.\n\n"
           "🛍️ Negozio su zampeditalia.it (link in bio) → «Il mio» → cerca il tuo @.\n\n"
           f"Non sei ancora sulla mappa? Scrivi qui sotto città e nome (per esempio «{rng.choice(CITTA)}, {gatto['nome']}, {gatto['parola']}»).")
    st["copertina"] = {"sopra": "🛍️ IL NEGOZIO", "grande": "Da 1 €", "sotto": "Il più bello d'Italia? 🏆", "tema": "attivita"}
    return "IL NEGOZIO", frasi, did

def presidente(D, rng, st):
    """Il Presidente di regione (commenti.py): chi ha più accessori nella sua regione. Il reel mostra chi c'è e quante regioni sono libere."""
    pres = sorted([a for a in D["animali"] if a.get("pres") and a["u"].lower() not in ESCLUSI], key=lambda a: (-len(a.get("acc", [])), -a.get("pt", 0)))
    if not pres: return negozio(D, rng, st)
    NOMI = {"osso": "l'osso d'oro", "fiocco": "il fiocco", "collare": "il collare d'oro", "corona": "la corona", "fuochi": "i fuochi d'artificio", "cappello": "il cappello di Babbo Natale", "sciarpa": "la sciarpa di Natale", "albero": "l'alberello di Natale"}  # come motore/negozio.py
    p, libere = pres[0], 20 - len(pres)
    cosa = " e ".join(NOMI[k] for k in p.get("acc", []) if k in NOMI) or "un accessorio"
    razza = p.get("razza_testo") or ("gatto" if p.get("t") == "gatto" else "cane")
    cane, gatto = esempio(rng, D)
    # scarsità in apertura: le regioni ancora libere, con 1 euro il titolo è tuo (gli acquisti fanno i Presidenti)
    frasi = [(f"{libere} regioni senza Presidente. La tua è libera?", {"tipo": "numero", "grande": str(libere), "sotto": "regioni senza Presidente: con 1 € il titolo è tuo 👑"}),
             (f"È {p['n']}, {razza} di {p['c']}: con {cosa} è {p['pres']}.", scena_di(p, f"{p['pres']} 🇮🇹"))]
    if len(pres) > 1:
        frasi.append(("Ecco gli altri Presidenti.", {"tipo": "classifica", "titolo": "I Presidenti 🇮🇹", "righe": [{"nome": f"{a['n']} · @{a['u']}", "valore": a["r"]} for a in pres[:5]], "utente": p["u"]}))
    frasi += [(f"{'Altre' if len(pres) == 1 else 'Ancora'} {libere} regioni non hanno un Presidente.", {"tipo": "numero", "grande": str(libere), "sotto": "regioni senza Presidente 👀"}),
              ("Chi ha più accessori nella sua regione diventa Presidente. Si parte da 1 euro.", {"tipo": "numero", "grande": "1 €", "sotto": "🦴 1 € · 🎀 1,49 · 📿 1,99 · 👑 2,99 · 🎆 3,99"}),
              ("E se qualcuno ti supera, la fascia passa subito a lui!", {"tipo": "numero", "grande": "⚡", "sotto": "chi ti supera ti toglie la fascia"}),
              ("Non sei ancora sulla mappa? Scrivi città e nome.", {"tipo": "commento", "testo": f"{rng.choice(CITTA)}, {cane['nome']}, {cane['parola']}"}),
              ("Il negozio è nel link in bio!", {"tipo": "chiusura", "testo": "🇮🇹 Diventa Presidente: link in bio"})]
    st["tag_extra"] = [a["u"] for a in pres[:5]]
    did = (f"🇮🇹 {'Abbiamo il primo Presidente di regione' if len(pres) == 1 else 'I Presidenti di regione di Zampe d’Italia'}: {p['n']} di @{p['u']}, {razza} di {p['c']}, con {cosa} è {p['pres']}!\n\n"
           + ("".join(f"🇮🇹 {a['n']} di @{a['u']}: {a['pres']}\n" for a in pres[1:5]) + "\n" if len(pres) > 1 else "")
           + f"{'Altre' if len(pres) == 1 else 'Ancora'} {libere} regioni non hanno un Presidente 👀 Chi ha più accessori nella sua regione prende la fascia tricolore sulla mappa e nel paese 3D, "
           "e se qualcuno lo supera la fascia passa subito a lui ⚡\n\n"
           "🛍️ Accessori da 1 €: zampeditalia.it (link in bio) → «Il mio» → cerca il tuo @.\n\n"
           f"Non sei ancora sulla mappa? Scrivi qui sotto città e nome (per esempio «{rng.choice(CITTA)}, {gatto['nome']}, {gatto['parola']}»).")
    st["copertina"] = {"sopra": "🇮🇹 PRESIDENTE DI REGIONE", "grande": f"{libere}<br>libere", "sotto": "Con 1 € il titolo è del tuo animale", "domanda": "La tua regione è libera? 👇", "tema": "attivita"}
    return "IL PRESIDENTE", frasi, did

def nomi(D, rng, st):
    """I nomi più diffusi sulla mappa: una storia che hanno solo i nostri dati (gli animali veri hanno un nome).
    Chi guarda controlla se c'è il nome del suo e lo scrive nei commenti."""
    conta = lambda t: Counter(a["n"].strip().title() for a in D["animali"] if a.get("k") == "animale" and a.get("t", "cane") == t).most_common(5)
    cani, gatti = conta("cane"), conta("gatto")
    if len(cani) < 3 or len(gatti) < 1: return sfida(D, rng, st)
    (n1, c1), (n2, _), (n3, _) = cani[:3]
    cane, gatto = esempio(rng, D)
    frasi = [
        (f"Il tuo cane si chiama {n1}? Non è l'unico.", {"tipo": "numero", "grande": n1, "sotto": f"il nome più diffuso: {c1} cani in Italia 🐶"}),
        (f"Dopo {n1} vengono {n2} e {n3}.", {"tipo": "classifica", "titolo": "I nomi dei cani 🐶", "righe": [{"nome": n, "valore": f"{c} cani"} for n, c in cani]}),
        (f"Tra i gatti vince {gatti[0][0]}.", {"tipo": "classifica", "titolo": "I nomi dei gatti 🐱", "righe": [{"nome": n, "valore": f"{c} gatti"} for n, c in gatti]}),
        ("Il tuo come si chiama? Scrivilo qui sotto.", {"tipo": "commento", "testo": f"{rng.choice(CITTA)}, {cane['nome']}, {cane['parola']}"}),
        ("Il nome del tuo entra in classifica!", {"tipo": "chiusura", "testo": "👇 Scrivi città e nome"}),
    ]
    did = (f"Il nome più diffuso per un cane sulla mappa d'Italia è {n1} ({c1}), poi {n2} e {n3}. Tra i gatti vince {gatti[0][0]} 🐶🐱\n\n"
           "Il tuo come si chiama? Scrivi qui sotto città e nome: si accende sulla mappa col tuo @ e il suo nome entra in classifica.")
    st["copertina"] = {"sopra": "IL NOME PIÙ DIFFUSO", "grande": n1, "sotto": f"{c1} cani in Italia si chiamano così", "domanda": "Il tuo come si chiama? 👇", "tema": "voto"}
    return "I NOMI D'ITALIA", frasi, did

CAPOLUOGHI = [("Veneto", "Venezia"), ("Piemonte", "Torino"), ("Lazio", "Roma"), ("Campania", "Napoli"), ("Puglia", "Bari"), ("Sicilia", "Palermo"), ("Sardegna", "Cagliari"), ("Lombardia", "Milano"), ("Toscana", "Firenze")]

def razze(D, rng, st):
    """La razza preferita di ogni regione (meticci a parte) e il meticcio re d'Italia: dati che hanno solo gli animali veri.
    Divide quanto basta («da noi vince un'altra razza!») per far commentare."""
    nome = {r[0]: r[1].lower() for r in D["razze"]["cani"]}
    cani = [a for a in D["animali"] if a.get("k") == "animale" and a.get("t", "cane") == "cane"]
    if len(cani) < 50: return sfida(D, rng, st)
    per = {}
    for a in cani:
        if a.get("razza") and a["razza"] != "meticcio": per.setdefault(a.get("r"), Counter())[a["razza"]] += 1
    cand = [(r, c, per[r].most_common(1)[0][0]) for r, c in CAPOLUOGHI if per.get(r) and per[r].most_common(1)[0][1] >= 3]
    if len(cand) < 3: return sfida(D, rng, st)
    scelte = [cand[0], cand[len(cand) // 2], cand[-1]]  # nord, centro, sud o isole
    pct = round(100 * sum(1 for a in cani if a.get("razza") == "meticcio") / len(cani))
    cane, _ = esempio(rng, D)
    frasi = [
        ("Ogni regione ha la sua razza. La tua?", {"tipo": "mappa", "luci": luci(D), "citta": [{"nome": c, "testo": nome.get(k, k).capitalize(), "colore": "d", "t": 0.3 + 0.35 * i} for i, (_, c, k) in enumerate(scelte)]}),
        (f"In {scelte[0][0]} vince il {nome.get(scelte[0][2], scelte[0][2])}, in {scelte[-1][0]} il {nome.get(scelte[-1][2], scelte[-1][2])}.", {"tipo": "numero", "grande": nome.get(scelte[0][2], scelte[0][2]).capitalize(), "sotto": f"la razza preferita in {scelte[0][0]} 🐶"}),
        (f"Ma il re è il meticcio: {pct} su cento.", {"tipo": "numero", "grande": f"{pct}%", "sotto": "dei cani sulla mappa è meticcio ❤️"}),
        ("E da te? Scrivi la razza del tuo.", {"tipo": "commento", "testo": f"{scelte[1][1]}, {cane['nome']}, {cane['parola']}"}),
        ("Scrivilo qui sotto!", {"tipo": "chiusura", "testo": "👇 Scrivi città e nome"}),
    ]
    did = (f"La razza preferita di ogni regione sulla mappa di Zampe d'Italia: " + ", ".join(f"{r} {nome.get(k, k)}" for r, _, k in scelte) +
           f". E il re d'Italia è il meticcio: {pct} cani su cento ❤️\n\nNella tua regione vince un'altra razza? Scrivi qui sotto città e nome del tuo: si accende sulla mappa col tuo @.")
    st["copertina"] = {"sopra": "LA RAZZA DI OGNI REGIONE", "grande": f"{pct}%", "sotto": "dei cani d'Italia è meticcio", "domanda": "E nella tua regione? 👇", "tema": "vetrina"}
    return "LE RAZZE D'ITALIA", frasi, did

def missione(D, rng, st):
    """La missione di tutti: il paese virtuale con più animali d'Italia, poi Italia contro Mondo.
    Tono da comunità («una famiglia», «insieme»): chi commenta non gioca con una pagina, costruisce qualcosa con gli altri."""
    tot = len(luci(D)); nc = len({a["c"] for a in D["tutti"] if a.get("k") != "stella"})
    cane, _ = esempio(rng, D)
    c = rng.choice(CITTA)
    frasi = [
        ("Stiamo costruendo il paese virtuale con più animali d'Italia.", {"tipo": "mappa", "luci": luci(D)}),
        (f"Siamo già {tot}, in {nc} città.", {"tipo": "numero", "grande": str(tot), "sotto": f"animali veri in {nc} città: una sola famiglia 🐾"}),
        ("Il traguardo: diecimila.", {"tipo": "numero", "grande": "10.000", "sotto": "animali d'Italia, il paese più grande, fatto da voi"}),
        ("Poi sfidiamo il mondo: Italia contro Mondo!", {"tipo": "duello", "sinistra": {"titolo": "Italia", "valore": f"{tot} animali"}, "destra": {"titolo": "Mondo", "valore": "presto 🌍"}}),
        ("Manca il tuo: scrivi città e nome.", {"tipo": "commento", "testo": f"{c}, {cane['nome']}, {cane['parola']}"}),
        ("Entra nella famiglia!", {"tipo": "chiusura", "testo": "🐾 Entra nella famiglia: scrivi la tua città"}),
    ]
    did = (f"🇮🇹 Stiamo costruendo insieme il paese virtuale con più animali d'Italia: siamo già {tot}, in {nc} città.\n\n"
           "Non è il gioco di una pagina: è la casa di tutti i nostri animali, e ogni commento è un mattone. "
           "Il traguardo è 10.000. Quando ci arriviamo, apriamo la sfida più grande: 🇮🇹 Italia contro Mondo 🌍\n\n"
           f"👇 Manca il tuo: scrivi qui sotto città e nome (per esempio «{c}, {cane['nome']}, {cane['parola']}») e tagga chi deve esserci con te.")
    st["copertina"] = {"sopra": "🇮🇹 LA NOSTRA MISSIONE", "grande": f"{tot}<br><i>/</i><br>10.000", "sotto": "animali d'Italia, una sola famiglia", "domanda": "Manca il tuo? 👇", "tema": "duello"}
    return "LA MISSIONE", frasi, did

def star(D, rng, st):
    """La star di oggi: la foto vera di un animale, mandata in privato da chi lo ha e col suo SÌ (messaggi.py → stato «ugc»).
    Niente disegni: è il reel meno «IA» che abbiamo. Senza foto nuove, esce la gara."""
    fatte = set(st.get("star_fatte", []))
    ugc = [x for x in carica(ROOT / "motore/stato.json", {}).get("ugc", []) if x["f"].endswith(".jpg") and x["f"] not in fatte and (ROOT / "docs/media/ugc" / x["f"]).exists()
           and x["u"].lower() not in ESCLUSI]
    if not ugc: return fondatore(D, rng, st)  # 2/11: il fondatore rende più della gara (2.700 views medie contro 2.000)
    x = ugc[0]; st["star_fatte"] = (st.get("star_fatte", []) + [x["f"]])[-500:]
    a = next((y for y in D["animali"] if y["u"].lower() == x["u"].lower() and y.get("k") == "animale"), None)
    nome, citta = (a["n"], a["c"]) if a else ("la star", None)
    resto = len(ugc) - 1
    frasi = [
        (f"La star di oggi è {nome}{', da ' + citta if citta else ''}!", {"tipo": "foto", "file": x["f"], "nome": nome, "utente": x["u"], "comune": citta}),
        ("Una foto vera, mandata da chi lo ama.", {"tipo": "foto", "file": x["f"], "nome": nome, "utente": x["u"], "comune": citta}),
        ("Vuoi che domani tocchi al tuo?", {"tipo": "numero", "grande": "📸", "sotto": "mandaci in privato la foto del tuo animale"}),
        ("Mandaci la sua foto in privato!", {"tipo": "chiusura", "testo": "📸 Mandaci la foto del tuo in DM"}),
    ]
    did = (f"⭐ La star di oggi è {nome}" + (f" di {citta}" if citta else "") + f", di @{x['u']}! 😍\n\n"
           "📸 Vuoi che domani tocchi al tuo? Mandaci in privato una foto del tuo animale: ogni giorno uno diventa la star del reel, col tuo @."
           + (f" (Ne abbiamo già {resto} in coda!)" if resto > 2 else "") + "\n\n👇 E scrivi qui sotto città e nome: si accende anche sulla mappa d'Italia.")
    st["tag_extra"] = [x["u"]]
    st["copertina"] = {"sopra": "⭐ LA STAR DI OGGI", "grande": nome, "sotto": citta or "foto vera, mandata in DM", "domanda": "Domani tocca al tuo? 📸", "tema": "fondatore"}
    return "LA STAR", frasi, did

def neopresidente(D, rng, st):
    """Festa per il Presidente di regione appena eletto (l'ultimo in st["presidente_festa"] o, se manca, il più recente):
    il suo animale in primo piano col nome del padrone, l'accessorio che gli ha dato il titolo e le regioni ancora libere.
    Chi è festeggiato lo condivide; chi guarda vede che con 1 euro il titolo può essere suo."""
    J = carica(ROOT / "docs/data/animali.json", {})
    pres = J.get("presidenti", {})
    if not pres: return presidente(D, rng, st)
    r = st.pop("presidente_festa", None) or list(pres)[-1]
    a = next((x for x in D["tutti"] if x.get("id") == pres.get(r)), None)
    if not a: return presidente(D, rng, st)
    nomi_acc = {"osso": "l'osso d'oro", "fiocco": "il fiocco", "collare": "il collare d'oro", "corona": "la corona", "fuochi": "i fuochi d'artificio", "cappello": "il cappello di Babbo Natale", "sciarpa": "la sciarpa di Natale", "albero": "l'alberello di Natale"}
    acc = nomi_acc.get((a.get("acc") or ["osso"])[-1], "un accessorio")
    libere = 20 - len(pres)
    tipo = "gatto" if a.get("t") == "gatto" else "cuccia"
    frasi = [
        (f"{a['n']} è {a['pres']}!", {"tipo": tipo, "nome": a["n"], "razza": a.get("razza_testo") or a.get("razza") or "meticcio",
                                     "seme": abs(hash(a["id"])) % 997 + 1, "utente": a["u"], "comune": a["pres"] + " 🇮🇹"}),
        (f"Le è bastato {acc}, da {a['c']}.", {"tipo": "numero", "grande": "👑", "sotto": f"{acc} e la fascia tricolore sulla mappa"}),
        (f"Ancora {libere} regioni senza Presidente. La tua?", {"tipo": "numero", "grande": str(libere), "sotto": "regioni senza Presidente: con 1 € il titolo è tuo"}),
        ("Il negozio è nel link in bio!", {"tipo": "chiusura", "testo": "👑 Diventa Presidente della tua regione"}),
    ]
    did = (f"🇮🇹 {a['n']} di @{a['u']} è la nuova {a['pres']}! Le è bastato {acc} 👑\n\n"
           f"Ancora {libere} regioni non hanno un Presidente: chi ha più accessori nella sua regione prende la fascia tricolore sulla mappa, e se qualcuno lo supera il titolo passa a lui ⚡\n\n"
           "🛍️ Accessori da 1 €: zampeditalia.it (link in bio) → «Il mio» → cerca il tuo @.\n"
           "👇 Non sei ancora sulla mappa? Scrivi qui sotto città e nome del tuo animale.")
    st["copertina"] = {"sopra": "🇮🇹 NUOVA PRESIDENTE", "grande": a["n"], "sotto": a["pres"] + " 👑", "domanda": "E nella tua regione? 👇", "tema": "attivita"}
    st["tag_extra"] = [a["u"]]
    return "PRESIDENTE", frasi, did

def sfida(D, rng, st):
    """Rifà la struttura del lancio (26.910 views, 4.408 commenti): una rivalità che capiscono tutti, cosa scrivere
    mostrato come un commento, il premio subito (la tua cuccia col tuo nome), il posto da Fondatore ancora libero,
    e la stessa domanda alla fine così il reel si riguarda. Cambia la squadra che insegue, per non ripetersi."""
    cani, gatti = D["cani"], D["gatti"]
    dietro = "gatti" if gatti < cani else "cani"
    cane, gatto = esempio(rng, D)
    ex = gatto if dietro == "gatti" else cane
    top = sorted(D["per_citta"].items(), key=lambda x: -sum(x[1].values()))[:6]
    a, b = [c for c, _ in rng.sample(top, 2)] if len(top) >= 2 else ("Milano", "Napoli")
    liberi = max(0, 7896 - len(D["per_citta"]))  # comuni italiani senza ancora un animale
    frasi = [
        (f"Cani contro Gatti: i {dietro} stanno perdendo.", {"tipo": "duello", "sinistra": {"titolo": "Cani", "valore": str(cani)}, "destra": {"titolo": "Gatti", "valore": str(gatti)}}),
        ("Quale città li salva?", {"tipo": "mappa", "luci": luci(D), "citta": [{"nome": a, "testo": a + "?", "colore": "d", "t": 0.3}, {"nome": b, "testo": b + "?", "colore": "c", "t": 0.7}]}),
        ("Scrivi città e nome.", {"tipo": "commento", "testo": f"{a}, {ex['nome']}, {ex['parola']}"}),
        ("E si accende col suo nome.", {"tipo": "gatto" if dietro == "gatti" else "cuccia", "nome": ex["nome"], "razza": ex["razza"], "seme": ex["seme"]}),
        ("Il primo del tuo comune diventa Fondatore.", {"tipo": "numero", "grande": str(liberi), "sotto": "comuni ancora spenti: il primo diventa Fondatore 👑"}),
        ("Allora: cani o gatti? Scrivi la tua città!", {"tipo": "chiusura", "testo": "👇 Scrivi città e nome"}),
    ]
    did = (f"Cani contro Gatti: {cani} a {gatti}. I {dietro} stanno perdendo: quale città li salva? 🐶🐱\n\n"
           f"Scrivi qui sotto città e nome del tuo animale (per esempio «{a}, {ex['nome']}, {ex['parola']}»): si accende sulla mappa col tuo @.")
    st["copertina"] = {"sopra": "CANI vs GATTI", "grande": f"{cani}<br><i>vs</i><br>{gatti}", "sotto": f"I {dietro} stanno perdendo", "domanda": "La tua città li salva? 👇", "tema": "duello"}
    return "CANI vs GATTI", frasi, did

def fuochi(D, rng, st):
    """Reel che chiede di seguire (Alberto, 3/11: «un reel che spinga i follow»): un traguardo di tutti, vicino e visibile
    (a 2.000 follower i fuochi d'artificio su tutta la mappa), il premio subito per chi segue (SEGUO = punti al suo animale)
    e un amico da taggare. Qui la richiesta di seguire è il contenuto, quindi sta anche nella fascia in basso."""
    fw = D.get("follower") or {}
    n = fw.get("n") or 0
    manca = max(1, 2000 - n)
    tot = len(luci(D))
    frasi = [
        (f"Mancano {manca} follower ai fuochi d'artificio su tutta l'Italia!", {"tipo": "numero", "grande": str(manca), "sotto": "follower ai fuochi d'artificio 🎆"}),
        (f"A 2.000 si accende la festa sopra tutti i {tot} animali della mappa.", {"tipo": "mappa", "luci": luci(D)}),
        (f"Seguici e scrivi SEGUO: {PS_P} al tuo animale.", {"tipo": "commento", "testo": "SEGUO"}),
        ("Tagga un amico: ci arriviamo insieme!", {"tipo": "chiusura", "testo": "➕ Segui e tagga un amico 👇"}),
    ]
    did = (f"🎆 Mancano {manca} follower ai fuochi d'artificio su tutta la mappa d'Italia!\n\n"
           f"Quando arriviamo a 2.000 si accende la festa sopra tutti i {tot} cani e gatti della mappa.\n"
           f"➕ Seguici e scrivi SEGUO qui sotto: {PS} punti al tuo animale.\n👥 Tagga un amico che ha un cane o un gatto: ci arriviamo insieme!")
    st["copertina"] = {"sopra": "MANCANO", "grande": str(manca), "sotto": "follower ai fuochi d'artificio 🎆", "domanda": "Ci aiuti? ➕👇", "tema": "duello"}
    st["banner_reel"] = f"➕ Seguici e scrivi SEGUO: {PS} punti 👇"
    st["senza_bonus"] = True  # la didascalia ha già la sua richiesta: niente altre righe in coda
    return "🎆 VERSO I 2.000", frasi, did

CORONA = datetime(2026, 11, 6, 21, 0, tzinfo=ZoneInfo("Europe/Rome"))  # l'incoronazione del primo Re degli animali d'Italia

def _regnanti(D):
    """Il Re d'Italia e il Re di ogni regione: l'animale con più punti (punti veri del gioco, ESCLUSI fuori)."""
    an = [a for a in D["animali"] if a.get("k") == "animale" and a.get("u", "").lower() not in ESCLUSI and a.get("pt")]
    top = sorted(an, key=lambda a: -a.get("pt", 0))
    regioni = {}
    for a in top:
        if a.get("r") and a["r"] not in regioni: regioni[a["r"]] = a
    return top, regioni

def regno(D, rng, st):
    """Conto alla rovescia per l'incoronazione (Alberto, 4/11: «voglio follower»): un evento con una scadenza, come i reel
    «Stasera alle 21 il primo Presidente» delle pagine simili. Si vince coi punti, e il modo più veloce per farli è seguirci (SEGUO)
    e far commentare gli amici: la richiesta di seguire ha un motivo dentro il gioco."""
    top, regioni = _regnanti(D)
    ore = max(1, int((CORONA - ORA).total_seconds() // 3600))
    quando = "stasera alle 21" if CORONA.date() == ORA.date() else ("domani sera alle 21" if (CORONA.date() - ORA.date()).days == 1 else "venerdì alle 21")
    t3 = top[:3]
    frasi = [
        (f"{quando[0].upper() + quando[1:]} incoroniamo il primo Re degli animali d'Italia. Sarà il tuo?", {"tipo": "numero", "grande": "👑", "sotto": f"{quando}: il Re degli animali d'Italia"}),
        (f"Oggi in testa c'è {t3[0]['n']}, di {t3[0]['c']}." if t3 else "Il trono è ancora libero.",
         {"tipo": "classifica", "titolo": "Corsa al trono 👑", "righe": [{"nome": f"{a['n']} · @{a['u']}", "valore": f"{a.get('pt', 0)} pt"} for a in t3], "utente": t3[0]["u"]} if t3 else {"tipo": "mappa", "luci": luci(D)}),
        (f"E ogni regione avrà il suo Re.", {"tipo": "mappa", "luci": luci(D)}),
        (f"Seguici e scrivi SEGUO: {PS_P} subito.", {"tipo": "commento", "testo": "SEGUO"}),
        ("Tagga gli amici: ogni amico che commenta vale tre punti!", {"tipo": "chiusura", "testo": "👑 Segui, scrivi SEGUO, tagga un amico"}),
    ]
    st["tag_extra"] = [a["u"] for a in t3]
    did = (f"👑 {quando[0].upper() + quando[1:]} incoroniamo il primo Re degli animali d'Italia, e il Re di ogni regione!\n\n"
           + ("Oggi in testa: " + ", ".join(f"{a['n']} di {a['c']} ({a['pt']} punti)" for a in t3) + ".\n\n" if t3 else "")
           + "Come si fanno punti:\n"
           f"➕ Seguici e scrivi SEGUO qui sotto: {PS} punti\n"
           "👥 Tagga gli amici: ogni amico che commenta col suo animale ti vale +3\n"
           "🐾 Non sei ancora sulla mappa? Commenta la tua città e il nome del tuo cane o gatto.\n\n"
           f"Mancano {ore} ore. Il tuo animale ha la stoffa del Re? 👇")
    st["copertina"] = {"sopra": quando.upper(), "grande": "👑 IL RE", "sotto": "degli animali d'Italia", "domanda": "Sarà il tuo? 👇", "tema": "fondatore"}
    st["banner_reel"] = f"👑 Seguici e scrivi SEGUO: {PS} punti per diventare Re"
    st["senza_bonus"] = True
    return "👑 IL RE D'ITALIA", frasi, did

def incoronazione(D, rng, st):
    """La serata: il primo Re degli animali d'Italia (più punti) e i Re delle regioni. Persone vere al centro: chi vince condivide."""
    top, regioni = _regnanti(D)
    if not top: return regno(D, rng, st)
    r0 = top[0]
    altri = sorted(regioni.values(), key=lambda a: -a.get("pt", 0))
    altri = [a for a in altri if a is not r0][:4]
    frasi = [
        ("È ufficiale!", {"tipo": "numero", "grande": "👑", "sotto": "il primo Re degli animali d'Italia"}),
        (f"Il primo Re degli animali d'Italia è {r0['n']}, di {r0['c']}!", {**scena_di(r0, f"Re d'Italia 👑 {r0['c']}")}),
        ("Ed ecco i Re delle regioni.", {"tipo": "classifica", "titolo": "I Re delle regioni 👑", "righe": [{"nome": f"{a['n']} · {a['r']}", "valore": f"@{a['u']}"} for a in altri], "utente": r0["u"]}),
        ("La prossima corona è tra un mese. Seguici per non perderla!", {"tipo": "chiusura", "testo": "➕ Seguici: la prossima corona può essere tua"}),
    ]
    st["tag_extra"] = [r0["u"]] + [a["u"] for a in altri]
    righe = "\n".join(f"👑 {a['r']}: {a['n']} di {a['c']} (@{a['u']})" for a in sorted(regioni.values(), key=lambda a: a["r"]))
    did = (f"👑 È ufficiale: il primo Re degli animali d'Italia è {r0['n']}, di {r0['c']}, con {r0['pt']} punti! Complimenti @{r0['u']} 🎉\n\n"
           f"I Re delle regioni:\n{righe}\n\n"
           "➕ Seguici e scrivi SEGUO: la prossima corona può essere del tuo animale.\n🐾 Non sei sulla mappa? Commenta la tua città e il nome del tuo cane o gatto.")
    st["copertina"] = {"sopra": "È UFFICIALE", "grande": r0["n"].upper(), "sotto": f"Re degli animali d'Italia 👑", "domanda": "Il prossimo sarà il tuo? 👇", "tema": "fondatore", "citta": r0["c"]}
    st["banner_reel"] = "➕ Seguici: la prossima corona può essere tua 👇"
    st["senza_bonus"] = True
    return "👑 È UFFICIALE", frasi, did

def ospiti(D, rng, st):
    """Reel per i follow (Alberto, 4/11: «fai follower senza sponsorizzare»): il premio arriva la sera stessa.
    Chi ci segue e scrive SEGUO entro le 21 vede il suo animale, col suo @, nel reel delle 21 (formato ospiti_sera).
    Qui si fotografa chi ci seguiva già (st «seguono_prima»): la sera si mostrano solo i nuovi."""
    st["seguono_prima"] = sorted(D.get("seguono", ()))
    cane, gatto = esempio(rng, D)
    c = rng.choice(CITTA)
    frasi = [
        ("Stasera alle 21 il tuo animale può finire in questo reel!", {"tipo": "numero", "grande": "21:00", "sotto": "il tuo animale nel reel, col tuo @ 🎬"}),
        ("Mettiamo tutti gli animali di chi ci segue da oggi.", {"tipo": "mappa", "luci": luci(D)}),
        ("Seguici e scrivi SEGUO con città e nome.", {"tipo": "commento", "testo": f"SEGUO {c}, {cane['nome']}, {cane['parola']}"}),
        (f"In più, {PS_P} subito. Ci vediamo alle 21!", {"tipo": "chiusura", "testo": "➕ Segui e scrivi SEGUO 👇"}),
    ]
    did = ("🎬 Stasera alle 21 il tuo animale può finire nel reel, col tuo @!\n\n"
           "Nel reel delle 21 mettiamo gli animali di tutti quelli che ci seguono da oggi.\n"
           f"➕ Seguici e scrivi qui sotto SEGUO con città e nome (per esempio «SEGUO {c}, {cane['nome']}, {cane['parola']}»): {PS} punti subito e il tuo animale si accende sulla mappa.\n"
           "👥 Tagga un amico che ha un cane o un gatto: stasera ci siete tutti e due!")
    st["copertina"] = {"sopra": "STASERA ALLE 21", "grande": "IL TUO<br>ANIMALE", "sotto": "nel nostro reel, col tuo @ 🎬", "domanda": "Ci sarà? ➕👇", "tema": "duello"}
    st["banner_reel"] = "➕ Seguici e scrivi SEGUO: stasera il tuo animale è nel reel 👇"
    st["senza_bonus"] = True
    return "🎬 STASERA ALLE 21", frasi, did

def ospiti_sera(D, rng, st):
    """La promessa del pomeriggio mantenuta: gli animali di chi ci segue da oggi, coi loro @. Chi c'è lo condivide."""
    prima = set(st.get("seguono_prima", []))
    st["seguono_prima"] = sorted(D.get("seguono", ()))  # la prossima volta si mostrano quelli arrivati da adesso
    nuovi_u = [u for u in D.get("seguono", ()) if u not in prima and u.lower() not in ESCLUSI]
    an = {a["u"].lower(): a for a in D["animali"] if a.get("k") == "animale"}
    nuovi = [an[u] for u in nuovi_u if u in an]
    if not prima or not nuovi: return regno(D, rng, st)  # niente foto del pomeriggio o nessun nuovo: si parla del Re
    rng.shuffle(nuovi)
    frasi = [
        (f"Promessa mantenuta: benvenuti ai {len(nuovi)} nuovi amici di oggi!" if len(nuovi) > 1 else "Promessa mantenuta: benvenuto al nuovo amico di oggi!",
         {"tipo": "numero", "grande": f"+{len(nuovi)}", "sotto": "animali nuovi nella famiglia di Zampe 🐾"}),
        (f"Ciao {nuovi[0]['n']}, da {nuovi[0]['c']}!", {**scena_di(nuovi[0])}),
        ("Eccoli tutti.", {"tipo": "classifica", "titolo": "I nuovi amici 🎬", "righe": [{"nome": f"{a['n']} · {a['c']}", "valore": f"@{a['u']}"} for a in nuovi[:5]], "utente": nuovi[0]["u"]}),
        ("Il prossimo è il tuo? Seguici e scrivi SEGUO!", {"tipo": "chiusura", "testo": "➕ Segui e scrivi SEGUO 👇"}),
    ]
    st["tag_extra"] = [a["u"] for a in nuovi[:20]]
    elenco = "\n".join(f"🐾 {a['n']} da {a['c']}" for a in nuovi[:30])
    did = (f"🎬 Promessa mantenuta! Ecco gli animali di chi ci segue da oggi:\n{elenco}\n\n"
           f"➕ Il prossimo è il tuo? Seguici e scrivi SEGUO con città e nome: {PS} punti, e nel prossimo reel dei nuovi amici c'è anche il tuo animale.\n"
           "👑 E venerdì alle 21 incoroniamo il primo Re degli animali d'Italia!")
    st["copertina"] = {"sopra": "PROMESSA MANTENUTA", "grande": f"+{len(nuovi)}", "sotto": "nuovi amici di oggi 🐾", "domanda": "Il prossimo è il tuo? ➕👇", "tema": "fondatore"}
    st["banner_reel"] = "➕ Seguici e scrivi SEGUO: il prossimo è il tuo animale 👇"
    st["senza_bonus"] = True
    return "🎬 I NUOVI AMICI", frasi, did

def amici(D, rng, st):
    """«Porta due amici e scali la classifica» (Alberto, 6/11). Regola vera in commenti.py: tagghi un amico, lui commenta (+3 a te),
    e quando ci segue e scrive SEGUO prendi altri +15 (premia_amico_segue). Due amici che seguono = +36, più di un SEGUO."""
    top, _ = _regnanti(D)
    t3 = top[:3]
    frasi = [
        ("Vuoi scalare la classifica? Porta due amici!", {"tipo": "numero", "grande": "+36", "sotto": "punti con 2 amici che ci seguono 👥"}),
        ("Taggali qui sotto.", {"tipo": "commento", "testo": "@amico1 @amico2 venite!"}),
        ("Quando ci seguono e scrivono SEGUO, quindici punti a testa per te.",
         {"tipo": "classifica", "titolo": "In testa 👑", "righe": [{"nome": f"{a['n']} · @{a['u']}", "valore": f"{a.get('pt', 0)} pt"} for a in t3], "utente": t3[0]["u"]} if t3 else {"tipo": "mappa", "luci": luci(D)}),
        ("Chi porta più amici, sale. Tagga ora!", {"tipo": "chiusura", "testo": "👥 Tagga 2 amici qui sotto"}),
    ]
    st["tag_extra"] = [a["u"] for a in t3]
    did = ("👥 Porta due amici e scala la classifica!\n\n"
           "1️⃣ Tagga qui sotto due amici che hanno un cane o un gatto\n"
           "2️⃣ Quando commentano col loro animale: +3 punti per te\n"
           "3️⃣ Quando ci seguono e scrivono SEGUO: +15 punti per te, per ognuno\n\n"
           "Due amici = +36 punti. Più amici porti, più il tuo animale sale verso la prossima corona 👑\n"
           "🐾 Non sei ancora sulla mappa? Commenta la tua città e il nome del tuo cane o gatto.")
    st["copertina"] = {"sopra": "PORTA 2 AMICI", "grande": "+36", "sotto": "punti e scali la classifica 👑", "domanda": "Chi tagghi? 👥👇", "tema": "duello"}
    st["banner_reel"] = "👥 Tagga 2 amici: se ci seguono, +15 punti a testa per te"
    st["senza_bonus"] = True
    return "👥 PORTA 2 AMICI", frasi, did

# ---------------------------------------------------------------- la serie della mappa (Alberto, 7/11): chi vede la pagina per la prima volta
# deve capire il gioco in pochi secondi. Ogni episodio usa la mappa vera del sito (scena «luce») e, se c'è, apre con un video vero.

def _dist(a, b):
    return math.hypot((a["lat"] - b["lat"]) * 111, (a["lng"] - b["lng"]) * 111 * math.cos(math.radians(a["lat"])))

def _a(c):  # «ad Atri», «a Treviso»
    return ("ad " if c[:1].lower() == "a" else "a ") + c

def _razza(a):
    r = (a.get("razza_testo") or a.get("razza") or "").replace("_", " ").strip()
    return "" if r in ("", "cane", "gatto") else r

def _intorno(D, centro, km=2000, escludi=()):  # tutte le luci vere: l'Italia di notte è già accesa, manca solo quel comune
    return [(a["lng"], a["lat"]) for a in D["animali"] if a.get("k") == "animale" and "lat" in a and a not in escludi and _dist(a, centro) < km][:4000]

def _clip(D, st, utente=None, a=None):
    """Un video vero per i primi secondi (docs/media/ugc/*.mp4, mandato in DM da chi ci segue, col suo SÌ). Meglio se è dell'animale raccontato.
    10/11 Alberto: «basta Thor». Senza video dei follower il reel si apre col volo 3D di notte sul paese della storia
    (reel/volo3d.js, il paese 3D del sito): ogni apertura è diversa e mostra l'animale vero nella sua cuccia."""
    fatte = set(st.get("clip_fatte", []))
    clip = [x for x in carica(ROOT / "motore/stato.json", {}).get("ugc", []) if x["f"].endswith(".mp4") and x["f"] not in fatte
            and (ROOT / "docs/media/ugc" / x["f"]).exists() and x["u"].lower() not in ESCLUSI]
    if not clip:
        if a and a.get("c"): st["intro_3d"] = {"comune": a["c"], "nome": a.get("n", "")}
        return None
    x = next((c for c in clip if utente and c["u"].lower() == utente.lower()), clip[0])
    st["clip_fatte"] = (st.get("clip_fatte", []) + [x["f"]])[-500:]
    st["intro"] = f"docs/media/ugc/{x['f']}"
    return x["u"]

def prima_luce(D, rng, st):
    """1. La prima luce: quale animale ha acceso per primo un comune. Il momento forte è il punto che passa da spento ad acceso."""
    an = [a for a in D["animali"] if a.get("k") == "animale" and _ts(a) and a["u"].lower() not in ESCLUSI and "lat" in a]
    primi = {}
    for a in sorted(an, key=lambda a: a["ts"]):
        primi.setdefault((a["c"], a.get("p")), a)
    usati = set(st.get("prime_luci", []))
    cand = sorted((a for a in primi.values() if a["c"] not in usati), key=lambda a: a["ts"], reverse=True)
    forza = st.pop("forza_prima_luce", None)  # test di crescita: il paese raccontato al buio che si è acceso
    if forza: cand = [a for a in primi.values() if a["c"] == forza] or cand
    cand = [a for a in cand if a["u"].lower() in D["seguono"]][:10] or cand[:10]
    if not cand: return puntata(D, rng, st)
    a = cand[0]; st["prime_luci"] = (list(usati) + [a["c"]])[-400:]
    st["luci_raccontate"] = (st.get("luci_raccontate", []) + [a["id"]])[-1000:]  # «Questa luce è di…» non racconta di nuovo lo stesso animale
    autore = _clip(D, st, a["u"], a)
    rz = _razza(a)
    frasi = [
        (f"Questa è l'Italia di notte. {_a(a['c'])[:1].upper() + _a(a['c'])[1:]} era tutto spento.", {"tipo": "luce", "centro": [a["lng"], a["lat"]], "intorno": _intorno(D, a, escludi=[a]),
          "punti": [{"lng": a["lng"], "lat": a["lat"], "acceso": False, "testo": f"La prima luce di {a['c']}"}]}),
        (f"Poi {a['n']}{', ' + rz + ',' if rz else ''} ha acceso la prima luce di {a['c']}!", {"tipo": "luce", "centro": [a["lng"], a["lat"]], "vicino": True, "intorno": _intorno(D, a, escludi=[a]),
          "punti": [{"lng": a["lng"], "lat": a["lat"], "testo": f"{a['n']} · @{a['u']}"}]}),
        ("Ogni animale può accendere la sua città: commenta città e nome.", {"tipo": "commento", "testo": f"{rng.choice(CITTA)}, Luna, cane"}),
        # 7/11 Alberto: la storia si chiude legandola al prossimo episodio, il motivo per seguire è vedere la prossima luce
        (f"{a['c']} si è accesa. Segui Zampe d'Italia per vedere la prossima luce.", {"tipo": "chiusura", "testo": "➕ Segui: la prossima luce è domani"}),
    ]
    st["tag_extra"] = [a["u"]]
    did = (f"✨ La prima luce di {a['c']} è di {a['n']}{' (' + rz + ')' if rz else ''}, di @{a['u']}! 👑\n\n"
           "Su Zampe d'Italia ogni animale accende una luce nella sua città, sulla mappa dell'Italia di notte (link in bio).\n"
           "👇 Il tuo comune è ancora al buio? Commenta la tua città e il nome del tuo cane o gatto (per esempio «Treviso, Luna, cane»): si accende col tuo @.\n"
           "➕ Segui Zampe d'Italia: ogni giorno raccontiamo una nuova prima luce. Domani la prossima!"
           + (f"\n🎥 Il video è di @{autore}" if autore else ""))
    st["copertina"] = {"luce": [a["lng"], a["lat"]], "sopra": "LA PRIMA LUCE", "grande": f"di {a['c']}", "sotto": f"{a['n']} 👑"}
    st["senza_bonus"] = True
    return f"✨ LA PRIMA LUCE", frasi, did

def testa_a_testa(D, rng, st):
    """2. Il derby: due comuni davvero vicini, sulla mappa e nel punteggio. Si mostra il distacco e si invita a partecipare."""
    an = [a for a in D["animali"] if a.get("k") == "animale" and "lat" in a and a.get("t") != "altro"]
    luoghi = {}
    for a in an:
        l = luoghi.setdefault(a["c"], {"c": a["c"], "lat": a["lat"], "lng": a["lng"], "n": 0}); l["n"] += 1
    L = [l for l in luoghi.values() if l["n"] >= 2]
    fatti = set(st.get("derby_vicini", []))
    coppie = sorted(((abs(x["n"] - y["n"]), _dist(x, y), x, y) for i, x in enumerate(L) for y in L[i + 1:]
                     if 3 < _dist(x, y) < 45 and abs(x["n"] - y["n"]) <= 2 and f"{x['c']}|{y['c']}" not in fatti), key=lambda t: (t[0], -min(t[2]["n"], t[3]["n"])))
    if not coppie: return prima_luce(D, rng, st)
    _, km, x, y = coppie[0]
    if x["n"] < y["n"]: x, y = y, x
    st["derby_vicini"] = (list(fatti) + [f"{x['c']}|{y['c']}", f"{y['c']}|{x['c']}"])[-200:]
    _clip(D, st, a={"c": y["c"]})
    if st.get("intro_3d"):  # 11/11: l'apertura è il duello, i due paesi 3D uno sopra l'altro (reel/apertura3d.py)
        st["intro_3d"]["duello"] = [[x["c"], x["n"]], [y["c"], y["n"]]]
    mezzo = {"lat": (x["lat"] + y["lat"]) / 2, "lng": (x["lng"] + y["lng"]) / 2}
    pari = x["n"] == y["n"]
    # 12/11 Alberto: «aggiungere i padroni o qualcosa sulle varie città». Le città col loro fatto vero (motore/citta.py, da Wikipedia)
    # e le squadre in campo: gli animali veri con il @ dei padroni, che vengono taggati (ricevono la notifica e condividono).
    import citta
    pv = {c: next((a.get("p", "") for a in an if a["c"] == c), "") for c in (x["c"], y["c"])}
    fx, fy = ((citta.fatto(c, pv[c]) or {}).get("fatto") for c in (x["c"], y["c"]))
    squadra = lambda c: sorted((a for a in an if a["c"] == c and a["u"].lower() not in ESCLUSI), key=lambda a: (a["u"].lower() not in D["seguono"], str(a.get("ts", ""))), reverse=False)
    sx, sy = squadra(x["c"]), squadra(y["c"])
    righe = [{"nome": f"{a['n']} · {x['c']}", "valore": "@" + a["u"]} for a in sx[:3]] + [{"nome": f"{a['n']} · {y['c']}", "valore": "@" + a["u"]} for a in sy[:2]]
    nomi = lambda l: " e ".join([", ".join(a["n"] for a in l[:-1]), l[-1]["n"]] if len(l) > 1 else [l[0]["n"]]) if l else ""
    st["tag_extra"] = list(dict.fromkeys(a["u"] for a in (sx[:5] + sy[:5])))[:10]  # 13/11: al massimo 10 (20 sembrava spam)
    if st.get("intro_3d") and (fx or fy): st["intro_3d"]["fatti"] = [fx, fy]
    frasi = [
        (f"{x['c']}{', ' + fx + ',' if fx else ''} contro {y['c']}{', ' + fy if fy else ''}: {round(km)} chilometri, e la sfida è aperta.", {"tipo": "luce", "centro": [mezzo["lng"], mezzo["lat"]], "s1": 1.5, "intorno": _intorno(D, mezzo, 50),
          "punti": [{"lng": x["lng"], "lat": x["lat"], "testo": f"{x['c']} · {x['n']}"}, {"lng": y["lng"], "lat": y["lat"], "testo": f"{y['c']} · {y['n']}"}]}),
        ((f"Pari: {x['n']} a {y['n']}. Il prossimo animale decide chi passa avanti." if pari else
          f"{x['n']} a {y['n']}: basta {'un animale' if x['n'] - y['n'] == 1 else 'due animali'} e {y['c']} pareggia."),
         {"tipo": "duello", "sinistra": {"titolo": x["c"], "valore": str(x["n"])}, "destra": {"titolo": y["c"], "valore": str(y["n"])}}),
    ]
    if sx and sy:
        frasi.append((f"In campo {nomi(sx[:2])} per {x['c']}, {nomi(sy[:2])} per {y['c']}.", {"tipo": "classifica", "titolo": "⚔️ Le squadre in campo", "righe": righe}))
    # 14/11, confronto dei 7 giorni: col duello 3D e i padroni taggati le views sono salite (2.023) ma i follower no (3,1 ogni 1.000):
    # la chiusura dà un motivo per seguire, vero: domani alle 13 c'è un'altra sfida tra due città
    frasi.append((f"Sei di {y['c']} o di {x['c']}? Commenta città e nome. Seguici: domani un'altra sfida.", {"tipo": "chiusura", "testo": "➕ Segui: domani un'altra sfida"}))
    did = (f"⚔️ {x['c']} {x['n']} – {y['n']} {y['c']}: due comuni a {round(km)} km, e la sfida è aperta!\n"
           + (f"🏰 {x['c']}, {fx}" + (f" · {y['c']}, {fy}" if fy else "") + "\n" if fx else (f"🏰 {y['c']}, {fy}\n" if fy else "")) + "\n"
           "Ogni animale accende una luce nella sua città sulla mappa dell'Italia di notte (link in bio).\n"
           f"👇 Commenta la tua città e il nome del tuo cane o gatto (per esempio «{y['c']}, Luna, cane»): si accende col tuo @ e conta per la tua città.\n"
           "👥 Tagga chi è di lì!\n➕ Seguici: ogni giorno alle 13 una sfida nuova tra due città vicine. La prossima può essere la tua.")
    st["copertina"] = {"luce": [mezzo["lng"], mezzo["lat"]], "sopra": "TESTA A TESTA", "grande": f"{x['n']} – {y['n']}", "sotto": f"{x['c']} vs {y['c']}"}
    st["senza_bonus"] = True
    return "⚔️ TESTA A TESTA", frasi, did

PROSSIME_LUCI = "domani alle 18"  # l'appuntamento della serie «Questa luce è di…» (config.json, orari: 18:00 questa_luce)

def questa_luce(D, rng, st):
    """3. Questa luce è di [Nome]: una nuova iscrizione in pochi secondi, e l'appuntamento con le prossime luci (un motivo per seguire)."""
    an = [a for a in D["animali"] if a.get("k") == "animale" and _ts(a) and a["u"].lower() not in ESCLUSI and "lat" in a]
    fatte = set(st.get("luci_raccontate", []))
    nuovi = sorted((a for a in an if a["id"] not in fatte), key=lambda a: a["ts"], reverse=True)
    nuovi = [a for a in nuovi[:30] if a["u"].lower() in D["seguono"]][:1] or nuovi[:1]
    if not nuovi: return prima_luce(D, rng, st)
    a = nuovi[0]; st["luci_raccontate"] = (list(fatte) + [a["id"]])[-1000:]
    autore = _clip(D, st, a["u"], a)
    rz = _razza(a)
    frasi = [
        (f"Questa luce è di {a['n']}{', ' + rz if rz else ''}, {_a(a['c'])}.", {"tipo": "luce", "centro": [a["lng"], a["lat"]], "intorno": _intorno(D, a, escludi=[a]),
          "punti": [{"lng": a["lng"], "lat": a["lat"], "acceso": False, "testo": f"Questa luce è di {a['n']}"}]}),
        ("Un commento, e il tuo animale si accende sulla mappa.", {"tipo": "commento", "testo": f"{a['c']}, {a['n']}, {a.get('t', 'cane')}"}),
        (f"Le prossime luci {PROSSIME_LUCI}. Seguici per vedere la tua!", {"tipo": "chiusura", "testo": f"➕ Le prossime luci {PROSSIME_LUCI}"}),
    ]
    st["tag_extra"] = [a["u"]]
    did = (f"💡 Questa luce è di {a['n']}{' (' + rz + ')' if rz else ''}, {_a(a['c'])}: benvenuti @{a['u']}! 🐾\n\n"
           "Su Zampe d'Italia ogni animale accende una luce nella sua città (la mappa è nel link in bio).\n"
           f"👇 Commenta la tua città e il nome del tuo cane o gatto: si accende col tuo @.\n"
           f"➕ Le prossime luci {PROSSIME_LUCI}: seguici per vedere se c'è la tua!"
           + (f"\n🎥 Il video è di @{autore}" if autore else ""))
    st["copertina"] = {"luce": [a["lng"], a["lat"]], "sopra": "QUESTA LUCE", "grande": f"è di {a['n']}", "sotto": a["c"]}
    st["senza_bonus"] = True
    return "💡 QUESTA LUCE È DI…", frasi, did

# ---------------------------------------------------------------- la Coppa delle Zampe (motore/coppa.py): reel di apertura, sorpasso e verdetto coi dati veri

def _coppa(D):
    st = carica(ROOT / "motore/stato.json", {})
    dove = {}
    for a in D["animali"]:
        if a.get("k") == "animale" and "lat" in a: dove.setdefault(f"{a['c']}|{a.get('p', '')}", a)
    return st.get("coppa"), st.get("coppa_albo", []), dove

_n = lambda k: (k or "").split("|")[0]

def _match(dove, a, b, pa, pb):
    x, y = dove[a], dove[b]
    mezzo = {"lat": (x["lat"] + y["lat"]) / 2, "lng": (x["lng"] + y["lng"]) / 2}
    lontani = _dist(x, y) > 120  # due città lontane: la mappa resta più larga
    return {"tipo": "luce", "centro": [mezzo["lng"], mezzo["lat"]], "s1": 0.7 if _dist(x, y) > 400 else 1.0 if lontani else 1.5, "intorno": _intorno(D_CORRENTE[0], mezzo),
            "punti": [{"lng": x["lng"], "lat": x["lat"], "testo": f"{_n(a)} · {pa}"}, {"lng": y["lng"], "lat": y["lat"], "testo": f"{_n(b)} · {pb}"}]}

D_CORRENTE = [None]
INVITO_COPPA = ("🏆 Ogni animale nuovo è un punto per la sua città: commenta qui sotto città, nome e cane o gatto (es. «Treviso, Luna, cane») e tagga chi è del tuo paese. "
                "Un punto in più con la prova del giorno su zampeditalia.it (link in bio).\n➕ Seguici per vedere il verdetto domenica alle 21!")

def coppa_apertura(D, rng, st):
    """Lunedì: parte il turno. Una sfida grande e una tra paesi piccoli, per far capire che vince anche chi è piccolo."""
    C, _, dove = _coppa(D); D_CORRENTE[0] = D
    if not C or not C.get("coppie"): return prima_luce(D, rng, st)
    coppie = [c for c in C["coppie"] if c[0] in dove and c[1] in dove]
    grande = coppie[0]
    piccole = coppie[len(coppie) // 2:] or coppie[-1:]  # la metà con meno giocatori: anche lì c'è una sfida vera
    p = piccole[rng.randrange(len(piccole))]
    _clip(D, st)
    frasi = [
        (f"Parte la Coppa delle Zampe: {len(coppie) * 2} comuni d'Italia, sfida a due.", _match(dove, grande[0], grande[1], 0, 0)),
        (f"{_n(grande[0])} contro {_n(grande[1])}. Ma anche {_n(p[0])} contro {_n(p[1])}: i paesi piccoli sfidano paesi piccoli.",
         {"tipo": "duello", "sinistra": {"titolo": _n(p[0]), "valore": "0"}, "destra": {"titolo": _n(p[1]), "valore": "0"}}),
        ("Una prova al giorno sul sito: un punto per la tua città.", {"tipo": "commento", "testo": "COPPA ··"}),
        ("Domenica alle 21 il trofeo. Gioca per la tua città!", {"tipo": "chiusura", "testo": "🏆 Gioca per la tua città"}),
    ]
    did = (f"🏆 Parte la Coppa delle Zampe, turno {C['turno']}: {len(coppie) * 2} comuni, sfide a due tra città con un numero simile di giocatori.\n"
           f"{_n(grande[0])} – {_n(grande[1])}, {_n(p[0])} – {_n(p[1])} e tante altre: anche il tuo paese ha la sua sfida.\n\n" + INVITO_COPPA)
    st["copertina"] = {"luce": [dove[grande[0]]["lng"], dove[grande[0]]["lat"]], "sopra": "PARTE LA COPPA", "grande": "delle Zampe", "sotto": "Gioca per la tua città 🏆"}
    st["banner_reel"] = "🏆 Gioca per la tua città: link in bio 👇"
    st["senza_bonus"] = True
    return "🏆 COPPA DELLE ZAMPE", frasi, did

def coppa_sorpasso(D, rng, st):
    """A metà settimana: l'ultimo sorpasso vero, o la sfida più tirata."""
    C, _, dove = _coppa(D); D_CORRENTE[0] = D
    if not C: return prima_luce(D, rng, st)
    P = C.get("punti", {})
    s = next((x for x in reversed(C.get("storia", [])) if x["sorpasso"] in dove and x["su"] in dove), None)
    if s:
        a, b = s["sorpasso"], s["su"]; testa = f"Sorpasso! {_n(a)} passa davanti {_a(_n(b))}."
    else:
        tirate = sorted((c for c in C["coppie"] if c[0] in dove and c[1] in dove and P.get(c[0], 0) + P.get(c[1], 0) > 0),
                        key=lambda c: (abs(P.get(c[0], 0) - P.get(c[1], 0)), -(P.get(c[0], 0) + P.get(c[1], 0))))
        if not tirate: return coppa_apertura(D, rng, st)
        a, b = tirate[0]
        if P.get(b, 0) > P.get(a, 0): a, b = b, a
        testa = f"{_n(a)} contro {_n(b)}: la sfida più tirata della Coppa."
    pa, pb = P.get(a, 0), P.get(b, 0)
    fine = datetime.fromisoformat(C["fine"]); giorni = max(0, (fine.date() - ORA.date()).days)
    frasi = [
        (testa, _match(dove, a, b, pa, pb)),
        (f"{pa} a {pb}, e mancano {giorni} giorni. Ogni giocatore porta un punto al giorno.", {"tipo": "duello", "sinistra": {"titolo": _n(a), "valore": str(pa)}, "destra": {"titolo": _n(b), "valore": str(pb)}}),
        (f"Sei di {_n(b)}? Gioca per la tua città!", {"tipo": "chiusura", "testo": f"🏆 Forza {_n(b)}!"}),
    ]
    did = f"⚔️ {_n(a)} {pa} – {pb} {_n(b)}: {testa.lower() if not s else 'sorpasso nella Coppa delle Zampe!'}\nMancano {giorni} giorni al verdetto.\n\n" + INVITO_COPPA
    st["copertina"] = {"luce": [dove[a]["lng"], dove[a]["lat"]], "sopra": "SORPASSO" if s else "TESTA A TESTA", "grande": f"{pa} – {pb}", "sotto": f"{_n(a)} vs {_n(b)}"}
    st["banner_reel"] = "🏆 Gioca per la tua città: link in bio 👇"
    st["senza_bonus"] = True
    return "⚔️ COPPA DELLE ZAMPE", frasi, did

def coppa_verdetto(D, rng, st):
    """Domenica alle 21: chi ha vinto la sua sfida prende il trofeo sulla mappa. Persone vere e città vere: chi vince condivide."""
    C, albo, dove = _coppa(D); D_CORRENTE[0] = D
    if not albo or not albo[-1]["vincitori"]: return coppa_sorpasso(D, rng, st)
    v = [x for x in albo[-1]["vincitori"] if x["c"] in dove]
    if not v: return prima_luce(D, rng, st)
    t = v[0]
    piccolo = next((x for x in reversed(v) if x is not t), None)
    frasi = [
        (f"Verdetto della Coppa delle Zampe: vince {_n(t['c'])}, {t['p']} a {t['pc']} contro {_n(t['contro'])}!", {"tipo": "luce", "centro": [dove[t["c"]]["lng"], dove[t["c"]]["lat"]], "intorno": _intorno(D, dove[t["c"]]),
          "punti": [{"lng": dove[t["c"]]["lng"], "lat": dove[t["c"]]["lat"], "acceso": False, "testo": f"🏆 {_n(t['c'])}"}]}),
        (f"Trofeo anche per {len(v) - 1} altre città" + (f", come {_n(piccolo['c'])}." if piccolo else "."),
         {"tipo": "classifica", "titolo": "🏆 I vincitori", "righe": [{"nome": _n(x["c"]), "valore": f"{x['p']}–{x['pc']}"} for x in v[:5]]}),
        ("Domani si riparte. Gioca per la tua città!", {"tipo": "chiusura", "testo": "🏆 Lunedì si riparte"}),
    ]
    elenco = "\n".join(f"🏆 {_n(x['c'])} {x['p']}–{x['pc']} {_n(x['contro'])}" for x in v[:15])
    did = f"🏆 Il verdetto della Coppa delle Zampe, turno {albo[-1]['turno']}!\n\n{elenco}\n\nI trofei sono sulla mappa di zampeditalia.it. Domani a mezzanotte parte il turno nuovo.\n\n" + INVITO_COPPA.replace("domenica alle 21", "domenica prossima")
    st["copertina"] = {"luce": [dove[t["c"]]["lng"], dove[t["c"]]["lat"]], "sopra": "HA VINTO", "grande": _n(t["c"]), "sotto": "Coppa delle Zampe 🏆"}
    st["banner_reel"] = "🏆 Lunedì si riparte: gioca per la tua città 👇"
    st["senza_bonus"] = True
    return "🏆 IL VERDETTO", frasi, did

# ================================================================ TEST DI CRESCITA (Alberto, 8/11): quali reel portano più follower
# Due format di scoperta, «Il paese al buio» e «Il campanile rivale», con il gancio scritto grande nel primo fotogramma (si capisce a volume zero),
# niente apertura con un video (il gancio è il primo fotogramma), la mappa solo quando mostra un cambiamento (uno svelamento, un punteggio).
# Ogni episodio esce in due versioni a confronto: voce sintetica dichiarata, oppure solo testo a schermo con musica ed effetti.
# Prima del rendering si verifica che il caso sia vero (verifica()); se non c'è un caso verificato l'episodio salta e si registra il motivo.

TEST_FORMATI = {"paese_al_buio": True, "campanile_rivale": True}

class Salta(Exception):
    """Non c'è un caso verificato (o una storia con un motivo per uscire): il reel non esce, e si registra perché."""

def _comuni():
    return [{"c": c, "p": p, "r": r, "lat": lat, "lng": lng} for c, p, r, lat, lng in carica(ROOT / "dati/comuni_min.json", [])]

def _luci_vere():
    """Tutte le luci della mappa in questo momento (docs/data/animali.json), per la verifica dei casi."""
    return [a for a in carica(ROOT / "docs/data/animali.json", {"animali": []})["animali"] if a.get("k") != "stella" and "lat" in a]

def _al_buio(com, luci):
    """Un comune è al buio se nessuna luce porta il suo nome e provincia, e nessuna luce sta a meno di 1 km dal suo centro."""
    return not any((a["c"] == com["c"] and a.get("p", "") == com["p"]) or _dist(a, com) < 1.0 for a in luci)

def _con_maiuscola(t): return t[:1].upper() + t[1:]

def paese_al_buio(D, rng, st):
    """Test 1 · Il paese al buio: «Atri è ancora al buio.» Tutto intorno è acceso, quel comune no. Chi è di lì accende la prima luce."""
    luci = _luci_vere()
    per_c = {}
    for a in luci: per_c.setdefault((a["c"], a.get("p", "")), []).append(a)
    griglia = {}
    for (c, p), v in per_c.items():
        x = v[0]; griglia.setdefault((round(x["lat"] * 5), round(x["lng"] * 5)), []).append({"c": c, "p": p, "lat": x["lat"], "lng": x["lng"], "n": len(v)})
    usati = set(st.get("paesi_buio", []))
    cand = []
    for com in _comuni():
        k = f"{com['c']}|{com['p']}"
        if k in usati or (com["c"], com["p"]) in per_c: continue
        gi, gj = round(com["lat"] * 5), round(com["lng"] * 5)
        vic = [l for di in (-1, 0, 1) for dj in (-1, 0, 1) for l in griglia.get((gi + di, gj + dj), []) if _dist(l, com) <= 12]
        if len(vic) < 3 or any(_dist(l, com) < 1.0 for l in vic): continue
        cand.append((len(vic), sum(l["n"] for l in vic), com, vic))
    if not cand: raise Salta("nessun comune al buio con almeno 3 comuni accesi entro 12 km")
    cand.sort(key=lambda t: (-t[0], -t[1], t[2]["c"]))
    _, _, com, vic = cand[rng.randrange(min(5, len(cand)))]
    if not _al_buio(com, luci): raise Salta(f"{com['c']} non è al buio")
    st["paesi_buio"] = (list(usati) + [f"{com['c']}|{com['p']}"])[-300:]
    v1, v2 = sorted(vic, key=lambda l: (-l["n"], l["c"]))[:2]
    c = com["c"]
    frasi = [
        (f"{c} è ancora al buio.", {"tipo": "gancio", "testo": f"*{c}* è ancora al buio.", "sotto": f"0 animali sulla mappa · {com['r']}", "icona": "🌑"}),
        (f"Intorno, {v1['c']} ha {luci_n(v1['n'])} e {v2['c']} {v2['n']}. {_con_maiuscola(_a(c))}, nessuna.",
         {"tipo": "luce", "centro": [com["lng"], com["lat"]], "s1": 5.0, "volo": "regione", "accendi": 0.3, "intorno": _intorno(D, com, 40),
          "punti": [{"lng": com["lng"], "lat": com["lat"], "spento": True, "testo": f"{c} · 0"},
                    {"lng": v1["lng"], "lat": v1["lat"], "testo": f"{v1['c']} · {v1['n']}"}, {"lng": v2["lng"], "lat": v2["lat"], "testo": f"{v2['c']} · {v2['n']}"}]}),
        (f"Vivi {_a(c)}? Scrivi città, nome e cane o gatto.", {"tipo": "commento", "testo": f"{c}, Luna, cane"}),
        ("Vediamo chi accende la prima luce.", {"tipo": "chiusura", "testo": f"💡 Chi accende {c}?"}),
    ]
    did = (f"🌑 {c} è ancora al buio sulla mappa degli animali d'Italia.\n"
           f"Intorno {v1['c']} ha {luci_n(v1['n'])} e {v2['c']} {v2['n']}: {_a(c)} ancora nessuna.\n\n"
           f"👇 Vivi {_a(c)}? Scrivi qui sotto città, nome e cane o gatto (per esempio «{c}, Luna, cane»): chi commenta per primo accende la prima luce di {c}, col suo @.\n"
           f"👥 Tagga chi è di {c}!\n➕ Segui Zampe d'Italia per vedere chi la accende.")
    st["copertina"] = {"luce": [com["lng"], com["lat"]], "sopra": "ANCORA AL BUIO", "grande": c, "sotto": "Chi accende la prima luce?"}
    st["banner_reel"] = f"💬 Vivi {_a(c)}? Commenta città e nome 👇"
    st["test_caso"] = {"tipo": "paese_al_buio", "comune": c, "p": com["p"], "lat": com["lat"], "lng": com["lng"], "vicini": [[v1["c"], v1["n"]], [v2["c"], v2["n"]]]}
    st["hashtag"] = "#cani #gatti #italia #animalidomestici "
    st["senza_bonus"] = True
    return "🌑 IL PAESE AL BUIO", frasi, did

def _stato_coppa():
    return carica(ROOT / "motore/stato.json", {}).get("coppa")

def campanile_rivale(D, rng, st):
    """Test 2 · Il campanile rivale: «Treviso contro Como. Chi passa?» Una sfida vera della Coppa, il punteggio, la Staffetta di quartiere."""
    import coppa as CP
    C = _stato_coppa()
    if not C or C.get("chiuso"): raise Salta("nessun turno della Coppa aperto")
    pos = {f"{x['c']}|{x['p']}": x for x in _comuni()}
    n_an = {}
    for a in D["animali"]:
        if a.get("k") == "animale": n_an[f"{a['c']}|{a.get('p', '')}"] = n_an.get(f"{a['c']}|{a.get('p', '')}", 0) + 1
    P, fatti = C.get("punti", {}), set(st.get("campanili", []))
    cand = [(a, b) for a, b in C.get("coppie", []) if a in pos and b in pos and n_an.get(a, 0) >= 2 and n_an.get(b, 0) >= 2
            and f"{C['turno']}|{a}|{b}" not in fatti and a.split("|")[0] != b.split("|")[0]]
    if not cand: raise Salta("nessuna sfida della Coppa con due comuni attivi ancora da raccontare")
    cand.sort(key=lambda x: (-(P.get(x[0], 0) + P.get(x[1], 0)), abs(P.get(x[0], 0) - P.get(x[1], 0)), -(n_an[x[0]] + n_an[x[1]])))
    a, b = cand[0]
    if P.get(b, 0) > P.get(a, 0): a, b = b, a
    pa, pb = P.get(a, 0), P.get(b, 0)
    A, B, xa, xb = _n(a), _n(b), pos[a], pos[b]
    st["campanili"] = (list(fatti) + [f"{C['turno']}|{a}|{b}"])[-300:]
    km = _dist(xa, xb); mezzo = {"lat": (xa["lat"] + xb["lat"]) / 2, "lng": (xa["lng"] + xb["lng"]) / 2}
    s1 = max(0.6, min(1.8, 600 / max(km / 0.43, 1)))  # tutte e due le città nel fotogramma
    qa, qb = CP.quartiere(C, a), CP.quartiere(C, b)
    fine = datetime.fromisoformat(C["fine"]); gg = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"][fine.weekday()]
    pt = lambda n: "1 punto" if n == 1 else f"{n} punti"
    frasi = [
        (f"{A} contro {B}. Chi passa?", {"tipo": "gancio", "testo": f"*{A}* contro *{B}*", "sotto": "Chi passa? · Coppa delle Zampe", "icona": "⚔️"}),
        (f"{A} {pt(pa)}, {B} {pt(pb)}: si chiude {gg} alle 20.", {"tipo": "luce", "centro": [mezzo["lng"], mezzo["lat"]], "s1": round(s1, 2), "volo": "regione", "accendi": 0.3,
          "intorno": _intorno(D, mezzo, max(60, km)), "punti": [{"lng": xa["lng"], "lat": xa["lat"], "testo": f"{A} · {pt(pa)}"}, {"lng": xb["lng"], "lat": xb["lat"], "testo": f"{B} · {pt(pb)}"}]}),
        ("Tre persone dello stesso comune, ognuna col suo animale: un punto in più.",
         {"tipo": "classifica", "titolo": "🔁 Staffetta di quartiere", "righe": [{"nome": A, "valore": f"{qa['n']}/3"}, {"nome": B, "valore": f"{qb['n']}/3"}]}),
        ("Chiama due amici del tuo comune. In tre completate la staffetta.", {"tipo": "chiusura", "testo": f"👥 Tagga 2 amici di {A} o {B}"}),
    ]
    did = (f"⚔️ {A} {pa} – {pb} {B}: chi passa? La sfida della Coppa delle Zampe si chiude {gg} alle 20.\n\n"
           f"🔁 Staffetta di quartiere: tre persone dello stesso comune commentano qui sotto città, nome e cane o gatto (per esempio «{A}, Luna, cane»). "
           f"Alla terza, un punto della Coppa per la città.\n👥 Chiama due amici del tuo comune!\n➕ Segui Zampe d'Italia per il verdetto di domenica alle 21.")
    st["copertina"] = {"luce": [mezzo["lng"], mezzo["lat"]], "sopra": "CHI PASSA?", "grande": f"{pa} – {pb}", "sotto": f"{A} vs {B}"}
    st["banner_reel"] = f"👥 {A} o {B}? In tre chiudete la staffetta 👇"
    st["test_caso"] = {"tipo": "campanile_rivale", "a": a, "b": b, "turno": C["turno"], "punti": [pa, pb], "staffetta": [qa["n"], qb["n"]]}
    st["hashtag"] = "#cani #gatti #italia #animalidomestici "
    st["senza_bonus"] = True
    return "⚔️ IL CAMPANILE RIVALE", frasi, did

def aggiornamento(D, rng, st):
    """Test: il reel di aggiornamento del gioco (l'altro slot del giorno). Lunedì la Coppa che parte, poi l'ultimo sorpasso, altrimenti la luce nuova."""
    if ORA.weekday() == 0: return coppa_apertura(D, rng, st)
    C = _stato_coppa() or {}
    ultimo = (C.get("storia") or [{}])[-1].get("t")
    if ultimo and ultimo != st.get("sorpasso_raccontato"):
        st["sorpasso_raccontato"] = ultimo; return coppa_sorpasso(D, rng, st)
    return questa_luce(D, rng, st)

def staffetta_fatta(D, rng, st, k, quando):
    """La sera, solo se è successo: un comune ha chiuso la Staffetta di quartiere e ha preso il punto."""
    C = _stato_coppa(); com = next((x for x in _comuni() if f"{x['c']}|{x['p']}" == k), None)
    if not C or not com: raise Salta("staffetta non trovata")
    import coppa as CP
    r = CP.avversario(C, k); P = C.get("punti", {}); c = com["c"]
    st["staffette_raccontate"] = (st.get("staffette_raccontate", []) + [f"{k}|{quando}"])[-200:]
    frasi = [
        (f"{c} ha chiuso la staffetta.", {"tipo": "gancio", "testo": f"*{c}* ha chiuso la staffetta", "sotto": "Tre persone, tre animali, un punto 🏆", "icona": "🔁"}),
        (f"Tre persone di {c}, ognuna col suo animale: un punto nella Coppa delle Zampe.", {"tipo": "luce", "centro": [com["lng"], com["lat"]], "volo": "regione", "accendi": 0.3, "intorno": _intorno(D, com, 40),
          "punti": [{"lng": com["lng"], "lat": com["lat"], "acceso": False, "testo": f"🔁 {c}"}]}),
        (f"Ora {c} {P.get(k, 0)}, {_n(r)} {P.get(r, 0)}." if r else f"Ora {c} ha {P.get(k, 0)} punti.",
         {"tipo": "duello", "sinistra": {"titolo": c, "valore": str(P.get(k, 0))}, "destra": {"titolo": _n(r) or "?", "valore": str(P.get(r, 0))}}),
        ("Il tuo comune? Chiama due amici e completate la staffetta.", {"tipo": "chiusura", "testo": "👥 In tre si chiude la staffetta"}),
    ]
    did = (f"🔁 {c} ha chiuso la Staffetta di quartiere: tre persone, ognuna col suo animale, e un punto nella Coppa delle Zampe.\n\n"
           "👇 Il tuo comune? Commenta città, nome e cane o gatto, e chiama due amici del tuo comune: in tre chiudete la staffetta.\n➕ Segui Zampe d'Italia per il verdetto di domenica alle 21.")
    st["copertina"] = {"luce": [com["lng"], com["lat"]], "sopra": "STAFFETTA CHIUSA", "grande": c, "sotto": "+1 nella Coppa 🏆"}
    st["test_caso"] = {"tipo": "staffetta_fatta", "comune": k, "quando": quando}
    st["senza_bonus"] = True
    return "🔁 STAFFETTA CHIUSA", frasi, did

def verdetto_sera(D, rng, st):
    """Test: alle 21 un reel solo se c'è una storia con un motivo per uscire. Prima il paese al buio che si è acceso, poi la staffetta chiusa."""
    luci = _luci_vere()
    for k in reversed(st.get("paesi_buio", [])[-14:]):  # un paese raccontato al buio che ora ha la sua prima luce: la storia si chiude
        c, p = k.split("|")
        if k in st.get("paesi_accesi", []): continue
        if any(a["c"] == c and a.get("p", "") == p and a.get("k") == "animale" for a in luci):
            st["paesi_accesi"] = (st.get("paesi_accesi", []) + [k])[-300:]
            st["forza_prima_luce"] = c
            st["test_caso"] = {"tipo": "paese_acceso", "comune": c, "p": p}
            return prima_luce(D, rng, st)
    C = _stato_coppa() or {}
    for k, q in (C.get("quartiere") or {}).items():
        for ev in q.get("log", []):
            if f"{k}|{ev['t']}" not in st.get("staffette_raccontate", []) and ev["t"][:10] >= (ORA - timedelta(days=1)).date().isoformat():
                return staffetta_fatta(D, rng, st, k, ev["t"])
    raise Salta("alle 21 nessuna storia con un motivo per uscire (nessun paese al buio acceso, nessuna staffetta chiusa)")

def verifica(cop):
    """Mappa e dati, prima di caricare il reel: il caso raccontato è ancora vero? Restituisce l'errore dimostrato, o None."""
    t = (cop.get("test") or {}).get("caso") or {}
    if t.get("tipo") == "paese_al_buio":
        com = {"c": t["comune"], "p": t["p"], "lat": t["lat"], "lng": t["lng"]}
        acc = [a for a in _luci_vere() if (a["c"] == com["c"] and a.get("p", "") == com["p"]) or _dist(a, com) < 1.0]
        if acc: return f"{com['c']} non è più al buio: ci sono {luci_n(len(acc))} (la prima alle {str(acc[0].get('ts', ''))[11:16]})."
    if t.get("tipo") == "campanile_rivale":
        C = _stato_coppa()
        if not C or C.get("chiuso") or C.get("turno") != t["turno"]: return "il turno della Coppa raccontato non è più aperto"
        if [t["a"], t["b"]] not in C.get("coppie", []) and [t["b"], t["a"]] not in C.get("coppie", []): return f"la sfida {_n(t['a'])} – {_n(t['b'])} non esiste nel turno"
        ora = [C.get("punti", {}).get(t["a"], 0), C.get("punti", {}).get(t["b"], 0)]
        if ora != t["punti"]: return f"il punteggio è cambiato: {ora[0]}–{ora[1]} invece di {t['punti'][0]}–{t['punti'][1]}"
    return None


# ================================================================ formati nuovi (12/11, Alberto: «voglio video nuovi, idee diverse, basta sempre ste cose»)
FRASI_FISSE = {"indovina": 45, "figurina": 40, "testa_a_testa": 58, "gara_follower": 50, "intruso": 40, "nomi_top": 45, "corsa": 50}  # testi scritti apposta (niente riscrittura dell'IA, che rovinerebbe il «tre, due, uno»)

MANTELLI = {"europeo", "grigio", "nero", "rosso", "bianco", "bicolore", "bicolore_rosso", "calico", "tartarugato", "meticcio"}  # colori, non razze: fuori dal quiz

def _nome_razza(D, t, k):
    for r in D["razze"]["gatti" if t == "gatto" else "cani"]:
        if r[0] == k: return r[1].split(" (")[0].split(" / ")[0]  # «Tricolore (calico)» → «Tricolore»: la voce non legge le parentesi
    return k.replace("_", " ")

def indovina(D, rng, st):
    """Indovina la razza: la sagoma nera, tre secondi, poi la risposta con quanti ce ne sono davvero sulla mappa. Due manche."""
    an = [a for a in D["animali"] if a.get("k") == "animale" and a.get("t") in ("cane", "gatto") and a.get("razza") and a["u"].lower() not in ESCLUSI]
    conta = {}
    for a in an:
        if a["razza"] in MANTELLI: continue
        conta.setdefault((a["t"], a["razza"]), []).append(a)
    fatte = set(st.get("quiz_razze", []))
    cand = [(k, v) for k, v in conta.items() if len(v) >= 6 and f"{k[0]}|{k[1]}" not in fatte]
    if len(cand) < 2: st["quiz_razze"] = []; cand = [(k, v) for k, v in conta.items() if len(v) >= 6]
    cani = [c for c in cand if c[0][0] == "cane"]; gatti = [c for c in cand if c[0][0] == "gatto"]
    scelte = [rng.choice(cani)] + ([rng.choice(gatti)] if gatti else [rng.choice([c for c in cani if c is not cani[0]])])
    st["quiz_razze"] = (list(fatte) + [f"{k[0]}|{k[1]}" for k, _ in scelte])[-60:]
    frasi, tag = [], []
    for i, ((t, k), v) in enumerate(scelte):
        es = sorted(v, key=lambda a: (a["u"].lower() not in D["seguono"], str(a.get("ts", ""))), reverse=False)[0]
        nome_r = _nome_razza(D, t, k); tag.append(es["u"])
        frasi.append(("Indovina la razza: tre, due, uno." if i == 0 else "E questo? Tre, due, uno.",
                      {"tipo": "sagoma", "t": t, "razza_k": k, "seme": rng.randrange(1, 99), "manche": f"{i + 1}/2", "titolo": "INDOVINA LA RAZZA" if i == 0 else "E QUESTO?"}))
        frasi.append((f"{nome_r}! Sulla mappa sono {len(v)}, come {es['n']} di {es['c']}.",
                      {"tipo": "svela", "t": t, "razza_k": k, "seme": frasi[-1][1]["seme"], "razza": nome_r, "riga": f"{len(v)} sulla mappa · come {es['n']} di {es['c']}"}))
    frasi.append(("Quante ne hai indovinate? Rispondi con città e nome del tuo animale.", {"tipo": "chiusura", "testo": "💬 Quante ne hai indovinate?"}))
    (t1, k1), _ = scelte[0]; (t2, k2), _ = scelte[1]
    did = (f"🐾 Indovina la razza! Due sagome, tre secondi ciascuna. Era facile? 🤔\n\n"
           f"Le risposte vere sono sulla mappa di Zampe d'Italia (link in bio): ogni animale è una luce nella sua città.\n"
           f"👇 Scrivi quante ne hai indovinate, con la tua città e il nome del tuo cane o gatto (es. «2 su 2! Treviso, Luna, cane»): il tuo animale si accende sulla mappa col tuo @.\n"
           "➕ Seguici: ogni settimana un quiz nuovo.")
    st["tag_extra"] = tag
    st["copertina"] = None
    st["banner_reel"] = "🤔 Indovini la razza? Rispondi nei commenti 👇"
    st["hashtag"] = "#cani #gatti #razze #quiz #italia #animalidomestici "
    st["senza_bonus"] = True
    return "🤔 INDOVINA LA RAZZA", frasi, did

def figurina_reel(D, rng, st):
    """Le figurine delle Zampe: si apre la bustina e escono due figurine vere, col numero d'arrivo sulla mappa e la rarità."""
    an = sorted((a for a in D["animali"] if a.get("k") == "animale" and a.get("t") in ("cane", "gatto") and _ts(a)), key=lambda a: str(a.get("ts", "")))
    numero = {a["id"]: i + 1 for i, a in enumerate(an)}
    fatte = set(st.get("figurine", []))
    buone = [a for a in an if a["u"].lower() not in ESCLUSI and a["id"] not in fatte]
    recenti = buone[-120:]
    def rar(a):
        r = str(a.get("ruolo", ""))
        if a.get("pres") or a.get("capo") or "Presidente" in r or "Capobranco" in r or "Re " in r: return "leggendaria", r.split("·")[0].strip()[:28] or "Capobranco"
        if r.startswith("Fondatore") or a.get("fondatore"): return "rara", f"Fondatore di {a['c']}"
        return "comune", ""
    cane = next((a for a in sorted(recenti, key=lambda a: (a["u"].lower() not in D["seguono"], rng.random())) if a["t"] == "cane"), None)
    gatto = next((a for a in sorted(recenti, key=lambda a: (a["u"].lower() not in D["seguono"], rng.random())) if a["t"] == "gatto"), None)
    carte = [x for x in (cane, gatto) if x] or recenti[-2:]
    st["figurine"] = (list(fatte) + [a["id"] for a in carte])[-2000:]
    frasi = []
    for i, a in enumerate(carte):
        rz = _nome_razza(D, a["t"], a.get("razza") or ("europeo" if a["t"] == "gatto" else "meticcio")); r, motivo = rar(a)
        frasi.append(((f"Figurina numero {numero[a['id']]}: " if i == 0 else f"E la numero {numero[a['id']]}: ") + f"{a['n']}, {rz.lower()} di {a['c']}.",
                      {"tipo": "figurina", "t": a["t"], "razza_k": a.get("razza") or ("europeo" if a["t"] == "gatto" else "meticcio"), "seme": rng.randrange(1, 99),
                       "nome": a["n"], "comune": a["c"], "razza": rz, "numero": numero[a["id"]], "totale": len(an), "rarita": r, "motivo": motivo, "busta": i == 0}))
    frasi.append(("Vuoi la figurina del tuo animale? Commenta città e nome.", {"tipo": "chiusura", "testo": "🃏 Vuoi la tua figurina? 👇"}))
    st["tag_extra"] = [a["u"] for a in carte]
    elenco = " · ".join(f"Nº {numero[a['id']]} {a['n']} ({a['c']})" for a in carte)
    did = (f"🃏 Le figurine delle Zampe! Ogni animale sulla mappa ha la sua, col numero d'arrivo: oggi {elenco}.\n\n"
           f"Siamo a {len(an)} figurine in tutta Italia. Le rare sono dei Fondatori, le leggendarie di Capobranco e Presidenti.\n"
           "👇 Vuoi la figurina del tuo animale? Commenta qui città, nome e cane o gatto (es. «Treviso, Luna, cane»): entra nella collezione col prossimo numero.\n"
           "➕ Seguici: ogni settimana apriamo una bustina nuova.")
    st["copertina"] = None
    st["banner_reel"] = "🃏 Commenta città e nome: la tua figurina 👇"
    st["hashtag"] = "#cani #gatti #figurine #italia #animalidomestici "
    st["senza_bonus"] = True
    return "🃏 LE FIGURINE", frasi, did

def gara_follower(D, rng, st):
    """La gara dei follower (12/11, Alberto: «una gara di follower»): quale città ci segue di più? Barre vere (chi ha scritto SEGUO, per città),
    il fatto vero della prima città, il totale vero dei follower verso i 2.000, e l'invito: SEGUO con la tua città, 2 punti al tuo paese."""
    import coppa, citta
    S = carica(ROOT / "motore/stato.json", {})
    g = coppa.classifica_follower(S, D["animali"])
    top = g["sempre"][:6]
    if len(top) < 3: raise Salta("troppo poche città con chi ci segue")
    nome = lambda k: k.split("|")[0]
    f1 = (citta.fatto(nome(top[0][0]), top[0][0].split("|")[1]) or {}).get("fatto")
    ore = S.get("follower_ore") or []; tot = ore[-1][1] if ore else (D.get("follower") or {}).get("n")
    (a, na), (b, nb), (c, nc) = [(nome(k), n) for k, n in top[:3]]
    righe = [{"nome": nome(k), "valore": n, **({"nota": f1} if i == 0 and f1 and len(f1) <= 26 else {})} for i, (k, n) in enumerate(top)]
    frasi = [
        ("Quale città ci segue di più?", {"tipo": "gancio", "testo": "Quale città ci segue *di più*?", "sotto": "🏁 La gara dei follower", "icona": "🏁"}),
        (f"{a}{', ' + f1 + ',' if f1 else ''} è prima con {na}. Poi {b} con {nb} e {c} con {nc}.", {"tipo": "barre", "titolo": "🏁 Chi ci segue di più", "righe": righe}),
    ]
    if tot and tot < coppa.OBIETTIVO:
        frasi.append((f"Siamo {tot}: a duemila facciamo i fuochi su tutta l'Italia.", {"tipo": "numero", "grande": f"{tot:,}".replace(",", "."), "sotto": f"follower veri · a {coppa.OBIETTIVO:,} i fuochi 🎆".replace(",", ".")}))
    frasi.append(("Seguici e scrivi SEGUO con la tua città: due punti al tuo paese.", {"tipo": "chiusura", "testo": "🏁 SEGUO + la tua città 👇"}))
    did = (f"🏁 La gara dei follower: quale città ci segue di più?\n👑 {a} {na} · 🥈 {b} {nb} · 🥉 {c} {nc}" + (f"\n{a}, {f1}: chi la batte?" if f1 else "") + "\n\n"
           f"👇 Seguici e scrivi SEGUO qui sotto, con la tua città e il nome del tuo cane o gatto (es. «SEGUO, Treviso, Luna, cane»): +2 punti al tuo paese nella Coppa delle Zampe.\n"
           f"👥 Tagga gli amici del tuo paese: ogni amico che ci segue fa salire la tua città."
           + (f"\n🎆 Siamo {tot}: a {coppa.OBIETTIVO} accendiamo i fuochi su tutta la mappa!" if tot and tot < coppa.OBIETTIVO else ""))
    st["banner_reel"] = "🏁 Scrivi SEGUO e la tua città 👇"
    st["copertina"] = None
    st["hashtag"] = "#cani #gatti #italia #campanilismo #animalidomestici "
    st["senza_bonus"] = True
    return "🏁 LA GARA DEI FOLLOWER", frasi, did

# ================================================================ i reel d'impatto (13/11, studio dei numeri: vedi «STUDIO 13/11» in decisioni-reel.md)
# Dallo studio: i nostri reel li vede solo una parte di chi ci segue; per uscire servono video che un estraneo capisce subito,
# guarda fino in fondo (o riguarda) e commenta anche senza conoscere il gioco. Due format: il rompicapo e la classifica dei nomi.
# 13/11 sera, Alberto: «si vede subito che c'era il gatto». Il rompicapo deve essere difficile davvero: 36 cani identici,
# l'intruso ha un solo dettaglio diverso (reel/costruisci.py varia_muso). Chi non lo trova riguarda il video: sono views.
INTRUSI = [  # (dettaglio, titolo, come lo dice la voce)
    ("occhiolino", "Trova il cane che fa l'*occhiolino*", "Trova il cane che fa l'occhiolino"),
    ("triste", "Trova il cane *triste*", "Trova il cane triste"),
    ("lingua", "Trova il cane con la *lingua fuori*", "Trova il cane con la lingua fuori"),
    ("senza_collare", "Trova il cane *senza collare*", "Trova il cane senza collare"),
]
RAZZE_INTRUSO = ["golden", "bassotto", "husky", "labrador_miele", "jack_russell", "pastore_tedesco", "barboncino", "maltese", "chihuahua", "border_collie"]
ORDINALI = ["prima", "seconda", "terza", "quarta", "quinta", "sesta"]

def intruso(D, rng, st):
    """Trova l'intruso: 36 cani uguali, uno ha un dettaglio diverso, cinque secondi veri. Si capisce senza conoscere la pagina; chi non lo trova riguarda."""
    n = st.get("intruso_n", 0); st["intruso_n"] = n + 1
    dettaglio, titolo, detto = INTRUSI[n % len(INTRUSI)]
    razza = RAZZE_INTRUSO[(n * 3 + rng.randrange(len(RAZZE_INTRUSO))) % len(RAZZE_INTRUSO)]
    dove = [rng.randrange(1, 6), rng.randrange(0, 6)]  # mai nella prima riga: troppo facile
    seme = rng.randrange(1, 99)
    sc = {"base": ["cane", razza, seme, "base"], "altro": ["cane", razza, seme, dettaglio], "dove": dove, "nr": 6, "nc": 6}
    tot = sum(1 for a in D["animali"] if a.get("k") == "animale")
    frasi = [
        (f"{detto}. Cinque. Quattro. Tre. Due. Uno.", {"tipo": "intruso", **sc, "titolo": titolo}),
        (f"Eccolo: {ORDINALI[dove[0]]} riga. L'avevi visto?", {"tipo": "intruso_svela", **sc, "titolo": "ECCOLO!", "riga_testo": f"{ORDINALI[dove[0]]} riga, {ORDINALI[dove[1]]} colonna"}),
        ("Scrivi in quanti secondi l'hai trovato. Domani è più difficile.", {"tipo": "chiusura", "testo": "⏱️ In quanti secondi? 👇"}),
    ]
    did = (f"👀 {detto}: sono 36 e hai 5 secondi. Trovato al primo colpo?\n\n"
           "👇 Scrivi in quanti secondi l'hai trovato (e sii onesto 😄). Poi mandalo a chi dice di avere l'occhio di falco.\n"
           f"🐾 Se hai un cane o un gatto, aggiungi la tua città e il suo nome (es. «3 secondi! Treviso, Luna, cane»): si accende sulla mappa d'Italia con gli altri {tot}.\n"
           "➕ Seguici: domani il rompicapo è più difficile.")
    st["copertina"] = None
    st["banner_reel"] = "⏱️ In quanti secondi l'hai trovato? 👇"
    st["hashtag"] = "#cani #gatti #rompicapo #trovalintruso #quiz #animalidomestici "
    st["senza_bonus"] = True
    return "👀 TROVA L'INTRUSO", frasi, did

def _conta_nomi(D, tipo=None):
    conta, citta, forma = {}, {}, {}
    for a in D["animali"]:
        if a.get("k") != "animale" or (tipo and a.get("t") != tipo): continue
        k = unicodedata.normalize("NFD", a["n"].lower()); k = "".join(ch for ch in k if ch.isalpha())
        if len(k) < 2: continue
        conta[k] = conta.get(k, 0) + 1; citta.setdefault(k, set()).add(a["c"]); forma.setdefault(k, a["n"].strip().title())
    return sorted(((forma[k], n, len(citta[k])) for k, n in conta.items()), key=lambda x: (-x[1], x[0]))

def nomi_top(D, rng, st):
    """I nomi più usati: conto alla rovescia dal quinto al primo, poi «scrivi il nome del tuo: ti rispondiamo con quanti ce ne sono»
    (commenti.py risponde davvero col numero). A rotazione: tutti, solo cani, solo gatti."""
    n = st.get("nomi_n", 0); st["nomi_n"] = n + 1
    tipo, di, emoji = [(None, "di cani e gatti", "🐾"), ("cane", "di cane", "🐶"), ("gatto", "di gatto", "🐱")][n % 3]
    top = _conta_nomi(D, tipo)[:5]
    if len(top) < 5: raise Salta("troppo pochi nomi")
    (n1, k1, c1) = top[0]
    righe = [{"nome": nm, "valore": (None if i == 0 else k)} for i, (nm, k, _) in enumerate(top)]
    diversi = len(_conta_nomi(D, tipo))
    frasi = [
        (f"Il nome {di} più usato in Italia?", {"tipo": "gancio", "testo": f"Il nome {di} *più usato* in Italia?", "sotto": f"{emoji} Il tuo c'è?", "icona": emoji}),
        (f"Quinto {top[4][0]}, quarto {top[3][0]}, terzo {top[2][0]}, secondo {top[1][0]}.", {"tipo": "barre", "titolo": f"{emoji} I nomi più usati", "righe": righe, "conto": True}),
        (f"E al primo posto: {n1}! Sono {k1}, in {c1} città.", {"tipo": "gancio", "testo": f"*{n1}*", "sotto": f"👑 {k1} sulla mappa · in {c1} città", "icona": "👑"}),
        ("Scrivi il nome del tuo: ti rispondiamo con quanti ce ne sono.", {"tipo": "commento", "testo": "Il mio si chiama…"}),
    ]
    did = (f"{emoji} Il nome {di} più usato in Italia? 5° {top[4][0]} · 4° {top[3][0]} · 3° {top[2][0]} · 2° {top[1][0]} · 👑 {n1} ({k1}).\n"
           f"Sulla mappa di Zampe d'Italia ci sono {diversi} nomi diversi.\n\n"
           "👇 Scrivi qui sotto il nome del tuo animale: ti rispondiamo con quanti si chiamano come lui in Italia (e se è l'unico!).\n"
           "🗺️ Aggiungi anche la città (es. «Treviso, Luna, cane») e accendiamo la sua luce.\n➕ Seguici: ogni settimana una classifica nuova.")
    st["copertina"] = None
    st["banner_reel"] = "✍️ Scrivi il nome del tuo: quanti ce ne sono? 👇"
    st["hashtag"] = "#cani #gatti #nomi #nomicani #nomigatti #animalidomestici "
    st["senza_bonus"] = True
    return f"{emoji} I NOMI PIÙ USATI", frasi, did

MESI = ["gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic"]

def corsa(D, rng, st):
    """La corsa a barre (14/11): 20 giorni in 10 secondi, le barre crescono e si sorpassano, coi dati veri della mappa.
    A rotazione: le città, le razze di cane, le regioni. Chi guarda resta per vedere chi vince e tifa per il suo."""
    n = st.get("corsa_n", 0); st["corsa_n"] = n + 1
    an = [a for a in D["animali"] if a.get("k") == "animale" and _ts(a)]
    sogg = n % 3
    if sogg == 0: chiave, gancio, sotto, titolo, unita, emoji = (lambda a: a["c"]), "La città con *più animali* d'Italia?", "giorni in 10 secondi", "🏁 La corsa delle città", "animali", "🏙️"
    elif sogg == 1:
        an = [a for a in an if a.get("t") == "cane" and a.get("razza")]
        chiave, gancio, sotto, titolo, unita, emoji = (lambda a: _nome_razza(D, "cane", a["razza"])), "Il cane *più amato* d'Italia?", "giorni in 10 secondi", "🏁 La corsa delle razze", "cani", "🐶"
    else: chiave, gancio, sotto, titolo, unita, emoji = (lambda a: a.get("r") or ""), "La regione con *più animali*?", "giorni in 10 secondi", "🏁 La corsa delle regioni", "animali", "🗺️"
    giorni = sorted({str(a["ts"])[:10] for a in an})
    if len(giorni) < 6: raise Salta("troppo pochi giorni di dati per una corsa")
    per = {}
    for a in an:
        k = chiave(a)
        if k: per.setdefault(k, {}); per[k][str(a["ts"])[:10]] = per[k].get(str(a["ts"])[:10], 0) + 1
    cum = {k: [] for k in per}
    for k, d in per.items():
        t = 0
        for g in giorni: t += d.get(g, 0); cum[k].append(t)
    dentro = set()  # chi è stato tra i primi sei in almeno un giorno (dal secondo in poi), al massimo dodici
    for i in range(1, len(giorni)):
        dentro |= set(sorted(cum, key=lambda k: (-cum[k][i], k))[:6])
    finale = sorted(dentro, key=lambda k: (-cum[k][-1], k))[:12]
    serie = [{"nome": k, "valori": cum[k]} for k in finale]
    (p1, v1), (p2, v2), (p3, v3) = [(k, cum[k][-1]) for k in finale[:3]]
    etichette = [f"{int(g[8:])} {MESI[int(g[5:7]) - 1]}" for g in giorni]
    art = "il " if sogg == 1 else ""
    frasi = [
        (gancio.replace("*", ""), {"tipo": "gancio", "testo": gancio, "sotto": f"🏁 {len(giorni)} {sotto}", "icona": emoji}),
        (f"Si parte il {int(giorni[0][8:])} {['gennaio','febbraio','marzo','aprile','maggio','giugno','luglio','agosto','settembre','ottobre','novembre','dicembre'][int(giorni[0][5:7]) - 1]}. Guarda chi sale.",
         {"tipo": "corsa", "titolo": titolo, "giorni": etichette, "serie": serie, "pausa": 5.0}),
        (f"Vince {art}{p1} con {v1}. {p2[:1].upper() + p2[1:]} è a {v1 - v2}.", {"tipo": "gancio", "testo": f"*{p1}*", "sotto": f"👑 {v1} {unita} · {p2} a {v1 - v2}", "icona": "👑"}),
        (("E la tua città? Scrivi città e nome: falla salire." if sogg != 1 else "E il tuo? Scrivi città, nome e razza: fallo salire."), {"tipo": "commento", "testo": f"{p2 if sogg == 0 else rng.choice(CITTA)}, Luna, cane"}),
    ]
    did = (f"🏁 {titolo[2:]}: {len(giorni)} giorni in 10 secondi. 👑 {p1} {v1} · 🥈 {p2} {v2} · 🥉 {p3} {v3}.\n\n"
           + ("👇 La tua città non c'è, o è troppo indietro? Scrivi qui sotto città, nome e cane o gatto (es. «Treviso, Luna, cane»): ogni animale la fa salire.\n👥 Tagga chi è della tua città!\n"
              if sogg != 1 else "👇 Che cane hai? Scrivi città, nome e razza (es. «Treviso, Luna, golden»): ogni cane fa salire la sua razza.\n")
           + "➕ Seguici: ogni settimana una corsa nuova.")
    st["copertina"] = None
    st["banner_reel"] = "🏁 Scrivi la tua città: falla salire 👇" if sogg != 1 else "🏁 Scrivi città, nome e razza 👇"
    st["hashtag"] = "#cani #gatti #italia #classifica #campanilismo #animalidomestici "
    st["senza_bonus"] = True
    return titolo.upper(), frasi, did

def scelta_18():
    """Le 18 a rotazione (12/11): il quiz, le figurine, la luce nuova: tre idee diverse, mai lo stesso video due giorni di fila (dal 13/11)."""
    return ["indovina", "intruso", "nomi_top", "figurina", "questa_luce"][(ORA.date() - date(2026, 11, 13)).days % 5]

def sera_18(D, rng, st):
    return FORMATI[scelta_18()](D, rng, st)


FORMATI = {"corsa": corsa, "intruso": intruso, "nomi_top": nomi_top, "gara_follower": gara_follower, "indovina": indovina, "figurina": figurina_reel, "sera_18": sera_18, "paese_al_buio": paese_al_buio, "campanile_rivale": campanile_rivale, "aggiornamento": aggiornamento, "verdetto_sera": verdetto_sera, "coppa_apertura": coppa_apertura, "coppa_sorpasso": coppa_sorpasso, "coppa_verdetto": coppa_verdetto, "prima_luce": prima_luce, "testa_a_testa": testa_a_testa, "questa_luce": questa_luce, "amici": amici, "ospiti": ospiti, "ospiti_sera": ospiti_sera, "re": regno, "incoronazione": incoronazione, "fuochi": fuochi, "missione": missione, "star": star, "neopresidente": neopresidente, "nomi": nomi, "razze": razze, "sfida": sfida, "presidente": presidente, "negozio": negozio, "gara": gara, "derby": derby, "altri": altri, "buio": buio, "attivita": attivita, "benvenuti": benvenuti, "voto": voto, "duello": duello, "vetrina": vetrina, "fondatore": fondatore, "puntata": puntata}
ORARI = [(9, "duello"), (11, "voto"), (13, "benvenuti"), (16, "voto"), (18, "fondatore"), (21, "puntata"), (22, "voto")]

# ---------------------------------------------------------------- variazione con Claude, entro regole rigide

def numeri(s): return re.findall(r"\d+", s)

MAX_PAROLE = 48  # circa 17 secondi, con la scena SEGUO: in ottobre la visione media era 8-11 s su reel di 25 s, la gente se ne andava a metà

def taglia(frasi, max_parole=None):
    """Troppe parole (la domenica, con Capobranco, Re degli inviti e bonus insieme): via le scene di mezzo, dalla più vicina alla fine.
    Restano sempre l'apertura, il bonus e la chiusura."""
    frasi = list(frasi)
    while sum(len(t.split()) for t, _ in frasi) > (max_parole or MAX_PAROLE) and len(frasi) > 4:
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
              "La PRIMA frase è il gancio del primo secondo: parla a chi guarda (tu, il tuo cane, il tuo gatto, la tua città) con una domanda o una sfida "
              "che si capisce anche senza conoscere il gioco, mai una statistica secca (no «Giorno 4», no «1823 animali accesi» da soli). "
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
    if sys.argv[1] == "verifica":  # Mappa e dati prima di caricare: il caso è ancora vero? (reel.yml)
        cop = json.loads(Path(sys.argv[2]).read_text()); err = verifica(cop)
        if err:
            st = carica(STORICO, {})
            st["test_saltati"] = (st.get("test_saltati", []) + [{"quando": ORA.strftime("%Y-%m-%d %H:%M"), "formato": cop.get("formato"), "id": cop.get("id"), "motivo": f"Mappa e dati: {err}"}])[-100:]
            STORICO.write_text(json.dumps(st, ensure_ascii=False, indent=1))
            print(f"Mappa e dati: errore dimostrato, il reel si ferma: {err}"); sys.exit(78)
        print("Mappa e dati: caso verificato"); return
    parti = sys.argv[1].split(":")
    formato, uscita = parti[0], sys.argv[2]  # «fondatore:prova» è un Trial Reel: il copione è lo stesso; «paese_al_buio:testo» è la versione solo testo del test
    variante_test = next((x for x in parti[1:] if x in ("voce", "testo")), None)
    if formato == "sera_18": formato = scelta_18()  # il copione e il rendimento portano il nome vero del format
    if formato == "auto":
        formato = min(ORARI, key=lambda o: abs(o[0] - ORA.hour))[1]
    st = carica(STORICO, {})
    rng = random.Random(ORA.strftime("%Y%m%d%H") + formato)
    D = dati()
    try:
        titolo, frasi, did = FORMATI[formato](D, rng, st)
    except Salta as e:  # niente caso verificato: il reel non esce, e il motivo resta nel registro del test
        st["test_saltati"] = (st.get("test_saltati", []) + [{"quando": ORA.strftime("%Y-%m-%d %H:%M"), "formato": formato, "motivo": str(e)}])[-100:]
        STORICO.write_text(json.dumps(st, ensure_ascii=False, indent=1))
        Path(uscita).write_text(json.dumps({"salta": str(e), "formato": formato}, ensure_ascii=False))
        print(f"reel saltato ({formato}): {e}"); sys.exit(78)
    caso = st.pop("test_caso", None)
    test = TEST_FORMATI.get(formato) or (caso and caso.get("tipo") in ("paese_acceso", "staffetta_fatta"))
    # 10 prove diverse a rotazione (Alberto, 1/11: «non togliere la voce a prescindere, fai 10 prove di impatto»): voce sì/no,
    # apertura (solita, «siamo già N animali, manca il tuo?», la missione del paese virtuale più grande d'Italia), durata 48 o 32 parole.
    # Ogni reel segna la sua variante in st["varianti"]: il bot del mattino confronta views e follower per variante.
    # 2/11: da 10 varianti a 2. Con 10 varianti e formati diversi ogni variante aveva un reel ogni 2-3 giorni: nessun confronto possibile.
    # Resta una prova sola, voce sì / voce no, sempre corta (32 parole): la visione media era scesa a 7 secondi su reel da 15-20.
    # 2/11 pomeriggio, Alberto: i reel senza voce, solo scritte, non vanno. Sempre con la voce.
    VARIANTI = [("voce", "solita", 32)]
    nv = st.get("variante_n", 0); st["variante_n"] = nv + 1
    voce_v, apertura, max_parole = VARIANTI[nv % len(VARIANTI)]
    if FRASI_FISSE.get(formato):  # quiz e figurine: testi scritti apposta
        voce_v, apertura, max_parole = (variante_test or "voce"), "fissa", 45
        test_like = True
    else: test_like = False
    if test:  # test di crescita: frasi fisse (niente riscrittura, il gancio è quello del test), voce o solo testo come da piano
        voce_v, apertura, max_parole = (variante_test or "voce"), "gancio", 40
    if formato in ("star", "missione", "neopresidente"): apertura = "solita"  # hanno già la loro apertura
    tot_luci = len(luci(D))
    if apertura == "comunita":
        frasi.insert(0, (f"Siamo già {tot_luci} animali d'Italia. Manca il tuo?", {"tipo": "numero", "grande": str(tot_luci), "sotto": "animali veri, una sola grande famiglia 🐾"}))
    elif apertura == "missione":
        frasi.insert(0, ("Stiamo costruendo il paese virtuale con più animali d'Italia.", {"tipo": "mappa", "luci": luci(D)}))
    # Niente scena SEGUO dentro il video: l'1/11 occupava 5 secondi su 15 e chi guardava scorreva via (views da 3.000 a meno di 1.000).
    # La richiesta di seguire resta dove non ruba il contenuto: la scritta fissa in alto («➕ Seguici +30»), la didascalia e le risposte ai commenti.
    # 8/11: «senza_bonus» (didascalia che ha già la sua richiesta) non vuol dire «reel per le attività»: prima tutti questi reel prendevano gli hashtag dei veterinari
    per_attivita = formato == "attivita"
    if st.pop("senza_bonus", False) or per_attivita:
        did = did.strip() + "\n\n"
    else:  # una richiesta sola: con 8 richieste diverse in didascalia (ottobre) non se ne faceva nessuna
        if "città e nome" not in did: did = did.strip() + "\n\n👇 Commenta la tua città e il nome del tuo cane o gatto (es. «Treviso, Luna, cane»): si accende sulla mappa col tuo @."
        if formato != "star": did = did.strip() + "\n📸 Ci segui? Mandaci in privato una foto o 5 secondi di video del tuo animale che corre o gioca: finisce nei nostri reel, col tuo @!"
        # dal 30/10 sera, togliendo questa riga, i follower sono passati da circa 250 a 20-30 al giorno: resta sempre
        did = did.strip() + f"\n\n➕ Seguici e scrivi SEGUO: {PS} punti" + (" e il costume di Halloween per il tuo animale" if ORA.date().isoformat() <= "2026-11-02" else " e le lucine sulla cuccia") + ". Nei reel mettiamo prima gli animali di chi ci segue."
        fw = D.get("follower") or {}
        if fw.get("n") and fw["n"] < 2000:  # il traguardo di tutti: per ora la priorità sono i follower
            did = did.strip() + f"\n\n🎆 A 2.000 follower facciamo i fuochi d'artificio su tutta la mappa d'Italia: ne mancano {2000 - fw['n']}. Seguici e dillo a un amico!"
    if not per_attivita and not test and not test_like:  # nel reel per le attività la parola PRENOTA non si tocca; nel test il gancio resta quello scelto
        frasi, did = varia(frasi, did, D)
    frasi = taglia(frasi, max_parole)
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
    voce_ia = voce_v == "voce"  # senza voce artificiale niente avviso in didascalia
    did = did.strip() + ("\n\nVoce generata con IA.\n\n" if voce_ia else "\n\n") + ("#veterinario #toelettatura #petshop #pensioneperanimali #animalidomestici " if per_attivita else st.pop("hashtag", "#cani #gatti #italia #canicontrogatti #animalidomestici ")) + tag_citta
    intro = st.pop("intro", None)
    intro_3d = st.pop("intro_3d", None)
    # l'aspetto grafico a rotazione: mai uguale ai due reel prima (reel/modello/scene.py, TEMI)
    temi = ["notte", "tramonto", "aurora", "giorno", "neon"]  # colori resi abbastanza scuri da passare il controllo di contrasto (reel/modello/scene.py)
    gia = st.get("temi", [])[-2:]
    tema = rng.choice([t for t in temi if t not in gia])
    st["temi"] = (st.get("temi", []) + [tema])[-10:]
    id_reel = ORA.strftime("%Y-%m-%d-%H%M") + "-" + formato
    st["varianti"] = dict(list({**st.get("varianti", {}), id_reel: f"{voce_v}-{apertura}-{max_parole}"}.items())[-200:])
    copione = {"voce": voce_ia, "variante": f"{voce_v}-{apertura}-{max_parole}", "tema": tema, "id": id_reel, "formato": formato, "testata": {"titolo": titolo},
               "conteggio": {"cani": D["cani"], "gatti": D["gatti"]}, "frasi": [{"testo": t, "scena": sc} for t, sc in frasi],
               "banner": st.pop("banner_reel", "💬 Commenta città e nome del tuo animale 👇"), "didascalia": did,
               "tag": [u for u in mostrati if u.lower() not in ESCLUSI], "copertina": st.pop("copertina", None), **({"intro": intro} if intro else {}), **({"intro_3d": intro_3d} if intro_3d and not intro else {}),
               **({"test": {"nome": "crescita-1", "formato": formato, "variante": voce_v, "slot": ORA.strftime("%H:%M"), "caso": caso}} if test else {})}
    if test: copione.pop("intro", None); copione.pop("intro_3d", None)  # nel test il primo fotogramma è il gancio: niente video prima
    Path(uscita).write_text(json.dumps(copione, ensure_ascii=False, indent=1))
    STORICO.write_text(json.dumps(st, ensure_ascii=False, indent=1))
    print(f"copione {copione['id']}: " + " / ".join(t for t, _ in frasi))

if __name__ == "__main__":
    main()
