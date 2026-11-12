"""Le città raccontate (Alberto 12/11: «possiamo aggiungere qualcosa sulle varie città, così arricchiamo?»).

Per ogni comune che entra in un reel: una frase vera che fa sentire orgoglioso chi è di lì («la città della Disfida»),
presa dal riassunto di Wikipedia in italiano. L'IA la accorcia, ma la frase si tiene solo se le sue parole stanno davvero
nel testo di Wikipedia: niente fatti inventati. Senza rete o senza chiave il reel esce uguale, solo senza la frase.
Le frasi restano in motore/citta.json (una volta per comune, con la fonte).
"""
import json, re, sys, urllib.parse, urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "motore/citta.json"
UA = {"User-Agent": "ZampeDItalia/1.0 (https://zampeditalia.it)"}

SISTEMA = """Ricevi il riassunto di Wikipedia di un comune italiano. Scrivi UNA espressione breve (da 3 a 8 parole) che descriva il comune
con il fatto più caratteristico e di cui chi ci vive va fiero: un soprannome, un monumento, una storia, un prodotto tipico, il mare o i monti.
Deve essere un'apposizione che si legge dopo il nome, per esempio «la città della Disfida» o «il borgo delle ceramiche».
Usa SOLO fatti scritti nel testo, con le parole del testo; niente numeri di abitanti, niente province, niente superlativi inventati.
Se il testo non ha niente di caratteristico rispondi {"fatto": null}. Rispondi solo JSON: {"fatto": "..."}"""


def _carica():
    try: return json.loads(CACHE.read_text())
    except (FileNotFoundError, json.JSONDecodeError): return {}


def wikipedia(comune):
    """Il riassunto della voce del comune (it.wikipedia.org), oppure None."""
    for titolo in (comune, f"{comune} (Italia)"):
        try:
            r = urllib.request.Request("https://it.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(titolo.replace(" ", "_")), headers=UA)
            j = json.loads(urllib.request.urlopen(r, timeout=12).read())
        except Exception as e:
            print(f"citta: Wikipedia non risponde per «{titolo}» ({e})", file=sys.stderr); continue
        testo = j.get("extract") or ""
        if j.get("type") == "standard" and re.search(r"\b(comune|città|frazione|capoluogo)\b", testo[:300], re.I):
            return {"testo": testo, "fonte": j.get("content_urls", {}).get("desktop", {}).get("page", "")}
    return None


def _vero(frase, testo):
    """La frase si tiene solo se almeno due terzi delle sue parole piene (5 lettere o più) stanno nel testo di Wikipedia."""
    t = testo.lower()
    piene = [w for w in re.findall(r"[a-zàèéìòù]+", frase.lower()) if len(w) >= 5]
    return bool(piene) and sum(w[:-1] in t for w in piene) >= max(1, round(len(piene) * 2 / 3))


def fatto(comune, provincia=""):
    """{"fatto": "la città della Disfida" o None, "abitanti": 92000 o None, "fonte": url} per il comune; dalla cache se c'è già."""
    cache = _carica(); k = f"{comune}|{provincia}"
    if k in cache: return cache[k]
    w = wikipedia(comune)
    if not w: return None  # senza rete non si salva niente: si riprova la volta dopo
    m = re.search(r"(\d{1,3}(?:[.\s ]\d{3})+|\d{3,6})\s+abitanti", w["testo"])
    abitanti = int(re.sub(r"\D", "", m.group(1))) if m else None
    frase = None
    try:
        sys.path.insert(0, str(ROOT / "motore")); import agenzia
        r, _ = agenzia.lavora(SISTEMA, f"Comune: {comune}\n\n{w['testo'][:1800]}")
        f = (r or {}).get("fatto")
        if isinstance(f, str) and 2 <= len(f.split()) <= 9 and _vero(f, w["testo"]): frase = f.strip().rstrip(".")
        print(f"citta: {comune} → {('«' + frase + '»') if frase else 'nessuna frase verificata'} (proposta: {f!r})", file=sys.stderr)
    except Exception as e:
        print(f"citta: frase non scritta per {comune} ({e})", file=sys.stderr)
    out = {"fatto": frase, "abitanti": abitanti, "fonte": w["fonte"], "giorno": date.today().isoformat()}
    cache[k] = out; CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1) + "\n")
    return out


def apposizione(comune, provincia=""):
    """«, la città della Disfida,» da mettere dopo il nome nella voce, oppure stringa vuota."""
    f = (fatto(comune, provincia) or {}).get("fatto")
    return f", {f}," if f else ""


if __name__ == "__main__":
    for c in sys.argv[1:]:  # «Barletta|BT» «Bisceglie|BT» …
        print(c, fatto(*(c.split("|") + [""])[:2]))
