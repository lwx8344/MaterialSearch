# MaterialSearch 简化版部署指南

## 项目简介

MaterialSearch 是一个本地素材搜索系统，支持：
- 文字搜图
- 以图搜图  
- 文字搜视频
- 以图搜视频
- 图文相似度计算

## 快速开始

### 1. 环境要求

- Python 3.9 或更高版本
- 内存：最少 2GB，推荐 4GB 以上
- 存储：根据素材数量而定
- 可选：GPU 加速（CUDA/MPS/DirectML）

### 2. 安装依赖

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# Windows 用户可以使用
pip install -r requirements_windows.txt
```

### 3. 配置素材路径

创建 `.env` 文件（可选）：

```env
# 素材路径（逗号分隔多个路径）
ASSETS_PATH=/path/to/your/photos,/path/to/your/videos

# 服务器配置
HOST=127.0.0.1
PORT=8085

# 登录配置（可选）
ENABLE_LOGIN=True
USERNAME=admin
PASSWORD=your_password

# 模型配置
MODEL_NAME=openai/clip-vit-base-patch16
DEVICE=auto
```

### 4. 启动服务

#### 方法一：使用简化启动脚本（推荐）

```bash
python start.py
```

#### 方法二：使用简化主程序

```bash
python main_simple.py
```

#### 方法三：使用原始主程序

```bash
python main.py
```

### 5. 访问系统

打开浏览器访问：`http://127.0.0.1:8085`

## 配置说明

### 素材路径配置

- `ASSETS_PATH`: 素材所在目录，支持多个路径（逗号分隔）
- `SKIP_PATH`: 跳过扫描的目录
- `IMAGE_EXTENSIONS`: 支持的图片格式
- `VIDEO_EXTENSIONS`: 支持的视频格式

### 模型配置

- `MODEL_NAME`: CLIP 模型名称
  - 中文小模型：`OFA-Sys/chinese-clip-vit-base-patch16`
  - 中文大模型：`OFA-Sys/chinese-clip-vit-large-patch14-336px`
  - 英文小模型：`openai/clip-vit-base-patch16`
  - 英文大模型：`openai/clip-vit-large-patch14-336`

- `DEVICE`: 推理设备
  - `auto`: 自动选择（推荐）
  - `cpu`: CPU 推理
  - `cuda`: NVIDIA GPU
  - `mps`: Apple Silicon GPU
  - `directml`: DirectML GPU

### 性能优化

- `SCAN_PROCESS_BATCH_SIZE`: 批处理大小
  - 4GB 显存：6
  - 8GB 显存：12
  - 16GB+ 显存：24

## 使用说明

### 1. 扫描素材

首次使用需要扫描素材：
1. 点击"开始扫描"按钮
2. 等待扫描完成
3. 扫描完成后即可开始搜索

### 2. 搜索功能

- **文字搜图/视频**: 输入描述文字进行搜索
- **以图搜图/视频**: 上传图片进行相似度搜索
- **图文相似度**: 计算文字和图片的相似度分数

### 3. 高级功能

- **路径过滤**: 可以按文件路径过滤搜索结果
- **时间过滤**: 可以按文件修改时间过滤搜索结果
- **阈值调整**: 可以调整搜索阈值来控制结果质量

## 故障排除

### 常见问题

1. **模型下载失败**
   - 检查网络连接
   - 设置代理：`export http_proxy=http://127.0.0.1:7890`
   - 使用离线模式：`export TRANSFORMERS_OFFLINE=1`

2. **内存不足**
   - 减少 `SCAN_PROCESS_BATCH_SIZE`
   - 使用较小的模型
   - 增加系统内存

3. **GPU 不可用**
   - 检查 CUDA 安装
   - 检查 PyTorch 版本
   - 尝试使用 CPU 模式

4. **扫描速度慢**
   - 使用 GPU 加速
   - 增加批处理大小
   - 减少扫描路径

### 日志查看

日志文件：`materialsearch.log`

```bash
# 查看实时日志
tail -f materialsearch.log

# 查看错误日志
grep ERROR materialsearch.log
```

## 文件结构

```
MaterialSearch/
├── start.py              # 简化启动脚本
├── main_simple.py        # 简化主程序
├── config_simple.py      # 简化配置文件
├── init_simple.py        # 简化初始化模块
├── main.py              # 原始主程序
├── config.py            # 原始配置文件
├── requirements.txt     # Python 依赖
├── static/              # 前端文件
├── instance/            # 数据库文件
└── tmp/                 # 临时文件
```

## 版本说明

- **简化版**: 移除了复杂的加密逻辑，更容易理解和修改
- **原始版**: 包含完整的加密保护功能

## 技术支持

- 项目地址：https://github.com/chn-lee-yumi/MaterialSearch/
- 问题反馈：请在 GitHub 上提交 Issue
- 使用交流：欢迎提交 Pull Request

## 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。 