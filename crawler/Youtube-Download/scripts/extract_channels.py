import os
import yaml
import subprocess
import sys
from pathlib import Path
import json
import argparse
import re


def get_subtitle_language(result: str):
    """
    Parse `yt-dlp --list-subs` output
    Returns a list of subtitles:
      [{"lang": "en", "type": "auto"}, {"lang": "ch-Hans", "type": "manual"}]
    """
    subtitles = []

    auto_flag = False
    manu_flag = False
    fallback_plain_table = False

    for line in result.splitlines():
        line = line.strip()
        if not line:
            continue

        if "auto-generated:" in line:
            auto_flag = True
            manu_flag = False
            fallback_plain_table = False

        elif "manually provided:" in line:
            auto_flag = False
            manu_flag = True
            fallback_plain_table = False

        elif line.lower().startswith("language name"):
            fallback_plain_table = True
            auto_flag = False
            manu_flag = False

        elif fallback_plain_table:
            parts = line.split()
            if parts:
                lang = parts[0]
                subtitles.append({"lang": lang, "type": "manual"})

        elif re.match(r"^\w+", line):
            parts = line.split()
            if parts:
                lang = parts[0]
                if auto_flag:
                    subtitles.append({"lang": lang, "type": "auto"})
                elif manu_flag:
                    subtitles.append({"lang": lang, "type": "manual"})

    return subtitles


def process_channel_videos(config_path="./config/config.yaml"):
    """
    Main workflow:
    1. Load configuration file
    2. Call yt-dlp to retrieve channel video metadata
    3. Parse all subtitle elements
    4. Output JSONL, saving only the subtitles
    """

    # ========= 1️⃣ 加载配置 =========
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    channel = config.get("channel")
    COOKIE_FILE = config.get("COOKIE_FILE", "./config/cookies.txt")
    start_index = config.get("start_index", 0)
    end_index = config.get("end_index", 1)
    sub_lang = config.get("subtitle_lang", None)

    if not channel:
        print("❌ The configuration file is missing the `channel` field; cannot proceed.")
        sys.exit(1)

    # ========= 2️⃣ 输出文件准备 =========
    base_output_dir = Path(config.get("output_dir", "./output"))
    channel_output_dir = base_output_dir / channel / "info"
    channel_output_dir.mkdir(parents=True, exist_ok=True)

    download_archive_name = config.get("download_archive_name", "downloaded_ids.txt")
    metadata_json_name = config.get("metadata_json_name", "video_metadata.jsonl")

    archive_path = channel_output_dir / download_archive_name
    json_output_path = channel_output_dir / metadata_json_name

    print(f"📥 Processing channel: {channel} (Video scope: {start_index}:{end_index})")
    print(f"📁 Output path: {channel_output_dir}")
    print(f"📄 Download archive file: {archive_path}")
    print(f"🧾 Metadata output file: {json_output_path}")

    # ========= 3️⃣ yt-dlp 命令 =========
    index_range = f"{start_index}:{end_index}"
    command = [
        "yt-dlp",
        "-j",
        "-I", index_range,
        "--cookies", COOKIE_FILE,
        "--ignore-errors",
        "--download-archive", str(archive_path),
        f"https://www.youtube.com/@{channel}/videos"
    ]

    # ========= 4️⃣ 执行解析 =========
    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as proc, \
            open(json_output_path, "a", encoding="utf-8") as outfile:

        for line in proc.stdout:
            try:
                data = json.loads(line)

                filtered = {
                    "id": data.get("id"),
                    "channel_id": data.get("channel_id"),
                    "language": data.get("language"),
                    "title": data.get("title"),
                    "description": data.get("description"),
                    "tags": data.get("tags"),
                    "categories": data.get("categories"),
                    "media_type": data.get("media_type"),
                    "live_status": data.get("live_status"),
                    "duration": data.get("duration"),
                    "upload_date": data.get("upload_date"),
                    "view_count": data.get("view_count"),
                    "like_count": data.get("like_count")
                }

                # ========= 检测字幕 =========
                if sub_lang:
                    video_url = f"https://www.youtube.com/watch?v={filtered['id']}"
                    try:
                        result = subprocess.check_output(
                            f"yt-dlp --list-subs --cookies {COOKIE_FILE} --skip-download {video_url}",
                            shell=True,
                            universal_newlines=True
                        )

                        subtitles = get_subtitle_language(result)
                        filtered["subtitles"] = subtitles

                    except subprocess.CalledProcessError:
                        filtered["subtitles"] = []

                # ========= 写到 JSONL =========
                json.dump(filtered, outfile, ensure_ascii=False)
                outfile.write("\n")

                print(f"✅ Video saved ID: {filtered['id']}")

            except json.JSONDecodeError:
                print("⚠️ Skipped one invalid entry. JSON")
                continue


# ========= 🚀 入口 =========
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="抓取频道元数据 & 记录字幕")
    parser.add_argument("--config", type=str, default="./config/config.yaml", help="配置文件路径")
    args = parser.parse_args()

    process_channel_videos(config_path=args.config)
