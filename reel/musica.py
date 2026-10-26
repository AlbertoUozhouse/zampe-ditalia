"""Musica originale e senza diritti per i reel, generata in modo procedurale (deriva da audio/synth_nt.py del kit).

Base notturna e allegra in Do maggiore a 100 BPM (Do Sol Lam Fa): pad, basso, marimba, cassa e clap.
Gli effetti cadono sui momenti indicati in un file JSON: {"durata": 21.2, "whoosh": [...], "pop": [...], "chime": [...], "tick": [...], "riser": t}
Uso: python3 reel/musica.py effetti.json uscita.wav
Solo numpy: i filtri sono FIR a finestra, niente scipy.
"""
import json, sys, wave
import numpy as np

SR = 44100
rng = np.random.default_rng(3)

def hz(m): return 440 * 2 ** ((m - 69) / 12)

def fir_lp(fc, n=129):
    t = np.arange(n) - (n - 1) / 2
    h = np.sinc(2 * fc / SR * t) * np.hamming(n)
    return h / h.sum()

def filtra(x, h): return np.convolve(x, h, mode="same")

def passabanda(x, lo, hi): return filtra(x, fir_lp(hi)) - filtra(x, fir_lp(lo))

def saw(f, t): return 2 * ((f * t) % 1) - 1

def marimba(m, d=0.5):
    t = np.arange(int(SR * d)) / SR; f = hz(m)
    s = np.sin(2*np.pi*f*t)*np.exp(-t*4) + 0.5*np.sin(2*np.pi*f*2.76*t)*np.exp(-t*9) + 0.25*np.sin(2*np.pi*f*5.4*t)*np.exp(-t*16)
    return s * np.minimum(1, t / 0.002)

def basso(m, d):
    t = np.arange(int(SR * d)) / SR; f = hz(m)
    s = (saw(f, t) * 0.8 + np.sin(2*np.pi*f*t)) * np.exp(-t*3.5) * np.minimum(1, t/0.004)
    return filtra(s, fir_lp(600))

def cassa():
    t = np.arange(int(SR * .35)) / SR; f = 45 + 80 * np.exp(-t * 30)
    return np.sin(2*np.pi*np.cumsum(f)/SR) * np.exp(-t*9)

def rumore(d, lo, hi, dec):
    t = np.arange(int(SR * d)) / SR
    return passabanda(rng.standard_normal(len(t)), lo, hi) * np.exp(-t * dec)

def pad(ms, d):
    t = np.arange(int(SR * d)) / SR
    s = sum(saw(hz(m) * (1 + dt), t) for m in ms for dt in (-0.004, 0.004))
    return filtra(s, fir_lp(1400)) * np.minimum(1, t/0.3) * np.minimum(1, (d - t)/0.3) * 0.05

def main():
    cfg = json.loads(open(sys.argv[1]).read())
    DUR = cfg["durata"]; N = int(SR * DUR)
    L = np.zeros(N); R = np.zeros(N); fx = np.zeros(N)

    def add(sig, t, pan=0.0, g=1.0):
        i = int(t * SR); n = min(len(sig), N - i)
        if n <= 0: return
        L[i:i+n] += sig[:n] * g * (1 - max(0, pan)); R[i:i+n] += sig[:n] * g * (1 + min(0, pan))

    def addfx(sig, t, g):
        i = int(max(0, t) * SR); n = min(len(sig), N - i)
        if n > 0: fx[i:i+n] += sig[:n] * g

    B = 60 / 100
    CH = [(48, [60, 64, 67]), (43, [59, 62, 67]), (45, [60, 64, 69]), (41, [60, 65, 69])]
    MEL = [76,79,81,79,76,74,72,74, 74,79,74,71,74,76,74,0, 72,76,81,79,76,72,76,79, 77,76,74,72,69,72,74,0]
    for bar in range(int(DUR / (4 * B)) + 1):
        t0 = bar * 4 * B; root, ch = CH[bar % 4]
        add(pad(ch, 4 * B), t0, g=1.3)
        for b in range(4):
            tb = t0 + b * B
            add(basso(root + (12 if b == 3 else 0), B * 0.9), tb, g=0.35)
            add(cassa(), tb, g=0.45)                      # la cassa parte subito: il reel non ha intro lenta
            if b in (1, 3): add(rumore(.25, 900, 5000, 18), tb, g=0.12, pan=0.1)
            add(rumore(.05, 7000, 15000, 80), tb + B/2, g=0.05, pan=-0.3)
        for k in range(8):
            m = MEL[(bar % 4) * 8 + k]
            if m: add(marimba(m + 12, 1.0), t0 + k * B/2, g=0.22, pan=0.2 * ((k % 2) * 2 - 1))

    def whoosh(d):
        n = rumore(d, 300, 6000, 0); t = np.arange(len(n)) / SR
        return n * np.sin(np.pi * t / d) ** 2
    def pop(f0=500):
        t = np.arange(int(SR * .12)) / SR; f = f0 * (1 + 3 * np.exp(-t * 60))
        return np.sin(2*np.pi*np.cumsum(f)/SR) * np.exp(-t*30)
    def chime(ms): return sum(marimba(m + 12, 1.2) for m in ms)
    def tick():
        t = np.arange(int(SR * .03)) / SR
        return passabanda(rng.standard_normal(len(t)), 2000, 8000) * np.exp(-t * 180)
    def riser(d):
        t = np.arange(int(SR * d)) / SR
        return rumore(d, 500, 9000, 0) * (t / d) ** 2

    # il picco di un effetto cade un fotogramma dopo l'immagine
    F = 1 / 30
    for t in cfg.get("whoosh", []): addfx(whoosh(0.5), t - 0.25 + F, 0.28)
    for i, t in enumerate(cfg.get("pop", [])): addfx(pop(420 + (i % 3) * 90), t + F, 0.35)
    for i, t in enumerate(cfg.get("chime", [])): addfx(chime([[84, 88, 91], [79, 84], [88]][i % 3]), t + F, 0.22)
    for t in cfg.get("tick", []): addfx(tick(), t + F, 0.12)
    if "riser" in cfg: addfx(riser(0.9), cfg["riser"] - 0.9, 0.25)

    mix = np.stack([L, R], 1) * 0.9 + fx[:, None]
    fo = np.ones(N); i = int(SR * (DUR - 0.8)); fo[i:] = np.linspace(1, 0, N - i); mix *= fo[:, None]
    mix /= np.max(np.abs(mix)) * 1.12   # picco sotto -1 dBTP
    with wave.open(sys.argv[2], "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix * 32767).astype("<i2").tobytes())
    print(f"musica scritta: {DUR} s")

if __name__ == "__main__":
    main()
