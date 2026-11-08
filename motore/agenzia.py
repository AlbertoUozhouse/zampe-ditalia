"""Centro Agenzia di Zampe d'Italia (Alberto, 7/11/2026): il flusso dei reel come un ufficio con 10 reparti e 100 postazioni.

Claude monta e pubblica; il Direttore video è un agente OpenAI (API) che dirige prima del montaggio e rivede dopo l'esportazione.
Ogni scambio (proposta, risposta, correzione, decisione) si registra in docs/data/agenzia/ e si vede nella stanza (docs/agenzia/).

Uso (reel.yml):
  python3 motore/agenzia.py prima <copione.json>                       # il Direttore sceglie apertura, inquadratura e momento della luce
  python3 motore/agenzia.py revisione <copione.json> <cartella> <giro>  # fotogrammi + trascrizione + dati + audio -> verdetto
     esce 0 = approvato · 10 = correzioni applicate al copione (rimontare) · 20 = ancora difetti dopo 2 revisioni (bozza, riserva)
Chiavi solo nei Secrets di GitHub: OPENAI_API_KEY (Direttore), ANTHROPIC_API_KEY (Claude). Senza OPENAI_API_KEY la revisione
non blocca la produzione: si registra «Direttore non collegato» e il reel esce come prima.
"""
import base64, json, os, re, subprocess, sys, time, urllib.error, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATI = ROOT / "docs/data/agenzia"
FOTO = ROOT / "docs/agenzia/fotogrammi"
CONFIG = json.loads((ROOT / "motore/config.json").read_text())
MODELLI_OPENAI = CONFIG.get("openai_modelli", ["gpt-5", "gpt-4.1", "gpt-4o"])  # il primo che risponde
CLAUDE = "claude-sonnet-5-5"
PERSONE = CONFIG.get("agenzia_modello_persone", "claude-haiku-5-5")  # le 100 persone dell'ufficio: un modello veloce ed economico
MAX_REVISIONI = 2

# ---------------------------------------------------------------- l'ufficio: 10 reparti, 100 postazioni con mansioni distinte
REPARTI = [
    ("direzione", "Direzione video", ["Direttore video (OpenAI)", "Vicedirettore: primi 5 secondi", "Controllo realismo", "Controllo leggibilità da telefono", "Controllo animale-comune-luce",
                                      "Scelta dell'apertura", "Scelta dell'inquadratura", "Momento della luce", "Archivio delle decisioni", "Segreteria di direzione"]),
    ("montaggio", "Montaggio", ["Montatore (Claude)", "Assemblaggio scene", "Animazioni della mappa", "Sottotitoli", "Fascia in basso", "Ritmo e durata",
                                "Apertura con video vero", "Esportazione", "Correzioni del Direttore", "Versioni e bozze"]),
    ("copione", "Copione", ["Capo copione", "Ganci dei primi 2 secondi", "Frasi della voce", "Didascalie", "Inviti a commentare", "Inviti a seguire",
                            "Grammatica e preposizioni", "Nomi e @ veri", "Episodi della serie", "Coppa delle Zampe: testi"]),
    ("mappa", "Mappa e dati", ["Responsabile dati", "Verifica comune", "Verifica animale", "Verifica luce", "Coordinate", "Rilievo e coste",
                               "Prime luci", "Testa a testa", "Classifiche", "Pulizia dati"]),
    ("audio", "Voce e musica", ["Tecnico audio", "Volume della voce", "Volume della musica", "Silenzi", "Picchi e saturazione", "Suono dell'apertura",
                                "Voce sintetica dichiarata", "Musica di sottofondo", "Effetti", "Normalizzazione -14 LUFS"]),
    ("grafica", "Grafica e copertine", ["Art director", "Copertine", "Colori notte", "Contrasto 3:1", "Font e testi grandi", "Icone e trofei",
                                        "Cartoline", "Anelli della Staffetta", "Etichette sulla mappa", "Formato 9:16"]),
    ("pubblicazione", "Pubblicazione", ["Responsabile coda", "Orari", "Upload sul sito", "Pubblicazione Instagram", "Copertina su Instagram", "Tag",
                                        "Reel di riserva", "Bozze", "Registro pubblicazioni", "Una sola pubblicazione"]),
    ("community", "Community", ["Community manager", "Risposte ai commenti", "Messaggi privati", "Foto e video dei follower", "Consensi (SÌ)", "Nuove luci",
                                "SEGUO e inviti", "Moderazione", "Star del giorno", "Benvenuti"]),
    ("coppa", "Coppa delle Zampe", ["Commissario della Coppa", "Abbinamenti", "Prova del giorno", "Luce Misteriosa", "Indovina la Zampa", "Staffetta",
                                     "Punti e codici", "Trofei e albo", "Reel di apertura e verdetto", "Misure del turno"]),
    # 7/11 Alberto: l'acquisizione di follower al centro. La Crescita propone pubblico, gancio e motivo per seguire prima del montaggio
    ("crescita", "Crescita (follower)", ["Responsabile crescita", "Pubblico da raggiungere", "Gancio per chi non ci conosce", "Motivo per seguire", "Prossimo episodio",
                                         "Follower ogni 1.000 account", "Organico e sponsorizzato", "Confronto a 7 giorni", "Scelte da riprovare", "Verbale dei 7 giorni"]),
    # 8/11 Alberto: «serve un reparto innovazione per inventarsi cose nuove» (undicesima stanza: 110 persone)
    # missione (Alberto, 8/11): giochi nuovi che servono, reel che evolvono in modo diverso, gioco sempre più realistico
    ("innovazione", "Innovazione", ["Capo innovazione", "Giochi nuovi", "Meccaniche di gioco", "Realismo degli animali", "Realismo della mappa e del 3D",
                                     "Nuovi stili di reel", "Riprese e montaggio diversi", "Suono e musica nuovi", "Fattibilità tecnica", "Esperimenti misurabili"]),
    # 8/11 Alberto: «il reparto grafica 3D» (dodicesima stanza: 120 persone). Fanno il 3D del sito (three.js: mondo3d.js, paese.js)
    # e delle scene dei reel; ogni mattina lavorano con l'Innovazione sulla traccia «realismo», nei reel guardano i fotogrammi.
    ("grafica3d", "Grafica 3D", ["Capo grafica 3D", "Animali in 3D", "Paesi e piazze in 3D", "Rilievo e terreno veri", "Luci della notte in 3D",
                                 "Materiali e texture", "Camere e inquadrature 3D", "Animazioni 3D", "Scene 3D per i reel", "3D leggero sul telefono"]),
]

def ufficio():
    return [{"id": rid, "nome": nome, "postazioni": [{"id": f"{rid}-{i + 1}", "ruolo": r} for i, r in enumerate(ruoli)]} for rid, nome, ruoli in REPARTI]

# ---------------------------------------------------------------- registro: ogni scambio va nella stanza

