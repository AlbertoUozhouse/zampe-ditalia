"""Il tifo (15/11): il tuo cane tifa la tua squadra e sulla mappa porta la sciarpa coi suoi colori.

Dallo studio della pagina rivale col nostro stesso gioco: «La tua casa coi colori della tua squadra» è il loro reel più visto
dopo il lancio (179.000 views). In Italia la squadra è l'identità più forte insieme alla città.
Solo nomi e colori delle squadre (nessun simbolo o stemma). Una squadra che non è qui non si mette: niente colori inventati.
"""
import re, unicodedata

# chiave: (nome da mostrare, colore 1, colore 2, parole che la indicano senza dubbi)
# i nomi che sono anche città (Napoli, Roma, Bari…) contano solo con una parola di tifo vicino: vedi trova()
SQUADRE = {
    "juventus": ("Juventus", "#F4F4F4", "#111111", ["juve", "juventus", "juventino", "juventina", "bianconeri", "bianconero"]),
    "inter": ("Inter", "#1B4FA0", "#111111", ["inter", "internazionale", "interista", "interisti"]),
    "milan": ("Milan", "#D2151C", "#111111", ["milan", "milanista", "milanisti"]),
    "napoli": ("Napoli", "#12A0D7", "#F4F4F4", ["napoli", "sscnapoli", "forzanapoli"]),
    "roma": ("Roma", "#8E1F2F", "#F0BC42", ["roma", "asroma", "romanista", "romanisti"]),
    "lazio": ("Lazio", "#87D8F7", "#F4F4F4", ["lazio", "laziale", "laziali", "biancocelesti"]),
    "fiorentina": ("Fiorentina", "#5B2A86", "#F4F4F4", ["fiorentina", "viola"]),
    "atalanta": ("Atalanta", "#1E71B8", "#111111", ["atalanta", "atalantino", "atalantina"]),
    "bologna": ("Bologna", "#A21C26", "#1A2F48", ["bologna"]),
    "torino": ("Torino", "#8A1E03", "#F4F4F4", ["torino", "granata", "toro"]),
    "genoa": ("Genoa", "#A41E2F", "#1C2C5B", ["genoa", "genoano"]),
    "sampdoria": ("Sampdoria", "#1B5497", "#F4F4F4", ["sampdoria", "samp", "doriano", "blucerchiati"]),
    "cagliari": ("Cagliari", "#A6192E", "#002350", ["cagliari"]),
    "udinese": ("Udinese", "#F4F4F4", "#111111", ["udinese"]),
    "verona": ("Verona", "#002F6C", "#FFD200", ["verona", "hellas", "hellasverona"]),
    "parma": ("Parma", "#F4F4F4", "#111111", ["parma"]),
    "lecce": ("Lecce", "#FFD200", "#C8102E", ["lecce"]),
    "bari": ("Bari", "#F4F4F4", "#C8102E", ["bari"]),
    "palermo": ("Palermo", "#F5A3C7", "#111111", ["palermo", "rosanero"]),
    "catania": ("Catania", "#C8102E", "#1E4E9C", ["catania", "rossazzurri"]),
    "salernitana": ("Salernitana", "#7B1E2B", "#F4F4F4", ["salernitana"]),
    "sassuolo": ("Sassuolo", "#00A651", "#111111", ["sassuolo", "neroverdi"]),
    "empoli": ("Empoli", "#1E5AA8", "#F4F4F4", ["empoli"]),
    "monza": ("Monza", "#D0021B", "#F4F4F4", ["monza"]),
    "como": ("Como", "#1E4C9A", "#F4F4F4", ["como"]),
    "cremonese": ("Cremonese", "#9E1B32", "#8A96A3", ["cremonese", "grigiorossi"]),
    "pisa": ("Pisa", "#002F6C", "#111111", ["pisa"]),
    "venezia": ("Venezia", "#F37021", "#00843D", ["venezia", "arancioneroverdi"]),
    "spezia": ("Spezia", "#F4F4F4", "#111111", ["spezia"]),
    "brescia": ("Brescia", "#1F4E9E", "#F4F4F4", ["brescia"]),
    "frosinone": ("Frosinone", "#FFD200", "#1E4C9A", ["frosinone"]),
    "pescara": ("Pescara", "#1E73BE", "#F4F4F4", ["pescara"]),
    "foggia": ("Foggia", "#C8102E", "#111111", ["foggia"]),
    "taranto": ("Taranto", "#C8102E", "#1E4C9A", ["taranto"]),
    "avellino": ("Avellino", "#00843D", "#F4F4F4", ["avellino"]),
    "benevento": ("Benevento", "#C8102E", "#FFD200", ["benevento"]),
    "reggina": ("Reggina", "#8A1538", "#F4F4F4", ["reggina"]),
    "catanzaro": ("Catanzaro", "#FFD200", "#C8102E", ["catanzaro"]),
    "cosenza": ("Cosenza", "#C8102E", "#1E4C9A", ["cosenza"]),
    "padova": ("Padova", "#F4F4F4", "#C8102E", ["padova"]),
    "vicenza": ("Vicenza", "#C8102E", "#F4F4F4", ["vicenza"]),
    "triestina": ("Triestina", "#C8102E", "#F4F4F4", ["triestina"]),
    "perugia": ("Perugia", "#C8102E", "#F4F4F4", ["perugia"]),
    "ternana": ("Ternana", "#00843D", "#C8102E", ["ternana"]),
    "ascoli": ("Ascoli", "#F4F4F4", "#111111", ["ascoli"]),
    "modena": ("Modena", "#FFD200", "#1E4C9A", ["modena"]),
    "reggiana": ("Reggiana", "#8A1538", "#F4F4F4", ["reggiana"]),
    "cesena": ("Cesena", "#F4F4F4", "#111111", ["cesena"]),
    "messina": ("Messina", "#C8102E", "#FFD200", ["messina"]),
    "casertana": ("Casertana", "#C8102E", "#1E4C9A", ["casertana"]),
    "juve_stabia": ("Juve Stabia", "#FFD200", "#1E4C9A", ["juvestabia", "stabia"]),
    "trapani": ("Trapani", "#8A1E03", "#F4F4F4", ["trapani"]),
    "barletta": ("Barletta", "#C8102E", "#F4F4F4", ["barletta"]),
    "bisceglie": ("Bisceglie", "#1B4FA0", "#111111", ["bisceglie"]),
}

