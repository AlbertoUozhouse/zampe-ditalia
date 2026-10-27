"""Messaggi privati di @zampeditalia: chi scrive CARTOLINA riceve in DM la cartolina del suo animale, da mettere in storia.

Instagram lascia scrivere in privato solo a chi ci ha scritto per primo (entro 24 ore), per questo il bot invita a mandare
la parola CARTOLINA. Gira dentro la guardia in due tempi:
disegna le cartoline (reel/cartolina.py) in docs/cartoline/ con un nome casuale, le pubblica, aspetta GitHub Pages e le manda.

Uso:
  python3 motore/messaggi.py              # un giro
  python3 motore/messaggi.py --diagnosi   # dice solo se l'API dei messaggi risponde e quante conversazioni vede

Il repository è pubblico e i log di GitHub li vede chiunque: qui non si stampano MAI testi dei messaggi né nomi, solo conteggi.
"""
import hashlib, json, os, re, subprocess, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "motore"))
from commenti import API, Gioco, Instagram, carica, norm  # noqa: E402

STATO = ROOT / "motore/messaggi.json"
ANIMALI = ROOT / "docs/data/animali.json"
CARTOLINE = ROOT / "docs/cartoline"
SITO = "https://zampeditalia.it/"
PAROLA = re.compile(r"(?i)cartolin")
SEGUE = re.compile(r"(?i)\b(ti seguo|seguo|seguito|seguita|follow)\b")


