#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MaterialSearch 简化启动脚本
整合了所有必要的初始化步骤，方便移植到其他机器运行
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_environment():
    """设置环境变量和基本配置"""
    # 设置默认的素材路径（如果未设置）
    if not os.getenv('ASSETS_PATH'):
        # 根据操作系统设置默认路径
        if sys.platform.startswith('win'):
            default_path = "C:/Users/Public/Pictures,C:/Users/Public/Videos"
        elif sys.platform.startswith('darwin'):  # macOS
            default_path = "/Users/Shared/Pictures,/Users/Shared/Videos"
        else:  # Linux
            default_path = "/home/shared/Pictures,/home/shared/Videos"
        
        os.environ['ASSETS_PATH'] = default_path
        print(f"设置默认素材路径: {default_path}")
    
    # 设置其他默认配置
    defaults = {
        'HOST': '127.0.0.1',
        'PORT': '8085',
        'LOG_LEVEL': 'INFO',
        'AUTO_SCAN': 'False',
        'ENABLE_LOGIN': 'False'
    }
    
    for key, value in defaults.items():
        if not os.getenv(key):
            os.environ[key] = value

def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('materialsearch.log', encoding='utf-8')
        ]
    )

def check_dependencies():
    """检查必要的依赖"""
    required_packages = [
        'torch', 'transformers', 'flask', 'sqlalchemy', 
        'pillow', 'opencv-python', 'numpy', 'faiss-cpu'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("缺少以下依赖包:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\n请运行以下命令安装依赖:")
        print("pip install -r requirements.txt")
        return False
    
    return True

def create_directories():
    """创建必要的目录"""
    directories = ['tmp', 'tmp/upload', 'tmp/video_clips', 'instance']
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

def main():
    """主函数"""
    print("=" * 60)
    print("MaterialSearch 本地素材搜索系统")
    print("=" * 60)
    
    # 设置环境
    setup_environment()
    
    # 设置日志
    setup_logging()
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 创建目录
    create_directories()
    
    print("环境检查完成，正在启动服务...")
    
    # 导入并启动主程序
    try:
        from main import app, init
        
        # 初始化
        init()
        
        # 获取配置
        host = os.getenv('HOST', '127.0.0.1')
        port = int(os.getenv('PORT', 8085))
        debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        
        print(f"服务启动在: http://{host}:{port}")
        print("按 Ctrl+C 停止服务")
        
        # 启动Flask应用
        app.run(host=host, port=port, debug=debug)
        
    except KeyboardInterrupt:
        print("\n服务已停止")
    except Exception as e:
        print(f"启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 