@echo off
chcp 65001 >nul
echo ================================================
echo MaterialSearch 本地素材搜索系统
echo ================================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到Python，请先安装Python 3.9或更高版本
    pause
    exit /b 1
)

REM 检查虚拟环境
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
echo 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo 检查依赖...
pip install -r requirements_windows.txt

REM 启动服务
echo 启动服务...
python start.py

pause 