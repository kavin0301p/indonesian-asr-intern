import os
import json
import re
from pathlib import Path
from pydub import AudioSegment
import yaml
import argparse


def parse_vtt_file(vtt_path):
    """
    Custom WEBVTT file parsing, compatible with:
    - WEBVTT header
    - Kind: captions
    - Language: en
    - Timestamp blocks + multi-line text
    """
    segments = []
    with open(vtt_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    current = {}
    text_buffer = []

    time_pattern = re.compile(r"(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3})")

    for line in lines:
        line = line.strip()
        if not line:
            if current and text_buffer:
                current["text"] = " ".join(text_buffer)
                segments.append(current)
                current = {}
                text_buffer = []
            continue

        match = time_pattern.match(line)
        if match:
            current["start"] = match.group(1)
            current["end"] = match.group(2)
        elif current:
            text_buffer.append(line)

    if current and text_buffer:
        current["text"] = " ".join(text_buffer)
        segments.append(current)

    return segments


def vtt_time_to_millis(time_str):
    """
    HH:MM:SS.MS → 毫秒
    """
    h, m, s = time_str.split(':')
    s, ms = s.split('.')
    return (int(h) * 3600 + int(m) * 60 + int(s)) * 1000 + int(ms)


def process_audio_with_vtt(audio_path, vtt_path, output_dir, target_sr, save_audio):
    audio = AudioSegment.from_file(audio_path)
    if audio.frame_rate != target_sr:
        audio = audio.set_frame_rate(target_sr)

    wav_dir = output_dir / "wav"
    if save_audio:
        wav_dir.mkdir(parents=True, exist_ok=True)

    output_json = []

    segments = parse_vtt_file(vtt_path)

    for idx, seg in enumerate(segments):
        start_ms = vtt_time_to_millis(seg["start"])
        end_ms = vtt_time_to_millis(seg["end"])

        seg_name = f"{idx+1:04d}.wav"
        seg_path = wav_dir / seg_name if save_audio else f"{seg_name}"

        if save_audio:
            segment = audio[start_ms:end_ms]
            segment.export(seg_path, format="wav")

        output_json.append({
            "segment": str(seg_path),
            "text": seg["text"].strip(),
            "start_ms": start_ms,
            "end_ms": end_ms
        })

    return output_json


def main(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    channel = config.get("channel")
    target_sr = config.get("slice_sample_rate", 16000)
    save_audio = config.get("slice_save_audio", True)  # 新增字段

    base_dir = Path("./output") / channel
    audio_dir = base_dir / "audio"
    subs_dir = base_dir / "subs"
    segments_dir = base_dir / "segments"

    segments_dir.mkdir(parents=True, exist_ok=True)

    for audio_file in audio_dir.glob("*.webm"):
        video_id = audio_file.stem

        vtt_candidates = list(subs_dir.glob(f"{video_id}.*.vtt"))
        if not vtt_candidates:
            print(f"❌ Subtitles not found:{video_id}")
            continue

        vtt_file = vtt_candidates[0]
        print(f"✅ Processing{video_id} ... (save_audio={save_audio})")

        seg_output_dir = segments_dir / video_id
        seg_output_dir.mkdir(parents=True, exist_ok=True)

        seg_info = process_audio_with_vtt(
            audio_file,
            vtt_file,
            seg_output_dir,
            target_sr,
            save_audio
        )

        # 写 JSON（和 wav/ 并列）
        with open(seg_output_dir / "segments.json", "w", encoding="utf-8") as f:
            json.dump(seg_info, f, ensure_ascii=False, indent=2)

        print(f"🎉 Completed: {len(seg_info)} segments, JSON saved -> {seg_output_dir/'segments.json'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="根据字幕切分音频，输出统一 wav 文件夹 + 起止时间 + 可选保存音频")
    parser.add_argument("--config", type=str, required=True, help="YAML 配置文件路径")
    args = parser.parse_args()

    main(config_path=args.config)
