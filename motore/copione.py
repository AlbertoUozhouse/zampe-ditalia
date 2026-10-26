"""Scrive il copione di un reel automatico partendo dai dati veri della mappa.

Uso: python3 motore/copione.py <formato|auto> <uscita.json>
Formati: duello (9:00), vetrina (13:00), fondatore (18:00), puntata (21:00). "auto" sceglie in base all'ora italiana.
Regola: nessun numero inventato. I numeri e i nomi vengono dai dati; Claude (se c'è ANTHROPIC_API_KEY) può solo
riformulare le frasi, e la riformulazione si scarta se cambia numeri o nomi o allunga troppo il testo.
"""
import json, os, random, re, sys, urllib.request
from datetime import datetime, date
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
STORICO = ROOT / "motore/reel_fatti.json"
LANCIO = date(2026, 10, 26)
ORA = datetime.now(ZoneInfo("Europe/Rome"))

# account di Alberto: restano sulla mappa ma non vengono mai nominati nei reel (la pagina cresce da sola)
ESCLUSI = {"thor_golden_life", "albertomarchesin"}

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
        per_citta.setdefault(a["c"], {"cani": 0, "gatti": 0})["gatti" if a.get("t") == "gatto" else "cani"] += 1
    oggi = ORA.date().isoformat()
    nuovi_fondatori = [a for a in an if a.get("ruolo", "").startswith("Fondatore") and str(a.get("ts", ""))[:10] == oggi and a["u"].lower() not in ESCLUSI]
    return {"animali": an, "tifo": tifo, "tutti": A, "razze": R, "per_citta": per_citta, "nuovi_fondatori": nuovi_fondatori,
            "cani": sum(1 for a in an + tifo if a.get("t") != "gatto"), "gatti": sum(1 for a in an + tifo if a.get("t") == "gatto")}

def luci(D):
    return [{"lng": a["lng"], "lat": a["lat"], "t": a.get("t", "cane")} for a in D["tutti"] if a.get("k") != "stella"]

def luci_n(n): return f"{n} {'luce' if n == 1 else 'luci'}"

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
        ("Scrivi nei commenti città, nome e razza del tuo animale.", {"tipo": "commento", "testo": f"{a}, {cane['nome']}, {cane['parola']}"}),
        ("Si accende la sua cuccia, col suo nome.", {"tipo": "cuccia", "nome": cane["nome"], "razza": cane["razza"], "seme": cane["seme"]}),
        ("Hai un gatto? Lui brilla sui tetti.", {"tipo": "gatto", "nome": gatto["nome"], "razza": gatto["razza"], "seme": gatto["seme"]}),
        (f"Allora: {a} o {b}? Scrivi la tua città!", {"tipo": "chiusura", "testo": "👇 Scrivi la tua città qui sotto"}),
    ]
    did = f"{a} o {b}: quale città si accende per prima? 🐶🐱\n\nScrivi qui sotto città, nome e razza (per esempio «{a}, {cane['nome']}, {cane['parola']}»): entro 15 minuti la luce del tuo animale si accende sulla mappa col tuo @. Il primo di ogni comune diventa il Fondatore 👑"
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
        ("E il tuo cane si accende così, col suo nome.", {"tipo": "cuccia", "nome": cane["nome"], "razza": cane["razza"], "seme": cane["seme"]}),
        ("Il tuo gatto, invece, brilla sui tetti.", {"tipo": "gatto", "nome": gatto["nome"], "razza": gatto["razza"], "seme": gatto["seme"]}),
        ("Qual è la tua razza? Scrivila qui sotto!", {"tipo": "chiusura", "testo": "👇 Scrivi la tua razza qui sotto"}),
    ]
    did = f"Ogni razza ha la sua cuccia 🐾 Sulla mappa di Zampe d'Italia ci sono già {nc} razze di cani e {ng} di gatti disegnate, ognuna diversa.\n\nScrivi qui sotto città, nome e razza: il tuo animale si accende sulla mappa col tuo @."
    return "CANI vs GATTI", frasi, did

