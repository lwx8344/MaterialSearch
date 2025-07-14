#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MaterialSearch 部署脚本
确保项目在新机器上开箱即用
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MaterialSearchSetup:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.requirements_file = self.project_root / "requirements.txt"
        self.instance_dir = self.project_root / "instance"
        self.tmp_dir = self.project_root / "tmp"
        
    def check_python_version(self):
        """检查Python版本"""
        logger.info("检查Python版本...")
        if sys.version_info < (3, 8):
            logger.error("需要Python 3.8或更高版本")
            return False
        logger.info(f"✓ Python版本: {sys.version}")
        return True
    
    def create_directories(self):
        """创建必要的目录"""
        logger.info("创建必要的目录...")
        
        directories = [
            self.instance_dir,
            self.tmp_dir,
            self.tmp_dir / "upload",
            self.tmp_dir / "video_clips"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"✓ 创建目录: {directory}")
        
        return True
    
    def install_dependencies(self):
        """安装依赖包"""
        logger.info("安装依赖包...")
        
        # 检查是否在虚拟环境中
        in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        
        if not in_venv:
            logger.warning("检测到系统Python环境，建议使用虚拟环境")
            logger.info("创建虚拟环境...")
            
            venv_path = self.project_root / "venv"
            try:
                subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
                logger.info("✓ 虚拟环境创建完成")
                
                # 获取虚拟环境中的Python路径
                if os.name == 'nt':  # Windows
                    python_path = venv_path / "Scripts" / "python.exe"
                else:  # Unix/Linux/macOS
                    python_path = venv_path / "bin" / "python"
                
                if python_path.exists():
                    logger.info("使用虚拟环境中的Python安装依赖...")
                    subprocess.run([
                        str(python_path), "-m", "pip", "install", "-r", str(self.requirements_file)
                    ], check=True)
                    logger.info("✓ 依赖包安装完成")
                    logger.info(f"请使用以下命令激活虚拟环境:")
                    if os.name == 'nt':
                        logger.info(f"  {venv_path}\\Scripts\\activate")
                    else:
                        logger.info(f"  source {venv_path}/bin/activate")
                    return True
                else:
                    logger.error("虚拟环境创建失败")
                    return False
                    
            except subprocess.CalledProcessError as e:
                logger.error(f"虚拟环境创建失败: {e}")
                return False
        else:
            # 已在虚拟环境中，直接安装
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(self.requirements_file)], check=True)
                logger.info("✓ 依赖包安装完成")
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"依赖包安装失败: {e}")
                return False
    
    def setup_database(self):
        """设置数据库"""
        logger.info("设置数据库...")
        
        try:
            from simple_db_init import init_database
            if init_database():
                logger.info("✓ 数据库设置完成")
                return True
            else:
                logger.error("数据库设置失败")
                return False
        except Exception as e:
            logger.error(f"数据库设置出错: {e}")
            return False
    
    def test_imports(self):
        """测试关键模块导入"""
        logger.info("测试模块导入...")
        
        try:
            import torch
            logger.info("✓ torch导入成功")
            
            import cv2
            logger.info("✓ cv2导入成功")
            
            import numpy as np
            logger.info("✓ numpy导入成功")
            
            from transformers import AutoModelForZeroShotImageClassification
            logger.info("✓ transformers导入成功")
            
            from models import DatabaseSession, Image, Video
            logger.info("✓ 数据库模型导入成功")
            
            return True
        except ImportError as e:
            logger.error(f"模块导入失败: {e}")
            return False
    
    def create_env_file(self):
        """创建环境配置文件"""
        logger.info("创建环境配置文件...")
        
        env_file = self.project_root / ".env"
        if not env_file.exists():
            env_content = """# MaterialSearch 环境配置
# 服务器配置
HOST=127.0.0.1
PORT=8085

# 扫描配置
ASSETS_PATH=/path/to/your/media/files
SKIP_PATH=/tmp
IMAGE_EXTENSIONS=.jpg,.jpeg,.png,.gif,.heic,.webp,.bmp
VIDEO_EXTENSIONS=.mp4,.flv,.mov,.mkv,.webm,.avi
IGNORE_STRINGS=thumb,avatar,__MACOSX,icons,cache
FRAME_INTERVAL=2
SCAN_PROCESS_BATCH_SIZE=6
IMAGE_MIN_WIDTH=64
IMAGE_MIN_HEIGHT=64
AUTO_SCAN=False
AUTO_SCAN_START_TIME=22:30
AUTO_SCAN_END_TIME=8:00
AUTO_SAVE_INTERVAL=100

# 模型配置
MODEL_NAME=openai/clip-vit-base-patch16
DEVICE=auto

# 搜索配置
CACHE_SIZE=64
POSITIVE_THRESHOLD=36
NEGATIVE_THRESHOLD=36
IMAGE_THRESHOLD=85

# 日志配置
LOG_LEVEL=INFO

# 其他配置
SQLALCHEMY_DATABASE_URL=sqlite:///./instance/assets.db
TEMP_PATH=./tmp
VIDEO_EXTENSION_LENGTH=0
ENABLE_LOGIN=False
USERNAME=admin
PASSWORD=password
FLASK_DEBUG=False
ENABLE_CHECKSUM=False
"""
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(env_content)
            logger.info("✓ 环境配置文件创建完成")
        else:
            logger.info("✓ 环境配置文件已存在")
        
        return True
    
    def create_startup_scripts(self):
        """创建启动脚本"""
        logger.info("创建启动脚本...")
        
        # Windows启动脚本
        if os.name == 'nt':
            bat_content = """@echo off
echo 启动 MaterialSearch...
python main.py
pause
"""
            with open(self.project_root / "start.bat", 'w', encoding='utf-8') as f:
                f.write(bat_content)
            logger.info("✓ Windows启动脚本创建完成")
        
        # Unix/Linux/macOS启动脚本
        sh_content = """#!/bin/bash
echo "启动 MaterialSearch..."
python3 main.py
"""
        sh_file = self.project_root / "start.sh"
        with open(sh_file, 'w', encoding='utf-8') as f:
            f.write(sh_content)
        
        # 设置执行权限
        try:
            os.chmod(sh_file, 0o755)
            logger.info("✓ Unix启动脚本创建完成")
        except Exception as e:
            logger.warning(f"无法设置Unix脚本执行权限: {e}")
        
        return True
    
    def create_readme(self):
        """创建使用说明"""
        logger.info("创建使用说明...")
        
        readme_content = """# MaterialSearch 自动标签系统

## 快速开始

### 1. 环境要求
- Python 3.8+
- 足够的磁盘空间用于存储媒体文件
- 建议有GPU加速（可选）

### 2. 配置
1. 编辑 `.env` 文件，设置你的媒体文件路径：
   ```
   ASSETS_PATH=/path/to/your/media/files
   ```

2. 根据需要调整其他配置参数

### 3. 启动
- Windows: 双击 `start.bat`
- Unix/Linux/macOS: 运行 `./start.sh`

### 4. 使用
1. 打开浏览器访问: http://127.0.0.1:8085
2. 点击"开始扫描"扫描媒体文件
3. 运行自动标签脚本：
   ```bash
   python auto_tag.py
   ```

## 功能特性
- 智能媒体文件搜索
- 自动标签识别
- 文件自动重命名
- 支持图片和视频

## 故障排除
- 查看日志文件了解详细错误信息
- 确保媒体文件路径正确
- 检查Python环境和依赖包

## 技术支持
项目地址: https://github.com/chn-lee-yumi/MaterialSearch
"""
        
        with open(self.project_root / "README_DEPLOY.md", 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        logger.info("✓ 使用说明创建完成")
        return True
    
    def run_setup(self):
        """运行完整设置"""
        logger.info("开始 MaterialSearch 设置...")
        
        steps = [
            ("检查Python版本", self.check_python_version),
            ("创建必要目录", self.create_directories),
            ("安装依赖包", self.install_dependencies),
            ("设置数据库", self.setup_database),
            ("测试模块导入", self.test_imports),
            ("创建环境配置", self.create_env_file),
            ("创建启动脚本", self.create_startup_scripts),
            ("创建使用说明", self.create_readme)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"\n=== {step_name} ===")
            if not step_func():
                logger.error(f"{step_name}失败，设置中断")
                return False
        
        logger.info("\n=== 设置完成 ===")
        logger.info("MaterialSearch 已准备就绪！")
        logger.info("请编辑 .env 文件设置你的媒体文件路径")
        logger.info("然后运行启动脚本开始使用")
        
        return True

def main():
    """主函数"""
    setup = MaterialSearchSetup()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("MaterialSearch 部署脚本")
        print("用法: python setup.py")
        print("选项:")
        print("  --help    显示帮助信息")
        return
    
    success = setup.run_setup()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 