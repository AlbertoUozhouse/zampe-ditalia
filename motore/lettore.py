"""Lettura dei commenti con Claude: tutti i commenti di una persona insieme, così si capiscono anche le frasi libere,
le storie divise in più commenti e le correzioni ("no, era il contrario"). Ogni dato che torna viene controllato:
il nome deve comparire nei commenti e il comune deve esistere davvero. Se Claude non risponde, non si inventa niente."""
import json, os, re, sys, urllib.request

MODELLO = "claude-sonnet-5-5"

ISTRUZIONI = """Sei il lettore dei commenti di "Zampe d'Italia", un gioco su Instagram: chi commenta accende la luce del proprio animale su una mappa dell'Italia.
Il formato chiesto è «città, nome, razza», ma la gente scrive come vuole: in ordine sparso, con la regione, la provincia, emoji, frasi libere, più animali insieme, o a pezzi in più commenti. Si accettano TUTTI gli animali domestici: cani, gatti, conigli, furetti, gechi, tartarughe, criceti, pappagalli, cavalli, ecc.

Ti do tutti i commenti di UNA persona, in ordine di tempo. Ricostruisci la situazione FINALE: quali animali ha, con nome e comune. I commenti successivi completano o correggono quelli precedenti.

Regole:
- "nome" è il nome proprio dell'animale, scritto esattamente come nel commento (solo correggendo le maiuscole). Mai il comune, la provincia, la regione, la razza, il colore o una parola qualunque come nome. Se il nome non c'è, l'animale va in "senza_nome".
- "comune" è il comune italiano dove vive, con il nome ufficiale (per esempio "Reggio Emilia" → "Reggio nell'Emilia", "Ostia" → "Roma", "Sestri Ponente" → "Genova", "Acilia" → "Roma", "Gravina" vicino a Catania → "Gravina di Catania"). "comune_scritto" sono le parole esatte usate nel commento. "provincia" è la sigla se la sai (es. "LI"). Una provincia o regione da sola NON è un comune: se la persona scrive "Cecina, Livorno", il comune è Cecina e Livorno è la provincia. Se scrive due comuni ("Milano o Lecco"), prendi il primo.
- Se non c'è nessun comune, l'animale va in "senza_comune". Se vive fuori dall'Italia, "estero": true.
- "specie": "cane", "gatto" oppure la specie in italiano al singolare minuscolo ("coniglio", "geco", "tartaruga", "furetto", "lepre", ...). Se la specie non è detta ma c'è una razza di cane o di gatto, deducila; "meticcio" senza altro è un cane; se non si capisce, "cane".
- "razza": razza, incrocio o colore come scritto ("golden retriever", "gatto nero", "incrocio pincher chihuahua", "gechina crestata"), oppure "".
- "tipo": "stella" se l'animale non c'è più (il commento inizia con "Stella:", oppure dice "in cielo", "non c'è più"; "Bergamo, stella, cane" invece è un cane di nome Stella), "sogno" se è un animale che la persona sogna di avere ("Sogno:"), altrimenti "animale".
- Più animali nello stesso commento sono voci separate. Massimo 5 animali per persona.
- "dal_commento": l'id del commento in cui compare quell'animale (l'ultimo che lo descrive).
- "voti": i commenti che sono solo un voto nella sfida, cioè solo emoji o parole di cane, di gatto o di un altro animale (🐰🐢🦎🐹🦜…), senza un nome: {"id": ..., "squadra": "cani"|"gatti"|"altri"}.
- "segue": true se la persona dice di seguire la pagina ("seguo", "ti seguo", "follow fatto").
- "rimuovi": true se chiede di togliere i suoi animali.
- "domanda": se la persona fa una domanda alla pagina, riassumila in poche parole, altrimenti null.
- I tag ad altri account (@nome) non sono animali e non sono nomi.

Rispondi SOLO con questo JSON, senza testo prima o dopo:
{"animali":[{"nome":"","specie":"","razza":"","comune":"","comune_scritto":"","provincia":"","tipo":"animale","dal_commento":""}],
 "senza_comune":[{"nome":"","specie":"","dal_commento":""}],
 "senza_nome":[{"specie":"","comune":"","comune_scritto":"","dal_commento":""}],
 "estero":false,"voti":[],"segue":false,"rimuovi":false,"domanda":null}"""


def _chiave():
    k = os.environ.get("ANTHROPIC_API_KEY")
    if k:
        return k
    try:  # sul Mac di Alberto la chiave sta nel portachiavi
        import subprocess
        return subprocess.run(["security", "find-generic-password", "-a", "zampe", "-s", "zampe-anthropic", "-w"],
                              capture_output=True, text=True, timeout=10).stdout.strip() or None
    except Exception:
        return None


