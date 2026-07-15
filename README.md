FLAC Quality Analyzer

Un analizzatore avanzato scritto in Python per verificare l'effettiva qualità dei file audio FLAC. Questo script esegue tre controlli principali:

    Lettura dei metadati (risoluzione, bitrate, frequenza di campionamento).

    Verifica dell'integrità strutturale tramite lo strumento ufficiale flac per rilevare file corrotti.

    Analisi spettrale (FFT) per rilevare eventuali "falsi FLAC" (file MP3 upscalati e mascherati da formato lossless).

Al termine dell'esecuzione, lo script genera automaticamente un report dettagliato in formato CSV.
⚙️ Requisiti di Sistema

Prima di configurare l'ambiente Python, assicurati di avere installato nel tuo sistema le librerie di base necessarie per l'analisi audio.

Sulle distribuzioni basate su Arch Linux (incluso CachyOS), apri il terminale ed esegui:
Bash

sudo pacman -S libsndfile flac

    Nota: libsndfile è essenziale per far funzionare il modulo Python soundfile, mentre il pacchetto flac fornisce il comando nativo utilizzato dallo script per testare l'integrità dei frame.

🐍 Installazione Dipendenze Python

Assicurati di avere il file requirements.txt nella stessa cartella dello script. Installa tutte le librerie necessarie tramite pip (se utilizzi ambienti virtuali come venv, ricordati di attivarlo prima):
Bash

pip install -r requirements.txt

Questo comando installerà:

    numpy e soundfile (per l'analisi spettrale)

    mutagen (per la lettura rapida dei metadati)

    tqdm (per la barra di progressione a schermo)

🚀 Come usare lo script

Una volta soddisfatti tutti i requisiti, puoi avviare l'analizzatore direttamente da terminale:
Bash

python analyzer.py

    Lo script ti chiederà di inserire il percorso della cartella contenente la tua musica.

    Puoi inserire un percorso assoluto (es. /home/nome-utente/Musica/) o relativo.

    L'analizzatore scansionerà ricorsivamente tutte le sottocartelle trovando ogni file .flac.

    Al termine, troverai il file flac_quality_report.csv salvato direttamente all'interno della cartella che hai appena analizzato.