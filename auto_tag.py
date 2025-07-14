#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动标签脚本
利用MaterialSearch的向量数据库和CLIP模型，为图片和视频自动添加标签
"""

import json
import logging
import os
import pickle
import re
import shutil
from collections import defaultdict
from pathlib import Path

import numpy as np
from tqdm import tqdm

from config import *
from database import get_image_id_path_features, get_video_paths, get_frame_times_features_by_path
from models import DatabaseSession, Image, Video
from process_assets import process_text
from tag_vocabulary import ENGLISH_TAGS, ENGLISH_TO_CHINESE

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AutoTagger:
    def __init__(self, tag_cache_file="tag_vectors.pkl"):
        """
        初始化自动标签器
        :param tag_cache_file: 标签向量缓存文件路径
        """
        self.tag_cache_file = tag_cache_file
        self.tag_vectors = {}  # 存储标签向量
        self.load_or_compute_tag_vectors()
        
    def load_or_compute_tag_vectors(self):
        """
        加载或计算标签向量
        """
        if os.path.exists(self.tag_cache_file):
            logger.info(f"从缓存文件加载标签向量: {self.tag_cache_file}")
            try:
                with open(self.tag_cache_file, 'rb') as f:
                    self.tag_vectors = pickle.load(f)
                logger.info(f"成功加载 {len(self.tag_vectors)} 个标签向量")
                return
            except Exception as e:
                logger.warning(f"加载标签向量缓存失败: {e}")
        
        logger.info("开始计算标签向量...")
        self.compute_tag_vectors()
        self.save_tag_vectors()
        
    def compute_tag_vectors(self):
        """
        计算所有标签的向量
        """
        logger.info(f"正在为 {len(ENGLISH_TAGS)} 个标签计算向量...")
        
        # 逐个处理标签以获得准确的向量
        for tag in tqdm(ENGLISH_TAGS, desc="计算标签向量"):
            # 计算单个标签的文本特征
            text_feature = process_text(tag)
            if text_feature is None:
                logger.warning(f"无法计算标签向量: {tag}")
                continue
                
            # 存储标签向量
            self.tag_vectors[tag] = text_feature.flatten()
                
        logger.info(f"完成标签向量计算，共 {len(self.tag_vectors)} 个标签")
        
    def save_tag_vectors(self):
        """
        保存标签向量到缓存文件
        """
        try:
            with open(self.tag_cache_file, 'wb') as f:
                pickle.dump(self.tag_vectors, f)
            logger.info(f"标签向量已保存到: {self.tag_cache_file}")
        except Exception as e:
            logger.error(f"保存标签向量失败: {e}")
            
    def compute_similarity(self, image_feature, tag_vectors):
        """
        计算图片特征与标签向量的相似度
        :param image_feature: 图片特征向量
        :param tag_vectors: 标签向量字典
        :return: 相似度分数字典
        """
        similarities = {}
        image_feature = image_feature.flatten()
        
        for tag, tag_vector in tag_vectors.items():
            # 计算余弦相似度
            similarity = np.dot(image_feature, tag_vector) / (np.linalg.norm(image_feature) * np.linalg.norm(tag_vector))
            similarities[tag] = float(similarity)
            
        return similarities
        
    def get_top_tags(self, similarities, top_k=5, threshold=0.3):
        """
        获取相似度最高的标签
        :param similarities: 相似度字典
        :param top_k: 返回前k个标签
        :param threshold: 相似度阈值
        :return: 标签列表
        """
        # 过滤低于阈值的标签
        filtered_similarities = {tag: score for tag, score in similarities.items() if score >= threshold}
        
        # 按相似度排序
        sorted_tags = sorted(filtered_similarities.items(), key=lambda x: x[1], reverse=True)
        
        # 返回前k个标签
        return sorted_tags[:top_k]
        
    def process_image(self, image_id, image_path, image_feature):
        """
        处理单张图片
        :param image_id: 图片ID
        :param image_path: 图片路径
        :param image_feature: 图片特征
        :return: 标签列表
        """
        # 计算相似度
        similarities = self.compute_similarity(image_feature, self.tag_vectors)
        
        # 获取top标签
        top_tags = self.get_top_tags(similarities, top_k=5, threshold=0.3)
        
        if not top_tags:
            logger.warning(f"图片 {image_path} 没有找到匹配的标签")
            return []
            
        # 转换为中文标签
        chinese_tags = []
        for tag, score in top_tags:
            chinese_tag = ENGLISH_TO_CHINESE.get(tag, tag)
            chinese_tags.append(chinese_tag)
            logger.debug(f"图片 {image_path}: {chinese_tag} (相似度: {score:.3f})")
            
        return chinese_tags
        
    def process_video(self, video_path):
        """
        处理视频，分析所有帧并合并标签
        :param video_path: 视频路径
        :return: 视频标签列表
        """
        logger.info(f"处理视频: {video_path}")
        
        with DatabaseSession() as session:
            frame_times, features = get_frame_times_features_by_path(session, video_path)
            
        if not features:
            logger.warning(f"视频 {video_path} 没有找到帧特征")
            return []
            
        # 处理所有帧
        all_tags = []
        for i, feature in enumerate(features):
            feature_array = np.frombuffer(feature, dtype=np.float32).reshape(1, -1)
            similarities = self.compute_similarity(feature_array, self.tag_vectors)
            top_tags = self.get_top_tags(similarities, top_k=3, threshold=0.3)
            
            for tag, score in top_tags:
                chinese_tag = ENGLISH_TO_CHINESE.get(tag, tag)
                all_tags.append(chinese_tag)
                
        # 统计标签频率
        tag_counts = defaultdict(int)
        for tag in all_tags:
            tag_counts[tag] += 1
            
        # 按频率排序，取前10个
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        video_tags = [tag for tag, count in sorted_tags[:10] if count >= 2]  # 至少出现2次
        
        logger.info(f"视频 {video_path} 标签: {video_tags}")
        return video_tags
        
    def update_database_tags(self, file_type, file_id, file_path, tags):
        """
        更新数据库中的标签
        :param file_type: 文件类型 ('image' 或 'video')
        :param file_id: 文件ID
        :param file_path: 文件路径
        :param tags: 标签列表
        """
        with DatabaseSession() as session:
            if file_type == 'image':
                record = session.query(Image).filter_by(id=file_id).first()
            else:
                record = session.query(Video).filter_by(id=file_id).first()
                
            if record and record is not None:
                record.tags = str(json.dumps(tags, ensure_ascii=False))
                session.commit()
                logger.info(f"已更新 {file_type} {file_path} 的标签: {tags}")
            else:
                logger.warning(f"未找到 {file_type} 记录: {file_path}")
                
    def generate_filename(self, original_path, tags):
        """
        根据标签生成新文件名
        :param original_path: 原始文件路径
        :param tags: 标签列表
        :return: 新文件路径
        """
        if not tags:
            return original_path
            
        # 获取文件信息
        path_obj = Path(original_path)
        extension = path_obj.suffix
        parent_dir = path_obj.parent
        
        # 取前3个标签作为文件名
        tag_part = "_".join(tags[:3])
        
        # 清理标签字符串，移除特殊字符
        tag_part = re.sub(r'[^\w\s-]', '', tag_part)
        tag_part = re.sub(r'[-\s]+', '_', tag_part)
        
        # 生成新文件名
        new_filename = f"{tag_part}{extension}"
        new_path = parent_dir / new_filename
        
        # 如果文件已存在，添加数字后缀
        counter = 1
        while new_path.exists():
            new_filename = f"{tag_part}_{counter}{extension}"
            new_path = parent_dir / new_filename
            counter += 1
            
        return str(new_path)
        
    def rename_file(self, old_path, new_path):
        """
        重命名文件
        :param old_path: 旧路径
        :param new_path: 新路径
        :return: 是否成功
        """
        try:
            shutil.move(old_path, new_path)
            logger.info(f"文件重命名: {old_path} -> {new_path}")
            return True
        except Exception as e:
            logger.error(f"文件重命名失败: {old_path} -> {new_path}, 错误: {e}")
            return False
            
    def process_all_images(self, enable_rename=False):
        """
        处理所有图片
        :param enable_rename: 是否启用重命名
        """
        logger.info("开始处理所有图片...")
        
        with DatabaseSession() as session:
            ids, paths, features = get_image_id_path_features(session)
            
        if not ids:
            logger.info("数据库中没有图片")
            return
            
        logger.info(f"找到 {len(ids)} 张图片")
        
        for i, (image_id, image_path, image_feature) in enumerate(zip(ids, paths, features)):
            logger.info(f"处理图片 {i+1}/{len(ids)}: {image_path}")
            
            # 检查是否已有标签
            with DatabaseSession() as session:
                record = session.query(Image).filter_by(id=image_id).first()
                if record is not None and record.tags is not None:
                    logger.info(f"图片 {image_path} 已有标签，跳过")
                    continue
                    
            # 处理图片
            feature_array = np.frombuffer(image_feature, dtype=np.float32).reshape(1, -1)
            tags = self.process_image(image_id, image_path, feature_array)
            
            if tags:
                # 更新数据库
                self.update_database_tags('image', image_id, image_path, tags)
                
                # 重命名文件
                if enable_rename:
                    new_path = self.generate_filename(image_path, tags)
                    if new_path != image_path:
                        if self.rename_file(image_path, new_path):
                            # 更新数据库中的路径
                            with DatabaseSession() as session:
                                record = session.query(Image).filter_by(id=image_id).first()
                                if record is not None:
                                    record.path = str(new_path)
                                    session.commit()
                                    
    def process_all_videos(self, enable_rename=False):
        """
        处理所有视频
        :param enable_rename: 是否启用重命名
        """
        logger.info("开始处理所有视频...")
        
        with DatabaseSession() as session:
            video_paths = list(get_video_paths(session))
            
        if not video_paths:
            logger.info("数据库中没有视频")
            return
            
        logger.info(f"找到 {len(video_paths)} 个视频")
        
        for i, video_path in enumerate(video_paths):
            logger.info(f"处理视频 {i+1}/{len(video_paths)}: {video_path}")
            
            # 检查是否已有标签
            with DatabaseSession() as session:
                record = session.query(Video).filter_by(path=video_path).first()
                if record is not None and record.tags is not None:
                    logger.info(f"视频 {video_path} 已有标签，跳过")
                    continue
                    
            # 处理视频
            tags = self.process_video(video_path)
            
            if tags:
                # 更新数据库中该视频的所有帧记录
                with DatabaseSession() as session:
                    video_records = session.query(Video).filter_by(path=video_path).all()
                    for record in video_records:
                        record.tags = str(json.dumps(tags, ensure_ascii=False))
                    session.commit()
                    
                # 重命名文件
                if enable_rename:
                    new_path = self.generate_filename(video_path, tags)
                    if new_path != video_path:
                        if self.rename_file(video_path, new_path):
                            # 更新数据库中的所有相关路径
                            with DatabaseSession() as session:
                                video_records = session.query(Video).filter_by(path=video_path).all()
                                for record in video_records:
                                    record.path = str(new_path)
                                session.commit()
                                
    def run(self, enable_rename=False):
        """
        运行自动标签程序
        :param enable_rename: 是否启用文件重命名
        """
        logger.info("开始自动标签程序...")
        
        # 处理图片
        self.process_all_images(enable_rename)
        
        # 处理视频
        self.process_all_videos(enable_rename)
        
        logger.info("自动标签程序完成！")


def main():
    """
    主函数
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="自动标签脚本")
    parser.add_argument("--rename", action="store_true", help="启用文件重命名")
    parser.add_argument("--images-only", action="store_true", help="只处理图片")
    parser.add_argument("--videos-only", action="store_true", help="只处理视频")
    
    args = parser.parse_args()
    
    # 创建自动标签器
    tagger = AutoTagger()
    
    if args.images_only:
        tagger.process_all_images(args.rename)
    elif args.videos_only:
        tagger.process_all_videos(args.rename)
    else:
        tagger.run(args.rename)


if __name__ == "__main__":
    main() 