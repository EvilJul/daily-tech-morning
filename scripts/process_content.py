#!/usr/bin/env python3
"""
内容处理脚本
功能：整合摘要生成和关键词提取
"""

import os
import sys
import json
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml
from fetch_rss import RSSFetcher
from summarize import AISummarizer, clean_html_text
from extract_keywords import KeywordExtractor


class ContentProcessor:
    """内容处理器"""
    
    def __init__(self, config_path='config.yaml'):
        """初始化"""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.raw_data_dir = self.config['storage']['raw_data_dir']
        self.processed_data_dir = self.config['storage']['processed_data_dir']
        
        # 确保目录存在
        os.makedirs(self.processed_data_dir, exist_ok=True)
        
        self.summarizer = AISummarizer(config_path)
        self.extractor = KeywordExtractor()
    
    def process(self, use_ai=False):
        """处理内容"""
        print("\n" + "=" * 60)
        print("📊 内容处理器")
        print("=" * 60)
        
        # 获取最新的原始数据
        fetcher = RSSFetcher()
        raw_data = fetcher.get_latest_raw()
        
        if not raw_data:
            print("❌ 没有找到原始数据，请先运行 fetch_rss.py")
            return None
        
        # 收集所有文章
        all_articles = []
        for source in raw_data.get('sources', []):
            all_articles.extend(source.get('articles', []))
        
        # 获取最近几天早报中已存在的链接（跨天去重）
        published_dir = self.config['morning_news']['output_dir']
        seen_links = set()
        
        if os.path.exists(published_dir):
            import glob
            # 获取最近7天的早报文件
            report_files = sorted(glob.glob(os.path.join(published_dir, 'morning_news_*.md')), reverse=True)[:7]
            for report_file in report_files:
                try:
                    with open(report_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # 提取所有链接
                        import re
                        links = re.findall(r'\[阅读原文\]\((https?://[^\s)]+)\)', content)
                        seen_links.update(links)
                except Exception as e:
                    print(f"  ⚠️ 读取早报失败: {report_file}")
        
        print(f"\n📰 已有 {len(seen_links)} 篇文章在最近7天早报中")
        
        # 去重（基于链接）
        unique_articles = []
        for article in all_articles:
            link = article.get('link', '')
            if link and link not in seen_links:
                seen_links.add(link)
                unique_articles.append(article)
            elif link:
                print(f"  🔄 跳过重复: {article.get('title', '')[:50]}...")
        
        print(f"\n📰 去重后共有 {len(unique_articles)} 篇新文章")
        
        # 处理每篇文章
        print("\n🔄 开始处理文章...")
        processed_articles = []
        
        for i, article in enumerate(unique_articles):
            # AI摘要
            summary_result = self.summarizer.summarize_article(article, use_ai=use_ai)
            
            # 关键词提取
            keyword_result = self.extractor.process_article(article)
            
            # 合并结果
            processed = {
                **article,
                'short_summary': summary_result['short_summary'],
                'funny_title': summary_result['funny_title'],
                'tags': summary_result['tags'] + keyword_result['keywords'][:3],
                'topics': keyword_result['topics'],
                'image_suggestion': summary_result['image_suggestion'],
                'processed_at': datetime.now().isoformat()
            }
            
            processed_articles.append(processed)
            
            if (i + 1) % 20 == 0:
                print(f"  已处理 {i + 1}/{len(unique_articles)} 篇")
        
        print(f"  ✅ 处理完成 {len(processed_articles)} 篇文章")
        
        # 保存处理后的数据
        output_file = os.path.join(
            self.processed_data_dir,
            f"processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'processed_at': datetime.now().isoformat(),
                'total_articles': len(processed_articles),
                'articles': processed_articles
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 处理后数据已保存: {output_file}")
        
        # 统计
        all_tags = []
        all_topics = []
        for article in processed_articles:
            all_tags.extend(article.get('tags', []))
            all_topics.extend(article.get('topics', []))
        
        from collections import Counter
        tag_stats = Counter(all_tags).most_common(10)
        topic_stats = Counter(all_topics).most_common(5)
        
        print(f"\n📊 统计:")
        print(f"   热门标签: {tag_stats[:5]}")
        print(f"   主题分布: {topic_stats}")
        
        return processed_articles
    
    def generate_enhanced_news(self, articles):
        """生成增强版早报"""
        print("\n📝 生成增强版早报...")
        
        # 按主题分类
        categorized = {
            'AI前沿': [],
            '科技创投': [],
            '开源动态': [],
            '工具推荐': [],
            '其他': []
        }
        
        for article in articles:
            topics = article.get('topics', [])
            funny_title = article.get('funny_title', article.get('title', ''))
            short_summary = clean_html_text(article.get('short_summary', article.get('summary', '')))
            
            item = {
                'title': funny_title,
                'summary': short_summary,
                'source': article.get('source', ''),
                'link': article.get('link', ''),
                'tags': article.get('tags', [])[:3],
                'image': article.get('image_suggestion', '')
            }
            
            if 'AI/机器学习' in topics:
                categorized['AI前沿'].append(item)
            elif '科技创投' in topics:
                categorized['科技创投'].append(item)
            elif '开源' in topics:
                categorized['开源动态'].append(item)
            elif '开发工具' in topics:
                categorized['工具推荐'].append(item)
            else:
                categorized['其他'].append(item)
        
        # 生成Markdown
        today = datetime.now().strftime('%Y年%m月%d日 %A')
        
        md_content = f"""---
title: "🤖 AI科技早报 - {today}"
date: {datetime.now().isoformat()}
slug: morning-news-{datetime.now().strftime('%Y-%m-%d')}
categories:
  - 科技资讯
  - AI前沿
tags:
  - 每日简报
  - 科技
  - AI
---

# 🤖 AI科技早报 - {today}

> 每天早上7点，了解AI和科技圈的新鲜事！

---

## 📊 今日概览

| 统计项 | 数量 |
|--------|------|
| 📝 文章总数 | {len(articles)} 篇 |
| 🔥 AI前沿 | {len(categorized['AI前沿'])} 篇 |
| 💰 创投动态 | {len(categorized['科技创投'])} 篇 |
| 🛠️ 工具推荐 | {len(categorized['工具推荐'])} 篇 |

---
"""
        
        for category, items in categorized.items():
            if items:
                md_content += f"\n## 🎯 {category}\n\n"
                for i, item in enumerate(items[:5], 1):
                    md_content += f"### {i}. {item['title']}\n\n"
                    md_content += f">{item['summary']}\n\n"
                    md_content += f"**标签**: {' '.join([f'`{t}`' for t in item['tags']])} · "
                    md_content += f"**来源**: {item['source']}\n\n"
                    md_content += f"[阅读原文]({item['link']}) · "
                    md_content += f"![配图建议]({item['image']})\n\n"
        
        md_content += f"""
---

## 💡 今日金句

> 在AI时代，最好的投资是学习本身。

---

> 📢 **关注我们**，获取每日最新科技资讯！
> 
> Powered by [Daily Tech Morning](https://github.com/EvilJul/daily-tech-morning)
"""
        
        # 保存
        output_file = os.path.join(
            self.processed_data_dir,
            f"enhanced_morning_news_{datetime.now().strftime('%Y%m%d')}.md"
        )
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        print(f"✅ 增强版早报已生成: {output_file}")
        return output_file


def main():
    """主函数"""
    use_ai = '--ai' in sys.argv
    
    processor = ContentProcessor()
    articles = processor.process(use_ai=use_ai)
    
    if articles:
        processor.generate_enhanced_news(articles)


if __name__ == '__main__':
    main()
