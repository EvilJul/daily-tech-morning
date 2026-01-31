#!/usr/bin/env python3
"""
关键词提取脚本
功能：从文本中提取关键词和标签
"""

import re
import os
import sys
from collections import Counter

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class KeywordExtractor:
    """关键词提取器"""
    
    def __init__(self):
        """初始化"""
        # 停用词
        self.stopwords = {
            '的', '了', '是', '在', '和', '与', '或', '为', '等', '这',
            '那', '有', '没有', '可以', '如何', '怎么', '什么',
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'shall',
            'can', 'need', 'dare', 'ought', 'used', 'to', 'of', 'in',
            'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into',
            'through', 'during', 'before', 'after', 'above', 'below',
            'between', 'under', 'again', 'further', 'then', 'once',
            'here', 'there', 'when', 'where', 'why', 'how', 'all',
            'each', 'few', 'more', 'most', 'other', 'some', 'such',
            'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than',
            'too', 'very', 'just', 'also', 'now', 'this', 'that',
            'these', 'those', 'it', 'its', 'they', 'them', 'their',
            'we', 'our', 'you', 'your', 'he', 'him', 'his', 'she',
            'her', 'i', 'me', 'my', 'who', 'whom', 'which', 'what',
            'whose', 'if', 'but', 'although', 'because', 'unless',
            'while', 'about', 'against', 'over', 'throughout'
        }
        
        # 常见科技词汇（不作为关键词）
        self.common_words = {
            'article', 'post', 'blog', 'news', 'update', 'release',
            'new', 'latest', 'recent', 'today', 'now', 'here',
            'read', 'learn', 'see', 'check', 'try', 'use', 'using'
        }
        
        # 主题关键词映射
        self.topic_keywords = {
            'AI/机器学习': ['ai', 'gpt', 'llm', 'machine learning', 'deep learning', 
                          'neural', '模型', '训练', '推理', 'agent', 'rag', 'embeddings'],
            '科技创投': ['startup', 'funding', '融资', '投资', '产品发布', 'launch',
                       'series a', 'series b', 'ipo', 'acquisition', '收购'],
            '开源': ['open source', 'github', '开源', 'apache', 'mit license', '社区'],
            '开发工具': ['framework', 'library', 'api', 'sdk', 'tool', '开发', '编程', '代码'],
            '云服务': ['cloud', 'aws', 'azure', 'gcp', 'serverless', 'k8s', 'docker'],
            '数据科学': ['data', 'analytics', '可视化', 'pandas', 'spark', 'hadoop']
        }
    
    def clean_text(self, text):
        """清理文本"""
        if not text:
            return ""
        # 转小写
        text = text.lower()
        # 移除URL
        text = re.sub(r'http[s]?://\S+', '', text)
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        # 移除特殊字符，保留字母、数字、中文
        text = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text)
        # 移除多余空格
        text = ' '.join(text.split())
        return text
    
    def extract_words(self, text):
        """提取词汇"""
        text = self.clean_text(text)
        words = text.split()
        
        # 过滤停用词和短词
        words = [
            w for w in words 
            if w not in self.stopwords 
            and w not in self.common_words
            and len(w) >= 2
        ]
        
        return words
    
    def extract_keywords(self, text, top_n=10):
        """提取关键词"""
        words = self.extract_words(text)
        
        # 统计词频
        word_counts = Counter(words)
        
        # 获取top_n
        keywords = word_counts.most_common(top_n)
        
        return [w for w, c in keywords]
    
    def detect_topics(self, text):
        """检测主题"""
        text = self.clean_text(text)
        text_lower = text.lower()
        
        detected_topics = []
        
        for topic, keywords in self.topic_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    detected_topics.append(topic)
                    break
        
        return detected_topics if detected_topics else ['其他']
    
    def process_article(self, article):
        """处理单篇文章"""
        text = f"{article.get('title', '')} {article.get('summary', '')} {article.get('content', '')}"
        
        return {
            'keywords': self.extract_keywords(text, top_n=8),
            'topics': self.detect_topics(text)
        }
    
    def process_batch(self, articles):
        """批量处理"""
        print(f"🔍 提取 {len(articles)} 篇文章的关键词...")
        
        results = []
        all_keywords = []
        
        for i, article in enumerate(articles):
            result = self.process_article(article)
            all_keywords.extend(result['keywords'])
            results.append(result)
            
            if (i + 1) % 20 == 0:
                print(f"  已处理 {i + 1}/{len(articles)} 篇")
        
        # 统计全局关键词
        keyword_stats = Counter(all_keywords).most_common(20)
        
        print(f"  ✅ 处理完成")
        print(f"  📊 全局热门关键词: {keyword_stats[:10]}")
        
        return results, keyword_stats


def main():
    """主函数"""
    print("=" * 60)
    print("🔍 关键词提取器")
    print("=" * 60)
    
    extractor = KeywordExtractor()
    
    # 测试
    test_text = """
    OpenAI今日发布了GPT-4.5模型，这是一个大型语言模型，在推理能力和创意写作方面有显著提升。
    这是AI领域的重大进展，机器学习和深度学习技术又向前迈进了一步。
    """
    
    keywords = extractor.extract_keywords(test_text, top_n=5)
    topics = extractor.detect_topics(test_text)
    
    print(f"\n测试文本关键词: {keywords}")
    print(f"检测到的主题: {topics}")


if __name__ == '__main__':
    main()
