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
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATI = ROOT / "docs/data/agenzia"
FOTO = ROOT / "docs/agenzia/fotogrammi"
CONFIG = json.loads((ROOT / "motore/config.json").read_text())
MODELLI_OPENAI = CONFIG.get("openai_modelli", ["gpt-5", "gpt-4.1", "gpt-4o"])  # il primo che risponde
CLAUDE = "claude-sonnet-5-5"
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
    ("analisi", "Analisi e crescita", ["Analista capo", "Follower ogni 1.000 account", "Organico e sponsorizzato", "Views e commenti", "Visione media", "Orari migliori",
                                       "Confronto formati", "Registro decisioni", "Controllo quotidiano", "Concorrenza"]),
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
    body = {"model": CLAUDE, "max_tokens": 2000, "system": istruzioni, "messages": [{"role": "user", "content": contenuto}]}
    try:
        r = urllib.request.Request("https://api.anthropic.com/v1/messages", data=json.dumps(body).encode(),
                                   headers={"x-api-key": k, "anthropic-version": "2023-06-01", "content-type": "application/json"})
        t = next(b["text"] for b in json.loads(urllib.request.urlopen(r, timeout=120).read())["content"] if b.get("type") == "text")
        return _json(t)
    except Exception as e:
        print(f"agenzia: Claude non ha risposto ({type(e).__name__})", file=sys.stderr)
        return None

# ---------------------------------------------------------------- materiali per il Direttore

def dati_mappa(cop):
    """I dati verificati della mappa per le scene del reel: comune, coordinate, animale e @ veri (docs/data/animali.json)."""
    A = json.loads((ROOT / "docs/data/animali.json").read_text())["animali"]
    out = []
    for i, f in enumerate(cop["frasi"]):
        sc = f["scena"]
        for q in sc.get("punti", []):
            vicini = [a for a in A if a.get("k") == "animale" and abs(a.get("lat", 0) - q["lat"]) < 0.02 and abs(a.get("lng", 0) - q["lng"]) < 0.02]
            out.append({"scena": i, "etichetta": q.get("testo"), "lat": q["lat"], "lng": q["lng"], "si_accende_in_scena": not q.get("acceso", True),
                        "comune_sulla_mappa": vicini[0]["c"] if vicini else None, "animali_li": [f"{a['n']} (@{a['u']})" for a in vicini[:5]], "luci_li": len(vicini)})
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

DIR_PRIMA = """Sei il Direttore video di Zampe d'Italia, pagina Instagram italiana: ogni animale accende una luce nella sua città sulla mappa dell'Italia di notte.
Ricevi il brief del reel e i dati verificati della mappa. Prima del montaggio scegli: l'apertura (il video vero di un animale per i primi secondi: tenerlo e quanto),
l'inquadratura della mappa (zoom tra 0.8 e 2.4: più alto = più vicino al comune) e il momento in cui la luce si accende nella scena della mappa (frazione della scena tra 0.2 e 0.7).
Chi guarda deve capire il gioco nei primi 5 secondi. Rispondi solo JSON:
{"apertura": {"usa_video": true/false, "secondi": 2.5-4.5, "perche": "..."}, "zoom": 0.8-2.4, "accensione": 0.2-0.7, "note_per_il_montaggio": ["..."], "decisione": "una frase"}"""

DIR_DOPO = """Sei il Direttore video di Zampe d'Italia e rispondi della qualità. Ricevi i fotogrammi del reel esportato (ogni immagine ha il suo secondo), la trascrizione con i tempi,
i dati verificati della mappa e le misure audio. Controlla: realismo (niente che sembri finto o sbagliato), chiarezza nei primi 5 secondi (si capisce che ogni animale accende una luce nella sua città?),
leggibilità da telefono (testi grandi, contrasto, niente testo tagliato), corrispondenza tra animale, comune e luce (l'etichetta e il punto acceso devono essere il comune e l'animale veri),
e audio (voce chiara, musica sotto la voce, -14 LUFS circa, niente silenzi lunghi). Approva solo se non ci sono difetti che un utente noterebbe.
Rispondi solo JSON: {"approvato": true/false, "difetti": [{"secondo": 3.0, "area": "realismo|primi5s|leggibilita|corrispondenza|audio", "problema": "...", "correzione": "..."}], "decisione": "una frase"}"""

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
            else: continue
            fatte.append(a)
        except (KeyError, ValueError, IndexError, TypeError):
            continue
    return fatte

