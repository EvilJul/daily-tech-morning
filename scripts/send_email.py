#!/usr/bin/env python3
"""
邮件发送脚本
功能：生成HTML格式邮件并发送
"""

import os
import sys
import smtplib
import argparse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml
import markdown


class EmailSender:
    """邮件发送器"""
    
    def __init__(self, config_path='config.yaml'):
        """初始化"""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.email_config = self.config.get('email', {})
        self.morning_news_config = self.config.get('morning_news', {})
        
        # 默认配置
        self.smtp_host = self.email_config.get('smtp_host', 'smtp.163.com')
        self.smtp_port = self.email_config.get('smtp_port', 465)
        self.username = self.email_config.get('username', '')
        self.password = self.email_config.get('password', '')
        self.use_tls = self.email_config.get('use_tls', False)
        self.use_ssl = self.email_config.get('use_ssl', True)
        self.from_name = self.email_config.get('from_name', 'AI科技早报')
        
        # 支持多邮箱配置
        to_addresses_raw = self.email_config.get('to_addresses', [])
        to_address_single = self.email_config.get('to_address', '')
        if to_addresses_raw:
            self.to_addresses = to_addresses_raw
        elif to_address_single:
            self.to_addresses = [to_address_single]
        else:
            self.to_addresses = []
    
    def generate_html_content(self, markdown_file):
        """将Markdown转换为HTML邮件内容"""
        try:
            with open(markdown_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取元数据（跳过YAML front matter）
            lines = content.split('\n')
            content_start = 0
            in_frontmatter = False
            
            # 跳过YAML front matter (--- ... ---)
            for i, line in enumerate(lines):
                if line.startswith('---'):
                    if not in_frontmatter:
                        in_frontmatter = True
                        content_start = i + 1
                    else:
                        content_start = i + 1
                    break
            
            # 提取正文内容
            body_content = '\n'.join(lines[content_start:])
            
            # 解析Markdown为HTML
            md = markdown.Markdown(
                extensions=[
                    'markdown.extensions.tables',  # 表格支持
                    'markdown.extensions.fenced_code',  # 代码块
                    'markdown.extensions.codehilite',  # 代码高亮
                    'markdown.extensions.toc',  # 目录
                ]
            )
            body_html = md.convert(body_content)
            
            # 提取标题和日期
            title = "AI科技早报"
            date_str = datetime.now().strftime('%Y年%m月%d日')
            
            for line in lines:
                if line.startswith('title:'):
                    title = line.replace('title:', '').strip().strip('"')
                if line.startswith('date:'):
                    date_str = line.replace('date:', '').strip().strip('"')
            
            # 生成完整HTML邮件
            html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        /* 基础样式 */
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
            line-height: 1.8;
            color: #2c3e50;
            background-color: #f5f6fa;
            margin: 0;
            padding: 0;
        }}
        
        /* 邮件容器 */
        .container {{
            max-width: 680px;
            margin: 0 auto;
            background-color: #ffffff;
        }}
        
        /* 头部 */
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: 600;
        }}
        .header .date {{
            margin-top: 10px;
            font-size: 14px;
            opacity: 0.9;
        }}
        
        /* 内容区域 */
        .content {{
            padding: 30px;
        }}
        
        /* 标题样式 */
        .content h2 {{
            color: #667eea;
            font-size: 20px;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
            margin-top: 30px;
            margin-bottom: 20px;
        }}
        .content h3 {{
            color: #333;
            font-size: 16px;
            margin-top: 25px;
            margin-bottom: 15px;
        }}
        
        /* 段落 */
        .content p {{
            margin: 15px 0;
            color: #444;
        }}
        
        /* 链接 */
        .content a {{
            color: #667eea;
            text-decoration: none;
            border-bottom: 1px dashed #667eea;
        }}
        .content a:hover {{
            border-bottom-style: solid;
        }}
        
        /* 原文链接按钮 */
        .read-more {{
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            text-decoration: none;
            font-size: 13px;
            margin-top: 10px;
        }}
        .read-more:hover {{
            opacity: 0.9;
        }}
        
        /* 表格样式 */
        .content table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: #f8f9fa;
            border-radius: 8px;
            overflow: hidden;
        }}
        .content table th,
        .content table td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #e9ecef;
        }}
        .content table th {{
            background: #667eea;
            color: white;
            font-weight: 500;
        }}
        .content table tr:last-child td {{
            border-bottom: none;
        }}
        
        /* 引用块 */
        .content blockquote {{
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            margin: 20px 0;
            padding: 15px 20px;
            color: #666;
        }}
        
        /* 列表 */
        .content ul, .content ol {{
            padding-left: 25px;
        }}
        .content li {{
            margin: 10px 0;
        }}
        
        /* 分隔线 */
        hr {{
            border: none;
            border-top: 1px solid #eee;
            margin: 30px 0;
        }}
        
        /* 文章卡片 */
        .article-card {{
            background: #f8f9fa;
            border-radius: 12px;
            padding: 20px;
            margin: 20px 0;
        }}
        .article-card h3 {{
            margin-top: 0;
            color: #333;
        }}
        
        /* 脚注 */
        .footnote {{
            font-size: 12px;
            color: #999;
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eee;
        }}
        
        /* 响应式 */
        @media (max-width: 600px) {{
            .container {{
                width: 100%;
            }}
            .header {{
                padding: 30px 20px;
            }}
            .content {{
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <p class="date">📅 {date_str}</p>
        </div>
        
        <div class="content">
            {body_html}
        </div>
        
        <div class="footnote">
            <p>🤖 由每日AI科技早报自动生成</p>
            <p>📧 每天早上9点准时推送</p>
        </div>
    </div>
</body>
</html>"""
            return html
            
        except Exception as e:
            print(f"❌ 生成HTML失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def send_email(self, to_address=None, subject=None, html_content=None, markdown_file=None):
        """发送邮件"""
        # 获取配置
        if not to_address:
            to_addresses = self.to_addresses
        else:
            to_addresses = [to_address]

        if not to_addresses:
            print("❌ 未配置收件人地址")
            return False

        if not html_content and markdown_file:
            html_content = self.generate_html_content(markdown_file)
        if not html_content:
            print("❌ 没有邮件内容")
            return False

        # 生成主题
        if not subject:
            date_str = datetime.now().strftime('%Y-%m-%d')
            subject = f"🤖 AI科技早报 - {date_str}"

        success_count = 0
        fail_count = 0

        for address in to_addresses:
            # 构建邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = Header(subject, 'utf-8')
            # QQ邮箱要求简单的From格式
            msg['From'] = self.username
            msg['To'] = address

            # 添加HTML内容
            part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(part)

            try:
                print(f"📧 正在发送邮件到 {address}...")

                if self.use_ssl:
                    server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
                else:
                    server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                    server.starttls()

                server.login(self.username, self.password)
                server.send_message(msg)
                server.quit()

                print(f"✅ 邮件发送成功！")
                success_count += 1

            except Exception as e:
                print(f"❌ 邮件发送失败到 {address}: {e}")
                fail_count += 1

        print(f"\n📊 发送结果: 成功 {success_count} 封, 失败 {fail_count} 封")
        return success_count > 0


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='发送AI科技早报邮件')
    parser.add_argument('--to', help='收件人邮箱')
    parser.add_argument('--subject', help='邮件主题')
    parser.add_argument('--file', help='早报Markdown文件路径')
    args = parser.parse_args()
    
    print("=" * 50)
    print("📧 AI科技早报 - 邮件发送")
    print("=" * 50)
    
    sender = EmailSender()
    
    # 检查邮件配置
    if not sender.email_config.get('enabled', False):
        print("⚠️ 邮件功能未在config.yaml中启用")
        return
    
    if not sender.username or not sender.password:
        print("❌ 请先配置邮箱账号和授权码")
        print("编辑 config.yaml 中的 email 部分")
        return
    
    # 发送邮件
    success = sender.send_email(
        to_address=args.to,
        subject=args.subject,
        markdown_file=args.file or sender.morning_news_config.get('output_dir') + '/morning_news_' + datetime.now().strftime('%Y%m%d') + '.md'
    )
    
    if success:
        print("\n🎉 邮件已发送！")
    else:
        print("\n❌ 邮件发送失败")


if __name__ == '__main__':
    main()
