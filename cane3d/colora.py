"""Colora un modello 3D proiettando le foto (profilo + fronte) e lo alleggerisce. uso: colora.py forma.glb lato.png fronte.png uscita.glb [facce]"""
import sys, numpy as np, trimesh, fast_simplification
from PIL import Image
forma, lato, fronte, out = sys.argv[1:5]; facce = int(sys.argv[5]) if len(sys.argv) > 5 else 30000
m = trimesh.load(forma, force="mesh")
m.update_faces(m.unique_faces()); m.remove_unreferenced_vertices()
if facce and len(m.faces) > facce: m = m.simplify_quadric_decimation(face_count=facce)
def box(img):  # il riquadro del cane nella foto (tutto ciò che non è sfondo bianco)
    a = np.asarray(img).astype(int); mask = (a.min(2) < 235)
    ys, xs = np.where(mask); return xs.min(), xs.max(), ys.min(), ys.max()
L, F = Image.open(lato).convert("RGB"), Image.open(fronte).convert("RGB")
la, fa = np.asarray(L), np.asarray(F)
lb, fb = box(L), box(F)
V, N = m.vertices, m.vertex_normals
lo, hi = V.min(0), V.max(0)
# la testa è dalla parte più alta del modello lungo x
alto = V[:, 1] > lo[1] + 0.8 * (hi[1] - lo[1])
testa_pos = V[alto, 0].mean() > (lo[0] + hi[0]) / 2
tx = (V[:, 0] - lo[0]) / (hi[0] - lo[0]); tx = 1 - tx if testa_pos else tx  # 0 = testa (a sinistra nella foto di profilo)
ty = (hi[1] - V[:, 1]) / (hi[1] - lo[1])
def pesca(a, b, u, w):
    x = np.clip((b[0] + u * (b[1] - b[0])).astype(int), 0, a.shape[1] - 1); y = np.clip((b[2] + w * (b[3] - b[2])).astype(int), 0, a.shape[0] - 1)
    return a[y, x].astype(float)
col_lato = pesca(la, lb, tx, ty)
tz = (V[:, 2] - lo[2]) / (hi[2] - lo[2])
col_fronte = pesca(fa, fb, tz, ty)
avanti = N[:, 0] * (1 if testa_pos else -1)  # quanto la normale guarda verso il muso
peso = np.clip((avanti - 0.35) / 0.4, 0, 1) * (tx < 0.35)
col = col_lato * (1 - peso[:, None]) + col_fronte * peso[:, None]
bianco = col.min(1) > 238  # lo sfondo preso per sbaglio sul bordo: lo sostituisco col colore medio del pelo
col[bianco] = np.median(col[~bianco], 0)
m.visual = trimesh.visual.ColorVisuals(m, vertex_colors=np.c_[col.clip(0, 255), np.full(len(col), 255)].astype(np.uint8))
m.export(out); print(out, len(m.faces), "facce", "testa a +x" if testa_pos else "testa a -x")
