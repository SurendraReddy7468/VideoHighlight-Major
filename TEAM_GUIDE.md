# VideoHighlight-Major — Team Learning Guide

## 1. Objective

This project builds a system that takes a long video and automatically produces a short, ready-to-post clip.

Given a video like:

```text
A 20-minute podcast interview
```

the system should output:

```text
A 30-60 second vertical clip containing the most engaging, understandable moment
```

The project focuses on **multimodal understanding** — combining audio, text (speech transcript), and video signals — rather than just picking a random loud or fast-talking section.

---

## 2. What the System Should Do

Given:

```text
Raw video file or YouTube link
```

the system produces:

```text
Highlights mode:
60-180s clip, 16:9, for YouTube/streaming

Shorts mode:
30-60s clip, 9:16 vertical, for Reels/TikTok/YouTube Shorts

Intro mode:
25-40s teaser clip designed to hook a viewer
```

Example: a 20-minute interview about "what success means" becomes a 20-second vertical clip of just the most quotable answer, with the speaker's face centered and captions burned in.

---

## 3. Core Concepts Used in This Project

```text
Speech-to-Text (Whisper)
Audio Signal Analysis (Energy, Pitch, Pauses)
TF-IDF Keyword Scoring
Sentiment Lexicon Scoring
Hook Detection (NLP pattern matching)
Scene Change Detection
Face Detection & Face-Aware Cropping
Multimodal Score Fusion
Narrative-Aware Segment Grouping   <- new in Major Project
LLM Semantic Re-Ranking (Llama 3.1) <- new in Major Project
Dynamic Top-N Selection            <- new in Major Project
Word-Level Caption Synchronization  <- new in Major Project
```

You don't need to understand all of these before writing any code — the learning path below builds them up one at a time.

---

## 4. The Big Picture

```text
Raw Video
   |
   v
Audio Extraction
   |
   v
Transcription (Whisper)
   |
   v
Segment Merging
   |
   v
Multimodal Scoring  (Audio + Text + Video signals)
   |
   v
Clip Selection
   |
   v
Format Conversion (crop to 9:16, add captions)
   |
   v
Final Short/Highlight Clip
```

Each box below is one Python module in `src/`. Read them in this order, not top-to-bottom in the file tree.

---

## 5. Step 1 — Load the Video

**File:** `src/preprocessing/video_loader.py`

Accepts either a local file path or a YouTube URL (via `yt-dlp`). If it's a URL, it downloads the video first.

```text
Input:
"https://youtube.com/watch?v=..." or "data/raw_videos/my_video.mp4"

Output:
A local video file path the rest of the pipeline can use
```

---

## 6. Step 2 — Extract Audio

**File:** `src/preprocessing/audio_extractor.py`

Video files contain both a video track and an audio track. We pull just the audio out as a `.wav` file, because every audio-analysis step downstream (Whisper, energy, pitch) works on audio only, not video frames.

```text
video.mp4  -->  audio.wav
```

---

## 7. Step 3 — Transcription (Whisper)

**File:** `src/analysis/text/transcription.py`

OpenAI's Whisper model listens to the audio and converts speech into text, with timestamps for every sentence.

Example output:

```text
{
  "start": 0.0,
  "end": 15.0,
  "text": "What is the definition of success for you?"
}
```

This is the single most important step — almost everything else in the pipeline reads this transcript.

---

## 8. Step 4 — Segment Merging

**File:** `src/preprocessing/segmenter.py`

Whisper produces many tiny chunks (a few words each). These are merged into readable, sentence-level segments based on natural pauses (gaps of silence), so we're scoring complete thoughts, not fragments.

```text
14 raw Whisper chunks  -->  2-3 merged segments
```

---

## 9. Step 5 — Audio Signal Analysis

**Files:** `src/analysis/audio/energy.py`, `pitch.py`, `pause_detection.py`

Three separate signals, each answering a different question about *how* something was said:

