#!/usr/bin/env python3
"""
早报生成脚本
功能：根据采集的数据生成每日早报
"""

import json
import os
import sys
from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader
import yaml

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fetch_rss import RSSFetcher


class MorningNewsGenerator:
    """早报生成器"""
    
    def __init__(self, config_path='config.yaml'):
        """初始化"""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.template_dir = self.config['morning_news']['template'].rsplit('/', 1)[0]
        self.template_file = self.config['morning_news']['template'].rsplit('/', 1)[-1]
        self.output_dir = self.config['morning_news']['output_dir']
        self.email_config = self.config.get('email', {})
        self.halo_config = self.config.get('halo', {})
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 设置Jinja2模板（关闭自动转义，因为我们要生成Markdown）
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=False
        )
    
    def load_raw_data(self, data_file=None):
        """加载原始数据"""
        if not data_file:
            # 获取最新的原始数据
            fetcher = RSSFetcher()
            raw_data = fetcher.get_latest_raw()
        else:
            with open(data_file, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
        
        return raw_data
    
    def categorize_articles(self, articles):
        """文章分类"""
        ai_keywords = ['ai', 'llm', 'gpt', 'machine learning', 'deep learning', 'neural', '模型', '大模型']
        tech_keywords = ['startup', '融资', '产品发布', '投资', '融资轮', '发布']
        
        ai_articles = []
        tech_articles = []
        other_articles = []
        
        for article in articles:
            text = f"{article.get('title', '')} {article.get('summary', '')}".lower()
            
            if any(kw in text for kw in ai_keywords):
                ai_articles.append(article)
            elif any(kw in text for kw in tech_keywords):
                tech_articles.append(article)
            else:
                other_articles.append(article)
        
        return {
            'ai': ai_articles,
            'tech': tech_articles,
            'other': other_articles
        }
    
    def generate_content(self, raw_data):
        """生成早报内容"""
        # 收集所有文章
        all_articles = []
        for source in raw_data.get('sources', []):
            all_articles.extend(source.get('articles', []))
        
        # 去重
        seen_links = set()
        unique_articles = []
        for article in all_articles:
            link = article.get('link', '')
            if link and link not in seen_links:
                seen_links.add(link)
                unique_articles.append(article)
        
        # 分类
        categorized = self.categorize_articles(unique_articles)
        
        # 提取分类
        categories = list(set(
            a.get('category', '未分类') 
            for a in unique_articles
        ))
        
        # 提取来源
        sources = list(set(
            a.get('source', '') 
            for a in unique_articles
        ))
        
        # 生成描述
        description = f"今日精选{len(unique_articles)}篇科技资讯，涵盖AI前沿、创投动态等。"
        
        # 准备模板数据
        today = datetime.now()
        date_str = today.strftime('%Y-%m-%d')
        
        data = {
            'title': self.config['morning_news']['title'],
            'subtitle': self.config['morning_news']['subtitle'],
            'date': today.isoformat(),
            'date_str': date_str,
            'date_formatted': today.strftime('%Y年%m月%d日 %A'),
            'articles': unique_articles[:10],  # 取前10篇
            'ai_articles': categorized['ai'][:5],
            'tech_articles': categorized['tech'][:5],
            'categories': categories,
            'sources': sources,
            'description': description,
            'quote': "在AI时代，最好的投资是学习本身。",
            'tools': [
                "🤗 HuggingFace - AI模型社区",
                "🔗 LangChain - AI应用开发框架",
                "📊 Weights & Biases - ML实验追踪",
                "🐍 Pandas - 数据分析利器"
            ]
        }
        
        return data
    
    def render_template(self, data):
        """渲染模板"""
        template = self.env.get_template(self.template_file)
        return template.render(data)
    
    def save(self, content, date_str=None):
        """保存早报"""
        if not date_str:
            date_str = datetime.now().strftime('%Y%m%d')
        
        filename = f"morning_news_{date_str}.md"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"💾 早报已保存: {filepath}")
        return filepath
    
    def generate(self, data_file=None, send_email_flag=True, use_processed=False):
        """生成完整早报"""
        print("\n📰 开始生成早报...")
        
        # 如果有已处理的数据，直接使用
        if use_processed:
            processed_dir = self.config['storage']['processed_data_dir']
            import glob
            processed_files = sorted(glob.glob(os.path.join(processed_dir, 'processed_*.json')), reverse=True)
            if processed_files:
                print("📥 使用已处理的最新数据...")
                with open(processed_files[0], 'r', encoding='utf-8') as f:
                    processed_data = json.load(f)
                
                # 直接使用已处理的数据
                data = self.generate_from_processed(processed_data)
            else:
                print("⚠️ 没有已处理的数据，使用原始数据...")
                raw_data = self.load_raw_data(data_file)
                data = self.generate_content(raw_data)
        else:
            # 加载数据
            print("📥 加载原始数据...")
            raw_data = self.load_raw_data(data_file)
            
            # 生成内容
            print("✍️ 生成早报内容...")
            data = self.generate_content(raw_data)
        
        # 渲染模板
        print("🎨 渲染模板...")
        content = self.render_template(data)
        
        # 保存
        print("💾 保存早报...")
        filepath = self.save(content)
        
        print(f"\n✅ 早报生成完成！")
        print(f"📄 文件: {filepath}")
        
        # 发送邮件（添加超时）
        if send_email_flag and self.email_config.get('enabled', False):
            import threading
            def send_mail():
                self.send_email_notification(filepath)
            t = threading.Thread(target=send_mail)
            t.daemon = True
            t.start()
            t.join(timeout=30)  # 最多等30秒
        
        return filepath, content
    
    def generate_from_processed(self, processed_data):
        """从已处理数据生成"""
        articles = processed_data.get('articles', [])
        
        # 分类
        categorized = {
            'ai': [],
            'tech': [],
            'other': []
        }
        
        for article in articles:
            topics = article.get('topics', [])
            if 'AI/机器学习' in topics or '数据科学' in topics:
                categorized['ai'].append(article)
            elif '科技创投' in topics:
                categorized['tech'].append(article)
            else:
                categorized['other'].append(article)
        
        today = datetime.now()
        date_str = today.strftime('%Y-%m-%d')
        
        return {
            'title': self.config['morning_news']['title'],
            'subtitle': self.config['morning_news']['subtitle'],
            'date': today.isoformat(),
            'date_str': date_str,
            'date_formatted': today.strftime('%Y年%m月%d日 %A'),
            'articles': articles[:10],
            'ai_articles': categorized['ai'][:5],
            'tech_articles': categorized['tech'][:5],
            'categories': list(set(a.get('category', '未分类') for a in articles)),
            'sources': list(set(a.get('source', '') for a in articles)),
            'description': f"今日精选{len(articles)}篇科技资讯，涵盖AI前沿、创投动态等。",
            'quote': "在AI时代，最好的投资是学习本身。",
            'tools': [
                "🤗 HuggingFace - AI模型社区",
                "🔗 LangChain - AI应用开发框架",
                "📊 Weights & Biases - ML实验追踪",
                "🐍 Pandas - 数据分析利器"
            ]
        }
    
    def send_email_notification(self, filepath):
        """发送邮件通知"""
        email_cfg = self.email_config
        
        if not email_cfg.get('enabled', False):
            return
        
        if not email_cfg.get('username') or not email_cfg.get('password'):
            print("\n⚠️ 邮件配置不完整，跳过邮件发送")
            return
        
        if not email_cfg.get('to_address'):
            print("\n⚠️ 未配置收件人地址，跳过邮件发送")
            return
        
        try:
            # 导入邮件模块
            from send_email import EmailSender
            
            sender = EmailSender()
            
            # 获取文件名
            filename = os.path.basename(filepath)
            
            print(f"\n📧 正在发送邮件到 {email_cfg['to_address']}...")
            
            success = sender.send_email(
                to_address=email_cfg['to_address'],
                markdown_file=filepath
            )
            
            if success:
                print("✅ 邮件发送成功！")
            else:
                print("⚠️ 邮件发送失败")
                
        except Exception as e:
            print(f"\n⚠️ 邮件发送异常: {e}")


def main():
    """主函数"""
    print("=" * 60)
    print("📰 每日AI科技早报 - 生成器")
    print("=" * 60)
    
    generator = MorningNewsGenerator()
    
    # 如果指定了数据文件
    data_file = sys.argv[1] if len(sys.argv) > 1 else None
    
    # 生成早报
    filepath, content = generator.generate(data_file)
    
    # 输出文件路径
    print(f"\n📄 生成的早报: {filepath}")


if __name__ == '__main__':
    main()
