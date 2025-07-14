# MaterialSearch 部署指南

## 概述

本指南将帮助你在新机器上快速部署 MaterialSearch 自动标签系统，确保开箱即用。

## 系统要求

### 基础要求
- **操作系统**: Windows 10+, macOS 10.14+, Ubuntu 18.04+
- **Python**: 3.8 或更高版本
- **内存**: 至少 4GB RAM（推荐 8GB+）
- **存储**: 足够的磁盘空间用于存储媒体文件和数据库
- **网络**: 首次运行需要网络连接下载AI模型

### 可选要求
- **GPU**: NVIDIA GPU（支持CUDA）可显著提升处理速度
- **显存**: 至少 4GB 显存（推荐 8GB+）

## 快速部署

### 方法一：自动部署（推荐）

1. **下载项目**
   ```bash
   git clone https://github.com/chn-lee-yumi/MaterialSearch.git
   cd MaterialSearch
   ```

2. **运行自动部署脚本**
   ```bash
   python3 setup.py
   ```

3. **配置环境**
   - 编辑 `.env` 文件，设置你的媒体文件路径
   - 根据需要调整其他配置参数

4. **启动系统**
   - Windows: 双击 `start.bat`
   - Unix/Linux/macOS: 运行 `./start.sh`

### 方法二：手动部署

1. **创建虚拟环境**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Unix/Linux/macOS
   # 或
   venv\Scripts\activate     # Windows
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **初始化数据库**
   ```bash
   python3 simple_db_init.py
   ```

4. **配置环境**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件
   ```

5. **启动系统**
   ```bash
   python3 main.py
   ```

## 配置说明

### 环境变量配置

编辑 `.env` 文件，主要配置项：

```bash
# 服务器配置
HOST=127.0.0.1          # 监听地址
PORT=8085               # 监听端口

# 扫描配置
ASSETS_PATH=/path/to/your/media/files  # 媒体文件路径（重要！）
SKIP_PATH=/tmp          # 跳过扫描的路径
IMAGE_EXTENSIONS=.jpg,.jpeg,.png,.gif,.heic,.webp,.bmp
VIDEO_EXTENSIONS=.mp4,.flv,.mov,.mkv,.webm,.avi

# 模型配置
MODEL_NAME=openai/clip-vit-base-patch16  # AI模型
DEVICE=auto              # 设备选择：auto/cpu/cuda/mps

# 性能配置
SCAN_PROCESS_BATCH_SIZE=6  # 批处理大小
FRAME_INTERVAL=2           # 视频帧间隔
```

### 性能优化建议

1. **GPU 加速**
   - 如果有 NVIDIA GPU，设置 `DEVICE=cuda`
   - 如果有 Apple Silicon，设置 `DEVICE=mps`

2. **内存优化**
   - 根据可用内存调整 `SCAN_PROCESS_BATCH_SIZE`
   - 4GB RAM: 设置为 4
   - 8GB RAM: 设置为 6-8
   - 16GB+ RAM: 设置为 12-16

3. **存储优化**
   - 确保有足够的磁盘空间
   - 定期清理临时文件：`rm -rf ./tmp/*`

## 使用流程

### 1. 首次使用

1. **启动系统**
   ```bash
   python3 main.py
   ```

2. **访问Web界面**
   - 打开浏览器访问: http://127.0.0.1:8085

3. **扫描媒体文件**
   - 点击"开始扫描"按钮
   - 等待扫描完成（首次扫描可能需要较长时间）

### 2. 自动标签

1. **运行自动标签脚本**
   ```bash
   # 为所有文件添加标签
   python3 auto_tag.py
   
   # 添加标签并重命名文件
   python3 auto_tag.py --rename
   
   # 只处理图片
   python3 auto_tag.py --images-only
   
   # 只处理视频
   python3 auto_tag.py --videos-only
   ```

2. **查看结果**
   - 在Web界面中查看已添加的标签
   - 检查文件是否已重命名

### 3. 搜索和筛选

1. **文字搜索**
   - 在搜索框中输入关键词
   - 支持中英文搜索

2. **图片搜索**
   - 上传参考图片
   - 系统会找到相似的媒体文件

3. **标签筛选**
   - 使用已添加的标签进行筛选
   - 组合多个标签进行精确搜索

## 故障排除

### 常见问题

1. **Python版本问题**
   ```bash
   # 检查Python版本
   python3 --version
   # 需要3.8+
   ```

2. **依赖安装失败**
   ```bash
   # 使用虚拟环境
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **数据库错误**
   ```bash
   # 重新初始化数据库
   python3 simple_db_init.py
   ```

4. **模型下载失败**
   ```bash
   # 检查网络连接
   # 或手动下载模型到 ~/.cache/huggingface/hub/
   ```

5. **内存不足**
   ```bash
   # 减少批处理大小
   # 编辑 .env 文件，设置 SCAN_PROCESS_BATCH_SIZE=4
   ```

6. **GPU相关问题**
   ```bash
   # 检查CUDA安装
   nvidia-smi
   
   # 或使用CPU模式
   # 编辑 .env 文件，设置 DEVICE=cpu
   ```

### 日志查看

- 系统日志会显示在控制台
- 错误信息会包含详细的堆栈跟踪
- 建议保存日志文件以便问题排查

## 高级配置

### 自定义标签库

编辑 `tag_vocabulary.py` 文件：

```python
TAG_VOCABULARY = {
    "你的中文标签": "your_english_tag",
    # 添加更多标签...
}
```

### 数据库迁移

如果需要升级数据库结构：

```bash
# 验证数据库结构
python3 simple_db_init.py --validate

# 重置数据库（会删除所有数据）
rm ./instance/assets.db
python3 simple_db_init.py
```

### 性能监控

1. **监控资源使用**
   ```bash
   # CPU和内存使用
   top
   
   # GPU使用（如果有）
   nvidia-smi
   ```

2. **优化建议**
   - 根据硬件配置调整批处理大小
   - 使用SSD存储提升I/O性能
   - 确保有足够的可用内存

## 备份和恢复

### 数据备份

1. **数据库备份**
   ```bash
   cp ./instance/assets.db ./backup/assets_$(date +%Y%m%d).db
   ```

2. **配置文件备份**
   ```bash
   cp .env ./backup/env_$(date +%Y%m%d)
   ```

### 数据恢复

1. **恢复数据库**
   ```bash
   cp ./backup/assets_20250101.db ./instance/assets.db
   ```

2. **恢复配置**
   ```bash
   cp ./backup/env_20250101 .env
   ```

## 安全建议

1. **网络安全**
   - 默认只监听本地地址（127.0.0.1）
   - 如需远程访问，请配置防火墙

2. **文件权限**
   - 确保媒体文件目录有适当的读取权限
   - 确保临时目录有写入权限

3. **数据保护**
   - 定期备份数据库
   - 不要将敏感文件放在扫描目录中

## 技术支持

### 获取帮助

1. **查看文档**
   - 阅读 `README.md` 和 `README_AUTO_TAG.md`

2. **检查日志**
   - 查看控制台输出的错误信息

3. **社区支持**
   - GitHub Issues: https://github.com/chn-lee-yumi/MaterialSearch/issues
   - 项目地址: https://github.com/chn-lee-yumi/MaterialSearch

### 贡献代码

欢迎提交 Pull Request 来改进项目！

## 更新日志

### v1.0.0
- 初始版本发布
- 支持图片和视频自动标签
- 支持文件自动重命名
- 完整的Web界面
- 数据库迁移系统
- 开箱即用的部署脚本 