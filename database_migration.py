#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本
确保数据库结构的一致性和可移植性
"""

import logging
import os
import sqlite3
from pathlib import Path

from models import create_tables, DatabaseSession, Image, Video
from config import SQLALCHEMY_DATABASE_URL

logger = logging.getLogger(__name__)

class DatabaseMigrator:
    def __init__(self):
        self.db_path = SQLALCHEMY_DATABASE_URL.replace("sqlite:///", "")
        self.db_dir = os.path.dirname(self.db_path)
        
    def get_current_schema_version(self):
        """获取当前数据库的版本号"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS schema_version (
                        version INTEGER PRIMARY KEY,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                
                cursor.execute("SELECT MAX(version) FROM schema_version")
                result = cursor.fetchone()
                return result[0] if result[0] else 0
        except Exception as e:
            logger.warning(f"获取数据库版本失败: {e}")
            return 0
    
    def set_schema_version(self, version):
        """设置数据库版本号"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
                conn.commit()
                logger.info(f"数据库版本已更新为: {version}")
        except Exception as e:
            logger.error(f"设置数据库版本失败: {e}")
    
    def migrate_to_version_1(self):
        """迁移到版本1：创建基础表结构"""
        logger.info("执行版本1迁移：创建基础表结构")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 创建 image 表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS image (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        path VARCHAR(255) NOT NULL,
                        original_name VARCHAR(255) NOT NULL,
                        modify_time DATETIME,
                        checksum VARCHAR(64) NOT NULL,
                        features BLOB,
                        tags VARCHAR(1024),
                        UNIQUE(path),
                        UNIQUE(checksum)
                    )
                """)
                
                # 创建 video 表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS video (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        path VARCHAR(255) NOT NULL,
                        original_name VARCHAR(255) NOT NULL,
                        frame_time INTEGER,
                        modify_time DATETIME,
                        checksum VARCHAR(64) NOT NULL,
                        features BLOB,
                        tags VARCHAR(1024),
                        UNIQUE(path),
                        UNIQUE(checksum)
                    )
                """)
                
                # 创建索引
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_image_path ON image(path)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_image_modify_time ON image(modify_time)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_image_checksum ON image(checksum)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_video_path ON video(path)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_video_modify_time ON video(modify_time)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_video_checksum ON video(checksum)")
                
                conn.commit()
                logger.info("版本1迁移完成")
                return True
                
        except Exception as e:
            logger.error(f"版本1迁移失败: {e}")
            return False
    
    def migrate_to_version_2(self):
        """迁移到版本2：添加缺失的字段"""
        logger.info("执行版本2迁移：添加缺失的字段")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 检查并添加 image 表的 original_name 字段
                cursor.execute("PRAGMA table_info(image)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'original_name' not in columns:
                    cursor.execute("ALTER TABLE image ADD COLUMN original_name VARCHAR(255)")
                    logger.info("为 image 表添加 original_name 字段")
                
                if 'tags' not in columns:
                    cursor.execute("ALTER TABLE image ADD COLUMN tags VARCHAR(1024)")
                    logger.info("为 image 表添加 tags 字段")
                
                # 检查并添加 video 表的 original_name 字段
                cursor.execute("PRAGMA table_info(video)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'original_name' not in columns:
                    cursor.execute("ALTER TABLE video ADD COLUMN original_name VARCHAR(255)")
                    logger.info("为 video 表添加 original_name 字段")
                
                if 'tags' not in columns:
                    cursor.execute("ALTER TABLE video ADD COLUMN tags VARCHAR(1024)")
                    logger.info("为 video 表添加 tags 字段")
                
                conn.commit()
                logger.info("版本2迁移完成")
                return True
                
        except Exception as e:
            logger.error(f"版本2迁移失败: {e}")
            return False
    
    def migrate_to_version_3(self):
        """迁移到版本3：更新现有记录的 original_name"""
        logger.info("执行版本3迁移：更新现有记录的 original_name")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 更新 image 表的 original_name
                cursor.execute("SELECT id, path FROM image WHERE original_name IS NULL OR original_name = ''")
                images = cursor.fetchall()
                
                for image_id, path in images:
                    if path:
                        original_name = os.path.basename(path)
                        cursor.execute("UPDATE image SET original_name = ? WHERE id = ?", (original_name, image_id))
                
                # 更新 video 表的 original_name
                cursor.execute("SELECT id, path FROM video WHERE original_name IS NULL OR original_name = ''")
                videos = cursor.fetchall()
                
                for video_id, path in videos:
                    if path:
                        original_name = os.path.basename(path)
                        cursor.execute("UPDATE video SET original_name = ? WHERE id = ?", (original_name, video_id))
                
                conn.commit()
                logger.info(f"版本3迁移完成，更新了 {len(images)} 个图片记录和 {len(videos)} 个视频记录")
                return True
                
        except Exception as e:
            logger.error(f"版本3迁移失败: {e}")
            return False
    
    def validate_database(self):
        """验证数据库结构"""
        logger.info("验证数据库结构...")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 检查 image 表
                cursor.execute("PRAGMA table_info(image)")
                image_columns = {column[1]: column[2] for column in cursor.fetchall()}
                
                required_image_columns = {
                    'id': 'INTEGER',
                    'path': 'VARCHAR(255)',
                    'original_name': 'VARCHAR(255)',
                    'modify_time': 'DATETIME',
                    'checksum': 'VARCHAR(64)',
                    'features': 'BLOB',
                    'tags': 'VARCHAR(1024)'
                }
                
                # 检查 video 表
                cursor.execute("PRAGMA table_info(video)")
                video_columns = {column[1]: column[2] for column in cursor.fetchall()}
                
                required_video_columns = {
                    'id': 'INTEGER',
                    'path': 'VARCHAR(255)',
                    'original_name': 'VARCHAR(255)',
                    'frame_time': 'INTEGER',
                    'modify_time': 'DATETIME',
                    'checksum': 'VARCHAR(64)',
                    'features': 'BLOB',
                    'tags': 'VARCHAR(1024)'
                }
                
                # 验证 image 表
                for column, expected_type in required_image_columns.items():
                    if column not in image_columns:
                        logger.error(f"Image 表缺少字段: {column}")
                        return False
                
                # 验证 video 表
                for column, expected_type in required_video_columns.items():
                    if column not in video_columns:
                        logger.error(f"Video 表缺少字段: {column}")
                        return False
                
                logger.info("数据库结构验证通过")
                return True
                
        except Exception as e:
            logger.error(f"数据库验证失败: {e}")
            return False
    
    def run_migrations(self):
        """运行所有迁移"""
        logger.info("开始数据库迁移...")
        
        # 确保数据库目录存在
        if self.db_dir and not os.path.exists(self.db_dir):
            os.makedirs(self.db_dir)
        
        current_version = self.get_current_schema_version()
        logger.info(f"当前数据库版本: {current_version}")
        
        # 运行迁移
        migrations = [
            (1, self.migrate_to_version_1),
            (2, self.migrate_to_version_2),
            (3, self.migrate_to_version_3)
        ]
        
        for version, migration_func in migrations:
            if current_version < version:
                logger.info(f"执行迁移到版本 {version}")
                if migration_func():
                    self.set_schema_version(version)
                    current_version = version
                else:
                    logger.error(f"迁移到版本 {version} 失败")
                    return False
        
        # 验证数据库结构
        if self.validate_database():
            logger.info("数据库迁移完成")
            return True
        else:
            logger.error("数据库验证失败")
            return False

def init_database():
    """初始化数据库（兼容性函数）"""
    migrator = DatabaseMigrator()
    return migrator.run_migrations()

def reset_database():
    """重置数据库（删除并重新创建）"""
    logger.info("重置数据库...")
    
    migrator = DatabaseMigrator()
    
    # 删除现有数据库
    if os.path.exists(migrator.db_path):
        os.remove(migrator.db_path)
        logger.info("已删除现有数据库文件")
    
    # 重新创建数据库
    return migrator.run_migrations()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="数据库迁移工具")
    parser.add_argument("--reset", action="store_true", help="重置数据库")
    parser.add_argument("--validate", action="store_true", help="验证数据库结构")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    if args.reset:
        reset_database()
    elif args.validate:
        migrator = DatabaseMigrator()
        migrator.validate_database()
    else:
        init_database() 