def chiedi(utente, commenti):
    """commenti: lista di {"id", "timestamp", "text"} di una persona. Restituisce il JSON di Claude oppure None."""
    k = _chiave()
    if not k:
        return None
    righe = "\n".join(f'[{c["id"]}] {c.get("timestamp", "")[:16]}  {c.get("text", "")}' for c in commenti[-25:])
    body = {"model": MODELLO, "max_tokens": 4000, "system": ISTRUZIONI,
            "messages": [{"role": "user", "content": f"Persona: @{utente}\nCommenti:\n{righe}"}]}
    for tentativo in range(3):
        try:
            r = urllib.request.Request("https://api.anthropic.com/v1/messages", data=json.dumps(body).encode(),
                                       headers={"x-api-key": k, "anthropic-version": "2023-06-01", "content-type": "application/json"})
            blocchi = json.loads(urllib.request.urlopen(r, timeout=90).read())["content"]
            testo = next(b["text"] for b in blocchi if b.get("type") == "text")
            return json.JSONDecoder().raw_decode(testo[testo.index("{"):])[0]
        except Exception as e:
            print(f"lettore: tentativo {tentativo + 1} non riuscito: {type(e).__name__}", file=sys.stderr)
    return None


DM = """Sei @zampeditalia e rispondi in privato su Instagram. Zampe d'Italia è un gioco: chi commenta sotto i nostri reel accende la luce del suo animale su una mappa notturna d'Italia (zampeditalia.it).
Regole che puoi spiegare:
- per entrare: commenta sotto un reel, oppure scrivi qui, «città, nome e animale», per esempio «Treviso, Luna, golden». Vale ogni animale: cani, gatti, conigli, furetti, gechi, tartarughe…;
- il primo animale di ogni comune diventa il Fondatore 👑 (+20 punti), gli altri +10;
- seguire la pagina e scrivere SEGUO vale +10 (+30 fino a domenica 8 novembre, la Settimana del follow); ogni amico taggato che poi commenta vale +3; chi ne porta di più in un giorno è il Re degli inviti e va nella puntata delle 21;
- scrivendo CARTOLINA qui si riceve la cartolina del proprio animale da mettere in storia;
- per un animale che non c'è più si scrive «Stella: città, nome»; per sparire dalla mappa si commenta RIMUOVI.
- il profilo privato va benissimo: si gioca uguale (commenti, luce sulla mappa, punti, cartolina); l'unica differenza è che nei reel non possiamo taggarlo, ma il nome e la città dell'animale compaiono lo stesso.
Tono: caldo, semplice, al massimo due frasi brevi, qualche emoji. Non inventare premi, date o funzioni che non sono qui. Non chiedere dati personali.
Se è una domanda sul gioco che queste regole non coprono, rispondi col buon senso restando dentro le regole (senza inventare premi, date o funzioni).
Se chi scrive ha un'attività per animali (veterinario, toelettatura, negozio, pensione, educatore) e vuole farsi vedere sulla mappa, digli di scriverci PRENOTA con il tipo di attività e il comune: prenotare è gratis e dà la precedenza e il -20%.
Solo se il messaggio è una proposta di collaborazione, una questione commerciale o una lamentela seria, rispondi che a breve gli scrive una persona del team.
Se il messaggio non richiede risposta (un cuore, «ok», «grazie»), puoi rispondere con un breve grazie oppure niente.
Rispondi SOLO con JSON: {"risposta": "testo oppure stringa vuota", "per_persona": true|false}"""


def rispondi_dm(utente, testi, suoi):
    """Risposta breve a un messaggio privato che non è un animale né una parola chiave. None se Claude non risponde."""
    k = _chiave()
    if not k:
        return None
    mappa = "; ".join(f"{a['n']} a {a['c']}" for a in suoi) or "nessuno ancora"
    body = {"model": MODELLO, "max_tokens": 2500, "system": DM,
            "messages": [{"role": "user", "content": f"I suoi animali sulla mappa: {mappa}\nMessaggi nuovi di @{utente}:\n" + "\n".join(testi[-6:])}]}
    try:
        r = urllib.request.Request("https://api.anthropic.com/v1/messages", data=json.dumps(body).encode(),
                                   headers={"x-api-key": k, "anthropic-version": "2023-06-01", "content-type": "application/json"})
        testo = next(b["text"] for b in json.loads(urllib.request.urlopen(r, timeout=60).read())["content"] if b.get("type") == "text")
        return json.JSONDecoder().raw_decode(testo[testo.index("{"):])[0]
    except Exception as e:
        print(f"lettore: risposta in privato non riuscita ({type(e).__name__})", file=sys.stderr)
        return None


