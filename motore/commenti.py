"""Motore dei commenti di Zampe d'Italia.

Legge i commenti dei reel recenti (Instagram API with Instagram Login), riconosce i formati del gioco,
aggiorna docs/data/animali.json e risponde secondo le regole del piano.

Uso:
  python motore/commenti.py                 # gira davvero (serve IG_TOKEN nell'ambiente)
  python motore/commenti.py --prova FILE    # legge commenti finti da un JSON e stampa le risposte, senza Instagram
  python motore/commenti.py --ricostruisci [--a-secco]   # rilegge tutti i commenti con Claude e rifà la mappa

I commenti li legge Claude (motore/lettore.py), tutti quelli di una persona insieme; il codice controlla ogni dato.

Solo libreria standard, così gira su GitHub Actions senza installare niente.
"""
import json, os, random, re, sys, time, unicodedata, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
from math import cos, radians, sqrt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lettore

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(os.environ.get("ZAMPE_OUT", ROOT))  # le prove scrivono altrove, mai sulla mappa vera
ANIMALI = OUT / "docs/data/animali.json"
STATO = OUT / "motore/stato.json"
COMUNI = ROOT / "dati/comuni_min.json"
API = "https://graph.instagram.com/v23.0"

GIORNI_REEL = 7            # si leggono i commenti dei reel pubblicati negli ultimi 7 giorni
QUOTA_RISPOSTE = 0.30      # agli altri si risponde a campione
MAX_RISPOSTE_ORA = 200
MAX_ANIMALI_PER_UTENTE = 5
SOGLIA_ALTRI = 15  # con 15 luci gli altri animali entrano nella sfida: Cani contro Gatti contro Altri (anche in copione.py)
PUNTI = {"animale": 10, "fondatore": 20, "tifo": 5, "sogno": 10, "stella": 0, "giornaliero": 5, "tag": 3, "segue": 10}

