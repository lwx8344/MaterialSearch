#!/bin/bash

echo "================================================"
echo "MaterialSearch 本地素材搜索系统"
echo "================================================"
echo

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误：未找到Python3，请先安装Python 3.9或更高版本"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "检查依赖..."
pip install -r requirements.txt

# 启动服务
echo "启动服务..."
python start.py 