class Sessione:
    def __init__(self, reel_id, formato, modalita="operativa"):
        DATI.mkdir(parents=True, exist_ok=True); (DATI / "sessioni").mkdir(exist_ok=True)
        self.f = DATI / "sessioni" / f"{reel_id}.json"
        self.d = json.loads(self.f.read_text()) if self.f.exists() else {"id": reel_id, "formato": formato, "modalita": modalita, "inizio": _ora(), "stato": "in corso", "scambi": [], "versioni": []}

    def scrivi(self, da, a, tipo, testo, dati=None):
        """tipo: proposta, risposta, correzione, decisione, nota. da/a: id di postazione (es. direzione-1, montaggio-1)."""
        self.d["scambi"].append({"t": _ora(), "da": da, "a": a, "tipo": tipo, "testo": testo, **({"dati": dati} if dati else {})})
        self.salva()

    def salva(self):
        self.f.write_text(json.dumps(self.d, ensure_ascii=False, indent=1) + "\n")
        reg = DATI / "registro.json"
        r = json.loads(reg.read_text()) if reg.exists() else []
        r = [x for x in r if x["id"] != self.d["id"]] + [{k: self.d.get(k) for k in ("id", "formato", "modalita", "inizio", "stato", "fine")} | {"scambi": len(self.d["scambi"])}]
        reg.write_text(json.dumps(r[-60:], ensure_ascii=False, indent=1) + "\n")
        (DATI / "ufficio.json").write_text(json.dumps(ufficio(), ensure_ascii=False) + "\n")

def _ora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

# ---------------------------------------------------------------- i due agenti

def _json(testo):
    testo = re.sub(r"^```(json)?|```$", "", testo.strip(), flags=re.M)
    return json.JSONDecoder().raw_decode(testo[testo.index("{"):])[0]

def openai(istruzioni, contenuto, immagini=()):
    """Il Direttore video (OpenAI, Chat Completions con immagini). Restituisce (json, modello) oppure (None, motivo)."""
    k = os.environ.get("OPENAI_API_KEY")
    if not k: return None, "manca OPENAI_API_KEY nei Secrets di GitHub"
    parti = [{"type": "text", "text": contenuto}] + [{"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(b).decode(), "detail": "low"}} for b in immagini]
    ultimo = ""
    for m in MODELLI_OPENAI:
        body = {"model": m, "response_format": {"type": "json_object"},
                "messages": [{"role": "system", "content": istruzioni}, {"role": "user", "content": parti}]}
        try:
            r = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=json.dumps(body).encode(),
                                       headers={"Authorization": f"Bearer {k}", "Content-Type": "application/json"})
            out = json.loads(urllib.request.urlopen(r, timeout=180).read())
            return _json(out["choices"][0]["message"]["content"]), m
        except urllib.error.HTTPError as e:
            ultimo = f"{m}: errore {e.code}"  # modello non disponibile o chiave non valida: si prova il successivo
            if e.code in (401, 429): break
        except Exception as e:
            ultimo = f"{m}: {type(e).__name__}"
    return None, ultimo

def claude(istruzioni, contenuto):
    """Claude, il montatore: traduce le correzioni del Direttore in azioni che il montaggio sa fare."""
    k = os.environ.get("ANTHROPIC_API_KEY")
    if not k: return None
    body = {"model": CLAUDE, "max_tokens": 8000, "system": istruzioni, "messages": [{"role": "user", "content": contenuto}], "output_config": {"effort": "medium"}}
    try:
        r = urllib.request.Request("https://api.anthropic.com/v1/messages", data=json.dumps(body).encode(),
                                   headers={"x-api-key": k, "anthropic-version": "2023-06-01", "content-type": "application/json"})
        t = next(b["text"] for b in json.loads(urllib.request.urlopen(r, timeout=120).read())["content"] if b.get("type") == "text")
        return _json(t)
    except Exception as e:
        print(f"agenzia: Claude non ha risposto ({type(e).__name__})", file=sys.stderr)
        return None

# ---------------------------------------------------------------- le 100 persone: ognuna fa la sua mansione sul reel, ogni capo reparto decide

PERSONA = """Lavori nel Centro Agenzia di Zampe d'Italia, una pagina Instagram italiana: ogni animale accende una luce nella sua città sulla mappa dell'Italia di notte.
Sei «{ruolo}» nel reparto «{reparto}». Fai SOLO la tua mansione sul reel qui sotto (materiali veri: copione, trascrizione coi secondi, dati verificati della mappa, misure audio, didascalia, numeri del progetto).
Tutta l'agenzia lavora per due cose (Alberto, 8/11): portare NUOVI FOLLOWER e fare contenuti BELLI (immagini curate, ritmo, testi chiari, emozione).
Guarda la tua mansione con questi due occhi: cosa in questo reel fa venire voglia di seguire la pagina, e cosa lo rende più bello o più brutto.
Sii concreto e breve, in italiano. Se nella tua mansione è tutto a posto dillo. Non inventare dati che non sono nei materiali.
Rispondi solo JSON: {{"controllato": "cosa hai controllato, una frase", "esito": "ok" oppure "segnalo", "secondo": numero o null, "problema": "...", "correzione": "...",
 "per_i_follower": "cosa aiuta o frena il follow, una frase", "per_la_bellezza": "cosa lo rende più bello, una frase", "idea": "una proposta utile per i prossimi reel, oppure vuoto"}}"""

CAPO = """Sei «{ruolo}», capo del reparto «{reparto}» del Centro Agenzia di Zampe d'Italia. Ricevi le relazioni delle tue 9 persone su questo reel.
Decidi per il reparto con due obiettivi: più follower e contenuti più belli. Cosa va corretto adesso (solo cose vere e importanti, con secondo, problema e correzione)
e quale idea portare avanti. Rispondi solo JSON: {{"decisione": "una frase", "da_correggere": [{{"secondo": numero o null, "problema": "...", "correzione": "..."}}],
 "per_i_follower": "una frase", "per_la_bellezza": "una frase", "idea_scelta": "..."}}"""

ERRORI_PERSONE = []

def lavora(sistema, contenuto, modello=None, immagini=()):
    """Una persona dell'ufficio al lavoro (Claude). Restituisce (json, token) oppure (None, 0).
    Con troppe richieste insieme (429/529) aspetta e riprova; se il modello delle persone non c'è, usa quello dei capi."""
    k = os.environ.get("ANTHROPIC_API_KEY")
    if not k: return None, 0
    modelli = [modello or PERSONE] + ([CLAUDE] if (modello or PERSONE) != CLAUDE else [])
    for m in modelli:
        # Haiku 5.5 e Sonnet 5.5 pensano prima di rispondere e il pensiero consuma max_tokens (7/11: risposte vuote o tagliate a 600):
        # sforzo basso, spazio largo, e su Haiku il pensiero spento (permesso fino allo sforzo «high»)
        parti = ([{"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": base64.b64encode(b).decode()}} for b in immagini]
                 + [{"type": "text", "text": contenuto}]) if immagini else contenuto
        body = {"model": m, "max_tokens": 4000 if m == CLAUDE else 1500, "system": sistema, "messages": [{"role": "user", "content": parti}],
                "output_config": {"effort": "low"}, **({"thinking": {"type": "disabled"}} if "haiku" in m else {})}
        for tentativo in range(5):
            try:
                r = urllib.request.Request("https://api.anthropic.com/v1/messages", data=json.dumps(body).encode(),
                                           headers={"x-api-key": k, "anthropic-version": "2023-06-01", "content-type": "application/json"})
                out = json.loads(urllib.request.urlopen(r, timeout=90).read())
                t = next(b["text"] for b in out["content"] if b.get("type") == "text")
                u = out.get("usage", {})
                return _json(t), u.get("input_tokens", 0) + u.get("output_tokens", 0)
            except urllib.error.HTTPError as e:
                ERRORI_PERSONE.append(f"{m}: {e.code}")
                if e.code in (429, 529, 500, 503): time.sleep(4 * (tentativo + 1)); continue
                break  # 400/404: modello non disponibile -> si passa al prossimo
            except Exception as e:
                ERRORI_PERSONE.append(f"{m}: {type(e).__name__}"); time.sleep(2)
    return None, 0

