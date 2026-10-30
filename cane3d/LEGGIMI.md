# Cani 3D realistici (prova)

Prova gratuita del 30/10/2026: da due foto di ChatGPT (lato.webp, fronte.webp) a un cane 3D vero.

1. Forma: space Hugging Face Hunyuan3D-2 con gradio_client, endpoint `/shape_generation` (anonimo funziona; la texture no).
2. Colori: `python colora.py forma.glb lato.png fronte.png artur.glb 40000` proietta le foto sui vertici (trimesh, numpy<2).

artur.glb = Artur (pastore maremmano, Presidente del Veneto), 40k facce, ~1 MB.
Da fare: naso e occhi più scuri, camminata (shader zampe + coda), inserirlo in docs/mondo3d.js per razza.
