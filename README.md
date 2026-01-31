# 🤖 AI科技早报

每日自动采集并发送的AI科技资讯早报。

## ✨ 功能特点

- 📥 **自动RSS采集** - 从多个科技源自动抓取最新资讯
- ✍️ **AI内容整理** - 使用LLM智能整理摘要
- 🎨 **精美HTML邮件** - 渲染美观的邮件模板
- ⏰ **定时自动发送** - 每天9点准时推送
- 📊 **详细日志记录** - 支持日志归档和错误追踪

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Git

### 安装部署

```bash
# 克隆项目
git clone https://github.com/EvilJul/daily-tech-morning.git
cd daily-tech-morning

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置邮件
cp config.yaml.example config.yaml
# 编辑 config.yaml 填入邮箱配置
```

### 配置说明

编辑 `config.yaml`:

```yaml
email:
  enabled: true
  smtp_host: smtp.qq.com
  smtp_port: 465
  username: your-email@qq.com
  password: your-auth-code
  from_name: AI科技早报
  to_address: recipient@outlook.com
  use_ssl: true

rss_sources:
  - name: HuggingFace Blog
    url: https://huggingface.co/blog/feed.xml
    category: ai
    enabled: true
```

### 本地测试

```bash
# 生成今日早报
python scripts/generate_morning_news.py

# 发送测试邮件
python scripts/send_email.py --file data/published/morning_news_$(date +%Y%m%d).md
```

### 定时任务设置

```bash
# 添加定时任务（每天9点执行）
crontab -e

# 添加以下行：
0 9 * * * /path/to/daily-tech-morning/scripts/daily_tech_morning.sh >> ~/.clawdbot/logs/daily-tech-morning.log 2>&1
```

## 📁 项目结构

```
daily-tech-morning/
├── config.yaml          # 配置文件
├── requirements.txt     # Python依赖
├── README.md            # 项目说明
├── CHANGELOG.md         # 更新日志
├── scripts/             # 脚本目录
│   ├── fetch_rss.py         # RSS抓取
│   ├── process_content.py   # 内容处理
│   ├── generate_morning_news.py  # 早报生成
│   └── send_email.py        # 邮件发送
├── templates/           # 邮件模板
│   └── morning_news.md.j2
├── data/                # 数据目录
│   ├── raw/             # 原始数据
│   ├── processed/       # 处理后数据
│   └── published/       # 发布的早报
├── web_preview/         # 网页预览
└── venv/                # 虚拟环境
```

## 📝 使用指南

### RSS源配置

在 `config.yaml` 中配置RSS源:

```yaml
rss_sources:
  - name: OpenAI Blog
    url: https://openai.com/blog/rss.xml
    category: ai
    enabled: true
  - name: 36氪
    url: https://36kr.com/feed
    category: tech
    enabled: true
```

### 查看日志

```bash
# 查看今日日志
cat ~/.clawdbot/logs/daily-tech-morning.log

# 实时查看
tail -f ~/.clawdbot/logs/daily-tech-morning.log
```

## 🛠️ 维护

### 更新依赖

```bash
pip install -r requirements.txt
```

### 查看帮助

```bash
python scripts/send_email.py --help
```

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📧 联系

- GitHub: [@EvilJul](https://github.com/EvilJul)
- 项目地址: https://github.com/EvilJul/daily-tech-morning

---

🤖 由 Clawdbot 自动维护 | 每天早上9点准时推送