VEDONO = {"direzione", "grafica", "grafica3d", "copione", "mappa", "crescita"}  # 8/11: questi reparti ricevono anche 6 fotogrammi del video

def ufficio_al_lavoro(S, mat, foto=()):
    """Le 100 persone lavorano sul reel: 90 relazioni + 8 decisioni dei capi reparto (il capo della Direzione è il Direttore OpenAI,
    quello del Montaggio è Claude). Tutto va nella stanza. Restituisce le decisioni dei reparti, che vanno al Direttore."""
    from concurrent.futures import ThreadPoolExecutor
    if not os.environ.get("ANTHROPIC_API_KEY") or CONFIG.get("agenzia_persone") is False: return []
    progetto = progetto_in_breve()
    scelti = [foto[i] for i in sorted({round(k * (len(foto) - 1) / 5) for k in range(6)})] if foto else []
    immagini = [f.read_bytes() for _, f in scelti]
    testo = json.dumps({**mat, "progetto": progetto, "fotogrammi_secondi_inviati": [s for s, _ in scelti]}, ensure_ascii=False)[:24000]
    lavori = [(rid, nome, p) for rid, nome, ruoli in REPARTI for p in ufficio_reparto(rid)[1:]]
    token = 0
    def uno(x):
        rid, nome, p = x
        return x, lavora(PERSONA.format(ruolo=p["ruolo"], reparto=nome) + ("\nRicevi anche 6 fotogrammi del reel: il secondo di ciascuno è in «fotogrammi_secondi_inviati»." if rid in VEDONO and immagini else ""),
                         testo, None, immagini if rid in VEDONO else ())
    rel = {}
    with ThreadPoolExecutor(4) as ex:  # 4 alla volta: con 10 insieme la chiave va oltre il limite di richieste
        for (rid, nome, p), (r, t) in ex.map(uno, lavori):
            token += t
            capo = f"{rid}-1"
            if not r: S.d["scambi"].append({"t": _ora(), "da": p["id"], "a": capo, "tipo": "nota", "testo": "Non ha risposto in tempo."}); continue
            rel.setdefault(rid, []).append({"ruolo": p["ruolo"], **r})
            S.d["scambi"].append({"t": _ora(), "da": p["id"], "a": capo, "tipo": "proposta" if r.get("esito") == "segnalo" else "nota",
                                  "testo": (r.get("problema") or r.get("controllato") or "")[:300], "dati": {k: r.get(k) for k in ("controllato", "esito", "secondo", "problema", "correzione", "idea")}})
    decisioni = []
    def capo(x):
        rid, nome = x
        ruolo = ufficio_reparto(rid)[0]["ruolo"]
        return x, lavora(CAPO.format(ruolo=ruolo, reparto=nome), json.dumps(rel.get(rid, []), ensure_ascii=False), CLAUDE)
    with ThreadPoolExecutor(8) as ex:
        for (rid, nome), (r, t) in ex.map(capo, [(rid, nome) for rid, nome, _ in REPARTI if rid not in ("direzione", "montaggio")]):
            token += t
            if not r: continue
            decisioni.append({"reparto": nome, **r})
            S.d["scambi"].append({"t": _ora(), "da": f"{rid}-1", "a": "direzione-1", "tipo": "decisione", "testo": r.get("decisione", ""), "dati": {"difetti": r.get("da_correggere", []), "idea": r.get("idea_scelta")}})
    for rid in ("direzione", "montaggio"):  # le loro persone riferiscono direttamente al Direttore e al Montatore
        if rel.get(rid): decisioni.append({"reparto": dict((a, b) for a, b, _ in REPARTI)[rid], "relazioni": rel[rid]})
    S.d["token_persone"] = S.d.get("token_persone", 0) + token
    if ERRORI_PERSONE:
        from collections import Counter
        S.d["errori_persone"] = dict(Counter(ERRORI_PERSONE)); print("agenzia: errori delle persone", S.d["errori_persone"], file=sys.stderr)
    S.salva()
    return decisioni

def ufficio_reparto(rid):
    return next(r["postazioni"] for r in ufficio() if r["id"] == rid)

def progetto_in_breve():
    """I numeri del progetto per chi lavora sul reel: follower, ultimi reel, Coppa (niente nomi utente)."""
    try:
        A = json.loads((ROOT / "docs/data/animali.json").read_text())
        R = json.loads((ROOT / "motore/rendimento.json").read_text())[-6:]
        C = json.loads((ROOT / "docs/data/coppa.json").read_text()) if (ROOT / "docs/data/coppa.json").exists() else {}
        return {"follower": (A.get("follower") or {}).get("n"), "luci": len(A.get("animali", [])),
                "ultimi_reel": [{k: x.get(k) for k in ("formato", "views", "reach", "comments", "shares", "follower_ogni_1000")} for x in R],
                "coppa": {"turno": C.get("turno"), "sfide": len(C.get("sfide", [])), "staffette": len(C.get("anelli", []))}}
    except Exception:
        return {}

# ---------------------------------------------------------------- materiali per il Direttore

def dati_mappa(cop, cartella=None):
    """I dati verificati della mappa per le scene del reel: comune, coordinate, animale e @ veri (docs/data/animali.json),
    e il secondo esatto in cui la luce si accende nel file finale (tempi.json scritto dal montaggio)."""
    A = json.loads((ROOT / "docs/data/animali.json").read_text())["animali"]
    tempi = {}
    if cartella and (Path(cartella) / "tempi.json").exists():
        tempi = {t["scena"]: t for t in json.loads((Path(cartella) / "tempi.json").read_text())["scene"]}
    out = []
    for i, f in enumerate(cop["frasi"]):
        sc = f["scena"]
        for q in sc.get("punti", []):
            vicini = sorted((a for a in A if a.get("k") == "animale" and abs(a.get("lat", 0) - q["lat"]) < 0.02 and abs(a.get("lng", 0) - q["lng"]) < 0.02), key=lambda a: str(a.get("ts", "")))
            t = tempi.get(i, {})
            out.append({"scena": i, "etichetta": q.get("testo"), "lat": q["lat"], "lng": q["lng"],
                        "luce": ("spenta all'inizio della scena, si accende" if not q.get("acceso", True) else "già accesa") + (f" al secondo {t['accensione']} del reel" if t.get("accensione") is not None else ""),
                        "scena_dal_secondo": t.get("inizio"), "scena_al_secondo": t.get("fine"),
                        "comune_sulla_mappa": vicini[0]["c"] if vicini else None,
                        "animali_li_in_ordine_di_arrivo": [f"{a['n']} (@{a['u']}, {str(a.get('ts', ''))[:10]})" for a in vicini[:5]], "luci_li_oggi": len(vicini)})
    return out

