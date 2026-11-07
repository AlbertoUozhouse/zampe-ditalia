"""L'Italia di notte con coste e rilievi veri: scarica le altitudini (AWS Terrain Tiles, formato terrarium, dati pubblici:
SRTM, GMTED, ETOPO1) e disegna le piastrelle della mappa del sito e l'immagine grande usata nei reel.

Uso: python3 strumenti/rilievo.py   (serve la rete; si lancia una volta sola, le piastrelle restano nel repository)
Scrive docs/tiles/{z}/{x}/{y}.jpg (z 5-9) e reel/assets/italia-notte.jpg + italia-notte.json (i confini, per mettere le luci al posto giusto).
"""
import io, json, math, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
Z = 9  # ~220 m per pixel: coste e valli leggibili; sopra lo zoom 9 il sito ingrandisce queste
LON0, LON1, LAT0, LAT1 = 2.0, 22.5, 33.5, 50.5  # più largo dell'Italia: sul telefono, allo zoom più lontano, la mappa riempie lo schermo
URL = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"

def tile_xy(lon, lat, z):
    n = 2 ** z
    x = (lon + 180) / 360 * n
    y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
    return x, y

def scarica(xy):
    x, y = xy
    with urllib.request.urlopen(URL.format(z=Z, x=x, y=y), timeout=60) as r:
        a = np.asarray(Image.open(io.BytesIO(r.read())).convert("RGB"), dtype=np.float32)
    return xy, a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768  # metri

def colora(h, metri_px, italia):
    """Notte: mare blu scuro (più scuro al largo), terra quasi nera coi rilievi in luce fredda da nord-ovest,
    l'Italia un filo più chiara dei paesi vicini, costa appena accesa."""
    from PIL import ImageFilter
    dy, dx = np.gradient(h, metri_px)
    pend = np.arctan(np.hypot(dx, dy) * 2.0)
    asp = np.arctan2(-dy, dx)
    az, alt = math.radians(315), math.radians(40)
    luce = np.clip(math.sin(alt) * np.cos(pend) + math.cos(alt) * np.sin(pend) * np.cos(az - asp), 0, 1)
    mare = h <= 0.5
    # profondità sfumata: i dati del fondale sono a quadretti grossi
    prof = np.clip(-h / 2500, 0, 1)
    prof = np.asarray(Image.fromarray((prof * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(18)), np.float32) / 255
    out = np.zeros(h.shape + (3,), np.float32)
    for i, (a, b) in enumerate(zip((12, 30, 72), (4, 12, 36))):  # #0C1E48 sotto costa → #040C24 al largo
        out[..., i] = a + (b - a) * prof
    quota = np.clip(h / 2200, 0, 1)
    t = (0.12 + 0.88 * luce ** 1.6) * (0.5 + 0.5 * quota)
    for i, (base, chiaro) in enumerate(zip((13, 15, 22), (88, 94, 112))):  # terra #0D0F16 → #585E70 sui versanti in luce
        terra = base + (chiaro - base) * t
        terra = np.where(italia, terra, terra * 0.62)  # fuori dall'Italia più spento
        out[..., i] = np.where(mare, out[..., i], terra)
    costa = mare & (~np.roll(mare, 1, 0) | ~np.roll(mare, -1, 0) | ~np.roll(mare, 1, 1) | ~np.roll(mare, -1, 1))
    for i, c in enumerate((58, 92, 158)):
        out[..., i] = np.where(costa, c, out[..., i])
    return np.clip(out, 0, 255).astype(np.uint8)

def maschera_italia(xs, ys, W, H):
    """Le regioni italiane (docs/data/regioni.json) disegnate sui pixel della mappa."""
    from PIL import ImageDraw
    m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
    for f in json.loads((ROOT / "docs/data/regioni.json").read_text())["features"]:
        g = f["geometry"]; polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poly in polys:
            pts = []
            for lon, lat in poly[0]:
                x, y = tile_xy(lon, lat, Z); pts.append(((x - xs[0]) * 256, (y - ys[0]) * 256))
            d.polygon(pts, fill=255)
    from PIL import ImageFilter
    return np.asarray(m.filter(ImageFilter.MaxFilter(9)), np.float32) > 0  # un po' più larga: le regioni sono semplificate

def main():
    x0, y0 = tile_xy(LON0, LAT1, Z); x1, y1 = tile_xy(LON1, LAT0, Z)
    xs, ys = range(int(x0), int(x1) + 1), range(int(y0), int(y1) + 1)
    W, H = len(xs) * 256, len(ys) * 256
    h = np.zeros((H, W), np.float32)
    with ThreadPoolExecutor(16) as ex:
        for (x, y), a in ex.map(scarica, [(x, y) for x in xs for y in ys]):
            h[(y - ys[0]) * 256:(y - ys[0] + 1) * 256, (x - xs[0]) * 256:(x - xs[0] + 1) * 256] = a
    lat_c = math.radians((LAT0 + LAT1) / 2)
    metri_px = 40075016.686 * math.cos(lat_c) / (256 * 2 ** Z)
    img = Image.fromarray(colora(h, metri_px, maschera_italia(xs, ys, W, H)))
    out = ROOT / "docs/tiles"
    for z in range(5, Z + 1):  # piramide: lo zoom z è l'immagine ridotta di 2^(Z-z)
        f = 2 ** (Z - z)
        im = img if f == 1 else img.resize((W // f, H // f), Image.LANCZOS)
        for tx in range(xs[0] // f, (xs[-1]) // f + 1):
            for ty in range(ys[0] // f, (ys[-1]) // f + 1):
                px, py = tx * 256 - xs[0] * 256 // f, ty * 256 - ys[0] * 256 // f
                t = Image.new("RGB", (256, 256), (6, 14, 38))
                t.paste(im.crop((max(0, px), max(0, py), min(im.width, px + 256), min(im.height, py + 256))), (max(0, -px), max(0, -py)))
                p = out / str(z) / str(tx); p.mkdir(parents=True, exist_ok=True)
                t.save(p / f"{ty}.jpg", quality=82, optimize=True)
    # l'immagine dei reel: zoom 8 (metà), ritagliata sull'Italia
    reel = img.resize((W // 2, H // 2), Image.LANCZOS)
    (ROOT / "reel/assets").mkdir(parents=True, exist_ok=True)
    reel.save(ROOT / "reel/assets/italia-notte.jpg", quality=86, optimize=True)
    (ROOT / "reel/assets/italia-notte.json").write_text(json.dumps({"z": Z - 1, "x0": xs[0] * 128, "y0": ys[0] * 128, "w": W // 2, "h": H // 2,
        "fonte": "AWS Terrain Tiles (SRTM, GMTED, ETOPO1)"}) + "\n")
    print(f"tiles z5-{Z}: {len(xs)}x{len(ys)} alla scala massima; immagine reel {W // 2}x{H // 2}")

if __name__ == "__main__":
    main()