PRENOTA = """Un'attività legata agli animali ci scrive in privato per prenotare il suo posto sulla mappa di Zampe d'Italia.
Dai messaggi capisci che tipo di attività è e in quale comune italiano si trova.
- "tipo": uno tra "veterinario", "toelettatura", "negozio" (negozio o shop per animali), "pensione" (pensione, asilo, dog sitter), "educatore" (educatore, addestratore, centro cinofilo), "altro"; null se non si capisce.
- "comune": il comune italiano con il nome ufficiale, null se non c'è. Una provincia da sola non è un comune.
Rispondi SOLO con JSON: {"tipo": ..., "comune": ...}"""


def prenotazione(testi):
    """Tipo di attività e comune da chi scrive PRENOTA. None se Claude non risponde."""
    k = _chiave()
    if not k:
        return None
    body = {"model": MODELLO, "max_tokens": 2000, "system": PRENOTA, "messages": [{"role": "user", "content": "\n".join(testi[-6:])}]}
    try:
        r = urllib.request.Request("https://api.anthropic.com/v1/messages", data=json.dumps(body).encode(),
                                   headers={"x-api-key": k, "anthropic-version": "2023-06-01", "content-type": "application/json"})
        testo = next(b["text"] for b in json.loads(urllib.request.urlopen(r, timeout=60).read())["content"] if b.get("type") == "text")
        return json.JSONDecoder().raw_decode(testo[testo.index("{"):])[0]
    except Exception as e:
        print(f"lettore: prenotazione non letta ({type(e).__name__})", file=sys.stderr)
        return None


def leggi(utente, commenti, comuni, norm, nome_proprio, razza, riservato=False):
    """Chiede a Claude e controlla tutto. Restituisce un dict pronto per il gioco, oppure None se Claude non ha risposto."""
    g = chiedi(utente, commenti)
    if g is None:
        return None
    tutto = norm(" ".join(c.get("text", "") for c in commenti))
    parole = f" {tutto} "

    def c_e(s):  # la parola o frase compare davvero nei commenti
        s = norm(s)
        return bool(s) and f" {s} " in parole

    def luogo(x):
        for prova in (f'{x.get("comune", "")} {x.get("provincia", "")}', x.get("comune", ""), x.get("comune_scritto", "")):
            if prova.strip():
                c, _ = comuni.trova(prova)
                if c:
                    # il comune deve essere stato scritto davvero (o almeno la sua parola principale)
                    scritto = x.get("comune_scritto") or x.get("comune", "")
                    if c_e(scritto) or c_e(c["c"]) or any(len(w) > 3 and c_e(w) for w in norm(c["c"]).split()):
                        return c
        return None

    animali, senza_comune, senza_nome, scartati = [], [], [], []
    visti = set()
    for x in g.get("animali", []) or []:
        nome = (x.get("nome") or "").strip()
        if not nome or not c_e(nome):
            scartati.append(("nome non nel testo", x)); continue
        L = luogo(x)
        specie = norm(x.get("specie") or "cane") or "cane"
        if not L:
            senza_comune.append({"n": nome_proprio(nome), "specie": specie, "id": x.get("dal_commento")}); continue
        if norm(nome) == norm(L["c"]):
            scartati.append(("nome uguale al comune", x)); continue
        if norm(nome) in visti:
            continue
        visti.add(norm(nome))
        t = specie if specie in ("cane", "gatto") else "altro"
        testo_razza = (x.get("razza") or "").strip()
        rz = razza(testo_razza, t) if t != "altro" else None
        k = x.get("tipo") if x.get("tipo") in ("stella", "sogno") else "animale"
        animali.append({"k": k, "t": t, "specie": specie, "n": nome_proprio(nome), "luogo": L,
                        "razza": rz or ("europeo" if t == "gatto" else "meticcio" if t == "cane" else None),
                        "razza_testo": testo_razza[:40] or specie, "id_commento": x.get("dal_commento")})
    for x in g.get("senza_comune", []) or []:
        if x.get("nome") and c_e(x["nome"]):
            senza_comune.append({"n": nome_proprio(x["nome"]), "specie": norm(x.get("specie") or ""), "id": x.get("dal_commento")})
    for x in g.get("senza_nome", []) or []:
        senza_nome.append({"specie": norm(x.get("specie") or ""), "luogo": luogo(x), "id": x.get("dal_commento")})
    ids = {c["id"] for c in commenti}
    voti = [v for v in g.get("voti", []) or [] if v.get("id") in ids and v.get("squadra") in ("cani", "gatti", "altri")]
    if scartati and not riservato:  # per i messaggi privati non si stampa niente: i log sono pubblici
        print(f"lettore: @{utente} scartati {scartati}", file=sys.stderr)
    return {"animali": animali[:5], "senza_comune": senza_comune, "senza_nome": senza_nome, "estero": bool(g.get("estero")),
            "voti": voti, "segue": bool(g.get("segue")), "rimuovi": bool(g.get("rimuovi")), "domanda": g.get("domanda")}
