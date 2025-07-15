#!/usr/bin/env python3
"""
修复数据库约束问题
Fix Database Constraint Issues
"""

import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

def fix_video_table():
    """
    修复video表的约束问题
    """
    try:
        db_path = Path("instance/assets.db")
        if not db_path.exists():
            logger.error("数据库文件不存在")
            return False
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        logger.info("开始修复video表...")
        
        # 1. 备份现有数据
        logger.info("备份现有数据...")
        cursor.execute("SELECT * FROM video")
        video_data = cursor.fetchall()
        logger.info(f"备份了 {len(video_data)} 条视频记录")
        
        # 2. 删除旧表
        logger.info("删除旧表...")
        cursor.execute("DROP TABLE IF EXISTS video")
        
        # 3. 创建新表（没有UNIQUE约束）
        logger.info("创建新表...")
        cursor.execute("""
            CREATE TABLE video (
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
        
        # 4. 创建索引（不包含UNIQUE约束）
        cursor.execute("CREATE INDEX idx_video_path ON video(path)")
        cursor.execute("CREATE INDEX idx_video_modify_time ON video(modify_time)")
        cursor.execute("CREATE INDEX idx_video_checksum ON video(checksum)")
        
        # 5. 恢复数据（跳过有问题的记录）
        logger.info("恢复数据...")
        restored_count = 0
        skipped_count = 0
        
        for row in video_data:
            try:
                # 检查是否有重复的path+frame_time组合
                cursor.execute(
                    "SELECT COUNT(*) FROM video WHERE path = ? AND frame_time = ?",
                    (row[1], row[3])  # path, frame_time
                )
                if cursor.fetchone()[0] == 0:
                    # 插入数据，跳过checksum如果为NULL
                    if row[5] is not None:  # checksum不为NULL
                        cursor.execute("""
                            INSERT INTO video (path, original_name, frame_time, modify_time, features, checksum, tags)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (row[1], row[2], row[3], row[4], row[6], row[5], row[7] if len(row) > 7 else None))
                    else:
                        cursor.execute("""
                            INSERT INTO video (path, original_name, frame_time, modify_time, features, tags)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (row[1], row[2], row[3], row[4], row[6], row[7] if len(row) > 7 else None))
                    restored_count += 1
                else:
                    skipped_count += 1
            except Exception as e:
                logger.warning(f"跳过有问题的记录: {e}")
                skipped_count += 1
        
        # 6. 提交更改
        conn.commit()
        conn.close()
        
        logger.info(f"修复完成！恢复了 {restored_count} 条记录，跳过了 {skipped_count} 条记录")
        return True
        
    except Exception as e:
        logger.error(f"修复失败: {e}")
        return False

def verify_fix():
    """
    验证修复结果
    """
    try:
        db_path = Path("instance/assets.db")
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 检查表结构
        cursor.execute(".schema video")
        schema = cursor.fetchall()
        
        # 检查是否有UNIQUE约束
        has_unique = any("UNIQUE" in line[0] for line in schema)
        
        # 检查checksum是否允许NULL
        cursor.execute("PRAGMA table_info(video)")
        columns = cursor.fetchall()
        checksum_nullable = any(col[1] == 'checksum' and col[3] == 0 for col in columns)
        
        conn.close()
        
        if not has_unique and checksum_nullable:
            logger.info("✅ 修复验证成功！")
            return True
        else:
            logger.error("❌ 修复验证失败！")
            return False
            
    except Exception as e:
        logger.error(f"验证失败: {e}")
        return False

def main():
    """主函数"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("🔧 修复数据库约束问题")
    print("="*50)
    
    if fix_video_table():
        if verify_fix():
            print("🎉 数据库修复成功！")
            print("现在可以正常扫描视频了。")
        else:
            print("⚠️ 修复可能不完整，请检查日志。")
    else:
        print("❌ 数据库修复失败！")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 