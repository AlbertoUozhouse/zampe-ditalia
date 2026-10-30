# Zampe d'Italia

Ogni animale accende una luce sull'Italia. Cani contro Gatti: quale città d'Italia vince?

- `docs/` è il sito con la mappa, pubblicato su GitHub Pages: https://zampeditalia.it
- `docs/data/animali.json` lo aggiorna in automatico il motore dei commenti.
- `dati/` contiene i comuni italiani con le coordinate e i confini delle regioni.

Si gioca nei commenti dei reel di [@zampeditalia](https://www.instagram.com/zampeditalia/).

## Zampe di corsa (minigioco)

`docs/gioco.html` (+ `gioco.js`, `gioco.css`): corsa notturna col proprio animale (preso dalla scheda «Il mio» della mappa, o scelto a mano), sfide tra amici con un link `gioco.html?sfida=Nome&p=punti&t=cane`.

Pubblicità: Google AdSense, annunci per giochi H5 («guarda un video e continua» + annuncio tra una partita e l'altra).
Per accenderla, quando l'account AdSense è approvato: in `docs/gioco.js` metti `PUB.client = "ca-pub-…"` e crea `docs/ads.txt` con la riga
`google.com, pub-…, DIRECT, f08c47fec0942fa0`. Finché `client` è vuoto il gioco va senza pubblicità e «Continua» è gratis una volta a partita.
