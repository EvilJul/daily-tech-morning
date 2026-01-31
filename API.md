# API 接口文档

## 概述

- **基础URL**: `http://localhost:49999`
- **响应格式**: JSON
- **编码**: UTF-8

---

## 早报相关

### 1. 获取早报列表

**GET** `/api/reports`

**响应示例**:
```json
[
  {
    "date": "2026-01-31",
    "title": "🤖 AI科技早报 - 2026年01月31日 Friday",
    "filename": "morning_news_20260131.md"
  }
]
```

---

### 2. 获取统计数据

**GET** `/api/stats`

**响应示例**:
```json
{
  "total_reports": 5,
  "total_articles": 320,
  "last_update": "2026-01-31T00:10:00.000000"
}
```

---

### 3. 获取特定早报内容

**GET** `/data/published/{filename}`

**示例**: `GET /data/published/morning_news_20260131.md`

**响应**: Markdown文件内容

---

## AI配置相关

### 4. 获取AI配置

**GET** `/api/ai-config`

**响应示例**:
```json
{
  "provider": "siliconflow",
  "model": "deepseek-ai/DeepSeek-V3.2",
  "base_url": "https://api.siliconflow.cn/v1",
  "api_key": "sk-xxx",
  "max_tokens": 1024,
  "temperature": 0.7
}
```

---

### 5. 保存AI配置

**POST** `/api/ai-config`

**请求体**:
```json
{
  "provider": "siliconflow",
  "model": "deepseek-ai/DeepSeek-V3.2",
  "base_url": "https://api.siliconflow.cn/v1",
  "api_key": "sk-xxx"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "AI配置已保存"
}
```

---

### 6. 测试AI连接

**POST** `/api/ai-test`

**请求体**:
```json
{
  "provider": "siliconflow",
  "model": "deepseek-ai/DeepSeek-V3.2",
  "base_url": "https://api.siliconflow.cn/v1",
  "api_key": "sk-xxx"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "siliconflow 连接成功！"
}
```

---

## 邮件配置相关

### 7. 获取邮件配置

**GET** `/api/email-config`

**响应示例**:
```json
{
  "enabled": true,
  "smtp_host": "smtp.qq.com",
  "smtp_port": 465,
  "username": "1419648701@qq.com",
  "password": "xxx",
  "from_name": "AI科技早报",
  "to_addresses": ["jinhua.tian@outlook.com"]
}
```

> ⚠️ 密码仅在配置文件中有效，API不返回密码

---

### 8. 保存邮件配置

**POST** `/api/email-config`

**请求体**:
```json
{
  "smtp_host": "smtp.qq.com",
  "smtp_port": 465,
  "username": "1419648701@qq.com",
  "password": "xxx",
  "to_addresses": ["jinhua.tian@outlook.com"]
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "邮件配置已保存"
}
```

---

### 9. 发送测试邮件

**POST** `/api/send-email`

**响应示例**:
```json
{
  "success": true,
  "message": "邮件已发送至 1 个收件人"
}
```

---

## 生成相关

### 10. 手动生成早报

**POST** `/api/generate`

**响应示例**:
```json
{
  "success": true,
  "message": "开始生成早报"
}
```

> ⚠️ 此接口启动后台任务，不会等待完成

---

### 11. 获取生成状态

**GET** `/api/generate/status`

**响应示例** (生成中):
```json
{
  "running": true,
  "logs": "📰 开始生成早报...\n📥 加载原始数据...\n✍️ 生成早报内容..."
}
```

**响应示例** (已完成):
```json
{
  "running": false,
  "logs": "✅ 早报生成完成！"
}
```

---

## 静态文件

### 12. 预览页面

**GET** `/` 或 `/index.html`

**响应**: HTML页面

---

### 13. marked.js 库

**GET** `/marked.min.js`

**响应**: marked.js库文件

---

## 错误处理

### 错误响应格式

```json
{
  "success": false,
  "message": "错误描述"
}
```

### 常见错误码

| 状态码 | 说明 |
|--------|------|
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 启动服务器

```bash
cd /Users/tian/clawd/daily-tech-morning
python3 scripts/preview_server.py 49999
```

**默认端口**: 49999

---

## 前端集成示例

```javascript
// 获取早报列表
fetch('/api/reports')
  .then(r => r.json())
  .then(data => {
    data.forEach(report => {
      console.log(report.date, report.title);
    });
  });

// 保存AI配置
fetch('/api/ai-config', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    provider: 'siliconflow',
    model: 'deepseek-ai/DeepSeek-V3.2',
    api_key: 'your-api-key'
  })
});
```
