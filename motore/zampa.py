"""Zampa, il protagonista della serie «Zampa ha 30 giorni per trovare casa», in foto realistiche fatte con l'IA (15/11).

Alberto: «il cane mi fa schifo, fammi un cane reale e bello» → immagini IA, come la pagina di Ugo (che è fatta così).
Prima si fa il ritratto di riferimento (sempre lo stesso cane), poi ogni scena di ogni puntata parte dal riferimento,
così Zampa è uguale in tutte le foto. Le foto restano in reel/assets/zampa/ (si fanno una volta sola) e i reel le usano
come sfondo a tutto schermo, coi contatori e le scritte sopra (reel/modello/scene.py zampa30).

La chiave sta solo nei Secrets di GitHub (OPENAI_API_KEY): lo script gira dentro .github/workflows/zampa.yml.
Uso: python3 motore/zampa.py ritratto            (il riferimento; si rifà solo se lo si cancella)
     python3 motore/zampa.py puntata bagno       (le 4 foto della puntata; quelle già fatte non si rifanno)
     python3 motore/zampa.py tutte               (tutte le puntate scritte)
"""
import base64, json, os, sys, urllib.error, urllib.request, uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CARTELLA = ROOT / "reel/assets/zampa"
MODELLO = "gpt-image-1"
STILE = ("Photorealistic, high-quality smartphone photo, natural soft light, shallow depth of field, warm colors, vertical 2:3 framing "
         "with the dog in the middle and empty space at the top and bottom for captions. No text, no letters, no watermark, no logos.")
ZAMPA = ("Zampa: a beautiful golden-retriever-like dog with long golden fur, floppy ears, warm brown eyes, a happy face and a worn red leather collar "
         "with a brass buckle, exactly like the reference photo. Always the same dog.")  # 15/11: il ritratto l'ha scelto Alberto con ChatGPT (reel/assets/zampa/riferimento.png)

# per ogni puntata (motore/copione.py SERIE_PUNTATE): la foto di ogni scena, e l'ultima per la scelta di domani
SCENE = {
    "inizio": ["Zampa sitting alone behind the bars of a kennel in an Italian animal shelter, looking sad at the camera, a bit dirty and messy fur, a few flies around.",
               "Zampa in the shelter yard posing awkwardly for an adoption photo, a volunteer (only hands visible) holding a small camera in front of him.",
               "Zampa with a chewed broken compact camera in his mouth, pieces on the floor, a guilty but proud face.",
               "Zampa looking straight at the camera with hopeful eyes, head slightly tilted, in the shelter."],
    "bagno": ["Zampa standing in a small bathtub full of foam in a shelter washroom, ears down, refusing the bath.",
              "Zampa shaking water everywhere, three volunteers (seen from behind, faces not visible) completely soaked, holding umbrellas, splashes in the air.",
              "Zampa clean and fluffy, wrapped in a towel, looking proud and happy; in the background a man in a soaked shirt (face not visible).",
              "Zampa clean and fluffy looking straight at the camera with hopeful eyes, head tilted."],
    "veterinario": ["Zampa in a veterinary clinic running away from a vet in a white coat (face not visible), a stethoscope on the table.",
                    "Zampa hiding inside an open cabinet full of gauze rolls in the vet clinic, only his head peeking out.",
                    "Zampa sitting on a veterinary scale with a small puddle under it, innocent face.",
                    "Zampa at the vet clinic looking straight at the camera with hopeful eyes."],
    "toelettatura": ["Zampa on a grooming table at a dog groomer, a groomer's hands holding scissors and a comb.",
                     "Zampa after grooming with a ridiculous fluffy poodle-like haircut and a small bow, looking surprised.",
                     "The empty grooming salon with an apron and scissors left on the table, Zampa with the fluffy haircut alone on the table.",
                     "Zampa with the fluffy haircut looking straight at the camera, hopeful."],
    "zampa": ["Zampa in the shelter yard, a volunteer's hand open in front of him asking for the paw, a dog biscuit in the other hand.",
              "Zampa lying happily on top of a volunteer sitting on the grass (face not visible), paws on his chest.",
              "Zampa surrounded by crumbs and an empty biscuit box, very satisfied face.",
              "Zampa looking straight at the camera with hopeful eyes, crumbs on his nose."],
    "guinzaglio": ["Zampa on a leash on a city sidewalk, first walk outside the shelter, excited.",
                   "Zampa pulling hard on the leash chasing a pigeon, the volunteer's arm stretched (only the arm visible).",
                   "Zampa happily running ahead on a long road dragging the leash, a tired volunteer far behind (small, from behind).",
                   "Zampa sitting on the sidewalk looking straight at the camera, tongue out, hopeful."],
    "dieta": ["Zampa in front of a bowl full of raw carrots, looking at it with disgust.",
              "Close-up of Zampa staring at the camera with an offended look, the carrot bowl next to him.",
              "Zampa's dog bed in the kennel with many carrots hidden under the blanket, Zampa pretending to sleep.",
              "Zampa looking straight at the camera with hopeful eyes."],
    "gatta": ["Zampa in the shelter facing a small bossy tabby cat sitting on a crate higher than him.",
              "The tabby cat staring Zampa down, Zampa's ears flattened, intimidated.",
              "The tabby cat sleeping comfortably on top of Zampa who lies on the floor without moving, resigned face.",
              "Zampa with the cat sleeping on his back, looking at the camera."],
    "foto": ["Zampa sitting in front of a simple photo backdrop with a softbox light, ready for a portrait.",
             "Zampa photographed mid-blink with eyes closed, funny face.",
             "Zampa caught mid-sneeze in front of the photo backdrop, very funny expression.",
             "Zampa finally looking straight at the camera with a beautiful perfect portrait pose."],
    "denti": ["Zampa in a washroom with a dog toothbrush and a tube of toothpaste in front of him, suspicious look.",
              "A volunteer's hand brushing Zampa's teeth, Zampa with a resigned expression.",
              "Zampa with white foam bubbles coming out of his mouth after eating the toothpaste, a squeezed empty tube on the floor.",
              "Zampa with clean shiny teeth smiling at the camera."],
    "cappottino": ["Zampa outdoors at night in the cold, a little light snow, a red knitted Christmas dog coat on the ground next to him.",
                   "Zampa tangled in the red knitted coat, struggling, with a volunteer's hands trying to dress him.",
                   "Zampa wearing the red knitted coat completely wrong, one leg sticking out of the neck hole, proud face, Christmas lights in the background.",
                   "Zampa in the red coat looking at the camera with hopeful eyes, Christmas lights bokeh."],
    "seduto": ["Zampa in the shelter office next to a table with a birthday cake with candles, balloons, a party for the shelter director.",
               "A volunteer's raised finger giving the 'sit' command to Zampa, Zampa looking at the cake.",
               "Zampa sitting right on top of the birthday cake, cream everywhere, guilty face.",
               "Zampa with cream on his nose looking at the camera."],
    "visita": ["A family of three (seen from behind, faces not visible) arriving at the shelter gate, Zampa watching them from his kennel.",
               "Zampa peeking out shyly from behind a kennel door.",
               "Zampa hiding under a parked white van in the shelter yard, only his eyes and nose visible.",
               "Zampa looking at the camera with shy hopeful eyes."],
}