def audio(mp4):
    """Il controllo della voce e della musica sul file: volume integrato, picco, silenzi e volume dei primi 5 secondi (ffmpeg)."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(mp4), "-af", "ebur128=peak=true,silencedetect=noise=-38dB:d=0.7", "-f", "null", "-"], capture_output=True, text=True).stderr
    i = re.findall(r"I:\s+(-?[\d.]+) LUFS", r); tp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r)
    silenzi = [(round(float(a), 1), round(float(b), 1)) for a, b in re.findall(r"silence_start: (-?[\d.]+)[\s\S]*?silence_end: (-?[\d.]+)", r)]
    r5 = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-t", "5", "-i", str(mp4), "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True).stderr
    m5 = re.findall(r"mean_volume: (-?[\d.]+) dB", r5)
    return {"lufs": float(i[-1]) if i else None, "picco_dbfs": float(tp[-1]) if tp else None, "silenzi_s": silenzi,
            "volume_medio_primi_5s_db": float(m5[0]) if m5 else None, "obiettivo": "-14 LUFS, picco sotto -1 dBFS, niente silenzi lunghi dopo l'apertura"}

def fotogrammi(mp4, cartella, versione, reel_id):
    """Un fotogramma ogni secondo (e a 0,5 s): per il Direttore (piccoli) e per la stanza (prima/dopo)."""
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp4)], capture_output=True, text=True).stdout)
    dove = FOTO / reel_id / f"v{versione}"; dove.mkdir(parents=True, exist_ok=True)
    out = []
    for s in [0.5] + list(range(1, int(dur) + 1)):
        s = min(s, dur - 0.05); f = dove / f"s{s:05.1f}.jpg"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{s}", "-i", str(mp4), "-frames:v", "1", "-vf", "scale=360:-2", "-q:v", "6", str(f)], check=True)
        out.append((round(s, 1), f))
    return dur, out

def trascrizione(cartella, cop):
    """Le parole della voce coi loro secondi nel reel finale (si aggiunge la durata dell'apertura, che viene prima)."""
    p = Path(cartella) / "parole.json"
    if not p.exists(): return " ".join(f["testo"] for f in cop["frasi"])
    parole = json.loads(p.read_text()); parole = parole.get("parole", parole) if isinstance(parole, dict) else parole
    off = 0.0
    if cop.get("intro") and (ROOT / cop["intro"]).exists():
        off = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(ROOT / cop["intro"])], capture_output=True, text=True).stdout or 0)
        off = min(off, float(cop.get("intro_durata") or off))
    return " ".join((f"[{w['s'] + off:.1f}s] " if i % 5 == 0 else "") + w.get("p", w.get("w", "")) for i, w in enumerate(parole))

# ---------------------------------------------------------------- le due fasi

CRESCITA_PRIMA = """Sei il Responsabile crescita di Zampe d'Italia (pagina Instagram: ogni animale accende una luce nella sua città sulla mappa dell'Italia di notte).
Il lavoro dell'agenzia ha un obiettivo: nuovi follower. Prima del montaggio, sul brief di questo reel proponi: il pubblico da raggiungere (chi è, concreto),
il gancio dei primi 2 secondi per chi NON conosce il progetto, il motivo per cui quella persona dovrebbe seguire Zampe d'Italia (una frase che regge da sola),
e la frase di chiusura che lega la storia al prossimo episodio (massimo 14 parole, per esempio «Atri si è accesa. Segui Zampe d'Italia per vedere la prossima luce.»).
Non promettere tempi o premi che non sono nel brief. Rispondi solo JSON: {"pubblico": "...", "gancio": "...", "motivo_per_seguire": "...", "chiusura": "...", "perche": "una frase"}"""

DIR_PRIMA = """Sei il Direttore video di Zampe d'Italia, pagina Instagram italiana: ogni animale accende una luce nella sua città sulla mappa dell'Italia di notte.
Ricevi il brief del reel e i dati verificati della mappa. Prima del montaggio scegli: l'apertura (il video vero di un animale per i primi secondi: tenerlo e quanto),
l'inquadratura della mappa (zoom tra 0.8 e 2.4: più alto = più vicino al comune) e il momento in cui la luce si accende nella scena della mappa (frazione della scena tra 0.2 e 0.7).
Chi guarda deve capire il gioco nei primi 5 secondi. Il reparto Crescita ti propone pubblico, gancio, motivo per seguire e chiusura («proposta_crescita»):
verifica che il motivo per seguire si capisca anche per chi vede il progetto per la prima volta; se no, riscrivilo tu. Rispondi solo JSON:
{"apertura": {"usa_video": true/false, "secondi": 2.5-4.5, "perche": "..."}, "zoom": 0.8-2.4, "accensione": 0.2-0.7,
 "crescita": {"motivo_chiaro_per_chi_non_ci_conosce": true/false, "motivo_per_seguire": "quello approvato o riscritto", "gancio": "...", "chiusura": "massimo 14 parole"},
 "note_per_il_montaggio": ["..."], "decisione": "una frase"}"""

DIR_DOPO = """Sei il Direttore video di Zampe d'Italia e rispondi della qualità. Ricevi i fotogrammi del reel esportato (ogni immagine ha il suo secondo), la trascrizione con i tempi,
i dati verificati della mappa e le misure audio. Controlla: realismo (niente che sembri finto o sbagliato), chiarezza nei primi 5 secondi (si capisce che ogni animale accende una luce nella sua città?),
leggibilità da telefono (testi grandi, contrasto, niente testo tagliato), corrispondenza tra animale, comune e luce (l'etichetta e il punto acceso devono essere il comune e l'animale veri),
e audio (voce chiara, musica sotto la voce, -14 LUFS circa, niente silenzi lunghi). Hai anche le relazioni dei reparti dell'ufficio («relazioni_reparti»): tienine conto, ma decidi tu.
Approva solo se non ci sono difetti che un utente noterebbe.
Rispondi solo JSON: {"approvato": true/false, "difetti": [{"secondo": 3.0, "area": "realismo|primi5s|leggibilita|corrispondenza|audio", "problema": "...", "correzione": "..."}], "decisione": "una frase"}"""

