#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MaterialSearch 简化主程序
使用简化的配置和初始化模块，移除复杂的加密逻辑
"""

import logging
import shutil
import threading
from functools import wraps
from io import BytesIO

from flask import Flask, abort, jsonify, redirect, request, send_file, session, url_for

# 导入简化的配置和初始化模块
from config_simple import *
from init_simple import init as init_system

# 导入其他必要模块
from database import get_image_path_by_id, is_video_exist, get_pexels_video_count
from models import DatabaseSession, DatabaseSessionPexelsVideo
from process_assets import match_text_and_image, process_image, process_text
from scan import Scanner
from search import (
    clean_cache,
    search_image_by_image,
    search_image_by_text_path_time,
    search_video_by_image,
    search_video_by_text_path_time,
    search_pexels_video_by_text,
)
from utils import crop_video, get_hash, resize_image_with_aspect_ratio

logger = logging.getLogger(__name__)
app = Flask(__name__)
app.secret_key = "MaterialSearch-Simple-Version"

scanner = Scanner()


def init():
    """
    清理和创建临时文件夹，初始化扫描线程（包括数据库初始化），根据AUTO_SCAN决定是否开启自动扫描线程
    """
    global scanner
    
    # 运行系统初始化
    init_system()
    
    # 运行数据库迁移
    try:
        from database_migration import init_database
        logger.info("开始数据库迁移...")
        if init_database():
            logger.info("数据库迁移完成")
        else:
            logger.error("数据库迁移失败")
    except Exception as e:
        logger.error(f"数据库迁移出错: {e}")
    
    # 检查ASSETS_PATH是否存在
    for path in ASSETS_PATH:
        if not os.path.isdir(path):
            logger.warning(f"ASSETS_PATH检查：路径 {path} 不存在！请检查输入的路径是否正确！")
    
    # 删除临时目录中所有文件
    shutil.rmtree(f'{TEMP_PATH}', ignore_errors=True)
    os.makedirs(f'{TEMP_PATH}/upload')
    os.makedirs(f'{TEMP_PATH}/video_clips')
    
    # 初始化扫描线程
    scanner.init()
    if AUTO_SCAN:
        auto_scan_thread = threading.Thread(target=scanner.auto_scan, args=())
        auto_scan_thread.start()


def login_required(view_func):
    """
    装饰器函数，用于控制需要登录认证的视图
    """
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        # 检查登录开关状态
        if ENABLE_LOGIN:
            # 如果开关已启用，则进行登录认证检查
            if "username" not in session:
                # 如果用户未登录，则重定向到登录页面
                return redirect(url_for("login"))
        # 调用原始的视图函数
        return view_func(*args, **kwargs)
    return wrapper


@app.route("/", methods=["GET"])
@login_required
def index_page():
    """主页"""
    return app.send_static_file("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """登录"""
    if request.method == "POST":
        # 获取用户IP地址
        ip_addr = request.environ.get("HTTP_X_FORWARDED_FOR", request.remote_addr)
        # 获取表单数据
        username = request.form["username"]
        password = request.form["password"]
        # 简单的验证逻辑
        if username == USERNAME and password == PASSWORD:
            # 登录成功，将用户名保存到会话中
            logger.info(f"用户登录成功 {ip_addr}")
            session["username"] = username
            return redirect(url_for("index_page"))
        # 登录失败，重定向到登录页面
        logger.info(f"用户登录失败 {ip_addr}")
        return redirect(url_for("login"))
    return app.send_static_file("login.html")


@app.route("/logout", methods=["GET", "POST"])
def logout():
    """登出"""
    # 清除会话数据
    session.clear()
    return redirect(url_for("login"))


@app.route("/api/scan", methods=["GET"])
@login_required
def api_scan():
    """开始扫描"""
    global scanner
    if not scanner.is_scanning:
        scan_thread = threading.Thread(target=scanner.scan, args=(False,))
        scan_thread.start()
        return jsonify({"status": "start scanning"})
    return jsonify({"status": "already scanning"})


@app.route("/api/status", methods=["GET"])
@login_required
def api_status():
    """状态"""
    global scanner
    result = scanner.get_status()
    with DatabaseSessionPexelsVideo() as session:
        result["total_pexels_videos"] = get_pexels_video_count(session)
    
    # 检查模型状态
    try:
        from process_assets import model, processor
        result["model_loaded"] = model is not None and processor is not None
        result["model_name"] = MODEL_NAME if model is not None else None
    except Exception as e:
        result["model_loaded"] = False
        result["model_name"] = None
        logger.warning(f"模型状态检查失败: {e}")
    
    return jsonify(result)


@app.route("/api/clean_cache", methods=["GET", "POST"])
@login_required
def api_clean_cache():
    """
    清缓存
    :return: 204 No Content
    """
    clean_cache()
    return "", 204


@app.route("/api/match", methods=["POST"])
@login_required
def api_match():
    """
    匹配文字对应的素材
    :return: json格式的素材信息列表
    """
    data = request.get_json()
    top_n = int(data["top_n"])
    search_type = data["search_type"]
    positive_threshold = data["positive_threshold"]
    negative_threshold = data["negative_threshold"]
    image_threshold = data["image_threshold"]
    img_id = data["img_id"]
    path = data["path"]
    start_time = data["start_time"]
    end_time = data["end_time"]
    upload_file_path = session.get('upload_file_path', '')
    session['upload_file_path'] = ""
    
    if search_type in (1, 3, 4):
        if not upload_file_path or not os.path.exists(upload_file_path):
            return "你没有上传文件！", 400
    
    logger.debug(data)
    
    # 进行匹配
    if search_type == 0:  # 文字搜图
        results = search_image_by_text_path_time(data["positive"], data["negative"], positive_threshold, negative_threshold,
                                                 path, start_time, end_time)
    elif search_type == 1:  # 以图搜图
        results = search_image_by_image(upload_file_path, image_threshold, path, start_time, end_time)
    elif search_type == 2:  # 文字搜视频
        results = search_video_by_text_path_time(data["positive"], data["negative"], positive_threshold, negative_threshold,
                                                 path, start_time, end_time)
    elif search_type == 3:  # 以图搜视频
        results = search_video_by_image(upload_file_path, image_threshold, path, start_time, end_time)
    elif search_type == 4:  # 图文相似度匹配
        score = match_text_and_image(process_text(data["positive"]), process_image(upload_file_path)) * 100
        return jsonify({"score": "%.2f" % score})
    elif search_type == 5:  # 文字搜Pexels视频
        results = search_pexels_video_by_text(data["positive"], data["negative"], positive_threshold, negative_threshold)
    else:
        return "不支持的搜索类型", 400
    
    return jsonify(results[:top_n])


@app.route("/api/get_image/<int:image_id>", methods=["GET"])
@login_required
def api_get_image(image_id):
    """获取图片"""
    try:
        image_path = get_image_path_by_id(image_id)
        if not image_path or not os.path.exists(image_path):
            abort(404)
        
        # 检查文件大小
        file_size = os.path.getsize(image_path)
        if file_size > 50 * 1024 * 1024:  # 50MB
            # 大文件需要调整大小
            resized_image = resize_image_with_aspect_ratio(image_path, max_width=1920, max_height=1080)
            return send_file(BytesIO(resized_image), mimetype='image/jpeg')
        
        return send_file(image_path)
    except Exception as e:
        logger.error(f"获取图片失败: {e}")
        abort(404)


@app.route("/api/get_video/<video_path>", methods=["GET"])
@login_required
def api_get_video(video_path):
    """获取视频"""
    try:
        # 解码视频路径
        video_path = video_path.replace('_', '/')
        if not is_video_exist(video_path):
            abort(404)
        
        return send_file(video_path)
    except Exception as e:
        logger.error(f"获取视频失败: {e}")
        abort(404)


@app.route(
    "/api/download_video_clip/<video_path>/<int:start_time>/<int:end_time>",
    methods=["GET"],
)
@login_required
def api_download_video_clip(video_path, start_time, end_time):
    """下载视频片段"""
    try:
        # 解码视频路径
        video_path = video_path.replace('_', '/')
        if not is_video_exist(video_path):
            abort(404)
        
        # 裁剪视频
        output_path = crop_video(video_path, start_time, end_time, VIDEO_EXTENSION_LENGTH)
        if not output_path or not os.path.exists(output_path):
            abort(404)
        
        return send_file(output_path, as_attachment=True, download_name=f"clip_{start_time}_{end_time}.mp4")
    except Exception as e:
        logger.error(f"下载视频片段失败: {e}")
        abort(404)


@app.route("/api/upload", methods=["POST"])
@login_required
def api_upload():
    """上传文件"""
    try:
        if 'file' not in request.files:
            return "没有文件", 400
        
        file = request.files['file']
        if file.filename == '':
            return "没有选择文件", 400
        
        # 保存文件
        filename = get_hash(file.read()) + os.path.splitext(file.filename)[1]
        file_path = os.path.join(TEMP_PATH, 'upload', filename)
        
        file.seek(0)  # 重置文件指针
        file.save(file_path)
        
        session['upload_file_path'] = file_path
        return jsonify({"status": "success"})
    except Exception as e:
        logger.error(f"文件上传失败: {e}")
        return "上传失败", 500


if __name__ == '__main__':
    # 打印配置信息
    from config_simple import print_config
    print_config()
    
    # 初始化
    init()
    
    # 启动Flask应用
    app.run(host=HOST, port=PORT, debug=FLASK_DEBUG) 