```text
Energy  -> How loud/intense is this moment? (excitement, emphasis)
Pitch   -> How much does tone vary? (animated speech vs monotone)
Pauses  -> Are there natural breaks? (helps find clean cut points)
```

Example: a segment scoring `energy=0.90` is spoken with noticeably more intensity than the video's average — a signal (not proof) that it might be a highlight-worthy moment.

---

## 10. Step 6 — Text Signal Analysis

**Files:** `src/analysis/text/keywords.py`, `sentiment.py`, `hook_detector.py`

Three signals, this time about *what* was said:

```text
Keywords  -> TF-IDF: which words are unusually important to THIS segment
             compared to the rest of the video (same idea as classic NLP)
Sentiment -> Positive/negative/neutral tone of the text
Hook      -> Does this sound like an attention-grabbing opener?
             ("Here's the thing nobody tells you...")
```

This is the same TF-IDF concept used in general text-classification projects — here it's applied per-segment instead of per-document.

---

## 11. Step 7 — Video Signal Analysis

**Files:** `src/analysis/video/scene_change.py`, `face_detect.py`

```text
Scene Change -> Did the camera angle/shot change during this segment?
Face         -> Is a face visible, and where (for cropping later)?
```

---

## 12. Step 8 — Multimodal Score Fusion

**File:** `src/scoring/highlight_score.py`

All the signals above get combined into one final score per segment, using weighted averages:

```text
Podcast mode:  Audio 45% + Text 45% + Video 10%
Normal mode:   Audio 30% + Text 30% + Video 40%
```

Podcast mode weights video lower because podcasts are mostly a static shot — what matters is what's being said, not what's visually happening.

---

## 13. Step 9 — Clip Selection & Format Conversion

**Files:** `src/editing/clip_generator.py`, `format_converter.py`

The highest-scoring segments are greedily selected until they add up to the target clip length, then stitched together with crossfades, and finally cropped to vertical (9:16) format using the face position from Step 11 to keep the speaker centered.

---

## 14. What's New in the Major Project

The mini project stops at Step 12 — score each segment independently, pick the highest scorers. The major project adds a layer that asks a harder question: **does this clip make sense on its own?**

```text
Narrative Grouping
   -> Finds related segment pairs (Question->Answer, Problem->Solution)
      and merges them so a clip never starts mid-explanation

LLM Semantic Re-Ranking (Llama 3.1)
   -> Re-scores each candidate clip on completeness and context,
      not just the raw signal score

Dynamic Top-N
   -> Instead of a fixed "always pick 3 clips," the number of clips
      output scales with how much genuinely good content exists

Karaoke Captions
   -> Word-level timestamps from Whisper are used to highlight
      each word as it's spoken, burned directly into the video
```

---

## 15. Recommended Learning Order

```text
1. Run test_stage1.py  -> understand transcription output
2. Run test_stage2.py  -> understand individual signal scores
3. Run test_stage3.py  -> understand scoring -> clip -> format conversion
4. Read highlight_score.py closely -> understand the weighted fusion
5. Read clip_generator.py -> understand greedy selection
6. THEN start reading the Feature 1-4 major project code
```

Don't start on narrative grouping or LLM re-ranking before steps 1-5 make sense — they build directly on top of the scoring system, not around it.

---

## 16. Setup

Full install steps are in `INSTALL.md` in the repo root. Short version:

```text
1. Install Python 3.12 (not 3.14 — some libraries don't support it yet)
2. Clone the repo
3. Create a venv, activate it
4. Install ffmpeg
5. pip install -r requirements.txt
6. Run test_stage1.py, test_stage2.py, test_stage3.py in order
```

---

## 17. Where to Go Deeper

The research papers behind Features 1-4 are cited in the project's presentation deck under "Related Work" — worth a skim once the code above makes sense, especially the HIVE paper (narrative-aware editing) and the "Minimal Clips, Maximum Salience" paper (dynamic clip count).