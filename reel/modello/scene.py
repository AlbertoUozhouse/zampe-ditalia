"""Scene parametriche per i reel automatici di Zampe d'Italia (HyperFrames, 1080x1920).

Ogni funzione riceve l'id della scena, la sua durata e i parametri del copione, e restituisce il file
compositions/<id>.html. Lo stile è quello dei reel di lancio: Italia di notte, luce calda per i cani,
verde-oro per i gatti. I disegni degli animali arrivano dalla fabbrica (docs/disegni.js) come SVG in assets/svg.
"""
import html, json, re
from pathlib import Path

ESC = html.escape

# Aspetti a rotazione, così due reel di fila non si somigliano: cambiano cielo, colline, prato, strada e mappa; animali e testi restano uguali.
TEMI = {
    "notte":    {"cielo": ("#050A1C", "#14254F", "#24396B"), "colline": "#101E44", "prato": "#0F2A2A", "strada": "#162650", "ombra": "#0B1634", "terra": "#1E3266", "bordo": "#34508F", "costa": "#5577C9", "bg": ("#18295A", "#0E1A3A", "#060B1A")},
    "tramonto": {"cielo": ("#2B1240", "#7A2A55", "#A8473F"), "colline": "#3A1636", "prato": "#2E1E26", "strada": "#3A1A3E", "ombra": "#8C2F5A", "terra": "#5A2350", "bordo": "#8C3F72", "costa": "#F2A65A", "bg": ("#8C2F5A", "#4A1645", "#1E0A24")},
    "aurora":   {"cielo": ("#031A1F", "#0B4D4A", "#17694F"), "colline": "#062B2C", "prato": "#0A2E22", "strada": "#0C3A3A", "ombra": "#0B4D4A", "terra": "#0E4A48", "bordo": "#1F7A70", "costa": "#5FE0B0", "bg": ("#0E5A55", "#06302F", "#021316")},
    # giorno: azzurro abbastanza scuro da tenere il contrasto 3:1 dei testi oro e verdi (il controllo HyperFrames lo pretende)
    "giorno":   {"cielo": ("#123F86", "#1F5FAE", "#2C68B0"), "colline": "#2E6E33", "prato": "#3A7F3E", "strada": "#3E4C5A", "ombra": "#1F5FAE", "terra": "#2E6E33", "bordo": "#4C9A50", "costa": "#E6F2FF", "bg": ("#24508F", "#173A6E", "#0C2448")},
    "neon":     {"cielo": ("#12002B", "#3B0A6B", "#7A1FA2"), "colline": "#22074A", "prato": "#1A0638", "strada": "#2A0A55", "ombra": "#3B0A6B", "terra": "#3B0F70", "bordo": "#8A3FD1", "costa": "#FF5FD2", "bg": ("#5A1890", "#2A0A55", "#12002B")},
}
T = dict(TEMI["notte"])

def usa_tema(nome):
    """Sceglie l'aspetto del reel prima di disegnare le scene (costruisci.py)."""
    T.clear(); T.update(TEMI.get(nome, TEMI["notte"]))

CIELO = """<linearGradient id="{p}-cielo" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c0}"/><stop offset=".6" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient>
<radialGradient id="{p}-alone"><stop offset="0" stop-color="#FFC55C" stop-opacity=".55"/><stop offset="1" stop-color="#FFC55C" stop-opacity="0"/></radialGradient>"""

STELLE = "".join(f'<circle cx="{x}" cy="{y}" r="{r}"/>' for x, y, r in
                 [(90, 380, 2.4), (210, 300, 1.6), (330, 420, 2), (470, 330, 1.4), (610, 390, 2.2), (160, 520, 1.6), (980, 560, 2),
                  (720, 300, 1.5), (40, 640, 1.8), (1030, 380, 1.4), (560, 250, 1.8), (260, 600, 1.3)])

def _primo_fotogramma(js):
    """Prima scena del reel: niente ingressi da vuoto, il primo fotogramma è già pieno e luminoso.
    Gli ingressi fromTo diventano piccoli assestamenti (scala 1.04 → 1), così resta il movimento ma non il buio."""
    # 20/11: solo gli ingressi dei primi 0,6 secondi (quelli che lascerebbero buio il primo fotogramma); quelli dopo restano com'erano,
    # così il tiro in porta e il «GOL!» del reel della partita arrivano al loro momento anche nella prima scena
    return re.sub(r'tl\.fromTo\(("[^"]+"), \{[^}]*\}, \{[^}]*?duration: ([\d.]+)[^}]*\}, ([\d.]+)\);',
                  lambda m: m.group(0) if float(m.group(3)) >= 0.6 else f'tl.fromTo({m.group(1)}, {{ scale: 1.04 }}, {{ scale: 1, duration: {m.group(2)}, ease: "power2.out" }}, 0);', js)

def _pagina(cid, nota, css, corpo, js):
    return f"""<template>
  <style>
    /* {nota} */
    #root {{ position: absolute; inset: 0; overflow: hidden; }}
    #root svg.sf {{ position: absolute; inset: 0; }}
    {css}
  </style>
  <div id="root" data-composition-id="{cid}" data-width="1080" data-height="1920">
    {corpo}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
{js}
    window.__timelines["{cid}"] = tl;
  </script>
</template>
"""

def _sfondo_notte(p, prato=True):
    terra = (f'<path d="M0 960 C200 920 380 950 540 935 C720 920 880 960 1080 930 V1920 H0Z" fill="{T["prato"]}"/>' if prato
             else f'<path d="M0 1240 L540 1060 L1080 1240 V1920 H0Z" fill="{T["strada"]}"/><path d="M0 1240 L540 1060 L1080 1240" fill="none" stroke="{T["costa"]}" stroke-width="6" opacity=".7"/>')
    return f"""<svg class="sf" viewBox="0 0 1080 1920" id="{p}-sf"><defs>{CIELO.format(p=p, c0=T["cielo"][0], c1=T["cielo"][1], c2=T["cielo"][2])}</defs>
      <rect width="1080" height="1920" fill="url(#{p}-cielo)"/><g fill="#fff" opacity=".7">{STELLE}</g>
      <circle cx="860" cy="430" r="150" fill="url(#{p}-alone)" opacity=".5"/><circle cx="860" cy="430" r="62" fill="#FFF4DE"/><circle cx="890" cy="411" r="56" fill="{T["ombra"]}"/>
      <path d="M0 860 C180 790 330 830 470 800 C640 760 800 820 1080 770 V1100 H0Z" fill="{T["colline"]}"/>
      <g fill="#FFC55C"><rect x="110" y="830" width="20" height="15" rx="2"/><rect x="760" y="800" width="20" height="15" rx="2"/><rect x="990" y="780" width="20" height="15" rx="2"/></g>
      {terra}</svg>"""

TARGA_CSS = """#root .targa { font: 800 64px/1 "Bricolage Grotesque", sans-serif; letter-spacing: 5px; padding: 10px 30px; border-radius: 16px; border: 7px solid; }
    #root .targa.d { color: #5A3417; background: #F3DDB0; border-color: #5E3519; box-shadow: 0 0 40px rgba(255,197,92,.6); }
    #root .targa.c { color: #2F3A10; background: #E9F2C4; border-color: #3D4A18; box-shadow: 0 0 40px rgba(207,227,107,.55); }
    #root .tag { margin-top: 18px; font: 900 36px var(--font-body); color: #111; background: #fff; border-radius: 18px; padding: 10px 24px; box-shadow: 0 10px 30px rgba(0,0,0,.4); }"""

# ---------------------------------------------------------------- scene

def cuccia(cid, dur, nome, svg, utente=None, comune=None):
    """Un cane nella sua cuccia accesa, nel giardino di notte, con la targa col nome."""
    sotto = ""
    if utente or comune:
        sotto = f'<span class="tag" id="{cid}-tag">{ESC("@" + utente) if utente else ""}{" · " if utente and comune else ""}{ESC(comune or "")}</span>'
    corpo = f"""{_sfondo_notte(cid)}
    <div class="eroe" id="{cid}-eroe"><img id="{cid}-img" src="assets/svg/{svg}" alt=""><span class="targa d" id="{cid}-targa">{ESC(nome.upper())}</span>{sotto}</div>"""
    css = f"""#root .eroe {{ position: absolute; left: 0; right: 0; top: 420px; display: flex; flex-direction: column; align-items: center; }}
    #root .eroe img {{ width: 560px; filter: drop-shadow(0 0 60px rgba(255,179,71,.65)); }}
    #root .eroe .targa {{ margin-top: -30px; }}
    {TARGA_CSS}"""
    js = f"""    tl.fromTo("#{cid}-sf", {{ scale: 1.1, transformOrigin: "540px 860px" }}, {{ scale: 1, duration: {dur:.2f}, ease: "power2.out" }}, 0);
    tl.fromTo("#{cid}-img", {{ y: 120, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.4, ease: "back.out(1.6)" }}, 0.05);
    tl.fromTo("#{cid}-targa", {{ opacity: 0.2 }}, {{ keyframes: [{{ opacity: 1, duration: 0.05 }}, {{ opacity: 0.35, duration: 0.05 }}, {{ opacity: 1, duration: 0.08 }}] }}, 0.45);"""
    if sotto:
        js += f'\n    tl.fromTo("#{cid}-tag", {{ y: 20, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.3, ease: "back.out(2)" }}, 0.6);'
    return _pagina(cid, f"Cuccia accesa di {nome}.", css, corpo, js)

def gatto(cid, dur, nome, svg, utente=None, comune=None):
    """Un gatto sul tetto con gli occhi che brillano e la targa col nome."""
    sotto = ""
    if utente or comune:
        sotto = f'<span class="tag" id="{cid}-tag">{ESC("@" + utente) if utente else ""}{" · " if utente and comune else ""}{ESC(comune or "")}</span>'
    corpo = f"""{_sfondo_notte(cid, prato=False)}
    <div class="eroe" id="{cid}-eroe"><img id="{cid}-img" src="assets/svg/{svg}" alt=""><span class="targa c" id="{cid}-targa">{ESC(nome.upper())}</span>{sotto}</div>"""
    css = f"""#root .eroe {{ position: absolute; left: 0; right: 0; top: 420px; display: flex; flex-direction: column; align-items: center; }}
    #root .eroe img {{ width: 560px; filter: drop-shadow(0 0 50px rgba(207,227,107,.45)); }}
    #root .eroe .targa {{ margin-top: -40px; }}
    {TARGA_CSS}"""
    js = f"""    tl.fromTo("#{cid}-sf", {{ y: 60 }}, {{ y: 0, duration: {dur:.2f}, ease: "power2.out" }}, 0);
    tl.fromTo("#{cid}-img", {{ y: 160, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.45, ease: "back.out(1.6)" }}, 0.05);
    tl.fromTo("#{cid}-targa", {{ scale: 0.4, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.3, ease: "back.out(2.6)" }}, 0.5);"""
    if sotto:
        js += f'\n    tl.fromTo("#{cid}-tag", {{ y: 20, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.3, ease: "back.out(2)" }}, 0.7);'
    return _pagina(cid, f"Gatto sul tetto: {nome}.", css, corpo, js)

def duello(cid, dur, sinistra, destra, svg_su="golden.svg", svg_giu="gatto-rosso.svg"):
    """Due contendenti uno sopra l'altro col VS: cani contro gatti, o città contro città.
    sinistra/destra: {"titolo": "Torino", "valore": "0 luci"} (valore facoltativo)."""
    def lato(k, d, cls):
        v = f'<b>{ESC(str(d["valore"]))}</b>' if d.get("valore") not in (None, "") else ""
        return f'<div class="nome {cls}" id="{cid}-{k}"><span>{ESC(d["titolo"])}</span>{v}</div>'
    corpo = f"""<div class="metà su"><img id="{cid}-a" src="assets/svg/{svg_su}" alt="">{lato("na", sinistra, "d")}</div>
    <div class="metà giu"><img id="{cid}-b" src="assets/svg/{svg_giu}" alt="">{lato("nb", destra, "c")}</div>
    <div class="vs"><span id="{cid}-vs">VS</span></div>"""
    css = """#root .metà { position: absolute; left: 0; right: 0; height: 400px; display: flex; align-items: center; justify-content: center; gap: 30px; }
    #root .su { top: 340px; background: radial-gradient(ellipse 60% 70% at 50% 60%, rgba(255,179,71,.35), rgba(255,179,71,0) 70%); }
    #root .giu { top: 760px; background: radial-gradient(ellipse 60% 70% at 50% 45%, rgba(207,227,107,.22), rgba(207,227,107,0) 70%); }
    #root .metà img { width: 380px; }
    #root .nome { display: flex; flex-direction: column; font: 800 64px/1 "Bricolage Grotesque", sans-serif; }
    #root .nome b { font: 900 40px var(--font-body); color: var(--cream); margin-top: 10px; }
    #root .nome.d { color: var(--gold); } #root .nome.c { color: var(--cat); }
    #root .vs { position: absolute; left: 0; right: 0; top: 678px; display: flex; justify-content: center; }
    #root .vs span { width: 130px; height: 130px; border-radius: 50%; display: grid; place-items: center; background: var(--night);
      border: 6px solid var(--cream); font: 800 58px/1 var(--font-display); color: var(--cream); box-shadow: 0 0 50px rgba(255,244,222,.45); }"""
    js = f"""    tl.fromTo("#{cid}-a", {{ x: -200, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.35, ease: "power3.out" }}, 0);
    tl.fromTo("#{cid}-b", {{ x: 200, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.35, ease: "power3.out" }}, 0.05);
    tl.fromTo("#{cid}-na", {{ y: 30, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.3, ease: "back.out(2)" }}, 0.2);
    tl.fromTo("#{cid}-nb", {{ y: 30, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.3, ease: "back.out(2)" }}, 0.3);
    tl.fromTo("#{cid}-vs", {{ scale: 0, rotation: 30 }}, {{ scale: 1, rotation: 0, duration: 0.35, ease: "back.out(3)" }}, 0.25);"""
    return _pagina(cid, "Duello: due contendenti e il VS.", css, corpo, js)

def mappa(cid, dur, italia, luci=(), citta=(), zoom=None, subito=False):
    """L'Italia di notte con le luci vere degli animali. citta: [{"nome","x","y","colore": "d"|"c", "testo": "Milano?"}],
    luci: [{"x","y","t": "cane"|"gatto"}], già proiettate nel fotogramma da costruisci.py."""
    pins, js = [], []
    for i, c in enumerate(citta):
        pins.append(f'''<g transform="translate({c["x"]} {c["y"]})"><g class="pin {c.get("colore", "d")}" id="{cid}-pin{i}">
        <circle class="onda" id="{cid}-onda{i}" r="40" fill="none" stroke-width="5"/><circle r="18" class="punto"/>
        <g transform="translate(0 {70 if c["y"] < 560 else -70})"><rect x="-{max(120, 14 * len(c["testo"]))}" y="-38" width="{2 * max(120, 14 * len(c["testo"]))}" height="70" rx="35" fill="rgba(6,11,26,.88)" class="bordo" stroke-width="4"/>
        <text y="13" text-anchor="middle">{ESC(c["testo"])}</text></g></g></g>''')
        t = c.get("t", 0.3 + i * 0.35)
        if subito:  # prima scena del reel: la città è già accesa nel primo fotogramma
            t = 0.0
        else:
            js.append(f'    tl.fromTo("#{cid}-pin{i}", {{ scale: 0, svgOrigin: "0 0" }}, {{ scale: 1, duration: 0.3, ease: "back.out(3)" }}, {t:.2f});')
        js.append(f'    for (let k = 0; k < 2; k++) tl.fromTo("#{cid}-onda{i}", {{ attr: {{ r: 20 }}, opacity: 1 }}, {{ attr: {{ r: 80 }}, opacity: 0, duration: 0.5, ease: "power1.out" }}, {t + 0.15:.2f} + k * 0.5);')
    # con tante luci i pallini si rimpiccioliscono: l'Italia deve sembrare ancora quasi al buio, da accendere (a 1.000 luci, raggio 5 invece di 30)
    r0 = round(max(4.5, min(30, 30 * (100 / max(len(luci), 1)) ** 0.8)), 1)
    pallini = "".join(f'<circle cx="{l["x"]}" cy="{l["y"]}" r="{l.get("r", r0)}" fill="url(#{cid}-{"g" if l["t"] == "gatto" else "glow"})"/>' for l in luci)
    css = f"""#root .terra {{ fill: {T["terra"]}; stroke: {T["bordo"]}; stroke-width: 1.4; }}
    #root .costa {{ fill: none; stroke: {T["costa"]}; stroke-width: 10; opacity: .8; }}""" + """
    #root text { font: 800 42px "Bricolage Grotesque", sans-serif; fill: var(--cream); }
    #root .d .punto { fill: var(--gold); } #root .d .onda, #root .d .bordo { stroke: var(--gold); }
    #root .c .punto { fill: var(--cat); } #root .c .onda, #root .c .bordo { stroke: var(--cat); }"""
    corpo = f"""<svg class="sf" viewBox="0 0 1080 1920"><defs>
      <filter id="{cid}-blur" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="8"/></filter>
      <radialGradient id="{cid}-glow"><stop offset="0" stop-color="#fff"/><stop offset=".25" stop-color="#FFC55C"/><stop offset="1" stop-color="#FFB347" stop-opacity="0"/></radialGradient>
      <radialGradient id="{cid}-g"><stop offset="0" stop-color="#fff"/><stop offset=".25" stop-color="#CFE36B"/><stop offset="1" stop-color="#CFE36B" stop-opacity="0"/></radialGradient></defs>
      <g id="{cid}-italia"><path class="costa" filter="url(#{cid}-blur)" d="{italia}"/><path class="terra" d="{italia}"/>
      <g id="{cid}-luci">{pallini}</g>{"".join(pins)}</g></svg>"""
    zj = ""
    if zoom:
        zj = f'    tl.to("#{cid}-italia", {{ scale: {zoom["s"]}, svgOrigin: "{zoom["x"]} {zoom["y"]}", x: {540 - zoom["x"]}, y: {720 - zoom["y"]}, duration: {max(0.6, dur - 1.0):.2f}, ease: "power2.inOut" }}, 0.85);'
    base = f"""    tl.fromTo("#{cid}-italia", {{ scale: 1.06, svgOrigin: "540 760" }}, {{ scale: 1, duration: 0.8, ease: "power2.out" }}, 0);
    tl.fromTo("#{cid}-luci", {{ opacity: 0 }}, {{ opacity: {1 if len(luci) < 200 else .8}, duration: 0.4 }}, 0.1);"""
    if subito:
        base = f'    tl.fromTo("#{cid}-italia", {{ scale: 1.03, svgOrigin: "540 760" }}, {{ scale: 1, duration: 0.8, ease: "power2.out" }}, 0);'
        luminoso = "".join(f'<circle cx="{c["x"]}" cy="{c["y"]}" r="120" fill="url(#{cid}-glow)" opacity=".55"/>' for c in citta)
        corpo = corpo.replace(f'<g id="{cid}-luci">', f'{luminoso}<g id="{cid}-luci">')
    return _pagina(cid, "Mappa dell'Italia di notte con le luci vere.", css, corpo, "\n".join([base, zj] + js))

