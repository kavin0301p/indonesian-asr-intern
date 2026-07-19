#!/bin/bash

# ========= 🧱 基本配置 =========
WORKSPACE_ROOT="/content/drive/MyDrive/GigaSpeech2/AudioDataCrawler-main/Youtube-Download"
DEFAULT_CHANNEL_ID="madangowri"
GLM4_API_KEY="fba65bf39c56486d80626fe0fac938c5.RUu9pPua4XZPypeE"
COOKIE_FILE="/content/drive/MyDrive/GigaSpeech2/AudioDataCrawler-main/Youtube-Download/config/cookies.txt"

# ========= ⚙️ 全局 CONFIG 设置 =========
CONFIG_NAME="config_ta"   # 所选取的设置
CONFIG_PATH="/content/drive/MyDrive/GigaSpeech2/AudioDataCrawler-main/Youtube-Download/config/${CONFIG_NAME}.yaml"

# ========= 📐 解析参数 =========
stage=4
CHANNEL_ID="$DEFAULT_CHANNEL_ID"

while [[ $# -gt 0 ]]; do
  case $1 in
    --stage)
      stage="$2"
      shift 2
      ;;
    --channel_id)
      CHANNEL_ID="$2"
      shift 2
      ;;
    *)
      echo "❌ 未知参数: $1"
      exit 1
      ;;
  esac
done

echo "🔧 当前执行阶段: stage $stage"
echo "📺 当前处理频道: $CHANNEL_ID"
echo "🗂️ 使用的 CONFIG: $CONFIG_PATH"

# ========= 📦 Stage 0: 安装依赖 =========
if [ "$stage" == 0 ]; then
  echo "📦 安装依赖包..."
  pip install -U git+https://github.com/yt-dlp/yt-dlp.git
  pip install -U zhipuai xlsxwriter
  sudo apt-get install -y dos2unix jq
  echo "📁 创建工作目录..."
  mkdir -p "$WORKSPACE_ROOT"
  if [ ! -f "$COOKIE_FILE" ]; then
    echo "❌ 缺失 cookies.txt，请参考文档说明，使用 Cookie Editor 导出并上传到：$COOKIE_FILE"
    exit 1
  else
    echo "✅ 已找到 cookies.txt"
  fi
fi

# ========= 📥 Stage 1: 抓取频道元数据 =========
if [ "$stage" == 1 ]; then
  echo "📥 抓取频道 $CHANNEL_ID 的元数据..."
  python scripts/extract_channels.py --config "$CONFIG_PATH"
fi

# ========= 🎯 Stage 2: 筛选元数据 =========
if [ "$stage" == 2 ]; then
  echo "🎯 筛选频道 $CHANNEL_ID 的元数据..."
  python scripts/filter.py --config "$CONFIG_PATH"
fi

# ========= 🎧 Stage 3: 下载音频 =========
if [ "$stage" == 3 ]; then
  echo "⬇️ 下载频道 $CHANNEL_ID 的音频和字幕..."
  python scripts/download.py --config "$CONFIG_PATH"
fi

# ========= ✂️ Stage 4: 按字幕切分音频 =========
if [ "$stage" == 4 ]; then
  echo "✂️ 按字幕切分音频..."
  python scripts/slice.py --config "$CONFIG_PATH"
fi

echo "✅ 阶段 $stage 执行完毕"
