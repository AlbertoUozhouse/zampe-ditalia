# Decisioni sui reel

Registro delle scelte sui reel automatici: cosa si cambia, perché (numeri da motore/rendimento.json), e cosa si guarda dopo.
Lo aggiorna ogni mattina il controllo delle 10:30. Solo numeri e formati, nessun nome utente (il repository è pubblico).

## REGOLE IN VIGORE (2/11/2026, dopo l'analisi del concorrente) — valgono più di tutto quello che c'è sotto

Il concorrente (case sulla mappa, stesso meccanismo) ha 12.200 follower con 19 post. Anche lui cala: da 357.000 views del primo reel a 11.800 dell'ultimo.
La differenza vera è il lancio (357.000 contro i nostri 35.000) e i commenti: circa 230 ogni 1.000 views contro i nostri 15-60. Ha l'etichetta «Profilo generato dall'IA»: l'aspetto da IA non è il problema.
Cosa fa: chiede una parola sola (la città), ha una fascia fissa in basso «Commenta la tua città → ricevi una casa» per tutto il video, 1-2 reel al giorno,
storie a puntate con scadenza («stasera alle 21», «3 giorni al voto»), l'@ vero del giocatore grande al centro, scarsità («solo 3 case così»), testo enorme bianco e giallo.

1. **Massimo 3 reel al giorno:** 13:00 buio, 18:00 star (solo se c'è una foto vera nuova, altrimenti niente reel), 21:00 puntata; la «sfida» (Cani contro Gatti col punteggio) alle 21 a giorni alterni (2, 4, 6, 8/11).
2. **Ogni reel ha la fascia fissa in basso** «💬 Commenta città e nome del tuo animale 👇» per tutto il video. Niente «Seguici» nel video: si chiede il commento, il follow sta in didascalia e nelle risposte.
3. **Si chiede meno:** «città e nome» (+ cane o gatto). La razza è facoltativa. Se manca cane/gatto la risposta lo chiede: è un commento in più.
4. **Sempre con la voce**, 32 parole.
5. **Niente reel di giochi, negozio o festa** finché non arriviamo a 5.000 follower (nei reel; sul sito restano).
6. **Un cambiamento al giorno al massimo, solo con i numeri.** Un formato non si tocca prima di 3 uscite. Chi cambia scrive qui cosa e perché.
7. **Cosa si guarda:** commenti ogni 1.000 views (obiettivo sopra 100) e follower al giorno. Le views seguono i commenti.
8. **Prossimo passo, da preparare e far vedere ad Alberto prima di pubblicarlo:** il nostro «Giorno 1», un rilancio come evento.

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

## 31/10/2026 — spingere gli acquisti: il Presidente di regione

Secondo acquisto arrivato. Il Presidente di regione è chi ha più accessori nella sua regione: oggi 2 Presidenti, 18 regioni libere.
Cambiato: le risposte a chi accende una luce dicono (una volta su due) quanto manca per essere Presidente della sua regione; la scheda «Il mio» del sito lo dice sopra il negozio; il reel presidente si apre con «18 regioni senza Presidente. La tua è libera?» ed esce ogni giorno alle 15:00 al posto del buio.
Da guardare: acquisti al giorno.

## 31/10/2026 — più accessori, più Presidenti; festa automatica per ogni nuovo Presidente

Le risposte e il sito dicono chiaro che chi ha più accessori nella regione è Presidente. Ogni nuovo Presidente (commenti.py → stato «feste_presidente», solo regione e un'impronta dell'id) fa partire da solo il reel «neopresidente» appena c'è spazio tra le 10 e le 22 (orari.py, festa).
Da guardare: acquisti nei giorni dopo ogni reel di festa.

## 1/11/2026 — qualità: via la scena SEGUO dal video, via Thor dal derby

Views in calo: dai 2.300-3.700 del 28-30/10 ai 488-895 del 31/10. Nel reel delle 12 dell'1/11, 5 secondi su 15 erano la scena «+30 seguici e scrivi SEGUO» (due volte): pubblicità invece di contenuto, chi guarda scorre via.
Cambiato: la scena SEGUO non entra più nei video. La richiesta di seguire resta nella scritta fissa in alto («➕ Seguici +30»), nella didascalia e nelle risposte ai commenti. Il derby non mostra più Thor come arbitro.
Da guardare: visione media in percentuale della durata e views dei reel dal pomeriggio dell'1/11; follower per animale nuovo (non deve scendere).

## 01/11/2026 — Crescita: alle 13:30 il «buio» al posto del «duello»

Follower: 1.305 (01/11, 13:30). Nuovi ieri (31/10): +158 con +244 animali nuovi (1 follower ogni 1,5 animali). Giorni prima: +236 (29/10), +230 (30/10). Media 3 giorni: +208 al giorno → circa 3-4 giorni ai 2.000 (ne mancano 695).
Ieri pesano i 3 reel falliti da sabato 18:00 (aspetto «giorno» bloccato dal controllo di contrasto, corretto oggi alle 13): la sera del 31/10 ha portato solo +22 follower tra le 18 e l'1. Stamattina 08-13: +47 contro +89 di ieri alla stessa ora (niente reel serali a spingere).
Reel maturi (29-31/10, rendimento.json aggiornato fino al 31/10 13:34; manca IG_TOKEN per i più recenti):
puntata 29/10 21:05 3.597 views, 13 condivisioni, 76 commenti ogni 1.000, 12,1 s · presidente 30/10 11:18 3.321, 43/1.000, 11,0 s · puntata 30/10 21:04 2.697, 58/1.000 ·
gara 30/10 18:11 2.331, 11 condivisioni, 32/1.000 · gara 29/10 18:18 1.737, 45/1.000 · corsa_luna 30/10 22:43 1.382, 55/1.000 · presidente 30/10 15:34 1.285, 17/1.000 ·
neopresidente 31/10 11:27 895, 38/1.000, 7,6 s · nomi 31/10 13:34 488, 0 condivisioni, 25/1.000, 6,4 s · buio e attivita 29/10 (Trial Reel) 236 e 235.
Il «nomi» è il peggiore dei reel non di prova: si guarda poco (6,4 s) e non si condivide.

Cambiato (una cosa sola): alle 13:30 esce ogni giorno il «buio» invece del «duello». Il buio, uscito normale (non Trial) il 28/10 alle 12:43, ha fatto 3.606 views e 43 commenti ogni 1.000,
e si apre con una domanda a chi guarda («Trova la tua città: è accesa o ancora al buio?») che porta a commentare chi non ha ancora un animale sulla mappa: proprio i giocatori nuovi che portano i follower.
Il duello alle 13:30 non era mai uscito (il 31/10 e il 1/11 c'erano nomi e razze). Il cambiamento di ieri (6 reel, presidente alle 15) non si annulla: il calo di ieri si spiega coi reel serali falliti.
Da guardare domani: views del buio delle 13:30 (sopra 2.000?) e follower nuovi tra le 13 e le 16; rendimento di razze (13:30 di oggi) contro nomi (488); i reel di stasera escono davvero dopo la correzione del contrasto.

## 1/11/2026 — meno IA: via la voce artificiale

Alberto: i reel sembrano fatti da una macchina. Primo passo: niente voce sintetica (config.json "voce_ia": false), solo musica (volume 0.6) e scritte grandi a ritmo di lettura; sparisce «Voce generata con IA» dalla didascalia.
Prossimi passi proposti: animali veri (foto e video mandati in DM dai giocatori, con il loro consenso), video veri girati da Alberto, meno cartoni.
Da guardare: visione media e views dei reel senza voce rispetto a quelli con voce.

## 1/11/2026 — animali veri: «La star di oggi»

Scelta di Alberto per avere reel meno «IA». Chi manda in privato la foto del suo animale riceve «Possiamo metterlo nel reel col tuo @? Rispondi SÌ»; col SÌ la foto si salva in docs/media/ugc (ridotta, senza dati nascosti) e ogni giorno alle 18 esce il reel «star» con la foto vera e il suo @. Senza foto in coda esce la gara. Ogni didascalia invita a mandare la foto.
Da guardare: quante foto arrivano al giorno, views e condivisioni dei reel star (chi è nel reel lo condivide).

## 1/11/2026 sera — 10 prove diverse e la missione

Alberto: non togliere la voce a tutti, fare 10 prove diverse di impatto, e far sentire la gente una comunità.
Cambiato: ogni reel prende a rotazione una di 10 varianti (VARIANTI in main() di motore/copione.py): voce sì/no × apertura (solita / «Siamo già N animali d'Italia. Manca il tuo?» / «Stiamo costruendo il paese virtuale con più animali d'Italia») × durata 48 o 32 parole. La variante di ogni reel è in motore/reel_fatti.json, chiave "varianti" (id del reel → variante): confrontare views, condivisioni e follower per variante dopo 2-3 giri completi, poi tenere le migliori e togliere le peggiori.
Nuovo formato «missione»: il paese virtuale con più animali d'Italia, traguardo 10.000, poi Italia contro Mondo; tono da famiglia. Esce l'1/11 alle 21.

## 1/11/2026 — la star solo per chi ci segue, e solo foto belle

Alberto: non tutti mandano belle foto, e chi non ci segue non deve diventare la star.
Cambiato (motore/messaggi.py, lettore.giudica_foto): chi non ha scritto SEGUO riceve «la star è riservata a chi ci segue»; le foto di chi ci segue le guarda Claude (animale ben visibile, a fuoco, luce buona, niente persone in primo piano, screenshot o scritte) prima di chiedere il SÌ. Se Claude non risponde la foto si riprova al giro dopo.

## 3/11/2026 — controllo del mattino: nessun cambiamento

Follower 1.536 (+136 il 2/11). Prima sfida con la fascia fissa in basso e la richiesta «città e nome» (2/11 21:10): 654 views, 78 commenti ogni 1.000 (il presidente delle 11:44 senza fascia: 2.255 views, 36 ogni 1.000), 2 condivisioni, 8,9 s di visione media.
I commenti per views raddoppiano, le views non ancora. Un reel solo non basta: le regole nuove restano uguali per 3 uscite. Il buio del 2/11 è stato tolto da Instagram (era senza voce).
Da guardare domani: commenti ogni 1.000 views di buio e puntata di oggi (obiettivo sopra 100) e follower del 3/11.

## 3/11/2026 sera — un reel che chiede di seguire: «fuochi»

Alberto: serve un reel che spinga i follow. Oggi follower +40 (1.567) e solo 91 commenti nuovi (ieri 711): con 2 reel al giorno e poche views arrivano pochi giocatori nuovi.
Nuovo formato `fuochi` (eccezione alla regola 2, perché qui seguire è il contenuto): il numero che manca ai 2.000 follower, la festa sopra tutti gli animali della mappa, SEGUO = punti al tuo animale, tagga un amico. Fascia in basso «➕ Seguici e scrivi SEGUO».
Esce il 4/11 alle 13:00 al posto del buio (fascia oraria in cui la gente segue di più: 11-16).
Da guardare: follower nuovi tra le 13 e le 17 del 4/11 contro le stesse ore del 3/11, e i SEGUO nei commenti.
