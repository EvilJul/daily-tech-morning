#!/usr/bin/env python3
"""
Halo 2.x 文章发布脚本
功能：将生成的早报发布到Halo博客
使用正确的Snapshots API格式
"""

import os
import sys
import json
import yaml
import asyncio
import argparse
from datetime import datetime
from pathlib import Path

import aiohttp
import markdown


class HaloPublisher:
    """Halo文章发布器"""
    
    def __init__(self, config_path: str = None):
        """初始化"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config.yaml"
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.halo = self.config.get('halo', {})
        self.url = self.halo.get('url', 'http://localhost:8090').rstrip('/')
        self.token = self.halo.get('admin_token', '')
        self.category_id = self.halo.get('category_id')
        self.category_slug = self.halo.get('category_slug', '')
        self.tag_ids = self.halo.get('tag_ids', [])
        
        # API端点
        self.posts_url = f"{self.url}/apis/content.halo.run/v1alpha1/posts"
        self.snapshots_url = f"{self.url}/apis/content.halo.run/v1alpha1/snapshots"
        self.categories_url = f"{self.url}/apis/content.halo.run/v1alpha1/categories"
    
    def get_content(self, date: str = None) -> dict:
        """获取今日早报内容"""
        if date is None:
            date = datetime.now().strftime('%Y%m%d')
        
        project_dir = Path(__file__).parent.parent
        data_dir = project_dir / "data" / "published"
        file_path = data_dir / f"morning_news_{date}.md"
        
        if not file_path.exists():
            files = sorted(data_dir.glob("morning_news_*.md"), reverse=True)
            if files:
                file_path = files[0]
            else:
                raise FileNotFoundError(f"未找到早报文件: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取标题
        title = "AI科技早报"
        for line in content.split('\n'):
            if line.startswith('# '):
                title = line.replace('# ', '').strip()
                break
        
        # 生成slug
        slug = f"ai-morning-news-{date}"
        
        return {
            'title': title,
            'slug': slug,
            'content': content,
            'raw_content': content,
            'date': date
        }
    
    def get_auth_header(self) -> dict:
        """获取认证头"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    async def get_categories(self) -> list:
        """获取分类列表"""
        if not self.token:
            raise ValueError("未配置Halo admin_token")
        
        headers = self.get_auth_header()
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self.categories_url, headers=headers) as resp:
                if resp.status >= 200 and resp.status < 300:
                    result = await resp.json()
                    return result.get('items', [])
                else:
                    print(f"获取分类失败: {resp.status}")
                    return []
    
    async def create_snapshot(self, content: dict) -> str:
        """创建内容快照"""
        print(f"📝 创建内容快照...")
        
        headers = self.get_auth_header()
        
        # 生成快照ID
        snapshot_id = f"snapshot-{content['date']}-{datetime.now().strftime('%S%H')}"
        now = datetime.now().isoformat() + 'Z'
        
        # 使用raw_content
        raw_content = content.get('raw_content', content.get('content', ''))
        md = markdown.Markdown(extensions=['tables', 'fenced_code'])
        html_content = md.convert(raw_content)
        
        snapshot_data = {
            "apiVersion": "content.halo.run/v1alpha1",
            "kind": "Snapshot",
            "metadata": {
                "name": snapshot_id,
                "annotations": {
                    "content.halo.run/keep-raw": "true"
                }
            },
            "spec": {
                "subjectRef": {
                    "group": "content.halo.run",
                    "version": "v1alpha1",
                    "kind": "Post",
                    "name": ""
                },
                "rawType": "HTML",
                "rawPatch": html_content,
                "contentPatch": html_content,
                "lastModifyTime": now,
                "owner": "fusheng",
                "contributors": ["fusheng"]
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.snapshots_url, json=snapshot_data, headers=headers) as resp:
                if resp.status >= 200 and resp.status < 300:
                    print(f"✅ 快照创建成功: {snapshot_id}")
                    return snapshot_id
                else:
                    text = await resp.text()
                    print(f"❌ 快照创建失败: {resp.status}")
                    print(f"   响应: {text[:300]}")
                    return None
    
    async def publish(self, content: dict = None) -> dict:
        """发布文章到Halo"""
        if content is None:
            content = self.get_content()
        
        if not self.token:
            raise ValueError("未配置Halo admin_token，请先在config.yaml中配置")
        
        # 获取分类ID
        category_id = self.category_id
        if not category_id and self.category_slug:
            print(f"🔍 通过slug '{self.category_slug}' 查找分类...")
            category_id = await self.get_category_id_by_slug(self.category_slug)
        
        print(f"📤 正在发布到 Halo...")
        print(f"   标题: {content['title']}")
        
        # 先创建快照
        snapshot_id = await self.create_snapshot(content)
        if not snapshot_id:
            return {"error": "创建快照失败"}
        
        now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S') + '.000000000Z'
        
        headers = self.get_auth_header()
        
        # 创建文章，引用快照
        post_data = {
            "apiVersion": "content.halo.run/v1alpha1",
            "kind": "Post",
            "metadata": {
                "generateName": f"post-{content['date']}-",
                "annotations": {
                    "content.halo.run/preferred-editor": "default"
                }
            },
            "spec": {
                "title": content['title'],
                "slug": content['slug'],
                "releaseSnapshot": snapshot_id,
                "headSnapshot": snapshot_id,
                "baseSnapshot": snapshot_id,
                "owner": "fusheng",
                "template": "",
                "cover": "",
                "deleted": False,
                "publish": True,
                "publishTime": now,
                "pinned": False,
                "allowComment": True,
                "visible": "PUBLIC",
                "priority": 0,
                "excerpt": {
                    "autoGenerate": True,
                    "raw": ""
                },
                "categories": [category_id] if category_id else [],
                "tags": [],
                "htmlMetas": []
            },
            "content": {
                "raw": "",
                "rawType": "HTML"
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.posts_url, json=post_data, headers=headers) as resp:
                text = await resp.text()
                
                if resp.status >= 200 and resp.status < 300:
                    result = json.loads(text)
                    post_name = result.get('metadata', {}).get('name')
                    
                    print(f"✅ 发布成功！")
                    print(f"   文章: {content['title']}")
                    print(f"   链接: {self.url}/archives/{content['slug']}")
                    print(f"   请在后台审核并发布")
                    return result
                else:
                    print(f"❌ 发布失败: {resp.status}")
                    print(f"   响应: {text[:500]}")
                    return {"error": text}


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='发布早报到Halo')
    parser.add_argument('--date', '-d', help='日期 (YYYYMMDD)', default=None)
    parser.add_argument('--categories', '-c', action='store_true', help='显示分类列表')
    parser.add_argument('--config', '-f', help='配置文件路径', default=None)
    
    args = parser.parse_args()
    
    if args.config and os.path.exists(args.config):
        config_path = args.config
    else:
        config_path = Path(__file__).parent.parent / "config.yaml"
    
    publisher = HaloPublisher(config_path=config_path)
    
    if args.categories:
        print("📂 可用分类：")
        categories = await publisher.get_categories()
        for cat in categories:
            spec = cat.get('spec', {})
            meta = cat.get('metadata', {})
            print(f"   名称: {meta.get('name')} - {spec.get('displayName')} ({spec.get('slug')})")
        return
    
    try:
        content = publisher.get_content(args.date)
        result = await publisher.publish(content)
        
        if result and 'error' not in result:
            print(f"\n🎉 已提交到 Halo!")
            print(f"   地址: {publisher.url}/archives/{content['slug']}")
            print(f"   请在后台审核并正式发布")
        else:
            print("\n❌ 发布失败，请检查配置")
            sys.exit(1)
            
    except FileNotFoundError as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"❌ 配置错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
