"""Pubblica su Instagram un'immagine, un reel o una storia già online sul sito (Instagram vuole un URL pubblico).

Uso (su GitHub Actions, con IG_TOKEN nei Secrets):
  python motore/pubblica.py --tipo IMAGE  --media media/come-si-gioca.jpg --didascalia contenuti/post-come-si-gioca.txt
  python motore/pubblica.py --tipo REELS  --media media/lancio.mp4        --didascalia contenuti/lancio.txt
  python motore/pubblica.py --tipo STORIES --media media/storia.jpg

I percorsi sono relativi a docs/, cioè al sito pubblicato su GitHub Pages.
"""
import argparse, json, os, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITO = "https://zampeditalia.it/"
API = "https://graph.instagram.com/v23.0"
REGISTRO = ROOT / "motore/pubblicati.json"

def chiama(method, path, token, **params):
    params["access_token"] = token
    url = f"{API}/{path}"
    data = None
    if method == "GET":
        url += "?" + urllib.parse.urlencode(params)
    else:
        data = urllib.parse.urlencode(params).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data, method=method), timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        # il messaggio d'errore di Instagram non contiene il token: si può stampare
        sys.exit(f"Instagram ha risposto {e.code}: {json.loads(e.read()).get('error', {}).get('message')}")

def pronto(cont, token, minuti=10):
    """Aspetta che Instagram finisca di elaborare un contenitore; esce con errore se lo rifiuta."""
    for _ in range(minuti * 6):
        stato = chiama("GET", cont, token, fields="status_code").get("status_code")
        if stato in (None, "FINISHED"):
            return
        if stato in ("ERROR", "EXPIRED"):
            sys.exit(f"Instagram non ha accettato il media: {stato}")
        time.sleep(10)
    sys.exit("Instagram non ha finito di elaborare il media in tempo")

def main():
    a = argparse.ArgumentParser()
    a.add_argument("--tipo", choices=["IMAGE", "REELS", "STORIES", "CAROSELLO"], required=True)
    a.add_argument("--media", required=True)
    a.add_argument("--didascalia")
    a.add_argument("--prova", action="store_true", help="prepara il contenitore senza pubblicare")
    a.add_argument("--tag", default="", help="account da taggare nel reel, separati da virgola: ricevono la notifica e il reel va nel loro profilo")
    a.add_argument("--trial", action="store_true", help="Trial Reel: mostrato prima solo a chi non segue; se Instagram lo rifiuta si pubblica normale")
    o = a.parse_args()
    token = os.environ.get("IG_TOKEN") or sys.exit("Manca IG_TOKEN.")
    url = SITO + o.media.lstrip("/")
    caption = (ROOT / "docs" / o.didascalia).read_text().strip() if o.didascalia else ""

    if o.tipo == "CAROSELLO":
        # ogni slide è un contenitore a sé, poi il carosello le raccoglie (massimo 10)
        figli = [chiama("POST", "me/media", token, image_url=SITO + m.strip().lstrip("/"), is_carousel_item="true")["id"] for m in o.media.split(",")[:10]]
        for f in figli: pronto(f, token)
        print(f"slide pronte: {len(figli)}")
        cont = chiama("POST", "me/media", token, media_type="CAROUSEL", children=",".join(figli), caption=caption)["id"]
        pronto(cont, token)
        time.sleep(5)
        pub = chiama("POST", "me/media_publish", token, creation_id=cont)["id"]
        info = chiama("GET", pub, token, fields="permalink,timestamp")
        print(f"pubblicato: {info.get('permalink')}")
        reg = json.loads(REGISTRO.read_text()) if REGISTRO.exists() else []
        reg.append({"id": pub, "tipo": "CAROSELLO", "media": o.media, "permalink": info.get("permalink"), "ts": datetime.now(timezone.utc).isoformat(timespec="seconds")})
        REGISTRO.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n")
        return
    params = {"caption": caption} if caption and o.tipo != "STORIES" else {}
    video = o.media.lower().endswith((".mp4", ".mov"))
    params["video_url" if video else "image_url"] = url
    if o.tipo != "IMAGE":
        params["media_type"] = o.tipo
    if o.tipo == "REELS":
        params["share_to_feed"] = "true"
    cont = None
    if o.trial and o.tipo == "REELS":
        # Meta promuove da solo il reel ai follower se va bene con chi non ci segue
        try:
            cont = chiama("POST", "me/media", token, trial_params=json.dumps({"graduation_strategy": "SS_PERFORMANCE"}), **params)["id"]
            print("Trial Reel accettato da Instagram")
        except SystemExit as e:
            print(f"Trial Reel rifiutato ({e}); pubblico come reel normale")
    tag = [t.strip().lstrip("@") for t in o.tag.split(",") if t.strip()][:20]
    if not cont and tag and o.tipo == "REELS":
        try:
            cont = chiama("POST", "me/media", token, user_tags=json.dumps([{"username": t} for t in tag]), **params)["id"]
            print(f"reel con {len(tag)} persone taggate")
        except SystemExit as e:
            print(f"tag rifiutati da Instagram ({e}); pubblico senza tag")
    if not cont:
        cont = chiama("POST", "me/media", token, **params)["id"]
    print(f"contenitore pronto: {cont}")

    # i video vengono elaborati da Instagram: si aspetta che il contenitore sia pronto (massimo 10 minuti)
    for _ in range(60):
        stato = chiama("GET", cont, token, fields="status_code").get("status_code")
        if stato in (None, "FINISHED"):
            break
        if stato in ("ERROR", "EXPIRED"):
            sys.exit(f"Instagram non ha accettato il media: {stato}")
        time.sleep(10)
    if o.prova:
        print("prova: non pubblico")
        return

    pub = chiama("POST", "me/media_publish", token, creation_id=cont)["id"]
    info = chiama("GET", pub, token, fields="permalink,timestamp")
    print(f"pubblicato: {info.get('permalink')}")
    reg = json.loads(REGISTRO.read_text()) if REGISTRO.exists() else []
    reg.append({"id": pub, "tipo": o.tipo, "media": o.media, "permalink": info.get("permalink"),
                "ts": datetime.now(timezone.utc).isoformat(timespec="seconds")})
    REGISTRO.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n")

if __name__ == "__main__":
    main()
