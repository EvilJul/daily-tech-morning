#!/usr/bin/env python3
"""
AI摘要生成脚本
功能：使用AI API生成文章摘要和风趣标题
"""

import os
import sys
import json
import re
import requests
from html import unescape

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml


def clean_html_text(text):
    """清理HTML标签和实体，提取纯文本"""
    if not text:
        return ""

    # 1. 解码HTML实体
    text = unescape(text)

    # 2. 移除HTML标签
    text = re.sub(r'<[^>]+>', '', text)

    # 3. 清理多余的空白字符
    text = re.sub(r'\s+', ' ', text)

    # 4. 清理特殊字符
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&#39;', "'")
    text = text.replace('&quot;', '"')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')

    return text.strip()


class AISummarizer:
    """AI摘要生成器"""

    def __init__(self, config_path='config.yaml'):
        """初始化"""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        self.ai_config = self.config.get('ai', {})
        self.provider = self.ai_config.get('provider', 'openai')
        self.model = self.ai_config.get('model', 'gpt-3.5-turbo')
        self.api_key = self.ai_config.get('api_key', '')
        self.max_tokens = self.ai_config.get('max_tokens', 1024)
        self.temperature = self.ai_config.get('temperature', 0.7)

    def summarize_article(self, article, use_ai=True):
        """生成文章摘要"""
        # 清理HTML内容，提取纯文本
        title = clean_html_text(article.get('title', ''))
        summary = clean_html_text(article.get('summary', ''))[:500]
        content = clean_html_text(article.get('content', ''))[:1000]

        if not use_ai or not self.api_key:
            # 不使用AI，确保摘要约50字
            raw_summary = summary[:300]
            if len(raw_summary) < 30:
                # 如果摘要太短，尝试从内容中提取
                raw_summary = content[:300]
            # 确保约50字
            short_summary = raw_summary[:150].rsplit('。', 1)[0] + '。'
            if len(short_summary) < 40:
                short_summary = raw_summary[:100] + '...'
            return {
                'short_summary': short_summary,
                'funny_title': self._generate_funny_title(title),
                'tags': self._extract_tags(article),
                'image_suggestion': self._get_image_suggestion(article)
            }

        # 使用AI生成摘要
        prompt = f"""
请为以下文章生成一个简短的摘要（约50字），并生成一个风趣的标题。

文章标题：{title}
原文摘要：{summary}
原文内容：{content}

请用JSON格式返回：
{{
    "summary": "简短的新闻摘要，约50字，保持风趣幽默风格",
    "funny_title": "一个吸引眼球的标题，带点幽默感",
    "tags": ["标签1", "标签2", "标签3"],
    "image_prompt": "配图建议，描述一个相关的图片场景"
}}

只返回JSON，不要其他内容。
"""

        try:
            response = self._call_ai(prompt)
            result = json.loads(response)

            return {
                'short_summary': result.get('summary', summary[:200]),
                'funny_title': result.get('funny_title', self._generate_funny_title(title)),
                'tags': result.get('tags', self._extract_tags(article)),
                'image_suggestion': result.get('image_prompt', self._get_image_suggestion(article))
            }
        except Exception as e:
            print(f"  ⚠️ AI生成失败: {e}")
            # 确保约50字
            raw_summary = summary[:300]
            if len(raw_summary) < 30:
                raw_summary = content[:300]
            short_summary = raw_summary[:150].rsplit('。', 1)[0] + '。'
            if len(short_summary) < 40:
                short_summary = raw_summary[:100] + '...'
            return {
                'short_summary': short_summary,
                'funny_title': self._generate_funny_title(title),
                'tags': self._extract_tags(article),
                'image_suggestion': self._get_image_suggestion(article)
            }

    def _call_ai(self, prompt):
        """调用AI API"""
        provider = self.provider.lower()

        if provider == 'openai':
            return self._call_openai(prompt)
        elif provider == 'openrouter':
            return self._call_openrouter(prompt)
        elif provider == 'minimax':
            return self._call_minimax(prompt)
        elif provider == 'deepseek':
            return self._call_deepseek(prompt)
        elif provider == 'siliconflow':
            return self._call_siliconflow(prompt)
        elif provider == 'qwen':
            return self._call_qwen(prompt)
        else:
            raise ValueError(f"不支持的AI提供商: {provider}")

    def _call_openai(self, prompt):
        """调用OpenAI API"""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }

        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()

        return response.json()['choices'][0]['message']['content']

    def _call_qwen(self, prompt):
        """调用通义千问API"""
        base_url = self.ai_config.get('base_url', '').strip()
        if not base_url:
            base_url = 'https://dashscope.aliyuncs.com/api/v1'
        url = f"{base_url}/services/aigc/text-generation/generation"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "input": {
                "messages": [{"role": "user", "content": prompt}]
            },
            "parameters": {
                "max_tokens": self.max_tokens,
                "temperature": self.temperature
            }
        }

        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()

        return response.json()['output']['text']

    def _call_openrouter(self, prompt):
        """调用OpenRouter API"""
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/EvilJul/daily-tech-morning",
            "X-Title": "Daily Tech Morning"
        }
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }

        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()

        return response.json()['choices'][0]['message']['content']

    def _call_minimax(self, prompt):
        """调用Minimax API"""
        base_url = self.ai_config.get('base_url', '').strip()
        if not base_url:
            base_url = 'https://api.minimax.chat/v1'
        url = f"{base_url}/text/chatcompletion_v2"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "tokens_to_generate": self.max_tokens,
            "temperature": self.temperature
        }

        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()

        return response.json()['choices'][0]['message']['content']

    def _call_deepseek(self, prompt):
        """调用DeepSeek API"""
        base_url = self.ai_config.get('base_url', '').strip()
        if not base_url:
            base_url = 'https://api.deepseek.com'
        url = f"{base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }

        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()

        return response.json()['choices'][0]['message']['content']

    def _call_siliconflow(self, prompt):
        """调用硅基流动(SiliconFlow) API"""
        base_url = self.ai_config.get('base_url', '').strip()
        if not base_url:
            base_url = 'https://api.siliconflow.cn/v1'
        url = f"{base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }

        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()

        return response.json()['choices'][0]['message']['content']

    def _generate_funny_title(self, title):
        """生成风趣标题（不使用AI）"""
        prefixes = [
            "🔥", "🚀", "💡", "⚡", "🎯", "📢", "🤖", "💻", "🔮", "✨"
        ]
        import random
        prefix = random.choice(prefixes)

        # 添加一些后缀
        suffixes = ["来了！", "更新啦！", "速看！", "惊了！", "揭秘！"]
        suffix = random.choice(suffixes)

        return f"{prefix} {title} {suffix}"

    def _extract_tags(self, article):
        """提取标签"""
        tags = []

        # 来源
        source = article.get('source', '')
        if source:
            tags.append(source)

        # 分类
        category = article.get('category', '')
        if category:
            tags.append(category)

        # 语言
        language = article.get('language', '')
        if language:
            tags.append(language)

        # 关键词
        keywords_map = {
            'ai': ['AI', '人工智能'],
            'gpt': ['GPT', 'LLM'],
            'ml': ['机器学习'],
            'deep learning': ['深度学习'],
            'startup': ['创业', '融资'],
            'product': ['产品', '发布']
        }

        text = f"{article.get('title', '')} {article.get('summary', '')}".lower()
        for key, values in keywords_map.items():
            if key in text:
                tags.extend(values)

        # 去重并返回前5个
        return list(set(tags))[:5]

    def _get_image_suggestion(self, article):
        """获取配图建议"""
        title = article.get('title', '').lower()

        if 'ai' in title or 'gpt' in title:
            return "🤖 机器人/AI芯片/神经网络图"
        elif 'code' in title or 'programming' in title:
            return "💻 代码编辑器/编程概念图"
        elif 'startup' in title or 'funding' in title:
            return "💰 火箭发射/资金图"
        elif 'product' in title or 'launch' in title:
            return "🎁 产品发布/礼物盒图"
        else:
            return "📱 科技场景/办公环境图"

    def process_articles(self, articles, use_ai=True):
        """批量处理文章"""
        print(f"📝 开始处理 {len(articles)} 篇文章...")

        processed = []
        for i, article in enumerate(articles):
            result = self.summarize_article(article, use_ai=use_ai)

            # 合并结果
            processed_article = {
                **article,
                'short_summary': result['short_summary'],
                'funny_title': result['funny_title'],
                'tags': result['tags'],
                'image_suggestion': result['image_suggestion']
            }
            processed.append(processed_article)

            if (i + 1) % 10 == 0:
                print(f"  已处理 {i + 1}/{len(articles)} 篇")

        print(f"  ✅ 处理完成 {len(articles)} 篇文章")
        return processed


def main():
    """主函数"""
    print("=" * 60)
    print("📝 AI摘要生成器")
    print("=" * 60)

    summarizer = AISummarizer()

    # 测试
    test_article = {
        'title': 'OpenAI发布GPT-4.5',
        'summary': 'OpenAI今日发布了最新的GPT-4.5模型，在推理能力和创意写作方面有显著提升。',
        'source': 'OpenAI Blog',
        'category': 'ai',
        'language': 'English'
    }

    result = summarizer.summarize_article(test_article, use_ai=False)
    print("\n测试结果:")
    print(f"  风趣标题: {result['funny_title']}")
    print(f"  摘要: {result['short_summary']}")
    print(f"  标签: {result['tags']}")
    print(f"  配图: {result['image_suggestion']}")


if __name__ == '__main__':
    main()