def fondatore(D, rng, st):
    libere = [c for c in CITTA if sum(D["per_citta"].get(c, {}).values()) == 0 and c not in st.get("fondatori", [])[-8:]]
    if not libere: return duello(D, rng, st)
    c = rng.choice(libere); st.setdefault("fondatori", []).append(c)
    cane, gatto = esempio(rng, D)
    frasi = [
        (f"{c} non ha ancora un Fondatore.", {"tipo": "mappa", "luci": luci(D), "citta": [{"nome": c, "testo": c + "?", "colore": "d", "t": 0.3}], "zoom": {"comune": c, "s": 2.2}}),
        (f"Ad oggi, a {c}, gli animali sulla mappa sono zero.", {"tipo": "numero", "grande": "0", "sotto": f"animali a {c}, per ora"}),
        (f"Il primo che scrive {c}, nome e razza", {"tipo": "commento", "testo": f"{c}, {cane['nome']}, {cane['parola']}"}),
        ("accende la prima cuccia della città, col suo nome.", {"tipo": "cuccia", "nome": cane["nome"], "razza": cane["razza"], "seme": cane["seme"], "comune": "Fondatore di " + c}),
        ("E diventa il Fondatore. Per sempre.", {"tipo": "gatto", "nome": gatto["nome"], "razza": gatto["razza"], "seme": gatto["seme"]}),
        (f"Chi sarà il Fondatore di {c}? Scrivilo qui sotto!", {"tipo": "chiusura", "testo": f"👑 Diventa il Fondatore di {c}"}),
    ]
    did = f"{c} non ha ancora un Fondatore 👑\n\nIl primo animale di {c} che arriva sulla mappa lo diventa per sempre. Scrivi qui sotto «{c}, nome e razza» (per esempio «{c}, {cane['nome']}, {cane['parola']}»): entro 15 minuti la sua luce si accende."
    return "CANI vs GATTI", frasi, did

def puntata(D, rng, st):
    n = (ORA.date() - LANCIO).days + 1
    tot = len([a for a in D["tutti"] if a.get("k") != "stella"])
    top = sorted(D["per_citta"].items(), key=lambda kv: -sum(kv[1].values()))[:5]
    cane, gatto = esempio(rng, D)
    frasi = [(f"Giorno {n} della mappa: {tot} {'luce accesa' if tot == 1 else 'luci accese'} in Italia.", {"tipo": "numero", "grande": str(tot), "sotto": "luci accese in Italia"}),
             (f"Cani {D['cani']}, gatti {D['gatti']}.", {"tipo": "duello", "sinistra": {"titolo": "Cani", "valore": str(D["cani"])}, "destra": {"titolo": "Gatti", "valore": str(D["gatti"])}})]
    nf = [a["n"] for a in D["nuovi_fondatori"]][:3]
    if nf:
        frasi.append((f"Nuovi Fondatori di oggi: {', '.join(nf)}.", {"tipo": "classifica", "titolo": "Nuovi Fondatori 👑", "righe": [{"nome": a["n"], "valore": a["c"]} for a in D["nuovi_fondatori"][:5]]}))
    elif top:
        frasi.append(("Ecco le città più accese.", {"tipo": "classifica", "titolo": "Le città più accese", "righe": [{"nome": c, "valore": luci_n(sum(v.values()))} for c, v in top]}))
    frasi += [("Ogni commento è una luce: scrivi città, nome e razza.", {"tipo": "commento", "testo": f"{rng.choice(CITTA)}, {cane['nome']}, {cane['parola']}"}),
              ("Domani tocca alla tua città?", {"tipo": "mappa", "luci": luci(D)}),
              ("Scrivi qui sotto e accendi la tua luce!", {"tipo": "chiusura", "testo": "👇 Accendi la tua luce qui sotto"})]
    did = f"Giorno {n} della mappa di Zampe d'Italia 🌙 {tot} {'luce accesa' if tot == 1 else 'luci accese'}: cani {D['cani']}, gatti {D['gatti']}.\n\nScrivi qui sotto città, nome e razza del tuo animale e accendi la tua luce col tuo @. Il primo di ogni comune diventa il Fondatore 👑"
    return f"GIORNO {n}", frasi, did

FORMATI = {"duello": duello, "vetrina": vetrina, "fondatore": fondatore, "puntata": puntata}
ORARI = [(9, "duello"), (13, "vetrina"), (18, "fondatore"), (21, "puntata")]

# ---------------------------------------------------------------- variazione con Claude, entro regole rigide

def numeri(s): return re.findall(r"\d+", s)

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
    formato, uscita = sys.argv[1], sys.argv[2]
    if formato == "auto":
        formato = min(ORARI, key=lambda o: abs(o[0] - ORA.hour))[1]
    st = carica(STORICO, {})
    rng = random.Random(ORA.strftime("%Y%m%d%H") + formato)
    D = dati()
    titolo, frasi, did = FORMATI[formato](D, rng, st)
    frasi, did = varia(frasi, did, D)
    did = did.strip() + "\n\nVoce generata con IA.\n\n#cani #gatti #italia #canicontrogatti"
    copione = {"id": ORA.strftime("%Y-%m-%d-%H%M") + "-" + formato, "formato": formato, "testata": {"titolo": titolo},
               "conteggio": {"cani": D["cani"], "gatti": D["gatti"]}, "frasi": [{"testo": t, "scena": sc} for t, sc in frasi],
               "banner": "📍 Scrivi città, nome e razza 👇", "didascalia": did}
    Path(uscita).write_text(json.dumps(copione, ensure_ascii=False, indent=1))
    STORICO.write_text(json.dumps(st, ensure_ascii=False, indent=1))
    print(f"copione {copione['id']}: " + " / ".join(t for t, _ in frasi))

if __name__ == "__main__":
    main()
