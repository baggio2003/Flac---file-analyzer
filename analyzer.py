# -*- coding: utf-8 -*-
"""
Analizzatore Avanzato di Qualità dei File FLAC (FIXED)
---------------------------------------------
Questo script scansiona ricorsivamente una cartella alla ricerca di file FLAC 
ed esegue tre tipi di analisi per ciascun file:
1. Lettura dei Metadati e Specifiche (Risoluzione, Bitrate, Campionamento) via Mutagen.
2. Verifica di Integrità strutturale del file via comando ufficiale 'flac -t'.
3. Analisi Spettrale (rilevamento di "Falsi FLAC" derivati da MP3) via Soundfile e FFT NumPy.

Genera inoltre un report finale dettagliato in formato CSV.
"""

import os
import sys
import csv
import subprocess
import numpy as np
import soundfile as sf
from mutagen.flac import FLAC

# Colori ANSI per la riga di comando (funzionano su Linux/macOS e Windows 10+)
if sys.platform == "win32":
    os.system('color')  # Attiva il supporto ANSI su Windows

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Gestione della barra di progressione (tqdm o fallback personalizzato)
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    # Fallback semplice se tqdm non è installato
    def tqdm(iterable, desc="", total=None):
        if total is None:
            total = len(iterable)
        for i, item in enumerate(iterable):
            percent = (i + 1) / total * 100
            print(f"\r{BLUE}{desc}{RESET} | Avanzamento: {BOLD}{i+1}/{total}{RESET} ({percent:.1f}%)", end="", flush=True)
            yield item
        print()

def analizza_metadati(file_path):
    """Analizza i metadati audio del file FLAC utilizzando Mutagen."""
    try:
        audio = FLAC(file_path)
        info = audio.info
        return {
            "sample_rate": info.sample_rate,
            "bits_per_sample": info.bits_per_sample,
            "channels": info.channels,
            "duration": round(info.length, 2),
            "bitrate": round(info.bitrate / 1000, 1) if info.bitrate else "N/D"
        }
    except Exception as e:
        return {"error": f"Errore metadati: {str(e)}"}

def verifica_integrita(file_path):
    """Esegue un controllo di integrità usando lo strumento da riga di comando ufficiale 'flac'."""
    try:
        # Comando: flac -t -s (test, silent) per testare il checksum MD5 interno dei frame
        risultato = subprocess.run(['flac', '-t', '-s', file_path], capture_output=True, text=True)
        if risultato.returncode == 0:
            return "OK", ""
        else:
            errore = risultato.stderr.strip() if risultato.stderr else "File corrotto o troncato"
            return "CORROTTO", errore
    except FileNotFoundError:
        return "N/D", "Strumento a riga di comando 'flac' non trovato nel sistema"

def analizza_falso_flac(file_path):
    """
    Analisi spettrale veloce via FFT NumPy per identificare falsi FLAC (upscalati da MP3).
    """
    try:
        info = sf.info(file_path)
        sr = info.samplerate
        duration = info.duration

        if sr < 32000:
            return "Inconcludente (Sample rate troppo bassa)", 0.0, 0.0

        # Leggiamo circa 10 secondi nel mezzo del file per evitare silenzi iniziali/finali e velocizzare
        if duration > 20:
            start_frame_pos = int((duration / 2 - 5) * sr)
            frames_to_read = int(10 * sr)
            # FIX: the argument is 'start', not 'start_frame' in soundfile
            data, _ = sf.read(file_path, start=start_frame_pos, frames=frames_to_read)
        else:
            data, _ = sf.read(file_path)

        # Se stereo, facciamo la media per ottenere un segnale mono
        if len(data.shape) > 1:
            data = np.mean(data, axis=1)

        n = len(data)
        if n == 0:
            return "Errore (File vuoto)", 0.0, 0.0

        # Calcoliamo la trasformata di Fourier (FFT reale)
        frequencies = np.fft.rfftfreq(n, d=1/sr)
        amplitudes = np.abs(np.fft.rfft(data))

        # Convertiamo in scala logaritmica (dB)
        amplitudes_db = 20 * np.log10(amplitudes + 1e-10)
        max_val = np.max(amplitudes_db)
        
        # Normalizziamo rispetto al picco massimo (il picco diventa 0 dB)
        if max_val > -100:
            amplitudes_db -= max_val

        # Definiamo le bande di frequenza per l'analisi del taglio (cutoff)
        idx_low = (frequencies > 1000) & (frequencies < 15000)
        idx_high = (frequencies > 16000) & (frequencies < 21000) if sr >= 44100 else (frequencies > 16000)

        if not np.any(idx_low) or not np.any(idx_high):
            return "Inconcludente (Bande frequenza insufficienti)", 0.0, 0.0

        mean_low = np.mean(amplitudes_db[idx_low])
        max_high = np.max(amplitudes_db[idx_high])
        mean_high = np.mean(amplitudes_db[idx_high])

        # Differenza tra l'energia media della banda principale e quella alta
        diff = mean_low - mean_high

        # HEURISTIC: Se la frequenza massima sopra i 16kHz è estremamente bassa (es. sotto -55dB)
        # e la differenza di energia media è marcata (>40dB), indica un taglio netto tipico di compressione lossy.
        if max_high < -55 and diff > 40:
            return "Sospetto Falso FLAC (MP3 Riconvertito)", float(max_high), float(diff)
        else:
            return "Vero Lossless", float(max_high), float(diff)

    except Exception as e:
        return f"Errore Spettro: {str(e)}", 0.0, 0.0