CLA_SQUADRA = """Sei Claude, il montatore di Zampe d'Italia. Ricevi le decisioni dei capi reparto sul reel. Correggi SOLO i difetti segnalati da almeno 3 reparti diversi
(lo stesso problema detto con parole diverse conta come uno) e solo se sono veri guardando il brief, i dati della mappa coi secondi e le misure audio. Non correggere dubbi, lacune di dati o gusti.
Azioni possibili: {"azione": "zoom", "scena": i, "valore": 0.8-2.4} · {"azione": "accensione", "scena": i, "valore": 0.2-0.7} · {"azione": "etichetta", "scena": i, "punto": j, "testo": "..."}
· {"azione": "frase", "scena": i, "testo": "..."} (stesso senso, al massimo 14 parole) · {"azione": "intro", "secondi": 0-4.5} · {"azione": "musica", "volume": 0.08-0.4} · {"azione": "fascia", "testo": "..."}
· {"azione": "didascalia_togli", "testo": "frase esatta da togliere"}.
Rispondi solo JSON: {"azioni": [...], "perche": [{"difetto": "...", "reparti": ["..."]}], "messaggio": "cosa correggi e perché, una o due frasi"}"""

CLA_CORR = """Sei Claude, il montatore di Zampe d'Italia. Il Direttore video ha trovato dei difetti. Traducili in azioni che il montaggio automatico sa fare; se un difetto non si può correggere con queste azioni, dillo.
Azioni possibili: {"azione": "zoom", "scena": i, "valore": 0.8-2.4} · {"azione": "accensione", "scena": i, "valore": 0.2-0.7} · {"azione": "etichetta", "scena": i, "punto": j, "testo": "..."}
· {"azione": "frase", "scena": i, "testo": "..."} (stesso senso, al massimo 14 parole) · {"azione": "intro", "secondi": 0-4.5} (0 = senza apertura) · {"azione": "musica", "volume": 0.08-0.4}
· {"azione": "fascia", "testo": "..."}. Rispondi solo JSON: {"azioni": [...], "non_correggibili": ["..."], "messaggio_al_direttore": "cosa hai cambiato, in una o due frasi"}"""

def _brief(cop):
    return {"formato": cop.get("formato"), "id": cop.get("id"), "frasi": [{"i": i, "testo": f["testo"], "scena": f["scena"]["tipo"]} for i, f in enumerate(cop["frasi"])],
            "apertura": cop.get("intro"), "fascia": cop.get("banner"), "didascalia": cop.get("didascalia", "")[:600], "voce": cop.get("voce"), "copertina": cop.get("copertina")}

def applica(cop, azioni):
    fatte = []
    for a in azioni or []:
        try:
            t = a.get("azione"); sc = cop["frasi"][int(a["scena"])]["scena"] if "scena" in a else None
            if t == "zoom" and sc and sc["tipo"] == "luce": sc["s1"] = max(0.8, min(2.4, float(a["valore"])))
            elif t == "accensione" and sc and sc["tipo"] == "luce": sc["accendi"] = max(0.2, min(0.7, float(a["valore"])))
            elif t == "etichetta" and sc and sc["tipo"] == "luce": sc["punti"][int(a["punto"])]["testo"] = str(a["testo"])[:40]
            elif t == "frase" and sc is not None and len(str(a["testo"]).split()) <= 14: cop["frasi"][int(a["scena"])]["testo"] = str(a["testo"])
            elif t == "intro":
                if float(a["secondi"]) <= 0: cop.pop("intro", None)
                else: cop["intro_durata"] = max(2.0, min(4.5, float(a["secondi"])))
            elif t == "musica": cop["vol_musica"] = max(0.08, min(0.4, float(a["volume"])))
            elif t == "fascia": cop["banner"] = str(a["testo"])[:70]
            elif t == "didascalia_togli" and str(a["testo"]) in cop.get("didascalia", ""): cop["didascalia"] = cop["didascalia"].replace(str(a["testo"]), "").replace("  ", " ")
            else: continue
            fatte.append(a)
        except (KeyError, ValueError, IndexError, TypeError):
            continue
    return fatte

def prima(cop_path):
    cop = json.loads(Path(cop_path).read_text())
    S = Sessione(cop["id"], cop.get("formato"))
    S.scrivi("montaggio-1", "crescita-1", "proposta", "Brief del reel prima del montaggio: chi vogliamo far diventare follower, con quale gancio e perché?", {"brief": _brief(cop)})
    indic = json.loads((DATI / "crescita.json").read_text()) if (DATI / "crescita.json").exists() else None
    cr, _ = lavora(CRESCITA_PRIMA, json.dumps({"brief": _brief(cop), "progetto": progetto_in_breve(), "indicazione_del_giorno": indic}, ensure_ascii=False), CLAUDE)
    if cr:
        S.scrivi("crescita-1", "direzione-1", "proposta", f"Pubblico: {cr.get('pubblico', '')} · Gancio: {cr.get('gancio', '')} · Motivo per seguire: {cr.get('motivo_per_seguire', '')} · Chiusura: {cr.get('chiusura', '')}", cr)
        S.d["crescita"] = cr
    S.scrivi("montaggio-1", "direzione-1", "proposta", "Brief del reel prima del montaggio: scegli apertura, inquadratura e momento della luce, e verifica il motivo per seguire.", {"brief": _brief(cop), "mappa": dati_mappa(cop)})
    r, chi = openai(DIR_PRIMA, json.dumps({"brief": _brief(cop), "dati_mappa": dati_mappa(cop), "proposta_crescita": cr}, ensure_ascii=False))
    if r is None:
        S.scrivi("direzione-1", "montaggio-1", "nota", f"Direttore video non collegato ({chi}): il montaggio parte con le scelte del copione."); return
    S.d["direttore_modello"] = chi
    S.scrivi("direzione-1", "montaggio-1", "risposta", r.get("decisione", "Scelte fatte."), r)
    vc = r.get("crescita") or {}
    if vc.get("chiusura") and len(vc["chiusura"].split()) <= 14 and cop["frasi"]:  # la chiusura verificata dal Direttore lega la storia al prossimo episodio
        cop["frasi"][-1]["testo"] = vc["chiusura"]
    if vc.get("motivo_per_seguire"):
        cop["didascalia"] = cop.get("didascalia", "").rstrip() + f"\n➕ {vc['motivo_per_seguire']}"
    S.scrivi("direzione-1", "crescita-1", "decisione", ("Motivo per seguire chiaro anche per chi non ci conosce." if vc.get("motivo_chiaro_per_chi_non_ci_conosce") else "Motivo per seguire riscritto dal Direttore.") + f" «{vc.get('motivo_per_seguire', '')}»", vc)
    ap = r.get("apertura") or {}
    if cop.get("intro") and ap.get("usa_video") is False: cop.pop("intro", None)
    elif cop.get("intro") and ap.get("secondi"): cop["intro_durata"] = max(2.0, min(4.5, float(ap["secondi"])))
    for f in cop["frasi"]:
        if f["scena"]["tipo"] == "luce":
            if r.get("zoom"): f["scena"]["s1"] = max(0.8, min(2.4, float(r["zoom"])))
            if r.get("accensione") and not f["scena"].get("vicino"): f["scena"]["accendi"] = max(0.2, min(0.7, float(r["accensione"])))
    Path(cop_path).write_text(json.dumps(cop, ensure_ascii=False))
    S.scrivi("montaggio-1", "direzione-1", "decisione", "Montaggio avviato con le scelte del Direttore.", {"apertura": cop.get("intro"), "intro_durata": cop.get("intro_durata")})

