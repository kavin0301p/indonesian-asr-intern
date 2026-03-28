# Indonesian ASR @ NTU Speech & Language Lab
Large-scale crawling and processing of Southeast Asian speech into ASR training datasets for downstream model training.

## Project Components:
- YouTube crawling with [yt-dlp](https://github.com/yt-dlp/yt-dlp) on Google Colab
- Data processing and model inference on NSCC ASPIRE2A
- Automatic transcription / segmentation via:
  - [GigaSpeech2](https://github.com/SpeechColab/GigaSpeech2)
  - [NeMo SDP (Granary)](https://github.com/NVIDIA/NeMo-speech-data-processor/tree/main/dataset_configs/multilingual/granary)
- Segment normalisation, filtering, and dataset export for ASR training

## Goals
1. Collect in-the-wild speech data from YouTube
   - Covering Indonesian, Indonesian–English code-switching, and Southeast Asian English accents (Indonesian, Filipino).
2. Run inference and processing on the NSCC
   - Reproduce and adapt the GigaSpeech2 and NeMo SDP / Granary pipelines for Indonesian and SEA speech.
3. Produce high-quality ASR training datasets for low-resource settings
   - Generate segmented audio + transcripts with consistent normalisation, filtering, and manifests ready for downstream ASR training.
   
## High-Level Pipeline
1. Crawl audio & metadata on Google Colab using yt-dlp.
2. Sync crawled data to NSCC via `scp` or `rsync` into the NSCC scratch directory.
3. Run speech processing pipelines:
   - GigaSpeech2
   - NeMo SDP / Granary
4. Apply text normalisation and filtering (language, numbers/dates, etc.)
5. Export manifests (JSONL/TXT) listing audio paths, timestamps, durations, and cleaned transcripts.

## Data Overview
Raw hours crawled:

| Language                    | Hours (approx.) |
|-----------------------------|-----------------|
| Indonesian (mono + CS)      | ~2,900          |
| English – Indonesian accent | ~763            |
| English – Filipino accent   | ~787            |

## Internship Timeline

- **Weeks 1–2 – GigaSpeech2 pipeline & crawling setup**  
  - Implemented the GigaSpeech2 pipeline on the NSCC cluster for a small Indonesian channel.  
  - Set up YouTube crawling (yt-dlp, VPN, cookie handling and sleep intervals).  
  - Refined filtering: reduced confidence threshold and allowed LID labels `ms` and `id`.  
  - Used WER to assess data loss at the force alignment stage.

- **Weeks 3–4 – Large-scale processing & Granary trial**  
  - Identified Indonesian speech data sources (news channels, vlogs, commentary, etc.).  
  - Scaled up crawling and processing to ~1.3k hours of Indonesian audio.  
  - Set up the NeMo SDP / Granary pipeline on NSCC, modifying config processors for ASR training.  
  - Generated Granary manifests and tarred datasets as pipeline outputs.

- **Weeks 5–6 – Scaling up & quality control**  
  - Implemented batching and parallel processing for the GigaSpeech2 pipeline on NSCC.  
  - Compared GigaSpeech2 and Granary for processing speed, segment length, and transcript quality.  
  - Investigated Granary segmentation issues (boundary word loss, chunking behaviour, hallucinations).

- **Weeks 7–8 – SEA English accents & normalisation**  
  - Shifted focus to SEA–accented English: Crawled Indonesian-accented English channels. 
  - Tested Indonesian text normalisation (numbers, currency, time).  
  - Prototyped a merged pipeline: Granary for transcription, GigaSpeech2 for force alignment, filtering, and segmentation.  
  - Exported segment-level `txt` samples containing utterance IDs and start–end timestamps.

- **Weeks 9–10 – Segmentation strategies & dataset assembly**  
  - Continued Indonesian and Filipino-accented English crawling.  
  - Implemented punctuation-based segmentation for Granary transcripts, inserted after the transcription stage.  
  - Added post-processing rules to remove utterances containing numbers and dates.  
  - Compiled processed segments into a training dataset with aligned `wav`–`txt` pairs.

- **Weeks 11–12 – Debugged crawling & accented English evaluation**  
  - Continued Filipino-accented English crawling.  
  - Updated the yt-dlp crawling script to use a local `deno` installation for deciphering YouTube `n`/`sig` values.  
  - Sampled ~10 hours of segment-level wav–transcript pairs for export.  
  - Compared GigaSpeech2 and Granary performance on noisy, accented English data.

- **Weeks 13–14 – Continued processing & repository preparation**  
  - Updated punctuation normalisation at force alignment stage to allow `'` and `-`.
  - Processed Indonesian and Filipino-accented English speech with the GigaSpeech2 pipeline.
  - Compiled GitHub repository.