# 17/11, Alberto: «a Roma lo stadio Olimpico, a Milano San Siro»: gli stadi del Campionato delle Zampe (la squadra di casa gioca nel suo).
# Solo nomi di luoghi, mai quelli degli sponsor: dove lo stadio ha il nome di un'azienda si dice «lo stadio di <città>».
STADI = {"inter": ("SAN SIRO", "Milano"), "milan": ("SAN SIRO", "Milano"), "roma": ("STADIO OLIMPICO", "Roma"), "lazio": ("STADIO OLIMPICO", "Roma"),
         "napoli": ("STADIO MARADONA", "Napoli"), "juventus": ("STADIO DI TORINO", "Torino"), "torino": ("STADIO GRANDE TORINO", "Torino"),
         "fiorentina": ("STADIO FRANCHI", "Firenze"), "bologna": ("STADIO DALL'ARA", "Bologna"), "genoa": ("MARASSI", "Genova"), "sampdoria": ("MARASSI", "Genova"),
         "atalanta": ("STADIO DI BERGAMO", "Bergamo"), "verona": ("STADIO BENTEGODI", "Verona"), "udinese": ("STADIO FRIULI", "Udine"), "cagliari": ("STADIO DI CAGLIARI", "Cagliari"),
         "lecce": ("STADIO VIA DEL MARE", "Lecce"), "bari": ("STADIO SAN NICOLA", "Bari"), "palermo": ("STADIO BARBERA", "Palermo"), "catania": ("STADIO MASSIMINO", "Catania"),
         "parma": ("STADIO TARDINI", "Parma"), "avellino": ("STADIO PARTENIO", "Avellino"), "salernitana": ("STADIO ARECHI", "Salerno"), "como": ("STADIO SINIGAGLIA", "Como"),
         "venezia": ("STADIO PENZO", "Venezia"), "pisa": ("ARENA GARIBALDI", "Pisa"), "cremonese": ("STADIO ZINI", "Cremona"), "sassuolo": ("STADIO DI REGGIO EMILIA", "Reggio Emilia")}


