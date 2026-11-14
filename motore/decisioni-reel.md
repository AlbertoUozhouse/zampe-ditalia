# Decisioni sui reel

Registro delle scelte sui reel automatici: cosa si cambia, perché (numeri da motore/rendimento.json), e cosa si guarda dopo.
Lo aggiorna ogni mattina il controllo delle 10:30. Solo numeri e formati, nessun nome utente (il repository è pubblico).

## STUDIO DEL 13/11/2026 — perché i reel non escono, e i reel d'impatto (67 reel organici, numeri di Instagram)

**Cosa dicono i numeri**
- Mediana delle views per settimana: 1.819 (27/10–2/11) → 763 (3–7/11) → 479 (8–13/11). I 12 reel più visti sono tutti del 27/10–2/11.
- Quella settimana arrivavano 200–700 animali nuovi al giorno e +150 follower al giorno: era l'onda del reel sponsorizzato del 26/10 (45.836 views). Dal 3/11 (sponsorizzata finita): 12–34 animali nuovi e +20 follower al giorno.
- Le views vanno insieme ai commenti (correlazione 0,83) e ai secondi guardati (0,62). I reel da 3.000+ views avevano 150–350 commenti; quelli di adesso 15–25. La reach di adesso (250–800) è meno della metà dei follower: Instagram non li mostra a chi non ci segue.
- Conclusione: i nostri reel parlano a chi conosce già il gioco. Un estraneo non capisce, non resta, non commenta, non lo manda a nessuno. Cambiare grafica non basta: serve un motivo per fermarsi, restare fino in fondo, commentare e inoltrare, valido per chiunque abbia un cane o un gatto.

**Le regole dei reel d'impatto**
1. Si capisce da zero: il primo fotogramma dice cosa fare o cosa si scopre, senza conoscere la pagina.
2. C'è un motivo per arrivare in fondo (un conto alla rovescia, una rivelazione) o per riguardare (un rompicapo).
3. Il commento è una risposta, non un'iscrizione: «in quanti secondi?», «come si chiama il tuo?». La città e il nome si chiedono dopo, nella risposta del bot.
4. Il bot risponde con un dato vero e personale (quanti si chiamano come il tuo animale, o che il nome è unico): è il motivo per scrivere e per far vedere la risposta.
5. Corti: 10–12 secondi.

**Costruiti il 13/11**
- «Trova l'intruso» (formato `intruso`): 36 cani identici, uno ha un solo dettaglio diverso (fa l'occhiolino, è triste, ha la lingua fuori, è senza collare); la voce conta un numero al secondo, poi l'intruso va al centro nell'anello d'oro. Prima versione (un gatto tra 25 cani) bocciata da Alberto la sera stessa: «si vede subito». Regola: il rompicapo deve essere difficile, chi non lo trova riguarda.
- «I nomi più usati» (formato `nomi_top`): conto alla rovescia dal quinto al primo, a rotazione tutti / cani / gatti; chiusura «scrivi il nome del tuo: ti rispondiamo con quanti ce ne sono».
- Il bot (commenti.py): a chi scrive solo il nome risponde col numero vero («Sulla mappa ci sono già 62 Luna, in 52 città», oppure «sarebbe il primo in tutta Italia») e chiede la città; a ogni animale nuovo dice se il nome è unico o in quanti sono.
- Alle 18 rotazione di cinque video: quiz della razza, intruso, nomi, figurine, luce nuova.
- Come si misura: views e reach contro la mediana di 479, commenti per reel (oggi 15–25), follower ogni 1.000 raggiunti. Si tiene quello che supera il doppio della mediana in due uscite.

## TEST DI CRESCITA (Alberto, 8/11/2026) — quali reel portano più follower