def revisione(cop_path, cartella, giro):
    cop = json.loads(Path(cop_path).read_text()); giro = int(giro)
    S = Sessione(cop["id"], cop.get("formato"))
    mp4 = Path(cartella) / "reel.mp4"
    dur, foto = fotogrammi(mp4, cartella, giro, cop["id"])
    au = audio(mp4)
    S.d["versioni"] = [v for v in S.d["versioni"] if v["v"] != giro] + [{"v": giro, "durata": round(dur, 1), "fotogrammi": [f"fotogrammi/{cop['id']}/v{giro}/{f.name}" for _, f in foto], "audio": au}]
    S.scrivi("audio-1", "direzione-1", "proposta", f"Controllo audio della versione {giro}: {au['lufs']} LUFS, picco {au['picco_dbfs']} dBFS, silenzi {au['silenzi_s'] or 'nessuno'}.", au)
    mat = {"versione": giro, "durata_s": round(dur, 1), "trascrizione": trascrizione(cartella, cop), "dati_mappa": dati_mappa(cop, cartella), "audio": au, "brief": _brief(cop),
           "fotogrammi_secondi": [s for s, _ in foto]}
    S.scrivi("montaggio-1", "direzione-1", "proposta", f"Versione {giro} esportata ({dur:.1f} s): ti mando {len(foto)} fotogrammi coi secondi, trascrizione, dati della mappa e audio.",
             {k: mat[k] for k in ("durata_s", "fotogrammi_secondi")})
    if giro == 1:  # l'ufficio al completo lavora sulla prima versione; le decisioni dei reparti vanno al Direttore
        mat["relazioni_reparti"] = ufficio_al_lavoro(S, mat, foto)
    r, chi = openai(DIR_DOPO, json.dumps(mat, ensure_ascii=False), [f.read_bytes() for _, f in foto])
    if r is None and giro == 1 and mat.get("relazioni_reparti"):  # niente Direttore: decide la squadra, a maggioranza di reparti
        c = claude(CLA_SQUADRA, json.dumps({"brief": _brief(cop), "decisioni_reparti": mat["relazioni_reparti"], "dati_mappa": mat["dati_mappa"], "audio": au}, ensure_ascii=False)) or {}
        fatte = applica(cop, c.get("azioni"))
        if fatte:
            Path(cop_path).write_text(json.dumps(cop, ensure_ascii=False))
            S.scrivi("montaggio-1", "pubblicazione-1", "correzione", f"Correzione di squadra (Direttore non collegato): {c.get('messaggio', '')}", {"azioni": fatte, "perche": c.get("perche", [])})
            return 10
        S.scrivi("montaggio-1", "pubblicazione-1", "decisione", "La squadra non ha trovato difetti segnalati da almeno 3 reparti: nessuna correzione.", {"perche": c.get("perche", [])})
    if r is None:
        print(f"agenzia: Direttore video non raggiungibile ({chi})", file=sys.stderr)
        corretto = any(x["testo"].startswith("Correzione di squadra") for x in S.d["scambi"])
        S.scrivi("direzione-1", "pubblicazione-1", "nota", f"Direttore video non collegato ({chi}): " + ("esce la versione corretta dalla squadra." if corretto else "il reel esce con la revisione della sola squadra."))
        S.d["stato"] = "corretto dalla squadra" if corretto else "senza direttore"; S.d["fine"] = _ora(); S.salva(); return 0
    S.d["direttore_modello"] = chi
    difetti = r.get("difetti") or []
    S.scrivi("direzione-1", "montaggio-1", "risposta", r.get("decisione") or ("Approvato." if r.get("approvato") else "Da correggere."), {"approvato": bool(r.get("approvato")), "difetti": difetti})
    if r.get("approvato") and not difetti:
        S.scrivi("direzione-1", "pubblicazione-1", "decisione", f"Approvata la versione {giro}: si pubblica una volta sola.")
        S.d["stato"] = "approvato"; S.d["approvata"] = giro; S.d["fine"] = _ora(); S.salva(); return 0
    if giro >= MAX_REVISIONI:
        S.scrivi("direzione-1", "pubblicazione-1", "decisione", f"Dopo {giro} revisioni restano difetti: il reel resta in bozza e parte quello di riserva.", {"difetti": difetti})
        S.d["stato"] = "bozza"; S.d["fine"] = _ora(); S.salva(); return 20
    c = claude(CLA_CORR, json.dumps({"brief": _brief(cop), "difetti": difetti, "dati_mappa": dati_mappa(cop, cartella), "relazioni_reparti": mat.get("relazioni_reparti", [])[:6]}, ensure_ascii=False)) or {"azioni": [], "messaggio_al_direttore": "Claude non ha risposto."}
    fatte = applica(cop, c.get("azioni"))
    Path(cop_path).write_text(json.dumps(cop, ensure_ascii=False))
    S.scrivi("montaggio-1", "direzione-1", "correzione", c.get("messaggio_al_direttore") or f"Applicate {len(fatte)} correzioni.", {"azioni": fatte, "non_correggibili": c.get("non_correggibili", [])})
    if not fatte:
        S.scrivi("montaggio-1", "pubblicazione-1", "decisione", "Nessuna correzione applicabile: il reel resta in bozza e parte quello di riserva.")
        S.d["stato"] = "bozza"; S.d["fine"] = _ora(); S.salva(); return 20
    return 10

CRESCITA_GIORNO = """Sei «{ruolo}» nel reparto Crescita di Zampe d'Italia: l'obiettivo è portare nuovi follower. Ricevi i numeri veri degli ultimi reel
(account raggiunti, commenti, condivisioni, follower arrivati dopo ciascuno e ogni 1.000 account, quando ci sono; «null» vuol dire dato non disponibile), le loro scelte creative
(apertura, gancio, chiusura) e i verbali dei 7 giorni. Dal punto di vista della tua mansione proponi cosa provare domani. Non inventare numeri.
Rispondi solo JSON: {{"osservazione": "cosa dicono i numeri, con il dato", "proposta": "cosa provare domani", "gancio": "primi 2 secondi, se lo proponi"}}"""

CRESCITA_CAPO = """Sei il Responsabile crescita di Zampe d'Italia. Leggi le proposte delle tue 9 persone e decidi l'indicazione per i reel di domani.
Rispondi solo JSON: {"pubblico": "...", "gancio": "...", "motivo_per_seguire": "...", "chiusura": "massimo 14 parole", "da_riprovare": "...", "da_evitare": "...", "dato": "su quale numero ti basi"}"""

