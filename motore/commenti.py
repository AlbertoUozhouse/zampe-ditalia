"""Motore dei commenti di Zampe d'Italia.

Legge i commenti dei reel recenti (Instagram API with Instagram Login), riconosce i formati del gioco,
aggiorna docs/data/animali.json e risponde secondo le regole del piano.

Uso:
  python motore/commenti.py                 # gira davvero (serve IG_TOKEN nell'ambiente)
  python motore/commenti.py --prova FILE    # legge commenti finti da un JSON e stampa le risposte, senza Instagram

Solo libreria standard, così gira su GitHub Actions senza installare niente.
"""
import json, os, random, re, sys, time, unicodedata, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
from math import cos, radians, sqrt
from pathlib import Path

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
PUNTI = {"animale": 10, "fondatore": 20, "tifo": 5, "sogno": 10, "stella": 0, "giornaliero": 5}

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

    def in_testa(self, testo):
        """Per i commenti senza virgole: cerca il comune più lungo all'inizio o alla fine ("Treviso Luna golden")."""
        w = norm(testo).split()
        for n in range(min(5, len(w) - 1), 0, -1):
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
GATTO_PAROLE = re.compile(r"\b(gatt[oaie]|micio|micia|siames|persian|maine|coon|british|certosin|ragdoll|sphynx|sfinge|soriano|tigrat|tuxedo)")
RAZZE = [  # stesse chiavi di docs/disegni.js
    (r"golden|retriever", "golden"), (r"labrador.*(nero|black)", "labrador_nero"), (r"labrador.*(cioccolat|marrone|choco)", "labrador_cioccolato"),
    (r"labrador|\blab\b", "labrador_miele"), (r"pastore tedesco|tedesco|german|\blupo\b", "pastore_tedesco"), (r"border|collie", "border_collie"),
    (r"husky|siberian", "husky"), (r"beagle", "beagle"), (r"jack|russel", "jack_russell"), (r"bassott|dachs|salsicc", "bassotto"),
    (r"chihuahua|chiuaua|chihuaua", "chihuahua"), (r"barbon|poodle|\btoy\b", "barboncino"), (r"bulldog|frenchie|bouledogue", "bulldog_francese"),
    (r"cavalier|king charles", "cavalier"), (r"shih|tzu|maltes|yorkshire|yorkie", "shih_tzu"), (r"amstaff|pit ?bull|staffordshire|staffy", "amstaff"),
    (r"meticc|incrocio|bastardin|\bmix\b", "meticcio"),
    (r"siames", "siamese"), (r"persian", "persiano"), (r"maine|coon", "maine_coon"), (r"british|certosin", "british"), (r"ragdoll", "ragdoll"),
    (r"sphynx|sfinge|nudo", "sphynx"), (r"bicolor|bianco e nero|bianconer|tuxedo", "bicolore"), (r"\bner[oa]\b", "nero"),
    (r"ross[oa]|arancion|fulv", "rosso"), (r"bianc[oa]", "bianco"), (r"tigrat|soriano|europeo|grigi[oa]", "europeo"),
]
GATTI = {"siamese", "persiano", "maine_coon", "british", "ragdoll", "sphynx", "bicolore", "nero", "rosso", "bianco", "europeo"}

def razza(testo, tipo):
    t = norm(testo)
    for pat, k in RAZZE:
        if re.search(pat, t) and ((k in GATTI) == (tipo == "gatto")):
            return k
    return None