- Config: `test_crescita` in motore/config.json. «anteprima» = nessuna uscita (si guardano le anteprime); «attivo» dal giorno «dal» per 7 giorni; «spento» = tutto come prima.
- Due format di scoperta: **Il paese al buio** («Cesano Maderno è ancora al buio.») e **Il campanile rivale** («Crotone contro Ercolano. Chi passa?»), almeno 2 episodi ciascuno, alternando le 13 e le 18. L'altro slot è un aggiornamento del gioco. Alle 21 solo una storia con un motivo (il paese al buio che si accende, una staffetta chiusa), altrimenti si salta e si registra il motivo.
- Primo fotogramma = il gancio scritto grande (si capisce a volume zero), senza video prima. La mappa entra solo per mostrare un cambiamento (il buco al buio tra le luci, il punteggio). Niente volo da tutta l'Italia.
- Voce sintetica dichiarata contro solo testo con musica ed effetti, su episodi dello stesso format (variante scritta nel copione, campo «test»).
- Mappa e dati verifica il caso prima del montaggio e prima del caricamento: un errore dimostrato ferma il reel (copione.py verifica).
- Staffetta di quartiere: tre persone diverse dello stesso comune in sfida, ognuna col suo animale, commentano città e nome: 1/3, 2/3, 3/3 e un punto della Coppa. Un commento riletto o un giro ripetuto non conta due volte.
- Verbale: docs/data/agenzia/test_crescita.json (verbale.py): per episodio follower, account raggiunti, follower ogni 1.000, metrica secondaria, fonte, dati mancanti; base = mediana dei reel organici delle 13 e 18 nei 14 giorni prima. Il sponsorizzato resta fuori. Si tiene un format solo se migliora la base su più episodi.
- Durante il test: niente cantieri nuovi dell'Innovazione.

## CENTRO AGENZIA (Alberto, 7/11/2026)

Ogni reel passa dal Direttore video (agente OpenAI, motore/agenzia.py): prima del montaggio sceglie apertura, inquadratura e momento della luce; dopo l'esportazione riceve fotogrammi coi secondi, trascrizione, dati verificati della mappa e misure audio, e restituisce secondo, problema e correzione. Claude traduce le correzioni in azioni del montaggio e rimonta. Al massimo 2 revisioni: approvato = si pubblica una volta sola; difetti dopo 2 giri = bozza (docs/media/bozze) e reel di riserva. Ogni scambio è nella stanza (zampeditalia.it/agenzia/, non collegata e non indicizzata). Senza Direttore raggiungibile i reel escono come prima e la stanza lo registra.
7/11 sera: primo giro sul reel delle 18 (prima_luce di Atri): la chiave OpenAI nei Secrets risponde 401 (non valida). Serve una chiave valida da Alberto.

## COPPA DELLE ZAMPE (Alberto, 7/11/2026)

Campionato settimanale tra comuni (motore/coppa.py, docs/coppa.js). Si gioca sul sito («🏆 Gioca per la tua città» sulla mappa); la prova del giorno dà il codice «COPPA XY» da commentare sotto un reel: un punto al giorno per persona alla città del suo animale (resta quella per tutto il turno). Coppie di comuni con un numero simile di giocatori attivi. Chiude la domenica alle 20, trofeo a chi vince la sua sfida (mappa e albo), riparte il lunedì a mezzanotte. Staffetta: 3 giocatori dello stesso comune = anello dorato e cartolina «Io gioco per…».
Prove: La Luce Misteriosa (indizi dai dati della mappa) e Indovina la Zampa (sagoma o dettaglio dei disegni della mappa; suoni veri non ne abbiamo), un giorno l'una e un giorno l'altra.
Reel: coppa_apertura (lun 13:00), coppa_sorpasso (gio 21:00), coppa_verdetto (dom 21:00), in config.json «settimanali». Primo turno: dal 7/11 al 15/11 (apertura domenica 8/11 alle 21).
Misure di ogni turno in motore/stato.json «coppa_misure»: giocatori, tornano (avevano giocato il turno prima), piu_giorni, nuovi_da_instagram (arrivati sulla mappa con un commento durante il turno). Le visite al sito non si possono contare senza uno strumento di statistiche (servirebbe un account di Alberto).
Dopo ogni turno: leggere coppa_misure e le risposte ai reel, e inventare la prova nuova da aggiungere (sempre da dati veri della mappa o materiali che abbiamo).

## SERIE DELLA MAPPA (Alberto, 7/11/2026) — vale più delle regole sotto

