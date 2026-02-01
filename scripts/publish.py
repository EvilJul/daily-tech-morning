#!/usr/bin/env python3
"""
主发布脚本
功能：生成早报后，发送到邮件和Halo
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


class MorningNewsPublisher:
    """早报发布器（邮件 + Halo）"""
    
    def __init__(self, config_path: str = None):
        """初始化"""
        if config_path is None:
            config_path = Path(__file__).parent / "config.yaml"
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.email_config = self.config.get('email', {})
        self.halo_config = self.config.get('halo', {})
        self.morning_news_config = self.config.get('morning_news', {})
        
        # 邮件配置
        self.smtp_host = self.email_config.get('smtp_host', 'smtp.qq.com')
        self.smtp_port = self.email_config.get('smtp_port', 465)
        self.username = self.email_config.get('username', '')
        self.password = self.email_config.get('password', '')
        self.to_addresses = self.email_config.get('to_addresses', [self.email_config.get('to_address', '')])
        
        # Halo配置
        self.halo_url = self.halo_config.get('url', 'http://localhost:8090').rstrip('/')
        self.halo_token = self.halo_config.get('admin_token', '')
        self.halo_category_id = self.halo_config.get('category_id')
        self.halo_category_slug = self.halo_config.get('category_slug', '')
        self.halo_tag_ids = self.halo_config.get('tag_ids', [])
        self.halo_enabled = self.halo_config.get('enabled', False)
        
        # Halo 2.x API端点
        self.halo_api_url = f"{self.halo_url}/apis/content.halo.run/v1alpha1/posts"
        self.halo_categories_url = f"{self.halo_url}/apis/content.halo.run/v1alpha1/categories"
    
    def get_content(self, date: str = None) -> dict:
        """获取今日早报内容"""
        if date is None:
            date = datetime.now().strftime('%Y%m%d')
        
        # 从脚本目录回到项目根目录
        project_dir = Path(__file__).parent.parent
        data_dir = project_dir / "data" / "published"
        file_path = data_dir / f"morning_news_{date}.md"
        
        if not file_path.exists():
            files = sorted(data_dir.glob("morning_news_*.md"), reverse=True)
            if files:
                file_path = files[0]
            else:
                raise FileNotFoundError(f"未找到早报文件")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取标题
        title = "AI科技早报"
        for line in content.split('\n'):
            if line.startswith('# '):
                title = line.replace('# ', '').strip()
                break
        
        slug = f"ai-morning-news-{date}"
        
        return {
            'title': title,
            'slug': slug,
            'content': content,
            'date': date
        }
    
    def get_auth_header(self) -> dict:
        """获取认证头"""
        return {
            "Authorization": f"Bearer {self.halo_token}",
            "Content-Type": "application/json"
        }
    
    async def get_categories(self) -> list:
        """获取分类列表"""
        if not self.halo_token:
            raise ValueError("未配置Halo admin_token")
        
        headers = self.get_auth_header()
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self.halo_categories_url, headers=headers) as resp:
                if resp.status >= 200 and resp.status < 300:
                    result = await resp.json()
                    return result.get('items', [])
                else:
                    text = await resp.text()
                    print(f"获取分类失败: {resp.status}")
                    print(f"响应: {text[:200]}")
                    return []
    
    async def get_category_id_by_slug(self, slug: str = None) -> str:
        """通过slug获取分类ID (Halo 2.x返回name不是ID)"""
        if not self.halo_token:
            raise ValueError("未配置Halo admin_token")
        
        if not slug:
            slug = self.halo_category_slug
        
        if not slug:
            return self.halo_category_id
        
        headers = self.get_auth_header()
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self.halo_categories_url, headers=headers) as resp:
                if resp.status >= 200 and resp.status < 300:
                    result = await resp.json()
                    items = result.get('items', [])
                    for item in items:
                        if item.get('spec', {}).get('slug') == slug:
                            name = item.get('metadata', {}).get('name')
                            print(f"✅ 找到分类: {item.get('spec', {}).get('displayName')} (name: {name})")
                            return name
                    print(f"❌ 未找到分类: {slug}")
                    return None
                else:
                    print(f"获取分类失败: {resp.status}")
                    return None
    
    async def send_email(self, content: dict) -> bool:
        """发送邮件（使用生成脚本的方式）"""
        if not self.email_config.get('enabled', False):
            print("📧 邮件功能未启用")
            return False
        
        print(f"📧 正在发送邮件...")
        
        # 调用generate脚本的邮件发送方法
        project_dir = Path(__file__).parent.parent
        sys.path.insert(0, str(project_dir))
        
        try:
            from generate_morning_news import MorningNewsGenerator
            generator = MorningNewsGenerator()
            
            # 获取文件路径
            date = content.get('date', datetime.now().strftime('%Y%m%d'))
            filepath = project_dir / "data" / "published" / f"morning_news_{date}.md"
            
            if filepath.exists():
                success = generator.send_email_notification(str(filepath))
                if success:
                    print("✅ 邮件发送成功！")
                return success
            else:
                print(f"❌ 邮件文件不存在: {filepath}")
                return False
        except Exception as e:
            print(f"❌ 邮件发送失败: {e}")
            return False
    
    async def publish_to_halo(self, content: dict) -> bool:
        """发布到Halo（使用publish_to_halo.py的逻辑）"""
        if not self.halo_enabled:
            print("📝 Halo功能未启用")
            return False
        
        if not self.halo_token:
            print("❌ Halo Token未配置")
            return False
        
        # 调用publish_to_halo.py的发布逻辑
        project_dir = Path(__file__).parent.parent
        sys.path.insert(0, str(project_dir))
        
        try:
            from publish_to_halo import HaloPublisher
            
            halo_config_path = project_dir / "config.yaml"
            publisher = HaloPublisher(config_path=str(halo_config_path))
            
            # 直接调用异步方法
            result = await publisher.publish(content)
            
            if result and 'error' not in result:
                return True
            else:
                print(f"❌ Halo发布失败")
                return False
        except Exception as e:
            print(f"❌ Halo发布异常: {e}")
            return False
    
    async def publish_all(self, content: dict = None) -> dict:
        """发送到所有渠道"""
        results = {
            'email': False,
            'halo': False
        }
        
        if content is None:
            content = self.get_content()
        
        # 并行发送
        tasks = []
        
        if self.email_config.get('enabled', False):
            tasks.append(self.send_email(content))
        
        if self.halo_enabled:
            tasks.append(self.publish_to_halo(content))
        
        if tasks:
            await asyncio.gather(*tasks)
        
        return results


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='发布早报')
    parser.add_argument('--date', '-d', help='日期 (YYYYMMDD)', default=None)
    parser.add_argument('--email-only', '-e', action='store_true', help='只发送邮件')
    parser.add_argument('--halo-only', '-H', action='store_true', help='只发布到Halo')
    parser.add_argument('--categories', '-c', action='store_true', help='显示分类列表')
    parser.add_argument('--config', '-f', help='配置文件路径', default=None)
    
    args = parser.parse_args()
    
    publisher = MorningNewsPublisher(config_path=args.config)
    
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
        
        print("=" * 50)
        print(f"📰 发布: {content['title']}")
        print("=" * 50)
        
        if args.email_only:
            await publisher.send_email(content)
        elif args.halo_only:
            await publisher.publish_to_halo(content)
        else:
            await publisher.publish_all(content)
            
    except FileNotFoundError as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
