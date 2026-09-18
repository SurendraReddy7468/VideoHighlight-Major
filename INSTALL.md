# Setup Guide — VideoHighlight-Major

Tested and verified on Windows (Python 3.12) and should work identically on macOS.
**Do not use Anaconda/conda** — this project uses plain pip + venv for consistency across machines.

## 1. Install Python 3.12

Python 3.14+ will NOT work — some dependencies (numba, numpy) don't yet support it.

- **Windows:** Download from https://www.python.org/downloads/release/python-3120/
  - Check "Add python.exe to PATH" during install
- **Mac:** `brew install python@3.12`

Verify:

python3.12 --version # Mac
py -3.12 --version # Windows


## 2. Clone the repo

git clone https://github.com/SurendraReddy7468/VideoHighlight-Major.git
cd VideoHighlight-Major


## 3. Create and activate a virtual environment

**Windows:**

py -3.12 -m venv env
.\env\Scripts\activate

**Mac:**

python3.12 -m venv env
source env/bin/activate


You should see `(env)` at the start of your terminal prompt.

## 4. Install ffmpeg (required, not a Python package)

**Windows:** `winget install ffmpeg`
**Mac:** `brew install ffmpeg`

Verify: `ffmpeg -version`

## 5. Install Python dependencies

pip install -r requirements.txt


This installs ~45 packages including Whisper, librosa, OpenCV, and torch — takes a few minutes.

## 6. Test the pipeline

Run the three test scripts in order to confirm everything works:

python test_stage1.py # download video, transcribe
python test_stage2.py # audio/text signal scoring
python test_stage3.py # full clip generation


By default these use a YouTube URL set inside `test_stage1.py` — you can change `SOURCE` to any other YouTube link or a local video path.

Output appears in `data/outputs/shorts/final_short.mp4`.

## Known issues

- `yt-dlp` may print a "JS runtime" warning — harmless, ignore it.
- The `data/` folder (videos, audio, transcripts) is gitignored on purpose — each person generates their own test files locally, they are never pushed to GitHub.