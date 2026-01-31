# 📘 Halo博客 API 操作指南

> 每日AI科技早报 - Halo博客集成配置文档

⚠️ **注意**：Halo博客发布功能目前暂未启用，需要获取API Token后才能使用。

---

## 📋 目录

1. [准备工作](#1-准备工作)
2. [Halo 2.x API访问方式](#2-halo-2x-api访问方式)
3. [配置config.yaml](#3-配置configyaml)
4. [API端点说明](#4-api端点说明)
5. [常见问题](#5-常见问题)
6. [测试验证](#6-测试验证)

---

## 1. 准备工作

### 1.1 确认Halo版本

本配置适用于 **Halo 2.x** 版本

```
访问: https://your-halo-domain/admin
在后台页面底部查看版本号
```

### 1.2 Halo 2.x API特点

Halo 2.x 使用 **Spring Security + OAuth2** 框架：
- 控制台API (Console API) 需要认证
- 公共API (Public API) 不需要认证
- 认证方式：OAuth2 Client Credentials

---

## 2. Halo 2.x API访问方式

### 方式一：通过后台设置（推荐）

**注意**：Halo 2.x 后台没有直接的"API令牌"菜单，需要通过配置实现：

1. **登录Halo后台**
   ```
   访问: https://your-halo-domain/admin
   ```

2. **启用API访问**
   - 进入 **系统** → **安全设置**
   - 确保 **API访问** 已启用

### 方式二：通过配置文件

在 Halo 的配置文件中添加 OAuth2 客户端配置：

编辑 `~/.halo2/application.yaml` 或启动参数：

```bash
# Docker 部署时添加启动参数
docker run -d --name halo \
  -p 8090:8090 \
  -v ~/.halo2:/root/.halo2 \
  halohub/halo:2.22 \
  --spring.security.oauth2.authorizationserver.client.registration.halo-client.client-id=halo-client \
  --spring.security.oauth2.authorizationserver.client.registration.halo-client.client-secret=secret \
  --spring.security.oauth2.authorizationserver.client.registration.halo-client.authorization-grant-types=client_credentials \
  --spring.security.oauth2.authorizationserver.client.registration.halo-client.client-authentication-methods=client_secret_basic
```

### 方式三：使用用户名密码认证（临时方案）

对于简单的API测试，可以使用用户名密码获取访问令牌：

```bash
# 获取访问令牌
curl -X POST 'https://your-halo-domain/oauth2/token' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'grant_type=password' \
  -d 'username=你的用户名' \
  -d 'password=你的密码' \
  -d 'client_id=halo-client' \
  -d 'client_secret=secret'
```

**响应示例**：
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

### 方式四：Halo官方插件

Halo官方提供了 **"API Tokens"** 插件：

1. 进入 **应用市场** → **插件**
2. 搜索安装 **API Tokens** 插件
3. 在插件设置中生成Token

---

---

## 3. 配置config.yaml

编辑项目根目录下的 `config.yaml`：

```yaml
# 🔧 Halo博客配置
halo:
  enabled: true  # 设置为true启用（需要先获取API Token）
  url: "https://your-halo-domain"
  access_token: "your-access-token"
  category_id: 1
  tag_ids: [1, 2, 3]
  post_status: "DRAFT"
  allow_comment: true
```

### ⚠️ 启用步骤

1. 按照本文档获取 `access_token`
2. 在 `config.yaml` 中配置Halo相关选项
3. 将 `halo.enabled` 设置为 `true`
4. 运行发布命令：`python3 scripts/publish_to_halo.py`

**当前状态**：`halo.enabled: false`（暂未启用）

### 3.1 获取分类ID

```bash
# 列出所有分类（需要认证）
curl -X GET 'https://your-halo-domain/api/v1-0/categories' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

### 3.2 获取标签ID

```bash
# 列出所有标签（需要认证）
curl -X GET 'https://your-halo-domain/api/v1-0/tags' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

---

## 4. API端点说明

### 4.1 文章相关API

| 操作 | 方法 | 端点 |
|------|------|------|
| 创建文章 | POST | `/api/v1-0/posts` |
| 更新文章 | PUT | `/api/v1-0/posts/{id}` |
| 获取文章 | GET | `/api/v1-0/posts/{id}` |
| 删除文章 | DELETE | `/api/v1-0/posts/{id}` |
| 列出文章 | GET | `/api/v1-0/posts` |

**创建文章请求示例**：
```bash
curl -X POST 'https://your-halo-domain/api/v1-0/posts' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "AI科技早报 - 2026年1月29日",
    "slug": "morning-news-2026-01-29",
    "content": "<p>这是早报内容</p>",
    "status": "DRAFT",
    "allowComment": true
  }'
```

### 4.2 分类API

| 操作 | 方法 | 端点 |
|------|------|------|
| 列出分类 | GET | `/api/v1-0/categories` |
| 获取分类 | GET | `/api/v1-0/categories/{id}` |
| 创建分类 | POST | `/api/v1-0/categories` |

### 4.3 标签API

| 操作 | 方法 | 端点 |
|------|------|------|
| 列出标签 | GET | `/api/v1-0/tags` |
| 获取标签 | GET | `/api/v1-0/tags/{id}` |
| 创建标签 | POST | `/api/v1-0/tags` |

### 4.4 公共API（无需认证）

Halo提供了一些公共API：

| 操作 | 方法 | 端点 |
|------|------|------|
| 列出文章(公开) | GET | `/api/v1-0/single/posts` |
| 获取页面 | GET | `/api/v1-0/single/pages/{slug}` |

---

## 5. 常见问题

### Q1: 后台没有API令牌生成选项？

**原因**：Halo 2.x 的API令牌需要通过插件或配置实现

**解决方法**：
1. 安装 **"API Tokens"** 插件（应用市场搜索）
2. 或使用用户名密码方式获取临时Token

### Q2: 401 Unauthorized？

**原因**：Token无效或过期

**解决方法**：
1. 检查Token格式：`Authorization: Bearer {token}`
2. 尝试重新获取Token
3. 检查Token是否过期

### Q3: 403 Forbidden？

**原因**：权限不足

**解决方法**：
1. 检查OAuth2客户端配置
2. 确保客户端有正确的权限

### Q4: API端点返回404？

**原因**：Halo版本或配置问题

**解决方法**：
1. 确认Halo版本是2.x
2. 检查API访问是否在后台启用
3. 确认URL格式正确（不要有多余/）

---

## 6. 测试验证

### 6.1 测试Token有效性

```bash
# 替换 YOUR_DOMAIN 和 YOUR_TOKEN
curl -X GET 'https://YOUR_DOMAIN/api/v1-0/posts?size=1' \
  -H 'Authorization: Bearer YOUR_TOKEN'
```

**成功响应**：
```json
{
  "page": 1,
  "size": 1,
  "total": 10,
  "items": [...]
}
```

### 6.2 测试发布文章

```bash
curl -X POST 'https://YOUR_DOMAIN/api/v1-0/posts' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "测试文章",
    "slug": "test-article",
    "content": "<p>这是一篇测试文章</p>",
    "status": "DRAFT"
  }'
```

---

## 📝 配置检查清单

在运行发布脚本前，确认以下项目：

- [ ] Halo版本是 2.x
- [ ] API访问已在后台启用（如果需要）
- [ ] 已获取有效的Access Token
- [ ] config.yaml 中的URL正确
- [ ] Token格式正确（Bearer {token}）
- [ ] 网络可访问Halo服务

---

## 🔗 相关链接

- **Halo官网**: https://halo.run
- **Halo文档**: https://docs.halo.run
- **Halo社区**: https://bbs.halo.run
- **GitHub**: https://github.com/halo-dev/halo

---

## ⚠️ 重要提醒

由于Halo 2.x的API认证方式较复杂，建议：

1. **优先使用插件方式**：安装 "API Tokens" 插件
2. **测试环境先行**：先在测试环境验证API功能
3. **保护Token**：不要将Token提交到公开仓库

**当前状态**：Halo发布功能暂未启用，需要获取API Token后才能使用。

---

## 📝 配置检查清单

在运行发布脚本前，确认以下项目：

- [ ] Halo版本是 2.x
- [ ] API访问已在后台启用（如果需要）
- [ ] 已获取有效的Access Token
- [ ] config.yaml 中的 `halo.enabled` 设置为 `true`
- [ ] config.yaml 中的URL正确
- [ ] Token格式正确（Bearer {token}）
- [ ] 网络可访问Halo服务

---

**启用Halo发布后，运行命令：**
```bash
python3 scripts/publish_to_halo.py
```

---

> 📅 文档创建日期: 2026-01-29
> 📝 最后更新: 2026-01-29
> ⚠️ Halo发布功能暂未启用
