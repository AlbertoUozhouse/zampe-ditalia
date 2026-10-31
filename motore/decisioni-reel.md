# Decisioni sui reel

Registro delle scelte sui reel automatici: cosa si cambia, perché (numeri da motore/rendimento.json), e cosa si guarda dopo.
Lo aggiorna ogni mattina il controllo delle 10:30. Solo numeri e formati, nessun nome utente (il repository è pubblico).

## 30/10/2026 — riparto dopo l'analisi dei primi 22 reel

Numeri: il lancio del 26/10 ore 21 ha fatto 26.910 views e 4.408 commenti (164 ogni 1.000 views, 116 condivisioni).
Tutti gli altri tra 235 e 3.573 views, commenti scesi a 15-90 ogni 1.000, condivisioni 0-13, visione media 6-13 s su reel di 23-28 s.
Fasce migliori: 21:00 (puntata 3.573 e 3.077) e 18:00 (fondatore 3.143). Trial Reel 12:30/15:30: 236 e 235 views.

Cambiato:
- da 5 reel al giorno (2 Trial Reel) a 3: 13:00 fondatore, 18:00 gara, 21:00 puntata;
- voce al massimo 40 parole (circa 15 s) invece di 70;
- prima frase = gancio rivolto a chi guarda (domanda o sfida), non una statistica;
- didascalia con una richiesta sola (+ il link al gioco) al posto di 8;
- bonus (SEGUO, inviti) in un reel su tre invece che in tutti.

Da guardare nei prossimi 3 giorni: views medie sopra 3.000, visione media sopra il 50% della durata, commenti ogni 1.000 views in salita.

## 30/10/2026 sera — formato «sfida», rifatto sul reel da 26.910 views

Il lancio del 26/10 funzionava per cinque motivi: una rivalità che capiscono tutti nel primo secondo («Cani contro Gatti, quale città vince?»),
cosa scrivere mostrato come un commento, il premio subito (la cuccia col tuo nome), il posto da Fondatore ancora libero, e la stessa domanda in chiusura.
In più ogni commento riceveva una risposta, che raddoppiava i commenti visibili.

Cambiato: nuovo formato `sfida` con la stessa struttura e i numeri di oggi (la squadra che perde, i comuni ancora spenti), senza bonus in mezzo.
Esce sabato 31/10 alle 21:00 al posto della puntata (`una_tantum` in config.json).
Stasera alle 22:30 esce anche il primo reel con una partita vera di Zampe di corsa (`pronto-corsa_luna`).
Da guardare: views e commenti ogni 1.000 views della sfida contro la puntata delle 21 del 29/10 (3.077 views, 73 commenti ogni 1.000).

## 30/10/2026 notte — idee nostre, non copiate: i dati degli animali veri

Le case di un gioco simile non hanno nome né razza; i nostri animali sì. Due formati nuovi che raccontano solo dati nostri:
- `nomi`: i nomi più diffusi (cani: Leo 30, Luna 27, Kira 22; gatti: Luna, Stella, Simba). Chi guarda controlla il nome del suo e lo scrive.
- `razze`: la razza preferita di ogni regione (meticci a parte) e il meticcio re d'Italia (58 cani su 100). Divide quanto basta per far commentare.
Escono sabato 31/10 alle 13 (`nomi`) e domenica 1/11 alle 13 (`razze`), al posto del fondatore. Rotazione dei 3 reel di sabato: nomi, gara (si apre con la gara vera), sfida: tre aspetti diversi.
Da guardare: commenti ogni 1.000 views (questi formati chiedono una risposta personale) e condivisioni.

## 31/10/2026 notte — rimesso il SEGUO in ogni reel e in ogni didascalia

Follower: 814 (29/10 sera) → 1.072 (30/10, 18:30): +258 in un giorno. Poi 1.072 → 1.093 in 7 ore (30/10 sera - 31/10 notte).
Il calo è arrivato subito dopo la modifica delle 18:30 del 30/10 che toglieva dalle didascalie «Seguici e scrivi SEGUO: +30 punti» e lasciava la scena SEGUO in un reel su tre.
Cambiato: la riga SEGUO torna in ogni didascalia; la scena SEGUO torna in ogni reel (non in sfida, nomi e razze, che hanno la scena del commento); voce fino a 48 parole.
Regola per il bot: la richiesta di seguire non si toglie più. La «richiesta sola» vale per cosa scrivere nel commento, non per il follow.
Da guardare: follower nuovi del 31/10 rispetto ai +258 del 30/10.

## 31/10/2026 notte — 6 reel al giorno, e cosa dicono i dati sui follower

Curva dei follower ricostruita dalla cronologia di docs/data/animali.json (30/10, ore UTC):
10-12 +32 follower / +43 animali nuovi · 12-15 +52 / +93 · 15-17:40 +26 / +37 · 17:40-20 +25 / +53 · 20-22 +12 / +48 · 22-01 +10 / +13.
1) I follower arrivano insieme ai giocatori nuovi: circa un follower ogni 1,5-2 animali nuovi. Il motore della crescita è far commentare persone nuove.
2) Le ore migliori sono 11-16 italiane. Di sera si accendono ancora animali, ma la parte che poi ci segue scende: tra le 21 e le 23 un follower ogni 4 animali, quando le didascalie non avevano più il SEGUO. Indizio, non prova.
Cambiato: 6 reel al giorno (12:00 fondatore, 13:30 duello, 15:00 buio, 16:30 derby, 18:00 gara, 21:00 puntata), più reel nelle ore in cui la gente segue; il buio si apre con «Trova la tua città: è accesa o ancora al buio?».
Da guardare: follower nuovi al giorno e follower per animale nuovo.
