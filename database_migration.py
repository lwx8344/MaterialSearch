#!/usr/bin/env python3
"""
数据库迁移脚本
Database Migration Script
"""

import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

def init_database():
    """
    初始化数据库，创建必要的表和列
    """
    try:
        # 确保instance目录存在
        instance_dir = Path("instance")
        instance_dir.mkdir(exist_ok=True)
        
        db_path = instance_dir / "assets.db"
        
        # 连接数据库
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 检查当前版本
        cursor.execute("PRAGMA user_version")
        current_version = cursor.fetchone()[0]
        logger.info(f"当前数据库版本: {current_version}")
        
        # 执行迁移
        migrations_applied = False
        
        # 版本 1: 创建基础表结构
        if current_version < 1:
            logger.info("执行迁移 1: 创建基础表结构")
            
            # 创建image表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS image (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path VARCHAR(255) NOT NULL,
                    original_name VARCHAR(255),
                    modify_time DATETIME,
                    features BLOB,
                    checksum VARCHAR(64),
                    tags VARCHAR(1024)
                )
            """)
            
            # 创建video表 (修复UNIQUE约束问题)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS video (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path VARCHAR(255) NOT NULL,
                    original_name VARCHAR(255),
                    frame_time INTEGER,
                    modify_time DATETIME,
                    features BLOB,
                    checksum VARCHAR(64),
                    tags VARCHAR(1024)
                )
            """)
            
            # 创建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_image_path ON image(path)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_image_modify_time ON image(modify_time)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_image_checksum ON image(checksum)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_video_path ON video(path)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_video_modify_time ON video(modify_time)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_video_checksum ON video(checksum)")
            
            cursor.execute("PRAGMA user_version = 1")
            migrations_applied = True
        
        # 版本 2: 添加缺失的列
        if current_version < 2:
            logger.info("执行迁移 2: 添加缺失的列")
            
            # 检查并添加image表的original_name列
            cursor.execute("PRAGMA table_info(image)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'original_name' not in columns:
                cursor.execute("ALTER TABLE image ADD COLUMN original_name VARCHAR(255)")
            
            # 检查并添加video表的original_name列
            cursor.execute("PRAGMA table_info(video)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'original_name' not in columns:
                cursor.execute("ALTER TABLE video ADD COLUMN original_name VARCHAR(255)")
            
            # 检查并添加tags列
            if 'tags' not in columns:
                cursor.execute("ALTER TABLE video ADD COLUMN tags VARCHAR(1024)")
            
            cursor.execute("PRAGMA table_info(image)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'tags' not in columns:
                cursor.execute("ALTER TABLE image ADD COLUMN tags VARCHAR(1024)")
            
            cursor.execute("PRAGMA user_version = 2")
            migrations_applied = True
        
        # 版本 3: 修复video表的UNIQUE约束问题
        if current_version < 3:
            logger.info("执行迁移 3: 修复video表约束")
            
            # 删除有问题的UNIQUE约束
            try:
                # 检查是否存在UNIQUE约束
                cursor.execute("PRAGMA index_list(video)")
                indexes = cursor.fetchall()
                
                # 删除可能存在的UNIQUE约束
                for index in indexes:
                    index_name = index[1]
                    if 'path' in index_name.lower() or 'checksum' in index_name.lower():
                        cursor.execute(f"DROP INDEX IF EXISTS {index_name}")
                
                # 重新创建正确的索引（不包含UNIQUE约束）
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_video_path ON video(path)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_video_checksum ON video(checksum)")
                
            except Exception as e:
                logger.warning(f"修复约束时出现警告: {e}")
            
            cursor.execute("PRAGMA user_version = 3")
            migrations_applied = True
        
        # 提交更改
        conn.commit()
        conn.close()
        
        if migrations_applied:
            logger.info("数据库迁移完成")
        else:
            logger.info("数据库已是最新版本")
        
        return True
        
    except Exception as e:
        logger.error(f"数据库迁移失败: {e}")
        return False

def reset_database():
    """
    重置数据库（删除所有数据）
    """
    try:
        db_path = Path("instance/assets.db")
        if db_path.exists():
            db_path.unlink()
            logger.info("数据库已重置")
        
        # 重新初始化
        return init_database()
        
    except Exception as e:
        logger.error(f"数据库重置失败: {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "reset":
        print("重置数据库...")
        success = reset_database()
    else:
        print("初始化数据库...")
        success = init_database()
    
    if success:
        print("✅ 操作成功")
    else:
        print("❌ 操作失败")
        sys.exit(1) 