def manda(ig, igsid, messaggio):
    body = json.dumps({"recipient": {"id": igsid}, "message": messaggio}).encode()
    req = urllib.request.Request(f"{API}/me/messages?access_token={urllib.parse.quote(ig.token)}", data=body,
                                 headers={"content-type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def conversazioni(ig):
    campi = "id,updated_time,participants,messages.limit(10){id,from,to,message,created_time}"
    yield from ig.pagine("me/conversations", platform="instagram", fields=campi, limit=25)


def online(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=15) as r:
            return r.status == 200
    except Exception:
        return False


def main():
    ig = Instagram(os.environ.get("IG_TOKEN") or sys.exit("Manca IG_TOKEN"))
    me = ig.io()
    mio_id, mio = str(me.get("user_id") or me.get("id")), me.get("username", "zampeditalia").lower()
    if "--diagnosi" in sys.argv:
        try:
            conv = list(conversazioni(ig))
            print(f"API dei messaggi: ok · conversazioni: {len(conv)} · messaggi letti: {sum(len(c.get('messages', {}).get('data', [])) for c in conv)}")
        except urllib.error.HTTPError as e:
            err = json.loads(e.read() or b"{}").get("error", {})
            print(f"API dei messaggi: errore {e.code} · {err.get('type')} · codice {err.get('code')} · {str(err.get('message'))[:160]}")
        return
    st = carica(STATO, {"fatti": []})
    fatti = set(st["fatti"])  # solo impronte (hash) dei messaggi già visti: nel repository pubblico non finisce chi ci scrive
    dati = carica(ANIMALI, {"animali": []})
    limite = (datetime.now(timezone.utc) - timedelta(hours=23)).isoformat()
    richieste, seguono = [], []
    for conv in conversazioni(ig):
        for m in conv.get("messages", {}).get("data", []):
            da = m.get("from", {})
            impronta = hashlib.sha256(("zampe" + m["id"]).encode()).hexdigest()[:16]
            if impronta in fatti or str(da.get("id")) == mio_id or (da.get("username") or "").lower() == mio:
                continue
            fatti.add(impronta)
            if m.get("created_time", "").replace("+0000", "+00:00") < limite:
                continue
            if PAROLA.search(m.get("message") or "") and not any(r[1] == da.get("id") for r in richieste):
                richieste.append((da.get("username", ""), da.get("id")))
            elif SEGUE.search(m.get("message") or "") and not any(r[1] == da.get("id") for r in seguono):
                seguono.append((da.get("username", ""), da.get("id")))
    if seguono:  # SEGUO scritto in privato vale come nei commenti: +10 una volta sola
        gioco = Gioco(); gioco.migra_punti()
        for u, igsid in seguono:
            esito = gioco.segue(u)
            testo = {"segue": "Grazie per il follow! 🎉 +10 punti per te, li vedi già in classifica su zampeditalia.it",
                     "segue_senza_luce": "Grazie per il follow! 🎉 I tuoi +10 punti arrivano appena accendi la luce del tuo animale: "
                                         "scrivi sotto un nostro reel città, nome e animale (per esempio «Treviso, Luna, golden») ✨"}.get(esito)
            try:
                if testo: manda(ig, igsid, {"text": testo})
            except urllib.error.HTTPError as e:
                print(f"messaggio non mandato: errore {e.code}", file=sys.stderr)
        gioco.salva()
        print(f"messaggi: SEGUO in privato {len(seguono)}")
    pronte = []
    for u, igsid in richieste:
        suoi = [a for a in dati["animali"] if a["u"].lower() == u.lower() and a["k"] in ("animale", "sogno", "stella")]
        try:
            if not suoi:
                manda(ig, igsid, {"text": "Ciao! 🐾 Prima accendi la luce del tuo animale: scrivi sotto un nostro reel città, nome e animale "
                                          "(per esempio «Treviso, Luna, golden»). Poi riscrivimi CARTOLINA e te la disegno ✨"})
                continue
            uscita = subprocess.run([sys.executable, str(ROOT / "reel/cartolina.py"), u], capture_output=True, text=True)
            nomi = [l.strip() for l in uscita.stdout.splitlines() if l.strip().endswith(".png")]
            if uscita.returncode or not nomi:
                print(f"cartolina non disegnata: {uscita.stderr[-300:]}", file=sys.stderr); continue
            manda(ig, igsid, {"text": f"Sto disegnando la cartolina di {', '.join(a['n'] for a in suoi[:3])} 🎨 Arriva qui tra pochi minuti!"})
            pronte.append((igsid, [SITO + "cartoline/" + n for n in nomi]))
        except urllib.error.HTTPError as e:
            print(f"messaggio non mandato: errore {e.code}", file=sys.stderr)
    st["fatti"] = sorted(fatti)[-20000:]
    # in attesa: solo l'ID anonimo che Instagram dà alla nostra app e l'indirizzo dell'immagine, niente nomi né testi
    st["in_attesa"] = st.get("in_attesa", []) + [{"igsid": i, "url": urls, "t": time.time()} for i, urls in pronte]
    STATO.write_text(json.dumps(st, indent=0) + "\n")
    if pronte:  # si pubblicano le immagini nuove; GitHub Pages di solito ci mette 1-2 minuti
        subprocess.run("git add docs/cartoline motore/messaggi.json && git commit -q -m 'Cartoline' && "
                       "(git pull -q --rebase -X theirs; git push -q)", shell=True, cwd=ROOT)
        fine = time.time() + 300
        while time.time() < fine and not all(online(u) for r in st["in_attesa"] for u in r["url"]):
            time.sleep(20)
    resta, mandate = [], 0
    for r in st["in_attesa"]:
        if not all(online(u) for u in r["url"]):
            if time.time() - r["t"] < 6 * 3600:
                resta.append(r)  # il sito non l'ha ancora pubblicata: si riprova al prossimo giro
            continue
        try:
            for u in r["url"]:
                manda(ig, r["igsid"], {"attachment": {"type": "image", "payload": {"url": u}}})
            manda(ig, r["igsid"], {"text": "Eccola! 💌 Mettila nella tua storia e tagga @zampeditalia ✨ "
                                           "Vuoi far salire la tua città? Tagga gli amici sotto i reel: +3 punti per ognuno che commenta, e chi ne porta di più oggi è il Re degli inviti 👑"})
            mandate += 1
        except urllib.error.HTTPError as e:
            print(f"cartolina non mandata: errore {e.code}", file=sys.stderr)
    if st["in_attesa"] or resta:
        st["in_attesa"] = resta
        STATO.write_text(json.dumps(st, indent=0) + "\n")
    print(f"messaggi: cartoline nuove {len(pronte)} · mandate {mandate} · in attesa {len(resta)}")


if __name__ == "__main__":
    main()
