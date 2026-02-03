#!/usr/bin/env python3
"""
数据归档脚本
功能：管理历史数据，支持检索和备份
"""

import os
import sys
import json
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml


class DataArchiver:
    """数据归档器"""
    
    def __init__(self, config_path=None):
        """初始化"""
        if config_path is None:
            script_dir = Path(__file__).parent.parent
            config_path = script_dir / "config.yaml"
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.raw_data_dir = self.config['storage']['raw_data_dir']
        self.processed_data_dir = self.config['storage']['processed_data_dir']
        self.backup_dir = self.config['storage']['backup_dir']
        self.max_history_days = self.config['storage']['max_history_days']
        
        # 确保目录存在
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def list_files(self, data_type='all'):
        """列出数据文件"""
        files = []
        
        if data_type in ['all', 'raw']:
            raw_files = sorted([
                {'path': os.path.join(self.raw_data_dir, f), 'type': 'raw', 'date': f.split('_')[1]}
                for f in os.listdir(self.raw_data_dir) if f.startswith('raw_')
            ])
            files.extend(raw_files)
        
        if data_type in ['all', 'processed']:
            processed_files = sorted([
                {'path': os.path.join(self.processed_data_dir, f), 'type': 'processed', 'date': f.split('_')[1]}
                for f in os.listdir(self.processed_data_dir) if f.startswith('processed_')
            ], key=lambda x: x['date'], reverse=True)
            files.extend(processed_files)
        
        if data_type in ['all', 'published']:
            published_files = sorted([
                {'path': os.path.join(self.published_data_dir, f), 'type': 'published', 'date': f.split('_')[2].replace('.md', '')}
                for f in os.listdir(self.published_data_dir) if f.startswith('morning_news_')
            ], key=lambda x: x['date'], reverse=True)
            files.extend(published_files)
        
        return files
    
    def get_file_info(self, filepath):
        """获取文件信息"""
        if not os.path.exists(filepath):
            return None
        
        stat = os.stat(filepath)
        return {
            'path': filepath,
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'created': datetime.fromtimestamp(stat.st_ctime).isoformat()
        }
    
    def backup(self, days=7):
        """备份数据"""
        print("\n" + "=" * 60)
        print("💾 数据备份")
        print("=" * 60)
        
        # 备份目录以日期命名
        backup_date = datetime.now().strftime('%Y%m%d')
        backup_folder = os.path.join(self.backup_dir, backup_date)
        os.makedirs(backup_folder, exist_ok=True)
        
        files_to_backup = self.list_files()
        backed_up = 0
        
        for file_info in files_to_backup:
            filepath = file_info['path']
            if not os.path.exists(filepath):
                continue
            
            # 计算文件修改日期
            file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
            if datetime.now() - file_mtime > timedelta(days=days):
                continue
            
            # 复制文件
            relative_path = os.path.relpath(filepath)
            dest_path = os.path.join(backup_folder, relative_path)
            
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.copy2(filepath, dest_path)
            backed_up += 1
        
        print(f"✅ 已备份 {backed_up} 个文件到: {backup_folder}")
        return backup_folder
    
    def cleanup(self, days=None):
        """清理旧数据"""
        if days is None:
            days = self.max_history_days
        
        print("\n🧹 清理旧数据...")
        
        cutoff_date = datetime.now() - timedelta(days=days)
        cleaned = 0
        
        for data_type in ['raw', 'processed']:
            dir_path = self.raw_data_dir if data_type == 'raw' else self.processed_data_dir
            
            for filename in os.listdir(dir_path):
                if not filename.startswith(data_type + '_'):
                    continue
                
                filepath = os.path.join(dir_path, filename)
                file_date = datetime.strptime(filename.split('_')[1], '%Y%m%d_%H%M%S')
                
                if file_date < cutoff_date:
                    os.remove(filepath)
                    cleaned += 1
        
        print(f"✅ 已清理 {cleaned} 个旧文件")
        return cleaned
    
    def search(self, keyword, data_type='all', limit=10):
        """搜索数据"""
        print(f"\n🔍 搜索关键词: {keyword}")
        
        results = []
        files = self.list_files(data_type)
        
        for file_info in files:
            filepath = file_info['path']
            
            if filepath.endswith('.json'):
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 搜索processed数据
                if 'articles' in data:
                    for article in data['articles']:
                        text = f"{article.get('title', '')} {article.get('summary', '')}"
                        if keyword.lower() in text.lower():
                            results.append({
                                'type': 'article',
                                'title': article.get('title', ''),
                                'summary': article.get('summary', '')[:200],
                                'source': article.get('source', ''),
                                'date': file_info['date'],
                                'link': article.get('link', '')
                            })
            
            if len(results) >= limit:
                break
        
        print(f"✅ 找到 {len(results)} 条结果")
        return results
    
    def get_stats(self):
        """获取统计信息"""
        stats = {
            'raw_files': 0,
            'processed_files': 0,
            'published_files': 0,
            'total_articles': 0,
            'date_range': {'start': None, 'end': None}
        }
        
        dates = []
        
        # 统计raw文件
        for f in os.listdir(self.raw_data_dir):
            if f.startswith('raw_'):
                stats['raw_files'] += 1
                date_str = f.split('_')[1]
                dates.append(date_str)
        
        # 统计processed文件
        for f in os.listdir(self.processed_data_dir):
            if f.startswith('processed_'):
                stats['processed_files'] += 1
                date_str = f.split('_')[1]
                dates.append(date_str)
        
        # 统计published文件
        published_dir = self.config['morning_news']['output_dir']
        for f in os.listdir(published_dir):
            if f.startswith('morning_news_'):
                stats['published_files'] += 1
                date_str = f.split('_')[2].replace('.md', '')
                dates.append(date_str)
        
        # 统计文章数
        for f in os.listdir(self.processed_data_dir):
            if f.startswith('processed_'):
                filepath = os.path.join(self.processed_data_dir, f)
                with open(filepath, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    stats['total_articles'] += data.get('total_articles', 0)
        
        if dates:
            dates.sort()
            stats['date_range']['start'] = dates[0]
            stats['date_range']['end'] = dates[-1]
        
        return stats
    
    def list_by_date(self, date_str=None):
        """按日期列出文件"""
        if not date_str:
            date_str = datetime.now().strftime('%Y%m%d')
        
        print(f"\n📅 {date_str} 的文件:")
        
        files = self.list_files()
        date_files = [f for f in files if date_str in f['date']]
        
        for f in date_files:
            info = self.get_file_info(f['path'])
            if info:
                size_kb = info['size'] / 1024
                print(f"  [{f['type']}] {os.path.basename(f['path'])} ({size_kb:.1f} KB)")
        
        return date_files


def main():
    """主函数"""
    print("=" * 60)
    print("💾 数据归档管理器")
    print("=" * 60)
    
    archiver = DataArchiver()
    
    # 显示统计
    stats = archiver.get_stats()
    print("\n📊 数据统计:")
    print(f"  原始数据文件: {stats['raw_files']}")
    print(f"  处理后文件: {stats['processed_files']}")
    print(f"  发布的早报: {stats['published_files']}")
    print(f"  总文章数: {stats['total_articles']}")
    if stats['date_range']['start']:
        print(f"  日期范围: {stats['date_range']['start']} ~ {stats['date_range']['end']}")
    
    # 列出今天的文件
    archiver.list_by_date()


if __name__ == '__main__':
    main()
