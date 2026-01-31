#!/usr/bin/env python3
"""
搜索脚本
功能：搜索历史早报和文章
"""

import os
import sys
import json
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml


class SearchEngine:
    """搜索引擎"""
    
    def __init__(self, config_path='config.yaml'):
        """初始化"""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.published_dir = self.config['morning_news']['output_dir']
        self.processed_dir = self.config['storage']['processed_data_dir']
    
    def search_articles(self, keyword, limit=20):
        """搜索文章"""
        results = []
        
        # 搜索processed数据
        for filename in sorted(os.listdir(self.processed_dir), reverse=True):
            if not filename.startswith('processed_'):
                continue
            
            filepath = os.path.join(self.processed_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for article in data.get('articles', []):
                text = f"{article.get('title', '')} {article.get('summary', '')} {article.get('tags', [])}"
                if keyword.lower() in text.lower():
                    results.append({
                        'title': article.get('title', ''),
                        'summary': article.get('short_summary', article.get('summary', ''))[:300],
                        'source': article.get('source', ''),
                        'date': data.get('processed_at', '')[:10],
                        'link': article.get('link', ''),
                        'tags': article.get('tags', [])[:5]
                    })
                    
                    if len(results) >= limit:
                        return results
        
        return results
    
    def search_reports(self, keyword, limit=10):
        """搜索早报"""
        results = []
        
        for filename in sorted(os.listdir(self.published_dir), reverse=True):
            if not filename.startswith('morning_news_'):
                continue
            
            filepath = os.path.join(self.published_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if keyword.lower() in content.lower():
                date_str = filename.replace('morning_news_', '').replace('.md', '')
                results.append({
                    'date': date_str,
                    'filepath': filepath,
                    'preview': content[:500]
                })
            
            if len(results) >= limit:
                break
        
        return results
    
    def list_reports(self, limit=10):
        """列出早报"""
        reports = []
        
        for filename in sorted(os.listdir(self.published_dir), reverse=True):
            if not filename.startswith('morning_news_'):
                continue
            
            filepath = os.path.join(self.published_dir, filename)
            date_str = filename.replace('morning_news_', '').replace('.md', '')
            
            # 读取标题
            with open(filepath, 'r') as f:
                title = 'Unknown'
                for line in f:
                    if line.startswith('title:'):
                        title = line.replace('title:', '').strip().strip('"')
                        break
            
            reports.append({
                'date': date_str,
                'title': title,
                'filepath': filepath
            })
            
            if len(reports) >= limit:
                break
        
        return reports


def main():
    """主函数"""
    print("=" * 60)
    print("🔍 搜索脚本")
    print("=" * 60)
    
    engine = SearchEngine()
    
    # 解析参数
    if len(sys.argv) > 1:
        keyword = ' '.join(sys.argv[1:])
        print(f"\n🔍 搜索: {keyword}\n")
        
        # 搜索文章
        print("📰 文章结果:")
        articles = engine.search_articles(keyword)
        for i, article in enumerate(articles[:5], 1):
            print(f"  {i}. {article['title'][:50]}...")
            print(f"     来源: {article['source']} | 日期: {article['date']}")
        
        print("\n📄 早报结果:")
        reports = engine.search_reports(keyword)
        for report in reports[:3]:
            print(f"  📅 {report['date']}")
    else:
        # 列出最近的早报
        print("\n📄 最近的早报:")
        reports = engine.list_reports()
        for report in reports:
            print(f"  📅 {report['date']}: {report['title']}")


if __name__ == '__main__':
    main()