def _chiave():
    return os.environ.get("OPENAI_API_KEY") or sys.exit("Manca OPENAI_API_KEY (va nei Secrets di GitHub).")


def _risposta(req):
    try:
        return json.loads(urllib.request.urlopen(req, timeout=300).read())
    except urllib.error.HTTPError as e:  # il messaggio d'errore di OpenAI non contiene la chiave
        sys.exit(f"OpenAI ha risposto {e.code}: {json.loads(e.read() or b'{}').get('error', {}).get('message', '')[:300]}")


def genera(prompt, uscita):
    corpo = json.dumps({"model": MODELLO, "prompt": prompt, "size": "1024x1536", "quality": "medium", "n": 1}).encode()
    req = urllib.request.Request("https://api.openai.com/v1/images/generations", data=corpo,
                                 headers={"Authorization": f"Bearer {_chiave()}", "Content-Type": "application/json"})
    uscita.write_bytes(base64.b64decode(_risposta(req)["data"][0]["b64_json"]))


def modifica(riferimento, prompt, uscita):
    """Una scena nuova partendo dalla foto di riferimento: lo stesso cane in un'altra situazione."""
    b = uuid.uuid4().hex
    parti = []
    for k, v in (("model", MODELLO), ("prompt", prompt), ("size", "1024x1536"), ("quality", "medium"), ("n", "1")):
        parti.append(f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
    parti.append(f'--{b}\r\nContent-Disposition: form-data; name="image[]"; filename="zampa.png"\r\nContent-Type: image/png\r\n\r\n'.encode()
                 + riferimento.read_bytes() + b"\r\n")
    parti.append(f"--{b}--\r\n".encode())
    req = urllib.request.Request("https://api.openai.com/v1/images/edits", data=b"".join(parti),
                                 headers={"Authorization": f"Bearer {_chiave()}", "Content-Type": f"multipart/form-data; boundary={b}"})
    uscita.write_bytes(base64.b64decode(_risposta(req)["data"][0]["b64_json"]))


def ritratto():
    CARTELLA.mkdir(parents=True, exist_ok=True)
    rif = CARTELLA / "riferimento.png"
    if rif.exists(): print("ritratto già fatto"); return rif
    genera(f"{ZAMPA} Portrait of Zampa sitting and looking at the camera, full body visible, plain soft background. {STILE}", rif)
    print("ritratto di Zampa fatto"); return rif


def puntata(ep):
    rif = ritratto()
    for i, scena in enumerate(SCENE[ep]):
        out = CARTELLA / f"{ep}-{i}.png"
        if out.exists(): continue
        modifica(rif, f"The same dog as in the reference photo ({ZAMPA}) {scena} {STILE}", out)
        print(f"foto fatta: {out.name}")


if __name__ == "__main__":
    cosa = sys.argv[1] if len(sys.argv) > 1 else ""
    if cosa == "ritratto": ritratto()
    elif cosa == "puntata": puntata(sys.argv[2])
    elif cosa == "tutte":
        for ep in SCENE: puntata(ep)
    else: sys.exit(__doc__)
