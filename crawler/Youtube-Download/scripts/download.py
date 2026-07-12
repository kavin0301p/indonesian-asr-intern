import json
import yaml
import subprocess
from pathlib import Path
import argparse


def download_audio_and_subtitles(config_path):
    # === 1️⃣ Load Configuration===
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    channel = config.get("channel")
    COOKIE_FILE = config.get("COOKIE_FILE", "./config/cookies.txt")
    subtitle_lang = config.get("subtitle_lang")

    # === 2️⃣ Directory Preparation ===
    base_output_dir = Path(config.get("output_dir", "./output"))
    channel_dir = base_output_dir / channel
    channel_audio_dir = channel_dir / "audio"
    channel_subs_dir = channel_dir / "subs"
    channel_info_dir = channel_dir / "info"

    channel_audio_dir.mkdir(parents=True, exist_ok=True)
    channel_subs_dir.mkdir(parents=True, exist_ok=True)

    # === 3️⃣ Download log file ===
    downloaded_list_file = channel_dir / "downloaded.txt"
    if downloaded_list_file.exists():
        with open(downloaded_list_file, "r", encoding="utf-8") as f:
            downloaded_ids = set(line.strip() for line in f if line.strip())
    else:
        downloaded_ids = set()

    # === 4️⃣ Filtered files ===
    filtered_info_file = channel_info_dir / "video_metadata-filtered.jsonl"
    with open(filtered_info_file, encoding="utf-8") as f:
        lines = f.readlines()

    for line_num, line in enumerate(lines, 1):
        try:
            info = json.loads(line)
        except json.JSONDecodeError:
            print(f"❌ Skip: No. {line_num} It is not legal. JSON")
            continue

        video_id = info["id"]
        if video_id in downloaded_ids:
            print(f"⏭️ Already downloaded, skipping:{video_id}")
            continue

        video_url = f"https://www.youtube.com/watch?v={video_id}"

        # === 5️⃣ 下载音频 ===
        audio_output = channel_audio_dir / f"{video_id}.webm"
        print(f"🎵 Downloading audio...：{video_id}")
        try:
            subprocess.run([
                "yt-dlp",
                "-f", "ba",
                "--cookies", COOKIE_FILE,
                "-o", str(audio_output),
                video_url
            ], check=True)
        except subprocess.CalledProcessError:
            print(f"⚠️ Audio download failed:{video_id}")
            continue  # 音频没下成功，整个跳过，不写记录

        # === 6️⃣ 下载字幕（最多 1 个） ===
        subtitles = info.get("subtitles", [])
        target_sub = None

        for sub in subtitles:
            if sub.get("lang") == subtitle_lang and sub.get("type") == "manual":
                target_sub = sub
                break

        if not target_sub:
            for sub in subtitles:
                if sub.get("lang") == subtitle_lang and sub.get("type") == "auto":
                    target_sub = sub
                    break

        if target_sub:
            lang = target_sub["lang"]
            print(f"📝 Downloading subtitles:{video_id} - {lang} ({target_sub['type']})")
            try:
                subprocess.run([
                    "yt-dlp",
                    "--write-sub",
                    "--sub-lang", lang,
                    "--sub-format", "vtt",
                    "--skip-download",
                    "--cookies", COOKIE_FILE,
                    "-o", str(channel_subs_dir / f"{video_id}"),
                    video_url
                ], check=True)
            except subprocess.CalledProcessError:
                print(f"⚠️ Subtitle download failed:{video_id} - {lang}")
        else:
            print(f"ℹ️ No subtitles available:{video_id} (priority {subtitle_lang})")

        # === 7️⃣ 下载成功，记录 ID ===
        with open(downloaded_list_file, "a", encoding="utf-8") as f:
            f.write(f"{video_id}\n")
        downloaded_ids.add(video_id)
        print(f"✅ Download completion recorded.：{video_id}")

    print("🎉 All audio and subtitle download tasks have been completed.")


# ========= 🚀 入口一致 =========
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="下载音频 + 字幕 (记录已下载)")
    parser.add_argument("--config", type=str, required=True, help="YAML 配置文件路径")
    args = parser.parse_args()

    download_audio_and_subtitles(config_path=args.config)