# ---------- riconoscimento dei commenti ----------
def analizza(testo, comuni):
    """Trasforma un commento in un'azione del gioco. Restituisce un dict con 'k' (tipo) oppure con 'manca'."""
    raw = re.sub(r"@\w[\w.]*", " ", testo).strip()           # i tag agli amici non fanno parte del formato
    t = norm(raw)
    if re.fullmatch(r"rimuovi( tutto)?", t):
        return {"k": "rimuovi"}
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
    parti = [p.strip() for p in re.split(r"[,;\n]| - | – ", raw) if p.strip()]
    if len(parti) == 1 and len(parti[0].split()) <= 6:
        c, resto = comuni.in_testa(parti[0])
        if c and resto:
            w = resto.split()
            parti = [c["c"] + " " + c["p"], w[0]] + ([" ".join(w[1:])] if len(w) > 1 else [])
    if len(parti) < 2:
        return None if kind == "animale" else {"k": kind, "manca": "formato"}
    luogo, err, resto = None, None, []
    for p in parti:
        if not luogo:
            c, e = comuni.trova(p)
            if c:
                luogo = c
                continue
            err = err or e
        resto.append(p)
    if not luogo:
        # sembra un tentativo di gioco solo se c'è anche una razza o una parola chiave
        if kind != "animale" or any(razza(p, "cane") or razza(p, "gatto") or GATTO_PAROLE.search(norm(p)) for p in parti):
            return {"k": kind, "manca": err or "comune"}
        return None
    if not resto:
        return {"k": kind, "manca": "nome", "luogo": luogo}
    nome = nome_proprio(resto[0])
    descr = " ".join(resto[1:])
    tipo = "gatto" if GATTO_PAROLE.search(norm(descr)) or razza(descr, "gatto") and not razza(descr, "cane") else "cane"
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
    "vicini": ["{n} è acceso a {c}! I tuoi vicini sono {v1} e {v2} 🐾"],
    "tifo": ["Tifo registrato: +1 per i {squadra} di {c}! 📣", "{c} ringrazia: un tifoso in più per i {squadra}! 🔥"],
    "sogno": ["Il sogno di {n} è in cielo sopra {c} ☁️", "Una nuvoletta in più su {c}: {n} ti aspetta nei sogni ☁️"],
    "stella": ["Una stella per {n} brilla sopra {c}. ✦", "{n} ora è una stella nel cielo di {c}. Sempre con te. ✦"],
    "manca_comune": ["Quasi! In quale comune vive? Scrivi per esempio «Treviso, {n}, golden» 🐾", "Non ho trovato il comune 🙈 Riscrivilo con città, nome e razza!"],
    "manca_provincia": ["Ci sono più comuni con quel nome: aggiungi la provincia, per esempio «Calliano TN» 🗺️"],
    "manca_nome": ["Come si chiama? Riscrivi «{c}, nome, razza» e si accende la sua luce ✨"],
    "manca_razza": ["Che razza è {n}? Scrivi «{c}, {n}, golden» oppure «{c}, {n}, gatto rosso» 🐶🐱"],
    "manca_formato": ["Scrivi per esempio «Sogno: Padova, Bruno, bassotto» oppure «Stella: Treviso, Max» ✨"],
    "rimosso": ["Fatto, abbiamo tolto le tue luci dalla mappa. Ti aspettiamo quando vuoi 🐾"],
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
        if method == "GET":
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
        if k == "rimuovi":
            prima = len(self.animali)
            self.dati["animali"] = [a for a in self.animali if a["u"].lower() != utente.lower()]
            self.cambiato |= prima != len(self.animali)
            return "rimosso", {}, True
        if "manca" in az:
            luogo = az.get("luogo") or {}
            if az.get("n") and any(a["u"].lower() == utente.lower() and norm(a["n"]) == norm(az["n"]) for a in self.animali):
                return None, {}, False  # animale già sulla mappa, riscritto senza razza: niente da chiedere
            return "manca_" + az["manca"], {"n": az.get("n", "il tuo animale"), "c": luogo.get("c", "Treviso")}, True
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
            gia.update(base, t=az["t"], razza=az.get("razza"), ts=gia["ts"])
            self.cambiato = True
            return None, {}, False
        if len(miei) >= MAX_ANIMALI_PER_UTENTE:
            return None, {}, False
        fondatore = k == "animale" and not any(a["k"] == "animale" and a["c"] == L["c"] and a["p"] == L["p"] for a in self.animali)
        pt = PUNTI["fondatore"] if fondatore else PUNTI[k]
        nuovo = {**base, "id": f"{utente}|{k}|{norm(az['n'])}", "k": k, "t": az["t"], "n": az["n"], "razza": az.get("razza"), "pt": pt}
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

    def bonus_giornaliero(self, utente, media_id):
        """+5 una volta al giorno a chi commenta un reel nuovo e ha già una luce."""
        oggi = datetime.now(timezone.utc).date().isoformat()
        chiave = utente.lower()
        if self.stato["bonus"].get(chiave) == oggi:
            return
        miei = [a for a in self.animali if a["u"].lower() == chiave and a["k"] in ("animale", "sogno")]
        if miei:
            max(miei, key=lambda a: a["pt"])["pt"] += PUNTI["giornaliero"]
            self.stato["bonus"][chiave] = oggi
            self.cambiato = True

# ---------- giro principale ----------
def gira(commenti, rispondi, mio_username=None):
    """commenti: iterabile di (media_id, commento); rispondi: funzione(comment_id, testo)."""
    comuni, gioco = Comuni(), Gioco()
    nuovi = risposte = 0
    for media_id, c in commenti:
        if c["id"] in gioco.visti:
            continue
        gioco.visti.add(c["id"])
        utente = c.get("username") or c.get("from", {}).get("username", "")
        if not utente or (mio_username and utente.lower() == mio_username.lower()):
            continue
        nuovi += 1
        az = analizza(c.get("text", ""), comuni)
        prima = len(gioco.animali)
        if az:
            chiave, par, obbligatoria = gioco.applica(az, utente, c.get("timestamp") or datetime.now(timezone.utc).isoformat())
        else:
            chiave, obbligatoria = None, False
        if len(gioco.animali) <= prima:  # il commento che accende una luce ha già i suoi punti
            gioco.bonus_giornaliero(utente, media_id)
        else:
            gioco.stato["bonus"][utente.lower()] = datetime.now(timezone.utc).date().isoformat()
        if not chiave or gioco.risposte_ultima_ora() >= MAX_RISPOSTE_ORA:
            continue
        if obbligatoria or random.random() < QUOTA_RISPOSTE:
            try:
                rispondi(c["id"], frase(chiave, **par))
                gioco.stato["risposte"].append(time.time())
                risposte += 1
            except Exception as e:  # una risposta fallita non deve fermare la mappa
                print(f"risposta non inviata a {c['id']}: {e}", file=sys.stderr)
    gioco.salva()
    luci = sum(1 for a in gioco.animali if a["k"] != "stella")
    print(f"commenti nuovi: {nuovi} · risposte: {risposte} · luci sulla mappa: {luci}")
    return gioco

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
    def tutti():
        for m in ig.reel_recenti():
            for c in ig.commenti(m["id"]):
                yield m["id"], c
    gira(tutti(), ig.rispondi, me.get("username"))

if __name__ == "__main__":
    main()