def prima(cop_path):
    cop = json.loads(Path(cop_path).read_text())
    S = Sessione(cop["id"], cop.get("formato"))
    S.scrivi("montaggio-1", "direzione-1", "proposta", "Brief del reel prima del montaggio: scegli apertura, inquadratura e momento della luce.", {"brief": _brief(cop), "mappa": dati_mappa(cop)})
    r, chi = openai(DIR_PRIMA, json.dumps({"brief": _brief(cop), "dati_mappa": dati_mappa(cop)}, ensure_ascii=False))
    if r is None:
        S.scrivi("direzione-1", "montaggio-1", "nota", f"Direttore video non collegato ({chi}): il montaggio parte con le scelte del copione."); return
    S.d["direttore_modello"] = chi
    S.scrivi("direzione-1", "montaggio-1", "risposta", r.get("decisione", "Scelte fatte."), r)
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
    mat = {"versione": giro, "durata_s": round(dur, 1), "trascrizione": trascrizione(cartella, cop), "dati_mappa": dati_mappa(cop), "audio": au, "brief": _brief(cop),
           "fotogrammi_secondi": [s for s, _ in foto]}
    S.scrivi("montaggio-1", "direzione-1", "proposta", f"Versione {giro} esportata ({dur:.1f} s): ti mando {len(foto)} fotogrammi coi secondi, trascrizione, dati della mappa e audio.",
             {k: mat[k] for k in ("durata_s", "fotogrammi_secondi")})
    r, chi = openai(DIR_DOPO, json.dumps(mat, ensure_ascii=False), [f.read_bytes() for _, f in foto])
    if r is None:
        S.scrivi("direzione-1", "pubblicazione-1", "nota", f"Direttore video non collegato ({chi}): il reel esce senza revisione, come prima.")
        S.d["stato"] = "senza direttore"; S.d["fine"] = _ora(); S.salva(); return 0
    S.d["direttore_modello"] = chi
    difetti = r.get("difetti") or []
    S.scrivi("direzione-1", "montaggio-1", "risposta", r.get("decisione") or ("Approvato." if r.get("approvato") else "Da correggere."), {"approvato": bool(r.get("approvato")), "difetti": difetti})
    if r.get("approvato") and not difetti:
        S.scrivi("direzione-1", "pubblicazione-1", "decisione", f"Approvata la versione {giro}: si pubblica una volta sola.")
        S.d["stato"] = "approvato"; S.d["approvata"] = giro; S.d["fine"] = _ora(); S.salva(); return 0
    if giro >= MAX_REVISIONI:
        S.scrivi("direzione-1", "pubblicazione-1", "decisione", f"Dopo {giro} revisioni restano difetti: il reel resta in bozza e parte quello di riserva.", {"difetti": difetti})
        S.d["stato"] = "bozza"; S.d["fine"] = _ora(); S.salva(); return 20
    c = claude(CLA_CORR, json.dumps({"brief": _brief(cop), "difetti": difetti, "dati_mappa": dati_mappa(cop)}, ensure_ascii=False)) or {"azioni": [], "messaggio_al_direttore": "Claude non ha risposto."}
    fatte = applica(cop, c.get("azioni"))
    Path(cop_path).write_text(json.dumps(cop, ensure_ascii=False))
    S.scrivi("montaggio-1", "direzione-1", "correzione", c.get("messaggio_al_direttore") or f"Applicate {len(fatte)} correzioni.", {"azioni": fatte, "non_correggibili": c.get("non_correggibili", [])})
    if not fatte:
        S.scrivi("montaggio-1", "pubblicazione-1", "decisione", "Nessuna correzione applicabile: il reel resta in bozza e parte quello di riserva.")
        S.d["stato"] = "bozza"; S.d["fine"] = _ora(); S.salva(); return 20
    return 10

if __name__ == "__main__":
    fase = sys.argv[1]
    if fase == "prima": prima(sys.argv[2])
    elif fase == "revisione": sys.exit(revisione(*sys.argv[2:5]))
    elif fase == "ufficio": DATI.mkdir(parents=True, exist_ok=True); (DATI / "ufficio.json").write_text(json.dumps(ufficio(), ensure_ascii=False) + "\n")
