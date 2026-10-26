"""Genera compositions/sottotitoli.html di un reel HyperFrames dai tempi parola per parola della voce.

Uso: python3 reel/sottotitoli.py <parole.json> <progetto-hyperframes> <durata> "Frase uno" "Frase due" ...
Le frasi sono i gruppi da mostrare (2–4 parole), nell'ordine della voce: devono ricomporre esattamente il testo letto.
"""
import json, sys
from pathlib import Path

# parole chiave, confrontate senza punteggiatura
ORO = {"cani", "cane", "fondatore", "spenta", "accende", "nome", "tifo", "città", "commenti", "vince", "luce", "notte"}
VERDE = {"gatti", "gatto", "tetti"}

def main():
    parole_json, progetto, durata, *frasi = sys.argv[1:]
    P = json.loads(Path(parole_json).read_text())["parole"]
    durata = float(durata)
    gruppi, i = [], 0
    for f in frasi:
        n = len(f.split())
        letto = " ".join(w["p"] for w in P[i:i + n])
        if letto != f:
            sys.exit(f"La frase «{f}» non corrisponde alla voce: «{letto}»")
        gruppi.append((i, i + n - 1)); i += n
    if i != len(P):
        sys.exit(f"Le frasi coprono {i} parole su {len(P)}")

    html, js = [], []
    for gi, (a, b) in enumerate(gruppi):
        ws = P[a:b + 1]
        s = max(0.1, ws[0]["s"] - 0.05)
        e = (P[b + 1]["s"] - 0.03) if b + 1 < len(P) else durata - 0.05
        spans = []
        for wi, w in enumerate(ws):
            k = w["p"].lower().strip(".,:;!?…")
            cls = " or" if k in ORO else " ve" if k in VERDE else ""
            spans.append(f'<span class="w{cls}" id="st-{gi}-{wi}">{w["p"].upper()}</span>')
            js.append(f'tl.fromTo("#st-{gi}-{wi}", {{ scale: 0.6, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.14, ease: "back.out(3)" }}, {max(s, w["s"] - 0.04):.3f});')
        html.append(f'<div class="g" id="st-g{gi}">{" ".join(spans)}</div>')
        js.append(f'tl.set("#st-g{gi}", {{ opacity: 1, visibility: "visible" }}, {s:.3f});')
        js.append(f'tl.to("#st-g{gi}", {{ opacity: 0, duration: 0.1, ease: "power2.in" }}, {e - 0.1:.3f});')
        js.append(f'tl.set("#st-g{gi}", {{ opacity: 0, visibility: "hidden" }}, {e:.3f});')

    righe_html = "\n    ".join(html)
    righe_js = "\n    ".join(js)
    out = f'''<template>
  <style>
    /* Sottotitoli giganti, 2–4 parole alla volta, sincronizzati sulla voce. Parole chiave: oro per i cani, verde-oro per i gatti. */
    #root {{ position: absolute; inset: 0; pointer-events: none; }}
    #root .g {{ position: absolute; left: 0; right: 0; top: 1150px; text-align: center; padding: 0 70px; opacity: 0; visibility: hidden;
      font: 800 92px/1.02 "Bricolage Grotesque", sans-serif; letter-spacing: -1px; color: #FFF4DE; overflow: visible;
      text-shadow: 0 6px 0 #060B1A, 0 0 30px rgba(6, 11, 26, .9), 0 0 6px #060B1A; }}
    #root .w {{ display: inline-block; }}
    #root .or {{ color: #FFC55C; }} #root .ve {{ color: #CFE36B; }}
  </style>
  <div id="root" data-composition-id="sottotitoli" data-width="1080" data-height="1920">
    {righe_html}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    {righe_js}
    window.__timelines["sottotitoli"] = tl;
  </script>
</template>
'''
    Path(progetto, "compositions/sottotitoli.html").write_text(out)
    print(f"{len(gruppi)} gruppi scritti")

if __name__ == "__main__":
    main()
