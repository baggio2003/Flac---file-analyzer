FLAC Quality Analyzer

An advanced Python script designed to verify the true quality of FLAC audio files. This script performs three main checks:

Metadata extraction (resolution, bitrate, sample rate).

Structural integrity verification using the official flac command-line tool to detect corrupted files.

Spectral analysis (FFT) to identify "fake FLACs" (upscaled MP3 files disguised as lossless format).

Upon completion, the script automatically generates a detailed report in CSV format.

⚙️ System Requirements

Before setting up the Python environment, make sure you have the necessary base libraries for audio analysis installed on your system.

On Arch Linux-based distributions (including CachyOS), open the terminal and run:

Bash

    sudo pacman -S libsndfile flac

Note: libsndfile is essential for the Python soundfile module to work, while the flac package provides the native command used by the script to test frame integrity.

🐍 Python Dependencies Installation

Ensure the requirements.txt file is located in the same directory as the script. Install all necessary libraries via pip (if you are using a virtual environment like venv, remember to activate it first):

Bash

    pip install -r requirements.txt

This command will install:

numpy and soundfile (for spectral analysis).

mutagen (for fast metadata reading).

tqdm (for the on-screen progress bar).

🚀 How to Use the Script

Once all requirements are met, you can launch the analyzer directly from the terminal:

Bash

    python analyzer.py

The script will prompt you to enter the path of the folder containing your music.

You can enter an absolute path (e.g., /home/username/Music/) or a relative one.

The analyzer will recursively scan all subfolders to find every .flac file.

When finished, you will find the flac_quality_report.csv file saved directly inside the folder you just analyzed.