def commento(cid, dur, testo):
    """La casella di commento in cui si scrive il formato del gioco, lettera per lettera."""
    spans = "".join(f'<span id="{cid}-c{i}">{"&nbsp;" if ch == " " else ESC(ch)}</span>' for i, ch in enumerate(testo))
    passo = min(0.075, max(0.035, (dur - 1.0) / max(1, len(testo))))
    fine = 0.2 + passo * len(testo)
    css = """#root .carta { position: absolute; left: 80px; right: 80px; top: 560px; background: #fff; border-radius: 40px; padding: 34px 38px;
      box-shadow: 0 30px 80px rgba(0,0,0,.5), 0 0 90px rgba(255,197,92,.25); }
    #root .chi { display: flex; align-items: center; gap: 20px; font: 800 34px var(--font-body); color: #444; }
    #root .avatar { width: 76px; height: 76px; border-radius: 50%; background: linear-gradient(135deg, #FFC55C, #FF8A65); }
    #root .riga { margin-top: 26px; display: flex; align-items: center; justify-content: space-between; gap: 16px; }
    #root .testo { font: 900 52px/1.1 var(--font-body); color: #111; white-space: nowrap; display: flex; align-items: center; overflow: hidden; min-height: 80px; padding: 6px 0; }
    #root .testo span { line-height: 68px; }  /* le emoji sono più alte delle lettere: devono stare dentro la casella */
    #root .invia { font: 900 32px var(--font-body); color: #fff; background: #2B7BFF; border-radius: 999px; padding: 14px 26px; }"""
    corpo = f"""<div class="carta" id="{cid}-carta"><div class="chi"><span class="avatar"></span>@il.tuo.nome</div>
      <div class="riga"><div class="testo">{spans}</div><span class="invia" id="{cid}-invia">Pubblica</span></div></div>"""
    js = f"""    tl.fromTo("#{cid}-carta", {{ y: 90, opacity: 0, scale: 0.92 }}, {{ y: 0, opacity: 1, scale: 1, duration: 0.3, ease: "back.out(1.8)" }}, 0);
    for (let i = 0; i < {len(testo)}; i++) tl.fromTo("#{cid}-c" + i, {{ opacity: 0 }}, {{ opacity: 1, duration: 0.01 }}, 0.2 + i * {passo:.3f});
    tl.fromTo("#{cid}-invia", {{ scale: 1 }}, {{ scale: 0.86, duration: 0.08, yoyo: true, repeat: 1 }}, {fine + 0.1:.2f});"""
    return _pagina(cid, f"Commento d'esempio: {testo}", css, corpo, js)

def numero(cid, dur, grande, sotto, colore="d"):
    """Un numero vero, grande, con la sua spiegazione sotto (per esempio "2" · "luci accese in Italia")."""
    css = """#root .box { position: absolute; left: 0; right: 0; top: 520px; display: flex; flex-direction: column; align-items: center; gap: 18px; text-align: center; padding: 0 80px; }
    #root .n { font: 800 300px/1 "Bricolage Grotesque", sans-serif; letter-spacing: -8px; }
    #root .n.d { color: var(--gold); text-shadow: 0 0 80px rgba(255,197,92,.6); } #root .n.c { color: var(--cat); text-shadow: 0 0 80px rgba(207,227,107,.5); }
    #root .s { font: 900 54px/1.15 var(--font-body); color: var(--cream); }"""
    corpo = f'<div class="box"><span class="n {colore}" id="{cid}-n">{ESC(str(grande))}</span><span class="s" id="{cid}-s">{ESC(sotto)}</span></div>'
    js = f"""    tl.fromTo("#{cid}-n", {{ scale: 0.4, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.4, ease: "back.out(2.4)" }}, 0.05);
    tl.fromTo("#{cid}-s", {{ y: 30, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.3, ease: "back.out(2)" }}, 0.3);"""
    return _pagina(cid, f"Numero vero: {grande} {sotto}", css, corpo, js)

def classifica(cid, dur, titolo, righe):
    """Una classifica corta (massimo 5 righe) con dati veri: [{"nome": "Treviso", "valore": "3 luci"}]."""
    def fs(testo, base, entra):  # 6/11: «Nome · @utente» lungo veniva tagliato e il controllo bloccava il reel: il testo si rimpicciolisce per entrare
        n = len(str(testo)); return base if n <= entra else max(22, int(base * entra / n))
    li = "".join(f'<li id="{cid}-r{i}"><span class="p">{i + 1}</span><span class="w" style="font-size:{fs(r["nome"], 46, 20)}px">{ESC(r["nome"])}</span>'
                 f'<span class="v" style="font-size:{fs(r["valore"], 40, 16)}px">{ESC(str(r["valore"]))}</span></li>'
                 for i, r in enumerate(righe[:5]))
    css = """#root .box { position: absolute; left: 80px; right: 80px; top: 400px; }
    #root h2 { font: 800 64px/1.05 "Bricolage Grotesque", sans-serif; color: var(--gold); text-align: center; margin-bottom: 30px; }
    #root ol { list-style: none; display: flex; flex-direction: column; gap: 16px; }
    #root li { display: grid; grid-template-columns: 70px 1fr auto; align-items: center; gap: 20px; background: rgba(20,36,77,.92); border: 3px solid rgba(85,119,201,.6);
      border-radius: 24px; padding: 18px 26px; font: 900 46px var(--font-body); color: var(--cream); }
    #root li:first-child { border-color: var(--gold); box-shadow: 0 0 40px rgba(255,197,92,.3); }
    #root .p { font: 800 52px "Bricolage Grotesque", sans-serif; color: var(--gold); text-align: center; }
    #root .v { color: var(--gold); max-width: 480px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 40px; }
    #root .w { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; min-width: 0; }"""
    corpo = f'<div class="box"><h2 id="{cid}-t">{ESC(titolo)}</h2><ol>{li}</ol></div>'
    js = f'    tl.fromTo("#{cid}-t", {{ y: -30, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.3, ease: "back.out(2)" }}, 0);\n'
    js += "\n".join(f'    tl.fromTo("#{cid}-r{i}", {{ x: 120, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.3, ease: "power3.out" }}, {0.25 + i * 0.18:.2f});' for i in range(len(righe[:5])))
    return _pagina(cid, f"Classifica: {titolo}", css, corpo, js)

def vetrina(cid, dur, animali):
    """Una griglia di 4–6 animali disegnati, ognuno col nome della razza: [{"svg": "beagle.svg", "nome": "Beagle", "t": "cane"}]."""
    celle = "".join(f'<div class="cella {"c" if a.get("t") == "gatto" else "d"}" id="{cid}-a{i}"><img src="assets/svg/{a["svg"]}" alt=""><span>{ESC(a["nome"])}</span></div>'
                    for i, a in enumerate(animali[:6]))
    css = """#root .griglia { position: absolute; left: 60px; right: 60px; top: 380px; display: grid; grid-template-columns: 1fr 1fr; gap: 26px 20px; }
    #root .cella { display: flex; flex-direction: column; align-items: center; }
    #root .cella img { width: 300px; }
    #root .cella.d img { filter: drop-shadow(0 0 30px rgba(255,179,71,.5)); } #root .cella.c img { filter: drop-shadow(0 0 26px rgba(207,227,107,.45)); }
    #root .cella span { margin-top: -6px; font: 800 38px "Bricolage Grotesque", sans-serif; color: var(--cream); background: rgba(6,11,26,.85); border-radius: 14px; padding: 4px 16px; }"""
    js = "\n".join(f'    tl.fromTo("#{cid}-a{i}", {{ scale: 0.4, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.3, ease: "back.out(2.2)" }}, {0.05 + i * 0.16:.2f});' for i in range(len(animali[:6])))
    return _pagina(cid, "Vetrina di razze disegnate.", css, f'<div class="griglia">{celle}</div>', js)

def chiusura(cid, dur, testo, svg_su="golden.svg", svg_giu="gatto-rosso.svg"):
    """Chiusura in loop: cane e gatto col VS e il pulsante con l'azione da fare nei commenti."""
    base = duello(cid, dur, {"titolo": "Cani"}, {"titolo": "Gatti"}, svg_su, svg_giu)
    extra_css = """#root .cta { position: absolute; left: 0; right: 0; top: 300px; display: flex; justify-content: center; }
    #root .cta span { font: 900 42px var(--font-body); color: #2A1606; background: var(--gold); border-radius: 22px; padding: 16px 34px; box-shadow: 0 0 50px rgba(255,197,92,.7); }"""
    base = base.replace("  </style>", f"    {extra_css}\n  </style>", 1)
    base = base.replace("  </div>\n  <script>", f'    <div class="cta"><span id="{cid}-cta">{ESC(testo)}</span></div>\n  </div>\n  <script>', 1)
    base = base.replace(f'    window.__timelines["{cid}"] = tl;',
                        f'    tl.fromTo("#{cid}-cta", {{ y: -30, scale: 0.6, opacity: 0 }}, {{ y: 0, scale: 1, opacity: 1, duration: 0.35, ease: "back.out(2.4)" }}, 0.6);\n'
                        f'    tl.to("#{cid}-cta", {{ scale: 1.08, duration: 0.15, yoyo: true, repeat: 1 }}, {max(1.2, dur - 1.2):.2f});\n    window.__timelines["{cid}"] = tl;')
    return base

def foto(cid, dur, file, nome, utente=None, comune=None):
    """La foto vera di un animale (mandata da chi lo ha, col suo permesso): grande, con lo sfondo sfocato della stessa foto e la targa col nome."""
    sotto = ""
    if utente or comune:
        sotto = f'<span class="tag" id="{cid}-tag">{ESC("@" + utente) if utente else ""}{" · " if utente and comune else ""}{ESC(comune or "")}</span>'
    corpo = f"""<div class="sfoca" style="background-image:url('assets/img/{file}')"></div>
    <div class="eroe" id="{cid}-eroe"><div class="cornice" id="{cid}-img"><img src="assets/img/{file}" alt=""></div><span class="targa d" id="{cid}-targa">⭐ {ESC(nome.upper())}</span>{sotto}</div>"""
    css = f"""#root .sfoca {{ position: absolute; inset: -60px; background-size: cover; background-position: center; filter: blur(40px) brightness(.45); }}
    #root .eroe {{ position: absolute; left: 0; right: 0; top: 330px; display: flex; flex-direction: column; align-items: center; }}
    #root .cornice {{ width: 860px; height: 1000px; border-radius: 48px; overflow: hidden; border: 10px solid #FFF4DE; box-shadow: 0 30px 90px rgba(0,0,0,.6); }}
    #root .cornice img {{ width: 100%; height: 100%; object-fit: cover; }}
    #root .eroe .targa {{ margin-top: -46px; }}
    {TARGA_CSS}"""
    js = f"""    tl.fromTo("#{cid}-img", {{ scale: 1.08 }}, {{ scale: 1, duration: {dur:.2f}, ease: "power1.out" }}, 0);
    tl.fromTo("#{cid}-targa", {{ y: 30, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.35, ease: "back.out(2)" }}, 0.3);"""
    if sotto:
        js += f'\n    tl.fromTo("#{cid}-tag", {{ y: 20, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.3, ease: "back.out(2)" }}, 0.55);'
    return _pagina(cid, f"Foto vera: {nome}.", css, corpo, js)

