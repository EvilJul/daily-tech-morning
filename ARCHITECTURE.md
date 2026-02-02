# 每日AI科技早报 - 技术架构文档

> 版本: v1.2.0  
> 更新日期: 2026-02-02  
> 作者: Clawdbot

---

## 目录

1. [项目概述](#1-项目概述)
2. [系统架构](#2-系统架构)
3. [数据流设计](#3-数据流设计)
4. [核心模块详解](#4-核心模块详解)
5. [技术栈](#5-技术栈)
6. [配置说明](#6-配置说明)
7. [部署指南](#7-部署指南)
8. [API文档](#8-api文档)
9. [常见问题](#9-常见问题)
10. [扩展指南](#10-扩展指南)

---

## 1. 项目概述

### 1.1 项目简介

**每日AI科技早报**是一个自动化资讯聚合与分发系统，每日定时采集AI科技领域最新资讯，经过智能整理后通过邮件和Halo博客自动推送给用户。

### 1.2 核心功能

| 功能 | 描述 | 状态 |
|------|------|------|
| RSS自动采集 | 从多个科技RSS源自动抓取最新资讯 | ✅ |
| AI内容整理 | 使用大模型智能摘要和分类 | ✅ |
| HTML邮件发送 | 渲染精美格式的邮件模板 | ✅ |
| Halo博客发布 | 自动发布到Halo 2.x博客系统 | ✅ |
| 定时任务 | 每天7点自动执行完整流程 | ✅ |
| 本地预览 | Web界面预览生成的早报 | ✅ |
| 多用户支持 | 支持配置多个邮件收件人 | ✅ |

### 1.3 数据统计

- **RSS数据源**: 7个
- **日均采集文章**: 50-100篇
- **生成早报文章**: 8-10篇
- **覆盖分类**: AI前沿、科技创投、创投动态

---

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          每日AI科技早报系统架构                               │
└─────────────────────────────────────────────────────────────────────────────┘

                              ⏰ 定时任务触发 (每日 7:00)
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           第一层: 数据采集层                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ HuggingFace  │  │   OpenAI     │  │   ArXiv AI   │  │    36氪      │    │
│  │   Blog       │  │   Blog       │  │              │  │              │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                 │                 │                 │            │
│         └─────────────────┴─────────────────┴─────────────────┘            │
│                                     │                                        │
│                                     ▼                                        │
│                    ┌────────────────────────────────────┐                   │
│                    │      fetch_rss.py                  │                   │
│                    │  • RSS/Atom 解析                   │                   │
│                    │  • 关键词过滤                      │                   │
│                    │  • 日期去重                        │                   │
│                    │  • 内容清洗                        │                   │
│                    └────────────────────────────────────┘                   │
│                                     │                                        │
│                                     ▼                                        │
│                    ┌────────────────────────────────────┐                   │
│                    │    data/raw/raw_YYYYMMDD_*.json    │                   │
│                    └────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           第二层: 内容处理层                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    generate_morning_news.py                         │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │    │
│  │  │  数据加载    │  │  AI摘要生成  │  │  分类与模板渲染          │  │    │
│  │  │  load_data  │  │  LLM API    │  │  categorize + Jinja2     │  │    │
│  │  └──────────────┘  └──────────────┘  └──────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                     │                                        │
│                                     ▼                                        │
│  ┌──────────────────────┐  ┌──────────────────────┐                        │
│  │  处理后数据          │  │  生成的早报          │                        │
│  │  data/processed/     │  │  data/published/     │                        │
│  │  enhanced_*.json     │  │  morning_news_*.md   │                        │
│  └──────────────────────┘  └──────────────────────┘                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    ▼                                 ▼
┌───────────────────────────────────────────┐   ┌───────────────────────────────────────────┐
│           第三层: 邮件发送层               │   │          第三层: Halo发布层              │
├───────────────────────────────────────────┤   ├───────────────────────────────────────────┤
│  ┌─────────────────────────────────────┐  │   │  ┌─────────────────────────────────────┐  │
│  │          send_email.py              │  │   │  │       publish_to_halo.py            │  │
│  │  • SMTP SSL连接                     │  │   │  │  • Halo 2.x API认证                 │  │
│  │  • HTML模板渲染                     │  │   │  │  • Snapshots API创建快照            │  │
│  │  • 多收件人支持                     │  │   │  │  • Posts API发布文章               │  │
│  │  • 响应式邮件设计                   │  │   │  │  • 分类/标签管理                   │  │
│  └─────────────────────────────────────┘  │   │  └─────────────────────────────────────┘  │
│                    │                       │   │                    │                     │
│                    ▼                       │   │                    ▼                     │
│         📧 jinhua.tian@outlook.com        │   │      https://www.fushengshare.xyz/      │
│         📧 user2@example.com (可选)       │   │         /archives/ai-morning-news-*     │
└───────────────────────────────────────────┘   └───────────────────────────────────────────┘
                    │                                 │
                    └────────────────┬────────────────┘
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           第四层: 预览服务层                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    preview_server.py (端口8080)                     │    │
│  │  • HTTP服务器 - 提供Web界面                                         │    │
│  │  • REST API - 早报列表、详情、统计                                  │    │
│  │  • 静态文件服务 - CSS/JS/图片                                      │    │
│  │  • 局域网访问支持 - 手机也能预览                                    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                     │                                        │
│                                     ▼                                        │
│                    ┌────────────────────────────────────┐                   │
│                    │         http://localhost:8080      │                   │
│                    │    http://192.168.x.x:8080 (局域网) │                   │
│                    └────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 模块依赖关系

```
                    ┌─────────────────┐
                    │   daily_tech_   │
                    │   morning.sh    │ ←── Cron定时任务调用
                    └────────┬────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                         publish.py                              │
│                   (统一发布入口脚本)                             │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  功能:                                                    │   │
│  │  • 生成早报 ──→ send_email() ──→ 邮件发送               │   │
│  │  • 生成早报 ──→ publish_to_halo() ──→ Halo发布          │   │
│  │  • 支持单独执行: --email-only, --halo-only               │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
         │                              │                              │
         ▼                              ▼                              ▼
┌─────────────────┐      ┌─────────────────────────────┐      ┌─────────────────┐
│ generate_       │      │         send_email.py       │      │ publish_        │
│ morning_news.py │ ───→ │  • generate_html_content() │ ───→ │ to_halo.py      │
│                 │      │  • send_email()            │      │                 │
│ • load_data()   │      │  • MIMEMultipart          │      │ • create_       │
│ • generate()    │      │  • SMTP_SSL               │      │   snapshot()    │
│ • categorize()  │      │                           │      │ • publish()     │
│ • render()      │      │                           │      │                 │
└─────────────────┘      └─────────────────────────────┘      └─────────────────┘
         │                              │                              │
         ▼                              ▼                              ▼
┌─────────────────┐      ┌─────────────────────────────┐      ┌─────────────────┐
│  fetch_rss.py   │      │  templates/                 │      │  Halo 2.x       │
│                 │      │  morning_news.md.j2         │      │  REST API       │
│ • fetch_all()   │      │  (Jinja2模板)               │      │                 │
│ • get_latest()  │      │                             │      │                 │
└─────────────────┘      └─────────────────────────────┘      └─────────────────┘
```

---

## 3. 数据流设计

### 3.1 数据生命周期

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              数据生命周期                                    │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  RSS源   │───→│ 原始数据 │───→│ 处理数据 │───→│ 早报文件 │───→│ 邮件/Halo│
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
     │              │               │               │               │
     │              │               │               │               │
     ▼              ▼               ▼               ▼               ▼
  外部网站    data/raw/        data/          data/           用户/博客
               *.json          processed/     published/
                              *.json         *.md
```

### 3.2 文件命名规范

| 文件类型 | 命名格式 | 示例 | 说明 |
|---------|---------|------|------|
| 原始数据 | `raw_YYYYMMDD_HHMMSS.json` | `raw_20260202_073001.json` | RSS采集的原始文章 |
| 处理数据 | `enhanced_YYYYMMDD_HHMMSS.json` | `enhanced_20260202_073010.json` | AI处理后的摘要 |
| 早报文件 | `morning_news_YYYYMMDD.md` | `morning_news_20260202.md` | 生成的Markdown早报 |

### 3.3 数据结构

#### 3.3.1 原始数据结构 (raw_*.json)

```json
{
  "fetch_time": "2026-02-02T07:30:01.123456",
  "sources": [
    {
      "name": "HuggingFace Blog",
      "url": "https://huggingface.co/blog/feed.xml",
      "category": "ai",
      "articles": [
        {
          "title": "Introducing Daggr",
          "link": "https://huggingface.co/blog/daggr",
          "summary": "Chain apps programmatically...",
          "published": "2026-02-01T10:00:00Z",
          "author": "HuggingFace Team"
        }
      ]
    }
  ]
}
```

#### 3.3.2 早报数据结构 (morning_news_*.md)

```yaml
---
title: "🤖 AI科技早报"
date: 2026-02-02T07:30:08.524573
slug: morning-news-2026-02-02
categories:
  - 科技资讯
  - AI前沿
tags:
  - 每日简报
  - 科技
  - AI
---

## AI前沿

### Introducing Daggr: Chain apps programmatically, inspect visually

<p>摘要内容...</p>

[阅读原文](https://huggingface.co/blog/daggr)

---

## 科技创投

### 阿里系前高管出任机器人租赁平台...

<p>摘要内容...</p>

[阅读原文](https://36kr.com/p/xxx)

---

> 在AI时代，最好的投资是学习本身。
>
> 由 [浮生随记](https://www.fushengshare.xyz) 每日自动推送
```

---

## 4. 核心模块详解

### 4.1 RSS采集模块 (fetch_rss.py)

**功能**: 从多个RSS源采集最新科技资讯

**主要类**: `RSSFetcher`

```python
class RSSFetcher:
    def __init__(self, config_path='config.yaml')
        """初始化加载配置"""
    
    def fetch_all(self) -> dict
        """采集所有配置的RSS源"""
    
    def fetch_single_source(self, source: dict) -> list
        """采集单个RSS源"""
    
    def get_latest_raw(self) -> dict
        """获取最新的原始数据文件"""
    
    def check_keywords(self, text: str, include=True) -> bool
        """检查关键词过滤"""
    
    def clean_text(self, text: str) -> str
        """清理文本内容"""
```

**采集流程**:
```
1. 遍历配置的RSS源
2. 解析RSS/Atom feed
3. 过滤包含关键词的文章
4. 清理HTML标签和特殊字符
5. 按日期排序去重
6. 保存到JSON文件
```

### 4.2 早报生成模块 (generate_morning_news.py)

**功能**: 加载数据、生成AI摘要、分类、渲染模板

**主要类**: `MorningNewsGenerator`

```python
class MorningNewsGenerator:
    def __init__(self, config_path='config.yaml')
        """初始化加载配置和Jinja2模板"""
    
    def load_raw_data(self, data_file=None) -> dict
        """加载原始数据，自动采集今日数据"""
    
    def generate_content(self, raw_data: dict) -> dict
        """生成早报内容"""
    
    def generate_from_processed(self, processed_data: dict) -> dict
        """从已处理数据生成"""
    
    def categorize_articles(self, articles: list) -> dict
        """文章分类 (AI/科技创投/其他)"""
    
    def render_template(self, data: dict) -> str
        """渲染Jinja2模板"""
    
    def generate(self, data_file=None) -> tuple
        """生成完整早报 (文件路径, 内容)"""
    
    def send_email_notification(self, filepath: str) -> bool
        """发送邮件通知"""
```

**分类逻辑**:
```python
AI关键词 = ['ai', 'llm', 'gpt', 'machine learning', '深度学习', '模型', '大模型']
科技创投关键词 = ['startup', '融资', '产品发布', '投资', '融资轮', '发布']

def categorize(article):
    text = article.title + " " + article.summary
    if any(kw in text.lower() for kw in AI关键词):
        return 'ai'
    elif any(kw in text.lower() for kw in 科技创投关键词):
        return 'tech'
    else:
        return 'other'
```

### 4.3 邮件发送模块 (send_email.py)

**功能**: 生成HTML邮件并通过SMTP发送

**主要类**: `EmailSender`

```python
class EmailSender:
    def __init__(self, config_path='config.yaml')
        """初始化邮件配置"""
    
    def generate_html_content(self, markdown_file: str) -> str
        """将Markdown转换为HTML邮件"""
    
    def send_email(self, to_address=None, subject=None, 
                   html_content=None, markdown_file=None) -> bool
        """发送邮件给指定收件人"""
```

**邮件模板特性**:
- 响应式设计 (移动端/桌面端适配)
- 紫色渐变主题
- 代码高亮支持
- 表格样式
- 链接新标签打开

### 4.4 Halo发布模块 (publish_to_halo.py)

**功能**: 将早报发布到Halo 2.x博客系统

**主要类**: `HaloPublisher`

```python
class HaloPublisher:
    def __init__(self, config_path='config.yaml')
        """初始化Halo配置"""
    
    def get_auth_header(self) -> dict
        """获取认证头"""
    
    async def create_snapshot(self, content: dict) -> str
        """创建内容快照 (Snapshots API)"""
    
    async def publish(self, content: dict) -> dict
        """发布文章到Halo"""
    
    async def get_categories(self) -> list
        """获取分类列表"""
    
    async def get_category_id_by_slug(self, slug: str) -> str
        """通过slug获取分类ID"""
```

**Halo API流程**:
```
1. Halo 2.x 使用 Snapshots API 管理内容版本
2. 创建Post前需先创建Snapshot
3. Post引用Snapshot的ID
4. 发布状态由Halo后台控制

POST /apis/content.halo.run/v1alpha1/snapshots
  → 创建内容快照

POST /apis/content.halo.run/v1alpha1/posts
  → 发布文章，引用快照ID
```

### 4.5 统一发布入口 (publish.py)

**功能**: 整合邮件和Halo发布，支持并行执行

**主要类**: `MorningNewsPublisher`

```python
class MorningNewsPublisher:
    def __init__(self, config_path='config.yaml')
        """初始化"""
    
    async def send_email(self, content: dict) -> bool
        """发送邮件"""
    
    async def publish_to_halo(self, content: dict) -> bool
        """发布到Halo"""
    
    async def publish_all(self, content: dict) -> dict
        """并行发送到所有渠道"""
```

**命令行参数**:
```bash
python publish.py [选项]

选项:
  --date, -d         指定日期 (YYYYMMDD)
  --email-only, -e   只发送邮件
  --halo-only, -H    只发布到Halo
  --categories, -c   显示分类列表
  --config, -f       配置文件路径
```

### 4.6 预览服务器模块 (preview_server.py)

**功能**: 提供Web预览界面和REST API

**主要类**: `PreviewHandler`

**API端点**:

| 端点 | 方法 | 描述 |
|------|------|------|
| `/` | GET | Web预览页面 |
| `/api/reports` | GET | 获取早报列表 |
| `/api/stats` | GET | 获取统计信息 |
| `/api/ai-config` | GET/POST | AI配置管理 |
| `/api/email-config` | GET/POST | 邮件配置管理 |
| `/api/generate` | POST | 手动触发生成 |
| `/api/generate/status` | GET | 获取生成状态 |
| `/api/send-email` | POST | 发送邮件 |

---

## 5. 技术栈

### 5.1 核心技术

| 类别 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **运行时** | Python | 3.11+ | 核心开发语言 |
| **模板引擎** | Jinja2 | - | Markdown模板渲染 |
| **Markdown解析** | Python-Markdown | - | 邮件内容解析 |
| **HTML解析** | BeautifulSoup4 | - | RSS内容清洗 |
| **HTTP客户端** | requests | - | RSS采集 |
| **异步HTTP** | aiohttp | - | Halo API调用 |
| **RSS解析** | feedparser | - | RSS/Atom解析 |
| **日期处理** | python-dateutil | - | 日期解析 |
| **YAML解析** | PyYAML | - | 配置文件解析 |

### 5.2 邮件技术

| 组件 | 说明 |
|------|------|
| smtplib | Python标准库 - SMTP协议 |
| email.mime | Python标准库 - MIME邮件构建 |
| SSL/TLS | 安全邮件传输 |

### 5.3 前端技术

| 组件 | 说明 |
|------|------|
| HTML5 | 页面结构 |
| CSS3 | 样式 (渐变、动画、响应式) |
| JavaScript (ES6+) | 交互逻辑 |
| marked.js | Markdown渲染 |
| Fetch API | 后端通信 |

### 5.4 部署技术

| 组件 | 说明 |
|------|------|
| crontab | Linux定时任务 |
| virtualenv | Python虚拟环境 |
| HTTP服务器 | SimpleHTTPRequestHandler |

---

## 6. 配置说明

### 6.1 配置文件结构

```yaml
# ==========================================
# 每日AI科技早报 - 配置文件
# ==========================================

# 邮件配置
email:
  enabled: true                          # 是否启用邮件功能
  smtp_host: smtp.qq.com                 # SMTP服务器
  smtp_port: 465                         # SMTP端口 (SSL)
  username: your-email@qq.com            # 发件人邮箱
  password: your-auth-code               # 授权码
  from_name: AI科技早报                  # 发件人名称
  to_addresses:                          # 收件人列表
    - jinhua.tian@outlook.com
    - user2@example.com                  # 可添加多个
  use_ssl: true                          # 使用SSL
  use_tls: false                         # 使用TLS

# Halo博客配置
halo:
  enabled: true                          # 是否启用Halo发布
  url: https://www.fushengshare.xyz      # Halo博客地址
  admin_token: your-halo-admin-token     # Halo管理员Token
  category_slug: tech-news               # 文章分类slug

# RSS源配置
rss_sources:
  - name: HuggingFace Blog
    url: https://huggingface.co/blog/feed.xml
    category: ai
    enabled: true
  
  - name: OpenAI Blog
    url: https://openai.com/blog/rss.xml
    category: ai
    enabled: true
  
  - name: ArXiv AI
    url: http://export.arxiv.org/api/query?search_query=cat:cs.AI
    category: ai
    enabled: true
  
  - name: 36氪
    url: https://36kr.com/feed
    category: tech
    enabled: true
  
  - name: TechCrunch
    https://techcrunch.com/feed/
    category: tech
    enabled: true

# 关键词过滤配置
keywords:
  include:                               # 必须包含的关键词
    - AI
    - 人工智能
    - Machine Learning
    - 融资
    - 融资轮
  exclude:                               # 排除的关键词
    - 广告
    - 推广

# 存储配置
storage:
  raw_data_dir: data/raw                 # 原始数据目录
  processed_data_dir: data/processed     # 处理数据目录
  output_dir: data/published             # 输出的早报目录

# 早报模板配置
morning_news:
  title: "🤖 AI科技早报"
  subtitle: "每天早上7点，准时推送AI科技最新资讯"
  template: templates/morning_news.md.j2

# 个人博客配置
blog:
  name: 浮生随记
  url: https://www.fushengshare.xyz

# AI模型配置 (用于生成摘要)
ai:
  provider: openai                       # AI提供商
  api_key: your-api-key                  # API密钥
  model: gpt-4o-mini                     # 模型名称
  base_url: https://api.openai.com/v1    # API地址
```

### 6.2 环境变量

| 变量名 | 说明 | 必填 |
|--------|------|------|
| `EMAIL_PASSWORD` | 邮箱授权码 | ✅ |
| `HALO_ADMIN_TOKEN` | Halo管理员Token | ✅ |
| `AI_API_KEY` | AI模型API密钥 | ✅ |

---

## 7. 部署指南

### 7.1 环境要求

- 操作系统: macOS / Linux / WSL
- Python: 3.11+
- Git: 任意版本
- 网络: 能够访问RSS源和SMTP服务器

### 7.2 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/EvilJul/daily-tech-morning.git
cd daily-tech-morning

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或: .\venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置项目
cp config.yaml.example config.yaml
# 编辑 config.yaml 填入配置

# 5. 测试运行
python scripts/fetch_rss.py        # 测试数据采集
python scripts/generate_morning_news.py  # 测试生成早报
python scripts/send_email.py       # 测试发送邮件
```

### 7.3 配置定时任务

```bash
# 编辑crontab
crontab -e

# 添加定时任务 (每天7点执行)
0 7 * * * /path/to/daily-tech-morning/scripts/daily_tech_morning.sh >> ~/.clawdbot/logs/daily-tech-morning.log 2>&1
```

### 7.4 启动预览服务器

```bash
# 启动预览服务器 (端口8080)
python scripts/preview_server.py 8080

# 访问地址
# 本地: http://localhost:8080
# 局域网: http://192.168.x.x:8080
```

---

## 8. API文档

### 8.1 预览服务器API

#### 获取早报列表

```http
GET /api/reports
```

**响应**:
```json
[
  {
    "date": "2026-02-02",
    "title": "🤖 AI科技早报",
    "filename": "morning_news_20260202.md"
  }
]
```

#### 获取统计数据

```http
GET /api/stats
```

**响应**:
```json
{
  "total_reports": 3,
  "total_articles": 28,
  "sources_count": 7,
  "last_update": "2026-02-02T07:30:01Z"
}
```

#### 手动触发生成

```http
POST /api/generate
```

**响应**:
```json
{
  "success": true,
  "message": "生成任务已启动"
}
```

#### 获取生成状态

```http
GET /api/generate/status
```

**响应**:
```json
{
  "status": "running",
  "logs": "📰 开始生成早报...\n📥 加载原始数据..."
}
```

#### 发送邮件

```http
POST /api/send-email
Content-Type: application/json

{
  "to_address": "user@example.com"
}
```

**响应**:
```json
{
  "success": true,
  "message": "邮件发送成功"
}
```

---

## 9. 常见问题

### Q1: 邮件发送失败

**问题**: `SMTP authentication failed`

**解决**:
1. 检查`config.yaml`中的`username`和`password`
2. QQ邮箱使用授权码而非密码
3. 确保SMTP服务已开启

### Q2: RSS采集无数据

**问题**: 采集返回0篇文章

**解决**:
1. 检查RSS源URL是否可访问
2. 检查关键词过滤配置
3. 查看日志确认是否有网络问题

### Q3: Halo发布失败

**问题**: 返回500错误

**解决**:
1. 检查`admin_token`是否有效
2. 确认`category_slug`存在
3. 检查Halo服务器状态

### Q4: 早报内容重复

**问题**: 今日早报与昨日相同

**解决**:
1. 确保定时任务执行`publish.py`而非单独的`generate_morning_news.py`
2. 检查是否有今日的原始数据文件

---

## 10. 扩展指南

### 10.1 添加新的RSS源

在`config.yaml`中添加:

```yaml
rss_sources:
  - name: 新数据源名称
    url: https://example.com/feed.xml
    category: ai  # 或 tech
    enabled: true
```

### 10.2 添加新的邮件收件人

在`config.yaml`中修改:

```yaml
email:
  to_addresses:
    - user1@example.com
    - user2@example.com
    - user3@example.com  # 添加新收件人
```

### 10.3 修改邮件模板

编辑`templates/morning_news.md.j2`:

```jinja2
---
title: "{{ title }}"
date: {{ date }}
---

## AI前沿

{% for article in ai_articles[:5] %}
### {{ article.title }}

{{ article.summary }}

[阅读原文]({{ article.link }})

---
{% endfor %}
```

### 10.4 添加新的发布渠道

参考`send_email.py`的实现，创建新的发布模块:

```python
class NewPublisher:
    async def publish(self, content: dict) -> bool:
        """发布到新渠道"""
        # 实现发布逻辑
        pass
```

然后在`publish.py`中集成:

```python
if self.new_channel_enabled:
    tasks.append(self.publish_to_new_channel(content))
```

---

## 更新日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.2.0 | 2026-02-02 | 添加Halo发布、本地预览、多用户支持 |
| v1.1.0 | 2026-01-31 | 添加HTML邮件渲染、响应式设计 |
| v1.0.0 | 2026-01-31 | 初始版本，基础RSS采集和邮件发送 |

---

## 许可证

MIT License

---

*文档由 Clawdbot 自动生成和维护*