def crescita_giorno():
    """Ogni mattina (rendimento.yml) la Crescita legge i numeri e lascia l'indicazione per i reel di domani: docs/data/agenzia/crescita.json.
    Il reparto la usa prima del montaggio di ogni reel (fase «prima»)."""
    from concurrent.futures import ThreadPoolExecutor
    R = [x for x in json.loads((ROOT / "motore/rendimento.json").read_text()) if not x.get("sponsorizzato")][-12:]
    righe = []
    for x in R:
        c = {}
        if x.get("file") and (ROOT / f"docs/contenuti/auto/{x['file']}.json").exists():
            cp = json.loads((ROOT / f"docs/contenuti/auto/{x['file']}.json").read_text()); fr = cp.get("frasi", [])
            c = {"apertura": "video vero" if cp.get("intro") else "mappa", "gancio": fr[0]["testo"] if fr else None, "chiusura": fr[-1]["testo"] if fr else None}
        righe.append({k: x.get(k) for k in ("quando", "formato", "views", "reach", "comments", "shares", "follower_dopo", "follower_ogni_1000")} | c)
    ver = json.loads((DATI / "verbali.json").read_text())[-10:] if (DATI / "verbali.json").exists() else []
    testo = json.dumps({"reel": righe, "verbali_7_giorni": ver, "progetto": progetto_in_breve()}, ensure_ascii=False)[:24000]
    oggi = datetime.now(timezone.utc).date().isoformat()
    if (DATI / f"sessioni/crescita-{oggi}.json").exists(): return  # una volta al giorno
    S = Sessione(f"crescita-{oggi}", "crescita del giorno")
    S.scrivi("crescita-10", "crescita-1", "nota", "Si parte dai numeri veri degli ultimi 12 reel organici e dai verbali dei 7 giorni.")
    pers = ufficio_reparto("crescita")[1:]
    rel = []
    with ThreadPoolExecutor(4) as ex:
        for p, (r, t) in zip(pers, ex.map(lambda p: lavora(CRESCITA_GIORNO.format(ruolo=p["ruolo"]), testo), pers)):
            S.d["token_persone"] = S.d.get("token_persone", 0) + t
            if r: rel.append({"ruolo": p["ruolo"], **r}); S.d["scambi"].append({"t": _ora(), "da": p["id"], "a": "crescita-1", "tipo": "proposta", "testo": f"{r.get('osservazione', '')} → {r.get('proposta', '')}"[:400], "dati": r})
    d, t = lavora(CRESCITA_CAPO, json.dumps(rel, ensure_ascii=False), CLAUDE)
    S.d["token_persone"] = S.d.get("token_persone", 0) + t
    if d:
        S.scrivi("crescita-1", "direzione-1", "decisione", f"Per domani: gancio «{d.get('gancio', '')}», chiusura «{d.get('chiusura', '')}». Dato: {d.get('dato', '')}", d)
        (DATI / "crescita.json").write_text(json.dumps({"giorno": oggi, **d}, ensure_ascii=False, indent=1) + "\n")
    S.d["stato"] = "fatto"; S.d["fine"] = _ora(); S.salva()

INNOVA = """Sei «{ruolo}» nel reparto Innovazione di Zampe d'Italia (pagina Instagram: ogni animale accende una luce nella sua città sulla mappa dell'Italia di notte;
c'è un sito con la mappa, i minigiochi e la Coppa delle Zampe tra comuni; i reel escono 3 volte al giorno). Il reparto ha tre compiti (Alberto, 8/11):
1) «gioco»: giochi NUOVI che servono davvero (portano gente a giocare, a tornare, a commentare e a seguire);
2) «reel»: far evolvere i reel in modo DIVERSO da quelli di oggi (non un'altra mappa con una luce: altro stile, ripresa, montaggio, racconto, suono);
3) «realismo»: rendere il gioco sempre più realistico (animali, paesi, mappa, 3D sul sito).
Dal punto di vista della tua mansione proponi UNA idea in UNA di queste tre tracce. Parti da quello che esiste (te lo diamo) e dai numeri veri; niente cose già fatte,
niente spese, niente follower finti, niente nomi di altre pagine, e solo cose che si possono fare col codice e i materiali che abbiamo (disegni SVG, three.js, mappa reale, foto e video dei follower col loro SÌ).
Rispondi solo JSON: {{"traccia": "gioco|reel|realismo", "idea": "nome breve", "come_funziona": "2-3 frasi", "perche_porta_follower": "...", "perche_e_bella": "...",
 "cosa_serve": "file e materiali che abbiamo", "come_misurarla": "quale numero guardare dopo 7 giorni"}}"""

INNOVA_CAPO = """Sei il Capo innovazione di Zampe d'Italia. Leggi le idee delle tue persone e scegli UNA idea per ciascuna traccia: «gioco» (un gioco nuovo che serve),
«reel» (un modo diverso di fare i reel), «realismo» (un passo per rendere il gioco più realistico). Per ognuna: quella che porta più follower, è bella e si può fare subito
con quello che abbiamo, con il primo passo tecnico concreto. Rispondi solo JSON:
{"gioco": {"idea": "...", "come_funziona": "...", "primo_passo": "...", "come_misurarla": "..."}, "reel": {...stessi campi}, "realismo": {...stessi campi}, "perche": "una frase"}"""

TRACCIA = {"Giochi nuovi": "gioco", "Meccaniche di gioco": "gioco", "Fattibilità tecnica": "gioco", "Realismo degli animali": "realismo",
           "Realismo della mappa e del 3D": "realismo", **{r: "realismo" for r in REPARTI[-1][2][1:]}, "Esperimenti misurabili": "realismo", "Nuovi stili di reel": "reel", "Riprese e montaggio diversi": "reel", "Suono e musica nuovi": "reel"}

INNOVA_PASSO = """Sei «{ruolo}» nel reparto Innovazione di Zampe d'Italia. La tua traccia «{traccia}» ha un CANTIERE aperto (lo trovi sotto): un'idea già scelta
che va messa online entro la scadenza. Niente idee nuove: scrivi il PROSSIMO passo concreto per finirla, dal punto di vista della tua mansione,
usando solo file e materiali che esistono (sito in docs/, motore in motore/, reel in reel/), senza spese e senza follower finti. Se il cantiere è in ritardo, proponi come tagliarlo
per uscire domani con una versione più piccola ma bella. Rispondi solo JSON: {{"passo": "cosa fare, 1-2 frasi", "file": ["percorsi"], "fatto_quando": "come si vede che è finito"}}"""

def cantieri():
    f = DATI / "cantieri.json"
    return json.loads(f.read_text()) if f.exists() else {}

def salva_cantieri(c):
    DATI.mkdir(parents=True, exist_ok=True)
    for v in c.values(): v["passi_proposti"] = (v.get("passi_proposti") or [])[-12:]
    (DATI / "cantieri.json").write_text(json.dumps(c, ensure_ascii=False, indent=1) + "\n")

