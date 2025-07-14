#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的数据库初始化脚本
不依赖外部库，确保数据库结构正确
"""

import os
import sqlite3
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def init_database():
    """初始化数据库"""
    db_path = "./instance/assets.db"
    db_dir = os.path.dirname(db_path)
    
    # 确保数据库目录存在
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
    
    logger.info(f"初始化数据库: {db_path}")
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # 创建 schema_version 表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
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
            
            # 设置版本号
            cursor.execute("INSERT OR IGNORE INTO schema_version (version) VALUES (3)")
            
            conn.commit()
            logger.info("✓ 数据库初始化完成")
            return True
            
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        return False

def validate_database():
    """验证数据库结构"""
    db_path = "./instance/assets.db"
    
    if not os.path.exists(db_path):
        logger.error("数据库文件不存在")
        return False
    
    logger.info("验证数据库结构...")
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # 检查 image 表
            cursor.execute("PRAGMA table_info(image)")
            image_columns = {column[1] for column in cursor.fetchall()}
            
            required_image_columns = {
                'id', 'path', 'original_name', 'modify_time', 
                'checksum', 'features', 'tags'
            }
            
            # 检查 video 表
            cursor.execute("PRAGMA table_info(video)")
            video_columns = {column[1] for column in cursor.fetchall()}
            
            required_video_columns = {
                'id', 'path', 'original_name', 'frame_time', 
                'modify_time', 'checksum', 'features', 'tags'
            }
            
            # 验证 image 表
            missing_image = required_image_columns - image_columns
            if missing_image:
                logger.error(f"Image 表缺少字段: {missing_image}")
                return False
            
            # 验证 video 表
            missing_video = required_video_columns - video_columns
            if missing_video:
                logger.error(f"Video 表缺少字段: {missing_video}")
                return False
            
            logger.info("✓ 数据库结构验证通过")
            return True
            
    except Exception as e:
        logger.error(f"数据库验证失败: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--validate":
        validate_database()
    else:
        init_database() 