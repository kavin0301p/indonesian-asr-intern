import json
import yaml
import logging
from pathlib import Path
import argparse

logging.basicConfig(level=logging.WARNING, format="%(message)s")


def is_any_a_in_b(list_a, list_b):
    """
    Determine whether at least one element in list_a is present in list_b (case-insensitive).
    """
    normalized_set_b = set(str(item).lower() for item in list_b)
    return any(str(item).lower() in normalized_set_b for item in list_a)


def filter_info_file(config_path, info_file):
    # ==== 📄 加载配置 ====
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    filter_cfg = config.get("filter", {})

    enable_language_filter = filter_cfg.get("enable_language_filter", False)
    target_language_abbr = filter_cfg.get("target_language_abbr", [])

    enable_duration_filter = filter_cfg.get("enable_duration_filter", False)
    min_duration = filter_cfg.get("min_duration", 0)
    max_duration = filter_cfg.get("max_duration", 999999)

    enable_like_count_filter = filter_cfg.get("enable_like_count_filter", False)
    min_like_count = filter_cfg.get("min_like_count", 0)

    filter_no_subtitle = filter_cfg.get("filter_no_subtitle", False)
    filter_no_manual_subtitle = filter_cfg.get("filter_no_manual_subtitle", False)

    # === 输出新文件名 ===
    output_file = Path(info_file).with_name(
        Path(info_file).stem + "-filtered.jsonl"
    )

    with open(info_file, encoding="utf-8", errors="ignore") as f1, \
         open(output_file, "w", encoding="utf-8") as f2:

        for line_num, line in enumerate(f1, 1):
            try:
                info = json.loads(line)
            except json.JSONDecodeError:
                logging.warning(f"❌ Skipping: Line {line_num} is not valid JSON.")
                continue

            if enable_language_filter:
                if not is_any_a_in_b([info.get("language")], target_language_abbr):
                    logging.warning(f"❌ Skipping: Language '{info.get('language')}' is not in {target_language_abbr}")
                    continue

            if enable_duration_filter:
                duration = info.get("duration", 0)
                if not (min_duration <= duration <= max_duration):
                    logging.warning(f"❌ Skipped: Duration {duration} is not within [{min_duration}, {max_duration}]")
                    continue

            if enable_like_count_filter:
                like_count = info.get("like_count")
                if like_count is not None and like_count < min_like_count:
                    logging.warning(f"❌ Skipped: Like count {like_count} is less than {min_like_count}")
                    continue

            subtitles = info.get("subtitles", [])
            if filter_no_subtitle:
                if not subtitles:
                    logging.warning("❌ Skipped: No subtitles (subtitles list is empty)")
                    continue

            if filter_no_manual_subtitle:
                has_manual = any(sub.get("type") == "manual" for sub in subtitles)
                if not has_manual:
                    logging.warning("❌Skip: No manual subtitles")
                    continue

            fields_to_keep = [
                "channel_id",
                "id",
                "title",
                "description",
                "duration",
                "upload_date",
                "like_count",
                "language",
                "subtitles"
            ]
            filtered_info = {field: info.get(field) for field in fields_to_keep}
            f2.write(json.dumps(filtered_info, ensure_ascii=False) + "\n")

    print(f"✅ Filtering complete, new file output:{output_file}")


# ========= 🚀 入口 =========
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="过滤 JSONL 元数据文件")
    parser.add_argument("--config", type=str, required=True, help="YAML 配置文件路径")
    args = parser.parse_args()

    config_path = args.config

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    channel = config.get("channel")
    if not channel:
        raise ValueError("❌ The `channel` field is missing from the configuration.")

    info_file = f"/content/drive/MyDrive/GigaSpeech2/id/raw_audio/Mono/{channel}/info/video_metadata.jsonl"

    filter_info_file(config_path=config_path, info_file=info_file)
