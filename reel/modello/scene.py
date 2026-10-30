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
    "tramonto": {"cielo": ("#2B1240", "#8C2F5A", "#F2784B"), "colline": "#3A1636", "prato": "#2E1E26", "strada": "#3A1A3E", "ombra": "#8C2F5A", "terra": "#5A2350", "bordo": "#8C3F72", "costa": "#F2A65A", "bg": ("#8C2F5A", "#4A1645", "#1E0A24")},
    "aurora":   {"cielo": ("#031A1F", "#0B4D4A", "#2FA37A"), "colline": "#062B2C", "prato": "#0A2E22", "strada": "#0C3A3A", "ombra": "#0B4D4A", "terra": "#0E4A48", "bordo": "#1F7A70", "costa": "#5FE0B0", "bg": ("#0E5A55", "#06302F", "#021316")},
    "giorno":   {"cielo": ("#2E7BD6", "#62A8F0", "#BFE3FF"), "colline": "#3E8E41", "prato": "#4FA34F", "strada": "#5A6B7A", "ombra": "#62A8F0", "terra": "#4FA34F", "bordo": "#2F7A33", "costa": "#FFFFFF", "bg": ("#4A95E6", "#2468BE", "#123E80")},
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
    return re.sub(r'tl\.fromTo\(("[^"]+"), \{[^}]*\}, \{[^}]*?duration: ([\d.]+)[^}]*\}, [\d.]+\);',
                  r'tl.fromTo(\1, { scale: 1.04 }, { scale: 1, duration: \2, ease: "power2.out" }, 0);', js)

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
    li = "".join(f'<li id="{cid}-r{i}"><span class="p">{i + 1}</span><span class="w">{ESC(r["nome"])}</span><span class="v">{ESC(str(r["valore"]))}</span></li>'
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

TIPI = {"cuccia": cuccia, "gatto": gatto, "duello": duello, "mappa": mappa, "commento": commento,
        "numero": numero, "classifica": classifica, "vetrina": vetrina, "chiusura": chiusura}