def innovazione_giorno():
    """Ogni mattina (rendimento.yml) l'Innovazione inventa: 9 idee, il capo ne sceglie una da provare (docs/data/agenzia/innovazione.json).
    Il controllo quotidiano la legge e, se è fattibile e rispetta le regole, la mette in produzione (una novità alla volta)."""
    from concurrent.futures import ThreadPoolExecutor
    esiste = {"formati_reel": sorted({x.get("formato") for x in json.loads((ROOT / "motore/rendimento.json").read_text())}),
              "giochi_sito": ["Zampe di corsa (corsa a ostacoli)", "Pappa al volo (prendi il cibo giusto)", "Riporta il bastone (lancio a tempo)", "Coppa delle Zampe (Luce Misteriosa, Indovina la Zampa, Staffetta)"],
              "stili_reel_oggi": ["mappa dell'Italia di notte che scende su un comune e una luce che si accende", "apertura col video di Thor", "classifiche e duelli disegnati", "cucce e gatti disegnati in SVG", "voce sintetica e musica"],
              "realismo_oggi": ["mappa con rilievo e coste vere (dati di altitudine)", "animali disegnati in SVG per razza", "paesi disegnati da vicino", "una vista 3D del paese (three.js)"],
              "eventi_fatti": ["Re degli animali d'Italia", "fuochi a 2.000 follower", "star del giorno con foto dei follower", "porta 2 amici"],
              "progetto": progetto_in_breve(), "indicazione_crescita": json.loads((DATI / "crescita.json").read_text()) if (DATI / "crescita.json").exists() else None,
              "idee_gia_proposte": [y.get("idea") for x in (json.loads((DATI / "innovazione.json").read_text()) if (DATI / "innovazione.json").exists() else []) for y in [x.get(k) or {} for k in ("scelta", "gioco", "reel", "realismo")] if y.get("idea")][-30:]}
    oggi = datetime.now(timezone.utc).date().isoformat()
    if (DATI / f"sessioni/innovazione-{oggi}.json").exists(): return  # una volta al giorno
    # 8/11 Alberto: «l'innovazione deve accelerare». Ogni idea scelta apre un CANTIERE con scadenza 48 ore: finché è aperto,
    # quella traccia non sceglie altre idee, e le 3 persone della traccia scrivono i passi per finirlo (il cantiere delle 14 lo costruisce).
    can = cantieri()
    aperti = {k: v for k, v in can.items() if v.get("stato") in ("da costruire", "in costruzione")}
    for v in aperti.values():
        if v.get("scadenza", "9") < oggi: v["in_ritardo"] = True
    esiste["cantieri_aperti"] = aperti
    testo = json.dumps(esiste, ensure_ascii=False)[:20000]
    S = Sessione(f"innovazione-{oggi}", "innovazione del giorno")
    pers = ufficio_reparto("innovazione")[1:] + ufficio_reparto("grafica3d")[1:]  # la Grafica 3D lavora sulla traccia «realismo»
    idee = []
    with ThreadPoolExecutor(4) as ex:
        # 8/11: col solo invito sceglievano tutti «reel»; ogni mansione ha la sua traccia (3 gioco, 3 realismo, 3 reel)
        def compito(p):
            tr = TRACCIA.get(p["ruolo"], "reel")
            if p["id"].startswith("grafica3d") and tr not in aperti:  # idea di realismo in 3D, dal punto di vista della mansione
                return lavora(INNOVA.format(ruolo=p["ruolo"] + " (reparto Grafica 3D)") + "\nLa tua traccia è «realismo»: proponi un passo in 3D (three.js nel sito o una scena 3D nei reel), bello da vedere sul telefono.", testo)
            if tr in aperti: return lavora(INNOVA_PASSO.format(ruolo=p["ruolo"], traccia=tr), json.dumps(aperti[tr], ensure_ascii=False) + "\n\n" + testo)
            return lavora(INNOVA.format(ruolo=p["ruolo"]) + f"\nLa tua traccia è «{tr}»: proponi un'idea solo in questa traccia.", testo)
        for p, (r, t) in zip(pers, ex.map(compito, pers)):
            S.d["token_persone"] = S.d.get("token_persone", 0) + t
            if r and TRACCIA.get(p["ruolo"], "reel") in aperti:
                tr = TRACCIA.get(p["ruolo"], "reel"); aperti[tr].setdefault("passi_proposti", []).append({"giorno": oggi, "ruolo": p["ruolo"], **r})
                S.d["scambi"].append({"t": _ora(), "da": p["id"], "a": "innovazione-1", "tipo": "proposta", "testo": f"Cantiere «{aperti[tr].get('idea', '')}»: {r.get('passo', '')}"[:400], "dati": r}); continue
            if r: idee.append({"ruolo": p["ruolo"], **r}); S.d["scambi"].append({"t": _ora(), "da": p["id"], "a": "innovazione-1", "tipo": "proposta", "testo": f"{r.get('idea', '')}: {r.get('come_funziona', '')}"[:400], "dati": r})
    liberi = [k for k in ("gioco", "reel", "realismo") if k not in aperti]
    d, t = (lavora(INNOVA_CAPO + f"\nScegli SOLO per queste tracce (le altre hanno un cantiere aperto): {', '.join(liberi)}.", json.dumps(idee, ensure_ascii=False), CLAUDE) if liberi and idee else ({}, 0))
    S.d["token_persone"] = S.d.get("token_persone", 0) + t
    scad = (datetime.now(timezone.utc).date() + timedelta(days=2)).isoformat()
    for k in liberi:
        if (d or {}).get(k, {}).get("idea"): can[k] = {**d[k], "traccia": k, "aperto": oggi, "scadenza": scad, "stato": "da costruire"}
    salva_cantieri(can)
    if d:
        S.scrivi("innovazione-1", "direzione-1", "decisione", " · ".join(f"{k.upper()}: «{(d.get(k) or {}).get('idea', '')}» (primo passo: {(d.get(k) or {}).get('primo_passo', '')})" for k in ("gioco", "reel", "realismo")), d)
        reg = DATI / "innovazione.json"; storia = json.loads(reg.read_text()) if reg.exists() else []
        reg.write_text(json.dumps((storia + [{"giorno": oggi, **d}])[-60:], ensure_ascii=False, indent=1) + "\n")
    S.d["stato"] = "fatto"; S.d["fine"] = _ora(); S.salva()

if __name__ == "__main__":
    fase = sys.argv[1]
    if fase == "prima": prima(sys.argv[2])
    elif fase == "revisione": sys.exit(revisione(*sys.argv[2:5]))
    elif fase == "crescita": crescita_giorno()
    elif fase == "innovazione": innovazione_giorno()
    elif fase == "cantiere":  # agenzia.py cantiere <gioco|reel|realismo> <in costruzione|online|scartato> [dove si vede / perché]
        c = cantieri(); v = c[sys.argv[2]]; v["stato"] = sys.argv[3]; v["aggiornato"] = datetime.now(timezone.utc).date().isoformat()
        if len(sys.argv) > 4: v["nota"] = sys.argv[4]
        if sys.argv[3] == "online": v["online_dal"] = v["aggiornato"]
        salva_cantieri(c)
    elif fase == "ufficio": DATI.mkdir(parents=True, exist_ok=True); (DATI / "ufficio.json").write_text(json.dumps(ufficio(), ensure_ascii=False) + "\n")
