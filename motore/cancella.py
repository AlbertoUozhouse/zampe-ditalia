"""Cancella da Instagram un contenuto pubblicato da noi, dato il suo id (in motore/pubblicati.json). Solo su richiesta di Alberto.
Uso: python motore/cancella.py <id>  (IG_TOKEN nei Secrets)"""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from pubblica import chiama, REGISTRO

mid = sys.argv[1].strip()
reg = json.loads(REGISTRO.read_text())
if not mid.isdigit() or not any(x["id"] == mid for x in reg):
    sys.exit("id non trovato tra i nostri contenuti: non cancello niente")
print(chiama("DELETE", mid, os.environ["IG_TOKEN"]))
REGISTRO.write_text(json.dumps([{**x, "cancellato": True} if x["id"] == mid else x for x in reg], ensure_ascii=False, indent=1) + "\n")
print("cancellato", mid)