def main():
    print(f"{BOLD}{CYAN}====================================================={RESET}")
    print(f"{BOLD}{CYAN}      ANALIZZATORE COMPLETO DI QUALITÀ FLAC          {RESET}")
    print(f"{BOLD}{CYAN}====================================================={RESET}\n")
    
    percorso_cartella = input("Inserisci il percorso della cartella da analizzare (es. /home/claudio/Music/): ").strip()
    if not percorso_cartella or not os.path.exists(percorso_cartella):
        print(f"{RED}Errore: Percorso non valido o non esistente.{RESET}")
        sys.exit(1)

    # Scansione dei file flac nella cartella e sottocartelle
    file_flac = []
    for root, _, files in os.walk(percorso_cartella):
        for file in files:
            if file.lower().endswith('.flac'):
                file_flac.append(os.path.join(root, file))

    totale_file = len(file_flac)
    if totale_file == 0:
        print(f"{YELLOW}Nessun file .flac trovato nella cartella specificata.{RESET}")
        sys.exit(0)

    print(f"\nTrovati {BOLD}{totale_file}{RESET} file FLAC da analizzare.\n")
    if not HAS_TQDM:
        print(f"{YELLOW}Nota: Per una barra di progressione grafica migliore, installa tqdm: 'pip install tqdm'{RESET}\n")

    report_data = []
    file_corrotti = 0
    file_falsi = 0

    # Ciclo di analisi con progressione visibile
    for file_path in tqdm(file_flac, desc="Analisi in corso", total=totale_file):
        rel_path = os.path.relpath(file_path, percorso_cartella)
        
        # 1. Metadati
        meta = analizza_metadati(file_path)
        
        if "error" in meta:
            # Errore grave di lettura del file
            report_data.append({
                "File": rel_path,
                "Integrita": "ERRORE LETTURA",
                "Spettro": "N/D",
                "Metadati": meta["error"],
                "Dettagli": ""
            })
            continue

        # 2. Integrità
        integrita, dettagli_integrita = verifica_integrita(file_path)
        if integrita == "CORROTTO":
            file_corrotti += 1

        # 3. Analisi Spettrale (Falso FLAC)
        spettro_risultato, max_high, diff = analizza_falso_flac(file_path)
        if "Sospetto Falso" in spettro_risultato:
            file_falsi += 1

        # Salvataggio dati report
        report_data.append({
            "File": rel_path,
            "Integrita": integrita,
            "Spettro": spettro_risultato,
            "Metadati": f"{meta['bits_per_sample']}bit | {meta['sample_rate']}Hz | {meta['channels']}ch | {meta['duration']}s | {meta['bitrate']}kbps",
            "Dettagli": dettagli_integrita if dettagli_integrita else f"MaxHigh: {max_high:.1f}dB, Diff: {diff:.1f}dB"
        })

    # Stampa i risultati sintetici a schermo
    print(f"\n{BOLD}{CYAN}====================================================={RESET}")
    print(f"{BOLD}{CYAN}                 SINTESI REPORT                      {RESET}")
    print(f"{BOLD}{CYAN}====================================================={RESET}")
    print(f"File totali analizzati: {BOLD}{totale_file}{RESET}")
    
    # Integrità
    if file_corrotti > 0:
        print(f"File Corrotti (MD5 mismatch): {RED}{BOLD}{file_corrotti}{RESET}")
    else:
        print(f"File Corrotti (MD5 mismatch): {GREEN}{BOLD}0 (Tutti integri!){RESET}")
        
    # Falsi FLAC
    if file_falsi > 0:
        print(f"File Sospetti Falsi FLAC (MP3): {RED}{BOLD}{file_falsi}{RESET}")
    else:
        print(f"File Sospetti Falsi FLAC (MP3): {GREEN}{BOLD}0 (Tutti Lossless reali!){RESET}")

    # Salvataggio su file CSV nella cartella analizzata
    csv_file_path = os.path.join(percorso_cartella, "flac_quality_report.csv")
    try:
        with open(csv_file_path, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["File", "Integrita", "Spettro", "Metadati", "Dettagli"])
            writer.writeheader()
            writer.writerows(report_data)
        print(f"\n{GREEN}Report dettagliato salvato correttamente in:{RESET}")
        print(f"{BOLD}{csv_file_path}{RESET}\n")
    except Exception as e:
        print(f"{RED}Errore nel salvataggio del report CSV: {e}{RESET}\n")

if __name__ == "__main__":
    main()