def stadio(k):
    """(nome dello stadio, città) della squadra; per le squadre senza stadio in elenco, «STADIO DI <CITTÀ>»."""
    if k in STADI: return STADI[k]
    n = nome(k); return (f"STADIO DI {n.upper()}", n)


# parole che dicono che si parla di calcio: senza una di queste, «Napoli» o «Roma» sono la città, non la squadra
TIFO = re.compile(r"(?i)\b(tif\w*|forza|squadra|ultr\w*|curva|stadio)\b|⚽")


def _norm(s):
    s = unicodedata.normalize("NFD", (s or "").lower())
    return re.sub(r"[^a-z0-9 ]", " ", "".join(c for c in s if not unicodedata.combining(c))).strip()


def _citta(chiave):
    """Il nome della squadra è anche il nome di una città?"""
    return chiave not in ("juventus", "inter", "milan", "lazio", "fiorentina", "atalanta", "genoa", "sampdoria", "udinese", "salernitana",
                          "cremonese", "spezia", "reggina", "triestina", "ternana", "reggiana", "casertana", "juve_stabia")


def trova(nome, testo=""):
    """La chiave della squadra dal nome scritto dal lettore («Juve», «SSC Napoli», «interista»), oppure None.
    testo: i commenti della persona. Il nome (o un suo soprannome) deve comparire davvero nei commenti; se la squadra ha il nome
    di una città e nei commenti c'è solo quel nome, serve anche una parola di tifo («tifa», «forza», ⚽…): altrimenti è la città dove vive."""
    n = _norm(nome)
    if not n: return None
    nomi = lambda k: {_norm(SQUADRE[k][0]), _norm(SQUADRE[k][0]).replace(" ", ""), *SQUADRE[k][3]}
    k = next((k for k in SQUADRE if n in nomi(k) or n.replace(" ", "") in nomi(k)), None)  # prima il nome intero («juve stabia» non è la Juve)
    if not k: k = next((k for k in SQUADRE if any(w in SQUADRE[k][3] for w in n.split() if w not in ("calcio", "ssc", "ac", "as", "fc", "us"))), None)
    if not k: return None
    if testo:
        tutto = f" {_norm(testo)} "
        scritto = [x for x in nomi(k) if f" {x} " in tutto]
        if not scritto: return None
        if _citta(k) and set(scritto) <= {_norm(SQUADRE[k][0])} and not TIFO.search(testo): return None
    return k


def colori(k):
    v = SQUADRE.get(k)
    return {"n": v[0], "c": [v[1], v[2]]} if v else None


def nome(k):
    return SQUADRE[k][0] if k in SQUADRE else ""


if __name__ == "__main__":
    prove = [("Juve", "Treviso, Luna, cane, forza Juve!"), ("Napoli", "Napoli, Luna, cane"), ("Napoli", "Napoli, Luna, cane, tifa Napoli ⚽"),
             ("Inter", "Milano Rex interista"), ("Roma", "Roma, Kira, gatto"), ("Roma", "Roma, Kira, gatto, romanista"), ("Barcellona", "tifa Barcellona"),
             ("Juve Stabia", "Castellammare, Rocky, forza Juve Stabia"), ("Torino", "Torino, Max"), ("granata", "Torino, Max, granata nel cuore")]
    for n, t in prove: print(f"{n!r:14} {t!r:50} → {trova(n, t)}")