# ---------- testo ----------
def norm(s):
    s = unicodedata.normalize("NFD", str(s).lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9' ]", " ", s.replace("’", "'"))).strip()

def nome_proprio(s):
    s = re.sub(r"[^\w' -]", "", s, flags=re.UNICODE).strip()
    return " ".join(w[:1].upper() + w[1:] for w in s.split())[:24]

# ---------- comuni ----------
# Quartieri e nomi comuni che non coincidono col nome ufficiale del comune.
ALIAS = {"mestre": "venezia", "marghera": "venezia", "lido di venezia": "venezia", "ostia": "roma",
         "reggio calabria": "reggio di calabria", "reggio emilia": "reggio nell'emilia", "bozen": "bolzano",
         "pesaro urbino": "pesaro", "forli cesena": "forli", "monza brianza": "monza", "la spezia": "la spezia",
         "aquila": "l'aquila", "laquila": "l'aquila"}

class Comuni:
    def __init__(self, path=COMUNI):
        self.per_nome = {}
        for c, p, r, lat, lng in json.loads(Path(path).read_text()):
            self.per_nome.setdefault(norm(c), []).append({"c": c, "p": p, "r": r, "lat": lat, "lng": lng})
        self.province = {x["p"] for v in self.per_nome.values() for x in v}

    def in_mezzo(self, testo):
        """Frasi libere: un comune dopo "a", "di", "da", "in" ("vive a Bari"). Restituisce (comune, frase senza il comune)."""
        w = norm(testo).split()
        for i, x in enumerate(w):
            if x in ("a", "di", "da", "in", "citta", "comune", "paese") and i + 1 < len(w):
                for n in range(min(5, len(w) - i - 1), 0, -1):
                    c, _ = self.trova(" ".join(w[i + 1:i + 1 + n]))
                    if c:
                        return c, " ".join(w[:i] + w[i + 1 + n:])
        return None, testo

    def in_testa(self, testo):
        """Per i commenti senza virgole: cerca il comune più lungo all'inizio o alla fine ("Treviso Luna golden")."""
        w = norm(testo).split()
        for n in range(min(6, len(w) - 1), 0, -1):
            for parte, resto in ((w[:n], w[n:]), (w[-n:], w[:-n])):
                c, _ = self.trova(" ".join(parte))
                if c:
                    return c, " ".join(resto)
        return None, testo

    def trova(self, testo):
        """Restituisce (comune, None) se trovato, (None, 'provincia') se omonimo senza provincia, (None, None) se sconosciuto."""
        t, prov = norm(testo), None
        m = re.match(r"^(.*\S)\s+([a-z]{2})$", t)  # "altivole tv" (le parentesi le toglie già norm)
        if m and m.group(2).upper() in self.province and ALIAS.get(m.group(1), m.group(1)) in self.per_nome:
            t, prov = m.group(1), m.group(2).upper()
        t = ALIAS.get(t, t)
        lista = self.per_nome.get(t) or self.per_nome.get(t.replace("'", " ")) or self.per_nome.get(t.replace(" ", "'"))
        if not lista:
            return None, None
        if prov:
            lista = [x for x in lista if x["p"] == prov] or lista
        if len(lista) > 1:
            return None, "provincia"
        return lista[0], None

# ---------- razze ----------
# Elenco unico in docs/data/razze.json, lo stesso che usa la mappa: vince il sinonimo più lungo trovato come parola intera.
GATTO_PAROLE = re.compile(r"\b(gatt[oaie]|micio|micia|micetto|micetta|gattino|gattina)\b")
_RAZZE = json.loads((ROOT / "docs/data/razze.json").read_text())
TABELLA = sorted(
    [{"sin": norm(x), "key": r[0], "tipo": "cane", "colore": False} for r in _RAZZE["cani"] for x in r[2]] +
    [{"sin": norm(x), "key": r[0], "tipo": "gatto", "colore": "colore" in r[5].split()} for r in _RAZZE["gatti"] for x in r[2]],
    key=lambda r: -len(r["sin"]))

def cerca_razza(testo, tipo=None):
    t = " " + norm(testo).replace("'", " ") + " "
    return next((r for r in TABELLA if (not tipo or r["tipo"] == tipo) and f" {r['sin']} " in t), None)

def tipo_animale(descr):
    """Cane o gatto? Le parole "gatto/micio" decidono; poi la razza più lunga; i soli colori non bastano per dire gatto."""
    if GATTO_PAROLE.search(norm(descr)):
        return "gatto"
    g, c = cerca_razza(descr, "gatto"), cerca_razza(descr, "cane")
    if g and not g["colore"] and (not c or len(g["sin"]) > len(c["sin"])):
        return "gatto"
    return "cane"

def razza(testo, tipo):
    r = cerca_razza(testo, tipo)
    return r["key"] if r else None

# parole che non sono mai il nome dell'animale
RIEMPITIVE = {"due", "tre", "quattro", "cinque", "i", "le", "gli", "con", "citta", "città", "vivo", "viviamo", "abito", "abitiamo", "nostri", "tuoi", "loro", "allora", "ciao", "ecco", "io", "sono", "ho", "il", "lo", "la", "mio", "mia", "miei", "mie", "si", "chiama", "vive", "abita", "a", "in", "di", "da",
              "ed", "e", "è", "un", "una", "uno", "che", "anche", "noi", "abbiamo", "nostro", "nostra", "zampeditalia", "qui", "sta", "ce", "c"}

def descrittiva(t):
    n = norm(t)
    return bool(re.search(r"\b(gatt[oaie]|gattin[oa]|cane|cana|cani|cagnolin[oa]|cucciol[oa]|razza)\b", n) or cerca_razza(n))

def inizia_descrizione(ws, i):
    """La parola i è l'inizio della razza o del tipo d'animale? ("pastore tedesco", "gatto rosso", "golden")"""
    w = norm(ws[i])
    if re.fullmatch(r"gatt[oaie]|gattin[oa]|cane|cana|cani|cagnolin[oa]|cucciol[oa]|razza", w):
        return True
    coda = " " + norm(" ".join(ws[i:i + 4])) + " "
    return any(coda.startswith(" " + r["sin"] + " ") for r in TABELLA if len(r["sin"]) > 2)

REGIONI = ["friuli venezia giulia", "friuli", "trentino alto adige", "trentino", "alto adige", "valle d'aosta", "emilia romagna", "emilia-romagna",
           "piemonte", "lombardia", "veneto", "liguria", "toscana", "umbria", "marche", "lazio", "abruzzo", "molise", "campania", "puglia",
           "basilicata", "calabria", "sicilia", "sardegna", "regione", "provincia"]

def senza_regioni(t):
    for r in REGIONI:
        t = re.sub(r"(?i)(?<![\w'])" + re.escape(r).replace("\\-", "[- ]").replace("\\ ", "[ -]") + r"(?![\w])", " ", t)
    return re.sub(r"\s+", " ", t).strip()

TIPI_RE = r"(cane|cana|cani|cagnolin[oa]|cucciol[oa]|gatt[oaie]|gattin[oaie]|micio|micia)"

def piu_animali(raw, comuni):
    """"Il mio cane Mia, i miei gatti Tigro e Tempesta, vivo a Reggio Emilia" → più animali nello stesso comune."""
    c, _ = comuni.in_mezzo(raw)
    if not c:
        for p in re.split(r"[,;.\n]", raw):
            c, _ = comuni.trova(p.strip()) if p.strip() else (None, None)
            if c: break
    if not c:
        return None
    trovati = []
    for seg in re.split(r"[,;.\n]", raw):
        m = re.search(r"(?i)\b" + TIPI_RE + r"\b(.*)", seg)
        if not m: continue
        t = "gatto" if norm(m.group(1)).startswith(("gatt", "mic")) else "cane"
        dopo = re.sub(r"(?i)\bsi chiam\w*\b", " ", m.group(2))
        parole = re.findall(r"[A-Za-zÀ-ÿ']+", dopo)
        # un nome è una parola con la maiuscola dopo "cane"/"gatto" che non sia il comune né la razza
        nomi = [w for w in parole if w[0].isupper() and w not in ("E", "Si", "Il", "La", "I", "Lo", "Le", "Gli", "Un", "Una")
                and norm(w) not in norm(c["c"]).split() and not descrittiva(w) and not inizia_descrizione([w], 0)]
        descr = " ".join(w for w in parole if descrittiva(w) or inizia_descrizione([w], 0))
        for n in nomi[:4]:
            trovati.append({"n": nome_proprio(n), "t": t, "razza": razza(descr, t) or ("europeo" if t == "gatto" else "meticcio"), "razza_testo": (descr or t)[:40]})
    return {"k": "multi", "luogo": c, "animali": trovati} if len(trovati) >= 2 else None

# ---------- riconoscimento dei commenti ----------
def analizza(testo, comuni):
    """Trasforma un commento in un'azione del gioco. Restituisce un dict con 'k' (tipo) oppure con 'manca'."""
    raw = re.sub(r"@\w[\w.]*", " ", testo).strip()           # i tag agli amici non fanno parte del formato
    raw = re.sub(r"[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F]+", " ", raw).strip() if not re.fullmatch(r"[\W_]+", raw) else raw
    raw = senza_regioni(raw)
    t = norm(raw)
    if re.fullmatch(r"rimuovi( tutto)?", t):
        return {"k": "rimuovi"}
    if re.search(r"(?i)\b(ti seguo|seguo|seguito|seguita|follow|followato|followata)\b", raw):
        resto_s = re.sub(r"(?i)\b(ti seguo|seguo|seguito|seguita|ho messo segui|follow|followato|followata|già|gia|anche)\b", " ", raw).strip(" ,.!")
        if not re.search(r"\w", resto_s):
            return {"k": "segue"}
        dentro = analizza(resto_s, comuni)
        if dentro:
            dentro["segue"] = True
            return dentro
        return {"k": "segue"}
    solo = re.sub(r"[\s!.]+", "", testo.lower())
    if solo and re.fullmatch(r"(🐶|🐕|🐩|🦮|cani|cane|teamcani|forzacani)+", solo):
        return {"k": "voto", "t": "cane"}
    if solo and re.fullmatch(r"(🐱|🐈|🐈‍⬛|😺|😸|gatti|gatto|teamgatti|forzagatti)+", solo):
        return {"k": "voto", "t": "gatto"}
    m = re.match(r"^tifo\s*(cani|cane|gatti|gatto)\s*[:,\-]?\s*(.+)$", t)
    if m:
        c, err = comuni.trova(m.group(2))
        if not c:
            return {"k": "tifo", "manca": err or "comune"}
        return {"k": "tifo", "t": "gatto" if m.group(1).startswith("gatt") else "cane", "luogo": c}
    kind = "animale"
    m = re.match(r"^(sogno|stella)\s*[:,\-]\s*(.+)$", raw, flags=re.I)
    if m:
        kind, raw = m.group(1).lower(), m.group(2)
    multi = piu_animali(raw, comuni)
    if multi:
        return multi
    parti = [p.strip() for p in re.split(r"[,;\n]| - | – |\. ", raw) if p.strip(" .")]
    parti = [p.strip(" .") for p in parti]
    if not parti:
        return None
    # 1) il comune: una parte intera, oppure all'inizio o alla fine di una parte ("Tarquinia gatto tigrato", "Leo Treviso"),
    #    oppure dopo "a/di/da/in" in una frase libera ("il mio cane Bobby vive a Bari")
    luogo, err, resto = None, None, []
    for p in parti:
        if not luogo:
            c, e = comuni.trova(p)
            if c:
                luogo = c; continue
            err = err or e
            if len(p.split()) <= 12:
                c, rimanente = comuni.in_testa(p)
                if c:
                    luogo = c
                    # "Genova quinto, Maila": una parola in più accanto al comune è un quartiere, se il nome è altrove
                    if rimanente and not (len(parti) > 1 and len(rimanente.split()) <= 2 and not descrittiva(rimanente)):
                        resto.append(rimanente)
                    continue
        resto.append(p)
    if not luogo:
        c, frase_senza = comuni.in_mezzo(raw)
        if c:
            luogo, resto = c, [frase_senza]
    # 2) il nome: le prime parole che non sono razza, tipo d'animale o parole di riempimento; il resto è la descrizione
    nome, descr = "", []
    for p in resto:
        ws = [w for w in p.split() if norm(w)]
        if not nome and len(ws) == 1 and len(resto) > 1 and ws[0][:1].isupper() and norm(ws[0]) not in RIEMPITIVE:
            nome = nome_proprio(ws[0]); continue  # "Como, Rex, husky": la parola sola col maiuscolo è il nome, anche se somiglia a una razza
        while ws and norm(ws[0]) in RIEMPITIVE:
            ws = ws[1:]
        if not nome and ws and not inizia_descrizione(ws, 0):
            presi = []
            for i, w in enumerate(ws):
                if inizia_descrizione(ws, i) or norm(w) in RIEMPITIVE: break
                presi.append(w)
            if len(presi) <= 3:  # un nome non è una frase intera
                nome = nome_proprio(" ".join(presi)); descr.append(" ".join(ws[len(presi):])); continue
        descr.append(" ".join(ws))
    descr = " ".join(d for d in descr if d).strip()
    if not nome:  # frasi libere: "si chiama Salem", oppure la prima parola con la maiuscola che non sia il comune
        m2 = re.search(r"\bchiama\s+([A-Za-zÀ-ÿ']+)", raw, re.I)
        cand = [m2.group(1)] if m2 else [w for w in re.findall(r"\b[A-ZÀ-Ý][a-zà-ÿ']+", raw)
                                          if norm(w) not in RIEMPITIVE and not descrittiva(w) and not (luogo and norm(w) in norm(luogo["c"]))]
        if cand:
            nome = nome_proprio(cand[0])
    sembra_gioco = kind != "animale" or bool(luogo) or bool(GATTO_PAROLE.search(norm(raw)) or cerca_razza(raw)
                                              or re.search(r"\b(cane|cagnolin|cucciol)", norm(raw)))
    if nome and luogo and norm(nome) == norm(luogo["c"]):
        nome = ""  # "Tarquinia gatto tigrato": Tarquinia è il comune, non il nome
    if not luogo:
        return {"k": kind, "manca": err or "comune", "n": nome or None} if sembra_gioco and (nome or descr) else None
    if not nome:
        return {"k": kind, "manca": "nome", "luogo": luogo}
    tipo = tipo_animale(descr)
    rz = razza(descr, tipo)
    if kind == "stella":
        return {"k": "stella", "t": tipo, "luogo": luogo, "n": nome, "razza": rz}
    if not rz and not descr:
        return {"k": kind, "manca": "razza", "luogo": luogo, "n": nome}
    return {"k": kind, "t": tipo, "luogo": luogo, "n": nome, "razza": rz or ("europeo" if tipo == "gatto" else "meticcio"), "razza_testo": descr[:40]}

# ---------- risposte ----------
FRASI = {
    "fondatore": [
        "{n} è il primo {animale} di {c} sulla mappa! 👑 Da oggi è il Fondatore della città.",
        "Si accende la prima luce di {c}: è {n}! 👑 Fondatore per sempre.",
        "{c} non era mai stata accesa. Ci ha pensato {n}: è il Fondatore! ✨",
    ],
    "animale": [
        "{n} si è acceso sulla mappa! È il {pos}° {animale} di {c} ✨",
        "Benvenuto {n}! A {c} ora brillano {tot} luci {squadra}. Forza!",
        "La luce di {n} è accesa: {c} sale nella sfida Cani contro Gatti! 🔥",
        "Ecco {n}, {pos}° {animale} di {c}. Tagga un amico e fai salire la città!",
    ],
    "animale_altro": ["{n} si è acceso a {c}! 🐾 La squadra degli altri animali ora ha {na} luci: a {soglia} entra nella sfida contro cani e gatti!",
                      "Benvenuto {n}! È il {na}° tra conigli, furetti, gechi e tartarughe: a {soglia} luci si sfida cani e gatti 🔥"],
    "sfida_fondatore": ["{n} è il primo di {c}: Fondatore! 👑 Ora {c} sfida {rc}, che ha già {rt}. Tagga gli amici di {c} e superatela 🔥",
                        "{c} si accende con {n}, il Fondatore 👑 La vicina {rc} ha {rt}: chi vince? Tagga i tuoi amici di {c}!"],
    "sfida_vicini": ["{n} è acceso! {c} {mt}, {rc} {rt}. Tagga gli amici di {c} e sorpassate! 🔥",
                     "Luce accesa per {n} ✨ Sfida tra vicini: {c} {mt} contro {rc} {rt}. Chi porti dalla tua città? 👥"],
    "sfida_testa": ["{n} è acceso! {c} è in testa con {mt}, {rc} insegue con {rt}. Tagga gli amici e allungate! 🔥"],
    "vicini": ["{n} è acceso a {c}! I tuoi vicini sono {v1} e {v2} 🐾"],
    "tifo": ["Tifo registrato: +1 per i {squadra} di {c}! 📣", "{c} ringrazia: un tifoso in più per i {squadra}! 🔥"],
    "sogno": ["Il sogno di {n} è in cielo sopra {c} ☁️", "Una nuvoletta in più su {c}: {n} ti aspetta nei sogni ☁️"],
    "stella": ["Una stella per {n} brilla sopra {c}. ✦", "{n} ora è una stella nel cielo di {c}. Sempre con te. ✦"],
    "manca_comune_nome": ["In quale comune vive {n}? Scrivilo qui sotto e si accende la sua luce 🗺️", "Che bello {n}! Dove vive? Scrivi il comune e accendo la sua luce ✨"],
    "manca_comune": ["Quasi! In quale comune vive? Scrivi per esempio «Treviso, {n}, golden» 🐾", "Non ho trovato il comune 🙈 Riscrivilo con città, nome e razza!"],
    "manca_provincia": ["Ci sono più comuni con quel nome: aggiungi la provincia, per esempio «Calliano TN» 🗺️"],
    "manca_nome": ["Come si chiama? Riscrivi «{c}, nome, razza» e si accende la sua luce ✨"],
    "manca_razza": ["Che razza è {n}? Scrivi «{c}, {n}, golden» oppure «{c}, {n}, gatto rosso» 🐶🐱"],
    "manca_formato": ["Scrivi per esempio «Sogno: Padova, Bruno, bassotto» oppure «Stella: Treviso, Max» ✨"],
    "multi": ["Si accendono {quanti} luci a {c}: {nomi}! ✨ Benvenuti sulla mappa 🐾", "{c} si illumina: {nomi} sono sulla mappa! 🔥"],
    "segue": ["Grazie per il follow! +10 punti per te 🎉", "Benvenuto tra noi! +10 punti per il follow 🐾"],
    "segue_senza_luce": ["Grazie per il follow! I tuoi +10 punti arrivano appena accendi la tua luce: scrivi città, nome e razza ✨"],
    "invito_salto": ["🚀 Seguici e scrivi SEGUO: +10 punti e {n} sale {dal} {al} posto in Italia!",
                     "Vuoi salire? Segui @zampeditalia e scrivi SEGUO: +10 punti, {n} passa {dal} {al} posto 🏆",
                     "👉 Manca solo il follow: seguici, scrivi SEGUO e {n} vola {dal} {al} posto (+10 punti) 🚀"],
    "invito_segui": ["👉 Seguici e scrivi SEGUO: +10 punti!", "Segui @zampeditalia e scrivi SEGUO: +10 punti e scali la classifica 🚀",
                     "Ultimo passo: seguici e scrivi SEGUO, +10 punti per te 🎁"],
    "cartolina": ["💌 Scrivici CARTOLINA in privato e ti mandiamo la cartolina di {n} da mettere in storia!",
                  "💌 Vuoi la cartolina di {n}? Scrivici CARTOLINA in DM 📲"],
    "aggiornato": ["Fatto! {n} ora brilla a {c} ✨", "Aggiornato: {n} è a {c} 🗺️"],
    "estero": ["Per ora la mappa è solo l'Italia 🇮🇹 Se hai un comune italiano del cuore, scrivilo e accendiamo la luce lì ✨"],
    "voto": ["Voto per i {squadra} registrato! 🔥 {squadra} {n}, {rivale} {altri}. Accendi anche la tua luce: città, nome e razza ✨",
             "+1 ai {squadra}! Ora sono {n} contro {altri}. Scrivi città, nome e razza e metti il tuo animale sulla mappa 🐾"],
    "voto_altri": ["+1 agli altri animali! 🐰🐢🦎 Conigli, furetti e tartarughe si fanno sentire. Accendi anche la tua luce: città, nome e specie ✨"],
    "altri": ["Sì! Da oggi si accendono tutti gli animali: furetti, conigli, gechi, tartarughe… 🐾 Scrivi città, nome e specie e arriva la sua luce ✨"],
    "rimosso": ["Fatto, abbiamo tolto le tue luci dalla mappa. Ti aspettiamo quando vuoi 🐾"],
    "tag": ["Hai taggato {amici}: per ognuno che commenta, +3 punti per te! 👥", "Inviti partiti per {amici}: per ognuno che commenta prendi +3 punti 🔥"],
    "tag_senza_luce": ["Bello l'invito a {amici}! Accendi prima la tua luce con città, nome e razza: poi ogni amico che commenta ti vale +3 punti 👥"],
    "premio": ["Benvenuto! Grazie a te {chi} ha appena preso +3 punti 🎉", "Sei arrivato con un invito: +3 punti a {chi} 👥"],
    "base": ["Ciao! Scrivi città, nome e razza del tuo animale, per esempio «Treviso, Luna, golden», e accendi la sua luce ✨"],
}

def frase(chiave, **kw):
    return random.choice(FRASI[chiave]).format(**kw)

# ---------- Instagram ----------
class Instagram:
    def __init__(self, token):
        self.token = token

    def _req(self, method, path, **params):
        params["access_token"] = self.token
        url = path if path.startswith("http") else f"{API}/{path}"
        data = None
        if method in ("GET", "DELETE"):
            url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
        else:
            data = urllib.parse.urlencode(params).encode()
        req = urllib.request.Request(url, data=data, method=method)
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())

    def pagine(self, path, **params):
        res = self._req("GET", path, **params)
        while True:
            yield from res.get("data", [])
            nxt = res.get("paging", {}).get("next")
            if not nxt:
                return
            with urllib.request.urlopen(nxt, timeout=30) as r:
                res = json.loads(r.read())

    def io(self):
        return self._req("GET", "me", fields="user_id,username")

    def reel_recenti(self):
        limite = datetime.now(timezone.utc) - timedelta(days=GIORNI_REEL)
        for m in self.pagine("me/media", fields="id,timestamp,media_product_type,permalink", limit=25):
            if datetime.fromisoformat(m["timestamp"].replace("+0000", "+00:00")) < limite:
                return
            yield m

    def commenti(self, media_id):
        yield from self.pagine(f"{media_id}/comments", fields="id,text,timestamp,username,from", limit=50)

    def cancella_mie_risposte(self, comment_id, mio):
        """Toglie le risposte della pagina sotto un commento (per rifare una risposta sbagliata)."""
        for r in self.pagine(f"{comment_id}/replies", fields="id,username,from"):
            if (r.get("username") or r.get("from", {}).get("username", "")).lower() == mio.lower():
                self._req("DELETE", r["id"])

    def rispondi(self, comment_id, testo):
        return self._req("POST", f"{comment_id}/replies", message=testo)

