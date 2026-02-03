#!/usr/bin/env python3
"""
RSS采集脚本
功能：从多个RSS源采集最新资讯
"""

import feedparser
import requests
import yaml
import json
import os
import sys
from datetime import datetime
from dateutil import parser as date_parser
from urllib.parse import urlparse
from pathlib import Path
import time
import urllib3
import ssl

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 创建不验证SSL的上下文
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class RSSFetcher:
    """RSS采集器"""
    
    def __init__(self, config_path=None):
        """初始化加载配置"""
        if config_path is None:
            script_dir = Path(__file__).parent.parent
            config_path = script_dir / "config.yaml"
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.sources = self.config['rss_sources']
        self.keywords = self.config['keywords']
        self.raw_data_dir = self.config['storage']['raw_data_dir']
        
        # 确保目录存在
        os.makedirs(self.raw_data_dir, exist_ok=True)
        
        # 会话用于HTTP请求
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'DailyTechMorning/1.0'
        })
    
    def parse_date(self, date_str):
        """解析日期字符串"""
        if not date_str:
            return datetime.now().isoformat()
        
        try:
            dt = date_parser.parse(date_str)
            return dt.isoformat()
        except:
            return datetime.now().isoformat()
    
    def check_keywords(self, text, include=True):
        """检查关键词"""
        text_lower = text.lower()
        
        if include:
            # 检查是否包含需要的关键词
            for keyword in self.keywords.get('include', []):
                if keyword.lower() in text_lower:
                    return True
            return False
        else:
            # 检查是否应该排除
            for keyword in self.keywords.get('exclude', []):
                if keyword.lower() in text_lower:
                    return False
            return True
    
    def clean_text(self, text):
        """清理文本"""
        if not text:
            return ""
        # 移除多余空白
        text = ' '.join(text.split())
        # 移除特殊字符
        text = text.replace('\xa0', ' ')
        return text.strip()
    
    def fetch_single_source(self, source):
        """采集单个RSS源"""
        name = source['name']
        url = source['url']
        category = source.get('category', 'tech')
        
        print(f"📥 采集: {name}...")
        
        try:
            # 使用requests获取RSS内容（禁用SSL验证）
            response = self.session.get(url, timeout=30, verify=False)
            response.raise_for_status()
            
            # 使用feedparser解析内容
            feed = feedparser.parse(response.content)
            
            if feed.bozo:
                print(f"  ⚠️ 解析警告: {feed.bozo_exception}")
            
            entries = []
            for entry in feed.entries[:15]:  # 取前15条
                # 获取摘要
                summary = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
                content = getattr(entry, 'content', [{}])[0].get('value', summary) if hasattr(entry, 'content') else summary
                
                # 构建文章信息
                article = {
                    'title': self.clean_text(entry.get('title', '')),
                    'link': entry.get('link', ''),
                    'summary': self.clean_text(summary[:500]),  # 限制长度
                    'content': self.clean_text(content[:2000]),
                    'published': self.parse_date(entry.get('published', '')),
                    'updated': self.parse_date(entry.get('updated', '')),
                    'author': entry.get('author', ''),
                    'source': name,
                    'category': category,
                    'tags': [tag.term for tag in getattr(entry, 'tags', [])],
                    'fetched_at': datetime.now().isoformat()
                }
                
                # 关键词过滤
                text_to_check = f"{article['title']} {article['summary']}"
                if self.check_keywords(text_to_check, include=True):
                    if self.check_keywords(text_to_check, include=False):
                        entries.append(article)
            
            print(f"  ✅ 获取 {len(entries)} 篇相关文章")
            return {
                'source': name,
                'url': url,
                'category': category,
                'articles': entries,
                'fetched_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"  ❌ 采集失败: {e}")
            return {
                'source': name,
                'url': url,
                'category': category,
                'articles': [],
                'error': str(e),
                'fetched_at': datetime.now().isoformat()
            }
    
    def fetch_all(self):
        """采集所有RSS源"""
        print(f"\n🤖 开始采集RSS源... ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n")
        
        results = []
        for source in self.sources:
            if source.get('enabled', True):
                result = self.fetch_single_source(source)
                results.append(result)
                time.sleep(1)  # 避免请求过快
        
        # 保存原始数据
        output_file = os.path.join(
            self.raw_data_dir,
            f"raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'fetched_at': datetime.now().isoformat(),
                'sources': results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 原始数据已保存: {output_file}")
        
        # 统计
        total_articles = sum(len(r.get('articles', [])) for r in results)
        print(f"\n📊 采集统计:")
        print(f"   总源数: {len(results)}")
        print(f"   总文章: {total_articles}")
        
        return results
    
    def get_latest_raw(self):
        """获取最新的原始数据文件"""
        files = sorted([
            f for f in os.listdir(self.raw_data_dir) 
            if f.startswith('raw_') and f.endswith('.json')
        ])
        
        if not files:
            return None
        
        latest_file = os.path.join(self.raw_data_dir, files[-1])
        with open(latest_file, 'r', encoding='utf-8') as f:
            return json.load(f)


def main():
    """主函数"""
    print("=" * 60)
    print("🤖 每日AI科技早报 - RSS采集器")
    print("=" * 60)
    
    fetcher = RSSFetcher()
    results = fetcher.fetch_all()
    
    return results


if __name__ == '__main__':
    main()
