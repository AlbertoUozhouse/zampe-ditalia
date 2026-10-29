"""Il negozio: accessori da 1 euro in su per il proprio animale, per sempre sulla mappa (osso, fiocco, collare d'oro, corona, fuochi d'artificio).
Ogni acquisto diventa una storia su @zampeditalia col regalo (messaggi.py + reel/cartolina.py --regalo).

Si paga con i Payment Link di Stripe (motore/config.json → "negozio"). Il sito aggiunge al link ?client_reference_id=<codice>,
un codice che lega il pagamento all'animale senza dati personali (lo stesso calcolo di docs/app.js).
Qui si leggono le sessioni pagate con la chiave STRIPE_KEY (Secret di GitHub, chiave limitata in sola lettura) e si dà l'accessorio.
Nei log solo numeri: mai email, nomi o @.
"""
import json, os, time, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARTICOLI = {"osso": ("Osso d'oro", 100), "fiocco": ("Fiocco", 149), "collare": ("Collare d'oro", 199), "corona": ("Corona", 299), "fuochi": ("Fuochi d'artificio", 399), "boost": ("Boost x2 per 24 ore", 100)}  # come in docs/app.js

def _hash(s):
    """FNV-1a a 32 bit, come Disegni.hash in docs/disegni.js."""
    h = 2166136261
    for ch in str(s):
        h ^= ord(ch) if ord(ch) < 0x10000 else 0xD800 + ((ord(ch) - 0x10000) >> 10)
        h = (h * 16777619) & 0xFFFFFFFF
    return h

def _b36(n):
    s = ""
    while True:
        n, r = divmod(n, 36); s = "0123456789abcdefghijklmnopqrstuvwxyz"[r] + s
        if not n: return s

def codice(id_): return "z" + _b36(_hash(id_))

def link():
    """I link di pagamento attivi: {articolo: url}. Vuoto finché il negozio non è aperto."""
    try: cfg = json.loads((ROOT / "motore/config.json").read_text())
    except (FileNotFoundError, json.JSONDecodeError): return {}
    return {k: u for k, u in cfg.get("negozio", {}).items() if k in ARTICOLI and str(u).startswith("https://")}

def _stripe(chiave, percorso, **q):
    r = urllib.request.Request("https://api.stripe.com/v1/" + percorso + "?" + urllib.parse.urlencode(q), headers={"Authorization": "Bearer " + chiave})
    return json.loads(urllib.request.urlopen(r, timeout=30).read())

def leggi(stato, animali):
    """Dà gli accessori pagati. stato["acquisti"] = {id animale: [articoli]}, stato["negozio_fatti"] = sessioni già lette."""
    acquisti = stato.setdefault("acquisti", {})
    chiave, ln = os.environ.get("STRIPE_KEY"), link()
    if chiave and ln:
        try:
            per_url = {u.split("?")[0]: k for k, u in ln.items()}
            plink = {p["id"]: per_url[p["url"]] for p in _stripe(chiave, "payment_links", limit=100)["data"] if p.get("url") in per_url}
            fatti = stato.setdefault("negozio_fatti", [])
            codici = {codice(a.get("id", "")): a.get("id") for a in animali if a.get("id")}
            nuovi = 0
            for s in _stripe(chiave, "checkout/sessions", limit=100, status="complete", **{"created[gte]": int(time.time()) - 3 * 86400})["data"]:
                k, ida = plink.get(s.get("payment_link")), codici.get(s.get("client_reference_id") or "")
                if s["id"] in fatti or s.get("payment_status") != "paid" or not k or not ida: continue
                if k == "boost":  # non è un accessorio: per 24 ore i punti della persona valgono doppio (commenti.py)
                    u = next((a["u"].lower() for a in animali if a.get("id") == ida), None)
                    if u: b = stato.setdefault("boost", {}); b[u] = max(b.get(u, 0), time.time()) + 86400
                elif k not in acquisti.setdefault(ida, []): acquisti[ida].append(k)
                stato.setdefault("negozio_storie", []).append({"id": ida, "k": k})  # messaggi.py ne fa una storia su @zampeditalia
                fatti.append(s["id"]); nuovi += 1
            stato["negozio_fatti"] = fatti[-2000:]
            if nuovi: print(f"negozio: {nuovi} accessori nuovi")
        except Exception as e:
            print(f"negozio: Stripe non risponde ({type(e).__name__}), riprovo al prossimo giro")
    for a in animali:
        if acquisti.get(a.get("id")): a["acc"] = acquisti[a["id"]]
        else: a.pop("acc", None)
    return ln if chiave else {}  # senza la chiave non vedremmo i pagamenti: il negozio resta chiuso, nessuno paga a vuoto