# ---------- stato del gioco ----------
def carica(path, vuoto):
    try:
        return json.loads(Path(path).read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return vuoto

def distanza(a, b):
    x = (a["lng"] - b["lng"]) * cos(radians((a["lat"] + b["lat"]) / 2))
    return sqrt(x * x + (a["lat"] - b["lat"]) ** 2)

class Gioco:
    def __init__(self):
        self.dati = carica(ANIMALI, {"aggiornato": None, "animali": []})
        self.stato = carica(STATO, {"visti": [], "risposte": [], "bonus": {}, "media_letti": {}})
        self.visti = set(self.stato["visti"])
        self.cambiato = False

    @property
    def animali(self):
        return self.dati["animali"]

    def salva(self):
        self.dati["aggiornato"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.stato["visti"] = sorted(self.visti)[-50000:]
        oggi = datetime.now(timezone.utc).date().isoformat()
        ig = self.stato.get("inviti_giorno", {})
        self.stato["inviti_giorno"] = {g: v for g, v in ig.items() if g >= (datetime.now(timezone.utc) - timedelta(days=7)).date().isoformat()}
        tot = {}
        for coppia in self.stato.get("premiati", []):
            tot[coppia.split(">")[0]] = tot.get(coppia.split(">")[0], 0) + 1
        self.dati["inviti"] = {"giorno": oggi, "oggi": sorted(ig.get(oggi, {}).items(), key=lambda x: -x[1])[:10],
                               "totale": sorted(tot.items(), key=lambda x: -x[1])[:10]}
        ora = time.time()
        self.stato["risposte"] = [t for t in self.stato["risposte"] if ora - t < 3600]
        ANIMALI.write_text(json.dumps(self.dati, ensure_ascii=False, separators=(",", ":")) + "\n")
        STATO.write_text(json.dumps(self.stato, ensure_ascii=False, indent=0) + "\n")

    def risposte_ultima_ora(self):
        ora = time.time()
        return sum(1 for t in self.stato["risposte"] if ora - t < 3600)

    def applica(self, az, utente, ts):
        """Aggiorna la mappa. Restituisce (chiave_frase, parametri, risposta_obbligatoria)."""
        k = az["k"]
        if k == "voto":  # un voto al giorno per persona nella sfida nazionale Cani contro Gatti
            oggi = datetime.now(timezone.utc).date().isoformat()
            fatti = self.stato.setdefault("voti_oggi", {})
            if fatti.get(utente.lower()) == oggi:
                return None, {}, False
            fatti[utente.lower()] = oggi
            v = self.dati.setdefault("voti", {"cani": 0, "gatti": 0})
            sq = {"gatto": "gatti", "altro": "altri"}.get(az["t"], "cani")
            v[sq] = v.get(sq, 0) + 1
            self.cambiato = True
            if sq == "altri":
                return "voto_altri", {"n": v[sq]}, False
            return "voto", {"squadra": sq, "n": v[sq], "altri": v["cani" if sq == "gatti" else "gatti"], "rivale": "cani" if sq == "gatti" else "gatti"}, False
        if k == "multi":
            nomi = []
            for x in az["animali"]:
                self.applica({"k": "animale", "luogo": az["luogo"], **x}, utente, ts); nomi.append(x["n"])
            return "multi", {"c": az["luogo"]["c"], "nomi": ", ".join(nomi[:-1]) + " e " + nomi[-1], "quanti": len(nomi)}, True
        if k == "rimuovi":
            prima = len(self.animali)
            self.dati["animali"] = [a for a in self.animali if a["u"].lower() != utente.lower()]
            self.cambiato |= prima != len(self.animali)
            return "rimosso", {}, True
        if "manca" in az:
            luogo = az.get("luogo") or {}
            if az.get("n") and any(a["u"].lower() == utente.lower() and norm(a["n"]) == norm(az["n"]) for a in self.animali):
                return None, {}, False  # animale già sulla mappa, riscritto senza razza: niente da chiedere
            chiave = "manca_comune_nome" if az["manca"] == "comune" and az.get("n") else "manca_" + az["manca"]
            return chiave, {"n": az.get("n") or "il tuo animale", "c": luogo.get("c", "Treviso")}, True
        L = az["luogo"]
        base = {"u": utente, "c": L["c"], "p": L["p"], "r": L["r"], "lat": L["lat"], "lng": L["lng"], "ts": ts}
        if k == "tifo":
            gia = next((a for a in self.animali if a["u"].lower() == utente.lower() and a["k"] == "tifo"), None)
            if gia:  # un tifo per persona: si può cambiare squadra o città
                gia.update(base, t=az["t"])
            else:
                self.animali.append({**base, "id": f"{utente}|tifo", "k": "tifo", "t": az["t"], "n": "", "pt": PUNTI["tifo"]})
            self.cambiato = True
            return "tifo", {"c": L["c"], "squadra": "gatti" if az["t"] == "gatto" else "cani"}, False
        miei = [a for a in self.animali if a["u"].lower() == utente.lower() and a["k"] != "tifo"]
        gia = next((a for a in miei if norm(a["n"]) == norm(az["n"]) and a["k"] == k), None)
        if gia:  # stesso animale riscritto: si aggiornano città e razza, i punti restano
            gia.update(base, t=az["t"], razza=az.get("razza"), razza_testo=az.get("razza_testo"), ts=gia["ts"])
            self.cambiato = True
            return None, {}, False
        if len(miei) >= MAX_ANIMALI_PER_UTENTE:
            return None, {}, False
        fondatore = k == "animale" and not any(a["k"] == "animale" and a["c"] == L["c"] and a["p"] == L["p"] for a in self.animali)
        pt = PUNTI["fondatore"] if fondatore else PUNTI[k]
        nuovo = {**base, "id": f"{utente}|{k}|{norm(az['n'])}", "k": k, "t": az["t"], "n": az["n"], "razza": az.get("razza"), "razza_testo": az.get("razza_testo"), "pt": pt}
        if fondatore:
            nuovo["ruolo"] = f"Fondatore di {L['c']}"
        self.animali.append(nuovo)
        self.cambiato = True
        if k in ("sogno", "stella"):
            return k, {"n": az["n"], "c": L["c"]}, k == "stella"
        animale = "gatto" if az["t"] == "gatto" else "cane"
        if fondatore:
            return "fondatore", {"n": az["n"], "c": L["c"], "animale": animale}, True
        stessa = [a for a in self.animali if a["k"] == "animale" and a["c"] == L["c"] and a["p"] == L["p"]]
        pos = sum(1 for a in stessa if a["t"] == az["t"])
        vicini = sorted((a for a in self.animali if a["k"] == "animale" and a is not nuovo and a["u"].lower() != utente.lower()),
                        key=lambda a: distanza(a, L))[:2]
        par = {"n": az["n"], "c": L["c"], "pos": pos, "animale": animale, "tot": pos, "squadra": "gatte" if az["t"] == "gatto" else "canine"}
        if len(vicini) == 2 and random.random() < 0.4:
            return "vicini", {**par, "v1": vicini[0]["n"], "v2": vicini[1]["n"]}, False
        return "animale", par, False

    def tag(self, utente, testo):
        """Segna gli amici taggati in un commento. Restituisce i nuovi invitati."""
        nuovi = []
        for amico in {m.rstrip(".").lower() for m in re.findall(r"@([\w.]+)", testo)}:
            if not amico or amico == utente.lower() or amico == "zampeditalia":
                continue
            if f"{utente.lower()}>{amico}" in self.stato.get("premiati", []):
                continue  # questo amico ha già fatto prendere i punti a chi lo invita
            chi = self.stato.setdefault("inviti", {}).setdefault(amico, [])
            if utente.lower() not in chi:
                chi.append(utente.lower()); nuovi.append(amico); self.cambiato = True
        return nuovi

    def premia_inviti(self, utente):
        """L'amico taggato ha commentato: +3 a chi l'ha invitato, una volta sola per coppia. Restituisce chi è stato premiato."""
        premiati = []
        for chi in self.stato.get("inviti", {}).pop(utente.lower(), []):
            coppia = f"{chi}>{utente.lower()}"
            if coppia in self.stato.setdefault("premiati", []):
                continue
            if self.ha_luce(chi):
                self.punti_extra(chi, PUNTI["tag"])
                self.stato["premiati"].append(coppia); premiati.append(chi)
                giorno = self.stato.setdefault("inviti_giorno", {}).setdefault(datetime.now(timezone.utc).date().isoformat(), {})
                giorno[chi] = giorno.get(chi, 0) + 1  # Sfida degli inviti: chi porta più amici oggi
        return premiati

    def segue(self, utente):
        """+10 una volta sola a chi scrive SEGUO (l'API non dice chi ci segue: vale sulla fiducia). Restituisce la frase da usare."""
        st = self.stato.setdefault("seguono", {})
        if st.get(utente.lower()) == "premiato":
            return None
        if self.ha_luce(utente):
            self.punti_extra(utente, PUNTI["segue"]); st[utente.lower()] = "premiato"
            return "segue"
        if st.get(utente.lower()) == "in_attesa":
            return None  # gliel'abbiamo già detto
        st[utente.lower()] = "in_attesa"; self.cambiato = True
        return "segue_senza_luce"

    def bonus_giornaliero(self, utente):
        """+5 una volta al giorno a chi commenta un reel nuovo e ha già una luce."""
        oggi = datetime.now(timezone.utc).date().isoformat()
        if self.stato["bonus"].get(utente.lower()) == oggi:
            return
        if self.ha_luce(utente):
            self.punti_extra(utente, PUNTI["giornaliero"])
            self.stato["bonus"][utente.lower()] = oggi

    # ---------- punti: base dell'animale + punti extra della persona (inviti, follow, bonus) ----------
    def ha_luce(self, utente):
        return any(a["u"].lower() == utente.lower() and a["k"] in ("animale", "sogno", "tifo") for a in self.animali)

    def punti_extra(self, utente, n):
        ex = self.stato.setdefault("extra", {})
        ex[utente.lower()] = ex.get(utente.lower(), 0) + n
        self.ricalcola()

    def migra_punti(self):
        """Una volta sola: i bonus prima stavano dentro i punti dell'animale, ora si tengono a parte per persona."""
        if "extra" in self.stato:
            return
        ex = {}
        for a in self.animali:
            base = 0 if a["k"] == "stella" else PUNTI["tifo"] if a["k"] == "tifo" else PUNTI["fondatore"] if a.get("ruolo") else PUNTI[a["k"]]
            ex[a["u"].lower()] = ex.get(a["u"].lower(), 0) + max(0, a.get("pt", 0) - base)
        self.stato["extra"] = {u: v for u, v in ex.items() if v}

    def ricalcola(self):
        """Fondatore = il primo animale acceso in ogni comune. Punti = base + extra della persona sull'animale migliore."""
        primo = {}
        for a in sorted((a for a in self.animali if a["k"] == "animale"), key=lambda a: a.get("ts") or ""):
            primo.setdefault((a["c"], a["p"]), a["id"])
        for a in self.animali:
            fond = a["k"] == "animale" and primo.get((a["c"], a["p"])) == a["id"]
            if fond: a["ruolo"] = f"Fondatore di {a['c']}"
            else: a.pop("ruolo", None)
            a["pt"] = 0 if a["k"] == "stella" else PUNTI["tifo"] if a["k"] == "tifo" else PUNTI["fondatore"] if fond else PUNTI[a["k"]]
        ex = self.stato.get("extra", {})
        per = {}
        for a in self.animali:
            if a["k"] in ("animale", "sogno", "tifo"):
                u = a["u"].lower()
                if u not in per or a["pt"] > per[u]["pt"]: per[u] = a
        for u, a in per.items():
            a["pt"] += ex.get(u, 0)
        self.cambiato = True

    def riconcilia(self, utente, letto, ts_di):
        """Mette sulla mappa gli animali letti da Claude per questa persona. Restituisce (nuovi, aggiornati)."""
        miei = {norm(a["n"]): a for a in self.animali if a["u"].lower() == utente.lower() and a["k"] in ("animale", "sogno", "stella")}
        nuovi, aggiornati = [], []
        for x in letto["animali"]:
            L = x["luogo"]
            campi = {"c": L["c"], "p": L["p"], "r": L["r"], "lat": L["lat"], "lng": L["lng"], "k": x["k"], "t": x["t"],
                     "n": x["n"], "razza": x["razza"], "razza_testo": x["razza_testo"]}
            if x["t"] == "altro": campi["specie"] = x["specie"]
            a = miei.get(norm(x["n"]))
            if a:
                if any(a.get(k) != v for k, v in campi.items() if k in ("c", "p", "k", "t", "n", "specie")):
                    aggiornati.append(a)
                a.update(campi)
                if x["t"] != "altro": a.pop("specie", None)
            else:
                if len(miei) + len(nuovi) >= MAX_ANIMALI_PER_UTENTE:
                    continue
                a = {"u": utente, **campi, "ts": ts_di(x.get("id_commento")), "id": f"{utente}|{x['k']}|{norm(x['n'])}", "pt": 0}
                self.animali.append(a); nuovi.append(a)
        if nuovi or aggiornati:
            self.ricalcola()
        return nuovi, aggiornati

# ---------- giro principale ----------
CORREZIONI = ROOT / "motore/correzioni.json"

def applica_correzioni(gioco):
    """Correzioni a mano lette da motore/correzioni.json, applicate una volta sola: toglie voci sbagliate e fa rielaborare commenti."""
    try:
        cor = json.loads(CORREZIONI.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return set()
    if not cor.get("id") or cor["id"] in gioco.stato.setdefault("correzioni_fatte", []):
        return set()
    via = {(x["u"].lower(), x["n"].lower()) for x in cor.get("togli", [])}
    gioco.dati["animali"] = [a for a in gioco.animali if (a["u"].lower(), a["n"].lower()) not in via]
    rifai = set(cor.get("rifai", []))
    gioco.visti -= rifai
    comuni = Comuni()
    for x in cor.get("aggiungi", []):
        c, _ = comuni.trova(x["comune"])
        if c:
            gioco.applica({"k": "animale", "t": x["t"], "luogo": c, "n": x["n"], "razza": x["razza"], "razza_testo": x.get("razza_testo", "")}, x["u"], x.get("ts") or datetime.now(timezone.utc).isoformat())
            if x.get("risposta_a"):
                gioco.stato.setdefault("risposte_da_fare", []).append({"id": x["risposta_a"], "testo": x["risposta"]})
    gioco.stato["correzioni_fatte"].append(cor["id"]); gioco.cambiato = True
    print(f"correzione {cor['id']}: tolte {len(via)} voci, da rifare {len(rifai)} commenti")
    return rifai

SPECIE_RE = r"furett|conigli|criceti|criceto|pappagall|uccell|cavall|tartarug|pesc|porcellin|asin|capr|galli|gec|lepr|rettil|serpent|iguan|cincill|maial"

def solo_tag(testo):
    return bool(re.fullmatch(r"\s*(@[\w.]+[\s,]*)+", testo or ""))

def rivale(gioco, a):
    """Il comune acceso più vicino (entro ~60 km): la sfida col paese accanto fa taggare gli amici della propria città."""
    conta = {}
    for x in gioco.animali:
        if x["k"] == "animale":
            k = (x["c"], x["p"]); conta.setdefault(k, [0, x]); conta[k][0] += 1
    mio = conta.get((a["c"], a["p"]), [0])[0]
    vicini = [(distanza(x, a), c, n) for (c, p), (n, x) in conta.items() if (c, p) != (a["c"], a["p"]) and distanza(x, a) < 0.6]
    if not vicini:
        return None
    davanti = [v for v in vicini if v[2] >= mio]  # meglio un vicino da superare
    _, c, n = min(davanti or vicini)
    luci = lambda k: f"{k} {'luce' if k == 1 else 'luci'}"
    return {"rc": c, "rt": luci(n), "mt": luci(mio), "testa": not davanti}

def invito_segui(gioco, u):
    """L'invito a seguirci, col posto concreto che si guadagna in classifica: «sale dal 140° all'11° posto».
    I posti si contano come sul sito: punti, e a pari punti chi è arrivato prima."""
    gara = [a for a in gioco.animali if a["k"] in ("animale", "sogno")]
    miei = [a for a in gara if a["u"].lower() == u.lower()]
    if miei:
        io = max(miei, key=lambda a: a.get("pt", 0))
        pt, ts = io.get("pt", 0), str(io.get("ts", ""))
        altri = [(a.get("pt", 0), str(a.get("ts", ""))) for a in gara if a["u"].lower() != u.lower()]
        r1 = 1 + sum(1 for p, t in altri if p > pt or p == pt and t < ts)
        r2 = 1 + sum(1 for p, t in altri if p > pt + PUNTI["segue"] or p == pt + PUNTI["segue"] and t < ts)
        if r2 < r1:
            al = lambda r, prep: f"{prep}ll'{r}°" if str(r)[0] == "8" or r == 11 else f"{prep}l {r}°"  # dall'11°, all'8°
            return frase("invito_salto", n=io["n"], dal=al(r1, "da"), al=al(r2, "a"))
    return frase("invito_segui")

def scegli_frase(gioco, u, letto, nuovi_a, aggiornati, nuovi_c):
    """La frase giusta per l'ultimo commento di questa persona."""
    ids = {c["id"] for c in nuovi_c}
    if nuovi_a:
        if len(nuovi_a) >= 2:
            nomi = [a["n"] for a in nuovi_a]
            citta = sorted({a["c"] for a in nuovi_a})
            return "multi", {"c": " e ".join(citta), "nomi": ", ".join(nomi[:-1]) + " e " + nomi[-1], "quanti": len(nomi)}
        a = nuovi_a[0]
        if a["k"] in ("stella", "sogno"):
            return a["k"], {"n": a["n"], "c": a["c"]}
        animale = a["t"] if a["t"] in ("cane", "gatto") else a.get("specie") or "animale"
        r = rivale(gioco, a)
        if r and random.random() < 0.6:
            return ("sfida_fondatore" if a.get("ruolo") else "sfida_testa" if r["testa"] else "sfida_vicini"), {"n": a["n"], "c": a["c"], "animale": animale, **r}
        if a.get("ruolo"):
            return "fondatore", {"n": a["n"], "c": a["c"], "animale": animale}
        if a["t"] == "altro" and random.random() < 0.7:
            na = sum(1 for x in gioco.animali if x["k"] == "animale" and x.get("t") == "altro")
            if na < SOGLIA_ALTRI:
                return "animale_altro", {"n": a["n"], "c": a["c"], "na": na, "soglia": SOGLIA_ALTRI}
        stessa = [x for x in gioco.animali if x["k"] == "animale" and x["c"] == a["c"] and x["p"] == a["p"] and x["t"] == a["t"]]
        squadra = "canine" if a["t"] == "cane" else "gatte" if a["t"] == "gatto" else "speciali"
        par = {"n": a["n"], "c": a["c"], "pos": len(stessa), "animale": animale, "tot": len(stessa), "squadra": squadra}
        vicini = sorted((x for x in gioco.animali if x["k"] == "animale" and x is not a and x["u"].lower() != u.lower()),
                        key=lambda x: distanza(x, a))[:2]
        if len(vicini) == 2 and random.random() < 0.4:
            return "vicini", {**par, "v1": vicini[0]["n"], "v2": vicini[1]["n"]}
        return "animale", par
    if aggiornati:
        a = aggiornati[0]
        return "aggiornato", {"n": a["n"], "c": a["c"]}
    for x in letto["senza_comune"]:
        if x.get("id") in ids:
            return "manca_comune_nome", {"n": x["n"]}
    for x in letto["senza_nome"]:
        if x.get("id") in ids:
            return ("manca_nome", {"c": x["luogo"]["c"]}) if x.get("luogo") else ("base", {})
    if letto["estero"] and not gioco.ha_luce(u):
        return "estero", {}
    if letto["domanda"] and any("?" in c.get("text", "") for c in nuovi_c):
        return "altri", {}
    return None, {}

def vuoto():
    return {"animali": [], "senza_comune": [], "senza_nome": [], "estero": False, "voti": [], "segue": False, "rimuovi": False, "domanda": None}

def per_persona(commenti, mio_username, visti=None):
    per = {}
    for media_id, c in commenti:
        u = c.get("username") or c.get("from", {}).get("username", "")
        if not u or (mio_username and u.lower() == mio_username.lower()):
            if visti is not None: visti.add(c["id"])
            continue
        per.setdefault(u, []).append(c)
    for v in per.values():
        v.sort(key=lambda c: c.get("timestamp", ""))
    return per

def gira(commenti, rispondi, mio_username=None, cancella=None, leggi_fn=None):
    """commenti: iterabile di (media_id, commento); rispondi: funzione(comment_id, testo); cancella: funzione(comment_id) per le risposte da rifare.
    Claude legge tutti i commenti di chi ha scritto qualcosa di nuovo; se non risponde, quei commenti si riprovano al giro dopo."""
    comuni, gioco = Comuni(), Gioco()
    gioco.migra_punti()
    rifai = applica_correzioni(gioco)
    for r in gioco.stato.pop("risposte_da_fare", []):  # risposte decise a mano nella correzione
        try:
            if cancella:
                for cid in r.get("cancella", [r["id"]]): cancella(cid)
            if r.get("testo"): rispondi(r["id"], r["testo"])
        except Exception as e:
            print(f"risposta di correzione non inviata ({r['id']}): {e}", file=sys.stderr)
    leggi_fn = leggi_fn or (lambda u, cs: lettore.leggi(u, cs, comuni, norm, nome_proprio, razza))
    per = per_persona(commenti, mio_username, gioco.visti)
    oggi = datetime.now(timezone.utc).date().isoformat()
    nuovi = risposte = 0
    for u, suoi in per.items():
        nuovi_c = [c for c in suoi if c["id"] not in gioco.visti or c["id"] in rifai]
        if not nuovi_c:
            continue
        letto = vuoto() if all(solo_tag(c.get("text", "")) for c in nuovi_c) else leggi_fn(u, suoi)
        if letto is None:
            print(f"@{u}: il lettore non ha risposto, riprovo al prossimo giro", file=sys.stderr)
            continue
        for c in nuovi_c:
            gioco.visti.add(c["id"])
            if c["id"] in rifai and cancella:
                try: cancella(c["id"])
                except Exception as e: print(f"risposta vecchia non cancellata ({c['id']}): {e}", file=sys.stderr)
        nuovi += len(nuovi_c)
        ts_di = lambda cid: next((c.get("timestamp") for c in suoi if c["id"] == cid), None) or nuovi_c[-1].get("timestamp") or datetime.now(timezone.utc).isoformat()
        if letto["rimuovi"]:
            chiave, par, _ = gioco.applica({"k": "rimuovi"}, u, None)
        else:
            nuovi_a, aggiornati = gioco.riconcilia(u, letto, ts_di)
            chiave, par = scegli_frase(gioco, u, letto, nuovi_a, aggiornati, nuovi_c)
        ids = {c["id"] for c in nuovi_c}
        for v in letto["voti"]:
            if v["id"] in ids:
                k2, p2, _ = gioco.applica({"k": "voto", "t": {"gatti": "gatto", "altri": "altro"}.get(v["squadra"], "cane")}, u, None)
                if k2 and not chiave: chiave, par = k2, p2
        if chiave in ("fondatore", "animale", "vicini", "multi", "sfida_fondatore", "sfida_vicini", "sfida_testa", "animale_altro"):
            gioco.stato["bonus"][u.lower()] = oggi  # il commento che accende una luce ha già i suoi punti
        else:
            gioco.bonus_giornaliero(u)
        seguono = gioco.stato.setdefault("seguono", {})
        frase_segue = None
        if letto["segue"] or seguono.get(u.lower()) == "in_attesa" and gioco.ha_luce(u):
            frase_segue = gioco.segue(u)
        # inviti: chi tagga amici prende +3 per ognuno che poi commenta; a chi tagga si risponde sempre
        taggati = [a for c in nuovi_c for a in gioco.tag(u, c.get("text", ""))]
        premiati = gioco.premia_inviti(u)
        extra = []
        if taggati:
            extra.append(frase("tag" if gioco.ha_luce(u) else "tag_senza_luce", amici=", ".join("@" + a for a in taggati[:5])))
        if premiati:
            extra.append(frase("premio", chi=", ".join("@" + a for a in premiati[:3])))
        if frase_segue:
            extra.append(frase(frase_segue))
        elif chiave in ("fondatore", "animale", "vicini", "multi", "aggiornato", "voto", "voto_altri", "sfida_fondatore", "sfida_vicini", "sfida_testa", "animale_altro") and not seguono.get(u.lower()):
            extra.append(invito_segui(gioco, u))  # commentano ma non ci seguono: lo chiediamo a ogni luce, col posto che guadagnano
        elif chiave in ("fondatore", "animale", "vicini", "multi", "sfida_fondatore", "sfida_vicini", "sfida_testa", "animale_altro"):
            extra.append(frase("cartolina", n=par.get("n") or par.get("nomi", "").split(",")[0].split(" e ")[0]))  # la cartolina in storia porta gente nuova
        if not chiave and not extra:
            continue
        if gioco.risposte_ultima_ora() >= MAX_RISPOSTE_ORA:
            continue
        if len(gioco.animali) >= 500 and chiave in ("animale", "vicini") and not taggati and random.random() > QUOTA_RISPOSTE:
            continue
        testo = " ".join(t for t in [frase(chiave, **par) if chiave else ""] + extra if t)
        try:
            rispondi(nuovi_c[-1]["id"], testo)
            gioco.stato["risposte"].append(time.time())
            risposte += 1
        except Exception as e:  # una risposta fallita non deve fermare la mappa
            print(f"risposta non inviata a {nuovi_c[-1]['id']}: {e}", file=sys.stderr)
    gioco.salva()
    luci = sum(1 for a in gioco.animali if a["k"] != "stella")
    print(f"commenti nuovi: {nuovi} · risposte: {risposte} · luci sulla mappa: {luci}")
    return gioco

def ricostruisci(commenti, rispondi, mio_username, cancella, prova):
    """Rilegge con Claude TUTTI i commenti e rifà la mappa da capo; a chi era stato capito male risponde con la versione giusta."""
    from concurrent.futures import ThreadPoolExecutor
    comuni, gioco = Comuni(), Gioco()
    gioco.migra_punti()
    prima = {}
    for a in gioco.animali:
        if a["k"] != "tifo":
            prima.setdefault(a["u"].lower(), set()).add((norm(a["n"]), a["c"], a["k"]))
    per = per_persona(commenti, mio_username)
    with ThreadPoolExecutor(8) as ex:
        letti = dict(ex.map(lambda u: (u, lettore.leggi(u, per[u], comuni, norm, nome_proprio, razza)), list(per)))
    rinomina = carica(CORREZIONI, {}).get("rinomina", {})  # i pochi casi ambigui decisi a mano: {"utente": {"Letto": "Giusto"}}
    for u, l in letti.items():
        for x in (l or {}).get("animali", []):
            x["n"] = rinomina.get(u, {}).get(x["n"], x["n"])
    mancano = [u for u, l in letti.items() if l is None]
    if mancano:
        sys.exit(f"il lettore non ha risposto per {mancano}: ricostruzione annullata, la mappa resta com'era")
    ora_vecchia = {(a["u"].lower(), norm(a["n"])): a["ts"] for a in gioco.animali}
    gioco.dati["animali"] = [a for a in gioco.animali if a["k"] == "tifo"]
    for u in sorted(per, key=lambda u: per[u][0].get("timestamp", "")):
        suoi = per[u]
        if letti[u]["rimuovi"]:
            continue
        gioco.riconcilia(u, letti[u], lambda cid, suoi=suoi: next((c.get("timestamp") for c in suoi if c["id"] == cid), suoi[0].get("timestamp")))
    # le luci accese all'inizio mantengono l'ora originale, così i Fondatori restano gli stessi quando il comune è giusto
    for a in gioco.animali:
        a["ts"] = min(a["ts"], ora_vecchia.get((a["u"].lower(), norm(a["n"])), a["ts"]))
    gioco.ricalcola()
    da_fare = []
    for u, suoi in per.items():
        l = letti[u]
        dopo = {(norm(a["n"]), a["c"], a["k"]) for a in gioco.animali if a["u"].lower() == u.lower() and a["k"] != "tifo"}
        miei = [a for a in gioco.animali if a["u"].lower() == u.lower() and a["k"] != "tifo"]
        testo = None
        if dopo != prima.get(u.lower(), set()):
            if miei:
                elenco = ", ".join(f"{a['n']} {'ad' if a['c'][:1] in 'AaEe' else 'a'} {a['c']}" + (" ✦" if a["k"] == "stella" else " 👑" if a.get("ruolo") else "") for a in miei)
                testo = (f"Avevo capito male, scusa 🙈 Ora è giusto: {elenco} ✨" if prima.get(u.lower())
                         else f"Eccoci! Si accende la luce: {elenco} ✨")
                if not gioco.stato.get("seguono", {}).get(u.lower()):
                    testo += " " + invito_segui(gioco, u)
            elif l["senza_comune"]:
                testo = frase("manca_comune_nome", n=l["senza_comune"][0]["n"])
            elif l["senza_nome"] and l["senza_nome"][0].get("luogo"):
                testo = frase("manca_nome", c=l["senza_nome"][0]["luogo"]["c"])
            elif l["estero"]:
                testo = frase("estero")
        domande = [c for c in suoi if "?" in c.get("text", "") and re.search(SPECIE_RE, norm(c.get("text", "")))]
        if testo:
            bersaglio = next((c for c in reversed(suoi) if not solo_tag(c.get("text", ""))), suoi[-1])
            da_fare.append((u, bersaglio, [c["id"] for c in suoi], testo))
        elif domande:
            da_fare.append((u, domande[-1], [domande[-1]["id"]], frase("altri")))
    for u in sorted(set(prima) - {x.lower() for x in per}):
        print(f"  (nessun commento letto per @{u}: le sue luci sono state tolte)")
    for u, c, canc, testo in da_fare:
        print(f"@{u}: «{c.get('text', '')[:90]}»\n   ↳ {testo}")
    print(f"luci prima: {sum(len(v) for v in prima.values())} · dopo: {sum(1 for a in gioco.animali if a['k'] != 'tifo')} · risposte da fare: {len(da_fare)}")
    if prova:
        for a in sorted(gioco.animali, key=lambda a: a["u"]):
            print(f"   {a['u'][:20]:20} {a['k'][:6]:6} {a['t']:5} {a.get('specie', ''):9} {a['n']:16} {a['c']} ({a['p']}) {a.get('razza')}|{a.get('razza_testo')} {a['pt']}pt {a.get('ruolo', '')}")
        return
    gioco.salva()
    fatte = 0
    for u, c, canc, testo in da_fare:
        try:
            for cid in canc: cancella(cid)
            rispondi(c["id"], testo); fatte += 1
        except Exception as e:
            print(f"risposta non inviata a @{u}: {e}", file=sys.stderr)
        time.sleep(2)  # piano: tante risposte di fila sembrano spam
    print(f"mappa ricostruita · risposte inviate: {fatte}")

def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--prova":
        prove = json.loads(Path(sys.argv[2]).read_text())
        gira((("prova", c) for c in prove), lambda cid, t: print(f"  ↳ risposta a {cid}: {t}"))
        return
    token = os.environ.get("IG_TOKEN")
    if not token:
        sys.exit("Manca IG_TOKEN: va messo nei Secrets del repository.")
    ig = Instagram(token)
    me = ig.io()
    if "--diagnosi" in sys.argv:  # cosa vede il motore, senza toccare la mappa
        print("account:", me.get("username"))
        print("profilo:", ig._req("GET", "me", fields="username,followers_count,media_count"))
        for met, extra in (("reach", {"period": "day"}), ("profile_views", {"period": "day", "metric_type": "total_value"}),
                           ("follower_count", {"period": "day"}), ("accounts_engaged", {"period": "day", "metric_type": "total_value"})):
            try:
                print("profilo", met, json.dumps(ig._req("GET", "me/insights", metric=met, **extra).get("data", []))[:400])
            except urllib.error.HTTPError as e:
                print("profilo", met, "n/d", e.code, e.read()[:150])
        for m in ig.pagine("me/media", fields="id,timestamp,media_type,media_product_type,comments_count,like_count,permalink", limit=10):
            print("media:", m)
            metriche = ["views", "reach", "likes", "comments", "shares", "saved", "total_interactions"]
            if m.get("media_product_type") == "REELS":
                metriche += ["ig_reels_avg_watch_time", "ig_reels_video_view_total_time"]
            st = {}
            for met in metriche:  # una per volta: se una non esiste per quel tipo, le altre si leggono lo stesso
                try:
                    d = ig._req("GET", f"{m['id']}/insights", metric=met).get("data", [])
                    if d: st[met] = d[0].get("values", [{}])[0].get("value", d[0].get("total_value", {}).get("value"))
                except urllib.error.HTTPError as e:
                    st[met] = f"n/d {e.code}"
            print("   statistiche:", json.dumps(st))
            for c in ig.pagine(f"{m['id']}/comments", fields="id,text,timestamp,username,from", limit=50):
                print("   commento:", c)
            for prova in ({}, {"fields": "comments{id,text,username}"}):
                path = f"{m['id']}/comments" if not prova else m["id"]
                try:
                    print("   grezzo", path, prova, "→", ig._req("GET", path, **prova))
                except urllib.error.HTTPError as e:
                    print("   grezzo", path, prova, "→ errore", e.code, e.read()[:300])
        return
    if "--ricostruisci" in sys.argv:
        lista = [(m["id"], c) for m in ig.reel_recenti() for c in ig.commenti(m["id"])]
        ricostruisci(lista, ig.rispondi, me.get("username"), lambda cid: ig.cancella_mie_risposte(cid, me.get("username", "zampeditalia")),
                     "--a-secco" in sys.argv)
        return
    def tutti():
        # Instagram li restituisce dal più recente: in ordine di arrivo il Fondatore è davvero il primo
        lista = [(m["id"], c) for m in ig.reel_recenti() for c in ig.commenti(m["id"])]
        return sorted(lista, key=lambda x: x[1].get("timestamp", ""))
    gira(tutti(), ig.rispondi, me.get("username"), lambda cid: ig.cancella_mie_risposte(cid, me.get("username", "zampeditalia")))

if __name__ == "__main__":
    main()
