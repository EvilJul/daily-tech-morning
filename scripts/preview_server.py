#!/usr/bin/env python3
"""
预览服务器
功能：提供Web预览界面和API
"""

import http.server
import socketserver
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml


class PreviewHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP处理器"""

    def __init__(self, *args, **kwargs):
        # 加载配置
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.yaml')
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        super().__init__(*args, **kwargs)

    def do_GET(self):
        """处理GET请求"""
        path = self.path

        # API: 早报列表
        if path == '/api/reports':
            self.send_reports()
            return

        # API: 统计数据
        if path == '/api/stats':
            self.send_stats()
            return

        # API: 大模型配置
        if path == '/api/ai-config':
            self.send_ai_config()
            return

        # API: 邮件配置
        if path == '/api/email-config':
            self.send_email_config()
            return

        # API: 生成状态
        if path == '/api/generate/status':
            self.send_generate_status()
            return

        # API: 特定早报
        if path.startswith('/api/report/'):
            filename = path.split('/')[-1]
            self.send_report(filename)
            return

        # 静态文件服务
        if path == '/' or path == '/index.html':
            path = '/web_preview/index.html'
        
        # 获取项目根目录
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # 确定文件路径
        if path.startswith('/web_preview/'):
            # web_preview目录下的文件
            file_path = os.path.join(base_dir, path.lstrip('/'))
        elif path.startswith('/data/published/'):
            # 早报数据文件
            file_path = os.path.join(base_dir, path.lstrip('/'))
        elif path.startswith('/marked.min.js'):
            # marked.js库文件
            file_path = os.path.join(base_dir, 'web_preview', 'marked.min.js')
        elif path.startswith('/css/') or path.startswith('/js/') or path.startswith('/images/'):
            # 其他静态文件
            file_path = os.path.join(base_dir, 'web_preview', path)
        else:
            file_path = os.path.join(base_dir, path.lstrip('/'))

        if os.path.exists(file_path) and os.path.isfile(file_path):
            self.send_file(file_path)
        else:
            self.send_error(404, 'File not found')

    def do_POST(self):
        """处理POST请求"""
        path = self.path

        # API: 手动生成早报
        if path == '/api/generate':
            self.handle_generate()
            return

        # API: 保存大模型配置
        if path == '/api/ai-config':
            self.save_ai_config()
            return

        # API: 测试AI连接
        if path == '/api/ai-test':
            self.test_ai_connection()
            return

        # API: 保存邮件配置
        if path == '/api/email-config':
            self.save_email_config()
            return

        # API: 发送邮件
        if path == '/api/send-email':
            self.send_email()
            return

        self.send_error(404, 'Not found')
    
    def send_reports(self):
        """发送早报列表"""
        reports = []
        published_dir = self.config['morning_news']['output_dir']
        
        for filename in sorted(os.listdir(published_dir), reverse=True):
            if not filename.startswith('morning_news_'):
                continue
            
            date_str = filename.replace('morning_news_', '').replace('.md', '')
            
            # 读取标题
            title = 'AI科技早报'
            filepath = os.path.join(published_dir, filename)
            with open(filepath, 'r') as f:
                for line in f:
                    if line.startswith('title:'):
                        title = line.replace('title:', '').strip().strip('"')
                        break
            
            reports.append({
                'date': f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}",
                'title': title,
                'filename': filename
            })
        
        self.send_json(reports)
    
    def send_stats(self):
        """发送统计数据"""
        stats = {
            'total_reports': 0,
            'total_articles': 0,
            'last_update': datetime.now().isoformat()
        }
        
        published_dir = self.config['morning_news']['output_dir']
        processed_dir = self.config['storage']['processed_data_dir']
        
        # 统计早报
        for f in os.listdir(published_dir):
            if f.startswith('morning_news_'):
                stats['total_reports'] += 1
        
        # 统计文章
        for f in os.listdir(processed_dir):
            if f.startswith('processed_'):
                filepath = os.path.join(processed_dir, f)
                with open(filepath, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    stats['total_articles'] += data.get('total_articles', 0)
        
        self.send_json(stats)
    
    def send_report(self, filename):
        """发送特定早报"""
        published_dir = self.config['morning_news']['output_dir']
        filepath = os.path.join(published_dir, filename)

        if os.path.exists(filepath):
            self.send_file(filepath, 'text/markdown')
        else:
            self.send_error(404, 'Report not found')

    def send_ai_config(self):
        """发送AI配置"""
        ai_config = self.config.get('ai', {})
        self.send_json({
            'provider': ai_config.get('provider', 'openrouter'),
            'model': ai_config.get('model', 'openai/gpt-4o-mini'),
            'base_url': ai_config.get('base_url', ''),
            'api_key': ai_config.get('api_key', ''),  # 返回配置中的API Key
            'max_tokens': ai_config.get('max_tokens', 500),
            'temperature': ai_config.get('temperature', 0.7)
        })

    def save_ai_config(self):
        """保存AI配置"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            config_data = json.loads(post_data.decode('utf-8'))

            # 更新配置
            if 'ai' not in self.config:
                self.config['ai'] = {}

            self.config['ai']['provider'] = config_data.get('provider', 'openrouter')
            self.config['ai']['model'] = config_data.get('model', 'openai/gpt-4o-mini')
            self.config['ai']['base_url'] = config_data.get('base_url', '')
            if config_data.get('api_key'):
                self.config['ai']['api_key'] = config_data.get('api_key')
            self.config['ai']['max_tokens'] = config_data.get('max_tokens', 500)
            self.config['ai']['temperature'] = config_data.get('temperature', 0.7)

            # 保存配置
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.yaml')
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, allow_unicode=True, indent=2)

            self.send_json({'success': True, 'message': 'AI配置已保存'})
        except Exception as e:
            self.send_json({'success': False, 'message': str(e)})

    def test_ai_connection(self):
        """测试AI连接"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            config_data = json.loads(post_data.decode('utf-8'))

            provider = config_data.get('provider', 'openrouter')
            api_key = config_data.get('api_key', '')
            model = config_data.get('model', 'openai/gpt-4o-mini')
            base_url = config_data.get('base_url', '').strip()

            # 默认Base URL（国内）
            default_urls = {
                'openai': 'https://api.openai.com/v1',
                'openrouter': 'https://openrouter.ai/api/v1',
                'minimax': 'https://api.minimax.chat/v1',
                'deepseek': 'https://api.deepseek.com',
                'siliconflow': 'https://api.siliconflow.cn/v1',
                'qwen': 'https://dashscope.aliyuncs.com/api/v1'
            }

            url = base_url or default_urls.get(provider, '')
            if not url:
                self.send_json({'success': False, 'message': f'未知提供商: {provider}'})
                return

            # 测试不同提供商
            if provider == 'openai':
                import requests
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                data = {
                    "model": model,
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 5
                }
                response = requests.post(url, headers=headers, json=data, timeout=10)

            elif provider in ['openrouter', 'deepseek']:
                import requests
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                if provider == 'openrouter':
                    headers["HTTP-Referer"] = "https://github.com/EvilJul/daily-tech-morning"
                data = {
                    "model": model,
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 5
                }
                response = requests.post(url, headers=headers, json=data, timeout=10)

            elif provider == 'minimax':
                import requests
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                data = {
                    "model": model,
                    "messages": [{"role": "user", "content": "test"}],
                    "tokens_to_generate": 5
                }
                response = requests.post(f"{url}/text/chatcompletion_v2", headers=headers, json=data, timeout=10)

            elif provider == 'siliconflow':
                import requests
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                data = {
                    "model": model,
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 5
                }
                response = requests.post(f"{url}/chat/completions", headers=headers, json=data, timeout=10)

            elif provider == 'qwen':
                import requests
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                data = {
                    "model": model,
                    "input": {"messages": [{"role": "user", "content": "test"}]},
                    "parameters": {"max_tokens": 5}
                }
                response = requests.post(f"{url}/services/aigc/text-generation/generation", headers=headers, json=data, timeout=10)

            else:
                self.send_json({'success': False, 'message': f'暂不支持该提供商: {provider}'})
                return

            if response.status_code == 200:
                self.send_json({'success': True, 'message': f'{provider} 连接成功！'})
            else:
                self.send_json({'success': False, 'message': f'连接失败: {response.status_code}'})

        except Exception as e:
            self.send_json({'success': False, 'message': str(e)})

    def send_email_config(self):
        """发送邮件配置"""
        email_config = self.config.get('email', {})
        # 兼容to_address和to_addresses两种写法
        to_addresses = email_config.get('to_addresses', [])
        if not to_addresses:
            to_addr = email_config.get('to_address', '')
            if to_addr:
                to_addresses = [to_addr] if isinstance(to_addr, str) else to_addr
        self.send_json({
            'enabled': email_config.get('enabled', False),
            'smtp_host': email_config.get('smtp_host', 'smtp.163.com'),
            'smtp_port': email_config.get('smtp_port', 465),
            'username': email_config.get('username', ''),
            'password': email_config.get('password', ''),  # 返回配置中的密码
            'from_name': email_config.get('from_name', 'AI科技早报'),
            'to_addresses': to_addresses
        })

    def save_email_config(self):
        """保存邮件配置"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            config_data = json.loads(post_data.decode('utf-8'))

            # 更新配置
            if 'email' not in self.config:
                self.config['email'] = {}

            self.config['email']['enabled'] = config_data.get('enabled', False)
            self.config['email']['smtp_host'] = config_data.get('smtp_host', 'smtp.163.com')
            self.config['email']['smtp_port'] = config_data.get('smtp_port', 465)
            self.config['email']['username'] = config_data.get('username', '')
            if config_data.get('password'):
                self.config['email']['password'] = config_data.get('password')
            self.config['email']['from_name'] = config_data.get('from_name', 'AI科技早报')
            self.config['email']['to_addresses'] = config_data.get('to_addresses', [])

            # 保存配置
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.yaml')
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, allow_unicode=True, indent=2)

            self.send_json({'success': True, 'message': '邮件配置已保存'})
        except Exception as e:
            self.send_json({'success': False, 'message': str(e)})

    def send_email(self):
        """发送邮件"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from email.header import Header
            
            email_config = self.config.get('email', {})
            
            # 获取配置
            smtp_host = email_config.get('smtp_host', 'smtp.163.com')
            smtp_port = email_config.get('smtp_port', 465)
            username = email_config.get('username', '')
            password = email_config.get('password', '')
            from_name = email_config.get('from_name', 'AI科技早报')
            
            # 收件人
            to_addresses = email_config.get('to_addresses', [])
            to_addr_single = email_config.get('to_address', '')
            if not to_addresses and to_addr_single:
                to_addresses = [to_addr_single]
            
            if not to_addresses:
                self.send_json({'success': False, 'message': '没有配置收件人地址'})
                return
            
            # 获取最新的早报
            published_dir = self.config['morning_news']['output_dir']
            report_files = sorted([f for f in os.listdir(published_dir) if f.startswith('morning_news_')], reverse=True)
            if not report_files:
                self.send_json({'success': False, 'message': '没有找到早报文件'})
                return
            
            latest_report = report_files[0]
            report_path = os.path.join(published_dir, latest_report)
            
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取标题
            title = 'AI科技早报'
            for line in content.split('\n'):
                if line.startswith('title:'):
                    title = line.replace('title:', '').strip().strip('"')
                    break
            
            # 生成HTML邮件
            import re
            content_clean = re.sub(r'^---[\s\S]*?---', '', content)
            
            # 简单转换Markdown到HTML
            html_body = content_clean
            html_body = html_body.replace('# ', '</h1>').replace('\n## ', '</h2>').replace('\n### ', '</h3>')
            html_body = html_body.replace('[阅读原文](', '<a href="').replace(')" target="_blank">阅读原文</a>')
            html_body = html_body.replace('\n>', '\n<blockquote>').replace('\n\n', '</blockquote>\n')
            
            html_content = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #667eea; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
        h2 {{ color: #764ba2; margin-top: 30px; }}
        blockquote {{ background: #f5f5f5; border-left: 4px solid #667eea; padding: 10px 15px; margin: 15px 0; }}
        a {{ color: #667eea; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f0f0ff; }}
    </style>
</head>
<body>
{content.replace('---[\s\S]*?---', '').replace('#', '</h1>').replace('\n##', '</h2>').replace('\n###', '</h3>').replace('[阅读原文](', '<a href="').replace(')', '" target="_blank">阅读原文</a>')}
</body>
</html>
'''
            # 发送邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = Header(title, 'utf-8')
            msg['From'] = f'{from_name} <{username}>'
            msg['To'] = ', '.join(to_addresses)
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            
            if smtp_port == 465:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port)
            else:
                server = smtplib.SMTP(smtp_host, smtp_port)
                server.starttls()
            
            server.login(username, password)
            server.sendmail(username, to_addresses, msg.as_string())
            server.quit()
            
            self.send_json({'success': True, 'message': f'邮件已发送至 {len(to_addresses)} 个收件人'})
        except Exception as e:
            self.send_json({'success': False, 'message': str(e)})

    def handle_generate(self):
        """处理手动生成请求"""
        try:
            # 启动生成进程
            import subprocess
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            # 后台执行生成脚本
            subprocess.Popen(
                [sys.executable, f'{base_dir}/scripts/generate_morning_news.py'],
                cwd=base_dir,
                stdout=open(f'{base_dir}/data/generate.log', 'w'),
                stderr=subprocess.STDOUT
            )

            self.send_json({'success': True, 'message': '开始生成早报'})
        except Exception as e:
            self.send_json({'success': False, 'message': str(e)})

    def send_generate_status(self):
        """发送生成状态"""
        try:
            log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data/generate.log')
            if os.path.exists(log_path):
                with open(log_path, 'r') as f:
                    logs = f.read()
                self.send_json({
                    'running': True,
                    'logs': logs[-5000:]  # 只返回最后5000字符
                })
            else:
                self.send_json({'running': False, 'logs': ''})
        except Exception as e:
            self.send_json({'running': False, 'logs': str(e)})

    def send_json(self, data):
        """发送JSON响应"""
        response = json.dumps(data, ensure_ascii=False, indent=2)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))
    
    def send_file(self, filepath, content_type=None):
        """发送文件"""
        if content_type is None:
            if filepath.endswith('.html'):
                content_type = 'text/html'
            elif filepath.endswith('.json'):
                content_type = 'application/json'
            elif filepath.endswith('.css'):
                content_type = 'text/css'
            elif filepath.endswith('.js'):
                content_type = 'application/javascript'
            else:
                content_type = 'application/octet-stream'
        
        with open(filepath, 'rb') as f:
            content = f.read()
        
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', len(content))
        self.end_headers()
        self.wfile.write(content)
    
    def log_message(self, format, *args):
        """日志"""
        print(f"[Preview] {args[0]}")


def run_server(port=8080):
    """运行服务器"""
    print("=" * 60)
    print("🌐 每日AI科技早报 - 预览服务器")
    print("=" * 60)
    print(f"\n🚀 服务器启动中...")
    print(f"📍 访问地址: http://0.0.0.0:{port}")
    print(f"🔗 预览页面: http://0.0.0.0:{port}/")
    print(f"🔗 局域网: http://192.168.31.97:{port}")
    print(f"📊 API端点: http://0.0.0.0:{port}/api/reports")
    print("\n按 Ctrl+C 停止服务器")
    print("=" * 60)

    # 绑定到0.0.0.0以允许局域网访问
    with socketserver.TCPServer(("0.0.0.0", port), PreviewHandler) as httpd:
        httpd.serve_forever()


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(port)