Obiettivo: chi vede la pagina per la prima volta capisce subito il gioco (ogni animale accende una luce nella sua città).
- Ogni reel apre con un animale vero in movimento (video mandato in DM da chi ci segue, col suo SÌ: docs/media/ugc/*.mp4, 4,5 s col suono vero), poi entro il quinto secondo la mappa del sito (scena `luce`, stessa immagine dell'Italia di notte del sito) col punto che si accende. Senza video dei follower si apre col volo 3D di notte sul paese della storia, fino alla cuccia dell'animale col suo nome (reel/volo3d.js, dal 10/11: Alberto, «basta Thor»). Thor non apre più i reel. Thor resta fuori da classifiche, premi e solleciti. Nessuna ricostruzione IA per ora (non abbiamo uno strumento per farle).
- Se si racconta un animale preciso si mostra la sua luce vera sulla mappa.
- Copertina: la mappa vera attorno al comune con la luce accesa e poche parole («La prima luce / di Atri»).
- Episodi: `prima_luce` (13:00), `questa_luce` (18:00, annuncia «le prossime luci domani alle 18»), `testa_a_testa` (13:00 l'8, 10, 12 e 14/11: due comuni vicini sulla mappa e nel punteggio). 21:00 puntata.
- Misura: follower arrivati dopo ogni reel (fino al reel dopo, massimo 6 ore) ogni 1.000 account raggiunti: rendimento.json «follower_ogni_1000» (dal 7/11). Il reel sponsorizzato del 26/10 (config.json «sponsorizzati») si tiene a parte. Confronto dopo 7 giorni: 14/11.
- Controllo quotidiano: sito online (mappa e piastrelle), nuove luci nelle ultime 24 ore, reel previsti contro pubblicati.

## REGOLE IN VIGORE (2/11/2026, dopo l'analisi del concorrente) — valgono più di tutto quello che c'è sotto

Il concorrente (case sulla mappa, stesso meccanismo) ha 12.200 follower con 19 post. Anche lui cala: da 357.000 views del primo reel a 11.800 dell'ultimo.
La differenza vera è il lancio (357.000 contro i nostri 35.000) e i commenti: circa 230 ogni 1.000 views contro i nostri 15-60. Ha l'etichetta «Profilo generato dall'IA»: l'aspetto da IA non è il problema.
Cosa fa: chiede una parola sola (la città), ha una fascia fissa in basso «Commenta la tua città → ricevi una casa» per tutto il video, 1-2 reel al giorno,
storie a puntate con scadenza («stasera alle 21», «3 giorni al voto»), l'@ vero del giocatore grande al centro, scarsità («solo 3 case così»), testo enorme bianco e giallo.

1. **3 reel al giorno:** 13:00 buio, 18:00 star (senza foto nuova esce il fondatore), 21:00 puntata; la «sfida» (Cani contro Gatti col punteggio) alle 21 a giorni alterni (2, 4, 6, 8/11).
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

## 4/11/2026 — controllo del mattino: torna il terzo reel

Il conteggio di Instagram era fermo dal 3/11 mattina: la copia intera del repository (quasi 1 GB) superava i 10 minuti. Ora rendimento.yml copia solo motore/.
Follower 1.576 (+43 il 3/11, +136 il 2/11). Commenti nuovi: 711 il 2/11, 98 il 3/11. Reel del 3/11: buio 614 views (62 commenti ogni 1.000), puntata 345 (38). Sfida del 2/11: 801 (76).
Con 2 reel al giorno (la star saltava senza foto) i giocatori nuovi sono crollati. Cambiato (uno solo): senza foto nuove alle 18 esce il fondatore, così i reel tornano 3.
Oggi: 13:00 fuochi (follow), 18:00 fondatore, 21:00 sfida. Da guardare: follower tra le 13 e le 17 e commenti nuovi del 4/11.

## 4/11/2026 pomeriggio — evento «Il Re degli animali d'Italia» (Alberto: «hai carta bianca, voglio follower»)

4/11 alle 15:30: +2 follower e 2 animali nuovi in tutto il giorno. Instagram fa vedere i reel a 200-450 persone: la stessa mappa con numeri diversi non è più una novità.
Le pagine simili crescono con eventi a scadenza («Stasera alle 21 il primo Presidente d'Italia», 24.000-93.000 views) e con persone vere al centro.
Nuovo evento: venerdì 6/11 alle 21 si incorona il primo Re degli animali d'Italia (più punti) e il Re di ogni regione. Si vince coi punti del gioco:
SEGUO = +30 (fino all'8/11), ogni amico taggato che commenta = +3. Seguire ha un motivo dentro il gioco, e chi è in classifica tagga e condivide.
Calendario: `re` (conto alla rovescia con la classifica vera) 4/11 18:00, 5/11 13:00 e 21:00, 6/11 13:00; `incoronazione` 6/11 21:00 (al posto della sfida).
Da guardare: SEGUO e tag nei commenti, follower al giorno dal 4 al 7/11.

## 4/11/2026 pomeriggio — «Stasera alle 21 il tuo animale nel reel» (Alberto: follower senza sponsorizzare)

Un reel per i follow col premio la sera stessa: `ospiti` (oggi 19:30: alle 18 era già uscito il fondatore) dice che alle 21 mettiamo nel reel gli animali di chi ci segue da oggi (SEGUO con città e nome);
`ospiti_sera` (21:00) mantiene la promessa: gli animali di chi ha scritto SEGUO dopo il reel delle 18, coi loro @ (si fotografa l'elenco SEGUO alle 18 in reel_fatti «seguono_prima»).
Ripetuto il 5/11 e il 7/11 alle 21 (ognuno mostra chi è arrivato dal reel precedente). Il Re resta: 5/11 13:00, 6/11 13:00, incoronazione 6/11 21:00.
Da guardare: SEGUO tra le 18 e le 21 del 4/11 e follower del 4-5/11.

## 5/11/2026 — controllo del mattino: nessun cambiamento

Follower 1.655: +67 il 4/11 (+2 fino alle 15:30, poi +65 la sera, coi reel fondatore 18:06, ospiti 19:37 e ospiti_sera 21:07), +18 stamattina.
Fuochi (4/11 13:09): 383 views, 8 commenti ogni 1.000, 5,6 s: debole, non si ripete. SEGUO nuovi: 746 → 759 il 4/11.
La sera rende più della mattina. Oggi resta il calendario: 13:00 re, 18:00 star/fondatore, 21:00 ospiti_sera. Da guardare: follower del 5/11, SEGUO tra le 13 e le 21.

## 6/11/2026 — controllo del mattino: nessun cambiamento, stasera l'incoronazione

Follower 1.684: +40 il 5/11, +7 stamattina. Numeri maturati: fuochi (4/11) salito a 1.486 views, il migliore dal 2/11; re (5/11 13:12) 461 views ma 106 commenti ogni 1.000, il valore più alto dal lancio (obiettivo regola 7 raggiunto).
ospiti_sera (4/11) 80 commenti ogni 1.000. I reel con una ragione per commentare o seguire (Re, nuovi amici) fanno commentare di più; le views restano basse (260-400 persone raggiunte).
Oggi resta il calendario: 13:00 re («stasera alle 21»), 18:00 star/fondatore, 21:00 incoronazione. Da guardare: views e condivisioni dell'incoronazione (chi vince condivide) e follower del 6-7/11.

## 6/11/2026 — «Porta 2 amici» (idea di Alberto)

Regola nuova del gioco (commenti.py, premia_amico_segue): l'amico che hai taggato ci segue e scrive SEGUO → +15 a chi l'ha invitato, una volta per coppia (sulla fiducia, come il SEGUO). Con il +3 del commento: 2 amici = +36.
Reel `amici` oggi alle 18:00 (al posto di star/fondatore) e domani 7/11 alle 13:00. Da guardare: tag nei commenti e SEGUO di amici invitati (coppie «>>» in stato «premiati»).

## 7/11/2026 — controllo del mattino: due reel falliti il 6/11, l'incoronazione pubblicata oggi

Follower 1.714: +25 il 6/11, +12 stamattina. Il 6/11 alle 18 il reel «amici» si è fermato al controllo HyperFrames (riga «Nome · @utente» tagliata nella classifica: corretto in reel/modello/scene.py, i nomi lunghi si rimpiccioliscono; provato qui, controllo ok).
Alle 21 l'incoronazione era montata ma GitHub Pages non l'ha messa online in 10 minuti: è uscita una riserva (fondatore). Il controllo del mattino ha già portato l'attesa a 20 minuti. L'incoronazione è stata pubblicata a mano oggi alle 11:17.
Il Re del 5/11: 652 views e 121 commenti ogni 1.000 (record). Oggi: 13:00 amici, 18:00 star/fondatore, 21:00 ospiti_sera. Nessun altro cambiamento.


## 2026-11-08 — verbale dei 7 giorni (automatico, motore/verbale.py)

- 2026-10-28-1136-voto: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).
- 2026-10-28-1227-voto: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).
- 2026-10-28-1236-altri: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).
- 2026-10-28-1243-buio: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).
- 2026-10-28-1535-attivita: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).
- 2026-10-28-1807-fondatore: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).
- 2026-10-28-1932-derby: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).
- 2026-10-28-2112-puntata: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).
- 2026-10-29-1239-buio: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).
- 2026-10-29-1542-attivita: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).
- 2026-10-29-1818-gara: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).
- 2026-10-29-2105-puntata: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).
- 2026-10-30-1118-presidente: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).
- 2026-10-30-1534-presidente: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).
- 2026-10-30-1811-gara: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).
- 2026-10-30-2104-puntata: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).
- 2026-10-30-2243-corsa_luna: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).
- 2026-10-31-1127-neopresidente: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).
- 2026-10-31-1334-nomi: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).
- 2026-10-31-1505-presidente: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).
- 2026-10-31-1636-derby: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).

## 8/11/2026 — controllo del mattino

Sito: GitHub Pages pubblica in meno di un minuto (docs 92 MB). Follower 1.736 (+21 il 7/11, +13 stamattina); luci nuove nelle 24 ore: 25.
Reel del 7/11: 3 previsti (amici 13, prima_luce 18, ospiti_sera 21) e 3 pubblicati, più l'incoronazione recuperata alle 11:17.
Primi follower attribuiti (finestra fino al reel dopo, dati non ancora maturi): prima_luce di Atri 0 su 232 account; ospiti_sera 7 su 286 (24,5 ogni 1.000).
Centro Agenzia: 1 sessione, «senza direttore» (OpenAI risponde 401: chiave da sostituire, Alberto avvisato il 7/11). Coppa delle Zampe: turno 1, ancora 0 punti (il reel di apertura esce stasera alle 21).
Nessun cambiamento oggi.


## 2026-11-08 — verbale dei 7 giorni (automatico, motore/verbale.py)

- 2026-11-01-1206-fondatore: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).


## 2026-11-08 — verbale dei 7 giorni (automatico, motore/verbale.py)

- 2026-11-01-1509-presidente: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).


## 2026-11-09 — verbale dei 7 giorni (automatico, motore/verbale.py)

- 2026-11-01-1637-derby: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).
- 2026-11-01-1809-star: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).
- 2026-11-01-1937-gioco_bastone: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).
- 2026-11-01-2113-missione: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).

## 2026-11-09 — controllo del giorno

- Sito ok (docs 124 MB), motore vivo (ultima mappa 10:03 UTC). 18 luci nuove in 24 ore, follower 1.766 → 1.773.
- Reel dell'8/11: 3 su 3 pubblicati (13 testa_a_testa, 18 questa_luce corretto dalla squadra, 21 coppa_apertura). Direttore OpenAI ancora 401 (Alberto avvisato).
- Rendimento (lanciato a mano: quello delle 8:40 non è partito): testa_a_testa 9 follower su 237 raggiunti = 38 ogni 1.000, il migliore finora; questa_luce 8,9; coppa_apertura 1.615 views ma 5,0 ogni 1.000; ospiti_sera ora 19,0.
- Coppa: 3 punti in tutto, nessuna staffetta. Test di crescita in «anteprima» (non attivo): attende l'approvazione delle anteprime. Cantieri in pausa: nessuno nuovo aperto.
- Nessun cambiamento oggi.


## 2026-11-09 — verbale dei 7 giorni (automatico, motore/verbale.py)

- 2026-11-02-1144-presidente: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).
- 2026-11-02-1345-buio: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).


## 2026-11-10 — verbale dei 7 giorni (automatico, motore/verbale.py)

- 2026-11-02-2110-sfida: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).

## 2026-11-10 — controllo del giorno

- Sito ok (docs 136 MB), motore vivo (ultima mappa 11:01). 19 luci nuove in 24 ore, follower 1.773 → 1.795.
- Reel del 9/11: 3 su 3 pubblicati (13:09 prima_luce, 18:11 questa_luce, 21:18 puntata), tutti corretti dalla squadra (accensione allineata alla voce, musica più bassa, invito a seguire nella fascia). Direttore OpenAI ancora 401.
- Rendimento (lanciato a mano, quello delle 8:40 ancora in ritardo): follower ogni 1.000 raggiunti — testa_a_testa 8/11 34,5; questa_luce 9/11 21,5; puntata 9/11 19,5; ospiti_sera 7/11 17,9; prima_luce 9/11 16,6 (543 raggiunti, 9 follower); questa_luce 8/11 7,7; coppa_apertura 4,6 (molte views, pochi follower).
- Coppa: 3 punti, nessuna staffetta. Test di crescita ancora in «anteprima»: attende l'approvazione di Alberto. Nessun cambiamento oggi.


## 2026-11-10 — verbale dei 7 giorni (automatico, motore/verbale.py)

- 2026-11-03-1310-buio: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).

## 2026-11-10 — «basta Thor», realismo e gara (Alberto)

- Apertura dei reel: niente più Thor. Volo 3D di notte sul paese della storia fino alla cuccia dell'animale (reel/volo3d.js); se il 3D non riesce il reel parte dalla mappa.
- Realismo: nel paese 3D il tempo vero di adesso nel comune e la luna vera di stanotte (docs/mondo3d.js: leggiMeteo, faseLuna). Nel reel compare con la data del giorno.
- Gara: ogni animale nuovo è un punto per la sua città nella Coppa (coppa.luce, una volta per animale; config «coppa_punto_per_luce»); la risposta al commento dice il punteggio e chi insegue; sul sito «Le sfide più calde»; Staffetta di quartiere accesa. Prima: 3 punti in 3 giorni, perché serviva il codice dal sito.
- Officina Innovazione ogni giorno alle 14:41: una novità visibile online al giorno (reel, sito/grafica, gioco a rotazione), con priorità a realismo e gara.
- 10/11 sera, Alberto: «il reparto deve fare di più innovazione». Ogni apertura 3D ha ora la sua REGIA inventata dal reparto Innovazione con la Grafica 3D (motore/agenzia.py regia, registro docs/data/agenzia/regie.json): cielo, nebbia, lampioni e lucciole di colori nuovi, un effetto (foglie d'autunno, lanterne che salgono, stelle cadenti, fuochi d'artificio) e il volo della telecamera (discesa, orbita, radente, rivelazione, spirale). Mai lo stesso volo due volte di fila; il meteo vero del comune ha la precedenza.


## 2026-11-11 — verbale dei 7 giorni (automatico, motore/verbale.py)

- 2026-11-03-2116-puntata: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).

## 2026-11-11 — controllo del giorno

- Sito ok (docs 152 MB), motore vivo (ultima mappa 11:02). 21 luci nuove in 24 ore, follower 1.793 → 1.822 in due giorni.
- Reel del 10/11: 3 su 3 pubblicati, tutti corretti dalla squadra. Il 18 è il primo con l'apertura 3D (regia «Lume sul lago», meteo vero). Direttore OpenAI ancora 401.
- Rendimento, follower ogni 1.000 raggiunti: testa_a_testa 10/11 **58,8** (11 follower su 187, record), puntata 10/11 37,4, questa_luce 9/11 17,9, questa_luce 10/11 (3D) 16,2, puntata 9/11 15,9, prima_luce 9/11 15,8. Il testa a testa è primo in entrambi gli episodi (34,5 e 58,8).
- CAMBIAMENTO DEL GIORNO (coi numeri): alle 13 ogni giorno il testa a testa al posto della prima luce (config orari). Ci sono coppie di comuni vicini e pari per molti giorni.
- Coppa: 8 punti (erano 3): il punto per ogni luce nuova funziona. Staffetta di quartiere: Darfo Boario Terme 2/3, altri 4 comuni a 1/3. Nessun doppio.
- 11/11 Officina (giorno «aspetto dei reel» + gara): il testa a testa si apre col duello in 3D, le due città rivali una sopra l'altra col nome, le luci e il VS in mezzo (reel/apertura3d.py). Provato su GitHub senza pubblicare (Barletta–Molfetta, regia del reparto «Due Fari Adriatici»): esce domani alle 13.


## 2026-11-11 — verbale dei 7 giorni (automatico, motore/verbale.py)

- 2026-11-04-1309-fuochi: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).


## 2026-11-12 — verbale dei 7 giorni (automatico, motore/verbale.py)

- 2026-11-04-1806-star: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).
- 2026-11-04-1933-ospiti: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).
- 2026-11-04-2107-ospiti_sera: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).

## 2026-11-12 — controllo del giorno

- Sito ok (docs 170 MB), motore vivo. 26 luci nuove in 24 ore, follower 1.814 → 1.842 in due giorni.
- Reel dell'11/11: 2 su 3. Il reel delle 21 (puntata) è stato montato ma NON pubblicato: GitHub Pages non ha messo online il video in 20 minuti; la riserva non è partita (startup_failure di GitHub). Riparato: dopo 10 minuti di attesa Instagram prende il video dalla copia nel repository (raw.githubusercontent.com, motore/pubblica.py SITO_MEDIA). La puntata di ieri sera non si ripubblica (racconta la sera dell'11).
- Rendimento, follower ogni 1.000 raggiunti: testa_a_testa 10/11 51,4; puntata 10/11 28,8; questa_luce 11/11 19,5 (748 views, le più alte degli ultimi giorni, apertura 3D «Marmo e Mare» con foglie); questa_luce 9/11 16,5; testa_a_testa 11/11 11,9. Media del testa a testa su 3 episodi: 32,6, sempre primo.
- Coppa: 20 punti (3 → 8 → 20), Staffetta di quartiere: Darfo Boario Terme e Napoli a 2/3. Regie 3D usate: Lume sul lago, Duello al golfo, Marmo e Mare (tutte diverse). Nessun cambiamento oggi oltre alla riparazione.
- 12/11 Officina (giorno «realismo»): il paese 3D all'ora vera del comune (posizione vera del sole): giorno con sole e ombre lunghe di novembre, tramonto d'oro, crepuscolo coi lampioni che si accendono, notte con la luna vera. Sul sito entrando in un paese e nell'apertura dei reel (le 13 escono di giorno, le 18 e le 21 di notte). Corretto anche un errore vecchio della mappa (impulso con raggio negativo).
- 12/11 sera, Alberto: «voglio video nuovi, idee diverse, basta sempre ste cose». Due format nuovi, senza mappa e senza paese: «Indovina la razza» (sagoma nera sotto il riflettore e anello del tempo, poi la rivelazione a colori con quanti ce ne sono davvero sulla mappa e un esempio vero; due manche; chiusura «quante ne hai indovinate?») e «Le figurine delle Zampe» (si apre la bustina, gira la carta lucida col disegno della razza, il numero d'arrivo, la città e la rarità: comune, rara per i Fondatori, leggendaria per Capobranco e Presidenti). Alle 18 rotazione: quiz (13/11), figurine (14/11), luce nuova (15/11), e così via.


## 2026-11-12 — verbale dei 7 giorni (automatico, motore/verbale.py)

- 2026-11-05-1312-re: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).
- 12/11 notte, Alberto: «una gara di follower» e «reel da 8k views: aggiungere i padroni o qualcosa sulle varie città». (1) La gara dei follower: ogni SEGUO nuovo = +2 punti alla città nella Coppa, risposta col posto del paese, classifiche sul sito accanto ai follower veri verso i 2.000; reel «Quale città ci segue di più?» a barre (13/11 alle 21, poi mercoledì e sabato alle 21). (2) Le città raccontate: motore/citta.py prende da Wikipedia una frase vera per ogni comune (si tiene solo se le parole sono nel testo), usata nel testo a testa, nel duello 3D e nella gara. (3) I padroni: il testa a testa ha la scena «Le squadre in campo» con gli animali e il @ dei padroni, e tagga fino a 20 padroni delle due città (notifica → condivisioni). Prima il testa a testa non taggava nessuno.


## 2026-11-13 — verbale dei 7 giorni (automatico, motore/verbale.py)

- 2026-11-05-1806-star: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).
- 2026-11-05-2111-ospiti_sera: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).

## 2026-11-13 — controllo del giorno

- Sito ok (docs 187 MB), motore vivo (mappa 11:18). 20 luci nuove in 24 ore, follower 1.836 → 1.857 in due giorni.
- Reel del 12/11: 3 su 3 pubblicati, tutti corretti dalla squadra. GitHub ha dato 503 al primo pull (temporaneo).
- Rendimento: il testa a testa del 12/11, il primo col DUELLO 3D, ha la reach più alta degli ultimi giorni (992 views, 764 raggiunti; i testa a testa prima: 234–287) ma 6,5 follower ogni 1.000 (5 follower). questa_luce 11/11 885 views (16,6), questa_luce 12/11 18,1, coppa_sorpasso 12/11 3,5 (il più debole: 4 commenti). Media testa a testa su 4 episodi: 26,9.
- Coppa: 30 punti; Staffetta di quartiere a 2/3 per Darfo, Napoli, Venezia, Bisceglie e Barletta. Gara dei follower partita ieri alle 21: ancora nessun SEGUO nuovo da conteggiare.
- Nessun cambiamento oggi: escono per la prima volta il testa a testa con città raccontate e padroni taggati (13), il quiz (18) e la gara dei follower (21). Da guardare domani: il giovedì il sorpasso della Coppa rende poco (3,5).
- 13/11 Officina (giorno «la gara»): il tabellone della Coppa in piazza nel paese 3D, sul sito e nell'apertura dei reel: la sfida vera della città (es. Barletta 1 – 0 Carrara), la Staffetta di quartiere, il posto tra le città che ci seguono e «SEGUO = +2 punti». Nei reel il tabellone si gira verso la telecamera.


## 2026-11-13 — verbale dei 7 giorni (automatico, motore/verbale.py)

- 2026-11-06-1306-re: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).


## 2026-11-14 — verbale dei 7 giorni (automatico, motore/verbale.py)

- 2026-11-06-2123-fondatore: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).

## 2026-11-14 — controllo del giorno

- Sito ok (docs 217 MB), motore vivo (mappa 11:06). 28 luci nuove in 24 ore, follower 1.871 → 1.885.
- Reel del 13/11: 3 su 3 pubblicati.
- **Il testa a testa del 13/11 (Barletta–Bisceglie: duello 3D, città raccontate, squadre in campo e 8 padroni taggati) ha fatto 2.023 views in meno di 24 ore, 1.595 raggiunti, 73 commenti, 11 condivisioni**: il migliore dal 2/11, quattro volte la mediana (479). I testa a testa prima dei tag: 329–464 views; col solo duello 3D (12/11): 1.085. I follower però sono pochi: 5 (3,1 ogni 1.000): chi arriva commenta per il suo paese ma non segue.
- Quiz «Indovina la razza» (13/11 alle 18): 865 views, 628 raggiunti, 5 condivisioni ma solo 5 commenti. Gara dei follower (alle 21): 353 views dopo 13 ore, debole.
- Coppa: da 30 a 74 punti in un giorno. Staffetta di quartiere chiusa 3 volte a Bisceglie (11 persone), 2 a Barletta (7), 1 a Napoli: nessun doppio (persone e commenti tutti unici, punti = staffette). Gara dei follower: 6 SEGUO nuovi contati (Bisceglie 3).
- Nessun cambiamento oggi: il testa a testa coi padroni taggati resta alle 13; stasera alle 18 esce il primo «Trova l'intruso».

## 2026-11-14 — confronto dei 7 giorni (chiesto da Alberto il 7/11): follower ogni 1.000 account raggiunti, reel dal 7/11

21 reel organici maturi da almeno 12 ore; nessun reel sponsorizzato nel periodo (quello del 26/10 resta a parte). Follower attribuiti: quelli arrivati dopo l'uscita fino al reel successivo (max 6 ore).

| Format | Reel | Views (mediana) | Views (max) | Commenti (mediana) | Follower attribuiti | Raggiunti | Follower ogni 1.000 |
|---|---|---|---|---|---|---|---|
| puntata (21) | 2 | 531 | 571 | 32 | 13 | 686 | 19,0 |
| ospiti_sera | 1 | 822 | 822 | 68 | 7 | 431 | 16,2 |
| questa_luce (18) | 5 | 485 | 924 | 15 | 26 | 1.944 | 13,4 |
| testa_a_testa (13) | 5 | 464 | 2.023 | 18 | 33 | 3.280 | 10,1 |
| prima_luce | 2 | 656 | 807 | 33 | 9 | 947 | 9,5 |
| gara_follower | 1 | 353 | 353 | 11 | 2 | 233 | 8,6 |
| indovina (quiz) | 1 | 865 | 865 | 5 | 3 | 628 | 4,8 |
| coppa_apertura | 1 | 1.814 | 1.814 | 33 | 6 | 1.347 | 4,5 |
| coppa_sorpasso | 1 | 1.273 | 1.273 | 27 | 1 | 950 | 1,1 |

Senza dato sui follower: incoronazione e amici (usciti prima che partisse il conteggio ora per ora). Totale: 100 follower attribuiti su 10.446 raggiunti (9,6 ogni 1.000); i follower veri della settimana sono +162 (1.723 → 1.885).

**Lettura.** Per follower ogni 1.000 vincono i reel con persone e animali veri nominati (puntata, ospiti_sera, questa_luce). Per follower in totale e per views vince il testa a testa (33 follower, 2.023 views il 13/11). Ma nel testa a testa più sale la reach più scende la resa: 29,8 e 44,4 ogni 1.000 con 250–300 raggiunti, 6,1 e 3,1 con 820 e 1.595: il pubblico in più commenta per il suo paese e non segue (5 follower a reel, sempre). I reel della Coppa fanno views (1.273–1.814) ma quasi nessun follower.

**Decisione (un cambiamento, coi numeri).** Il testa a testa resta alle 13: è l'unico che porta gente nuova. Da oggi chiude con un motivo vero per seguire («Seguici: domani un'altra sfida», anche in didascalia). Da rivedere tra una settimana: se il sorpasso della Coppa del giovedì resta sotto 5 ogni 1.000, al suo posto torna la puntata.
- 14/11 Officina (giorno «aspetto dei reel», dallo studio del 13/11): «La corsa delle città» (formato `corsa`, scena `corsa`): le barre delle città crescono giorno per giorno dal 26/10 e si sorpassano, con la data che scorre (i giorni con più arrivi durano di più), poi «Vince Napoli con 93. Roma è a 4» e «E la tua città? Falla salire». Dati veri della mappa; a rotazione città, razze di cane, regioni. Prima uscita lunedì 16/11 alle 21 (una tantum): si confronta con la mediana di 479 views.


## 2026-11-14 — verbale dei 7 giorni (automatico, motore/verbale.py)

- 2026-11-06-2110-incoronazione: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).
- 2026-11-07-1303-amici: Follower attribuiti: indisponibile (il conteggio dei follower ora per ora non copre l'uscita di questo reel).