def luce(cid, dur, img, w, h, centro, punti, intorno=(), s0=0.46, s1=1.7, accendi=0.35, vicino=False, italia_c=None, volo="italia"):
    """La mappa del sito nel reel (stessa immagine dell'Italia di notte, strumenti/rilievo.py): si parte da tutta l'Italia,
    si scende sul comune e il punto passa da spento ad acceso. centro/punti/intorno sono già in pixel dell'immagine.
    punti: [{"x","y","testo","acceso": True|False}] (acceso False = si accende in scena); intorno: le altre luci vere vicine."""
    cx, cy = centro
    fx, fy = 540, 800  # dove arriva il comune nel fotogramma
    glow = f'<radialGradient id="{cid}-gl"><stop offset="0" stop-color="#FFF6DC"/><stop offset=".22" stop-color="#FFC35A"/><stop offset=".6" stop-color="#FF9F2E" stop-opacity=".35"/><stop offset="1" stop-color="#FF9F2E" stop-opacity="0"/></radialGradient>'
    vicine = "".join(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="7" fill="url(#{cid}-gl)"/>' for x, y in intorno)
    pp, etichette, js = [], [], []
    for i, q in enumerate(punti):
        on = q.get("acceso", True)
        if q.get("spento"):  # un comune che resta al buio: punto grigio e un anello che lo indica (test di crescita: il paese al buio)
            pp.append(f'<g transform="translate({q["x"]:.0f} {q["y"]:.0f})"><circle r="22" fill="#05070F" opacity=".88"/><circle r="22" fill="none" stroke="#C9D3EA" stroke-width="2.5" stroke-dasharray="5 4"/>'
                      f'<circle r="5" fill="#6E7A99"/><circle id="{cid}-onda{i}" r="24" fill="none" stroke="#FFFFFF" stroke-width="3" opacity="0"/></g>')
            if q.get("testo"): etichette.append(f'<div class="pill buio" id="{cid}-t{i}" data-i="{i}">{ESC(q["testo"])}</div>')
            t_on = accendi * dur
            for k in range(3):
                js.append(f'    tl.fromTo("#{cid}-onda{i}", {{ attr: {{ r: 24 }}, opacity: 1 }}, {{ attr: {{ r: 70 }}, opacity: 0, duration: 0.8, ease: "power1.out" }}, {t_on + k * 0.7:.2f});')
            if q.get("testo"): js.append(f'    tl.fromTo("#{cid}-t{i}", {{ y: 20, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.3, ease: "back.out(2)" }}, {t_on + 0.1:.2f});')
            continue
        pp.append(f'<g transform="translate({q["x"]:.0f} {q["y"]:.0f})"><circle id="{cid}-sp{i}" r="5" fill="#6E7A99" stroke="#C9D3EA" stroke-width="1.5" opacity="{0 if on else 1}"/>'
                  f'<circle id="{cid}-on{i}" r="40" fill="url(#{cid}-gl)" opacity="{1 if on else 0}"/><circle id="{cid}-onda{i}" r="8" fill="none" stroke="#FFD27A" stroke-width="2.5" opacity="0"/></g>')
        if q.get("testo"):
            etichette.append(f'<div class="pill" id="{cid}-t{i}" data-i="{i}">{ESC(q["testo"])}</div>')
        t_on = accendi * dur if not on else 0.6
        if not on:
            js.append(f'    tl.to("#{cid}-sp{i}", {{ opacity: 0, duration: 0.15 }}, {t_on:.2f});')
            js.append(f'    tl.fromTo("#{cid}-on{i}", {{ opacity: 0, attr: {{ r: 4 }} }}, {{ opacity: 1, attr: {{ r: 46 }}, duration: 0.45, ease: "back.out(3)" }}, {t_on:.2f});')
        for k in range(2):
            js.append(f'    tl.fromTo("#{cid}-onda{i}", {{ attr: {{ r: 8 }}, opacity: .95 }}, {{ attr: {{ r: 70 }}, opacity: 0, duration: 0.7, ease: "power1.out" }}, {t_on + 0.05 + k * 0.55:.2f});')
        js.append(f'    tl.fromTo("#{cid}-t{i}", {{ y: 20, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.3, ease: "back.out(2)" }}, {t_on + 0.15:.2f});' if q.get("testo") else "")
    # le etichette stanno nel fotogramma (non si ingrandiscono): sotto il comune, una per riga
    css = f"""#root .mondo {{ position: absolute; left: 0; top: 0; width: {w}px; height: {h}px; transform-origin: 0 0; }}
    #root .mondo img, #root .mondo svg {{ position: absolute; left: 0; top: 0; width: {w}px; height: {h}px; }}
    #root .pills {{ position: absolute; left: 60px; right: 60px; top: {300 if any(q.get("spento") for q in punti) else fy + 70}px; display: flex; flex-direction: column; align-items: center; gap: 14px; }}
    #root .pill {{ font: 800 48px/1.1 "Bricolage Grotesque", sans-serif; color: #FFF4DE; background: rgba(4,12,36,.86); border: 4px solid #FFC35A; border-radius: 999px; padding: 12px 34px; text-align: center; }}
    #root .pill.buio {{ border-color: #C9D3EA; color: #C9D3EA; }}"""
    corpo = f"""<div class="mondo" id="{cid}-m"><img src="assets/img/italia-notte.jpg" alt=""><svg viewBox="0 0 {w} {h}"><defs>{glow}</defs><g>{vicine}</g>{"".join(pp)}</svg></div>
    <div class="pills">{"".join(etichette)}</div>"""
    # da tutta l'Italia al comune: trasformazione della «carta» (scala attorno all'origine, poi spostamento)
    ix, iy = italia_c or (w * 0.5, h * 0.5)  # il centro dell'Italia nell'immagine (costruisci.py)
    a = (540 - ix * s0, 900 - iy * s0)
    b = (fx - cx * s1, fy - cy * s1)
    if volo == "regione":  # test di crescita 8/11: niente volo da tutta l'Italia (uguale in ogni reel): si parte già sulla zona
        a = (fx - cx * s1 * 0.55, fy - cy * s1 * 0.55); s0 = s1 * 0.55
    if vicino:  # seconda scena sullo stesso comune: si resta vicini, niente volo da tutta l'Italia
        a = (b[0] + cx * s1 * 0.06, b[1] + cy * s1 * 0.06); s0 = s1 * 0.94
    js.insert(0, f'    tl.fromTo("#{cid}-m", {{ x: {a[0]:.0f}, y: {a[1]:.0f}, scale: {s0} }}, {{ x: {b[0]:.0f}, y: {b[1]:.0f}, scale: {s1}, duration: {max(0.8, accendi * dur - 0.05):.2f}, ease: "power2.inOut" }}, 0);')
    # 8/11: l'avvicinamento finale tiene il comune fermo al suo posto (prima si spostava di cx·0.08, troppo con lo zoom alto)
    js.append(f'    tl.to("#{cid}-m", {{ x: {fx - cx * s1 * 1.08:.0f}, y: {fy - cy * s1 * 1.08:.0f}, scale: {s1 * 1.08:.3f}, duration: {max(0.4, dur * (1 - accendi)):.2f}, ease: "none" }}, {accendi * dur:.2f});')
    return _pagina(cid, "La mappa del sito: un punto si accende.", css, corpo, "\n".join(j for j in js if j))

def gancio(cid, dur, testo, sotto="", icona=""):
    """Il gancio del primo fotogramma (test di crescita, 8/11): la frase si legge a volume zero già al fotogramma 0.
    Le parole tra *asterischi* sono in oro. Come prima scena, gli ingressi diventano solo un piccolo assestamento (_primo_fotogramma)."""
    pulito = testo.replace("*", "")
    fs = 132 if len(pulito) <= 24 else max(84, int(132 * 24 / len(pulito)))
    parti = re.split(r"(\*[^*]+\*)", testo)
    h = "".join(f'<span class="o">{ESC(x[1:-1])}</span>' if x.startswith("*") else ESC(x) for x in parti if x)
    css = f"""#root .box {{ position: absolute; left: 70px; right: 70px; top: 360px; display: flex; flex-direction: column; align-items: center; gap: 30px; text-align: center; }}
    #root .ic {{ font-size: 150px; line-height: 1; filter: drop-shadow(0 0 40px rgba(255,197,92,.45)); }}
    #root h1 {{ font: 800 {fs}px/1.0 "Bricolage Grotesque", sans-serif; letter-spacing: -2px; color: #FFF4DE; text-transform: uppercase;
      text-shadow: 0 8px 0 #060B1A, 0 0 40px rgba(6,11,26,.9); }}
    #root h1 .o {{ color: var(--gold); }}
    #root .s {{ font: 900 50px/1.15 var(--font-body); color: #FFF4DE; background: rgba(6,11,26,.72); border: 3px solid rgba(255,197,92,.6); border-radius: 26px; padding: 14px 30px; }}"""
    corpo = (f'<div class="box">' + (f'<div class="ic" id="{cid}-i">{ESC(icona)}</div>' if icona else "") + f'<h1 id="{cid}-h">{h}</h1>'
             + (f'<div class="s" id="{cid}-s">{ESC(sotto)}</div>' if sotto else "") + "</div>")
    js = f'    tl.fromTo("#{cid}-h", {{ scale: 0.8, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.4, ease: "back.out(2)" }}, 0);'
    if icona: js += f'\n    tl.fromTo("#{cid}-i", {{ y: -20, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.4, ease: "back.out(2)" }}, 0);'
    if sotto: js += f'\n    tl.fromTo("#{cid}-s", {{ y: 20, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.3, ease: "back.out(2)" }}, 0);'
    return _pagina(cid, f"Gancio: {pulito}", css, corpo, js)

# ================================================================ formati nuovi (12/11, Alberto: «voglio video nuovi, idee diverse, basta sempre ste cose»)
# Niente mappa e niente paese: il quiz della razza e le figurine da collezione. Le animazioni usano tl.set/tl.to (non fromTo),
# così come prima scena il primo fotogramma è già pieno senza che _primo_fotogramma schiacci la sequenza.

SPOT = """#root .spot {{ position: absolute; inset: 0; background: radial-gradient(ellipse 70% 45% at 50% 46%, {a} 0, {b} 55%, #05030F 100%); }}
    #root .raggi {{ position: absolute; left: 50%; top: 46%; width: 2400px; height: 2400px; margin: -1200px 0 0 -1200px;
      background: repeating-conic-gradient(from 0deg, rgba(255,255,255,.05) 0 6deg, transparent 6deg 18deg); }}"""

def sagoma(cid, dur, svg, manche="1/2", titolo="INDOVINA LA RAZZA"):
    """Il quiz: la sagoma nera dell'animale sotto un riflettore, un anello che si consuma (il tempo per rispondere)."""
    css = SPOT.format(a="#4B2A8C", b="#1A0F3D") + """
    #root .tit { position: absolute; left: 0; right: 0; top: 300px; text-align: center; font: 800 96px/1 "Bricolage Grotesque", sans-serif; color: #FFF4DE; letter-spacing: -1px;
      text-shadow: 0 8px 0 #05030F, 0 0 40px rgba(155,120,255,.7); }
    #root .man { position: absolute; left: 50%; top: 420px; transform: translateX(-50%); font: 900 40px var(--font-body); color: #2A1606; background: #FFC55C; border-radius: 999px; padding: 6px 26px; }
    #root .ogg { position: absolute; left: 50%; top: 820px; width: 720px; height: 720px; margin: -360px 0 0 -360px; }
    #root .ogg img { position: absolute; left: 80px; top: 80px; width: 560px; height: 560px; object-fit: contain; filter: brightness(0) drop-shadow(0 0 26px rgba(190,160,255,.95)); }
    #root .ogg svg { position: absolute; inset: 0; transform: rotate(-90deg); }
    #root .q { position: absolute; left: 0; right: 0; top: 520px; text-align: center; font: 800 520px/1 "Bricolage Grotesque", sans-serif; color: rgba(255,255,255,.06); }"""
    corpo = f"""<div class="spot"></div><div class="raggi" id="{cid}-r"></div><div class="q">?</div>
    <div class="tit" id="{cid}-t">{ESC(titolo)}</div><div class="man">{ESC(manche)}</div>
    <div class="ogg" id="{cid}-o"><svg viewBox="0 0 720 720"><circle cx="360" cy="360" r="340" fill="none" stroke="rgba(255,255,255,.12)" stroke-width="18"/>
      <circle id="{cid}-a" cx="360" cy="360" r="340" fill="none" stroke="#FFC55C" stroke-width="18" stroke-linecap="round" stroke-dasharray="2136" stroke-dashoffset="0"/></svg>
      <img id="{cid}-img" src="assets/svg/{svg}" alt=""></div>"""
    js = f"""    tl.to("#{cid}-r", {{ rotation: 25, duration: {dur:.2f}, ease: "none" }}, 0);
    tl.to("#{cid}-a", {{ attr: {{ "stroke-dashoffset": 2136 }}, duration: {max(0.6, dur - 0.2):.2f}, ease: "none" }}, 0);
    tl.to("#{cid}-img", {{ scale: 1.06, duration: {dur / 2:.2f}, ease: "sine.inOut", yoyo: true, repeat: 1 }}, 0);
    tl.to("#{cid}-o", {{ keyframes: [{{ x: -8, duration: 0.05 }}, {{ x: 8, duration: 0.05 }}, {{ x: -5, duration: 0.05 }}, {{ x: 0, duration: 0.05 }}] }}, {max(0.1, dur - 0.45):.2f});"""
    return _pagina(cid, "Quiz: la sagoma della razza.", css, corpo, js)

def svela(cid, dur, svg, razza, riga=""):
    """La risposta del quiz: lampo, l'animale a colori, il nome della razza e quanti ce ne sono davvero sulla mappa."""
    css = SPOT.format(a="#C47A1E", b="#3A1A08") + """
    #root .tit { position: absolute; left: 40px; right: 40px; top: 300px; text-align: center; font: 800 112px/1 "Bricolage Grotesque", sans-serif; color: #FFC55C; letter-spacing: -2px;
      text-shadow: 0 8px 0 #1A0A02, 0 0 50px rgba(255,197,92,.8); }
    #root .ogg { position: absolute; left: 50%; top: 820px; width: 720px; height: 720px; margin: -360px 0 0 -360px; }
    #root .ogg img { position: absolute; left: 80px; top: 80px; width: 560px; height: 560px; object-fit: contain; filter: drop-shadow(0 0 50px rgba(255,197,92,.7)); }
    #root .riga { position: absolute; left: 60px; right: 60px; top: 1300px; text-align: center; }
    #root .riga span { font: 900 44px/1.2 var(--font-body); color: #FFF4DE; background: rgba(26,10,2,.78); border: 3px solid #FFC55C; border-radius: 26px; padding: 12px 26px; display: inline-block; }
    #root .lampo { position: absolute; inset: 0; background: #FFF6E0; }"""
    corpo = f"""<div class="spot"></div><div class="raggi" id="{cid}-r"></div>
    <div class="tit" id="{cid}-t">{ESC(razza.upper())}</div>
    <div class="ogg"><img id="{cid}-img" src="assets/svg/{svg}" alt=""></div>
    {f'<div class="riga"><span id="{cid}-g">{ESC(riga)}</span></div>' if riga else ""}<div class="lampo" id="{cid}-l"></div>"""
    js = f"""    tl.set("#{cid}-img", {{ scale: 1.25 }}, 0); tl.set("#{cid}-t", {{ scale: 2.2, opacity: 0 }}, 0);
    tl.to("#{cid}-l", {{ opacity: 0, duration: 0.35, ease: "power2.out" }}, 0);
    tl.to("#{cid}-img", {{ scale: 1, duration: 0.5, ease: "back.out(2.2)" }}, 0.02);
    tl.to("#{cid}-t", {{ scale: 1, opacity: 1, duration: 0.35, ease: "back.out(2.6)" }}, 0.12);
    tl.to("#{cid}-r", {{ rotation: -30, duration: {dur:.2f}, ease: "none" }}, 0);"""
    if riga:
        js += f'\n    tl.set("#{cid}-g", {{ y: 30, opacity: 0 }}, 0); tl.to("#{cid}-g", {{ y: 0, opacity: 1, duration: 0.3, ease: "back.out(2)" }}, 0.55);'
    return _pagina(cid, f"Quiz: è un {razza}.", css, corpo, js)

RARITA = {"comune": ("#6FB6FF", "#2E5AA8", "COMUNE"), "rara": ("#FFE08A", "#C98A1E", "★ RARA"), "leggendaria": ("#FF7AD9", "#6A4CFF", "★★ LEGGENDARIA")}

def figurina(cid, dur, svg, nome, comune, razza, numero, totale, rarita="comune", motivo="", busta=False):
    """La figurina da collezione: (busta che si apre), la carta che gira, il bagliore olografico che passa sopra."""
    c1, c2, etich = RARITA.get(rarita, RARITA["comune"])
    css = SPOT.format(a="#1E3F7A", b="#0A1430") + f"""
    #root .carta {{ position: absolute; left: 230px; top: 330px; width: 620px; height: 800px; border-radius: 34px; padding: 16px;
      background: linear-gradient(135deg, {c1}, {c2}); box-shadow: 0 30px 80px rgba(0,0,0,.6), 0 0 60px {c1}88; transform-style: preserve-3d; overflow: hidden; }}
    #root .dentro {{ position: absolute; inset: 16px; border-radius: 22px; background: linear-gradient(180deg, #FFF8EA, #F1E3C6); overflow: hidden; }}
    #root .num {{ position: absolute; left: 22px; right: 22px; top: 18px; display: flex; justify-content: space-between; font: 900 30px var(--font-body); color: #3A2410; }}
    #root .fin {{ position: absolute; left: 34px; right: 34px; top: 74px; height: 430px; border-radius: 20px; background: radial-gradient(circle at 50% 45%, {c1}, {c2}); border: 5px solid #3A2410; }}
    #root .fin img {{ position: absolute; left: 50%; top: 50%; width: 480px; height: 480px; margin: -240px 0 0 -240px; object-fit: contain; filter: drop-shadow(0 12px 18px rgba(0,0,0,.35)); }}
    #root .nome {{ position: absolute; left: 20px; right: 20px; top: 522px; text-align: center; font: 800 {78 if len(nome) <= 10 else max(46, int(78 * 10 / len(nome)))}px/1 "Bricolage Grotesque", sans-serif; color: #2A1606; }}
    #root .info {{ position: absolute; left: 20px; right: 20px; top: 612px; text-align: center; font: 900 34px/1.15 var(--font-body); color: #5A3A1A; }}
    #root .rar {{ position: absolute; left: 50%; bottom: 26px; transform: translateX(-50%); white-space: nowrap; font: 900 30px var(--font-body); color: #FFF; background: linear-gradient(90deg, {c2}, {c1}); border-radius: 999px; padding: 8px 24px; }}
    #root .holo {{ position: absolute; inset: -40%; background: linear-gradient(115deg, transparent 40%, rgba(255,255,255,.75) 48%, rgba(255,120,220,.35) 52%, rgba(120,220,255,.35) 56%, transparent 64%); }}
    #root .busta {{ position: absolute; left: 210px; top: 300px; width: 660px; height: 860px; }}
    #root .busta .p {{ position: absolute; left: 0; right: 0; border-radius: 18px; background: linear-gradient(160deg, #F2F4FF 0%, #B9C3E8 30%, #FFFFFF 48%, #8E9BD0 70%, #E8ECFF 100%);
      box-shadow: inset 0 0 0 8px rgba(255,255,255,.35), 0 30px 80px rgba(0,0,0,.6); display: flex; align-items: center; justify-content: center; }}
    #root .busta .su {{ top: 0; height: 180px; border-radius: 18px 18px 6px 6px; }}
    #root .busta .giu {{ top: 186px; height: 674px; flex-direction: column; gap: 18px; text-align: center; }}
    #root .busta b {{ font: 800 92px/0.95 "Bricolage Grotesque", sans-serif; color: #1E2A6A; }}
    #root .busta i {{ font: 900 italic 40px var(--font-body); color: #C0392B; background: #FFE08A; border-radius: 12px; padding: 6px 18px; }}"""
    corpo = f"""<div class="spot"></div><div class="raggi" id="{cid}-r"></div>
    <div class="carta" id="{cid}-c"><div class="dentro"><div class="num"><span>Nº {numero:04d}</span><span>ZAMPE D'ITALIA</span></div>
      <div class="fin"><img src="assets/svg/{svg}" alt=""></div><div class="nome">{ESC(nome)}</div><div class="info">{ESC(razza)} · {ESC(comune)}</div>
      <div class="rar">{ESC(etich)}{(" · " + ESC(motivo)) if motivo else ""}</div></div><div class="holo" id="{cid}-h"></div></div>"""
    js = f"""    tl.to("#{cid}-r", {{ rotation: 30, duration: {dur:.2f}, ease: "none" }}, 0);
    tl.set("#{cid}-h", {{ x: -700 }}, 0);"""
    if busta:
        corpo += f"""<div class="busta" id="{cid}-b"><div class="p su" id="{cid}-bs"><b style="font-size:46px">✂︎ · · · · · · · · · · ·</b></div>
      <div class="p giu" id="{cid}-bg"><b>FIGURINE<br>DELLE ZAMPE</b><i>Nº ? di {totale}</i><b style="font-size:150px">🐾</b></div></div>"""
        js += f"""
    tl.set("#{cid}-c", {{ rotationY: 90, opacity: 0, y: 160 }}, 0);
    tl.to("#{cid}-b", {{ keyframes: [{{ rotation: -3, duration: 0.07 }}, {{ rotation: 3, duration: 0.07 }}, {{ rotation: -2, duration: 0.07 }}, {{ rotation: 0, duration: 0.07 }}] }}, 0.1);
    tl.to("#{cid}-bs", {{ y: -520, rotation: -28, opacity: 0, duration: 0.5, ease: "power2.in" }}, 0.4);
    tl.to("#{cid}-bg", {{ y: 900, opacity: 0, duration: 0.55, ease: "power2.in" }}, 0.75);
    tl.to("#{cid}-c", {{ rotationY: 0, opacity: 1, y: 0, duration: 0.6, ease: "back.out(1.8)" }}, 0.8);
    tl.to("#{cid}-h", {{ x: 700, duration: 1.1, ease: "power1.inOut", repeat: 2, repeatDelay: 0.5 }}, 1.3);"""
    else:
        js += f"""
    tl.set("#{cid}-c", {{ rotationY: -90, opacity: 0 }}, 0);
    tl.to("#{cid}-c", {{ rotationY: 0, opacity: 1, duration: 0.55, ease: "back.out(1.8)" }}, 0.05);
    tl.to("#{cid}-h", {{ x: 700, duration: 1.1, ease: "power1.inOut", repeat: 2, repeatDelay: 0.5 }}, 0.6);"""
    return _pagina(cid, f"Figurina Nº {numero}: {nome}.", css, corpo, js)


def barre(cid, dur, titolo, righe, evidenzia=None, conto=False):
    """La gara a barre (12/11, la gara dei follower): le città in fila, le barre crescono una dopo l'altra, la prima ha la corona.
    righe: [{"nome": "Napoli", "valore": 28, "nota": "la città del Vesuvio"}] in ordine; evidenzia: il nome da accendere."""
    righe = [dict(r) for r in righe[:8]]; mx = max([r["valore"] or 0 for r in righe] + [1])
    for r in righe:  # conto alla rovescia (13/11): il primo resta nascosto, lo svela la scena dopo
        if r["valore"] is None: r["_n"] = True; r["valore"] = mx; r["nome"] = "? ? ?"
    css = SPOT.format(a="#16365F", b="#08142E") + """
    #root .tit { position: absolute; left: 50px; right: 50px; top: 300px; text-align: center; font: 800 76px/1 "Bricolage Grotesque", sans-serif; color: #FFC55C; text-shadow: 0 6px 0 #05030F; }
    #root .lista { position: absolute; left: 60px; right: 60px; top: 420px; display: flex; flex-direction: column; gap: 14px; }
    #root .r { position: relative; height: 76px; border-radius: 18px; background: rgba(255,255,255,.07); overflow: hidden; }
    #root .r i { position: absolute; left: 0; top: 0; bottom: 0; border-radius: 18px; background: linear-gradient(90deg, #2E5AA8, #5AA9F5); }
    #root .r.p i { background: linear-gradient(90deg, #E8A93A, #FFD27A); } #root .r.na i { background: repeating-linear-gradient(45deg, #3A2E12 0 18px, #5A4618 18px 36px); width: 100% !important; }
    #root .r.na { outline: 4px dashed #FFC55C; outline-offset: -4px; } #root .r.ev i { background: linear-gradient(90deg, #C2185B, #FF5FA2); }
    #root .r b { position: absolute; left: 22px; top: 50%; transform: translateY(-50%); font: 900 38px var(--font-body); color: #FFF4DE; text-shadow: 0 2px 6px rgba(0,0,0,.6); white-space: nowrap; }
    #root .r b small { font-size: 26px; opacity: .85; font-weight: 800; }
    #root .r span { position: absolute; right: 22px; top: 50%; transform: translateY(-50%); font: 800 44px "Bricolage Grotesque", sans-serif; color: #FFF4DE; }"""
    li = "".join(f'<div class="r{" p" if i == 0 else ""}{" na" if r.get("_n") else ""}{" ev" if evidenzia and r["nome"] == evidenzia else ""}" id="{cid}-r{i}"><i id="{cid}-b{i}" style="width:{max(18, round(100 * r["valore"] / mx))}%"></i>'
                 f'<b>{"👑 " if i == 0 else f"{i + 1}. "}{ESC(r["nome"])}{f" <small>· {ESC(r["nota"])}</small>" if r.get("nota") else ""}</b><span>{"?" if r.get("_n") else r["valore"]}</span></div>' for i, r in enumerate(righe))
    corpo = f'<div class="spot"></div><div class="raggi" id="{cid}-x"></div><div class="tit">{ESC(titolo)}</div><div class="lista">{li}</div>'
    js = f'    tl.to("#{cid}-x", {{ rotation: 20, duration: {dur:.2f}, ease: "none" }}, 0);'
    for i in range(len(righe)):
        t0 = 0.15 + (len(righe) - 1 - i) * (max(0.3, (dur - 0.9) / len(righe)) if conto else 0.22)  # dall'ultima alla prima; nel conto alla rovescia una alla volta, con la voce
        if conto: js += f'\n    tl.set("#{cid}-r{i}", {{ opacity: 0, x: 80 }}, 0); tl.to("#{cid}-r{i}", {{ opacity: 1, x: 0, duration: 0.3, ease: "power3.out" }}, {t0:.2f});'
        js += f'\n    tl.set("#{cid}-b{i}", {{ scaleX: 0, transformOrigin: "0 50%" }}, 0); tl.to("#{cid}-b{i}", {{ scaleX: 1, duration: 0.5, ease: "power3.out" }}, {t0:.2f});'
    return _pagina(cid, f"Gara a barre: {titolo}", css, corpo, js)

def _griglia(cid, base, altro, dove, righe, colonne, lato):
    """Le celle del rompicapo: tutte uguali tranne una (dove = (riga, colonna) da 0). Piccole rotazioni fisse, così l'occhio deve cercare."""
    x0 = (1080 - colonne * lato) / 2; out = []
    for r in range(righe):
        for c in range(colonne):
            k = r * colonne + c; rot = ((k * 37) % 13) - 6; sc = 1.16 + ((k * 53) % 9) / 100  # i disegni hanno margine: ingranditi riempiono la cella
            qui = (r, c) == tuple(dove)
            ident = f'id="{cid}-x" ' if qui else ""
            out.append(f'<img {ident}src="assets/svg/{altro if qui else base}" alt="" '
                       f'style="left:{x0 + c * lato:.0f}px;top:{r * lato:.0f}px;width:{lato}px;height:{lato}px;transform:rotate({rot}deg) scale({sc:.2f})">')
    return "".join(out)

INTRUSO_CSS = """#root .tit {{ position: absolute; left: 40px; right: 220px; top: 296px; text-align: left; padding-left: 50px; font: 800 {fs}px/1.02 "Bricolage Grotesque", sans-serif; color: #FFF4DE; text-shadow: 0 6px 0 #05030F; }}
    #root .tit b {{ color: #FFC55C; }}
    #root .gr {{ position: absolute; left: 0; top: 452px; width: 1080px; height: {h}px; }}
    #root .gr img {{ position: absolute; object-fit: contain; filter: drop-shadow(0 6px 8px rgba(0,0,0,.45)); }}
    #root .tempo {{ position: absolute; left: 70px; right: 70px; top: 418px; height: 16px; border-radius: 999px; background: rgba(255,255,255,.14); overflow: hidden; }}
    #root .tempo i {{ display: block; height: 100%; width: 100%; background: linear-gradient(90deg, #FF5F5F, #FFC55C); border-radius: 999px; transform-origin: 0 50%; }}
    #root .num {{ position: absolute; right: 70px; top: 284px; width: 120px; height: 120px; border-radius: 50%; background: #FFC55C; color: #2A1606; font: 800 84px/120px "Bricolage Grotesque", sans-serif; text-align: center; box-shadow: 0 0 40px rgba(255,197,92,.7); }}"""

def intruso(cid, dur, base, altro, dove, titolo, nr=5, nc=5, conta=5, tempi=None):
    """Il rompicapo (13/11, i reel d'impatto: chi guarda si ferma, cerca e riguarda): tanti animali uguali e un intruso, il tempo che scorre.
    Si capisce senza conoscere la pagina. titolo con *asterischi* per la parola in oro."""
    lato = 940 // nc; parti = re.split(r"(\*[^*]+\*)", titolo)
    tit = "".join(f"<b>{ESC(x[1:-1])}</b>" if x.startswith("*") else ESC(x) for x in parti if x)
    css = SPOT.format(a="#243B7A", b="#0A1230") + "\n    " + INTRUSO_CSS.format(fs=70 if len(titolo) <= 26 else 56, h=nr * lato)
    corpo = f"""<div class="spot"></div><div class="tit">{tit}</div><div class="num" id="{cid}-n">{conta}</div>
    <div class="tempo"><i id="{cid}-t"></i></div><div class="gr" id="{cid}-g">{_griglia(cid, base, altro, dove, nr, nc, lato)}</div>"""
    t0 = dur * 0.38  # il conto alla rovescia occupa l'ultimo 62% della scena (la voce conta «cinque, quattro…»)
    passo = (dur - t0) / conta
    js = [f'    tl.to("#{cid}-t", {{ scaleX: 0, duration: {dur - 0.1:.2f}, ease: "none" }}, 0.05);',
          f'    tl.to("#{cid}-g", {{ scale: 1.03, transformOrigin: "540px {nr * lato / 2:.0f}px", duration: {dur:.2f}, ease: "none" }}, 0);']
    for i in range(1, conta):
        t = tempi[i] if tempi and len(tempi) == conta else t0 + i * passo  # il numero cambia quando la voce lo dice (costruisci.py passa i tempi delle parole)
        js.append(f'    tl.set("#{cid}-n", {{ textContent: "{conta - i}" }}, {t:.2f}); tl.to("#{cid}-n", {{ keyframes: [{{ scale: 1.3, duration: 0.08 }}, {{ scale: 1, duration: 0.12 }}] }}, {t:.2f});')
    return _pagina(cid, f"Rompicapo: {titolo.replace('*', '')}", css, corpo, "\n".join(js))

def intruso_svela(cid, dur, base, altro, dove, titolo, riga_testo="", nr=5, nc=5):
    """La soluzione del rompicapo: gli altri si spengono, un anello d'oro sull'intruso e si va vicino."""
    lato = 940 // nc; x0 = (1080 - nc * lato) / 2
    cx, cy = x0 + dove[1] * lato + lato / 2, dove[0] * lato + lato / 2
    css = SPOT.format(a="#5A3A0E", b="#1A0F04") + "\n    " + INTRUSO_CSS.format(fs=76, h=nr * lato) + f"""
    #root .gr img {{ opacity: .22; }} #root .gr img#{cid}-x {{ opacity: 1; filter: drop-shadow(0 0 30px rgba(255,197,92,.95)); }}
    #root .an {{ position: absolute; left: {cx - lato * 0.62:.0f}px; top: {cy - lato * 0.62:.0f}px; width: {lato * 1.24:.0f}px; height: {lato * 1.24:.0f}px; border-radius: 50%; border: 10px solid #FFC55C; box-shadow: 0 0 50px rgba(255,197,92,.9); }}
    #root .dove {{ position: absolute; left: 470px; right: 50px; top: 306px; text-align: right; }}
    #root .dove span {{ font: 900 34px var(--font-body); color: #2A1606; background: #FFC55C; border-radius: 999px; padding: 10px 24px; white-space: nowrap; }}"""
    corpo = f"""<div class="spot"></div><div class="tit"><b>{ESC(titolo)}</b></div>
    <div class="gr" id="{cid}-g">{_griglia(cid, base, altro, dove, nr, nc, lato)}<div class="an" id="{cid}-a"></div></div>
    {f'<div class="dove"><span id="{cid}-d">{ESC(riga_testo)}</span></div>' if riga_testo else ""}"""
    js = f"""    tl.set("#{cid}-a", {{ scale: 2.4, opacity: 0 }}, 0); tl.to("#{cid}-a", {{ scale: 1, opacity: 1, duration: 0.4, ease: "back.out(2.4)" }}, 0.05);
    tl.to("#{cid}-a", {{ keyframes: [{{ scale: 1.12, duration: 0.35 }}, {{ scale: 1, duration: 0.35 }}], repeat: 3 }}, 0.5);
    tl.to("#{cid}-g", {{ scale: {2.3 if nc >= 6 else 1.3}, x: {540 - cx:.0f}, y: {330 - cy:.0f}, transformOrigin: "{cx:.0f}px {cy:.0f}px", duration: {max(0.8, dur - 0.3):.2f}, ease: "power2.out" }}, 0.25);"""  # l'intruso va al centro, sopra le scritte
    return _pagina(cid, "Rompicapo: la soluzione.", css, corpo, js)

def corsa(cid, dur, titolo, giorni, serie, n=6):
    """La corsa a barre (14/11, i reel d'impatto): le barre crescono giorno per giorno e si sorpassano, con la data che scorre.
    Dati veri: serie = [{"nome": "Napoli", "valori": [cumulato per ogni giorno]}], giorni = le etichette («26 ott»). Si resta per vedere chi vince.
    Nome a sinistra, barra al centro, numero subito dopo la barra (chiaro sul fondo scuro: sempre leggibile). Le posizioni sono «top», non transform."""
    K = len(giorni); H = 108; COL = 310; MAXW = 520
    colori = ["#FFC55C", "#5AA9F5", "#FF7AA8", "#6FE3B0", "#B99BFF", "#FF9F5A", "#7FD3FF", "#E8E06A", "#F28C8C", "#9BE08A", "#C9A0FF", "#FFD27A"]
    def stato(k):
        vivi = sorted(((s["valori"][k], s["nome"], i) for i, s in enumerate(serie) if s["valori"][k] > 0), key=lambda x: (-x[0], x[1]))
        return max([v for v, _, _ in vivi] + [1]), {i: r for r, (_, _, i) in enumerate(vivi)}
    larg = lambda v, mx: round((0.06 + 0.94 * v / mx) * MAXW)
    # il tempo non è uguale per tutti i giorni: quelli con più arrivi durano di più, quelli fermi scorrono veloci (la corsa resta viva fino in fondo)
    t0 = 0.3; incr = [sum(max(0, s["valori"][k] - s["valori"][k - 1]) for s in serie) for k in range(1, K)]
    pesi = [0.3 + 0.7 * (x / max(incr + [1])) ** 0.5 for x in incr]
    durate = [p / sum(pesi) * (dur - 1.4) for p in pesi]; tempi = [t0]
    for d_ in durate: tempi.append(tempi[-1] + d_)
    mx, pos = stato(0); righe, js = [], []
    # il posto e la larghezza di partenza stanno nel CSS (fermi); GSAP sposta solo con y e x rispetto a quelli. Chi è fuori dai primi è «hidden», non solo trasparente.
    casa = {i: min(pos.get(i, 99), n) for i in range(len(serie))}; l0 = {i: larg(s["valori"][0], mx) for i, s in enumerate(serie)}
    for i, s in enumerate(serie):
        vis = casa[i] < n; fs = 40 if len(s["nome"]) <= 13 else max(24, int(40 * 13 / len(s["nome"])))
        righe.append(f'<div class="b" id="{cid}-b{i}" style="top:{casa[i] * H}px;opacity:{1 if vis else 0};visibility:{"visible" if vis else "hidden"}"><b style="font-size:{fs}px">{ESC(s["nome"])}</b>'
                     f'<i id="{cid}-i{i}" style="width:{l0[i]}px;background:{colori[i % len(colori)]}"></i><span id="{cid}-v{i}" style="left:{COL + l0[i] + 14}px">{s["valori"][0]}</span></div>')
    for k in range(1, K):
        t, passo = tempi[k - 1], durate[k - 1]; mx_p, pos_p = mx, pos; mx, pos = stato(k)
        js.append(f'    tl.set("#{cid}-g", {{ textContent: "{giorni[k]}" }}, {t + passo / 2:.2f});')
        for i, s in enumerate(serie):
            r, rp = pos.get(i, 99), pos_p.get(i, 99); v, vp = s["valori"][k], s["valori"][k - 1]
            if min(r, n) != min(rp, n):
                if r < n and rp >= n: js.append(f'    tl.set("#{cid}-b{i}", {{ visibility: "visible" }}, {t:.2f});')
                js.append(f'    tl.to("#{cid}-b{i}", {{ y: {(min(r, n) - casa[i]) * H}, opacity: {1 if r < n else 0}, duration: {passo:.2f}, ease: "power1.inOut" }}, {t:.2f});')
                if r >= n and rp < n: js.append(f'    tl.set("#{cid}-b{i}", {{ visibility: "hidden" }}, {t + passo:.2f});')
            if r < n and (v != vp or mx != mx_p or rp >= n):
                js.append(f'    tl.to("#{cid}-i{i}", {{ width: {larg(v, mx)}, duration: {passo:.2f}, ease: "none" }}, {t:.2f});')
                js.append(f'    tl.to("#{cid}-v{i}", {{ x: {larg(v, mx) - l0[i]}, duration: {passo:.2f}, ease: "none" }}, {t:.2f});')
            if v != vp:
                js.append(f'    tl.set("#{cid}-v{i}", {{ textContent: "{v}" }}, {t + passo / 2:.2f});')
    primo = min(pos, key=pos.get)  # chi è in testa all'ultimo giorno: la sua barra lampeggia alla fine
    js.append(f'    tl.to("#{cid}-i{primo}", {{ keyframes: [{{ scaleY: 1.25, duration: 0.18 }}, {{ scaleY: 1, duration: 0.18 }}], repeat: 2 }}, {tempi[-1]:.2f});')
    css = SPOT.format(a="#16365F", b="#08142E") + f"""
    #root .tit {{ position: absolute; left: 60px; right: 330px; top: 300px; font: 800 60px/1 "Bricolage Grotesque", sans-serif; color: #FFF4DE; text-shadow: 0 6px 0 #05030F; }}
    #root .gio {{ position: absolute; right: 60px; top: 286px; min-width: 250px; text-align: center; font: 800 58px/1 "Bricolage Grotesque", sans-serif; color: #2A1606; background: #FFC55C; border-radius: 22px; padding: 16px 20px; box-shadow: 0 0 40px rgba(255,197,92,.6); }}
    #root .pista {{ position: absolute; left: 40px; right: 40px; top: 430px; height: {n * H}px; }}
    #root .b {{ position: absolute; left: 0; right: 0; height: {H - 18}px; }}
    #root .b b {{ position: absolute; left: 0; width: {COL - 20}px; top: 0; bottom: 0; display: flex; align-items: center; justify-content: flex-end; text-align: right; font: 900 40px/1.05 var(--font-body); color: #FFF4DE; }}
    #root .b i {{ position: absolute; left: {COL}px; top: 0; bottom: 0; border-radius: 16px; box-shadow: inset 0 -10px 0 rgba(0,0,0,.18); }}
    #root .b span {{ position: absolute; top: 0; bottom: 0; display: flex; align-items: center; font: 800 50px "Bricolage Grotesque", sans-serif; color: #FFF4DE; white-space: nowrap; }}"""
    corpo = f'<div class="spot"></div><div class="tit">{ESC(titolo)}</div><div class="gio" id="{cid}-g">{ESC(giorni[0])}</div><div class="pista">{"".join(righe)}</div>'
    return _pagina(cid, f"Corsa a barre: {titolo}", css, corpo, "\n".join(js))

def padroni(cid, dur, titolo, persone):
    """I padroni in campo (15/11, Alberto: «inseriamo anche i proprietari!»): fino a 10 animali veri della mappa, ognuno disegnato,
    col suo nome, il @ di chi lo ha e la città. Chi è nel reel viene taggato: riceve la notifica, lo guarda, lo ricondivide.
    Dai numeri: il testa a testa del 13/11 con 8 padroni in vista ha fatto 2.452 views e 16 condivisioni (gli altri reel al massimo 6).
    persone = [{"svg": "golden-4-solo.svg", "nome": "Luna", "utente": "mario", "citta": "Treviso", "t": "cane"}]"""
    def fs(testo, base, em):  # la misura che entra nei 280 px del biglietto (em = larghezza media di una lettera): niente testo tagliato
        return max(18, min(base, int(280 / (max(1, len(str(testo))) * em))))
    pp = persone[:10]
    celle = "".join(f'<div class="pc {"c" if x.get("t") == "gatto" else "d"}" id="{cid}-p{i}"><img src="assets/svg/{x["svg"]}" alt="">'
                    f'<div class="tx"><b style="font-size:{fs(x["nome"], 50, 0.62)}px">{ESC(x["nome"])}</b>'
                    f'<i style="font-size:{fs("@" + x["utente"], 32, 0.62)}px">@{ESC(x["utente"])}</i>'
                    f'<span style="font-size:{fs(x.get("citta", ""), 28, 0.6)}px">{ESC(x.get("citta", ""))}</span></div></div>' for i, x in enumerate(pp))
    css = SPOT.format(a="#1D3A73", b="#08142E") + """
    #root .tit { position: absolute; left: 60px; right: 60px; top: 290px; text-align: center; font: 800 62px/1.05 "Bricolage Grotesque", sans-serif; color: #FFF4DE; text-shadow: 0 6px 0 #05030F; }
    #root .tit b { color: #FFC55C; }
    #root .gr { position: absolute; left: 50px; right: 50px; top: 430px; display: grid; grid-template-columns: 1fr 1fr; gap: 16px 20px; }
    #root .pc { position: relative; height: 186px; border-radius: 26px; background: rgba(20,36,77,.94); border: 3px solid rgba(85,119,201,.65); overflow: hidden; }
    #root .pc.c { border-color: rgba(207,227,107,.55); }
    #root .pc img { position: absolute; left: 6px; top: 12px; width: 160px; height: 160px; object-fit: contain; filter: drop-shadow(0 6px 10px rgba(0,0,0,.5)); }
    #root .pc .tx { position: absolute; left: 172px; right: 10px; top: 0; bottom: 0; display: flex; flex-direction: column; justify-content: center; gap: 0; }
    #root .pc b, #root .pc i, #root .pc span { display: block; white-space: nowrap; }
    #root .pc b { font: 800 50px/1.25 "Bricolage Grotesque", sans-serif; color: #FFF4DE; }
    #root .pc i { font: 900 32px/1.25 var(--font-body); font-style: normal; color: #FFC55C; }
    #root .pc span { font: 800 28px/1.25 var(--font-body); color: #B9C8F0; }"""
    parti = re.split(r"(\*[^*]+\*)", titolo)
    tit = "".join(f"<b>{ESC(x[1:-1])}</b>" if x.startswith("*") else ESC(x) for x in parti if x)
    corpo = f'<div class="spot"></div><div class="tit" id="{cid}-t">{tit}</div><div class="gr">{celle}</div>'
    js = [f'    tl.fromTo("#{cid}-t", {{ y: -30, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.3, ease: "back.out(2)" }}, 0);']
    js += [f'    tl.fromTo("#{cid}-p{i}", {{ scale: 0.5, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.3, ease: "back.out(2.2)" }}, {0.2 + i * 0.12:.2f});' for i in range(len(pp))]
    giro = 0.2 + len(pp) * 0.12 + 0.4  # poi una luce d'oro passa su ogni padrone, uno dopo l'altro
    passo = max(0.15, min(0.4, (dur - giro - 0.3) / max(1, len(pp))))
    js += [f'    tl.to("#{cid}-p{i}", {{ keyframes: [{{ scale: 1.05, borderColor: "#FFC55C", duration: 0.15 }}, {{ scale: 1, borderColor: "rgba(85,119,201,.65)", duration: 0.25 }}] }}, {giro + i * passo:.2f});' for i in range(len(pp))]
    return _pagina(cid, f"I padroni in campo: {titolo.replace('*', '')}", css, corpo, "\n".join(js))

def tifosi(cid, dur, animali):
    """Il tifo (15/11): sei cani grandi, ognuno con la sciarpa della sua squadra, il nome della squadra sotto e i suoi due colori.
    animali = [{"svg": "golden-21-juventus-solo.svg", "nome": "Juventus", "c": ["#F4F4F4", "#111111"]}]"""
    celle = "".join(f'<div class="tc" id="{cid}-a{i}"><img src="assets/svg/{a["svg"]}" alt=""><span>{ESC(a["nome"])}</span>'
                    f'<i style="background:linear-gradient(90deg,{a["c"][0]} 0 50%,{a["c"][1]} 50% 100%)"></i></div>' for i, a in enumerate(animali[:6]))
    css = SPOT.format(a="#1E5A3A", b="#071A12") + """
    #root .gr { position: absolute; left: 40px; right: 40px; top: 290px; display: grid; grid-template-columns: 1fr 1fr; gap: 0 20px; }
    #root .tc { position: relative; height: 385px; display: flex; flex-direction: column; align-items: center; }
    #root .tc img { width: 330px; height: 300px; object-fit: cover; object-position: 50% 30%; filter: drop-shadow(0 10px 16px rgba(0,0,0,.55)); }
    #root .tc span { margin-top: -4px; font: 800 40px/1.2 "Bricolage Grotesque", sans-serif; color: #FFC55C; background: rgba(6,11,26,.88); border-radius: 16px; padding: 2px 22px; }
    #root .tc i { display: block; width: 150px; height: 10px; margin-top: 6px; border-radius: 5px; border: 2px solid rgba(255,255,255,.35); }"""
    js = "\n".join(f'    tl.fromTo("#{cid}-a{i}", {{ scale: 0.4, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.3, ease: "back.out(2.2)" }}, {0.05 + i * 0.2:.2f});' for i in range(len(animali[:6])))
    js += "\n" + "\n".join(f'    tl.to("#{cid}-a{i}", {{ keyframes: [{{ scale: 1.08, duration: 0.14 }}, {{ scale: 1, duration: 0.2 }}] }}, {0.05 + len(animali[:6]) * 0.2 + 0.3 + i * 0.25:.2f});' for i in range(len(animali[:6])))
    return _pagina(cid, "Le tifoserie a quattro zampe.", css, f'<div class="spot"></div><div class="gr">{celle}</div>', js)

def tappa(cid, dur, svg, tappa, comune, riga=""):
    """Il Giro d'Italia di Zampa (15/11): Zampa, il cagnolino della mappa con la sciarpa tricolore, arriva nel paese della tappa.
    riga: il fatto vero della città (motore/citta.py) o i voti che l'hanno scelta."""
    fs = 112 if len(comune) <= 10 else 88 if len(comune) <= 15 else 64
    css = SPOT.format(a="#2A6B4A", b="#0A1F14") + f"""
    #root .giro {{ position: absolute; left: 0; right: 0; top: 300px; text-align: center; font: 900 34px/1.2 var(--font-body); color: #FFC55C; letter-spacing: 1px; }}
    #root .num {{ position: absolute; left: 50%; top: 356px; width: 360px; margin-left: -180px; text-align: center; font: 800 64px/1.2 "Bricolage Grotesque", sans-serif; color: #2A1606; background: #FFC55C; border-radius: 26px; box-shadow: 0 0 50px rgba(255,197,92,.6); }}
    #root .zampa {{ position: absolute; left: 220px; top: 450px; width: 640px; height: 560px; object-fit: contain; filter: drop-shadow(0 18px 24px rgba(0,0,0,.55)); }}
    #root .arr {{ position: absolute; left: 40px; right: 40px; top: 1010px; text-align: center; font: 900 46px/1.2 var(--font-body); color: #FFF4DE; }}
    #root .citta {{ position: absolute; left: 30px; right: 30px; top: 1070px; text-align: center; font: 800 {fs}px/1.1 "Bricolage Grotesque", sans-serif; color: #FFC55C; text-shadow: 0 6px 0 #05030F, 0 0 60px rgba(255,197,92,.45); }}
    #root .riga {{ position: absolute; left: 70px; right: 70px; top: 1260px; text-align: center; }}
    #root .riga span {{ display: inline-block; font: 900 36px/1.3 var(--font-body); color: #FFF4DE; background: rgba(6,11,26,.85); border: 3px solid rgba(255,197,92,.7); border-radius: 22px; padding: 8px 26px; }}"""
    corpo = (f'<div class="spot"></div><div class="giro">🗺️ IL GIRO D\'ITALIA DI ZAMPA</div><div class="num" id="{cid}-n">TAPPA {tappa}</div>'
             f'<img class="zampa" id="{cid}-z" src="assets/svg/{svg}" alt=""><div class="arr" id="{cid}-a">Zampa arriva a</div><div class="citta" id="{cid}-c">{ESC(comune)}</div>'
             + (f'<div class="riga"><span id="{cid}-r">{ESC(riga)}</span></div>' if riga else ""))
    js = f"""    tl.fromTo("#{cid}-n", {{ scale: 0.4, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.35, ease: "back.out(2.4)" }}, 0.05);
    tl.fromTo("#{cid}-z", {{ x: -700, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.6, ease: "back.out(1.4)" }}, 0.1);
    tl.to("#{cid}-z", {{ keyframes: [{{ y: -30, duration: 0.18 }}, {{ y: 0, duration: 0.18 }}], repeat: 2 }}, 0.75);
    tl.fromTo("#{cid}-a", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.25 }}, 0.5);
    tl.fromTo("#{cid}-c", {{ scale: 0.3, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.4, ease: "back.out(2.2)" }}, 0.7);""" + (
        f'\n    tl.fromTo("#{cid}-r", {{ y: 30, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.3, ease: "back.out(2)" }}, 1.1);' if riga else "")
    return _pagina(cid, f"Il Giro d'Italia di Zampa: tappa {tappa}, {comune}.", css, corpo, js)

def avvento(cid, dur, giorno, aperte, nuova):
    """Il Calendario dell'Avvento delle Zampe (1–24 dicembre): 24 caselle, quelle già aperte mostrano l'animale che c'era dentro,
    oggi si apre la casella del giorno. aperte = {"3": "golden-12-solo.svg", ...}; nuova = svg dell'animale di oggi."""
    celle = []
    for i in range(1, 25):
        dentro = f'<img src="assets/svg/{nuova if i == giorno else aperte.get(str(i), "")}" alt="">' if (i == giorno or str(i) in aperte) else ""
        porta = "" if (str(i) in aperte and i != giorno) else f'<b class="porta" id="{cid}-p{i}">{i}</b>'
        celle.append(f'<div class="cas{" oggi" if i == giorno else ""}" id="{cid}-c{i}">{dentro}{porta}</div>')
    css = SPOT.format(a="#7A1F2B", b="#1A0508") + """
    #root .tit { position: absolute; left: 40px; right: 40px; top: 285px; text-align: center; font: 800 54px/1.1 "Bricolage Grotesque", sans-serif; color: #FFF4DE; text-shadow: 0 5px 0 #05030F; }
    #root .tit b { color: #FFC55C; }
    #root .gr { position: absolute; left: 60px; right: 60px; top: 420px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }
    #root .cas { position: relative; height: 160px; border-radius: 18px; background: #0E2A1B; border: 3px solid #C9A24A; overflow: hidden; }
    #root .cas img { position: absolute; left: 10%; top: 6%; width: 80%; height: 88%; object-fit: contain; }
    #root .porta { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font: 800 64px/1 "Bricolage Grotesque", sans-serif; color: #FFE7A8;
      background: repeating-linear-gradient(45deg, #B3202E 0 18px, #C8303E 18px 36px); transform-origin: 0 50%; }
    #root .cas.oggi { border-color: #FFC55C; box-shadow: 0 0 40px rgba(255,197,92,.9); }"""
    corpo = f'<div class="spot"></div><div class="tit">🎄 Il Calendario <b>delle Zampe</b></div><div class="gr">{"".join(celle)}</div>'
    js = f"""    tl.to("#{cid}-c{giorno}", {{ keyframes: [{{ scale: 1.12, duration: 0.25 }}, {{ scale: 1, duration: 0.25 }}], repeat: 1 }}, 0.3);
    tl.to("#{cid}-p{giorno}", {{ scaleX: 0, duration: 0.6, ease: "power2.inOut" }}, {max(1.2, dur * 0.45):.2f});
    tl.to("#{cid}-c{giorno}", {{ scale: 1.25, zIndex: 5, duration: 0.4, ease: "back.out(2)" }}, {max(1.8, dur * 0.45 + 0.6):.2f});"""
    return _pagina(cid, f"Il Calendario dell'Avvento delle Zampe: casella {giorno}.", css, corpo, js)

SFONDI_30 = {  # le stanze della serie (colori piatti, come un cartone)
    "canile": ("#33405F", "#4A3B2E", True), "bagno": ("#7FB7C9", "#D9E4EA", False), "veterinario": ("#CFE3DA", "#9DB8AD", False),
    "toelettatura": ("#E9B7C9", "#B98A9C", False), "parco": ("#8CC9E8", "#4F9A4A", False), "strada": ("#9BB4D0", "#5D5D66", False),
    "casa": ("#F2C98A", "#A86B3C", False), "notte": ("#18223F", "#2B2433", False)}

def zampa30(cid, dur, svg="", giorni=30, famiglia=0, testo="", banner="", sfondo="canile", sporco=True, oggetti=(), scelta=None, famiglia_prima=None, foto="", etichette=(), sfx=None):
    """La serie «Zampa ha 30 giorni per trovare casa» (15/11, Alberto: «facciamo il cane»): Zampa grande, i contatori in alto
    (GIORNI che mancano, FAMIGLIA in percentuale), il nastro giallo con la posta in gioco, la frase grande della puntata,
    e alla fine la scelta per domani (scelta = {"a": ["🛁", "IL BAGNO", "BAGNO"], "b": [...]}): decide chi commenta."""
    muro, pavimento, sbarre = SFONDI_30.get(sfondo, SFONDI_30["canile"])
    fp = famiglia if famiglia_prima is None else famiglia_prima
    sb = "".join(f'<i class="sb" style="left:{60 + k * 140}px"></i>' for k in range(7)) if sbarre else ""
    st = ""
    if sporco:  # la puzza (righe verdi che ondeggiano), le mosche, le macchie di fango
        st += ('<svg class="puzza" viewBox="0 0 1080 900"><path d="M300 520 q-30 -50 0 -100 q30 -50 0 -100" /><path d="M780 520 q-30 -50 0 -100 q30 -50 0 -100" />'
               '<path d="M250 700 q-25 -40 0 -80 q25 -40 0 -80" /><path d="M840 700 q-25 -40 0 -80 q25 -40 0 -80" /></svg>'
               f'<i class="mosca" id="{cid}-m1"></i><i class="mosca" id="{cid}-m2"></i>')
    ogg = "".join(f'<span class="ogg" style="left:{x}px;top:{y}px;font-size:{z}px" id="{cid}-o{i}">{ESC(e)}</span>' for i, (e, x, y, z) in enumerate(oggetti))
    sc = ""
    if scelta:
        sc = "".join(f'<div class="op op{k}" id="{cid}-op{k}"><span class="em">{ESC(v[0])}</span><b>{ESC(v[1])}</b><i>scrivi {ESC(v[2])}</i></div>' for k, v in (("a", scelta["a"]), ("b", scelta["b"])))
        sc = f'<div class="scelta"><div class="dom">Domani cosa fa Paolino?</div>{sc}<div class="o">oppure</div></div>'
    css = f"""
    #root .muro {{ position: absolute; inset: 0; background: {muro}; }}
    #root .pav {{ position: absolute; left: 0; right: 0; bottom: 0; height: 560px; background: {pavimento}; }}
    #root .sb {{ position: absolute; top: 0; height: 1360px; width: 26px; background: #1C2335; border-radius: 0 0 8px 8px; box-shadow: 6px 0 0 rgba(0,0,0,.25); }}
    #root .hud {{ position: absolute; left: 40px; top: 290px; display: flex; gap: 16px; }}
    #root .hud div {{ min-width: 200px; padding: 10px 20px; border-radius: 18px; background: rgba(12,10,14,.9); border: 4px solid #F3E6C8; text-align: center; }}
    #root .hud small {{ display: block; font: 900 26px/1.2 var(--font-body); color: #E9E2D2; letter-spacing: 1px; }}
    #root .hud b {{ display: block; font: 800 76px/1 "Bricolage Grotesque", sans-serif; color: #FFC55C; }}
    #root .hud .f b {{ color: #6FE38F; }}
    #root .nastro {{ position: absolute; left: 50px; right: 50px; top: 470px; text-align: center; }}
    #root .nastro span {{ display: inline-block; transform: rotate(-3deg); font: 800 54px/1.1 "Bricolage Grotesque", sans-serif; color: #1A1206; background: #FFD23F; border: 5px solid #1A1206; border-radius: 14px; padding: 10px 26px; box-shadow: 0 8px 0 rgba(0,0,0,.35); }}
    #root .zampa {{ position: absolute; left: -80px; top: 360px; width: 1240px; height: 1080px; object-fit: contain; filter: drop-shadow(0 22px 26px rgba(0,0,0,.45)); }}
    #root .zampa.intero {{ left: 185px; top: 470px; width: 710px; height: 780px; }}
    #root .quadro {{ position: absolute; inset: 0; overflow: hidden; }}
    #root .foto {{ position: absolute; left: -100px; top: 170px; width: 1280px; height: 1920px; object-fit: cover; }}
    #root .specchio {{ position: absolute; left: -100px; top: -1750px; width: 1280px; height: 1920px; object-fit: cover; transform: scaleY(-1); }}
    #root .velo {{ position: absolute; left: 0; right: 0; top: 0; height: 520px; background: linear-gradient(180deg, rgba(0,0,0,.58) 0, rgba(0,0,0,.32) 60%, rgba(0,0,0,0) 100%); }}
    #root .velo ~ .hud {{ top: 196px; left: 30px; gap: 10px; }}
    #root .barra {{ position: absolute; left: 30px; top: 296px; width: 314px; height: 14px; border-radius: 8px; background: rgba(255,255,255,.25); border: 2px solid #F3E6C8; }}
    #root .barra i {{ position: absolute; left: 0; top: 0; bottom: 0; border-radius: 8px; background: linear-gradient(90deg, #6FE38F, #FFD23F); }}
    #root .et {{ position: absolute; max-width: 330px; }}
    #root .et.s {{ left: 22px; }} #root .et.d {{ right: 22px; text-align: right; }}
    #root .et span {{ display: inline-block; font: 900 34px/1.15 var(--font-body); color: #1A1206; background: #FFF8EA; border: 4px solid #1A1206; border-radius: 16px; padding: 8px 14px; box-shadow: 0 7px 0 rgba(0,0,0,.35); }}
    #root .et.s span {{ transform: rotate(-4deg); border-right-width: 10px; border-right-color: #FFD23F; }}
    #root .et.d span {{ transform: rotate(4deg); border-left-width: 10px; border-left-color: #FFD23F; }}
    #root .sfx {{ position: absolute; }} #root .sfx.s {{ left: 14px; }} #root .sfx.d {{ right: 14px; }}
    #root .sfx span {{ display: inline-block; transform: rotate(-9deg); font: 800 72px/1 "Bricolage Grotesque", sans-serif; color: #FFD23F; background: #E2394B; border: 6px solid #1A1206; border-radius: 22px; padding: 6px 20px; box-shadow: 0 10px 0 rgba(0,0,0,.4); }}
    #root .velo ~ .hud div {{ min-width: 150px; padding: 6px 14px; border-width: 3px; border-radius: 14px; }}
    #root .velo ~ .hud small {{ font-size: 20px; }} #root .velo ~ .hud b {{ font-size: 54px; }}
    #root .velo ~ .nastro {{ top: 214px; left: 360px; right: 26px; text-align: right; }}
    #root .velo ~ .nastro span {{ font-size: 30px; padding: 8px 14px; border-width: 4px; }}
    #root .velo ~ .frase {{ top: 336px; left: 24px; right: 24px; text-shadow: 0 5px 0 #0A0A0A, 4px 0 0 #0A0A0A, -4px 0 0 #0A0A0A, 0 -4px 0 #0A0A0A, 0 0 24px rgba(0,0,0,.8); }}
    #root .velo ~ .scelta {{ top: 326px; height: 200px; left: 24px; right: 24px; }}
    #root .velo ~ .scelta .dom {{ top: 0; left: 120px; right: 120px; font-size: 52px; background: rgba(10,10,10,.6); border-radius: 18px; padding: 4px 10px; }}
    #root .velo ~ .scelta .op {{ top: 84px; width: 470px; height: 112px; flex-direction: row; gap: 12px; border-width: 5px; border-radius: 22px; }}
    #root .velo ~ .scelta .op .em {{ font-size: 60px; }} #root .velo ~ .scelta .op b {{ font-size: 40px; }} #root .velo ~ .scelta .op i {{ display: none; }}
    #root .velo ~ .scelta .o {{ top: 112px; width: 90px; margin-left: -45px; font-size: 24px; line-height: 50px; }}
    #root .zampa.intero ~ .frase {{ top: 1262px; }}
    #root .puzza {{ position: absolute; left: -60px; top: 420px; width: 1200px; height: 1000px; }}
    #root .puzza path {{ fill: none; stroke: #8DB255; stroke-width: 14; stroke-linecap: round; opacity: .85; }}
    #root .mosca {{ position: absolute; left: 470px; top: 560px; width: 22px; height: 22px; border-radius: 50%; background: #151515; box-shadow: -12px -12px 0 -4px rgba(230,240,255,.85), 12px -12px 0 -4px rgba(230,240,255,.85); }}
    #root .ogg {{ position: absolute; line-height: 1.15; color: #1A1206; background: #FFF8EA; border: 5px solid #1A1206; border-radius: 50%; padding: 10px 14px; box-shadow: 0 8px 0 rgba(0,0,0,.3); }}
    #root .frase {{ position: absolute; left: 40px; right: 40px; top: 1300px; text-align: center; font: 800 {78 if len(testo) <= 22 else 62 if len(testo) <= 34 else 50}px/1.08 "Bricolage Grotesque", sans-serif; color: #FFFFFF;
      text-shadow: 0 6px 0 #0A0A0A, 4px 0 0 #0A0A0A, -4px 0 0 #0A0A0A, 0 -4px 0 #0A0A0A; }}
    #root .scelta {{ position: absolute; left: 40px; right: 40px; top: 1060px; height: 400px; }}
    #root .dom {{ position: absolute; left: 0; right: 0; top: 0; text-align: center; font: 800 58px/1.1 "Bricolage Grotesque", sans-serif; color: #FFF; text-shadow: 0 5px 0 #0A0A0A; }}
    #root .op {{ position: absolute; top: 100px; width: 430px; height: 290px; border-radius: 30px; background: #FFF8EA; border: 6px solid #1A1206; box-shadow: 0 12px 0 rgba(0,0,0,.35); display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; }}
    #root .opa {{ left: 0; }} #root .opb {{ right: 0; }}
    #root .op .em {{ font-size: 110px; line-height: 1.1; color: #1A1206; }}
    #root .op b {{ font: 800 48px/1.1 "Bricolage Grotesque", sans-serif; color: #1A1206; }}
    #root .op i {{ font: 900 30px/1.2 var(--font-body); font-style: normal; color: #9A5A00; }}
    #root .o {{ position: absolute; left: 50%; top: 210px; width: 120px; margin-left: -60px; text-align: center; font: 900 30px/60px var(--font-body); color: #1A1206; background: #FFD23F; border-radius: 30px; border: 4px solid #1A1206; }}"""
    if foto:  # 15/11 sera: Zampa vero (foto IA realistica, motore/zampa.py) a tutto schermo, che si avvicina piano; sopra contatori e scritte
        sb, st, ogg = "", "", ""
    intero = svg.endswith(".png")  # Zampa intero in 3D (reel/zampa3d.js): sta in piedi sul pavimento, la frase sotto i piedi
    fondo = (f'<div class="quadro" id="{cid}-z"><img class="specchio" src="assets/img/{foto}" alt=""><img class="foto" src="assets/img/{foto}" alt=""></div><div class="velo"></div>' if foto else
             f'<div class="muro"></div><div class="pav"{" style=\'height:760px\'" if intero else ""}></div>{sb}<img class="zampa{" intero" if intero else ""}" id="{cid}-z" src="assets/svg/{svg}" alt="">')
    et = "".join(f'<div class="et {x.get("lato", "s")}" id="{cid}-e{i}" style="top:{x.get("y", 800)}px"><span>{ESC(x.get("e", ""))} {ESC(x["t"])}</span></div>' for i, x in enumerate(etichette))
    if sfx: et += f'<div class="sfx {sfx.get("lato", "d")}" id="{cid}-x" style="top:{sfx.get("y", 760)}px"><span>{ESC(sfx["t"])}</span></div>'
    barra = f'<div class="barra"><i id="{cid}-bf" style="width:{max(2, fp)}%"></i></div>' if foto else ""
    corpo = (f'{fondo}{st}{ogg}{et}{barra}'
             f'<div class="hud"><div><small>GIORNI</small><b id="{cid}-g">{giorni}</b></div><div class="f"><small>FAMIGLIA</small><b id="{cid}-f">{fp}%</b></div></div>'
             + (f'<div class="nastro"><span id="{cid}-n">{ESC(banner)}</span></div>' if banner else "")
             + (f'<div class="frase" id="{cid}-t">{ESC(testo)}</div>' if testo and not scelta else "") + sc)
    js = ([f'    tl.fromTo("#{cid}-z", {{ scale: 1.0 }}, {{ scale: 1.05, transformOrigin: "50% 60%", duration: {dur:.2f}, ease: "none" }}, 0);'] if foto else
          [f'    tl.fromTo("#{cid}-z", {{ scale: 0.85, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.35, ease: "back.out(2)" }}, 0.05);',
           f'    tl.to("#{cid}-z", {{ keyframes: [{{ rotation: -3, duration: 0.25 }}, {{ rotation: 3, duration: 0.25 }}, {{ rotation: 0, duration: 0.25 }}], repeat: {max(1, int(dur / 1.5))} }}, 0.4);'])
    if banner: js.append(f'    tl.fromTo("#{cid}-n", {{ scale: 0.3, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.35, ease: "back.out(2.4)" }}, 0.25);')
    if testo and not scelta: js.append(f'    tl.fromTo("#{cid}-t", {{ scale: 0.4, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.3, ease: "back.out(2.2)" }}, 0.5);')
    if sporco and not foto:
        for k, (dx, dy) in enumerate([(160, -60), (-140, 90)]):
            js.append(f'    tl.to("#{cid}-m{k + 1}", {{ keyframes: [{{ x: {dx}, y: {dy}, duration: 0.5 }}, {{ x: {-dx // 2}, y: {-dy}, duration: 0.5 }}, {{ x: 0, y: 0, duration: 0.5 }}], repeat: {max(1, int(dur / 1.5))} }}, {0.1 + k * 0.2:.2f});')
    for i in range(len(oggetti)):
        js.append(f'    tl.fromTo("#{cid}-o{i}", {{ scale: 0, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.35, ease: "back.out(2.6)" }}, {0.6 + i * 0.3:.2f});')
    for i, x in enumerate(etichette):
        dx = -260 if x.get("lato", "s") == "s" else 260
        js.append(f'    tl.fromTo("#{cid}-e{i}", {{ x: {dx}, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.35, ease: "back.out(1.8)" }}, {0.5 + i * 0.6:.2f});')
        js.append(f'    tl.to("#{cid}-e{i}", {{ keyframes: [{{ scale: 1.06, duration: 0.3 }}, {{ scale: 1, duration: 0.3 }}], repeat: {max(1, int(dur / 1.4))} }}, {1.0 + i * 0.6:.2f});')
    if sfx:
        t0 = sfx.get("t0", 0.4)
        js.append(f'    tl.fromTo("#{cid}-x", {{ scale: 0, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.3, ease: "back.out(3)" }}, {t0:.2f});')
        js.append(f'    tl.to("#{cid}-x", {{ keyframes: [{{ x: -10, duration: 0.05 }}, {{ x: 10, duration: 0.05 }}, {{ x: -6, duration: 0.05 }}, {{ x: 0, duration: 0.05 }}], repeat: 3 }}, {t0 + 0.3:.2f});')
    if scelta:
        js.append(f'    tl.fromTo("#{cid}-opa", {{ x: -300, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.4, ease: "back.out(1.8)" }}, 0.3);')
        js.append(f'    tl.fromTo("#{cid}-opb", {{ x: 300, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.4, ease: "back.out(1.8)" }}, 0.5);')
        js.append(f'    tl.to(["#{cid}-opa", "#{cid}-opb"], {{ keyframes: [{{ scale: 1.06, duration: 0.3 }}, {{ scale: 1, duration: 0.3 }}], repeat: {max(1, int(dur / 1.2))}, stagger: 0.3 }}, 1.0);')
    if famiglia_prima is not None and famiglia_prima != famiglia:
        js.append(f'    tl.set("#{cid}-f", {{ textContent: "{famiglia}%" }}, {max(0.8, dur * 0.5):.2f}); tl.to("#{cid}-f", {{ keyframes: [{{ scale: 1.4, duration: 0.15 }}, {{ scale: 1, duration: 0.2 }}] }}, {max(0.8, dur * 0.5):.2f});')
        if foto: js.append(f'    tl.to("#{cid}-bf", {{ width: "{max(2, famiglia)}%", duration: 0.6, ease: "power2.out" }}, {max(0.8, dur * 0.5):.2f});')
    return _pagina(cid, f"Zampa ha 30 giorni: {testo or banner}", css, corpo, "\n".join(js))

# ---------------------------------------------------------------- Paolino a cartone (16/11 sera)
# Alberto, dopo il Giorno 1 con le foto: «è un flop, dovevamo farlo in grafica animata come gli altri», col video della puntata di Ugo:
# cartone 2D piatto con contorni spessi, il numero gigante dei giorni, «AVETE SCELTO» col voto in percentuale, «PAROLE VOSTRE» (il commento
# di un follower), il personaggio che si muove e sviene, le nuvolette, le etichette storte colorate. Paolino e il cast li ha disegnati Alberto
# con ChatGPT (reel/assets/paolino, sfondo trasparente); gli sfondi sono disegnati qui, piatti, con lo stesso contorno scuro.
LINEA = "#2A1A10"
CARTONE_SFONDI = {
    "canile": f"""<rect width="1080" height="1300" fill="#34436E"/>{''.join(f'<rect x="{x}" y="0" width="14" height="1300" fill="#2C3960"/>' for x in range(60, 1080, 120))}
      <rect x="70" y="330" width="300" height="330" rx="10" fill="#1B2547" stroke="{LINEA}" stroke-width="10"/><circle cx="290" cy="420" r="44" fill="#FFE9A8"/><circle cx="312" cy="404" r="40" fill="#1B2547"/>
      <g fill="#fff"><circle cx="130" cy="390" r="5"/><circle cx="200" cy="560" r="4"/><circle cx="320" cy="600" r="5"/></g>
      {''.join(f'<rect x="{x}" y="330" width="16" height="330" fill="#6B7896" stroke="{LINEA}" stroke-width="5"/>' for x in (130, 205, 280))}
      <rect x="760" y="560" width="230" height="120" rx="12" fill="#E2432F" stroke="{LINEA}" stroke-width="9" transform="rotate(4 875 620)"/>
      <g fill="#fff" transform="rotate(4 875 620)"><ellipse cx="875" cy="640" rx="26" ry="20"/><circle cx="843" cy="610" r="11"/><circle cx="866" cy="596" r="11"/><circle cx="889" cy="596" r="11"/><circle cx="910" cy="610" r="11"/></g>
      <rect x="0" y="1290" width="1080" height="630" fill="#5A4130"/><rect x="0" y="1285" width="1080" height="16" fill="{LINEA}"/>
      {''.join(f'<rect x="{x}" y="{y}" width="16" height="10" fill="{c}" transform="rotate({r} {x} {y})"/>' for x, y, c, r in ((120, 1400, "#FFD23F", 20), (310, 1520, "#E2432F", -15), (880, 1450, "#6FE38F", 30), (980, 1700, "#FFD23F", 10), (60, 1760, "#E2432F", 40), (700, 1820, "#6FE38F", -20)))}
      <ellipse cx="190" cy="1640" rx="120" ry="42" fill="#9AA6B8" stroke="{LINEA}" stroke-width="8"/><ellipse cx="190" cy="1628" rx="88" ry="22" fill="#6B7896"/>""",
    "bagno": f"""<rect width="1080" height="1300" fill="#A9DDEA"/>{''.join(f'<rect x="{x}" y="0" width="6" height="1300" fill="#8CC6D6"/>' for x in range(0, 1080, 108))}{''.join(f'<rect x="0" y="{y}" width="1080" height="6" fill="#8CC6D6"/>' for y in range(0, 1300, 108))}
      <rect x="60" y="520" width="240" height="14" rx="7" fill="#9AA6B8" stroke="{LINEA}" stroke-width="6"/><path d="M80 534 h200 v300 l-40 -30 l-40 30 l-40 -30 l-40 30 z" fill="#F28DB2" stroke="{LINEA}" stroke-width="8"/>
      <rect x="0" y="1290" width="1080" height="630" fill="#EEF4F6"/>{''.join(f'<rect x="{x}" y="{y}" width="120" height="120" fill="#C9D6DD"/>' for y in range(1300, 1920, 240) for x in range(0, 1080, 240))}{''.join(f'<rect x="{x}" y="{y}" width="120" height="120" fill="#C9D6DD"/>' for y in range(1420, 1920, 240) for x in range(120, 1080, 240))}
      <rect x="0" y="1285" width="1080" height="16" fill="{LINEA}"/>
      <path d="M930 760 h70 v40 h-40 v60" fill="none" stroke="{LINEA}" stroke-width="30" stroke-linecap="round"/><path d="M930 760 h70 v40 h-40 v60" fill="none" stroke="#C7D0D9" stroke-width="16" stroke-linecap="round"/>
      <rect x="500" y="1010" width="560" height="300" rx="70" fill="#FBFDFF" stroke="{LINEA}" stroke-width="10"/><rect x="480" y="990" width="600" height="48" rx="24" fill="#FBFDFF" stroke="{LINEA}" stroke-width="10"/>
      <g fill="#FBFDFF" stroke="{LINEA}" stroke-width="8">{''.join(f'<circle cx="{x}" cy="{y}" r="{r}"/>' for x, y, r in ((560, 975, 48), (640, 950, 62), (740, 965, 54), (840, 945, 66), (950, 970, 52), (1030, 960, 40)))}</g>
      <g fill="#D4A017" stroke="{LINEA}" stroke-width="7"><path d="M560 1300 l-20 60 h50 l10 -60z"/><path d="M1000 1300 l20 60 h-50 l-10 -60z"/></g>""",
    "strada": f"""<rect width="1080" height="1300" fill="#8ED3F5"/><circle cx="930" cy="230" r="70" fill="#FFE27A" stroke="{LINEA}" stroke-width="8"/>
      {''.join(f'<rect x="{x}" y="{y}" width="{w}" height="{1260 - y}" fill="{c}" stroke="{LINEA}" stroke-width="10"/><rect x="{x - 14}" y="{y - 40}" width="{w + 28}" height="44" fill="#7A3B22" stroke="{LINEA}" stroke-width="9"/>'
               + ''.join(f'<rect x="{x + wx}" y="{y + wy}" width="80" height="110" fill="#2F4F7F" stroke="{LINEA}" stroke-width="7"/><rect x="{x + wx - 30}" y="{y + wy}" width="26" height="110" fill="#4C9A5B" stroke="{LINEA}" stroke-width="5"/><rect x="{x + wx + 84}" y="{y + wy}" width="26" height="110" fill="#4C9A5B" stroke="{LINEA}" stroke-width="5"/>'
                         for wx in (60, w - 140) for wy in (90, 300))
               for x, y, w, c in ((0, 420, 360, "#F2B84B"), (360, 360, 360, "#E07A4F"), (720, 460, 360, "#F2A7A0")))}
      <path d="M380 940 h320 v70 h-320z" fill="#fff" stroke="{LINEA}" stroke-width="8"/>{''.join(f'<rect x="{380 + k * 64}" y="940" width="32" height="70" fill="#E2432F"/>' for k in range(5))}
      <rect x="420" y="1010" width="240" height="250" fill="#3B2A20" stroke="{LINEA}" stroke-width="8"/><rect x="440" y="1030" width="90" height="120" fill="#8ED3F5" stroke="{LINEA}" stroke-width="5"/>
      <rect x="0" y="1260" width="1080" height="120" fill="#D8C7A6" stroke="{LINEA}" stroke-width="10"/><rect x="0" y="1380" width="1080" height="540" fill="#585C6C"/>
      {''.join(f'<rect x="{x}" y="1650" width="110" height="22" rx="8" fill="#F4F4F4"/>' for x in range(30, 1080, 220))}""",
    "veterinario": f"""<rect width="1080" height="1300" fill="#CDEBDD"/><rect x="0" y="880" width="1080" height="46" fill="#9FD1B9"/>
      <rect x="640" y="300" width="330" height="140" rx="14" fill="#2E9E6B" stroke="{LINEA}" stroke-width="9"/><path d="M805 330 v80 M765 370 h80" stroke="#fff" stroke-width="26" stroke-linecap="round"/>
      <rect x="80" y="320" width="260" height="340" rx="10" fill="#FFFDF5" stroke="{LINEA}" stroke-width="9"/><path d="M210 400 v120 M150 460 h120" stroke="#E2432F" stroke-width="36" stroke-linecap="round"/>
      <rect x="130" y="580" width="160" height="22" rx="11" fill="#9AA6B8"/>
      <rect x="0" y="1290" width="1080" height="630" fill="#EEF3F4"/>{''.join(f'<rect x="0" y="{y}" width="1080" height="5" fill="#D2DCE0"/>' for y in range(1400, 1920, 110))}<rect x="0" y="1285" width="1080" height="16" fill="{LINEA}"/>
      <rect x="560" y="1110" width="480" height="44" rx="10" fill="#C7D0D9" stroke="{LINEA}" stroke-width="9"/><rect x="600" y="1150" width="22" height="200" fill="#9AA6B8" stroke="{LINEA}" stroke-width="6"/><rect x="980" y="1150" width="22" height="200" fill="#9AA6B8" stroke="{LINEA}" stroke-width="6"/>""",
    # 22/11: il parco (la puntata di Alexa)
    "parco": f"""<rect width="1080" height="1300" fill="#8ED3F5"/><circle cx="880" cy="230" r="70" fill="#FFE27A" stroke="{LINEA}" stroke-width="8"/>
      <path d="M0 980 Q270 900 540 960 T1080 940 V1300 H0Z" fill="#7CC36B" stroke="{LINEA}" stroke-width="8"/>
      {''.join(f'<rect x="{x - 18}" y="{y}" width="36" height="{1180 - y}" fill="#7A4A2A" stroke="{LINEA}" stroke-width="7"/><circle cx="{x}" cy="{y}" r="{r}" fill="#3F9A4E" stroke="{LINEA}" stroke-width="8"/><circle cx="{x - r * 0.35}" cy="{y - r * 0.3}" r="{r * 0.45}" fill="#56B062"/>' for x, y, r in ((130, 720, 150), (480, 640, 130), (900, 700, 160)))}
      <rect x="0" y="1180" width="1080" height="740" fill="#6DB85C"/><path d="M380 1920 Q520 1500 540 1300 Q560 1500 700 1920Z" fill="#E6C88F" stroke="{LINEA}" stroke-width="7"/>
      <rect x="0" y="1175" width="1080" height="12" fill="{LINEA}"/>
      <rect x="700" y="1080" width="300" height="26" rx="8" fill="#B5763F" stroke="{LINEA}" stroke-width="7"/><rect x="700" y="1030" width="300" height="22" rx="8" fill="#B5763F" stroke="{LINEA}" stroke-width="7"/>
      <rect x="720" y="1104" width="18" height="70" fill="#5A6472"/><rect x="962" y="1104" width="18" height="70" fill="#5A6472"/>
      {''.join(f'<circle cx="{x}" cy="{y}" r="9" fill="{c}" stroke="{LINEA}" stroke-width="3"/>' for x, y, c in ((90, 1400, "#F28DB2"), (260, 1700, "#FFD23F"), (850, 1450, "#F28DB2"), (960, 1760, "#FFFFFF"), (180, 1250, "#FFFFFF")))}""",
    # 17/11 (Officina): il bar del paese (la puntata della fuga) e l'ufficio del canile (il colloquio con la famiglia)
    "bar": f"""<rect width="1080" height="1300" fill="#E9B97A"/><rect x="0" y="880" width="1080" height="420" fill="#8A5A3B"/>{''.join(f'<rect x="{x}" y="880" width="10" height="420" fill="#74492E"/>' for x in range(90, 1080, 150))}
      {''.join(f'<rect x="70" y="{y}" width="540" height="18" fill="#6B4226" stroke="{LINEA}" stroke-width="6"/>' for y in (430, 610))}
      {''.join(f'<path d="M{x} {y} v-80 q0 -20 14 -26 v-20 h12 v20 q14 6 14 26 v80z" fill="{c}" stroke="{LINEA}" stroke-width="6"/>' for x, y, c in ((100, 430, "#4C9A5B"), (170, 430, "#C8442E"), (240, 430, "#E9A23B"), (330, 430, "#4C9A5B"), (420, 430, "#7FB7C9"), (510, 430, "#C8442E"), (120, 610, "#E9A23B"), (210, 610, "#7FB7C9"), (300, 610, "#C8442E"), (400, 610, "#4C9A5B"), (500, 610, "#E9A23B")))}
      <rect x="680" y="300" width="330" height="390" rx="14" fill="#2E3B33" stroke="{LINEA}" stroke-width="10"/><g stroke="#F4F4F4" stroke-width="8" stroke-linecap="round" opacity=".8">{''.join(f'<path d="M720 {y} h{w}"/>' for y, w in ((370, 200), (430, 240), (490, 170), (550, 220), (610, 150)))}</g>
      {''.join(f'<path d="M{x} 0 v120" stroke="{LINEA}" stroke-width="6"/><path d="M{x - 60} 180 a60 60 0 0 1 120 0z" fill="#FFD23F" stroke="{LINEA}" stroke-width="7"/>' for x in (300, 860))}
      <rect x="0" y="1060" width="1080" height="44" fill="#C9A27A" stroke="{LINEA}" stroke-width="8"/><rect x="0" y="1100" width="1080" height="200" fill="#5A3A26" stroke="{LINEA}" stroke-width="8"/>
      <rect x="740" y="880" width="250" height="180" rx="16" fill="#C7D0D9" stroke="{LINEA}" stroke-width="9"/><rect x="790" y="1000" width="40" height="60" fill="#9AA6B8" stroke="{LINEA}" stroke-width="5"/><rect x="890" y="1000" width="40" height="60" fill="#9AA6B8" stroke="{LINEA}" stroke-width="5"/>
      <rect x="0" y="1300" width="1080" height="620" fill="#F4F4F4"/>{''.join(f'<rect x="{x}" y="{y}" width="120" height="120" fill="#2B2B33"/>' for y in range(1300, 1920, 240) for x in range(0, 1080, 240))}{''.join(f'<rect x="{x}" y="{y}" width="120" height="120" fill="#2B2B33"/>' for y in range(1420, 1920, 240) for x in range(120, 1080, 240))}
      <rect x="0" y="1295" width="1080" height="14" fill="{LINEA}"/>""",
    "ufficio": f"""<rect width="1080" height="1300" fill="#F2E3C6"/><rect x="0" y="1000" width="1080" height="300" fill="#E2CDA6"/>
      <rect x="80" y="330" width="320" height="380" rx="10" fill="#8ED3F5" stroke="{LINEA}" stroke-width="10"/><path d="M240 330 v380 M80 520 h320" stroke="{LINEA}" stroke-width="8"/><circle cx="330" cy="420" r="34" fill="#FFE27A"/>
      <circle cx="820" cy="430" r="96" fill="#FFFDF5" stroke="{LINEA}" stroke-width="10"/><path d="M820 430 v-62 M820 430 l-52 -30" stroke="{LINEA}" stroke-width="10" stroke-linecap="round"/><circle cx="820" cy="430" r="10" fill="{LINEA}"/>
      <rect x="720" y="640" width="260" height="660" rx="8" fill="#9AA6B8" stroke="{LINEA}" stroke-width="9"/>{''.join(f'<rect x="745" y="{y}" width="210" height="190" rx="6" fill="#B8C2CC" stroke="{LINEA}" stroke-width="6"/><rect x="815" y="{y + 80}" width="70" height="18" rx="9" fill="#5A6472"/>' for y in (665, 875, 1085))}
      <rect x="0" y="1300" width="1080" height="620" fill="#B9875A"/>{''.join(f'<rect x="0" y="{y}" width="1080" height="6" fill="#9C6F45"/>' for y in range(1390, 1920, 100))}<rect x="0" y="1295" width="1080" height="14" fill="{LINEA}"/>""",
}
def sfondo_stadio(ca, cb):
    """17/11, il Campionato delle Zampe: lo stadio di notte, metà curva coi colori della squadra di casa e metà con quelli degli ospiti."""
    teste = "".join(f'<circle cx="{x}" cy="{y}" r="11" fill="{(ca if x < 540 else cb)[(x // 30 + y // 40) % 2]}" stroke="{LINEA}" stroke-width="3"/>'
                    for y in range(500, 980, 40) for x in range(15 + (y // 40 % 2) * 15, 1080, 30) if y > 470 + abs(x - 540) * 0.12)
    return f"""<rect width="1080" height="1920" fill="#16204A"/>
      <path d="M150 140 L-60 1000 L360 1000Z" fill="#FFF3B0" opacity=".12"/><path d="M930 140 L720 1000 L1140 1000Z" fill="#FFF3B0" opacity=".12"/>
      {''.join(f'<rect x="{x - 8}" y="150" width="16" height="380" fill="#5A6472" stroke="{LINEA}" stroke-width="5"/><rect x="{x - 70}" y="110" width="140" height="70" rx="8" fill="#FFF3B0" stroke="{LINEA}" stroke-width="7"/>' for x in (150, 930))}
      <path d="M0 520 Q540 380 1080 520 V1050 H0Z" fill="#2C3960" stroke="{LINEA}" stroke-width="10"/>
      <path d="M0 520 Q270 440 540 420 V1050 H0Z" fill="{ca[1]}" opacity=".35"/><path d="M540 420 Q810 440 1080 520 V1050 H540Z" fill="{cb[1]}" opacity=".35"/>
      {teste}
      <rect x="0" y="990" width="1080" height="70" fill="#E2432F" stroke="{LINEA}" stroke-width="8"/>{''.join(f'<rect x="{x}" y="1002" width="150" height="46" rx="6" fill="{c}"/>' for x, c in ((30, ca[0]), (230, "#FFD23F"), (430, "#FFFFFF"), (630, "#FFD23F"), (830, cb[0])))}
      <rect x="0" y="1060" width="1080" height="860" fill="#3FA34D"/>{''.join(f'<rect x="0" y="{y}" width="1080" height="70" fill="#379645"/>' for y in range(1130, 1920, 140))}
      <path d="M0 1100 H1080 M540 1100 V1920" stroke="#F4F4F4" stroke-width="10"/><ellipse cx="540" cy="1500" rx="250" ry="90" fill="none" stroke="#F4F4F4" stroke-width="10"/>
      <rect x="0" y="1055" width="1080" height="12" fill="{LINEA}"/>"""


CARTONE_COLORI = {"rosso": ("#E2432F", "#FFFFFF"), "giallo": ("#FFD23F", "#1A1206"), "verde": ("#5BD07A", "#1A1206"), "rosa": ("#F0609E", "#FFFFFF"),
                  "arancio": ("#F28C28", "#FFFFFF"), "blu": ("#3E8EF0", "#FFFFFF"), "bianco": ("#FFF8EA", "#1A1206")}


def cartone(cid, dur, sfondo="canile", giorni=30, famiglia=0, famiglia_prima=None, attori=(), etichette=(), nuvole=(), oggetti=(), sfx=None,
            numero=None, voto=None, commento=None, scelta=None, hud=True, colori=None, tabellone=None, tabella=None, tiro=None, regia=True):
    """Una scena di Paolino a cartone. attori: [{"img": "felice", "x": 540, "y": 1560, "h": 700, "flip": False, "anim": ["entra_sx", "respira"], "t0": 0}]
    (x e y = centro dei piedi); etichette: [{"t": "PAOLINO", "c": "rosso", "x": 60, "y": 900, "r": -5, "z": 64, "t0": 0.3}];
    nuvole: [{"t": "VIENI, TESORO!", "x": 80, "y": 640, "w": 440, "coda": "sx", "t0": 0.4}]; oggetti: emoji come attrezzi di scena
    [{"e": "🧽", "x": 300, "y": 900, "z": 130, "t0": 1}]; numero: {"n": 29, "sotto": "PER TROVARE CASA"}; voto: {"parola": "IL BAGNO", "chiave": "BAGNO", "pc": 64};
    commento: {"t": "testo del commento", "cuori": 12}; scelta: {"a": [emoji, nome, parola], "b": [...]}.
    23/11 (Officina, «la regia»): lo sfondo, i personaggi e gli oggetti stanno dentro una telecamera che si muove piano in ogni scena
    (avvicinamento, carrellata a sinistra, allontanamento, carrellata a destra, a turno) e fa un colpo di zoom sui momenti forti
    (BAU!, GOL!, lo svenimento); le scritte restano ferme. Il numero dei giorni è un calendario a strappo: con numero["prima"]
    si vede il numero di ieri e il foglio si gira e vola via."""
    fp = famiglia if famiglia_prima is None else famiglia_prima
    css = f"""
    #root .fondo {{ position: absolute; inset: 0; }}
    #root .hud {{ position: absolute; left: 34px; top: 190px; display: flex; gap: 12px; z-index: 4; }}
    #root .hud div {{ min-width: 150px; padding: 6px 16px 4px; border-radius: 12px; background: #15100C; border: 4px solid #F3E6C8; text-align: center; }}
    #root .hud small {{ display: block; font: 900 20px/1.2 var(--font-body); color: #F3E6C8; letter-spacing: 1px; }}
    #root .hud b {{ display: block; font: 400 56px/1.05 "Anton", sans-serif; color: #FFD23F; }}
    #root .hud .f b {{ color: #6FE38F; }}
    #root .att {{ position: absolute; width: 1000px; display: flex; justify-content: center; align-items: flex-end; }}
    #root .att img {{ height: 100%; width: auto; filter: drop-shadow(0 14px 0 rgba(0,0,0,.18)); }}
    #root .att.flip img {{ transform: scaleX(-1); }}
    #root .om {{ position: absolute; height: 34px; border-radius: 50%; background: rgba(0,0,0,.22); }}
    #root .et {{ position: absolute; white-space: nowrap; z-index: 3; }}
    #root .et span {{ display: inline-block; font: 400 var(--z)/1.05 "Anton", sans-serif; letter-spacing: 1px; padding: 8px 22px 10px; border: 6px solid #1A1206; border-radius: 12px; box-shadow: 0 8px 0 rgba(0,0,0,.35); transform: rotate(var(--r)); }}
    #root .nv {{ position: absolute; z-index: 3; }}
    #root .nv div {{ position: relative; padding: 18px 26px; background: #FFFFFF; border: 7px solid #1A1206; border-radius: 44px; font: 400 60px/1.08 "Anton", sans-serif; color: #1A1206; text-align: center; box-shadow: 0 8px 0 rgba(0,0,0,.25); }}
    #root .nv div::after {{ content: ""; position: absolute; bottom: -30px; width: 44px; height: 44px; background: #FFFFFF; border-right: 7px solid #1A1206; border-bottom: 7px solid #1A1206; transform: rotate(45deg) skew(12deg, 12deg); }}
    #root .nv.sx div::after {{ left: 70px; }} #root .nv.dx div::after {{ right: 70px; }}
    #root .og {{ position: absolute; line-height: 1; z-index: 2; color: #1A1206; filter: drop-shadow(0 8px 0 rgba(0,0,0,.25)); }}
    #root .sfx {{ position: absolute; z-index: 4; }}
    #root .sfx span {{ display: inline-block; transform: rotate(-8deg); font: 400 110px/1 "Anton", sans-serif; color: #FFD23F; -webkit-text-stroke: 8px #1A1206; paint-order: stroke fill; text-shadow: 0 10px 0 #1A1206; }}
    #root .cam, #root .mondo {{ position: absolute; inset: 0; }}
    #root .cal {{ position: absolute; left: 280px; width: 520px; top: 300px; z-index: 3; perspective: 1400px; }}
    #root .cal .tt {{ position: relative; height: 96px; background: #E2432F; border: 8px solid #1A1206; border-radius: 24px 24px 0 0; text-align: center; font: 400 64px/80px "Anton", sans-serif; letter-spacing: 4px; color: #FFFFFF; }}
    #root .cal .an {{ position: absolute; top: -26px; width: 26px; height: 54px; border-radius: 13px; background: #6B7896; border: 6px solid #1A1206; }}
    #root .cal .pg {{ position: relative; height: 350px; margin-top: -8px; background: #FFF8EA; border: 8px solid #1A1206; border-radius: 0 0 24px 24px; text-align: center; box-shadow: 0 10px 0 #D9CBB0, 0 18px 0 #1A1206; }}
    #root .cal .pg b {{ display: block; font: 400 290px/340px "Anton", sans-serif; color: #1A1206; }}
    #root .cal .fg {{ position: absolute; left: 0; right: 0; top: 96px; margin-top: -8px; box-shadow: none; transform-origin: 50% 0%; backface-visibility: visible; }}
    #root .cal-s {{ position: absolute; left: 0; right: 0; top: 780px; text-align: center; z-index: 3; }}
    #root .cal-s span {{ display: inline-block; font: 400 58px/1.1 "Anton", sans-serif; color: #1A1206; background: #5BD07A; border: 6px solid #1A1206; border-radius: 12px; padding: 6px 24px 8px; transform: rotate(-3deg); box-shadow: 0 8px 0 rgba(0,0,0,.35); }}
    #root .num {{ position: absolute; left: 0; right: 0; top: 290px; text-align: center; z-index: 3; }}
    #root .num b {{ display: block; font: 400 330px/0.95 "Anton", sans-serif; color: #FFC93C; -webkit-text-stroke: 12px #1A1206; paint-order: stroke fill; text-shadow: 0 14px 0 #1A1206; }}
    #root .num i {{ display: block; font: 400 120px/1 "Anton", sans-serif; font-style: normal; color: #FFFFFF; -webkit-text-stroke: 9px #1A1206; paint-order: stroke fill; text-shadow: 0 9px 0 #1A1206; }}
    #root .num span {{ display: inline-block; margin-top: 26px; font: 400 64px/1.1 "Anton", sans-serif; color: #1A1206; background: #5BD07A; border: 6px solid #1A1206; border-radius: 12px; padding: 6px 24px 8px; transform: rotate(-3deg); box-shadow: 0 8px 0 rgba(0,0,0,.35); }}
    #root .vt {{ position: absolute; left: 40px; right: 40px; top: 300px; text-align: center; z-index: 3; }}
    #root .vt .h {{ font: 400 104px/1 "Anton", sans-serif; color: #FFFFFF; -webkit-text-stroke: 9px #1A1206; paint-order: stroke fill; text-shadow: 0 9px 0 #1A1206; }}
    #root .vt .p {{ display: inline-block; margin-top: 26px; font: 400 150px/1.05 "Anton", sans-serif; color: #1A1206; background: #FFF1C9; border: 8px solid #1A1206; border-radius: 22px; padding: 6px 46px 14px; transform: rotate(-3deg); box-shadow: 0 12px 0 rgba(0,0,0,.35); }}
    #root .vt .bar {{ position: relative; margin: 40px auto 0; width: 820px; height: 86px; border-radius: 43px; background: #2C2C38; border: 6px solid #1A1206; overflow: hidden; }}
    #root .vt .bar i {{ position: absolute; left: 0; top: 0; bottom: 0; background: #5BD07A; }}
    #root .vt .bar em {{ position: absolute; inset: 0; font: 400 54px/74px "Anton", sans-serif; font-style: normal; color: #FFFFFF; -webkit-text-stroke: 6px #1A1206; paint-order: stroke fill; }}
    #root .cm {{ position: absolute; left: 50px; right: 50px; top: 760px; z-index: 3; }}
    #root .cm .q {{ background: #FFFFFF; border: 7px solid #1A1206; border-radius: 26px; padding: 30px 34px 22px; box-shadow: 0 10px 0 rgba(0,0,0,.3); font: 800 50px/1.2 var(--font-body); color: #1A1206; }}
    #root .cm .q small {{ display: block; margin-top: 10px; font: 900 40px/1 var(--font-body); color: #E2432F; }}
    #root .cm .tg {{ position: absolute; right: 30px; top: -58px; }}
    #root .cm .tg span {{ display: inline-block; font: 400 62px/1.05 "Anton", sans-serif; color: #1A1206; background: #FFD23F; border: 6px solid #1A1206; border-radius: 12px; padding: 6px 22px 8px; transform: rotate(4deg); box-shadow: 0 8px 0 rgba(0,0,0,.35); }}
    #root .sc {{ position: absolute; left: 40px; right: 40px; top: 300px; z-index: 3; text-align: center; }}
    #root .sc .h {{ font: 400 92px/1.02 "Anton", sans-serif; color: #FFFFFF; -webkit-text-stroke: 8px #1A1206; paint-order: stroke fill; text-shadow: 0 8px 0 #1A1206; }}
    #root .sc .ops {{ position: relative; margin-top: 34px; height: 300px; }}
    #root .sc .op {{ position: absolute; top: 0; width: 470px; height: 280px; border-radius: 28px; background: #FFF1C9; border: 8px solid #1A1206; box-shadow: 0 12px 0 rgba(0,0,0,.35); display: flex; flex-direction: column; align-items: center; justify-content: center; }}
    #root .sc .opa {{ left: 0; }} #root .sc .opb {{ right: 0; }}
    #root .sc .op .em {{ font-size: 100px; line-height: 1.1; color: #1A1206; }}
    #root .sc .op b {{ font: 400 64px/1.05 "Anton", sans-serif; color: #1A1206; }}
    #root .sc .o {{ position: absolute; left: 50%; top: 110px; width: 130px; margin-left: -65px; font: 400 36px/62px "Anton", sans-serif; color: #1A1206; background: #FFD23F; border: 5px solid #1A1206; border-radius: 31px; }}"""
    js = []
    fondo_svg = sfondo_stadio(*(colori or [["#1B4FA0", "#111111"], ["#D2151C", "#111111"]])) if sfondo == "stadio" else CARTONE_SFONDI.get(sfondo, CARTONE_SFONDI["canile"])
    mondo = [f'<svg class="fondo" viewBox="0 0 1080 1920">{fondo_svg}</svg>']; corpo = []; colpi = []  # mondo: dentro la telecamera; corpo: le scritte ferme
    css += """
    #root .tb { position: absolute; left: 40px; right: 40px; top: 250px; z-index: 3; text-align: center; }
    #root .tb .s { display: inline-block; font: 400 46px/1.05 "Anton", sans-serif; color: #1A1206; background: #FFD23F; border: 6px solid #1A1206; border-radius: 12px; padding: 4px 22px 6px; transform: rotate(-2deg); box-shadow: 0 8px 0 rgba(0,0,0,.35); }
    #root .tb .q { display: grid; grid-template-columns: 1fr auto 1fr; align-items: stretch; margin-top: 22px; background: #15100C; border: 8px solid #F3E6C8; border-radius: 26px; overflow: hidden; box-shadow: 0 12px 0 rgba(0,0,0,.4); }
    #root .tb .q b { font: 400 66px/1.05 "Anton", sans-serif; padding: 26px 10px; color: #FFFFFF; -webkit-text-stroke: 6px #15100C; paint-order: stroke fill; }
    #root .tb .q em { font: 400 140px/1 "Anton", sans-serif; font-style: normal; color: #FFD23F; padding: 14px 18px; white-space: nowrap; }
    #root .tb .q em.lungo { font-size: 104px; padding-top: 30px; }
    #root .cl { position: absolute; left: 60px; right: 60px; top: 300px; z-index: 3; }
    #root .cl h3 { margin: 0 0 18px; text-align: center; font: 400 80px/1 "Anton", sans-serif; color: #FFFFFF; -webkit-text-stroke: 8px #1A1206; paint-order: stroke fill; text-shadow: 0 8px 0 #1A1206; }
    #root .cl .r { display: grid; grid-template-columns: 70px 1fr 160px; align-items: center; gap: 14px; margin-bottom: 14px; background: #FFF8EA; border: 6px solid #1A1206; border-radius: 18px; padding: 8px 18px; box-shadow: 0 7px 0 rgba(0,0,0,.3); }
    #root .cl .r span { font: 400 54px/1 "Anton", sans-serif; color: #1A1206; }
    #root .cl .r b { font: 400 56px/1.1 "Anton", sans-serif; color: #1A1206; text-align: left; }
    #root .cl .r i { font: 400 56px/1 "Anton", sans-serif; font-style: normal; color: #1A1206; text-align: right; }
    #root .cl .r.primo { background: #FFD23F; }"""
    if tabellone:
        T = tabellone; bg = lambda c: f"background:linear-gradient(90deg,{c[0]} 0 50%,{c[1]} 50% 100%)"
        corpo.append(f'<div class="tb" id="{cid}-tb">' + (f'<div class="s">{ESC(T["sopra"])}</div>' if T.get("sopra") else "")
                     + f'<div class="q"><b style="{bg(T["ca"])}">{ESC(T["a"])}</b><em id="{cid}-ts"{" class=\"lungo\"" if len(str(T.get("ga", 0)) + str(T.get("gb", 0))) > 2 else ""}><span id="{cid}-ga">{T.get("ga", 0)}</span> – <span id="{cid}-gb">{T.get("gb", 0)}</span></em><b style="{bg(T["cb"])}">{ESC(T["b"])}</b></div></div>')
        js.append(f'    tl.fromTo("#{cid}-tb", {{ y: -120, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.4, ease: "back.out(1.6)" }}, 0.05);')
        js.append(f'    tl.fromTo("#{cid}-ts", {{ scale: 2.2 }}, {{ scale: 1, duration: 0.4, ease: "back.out(2)" }}, 0.35);')
        if T.get("conta"):  # 20/11 (Officina): il punteggio sale da 0 al risultato finale, gol dopo gol
            js.append(f'    tl.fromTo("#{cid}-ga", {{ innerText: 0 }}, {{ innerText: {int(T.get("ga", 0))}, snap: {{ innerText: 1 }}, duration: 1.6, ease: "power1.in" }}, 0.4);')
            js.append(f'    tl.fromTo("#{cid}-gb", {{ innerText: 0 }}, {{ innerText: {int(T.get("gb", 0))}, snap: {{ innerText: 1 }}, duration: 1.6, ease: "power1.in" }}, 0.4);')
    if tiro is not None:  # 20/11 (Officina): la porta in mezzo al campo e il pallone che entra, poi «GOL!»
        t0 = float(tiro)
        mondo.append(f'''<svg class="porta" viewBox="0 0 420 220" style="position:absolute;left:330px;top:1085px;width:420px;height:220px;z-index:1">
          <g stroke="#F4F4F4" stroke-width="3" opacity=".75">{''.join(f'<path d="M{x} 20 V215"/>' for x in range(30, 400, 30))}{''.join(f'<path d="M14 {y} H406"/>' for y in range(40, 215, 30))}</g>
          <path d="M10 215 V12 H410 V215" fill="none" stroke="#FFFFFF" stroke-width="16" stroke-linejoin="round"/><path d="M10 215 V12 H410 V215" fill="none" stroke="#1A1206" stroke-width="5"/></svg>
          <div class="og" id="{cid}-pl" style="left:80px;top:1560px;font-size:110px;color:#FFFFFF;z-index:3">⚽</div>''')
        corpo.append(f'<div class="sfx" id="{cid}-gl" style="left:330px;top:900px"><span>GOL!</span></div>'); colpi.append(t0 + 0.7)
        js.append(f'    tl.fromTo("#{cid}-pl", {{ x: 0, y: 0, rotation: 0, scale: 1 }}, {{ x: 400, y: -400, rotation: 720, scale: 0.55, duration: 0.7, ease: "power2.out" }}, {t0:.2f});')
        js.append(f'    tl.to("#{cid}-pl", {{ opacity: 0, duration: 0.1 }}, {t0 + 0.72:.2f});')  # il pallone sparisce nella rete (sotto ci passano i sottotitoli)
        js.append(f'    tl.fromTo("#{cid}-gl", {{ scale: 0, opacity: 0 }}, {{ scale: 1.25, opacity: 1, duration: 0.3, ease: "back.out(3)" }}, {t0 + 0.7:.2f});')
        js.append(f'    tl.to("#{cid}-gl", {{ keyframes: [{{ rotation: -6, duration: 0.08 }}, {{ rotation: 6, duration: 0.08 }}, {{ rotation: 0, duration: 0.08 }}], repeat: 3 }}, {t0 + 1.0:.2f});')
    if tabella:
        righe = "".join(f'<div class="r{" primo" if i == 0 else ""}" id="{cid}-r{i}"><span>{i + 1}</span><b>{ESC(x["nome"])}</b><i>{x["pt"]} PT</i></div>' for i, x in enumerate(tabella[:5]))
        corpo.append(f'<div class="cl"><h3 id="{cid}-ch">CLASSIFICA</h3>{righe}</div>')
        js.append(f'    tl.fromTo("#{cid}-ch", {{ y: -60, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.3, ease: "back.out(2)" }}, 0.05);')
        for i in range(len(tabella[:5])):
            js.append(f'    tl.fromTo("#{cid}-r{i}", {{ x: {-700 if i % 2 == 0 else 700}, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.35, ease: "back.out(1.6)" }}, {0.3 + i * 0.2:.2f});')
    for i, o in enumerate(oggetti):
        mondo.append(f'<div class="og" id="{cid}-g{i}" style="left:{o["x"]}px;top:{o["y"]}px;font-size:{o.get("z", 120)}px{";color:" + o["colore"] if o.get("colore") else ""}">{ESC(o["e"])}</div>')
        js.append(f'    tl.fromTo("#{cid}-g{i}", {{ scale: 0, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.35, ease: "back.out(2.6)" }}, {o.get("t0", 0.3):.2f});')
        if o.get("vola"): js.append(f'    tl.to("#{cid}-g{i}", {{ keyframes: [{{ y: -24, duration: 0.4 }}, {{ y: 0, duration: 0.4 }}], repeat: {max(1, int(dur / 0.8))} }}, {o.get("t0", 0.3) + 0.35:.2f});')
    for i, a in enumerate(attori):
        h = a.get("h", 700); x, y = a.get("x", 540), a.get("y", 1560)
        mondo.append(f'<div class="om" style="left:{x - h * 0.32:.0f}px;top:{y - 20}px;width:{h * 0.64:.0f}px"></div>')
        mondo.append(f'<div class="att{" flip" if a.get("flip") else ""}" id="{cid}-a{i}" style="left:{x - 500}px;top:{y - h}px;height:{h}px">'
                     + (f'<img src="assets/svg/{a["svg"]}" alt=""></div>' if a.get("svg") else f'<img src="assets/img/paolino-{a["img"]}.png" alt=""></div>'))
        t0 = a.get("t0", 0.0); an = a.get("anim", ["pop"]); an = [an] if isinstance(an, str) else an; sel = f"#{cid}-a{i}"
        rip = lambda per: max(1, int((dur - t0) / per))
        for k in an:
            if k == "pop": js.append(f'    tl.fromTo("{sel}", {{ scale: 0.6, opacity: 0, transformOrigin: "50% 100%" }}, {{ scale: 1, opacity: 1, duration: 0.35, ease: "back.out(2.2)" }}, {t0:.2f});')
            elif k in ("entra_sx", "entra_dx"): js.append(f'    tl.fromTo("{sel}", {{ x: {-1000 if k == "entra_sx" else 1000} }}, {{ x: 0, duration: 0.5, ease: "back.out(1.3)" }}, {t0:.2f});')
            elif k == "respira": js.append(f'    tl.to("{sel}", {{ keyframes: [{{ scaleY: 1.035, duration: 0.6 }}, {{ scaleY: 1, duration: 0.6 }}], transformOrigin: "50% 100%", repeat: {rip(1.2)} }}, {t0 + 0.4:.2f});')
            elif k == "salta": js.append(f'    tl.to("{sel}", {{ keyframes: [{{ y: -70, duration: 0.22, ease: "power2.out" }}, {{ y: 0, duration: 0.22, ease: "power2.in" }}], repeat: {rip(0.6)}, repeatDelay: 0.16 }}, {t0 + 0.3:.2f});')
            elif k == "trema": js.append(f'    tl.to("{sel}", {{ keyframes: [{{ x: -9, duration: 0.05 }}, {{ x: 9, duration: 0.05 }}, {{ x: -6, duration: 0.05 }}, {{ x: 0, duration: 0.05 }}], repeat: {rip(0.2)} }}, {t0 + 0.2:.2f});')
            elif k == "scrolla": js.append(f'    tl.to("{sel}", {{ keyframes: [{{ rotation: -7, duration: 0.07 }}, {{ rotation: 7, duration: 0.07 }}, {{ rotation: 0, duration: 0.07 }}], transformOrigin: "50% 90%", repeat: {rip(0.21)} }}, {t0 + 0.2:.2f});')
            elif k == "corre":  # attraversa la scena da a["da"] (x relativo) ad a["a"], saltellando
                js.append(f'    tl.fromTo("{sel}", {{ x: {a.get("da", -1100)} }}, {{ x: {a.get("a", 1100)}, duration: {max(0.8, dur - t0):.2f}, ease: "none" }}, {t0:.2f});')
                js.append(f'    tl.to("{sel}", {{ keyframes: [{{ y: -40, duration: 0.14 }}, {{ y: 0, duration: 0.14 }}], repeat: {rip(0.28)} }}, {t0:.2f});')
            elif k == "cade":  # sviene: si gira di lato e cade (a["t1"] = quando)
                t1 = a.get("t1", t0 + 1.0); colpi.append(t1 + 0.3)
                js.append(f'    tl.to("{sel}", {{ rotation: {a.get("verso", 88)}, y: 60, scale: {a.get("scala", 1)}, duration: 0.45, ease: "bounce.out", transformOrigin: "50% 100%" }}, {t1:.2f});')
            elif k == "esci_dx": js.append(f'    tl.to("{sel}", {{ x: 1100, duration: 0.45, ease: "power2.in" }}, {a.get("t1", dur - 0.6):.2f});')
    for i, e in enumerate(etichette):
        bg, fg = CARTONE_COLORI.get(e.get("c", "giallo"), CARTONE_COLORI["giallo"])
        corpo.append(f'<div class="et" id="{cid}-e{i}" style="left:{e.get("x", 60)}px;top:{e.get("y", 900)}px;--r:{e.get("r", -4)}deg;--z:{e.get("z", 64)}px">'
                     f'<span style="background:{bg};color:{fg}">{ESC(e["t"])}</span></div>')
        js.append(f'    tl.fromTo("#{cid}-e{i}", {{ scale: 0.2, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.3, ease: "back.out(2.6)" }}, {e.get("t0", 0.3 + i * 0.4):.2f});')
    for i, n in enumerate(nuvole):
        corpo.append(f'<div class="nv {n.get("coda", "sx")}" id="{cid}-n{i}" style="left:{n.get("x", 80)}px;top:{n.get("y", 600)}px;width:{n.get("w", 460)}px"><div>{ESC(n["t"])}</div></div>')
        js.append(f'    tl.fromTo("#{cid}-n{i}", {{ scale: 0, opacity: 0, transformOrigin: "{"20%" if n.get("coda", "sx") == "sx" else "80%"} 100%" }}, {{ scale: 1, opacity: 1, duration: 0.3, ease: "back.out(2.4)" }}, {n.get("t0", 0.5):.2f});')
    if sfx:
        corpo.append(f'<div class="sfx" id="{cid}-x" style="left:{sfx.get("x", 600)}px;top:{sfx.get("y", 700)}px"><span>{ESC(sfx["t"])}</span></div>')
        t0 = sfx.get("t0", 0.4); colpi.append(t0)
        js.append(f'    tl.fromTo("#{cid}-x", {{ scale: 0, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.25, ease: "back.out(3)" }}, {t0:.2f});')
        js.append(f'    tl.to("#{cid}-x", {{ keyframes: [{{ x: -10, duration: 0.05 }}, {{ x: 10, duration: 0.05 }}, {{ x: 0, duration: 0.05 }}], repeat: 4 }}, {t0 + 0.25:.2f});')
    hud_g = giorni
    if numero and regia:  # 23/11: il calendario a strappo (il numero di ieri si gira e vola via, sotto c'è quello di oggi)
        prima = numero.get("prima"); T = 0.55
        corpo.append(f'<div class="cal" id="{cid}-cal"><div class="tt">MANCANO<i class="an" style="left:90px"></i><i class="an" style="right:90px"></i></div>'
                     f'<div class="pg"><b id="{cid}-nb"{" style=\"opacity:0\"" if prima else ""}>{numero["n"]}</b></div>'
                     + (f'<div class="pg fg" id="{cid}-fg"><b id="{cid}-fb">{prima}</b></div>' if prima else "") + '</div>'
                     + (f'<div class="cal-s"><span id="{cid}-ns">GIORNI {ESC(numero["sotto"])}</span></div>' if numero.get("sotto") else ""))
        js.append(f'    tl.fromTo("#{cid}-cal", {{ y: -500, rotation: -6 }}, {{ y: 0, rotation: 0, duration: 0.45, ease: "back.out(1.4)" }}, 0.05);')
        if numero.get("sotto"): js.append(f'    tl.fromTo("#{cid}-ns", {{ scale: 0.2, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.3, ease: "back.out(2.6)" }}, 0.6);')
        if prima:  # il foglio si alza sugli anelli (si vede il davanti), di taglio cambia il numero, poi si vede il retro bianco e vola via
            hud_g = prima
            js.append(f'    tl.to("#{cid}-fg", {{ rotationX: -88, duration: 0.16, ease: "power2.in" }}, {T:.2f});')
            js.append(f'    tl.set("#{cid}-fb", {{ opacity: 0 }}, {T + 0.16:.2f}); tl.set("#{cid}-nb", {{ opacity: 1 }}, {T + 0.16:.2f}); tl.set("#{cid}-hg", {{ textContent: "{numero["n"]}" }}, {T + 0.16:.2f});')
            js.append(f'    tl.to("#{cid}-fg", {{ rotationX: -175, y: -380, x: 160, rotation: 14, opacity: 0, duration: 0.45, ease: "power1.out" }}, {T + 0.16:.2f});')
            js.append(f'    tl.fromTo("#{cid}-nb", {{ scale: 1.3 }}, {{ scale: 1, duration: 0.35, ease: "back.out(3)" }}, {T + 0.16:.2f});')
            js.append(f'    tl.to("#{cid}-hg", {{ keyframes: [{{ scale: 1.4, duration: 0.15 }}, {{ scale: 1, duration: 0.2 }}] }}, {T + 0.16:.2f});')
            colpi.append(T + 0.16)
    elif numero:
        corpo.append(f'<div class="num"><b id="{cid}-nb">{numero["n"]}</b><i id="{cid}-ni">GIORNI</i>' + (f'<span id="{cid}-ns">{ESC(numero["sotto"])}</span>' if numero.get("sotto") else "") + '</div>')
        js.append(f'    tl.fromTo("#{cid}-nb", {{ scale: 2.4, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.4, ease: "back.out(1.8)" }}, 0.05);')
        js.append(f'    tl.fromTo("#{cid}-ni", {{ y: 60, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.3, ease: "back.out(2)" }}, 0.3);')
        if numero.get("sotto"): js.append(f'    tl.fromTo("#{cid}-ns", {{ scale: 0.2, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.3, ease: "back.out(2.6)" }}, 0.6);')
    if voto:
        pc = max(0, min(100, int(voto.get("pc", 0)))); con_pc = "pc" in voto and voto["pc"] is not None  # 21/11: senza voti niente barra (era «TV 0%»)
        corpo.append(f'<div class="vt"><div class="h" id="{cid}-vh">AVETE SCELTO</div><div class="p" id="{cid}-vp">{ESC(voto["parola"])}</div>'
                     + (f'<div class="bar" id="{cid}-vb"><i id="{cid}-vi" style="width:{pc}%"></i><em>{ESC(voto["chiave"])} {pc}%</em></div>' if con_pc else "") + '</div>')
        js.append(f'    tl.fromTo("#{cid}-vh", {{ y: -60, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.3, ease: "back.out(2)" }}, 0.05);')
        js.append(f'    tl.fromTo("#{cid}-vp", {{ scale: 0.2, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.35, ease: "back.out(2.4)" }}, 0.35);')
        if con_pc: js.append(f'    tl.fromTo("#{cid}-vb", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.2 }}, 0.7); tl.fromTo("#{cid}-vi", {{ width: "0%" }}, {{ width: "{pc}%", duration: 0.8, ease: "power2.out" }}, 0.75);')
    if commento:
        corpo.append(f'<div class="cm" id="{cid}-c"><div class="q">«{ESC(commento["t"])}»' + (f'<small>♥ {commento["cuori"]}</small>' if commento.get("cuori") else "")
                     + f'</div><div class="tg" id="{cid}-ct"><span>PAROLE VOSTRE</span></div></div>')
        js.append(f'    tl.fromTo("#{cid}-c", {{ y: 80, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.35, ease: "back.out(1.8)" }}, {commento.get("t0", 0.4):.2f});')
        js.append(f'    tl.fromTo("#{cid}-ct", {{ scale: 0, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.3, ease: "back.out(3)" }}, {commento.get("t0", 0.4) + 0.4:.2f});')
    if scelta:
        ops = "".join(f'<div class="op op{k}" id="{cid}-op{k}"><span class="em">{ESC(v[0])}</span><b>{ESC(v[1])}</b></div>' for k, v in (("a", scelta["a"]), ("b", scelta["b"])))
        corpo.append(f'<div class="sc"><div class="h" id="{cid}-sh">DOMANI COSA FA PAOLINO?</div><div class="ops">{ops}<div class="o">OPPURE</div></div></div>')
        js.append(f'    tl.fromTo("#{cid}-sh", {{ y: -60, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.3, ease: "back.out(2)" }}, 0.05);')
        js.append(f'    tl.fromTo("#{cid}-opa", {{ x: -320, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.4, ease: "back.out(1.8)" }}, 0.3);')
        js.append(f'    tl.fromTo("#{cid}-opb", {{ x: 320, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.4, ease: "back.out(1.8)" }}, 0.5);')
        js.append(f'    tl.to(["#{cid}-opa", "#{cid}-opb"], {{ keyframes: [{{ scale: 1.05, duration: 0.3 }}, {{ scale: 1, duration: 0.3 }}], repeat: {max(1, int(dur / 1.2))}, stagger: 0.3 }}, 1.0);')
    if hud: corpo.append(f'<div class="hud"><div><small>GIORNI</small><b id="{cid}-hg">{hud_g}</b></div><div class="f"><small>FAMIGLIA</small><b id="{cid}-f">{fp}%</b></div></div>')
    if hud and famiglia_prima is not None and famiglia_prima != famiglia:
        js.append(f'    tl.set("#{cid}-f", {{ textContent: "{famiglia}%" }}, {max(0.8, dur * 0.5):.2f}); tl.to("#{cid}-f", {{ keyframes: [{{ scale: 1.4, duration: 0.15 }}, {{ scale: 1, duration: 0.2 }}] }}, {max(0.8, dur * 0.5):.2f});')
    if regia:
        k = int(re.sub(r"\D", "", cid) or 0)
        s0, x0, s1, x1 = [(1.0, 0, 1.07, 0), (1.07, 28, 1.07, -28), (1.08, 0, 1.0, 0), (1.07, -28, 1.07, 28)][k % 4]
        js.insert(0, f'    tl.set("#{cid}-cam", {{ scale: {s0}, x: {x0}, transformOrigin: "50% 60%" }}, 0); tl.to("#{cid}-cam", {{ scale: {s1}, x: {x1}, duration: {dur:.2f}, ease: "sine.inOut" }}, 0);')
        fatti = []
        for t in sorted(colpi):
            if t > dur - 0.5 or any(abs(t - f) < 0.7 for f in fatti): continue
            fatti.append(t)
            js.append(f'    tl.to("#{cid}-m", {{ keyframes: [{{ scale: 1.09, duration: 0.12, ease: "power2.out" }}, {{ scale: 1, duration: 0.5, ease: "power2.inOut" }}], transformOrigin: "50% 55%" }}, {t:.2f});')
        corpo.insert(0, f'<div class="cam" id="{cid}-cam"><div class="mondo" id="{cid}-m">' + "".join(mondo) + '</div></div>')
    else:
        corpo = mondo + corpo
    return _pagina(cid, "Paolino a cartone", css, "\n    ".join(corpo), "\n".join(js))

TIPI = {"cartone": cartone, "zampa30": zampa30, "avvento": avvento, "tappa": tappa, "tifosi": tifosi, "padroni": padroni, "corsa": corsa, "intruso": intruso, "intruso_svela": intruso_svela, "barre": barre, "sagoma": sagoma, "svela": svela, "figurina": figurina, "gancio": gancio, "luce": luce, "foto": foto, "cuccia": cuccia, "gatto": gatto, "duello": duello, "mappa": mappa, "commento": commento,
        "numero": numero, "classifica": classifica, "vetrina": vetrina, "chiusura": chiusura}
