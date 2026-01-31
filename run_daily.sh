#!/bin/bash
# 每日运行脚本

echo "========================================"
echo "🤖 每日AI科技早报 - 自动运行"
echo "========================================"
echo ""

# 切换到项目目录
cd "$(dirname "$0")"

# 1. 采集RSS
echo "📥 步骤1: 采集RSS资讯..."
python scripts/fetch_rss.py
echo ""

# 2. 生成早报
echo "📰 步骤2: 生成早报..."
python scripts/generate_morning_news.py
echo ""

echo "========================================"
echo "✅ 今日早报生成完成！"
echo "========================================"
